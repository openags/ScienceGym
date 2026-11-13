"""Contact-actuated hinged cover opening and return; no cover actuator."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse,json,shutil,traceback
from datetime import datetime,timezone
import numpy as np,mujoco
from scipy.spatial.transform import Rotation
from optical_assets import load
from nicolet_world import build
from world import HERE
from run_bath import BathRobot
from hardware_control import HardwareRobot
from control import DOWN,ExecutionFailure
from precision_ik import solve
from trace_store import sha

SIDE=Rotation.from_euler('x',np.pi/2).as_matrix()@DOWN


class NicoletRobot(BathRobot):
    ik=solve
    def audit_contacts(self):
        HardwareRobot.audit_contacts(self)
        forces={'left_finger':0.,'right_finger':0.}
        for i,c in enumerate(self.data.contact):
            names=[self.model.body(int(self.model.geom_bodyid[g])).name for g in c.geom]
            if {'spectrometer_lid','nicolet'}<=set(names):
                f=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,f)
                if f[0]>10. or c.dist<-.0001:raise ExecutionFailure('Nicolet cover contacts case beyond seating allowance')
            sides=set(names)&set(forces)
            if not sides:continue
            other=next((n for n in names if n not in forces),None);f=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,f)
            if other not in {'spectrometer_lid','hand',None} and f[0]>.05:raise ExecutionFailure('Nicolet gripper contacted unintended body '+str(names))
            if other=='spectrometer_lid':
                for side in sides:forces[side]+=max(0.,float(f[0]))
        if max(forces.values())>25.:raise ExecutionFailure('Nicolet cover exceeded selected 25 N per-finger bound')

    def angle(self):return float(self.data.joint('spectrometer_lid_hinge').qpos[0])

    def pose(self,angle):
        rotation=Rotation.from_euler('x',angle).as_matrix();tool=rotation@SIDE
        point=np.array(self.configuration['hinge_origin_m'])+rotation@np.array(self.configuration['local_grasp_from_hinge_m'])
        return point-tool@np.array([0,0,.005]),tool

    def grip_cover(self):
        self.active_object='spectrometer_lid';self.site=self.model.site('tcp').id;self.finger(.025)
        point,rotation=self.pose(self.angle());approach=-rotation[:,2]*.10
        # The open-cover release already parks on this observed approach
        # ray. Adding the closed-cover overhead waypoint there would put
        # the wrist above the robot's reach, despite a reachable handle.
        if abs(self.angle())<.1:self.move(point+approach+[0,0,.10],rotation,1.8)
        self.move(point+approach,rotation,1.3);self.move(point,rotation,1.5)
        self.finger(.004);self.clamp_force=self.configuration['selected_grip_N'];self.advance(.3);self.held_cover()
        self.checkpoint('spectrometer_cover_grasped',angle_rad=self.angle(),contacts=self.contacts('spectrometer_lid'))

    def held_cover(self):
        forces={}
        for c in self.contacts('spectrometer_lid'):forces[c['other']]=forces.get(c['other'],0)+c['force_n']
        if not all(forces.get(s,0)>.1 for s in ['left_finger','right_finger']):raise ExecutionFailure('Nicolet cover bilateral grip lost')

    def rotate_cover(self,target):
        for angle in np.linspace(self.angle(),target,max(2,int(abs(target-self.angle())/.025)+1))[1:]:
            self.held_cover();point,rotation=self.pose(angle);self.move(point,rotation,.15)
            if abs(self.angle()-angle)>.025:raise ExecutionFailure('Nicolet cover failed observed angular tracking')
        self.advance(.3);self.checkpoint('spectrometer_cover_positioned',target_rad=target,angle_rad=self.angle())

    def release_cover(self,target):
        # Unload the handle before opening. A step change from 12 N clamp
        # to a wide opening kicked the closed cover into its seating faces.
        point,rotation=self.pose(self.angle())
        for force in np.linspace(self.clamp_force or 0.,.2,12):self.clamp_force=float(force);self.advance(.03)
        opening=2*float(np.mean(self.data.qpos[7:9]));self.clamp_force=None
        for gap in np.linspace(opening,.025,20)[1:]:self.grip_target=gap/2;self.advance(.03)
        self.advance(.2);self.move(point-rotation[:,2]*.10,rotation,1.5);self.advance(1.)
        error=abs(self.angle()-target)
        if error>.01:raise ExecutionFailure('Nicolet cover not retained after release')
        self.checkpoint('spectrometer_cover_released',target_rad=target,angle_rad=self.angle(),contacts=self.contacts('spectrometer_lid'))


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',default='runs/nicolet');p.add_argument('--case',choices=['nominal','missing_handle','locked_hinge'],default='nominal');p.add_argument('--seed',type=int,default=0);p.add_argument('--timestep',type=float,choices=[.001,.0005],default=.001);a=p.parse_args()
    out=HERE/a.out;out.mkdir(parents=True,exist_ok=True);old=[x for x in out.iterdir() if x.name!='history']
    if old:
        archive=out/'history'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');archive.mkdir(parents=True)
        for x in old:x.replace(archive/x.name)
    names=['run_nicolet.py','nicolet_world.py','optical_assets.py','run_bath.py','bath_world.py','bath_assets.py','hardware_control.py','continuous_control.py','control.py','precision_ik.py','world.py','contact_safety.py','device_assets.py','extended_device_assets.py','robot_source.json','geometry/nicolet_6700/catalog.json',
           '../../assets/nicolet_6700_v1/interfaces.json','../../assets/nicolet_6700_v1/geometry_checks.json']
    pins={n:sha(HERE/n) for n in names};archive={n:'source_snapshot/'+n.replace('../','parent/') for n in names}
    for n,rel in archive.items():target=out/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(HERE/n,target)
    robot=None;cfg=None;passed=False;failure=None
    try:
        cfg=build(out/'workcell.xml',case=a.case,timestep=a.timestep);pins['workcell.xml']=sha(out/'workcell.xml')
        initial_model=load(out/'workcell.xml');initial_data=mujoco.MjData(initial_model);mujoco.mj_forward(initial_model,initial_data)
        for contact in initial_data.contact:
            contact_bodies={initial_model.body(int(initial_model.geom_bodyid[g])).name for g in contact.geom}
            if contact_bodies&{'spectrometer_lid','sample_slider'} and contact.dist<-.00001:raise ExecutionFailure('Initial optical moving-part overlap: '+str(contact_bodies))
        robot=NicoletRobot(out/'workcell.xml',cfg,seed=a.seed)
        robot.grip_cover();robot.rotate_cover(cfg['selected_open_angle_rad']);robot.release_cover(cfg['selected_open_angle_rad'])
        robot.grip_cover();robot.rotate_cover(0.);robot.release_cover(0.);passed=True
    except Exception as e:failure=type(e).__name__+': '+str(e);traceback.print_exc()
    finally:
        if robot:
            if not robot.trace or robot.data.time>robot.trace[-1][0]+1e-10:
                robot.trace.append((float(robot.data.time),robot.data.qpos.copy(),robot.data.qvel.copy(),robot.data.ctrl.copy()))
            robot.save_state();robot.close();np.savez_compressed(out/'physics_trace.npz',time=[r[0] for r in robot.trace],qpos=[r[1] for r in robot.trace],qvel=[r[2] for r in robot.trace],ctrl=[r[3] for r in robot.trace])
        if any(sha(HERE/n)!=pins[n] for n in names):passed=False;failure='Sources changed during execution'
        result=dict(status='passed' if passed else 'failed',failure=failure,case=a.case,seed=a.seed,configuration=cfg,input_sha256=pins,source_archive=archive,
            observations=robot.timeline if robot else [],simulated_seconds=float(robot.data.time) if robot else 0,
            maximum_solver_iterations=robot.maximum_solver_iterations if robot else 0,warnings=[int(w.number) for w in robot.data.warning] if robot else [],
            artifacts_sha256={n:sha(out/n) for n in ['physics_trace.npz'] if (out/n).exists()},whole_paper_validated=False)
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('NICOLET COVER',result['status'],failure,flush=True)
    return passed

if __name__=='__main__':raise SystemExit(0 if main() else 1)
