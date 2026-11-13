"""Independently replay visual completion from retained native sensor packets.

Predictions use the pinned public actor model and code. Equipment truth is
loaded only after predictions, for final error review; nothing feeds the actor.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys

import mujoco
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def difference(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return max((difference(a[k], b[k]) for k in a), default=0.) if set(a) == set(b) else float('inf')
    if isinstance(a, list) and isinstance(b, list):
        return max((difference(x, y) for x, y in zip(a, b)), default=0.) if len(a) == len(b) else float('inf')
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a)-float(b))
    return 0. if a == b else float('inf')


def json_finite(value):
    if isinstance(value, dict):
        return {k:json_finite(v) for k,v in value.items()}
    if isinstance(value, list):
        return [json_finite(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def verify(folder):
    folder = Path(folder).resolve()
    output = folder/'visual_outcome_review.json'
    if output.exists():
        raise FileExistsError(output)
    result = json.loads((folder/'result.json').read_text())
    receipt = json.loads((folder/'actor_isolation.json').read_text())
    physical = json.loads((folder/'physical_slider_review.json').read_text())
    isolation = json.loads((folder/'isolation_verification.json').read_text())
    events = result.get('actor_last_output', {}).get('events', [])
    checks = {}
    checks['observed_slider_entry_point'] = (result.get('requires_visual_outcome_confirmation') is True and
                                            result['actor_entry_point'] == 'ftir_slider_observed_actor.py')
    checks['independent_physics_passed'] = (physical['passed'] and physical['trace_sha256'] == sha(folder/'trace.npz')
                                          and physical['model_sha256'] == sha(folder/'world.xml'))
    checks['isolated_execution_passed'] = (isolation['passed'] and
                                         isolation['isolation_receipt_sha256'] == sha(folder/'actor_isolation.json'))
    code = folder/'actor_bundle/code'
    required = ['ftir_slider_outcome.py', 'ftir_slider_vision.py', 'ftir_vision.py',
                'ftir_slider_posture.py', 'observations.py', 'ftir_hand.py', 'ftir_cover_geometry.py']
    checks['pinned_observer_modules'] = all(sha(code/n) == receipt['source_modules'].get(n) for n in required)
    if not checks['pinned_observer_modules']:
        raise ValueError('Pinned observer code changed')
    sys.path.insert(0, str(code))
    from ftir_slider_posture import initialize_slider
    from ftir_slider_vision import SliderObservation
    from ftir_slider_outcome import SliderRangeObservation
    from ftir_vision import KeyRowObservation
    from observations import StateEstimate

    planning = next(e for e in events if e['state'] == 'observed_geometry_path_planned')
    observations = [e for e in events if e['state'] == 'slider_outcome_observation']
    confirmations = [e for e in events if e['state'] == 'slider_outcome_confirmed']
    checks['one_visual_confirmation'] = len(confirmations) == 1
    selected = [] if not confirmations else confirmations[0]['sensor_frames']
    selected_times = [float(r['time_s']) for r in selected]
    checks['eight_distinct_fresh_frames'] = (len(selected_times) == 8 and
        len(set(selected_times)) == 8 and selected_times[-1]-selected_times[0] >= .65 and
        bool(np.all((np.diff(selected_times) > .09) & (np.diff(selected_times) < .11))))
    end_events = {e['state']:float(e['time_s']) for e in events if e['state'] in {
        'restore_hand_endpoint', 'turn_to_outcome_view_started', 'turn_to_outcome_view_endpoint',
        'slider_outcome_confirmed', 'return_from_outcome_view_endpoint'}}
    expected_order = ['restore_hand_endpoint', 'turn_to_outcome_view_started', 'turn_to_outcome_view_endpoint',
                      'slider_outcome_confirmed', 'return_from_outcome_view_endpoint']
    checks['observe_after_withdraw_then_return'] = (all(n in end_events for n in expected_order) and
        all(end_events[a] <= end_events[b] for a, b in zip(expected_order[:-1], expected_order[1:])))
    responses = json.loads((folder/'actor_responses.json').read_text())
    completion_time = end_events.get('return_from_outcome_view_endpoint', float('inf'))
    checks['no_premature_completion'] = not any(r.get('policy_complete') and r['time_s'] < completion_time-1e-8 for r in responses)

    # Initial frames independently reconstruct the closed-position baseline;
    # no recorded fit or selected equipment pose is supplied to the observer.
    sensor_data = np.load(folder/'sensor_observations.npz')
    needed = {round(float(e['time_s']), 6) for e in observations}
    rgb_index = json.loads((folder/'head_rgb_index.json').read_text())
    colors = {}
    used_chunks = {}
    for part in rgb_index['chunks']:
        path = folder/part['path']
        with np.load(path) as data:
            ts = data['time']
            chosen = [i for i,t in enumerate(ts) if t < planning['time_s'] or round(float(t), 6) in needed]
            if not chosen:
                continue
            if sha(path) != part['sha256']:
                raise ValueError('Native RGB chunk changed')
            used_chunks[part['path']] = part['sha256']
            rgb = data['rgb']
            for i in chosen:
                colors[round(float(ts[i]), 6)] = rgb[i].copy()
    depth_index = json.loads((folder/'head_depth_index.json').read_text())
    depths = {}
    for part in depth_index['parts']:
        if part['first_time_s'] >= planning['time_s'] and not any(part['first_time_s']-1e-6 <= t <= part['last_time_s']+1e-6 for t in needed):
            continue
        path = folder/part['path']
        if sha(path) != part['sha256']:
            raise ValueError('Native depth chunk changed')
        used_chunks[part['path']] = part['sha256']
        with np.load(path) as data:
            shuffled = data['bytes']
            values = shuffled.transpose(1, 2, 3, 0).copy().view('<f4').reshape(shuffled.shape[1:])
            for t,z in zip(data['time'], values):
                key = round(float(t), 6)
                if key in colors:
                    depths[key] = z.copy()
    model = mujoco.MjModel.from_xml_path(str(folder/'actor_bundle/model/world.xml'))
    xy = json.loads((folder/'staging.json').read_text())['robot_map_xy_prior_m']
    data = initialize_slider(model, xy)
    estimate = StateEstimate(model, data)
    prior = folder/'actor_bundle/model/policy/slider_push_prior.json'
    shape = folder/'actor_bundle/model/known_objects/nicolet_passive_dynamics.glb'
    keys = KeyRowObservation(model, data)
    closed = SliderObservation(model, data, prior, shape)
    baselines = []
    predictions = []
    observer = None
    recorded = {round(float(e['time_s']), 6):e for e in observations}
    for t in sorted(colors):
        i = int(np.argmin(abs(sensor_data['time_s']-t)))
        if abs(sensor_data['time_s'][i]-t) > 1e-6 or t not in depths:
            raise ValueError('Image/proprioception timestamp mismatch')
        packet = {k:sensor_data[k][i] for k in ['time_s', 'joint_position', 'joint_velocity', 'imu_quaternion', 'imu_gyro']}
        packet['depth'] = depths[t]
        estimate.update(packet)
        key_row = keys.observe(colors[t], depths[t])
        if t < planning['time_s']:
            fitted = closed.observe(depths[t], key_row)
            if fitted['accepted']:
                baselines.append(fitted)
            continue
        if observer is None:
            observer = SliderRangeObservation(model, data, prior, shape, baselines)
        prediction = observer.observe(depths[t], key_row)
        recorded_event = recorded[t]
        error = max(difference(key_row, recorded_event['key_observation']),
                    difference(prediction, recorded_event['observation']))
        predictions.append(dict(time_s=t, observation=prediction,
                                maximum_recorded_prediction_difference=error))
        print('outcome_replay', t, prediction['accepted'], error, flush=True)
    baseline_error = difference(baselines[-8:], planning['grip_observations'])
    checks['closed_baseline_reconstructed'] = len(baselines) >= 8 and baseline_error < 1e-9
    checks['native_outcome_predictions_reproduced'] = (len(predictions) == len(observations) and len(predictions) >= 8
        and all(r['maximum_recorded_prediction_difference'] < 1e-9 for r in predictions))
    by_time = {round(r['time_s'], 6):r['observation'] for r in predictions}
    checks['confirmed_frames_independently_accepted'] = bool(selected) and all(
        by_time.get(round(r['time_s'], 6), {}).get('accepted') for r in selected)
    checks['selected_positions_match_replay'] = bool(selected) and all(
        abs(by_time.get(round(r['time_s'], 6), {}).get('baseline_corrected_position_m', float('inf'))-r['observed_position_m']) < 1e-9 for r in selected)
    checks['selected_position_sequence_stable'] = bool(selected) and np.std([r['observed_position_m'] for r in selected]) < .002

    # Only now inspect equipment truth. These values are never used above.
    plant = mujoco.MjModel.from_xml_path(str(folder/'world.xml'))
    trace = np.load(folder/'trace.npz')
    slider = int(plant.joint('nicolet_door_slide').qposadr[0])
    truth_rows = []
    for row in selected:
        index = max(0, int(np.argmin(abs(trace['time']-row['time_s'])))-1)
        truth = float(trace['qpos'][index, slider])
        truth_rows.append(dict(sensor_time_s=row['time_s'], source_state_time_s=float(trace['time'][index]),
                               actual_slider_position_m=truth, observed_slider_position_m=row['observed_position_m'],
                               absolute_error_m=abs(truth-row['observed_position_m'])))
    checks['actual_gap_inside_unchanged_requirement'] = bool(truth_rows) and all(.065 <= r['actual_slider_position_m'] <= .075 for r in truth_rows)
    checks['observed_position_error_below_guard_margin'] = bool(truth_rows) and max(r['absolute_error_m'] for r in truth_rows) < .001
    checks = {k:bool(v) for k,v in checks.items()}
    report = dict(passed=all(checks.values()), checks=checks,
                  thresholds=dict(required_distinct_frames=8, minimum_span_s=.65,
                                  maximum_position_std_m=.002, maximum_position_error_m=.001,
                                  unchanged_physical_gap_m=[.065, .075]),
                  baseline_replay_error=baseline_error, predictions=predictions, truth_review=truth_rows,
                  used_native_chunks=used_chunks, verifier_sha256=sha(__file__),
                  physical_review_sha256=sha(folder/'physical_slider_review.json'),
                  isolation_review_sha256=sha(folder/'isolation_verification.json'),
                  result_sha256=sha(folder/'result.json'), trace_sha256=sha(folder/'trace.npz'),
                  qualified_skill=False, qualified_paper_branch=False,
                  scope='One executed window operation with independent native-sensor outcome replay and post-prediction truth review. No walking integration, calibration, reliability campaign or complete paper branch.')
    report = json_finite(report)
    output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    shutil.copyfile(__file__, folder/'verify_slider_outcome.py')
    print(json.dumps(dict(passed=report['passed'], checks=checks)), flush=True)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('folder')
    if not verify(p.parse_args().folder)['passed']:
        raise SystemExit(1)
