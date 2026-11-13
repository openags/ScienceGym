"""Read native recorded tool shape and rigid-grasp drift; no force/replay credit."""
import json
from pathlib import Path
import sys
import zipfile

import mujoco
import numpy as np

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))
from evaluate_tool_actuation_recording import rows, sha

RUN = BASE / 'runs/dex3_heel_visual_actuation_02'
OUT = Path(__file__).parent
result = json.loads((RUN / 'result.json').read_text())
contract = json.loads((RUN / 'contract.json').read_text())
assert sha(RUN / 'trace.npz') == result['trace_sha256']
assert sha(RUN / 'world.xml') == contract['model_sha256']
assert sha(RUN / 'contract.json') == result['contract_sha256']
changes = [e for e in json.loads((RUN / 'events.json').read_text()) if 'phase' in e]
begin = next(e['time_s'] for e in changes if e['phase'] == 'hold')
end = next(e['time_s'] for e in changes if e['time_s'] > begin and e['phase'] not in
           {'hold', 'tool_squeeze', 'tool_reopen'})
with zipfile.ZipFile(RUN / 'trace.npz') as z:
    times = rows(z, 'time')
    first, stop = np.searchsorted(times, [begin - 1e-8, end - 1e-8])
    q = rows(z, 'qpos', int(first), int(stop))
    times = times[first:stop]
m = mujoco.MjModel.from_xml_path(str(RUN / 'world.xml'))
d, rest = mujoco.MjData(m), mujoco.MjData(m)
rest.qpos[:] = q[0]
tool = {m.body('tweezer').id}
for body in range(m.nbody):
    if m.body_parentid[body] in tool:
        tool.add(body)
for joint in range(m.njnt):
    if m.jnt_bodyid[joint] in tool and m.jnt_type[joint] == mujoco.mjtJoint.mjJNT_HINGE:
        rest.qpos[m.jnt_qposadr[joint]] = 0.
mujoco.mj_kinematics(m, rest)
root = m.body('tweezer').id
endpoints = []
for label, sign in [('negative', -1.), ('positive', 1.)]:
    tip = max((b for b in tool if m.body(b).name.startswith(label + '_beam_')),
              key=lambda b: m.body(b).name)
    point = rest.xpos[root] + rest.xmat[root].reshape(3, 3) @ np.array([-.130, sign * .004, 0.])
    endpoints.append((tip, rest.xmat[tip].reshape(3, 3).T @ (point - rest.xpos[tip])))
phase_times = np.array([e['time_s'] for e in changes])
phase_names = np.array([e['phase'] for e in changes])
phases = phase_names[np.searchsorted(phase_times, times + 1e-8, side='right') - 1]
gaps, poses, rotations = [], [], []
for row in q:
    d.qpos[:] = row
    mujoco.mj_kinematics(m, d)
    tips = [d.xpos[b] + d.xmat[b].reshape(3, 3) @ point for b, point in endpoints]
    gaps.append(float(np.linalg.norm(tips[1] - tips[0])))
    wrist = d.site('right_wrist_reference')
    poses.append(wrist.xmat.reshape(3, 3).T @ (d.body('tweezer').xpos - wrist.xpos))
    rotations.append(wrist.xmat.reshape(3, 3).T @ d.body('tweezer').xmat.reshape(3, 3))
gaps, poses, rotations = np.array(gaps), np.array(poses), np.array(rotations)
drift = np.linalg.norm(poses - poses[0], axis=1)
from scipy.spatial.transform import Rotation
angular = Rotation.from_matrix(rotations @ rotations[0].T).magnitude()
native = OUT / 'native_shape.npz'
np.savez_compressed(native, time_s=times, phase=phases, tip_gap_m=gaps,
                    tool_wrist_translation_m=poses, tool_wrist_rotation=rotations)
measurements = []
for phase in ['hold', 'tool_squeeze', 'tool_reopen']:
    selected = phases == phase
    if not selected.any():
        measurements.append(dict(phase=phase, samples=0))
        continue
    index = np.flatnonzero(selected)[np.argmin(gaps[selected])]
    measurements.append(dict(phase=phase, samples=int(selected.sum()),
        minimum_tip_gap_m=float(gaps[index]), minimum_gap_time_s=float(times[index]),
        maximum_tip_gap_m=float(gaps[selected].max()),
        maximum_translation_drift_m=float(drift[selected].max()),
        maximum_rotation_drift_rad=float(angular[selected].max())))
report = dict(scope=__doc__, source_result_sha256=sha(RUN / 'result.json'),
    source_trace_sha256=result['trace_sha256'], source_contract_sha256=result['contract_sha256'],
    script_sha256=sha(__file__), helper_sha256=sha(BASE / 'evaluate_tool_actuation_recording.py'),
    native_sha256=sha(native), sample_period_s=float(m.opt.timestep), measurements=measurements,
    physical_replay_performed=False, contact_force_evaluated=False,
    qualified_tool_actuation=False, qualified_paper_branch=False)
(OUT / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(measurements), flush=True)
