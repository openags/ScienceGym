"""Continuous sensor-only walking, station preparation and visual tool pickup.

Only encoder/IMU samples and native RGB-D frames enter this actor. Controller
handoffs initialize internal estimates from those observations, never plant
poses. The stationary controller uses both feet as a declared support model;
actual support, contacts and all task outcomes require independent assessment.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import pickle
import sys

import mujoco
import numpy as np

from balance import Balance
from groot_walking_actor import GrootWalkingActor
from map_localization import MapLocalization
from observations import StateEstimate, robot_joints
from visual_tool_actor import ToolActor


def smooth(value):
    x = float(np.clip(value, 0., 1.))
    return x*x*x*(10. + x*(-15. + 6.*x))


class StationPreparation:
    def __init__(self, model, estimated_qpos, targets):
        self.m, self.d = model, mujoco.MjData(model)
        self.d.qpos[:] = estimated_qpos
        mujoco.mj_forward(model, self.d)
        self.estimate = StateEstimate(model, self.d)
        self.balance = Balance(model, self.d)
        self.balance.rotate_foot_constraints = True
        self.balance.solver_backend = 'clarabel'
        self.balance.pelvis_rotation = self.d.body('pelvis').xmat.reshape(3, 3).copy()
        self.com_start = self.d.subtree_com[model.body('pelvis').id].copy()
        self.com_goal = self.balance.com_target.copy()
        joints = model.actuator_trnid[:, 0]
        names = [model.joint(j).name for j in joints]
        self.qa, self.va = model.jnt_qposadr[joints], model.jnt_dofadr[joints]
        self.start = self.d.qpos[self.qa].copy()
        self.target = self.start.copy()
        self.selected = np.array([names.index(n) for n in targets])
        self.target[self.selected] = [targets[n] for n in targets]
        # The first native handoff settled 45 mrad away from the waist target
        # under equal posture weights. Prioritize that preparation coordinate
        # within the same constrained balance problem and source limits.
        self.posture_weights = np.ones(model.nu)
        self.posture_weights[names.index('waist_pitch_joint')] = 3.
        limits = model.jnt_range[joints]
        if np.any(self.target < limits[:, 0]) or np.any(self.target > limits[:, 1]):
            raise ValueError('Preparation target violates a source joint limit')
        self.hands = np.array([i for i, name in enumerate(names) if '_hand_' in name])
        self.selector = np.eye(model.nv)[:, self.va[self.hands]]
        self.next_balance = 0.
        self.body_torque = np.zeros(model.nu)
        self.error = self.speed = None
        self.stable_since = None

    def shift_estimated_frame(self, correction):
        # Map registration changes a coordinate estimate, not physical state
        # or a physical target. Translate every retained reference together.
        self.estimate.anchors += correction
        self.balance.foot_positions = [p + correction for p in self.balance.foot_positions]
        self.com_start += correction
        self.com_goal += correction
        self.balance.com_target += correction
        mujoco.mj_forward(self.m, self.d)

    def torque(self, packet, elapsed):
        self.estimate.update(packet)
        m, d = self.m, self.d
        fraction = smooth((elapsed - 2.) / 8.)
        posture = self.start + fraction * (self.target - self.start)
        if elapsed + 1e-8 >= self.next_balance:
            self.balance.com_target = self.com_start + smooth(elapsed / 2.) * (self.com_goal - self.com_start)
            self.body_torque = self.balance.torque(posture=posture, dt=.01,
                                                  posture_weights=self.posture_weights)
            self.next_balance = (round(elapsed * 100) + 1) / 100
        # The source finger inertias require a sampled-inertia bound, just as
        # in the walking/pickup actors. The model's masses remain unchanged.
        mass = np.zeros((m.nv, m.nv))
        mujoco.mj_fullM(m, d, mass)
        inertia = np.linalg.inv(self.selector.T @ np.linalg.solve(mass, self.selector))
        values, axes = np.linalg.eigh(inertia)
        if np.min(values) <= 0.:
            raise RuntimeError('Nonpositive preparation hand inertia')
        kp = np.minimum(3., .25 * values / .001**2)
        kd = np.minimum(2 * np.sqrt(kp * values), .4 * values / .001)
        torque = self.body_torque.copy()
        hand_error = axes.T @ (posture - d.qpos[self.qa])[self.hands]
        hand_speed = axes.T @ d.qvel[self.va[self.hands]]
        torque[self.hands] = ((d.qfrc_bias - d.qfrc_passive)[self.va[self.hands]]
                             + axes @ (kp * hand_error - kd * hand_speed))
        self.error = float(np.max(abs(self.target[self.selected] - d.qpos[self.qa[self.selected]])))
        self.speed = float(np.max(abs(d.qvel[self.va[self.selected]])))
        ready = elapsed >= 10. and self.error < .04 and self.speed < .08 and np.linalg.norm(d.qvel[:2]) < .03
        self.stable_since = (elapsed if self.stable_since is None else self.stable_since) if ready else None
        return np.clip(torque, m.actuator_ctrlrange[:, 0], m.actuator_ctrlrange[:, 1])


class StationPickupActor:
    fields = {'time_s', 'joint_position', 'joint_velocity', 'imu_quaternion',
              'imu_gyro', 'head_rgb', 'head_depth'}

    def __init__(self, model, directory, walking_prior, tool_prior, preparation_targets):
        self.m = model
        self.walking = GrootWalkingActor(model, directory, walking_prior)
        self.tool_prior = deepcopy(tool_prior)
        if 'initial_robot_qpos' in self.tool_prior:
            raise ValueError('A station handoff must derive its robot pose from sensors')
        self.pickup_type = ToolActor
        if 'carry_distance_m' in self.tool_prior:
            from carry_tool_actor import ToolActor as CarryActor
            self.pickup_type = CarryActor
        self.targets = preparation_targets
        self.phase = 'walk'
        self.started = None
        self.preparation = None
        self.localizer = None
        self.registration = None
        self.registered_frames = 0
        self.pickup = None
        self.pickup_started = None
        self.events = []

    def update(self, observation):
        if set(observation) != self.fields:
            raise ValueError('Unexpected continuous-station observation field')
        t = float(observation['time_s'])
        packet = {k: observation[k] for k in self.fields - {'head_rgb', 'head_depth'}}
        packet['depth'] = None
        if self.phase == 'walk':
            torque, command = self.walking.torque(packet)
            if self.walking.navigation_stage == 'arrived':
                self.started = t
                self.preparation = StationPreparation(self.m, self.walking.odometry.d.qpos.copy(), self.targets)
                self.phase = 'prepare'
                self.events.append(dict(time_s=t, kind='station_arrived',
                    estimated_position_m=self.walking.navigation_position.tolist(),
                    source='Leg odometry from encoders/IMU and declared initial map pose'))
        elif self.phase in {'prepare', 'localize'}:
            elapsed = t - self.started
            torque = self.preparation.torque(packet, elapsed)
            command = np.zeros(3)
            if elapsed < 2.:
                walking_torque, _ = self.walking.torque(packet)
                fraction = smooth(elapsed / 2.)
                torque = (1-fraction) * walking_torque + fraction * torque
            if self.phase == 'prepare':
                if self.preparation.stable_since is not None and elapsed-self.preparation.stable_since >= 1.:
                    self.phase = 'localize'
                    self.events.append(dict(time_s=t, kind='station_posture_ready',
                        maximum_target_error_rad=self.preparation.error,
                        maximum_selected_joint_speed_rad_s=self.preparation.speed))
                elif elapsed > 22.:
                    raise RuntimeError('Station preparation did not settle')
            if self.phase == 'localize' and observation['head_depth'] is not None:
                if self.localizer is None:
                    h, w = np.asarray(observation['head_depth']).shape
                    self.localizer = MapLocalization(self.m, self.preparation.d, width=w, height=h, pixel_center=.5)
                coarse = self.localizer.register(observation['head_depth'])
                self.registration = dict(time_s=t, coarse=coarse)
                if coarse['accepted']:
                    self.preparation.shift_estimated_frame(np.asarray(coarse['correction_m']))
                    fine = self.localizer.register(observation['head_depth'],
                        max_depth_difference_m=.004, huber_scale_m=.0002)
                    self.registration['fine'] = fine
                    if fine['accepted']:
                        self.preparation.shift_estimated_frame(np.asarray(fine['correction_m']))
                    accepted = (fine['accepted'] and fine['iterations'][-1]['median_residual_m'] < .001
                                and np.linalg.norm(coarse['correction_m']) < .002)
                    self.registered_frames = self.registered_frames + 1 if accepted else 0
                else:
                    self.registered_frames = 0
                if self.registered_frames >= 3:
                    self.localizer.close()
                    self.localizer = None
                    prior = deepcopy(self.tool_prior)
                    prior['initial_robot_qpos'] = self.preparation.d.qpos.tolist()
                    self.pickup = self.pickup_type(self.m, prior)
                    self.pickup_started = t
                    self.phase = 'pickup'
                    self.events.append(dict(time_s=t, kind='sensor_based_pickup_handoff',
                        consecutive_registered_frames=self.registered_frames,
                        registration=self.registration,
                        robot_pose_source='Own encoders/IMU, leg odometry and native-depth static-map registration'))
            if self.phase == 'localize' and elapsed > 34.:
                raise RuntimeError('Station map registration did not settle')
        else:
            packet = dict(observation, time_s=t-self.pickup_started)
            response = self.pickup.update(packet)
            # Keep event times in the uninterrupted simulation clock.
            pickup_events = [dict(e, time_s=float(e['time_s'])+self.pickup_started) for e in response['events']]
            response.update(events=self.events + pickup_events, mission_phase='pickup',
                            navigation_position_m=self.walking.navigation_position.copy())
            return response
        return dict(torque=torque, commanded_velocity=command, error=None, failure=None,
            complete=False, phase=self.phase, mission_phase=self.phase, events=list(self.events),
            navigation_position_m=self.walking.navigation_position.copy(),
            navigation_stage=self.walking.navigation_stage,
            preparation_error_rad=None if self.preparation is None else self.preparation.error,
            preparation_speed_rad_s=None if self.preparation is None else self.preparation.speed,
            static_map_registration=self.registration)

    def close(self):
        if self.localizer is not None:
            self.localizer.close()
        if self.pickup is not None and self.pickup.map_localizer is not None:
            self.pickup.map_localizer.close()

    def error_response(self, error):
        # A nested carrying failure must not replace the already executed
        # pickup/transport history with only the three navigation events.
        # Keep the same continuous clock used by successful responses.
        history = list(self.events)
        if self.pickup is not None:
            history += [dict(e, time_s=float(e['time_s'])+self.pickup_started)
                        for e in self.pickup.events]
        return dict(torque=np.zeros(self.m.nu), error=type(error).__name__+': '+str(error),
                    events=history, phase=self.phase)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model', required=True)
    p.add_argument('--policy', default='/model/policy')
    a = p.parse_args()
    policy = Path(a.policy)
    read = lambda name: json.loads((policy / name).read_text())
    actor = StationPickupActor(mujoco.MjModel.from_xml_path(a.model), policy,
        read('walking_prior.json'), read('tool_prior.json'), read('preparation_targets.json'))
    try:
        while True:
            try:
                observation = pickle.load(sys.stdin.buffer)
            except EOFError:
                break
            try:
                response = actor.update(observation)
            except Exception as error:
                response = actor.error_response(error)
            pickle.dump(response, sys.stdout.buffer, protocol=5)
            sys.stdout.buffer.flush()
            if response['error']:
                break
    finally:
        actor.close()


if __name__ == '__main__':
    main()
