"""Turn then translate using one estimator, balance task and physics clock.

The transition uses encoder/IMU kinematics only. Keeping the existing balance
task preserves sole anchors, the crouched COM height and the new body heading.
No physical state is assigned at the transition.
"""
import numpy as np

from quasistatic_turning import QuasistaticTurner, yaw_rotation
from quasistatic_walking import QuasistaticWalker


class QuasistaticTurnWalk(QuasistaticTurner):
    def __init__(self, model, data, initial_xy, relative_yaw, forward_distance):
        super().__init__(model, data, initial_xy, relative_yaw)
        self.forward_distance = float(forward_distance)
        if not np.isfinite(self.forward_distance) or not .12 <= self.forward_distance <= 1.:
            raise ValueError('Forward distance must be between 0.12 and 1 metre')
        self.translating = False
        self.steps_at_transition = None

    def before_control(self, t):
        if not self.translating:
            super().before_control(t)
            if self.phase != 'parked' or t-self.parking_time < 2.:
                # A turn is an intermediate phase, never task completion.
                self.finished = False
                return
            forward = self.d.body('pelvis').xmat.reshape(3, 3)[:, 0]
            heading = float(np.arctan2(forward[1], forward[0]))
            error = float(np.arctan2(np.sin(heading-self.target_heading),
                                     np.cos(heading-self.target_heading)))
            if abs(error) >= .02 or np.linalg.norm(self.d.qvel[:6]) >= .03:
                self.finished = False
                if t-self.parking_time > 8.:
                    raise RuntimeError('Turn did not settle before forward walking')
                return
            feet = np.array(self.balance.foot_positions)
            center = feet[:, :2].mean(axis=0)
            direction = yaw_rotation(self.target_heading)[:2, 0]
            self.goal = center+self.forward_distance*direction
            self.foot_offsets = feet[:, :2]-center
            self.initial_separation = feet[0, :2]-feet[1, :2]
            self.steps_at_transition = self.steps
            self.translating = True
            self.finished = False
            self.parking_time = None
            self.events.append(dict(state='continuous_turn_walk_handoff', time_s=t,
                                    completed_turn_steps=self.steps,
                                    estimated_position_m=self.d.qpos[:3].tolist(),
                                    observed_heading_rad=heading,
                                    target_heading_rad=self.target_heading,
                                    goal_sole_center_m=self.goal.tolist(),
                                    forward_distance_m=self.forward_distance))
            QuasistaticWalker.begin_step(self, t)
        self.balance.pelvis_rotation = yaw_rotation(self.target_heading)

    def begin_step(self, t):
        if self.translating:
            QuasistaticWalker.begin_step(self, t)
        else:
            super().begin_step(t)
