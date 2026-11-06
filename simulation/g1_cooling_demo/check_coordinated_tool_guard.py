"""Compare a corrected coordinated-finger guard with recorded sensor commands.

The old failed trial remains failed. This checks unchanged command history and
the alternative command at its terminal observation, not physical continuation.
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

from visual_tool_actor import ToolActor


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def check(run, out):
    run, out = Path(run).resolve(), Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    here = Path(__file__).parent
    result = json.loads((run / 'result.json').read_text())
    contract = json.loads((run / 'contract.json').read_text())
    assert result['failure'] == 'Source contact feature cannot close toward the opposed fingers'
    assert sha(run / 'contract.json') == result['contract_sha256']
    assert sha(run / 'actor_isolation.json') == contract['actor_isolation_sha256']
    isolation = json.loads((run / 'actor_isolation.json').read_text())
    for name, key in [('sensors.npz', 'sensors_sha256'), ('responses.pkl', 'responses_sha256'),
                      ('camera_index.json', 'camera_index_sha256')]:
        assert sha(run / name) == result[key]
    source_hashes = {}
    for module in list(sys.modules.values()):
        path = getattr(module, '__file__', None)
        if path is None or Path(path).resolve().parent != here or Path(path).name == Path(__file__).name:
            continue
        path = Path(path).resolve()
        source_hashes[path.name] = sha(path)
        if path.name != 'dex3_tool_actor.py':
            assert source_hashes[path.name] == isolation['source_modules'][path.name]
        shutil.copyfile(path, out / path.name)
    shutil.copyfile(__file__, out / Path(__file__).name)
    prior = json.loads((run / 'policy_source/tool_prior.json').read_text())
    assert sha(run / 'policy_source/tool_prior.json') == contract['controller_prior_sha256']
    prior['tool_shape_path'] = str(run / 'object_shape_source/tool_shape.glb')
    actor = ToolActor(mujoco.MjModel.from_xml_path(str(run / 'controller_model/world.xml')), prior)
    sensors = dict(np.load(run / 'sensors.npz'))
    responses = pickle.loads((run / 'responses.pkl').read_bytes())
    cameras = json.loads((run / 'camera_index.json').read_text())
    maximum, compared, failure, terminal = 0., 0, None, None
    try:
        for i, expected in enumerate(responses):
            packet = {key: values[i] for key, values in sensors.items()}
            frame = int(packet.pop('camera_frame_id'))
            packet.update(head_rgb=None, head_depth=None)
            if frame >= 0:
                entry = cameras[frame]
                assert sha(run / entry['file']) == entry['sha256']
                with np.load(run / entry['file']) as image:
                    packet.update({key: image[key] for key in image.files})
            response = actor.update(packet)
            if expected.get('error'):
                assert i == len(responses) - 1
                points = actor.points()
                direction = (points[1] + points[2]) / 2 - points[0]
                distance = float(np.linalg.norm(direction))
                direction /= max(distance, 1e-12)
                lever = []
                for k, ((body, _), driver, sign) in enumerate(zip(actor.features, actor.drivers, actor.signs)):
                    jp, jr = np.zeros((3, actor.m.nv)), np.zeros((3, actor.m.nv))
                    mujoco.mj_jac(actor.m, actor.d, jp, jr, points[k], body)
                    lever.append(float(sign * (direction if k == 0 else -direction) @ jp[:, actor.va[driver]]))
                _, matrices, _ = actor.coordinated_finger_state(points)
                terminal = dict(time_s=float(packet['time_s']), phase=response['phase'],
                    original_error=expected['error'], corrected_error=response.get('error'),
                    original_single_joint_levers_m=lever, material_point_separation_m=distance,
                    coordinated_condition_numbers=[float(np.linalg.cond(j)) for j in matrices],
                    coordinated_minimum_singular_values_m=[float(np.linalg.svd(j, compute_uv=False)[-1]) for j in matrices],
                    corrected_command_finite=bool(np.isfinite(response['torque']).all()),
                    corrected_command_within_source_limits=bool(np.all(response['torque'] >= actor.m.actuator_ctrlrange[:, 0])
                        and np.all(response['torque'] <= actor.m.actuator_ctrlrange[:, 1])))
                break
            maximum = max(maximum, float(np.max(abs(response['torque'] - expected['torque']))))
            compared += 1
            if maximum > 1e-10:
                raise RuntimeError('Commands changed before the original guard failure')
            if i % 10000 == 0:
                print('controller_prefix', round(float(packet['time_s']), 3), response['phase'], flush=True)
    except Exception as error:
        failure = type(error).__name__ + ': ' + str(error)
    passed = bool(failure is None and terminal and terminal['corrected_error'] is None
        and terminal['corrected_command_finite'] and terminal['corrected_command_within_source_limits']
        and compared == len(responses) - 1 and maximum == 0.)
    report = dict(scope=__doc__, passed=passed, failure=failure,
        compared_prefix_commands=compared, maximum_torque_error=maximum, terminal_observation=terminal,
        source_result_sha256=sha(run / 'result.json'), source_contract_sha256=result['contract_sha256'],
        source_sensor_sha256=result['sensors_sha256'], source_responses_sha256=result['responses_sha256'],
        changed_actor_source=source_hashes, script_sha256=sha(__file__),
        physical_continuation_executed=False, qualified_tool_actuation=False, qualified_paper_branch=False)
    (out / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)
    return passed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recording')
    parser.add_argument('output')
    args = parser.parse_args()
    if not check(args.recording, args.output):
        raise SystemExit(1)
