"""Sensor-only adapter for the pinned official Unitree 29DoF velocity policy.

Observation ordering/history and action scaling follow the upstream sources in
locomotion_policy/reference (Unitree Robotics, Apache-2.0). This adapter adds
Inspire finger hold and motor-limit clipping, without plant-state access.
"""
import argparse
from collections import deque
from pathlib import Path
import pickle
import sys

import mujoco
import numpy as np
import onnxruntime as ort
from scipy.spatial.transform import Rotation
import yaml

SDK_JOINTS = ([s+'_'+j+'_joint' for s in ['left','right']
               for j in ['hip_pitch','hip_roll','hip_yaw','knee','ankle_pitch','ankle_roll']]
              + ['waist_'+j+'_joint' for j in ['yaw','roll','pitch']]
              + [s+'_'+j+'_joint' for s in ['left','right']
                 for j in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow',
                           'wrist_roll','wrist_pitch','wrist_yaw']])


class WalkingActor:
    def __init__(self, model, directory, speed=.2):
        self.m = model
        self.cfg = yaml.safe_load((Path(directory)/'deploy.yaml').read_text())
        self.order = np.asarray(self.cfg['joint_ids_map'], dtype=int)
        self.default = np.asarray(self.cfg['default_joint_pos'], dtype=np.float32)
        self.kp = np.asarray(self.cfg['stiffness'])
        self.kd = np.asarray(self.cfg['damping'])
        self.action = np.zeros(29, dtype=np.float32)
        self.target = self.default.copy()
        self.history = {}
        self.next_policy = 0.
        self.speed = speed
        hinges = [model.joint(j).name for j in range(model.njnt)
                  if model.jnt_type[j] == mujoco.mjtJoint.mjJNT_HINGE]
        self.encoder_index = np.array([hinges.index(name) for name in SDK_JOINTS])
        self.motor_index = np.array([next(i for i in range(model.nu)
            if model.actuator_trnid[i,0] == model.joint(name).id) for name in SDK_JOINTS])
        self.hand_motors = np.array([i for i in range(model.nu) if i not in self.motor_index])
        self.hand_encoders = np.array([hinges.index(model.joint(model.actuator_trnid[i,0]).name)
                                       for i in self.hand_motors])
        options = ort.SessionOptions(); options.intra_op_num_threads = 1; options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(str(Path(directory)/'policy.onnx'),
                                           sess_options=options, providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        self.policy_evaluations = 0

    def torque(self, obs):
        if set(obs) != {'time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro','depth'}:
            raise ValueError('Non-sensor field in actor input')
        t = obs['time_s']
        q = np.asarray(obs['joint_position'])[self.encoder_index]
        dq = np.asarray(obs['joint_velocity'])[self.encoder_index]
        # This first compatibility trial uses a declared time-based speed
        # command, not goal-directed navigation or simulator root feedback.
        command = np.array([self.speed if 2 <= t < 10 else 0., 0., 0.], dtype=np.float32)
        if t+1e-8 >= self.next_policy:
            quat = np.asarray(obs['imu_quaternion'])
            gravity = Rotation.from_quat(quat[[1,2,3,0]]).inv().apply([0.,0.,-1.])
            terms = dict(base_ang_vel=obs['imu_gyro'], projected_gravity=gravity,
                         velocity_commands=command, joint_pos_rel=q[self.order]-self.default,
                         joint_vel_rel=dq[self.order], last_action=self.action)
            inputs = []
            for name, cfg in self.cfg['observations'].items():
                value = np.asarray(terms[name], dtype=np.float32)
                if cfg['clip'] is not None: value = np.clip(value, *cfg['clip'])
                value = value*np.asarray(cfg['scale'], dtype=np.float32)
                count = cfg['history_length']
                if name not in self.history: self.history[name] = deque([value.copy() for _ in range(count)], maxlen=count)
                self.history[name].append(value.copy())
                inputs.extend(self.history[name])
            vector = np.concatenate(inputs).astype(np.float32)[None]
            self.action = self.session.run(None, {self.input_name:vector})[0].reshape(29)
            if not np.isfinite(self.action).all(): raise ValueError('Non-finite policy output')
            cfg = self.cfg['actions']['JointPositionAction']
            self.target = self.action*np.asarray(cfg['scale'])+np.asarray(cfg['offset'])
            self.next_policy += self.cfg['step_dt']
            self.policy_evaluations += 1
        sdk_target = np.empty(29); sdk_target[self.order] = self.target
        torque = np.zeros(self.m.nu)
        torque[self.motor_index] = (sdk_target-q)*self.kp-dq*self.kd
        torque[self.hand_motors] = (-1.*np.asarray(obs['joint_position'])[self.hand_encoders]
                                   -.05*np.asarray(obs['joint_velocity'])[self.hand_encoders])
        return np.clip(torque, self.m.actuator_ctrlrange[:,0], self.m.actuator_ctrlrange[:,1]), command


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--model',required=True)
    parser.add_argument('--policy',default='/model/policy'); parser.add_argument('--speed',type=float,default=.2)
    args = parser.parse_args()
    model = mujoco.MjModel.from_xml_path(args.model)
    actor = WalkingActor(model, args.policy, args.speed)
    while True:
        try: packet = pickle.load(sys.stdin.buffer)
        except EOFError: break
        try:
            torque, command = actor.torque(packet)
            response = dict(torque=torque, error=None, commanded_velocity=command,
                            policy_evaluations=actor.policy_evaluations)
        except Exception as error:
            response = dict(torque=np.zeros(model.nu), error=str(error))
        pickle.dump(response, sys.stdout.buffer, protocol=5); sys.stdout.buffer.flush()


if __name__ == '__main__': main()
