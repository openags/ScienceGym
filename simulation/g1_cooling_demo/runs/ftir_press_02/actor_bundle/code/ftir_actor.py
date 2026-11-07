"""Isolated RGB-D and proprioception actor for a single FTIR key press attempt.

The initial station/posture is authored setup. A completed attempt still needs
independent physical switch/contact verification; it is not paper acceptance.
"""
import argparse
import pickle
import sys

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation, Slerp

from balance import Balance
from observations import StateEstimate
from ftir_hand import initialize, ArmIK, PointingHand, POINTING
from ftir_vision import KeyRowObservation


class FTIRActor:
    fields={'time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro','depth','rgb'}

    def __init__(self, model, xy, label='BACKGROUND'):
        self.m=model;self.d=initialize(model,xy);self.label=label
        self.estimate=StateEstimate(model,self.d);self.balance=Balance(model,self.d)
        self.balance.rotate_foot_constraints=True
        self.vision=KeyRowObservation(model,self.d);self.hand=PointingHand(model);self.ik=ArmIK(model)
        self.original_posture=self.balance.posture.copy()
        self.actuator_ids={model.joint(j).name:i for i,j in enumerate(model.actuator_trnid[:,0])}
        self.arm_actuators=np.array([self.actuator_ids[model.joint(j).name] for j in self.ik.joints])
        self.next_control=0.;self.last_torque=np.zeros(model.nu);self.last_time=None
        self.observations=[];self.events=[];self.plan=None;self.phase=-1;self.phase_started=None
        self.last_detection=None;self.last_tip=None;self.contact_samples=0;self.failure=None;self.finished=False
        self.latest_ik=None;self.reached_since=None;self.total_accepted=0

    def make_plan(self,t):
        recent=self.observations[-8:]
        positions=np.array([o['buttons'][self.label] for o in recent])
        if np.max(np.std(positions,axis=0))>.002:raise RuntimeError('Observed key row is not stationary')
        self.surface=np.median(positions,axis=0)
        self.normal=np.mean([o['outward_normal'] for o in recent],axis=0);self.normal/=np.linalg.norm(self.normal)
        row=np.mean([o['row_direction'] for o in recent],axis=0)
        target,rotation,self.pad_contact=self.hand.at_surface(self.surface,self.normal,row)
        initial=self.d.site('right_wrist_reference').xpos.copy()
        initial_rotation=self.d.site('right_wrist_reference').xmat.reshape(3,3).copy()
        raised=initial+[-.03,0,.07]
        self.plan=[('raise',2.,raised,initial_rotation,0.),('point',3.,raised,rotation,1.),
                   ('approach',3.,target+self.normal*.030,rotation,1.),
                   ('press',3.,target-self.normal*.001,rotation,1.),
                   ('hold',.5,target-self.normal*.001,rotation,1.),
                   ('withdraw',2.,target+self.normal*.035,rotation,1.),
                   ('clear',3.,raised,rotation,1.),('fold',2.,raised,initial_rotation,0.),
                   ('return',2.,initial,initial_rotation,0.)]
        self.previous_position=initial;self.previous_rotation=initial_rotation;self.previous_curl=0.
        self.phase=0;self.phase_started=t
        self.balance.palm_rotations={'right':initial_rotation}
        self.events.append(dict(state='sensor_target_selected',time_s=t,label=self.label,
                                surface_m=self.surface.tolist(),outward_normal=self.normal.tolist(),
                                accepted_frames=len(recent),source='native_rgb_and_depth_only'))

    def update(self,obs):
        if set(obs)!=self.fields:raise ValueError('Non-sensor field in FTIR actor input')
        t=float(obs['time_s']);detection=None
        if t+1e-8>=self.next_control:
            self.estimate.update({k:v for k,v in obs.items() if k!='rgb'})
            if obs['rgb'] is not None and obs['depth'] is not None:
                detection=self.vision.observe(obs['rgb'],obs['depth'])
                self.last_detection=detection
                if detection and detection['accepted']:
                    self.observations.append(detection);self.total_accepted+=1
            if self.plan is None and t>=2 and len(self.observations)>=8:self.make_plan(t)
            if self.plan is None and t>5:raise RuntimeError('Four FTIR controls were not observed reliably')
            targets,forces=None,None;posture=self.original_posture.copy()
            if self.plan is not None and not self.finished:
                name,duration,goal,rotation,curl=self.plan[self.phase]
                u=float(np.clip((t-self.phase_started)/duration,0,1));smooth=u*u*(3-2*u)
                target=self.previous_position+smooth*(goal-self.previous_position)
                target_rotation=Slerp([0.,1.],Rotation.from_matrix([self.previous_rotation,rotation]))([smooth]).as_matrix()[0]
                hand_u=self.previous_curl+smooth*(curl-self.previous_curl)
                for joint,value in POINTING.items():
                    a=self.actuator_ids[joint];posture[a]=self.original_posture[a]+hand_u*(value-self.original_posture[a])
                seed=self.d.qpos[self.ik.qa] if self.latest_ik is None else self.latest_ik
                q,pe,re=self.ik.solve(self.d,target,target_rotation,seed)
                if pe>.003 or re>.035:raise RuntimeError(f'Arm target infeasible in {name}: {pe:.5f} m, {re:.5f} rad')
                self.latest_ik=q;posture[self.arm_actuators]=q
                self.balance.palm_rotations={'right':target_rotation};targets={'right':target}
                if name in ['press','hold']:
                    force=.45*(float(np.clip((u-.65)/.35,0,1)) if name=='press' else 1.)
                    forces={'right':-self.normal*force}
                tip=self.hand.observed_contact_point(self.d,self.pad_contact)
                delta=tip-self.surface;gap=float(np.dot(delta,self.normal));lateral=float(np.linalg.norm(delta-gap*self.normal))
                self.last_tip=dict(position_m=tip.tolist(),normal_gap_m=gap,lateral_error_m=lateral)
                if name=='hold' and gap<-.0001 and lateral<.003:self.contact_samples+=1
                position_error=float(np.linalg.norm(goal-self.d.site('right_wrist_reference').xpos))
                rotation_error=float(np.linalg.norm(Rotation.from_matrix(rotation@self.d.site('right_wrist_reference').xmat.reshape(3,3).T).as_rotvec()))
                ready=position_error<.005 and rotation_error<.035
                if u>=1 and ready:
                    if self.reached_since is None:self.reached_since=t
                    if t-self.reached_since>=.15:
                        if name=='hold' and self.contact_samples<10:self.failure='No sufficient proprioceptive contact-depth evidence'
                        self.events.append(dict(state=name+'_endpoint',time_s=t,position_error_m=position_error,
                                                rotation_error_rad=rotation_error,tip=self.last_tip))
                        self.previous_position=goal.copy();self.previous_rotation=rotation.copy();self.previous_curl=curl
                        self.phase+=1;self.phase_started=t;self.reached_since=None
                        if self.phase==len(self.plan):self.finished=True
                elif t-self.phase_started>duration+5:
                    raise RuntimeError('Robot pose did not reach '+name)
            self.last_torque=self.balance.torque(targets=targets,forces=forces,posture=posture,
                                                 dt=.01 if self.last_time is None else t-self.last_time)
            self.last_time=t;self.next_control=(round(t*100)+1)/100
        return dict(torque=self.last_torque,error=None,
                    policy_state='finished' if self.finished else 'observe' if self.plan is None else self.plan[self.phase][0],
                    policy_complete=self.finished,policy_failure=self.failure,events=self.events,
                    accepted_key_observations=self.total_accepted,observation=detection,estimated_tip=self.last_tip,
                    estimated_root_position_m=self.d.qpos[:3].tolist(),contact_depth_samples=self.contact_samples)


def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--initial-xy',nargs=2,type=float,default=[5.95,-5.55]);p.add_argument('--label',default='BACKGROUND');a=p.parse_args()
    m=mujoco.MjModel.from_xml_path(a.model);actor=FTIRActor(m,a.initial_xy,a.label)
    while True:
        try:packet=pickle.load(sys.stdin.buffer)
        except EOFError:break
        try:response=actor.update(packet)
        except Exception as error:response=dict(torque=np.zeros(m.nu),error=str(error))
        pickle.dump(response,sys.stdout.buffer,protocol=5);sys.stdout.buffer.flush()
        if response['error']:break


if __name__=='__main__':main()
