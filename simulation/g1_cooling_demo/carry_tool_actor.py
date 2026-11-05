"""Visual pickup followed by loaded withdrawal, stepping, return and release.

The short out-and-back route develops the carrying handoff required before
cross-station work. It is not a paper branch. The actor receives only the same
native camera and proprioceptive inputs as the visual pickup. A rigid grasp
hypothesis is used for collision planning only; the plant tool stays passive.
"""
import argparse
import copy
import itertools
import json
import pickle
from pathlib import Path
import sys

import mujoco
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation

from visual_tool_actor import ToolActor as VisualPickup
from dex3_tool_actor import ToolActor as Pickup
from quasistatic_walking import QuasistaticWalker
from source_proximity import SourceClearance, transform
from ftir_hand import ArmIK


def pose(site):
    T=np.eye(4);T[:3,:3]=site.xmat.reshape(3,3);T[:3,3]=site.xpos
    return T


class CarryClearance:
    """Arm and hypothesized tool versus observed surfaces and public map.

    Original hand-internal assemblies and the legs are not certified by this
    arm guard. The independent full-plant evaluator retains those obligations.
    """
    def __init__(self, actor):
        p=actor.planner
        # The state predictor disables native contacts. Use an independent
        # copy to screen the actual source collision shapes as well as meshes.
        self.m=copy.copy(p.m)
        self.m.opt.disableflags &= ~int(mujoco.mjtDisableBit.mjDSBL_CONTACT)
        self.d=mujoco.MjData(self.m)
        # The pickup planner's positive-elbow search family is not a source
        # limit. Loaded withdrawal may use the complete official joint range,
        # retaining ArmIK's 5 mrad source-limit margin and geometric checks.
        self.ik=ArmIK(self.m)
        self.d.qpos[:]=actor.d.qpos;mujoco.mj_forward(self.m,self.d)
        self.environment=trimesh.collision.CollisionManager()
        meshes={n:v for n,v in p.environment_meshes.items() if n!='observed_tool_shape'}
        for n,mesh in meshes.items():
            self.environment.add_object(n,mesh,transform(p.environment._objs[n]['obj']))
        from robot_source_meshes import source_adjacency
        self.clearance=SourceClearance(self.m,self.d,p.robot,p.source,self.environment,meshes,
            p.ik.joints,source_adjacency(self.m,p.source),check_fixed_environment=False)
        self.tool=actor.mesh
        self.wrist_from_tool=np.linalg.inv(np.asarray(actor.geometry['source_tool_from_wrist']))
        self.allowed={r['body'] for r in actor.geometry['robot_contact_features']}
        self.robot=p.robot

    def check(self,q):
        self.d.qpos[:]=q;mujoco.mj_kinematics(self.m,self.d);mujoco.mj_comPos(self.m,self.d)
        mujoco.mj_collision(self.m,self.d)
        penetrations=[dict(parts=[self.m.geom(g).name for g in c.geom],distance_m=float(c.dist))
            for c in self.d.contact if c.dist<0.]
        if penetrations:
            return dict(clear=False,kind='native_source_self_contact',contacts=penetrations)
        self.clearance.fixed_state=self.d.qpos[self.clearance.fixed].copy()
        arm=self.clearance.check(.001)
        if not arm['clear']:return arm
        T=pose(self.d.site('right_wrist_reference'))@self.wrist_from_tool
        distance=float(self.environment.min_distance_single(self.tool,T))
        if distance<.001:
            return dict(clear=False,kind='hypothesized_tool_environment',distance_m=distance)
        for name in self.robot._objs:
            b=self.d.body(name);self.robot.set_transform(name,pose(b))
        collision,names=self.robot.in_collision_single(self.tool,T,return_names=True)
        unexpected=sorted(set(names)-self.allowed)
        if collision and unexpected:
            return dict(clear=False,kind='hypothesized_tool_robot',parts=unexpected)
        return dict(clear=True,tool_environment_distance_m=distance,
                    tool_pose_basis='source grasp transform and own wrist; slip not observed')


