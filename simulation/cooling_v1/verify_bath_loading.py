"""Independent continuous-state audit of the selected bath loading sequence.

A resumed diagnostic or a limited development episode cannot satisfy this
contract. Only an initial-state run with the complete ordered chain qualifies.
"""
import argparse,json
from pathlib import Path
from types import SimpleNamespace
import numpy as np,mujoco
from bath_assets import load
from contact_safety import audit
from control import ExecutionFailure
from support_observation import support_load
from trace_store import sha,load_trace


def verify(directory):
 directory=Path(directory);result=json.loads((directory/'result.json').read_text());cfg=result['configuration'];checks=[]
 def check(name,passed,**values):checks.append(dict(name=name,passed=bool(passed),**values))
 check('complete_initial_state_execution',result['status'] in {'passed','development_pass'} and result.get('development_limit') is None and result.get('failure') is None,execution_status=result['status'],failure=result.get('failure'))
 archive=result['source_archive'];changed=[]
 for n,digest in result['input_sha256'].items():
  p=directory/n if n=='workcell.xml' else directory/archive/n
  if sha(p)!=digest:changed.append(n)
 check('archived_input_hashes',not changed,changed=changed)
 t=load_trace(directory,result['artifacts_sha256']['physics_trace.npz']);times=t['time'];check('finite_trace',all(np.isfinite(v).all() for v in t.values()))
 check('continuous_clock_from_initialization',len(times)>1 and times[0]<=.005001 and np.all(np.diff(times)>0) and np.max(np.diff(times))<=.001001,samples=len(times),start_s=float(times[0]),maximum_interval_s=float(np.max(np.diff(times))))
 check('trace_reaches_end',abs(times[-1]-result['simulated_seconds'])<1e-9)
 m=load(directory/'workcell.xml');m.opt.disableflags|=int(mujoco.mjtDisableBit.mjDSBL_WARMSTART);d=mujoco.MjData(m)
 check('no_attachment_weld',not any(v==mujoco.mjtEq.mjEQ_WELD for v in m.eq_type))
 check('robot_only_actuation',m.nu==8 and all(m.body(m.jnt_bodyid[j]).name.startswith('link') for j in m.actuator_trnid[:7,0]))
 payload=float(sum(m.body(n).mass[0] for n in ['calibration_block','block_cradle']));check('selected_payload_limit',payload<=3.,mass_kg=payload,limit_kg=3.)
 check('copper_mass_from_volume',abs(float(m.body('calibration_block').mass[0])-cfg['block']['mass_kg'])<1e-9)
 check('numerical_guards',result['maximum_solver_iterations']<m.opt.iterations and not any(result['warnings']),maximum_solver_iterations=result['maximum_solver_iterations'],solver_limit=m.opt.iterations,warnings=result['warnings'])
 check('bounded_gripper_commands',np.max(abs(t['ctrl'][:,7]))<=40.000001)
 names=['bath_lid','calibration_block','block_cradle'];addresses={n:int(m.joint(n+'_free').qposadr[0]) for n in names}
 for n,a in addresses.items():
  speed=np.linalg.norm(np.diff(t['qpos'][:,a:a+3],axis=0),axis=1)/np.diff(times)
  check('continuous_motion_'+n,np.max(speed)<1.,maximum_speed_m_s=float(np.max(speed)))
 chain=[('bath_lid_grasped',None),('bath_lid_load_transferred',None),('bath_lid_supported',None),
        ('bath_payload_lifted','calibration_block'),('bath_payload_supported','calibration_block'),
        ('bath_payload_lifted','block_cradle'),('bath_payload_supported','block_cradle'),('bath_block_retained_in_cradle',None),
        ('bath_payload_lifted','block_cradle'),('bath_payload_supported','block_cradle'),('bath_block_retained_in_cradle',None),
        ('bath_payload_lifted','calibration_block'),('bath_payload_supported','calibration_block'),
        ('bath_lid_grasped',None),('bath_lid_load_transferred',None),('bath_lid_supported',None)]
 events=result['observations'];check('complete_ordered_chain',[(e['label'],e.get('body')) for e in events]==chain)
 def state(at):
  i=int(np.argmin(abs(times-at)));d.qpos[:]=t['qpos'][i];d.qvel[:]=t['qvel'][i];d.ctrl[:]=t['ctrl'][i];mujoco.mj_forward(m,d);return i
 def grip(body):
  forces={'left_finger':0.,'right_finger':0.}
  for i,c in enumerate(d.contact):
   bs=[m.body(int(m.geom_bodyid[g])).name for g in c.geom]
   if body not in bs:continue
   f=np.zeros(6);mujoco.mj_contactForce(m,d,i,f)
   for side in set(bs)&set(forces):forces[side]+=max(0.,float(f[0]))
  return forces
 for j,event in enumerate(events):
  i=state(event['time_s']);label=event['label'];check('exact_event_'+str(j),abs(times[i]-event['time_s'])<1e-9)
  if label in {'bath_payload_lifted','bath_lid_grasped'}:
   n=event.get('body','bath_lid');forces=grip(n);a=addresses[n]
   earlier=next((e for e in reversed(events[:j]) if e['label'] in {'bath_payload_supported','bath_lid_supported'} and e.get('body','bath_lid')==n),None)
   start=int(np.argmin(abs(times-earlier['time_s']))) if earlier else 0
   lift=float(t['qpos'][i,a+2]-t['qpos'][start,a+2]);minimum=.08 if n=='bath_lid' else .10
   check('physical_grasp_and_lift_'+str(j),min(forces.values())>.1 and lift>=minimum,body=n,lift_m=lift,normal_forces_N=forces)
  elif label in {'bath_payload_supported','bath_lid_supported'}:
   n=event.get('body','bath_lid');support=event['support'];forces=grip(n);load=support_load(m,d,n,support)
   if n=='bath_lid':target=cfg['lid_closed_body_m'] if support=='bath' else cfg['lid_park_body_m']
   elif n=='block_cradle':target=cfg['cradle_bath_target_m'] if support=='bath_load_support' else cfg['cradle_park_m']
   else:target=d.body('block_cradle').xpos+cfg['block_in_cradle_offset_m'] if support=='block_cradle' else cfg['block_park_m']
   error=float(np.linalg.norm(d.body(n).xpos-target));tilt=float(np.arccos(np.clip(d.body(n).xmat[8],-1,1)));weight=load['body_weight_n']
   if n=='block_cradle':weight+=float(m.body('calibration_block').mass[0])*9.81
   check('released_support_'+str(j),error<.002 and tilt<.035 and sum(forces.values())<.01 and load['vertical_force_n']>.8*weight,body=n,support=support,error_m=error,tilt_rad=tilt,load=load,required_weight_N=weight,finger_normal_N=forces)
  elif label=='bath_block_retained_in_cradle':
   load=support_load(m,d,'calibration_block','block_cradle');error=float(np.linalg.norm(d.body('calibration_block').xpos-d.body('block_cradle').xpos-cfg['block_in_cradle_offset_m']))
   check('block_retained_'+str(j),load['vertical_force_n']>.8*load['body_weight_n'] and error<.002,relative_error_m=error,load=load)
 # Recompute all saved contacts, including the slow load transfer and paths.
 proxy=SimpleNamespace(model=m,data=d,peak_unintended_force=0.);bad=[];max_force={n:0. for n in names};max_bath=0.;worst_payload_overlap=0.
 cradle_lifts=[e['time_s'] for e in events if e['label']=='bath_payload_lifted' and e.get('body')=='block_cradle'];cradle_supports=[e['time_s'] for e in events if e['label']=='bath_payload_supported' and e.get('body')=='block_cradle'];relative_error=0.
 for i,at in enumerate(times):
  d.qpos[:]=t['qpos'][i];d.qvel[:]=t['qvel'][i];d.ctrl[:]=t['ctrl'][i];mujoco.mj_forward(m,d)
  try:audit(proxy)
  except ExecutionFailure as error:
   if len(bad)<10:bad.append(dict(time_s=float(at),failure=str(error)))
  forces={n:{'left_finger':0.,'right_finger':0.} for n in names}
  for k,c in enumerate(d.contact):
   bs=[m.body(int(m.geom_bodyid[g])).name for g in c.geom];f=np.zeros(6);mujoco.mj_contactForce(m,d,k,f)
   for n in set(bs)&set(names):
    for side in set(bs)&{'left_finger','right_finger'}:forces[n][side]+=max(0.,float(f[0]))
   if 'bath' in bs and set(bs)&{'calibration_block','block_cradle'}:max_bath=max(max_bath,float(f[0]));worst_payload_overlap=min(worst_payload_overlap,float(c.dist))
   if set(bs)&{'left_finger','right_finger'}:
    other=next((n for n in bs if n not in {'left_finger','right_finger'}),None)
    if other not in {*names,'hand',None} and f[0]>.05 and len(bad)<10:bad.append(dict(time_s=float(at),bodies=bs,force_N=float(f[0])))
  for n in names:max_force[n]=max(max_force[n],*forces[n].values())
  if any(start<=at<=end for start,end in zip(cradle_lifts,cradle_supports)):
   relative_error=max(relative_error,float(np.linalg.norm(d.body('calibration_block').xpos-d.body('block_cradle').xpos-cfg['block_in_cradle_offset_m'])))
  if i and i%50000==0:print('BATH AUDIT',i,'/',len(times),flush=True)
 check('sampled_robot_contact_clearance',not bad,failures=bad)
 check('selected_finger_force_limits',max_force['bath_lid']<=25. and max(max_force[n] for n in ['calibration_block','block_cradle'])<=35.,maximum_per_finger_N=max_force)
 check('payload_clear_of_bath_case',max_bath<=.5,maximum_normal_N=max_bath,maximum_overlap_m=-worst_payload_overlap)
 check('block_stays_in_cradle_during_both_transfers',len(cradle_lifts)==len(cradle_supports)==2 and relative_error<.002,maximum_relative_position_error_m=relative_error)
 report=dict(passed=all(c['passed'] for c in checks),checks=checks,result_sha256=sha(directory/'result.json'),verifier_sha256=sha(Path(__file__)),engine_version=mujoco.__version__,whole_paper_validated=False,scope='Selected dry bath load handling: lid removal, bored copper block into cradle, retained bath placement and complete recovery. Fluid, probes, circuits and calibration are separate obligations.')
 (directory/'verification.json').write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory');a=p.parse_args();r=verify(a.directory);print(json.dumps(dict(passed=r['passed'],checks=len(r['checks']),failed=[c for c in r['checks'] if not c['passed']]),indent=2));raise SystemExit(0 if r['passed'] else 1)
