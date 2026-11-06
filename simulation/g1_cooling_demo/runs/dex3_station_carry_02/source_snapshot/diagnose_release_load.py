"""Attribute sparse recorded release loads to native contacts and constraints.

This offline diagnostic may read plant state. It supplies no actor input and
does not replace continuous replay or independent manipulation acceptance.
"""
import argparse
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from build_tool_station import sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('recording', type=Path)
    p.add_argument('model_run', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--times', type=float, nargs='+', required=True)
    a = p.parse_args()
    result = json.loads((a.recording/'result.json').read_text())
    contract = json.loads((a.model_run/'contract.json').read_text())
    assert sha(a.recording/'trace.npz') == result['trace_sha256']
    assert sha(a.model_run/'world.xml') == contract['model_sha256']
    if a.recording.resolve() != a.model_run.resolve():
        assert sha(a.model_run/'contract.json') == result['actor_contract_sha256']
    a.output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, a.output/Path(__file__).name)
    m = mujoco.MjModel.from_xml_path(str((a.model_run/'world.xml').resolve()))
    d = mujoco.MjData(m)
    z = dict(np.load(a.recording/'trace.npz'))
    prior = json.loads((a.model_run/'policy_source/tool_prior.json').read_text())
    drivers = prior['closing_drivers']
    hand = {b for b in range(m.nbody) if m.body(b).name.startswith('right_hand_')}
    rows = []
    for t in a.times:
        if not z['time'][0] <= t <= z['time'][-1]:
            raise ValueError('Requested state is outside the recorded trace')
        i = int(np.argmin(abs(z['time']-t)))
        d.qpos[:] = z['qpos'][i]
        d.qvel[:] = z['qvel'][i]
        d.ctrl[:] = z['ctrl'][i]
        d.qacc_warmstart[:] = z['qacc_warmstart'][i] if 'qacc_warmstart' in z else 0.
        mujoco.mj_forward(m, d)
        contacts = []
        for ci, c in enumerate(d.contact):
            bs = [int(m.geom_bodyid[g]) for g in c.geom]
            if not hand.intersection(bs):
                continue
            force = np.zeros(6)
            mujoco.mj_contactForce(m, d, ci, force)
            contacts.append(dict(bodies=[m.body(b).name for b in bs],
                geoms=[m.geom(g).name for g in c.geom], distance_m=float(c.dist),
                force_contact_frame=force.tolist(), position_m=c.pos.tolist()))
        joints = {}
        for name in drivers:
            j = m.joint(name)
            dof = int(j.dofadr[0])
            joints[name] = dict(position_rad=float(d.qpos[j.qposadr[0]]),
                velocity_rad_s=float(d.qvel[dof]), source_range_rad=j.range.tolist(),
                native_constraint_torque_nm=float(d.qfrc_constraint[dof]))
        rows.append(dict(time_s=float(z['time'][i]), contacts=contacts, closing_joints=joints))
    report = dict(scope=__doc__, trace_sha256=result['trace_sha256'],
        model_sha256=contract['model_sha256'], script_sha256=sha(__file__),
        recorded_warmstart_available='qacc_warmstart' in z, rows=rows,
        continuous_replay=False, qualification=False)
    (a.output/'review.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
