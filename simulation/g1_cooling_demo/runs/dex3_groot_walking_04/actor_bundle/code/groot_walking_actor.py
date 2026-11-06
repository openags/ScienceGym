"""Sensor-only adapter for NVIDIA's pinned decoupled G1 body policies.

Observation/history/action processing is adapted from G1GearWbcPolicy,
Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES, Apache-2.0.
See locomotion_groot_policy/LICENSE and its separate model-weight license.

The 15 lower-body references come from the unmodified official ONNX weights.
An authored upper-body/empty-hand posture uses the same public robot model
and sampled inertia bounds as the current Dex3 control work. Plant dynamics,
source limits and object poses are never changed or available to this actor.
"""
import argparse
from collections import deque
import json
from pathlib import Path
import pickle
import sys

import mujoco
import numpy as np
import onnxruntime as ort
from scipy.spatial.transform import Rotation
import yaml

from observations import robot_joints
from walking_actor import SDK_JOINTS


def single_observation(config, q, dq, quat, omega, command, previous_action):
    defaults = np.zeros(29, dtype=np.float32)
    defaults[:15] = np.asarray(config['default_angles'], dtype=np.float32)
    w, x, y, z = np.asarray(quat)
    gravity = np.array([-2 * (x * z - w * y), -2 * (y * z + w * x),
                        -(w * w - x * x - y * y + z * z)])
    row = np.zeros(86, dtype=np.float32)
    row[:3] = command * np.asarray(config['cmd_scale'], dtype=np.float32)
    row[3] = config['height_cmd']
    row[4:7] = config['rpy_cmd']
    row[7:10] = np.asarray(omega) * config['ang_vel_scale']
    row[10:13] = gravity
    row[13:42] = (q - defaults) * config['dof_pos_scale']
    row[42:71] = dq * config['dof_vel_scale']
    row[71:86] = previous_action
    return row


class GrootBodyPolicy:
    def __init__(self, directory):
        directory = Path(directory)
        self.cfg = yaml.safe_load((directory / 'policy.yaml').read_text())
        assert self.cfg['num_actions'] == 15 and self.cfg['num_obs'] == 516
        assert self.cfg['obs_history_len'] == 6
        self.history = deque(maxlen=6)
        self.action = np.zeros(15, dtype=np.float32)
        self.command = np.asarray(self.cfg['cmd_init'], dtype=np.float32)
        options = ort.SessionOptions()
        options.intra_op_num_threads = options.inter_op_num_threads = 1
        self.sessions = {name: ort.InferenceSession(str(directory / (name + '.onnx')),
            sess_options=options, providers=['CPUExecutionProvider']) for name in ['balance', 'walk']}
        for session in self.sessions.values():
            assert session.get_inputs()[0].shape[-1] == 516
            assert session.get_outputs()[0].shape[-1] == 15
        self.evaluations = 0
        self.last_mode = 'balance'

    def infer(self, q, dq, quaternion, angular_velocity, command):
        # Preserve upstream set_observation -> get_action ordering: the
        # observation contains the preceding command, then mode selection
        # uses the new command. Missing history is padded with zero rows.
        row = single_observation(self.cfg, q, dq, quaternion, angular_velocity, self.command, self.action)
        self.history.append(row)
        while len(self.history) < 6:
            self.history.appendleft(np.zeros_like(row))
        vector = np.concatenate(self.history)[None]
        self.command = np.asarray(command, dtype=np.float32).copy()
        self.last_mode = 'balance' if np.linalg.norm(self.command) < .05 else 'walk'
        session = self.sessions[self.last_mode]
        self.action = session.run(None, {session.get_inputs()[0].name: vector})[0].reshape(15)
        if not np.isfinite(self.action).all():
            raise RuntimeError('Nonfinite official policy output')
        self.evaluations += 1
        return self.action * self.cfg['action_scale'] + np.asarray(self.cfg['default_angles'], dtype=np.float32)


