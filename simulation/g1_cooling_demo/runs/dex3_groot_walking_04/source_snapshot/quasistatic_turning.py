"""Alternating foot placements for an in-place turn on a declared level floor.

The inherited estimator consumes encoders and IMU. No plant pose, contact ID
or evaluated support state is available here. Only motor torques are returned.
"""
import numpy as np
from scipy.spatial.transform import Rotation

from quasistatic_walking import QuasistaticWalker


def yaw_rotation(angle):
    return Rotation.from_rotvec([0., 0., float(angle)]).as_matrix()


class QuasistaticTurner(QuasistaticWalker):
    def __init__(self, model, data, initial_xy, relative_yaw, maximum_step_yaw=np.deg2rad(10.)):
        super().__init__(model, data, initial_xy, initial_xy)
        self.relative_yaw = float(relative_yaw)
        self.maximum_step_yaw = float(maximum_step_yaw)
        if (not np.isfinite([self.relative_yaw, self.maximum_step_yaw]).all()
                or not 0. < abs(self.relative_yaw) <= np.pi
                or not 0. < self.maximum_step_yaw <= np.deg2rad(15.)):
            raise ValueError('Invalid in-place turning request')
        self.turn_initialized = False

    def before_control(self, t):
        b = self.balance
        if not self.turn_initialized:
            forward = self.d.body('pelvis').xmat.reshape(3, 3)[:, 0]
            self.initial_heading = float(np.arctan2(forward[1], forward[0]))
            self.target_heading = self.initial_heading+self.relative_yaw
            self.cycle_heading = self.initial_heading
            self.foot_headings = np.full(2, self.initial_heading)
            self.initial_foot_rotations = np.array(b.foot_rotations)
            self.turn_center = np.mean(b.foot_positions, axis=0)
            self.turn_offsets = np.array(b.foot_positions)-self.turn_center
            self.turn_initialized = True
            self.events.append(dict(state='quasistatic_turn_requested', time_s=t,
                                    initial_heading_rad=self.initial_heading,
                                    relative_yaw_rad=self.relative_yaw,
                                    maximum_step_yaw_rad=self.maximum_step_yaw,
                                    center_from_proprioception_m=self.turn_center.tolist()))
        if self.phase in {'swing', 'land'}:
            u = self.blend((t-self.phase_started)/3.) if self.phase=='swing' else 1.
            heading = self.swing_heading_from+u*(self.cycle_heading-self.swing_heading_from)
            self.foot_headings[self.swing] = heading
            b.foot_rotations[self.swing] = yaw_rotation(heading-self.initial_heading)@self.initial_foot_rotations[self.swing]
        # The torso follows the midpoint of the two commanded sole headings,
        # keeping the hip-yaw excursion bounded during each support exchange.
        b.pelvis_rotation = yaw_rotation(float(np.mean(self.foot_headings)))

    def begin_step(self, t):
        b = self.balance
        feet = np.array(b.foot_positions)
        if self.steps % 2 == 0:
            remaining = self.target_heading-self.cycle_heading
            if abs(remaining)<1e-8 and self.steps>=2:
                self.shift_from = b.com_target.copy()
                self.shift_to = self.shift_from.copy()
                self.shift_to[:2] = self.turn_center[:2]
                self.enter('recenter', t)
                return
            self.cycle_heading += float(np.clip(remaining, -self.maximum_step_yaw, self.maximum_step_yaw))
            rotation = yaw_rotation(self.cycle_heading-self.initial_heading)
            self.cycle_targets = self.turn_center+(rotation@self.turn_offsets.T).T
            if np.max(np.linalg.norm(self.cycle_targets[:,:2]-feet[:,:2], axis=1))>self.step_length:
                raise RuntimeError('Turning placement exceeds the declared step-length bound')
        self.shift_from = b.com_target.copy()
        self.shift_to = self.shift_from.copy()
        self.shift_to[:2] = feet[1-self.swing,:2]
        self.swing_from = feet[self.swing].copy()
        self.swing_to = self.cycle_targets[self.swing].copy()
        self.swing_heading_from = float(self.foot_headings[self.swing])
        self.events.append(dict(state='quasistatic_turn_foot_target', time_s=t,
                                foot=['left','right'][self.swing], position_m=self.swing_to.tolist(),
                                relative_heading_rad=self.cycle_heading-self.initial_heading))
        self.enter('shift', t)

    def landing_orientation_ready(self):
        actual = self.d.site_xmat[self.estimate.soles[self.swing]].reshape(3, 3)
        desired = self.balance.foot_rotations[self.swing]
        return np.linalg.norm(Rotation.from_matrix(desired@actual.T).as_rotvec()) < .02
