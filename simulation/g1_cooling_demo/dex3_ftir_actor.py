"""Sensor-only G1/Dex3 FTIR key approach, press, withdrawal and return.

The component starts at an explicitly authored stationary pointing posture.
Only native images, encoders and IMU enter the actor. Native key displacement,
contact forces and whole-run success are independent evaluator measurements.
"""
import argparse
import json
import pickle
import sys

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

from balance import Balance
from dex3_ftir_hand import Dex3PointingHand
from dex3_ftir_planning import ObservedKeyApproach
from ftir_hand import ArmIK
from ftir_vision import KeyRowObservation
from observations import StateEstimate


def smooth(u):
    u = float(np.clip(u, 0., 1.))
    return u*u*u*(10.+u*(-15.+6.*u))


class Dex3FTIRActor:
    fields = {'time_s', 'joint_position', 'joint_velocity', 'imu_quaternion',
              'imu_gyro', 'depth', 'rgb'}

    def __init__(self, model, setup, label='BACKGROUND'):
        self.m, self.d = model, mujoco.MjData(model)
        self.d.qpos[:7] = setup['root_qpos']
        for name, value in setup['joints'].items():
            self.d.joint(name).qpos[0] = value
        mujoco.mj_forward(model, self.d)
        self.estimate = StateEstimate(model, self.d)
        self.balance = Balance(model, self.d)
        self.balance.rotate_foot_constraints = True
        self.balance.solver_backend = 'clarabel'
        self.balance.pelvis_rotation = self.d.body('pelvis').xmat.reshape(3, 3).copy()
        self.com_start = self.d.subtree_com[model.body('pelvis').id].copy()
        self.com_goal = self.balance.com_target.copy()
        com_mode = setup.get('com_target_mode', 'sole_center')
        if com_mode not in {'sole_center', 'initial'}:
            raise ValueError('Unknown stationary COM target mode')
        if com_mode == 'initial':
            # A stationary reaching task need not translate the body to the
            # midpoint of the feet. Preserve the own-model starting COM;
            # the unchanged contact-wrench constraints must support it.
            self.com_goal = self.com_start.copy()
        self.press_force = float(setup.get('press_force_n', .45))
        if not np.isfinite(self.press_force) or not 0. <= self.press_force <= .45:
            raise ValueError('Press feedforward must be between zero and 0.45 N')
        self.press_depth = float(setup.get('press_depth_m', .001))
        if not np.isfinite(self.press_depth) or not .0005 <= self.press_depth <= .002:
            raise ValueError('Commanded press depth must be between 0.5 and 2 mm')
        lowering = float(setup.get('com_lowering_m', 0.))
        leg_weight = float(setup.get('leg_posture_weight', 1.))
        if not 0. <= lowering <= .04 or not .1 <= leg_weight <= 1.:
            raise ValueError('Station balance settings outside declared development bounds')
        self.com_goal[2] -= lowering
        self.vision = KeyRowObservation(model, self.d)
        self.hand, self.ik = Dex3PointingHand(model), ArmIK(model)
        joints = model.actuator_trnid[:, 0]
        names = [model.joint(j).name for j in joints]
        self.posture_weights = np.ones(model.nu)
        for i, name in enumerate(names):
            if any('_'+part+'_' in name for part in ['hip', 'knee', 'ankle']):
                self.posture_weights[i] = leg_weight
        if setup.get('body_joint_damper', False):
            self.balance.joint_limit_indices = [i for i, n in enumerate(names) if '_hand_' not in n]
            self.balance.joint_limit_margin_rad = .01
            self.balance.joint_limit_frequency_rad_s = 12.
        self.qa, self.va = model.jnt_qposadr[joints], model.jnt_dofadr[joints]
        self.hands = np.array([i for i, name in enumerate(names) if '_hand_' in name])
        self.selector = np.eye(model.nv)[:, self.va[self.hands]]
        self.arm = np.array([names.index(model.joint(j).name) for j in self.ik.joints])
        self.original_posture = self.d.qpos[self.qa].copy()
        self.label = label
        self.observations, self.events = [], []
        self.next_balance = 0.
        self.body_torque = np.zeros(model.nu)
        self.plan, self.stages = None, None
        self.phase, self.phase_started = 0, 0.
        self.finished, self.failure = False, None
        self.reached_since = None
        self.last_tip = None
        self.contact_depth_samples = 0
        self.last_detection = None
        self.latest_ik = None
        self.tracking = None

    def make_plan(self, depth, t):
        recent = self.observations[-8:]
        positions = np.array([o['buttons'][self.label] for o in recent])
        if np.max(np.std(positions, axis=0)) > .002:
            raise RuntimeError('Observed key row is not stationary')
        self.planner = ObservedKeyApproach(self.m, self.d, depth)
        self.plan = self.planner.build(recent[-1], self.label)
        if not self.plan['planned']:
            raise RuntimeError('No sensor-derived collision-screened FTIR approach')
        self.surface = np.asarray(self.plan['surface_m'])
        self.normal = np.asarray(self.plan['normal'])
        self.contact_wrist = np.asarray(self.plan['contact_wrist_m'])
        self.rotation = np.asarray(self.plan['wrist_rotation'])
        self.material = np.asarray(self.plan['wrist_local_contact_m'])
        path = np.asarray(self.plan['arm_path_rad'])
        stages = []
        for i, (a, b) in enumerate(zip(path[:-1], path[1:])):
            duration = max(1., 1.875*float(np.max(abs(b-a)))/.45)
            stages.append(dict(name='approach_'+str(i), kind='joint', duration=duration, start=a, goal=b))
        for name, duration, a, b in [('press', 3., .03, -self.press_depth),
                                    ('hold', .65, -self.press_depth, -self.press_depth),
                                    ('withdraw', 2., -self.press_depth, .03)]:
            stages.append(dict(name=name, kind='cartesian', duration=duration,
                               start=self.contact_wrist+a*self.normal, goal=self.contact_wrist+b*self.normal))
        for i, (a, b) in enumerate(zip(path[:0:-1], path[-2::-1])):
            duration = max(1., 1.875*float(np.max(abs(b-a)))/.45)
            stages.append(dict(name='return_'+str(i), kind='joint', duration=duration, start=a, goal=b))
        stages.append(dict(name='rest', kind='joint', duration=2., start=path[0], goal=path[0]))
        self.stages, self.phase_started = stages, t
        self.kinematic = mujoco.MjData(self.m)
        self.kinematic.qpos[:] = self.d.qpos
        self.events.append(dict(time_s=t, kind='sensor_target_selected', label=self.label,
            source='native_head_rgb_depth_and_own_robot_state', plan=self.plan,
            commanded_press_depth_m=self.press_depth,
            nominal_motion_duration_s=sum(s['duration'] for s in stages)))

    def update(self, packet):
        if set(packet) != self.fields:
            raise ValueError('Unexpected input to the isolated FTIR actor')
        t = float(packet['time_s'])
        self.estimate.update({k:v for k, v in packet.items() if k != 'rgb'})
        m, d = self.m, self.d
        posture = self.original_posture.copy()
        if t+1e-8 >= self.next_balance:
            if packet['rgb'] is not None and packet['depth'] is not None:
                detection = self.vision.observe(packet['rgb'], packet['depth'])
                self.last_detection = detection
                if detection and detection['accepted']:
                    self.observations.append(detection)
                if self.plan is None and t >= 2. and len(self.observations) >= 8:
                    self.make_plan(packet['depth'], t)
            if self.plan is None and t > 5.:
                raise RuntimeError('Four FTIR controls were not observed reliably')
            self.balance.com_target = self.com_start+smooth(t/2.)*(self.com_goal-self.com_start)
            targets, forces = None, None
            if self.stages is not None and not self.finished:
                stage = self.stages[self.phase]
                elapsed = t-self.phase_started
                u = float(np.clip(elapsed/stage['duration'], 0., 1.))
                fraction = smooth(u)
                name = stage['name']
                if stage['kind'] == 'joint':
                    arm = stage['start']+fraction*(stage['goal']-stage['start'])
                    self.kinematic.qpos[self.ik.qa] = arm
                    mujoco.mj_kinematics(m, self.kinematic)
                    wrist = self.kinematic.site('right_wrist_reference')
                    target, rotation = wrist.xpos.copy(), wrist.xmat.reshape(3, 3).copy()
                    self.latest_ik = arm
                else:
                    target = stage['start']+fraction*(stage['goal']-stage['start'])
                    rotation = self.rotation
                    arm, pe, re = self.ik.solve(d, target, rotation, self.latest_ik)
                    if pe > .003 or re > .035:
                        raise RuntimeError('Observed key target became unreachable in '+name)
                    self.latest_ik = arm
                posture[self.arm] = arm
                self.balance.palm_rotations = {'right':rotation}
                targets = {'right':target}
                if name in ['press', 'hold']:
                    force = self.press_force*(float(np.clip((u-.65)/.35, 0., 1.)) if name == 'press' else 1.)
                    forces = {'right':-self.normal*force}
                    point = self.hand.observed_contact_point(d, self.material)
                    delta = point-self.surface
                    gap = float(delta@self.normal)
                    lateral = float(np.linalg.norm(delta-gap*self.normal))
                    self.last_tip = dict(normal_gap_m=gap, lateral_error_m=lateral)
                    if name == 'hold' and gap < -.0001 and lateral < .003:
                        self.contact_depth_samples += 1
                error = float(np.linalg.norm(target-d.site('right_wrist_reference').xpos))
                rerror = float(np.linalg.norm(Rotation.from_matrix(
                    rotation@d.site('right_wrist_reference').xmat.reshape(3, 3).T).as_rotvec()))
                self.tracking = dict(wrist_position_error_m=error, wrist_rotation_error_rad=rerror,
                    wrist_target_m=target.tolist(), wrist_estimated_m=d.site('right_wrist_reference').xpos.tolist())
                ready = name in ['hold', 'rest'] or (error < .005 and rerror < .035)
                if u >= 1. and ready:
                    if self.reached_since is None:
                        self.reached_since = t
                    if t-self.reached_since >= .15:
                        if name == 'hold' and self.contact_depth_samples < 10:
                            self.failure = 'Insufficient proprioceptive press-depth evidence'
                        self.events.append(dict(time_s=t, kind='stage_completed', stage=name,
                            wrist_position_error_m=error, wrist_rotation_error_rad=rerror))
                        self.phase += 1
                        self.phase_started, self.reached_since = t, None
                        if self.phase == len(self.stages):
                            self.finished = True
                elif elapsed > stage['duration']+5.:
                    raise RuntimeError('Robot pose did not reach '+name)
            self.body_torque = self.balance.torque(targets=targets, forces=forces, posture=posture,
                                                   posture_weights=self.posture_weights, dt=.01)
            self.next_balance = (round(t*100)+1)/100
        mass = np.zeros((m.nv, m.nv))
        mujoco.mj_fullM(m, d, mass)
        inertia = np.linalg.inv(self.selector.T@np.linalg.solve(mass, self.selector))
        values, axes = np.linalg.eigh(inertia)
        if np.min(values) <= 0.:
            raise RuntimeError('Nonpositive Dex3 hand inertia')
        kp = np.minimum(3., .25*values/.001**2)
        kd = np.minimum(2*np.sqrt(kp*values), .4*values/.001)
        error = axes.T@(self.original_posture-d.qpos[self.qa])[self.hands]
        speed = axes.T@d.qvel[self.va[self.hands]]
        torque = self.body_torque.copy()
        torque[self.hands] = (d.qfrc_bias-d.qfrc_passive)[self.va[self.hands]]+axes@(kp*error-kd*speed)
        torque = np.clip(torque, m.actuator_ctrlrange[:, 0], m.actuator_ctrlrange[:, 1])
        return dict(torque=torque, error=None, events=self.events,
            policy_state='finished' if self.finished else 'observe' if self.stages is None else self.stages[self.phase]['name'],
            policy_complete=self.finished, policy_failure=self.failure,
            accepted_key_observations=len(self.observations), estimated_tip=self.last_tip,
            contact_depth_samples=self.contact_depth_samples, tracking=self.tracking)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model', required=True)
    p.add_argument('--setup', required=True)
    a = p.parse_args()
    model = mujoco.MjModel.from_xml_path(a.model)
    actor = Dex3FTIRActor(model, json.load(open(a.setup)))
    while True:
        try:
            packet = pickle.load(sys.stdin.buffer)
        except EOFError:
            break
        try:
            response = actor.update(packet)
        except Exception as error:
            response = dict(torque=np.zeros(model.nu), error=str(error), events=actor.events)
        pickle.dump(response, sys.stdout.buffer, protocol=5)
        sys.stdout.buffer.flush()
        if response['error']:
            break


if __name__ == '__main__':
    main()
