"""Replay a failed controller's sensor record and retain its rejected balance QP.

Only the original observations enter the isolated actor. An optional candidate
must reproduce every previously accepted response before resolving the last
failed packet. No motor output is applied and no physical execution is claimed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pickle
import shutil
import subprocess
import sys
import time

import numpy as np

from verify_tool_grasp import difference


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recording', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--actor-run', type=Path)
    a = parser.parse_args()
    source, out = a.recording.resolve(), a.output.resolve()
    actor = a.actor_run.resolve() if a.actor_run else source
    result = json.loads((source/'result.json').read_text())
    contract = json.loads((actor/'contract.json').read_text())
    isolation = json.loads((actor/'actor_isolation.json').read_text())
    assert isolation['passed'] and 'Conic balance QP rejected' in result['failure']
    assert sha(source/'sensors.npz') == result['sensors_sha256']
    assert sha(source/'responses.pkl') == result['responses_sha256']
    assert contract['model_sha256'] == json.loads((source/'contract.json').read_text())['model_sha256']
    for name, digest in isolation['source_modules'].items():
        assert sha(actor/'actor_bundle/code'/name) == digest
    sensors = dict(np.load(source/'sensors.npz'))
    responses = pickle.loads((source/'responses.pkl').read_bytes())
    frames = json.loads((source/'camera_index.json').read_text())
    assert len(responses) == len(sensors['time_s'])
    assert responses[-1]['error'] and not any(r['error'] for r in responses[:-1])
    wrapper = Path(__file__).with_name('capture_balance_failure.py')
    out.mkdir(parents=True, exist_ok=False)
    for path in [Path(__file__), wrapper, Path(__file__).with_name('verify_tool_grasp.py')]:
        shutil.copyfile(path, out/path.name)
    name = contract['actor_module']
    assert name in {'carry_tool_actor', 'visual_tool_actor', 'inspection_tool_actor'}
    command = isolation['command_prefix'] + [sys.executable, '-c', wrapper.read_text(),
        '--diagnostic-actor', name, '--model', '/model/world.xml']
    report = dict(scope=__doc__, source_result_sha256=sha(source/'result.json'),
        actor_contract_sha256=sha(actor/'contract.json'), source_sensors_sha256=result['sensors_sha256'],
        script_sha256=sha(__file__), diagnostic_wrapper_sha256=sha(wrapper),
        physical_execution=False, qualified_carry=False, candidate_actor=actor != source)
    started = time.monotonic(); maximum_error = 0.; failure = None
    with (out/'actor_stderr.log').open('wb') as log:
        child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=log, env=isolation['environment'])
        try:
            for i, recorded in enumerate(responses):
                packet = {k: v[i] for k, v in sensors.items()}
                frame = int(packet.pop('camera_frame_id'))
                packet.update(head_rgb=None, head_depth=None)
                if frame >= 0:
                    info = frames[frame]; path = source/info['file']
                    assert sha(path) == info['sha256']
                    with np.load(path) as data:
                        packet.update({k: data[k] for k in data.files})
                pickle.dump(packet, child.stdin, protocol=5); child.stdin.flush()
                response = pickle.load(child.stdout)
                if not recorded['error']:
                    assert response.get('error') is None, 'Candidate failed before original rejection'
                    error = difference(recorded, {k: response[k] for k in recorded})
                    maximum_error = max(maximum_error, error)
                    assert error <= 1e-10, 'Candidate changed the accepted prefix at '+str(i)
                else:
                    report.update(prefix_packets_replayed=i, maximum_prefix_response_error=maximum_error,
                        rejection_time_s=float(packet['time_s']), original_failure=recorded['error'],
                        candidate_failure=response.get('error'),
                        rejected_packet_resolved=response.get('error') is None)
                    problem = response.pop('diagnostic_balance_problem', None)
                    if problem is not None:
                        path = out/'rejected_balance_problem.npz'
                        np.savez_compressed(path, **problem)
                        report['rejected_balance_problem'] = dict(file=path.name, sha256=sha(path))
                    if actor == source:
                        assert response.get('error') == recorded['error']
                        assert problem is not None, 'Expected rejected QP was not captured'
                        report['original_rejection_reproduced'] = True
                    else:
                        assert response.get('error') is None, 'Candidate still rejects the packet'
                        assert np.isfinite(response['torque']).all()
                        path = out/'candidate_final_response.pkl'
                        path.write_bytes(pickle.dumps(response, protocol=5))
                        report['candidate_final_response_sha256'] = sha(path)
                if i % 10000 == 0:
                    print('sensor_packets', i, 'of', len(responses), 'wall_s', round(time.monotonic()-started, 1), flush=True)
        except Exception as error:
            failure = type(error).__name__+': '+str(error)
        finally:
            child.stdin.close()
            try: child.wait(timeout=15)
            except subprocess.TimeoutExpired: child.kill(); child.wait()
    report.update(failure=failure, wall_seconds=time.monotonic()-started)
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)
    if failure: raise SystemExit(1)


if __name__ == '__main__':
    main()
