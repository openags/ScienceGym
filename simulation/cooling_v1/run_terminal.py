"""Physical wire insertion, driver operation, pull check and reverse recovery."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse
import json
import shutil
from collections import deque
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import mujoco
from scipy.spatial.transform import Rotation
from world import HERE
from terminal_world import build
from hardware_control import HardwareRobot
from control import ExecutionFailure,DOWN
from trace_store import sha
from precision_ik import solve as precise_ik

WIRE_ROTATION=Rotation.from_euler('z',np.pi/2).as_matrix()@DOWN


class TerminalRobot(HardwareRobot):
    ik=precise_ik
    def __init__(self,path,configuration,**kwargs):
        self.configuration=configuration;self.prefix=configuration['terminal']['prefix']
        self.driver_speed=0.;self.driver_mode=None;self.driver_complete=False
        self.maximum_solver_iterations=0;self.solver_limit_steps=0;self.maximum_edge_strain=0.
        self.maximum_axial_N=0.;self.next_progress=10.
        self.grip_samples=deque(maxlen=60);self.grip_observations=[]
        super().__init__(path,**kwargs)

    def advance(self,duration):
        audit_stride=max(1,round(.001/self.model.opt.timestep))
        trace_stride=max(1,round(.005/self.model.opt.timestep))
        for _ in range(max(1,round(duration/self.model.opt.timestep))):
            self.data.ctrl[:7]=self.joint_target+self.data.qfrc_bias[:7]/self.kp
            requested=-self.clamp_force if self.clamp_force is not None else 2000*(self.grip_target-np.mean(self.data.qpos[7:9]))-40*np.mean(self.data.qvel[7:9])
            self.data.ctrl[7]=np.clip(requested,-40,40);self.data.ctrl[self.model.actuator('driver_motor').id]=self.driver_speed
            mujoco.mj_step(self.model,self.data);self.physics_steps+=1
            iterations=int(np.max(self.data.solver_niter));self.maximum_solver_iterations=max(self.maximum_solver_iterations,iterations)
            if iterations>=self.model.opt.iterations:
                self.solver_limit_steps+=1;raise ExecutionFailure('Constraint solver reached its iteration limit')
            if any(w.number for w in self.data.warning):raise ExecutionFailure('MuJoCo numerical warning')
            if not np.isfinite(self.data.qpos).all():raise ExecutionFailure('Nonfinite state')
            self.maximum_edge_strain=max(self.maximum_edge_strain,float(np.max(abs(self.data.flexedge_length/self.model.flexedge_length0-1))))
            if self.maximum_edge_strain>.01:raise ExecutionFailure('Extension exceeded selected 1% edge-strain bound')
            if self.physics_steps%audit_stride==0:self.audit_contacts()
            if self.physics_steps%trace_stride==0:self.save_state()
            if self.driver_mode and self.driver_complete:
                self.save_state();return
        if self.data.time>=self.next_progress:
            print('WIRE PHYSICS',round(self.data.time,3),'mode',self.driver_mode,'active',self.active_object,flush=True)
            self.next_progress=self.data.time+10

    def save_state(self):
        if not self.trace or self.data.time>self.trace[-1][0]+1e-10:
            self.trace.append((float(self.data.time),self.data.qpos.copy(),self.data.qvel.copy(),self.data.ctrl.copy()))

    def checkpoint(self,label,**values):
        self.save_state();return super().checkpoint(label,**values)

    def contacts(self,body):
        rows=[]
        for i,c in enumerate(self.data.contact):
            names=[self.model.body(int(self.model.geom_bodyid[g])).name if g>=0 else 'wire_extension' for g in c.geom]
            if body not in names:continue
            force=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,force)
            rows.append(dict(other=names[1-names.index(body)],force_n=float(force[0]),distance_m=float(c.dist)))
        return rows

    def observe(self):
        clamp=0.;driver=np.zeros(3);finger=np.zeros(3);fingers={};clip=0.
        for i,c in enumerate(self.data.contact):
            if min(c.geom)<0:continue
            bodies=[self.model.body(int(self.model.geom_bodyid[g])).name for g in c.geom]
            force=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,force);world=c.frame.reshape(3,3).T@force[:3]
            if {self.prefix+'_plate','wire'}<=set(bodies):clamp+=force[0]
            if {self.prefix+'_screw','driver_rotor'}<=set(bodies):driver+=world*(1 if bodies[1]==self.prefix+'_screw' else -1)
            if 'wire' in bodies:
                other=bodies[1-bodies.index('wire')]
                if other in {'left_finger','right_finger'}:
                    fingers[other]=fingers.get(other,0.)+float(force[0]);finger+=world*(1 if bodies[1]=='wire' else -1)
                if other.startswith('wire_clip_leaf'):clip+=force[0]
        axis=np.array(self.configuration['terminal']['insertion_axis']);entry=np.array(self.configuration['entry_m']);tip=self.data.site('wire_tip').xpos
        return dict(time_s=float(self.data.time),depth_m=float(np.dot(tip-entry,axis)),tip_m=tip.tolist(),
            clamp_normal_N=float(clamp),driver_axial_N=float(-driver[2]),driver_force_world_N=driver.tolist(),
            finger_normal_N=fingers,finger_axial_N=float(np.dot(finger,axis)),clip_normal_N=float(clip),
            screw_advance_m=float(self.data.joint(self.prefix+'_advance').qpos[0]),screw_turn_rad=float(self.data.joint(self.prefix+'_turn').qpos[0]))

    def audit_contacts(self):
        super().audit_contacts()
        finger_forces={'left_finger':0.,'right_finger':0.}
        for i,c in enumerate(self.data.contact):
            bodies=[self.model.body(int(self.model.geom_bodyid[g])).name if g>=0 else 'wire_extension' for g in c.geom]
            force=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,force)
            if set(bodies)&{'left_finger','right_finger'}:
                other=next((n for n in bodies if n not in {'left_finger','right_finger'}),None)
                if other not in {'wire','hand',None} and force[0]>.02:raise ExecutionFailure('Unintended wire-gripper contact: '+str(bodies))
                if other=='wire':
                    for side in finger_forces:
                        if side in bodies:finger_forces[side]+=float(force[0])
            if 'driver_rotor' in bodies:
                other=bodies[1-bodies.index('driver_rotor')]
                if other not in {self.prefix+'_screw','driver_mount','hand'} and force[0]>.05:
                    raise ExecutionFailure('Driver contacted unintended surface: '+str(bodies))
        self.grip_samples.append((float(self.data.time),finger_forces['left_finger'],finger_forces['right_finger']))
        if self.driver_mode:
            observation=self.observe();self.maximum_axial_N=max(self.maximum_axial_N,abs(observation['driver_axial_N']))
            if abs(observation['driver_axial_N'])>1.:raise ExecutionFailure('Driver exceeded selected 1 N axial bound')
            if observation['clamp_normal_N']>6.:raise ExecutionFailure('Terminal exceeded selected 6 N clamp bound')
            reached=(self.driver_mode=='tighten' and observation['clamp_normal_N']>=4.) or (self.driver_mode=='loosen' and observation['screw_advance_m']>-.00003)
            if reached:self.driver_speed=0.;self.driver_complete=True

    def held(self):
        # Contact features on round insulation can switch between samples.
        # Check bilateral impulse over 50 ms, bounded gaps and the actual
        # wire position inside the needle pads, instead of a duty threshold
        # that can accept a wire on the pad edge or reject stable loading.
        samples=np.array([r for r in self.grip_samples if r[0]>=self.data.time-.050001])
        bilateral=np.all(samples[:,1:]>.02,axis=1) if len(samples) else np.array([],bool)
        gap=longest=0
        for present in bilateral:
            gap=0 if present else gap+1;longest=max(longest,gap)
        body=self.data.body('wire').xmat.reshape(3,3);hand=self.data.body('hand').xmat.reshape(3,3)
        delta=self.data.site_xpos[self.site]-self.position('wire');axis=body@np.array(self.configuration['terminal']['insertion_axis'])
        axial=float(np.dot(delta,axis));radial=float(np.linalg.norm(delta-axial*axis));angle=float(np.arccos(np.clip(abs(np.dot(axis,hand[:,0])),-1,1)))
        observation=dict(time_s=float(self.data.time),samples=len(samples),bilateral_fraction=float(bilateral.mean()) if len(samples) else 0.,
            mean_normal_N=samples[:,1:].mean(axis=0).tolist() if len(samples) else [0.,0.],longest_gap_s=longest*.001,
            grasp_axial_offset_m=axial,grasp_radial_offset_m=radial,wire_pad_axis_angle_rad=angle)
        self.grip_observations.append(observation)
        if (len(samples)<45 or longest>3 or min(observation['mean_normal_N'])<.2
            or abs(axial)>self.configuration['grasp_axial_limit_m'] or radial>self.configuration['grasp_radial_limit_m']
            or angle>self.configuration['grasp_axis_angle_limit_rad']):
            raise ExecutionFailure('Wire sustained bilateral grip lost: '+str(observation))
        return body.T@(self.data.site_xpos[self.site]-self.position('wire')),body.T@self.data.site_xmat[self.site].reshape(3,3)

    def position_wire(self,target,duration=.4):
        self.held()
        # A grasp defines one rigid tool-to-part transform. Re-estimating it
        # after every waypoint accumulates tracking error as a new offset,
        # progressively walking the wire toward the edge of the needle pad.
        offset,rotation=self.wire_grasp_transform
        self.move(np.asarray(target)+offset,rotation,duration)

    def grasp_wire(self,lift):
        self.site=self.model.site('tcp').id;self.active_object='wire';self.finger(.003)
        p=self.grasp_site('wire');rotation=self.data.body('wire').xmat.reshape(3,3)@WIRE_ROTATION
        self.move(p+[0,0,.10],rotation,1.5);self.move(p,rotation,1.5)
        for _ in range(3):
            rotation=self.data.body('wire').xmat.reshape(3,3)@WIRE_ROTATION
            self.move(self.grasp_site('wire'),rotation,.2)
        # Close gently around the observed wire axis. A position closure
        # rolled the released round lead beyond the unchanged 0.1 rad
        # alignment bound in the half-step run's final regrasp.
        for force in np.linspace(.2,1.,20):self.clamp_force=float(force);self.advance(.02)
        rotation=self.data.body('wire').xmat.reshape(3,3)@WIRE_ROTATION
        self.move(self.grasp_site('wire'),rotation,.4)
        for force in np.linspace(1.,self.configuration['wire_grip_N'],20):self.clamp_force=float(force);self.advance(.02)
        self.advance(.2)
        self.wire_grasp_transform=self.held()
        if lift:self.move(self.data.site_xpos[self.site]+[0,0,lift],rotation,1.5)
        self.checkpoint('wire_grasped',lift_m=lift,observation=self.observe())

    def drive(self,tighten):
        self.site=self.model.site('driver_tcp').id;self.active_object=self.prefix+'_screw';self.finger(.016)
        center=self.position(self.prefix+'_screw');self.move(center+[0,0,.10],DOWN,2.);self.move(center+[0,0,.005],DOWN,1.5)
        for _ in range(100):
            head=self.data.body(self.prefix+'_screw').xmat.reshape(3,3);rotor=self.data.body('driver_rotor').xmat.reshape(3,3)
            error=(np.arctan2(head[1,0],head[0,0])-np.arctan2(rotor[1,0],rotor[0,0])+np.pi/2)%np.pi-np.pi/2
            if abs(error)<.005:break
            self.driver_speed=float(np.clip(6*error,-2,2));self.advance(.03)
        else:raise ExecutionFailure('Driver slot phase failed to align')
        self.driver_speed=0.;self.advance(.1)
        seat=None
        for offset in np.linspace(.0005,.00005,46):
            target=self.position(self.prefix+'_screw')+[0,0,offset];self.move(target,DOWN,.06);self.advance(.04)
            observation=self.observe()
            if observation['driver_axial_N']>.6:raise ExecutionFailure('Driver seating exceeded selected 0.6 N bound')
            if observation['driver_axial_N']>.08:seat=target-self.position(self.prefix+'_screw');break
        if seat is None:raise ExecutionFailure('Driver did not seat in the physical slot')
        self.checkpoint('driver_seated',operation='tighten' if tighten else 'loosen',observation=observation)
        if not tighten:
            # The slot sidewalls transmit torque without loading its floor.
            # Relieve the selected 20 um axial preload before backing out;
            # otherwise the rising screw head drives the bit above 1 N.
            self.move(self.data.site_xpos[self.site]+[0,0,.00002],DOWN,.4);self.advance(.2)
            seat=self.data.site_xpos[self.site].copy()-self.position(self.prefix+'_screw')
        self.driver_mode='tighten' if tighten else 'loosen';self.driver_complete=False;self.driver_speed=-2. if tighten else 2.
        start=float(self.data.time)
        while not self.driver_complete and self.data.time-start<30:
            target=self.position(self.prefix+'_screw')+seat
            self.joint_target=self.ik(target,DOWN);self.advance(.01)
        completed=self.driver_complete;self.driver_speed=0.;self.driver_mode=None;self.driver_complete=False
        self.joint_target=self.data.qpos[:7].copy()
        if not completed:raise ExecutionFailure('Driver did not reach the observed thread/clamp condition')
        self.checkpoint('terminal_tightened' if tighten else 'terminal_opened',observation=self.observe())
        self.move(self.data.site_xpos[self.site]+[0,0,.10],DOWN,1.5);self.advance(1.)
        observation=self.observe();self.checkpoint('driver_retracted',operation='tighten' if tighten else 'loosen',observation=observation)
        if tighten and observation['clamp_normal_N']<1.:raise ExecutionFailure('Clamp preload lost after driver withdrawal')

    def pull_check(self):
        # The transport grip is deliberately light. Regrip the insulated
        # extension at the declared pull-test load, then regulate the actual
        # axial reaction rather than infer tension from TCP displacement.
        self.clamp_force=self.configuration['wire_pull_grip_N'];self.advance(.2)
        axis=np.array(self.configuration['terminal']['insertion_axis']);before=self.position('wire')
        start=self.data.site_xpos[self.site].copy();rotation=self.data.site_xmat[self.site].reshape(3,3).copy()
        distance=0.;stable=0.;records=[]
        for _ in range(1000):
            observation=self.observe();force=abs(observation['finger_axial_N'])
            speed=float(np.clip(.01*(1.1-force),-.0002,.001));distance=max(0.,distance+speed*.01)
            if distance>.002:raise ExecutionFailure('Pull test exhausted selected 2 mm travel bound')
            self.joint_target=self.ik(start-axis*distance,rotation);self.advance(.01)
            observation=self.observe();force=abs(observation['finger_axial_N'])
            displacement=float(np.linalg.norm(self.position('wire')-before))
            records.append(dict(time_s=float(self.data.time),force_N=force,displacement_m=displacement,command_travel_m=distance))
            if displacement>.0002:raise ExecutionFailure('Wire slipped during physical pull check')
            if force>1.5:raise ExecutionFailure('Pull test exceeded selected 1.5 N stop bound')
            stable=stable+.01 if force>=1. else 0.
            if stable>=.30:break
        else:raise ExecutionFailure('Physical pull did not sustain 1 N for 0.3 s')
        self.checkpoint('wire_pull_checked',observation=self.observe(),displacement_m=displacement,force_observations=records,
            sustained_seconds=stable,minimum_force_N=min(r['force_N'] for r in records[-30:]))
        self.move(start,rotation,.5);self.finger(.003);self.move(self.data.site_xpos[self.site]+[0,0,.10],rotation,1.5)


def execute(robot,limit):
    cfg=robot.configuration;axis=np.array(cfg['terminal']['insertion_axis']);target=np.array(cfg['wire_inserted_grasp_m']);park=np.array(cfg['wire_park_m'])
    robot.grasp_wire(.10)
    if limit=='grasp':return
    robot.position_wire(target-axis*.040+[0,0,.10],2.)
    robot.position_wire(target-axis*.040,1.5)
    for offset in np.linspace(.040,0,81)[1:]:robot.position_wire(target-axis*offset,.08)
    observation=robot.observe();robot.checkpoint('wire_inserted_while_held',observation=observation)
    if not .0045<observation['depth_m']<.0055:raise ExecutionFailure('Wire did not reach selected insertion depth')
    robot.finger(.003);robot.move(robot.data.site_xpos[robot.site]+[0,0,.10],WIRE_ROTATION,1.5);robot.advance(1.)
    observation=robot.observe();robot.checkpoint('wire_retained_by_fixture',observation=observation)
    if not (.004<observation['depth_m']<.006 and observation['clip_normal_N']>.01):raise ExecutionFailure('Wire not held by passive fixture')
    if limit=='insertion':return
    robot.drive(True)
    robot.grasp_wire(0)
    robot.pull_check()
    if limit=='retention':return
    robot.drive(False);robot.grasp_wire(0)
    for distance in np.linspace(.0005,.040,80):robot.position_wire(target-axis*distance,.06)
    robot.checkpoint('wire_withdrawn',observation=robot.observe())
    robot.position_wire(target-axis*.040+[0,0,.10],1.5);robot.position_wire(park+[0,0,.10],2.)
    for height in np.linspace(.10,.00005,35):robot.position_wire(park+[0,0,height],.10)
    robot.finger(.003);robot.move(robot.data.site_xpos[robot.site]+[0,0,.10],WIRE_ROTATION,1.5);robot.advance(1.)
    error=float(np.linalg.norm(robot.position('wire')-park));robot.checkpoint('wire_returned',error_m=error,observation=robot.observe())
    if error>.002:raise ExecutionFailure('Wire did not return to its supported staging position')


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',default='runs/terminal_debug/robot');p.add_argument('--pin',type=int,default=3)
    p.add_argument('--limit',choices=['grasp','insertion','retention']);p.add_argument('--no-clamp',action='store_true');p.add_argument('--no-bit',action='store_true')
    p.add_argument('--seed',type=int,default=0);p.add_argument('--timestep',type=float,choices=[.0001,.00005],default=.0001);a=p.parse_args()
    out=HERE/a.out;out.mkdir(parents=True,exist_ok=True);old=[x for x in out.iterdir() if x.name!='history']
    if old:
        history=out/'history'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');history.mkdir(parents=True)
        for x in old:x.replace(history/x.name)
    names=['run_terminal.py','terminal_world.py','terminal_mechanism.py','hardware_control.py','continuous_control.py','control.py','world.py',
        'contact_safety.py','precision_ik.py','device_assets.py','extended_device_assets.py','geometry/mcc_usb_tc/catalog.json','robot_source.json',
        '../../assets/mcc_usb_tc_v1/interfaces.json','../../assets/mcc_usb_tc_v1/geometry_checks.json']
    pins={n:sha(HERE/n) for n in names};archive={n:'source_snapshot/'+n.replace('../','parent/') for n in names}
    for n in names:
        dest=out/archive[n];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(HERE/n,dest)
    robot=None;configuration=None;failure=None;passed=False
    try:
        configuration=build(out/'workcell.xml',pin=a.pin,clamp=not a.no_clamp,bit=not a.no_bit,timestep=a.timestep);pins['workcell.xml']=sha(out/'workcell.xml')
        robot=TerminalRobot(out/'workcell.xml',configuration,seed=a.seed);execute(robot,a.limit);passed=True
    except BaseException as error:failure=type(error).__name__+': '+str(error);print(failure,flush=True)
    finally:
        if robot:
            robot.save_state();robot.close();np.savez_compressed(out/'physics_trace.npz',time=[r[0] for r in robot.trace],qpos=[r[1] for r in robot.trace],qvel=[r[2] for r in robot.trace],ctrl=[r[3] for r in robot.trace])
        if any(sha(HERE/n)!=pins[n] for n in names):passed=False;failure='Source changed during execution'
        result=dict(status=('development_pass' if a.limit else 'passed') if passed else 'failed',failure=failure,configuration=configuration,seed=a.seed,
            input_sha256=pins,source_archive=archive,engine_version=mujoco.__version__,observations=robot.timeline if robot else [],
            simulated_seconds=float(robot.data.time) if robot else 0,development_limit=a.limit,
            grip_observations=robot.grip_observations if robot else [],
            numerics=dict(maximum_solver_iterations=robot.maximum_solver_iterations,solver_limit_steps=robot.solver_limit_steps,
                warnings=[int(w.number) for w in robot.data.warning],physics_steps=robot.physics_steps,maximum_edge_strain=robot.maximum_edge_strain) if robot else None,
            artifacts_sha256={n:sha(out/n) for n in ['physics_trace.npz'] if (out/n).exists()},whole_paper_validated=False,
            scope='One selected 24 AWG extension end: staged grasp, physical insertion/fixture retention, contact-driven screw operation, robot pull check and reverse recovery. Fine-wire connector, complete thermocouple path and electrical measurements remain separate obligations.')
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('TERMINAL RESULT',result['status'],failure,flush=True)
    return passed


if __name__=='__main__':raise SystemExit(0 if main() else 1)
