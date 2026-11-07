"""Inspect selected recorded tool configurations without claiming native replay.

Only geometry at recorded poses is measured. Contact forces, dynamic continuity
and task success require the independent full recording evaluator.
"""
import argparse
import json
from pathlib import Path
import shutil
import zipfile

import mujoco
import numpy as np

from evaluate_tool_actuation_recording import rows, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('run', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--time', type=float, nargs='+', required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    result = json.loads((a.run/'result.json').read_text())
    events = json.loads((a.run/'events.json').read_text())
    start = next(e['time_s'] for e in events if e.get('phase') == 'hold')
    requested = sorted(set([start, *a.time]))
    if sha(a.run/'trace.npz') != result['trace_sha256']:
        raise ValueError('Recorded trace digest changed')
    with zipfile.ZipFile(a.run/'trace.npz') as archive:
        times = rows(archive, 'time')
        indices = [int(np.argmin(abs(times-t))) for t in requested]
        with archive.open('qpos.npy') as stream:
            version = np.lib.format.read_magic(stream)
            reader = {(1, 0): np.lib.format.read_array_header_1_0,
                      (2, 0): np.lib.format.read_array_header_2_0}[version]
            shape, fortran, dtype = reader(stream)
            assert len(shape) == 2 and not fortran and not dtype.hasobject
            row_bytes = shape[1]*dtype.itemsize
            cursor, states = 0, []
            for i in indices:
                stream.seek((i-cursor)*row_bytes, 1)
                states.append(np.frombuffer(stream.read(row_bytes), dtype=dtype).copy())
                cursor = i+1
    m = mujoco.MjModel.from_xml_path(str(a.run/'world.xml'))
    d = mujoco.MjData(m)
    d.qpos[:] = states[0]
    tool = {m.body('tweezer').id}
    for b in range(m.nbody):
        if int(m.body_parentid[b]) in tool:
            tool.add(b)
    for j in range(m.njnt):
        if int(m.jnt_bodyid[j]) in tool and m.jnt_type[j] == mujoco.mjtJoint.mjJNT_HINGE:
            d.qpos[m.jnt_qposadr[j]] = 0.
    mujoco.mj_kinematics(m, d)
    root = m.body('tweezer').id
    endpoints = []
    for label, sign in [('negative', -1.), ('positive', 1.)]:
        tip = max((b for b in tool if m.body(b).name.startswith(label+'_beam_')),
                  key=lambda b: m.body(b).name)
        point = d.xpos[root]+d.xmat[root].reshape(3, 3) @ np.array([-.130, sign*.004, 0.])
        endpoints.append((tip, d.xmat[tip].reshape(3, 3).T @ (point-d.xpos[tip])))
    samples, reference = [], None
    for i, q in zip(indices, states):
        d.qpos[:] = q
        mujoco.mj_kinematics(m, d)
        tips = [d.xpos[b]+d.xmat[b].reshape(3, 3)@v for b, v in endpoints]
        wrist = d.site('right_wrist_reference')
        position = wrist.xmat.reshape(3, 3).T@(d.xpos[root]-wrist.xpos)
        if reference is None:
            reference = position.copy()
        samples.append(dict(time_s=float(times[i]), tip_gap_m=float(np.linalg.norm(tips[1]-tips[0])),
            tool_wrist_drift_m=float(np.linalg.norm(position-reference))))
    report = dict(scope=__doc__, source_result_sha256=sha(a.run/'result.json'),
        trace_sha256=result['trace_sha256'], model_sha256=sha(a.run/'world.xml'),
        source_sha256=sha(__file__), samples=samples, physical_replay=False,
        qualified_tool_actuation=False)
    shutil.copyfile(__file__, a.output/Path(__file__).name)
    (a.output/'review.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
