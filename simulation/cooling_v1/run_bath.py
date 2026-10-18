"""Actuated A25 lid removal/return and bounded AC150 front-key operations."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse,json,shutil
from datetime import datetime,timezone
import numpy as np,mujoco
from scipy.spatial.transform import Rotation
from world import HERE
from bath_world import build
from hardware_control import HardwareRobot
from control import ExecutionFailure,DOWN
from cover_world import SIDE
from trace_store import sha
LID_ROTATION=Rotation.from_euler('x',np.deg2rad(15)).as_matrix()@DOWN


class BathRobot(HardwareRobot):
 def __init__(self,path,configuration,**kwargs):
  self.configuration=configuration;self.maximum_solver_iterations=0;self.next_progress=10.;super().__init__(path,**kwargs)
 def advance(self,duration):
  for _ in range(max(1,round(duration/self.model.opt.timestep))):
   self.data.ctrl[:7]=self.joint_target+self.data.qfrc_bias[:7]/self.kp
   requested=-self.clamp_force if self.clamp_force is not None else 2000*(self.grip_target-np.mean(self.data.qpos[7:9]))-40*np.mean(self.data.qvel[7:9])
   self.data.ctrl[7]=np.clip(requested,-40,40);mujoco.mj_step(self.model,self.data);self.physics_steps+=1
   iterations=int(np.max(self.data.solver_niter));self.maximum_solver_iterations=max(self.maximum_solver_iterations,iterations)
   if iterations>=self.model.opt.iterations:raise ExecutionFailure('Bath constraint solver exhausted its iteration limit')
   if any(w.number for w in self.data.warning) or not np.isfinite(self.data.qpos).all():raise ExecutionFailure('Bath numerical warning or nonfinite state')
   self.audit_contacts()
   if self.physics_steps%5==0:self.save_state()
  if self.data.time>=self.next_progress:print('BATH PHYSICS',round(self.data.time,3),'active',self.active_object,flush=True);self.next_progress=self.data.time+10
 def save_state(self):
  if not self.trace or self.data.time>self.trace[-1][0]+1e-10:self.trace.append((float(self.data.time),self.data.qpos.copy(),self.data.qvel.copy(),self.data.ctrl.copy()))
 def checkpoint(self,label,**values):self.save_state();return super().checkpoint(label,**values)
 def audit_contacts(self):
  super().audit_contacts()
  for i,c in enumerate(self.data.contact):
   names=[self.model.body(int(self.model.geom_bodyid[g])).name for g in c.geom];f=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,f)
   if set(names)&{'left_finger','right_finger'}:
    other=next((n for n in names if n not in {'left_finger','right_finger'}),None)
    if other not in {'bath_lid','hand',None} and f[0]>.05:raise ExecutionFailure('Bath finger contact with unintended body '+str(names))
 def held(self):
  contacts=self.contacts('bath_lid')
  if not {'left_finger','right_finger'}<={c['other'] for c in contacts if c['force_n']>.1}:raise ExecutionFailure('Bath lid bilateral grip lost')
  rotation=self.data.body('bath_lid').xmat.reshape(3,3)
  return rotation.T@(self.data.site_xpos[self.site]-self.position('bath_lid')),rotation.T@self.data.site_xmat[self.site].reshape(3,3)
 def grasp_lid(self):
  self.site=self.model.site('tcp').id;self.active_object='bath_lid';self.finger(.035);p=self.grasp_site('bath_lid')
  # A forward wrist inclination clears the controller behind the lid.
  self.move(p+[0,-.12,.15],LID_ROTATION,1.8);self.move(p+[0,0,.12],LID_ROTATION,1.5);self.move(p,LID_ROTATION,1.8)
  for _ in range(2):self.move(self.grasp_site('bath_lid'),LID_ROTATION,.25)
  self.finger(.012);self.clamp_force=12.;self.advance(.3);self.held();before=self.position('bath_lid');self.move(self.data.site_xpos[self.site]+[0,0,.10],LID_ROTATION,1.8)
  lifted=float(self.position('bath_lid')[2]-before[2])
  if lifted<.08:raise ExecutionFailure('Bath lid failed observed lift')
  self.checkpoint('bath_lid_grasped',lift_m=lifted,contacts=self.contacts('bath_lid'))
 def place_lid(self,target,support):
  target=np.array(target);start=self.position('bath_lid');height=max(start[2],target[2]+.12)
  for u in np.linspace(0,1,8)[1:]:
   offset,rotation=self.held();self.move(np.r_[start[:2]+u*(target[:2]-start[:2]),height]+offset,rotation,.45)
  for height in np.r_[np.linspace(.10,.006,14),[.003,.001,.0005]]:
   offset,rotation=self.held();self.move(target+offset+[0,0,height],rotation,.20)
  self.finger(.035);self.move(self.data.site_xpos[self.site]+[0,0,.12],rotation,1.5);self.advance(.5)
  error=float(np.linalg.norm(self.position('bath_lid')-target));tilt=float(np.arccos(np.clip(self.data.body('bath_lid').xmat.reshape(3,3)[2,2],-1,1)));load=0.
  for i,c in enumerate(self.data.contact):
   bodies=[self.model.body(int(self.model.geom_bodyid[g])).name for g in c.geom]
   if set(bodies)!={'bath_lid',support}:continue
   f=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,f);force=c.frame.reshape(3,3).T@f[:3];load+=force[2]*(1 if bodies[1]=='bath_lid' else -1)
  weight=float(self.model.body('bath_lid').mass*9.81);contacts=self.contacts('bath_lid')
  self.checkpoint('bath_lid_supported',support=support,error_m=error,tilt_rad=tilt,vertical_load_N=float(load),weight_N=weight,contacts=contacts)
  if error>.002 or tilt>.035 or load<weight*.8 or any(c['other'] in {'left_finger','right_finger'} and c['force_n']>.01 for c in contacts):raise ExecutionFailure('Bath lid support or release failed')


def execute(robot,limit):
 robot.grasp_lid();robot.place_lid(robot.configuration['lid_park_body_m'],'lid_stand')
 if limit=='removal':return
 robot.site=robot.model.site('bath_pusher_tcp').id
 # These dry-bath keys do not command the pump/heater to start. No thermal
 # or electronics success is inferred from their physical travel.
 for key in ['AC150_standby','AC150_escape','AC150_standby']:
  target=next(k for k in robot.configuration['keys'] if k['id']==key)
  robot.press_button(target['physical_body'],target['axis'],SIDE,target['travel_m']);robot.advance(.2)
  travel=float(robot.data.joint(target['physical_body']+'_travel').qpos[0])
  if abs(travel)>.0001:raise ExecutionFailure('Bath key did not return after release')
  robot.checkpoint('bath_key_released',body=target['physical_body'],travel_m=travel)
 robot.grasp_lid();robot.place_lid(robot.configuration['lid_closed_body_m'],'bath')


def main():
 p=argparse.ArgumentParser();p.add_argument('--out',default='runs/bath_debug/robot');p.add_argument('--limit',choices=['removal']);a=p.parse_args();out=HERE/a.out;out.mkdir(parents=True,exist_ok=True)
 old=[x for x in out.iterdir() if x.name!='history']
 if old:
  history=out/'history'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');history.mkdir(parents=True)
  for x in old:x.replace(history/x.name)
 names=['run_bath.py','bath_world.py','bath_assets.py','hardware_control.py','continuous_control.py','control.py','world.py','contact_safety.py','device_assets.py','extended_device_assets.py','robot_source.json','geometry/thermo_a25_ac150/catalog.json','../../assets/thermo_a25_ac150_v1/interfaces.json','../../assets/thermo_a25_ac150_v1/geometry_checks.json']
 pins={n:sha(HERE/n) for n in names};archive={n:'source_snapshot/'+n.replace('../','parent/') for n in names}
 for n in names:
  target=out/archive[n];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(HERE/n,target)
 robot=None;configuration=None;failure=None;passed=False
 try:
  configuration=build(out/'workcell.xml');pins['workcell.xml']=sha(out/'workcell.xml');robot=BathRobot(out/'workcell.xml',configuration);execute(robot,a.limit);passed=True
 except BaseException as error:failure=type(error).__name__+': '+str(error);print(failure,flush=True)
 finally:
  if robot:
   robot.save_state();robot.close();np.savez_compressed(out/'physics_trace.npz',time=[r[0] for r in robot.trace],qpos=[r[1] for r in robot.trace],qvel=[r[2] for r in robot.trace],ctrl=[r[3] for r in robot.trace])
  if any(sha(HERE/n)!=pins[n] for n in names):passed=False;failure='Source changed during execution'
  result=dict(status=('development_pass' if a.limit else 'passed') if passed else 'failed',failure=failure,configuration=configuration,source_archive=archive,input_sha256=pins,engine_version=mujoco.__version__,observations=robot.timeline if robot else [],simulated_seconds=float(robot.data.time) if robot else 0,
   maximum_solver_iterations=robot.maximum_solver_iterations if robot else None,warnings=[int(w.number) for w in robot.data.warning] if robot else [],physics_steps=robot.physics_steps if robot else 0,development_limit=a.limit,
   artifacts_sha256={n:sha(out/n) for n in ['physics_trace.npz'] if (out/n).exists()},whole_paper_validated=False,
   scope='Lid removal, supported parking, dry-bath front-key presses and lid return. No filling, sensor/block loading, wiring or thermal calibration acceptance.')
  (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('BATH RESULT',result['status'],failure,flush=True)
 return passed
if __name__=='__main__':raise SystemExit(0 if main() else 1)
