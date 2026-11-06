"""Fault-injection checks for the post-withdrawal visual recovery state machine.

Synthetic observations exercise failure handling only; they are not physical
or perception validation. Full native-sensor execution is still required.
"""
import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from ftir_slider_observed_actor import ObservedSliderActor


def subject():
    a = ObservedSliderActor.__new__(ObservedSliderActor)
    a.failure = 'Tactile contact was lost during push'
    a.recovery_context = dict(code='push_contact_loss', filtered_distal_load_n=.01,
                              commanded_push_displacement_m=.069,
                              contact_loss_duration_s=.36)
    a.pending_contact_recovery = dict(reason=a.failure, context=dict(a.recovery_context))
    a.outcome_yaw = -.5
    a.visual_yaw_tolerance = .005
    a.visual_posture_weights = np.ones(1)
    a.events = []
    a.visual_phase = 'observe_window_outcome'
    a.visual_phase_started = 0.
    a.visual_start_yaw = -.5
    a.visual_stable_since = None
    a.visual_finished = a.outcome_verified = False
    a.outcome_window = []
    a.outcome_accepted_count = a.total_accepted = 0
    a.last_outcome_sensor_time = a.last_time = None
    a.next_control = 0.
    a.last_torque = np.zeros(1)
    a.visual_posture = np.zeros(1)
    a.actuator_ids = {'waist_yaw_joint':0}
    a.grip_observations = []
    a.joint = SimpleNamespace(qpos=np.array([-.5]), qvel=np.zeros(1))
    a.d = SimpleNamespace(joint=lambda _:a.joint, qpos=np.zeros(3))
    a.balance = SimpleNamespace(torque=lambda **_:np.zeros(1), qa=np.array([0]))
    a.estimate = SimpleNamespace(update=lambda _:None)
    a.vision = SimpleNamespace(observe=lambda *_:dict(accepted=True))
    a.outcome_vision = SimpleNamespace(observe=lambda *_:dict(accepted=True, baseline_corrected_position_m=.072))
    return a


def packet(a, t):
    obs = {k:None for k in a.fields}
    obs.update(time_s=t, right_touch_n=np.zeros(7), rgb=True, depth=True)
    return obs


def check():
    checks = {}
    a = subject()
    checks['late_contact_loss_can_be_inspected'] = a.recoverable_contact_loss()
    for name, changes in [
        ('early_loss', {'commanded_push_displacement_m':.059}),
        ('overload', {'code':'tactile_overload', 'filtered_distal_load_n':6.1}),
        ('short_loss', {'contact_loss_duration_s':.34}),
        ('nonfinite_load', {'filtered_distal_load_n':float('nan')})]:
        a = subject(); a.recovery_context.update(changes)
        checks[name+'_cannot_enter_recovery_inspection'] = not a.recoverable_contact_loss()

    a = subject()
    for i in range(7):a.update(packet(a, i/10))
    checks['seven_frames_do_not_resolve_fault'] = bool(a.failure and not a.outcome_verified)
    a.update(packet(a, .6))
    checks['repeated_timestamp_is_not_a_new_frame'] = len(a.outcome_window) == 7
    a.update(packet(a, .7))
    checks['eight_frames_require_return_before_resolution'] = bool(a.outcome_verified and a.failure and not a.visual_finished)
    a.joint.qpos[0] = -.2
    a.update(packet(a, 3.8)); a.update(packet(a, 4.9))
    checks['settled_return_resolves_fault_with_explicit_record'] = (a.visual_finished and a.failure is None
        and sum(e['state']=='contact_loss_recovery_confirmed' for e in a.events)==1)
    fault = next(e['fault'] for e in a.events if e['state']=='contact_loss_recovery_confirmed')
    checks['original_fault_is_preserved'] = fault == a.pending_contact_recovery

    a = subject()
    a.outcome_vision.observe = lambda *_:dict(accepted=False)
    a.update(packet(a, 12.1)); a.joint.qpos[0] = -.2
    a.update(packet(a, 15.2)); a.update(packet(a, 16.3))
    checks['failed_visual_confirmation_remains_failed_after_return'] = (a.visual_finished
        and a.failure == 'Visual slider completion was not confirmed within the observation interval'
        and not any(e['state']=='contact_loss_recovery_confirmed' for e in a.events))

    a = subject(); a.visual_phase = None
    a.failure = 'Tactile load exceeded bound'; a.recovery_context['code'] = 'tactile_overload'
    response = dict(policy_complete=True, policy_failure=a.failure)
    with patch('ftir_slider_observed_actor.SliderActor.update', return_value=response):
        returned = a.update(packet(a, 0.))
    checks['overload_stays_terminal_after_withdrawal'] = returned == response and a.visual_phase is None

    a = subject(); a.joint.qpos[0] = -.48
    for i in range(9):a.update(packet(a, i/10))
    checks['unsettled_view_cannot_confirm_outcome'] = not a.outcome_verified and not a.outcome_window

    paths = [Path(__file__), Path(__file__).with_name('ftir_slider_actor.py'),
             Path(__file__).with_name('ftir_slider_observed_actor.py')]
    return dict(passed=all(checks.values()), checks=checks,
                source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                scope=__doc__.strip())


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--out', required=True); args = p.parse_args()
    out = Path(args.out)
    if out.exists():raise FileExistsError(out)
    report = check(); out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))
    if not report['passed']:raise SystemExit(1)
