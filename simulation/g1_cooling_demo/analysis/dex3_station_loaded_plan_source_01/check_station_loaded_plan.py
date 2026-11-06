"""Replay native station observations through the loaded withdrawal decision.

The revised actor receives only original sensor packets and a public support
map. All responses before the failed planning decision must remain identical.
This is a controller/planning diagnostic, never physical continuation evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pickle

import mujoco
import numpy as np

from carry_tool_actor import public_support_prior
from station_pickup_actor import StationPickupActor


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def difference(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        if a.keys() != b.keys():
            return float('inf')
        return max((difference(a[k], b[k]) for k in a), default=0.)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return float('inf')
        return max((difference(x, y) for x, y in zip(a, b)), default=0.)
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        a, b = np.asarray(a), np.asarray(b)
        if a.shape != b.shape:
            return float('inf')
        return float(np.max(abs(a-b), initial=0.))
    if isinstance(a, (float, np.floating)) and isinstance(b, (float, np.floating)):
        return abs(float(a)-float(b))
    return 0. if a == b else float('inf')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recording', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    run, out = args.recording.resolve(), args.output.resolve()
    out.mkdir(exist_ok=False, parents=True)
    read = lambda name: json.loads((run/name).read_text())
    result, contract, isolation = [read(n) for n in
        ['result.json', 'contract.json', 'actor_isolation.json']]
    for name, key in [('sensors.npz', 'sensors_sha256'), ('responses.pkl', 'responses_sha256'),
                      ('camera_index.json', 'camera_index_sha256'), ('contract.json', 'contract_sha256')]:
        assert sha(run/name) == result[key]
    model_path = run/'actor_bundle/model/world.xml'
    assert sha(model_path) == isolation['bundled_model_sha256']
    events = read('events.json')
    decision = next(e for e in events if e.get('kind') == 'carry_arm_plan')
    assert not decision['plan']['planned']
    model = mujoco.MjModel.from_xml_path(str(model_path))
    prior = read('policy_source/tool_prior.json')
    prior['carry_support_contacts'] = public_support_prior(model, read('laboratory_import.json'),
        contract['physical_acceptance']['maximum_sole_penetration_m'])
    prior['tool_shape_path'] = str(run/'object_shape_source/tool_shape.glb')
    assert sha(Path(prior['tool_shape_path'])) == prior['tool_shape_sha256']
    actor = StationPickupActor(model, run/'policy_source', read('walking_prior.json'), prior,
        read('policy_source/preparation_targets.json'))
    sensors = dict(np.load(run/'sensors.npz'))
    responses = pickle.loads((run/'responses.pkl').read_bytes())
    frames = read('camera_index.json')
    compared, error, frame_count, failure, reached = 0, 0., 0, None, False
    try:
        for i, expected in enumerate(responses):
            packet = {k: v[i] for k, v in sensors.items()}
            frame = int(packet.pop('camera_frame_id'))
            packet.update(head_rgb=None, head_depth=None)
            if frame >= 0:
                entry = frames[frame]
                assert sha(run/entry['file']) == entry['sha256']
                with np.load(run/entry['file']) as native:
                    packet.update({k: native[k] for k in native.files})
                frame_count += 1
            response = actor.update(packet)
            if float(packet['time_s']) >= decision['time_s']-1e-8:
                reached = actor.pickup is not None and actor.pickup.carry_plan is not None
                break
            actual = {k: v for k, v in response.items() if k != 'events'}
            error = max(error, difference(expected, actual))
            compared += 1
            if error > 1e-10:
                raise RuntimeError('Earlier sensor-driven response changed at packet '+str(i))
            if i % 10000 == 0:
                print('loaded_plan_prefix', float(packet['time_s']), response['phase'], flush=True)
    except Exception as exc:
        failure = type(exc).__name__+': '+str(exc)
    finally:
        actor.close()
    plan = actor.pickup.carry_plan if actor.pickup is not None else None
    report = dict(scope=__doc__, passed=bool(failure is None and reached and plan['planned']),
        failure=failure, compared_prefix_packets=compared,
        maximum_prefix_response_error=error if np.isfinite(error) else None,
        camera_frames_replayed=frame_count, reached_recorded_decision=reached,
        recorded_decision_time_s=decision['time_s'], original_plan=decision['plan'], revised_plan=plan,
        public_support_prior=prior['carry_support_contacts'],
        source_result_sha256=sha(run/'result.json'), source_events_sha256=sha(run/'events.json'),
        source_sensors_sha256=result['sensors_sha256'], source_responses_sha256=result['responses_sha256'],
        source_model_sha256=sha(model_path),
        actor_source_sha256={p.name: sha(p) for p in Path(__file__).parent.glob('*.py')},
        physical_continuation_executed=False, qualified_carry=False, qualified_paper_branch=False)
    (out/'review.json').write_text(json.dumps(report, indent=2)+'\n')
    if actor.pickup is not None:
        np.savez_compressed(out/'estimated_handoff.npz', robot_estimated_qpos=actor.pickup.d.qpos)
    print(json.dumps({k: report[k] for k in ['passed', 'failure', 'compared_prefix_packets',
        'maximum_prefix_response_error', 'reached_recorded_decision']}), flush=True)
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
