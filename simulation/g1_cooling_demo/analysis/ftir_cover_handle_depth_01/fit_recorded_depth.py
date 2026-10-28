import json,sys,numpy as np,mujoco
from pathlib import Path
sys.path.insert(0,str(Path('simulation/g1_cooling_demo').resolve()))
from ftir_hand import initialize_cover
from ftir_vision import KeyRowObservation
from ftir_cover_geometry import observe_handle
from observations import StateEstimate
from depth_io import load
b=Path('simulation/g1_cooling_demo/runs/ftir_cover_02');m=mujoco.MjModel.from_xml_path(str((b/'controller_model/world.xml').resolve()));d=initialize_cover(m);estimate=StateEstimate(m,d);vision=KeyRowObservation(m,d)
s=dict(np.load(b/'sensor_observations.npz'));colors=np.load(b/'head_rgb_chunks/000000.npz');prior=json.load(open('assets/nicolet_6700_mechanism_v1/cover_grasp_prior.json'));rows=[]
for time,depth in load(b):
 if time<1.3:continue
 if time>2.001:break
 i=np.argmin(abs(s['time_s']-time));j=np.argmin(abs(colors['time']-time));packet={k:v[i] for k,v in s.items() if k!='right_touch_n'};packet['depth']=depth;estimate.update(packet)
 o=vision.observe(colors['rgb'][j],depth);r=observe_handle(m,d,depth,o,prior) if o.get('accepted') else o
 rows.append(dict(time_s=float(time),**r));print(json.dumps(rows[-1]),flush=True)
out=Path('simulation/g1_cooling_demo/analysis/ftir_cover_handle_depth_01');out.mkdir(exist_ok=False);(out/'predictions.json').write_text(json.dumps(rows,indent=2)+'\n')
# Held-out comparison after predictions are frozen; not fed into fitting.
pm=mujoco.MjModel.from_xml_path(str((b/'world.xml').resolve()));pd=mujoco.MjData(pm);trace=np.load(b/'trace.npz');reviews=[]
for row in rows:
 if not row.get('accepted'):continue
 i=np.argmin(abs(trace['time']-row['time_s']));pd.qpos[:]=trace['qpos'][i];mujoco.mj_forward(pm,pd);error=np.array(row['handle_m'])-pd.site('nicolet_cover_handle').xpos
 reviews.append(dict(time_s=row['time_s'],error_m=error.tolist(),norm_m=float(np.linalg.norm(error))))
(out/'held_out_review.json').write_text(json.dumps(reviews,indent=2)+'\n');print('errors',reviews,flush=True)
