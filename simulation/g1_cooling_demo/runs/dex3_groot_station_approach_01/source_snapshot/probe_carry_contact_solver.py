"""Compare contact solvers from one recorded grasp state and motor sequence.

This is an offline sensitivity diagnostic in the complete room. Controls are
recorded and replayed open loop; changed physics invalidates prior qualification.
No controller receives simulator state. No skill or branch success is awarded.
"""
import argparse
import json
from pathlib import Path
import shutil
import time
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

from build_tool_station import absolve_assets, sha


def local_tool(data):
    wrist = data.body('right_wrist_yaw_link')
    return wrist.xmat.reshape(3, 3).T@(data.body('tweezer').xpos-wrist.xpos)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('recording', type=Path)
    p.add_argument('model_run', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--start', type=float, default=64.)
    p.add_argument('--seconds', type=float, default=2.)
    a = p.parse_args()
    source, run, out = a.recording.resolve(), a.model_run.resolve(), a.output.resolve()
    result = json.loads((source/'result.json').read_text())
    contract = json.loads((run/'contract.json').read_text())
    assert sha(source/'trace.npz') == result['trace_sha256']
    assert sha(run/'contract.json') == result['actor_contract_sha256']
    assert sha(run/'world.xml') == contract['model_sha256']
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, out/Path(__file__).name)
    with np.load(source/'trace.npz') as z:
        times = z['time'].copy()
        first = int(np.argmin(abs(times-a.start)))
        stop = int(np.argmin(abs(times-times[first]-a.seconds)))
        if stop <= first or abs(times[stop]-times[first]-a.seconds) > .0011:
            raise ValueError('Requested interval is not in the source recording')
        q0, v0 = z['qpos'][first].copy(), z['qvel'][first].copy()
        controls = z['ctrl'][first:stop].copy()
        recorded_end = z['qpos'][stop].copy()
        interval = float(np.median(np.diff(times[first:stop+1])))
    rows = []
    for label, cone, ratio in [('source', None, None), ('elliptic_1', 'elliptic', 1.),
                               ('elliptic_10', 'elliptic', 10.)]:
        folder = out/label
        folder.mkdir()
        xml = ET.parse(run/'world.xml').getroot()
        absolve_assets(xml, run/'world.xml')
        if cone:
            xml.find('option').set('cone', cone)
            xml.find('option').set('impratio', str(ratio))
        ET.ElementTree(xml).write(folder/'world.xml', encoding='unicode')
        m = mujoco.MjModel.from_xml_path(str(folder/'world.xml'))
        d = mujoco.MjData(m)
        d.qpos[:], d.qvel[:], d.time = q0, v0, float(times[first])
        mujoco.mj_forward(m, d)
        initial = local_tool(d).copy()
        stride = round(interval/m.opt.timestep)
        assert stride > 0 and abs(stride*m.opt.timestep-interval) < 1e-9
        root = m.body('tweezer').id
        tool_bodies = {root}
        for i in range(m.nbody):
            if m.body_parentid[i] in tool_bodies:
                tool_bodies.add(i)
        fingers = {m.body(n).id: next(f for f in ['thumb', 'index', 'middle'] if f in n)
                   for n in contract['allowed_tool_contact_bodies']}
        samples, start = [], time.monotonic()
        external = False
        for k, control in enumerate(controls):
            d.ctrl[:] = control
            for _ in range(stride):
                mujoco.mj_step(m, d)
                external |= bool(np.any(d.xfrc_applied) or np.any(d.qfrc_applied))
            if k % 10 == 0:
                mujoco.mj_kinematics(m, d)
                force = dict.fromkeys(['thumb', 'index', 'middle'], 0.)
                for ci, c in enumerate(d.contact):
                    bs = set(map(int, m.geom_bodyid[c.geom]))
                    other = bs & fingers.keys()
                    if not (other and bs & tool_bodies):
                        continue
                    f = np.zeros(6)
                    mujoco.mj_contactForce(m, d, ci, f)
                    force[fingers[next(iter(other))]] += float(f[0])
                samples.append(dict(time_s=float(d.time), tool_in_wrist_m=local_tool(d).tolist(),
                                    finger_normal_force_n=force, pelvis_height_m=float(d.qpos[2])))
            if k % 500 == 0:
                print(label, 'seconds', round(k*interval, 3), 'wall', round(time.monotonic()-start, 1), flush=True)
            if np.any(d.warning.number):
                break
        mujoco.mj_kinematics(m, d)
        report = dict(label=label, scope=__doc__, source_model_sha256=contract['model_sha256'],
            model_sha256=sha(folder/'world.xml'), cone=int(m.opt.cone), impratio=float(m.opt.impratio),
            timestep_s=float(m.opt.timestep), source_trace_sha256=result['trace_sha256'],
            start_time_s=float(times[first]), end_time_s=float(d.time),
            initial_warmstart='Zero: source diagnostic trace does not contain warmstart',
            exact_replay_claimed=False, external_force_observed=external,
            warnings=d.warning.number.tolist(), tool_in_wrist_change_m=(local_tool(d)-initial).tolist(),
            final_q_max_difference_from_recorded=float(np.max(abs(d.qpos-recorded_end))),
            final_finger_normal_force_n=samples[-1]['finger_normal_force_n'],
            pelvis_height_m=float(d.qpos[2]), wall_seconds=time.monotonic()-start,
            qualified_carry=False, qualified_paper_branch=False)
        (folder/'samples.json').write_text(json.dumps(samples, indent=2)+'\n')
        (folder/'result.json').write_text(json.dumps(report, indent=2)+'\n')
        rows.append(report)
        print(json.dumps(report), flush=True)
    (out/'comparison.json').write_text(json.dumps(dict(scope=__doc__,
        documentation='https://mujoco.readthedocs.io/en/stable/modeling.html#preventing-slip',
        source_sha256=sha(__file__), variants=rows), indent=2)+'\n')


if __name__ == '__main__':
    main()
