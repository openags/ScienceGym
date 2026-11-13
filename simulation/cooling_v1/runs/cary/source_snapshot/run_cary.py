"""Contact-driven Cary main sliding-lid opening, release and recovery."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse,json,shutil,traceback
from datetime import datetime,timezone
import numpy as np,mujoco
from world import HERE
from cary_world import build
from hardware_control import HardwareRobot
from control import DOWN,ExecutionFailure
from precision_ik import solve
from trace_store import sha

class CaryRobot(HardwareRobot):
 def __init__(self,path,cfg,**kw):self.configuration=cfg;self.maximum_solver_iterations=0;self.next_progress=10.;super().__init__(path,**kw)
 def ik(self,xyz,rotation=DOWN):return solve(self,xyz,rotation)
 def advance(self,duration):
  for _ in range(max(1,round(duration/self.model.opt.timestep))):
   self.data.ctrl[:7]=self.joint_target+self.data.qfrc_bias[:7]/self.kp
   requested=-self.clamp_force if self.clamp_force is not None else 2000*(self.grip_target-np.mean(self.data.qpos[7:9]))-40*np.mean(self.data.qvel[7:9])
   self.data.ctrl[7]=np.clip(requested,-40,40);mujoco.mj_step(self.model,self.data);self.physics_steps+=1
   iterations=int(np.max(self.data.solver_niter));self.maximum_solver_iterations=max(self.maximum_solver_iterations,iterations)
   if iterations>=self.model.opt.iterations:raise ExecutionFailure('Cary solver exhausted iteration bound')
   if any(w.number for w in self.data.warning) or not np.isfinite(self.data.qpos).all():raise ExecutionFailure('Cary numerical warning')
   self.audit_contacts()
   if self.physics_steps%max(1,round(.005/self.model.opt.timestep))==0:self.save_state()
  if self.data.time>=self.next_progress:print('CARY PHYSICS',round(self.data.time,3),'slide',round(self.travel(),5),flush=True);self.next_progress=self.data.time+10
 def save_state(self):
  if not self.trace or self.data.time>self.trace[-1][0]+1e-10:self.trace.append((float(self.data.time),self.data.qpos.copy(),self.data.qvel.copy(),self.data.ctrl.copy()))
 def checkpoint(self,label,**values):self.save_state();return super().checkpoint(label,**values)
 def travel(self):return float(self.data.joint('cary_lid_travel').qpos[0])
 def audit_contacts(self):
  super().audit_contacts();forces={'left_finger':0.,'right_finger':0.}
  for i,c in enumerate(self.data.contact):
   names=[self.model.body(int(self.model.geom_bodyid[g])).name for g in c.geom]
   if not set(names)&set(forces):continue
   force=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,force)
   other=next((n for n in names if n not in forces),None)
   if other not in {'hand','cary_lid',None} and force[0]>.05:raise ExecutionFailure('Cary finger contacts unintended '+str(names))
   if other=='cary_lid':
    for side in forces:
     if side in names:forces[side]+=max(0.,float(force[0]))
  if max(forces.values())>self.configuration['selected_finger_force_limit_N']:raise ExecutionFailure('Cary grip force exceeds bound '+str(forces))
 def held(self):
  forces={}
  for c in self.contacts('cary_lid'):forces[c['other']]=forces.get(c['other'],0.)+c['force_n']
  if not all(forces.get(side,0)>.1 for side in ['left_finger','right_finger']):raise ExecutionFailure('Cary lid bilateral grip missing')
 def grasp_lid(self):
  self.active_object='cary_lid';self.finger(.020);point=self.grasp_site('cary_lid')+[0,0,.0015]
  self.move(point+[0,-.08,.14],DOWN,2.);self.move(point+[0,0,.10],DOWN,1.5);self.move(point,DOWN,1.5)
  for _ in range(2):self.move(self.grasp_site('cary_lid')+[0,0,.0015],DOWN,.25)
  # Close under a ramped force; a position step accelerated a jaw into
  # the narrow pull and exceeded the unchanged 20 N contact bound.
  for force in np.linspace(.2,self.configuration['selected_grip_N'],40):self.clamp_force=float(force);self.advance(.02)
  self.advance(.3);self.held();self.checkpoint('cary_lid_grasped',travel_m=self.travel(),contacts=self.contacts('cary_lid'))
 def slide(self,target):
  start=self.travel();point=self.data.site_xpos[self.site].copy();offset=point-self.grasp_site('cary_lid');correction=0.
  # Resolve the reversal gently. A 5 mm / 0.25 s first move after the
  # open stop overloaded one jaw in the half-step run. The force bound is
  # unchanged; shorter, slower moves reduce the acceleration demand.
  for value in np.linspace(start,target,max(2,int(np.ceil(abs(target-start)/.0025))+1))[1:]:
   self.held();command=self.grasp_site('cary_lid')+offset+[0,value-self.travel()+correction,0];self.move(command,DOWN,.40)
   error=value-self.travel();correction=float(np.clip(correction+error*.5,-.003,.003))
   if abs(error)>.003:raise ExecutionFailure('Cary sliding lid stalled '+str((value,self.travel())))
  if abs(self.travel()-target)>.0005:raise ExecutionFailure('Cary lid endpoint not reached')
  self.checkpoint('cary_lid_positioned',target_m=target,travel_m=self.travel(),contacts=self.contacts('cary_lid'))
 def release(self,target):
  for force in np.linspace(self.configuration['selected_grip_N'],.2,20):self.clamp_force=float(force);self.advance(.02)
  self.finger(.020);self.move(self.data.site_xpos[self.site]+[0,0,.12],DOWN,1.5);self.advance(1.)
  error=abs(self.travel()-target);fingers=sum(c['force_n'] for c in self.contacts('cary_lid') if c['other'] in {'left_finger','right_finger'})
  if error>.0005 or fingers>.01:raise ExecutionFailure('Cary lid failed released endpoint')
  self.checkpoint('cary_lid_released',target_m=target,travel_m=self.travel(),error_m=error,finger_force_N=fingers)

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',default='runs/cary_debug/slide');p.add_argument('--seed',type=int,default=0);p.add_argument('--case',choices=['nominal','missing_pull','locked_slide'],default='nominal');p.add_argument('--timestep',type=float,default=.001);a=p.parse_args();out=HERE/a.out;out.mkdir(parents=True,exist_ok=True)
 old=[x for x in out.iterdir() if x.name!='history']
 if old:
  archive=out/'history'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');archive.mkdir(parents=True)
  for x in old:x.replace(archive/x.name)
 names=['run_cary.py','cary_world.py','cary_assets.py','hardware_control.py','continuous_control.py','control.py','precision_ik.py','world.py','contact_safety.py','device_assets.py','extended_device_assets.py','optical_assets.py','robot_source.json','geometry/cary_5000/catalog.json','../../assets/cary_5000_v1/interfaces.json','../../assets/cary_5000_v1/geometry_checks.json']
 pins={n:sha(HERE/n) for n in names};archive={n:'source_snapshot/'+n.replace('../','parent/') for n in names}
 for n in names:
  destination=out/archive[n];destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(HERE/n,destination)
 robot=None;cfg=None;failure=None;passed=False
 try:
  cfg=build(out/'workcell.xml',a.case,a.timestep);pins['workcell.xml']=sha(out/'workcell.xml');robot=CaryRobot(out/'workcell.xml',cfg,seed=a.seed)
  for target in [.305,0.]:robot.grasp_lid();robot.slide(target);robot.release(target)
  passed=True
 except BaseException as error:failure=type(error).__name__+': '+str(error);traceback.print_exc()
 finally:
  if robot:
   robot.save_state();robot.close();np.savez_compressed(out/'physics_trace.npz',time=[r[0] for r in robot.trace],qpos=[r[1] for r in robot.trace],qvel=[r[2] for r in robot.trace],ctrl=[r[3] for r in robot.trace])
  if any(sha(HERE/n)!=pins[n] for n in names):passed=False;failure='Sources changed during execution'
  result=dict(status='passed' if passed else 'failed',failure=failure,configuration=cfg,seed=a.seed,observations=robot.timeline if robot else [],input_sha256=pins,source_archive=archive,simulated_seconds=float(robot.data.time) if robot else 0,numerics=dict(maximum_solver_iterations=robot.maximum_solver_iterations if robot else 0,warnings=[int(w.number) for w in robot.data.warning] if robot else []),artifacts_sha256={n:sha(out/n) for n in ['physics_trace.npz'] if (out/n).exists()},whole_paper_validated=False)
  (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('CARY',result['status'],failure,flush=True)
 return passed
if __name__=='__main__':raise SystemExit(0 if main() else 1)
