"""Hypothetical nearby stance reach screen using previously observed features.

Recorded encoders/IMU initialize the posture; robot map XY is varied explicitly.
This is kinematic planning, not a new camera observation or executed walking.
"""
import json,sys,itertools,numpy as np,mujoco
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'simulation/g1_cooling_demo'))
from ftir_cover_actor import CoverActor
run=ROOT/'simulation/g1_cooling_demo/runs/ftir_cover_09'
m=mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'));s=np.load(run/'sensor_observations.npz');i=np.argmin(abs(s['time_s']-2))
packet={k:s[k][i] for k in s.files if k!='right_touch_n'};packet['depth']=None
obs=[r['observation'] for r in json.load(open(run/'actor_responses.json')) if r['time_s']<=2.001 and r.get('observation') and r['observation'].get('handle_fit',{}).get('accepted')][-8:]
deltas=sorted(itertools.product([-.09,-.06,-.03,0.,.03,.06,.09],repeat=2),key=lambda p:np.linalg.norm(p))
rows=[]
for delta in deltas:
 xy=np.array([5.95,-5.35])+delta;a=CoverActor(m,xy,HERE/'priors/00.json');a.estimate.update(packet);a.observations=obs
 try:a.make_plan(2);row=dict(delta_xy_m=list(delta),xy_m=xy.tolist(),passed=True,event=a.events[-1])
 except Exception as error:row=dict(delta_xy_m=list(delta),xy_m=xy.tolist(),passed=False,error=str(error))
 rows.append(row);print(json.dumps({k:v for k,v in row.items() if k!='event'}),flush=True)
 if sum(r['passed'] for r in rows)>=4:break
(HERE/'stance_review.json').write_text(json.dumps(dict(scope=__doc__,rows=rows,qualified=False),indent=2)+'\n')
