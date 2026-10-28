"""Independent saved-state audit of the passive Cary sliding-lid cycle."""
import argparse,json
from pathlib import Path
from types import SimpleNamespace
import numpy as np,mujoco
from cary_assets import load
from contact_safety import audit
from control import ExecutionFailure
from trace_store import sha,load_trace

def verify(directory,expected='nominal'):
 directory=Path(directory);result=json.loads((directory/'result.json').read_text());cfg=result['configuration'];checks=[]
 def check(name,passed,**values):checks.append(dict(name=name,passed=bool(passed),**values))
 check('expected_execution_outcome',cfg['case']==expected and result['status']==('passed' if expected=='nominal' else 'failed'),failure=result['failure'])
 changed=[n for n,digest in result['input_sha256'].items() if sha(directory/(n if n=='workcell.xml' else result['source_archive'][n]))!=digest]
 check('archived_input_hashes',not changed,changed=changed)
 t=load_trace(directory,result['artifacts_sha256']['physics_trace.npz']);times=t['time'];check('finite_saved_states',all(np.isfinite(v).all() for v in t.values()))
 check('continuous_clock',len(times)>1 and np.all(np.diff(times)>0) and np.max(np.diff(times))<=.005001,samples=len(times),maximum_interval_s=float(np.max(np.diff(times))))
 check('trace_reaches_end',abs(times[-1]-result['simulated_seconds'])<1e-9)
 m=load(directory/'workcell.xml');m.opt.disableflags|=int(mujoco.mjtDisableBit.mjDSBL_WARMSTART);d=mujoco.MjData(m);joint=m.joint('cary_lid_travel');travel=t['qpos'][:,joint.qposadr[0]]
 check('passive_lid_robot_only_actuation',joint.id not in m.actuator_trnid[:,0] and m.nu==8)
 check('no_attachment_weld',not any(v==mujoco.mjtEq.mjEQ_WELD for v in m.eq_type))
 check('bounded_gripper_command',np.max(abs(t['ctrl'][:,7]))<=40.000001)
 check('selected_track_resistance',abs(float(m.dof_frictionloss[joint.dofadr[0]])-cfg['selected_slide_friction_N'])<1e-12)
 speed=float(np.max(abs(np.diff(travel)/np.diff(times))));check('continuous_lid_motion',speed<.3,maximum_sampled_speed_m_s=speed)
 numerical=result['numerics'];check('numerical_guards',numerical['maximum_solver_iterations']<m.opt.iterations and not any(numerical['warnings']),observed=numerical)
 rows=[];bad=[];maximum=0.;case_load=0.;worst_overlap=0.;proxy=SimpleNamespace(model=m,data=d,peak_unintended_force=0.)
 for index,at in enumerate(times):
  d.qpos[:]=t['qpos'][index];d.qvel[:]=t['qvel'][index];d.ctrl[:]=t['ctrl'][index];mujoco.mj_forward(m,d);fingers={'left_finger':0.,'right_finger':0.}
  try:audit(proxy)
  except ExecutionFailure as error:
   if len(bad)<10:bad.append(dict(time_s=float(at),failure=str(error)))
  for i,c in enumerate(d.contact):
   names=[m.body(int(m.geom_bodyid[g])).name for g in c.geom];f=np.zeros(6);mujoco.mj_contactForce(m,d,i,f)
   if 'cary_lid' in names:
    for side in set(names)&set(fingers):fingers[side]+=max(0.,float(f[0]))
    if 'cary' in names:case_load=max(case_load,float(f[0]));worst_overlap=min(worst_overlap,float(c.dist))
   if set(names)&set(fingers):
    other=next((n for n in names if n not in fingers),None)
    if other not in {'hand','cary_lid',None} and f[0]>.05 and len(bad)<10:bad.append(dict(time_s=float(at),bodies=names,force_N=float(f[0])))
  maximum=max(maximum,*fingers.values());rows.append(fingers)
 check('sampled_robot_contact_clearance',not bad,failures=bad)
 check('lid_case_clearance',case_load<10. and worst_overlap>=-.0001,maximum_contact_N=case_load,maximum_overlap_m=-worst_overlap)
 if expected=='nominal':check('selected_finger_force_bound',maximum<=cfg['selected_finger_force_limit_N'],maximum_per_finger_N=maximum)
 events=result['observations'];labels=[e['label'] for e in events];chain=['cary_lid_grasped','cary_lid_positioned','cary_lid_released']*2
 if expected=='nominal':check('complete_ordered_chain',labels==chain)
 elif expected=='missing_pull':
  check('missing_pull_rejected_before_grasp',not events and 'bilateral grip missing' in result['failure'])
  check('pull_physically_absent',not any((m.geom(i).name or '').startswith('cary_pull_') for i in range(m.ngeom)))
 elif expected=='locked_slide':
  check('physical_slide_stop',np.max(abs(m.jnt_range[joint.id]-[0,.0001]))<1e-12)
  check('locked_slide_rejected_before_opening',labels==['cary_lid_grasped'] and np.max(abs(travel))<.001)
 else:raise ValueError(expected)
 for number,event in enumerate(events):
  k=int(np.argmin(abs(times-event['time_s'])));check('exact_event_'+str(number),abs(times[k]-event['time_s'])<1e-9)
  if event['label']=='cary_lid_grasped':check('bilateral_grasp_'+str(number),min(rows[k].values())>.1,normal_forces_N=rows[k])
  elif event['label']=='cary_lid_positioned':check('contact_driven_position_'+str(number),abs(travel[k]-event['target_m'])<.0005 and min(rows[k].values())>.1,actual_travel_m=float(travel[k]),target_m=event['target_m'],normal_forces_N=rows[k])
  elif event['label']=='cary_lid_released':
   indices=np.flatnonzero((times>=times[k]-.99)&(times<=times[k]));error=float(np.max(abs(travel[indices]-event['target_m'])));force=max(sum(rows[i].values()) for i in indices)
   check('passive_retention_after_release_'+str(number),error<.0005 and force<.01 and len(indices)>=198,maximum_position_error_m=error,maximum_finger_N=force,samples=len(indices))
 report=dict(passed=all(c['passed'] for c in checks),expected=expected,checks=checks,result_sha256=sha(directory/'result.json'),verifier_sha256=sha(Path(__file__)),engine_version=mujoco.__version__,whole_paper_validated=False,scope=cfg['scope'])
 (directory/'verification.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--expected',choices=['nominal','missing_pull','locked_slide'],default='nominal');a=p.parse_args();r=verify(a.directory,a.expected);print(json.dumps(dict(passed=r['passed'],checks=len(r['checks']),failed=[c for c in r['checks'] if not c['passed']]),indent=2));raise SystemExit(0 if r['passed'] else 1)
