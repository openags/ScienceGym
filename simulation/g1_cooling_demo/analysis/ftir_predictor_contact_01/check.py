"""Check that a compact robot predictor preserves state, IK and motor dynamics.

The physical plant is untouched. The alternative predictor retains the source
robot meshes/kinematics/inertias and disables its unused collision solver.
This is a sampled model/control regression, not an execution qualification.
"""
import json,sys,time,numpy as np,mujoco
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;BASE=ROOT/'simulation/g1_cooling_demo'
sys.path.insert(0,str(BASE))
from ftir_cover_actor import CoverActor
paths=[BASE/'runs/ftir_cover_11/controller_model/world.xml',BASE/'runs/ftir_cover_10/controller_model/world.xml']
models=[mujoco.MjModel.from_xml_path(str(p)) for p in paths]
models[1].opt.disableflags|=int(mujoco.mjtDisableBit.mjDSBL_CONTACT)
for name in ['body_mass','body_inertia','jnt_range','actuator_ctrlrange','eq_data']:
 assert np.array_equal(getattr(models[0],name),getattr(models[1],name)),name
actors=[CoverActor(m,[5.95,-5.32],ROOT/'assets/nicolet_6700_mechanism_v1/cover_grasp_prior.json') for m in models]
s=np.load(BASE/'runs/ftir_cover_10/sensor_observations.npz');rows=[];elapsed=[0.,0.]
for t in [0.,2.,14.5,16.,16.5,17.,17.5,20.,23.,27.]:
 i=np.argmin(abs(s['time_s']-t));packet={k:s[k][i] for k in s.files if k!='right_touch_n'};packet['depth']=None;states=[]
 for n,a in enumerate(actors):
  start=time.monotonic();a.estimate.update(packet);m,d=a.m,a.d;mass=np.zeros((m.nv,m.nv));mujoco.mj_fullM(m,d,mass)
  target=d.site('right_wrist_reference').xpos+np.array([.001,-.001,.001]);rotation=d.site('right_wrist_reference').xmat.reshape(3,3).copy()
  ik,pe,re=a.ik.solve(d,target,rotation,d.qpos[a.ik.qa]);a.balance.palm_rotations={'right':rotation}
  torque=a.balance.torque(targets={'right':target},posture=a.original_posture,dt=.01,contact_forces={'right':np.array([3.,1.,4.])})
  states.append(dict(qpos=d.qpos.copy(),qvel=d.qvel.copy(),mass=mass,bias=d.qfrc_bias.copy(),passive=d.qfrc_passive.copy(),
      camera=d.cam_xpos.copy(),ik=ik,torque=torque))
  elapsed[n]+=time.monotonic()-start
 delta={key:float(np.max(abs(states[0][key]-states[1][key]))) for key in states[0]}
 row=dict(time_s=float(s['time_s'][i]),maximum_difference=delta,passed=max(delta.values())<1e-9);rows.append(row);print(json.dumps(row),flush=True)
report=dict(scope=__doc__,passed=all(r['passed'] for r in rows),rows=rows,predictor_geometry_counts=[m.ngeom for m in models],
 measured_regression_seconds=elapsed,physical_plant_changed=False,qualified=False)
(HERE/'review.json').write_text(json.dumps(report,indent=2)+'\n')
