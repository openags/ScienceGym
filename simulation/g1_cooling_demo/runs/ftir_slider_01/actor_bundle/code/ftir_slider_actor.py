"""Sensor-isolated preparation, geometric planning and tactile window push.

Only motor torques leave the actor. A completed command sequence still needs
independent device-motion/contact replay; this does not qualify a skill.
"""
import argparse
import pickle
import sys

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

from ftir_slider_scan_actor import SliderScanActor
from ftir_slider_planning import SliderPlanner
from ftir_slider_vision import SliderObservation


class SliderActor(SliderScanActor):
    fields=SliderScanActor.fields|{'right_touch_n'}

    def __init__(self,model,xy,prior,shape):
        super().__init__(model,xy)
        self.prior_path,self.shape_path=prior,shape
        self.grip_vision=SliderObservation(model,self.d,prior,shape)
        self.grip_observations=[];self.prepared=False;self.motions=[]
        self.filtered_touch=0.;self.touch_since=None;self.lost_since=None
        self.contact_offset=0.;self.contact_confirmed=False;self.recovering=False
        self.reference_data=mujoco.MjData(model)
        self.last_target=None;self.last_rotation=None;self.commanded_pose=None

    def arm_pose(self,q):
        d=self.reference_data;d.qpos[:]=self.planner.initial;d.qpos[self.ik.qa]=q
        mujoco.mj_kinematics(self.m,d)
        site=d.site('right_wrist_reference')
        return site.xpos.copy(),site.xmat.reshape(3,3).copy()

    def build_motion(self,t):
        if len(self.grip_observations)<8:
            raise RuntimeError('Closed slider grip was not observed reliably')
        self.planner=SliderPlanner(self.m,self.d,self.scan_observations,self.prior_path,self.shape_path)
        self.solution=self.planner.build()
        self.baseline_posture=self.d.qpos[self.balance.qa].copy()
        self.pointing=self.solution['candidate']['hand_q']
        self.folded={n:float(self.d.joint(n).qpos[0]) for n in self.pointing}
        self.normal=np.array(self.solution['outward_normal']);self.direction=np.array(self.solution['direction'])
        self.contact_position=np.array(self.solution['contact_palm_position_m'])
        self.contact_rotation=np.array(self.solution['contact_palm_rotation'])
        self.precontact=self.contact_position+self.normal*.02
        self.push_end=self.contact_position+self.direction*.07
        self.return_segments=[]
        for i,(a,b) in enumerate(zip(self.solution['return_path'][:-1],self.solution['return_path'][1:])):
            self.return_segments.append(dict(name='return_'+str(i),kind='joint',duration=max(2.,np.linalg.norm(np.array(b)-a)/.25),a=a,b=b))
        motions=[dict(name='prepare_hand',kind='hand',duration=3.,hand=self.pointing)]
        for i,(a,b) in enumerate(zip(self.solution['entry_path'][:-1],self.solution['entry_path'][1:])):
            motions.append(dict(name='entry_'+str(i),kind='joint',duration=max(2.,np.linalg.norm(np.array(b)-a)/.25),a=a,b=b))
        motions.extend([dict(name='align',kind='pose',duration=4.,position=self.contact_position),
                        dict(name='seek_contact',kind='seek',duration=3.),
                        dict(name='push',kind='push',duration=10.),
                        dict(name='withdraw',kind='pose',duration=3.,position=self.push_end+self.normal*.03),
                        dict(name='clear_to_entry',kind='pose',duration=5.,position=self.precontact)])
        motions.extend(self.return_segments)
        motions.append(dict(name='restore_hand',kind='hand',duration=3.,hand=self.folded))
        self.motions=motions;self.phase=0;self.prepared=True;self.finished=False
        self.events.append(dict(state='observed_geometry_path_planned',time_s=t,
                                source='current_encoders_IMU_RGBD_and_public_unposed_CAD',solution=self.solution,
                                accepted_grip_observations=len(self.grip_observations),
                                grip_observations=self.grip_observations[-8:]))
        self.begin_phase(t)

    def begin_phase(self,t):
        self.phase_started=t;self.reached_since=None
        self.start_position=self.d.site('right_wrist_reference').xpos.copy()
        self.start_rotation=self.d.site('right_wrist_reference').xmat.reshape(3,3).copy()
        self.start_hand={n:float(self.d.joint(n).qpos[0]) for n in self.pointing}

    def recover(self,t,reason):
        if self.recovering:raise RuntimeError('Recovery failed: '+reason)
        self.failure=reason;self.recovering=True
        current=self.d.site('right_wrist_reference').xpos.copy()
        self.motions=[dict(name='withdraw_abort',kind='pose',duration=3.,position=current+self.normal*.03),
                      dict(name='clear_to_entry_abort',kind='pose',duration=5.,position=self.precontact),
                      *self.return_segments,
                      dict(name='restore_hand',kind='hand',duration=3.,hand=self.folded)]
        self.phase=0;self.contact_confirmed=False;self.contact_offset=0.
        self.events.append(dict(state='recovery_started',time_s=t,reason=reason))
        self.begin_phase(t)

    def update(self,obs):
        if set(obs)!=self.fields:raise ValueError('Non-sensor field in FTIR actor input')
        touch=np.asarray(obs['right_touch_n'],dtype=float)
        if touch.shape!=(7,) or not np.isfinite(touch).all() or np.any(touch<0):
            raise ValueError('Invalid tactile observation')
        if not self.prepared:
            response=super().update({k:v for k,v in obs.items() if k!='right_touch_n'})
            detection=response.get('observation')
            if detection and detection['accepted']:
                grip=self.grip_vision.observe(obs['depth'],detection)
                response['grip_observation']=grip
                if grip['accepted']:self.grip_observations.append(grip)
            if self.finished:
                self.build_motion(float(obs['time_s']))
                response.update(policy_complete=False,policy_state='prepare_hand',events=self.events)
            return response
        t=float(obs['time_s'])
        if t+1e-8>=self.next_control:
            dt=.01 if self.last_time is None else t-self.last_time
            self.estimate.update({k:v for k,v in obs.items() if k not in {'rgb','right_touch_n'}})
            self.filtered_touch+=(1-np.exp(-dt/.05))*(float(touch[2])-self.filtered_touch)
            posture=self.baseline_posture.copy();force=None
            if not self.finished:
                motion=self.motions[self.phase];name=motion['name'];kind=motion['kind']
                recovered_now=False
                u=float(np.clip((t-self.phase_started)/motion['duration'],0,1));s=u*u*(3-2*u)
                hand=self.pointing.copy();target_R=self.contact_rotation
                hint=self.d.qpos[self.ik.qa] if self.latest_ik is None else self.latest_ik
                if kind=='hand':
                    hand={n:self.start_hand[n]+s*(v-self.start_hand[n]) for n,v in motion['hand'].items()}
                    target,target_R=self.start_position,self.start_rotation
                elif kind=='joint':
                    hint=np.array(motion['a'])+s*(np.array(motion['b'])-motion['a'])
                    target,target_R=self.arm_pose(hint)
                elif kind=='pose':
                    target=self.start_position+s*(np.asarray(motion['position'])-self.start_position)
                elif kind=='seek':
                    self.contact_offset=-.0015*s
                    target=self.contact_position+self.normal*self.contact_offset
                    force=-self.normal*min(2.,2*u)
                    if self.filtered_touch>.2:
                        if self.touch_since is None:self.touch_since=t
                        if t-self.touch_since>=.2:self.contact_confirmed=True
                    else:self.touch_since=None
                elif kind=='push':
                    self.contact_offset=float(np.clip(self.contact_offset-.0005*(2.-self.filtered_touch)*dt,-.003,.001))
                    target=self.contact_position+s*self.direction*.07+self.normal*self.contact_offset
                    force=-self.normal*2.
                    if self.filtered_touch<.1:
                        if self.lost_since is None:self.lost_since=t
                    else:self.lost_since=None
                else:raise ValueError('Unknown slider phase')
                if kind in {'seek','push'} and (self.filtered_touch>6. or (kind=='push' and self.lost_since is not None and t-self.lost_since>.35)):
                    self.recover(t,'Tactile load exceeded bound or contact was lost')
                    target=self.start_position;target_R=self.start_rotation;force=None
                    recovered_now=True
                for n,v in hand.items():posture[self.actuator_ids[n]]=v
                q,pe,re=self.ik.solve(self.d,target,target_R,hint)
                if pe>.003 or re>.035:raise RuntimeError(f'Slider arm IK failed in {name}: {pe:.6f} m, {re:.6f} rad')
                self.latest_ik=q;posture[self.arm_actuators]=q
                self.last_target=target.copy();self.last_rotation=target_R.copy()
                self.commanded_pose=dict(position_m=target.tolist(),rotation=target_R.tolist(),normal_offset_m=self.contact_offset)
                error=float(np.linalg.norm(target-self.d.site('right_wrist_reference').xpos))
                rotation_error=float(np.linalg.norm(Rotation.from_matrix(target_R@self.d.site('right_wrist_reference').xmat.reshape(3,3).T).as_rotvec()))
                ready=(kind=='seek' and self.contact_confirmed) or (u>=1 and (kind=='push' or (error<.005 and rotation_error<.035)))
                if recovered_now:
                    pass
                elif ready:
                    if self.reached_since is None:self.reached_since=t
                    if t-self.reached_since>=.15:
                        self.events.append(dict(state=name+'_endpoint',time_s=t,position_error_m=error,rotation_error_rad=rotation_error,distal_index_load_n=self.filtered_touch))
                        self.phase+=1
                        if self.phase>=len(self.motions):self.finished=True
                        else:self.begin_phase(t)
                elif kind=='seek' and u>=1:
                    self.recover(t,'No confirmed distal-pad contact during bounded search')
                    force=None;self.last_target=self.start_position.copy();self.last_rotation=self.start_rotation.copy()
                elif t-self.phase_started>motion['duration']+5.:
                    raise RuntimeError('Robot did not settle in slider phase '+name)
            else:
                for n,v in self.folded.items():posture[self.actuator_ids[n]]=v
            self.balance.palm_rotations={'right':self.last_rotation}
            self.last_torque=self.balance.torque(posture=posture,targets={'right':self.last_target},
                contact_forces=None if force is None else {'right':force},dt=dt)
            self.last_time=t;self.next_control=(round(t*100)+1)/100
        return dict(torque=self.last_torque,error=None,policy_state='finished' if self.finished else self.motions[self.phase]['name'],
                    policy_complete=self.finished,policy_failure=self.failure,events=self.events,
                    accepted_key_observations=self.total_accepted,accepted_grip_observations=len(self.grip_observations),
                    observation=None,touch=dict(distal_index_n=float(touch[2]),filtered_distal_index_n=self.filtered_touch),
                    commanded_pose=self.commanded_pose,estimated_root_position_m=self.d.qpos[:3].tolist())


def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True)
    p.add_argument('--initial-xy',nargs=2,type=float,default=[5.95,-5.20])
    p.add_argument('--prior',default='/model/policy/slider_push_prior.json')
    p.add_argument('--shape',default='/model/known_objects/nicolet_passive_dynamics.glb');a=p.parse_args()
    m=mujoco.MjModel.from_xml_path(a.model);actor=SliderActor(m,a.initial_xy,a.prior,a.shape)
    while True:
        try:packet=pickle.load(sys.stdin.buffer)
        except EOFError:break
        try:response=actor.update(packet)
        except Exception as error:response=dict(torque=np.zeros(m.nu),error=str(error))
        pickle.dump(response,sys.stdout.buffer,protocol=5);sys.stdout.buffer.flush()
        if response['error']:break


if __name__=='__main__':main()
