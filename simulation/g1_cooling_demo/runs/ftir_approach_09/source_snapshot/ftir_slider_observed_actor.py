"""Push the window, withdraw, then confirm its position from fresh native RGB-D.

The additional torso turns use bounded motor control and the same robot-state
estimator. No device joint, scene pose or evaluator result enters the actor.
"""
import argparse
import pickle
import sys

import mujoco
import numpy as np

from ftir_slider_actor import SliderActor
from ftir_slider_outcome import SliderRangeObservation


class ObservedSliderActor(SliderActor):
    def __init__(self, model, xy, prior, shape, initial_state=None, started_at=0., outcome_yaw=-.5):
        super().__init__(model, xy, prior, shape, initial_state=initial_state, started_at=started_at)
        self.outcome_yaw = float(outcome_yaw)
        if not np.isfinite(self.outcome_yaw) or not -.65 <= self.outcome_yaw <= -.35:
            raise ValueError('Outcome viewing angle outside the declared torso interval')
        self.visual_yaw_tolerance = .005
        self.visual_posture_weights = np.ones(self.m.nu)
        self.visual_posture_weights[self.actuator_ids['waist_yaw_joint']] = 4.
        self.visual_phase = None
        self.visual_finished = False
        self.outcome_verified = False
        self.outcome_window = []
        self.outcome_accepted_count = 0
        self.last_outcome_sensor_time = None
        self.pending_contact_recovery = None

    def recoverable_contact_loss(self):
        """Only a late, bounded-load push may proceed to outcome inspection.

        This permits observation, never success. The original fault stays
        active until eight fresh RGB-D fits pass and the torso returns safely.
        An overload, failed acquisition or early loss remains terminal.
        """
        context = self.recovery_context or {}
        return (self.failure == 'Tactile contact was lost during push'
                and context.get('code') == 'push_contact_loss'
                and 0. <= context.get('filtered_distal_load_n', float('inf')) < .1
                and .060 <= context.get('commanded_push_displacement_m', -1.) <= .070
                and context.get('contact_loss_duration_s', 0.) > .35)

    def begin_visual_phase(self, name, t):
        self.visual_phase = name
        self.visual_phase_started = t
        self.visual_start_yaw = float(self.d.joint('waist_yaw_joint').qpos[0])
        self.visual_stable_since = None
        self.events.append(dict(state=name+'_started', time_s=t,
                                requested_outcome_yaw_rad=self.outcome_yaw,
                                viewing_yaw_tolerance_rad=self.visual_yaw_tolerance))

    def update(self, obs):
        if set(obs) != self.fields:
            raise ValueError('Non-sensor field in FTIR actor input')
        t = float(obs['time_s'])
        if self.visual_phase is None:
            response = super().update(obs)
            if not response['policy_complete']:
                return response
            if response['policy_failure'] and not self.recoverable_contact_loss():
                return response
            if response['policy_failure']:
                self.pending_contact_recovery = dict(reason=self.failure, context=dict(self.recovery_context))
                self.events.append(dict(state='contact_loss_outcome_inspection_started', time_s=t,
                                        fault=self.pending_contact_recovery,
                                        source='completed_motor_withdrawal_after_native_tactile_guard'))
            self.outcome_vision = SliderRangeObservation(
                self.m, self.d, self.prior_path, self.shape_path, self.grip_observations)
            self.visual_posture = self.d.qpos[self.balance.qa].copy()
            self.begin_visual_phase('turn_to_outcome_view', t)
            response.update(policy_complete=False, policy_state=self.visual_phase,
                            outcome_verified=False, accepted_outcome_observations=0)
            return response

        touch = np.asarray(obs['right_touch_n'], dtype=float)
        if touch.shape != (7,) or not np.isfinite(touch).all() or np.any(touch < 0):
            raise ValueError('Invalid tactile observation')
        detection = None
        outcome = None
        if t+1e-8 >= self.next_control:
            self.estimate.update({k:v for k,v in obs.items() if k not in {'rgb', 'right_touch_n'}})
            posture = self.visual_posture.copy()
            yaw_target = -.2 if self.visual_phase in {'return_from_outcome_view', 'finished'} else self.outcome_yaw
            yaw = float(self.d.joint('waist_yaw_joint').qpos[0])
            velocity = float(self.d.joint('waist_yaw_joint').qvel[0])
            elapsed = t-self.visual_phase_started
            if self.visual_phase in {'turn_to_outcome_view', 'return_from_outcome_view'}:
                u = float(np.clip(elapsed/3., 0., 1.))
                posture[self.actuator_ids['waist_yaw_joint']] = self.visual_start_yaw+(yaw_target-self.visual_start_yaw)*u*u*(3-2*u)
                settled = u >= 1. and abs(yaw-yaw_target) < self.visual_yaw_tolerance and abs(velocity) < .03
                if settled:
                    if self.visual_stable_since is None:
                        self.visual_stable_since = t
                    if t-self.visual_stable_since >= 1.:
                        self.events.append(dict(state=self.visual_phase+'_endpoint', time_s=t,
                                                observed_yaw_rad=yaw, observed_yaw_velocity_rad_s=velocity))
                        if self.visual_phase == 'turn_to_outcome_view':
                            self.begin_visual_phase('observe_window_outcome', t)
                        else:
                            if (self.pending_contact_recovery is not None and self.outcome_verified
                                    and self.failure == self.pending_contact_recovery['reason']):
                                self.events.append(dict(state='contact_loss_recovery_confirmed', time_s=t,
                                                        fault=self.pending_contact_recovery,
                                                        sensor_frames=[dict(time_s=s, observed_position_m=p)
                                                                       for s,p in self.outcome_window],
                                                        source='fresh_native_RGBD_confirmation_and_settled_motor_return'))
                                self.failure = None
                            self.visual_phase = 'finished'
                            self.visual_finished = True
                else:
                    self.visual_stable_since = None
                if elapsed > 8. and not settled:
                    if self.visual_phase == 'return_from_outcome_view':
                        raise RuntimeError('Torso did not settle after outcome observation')
                    self.failure = 'Torso did not settle at the outcome observation posture'
                    self.begin_visual_phase('return_from_outcome_view', t)
            else:
                posture[self.actuator_ids['waist_yaw_joint']] = yaw_target

            if self.visual_phase == 'observe_window_outcome':
                fresh = (obs['rgb'] is not None and obs['depth'] is not None and
                         (self.last_outcome_sensor_time is None or t > self.last_outcome_sensor_time))
                if fresh:
                    self.last_outcome_sensor_time = t
                    pose_ready = abs(yaw-self.outcome_yaw) < self.visual_yaw_tolerance and abs(velocity) < .03
                    if pose_ready:
                        detection = self.vision.observe(obs['rgb'], obs['depth'])
                        if detection and detection['accepted']:
                            self.total_accepted += 1
                        outcome = self.outcome_vision.observe(obs['depth'], detection)
                    else:
                        outcome = dict(accepted=False, reason='viewing_posture_not_settled')
                    outcome['viewing_pose_accepted'] = bool(pose_ready)
                    self.events.append(dict(state='slider_outcome_observation', time_s=t,
                                            key_observation=detection, observation=outcome))
                    if outcome['accepted']:
                        self.outcome_accepted_count += 1
                        self.outcome_window.append((t, outcome['baseline_corrected_position_m']))
                        self.outcome_window = self.outcome_window[-8:]
                    else:
                        self.outcome_window = []
                    if (len(self.outcome_window) == 8 and
                            self.outcome_window[-1][0]-self.outcome_window[0][0] >= .65 and
                            np.std([p for _,p in self.outcome_window]) < .002):
                        self.outcome_verified = True
                        self.events.append(dict(state='slider_outcome_confirmed', time_s=t,
                                                sensor_frames=[dict(time_s=s, observed_position_m=p) for s,p in self.outcome_window],
                                                source='fresh_native_head_RGBD_and_robot_proprioception'))
                        self.begin_visual_phase('return_from_outcome_view', t)
                if self.visual_phase == 'observe_window_outcome' and t-self.visual_phase_started > 12.:
                    self.failure = 'Visual slider completion was not confirmed within the observation interval'
                    self.begin_visual_phase('return_from_outcome_view', t)

            dt = .01 if self.last_time is None else t-self.last_time
            # No fixed world-space wrist target during a torso turn: both
            # withdrawn hands follow their retained joint posture.
            self.last_torque = self.balance.torque(posture=posture, posture_weights=self.visual_posture_weights, dt=dt)
            self.last_time = t
            self.next_control = (round(t*100)+1)/100
        return dict(torque=self.last_torque, error=None, policy_state=self.visual_phase,
                    policy_complete=self.visual_finished, policy_failure=self.failure,
                    events=self.events, accepted_key_observations=self.total_accepted,
                    accepted_grip_observations=len(self.grip_observations),
                    accepted_outcome_observations=self.outcome_accepted_count,
                    outcome_verified=self.outcome_verified, outcome_observation=outcome,
                    observation=detection, commanded_pose=None,
                    touch=dict(distal_index_n=float(touch[2])),
                    estimated_root_position_m=self.d.qpos[:3].tolist())


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model', required=True)
    p.add_argument('--initial-xy', nargs=2, type=float, default=[5.95, -5.20])
    p.add_argument('--prior', default='/model/policy/slider_push_prior.json')
    p.add_argument('--shape', default='/model/known_objects/nicolet_passive_dynamics.glb')
    args = p.parse_args()
    model = mujoco.MjModel.from_xml_path(args.model)
    actor = ObservedSliderActor(model, args.initial_xy, args.prior, args.shape)
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


if __name__ == '__main__':
    main()
