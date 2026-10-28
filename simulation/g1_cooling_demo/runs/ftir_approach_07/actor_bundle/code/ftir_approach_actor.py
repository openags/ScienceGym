"""One sensor-isolated actor for an aisle approach and observed FTIR window task.

Walking, settling, posture preparation, map registration and manipulation share
one uninterrupted plant clock. The handoff passes a robot sensor estimate;
neither the physical robot nor the equipment is repositioned by this actor.
"""
import argparse
import pickle
import sys

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

from walking_actor import WalkingActor, SDK_JOINTS
from odometry import LegOdometry
from observations import StateEstimate
from map_localization import MapLocalization
from ftir_slider_posture import initialize_slider
from ftir_slider_observed_actor import ObservedSliderActor
from ftir_hand import rest_hand_pose, walking_arm_pose


class FtirApproachActor:
    fields = ObservedSliderActor.fields

    def __init__(self, model, policy, initial_xy, station_xy, prior, shape, walking_controller='official_policy'):
        self.m = model
        self.d = mujoco.MjData(model)
        self.goal = np.asarray(station_xy, dtype=float)
        self.odom = LegOdometry(model, self.d, initial_xy)
        self.walking_controller = walking_controller
        self.walking_event_cursor = 0
        if walking_controller == 'quasistatic':
            from quasistatic_walking import QuasistaticWalker
            # Keep the motor controller's estimate separate from the map
            # registration estimate, as in the official-policy adapter.
            self.walker = QuasistaticWalker(model,mujoco.MjData(model),initial_xy,station_xy)
            steps = 2*int(np.ceil(np.linalg.norm(self.goal-np.asarray(initial_xy))/.12))
            self.approach_timeout = 25.+16.*steps
        elif walking_controller == 'official_policy':
            self.walker = WalkingActor(model, policy, speed=.4, gains='training', park=True,
                                       stop_at=float('inf'), hand_pose=rest_hand_pose(), arm_pose=walking_arm_pose())
            self.walker.minimum_stop_dwell_s = .8
            self.walker.parking_speed_limit = .03
            self.approach_timeout = 32.
        else:
            raise ValueError('Unknown approach walking controller')
        self.prior, self.shape = prior, shape
        self.stage = 'approach'
        self.events = []
        self.station = None
        self.registration = None
        self.registration_updates = []
        self.velocity_ema = np.zeros(3)
        self.stop_time = None
        self.prepare_time = None
        self.last_torque = np.zeros(model.nu)
        self.joint_names = [model.joint(j).name for j in model.actuator_trnid[:,0]]
        self.upper_actuators = [i for i,n in enumerate(self.joint_names) if n not in SDK_JOINTS[:12]]
        self.preparation = None
        self.command = np.zeros(3)
        self.command_time = None

    def begin_registration(self, packet):
        mujoco.mj_forward(self.m, self.d)
        self.estimate = StateEstimate(self.m, self.d)
        self.estimate.update(packet)
        self.registration = MapLocalization(self.m, self.d, width=640, height=360,
                                            pixel_center=.5, translation_axes=(0, 1))
        self.registration_started = float(packet['time_s'])
        self.stage = 'register_workstation'
        self.events.append(dict(state='workstation_registration_started', time_s=self.registration_started))

    def update(self, obs):
        if set(obs) != self.fields:
            raise ValueError('Non-sensor field in FTIR actor input')
        packet = {k:v for k,v in obs.items() if k not in {'rgb', 'right_touch_n'}}
        t = float(obs['time_s'])
        if self.station is not None:
            response = self.station.update(obs)
            response['events'] = self.events+response['events']
            response['mission_stage'] = 'station_operation'
            return response
        if self.stage == 'approach':
            position = self.odom.update(packet)
            self.velocity_ema = .98*self.velocity_ema+.02*self.d.qvel[:3]
            orientation = Rotation.from_quat(np.asarray(obs['imu_quaternion'])[[1,2,3,0]])
            forward = orientation.apply([1., 0., 0.])
            yaw = float(np.arctan2(forward[1], forward[0]))
            error = self.goal-position[:2]
            speed_estimate = max(0., float(self.velocity_ema[0]))
            braking = max(.14, .35*speed_estimate+speed_estimate**2/(2*.5))
            if self.walking_controller == 'official_policy' and t >= 2. and self.stop_time is None and error[0] < braking and abs(error[1]) < .10 and abs(yaw) < .10:
                self.stop_time = t
                self.walker.stop_at = t
                self.events.append(dict(state='stop_at_ftir_approach', time_s=t,
                                        estimated_position_m=position.tolist(), braking_distance_m=float(braking)))
            command = np.zeros(3)
            if self.walking_controller == 'official_policy' and t >= 2. and self.stop_time is None:
                speed = float(np.clip(.25+.5*(.25-self.velocity_ema[0]), .18, .3))
                velocity = np.array([speed if error[0] > .12 else 0., np.clip(1.8*error[1], -.15, .15), 0.])
                command[:2] = orientation.inv().apply(velocity)[:2]
                command[2] = np.clip(-1.2*yaw, -.2, .2)
            dt = 0. if self.command_time is None else max(0., t-self.command_time)
            self.command += np.clip(command-self.command, -np.array([.5,.4,.4])*dt,
                                    np.array([.5,.4,.4])*dt)
            self.command_time = t
            if self.walker.parking_time is not None and t-self.walker.parking_time >= 2.:
                if self.prepare_time is None:
                    self.prepare_time = t
                    self.prepare_posture = self.walker.balance.posture.copy()
                    self.station_posture = initialize_slider(self.m).qpos[self.walker.balance.qa].copy()
                    # Walking leaves a different foot stance from the authored
                    # station setup. Preserve its leg posture as well as the
                    # balance controller's measured foot constraints.
                    for i, name in enumerate(self.joint_names):
                        if name in SDK_JOINTS[:12]:
                            self.station_posture[i] = self.prepare_posture[i]
                    weights = np.ones(self.m.nu)
                    for i in self.upper_actuators:
                        weights[i] = 4. if self.joint_names[i].startswith('waist_') else 3.
                    self.walker.parking_posture_weights = weights
                    self.events.append(dict(state='prepare_ftir_posture', time_s=t))
                u = float(np.clip((t-self.prepare_time)/5., 0., 1.))
                self.walker.balance.posture = self.prepare_posture+u*u*(3-2*u)*(self.station_posture-self.prepare_posture)
            self.walker.estimated_base_speed = float(np.linalg.norm(self.velocity_ema[:2]))
            self.last_torque, _ = self.walker.torque(packet, command_override=self.command)
            if self.walking_controller == 'quasistatic':
                self.events.extend(self.walker.events[self.walking_event_cursor:])
                self.walking_event_cursor = len(self.walker.events)
            if self.prepare_time is not None and t-self.prepare_time >= 7.:
                joints = self.d.qpos[self.walker.balance.qa]
                yaw_q = float(self.d.joint('waist_yaw_joint').qpos[0])
                yaw_v = float(self.d.joint('waist_yaw_joint').qvel[0])
                upper_error = float(np.max(abs(joints[self.upper_actuators]-self.station_posture[self.upper_actuators])))
                speed = float(np.linalg.norm(self.velocity_ema[:2]))
                self.preparation = dict(maximum_upper_joint_error_rad=upper_error,
                                        waist_yaw_error_rad=abs(yaw_q+.5), waist_yaw_speed_rad_s=abs(yaw_v),
                                        estimated_horizontal_speed_m_s=speed)
                if (upper_error < .05 and abs(yaw_q+.5) < .02 and abs(yaw_v) < .03
                        and speed < .03 and np.linalg.norm(obs['imu_gyro']) < .1):
                    self.begin_registration(packet)
            if t > self.approach_timeout and self.stage == 'approach':
                raise RuntimeError('FTIR approach or posture handoff timed out')
        if self.stage == 'register_workstation':
            self.estimate.update(packet)
            self.last_torque, _ = self.walker.torque(packet, command_override=np.zeros(3))
            if obs['depth'] is not None:
                before = self.d.qpos[:3].copy()
                fitted = self.registration.register(obs['depth'])
                eigen = (fitted.get('iterations') or [{}])[-1].get('eigenvalues', [])
                conditioned = len(eigen) == 2 and eigen[0] >= .01*eigen[-1]
                accepted = fitted['accepted'] and conditioned
                if accepted:
                    correction = np.asarray(fitted['correction_m'])
                    self.estimate.anchors += correction
                    self.registration_updates.append(dict(time_s=t, position_m=self.d.qpos[:3].tolist(),
                                                          correction_m=correction.tolist()))
                else:
                    self.d.qpos[:3] = before
                    mujoco.mj_forward(self.m, self.d)
                    self.registration_updates = []
                self.events.append(dict(state='workstation_registration_observation', time_s=t,
                                        accepted=bool(accepted), well_conditioned=bool(conditioned), fit=fitted))
            if len(self.registration_updates) >= 5 and t-self.registration_started >= .5:
                recent = self.registration_updates[-5:]
                positions = np.array([r['position_m'] for r in recent])
                xy = self.d.qpos[:2]
                if np.max(np.std(positions, axis=0)) < .001:
                    if np.linalg.norm(xy-self.goal) > .10:
                        raise RuntimeError('Observed parking position outside the FTIR handoff envelope')
                    self.registration.close()
                    self.registration = None
                    mujoco.mj_forward(self.m, self.d)
                    self.events.append(dict(state='continuous_station_handoff', time_s=t,
                                            estimated_root_position_m=self.d.qpos[:3].tolist(),
                                            registration_observations=recent,
                                            source='encoders_IMU_and_native_depth_registered_to_public_architecture'))
                    self.station = ObservedSliderActor(self.m, xy, self.prior, self.shape,
                                                       initial_state=self.d, started_at=t)
                    response = self.station.update(obs)
                    response['events'] = self.events+response['events']
                    response['mission_stage'] = 'station_operation'
                    return response
            if t-self.registration_started > 5.:
                raise RuntimeError('FTIR map registration did not produce a stable, observable pose')
        return dict(torque=self.last_torque, error=None, policy_state=self.stage, mission_stage=self.stage,
                    policy_complete=False, policy_failure=None, events=self.events,
                    accepted_key_observations=0, observation=None, commanded_pose=None,
                    preparation=self.preparation,
                    walking_controller=self.walking_controller,
                    walking_phase=getattr(self.walker,'phase',None),
                    commanded_velocity=self.command.tolist(),
                    estimated_root_position_m=self.d.qpos[:3].tolist())

    def close(self):
        if self.registration is not None:
            self.registration.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model', required=True)
    p.add_argument('--policy', default='/model/policy')
    p.add_argument('--initial-xy', nargs=2, type=float, default=[4.95, -5.20])
    p.add_argument('--station-xy', nargs=2, type=float, default=[5.95, -5.20])
    p.add_argument('--walking-controller', choices=['official_policy','quasistatic'], default='official_policy')
    p.add_argument('--prior', default='/model/policy/slider_push_prior.json')
    p.add_argument('--shape', default='/model/known_objects/nicolet_passive_dynamics.glb')
    args = p.parse_args()
    model = mujoco.MjModel.from_xml_path(args.model)
    actor = FtirApproachActor(model, args.policy, args.initial_xy, args.station_xy, args.prior, args.shape, args.walking_controller)
    try:
        while True:
            try:
                packet = pickle.load(sys.stdin.buffer)
            except EOFError:
                break
            try:
                response = actor.update(packet)
            except Exception as error:
                response = dict(torque=np.zeros(model.nu), error=str(error))
            pickle.dump(response, sys.stdout.buffer, protocol=5)
            sys.stdout.buffer.flush()
            if response['error']:
                break
    finally:
        actor.close()


if __name__ == '__main__':
    main()
