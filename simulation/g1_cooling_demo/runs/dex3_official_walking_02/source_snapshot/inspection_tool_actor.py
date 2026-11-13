"""Sensor-driven held-tool inspection and return to the pickup location.

The path is recomputed from encoders/IMU, the observed pickup map and unposed
source geometry. A nominal rigid grasp is a collision-planning hypothesis only.
Native RGB-D is checked at the inspection pose; tool truth is never available.
"""
import argparse
import json
import pickle
from pathlib import Path
import sys

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

from carry_tool_actor import CarryClearance
from held_tool_observation import HeldToolObservation
from visual_tool_actor import ToolActor as VisualPickup


class ToolActor(VisualPickup):
    inspection_phases = frozenset({'inspect_move', 'inspect_hold', 'inspect_return'})
    loaded_phases = VisualPickup.loaded_phases | inspection_phases

    def __init__(self, model, prior):
        super().__init__(model, prior)
        config = prior['tool_inspection']
        self.inspection_raise = float(config['raise_m'])
        self.inspection_roll = float(config['wrist_rotation_rad'])
        self.inspection_duration = float(config['motion_duration_s'])
        self.inspection_hold = float(config['observation_duration_s'])
        if not (0 < self.inspection_raise <= .08 and abs(self.inspection_roll) <= .6
                and self.inspection_duration >= 4. and self.inspection_hold >= 2.):
            raise ValueError('Inspection request outside the screened motion envelope')
        self.inspection_done = False
        self.inspection_guard = None
        self.inspection_plan = None
        self.inspection_clock = 0.
        self.inspection_reports = []
        self.inspection_clearance = None
        self.inspection_dwell = None
        self.inspection_next_guard = 0.
        self.held_detector = None
        self.inspection_started = False
        self.required_inspection_detections = int(config['minimum_detected_frames'])

    @staticmethod
    def blend(u):
        u = float(np.clip(u, 0., 1.))
        return u**3 * (10. + u * (-15. + 6.*u))

    def plan_inspection(self):
        self.inspection_guard = guard = CarryClearance(self)
        self.held_detector = HeldToolObservation(self.mesh, self.planner.source)
        initial = self.d.qpos.copy()
        self.inspection_origin = self.wrist_position.copy()
        self.inspection_rotation = self.wrist_rotation.copy()
        self.inspection_center = self.center_offset.copy()
        self.inspection_posture = self.initial[self.arm_indices].copy()
        start = self.inspection_origin + self.inspection_rotation @ self.inspection_center
        start += [0., 0., self.lift_height]
        q, rows, path = initial.copy(), [], []
        for u in np.linspace(0., 1., 61):
            rotation = self.inspection_rotation @ Rotation.from_rotvec([0., 0., u*self.inspection_roll]).as_matrix()
            position = start + [0., 0., u*self.inspection_raise]
            guard.d.qpos[:] = q
            joints, pe, re = guard.ik.solve(guard.d, position, rotation, q[guard.ik.qa])
            q[guard.ik.qa] = joints
            clearance = guard.check(q)
            rows.append(dict(fraction=float(u), position_error_m=pe, rotation_error_rad=re,
                             clearance=clearance))
            if pe > .001 or re > .025 or not clearance['clear']:
                return dict(planned=False, reason='inspection_path', samples=rows)
            path.append(joints.tolist())
        return dict(planned=True, joint_path=path, samples=rows,
                    source='Own-robot state, observed surfaces and source grasp geometry',
                    rigid_grasp_hypothesis=True, physical_execution=False)

    def change(self, phase, t):
        if phase == 'lower' and self.phase == 'hold' and not self.inspection_done:
            self.inspection_plan = self.plan_inspection()
            self.events.append(dict(time_s=t, kind='inspection_plan', plan=self.inspection_plan))
            if not self.inspection_plan['planned']:
                self.inspection_done = True
                self.abort('No collision-screened held-tool inspection path', t)
                return
            self.inspection_clock = 0.
            self.inspection_started = True
            phase = 'inspect_move'
        self.inspection_dwell = None
        super().change(phase, t)

    def before_target(self, t, dt):
        if self.phase not in self.inspection_phases:
            return
        elapsed = t - self.phase_started
        current = self.d.site('right_wrist_reference')
        target = self.wrist_position + self.wrist_rotation @ self.center_offset + [0., 0., self.lift_height]
        pe = float(np.linalg.norm(current.xpos - target))
        re = float(np.linalg.norm(Rotation.from_matrix(current.xmat.reshape(3, 3) @ self.wrist_rotation.T).as_rotvec()))
        if t >= self.inspection_next_guard:
            self.inspection_clearance = self.inspection_guard.check(self.d.qpos)
            self.inspection_next_guard = t + .05
            if not self.inspection_clearance['clear']:
                self.failure = 'Observed inspection geometry violates clearance'
                self.change('finished', t)
                return
        if self.phase == 'inspect_hold':
            u = 1.
            if elapsed >= self.inspection_hold:
                if sum(r['component_found'] for r in self.inspection_reports) < self.required_inspection_detections:
                    self.failure = 'Insufficient observed held-tool surfaces before return'
                self.inspection_clock = 0.
                self.change('inspect_return', t)
        else:
            if pe < .004 and re < .025:
                self.inspection_clock = min(self.inspection_duration, self.inspection_clock + dt)
            fraction = self.blend(self.inspection_clock / self.inspection_duration)
            u = 1. - fraction if self.phase == 'inspect_return' else fraction
            if self.inspection_clock >= self.inspection_duration and pe < .003 and re < .02:
                if self.inspection_dwell is None:
                    self.inspection_dwell = t
                if t - self.inspection_dwell >= .3:
                    if self.phase == 'inspect_move':
                        self.change('inspect_hold', t)
                    else:
                        self.inspection_done = True
                        self.wrist_position = self.inspection_origin.copy()
                        self.wrist_rotation = self.inspection_rotation.copy()
                        self.balance.palm_rotations = {'right': self.wrist_rotation}
                        self.initial[self.arm_indices] = self.inspection_posture
                        super().change('lower', t)
                        return
            else:
                self.inspection_dwell = None
            if elapsed > self.inspection_duration + 10.:
                self.failure = 'Inspection arm did not settle before timeout'
                self.change('finished', t)
                return
        path = np.asarray(self.inspection_plan['joint_path'])
        point = u * (len(path)-1)
        i = min(int(point), len(path)-2)
        self.initial[self.arm_indices] = path[i] + (point-i)*(path[i+1]-path[i])
        self.wrist_rotation = self.inspection_rotation @ Rotation.from_rotvec([0., 0., u*self.inspection_roll]).as_matrix()
        origin_target = self.inspection_origin + self.inspection_rotation @ self.inspection_center
        self.wrist_position = origin_target + [0., 0., u*self.inspection_raise] - self.wrist_rotation @ self.inspection_center
        self.balance.palm_rotations = {'right': self.wrist_rotation}

    def inspect_image(self, obs):
        D, df = self.camera('head_depth')
        wrist = np.eye(4)
        wrist[:3, :3] = self.d.site('right_wrist_reference').xmat.reshape(3, 3)
        wrist[:3, 3] = self.d.site('right_wrist_reference').xpos
        expected = wrist @ np.linalg.inv(np.asarray(self.geometry['source_tool_from_wrist']))
        body_poses = {}
        for name in self.planner.source:
            body = self.d.body(name); T = np.eye(4)
            T[:3,:3] = body.xmat.reshape(3,3); T[:3,3] = body.xpos
            body_poses[name] = T
        proposal, component, _ = self.held_detector.detect(obs['head_depth'], D, df, expected, body_poses)
        # Detect from pixels first. The grasp hypothesis bounds the search,
        # but it is never returned as an observed tool pose.
        report = dict(time_s=float(obs['time_s']), component_found=proposal['candidate_found'],
                      component_points=len(component), proposal=proposal,
                      predicted_grasp_is_not_an_observation=True)
        self.inspection_reports.append(report)
        self.events.append(dict(time_s=float(obs['time_s']), kind='held_tool_observation', report=report))

    def hand_load_feedforward(self):
        result = super().hand_load_feedforward()
        if self.inspection_started and self.phase in self.loaded_phases:
            # Turning the loaded wrist changes disturbances on the four
            # non-closing joints. Compensate only their own motor residuals;
            # retain the original force gates and source torque limits.
            for k,a in enumerate(self.hand):
                if a not in self.drivers:
                    bound = .5*np.max(abs(self.m.actuator_ctrlrange[a]))
                    result[k] = np.clip(self.filtered[a], -bound, bound)
        return result

    def balance_torque(self, target, posture, motion):
        if self.phase in self.inspection_phases and self.previous_balance_time is not None:
            period=self.last_time + .001-self.previous_balance_time
            if not .0099<=period<=.0101:
                raise RuntimeError('Unexpected inspection balance reference period')
            motion=dict(target_velocities={'right':(target-self.previous_wrist_target)/period},
                palm_angular_velocities={'right':Rotation.from_matrix(
                    self.wrist_rotation@self.previous_wrist_rotation.T).as_rotvec()/period})
        return super().balance_torque(target, posture, motion)

    def update(self, obs):
        response = super().update(obs)
        if self.phase == 'inspect_hold' and obs['head_rgb'] is not None:
            self.inspect_image(obs)
        response.update(inspection_completed=self.inspection_done,
                        inspection_frames=len(self.inspection_reports),
                        inspection_detections=sum(r['component_found'] for r in self.inspection_reports),
                        inspection_clearance=self.inspection_clearance)
        return response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--prior', default='/model/policy/tool_prior.json')
    args = parser.parse_args()
    actor = ToolActor(mujoco.MjModel.from_xml_path(args.model), json.loads(Path(args.prior).read_text()))
    while True:
        try:
            obs = pickle.load(sys.stdin.buffer)
        except EOFError:
            break
        try:
            response = actor.update(obs)
        except Exception as error:
            response = dict(torque=np.zeros(actor.m.nu), error=str(error))
        pickle.dump(response, sys.stdout.buffer, protocol=5)
        sys.stdout.buffer.flush()
        if response['error']:
            break


if __name__ == '__main__':
    main()
