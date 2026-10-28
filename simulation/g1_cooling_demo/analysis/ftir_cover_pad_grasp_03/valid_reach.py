import json,sys,numpy as np,mujoco
from pathlib import Path
from scipy.spatial.transform import Rotation,Slerp
sys.path.insert(0,str(Path('simulation/g1_cooling_demo').resolve()))
from ftir_cover_actor import CoverActor
b=Path('simulation/g1_cooling_demo/runs/ftir_cover_05');m=mujoco.MjModel.from_xml_path(str((b/'controller_model/world.xml').resolve()));s=np.load(b/'sensor_observations.npz');i=np.argmin(abs(s['time_s']-2));packet={k:s[k][i] for k in s.files if k!='right_touch_n'};packet['depth']=None
obs=[r['observation'] for r in json.load(open(b/'actor_responses.json')) if r['time_s']<=2.001 and r.get('observation') and r['observation'].get('handle_fit',{}).get('accepted')][-8:]
base=json.load(open('assets/nicolet_6700_mechanism_v1/cover_grasp_prior.json'));folder=Path('simulation/g1_cooling_demo/analysis/ftir_cover_pad_grasp_03');candidates=json.load(open(folder/'pad_grasps.json'))['candidates'];rows=[]
profiles=[(.06,0),(.06,.06),(.10,.08),(.03,.08),(.12,.12),(0.,.12),(0.,.2),(.03,.15),(-.01,.1)]
for n,c in enumerate(candidates):
 p=dict(base,handle_frame_from_palm=c['handle_frame_from_palm'],nominal_grip_q=c['q']);fn=Path('/tmp/sciencegym-cover-valid-prior.json');fn.write_text(json.dumps(p));a=CoverActor(m,[5.95,-5.35],fn);a.estimate.update(packet);a.observations=obs
 try:a.make_plan(2)
 except RuntimeError:pass
 for standoff,height in profiles:
  plan=list(a.plan);old=plan[1];plan[1]=(old[0],old[1],a.grip_position+a.front*standoff+np.array([0,0,height]),*old[3:])
  seed=a.d.qpos[a.ik.qa].copy();prev,pr=a.initial,a.initial_R;failure=None;maxerr=[0.,0.]
  for name,_,goal,rot,_ in plan:
   rotations=Slerp([0,1],Rotation.from_matrix([pr,rot]))
   for u in np.linspace(0,1,51):
    v=u*u*(3-2*u);t,R=a.arc(v) if name=='lift' else (prev+v*(goal-prev),rotations([v]).as_matrix()[0]);seed,pe,re=a.ik.solve(a.d,t,R,seed);maxerr=[max(maxerr[0],pe),max(maxerr[1],re)]
    if pe>.003 or re>.035:failure=dict(phase=name,u=float(u),pe=pe,re=re);break
   if failure:break
   prev,pr=goal,rot
  row=dict(candidate=n,standoff_m=standoff,height_m=height,passed=failure is None,failure=failure,maximum_errors=maxerr);rows.append(row)
  if failure is None:print(json.dumps(row),flush=True)
 print('screened',n,'passes',sum(x['passed'] for x in rows),flush=True)
(folder/'approach_profiles.json').write_text(json.dumps(rows,indent=2)+'\n')
