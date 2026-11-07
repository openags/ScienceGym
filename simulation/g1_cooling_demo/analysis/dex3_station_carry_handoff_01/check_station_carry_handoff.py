"""Replay a recorded station prefix with the carrying actor at the handoff.

Only recorded encoders, IMU and native camera frames enter the actor. The
diagnostic stops after its first pickup response. No changed physics or
successful carrying is inferred from this controller compatibility check.
"""
import argparse
import json
from pathlib import Path
import pickle
import shutil

import mujoco
import numpy as np

from run_dex3_walking import sha
from station_pickup_actor import StationPickupActor

HERE = Path(__file__).resolve().parent


def check(recording, carrying, output):
    recording, carrying, output = [Path(p).resolve() for p in (recording, carrying, output)]
    output.mkdir(parents=True, exist_ok=False)
    read = lambda base, name: json.loads((base / name).read_text())
    result, contract = read(recording, 'result.json'), read(recording, 'contract.json')
    for name, key in [('contract.json', 'contract_sha256'), ('sensors.npz', 'sensors_sha256'),
                      ('responses.pkl', 'responses_sha256'), ('camera_index.json', 'camera_index_sha256')]:
        assert sha(recording / name) == result[key]
    carry_contract = read(carrying, 'contract.json')
    assert carry_contract['task'] == 'visual_pickup_loaded_out_and_back_release'
    assert sha(carrying / 'policy_source/tool_prior.json') == carry_contract['controller_prior_sha256']
    prior = read(carrying, 'policy_source/tool_prior.json')
    prior.pop('initial_robot_qpos')
    shape = carrying / 'object_shape_source/tool_shape.glb'
    assert sha(shape) == prior['tool_shape_sha256']
    prior['tool_shape_path'] = str(shape)
    isolation = read(recording, 'actor_isolation.json')
    assert sha(recording / 'actor_bundle/model/world.xml') == isolation['bundled_model_sha256']
    for item in isolation['input_files']:
        assert sha(recording / item['path']) == item['sha256']
    modules = set(isolation['source_modules']) | {'carry_tool_actor.py', 'quasistatic_walking.py'}
    snapshot = output / 'actor_source'
    snapshot.mkdir()
    for name in modules:
        shutil.copyfile(HERE / name, snapshot / name)
    shutil.copyfile(__file__, output / Path(__file__).name)
    model = mujoco.MjModel.from_xml_path(str(recording / 'actor_bundle/model/world.xml'))
    actor = StationPickupActor(model, recording / 'policy_source',
        read(recording, 'walking_prior.json'), prior,
        read(recording, 'policy_source/preparation_targets.json'))
    sensor = dict(np.load(recording / 'sensors.npz'))
    responses = pickle.loads((recording / 'responses.pkl').read_bytes())
    cameras = read(recording, 'camera_index.json')
    compared, maximum, frame_count, failure = 0, 0., 0, None
    first_pickup_time = None
    try:
        for i, expected in enumerate(responses):
            packet = {key: value[i] for key, value in sensor.items()}
            frame = int(packet.pop('camera_frame_id'))
            packet.update(head_rgb=None, head_depth=None)
            if frame >= 0:
                entry = cameras[frame]
                assert sha(recording / entry['file']) == entry['sha256']
                assert abs(entry['time_s']-float(packet['time_s'])) < 1e-8
                with np.load(recording / entry['file']) as values:
                    packet.update({key: values[key] for key in values.files})
                frame_count += 1
            response = actor.update(packet)
            maximum = max(maximum, float(np.max(abs(response['torque']-expected['torque']))))
            compared += 1
            if maximum > 1e-10:
                raise RuntimeError('Station prefix or first pickup torque changed')
            if response.get('mission_phase') == 'pickup':
                first_pickup_time = float(packet['time_s'])
                break
            if i % 5000 == 0:
                print('station_carry_prefix', round(float(packet['time_s']), 3), response['phase'], flush=True)
    except Exception as error:
        failure = type(error).__name__ + ': ' + str(error)
    finally:
        actor.close()
    checks = dict(prefix_exact=failure is None and compared > 10000 and maximum == 0.,
        native_camera_frames_used=frame_count > 0, reached_first_pickup_response=first_pickup_time is not None,
        carrying_actor_selected=actor.pickup is not None and type(actor.pickup).__module__ == 'carry_tool_actor',
        carrying_return_uses_handoff_estimate=actor.pickup is not None and np.array_equal(
            actor.pickup.initial_base_xy, actor.preparation.d.qpos[:2]))
    report = dict(scope=__doc__, passed=all(checks.values()), checks=checks, failure=failure,
        compared_sensor_packets=compared, maximum_torque_error=maximum,
        replayed_camera_frames=frame_count, first_pickup_time_s=first_pickup_time,
        source_result_sha256=sha(recording / 'result.json'),
        source_sensor_sha256=result['sensors_sha256'], source_responses_sha256=result['responses_sha256'],
        carrying_contract_sha256=sha(carrying / 'contract.json'),
        carrying_prior_sha256=carry_contract['controller_prior_sha256'],
        actor_source_sha256={name: sha(snapshot / name) for name in sorted(modules)},
        script_sha256=sha(__file__), physical_continuation_executed=False,
        qualified_carry=False, qualified_paper_branch=False)
    (output / 'review.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: report[key] for key in ['passed', 'failure', 'checks', 'compared_sensor_packets']}), flush=True)
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recording')
    parser.add_argument('carrying')
    parser.add_argument('output')
    args = parser.parse_args()
    if not check(args.recording, args.carrying, args.output):
        raise SystemExit(1)
