"""Development: place a block in its cradle, load the bath and recover it."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse,json,shutil,traceback
from datetime import datetime,timezone
import numpy as np,mujoco
from scipy.spatial.transform import Rotation
from world import HERE
from bath_loading_world import build
from run_bath import BathRobot
from hardware_control import HardwareRobot
from support_observation import support_load
from control import DOWN,ExecutionFailure
from trace_store import sha
from precision_ik import solve as precise_ik


class LoadingRobot(BathRobot):
    def advance(self,duration):
        # Estimate the part of the payload weight currently borne by the
        # gripper, from external support contacts. Compensate that load only
        # through the seven bounded arm actuators. Robot-only gravity
        # compensation otherwise lets the wrist sag into the stand guides.
        if not hasattr(self,'payload_feedforward'):
            self.payload_feedforward=0.
            self.payload_jacobian=np.zeros((3,self.model.nv))
        dt=self.model.opt.timestep
        for _ in range(max(1,round(duration/dt))):
            names=([self.active_object] if self.active_object=='calibration_block' else
                   ['block_cradle','calibration_block'] if self.active_object=='block_cradle' else [])
            names=names if self.clamp_force is not None else []
            torque=np.zeros(7);weight=0.
            if names:
                ids={self.model.body(n).id for n in names};masses=np.array([self.model.body_mass[i] for i in ids])
                center=sum(self.data.xipos[i]*mass for i,mass in zip(ids,masses))/sum(masses)
                weight=float(sum(masses)*9.81);supported=0.
                for i,c in enumerate(self.data.contact):
                    bodies=[int(self.model.geom_bodyid[g]) for g in c.geom]
                    if sum(b in ids for b in bodies)!=1:continue
                    other=bodies[1] if bodies[0] in ids else bodies[0]
                    if self.model.body(other).name in {'left_finger','right_finger','hand'}:continue
                    force=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,force)
                    supported+=(c.frame.reshape(3,3).T@force[:3])[2]*(1 if bodies[1] in ids else -1)
                target=np.clip(weight-supported,0.,weight)
                self.payload_feedforward+=(target-self.payload_feedforward)*min(1.,dt/.15)
                mujoco.mj_jac(self.model,self.data,self.payload_jacobian,None,center,self.model.body('hand').id)
                torque=self.payload_jacobian[2,:7]*self.payload_feedforward
            else:self.payload_feedforward=0.
            self.data.ctrl[:7]=self.joint_target+(self.data.qfrc_bias[:7]+torque)/self.kp
            requested=-self.clamp_force if self.clamp_force is not None else 2000*(self.grip_target-np.mean(self.data.qpos[7:9]))-40*np.mean(self.data.qvel[7:9])
            self.data.ctrl[7]=np.clip(requested,-40,40);mujoco.mj_step(self.model,self.data);self.physics_steps+=1
            iterations=int(np.max(self.data.solver_niter));self.maximum_solver_iterations=max(self.maximum_solver_iterations,iterations)
            if iterations>=self.model.opt.iterations:raise ExecutionFailure('Bath constraint solver exhausted its iteration limit')
            if any(w.number for w in self.data.warning) or not np.isfinite(self.data.qpos).all():raise ExecutionFailure('Bath numerical warning or nonfinite state')
            self.audit_contacts()
            if self.physics_steps%5==0:self.save_state()
        if self.data.time>=self.next_progress:print('BATH PHYSICS',round(self.data.time,3),'active',self.active_object,'payload compensation N',round(self.payload_feedforward,3),flush=True);self.next_progress=self.data.time+10

    def ik(self,xyz,rotation=DOWN):
        if self.active_object=='bath_lid':return super().ik(xyz,rotation)
        return precise_ik(self,xyz,rotation)

    def audit_contacts(self):
        HardwareRobot.audit_contacts(self)
        forces={'left_finger':0.,'right_finger':0.}
        for i,c in enumerate(self.data.contact):
            names=[self.model.body(int(self.model.geom_bodyid[g])).name for g in c.geom]
            if 'bath' in names and set(names)&{'block_cradle','calibration_block'}:
                f=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,f)
                if f[0]>.5:raise ExecutionFailure('Calibration payload contacts bath enclosure: '+str(names))
            if self.active_object=='bath_lid' and 'bath_lid' in names and set(names)&{'block_cradle','calibration_block'}:
                f=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,f)
                if f[0]>.05:raise ExecutionFailure('Lid route contacts staged calibration load: '+str(names))
            sides=set(names)&set(forces)
            if not sides:continue
            other=next((n for n in names if n not in forces),None);f=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,f)
            if other not in {self.active_object,'hand',None} and f[0]>.05:raise ExecutionFailure('Load gripper contacted unintended body '+str(names))
            if other==self.active_object:
                for side in sides:forces[side]+=max(0.,float(f[0]))
        if max(forces.values())>(25. if self.active_object=='bath_lid' else 35.):raise ExecutionFailure('Load handling finger force exceeded bound: '+str(forces))

    def payload_held(self,name):
        forces={}
        for c in self.contacts(name):forces[c['other']]=forces.get(c['other'],0)+c['force_n']
        if not all(forces.get(side,0)>.1 for side in ['left_finger','right_finger']):raise ExecutionFailure('Load bilateral grip lost: '+name)
        rotation=self.data.body(name).xmat.reshape(3,3)
        return rotation.T@(self.data.site_xpos[self.site]-self.position(name)),rotation.T@self.data.site_xmat[self.site].reshape(3,3)

    def grasp_payload(self,name):
        self.site=self.model.site('tcp').id;self.active_object=name
        block=name=='calibration_block';width=.05 if block else self.configuration['cradle_grasp_width_m']
        rotation=np.array([[0.,1.,0.],[0.,0.,1.],[1.,0.,0.]]) if block else DOWN
        # Centre the yoke on the 44.5 mm source pad datum, not on its
        # 50 mm tip. The side-grasp block uses its separately selected datum.
        pad_offset=rotation@np.array([0,0,-.005 if block else .0005]);self.finger(self.configuration['block_release_opening_m'] if block else width+.018);point=self.grasp_site(name)+pad_offset
        if not block:
            # Reorient the empty hand away from the near-base singularity.
            # The side-grasp withdrawal and overhead yoke approach are each
            # reachable, but interpolating between them beside the stand is
            # not. This high front waypoint was swept for arm clearance.
            via=np.array([.40,-.16,1.12])
            self.move(via,self.data.site_xmat[self.site].reshape(3,3).copy(),1.8)
            self.move(via,rotation,1.8)
        approach=np.array([0,-.04,0]) if block else np.array([0,0,.12])
        self.move(point+approach+[0,0,.10 if block else 0],rotation,1.8)
        if block:self.move(point+approach,rotation,1.)
        self.move(point,rotation,1.8)
        for _ in range(2):self.move(self.grasp_site(name)+pad_offset,rotation,.3)
        self.finger(width-.004)
        # Centre the observed contact pads under a light clamp before
        # increasing load. The supported copper block must not be pushed
        # sideways by a single loaded finger to find the opposite jaw.
        self.clamp_force=2.;self.advance(.15);command=self.grasp_site(name)+pad_offset
        for _ in range(12):
            command+=np.clip((self.grasp_site(name)+pad_offset-self.data.site_xpos[self.site])*.7,-.0003,.0003)
            self.move(command,rotation,.15)
            forces={}
            for c in self.contacts(name):forces[c['other']]=forces.get(c['other'],0.)+c['force_n']
            if all(forces.get(s,0.)>.1 for s in ['left_finger','right_finger']):break
        else:raise ExecutionFailure('Cannot centre load grip without pushing supported payload')
        for force in np.linspace(2.,self.configuration['block_grip_N' if block else 'cradle_grip_N'],20):self.clamp_force=float(force);self.advance(.02)
        self.advance(.3)
        self.payload_held(name);before={n:self.position(n) for n in ['calibration_block','block_cradle']}
        if block and np.linalg.norm(before[name]-self.position('block_cradle')-self.configuration['block_in_cradle_offset_m'])<.03:
            self.move(self.data.site_xpos[self.site]+[0,0,self.configuration['block_entry_clearance_m']],rotation,1.)
            self.move(self.data.site_xpos[self.site]+[0,-.12,0],rotation,1.5)
        if not block:
            start=self.data.site_xpos[self.site].copy()
            for dz in np.linspace(.0001,.004,40):self.move(start+[0,0,dz],rotation,.08)
            # Joint interpolation over one 120 mm lift bowed the wrist
            # sideways while the loaded yoke was still inside its guide
            # pins. Resolve the loaded lift as a Cartesian path instead.
            start=self.data.site_xpos[self.site].copy()
            for dz in np.linspace(.002,.12,60):self.move(start+[0,0,dz],rotation,.08)
        else:self.move(self.data.site_xpos[self.site]+[0,0,.12],rotation,2.)
        lifted=float(self.position(name)[2]-before[name][2])
        if lifted<.10:raise ExecutionFailure('Load failed observed lift: '+name)
        if not block:
            displacement=self.position('calibration_block')-self.position('block_cradle')
            if np.linalg.norm(displacement-self.configuration['block_in_cradle_offset_m'])>.002:raise ExecutionFailure('Block escaped its physical cradle')
        self.checkpoint('bath_payload_lifted',body=name,lift_m=lifted,contacts=self.contacts(name))

    def place_payload(self,name,target,support):
        target=np.array(target);start=self.position(name)
        height=max(start[2],target[2]+(self.configuration['block_transfer_clearance_m'] if name=='calibration_block' else .12))
        correction=np.zeros(3)
        # Keep the measured post-lift tool transform fixed. Recomputing the
        # relative orientation at each waypoint integrated gravity-induced
        # tracking error into a growing wrist pitch. Position feedback still
        # compensates weight through the arm actuators; grip is rechecked.
        carry_offset=self.data.site_xpos[self.site]-self.position(name)
        carry_rotation=self.data.site_xmat[self.site].reshape(3,3).copy()
        def move_center(desired,duration):
            nonlocal correction
            self.payload_held(name);rotation=carry_rotation
            self.move(desired+carry_offset+correction,rotation,duration)
            # External payload weight is not part of robot-only gravity
            # compensation. Integrate observed pose error through actuators.
            gain,increment=(.4,.0002) if name=='block_cradle' else (.7,.001)
            correction=np.clip(correction+np.clip((desired-self.position(name))*gain,-increment,increment),-.010,.010)
            return rotation
        if name=='calibration_block' and support=='block_cradle':
            # Approach beneath the balanced yoke. The body and gripper stay
            # below the bar until the arm has withdrawn toward the front. The
            # staging guide pins end 16 mm above the block's seated datum;
            # use 30 mm entry height to clear them before descending.
            pre=target+[0,-.12,self.configuration['block_entry_clearance_m']]
            move_center(np.r_[start[:2],height],1.2)
            for u in np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(pre[:2]-start[:2])/.025))+1))[1:]:
                move_center(np.r_[start[:2]+u*(pre[:2]-start[:2]),height],.55)
            move_center(pre,1.8)
            for u in np.linspace(0,1,13)[1:]:rotation=move_center(pre+np.array([0,.12*u,0]),.3)
            clearance=self.configuration['block_entry_clearance_m']
        else:
            move_center(np.r_[start[:2],height],1.2)
            if name=='block_cradle':
                # Go around the projecting AC150 head. The earlier direct
                # diagonal crossed its left face with the loaded yoke.
                corner=np.array([start[0],target[1]]) if support=='bath_load_support' else np.array([target[0],start[1]])
                points=[corner,target[:2]];origin=start[:2]
                for end in points:
                    for u in np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(end-origin)/.010))+1))[1:]:
                        rotation=move_center(np.r_[origin+u*(end-origin),height],.6)
                    origin=end
            else:
                for u in np.linspace(0,1,11)[1:]:rotation=move_center(np.r_[start[:2]+u*(target[:2]-start[:2]),height],.45)
            clearance=height-target[2]
        descent=np.linspace(clearance,.006,max(2,int(np.ceil((clearance-.006)/.006))+1))[1:]
        for gap in np.r_[descent,np.arange(.0055,-.00001,-.0005)]:
            rotation=move_center(target+[0,0,gap],.2)
        self.finger(self.configuration['block_release_opening_m'] if name=='calibration_block' else .025)
        if name=='calibration_block' and support=='block_cradle':self.move(self.data.site_xpos[self.site]+[0,-.12,0],rotation,1.5)
        self.move(self.data.site_xpos[self.site]+[0,0,.15],rotation,1.8);self.advance(.6)
        error=float(np.linalg.norm(self.position(name)-target));tilt=float(np.arccos(np.clip(self.data.body(name).xmat[8],-1,1)))
        load=support_load(self.model,self.data,name,support);required_weight=load['body_weight_n']
        if name=='block_cradle':required_weight+=float(self.model.body_mass[self.model.body('calibration_block').id])*9.81
        if error>.002 or tilt>.035 or load['vertical_force_n']<.8*required_weight:raise ExecutionFailure('Load placement failed '+name+' '+str((error,tilt,load['vertical_force_n'],required_weight)))
        self.checkpoint('bath_payload_supported',body=name,support=support,error_m=error,tilt_rad=tilt,load=load,required_weight_N=required_weight)
        if name=='block_cradle':
            block_load=support_load(self.model,self.data,'calibration_block','block_cradle')
            if block_load['vertical_force_n']<.8*block_load['body_weight_n']:raise ExecutionFailure('Cradle no longer supports block')
            self.checkpoint('bath_block_retained_in_cradle',load=block_load,relative_position_m=(self.position('calibration_block')-self.position('block_cradle')).tolist())


def execute(robot,limit):
    cfg=robot.configuration;robot.grasp_lid();robot.place_lid(cfg['lid_park_body_m'],'lid_stand')
    robot.grasp_payload('calibration_block');robot.place_payload('calibration_block',robot.position('block_cradle')+cfg['block_in_cradle_offset_m'],'block_cradle')
    if limit=='cradle':return
    robot.grasp_payload('block_cradle');robot.place_payload('block_cradle',cfg['cradle_bath_target_m'],'bath_load_support')
    if limit=='loaded':return
    robot.grasp_payload('block_cradle');robot.place_payload('block_cradle',cfg['cradle_park_m'],'block_cradle_stand')
    robot.grasp_payload('calibration_block');robot.place_payload('calibration_block',cfg['block_park_m'],'calibration_block_stand')
    robot.grasp_lid();robot.place_lid(cfg['lid_closed_body_m'],'bath')


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',default='runs/bath_debug/loading');p.add_argument('--limit',choices=['cradle','loaded']);a=p.parse_args();out=HERE/a.out;out.mkdir(parents=True,exist_ok=True)
    old=[x for x in out.iterdir() if x.name!='history']
    if old:
        archive=out/'history'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');archive.mkdir(parents=True)
        for x in old:x.replace(archive/x.name)
    names=['run_bath_loading.py','bath_loading_world.py','run_bath.py','bath_world.py','bath_assets.py','hardware_control.py','continuous_control.py','control.py','precision_ik.py','world.py','contact_safety.py','support_observation.py','device_assets.py','extended_device_assets.py','robot_source.json','geometry/thermo_a25_ac150/catalog.json']
    pins={n:sha(HERE/n) for n in names}
    for n in names:
        target=out/'source_snapshot'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(HERE/n,target)
    robot=None;configuration=None;passed=False;failure=None
    try:
        configuration=build(out/'workcell.xml');pins['workcell.xml']=sha(out/'workcell.xml');robot=LoadingRobot(out/'workcell.xml',configuration)
        payload=sum(float(robot.model.body_mass[robot.model.body(n).id]) for n in ['calibration_block','block_cradle'])
        if payload>3.:raise ExecutionFailure('Loaded cradle exceeds selected robot payload')
        execute(robot,a.limit);passed=True
    except Exception as error:failure=type(error).__name__+': '+str(error);traceback.print_exc()
    finally:
        if robot:
            robot.save_state();robot.close();np.savez_compressed(out/'physics_trace.npz',time=[r[0] for r in robot.trace],qpos=[r[1] for r in robot.trace],qvel=[r[2] for r in robot.trace],ctrl=[r[3] for r in robot.trace])
        if any(sha(HERE/n)!=pins[n] for n in names):passed=False;failure='Sources changed during execution'
        result=dict(status='development_pass' if passed else 'failed',failure=failure,configuration=configuration,development_limit=a.limit,
            observations=robot.timeline if robot else [],input_sha256=pins,source_archive='source_snapshot',simulated_seconds=float(robot.data.time) if robot else 0,
            maximum_solver_iterations=robot.maximum_solver_iterations if robot else 0,warnings=[int(w.number) for w in robot.data.warning] if robot else [],
            artifacts_sha256={n:sha(out/n) for n in ['physics_trace.npz'] if (out/n).exists()},whole_paper_validated=False)
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('BATH LOAD',result['status'],failure,flush=True)
    return passed


if __name__=='__main__':raise SystemExit(0 if main() else 1)
