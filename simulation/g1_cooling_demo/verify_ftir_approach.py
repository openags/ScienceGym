"""Replay a frozen walking/station actor using only its native sensor packets.

An independent process receives encoders, IMU, tactile and camera frames in
their original order. The process has no access to plant states or reports.
Only the evaluator compares motor outputs and then examines physical truth.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pickle
import shutil
import subprocess
import sys

import mujoco
import numpy as np

from isolation import namespace_prefix
from verify_slider_outcome import difference, json_finite
from event_canonicalization import canonical_events


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frames(folder, index_name, parts_key, depth=False):
    index = json.loads((folder/index_name).read_text())
    for row in index[parts_key]:
        path = folder/row['path']
        if sha(path) != row['sha256']:
            raise ValueError('Native camera chunk changed: '+row['path'])
        with np.load(path) as chunk:
            if depth:
                raw = chunk['bytes']
                pixels = raw.transpose(1, 2, 3, 0).copy().view('<f4').reshape(raw.shape[1:])
            else:
                pixels = chunk['rgb']
            yield from zip(chunk['time'], pixels)


def plain(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {k:plain(v) for k,v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    return value


def event_differences(actual, recorded, path='$', examples=None):
    """Retain bounded mismatch locations, including nonfinite numeric leaves."""
    if examples is None:
        examples = []
    if len(examples) >= 100 or difference(actual, recorded) == 0.:
        return examples
    if isinstance(actual, dict) and isinstance(recorded, dict):
        if set(actual) != set(recorded):
            examples.append(dict(path=path, reason='different dictionary keys',
                                 actual=sorted(map(str, actual)), recorded=sorted(map(str, recorded))))
        for key in actual:
            if key in recorded:
                event_differences(actual[key], recorded[key], path+'/'+str(key), examples)
    elif isinstance(actual, list) and isinstance(recorded, list):
        if len(actual) != len(recorded):
            examples.append(dict(path=path, reason='different list lengths',
                                 actual=len(actual), recorded=len(recorded)))
        for i, (a, b) in enumerate(zip(actual, recorded)):
            event_differences(a, b, path+'/'+str(i), examples)
    else:
        examples.append(dict(path=path, actual=repr(actual), recorded=repr(recorded)))
    return examples


def verify(folder):
    folder = Path(folder).resolve()
    output = folder/'continuous_approach_review.json'
    if output.exists():
        raise FileExistsError(output)
    result = json.loads((folder/'result.json').read_text())
    receipt = json.loads((folder/'actor_isolation.json').read_text())
    staging = json.loads((folder/'staging.json').read_text())
    physics = json.loads((folder/'physical_slider_review.json').read_text())
    isolation = json.loads((folder/'isolation_verification.json').read_text())
    code = folder/'actor_bundle/code'
    model_dir = folder/'actor_bundle/model'
    if result.get('actor_entry_point') != 'ftir_approach_actor.py':
        raise ValueError('Requires the continuous approach actor')
    if (sha(model_dir/'world.xml') != receipt['bundled_model_sha256'] or
            not all(sha(code/n) == h for n,h in receipt['source_modules'].items()) or
            not all(sha(folder/r['path']) == r['sha256'] for r in receipt['input_files'])):
        raise ValueError('Frozen actor input changed')
    sensors = dict(np.load(folder/'sensor_observations.npz'))
    allowed = {'time_s', 'joint_position', 'joint_velocity', 'imu_quaternion', 'imu_gyro', 'right_touch_n'}
    if set(sensors) != allowed:
        raise ValueError('Unexpected native sensor fields')
    trace = dict(np.load(folder/'trace.npz'))
    responses = json.loads((folder/'actor_responses.json').read_text())
    recorded = {round(r['time_s'], 8):r for r in responses}
    colors = iter(frames(folder, 'head_rgb_index.json', 'chunks'))
    depths = iter(frames(folder, 'head_depth_index.json', 'parts', depth=True))
    color = next(colors, None)
    depth = next(depths, None)
    command = namespace_prefix(code, model_dir)+[
        sys.executable, '/actor/ftir_approach_actor.py', '--model', '/model/world.xml',
        '--initial-xy', *map(str, staging['robot_map_xy_prior_m']),
        '--station-xy', *map(str, staging['station_map_xy_goal_m'])]
    if staging.get('walking_controller') is not None:
        command.extend(['--walking-controller',staging['walking_controller']])
    max_torque = max_response = 0.
    compared = camera_frames = 0
    failure = None
    answer = {}
    with open(folder/'continuous_replay_stderr.log', 'w') as stderr:
        process = subprocess.Popen(command, env=receipt['environment'], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=stderr, close_fds=True)
        try:
            for i,t in enumerate(sensors['time_s']):
                packet = {k:v[i] for k,v in sensors.items()}
                packet.update(rgb=None, depth=None)
                if color is not None and abs(color[0]-t) < 1e-8:
                    if depth is None or abs(depth[0]-t) >= 1e-8:
                        raise ValueError('Camera timestamps do not match')
                    packet.update(rgb=color[1], depth=depth[1])
                    color, depth = next(colors, None), next(depths, None)
                    camera_frames += 1
                if abs(trace['time'][i]-t) > 1e-8:
                    raise ValueError('Sensor and motor trace timestamps do not match')
                pickle.dump(packet, process.stdin, protocol=5)
                process.stdin.flush()
                answer = pickle.load(process.stdout)
                if answer.get('error'):
                    raise RuntimeError(answer['error'])
                max_torque = max(max_torque, float(np.max(abs(answer['torque']-trace['ctrl'][i]))))
                key = round(float(t), 8)
                if key in recorded:
                    comparable = dict(time_s=float(t), **{
                        k:plain(v) for k,v in answer.items() if k not in {'torque', 'events'}})
                    max_response = max(max_response, difference(comparable, recorded[key]))
                    compared += 1
                if i % 2500 == 0:
                    print('continuous_sensor_replay', i, len(sensors['time_s']),
                          'torque_error', max_torque, 'response_error', max_response, flush=True)
        except Exception as error:
            failure = str(error)
        finally:
            process.stdin.close()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    replay_events = plain(answer.get('events', []))
    recorded_events = result.get('actor_last_output', {}).get('events', [])
    raw_event_error = difference(replay_events, recorded_events)
    event_error = difference(canonical_events(replay_events), canonical_events(recorded_events))
    replay_event_path = folder/'replayed_events.json'
    if replay_event_path.exists():
        raise FileExistsError(replay_event_path)
    replay_event_path.write_text(json.dumps(json_finite(replay_events), indent=2, allow_nan=False)+'\n')
    raw_event_examples = event_differences(replay_events, recorded_events)
    event_examples = event_differences(canonical_events(replay_events), canonical_events(recorded_events))
    handoffs = [e for e in replay_events if e['state'] == 'continuous_station_handoff']
    confirmations = [e for e in replay_events if e['state'] == 'slider_outcome_confirmed']
    selected = confirmations[0]['sensor_frames'] if len(confirmations) == 1 else []
    times = [r['time_s'] for r in selected]
    checks = dict(
        frozen_sensor_actor_replayed=failure is None and process.returncode == 0,
        every_motor_output_reproduced=max_torque < 1e-8,
        every_retained_response_reproduced=compared == len(responses) and max_response < 1e-9,
        full_event_sequence_reproduced=event_error < 1e-9,
        every_camera_frame_consumed=color is None and depth is None,
        independent_physics_passed=physics['passed'] and physics['trace_sha256'] == sha(folder/'trace.npz')
                                   and physics['model_sha256'] == sha(folder/'world.xml'),
        isolation_passed=isolation['passed'] and isolation['isolation_receipt_sha256'] == sha(folder/'actor_isolation.json'),
        attempt_completed=result['status'] == 'attempt_finished_pending_independent_slider_verification',
        one_sensor_derived_handoff=len(handoffs) == 1,
        one_visual_confirmation=len(confirmations) == 1,
        eight_fresh_confirmation_frames=len(times) == len(set(times)) == 8 and times[-1]-times[0] >= .65
                                        and bool(np.all((np.diff(times) > .09) & (np.diff(times) < .11))),
        stable_visual_positions=bool(selected) and np.std([r['observed_position_m'] for r in selected]) < .002,
    )
    # The new actor process has now exited. Truth is used only by this reviewer.
    model = mujoco.MjModel.from_xml_path(str(folder/'world.xml'))
    checks['continuous_physics_clock'] = bool(np.allclose(np.diff(trace['time']), model.opt.timestep, rtol=0, atol=1e-9))
    checks['declared_initial_pose_preserved'] = bool(np.array_equal(trace['qpos'][0], staging['initial_qpos']))
    handoff_truth = None
    if len(handoffs) == 1:
        h = handoffs[0]
        index = int(np.argmin(abs(trace['time']-h['time_s'])))
        travel = float(np.linalg.norm(trace['qpos'][index,:2]-trace['qpos'][0,:2]))
        estimate = np.array(h['estimated_root_position_m'])
        error = float(np.linalg.norm(estimate[:2]-trace['qpos'][index,:2]))
        handoff_truth = dict(time_s=h['time_s'], executed_horizontal_displacement_m=travel,
                             estimated_root_position_m=estimate.tolist(), xy_error_m=error)
        checks['executed_approach_before_operation'] = travel > .5
        checks['handoff_xy_error_below_five_mm'] = error < .005
        checks['handoff_after_stable_map_observations'] = len(h['registration_observations']) >= 5
    else:
        checks.update(executed_approach_before_operation=False, handoff_xy_error_below_five_mm=False,
                      handoff_after_stable_map_observations=False)
    slider = int(model.joint('nicolet_door_slide').qposadr[0])
    truth_rows = []
    for row in selected:
        i = max(0, int(np.argmin(abs(trace['time']-row['time_s'])))-1)
        truth = float(trace['qpos'][i,slider])
        truth_rows.append(dict(sensor_time_s=row['time_s'], actual_slider_position_m=truth,
                               observed_slider_position_m=row['observed_position_m'],
                               absolute_error_m=abs(truth-row['observed_position_m'])))
    checks['actual_gap_inside_unchanged_requirement'] = bool(truth_rows) and all(.065 <= r['actual_slider_position_m'] <= .075 for r in truth_rows)
    checks['observed_error_below_guard_margin'] = bool(truth_rows) and max(r['absolute_error_m'] for r in truth_rows) < .001
    report = json_finite(dict(passed=all(checks.values()), checks={k:bool(v) for k,v in checks.items()},
        failure=failure, maximum_torque_replay_error_nm=max_torque, maximum_response_replay_error=max_response,
        maximum_event_replay_error=event_error, sensor_packets=len(sensors['time_s']), camera_frames=camera_frames,
        raw_maximum_event_replay_error=raw_event_error, raw_event_difference_examples=raw_event_examples,
        event_comparison='Ordered events and paths; only planning baseline self-intersection pairs are an unordered set',
        event_canonicalization_sha256=sha(Path(__file__).with_name('event_canonicalization.py')),
        event_difference_examples=event_examples, replayed_events_sha256=sha(replay_event_path),
        comparison_helper_sha256=sha(Path(__file__).with_name('verify_slider_outcome.py')),
        compared_responses=compared, handoff_truth_review=handoff_truth, outcome_truth_review=truth_rows,
        verifier_sha256=sha(__file__), physical_review_sha256=sha(folder/'physical_slider_review.json'),
        isolation_review_sha256=sha(folder/'isolation_verification.json'), result_sha256=sha(folder/'result.json'),
        trace_sha256=sha(folder/'trace.npz'), sensors_sha256=sha(folder/'sensor_observations.npz'),
        camera_indexes_sha256={n:sha(folder/n) for n in ['head_rgb_index.json','head_depth_index.json']},
        qualified_skill=False, qualified_paper_branch=False,
        scope='One continuous local walking approach and observed window operation; no carrying, full interstation experiment or reliability qualification.'))
    output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    shutil.copyfile(__file__, folder/Path(__file__).name)
    print(json.dumps({'passed':report['passed'], 'checks':report['checks']}), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder')
    args = parser.parse_args()
    if not verify(args.folder)['passed']:
        raise SystemExit(1)