def plan_carry_arm(actor):
    """Screen a raised, wrist-rotating withdrawal from the estimated grasp.

    Fixed-base, sampled planning does not certify body motion or execution.
    Every candidate uses original source joint limits and the held-tool guard.
    """
    guard=actor.guard;ik=guard.ik;initial=actor.d.qpos.copy()
    R=actor.return_rotation
    start=actor.return_wrist+R@actor.center_offset+[0.,0.,actor.lift_height]
    raised=start+[0.,0.,.05];end=raised+actor.withdraw_delta
    attempts=[]

    def segment(q,a,b,rotation_vector):
        qs=[];rows=[]
        for u in np.linspace(0.,1.,51):
            guard.d.qpos[:]=q;mujoco.mj_kinematics(actor.m,guard.d)
            rotation=R@Rotation.from_rotvec(rotation_vector*u).as_matrix()
            joints,pe,re=ik.solve(guard.d,a+u*(b-a),rotation,q[ik.qa])
            q=q.copy();q[ik.qa]=joints
            clearance=guard.check(q)
            rows.append(dict(fraction=float(u),position_error_m=pe,rotation_error_rad=re,clearance=clearance))
            qs.append(q[ik.qa].tolist())
            if pe>.001 or re>.025 or not clearance['clear']:return None,rows
        return q,dict(joint_path=qs,samples=rows)

    q,raise_path=segment(initial,start,raised,np.zeros(3))
    if q is None:return dict(planned=False,reason='raised_path',detail=raise_path)
    candidates={(0.,0.,0.)}
    for angle in [.2,.4,.6,.8]:
        for axis in range(3):
            for sign in [-1.,1.]:
                r=np.zeros(3);r[axis]=sign*angle;candidates.add(tuple(r))
    # A single-axis rotation unnecessarily forced the previous carrying pose
    # to turn 0.8 rad. Search combined rotations before accepting that large
    # change in payload orientation; every candidate keeps the same retreat,
    # official joint limits, endpoint margin and source-geometry checks.
    for r in itertools.product([-.4,-.2,0.,.2,.4],[-.8,-.6,-.4,-.2,0.,.2,.4,.6,.8],[-.4,-.2,0.,.2,.4]):
        if np.linalg.norm(r)<=.8+1e-12:candidates.add(r)
    candidates=[np.asarray(r) for r in sorted(candidates,key=lambda r:(np.linalg.norm(r),r))]
    if actor.body_withdrawal:candidates=[np.zeros(3)]
    for r in candidates:
        guard.d.qpos[:]=q;mujoco.mj_kinematics(actor.m,guard.d)
        goal,pe,re=ik.solve(guard.d,end,R@Rotation.from_rotvec(r).as_matrix(),q[ik.qa])
        row=dict(rotation_vector_rad=r.tolist(),endpoint_position_error_m=pe,endpoint_rotation_error_rad=re)
        attempts.append(row)
        if pe>.001 or re>.025:row['failure']='endpoint_ik';continue
        margin=float(np.min(np.minimum(goal-ik.low,ik.high-goal)))
        row['endpoint_joint_margin_rad']=margin
        if margin<.08:row['failure']='endpoint_joint_margin';continue
        final,path=segment(q,raised,end,r)
        if final is None:row.update(failure='withdrawal_path',detail=path[-1]);continue
        path_margin=float(np.min(np.minimum(final[ik.qa]-ik.low,ik.high-final[ik.qa])))
        row['path_endpoint_joint_margin_rad']=path_margin
        if path_margin<.08:row['failure']='path_endpoint_joint_margin';continue
        return dict(planned=True,rotation_vector_rad=r.tolist(),raise_path=raise_path,
                    retract_path=path,attempts=attempts,
                    candidate_order='Increasing wrist rotation magnitude; single and combined source-frame axes',
                    source_joint_range='Official source bounds minus 5 mrad margin',
                    physical_execution=False)
    return dict(planned=False,reason='no_loaded_withdrawal_path',attempts=attempts)


