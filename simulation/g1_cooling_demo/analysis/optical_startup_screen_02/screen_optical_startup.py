"""Check a short coupon startup against the unchanged tool-run contact bound.

Uses an existing standing motor-command prefix in the complete laboratory.
This is a bounded asset diagnostic, not a complete support or robot-operation
qualification. The full three-second support review remains required.
"""
import argparse
import json
from pathlib import Path
import shutil
import time

import mujoco
import numpy as np

from frozen_collision_plugins import load, sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('scene',type=Path);p.add_argument('baseline',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();scene,baseline,out=[v.resolve() for v in [a.scene,a.baseline,a.output]]
    binding=json.loads((scene/'binding.json').read_text())
    state=json.loads((scene/'initial_state.json').read_text())
    result=json.loads((baseline/'result.json').read_text())
    contract=json.loads((baseline/'contract.json').read_text())
    assert sha(scene/'world.xml')==binding['world_sha256']
    assert sha(scene/'initial_state.json')==binding['initial_state_sha256']
    assert sha(baseline/'trace.npz')==result['trace_sha256']
    assert sha(baseline/'contract.json')==result['contract_sha256']
    loader=Path(__file__).with_name('frozen_collision_plugins.py')
    load(binding['collision_plugins'],sha(loader))
    m=mujoco.MjModel.from_xml_path(str(scene/'world.xml'));d=mujoco.MjData(m)
    d.qpos[:],d.qvel[:]=state['qpos'],state['qvel'];mujoco.mj_forward(m,d)
    out.mkdir(parents=True,exist_ok=False)
    for path in [Path(__file__),loader]:shutil.copyfile(path,out/path.name)
    steps=round(.15/m.opt.timestep)
    with np.load(baseline/'trace.npz') as z:commands=z['ctrl'][:steps].copy()
    specimen=m.body('optical_witness_white').id;tray=m.body('carrier_tray').id
    bound=contract['physical_acceptance']['maximum_other_penetration_m']
    maximum=0.;load_maximum=0.;other=set();paint=False;rows=[];started=time.monotonic()
    for i,control in enumerate(commands):
        d.ctrl[:]=control;mujoco.mj_step(m,d)
        for ci,c in enumerate(d.contact):
            bodies=m.geom_bodyid[c.geom]
            if specimen not in bodies:continue
            maximum=max(maximum,-float(c.dist))
            if tray not in bodies:other.update(m.body(int(b)).name for b in bodies if b!=specimen)
            own=int(c.geom[0] if bodies[0]==specimen else c.geom[1])
            f=np.zeros(6);mujoco.mj_contactForce(m,d,ci,f);load_maximum=max(load_maximum,float(f[0]))
            if f[0]>1e-8 and 'paint' in m.geom(own).name:paint=True
        if i%10==0:rows.append((float(d.time),d.qpos.copy(),d.qvel.copy()))
        if i%500==0:print('startup',float(d.time),'wall_s',time.monotonic()-started,flush=True)
    checks=dict(unchanged_contact_bound=maximum<=bound,only_tray_support=not other,
        no_optical_face_contact=not paint,no_numerical_warnings=not np.any(d.warning.number),
        no_external_forces=not np.any(d.xfrc_applied) and not np.any(d.qfrc_applied))
    np.savez_compressed(out/'trace.npz',time=np.asarray([r[0] for r in rows]),
        qpos=np.asarray([r[1] for r in rows]),qvel=np.asarray([r[2] for r in rows]))
    report=dict(scope=__doc__,passed_startup_screen=bool(all(checks.values())),
        checks={k:bool(v) for k,v in checks.items()},simulated_seconds=float(d.time),
        maximum_specimen_penetration_m=maximum,unchanged_bound_m=bound,maximum_contact_load_n=load_maximum,
        other_contact_bodies=sorted(other),binding_sha256=sha(scene/'binding.json'),world_sha256=binding['world_sha256'],
        initial_state_sha256=binding['initial_state_sha256'],baseline_result_sha256=sha(baseline/'result.json'),
        trace_sha256=sha(out/'trace.npz'),source_sha256={p.name:sha(p) for p in out.glob('*.py')},
        passed_asset_support=False,qualified_robot_handling=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
    if not report['passed_startup_screen']:raise SystemExit(1)


if __name__=='__main__':main()
