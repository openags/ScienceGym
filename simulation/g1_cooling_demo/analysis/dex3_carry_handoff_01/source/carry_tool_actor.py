"""Visual pickup followed by loaded withdrawal, stepping, return and release.

The short out-and-back route develops the carrying handoff required before
cross-station work. It is not a paper branch. The actor receives only the same
native camera and proprioceptive inputs as the visual pickup. A rigid grasp
hypothesis is used for collision planning only; the plant tool stays passive.
"""
import argparse
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


def pose(site):
    T=np.eye(4);T[:3,:3]=site.xmat.reshape(3,3);T[:3,3]=site.xpos
    return T


class CarryClearance:
    """Arm and hypothesized tool versus observed surfaces and public map.

    Original hand-internal assemblies and the legs are not certified by this
    arm guard. The independent full-plant evaluator retains those obligations.
    """
    def __init__(self, actor):
        p=actor.planner;self.m=p.m;self.d=mujoco.MjData(self.m)
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


class LoadedWalker(QuasistaticWalker):
    def __init__(self, actor, goal):
        super().__init__(actor.m,actor.d,actor.d.qpos[:2],goal,step_length=.06)
        self.actor=actor
        # Preserve the current sensor-derived anchors; never reinitialize the
        # estimator from a physical base pose or assume the feet did not move.
        self.estimate.anchors=actor.estimate.anchors.copy()
        self.estimate.last_time=actor.last_time

    def control_tasks(self,t):
        a=self.actor
        self.initial_com_height=a.carry_com_height
        self.balance.pelvis_rotation=a.carry_pelvis_rotation
        self.balance.palm_rotations={'right':a.wrist_rotation}
        return dict(targets={'right':a.control_target},posture=a.control_posture,
                    **a.control_motion)


class ToolActor(VisualPickup):
    transport_phases=frozenset({'carry_raise','carry_retract','carry_walk_out',
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

    def abort(self,reason,t):
        if self.phase in self.transport_phases:
            # No release/lowering command over unknown support. End this
            # diagnostic with failure and retain its last motor commands.
            if self.failure is None:
                self.failure=reason;super().change('finished',t)
            return
        super().abort(reason,t)

    def change(self,phase,t):
        if phase=='lower' and self.phase=='hold' and not self.transported:
            self.return_wrist=self.wrist_position.copy()
            self.carry_pelvis_rotation=self.d.body('pelvis').xmat.reshape(3,3).copy()
            forward=self.carry_pelvis_rotation[:,0].copy();forward[2]=0.;forward/=np.linalg.norm(forward)
            self.withdraw_delta=-.10*forward
            self.raised_wrist=self.return_wrist+np.array([0.,0.,.05])
            self.retracted_wrist=self.raised_wrist+self.withdraw_delta
            self.origin_feet=np.mean(self.estimate.anchors,axis=0)[:2].copy()
            self.out_feet=self.origin_feet-self.distance*forward[:2]
            self.carry_com_height=float(self.d.subtree_com[self.m.body('pelvis').id,2])
            self.guard=CarryClearance(self)
            self.events.append(dict(time_s=t,kind='carry_goal',distance_m=self.distance,
                source='Authored local out-and-back task relative to sensor-derived stance',
                inferred_payload_transform=True))
            phase='carry_raise'
        self.carry_dwell=None
        super().change(phase,t)

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
        self.walker=None

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
        if self.phase not in self.transport_phases:return
        elapsed=t-self.phase_started
        if self.phase=='carry_raise':
            self.wrist_position=self.return_wrist+self.blend(elapsed/3.)*(self.raised_wrist-self.return_wrist)
            if self.settled(t,3.):self.change('carry_retract',t)
        elif self.phase=='carry_retract':
            self.wrist_position=self.raised_wrist+self.blend(elapsed/4.)*self.withdraw_delta
            if self.settled(t,4.):
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
            if self.settled(t,2.):self.change('carry_extend',t)
        elif self.phase=='carry_extend':
            self.wrist_position=self.retracted_wrist-self.blend(elapsed/4.)*self.withdraw_delta
            if self.settled(t,4.):self.change('carry_descend',t)
        elif self.phase=='carry_descend':
            self.wrist_position=self.raised_wrist+self.blend(elapsed/3.)*(self.return_wrist-self.raised_wrist)
            if self.settled(t,3.):
                self.transported=True;self.change('lower',t)
        if t>=self.next_carry_check:
            self.carry_clearance=self.guard.check(self.d.qpos)
            self.next_carry_check=t+.05
            if not self.carry_clearance['clear']:
                self.abort('Loaded-arm clearance: '+json.dumps(self.carry_clearance),t)

    def balance_torque(self,target,posture,motion):
        if self.phase in self.transport_phases and self.previous_balance_time is not None:
            period=float(self.carry_observation['time_s'])-self.previous_balance_time
            if not .0099<=period<=.0101:raise RuntimeError('Unexpected carrying reference period')
            motion=dict(target_velocities={'right':(target-self.previous_wrist_target)/period})
        if self.walker is not None:
            self.control_target=target;self.control_posture=posture;self.control_motion=motion
            torque,_=self.walker.torque(dict(self.carry_observation,depth=None))
            return torque
        return super().balance_torque(target,posture,motion)

    def update(self,obs):
        self.carry_observation={k:obs[k] for k in Pickup.fields}
        result=super().update(obs)
        result.update(carry_completed=self.transported,carry_clearance=self.carry_clearance,
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