class LoadedWalker(QuasistaticWalker):
    def __init__(self, actor, goal):
        super().__init__(actor.m,actor.d,actor.d.qpos[:2],goal,step_length=.06)
        self.actor=actor
        # Preserve the current sensor-derived anchors; never reinitialize the
        # estimator from a physical base pose or assume the feet did not move.
        self.estimate.anchors=actor.estimate.anchors.copy()
        self.estimate.last_time=actor.last_time

    def begin_step(self,t):
        super().begin_step(t)
        if self.phase=='shift' and self.actor.support_inset_m:
            feet=np.asarray(self.balance.foot_positions)
            direction=feet[self.swing,:2]-feet[1-self.swing,:2]
            direction/=np.linalg.norm(direction)
            # Keep COM inside the stance sole, with 15 mm remaining to the
            # balance controller's conservative 25 mm lateral COP boundary.
            # Reaching the sole center required ankle angles outside the
            # 10 mrad source margin in the zero-rotation carrying trial.
            self.shift_to[:2]+=self.actor.support_inset_m*direction

    def control_tasks(self,t):
        a=self.actor
        a.configure_body_limits(self.balance)
        self.initial_com_height=a.carry_com_height
        self.balance.pelvis_rotation=a.carry_pelvis_rotation
        self.balance.palm_rotations={'right':a.wrist_rotation}
        return dict(targets={'right':a.control_target},posture=a.control_posture,
                    **a.control_motion)


