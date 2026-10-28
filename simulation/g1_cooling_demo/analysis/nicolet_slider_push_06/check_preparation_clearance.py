"""Counterfactual preparation-space screen; no executed movement credit."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
import mujoco
import numpy as np

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
sys.path.insert(0,str(BASE))
from ftir_hand import mimic
from ftir_slider_posture import initialize_slider
from walking_actor import SDK_JOINTS


def main():
    output=HERE/'preparation_clearance.json'
    if output.exists():raise FileExistsError(output)
    source=BASE/'runs/ftir_approach_06'
    m=mujoco.MjModel.from_xml_path(str(source/'world.xml'))
    d=mujoco.MjData(m)
    initial=np.array(json.loads((source/'staging.json').read_text())['initial_qpos'])
    target=initialize_slider(m).qpos.copy()
    upper=[int(m.joint(name).qposadr[0]) for name in SDK_JOINTS[12:]]
    imported=json.loads((source/'laboratory_import.json').read_text())
    labels={p['geom']:p['source_part'] for p in imported['parts']}
    floors={m.geom(p['geom']).id for p in imported['parts'] if p['source_part'] in {'indoor_floor','annex_floor','outdoor_floor','outdoor_access_path'}}
    def under(body,root):
        root=m.body(root).id
        while body and body!=root:body=int(m.body_parentid[body])
        return body==root
    robot={g for g in range(m.ngeom) if under(int(m.geom_bodyid[g]),'pelvis')}
    feet={g for g in robot if any(under(int(m.geom_bodyid[g]),s+'_ankle_roll_link') for s in ['left','right'])}
    candidates=[]
    for x in [5.65,5.70,5.75,5.80,5.85,5.90,5.95]:
        pairs={}
        for u in np.linspace(0,1,101):
            d.qpos[:]=initial
            d.qpos[:2]=[x,-5.2]
            d.qpos[upper]=initial[upper]+u*(target[upper]-initial[upper])
            mimic(m,d);mujoco.mj_forward(m,d)
            for c in d.contact:
                a,b=map(int,c.geom)
                if c.dist>=-.00002 or not ({a,b}&robot):continue
                if (a in feet and b in floors) or (b in feet and a in floors):continue
                names=tuple(sorted([m.geom(a).name,m.geom(b).name]))
                row=pairs.setdefault(names,dict(first_fraction=float(u),minimum_distance_m=0.))
                row['minimum_distance_m']=min(row['minimum_distance_m'],float(c.dist))
        candidates.append(dict(root_xy_m=[x,-5.2],sampled_preparation_clear=not pairs,
                               contacts=[dict(parts=list(names),source_parts=[labels.get(n,n) for n in names],**v) for names,v in pairs.items()]))
    report=dict(candidates=candidates,poses_per_candidate=101,
                scope='Authored geometry screen with nominal legs and raised forearms. Actual walking stance, deformation, tracking and reach still need execution; this is not acceptance evidence.',
                source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),source/'world.xml',source/'staging.json',BASE/'ftir_hand.py',BASE/'ftir_slider_posture.py']})
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps([dict(root_xy_m=r['root_xy_m'],clear=r['sampled_preparation_clear'],contact_pairs=len(r['contacts'])) for r in candidates]),flush=True)


if __name__=='__main__':main()
