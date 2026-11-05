"""Compare CCD on every retained native state before a recorded tool lift.

Each state is explicitly restored for offline attribution. This is not a new
continuous trajectory or carrying qualification. The original case must match
the recorded next states before differences between collision options are used.
All geometry, motor commands, contact parameters and force bounds are retained.
"""
import argparse
import json
from pathlib import Path
import shutil
import time

import mujoco
import numpy as np

from frozen_collision_plugins import sha

SCRIPT_SHA256 = sha(__file__)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    run,out=a.run.resolve(),a.output.resolve()
    result=json.loads((run/'result.json').read_text())
    contract=json.loads((run/'contract.json').read_text())
    assert sha(run/'contract.json')==result['contract_sha256']
    assert sha(run/'world.xml')==contract['model_sha256']
    assert sha(run/'trace.npz')==result['trace_sha256']
    events=json.loads((run/'events.json').read_text())
    lift=next(e['time_s'] for e in events if e.get('phase')=='lift')
    with np.load(run/'trace.npz') as z:
        times=z['time'];idx=np.flatnonzero((times>=lift-.5)&(times<lift))
        first,last=int(idx[0]),int(idx[-1])+1
        trace={k:z[k][first:last+1].copy() for k in ['time','qpos','qvel','qacc_warmstart','ctrl']}
    out.mkdir(parents=True,exist_ok=False)
    for path in [Path(__file__),Path(__file__).with_name('frozen_collision_plugins.py')]:
        shutil.copyfile(path,out/path.name)
    rows=[]
    for variant in ['original','tight_native','single_contact_native','legacy_ccd']:
        m=mujoco.MjModel.from_xml_path(str(run/'world.xml'))
        if variant=='tight_native':m.opt.ccd_tolerance=1e-10;m.opt.ccd_iterations=1000
        elif variant=='single_contact_native':m.opt.disableflags|=int(mujoco.mjtDisableBit.mjDSBL_MULTICCD)
        elif variant=='legacy_ccd':m.opt.disableflags|=int(mujoco.mjtDisableBit.mjDSBL_NATIVECCD)
        d=mujoco.MjData(m)
        tool={m.body('tweezer').id}
        for b in range(m.nbody):
            if m.body_parentid[b] in tool:tool.add(b)
        allowed={m.body(n).id for n in contract['allowed_tool_contact_bodies']}
        thresholds=np.array([contract['physical_acceptance'][n] for n in
            ['minimum_thumb_load_n','minimum_each_opposing_finger_load_n','minimum_each_opposing_finger_load_n']])
        forces=[];losses=[];qerror=verror=0.;started=time.monotonic()
        for i in range(len(trace['time'])-1):
            d.qpos[:],d.qvel[:],d.time=trace['qpos'][i],trace['qvel'][i],float(trace['time'][i])
            d.ctrl[:]=trace['ctrl'][i];mujoco.mj_forward(m,d);d.qacc_warmstart[:]=trace['qacc_warmstart'][i]
            mujoco.mj_step(m,d)
            qerror=max(qerror,float(np.max(abs(d.qpos-trace['qpos'][i+1]))))
            verror=max(verror,float(np.max(abs(d.qvel-trace['qvel'][i+1]))))
            values=np.zeros(3);contacts=[]
            for ci,c in enumerate(d.contact):
                bodies=set(map(int,m.geom_bodyid[c.geom]))
                if not (bodies&tool and bodies&allowed):continue
                name=m.body(next(iter(bodies&allowed))).name
                finger=next(k for k,n in enumerate(['thumb','index','middle']) if n in name)
                wrench=np.zeros(6);mujoco.mj_contactForce(m,d,ci,wrench);values[finger]+=max(0.,float(wrench[0]))
                contacts.append(dict(finger=finger,parts=[m.geom(int(g)).name for g in c.geom],
                    distance_m=float(c.dist),normal_force_n=float(wrench[0]),normal=c.frame[:3].tolist()))
            forces.append(values)
            if np.any(values<=thresholds):losses.append(dict(time_s=float(trace['time'][i]),force_n=values.tolist(),contacts=contacts))
        np.savez_compressed(out/(variant+'.npz'),time_s=trace['time'][:-1],force_n=forces)
        row=dict(variant=variant,samples=len(forces),lost_samples=len(losses),lost_steps=losses,
            maximum_next_q_error=qerror,maximum_next_v_error=verror,warning_counts=d.warning.number.tolist(),
            ccd_tolerance_m=float(m.opt.ccd_tolerance),ccd_iterations=int(m.opt.ccd_iterations),
            disableflags=int(m.opt.disableflags),wall_seconds=time.monotonic()-started)
        rows.append(row)
        report=dict(scope=__doc__,script_sha256=SCRIPT_SHA256,source_result_sha256=sha(run/'result.json'),
            source_contract_sha256=sha(run/'contract.json'),first_lift_time_s=lift,cases=rows,
            baseline_matches_recording=rows[0]['maximum_next_q_error']<=1e-10 and rows[0]['maximum_next_v_error']<=1e-7,
            complete=len(rows)==4,qualified_carry=False,qualified_robot_handling=False)
        (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:v for k,v in row.items() if k!='lost_steps'}),flush=True)


if __name__=='__main__':main()
