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
from balance import Balance
from observations import StateEstimate

SDK_JOINTS = ([s+'_'+j+'_joint' for s in ['left','right']
               for j in ['hip_pitch','hip_roll','hip_yaw','knee','ankle_pitch','ankle_roll']]
              + ['waist_'+j+'_joint' for j in ['yaw','roll','pitch']]
              + [s+'_'+j+'_joint' for s in ['left','right']
                 for j in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow',
                           'wrist_roll','wrist_pitch','wrist_yaw']])


class WalkingActor:
    def __init__(self, model, directory, speed=.2, gains='training', hold_heading=False, stop_at=10., park=False):
        self.m = model
        self.cfg = yaml.safe_load((Path(directory)/'deploy.yaml').read_text())
        self.order = np.asarray(self.cfg['joint_ids_map'], dtype=int)
        self.default = np.asarray(self.cfg['default_joint_pos'], dtype=np.float32)
        self.kp = np.asarray(self.cfg['stiffness'])
        self.kd = np.asarray(self.cfg['damping'])
        self.effort = np.array([88,139,88,139,25,25]*2+[88,25,25]+[25,25,25,25,25,5,5]*2)
        if gains == 'training':
            # UNITREE_G1_29DOF_CFG in the pinned upstream training model.
            self.kp[13:15] = 40.
            self.kd[15:] = 1.
        elif gains != 'deploy': raise ValueError('Unknown gain source')
        self.action = np.zeros(29, dtype=np.float32)
        self.target = self.default.copy()
        self.history = {}
        self.next_policy = 0.
        self.speed = speed
        self.stop_at = stop_at
        self.hold_heading = hold_heading
        self.heading_reference = None
        self.park = park
        self.parking_time = None
        self.balance = None
        self.parking_data = mujoco.MjData(model)
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

    def torque(self, obs, command_override=None):
        if set(obs) != {'time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro','depth'}:
            raise ValueError('Non-sensor field in actor input')
        t = obs['time_s']
        if self.balance is not None:
            if t+1e-8 >= self.balance_next:
                self.estimate.update(obs)
                self.parking_torque = self.balance.torque(dt=.01)
                self.balance_next += .01
            return self.parking_torque, np.zeros(3)
        q = np.asarray(obs['joint_position'])[self.encoder_index]
        dq = np.asarray(obs['joint_velocity'])[self.encoder_index]
        # This first compatibility trial uses a declared time-based speed
        # command, not goal-directed navigation or simulator root feedback.
        command = np.array([self.speed if 2 <= t < self.stop_at else 0., 0., 0.], dtype=np.float32)
        quat = np.asarray(obs['imu_quaternion'])
        rotation = Rotation.from_quat(quat[[1,2,3,0]])
        forward = rotation.apply([1.,0.,0.])
        yaw = np.arctan2(forward[1],forward[0])
        if self.heading_reference is None: self.heading_reference = yaw
        if self.park and t >= self.stop_at+getattr(self,'minimum_stop_dwell_s',.6) and getattr(self,'estimated_base_speed',0.)<getattr(self,'parking_speed_limit',float('inf')):
            d = self.parking_data; m = self.m
            hinges = [j for j in range(m.njnt) if m.jnt_type[j]==mujoco.mjtJoint.mjJNT_HINGE]
            d.qpos[m.jnt_qposadr[hinges]] = obs['joint_position']
            d.qvel[m.jnt_dofadr[hinges]] = obs['joint_velocity']
            d.qpos[3:7] = quat;d.qvel[3:6] = obs['imu_gyro'];d.qpos[:3]=0;d.qvel[:3]=0
            mujoco.mj_kinematics(m,d)
            feet = [d.site(s+'_sole') for s in ['left','right']]
            level = abs(feet[0].xpos[2]-feet[1].xpos[2]) < .008
            flat = all(f.xmat.reshape(3,3)[2,2]>.99 for f in feet)
            if level and flat and np.linalg.norm(obs['imu_gyro'])<.4:
                d.qpos[2] = -min(f.xpos[2] for f in feet);mujoco.mj_forward(m,d)
                self.estimate = StateEstimate(m,d); self.estimate.update(obs)
                self.balance = Balance(m,d)
                self.balance.pelvis_rotation = Rotation.from_euler('z',yaw).as_matrix()
                self.balance.rotate_foot_constraints = True
                self.parking_time = t; self.balance_next = t+.01
                self.parking_torque = self.balance.torque(dt=.01)
                return self.parking_torque, np.zeros(3)
        if self.hold_heading and 2 <= t < self.stop_at:
            error = np.arctan2(np.sin(self.heading_reference-yaw),np.cos(self.heading_reference-yaw))
            command[2] = np.clip(1.2*error,-.2,.2)
        if command_override is not None:
            command = np.asarray(command_override,dtype=np.float32)
        if t+1e-8 >= self.next_policy:
            gravity = rotation.inv().apply([0.,0.,-1.])
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
        body_torque = (sdk_target-q)*self.kp-dq*self.kd
        torque[self.motor_index] = np.clip(body_torque,-self.effort,self.effort)
        torque[self.hand_motors] = (-1.*np.asarray(obs['joint_position'])[self.hand_encoders]
                                   -.05*np.asarray(obs['joint_velocity'])[self.hand_encoders])
        return np.clip(torque, self.m.actuator_ctrlrange[:,0], self.m.actuator_ctrlrange[:,1]), command


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--model',required=True)
    parser.add_argument('--policy',default='/model/policy'); parser.add_argument('--speed',type=float,default=.2)
    parser.add_argument('--gains',choices=['training','deploy'],default='training')
    parser.add_argument('--hold-heading',action='store_true')
    parser.add_argument('--stop-at',type=float,default=10.)
    parser.add_argument('--park',action='store_true')
    args = parser.parse_args()
    model = mujoco.MjModel.from_xml_path(args.model)
    actor = WalkingActor(model, args.policy, args.speed, args.gains, args.hold_heading, args.stop_at, args.park)
    while True:
        try: packet = pickle.load(sys.stdin.buffer)
        except EOFError: break
        try:
            torque, command = actor.torque(packet)
            response = dict(torque=torque, error=None, commanded_velocity=command,
                            policy_evaluations=actor.policy_evaluations,parking_time_s=actor.parking_time,
                            control_mode='stationary_balance' if actor.balance else 'official_velocity_policy')
        except Exception as error:
            response = dict(torque=np.zeros(model.nu), error=str(error))
        pickle.dump(response, sys.stdout.buffer, protocol=5); sys.stdout.buffer.flush()


if __name__ == '__main__': main()
