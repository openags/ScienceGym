"""Independent physics evaluation of one continuous transport/return episode."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import mujoco
import trimesh

def verify(folder):
 folder=Path(folder).resolve();model=mujoco.MjModel.from_xml_path(str(folder/'world.xml'));data=mujoco.MjData(model);tr=np.load(folder/'trace.npz');result=json.loads((folder/'result.json').read_text());checks=[]
 def check(name,value,**details):checks.append(dict(name=name,passed=bool(value),**details))
 check('executor_and_policy_completed',result['status']=='completed' and result['actor_last_output'].get('policy_complete',False))
 check('floating_robot_without_weld',model.jnt_type[0]==mujoco.mjtJoint.mjJNT_FREE and not np.any(model.eq_type==mujoco.mjtEq.mjEQ_WELD))
 check('motors_drive_hinges_only',all(model.jnt_type[j]==mujoco.mjtJoint.mjJNT_HINGE for j in model.actuator_trnid[:,0]))
 check('recorded_code_matches_snapshots',all(hashlib.sha256((folder/'source_snapshot'/name).read_bytes()).hexdigest()==sha for name,sha in result['source_sha256'].items()))
 check('motor_limits',np.all(tr['ctrl']>=model.actuator_ctrlrange[:,0]-1e-9) and np.all(tr['ctrl']<=model.actuator_ctrlrange[:,1]+1e-9))
 check('standing_throughout',np.min(tr['qpos'][:,2])>.6 and np.max(np.linalg.norm(tr['qpos'][:,4:6],axis=1))<.2)
 qa=model.joint('tray_free').qposadr[0];pos=tr['qpos'][:,qa:qa+3];delta=np.linalg.norm(pos[:,:2]-pos[0,:2],axis=1);height=pos[:,2]-pos[0,2]
 check('actual_outbound_transport',float(delta.max())>=.04,maximum_m=float(delta.max()))
 check('actual_lift_at_least_7cm',float(height.max())>=.07,maximum_m=float(height.max()))
 # Count distinct lifted intervals from plant positions, independent of the
 # actor's declared stages. Require >= 0.5 s above threshold in each interval.
 airborne=height>.07;begins=np.flatnonzero(airborne&~np.r_[False,airborne[:-1]]);ends=np.flatnonzero(airborne&~np.r_[airborne[1:],False]);lifts=[dict(begin_s=float(tr['time'][a]),end_s=float(tr['time'][b])) for a,b in zip(begins,ends) if tr['time'][b]-tr['time'][a]>=.5]
 required=2 if result.get('return_to_source') else 1;check('required_distinct_lifts',len(lifts)>=required,intervals=lifts,required=required)
 if result.get('return_to_source'):check('returned_to_source_within_2cm',delta[-1]<.02,final_error_m=float(delta[-1]))
 else:check('final_displacement_at_least_4cm',delta[-1]>=.04,final_m=float(delta[-1]))
 dof=model.joint('tray_free').dofadr[0];last=tr['time']>=tr['time'][-1]-1
 check('tray_stable_after_release',np.max(np.linalg.norm(tr['qvel'][last,dof:dof+6],axis=1))<.01)
 data.qpos[:]=tr['qpos'][-1];data.qvel[:]=tr['qvel'][-1];mujoco.mj_forward(model,data);traybody=model.body('carrier_tray').id;table=model.geom('bench_top').id;table_contact=False;hand_contact=False
 for c in data.contact:
  a,b=int(c.geom1),int(c.geom2)
  if model.geom_bodyid[a]!=traybody and model.geom_bodyid[b]!=traybody:continue
  other=b if model.geom_bodyid[a]==traybody else a
  table_contact|=other==table
  hand_contact|=model.geom_bodyid[other]!=0 and model.body(model.geom_bodyid[other]).name!='calibration_copper_stock'
 check('final_release_on_table',table_contact and not hand_contact and abs(pos[-1,2]-.9)<.005)
 events=result['actor_last_output'].get('policy_events',[]);gates=[e for e in events if e['state'] in ['transfer','place','release','retract']]
 obs=json.loads((folder/'policy_observations.json').read_text());fresh=[]
 for e in gates:
  previous=[o for o in obs if o['time_s']<=e['time_s']+1e-7 and o['observation'] is not None]
  fresh.append(bool(e['evidence']) and bool(previous) and e['time_s']-previous[-1]['time_s']<=.15 and e['evidence']==previous[-1]['observation'])
 check('outcome_transitions_have_fresh_depth_evidence',len(gates)>=required*4 and all(fresh),transition_count=len(gates))
 check('separate_sensor_actor',result['actor_process_separate'] and set(result['actor_input_fields'])=={'time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro','depth'})
 # Record actual geometric clearance; body-origin rise alone is not clearance.
 vertices=trimesh.load(folder/'tray_visual.stl').vertices;peak=int(np.argmax(height));data.qpos[:]=tr['qpos'][peak];mujoco.mj_kinematics(model,data);body=data.body('carrier_tray');clearance=float((vertices@body.xmat.reshape(3,3).T+body.xpos)[:,2].min()-.9)
 check('complete_tray_off_table_at_peak',clearance>.005,minimum_clearance_m=clearance)
 payload_metrics=None
 if result.get('payload_present'):
  vertices=trimesh.load(folder/'calibration_copper_stock.stl').vertices;worst=np.zeros(3);contained=True
  for i in range(0,len(tr['time']),10):
   data.qpos[:]=tr['qpos'][i];mujoco.mj_kinematics(model,data);block=data.body('calibration_copper_stock');tray=data.body('carrier_tray');world=vertices@block.xmat.reshape(3,3).T+block.xpos;local=(world-tray.xpos)@tray.xmat.reshape(3,3)
   extent=np.max(abs(local[:,:2]),axis=0);worst[:2]=np.maximum(worst[:2],extent);worst[2]=max(worst[2],-float(local[:,2].min()))
   contained &= bool(extent[0]<.151 and extent[1]<.101 and local[:,2].min()>-.005 and local[:,2].min()<.06)
  payload_metrics=dict(body_mass_kg=float(model.body_mass[model.body('calibration_copper_stock').id]),maximum_local_xy_extent_m=worst[:2].tolist(),maximum_below_tray_origin_m=float(worst[2]))
  check('copper_stock_retained_in_tray',contained,**payload_metrics)
 data=mujoco.MjData(model);data.qpos[:]=tr['qpos'][0];data.qvel[:]=tr['qvel'][0];mujoco.mj_forward(model,data);data.qacc_warmstart[:]=tr['qacc_warmstart'][0];qerr=0.;verr=0.
 for i in range(len(tr['time'])-1):
  data.ctrl[:]=tr['ctrl'][i]
  for _ in range(round(float(tr['time'][i+1]-tr['time'][i])/model.opt.timestep)):mujoco.mj_step(model,data)
  qerr=max(qerr,float(np.max(abs(data.qpos-tr['qpos'][i+1]))));verr=max(verr,float(np.max(abs(data.qvel-tr['qvel'][i+1]))))
 check('continuous_motor_replay_matches',qerr<1e-7 and verr<1e-6,max_qpos_error=qerr,max_qvel_error=verr)
 check('no_external_applied_forces',not np.any(data.xfrc_applied) and not np.any(data.qfrc_applied))
 out=dict(passed=all(c['passed'] for c in checks),checks=checks,scope='One continuous carrier transport subtask; no full-paper or acceptance-trial credit.',whole_paper_validated=False,qualified_paper_branches=0,metrics=dict(duration_s=float(tr['time'][-1]),lift_m=float(height.max()),maximum_transport_m=float(delta.max()),final_displacement_m=float(delta[-1]),minimum_tray_clearance_at_peak_m=clearance,lift_intervals=lifts,payload=payload_metrics),verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),limitations=['Idealized depth/IMU and fixed-foot localization.','Known empty-bench background model and single-carrier visual prior.','No sensor calibration, full laboratory dynamics, walking or complete paper branches.','A loaded case starts preloaded; it grants no loading or fabrication credit.'])
 (folder/'transport_verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
 plot=dict(time=tr['time'][::10].tolist(),tray_height_cm=(height[::10]*100).tolist(),tray_y_cm=((pos[::10,1]-pos[0,1])*100).tolist());(folder/'plot.json').write_text(json.dumps(plot)+'\n')
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('folder');a=p.parse_args();verify(a.folder)
