"""Sensor-only full-G1 arm/finger coordination from an authored pregrasp.

This development actor has no visual localization or approach. It uses robot
encoders, IMU and idealized native pad signals; object outcomes require a
separate physical evaluator. Motor-load estimates are not hardware calibrated.
"""
import argparse
import json
import pickle
import sys

import mujoco
import numpy as np

from balance import Balance
from observations import StateEstimate


class ToolActor:
    fields = {'time_s', 'joint_position', 'joint_velocity', 'imu_quaternion', 'imu_gyro', 'right_touch_n'}

    def __init__(self, model, prior):
        self.m = model; self.d = mujoco.MjData(model)
        self.close_timeout = float(prior.get('close_timeout_s', 6.))
        if not 1. <= self.close_timeout <= 30.: raise ValueError('Invalid bounded grasp timeout')
        self.d.qpos[:] = prior['initial_robot_qpos']; mujoco.mj_forward(model, self.d)
        self.estimate = StateEstimate(model, self.d)
        self.balance = Balance(model, self.d); self.balance.rotate_foot_constraints = True
        self.balance.solver_backend = 'clarabel'
        self.names = [model.joint(j).name for j in model.actuator_trnid[:, 0]]
        self.qa = model.jnt_qposadr[model.actuator_trnid[:, 0]]
        self.va = model.jnt_dofadr[model.actuator_trnid[:, 0]]
        self.hand = np.array([i for i, n in enumerate(self.names) if n.startswith('right_')
                              and any(f in n for f in ['index', 'thumb', 'middle', 'ring', 'little'])])
        assert len(self.hand) == 6
        self.drivers = np.array([self.names.index(n) for n in ['right_index_1_joint', 'right_thumb_2_joint']])
        self.initial = self.d.qpos[self.qa].copy(); self.command = self.initial.copy()
        self.lower = np.maximum(self.initial-.02, model.jnt_range[model.actuator_trnid[:, 0], 0])
        self.upper = np.minimum(self.initial+.08, model.jnt_range[model.actuator_trnid[:, 0], 1])
        self.coupling = np.zeros((model.nv, model.nu)); self.coupling[self.va, np.arange(model.nu)] = 1
        for i in range(model.neq):
            a, b = model.eq_obj1id[i], model.eq_obj2id[i]
            self.coupling[model.jnt_dofadr[a]] = model.eq_data[i, 1]*self.coupling[model.jnt_dofadr[b]]
        self.wrist_position = self.d.site('right_wrist_reference').xpos.copy()
        self.wrist_rotation = self.d.site('right_wrist_reference').xmat.reshape(3, 3).copy()
        self.balance.palm_rotations = {'right': self.wrist_rotation}
        self.pad_bodies = [model.body(n).id for n in ['right_index_force_sensor_3', 'right_thumb_force_sensor_4']]
        self.pad_reference = self.pad_midpoint(); self.center_offset = np.zeros(3)
        self.filtered = np.zeros(model.nu); self.previous_velocity = None
        self.previous_torque = np.zeros(model.nu); self.body_torque = np.zeros(model.nu)
        self.flags = np.zeros(2, dtype=bool); self.flag_release_since = [None, None]
        self.hold_since = None; self.load_since = None; self.lost_since = None
        self.phase = 'settle'; self.phase_started = 0.; self.hold_entered = False
        self.lift_height = 0.; self.abort_height = 0.; self.failure = None
        self.release_command = None; self.next_balance = 0.; self.last_time = None
        self.events = []

    def pad_midpoint(self):
        wrist = self.d.site('right_wrist_reference')
        return wrist.xmat.reshape(3, 3).T@(np.mean(self.d.xpos[self.pad_bodies], axis=0)-wrist.xpos)

    def change(self, phase, t):
        self.phase = phase; self.phase_started = t
        self.events.append(dict(time_s=t, phase=phase))

    def abort(self, reason, t):
        if self.failure is not None: return
        self.failure = reason; self.abort_height = self.lift_height
        self.change('abort_lower', t)

    def update(self, obs):
        if set(obs) != self.fields: raise ValueError('Unexpected actor observation fields')
        t = float(obs['time_s']); dt = .001 if self.last_time is None else t-self.last_time
        if not .0009999 <= dt <= .0010001: raise ValueError('Unexpected controller period')
        if not all(np.isfinite(np.asarray(v)).all() for v in obs.values()):
            raise ValueError('Nonfinite sensor packet')
        packet = {k: v for k, v in obs.items() if k != 'right_touch_n'}; packet['depth'] = None
        self.estimate.update(packet)
        m, d = self.m, self.d
        gravity = self.coupling.T@(d.qfrc_bias-d.qfrc_passive)
        if self.previous_velocity is not None:
            mass = np.empty((m.nv, m.nv)); mujoco.mj_fullM(m, d, mass)
            acceleration = (d.qvel-self.previous_velocity)/dt
            predicted = self.coupling.T@(mass@acceleration)+gravity
            self.filtered += (1-np.exp(-dt/.03))*(self.previous_torque-predicted-self.filtered)
        self.previous_velocity = d.qvel.copy()
        direction = d.xpos[self.pad_bodies[1]]-d.xpos[self.pad_bodies[0]]
        direction /= max(np.linalg.norm(direction), 1e-12)
        lever = []
        for b, a, sign in zip(self.pad_bodies, self.drivers, [1., -1.]):
            jp, jr = np.zeros((3, m.nv)), np.zeros((3, m.nv))
            mujoco.mj_jacBody(m, d, jp, jr, b)
            lever.append(float(sign*direction@(jp@self.coupling[:, a])))
        lever = np.asarray(lever)
        if np.any(lever <= .001): raise RuntimeError('Opposing finger motion is no longer available')
        effort = self.filtered[self.drivers]; proxy = effort/lever
        if max(np.asarray(obs['right_touch_n'])) > 4. or max(abs(effort)) > .12:
            self.abort('Observed hand load exceeds the development bound', t)
        if self.phase == 'settle' and t >= 2.:
            self.change('close', t)
        if self.phase == 'close':
            for i in range(2):
                if not self.flags[i] and proxy[i] > .05:
                    self.flags[i] = True; self.flag_release_since[i] = None
                elif self.flags[i] and proxy[i] < .02:
                    if self.flag_release_since[i] is None: self.flag_release_since[i] = t
                    if t-self.flag_release_since[i] >= .05: self.flags[i] = False
                else: self.flag_release_since[i] = None
            if all(self.flags):
                if self.hold_since is None: self.hold_since = t
                if t-self.hold_since >= .05: self.hold_entered = True
            else: self.hold_since = None
            if self.hold_entered and min(proxy) >= .2:
                if self.load_since is None: self.load_since = t
                if t-self.load_since >= .5: self.change('lift', t)
            else: self.load_since = None
            if t-self.phase_started > self.close_timeout: self.abort('No sustained opposing load before grasp timeout', t)
        if self.hold_entered and self.phase in {'close', 'lift', 'hold', 'lower'}:
            if min(effort) < .003:
                if self.lost_since is None: self.lost_since = t
                if t-self.lost_since >= .15: self.abort('Observed loss of opposing finger load', t)
            else: self.lost_since = None
        if self.phase in {'close', 'lift', 'hold', 'lower'}:
            speed = np.clip(.0005/lever, .001, .014)
            for i, a in enumerate(self.drivers):
                target = .6*lever[i] if self.hold_entered else .04*lever[i]
                rate = np.clip([.4, 1.2][i]*(target-effort[i]), -speed[i], speed[i]) if self.hold_entered or self.flags[i] else speed[i]
                self.command[a] = np.clip(self.command[a]+rate*dt, self.lower[a], self.upper[a])
            desired = self.pad_reference-self.pad_midpoint()
            desired *= min(1., .02/max(np.linalg.norm(desired), 1e-12))
            delta = (1-np.exp(-dt/.05))*(desired-self.center_offset)
            delta *= min(1., .006*dt/max(np.linalg.norm(delta), 1e-12))
            self.center_offset += delta
        elapsed = t-self.phase_started
        smooth = lambda x: (lambda u: u*u*(3-2*u))(float(np.clip(x, 0., 1.)))
        if self.phase == 'lift':
            self.lift_height = .03*smooth(elapsed/2.)
            if elapsed >= 2.: self.change('hold', t)
        elif self.phase == 'hold' and elapsed >= 1.:
            self.change('lower', t)
        elif self.phase in {'lower', 'abort_lower'}:
            height = .03 if self.phase == 'lower' else self.abort_height
            self.lift_height = height*(1-smooth(elapsed/2.))
            if elapsed >= 2.:
                self.release_command = self.command.copy(); self.change('release', t)
        elif self.phase == 'release':
            self.command = self.release_command+smooth(elapsed/2.)*(self.initial-self.release_command)
            if elapsed >= 2.: self.change('rest', t)
        elif self.phase == 'rest' and elapsed >= 2.:
            self.change('finished', t)
        wrist_target = self.wrist_position+self.wrist_rotation@self.center_offset+[0., 0., self.lift_height]
        if t+1e-9 >= self.next_balance:
            posture = self.initial.copy(); posture[self.hand] = self.command[self.hand]
            self.body_torque = self.balance.torque(targets={'right': wrist_target}, posture=posture, dt=.01)
            self.next_balance = (round(t*100)+1)/100
        torque = self.body_torque.copy()
        torque[self.hand] = (gravity+3.*(self.command-d.qpos[self.qa])-.08*d.qvel[self.va])[self.hand]
        torque = np.clip(torque, m.actuator_ctrlrange[:, 0], m.actuator_ctrlrange[:, 1])
        self.previous_torque = torque.copy(); self.last_time = t
        return dict(torque=torque, error=None, phase=self.phase, failure=self.failure,
            complete=self.phase == 'finished', requested_joint_position=self.command.copy(),
            motor_load_nm=effort.copy(), force_proxy_n=proxy.copy(), contact_flags=self.flags.copy(),
            hold_phase_entered=self.hold_entered, wrist_target_m=wrist_target.copy(),
            wrist_observed_m=d.site('right_wrist_reference').xpos.copy(),
            encoder_center_offset_m=self.center_offset.copy(), lift_height_m=self.lift_height,
            events=list(self.events))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--model', required=True)
    parser.add_argument('--prior', default='/model/policy/tool_prior.json'); args = parser.parse_args()
    actor = ToolActor(mujoco.MjModel.from_xml_path(args.model), json.loads(open(args.prior).read()))
    while True:
        try: obs = pickle.load(sys.stdin.buffer)
        except EOFError: break
        try: response = actor.update(obs)
        except Exception as error: response = dict(torque=np.zeros(actor.m.nu), error=str(error))
        pickle.dump(response, sys.stdout.buffer, protocol=5); sys.stdout.buffer.flush()
        if response['error']: break


if __name__ == '__main__': main()
