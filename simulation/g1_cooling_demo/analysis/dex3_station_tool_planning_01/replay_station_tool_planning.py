"""Recheck station tool-pose alternatives on the original sensor prefix.

Only a declared observation-based ambiguity option changes. All actor modules
come from the recording's frozen source snapshot. This diagnostic stops at the
first observed plan; it never treats changed-command replay as physical motion.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pickle
import shutil
import sys

import mujoco
import numpy as np


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def replay(run, output):
    run, output = Path(run).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, output / Path(__file__).name)
    result = json.loads((run / 'result.json').read_text())
    contract = json.loads((run / 'contract.json').read_text())
    assert sha(run / 'contract.json') == result['contract_sha256']
    for name, key in [('sensors.npz', 'sensors_sha256'),
                      ('responses.pkl', 'responses_sha256'),
                      ('camera_index.json', 'camera_index_sha256')]:
        assert sha(run / name) == result[key]
    snapshot = run / 'source_snapshot'
    for name, digest in contract['source_snapshot_sha256'].items():
        assert sha(snapshot / name) == digest
    sys.path.insert(0, str(snapshot))
    from station_pickup_actor import StationPickupActor

    policy = run / 'policy_source'
    prior = json.loads((policy / 'tool_prior.json').read_text())
    assert sha(policy / 'tool_prior.json') == contract['controller_prior_sha256']
    assert not prior.get('resolve_tool_pose_ambiguity', False)
    prior['resolve_tool_pose_ambiguity'] = True
    shape = run / 'object_shape_source/tool_shape.glb'
    assert sha(shape) == prior['tool_shape_sha256']
    prior['tool_shape_path'] = str(shape)
    actor = StationPickupActor(
        mujoco.MjModel.from_xml_path(str(run / 'actor_bundle/model/world.xml')),
        policy, json.loads((run / 'walking_prior.json').read_text()), prior,
        json.loads((policy / 'preparation_targets.json').read_text()))
    sensor = dict(np.load(run / 'sensors.npz'))
    responses = pickle.loads((run / 'responses.pkl').read_bytes())
    cameras = json.loads((run / 'camera_index.json').read_text())
    compared, maximum, frames, failure = 0, 0., 0, None
    events = []
    try:
        for i, expected in enumerate(responses):
            packet = {key: value[i] for key, value in sensor.items()}
            frame = int(packet.pop('camera_frame_id'))
            packet.update(head_rgb=None, head_depth=None)
            if frame >= 0:
                entry = cameras[frame]
                assert sha(run / entry['file']) == entry['sha256']
                assert abs(entry['time_s'] - float(packet['time_s'])) < 1e-8
                with np.load(run / entry['file']) as image:
                    packet.update({key: image[key] for key in image.files})
                frames += 1
            response = actor.update(packet)
            maximum = max(maximum, float(np.max(abs(response['torque'] - expected['torque']))))
            compared += 1
            if maximum > 1e-10:
                raise RuntimeError('Controller prefix changed before the observed plan')
            if i % 5000 == 0:
                print('sensor_prefix', round(float(packet['time_s']), 3), response['phase'], flush=True)
            events = response['events']
            if any(event.get('kind') == 'observed_tool_plan' for event in events):
                break
    except Exception as error:
        failure = type(error).__name__ + ': ' + str(error)
    finally:
        actor.close()
    plans = [event for event in events if event.get('kind') == 'observed_tool_plan']
    alternatives = [event for event in events if event.get('kind') == 'observed_tool_pose_ambiguity']
    report = dict(scope=__doc__, failure=failure,
        source_result_sha256=sha(run / 'result.json'),
        source_contract_sha256=result['contract_sha256'],
        source_sensors_sha256=result['sensors_sha256'],
        source_responses_sha256=result['responses_sha256'],
        source_camera_index_sha256=result['camera_index_sha256'],
        actor_source_sha256=contract['source_snapshot_sha256'],
        script_sha256=sha(__file__), changed_option='resolve_tool_pose_ambiguity: false -> true',
        compared_sensor_packets=compared, maximum_prefix_torque_error=maximum,
        replayed_camera_frames=frames, final_plan=plans[-1] if plans else None,
        observation_supported_alternatives=alternatives,
        planned=bool(failure is None and plans and plans[-1]['plan']['planned']),
        changed_physical_continuation_executed=False,
        qualified_approach=False, qualified_grasp=False, qualified_paper_branch=False)
    (output / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in
        ['failure', 'compared_sensor_packets', 'maximum_prefix_torque_error', 'planned']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recording')
    parser.add_argument('output')
    args = parser.parse_args()
    replay(args.recording, args.output)
