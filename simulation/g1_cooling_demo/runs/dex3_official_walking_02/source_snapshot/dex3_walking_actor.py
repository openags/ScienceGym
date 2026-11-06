"""Official Unitree body policy with an empty Dex3 hand posture controller.

Only encoder and IMU packets enter the actor. Hand inertia and gravity are
computed from the public robot model, without object/contact observations.
This adapter does not implement carrying, navigation, or task execution.
"""
import argparse
import json
from pathlib import Path
import pickle
import sys

import mujoco
import numpy as np

from observations import robot_joints
from walking_actor import WalkingActor


class Dex3WalkingActor(WalkingActor):
    def __init__(self, model, directory, prior):
        super().__init__(model, directory, speed=prior['speed_m_s'], gains='training',
                         hold_heading=True, stop_at=prior['stop_at_s'],
                         hand_pose=prior['hand_pose'],
                         minimum_shoulder_abduction=prior.get('minimum_shoulder_abduction_rad'))
        self.dt = float(prior['control_period_s'])
        assert self.dt == .001 and model.nu == 43 and len(self.hand_motors) == 14
        self.own = mujoco.MjData(model)
        joints = np.asarray(robot_joints(model))
        self.qa, self.va = model.jnt_qposadr[joints], model.jnt_dofadr[joints]
        self.hand_va = model.jnt_dofadr[model.actuator_trnid[self.hand_motors, 0]]
        self.selector = np.eye(model.nv)[:, self.hand_va]

    def torque(self, obs, command_override=None):
        # Body policy preprocessing, history, 50 Hz inference, gains and
        # command clipping are inherited from the pinned upstream adapter.
        torque, command = super().torque(obs, command_override)
        m, d = self.m, self.own
        d.qpos[self.qa] = obs['joint_position']
        d.qvel[self.va] = obs['joint_velocity']
        d.qpos[3:7] = obs['imu_quaternion']
        d.qvel[3:6] = obs['imu_gyro']
        mujoco.mj_forward(m, d)
        mass = np.zeros((m.nv, m.nv))
        mujoco.mj_fullM(m, d, mass)
        inverse_hand_mass = self.selector.T @ np.linalg.solve(mass, self.selector)
        inertia, axes = np.linalg.eigh(np.linalg.inv(inverse_hand_mass))
        if np.min(inertia) <= 0.:
            raise RuntimeError('Nonpositive hand inertia')
        # Same sampled stability bounds used by the current Dex3 grasp actor.
        kp = np.minimum(3., .25 * inertia / self.dt**2)
        kd = np.minimum(2 * np.sqrt(kp * inertia), .4 * inertia / self.dt)
        error = axes.T @ (self.hand_target - np.asarray(obs['joint_position'])[self.hand_encoders])
        speed = axes.T @ np.asarray(obs['joint_velocity'])[self.hand_encoders]
        torque[self.hand_motors] = d.qfrc_bias[self.hand_va] + axes @ (kp * error - kd * speed)
        return np.clip(torque, m.actuator_ctrlrange[:, 0], m.actuator_ctrlrange[:, 1]), command


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model', required=True)
    p.add_argument('--policy', default='/model/policy')
    p.add_argument('--prior', default='/model/policy/walking_prior.json')
    a = p.parse_args()
    actor = Dex3WalkingActor(mujoco.MjModel.from_xml_path(a.model), a.policy,
                            json.loads(Path(a.prior).read_text()))
    while True:
        try:
            packet = pickle.load(sys.stdin.buffer)
        except EOFError:
            break
        try:
            torque, command = actor.torque(packet)
            response = dict(torque=torque, commanded_velocity=command, error=None,
                            policy_evaluations=actor.policy_evaluations)
        except Exception as error:
            response = dict(torque=np.zeros(actor.m.nu), error=type(error).__name__ + ': ' + str(error))
        pickle.dump(response, sys.stdout.buffer, protocol=5)
        sys.stdout.buffer.flush()


if __name__ == '__main__':
    main()
