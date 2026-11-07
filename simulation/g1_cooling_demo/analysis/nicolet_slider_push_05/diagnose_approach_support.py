"""Locate early support minima in a retained trial without changing its review."""
import argparse
import hashlib
import json
from pathlib import Path
import mujoco
import numpy as np


def main(folder, output):
    folder, output = Path(folder), Path(output)
    if output.exists():
        raise FileExistsError(output)
    trace = dict(np.load(folder/'trace.npz'))
    m = mujoco.MjModel.from_xml_path(str((folder/'world.xml').resolve()))
    d = mujoco.MjData(m)
    d.qpos[:] = trace['qpos'][0]
    d.qvel[:] = trace['qvel'][0]
    mujoco.mj_forward(m,d)
    d.qacc_warmstart[:] = trace['qacc_warmstart'][0]
    imported = json.loads((folder/'laboratory_import.json').read_text())
    floors = {m.geom(p['geom']).id for p in imported['parts'] if p['source_part'] in
              {'indoor_floor','annex_floor','outdoor_floor','outdoor_access_path'}}
    feet = set()
    for g in range(m.ngeom):
        body = int(m.geom_bodyid[g])
        while body:
            if m.body(body).name in {'left_ankle_roll_link','right_ankle_roll_link'}:
                feet.add(g)
                break
            body = int(m.body_parentid[body])
    rows=[]
    max_error=0.
    for i,t in enumerate(trace['time'][:-1]):
        if t>7.:
            break
        max_error=max(max_error,float(np.max(abs(d.qpos-trace['qpos'][i]))))
        d.ctrl[:]=trace['ctrl'][i]
        mujoco.mj_step(m,d)
        load=0.
        for j,c in enumerate(d.contact):
            a,b=map(int,c.geom)
            if (a in feet and b in floors) or (b in feet and a in floors):
                force=np.zeros(6)
                mujoco.mj_contactForce(m,d,j,force)
                load+=abs(float(force[0]))
        if t>.5:
            rows.append(dict(time_s=float(t),sole_normal_load_n=load,root_height_m=float(trace['qpos'][i,2]),
                             vertical_velocity_m_s=float(trace['qvel'][i,2])))
    low=[r for r in rows if r['sole_normal_load_n']<=100.]
    joints=[]
    for j in range(m.njnt):
        if m.jnt_limited[j]:
            q=trace['qpos'][:,m.jnt_qposadr[j]]
            lo,hi=m.jnt_range[j]
            excess=np.maximum(lo-q,q-hi)
            i=int(np.argmax(excess))
            if excess[i]>.005:
                joints.append(dict(joint=m.joint(j).name,time_s=float(trace['time'][i]),excess_rad=float(excess[i])))
    report=dict(minimum_support=min(rows,key=lambda r:r['sole_normal_load_n']),
                below_existing_100n_bound=low,below_bound_duration_s=len(low)*m.opt.timestep,
                joint_limit_excursions=joints,maximum_prefix_position_replay_error=max_error,
                trace_sha256=hashlib.sha256((folder/'trace.npz').read_bytes()).hexdigest(),
                reviewer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                scope='Evaluator-only diagnosis of first seven seconds. Original failed review and all acceptance criteria unchanged.')
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='below_existing_100n_bound'}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');p.add_argument('output');a=p.parse_args()
    main(a.folder,a.output)
