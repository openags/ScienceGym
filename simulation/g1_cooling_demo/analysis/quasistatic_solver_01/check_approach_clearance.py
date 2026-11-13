"""Screen the measured short-step body envelope along the declared approach.

This is evaluator-side counterfactual geometry, not a new executed walk and
not information supplied to the sensor controller.
"""
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np

HERE=Path(__file__).resolve().parent;BASE=HERE.parents[1]


def main():
    output=HERE/'approach_clearance.json'
    if output.exists():raise FileExistsError(output)
    source=BASE/'runs/ftir_approach_06'
    probe=BASE/'analysis/quasistatic_walk_08'
    trace=dict(np.load(probe/'trace.npz'))
    m=mujoco.MjModel.from_xml_path(str(source/'world.xml'));d=mujoco.MjData(m)
    imported=json.loads((source/'laboratory_import.json').read_text())
    def under(body,name):
        root=m.body(name).id
        while body and body!=root:body=int(m.body_parentid[body])
        return body==root
    robot={g for g in range(m.ngeom) if under(int(m.geom_bodyid[g]),'pelvis')}
    feet={g for g in robot if any(under(int(m.geom_bodyid[g]),s+'_ankle_roll_link') for s in ['left','right'])}
    floors={m.geom(p['geom']).id for p in imported['parts'] if p['source_part'] in {'indoor_floor','annex_floor','outdoor_floor','outdoor_access_path'}}
    contacts={};count=0
    for offset in np.linspace(0.,.88,9):
        for i in range(0,len(trace['time']),50):
            d.qpos[:]=trace['qpos'][i];d.qpos[0]+=offset;mujoco.mj_forward(m,d);count+=1
            for c in d.contact:
                a,b=map(int,c.geom)
                if c.dist>=-.00002 or not ({a,b}&robot):continue
                if (a in feet and b in floors) or (b in feet and a in floors):continue
                pair=tuple(sorted([m.geom(a).name,m.geom(b).name]))
                row=contacts.setdefault(pair,dict(first_offset_m=float(offset),first_pose_time_s=float(trace['time'][i]),minimum_distance_m=0.))
                row['minimum_distance_m']=min(row['minimum_distance_m'],float(c.dist))
    result=dict(passed=not contacts,sampled_poses=count,root_start_xy_m=[4.95,-5.2],requested_station_xy_m=[5.95,-5.2],
                contacts=[dict(parts=list(k),**v) for k,v in contacts.items()],
                scope='Sampled envelope on translated retained poses, including the station end. No dynamics, exact full-path clearance, sensor isolation or operation credit.',
                hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),probe/'trace.npz',source/'world.xml',source/'laboratory_import.json']})
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    if not result['passed']:raise SystemExit(1)


if __name__=='__main__':main()