class GrootWalkingActor:
    def __init__(self, model, directory, prior):
        self.m, self.d = model, mujoco.MjData(model)
        self.policy = GrootBodyPolicy(directory)
        self.prior = prior
        self.dt = prior['control_period_s']
        assert self.dt == .001 and model.nu == 43 and np.all(model.actuator_gear[:, 0] == 1.)
        joints = robot_joints(model)
        names = [model.joint(j).name for j in joints]
        self.qa = model.jnt_qposadr[joints]
        self.va = model.jnt_dofadr[joints]
        self.body_encoders = np.array([names.index(name) for name in SDK_JOINTS])
        self.body_joints = np.array([model.joint(name).id for name in SDK_JOINTS])
        self.body_motors = np.array([np.flatnonzero(model.actuator_trnid[:, 0] == j).item() for j in self.body_joints])
        self.posture_motors = np.array([i for i in range(model.nu) if i not in self.body_motors[:15]])
        posture_joints = model.actuator_trnid[self.posture_motors, 0]
        self.posture_encoders = np.array([names.index(model.joint(j).name) for j in posture_joints])
        self.posture_va = model.jnt_dofadr[posture_joints]
        self.selector = np.eye(model.nv)[:, self.posture_va]
        body_targets = dict(zip(SDK_JOINTS, prior['target_body_pose_rad']))
        target_map = {**body_targets, **prior['hand_pose']}
        self.posture_target = np.array([target_map[model.joint(j).name] for j in posture_joints])
        self.posture_stiffness = np.array([3. if '_hand_' in model.joint(j).name else 30. for j in posture_joints])
        self.kp = np.asarray(self.policy.cfg['kps'], dtype=np.float32)
        self.kd = np.asarray(self.policy.cfg['kds'], dtype=np.float32)
        self.lower_target = np.asarray(self.policy.cfg['default_angles'], dtype=np.float32)
        self.next_policy = 0.
        self.heading_reference = None

    def torque(self, obs):
        if set(obs) != {'time_s', 'joint_position', 'joint_velocity', 'imu_quaternion', 'imu_gyro', 'depth'}:
            raise ValueError('Non-sensor field in actor input')
        t = float(obs['time_s'])
        q, dq = np.asarray(obs['joint_position']), np.asarray(obs['joint_velocity'])
        quaternion = np.asarray(obs['imu_quaternion'])
        forward = Rotation.from_quat(quaternion[[1, 2, 3, 0]]).apply([1., 0., 0.])
        yaw = np.arctan2(forward[1], forward[0])
        if self.heading_reference is None:
            self.heading_reference = yaw
        command = np.zeros(3, dtype=np.float32)
        if 2 <= t < self.prior['stop_at_s']:
            command[0] = self.prior['speed_m_s']
            error = np.arctan2(np.sin(self.heading_reference - yaw), np.cos(self.heading_reference - yaw))
            command[2] = np.clip(1.2 * error, -.2, .2)
        if t + 1e-8 >= self.next_policy:
            self.lower_target = self.policy.infer(q[self.body_encoders], dq[self.body_encoders],
                quaternion, np.asarray(obs['imu_gyro']), command)
            limits = self.m.jnt_range[self.body_joints[:15]]
            self.lower_target = np.clip(self.lower_target, limits[:, 0] + .01, limits[:, 1] - .01)
            self.next_policy += .02
        m, d = self.m, self.d
        d.qpos[self.qa], d.qvel[self.va] = q, dq
        d.qpos[3:7], d.qvel[3:6] = quaternion, obs['imu_gyro']
        mujoco.mj_forward(m, d)
        mass = np.zeros((m.nv, m.nv))
        mujoco.mj_fullM(m, d, mass)
        effective = np.linalg.inv(self.selector.T @ np.linalg.solve(mass, self.selector))
        inertia, axes = np.linalg.eigh(effective)
        if np.min(inertia) <= 0.:
            raise RuntimeError('Nonpositive posture inertia')
        root = (axes * np.sqrt(inertia)) @ axes.T
        inverse_root = (axes / np.sqrt(inertia)) @ axes.T
        frequencies, modes = np.linalg.eigh(inverse_root @ np.diag(self.posture_stiffness) @ inverse_root)
        frequencies = np.minimum(np.maximum(frequencies, 0.), .25 / self.dt**2)
        stiffness = root @ (modes * frequencies) @ modes.T @ root
        damping = root @ (modes * np.minimum(2 * np.sqrt(frequencies), .4 / self.dt)) @ modes.T @ root
        torque = np.zeros(m.nu)
        torque[self.body_motors[:15]] = ((self.lower_target - q[self.body_encoders[:15]]) * self.kp
                                        - dq[self.body_encoders[:15]] * self.kd)
        torque[self.posture_motors] = (d.qfrc_bias[self.posture_va]
            + stiffness @ (self.posture_target - q[self.posture_encoders])
            - damping @ dq[self.posture_encoders])
        return np.clip(torque, m.actuator_ctrlrange[:, 0], m.actuator_ctrlrange[:, 1]), command


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model', required=True)
    p.add_argument('--policy', default='/model/policy')
    p.add_argument('--prior', default='/model/policy/walking_prior.json')
    a = p.parse_args()
    actor = GrootWalkingActor(mujoco.MjModel.from_xml_path(a.model), a.policy,
                              json.loads(Path(a.prior).read_text()))
    while True:
        try:
            packet = pickle.load(sys.stdin.buffer)
        except EOFError:
            break
        try:
            torque, command = actor.torque(packet)
            response = dict(torque=torque, commanded_velocity=command, error=None,
                            policy_evaluations=actor.policy.evaluations, policy_mode=actor.policy.last_mode)
        except Exception as error:
            response = dict(torque=np.zeros(actor.m.nu), error=type(error).__name__ + ': ' + str(error))
        pickle.dump(response, sys.stdout.buffer, protocol=5)
        sys.stdout.buffer.flush()


if __name__ == '__main__':
    main()
