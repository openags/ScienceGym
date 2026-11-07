import json,sys,numpy as np,mujoco
from pathlib import Path
from scipy.spatial.transform import Rotation,Slerp
sys.path.insert(0,str(Path('simulation/g1_cooling_demo').resolve()))
from ftir_cover_actor import CoverActor
b=Path('simulation/g1_cooling_demo/runs/ftir_cover_05');m=mujoco.MjModel.from_xml_path(str((b/'controller_model/world.xml').resolve()));s=np.load(b/'sensor_observations.npz');i=np.argmin(abs(s['time_s']-2));packet={k:s[k][i] for k in s.files if k!='right_touch_n'};packet['depth']=None
obs=[r['observation'] for r in json.load(open(b/'actor_responses.json')) if r['time_s']<=2.001 and r.get('observation') and r['observation'].get('handle_fit',{}).get('accepted')][-8:]
base=json.load(open('assets/nicolet_6700_mechanism_v1/cover_grasp_prior.json'));folder=Path('simulation/g1_cooling_demo/analysis/ftir_cover_pad_grasp_03');candidates=json.load(open(folder/'pad_grasps.json'))['candidates'];rows=[]

rng=np.random.default_rng(846)
for n,c in enumerate(candidates):
 p=dict(base,handle_frame_from_palm=c['handle_frame_from_palm'],nominal_grip_q=c['q']);fn=Path('/tmp/sciencegym-cover-endpoint-prior.json');fn.write_text(json.dumps(p));a=CoverActor(m,[5.95,-5.35],fn);a.estimate.update(packet);a.observations=obs
 try:a.make_plan(2)
 except RuntimeError:pass
 target=a.grip_position+a.front*.06
 best=None
 for j in range(40):
  seed=a.d.qpos[a.ik.qa].copy() if j==0 else rng.uniform(a.ik.low,a.ik.high)
  q,pe,re=a.ik.solve(a.d,target,a.grip_rotation,seed)
  if best is None or pe+.15*re<best['pe']+.15*best['re']:best=dict(pe=pe,re=re,q=q.tolist(),seed=j)
  if pe<.0003 and re<.005:break
 row=dict(candidate=n,best=best);rows.append(row);print(json.dumps(row),flush=True)
(folder/'endpoint_ik.json').write_text(json.dumps(rows,indent=2)+'\n')
