"""Counterfactual collision screen for the new withdrawn-hand viewing angle.

Retained robot joint poses are held while the waist angle is swept. These
static poses are not an executed trajectory or a dynamic-support validation.
"""
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np


HERE=Path(__file__).resolve().parent;BASE=HERE.parents[1]
RUN=BASE/'runs/ftir_approach_08'


def main():
    out=HERE/'view_clearance.json'
    if out.exists():raise FileExistsError(out)
    m=mujoco.MjModel.from_xml_path(str(RUN/'world.xml'));d=mujoco.MjData(m)
    trace=dict(np.load(RUN/'trace.npz'))
    def under(body,name):
        root=m.body(name).id
        while body and body!=root:body=int(m.body_parentid[body])
        return body==root
    robot={g for g in range(m.ngeom) if under(int(m.geom_bodyid[g]),'pelvis')}
    feet={g for g in robot if any(under(int(m.geom_bodyid[g]),s+'_ankle_roll_link') for s in ['left','right'])}
    imported=json.loads((RUN/'laboratory_import.json').read_text())
    floor={m.geom(p['geom']).id for p in imported['parts'] if p['source_part'] in {'indoor_floor','annex_floor','outdoor_floor','outdoor_access_path'}}
    rows=[]
    for t in [220.4,225.5,241.0]:
        index=int(np.argmin(abs(trace['time']-t)))
        for yaw in np.linspace(-.605,-.195,42):
            d.qpos[:]=trace['qpos'][index];d.qvel[:]=0.
            d.joint('waist_yaw_joint').qpos[0]=yaw;mujoco.mj_forward(m,d)
            violations=[]
            for c in d.contact:
                a,b=map(int,c.geom)
                if not {a,b}&robot:continue
                sole=(a in feet and b in floor) or (b in feet and a in floor)
                tolerance=.001 if sole else .00002
                if c.dist < -tolerance:
                    violations.append(dict(parts=[m.geom(a).name,m.geom(b).name],distance_m=float(c.dist),bound_m=tolerance))
            rows.append(dict(retained_time_s=float(trace['time'][index]),waist_yaw_rad=float(yaw),violations=violations))
    report=dict(passed=not any(r['violations'] for r in rows),poses=len(rows),rows=rows,
                source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),RUN/'world.xml',RUN/'trace.npz',RUN/'laboratory_import.json']},scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['passed','poses']}))
    if not report['passed']:raise SystemExit(1)


if __name__=='__main__':main()
