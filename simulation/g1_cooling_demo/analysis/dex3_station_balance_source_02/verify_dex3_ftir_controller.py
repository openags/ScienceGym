"""Replay every frozen isolated Dex3 FTIR response from recorded sensors.

Reproducibility is separate from physical task success. Failed executions may
replay exactly and remain failures.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pickle
import subprocess
import sys

import numpy as np


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def difference(a, b):
    if isinstance(a, dict):
        if not isinstance(b, dict) or set(a) != set(b):
            return float('inf')
        return max([difference(a[k], b[k]) for k in a]+[0.])
    if isinstance(a, (list, tuple)):
        if not isinstance(b, (list, tuple)) or len(a) != len(b):
            return float('inf')
        return max([difference(x, y) for x, y in zip(a, b)]+[0.])
    if isinstance(a, np.ndarray):
        aa, bb = np.asarray(a), np.asarray(b)
        if aa.shape != bb.shape:
            return float('inf')
        if aa.dtype.kind == 'b':
            return 0. if np.array_equal(aa, bb) else float('inf')
        if not np.isfinite(aa).all() or not np.isfinite(bb).all():
            return float('inf')
        return float(np.max(abs(aa.astype(float)-bb.astype(float)), initial=0.))
    if isinstance(a, (float, int, np.number)) and not isinstance(a, bool):
        return abs(float(a)-float(b)) if np.isfinite([a, b]).all() else float('inf')
    return 0. if a == b else float('inf')


def verify(folder):
    folder = Path(folder).resolve()
    result = json.loads((folder/'result.json').read_text())
    contract = json.loads((folder/'contract.json').read_text())
    assert sha(folder/'contract.json') == result['contract_sha256']
    assert sha(folder/'actor_isolation.json') == contract['actor_isolation_sha256']
    assert sha(folder/'policy_source/robot_setup.json') == contract['setup_sha256']
    for name in ['sensors.npz', 'responses.pkl', 'events.json', 'camera_index.json']:
        key = {'sensors.npz':'sensors', 'responses.pkl':'responses', 'events.json':'events',
               'camera_index.json':'camera_index'}[name]+'_sha256'
        assert sha(folder/name) == result[key]
    receipt = json.loads((folder/'actor_isolation.json').read_text())
    assert receipt['passed']
    for name, digest in receipt['source_modules'].items():
        assert sha(folder/'actor_bundle/code'/name) == digest
    assert sha(folder/'actor_bundle/model/world.xml') == receipt['bundled_model_sha256']
    for row in receipt['input_files']:
        assert sha(folder/row['path']) == row['sha256']
    sensor = dict(np.load(folder/'sensors.npz'))
    expected = pickle.loads((folder/'responses.pkl').read_bytes())
    frames = json.loads((folder/'camera_index.json').read_text())
    command = receipt['command_prefix']+[sys.executable, '/actor/dex3_ftir_actor.py',
        '--model', '/model/world.xml', '--setup', '/model/policy/robot_setup.json']
    count = images = 0
    error, event_error, failure, events, actual = 0., None, None, [], {}
    with (folder/'controller_replay_stderr.log').open('w') as stream:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=stream, env=receipt['environment'])
        try:
            for i, response in enumerate(expected):
                packet = {k:v[i] for k, v in sensor.items() if k != 'camera_frame_id'}
                frame_id = int(sensor['camera_frame_id'][i])
                packet.update(rgb=None, depth=None)
                if frame_id >= 0:
                    entry = frames[frame_id]
                    assert entry['id'] == frame_id and abs(entry['time_s']-float(packet['time_s'])) < 1e-8
                    assert sha(folder/entry['file']) == entry['sha256']
                    with np.load(folder/entry['file']) as frame:
                        packet.update(rgb=frame['rgb'], depth=frame['depth'])
                    images += 1
                pickle.dump(packet, process.stdin, protocol=5)
                process.stdin.flush()
                actual = pickle.load(process.stdout)
                events = actual.get('events', events)
                error = max(error, difference(response, {k:v for k, v in actual.items() if k != 'events'}))
                count += 1
                if actual['error']:
                    break
            event_error = difference(json.loads((folder/'events.json').read_text()), events)
            error = max(error, event_error)
        except Exception as exc:
            failure = type(exc).__name__+': '+str(exc)
        finally:
            process.stdin.close()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    passed = failure is None and count == len(expected) == len(sensor['time_s']) and error < 1e-10 and images == len(frames)>0
    report = dict(scope=__doc__, passed=passed, failure=failure,
        responses_compared=count, sensor_packets=len(sensor['time_s']), camera_frames_replayed=images,
        maximum_response_error=error if np.isfinite(error) else None,
        event_history_error=event_error if event_error is not None and np.isfinite(event_error) else None,
        recorded_execution_failure=result['failure'], recorded_actor_error=actual.get('error'),
        source_result_sha256=sha(folder/'result.json'), verifier_sha256=sha(__file__),
        qualified_ftir_press=False, qualified_paper_branch=False)
    (folder/'controller_replay.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder')
    a = p.parse_args()
    if not verify(a.folder)['passed']:
        raise SystemExit(1)