class ToolActor(VisualPickup):
    transport_phases=frozenset({'carry_preload','carry_raise','carry_retract','carry_walk_out',
        'carry_pause','carry_walk_back','carry_align','carry_extend','carry_descend'})
    loaded_phases=VisualPickup.loaded_phases|transport_phases

    def __init__(self,model,prior):
        super().__init__(model,prior)
        self.distance=float(prior['carry_distance_m'])
        if not .02<=self.distance<=.30:raise ValueError('Local carrying distance outside declared development range')
        self.transported=False;self.walker=None;self.guard=None
        self.carry_dwell=None;self.next_carry_check=0.;self.carry_clearance=None
        self.control_target=None;self.control_posture=None;self.control_motion={}
        self.carry_observation=None
        self.carry_plan=None
        self.carry_force=np.asarray(prior.get('carry_hold_force_proxy_n',self.hold_force),dtype=float)
        if self.carry_force.shape!=(3,) or not np.isfinite(self.carry_force).all() or np.any(self.carry_force<self.hold_force) or max(self.carry_force)>=4.:
            raise ValueError('Invalid loaded-transport force targets')
        self.carry_load_since=None
        self.preload_before_lift=bool(prior.get('carry_preload_before_lift',False))
        self.carry_command_excursion=float(prior.get('carry_driver_command_excursion_rad',.15))
        if not .15<=self.carry_command_excursion<=.30:
            raise ValueError('Carrying command excursion outside the declared controller range')
        self.carry_motor_load_abort_nm=float(prior.get('carry_motor_load_abort_nm',.15))
        if not .15<=self.carry_motor_load_abort_nm<=.5*self.source_driver_effort_nm:
            raise ValueError('Carry load observer bound exceeds half the source motor effort rating')
        self.finger_load_compensation=bool(prior.get('carry_finger_load_compensation',False))
        self.body_joint_damper=bool(prior.get('carry_body_joint_damper',False))
        self.body_withdrawal=bool(prior.get('carry_body_withdrawal',False))
        self.support_inset_m=float(prior.get('carry_support_inset_m',0.))
        if not 0.<=self.support_inset_m<=.01:
            raise ValueError('Carrying support target inset must be 0 to 10 mm')
        self.proximal_preshape=float(prior.get('carry_proximal_preshape_rad',0.))
        if not 0.<=self.proximal_preshape<=.08:
            raise ValueError('Supported proximal preshape must be 0 to 0.08 rad')
        self.preshape_indices=np.array([self.names.index('right_hand_'+f+'_0_joint')
                                       for f in ['index','middle']])
        self.preshape_duration=12.
        if np.any(self.initial[self.preshape_indices]+self.proximal_preshape>
                  self.m.jnt_range[self.m.actuator_trnid[self.preshape_indices,0],1]-.01):
            raise ValueError('Preshape violates the unchanged source joint margin')
        self.prelift_load_dwell=float(prior.get('carry_prelift_proxy_dwell_s',.5))
        if not .5<=self.prelift_load_dwell<=2.:
            raise ValueError('Pre-lift load dwell outside the development range')

    def hand_load_feedforward(self):
        result=super().hand_load_feedforward()
        if self.finger_load_compensation and self.phase in self.loaded_phases:
            # The four posture joints have no force servo. With only PD,
            # their load-dependent deflection can move contact to a tool edge.
            # Compensate the filtered own-motor inverse-dynamics residual.
            # Closing joints retain their existing force feedback; including
            # them here would change the force servo's plant and equilibrium.
            for k,a in enumerate(self.hand):
                if a in self.drivers:continue
                bound=.5*np.max(abs(self.m.actuator_ctrlrange[a]))
                result[k]=np.clip(self.filtered[a],-bound,bound)
        return result

    def configure_body_limits(self,balance):
        if self.body_joint_damper:
            balance.joint_limit_indices=[i for i,n in enumerate(self.names) if '_hand_' not in n]
            balance.joint_limit_margin_rad=.01
            balance.joint_limit_frequency_rad_s=12.

    def abort(self,reason,t):
        if self.phase in self.transport_phases:
            # No release/lowering command over unknown support. End this
            # diagnostic with failure and retain its last motor commands.
            if self.failure is None:
                self.failure=reason;super().change('finished',t)
            return
        super().abort(reason,t)

    def change(self,phase,t):
        if phase=='lift' and self.phase=='close' and self.proximal_preshape:
            if t-self.phase_started<self.preshape_duration:
                return
        if phase=='close' and self.phase=='settle' and self.preload_before_lift:
            # Establish the carrying grasp while the tool is still supported.
            # Increasing force after pickup made the slender tool migrate out
            # of the fingers during the long load-settling interval.
            self.hold_force=self.carry_force.copy()
            self.lift_force=.85*self.carry_force
            self.motor_load_abort_nm=self.carry_motor_load_abort_nm
            self.configure_driver_commands()
            self.minimum_load_dwell=self.prelift_load_dwell
            self.events.append(dict(time_s=t,kind='carrying_force_before_lift',
                hold_force_proxy_n=self.hold_force.tolist(),
                lift_force_proxy_threshold_n=self.lift_force.tolist(),
                minimum_sustained_load_s=self.prelift_load_dwell))
        if phase=='lower' and self.phase=='hold' and not self.transported:
            self.return_wrist=self.wrist_position.copy()
            self.return_rotation=self.wrist_rotation.copy()
            self.carry_pelvis_rotation=self.d.body('pelvis').xmat.reshape(3,3).copy()
            forward=self.carry_pelvis_rotation[:,0].copy();forward[2]=0.;forward/=np.linalg.norm(forward)
            self.withdraw_delta=-(0. if self.body_withdrawal else .10)*forward
            self.raised_wrist=self.return_wrist+np.array([0.,0.,.05])
            self.retracted_wrist=self.raised_wrist+self.withdraw_delta
            self.origin_feet=np.mean(self.estimate.anchors,axis=0)[:2].copy()
            self.out_feet=self.origin_feet-self.distance*forward[:2]
            self.carry_com_height=float(self.d.subtree_com[self.m.body('pelvis').id,2])
            self.guard=CarryClearance(self)
            self.carry_plan=plan_carry_arm(self)
            self.events.append(dict(time_s=t,kind='carry_arm_plan',plan=self.carry_plan))
            if not self.carry_plan['planned']:
                self.failure='No collision-screened loaded withdrawal path'
                super().change('finished',t);return
            self.carry_rotation_delta=np.asarray(self.carry_plan['rotation_vector_rad'])
            self.carry_center_offset=self.center_offset.copy()
            final_rotation=self.return_rotation@Rotation.from_rotvec(self.carry_rotation_delta).as_matrix()
            self.retracted_wrist+=(self.return_rotation-final_rotation)@self.carry_center_offset
            self.events.append(dict(time_s=t,kind='carry_goal',distance_m=self.distance,
                source='Authored local out-and-back task relative to sensor-derived stance',
                inferred_payload_transform=True,
                withdrawal_mode='body_translation' if self.body_withdrawal else 'arm_then_body'))
            preload=bool(np.any(self.carry_force>self.hold_force))
            self.hold_force=self.carry_force.copy()
            self.motor_load_abort_nm=self.carry_motor_load_abort_nm
            self.configure_driver_commands()
            phase='carry_preload' if preload else 'carry_raise'
        self.carry_dwell=None
        super().change(phase,t)

    def configure_driver_commands(self):
        # This is a PD reference envelope, not a source joint limit. The old
        # +/-0.15 rad reference clipped thumb/index force feedback while the
        # measured load was below target. Retain official limits and the
        # unchanged force and motor-load stop guards for any wider envelope.
        ranges=self.m.jnt_range[self.m.actuator_trnid[self.drivers,0]]
        self.lower[self.drivers]=np.maximum(self.initial[self.drivers]-self.carry_command_excursion,ranges[:,0])
        self.upper[self.drivers]=np.minimum(self.initial[self.drivers]+self.carry_command_excursion,ranges[:,1])

    @staticmethod
    def blend(u):
        u=float(np.clip(u,0.,1.));return u**3*(10.+u*(-15.+6.*u))

    def start_walk(self,goal,t):
        self.walk_base=self.d.qpos[:3].copy()
        self.walk_wrist=self.wrist_position.copy()
        self.walker=LoadedWalker(self,goal)
        self.estimate=self.walker.estimate

    def finish_walk(self):
        self.balance=self.walker.balance
        self.com_start=self.d.subtree_com[self.m.body('pelvis').id].copy()
        self.com_goal=self.balance.com_target.copy()
        for i,name in enumerate(self.names):
            if any('_'+joint+'_' in name for joint in ['hip','knee','ankle']):
                self.initial[i]=self.d.qpos[self.qa[i]]
        self.walker=None

    def arm_reference(self,segment,u):
        path=np.asarray(self.carry_plan[segment+'_path']['joint_path'])
        point=float(np.clip(u,0.,1.))*(len(path)-1);i=min(int(point),len(path)-2)
        self.initial[self.arm_indices]=path[i]+(point-i)*(path[i+1]-path[i])

    def settled(self,t,duration):
        target=self.wrist_position+self.wrist_rotation@self.center_offset+[0.,0.,self.lift_height]
        w=self.d.site('right_wrist_reference')
        pe=float(np.linalg.norm(w.xpos-target))
        re=float(np.linalg.norm(Rotation.from_matrix(w.xmat.reshape(3,3)@self.wrist_rotation.T).as_rotvec()))
        if t-self.phase_started>=duration and pe<.003 and re<.025:
            if self.carry_dwell is None:self.carry_dwell=t
            return t-self.carry_dwell>=.3
        self.carry_dwell=None
        if t-self.phase_started>duration+8.:self.abort('Loaded arm failed to settle',t)
        return False

    def before_target(self,t,dt):
        if self.phase=='close' and self.proximal_preshape:
            # Move the two proximal finger joints while the tool is supported.
            # The distal force servos remain active and can open as needed.
            # The 12 s ramp keeps the compensating distal reference speed
            # within the existing 0.015 rad/s cap. This is an authored grasp
            # hypothesis based on source kinematics, not a measured slip pose.
            u=self.blend((t-self.phase_started)/self.preshape_duration)
            self.command[self.preshape_indices]=self.initial[self.preshape_indices]+u*self.proximal_preshape
        if self.phase not in self.transport_phases:return
        elapsed=t-self.phase_started
        if self.phase=='carry_preload':
            # A fresh sustained load observation is required before starting
            # the rotated transport pose; elapsed time alone cannot pass.
            if np.all(self.latest_force_proxy>.85*self.carry_force):
                if self.carry_load_since is None:self.carry_load_since=t
                if t-self.carry_load_since>=.5:self.change('carry_raise',t)
            else:self.carry_load_since=None
            if elapsed>15.:self.abort('Carrying preload did not reach sustained force targets',t)
        elif self.phase=='carry_raise':
            u=self.blend(elapsed/3.);self.arm_reference('raise',u)
            self.wrist_position=self.return_wrist+u*(self.raised_wrist-self.return_wrist)
            if self.settled(t,3.):
                if self.body_withdrawal:
                    # Keep the raised grasp orientation; actual foot-driven
                    # body translation performs withdrawal from the bench.
                    # No empty arm-retraction stage is recorded as executed.
                    self.start_walk(self.out_feet,t);self.change('carry_walk_out',t)
                else:self.change('carry_retract',t)
        elif self.phase=='carry_retract':
            u=self.blend(elapsed/6.);self.arm_reference('retract',u)
            self.wrist_position=self.raised_wrist+u*self.withdraw_delta
            self.wrist_rotation=self.return_rotation@Rotation.from_rotvec(u*self.carry_rotation_delta).as_matrix()
            self.wrist_position+=(self.return_rotation-self.wrist_rotation)@self.carry_center_offset
            if self.settled(t,6.):
                self.start_walk(self.out_feet,t);self.change('carry_walk_out',t)
        elif self.phase in {'carry_walk_out','carry_walk_back','carry_pause'}:
            self.wrist_position=self.walk_wrist+(self.d.qpos[:3]-self.walk_base)
            if self.phase=='carry_walk_out' and self.walker.finished:
                self.change('carry_pause',t)
            elif self.phase=='carry_pause' and elapsed>=1.:
                self.finish_walk();self.start_walk(self.origin_feet,t);self.change('carry_walk_back',t)
            elif self.phase=='carry_walk_back' and self.walker.finished:
                self.finish_walk();self.align_from=self.wrist_position.copy();self.change('carry_align',t)
            elif elapsed>100.:self.abort('Loaded stepping exceeded development timeout',t)
        elif self.phase=='carry_align':
            self.wrist_position=self.align_from+self.blend(elapsed/2.)*(self.retracted_wrist-self.align_from)
            if self.settled(t,2.):self.change('carry_descend' if self.body_withdrawal else 'carry_extend',t)
        elif self.phase=='carry_extend':
            u=self.blend(elapsed/6.);self.arm_reference('retract',1-u)
            self.wrist_rotation=self.return_rotation@Rotation.from_rotvec((1-u)*self.carry_rotation_delta).as_matrix()
            self.wrist_position=self.raised_wrist+(1-u)*self.withdraw_delta+(self.return_rotation-self.wrist_rotation)@self.carry_center_offset
            if self.settled(t,6.):self.change('carry_descend',t)
        elif self.phase=='carry_descend':
            u=self.blend(elapsed/3.);self.arm_reference('raise',1-u)
            self.wrist_position=self.raised_wrist+u*(self.return_wrist-self.raised_wrist)
            if self.settled(t,3.):
                self.transported=True;self.change('lower',t)
        self.balance.palm_rotations={'right':self.wrist_rotation}
        if t>=self.next_carry_check:
            self.carry_clearance=self.guard.check(self.d.qpos)
            self.next_carry_check=t+.05
            if not self.carry_clearance['clear']:
                self.abort('Loaded-arm clearance: '+json.dumps(self.carry_clearance),t)

    def balance_torque(self,target,posture,motion):
        if self.phase in self.transport_phases:self.configure_body_limits(self.balance)
        if self.phase in self.transport_phases and self.previous_balance_time is not None:
            period=float(self.carry_observation['time_s'])-self.previous_balance_time
            if not .0099<=period<=.0101:raise RuntimeError('Unexpected carrying reference period')
            motion=dict(target_velocities={'right':(target-self.previous_wrist_target)/period},
                palm_angular_velocities={'right':Rotation.from_matrix(self.wrist_rotation@self.previous_wrist_rotation.T).as_rotvec()/period})
        if self.walker is not None:
            self.control_target=target;self.control_posture=posture;self.control_motion=motion
            torque,_=self.walker.torque(dict(self.carry_observation,depth=None))
            return torque
        return super().balance_torque(target,posture,motion)

    def update(self,obs):
        self.carry_observation={k:obs[k] for k in Pickup.fields}
        result=super().update(obs)
        result.update(carry_completed=self.transported,carry_clearance=self.carry_clearance,
            motor_load_abort_nm=self.motor_load_abort_nm,
            stance_estimated_m=self.d.qpos[:3].copy(),
            walk_phase=None if self.walker is None else self.walker.phase,
            walk_steps=0 if self.walker is None else self.walker.steps)
        return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--prior',default='/model/policy/tool_prior.json');a=p.parse_args()
    actor=ToolActor(mujoco.MjModel.from_xml_path(a.model),json.loads(Path(a.prior).read_text()))
    while True:
        try:obs=pickle.load(sys.stdin.buffer)
        except EOFError:break
        try:response=actor.update(obs)
        except Exception as error:response=dict(torque=np.zeros(actor.m.nu),error=str(error))
        pickle.dump(response,sys.stdout.buffer,protocol=5);sys.stdout.buffer.flush()
        if response['error']:break


if __name__=='__main__':main()
