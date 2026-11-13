"""RGB-D registered, tactile-gated opening of a passive FTIR cover.

Only robot sensors and an object-relative geometric affordance are available.
The hinge path is computed after observing the key row, not supplied in world
coordinates. Actual device motion and grasp quality need independent review.
"""
import argparse
import json
import pickle
import sys
from pathlib import Path

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation, Slerp

from ftir_actor import FTIRActor
from ftir_hand import initialize_cover
from ftir_cover_geometry import observe_handle


class CoverActor(FTIRActor):
    fields = FTIRActor.fields | {'right_touch_n'}

    def __init__(self, model, xy, prior):
        super().__init__(model, xy, initial_state=initialize_cover(model,xy))
        self.prior = json.loads(Path(prior).read_text())
        self.open_q = dict(self.prior['nominal_grip_q'], right_index_1_joint=0., right_thumb_2_joint=.05)
        self.closed_q = dict(self.prior['nominal_grip_q'])
        for joint in ['right_index_1_joint','right_thumb_2_joint']:self.closed_q[joint]+=.08
        for posture in [self.open_q,self.prior['nominal_grip_q'],self.closed_q]:
            candidate=self.d.qpos.copy()
            for name,value in posture.items():candidate[self.m.joint(name).qposadr[0]]=value
            for eq in range(self.m.neq):
                a,b=self.m.eq_obj1id[eq],self.m.eq_obj2id[eq]
                candidate[self.m.jnt_qposadr[a]]=self.m.eq_data[eq,0]+self.m.eq_data[eq,1]*candidate[self.m.jnt_qposadr[b]]
            for joint in range(self.m.njnt):
                name=self.m.joint(joint).name
                if self.m.jnt_limited[joint] and name.startswith('right_') and any(f in name for f in ['index','thumb','middle','ring','little']):
                    if not self.m.jnt_range[joint,0]<=candidate[self.m.jnt_qposadr[joint]]<=self.m.jnt_range[joint,1]:
                        raise ValueError('Cover grasp exceeds source joint limits: '+name)
        self.last_touch = None
        self.grasp_since = None
        self.grasp_confirmed = False
        self.lost_since = None
        self.commanded_pose = None
        # Development grip-force band; these gains are not vendor calibration.
        # Adapt motor effort from the two tactile loads, with bounded integral
        # action. A band permits the unequal loads needed to support the lid.
        self.filtered_load = np.zeros(2)
        self.grip_effort = np.zeros(2)
        self.grip_control = None
        self.initial_com = self.d.subtree_com[self.m.body('pelvis').id].copy()
        self.centered_com = self.balance.com_target.copy()
        self.wrist_integral = np.zeros(3)
        self.wrist_load_compensation = None

    def make_plan(self, t):
        recent = self.observations[-8:]
        observed = np.median([[o['buttons'][k['label']] for k in self.prior['keys']] for o in recent], axis=0)
        if np.max(np.std([[o['buttons'][k['label']] for k in self.prior['keys']] for o in recent], axis=0)) > .002:
            raise RuntimeError('Observed instrument key row is not stationary')
        normal = np.mean([o['outward_normal'] for o in recent], axis=0); normal /= np.linalg.norm(normal)
        row = observed[-1] - observed[0]; row -= row.dot(normal)*normal; row /= np.linalg.norm(row)
        known_normal = -np.array(self.prior['keys'][0]['inward_axis'])
        known_row = np.array([1., 0, 0])
        basis = lambda r,n: np.column_stack([r, np.cross(n,r), n])
        self.rotation = basis(row,normal) @ basis(known_row,known_normal).T
        source_caps = np.array([k['center_m'] for k in self.prior['keys']]) + known_normal*self.prior['key_cap_thickness_m']/2
        translation = np.mean(observed-source_caps@self.rotation.T, axis=0)
        handle_points=np.array([o['handle_fit']['handle_m'] for o in recent])
        if np.max(np.std(handle_points,axis=0))>.001:raise RuntimeError('Observed handle is not stationary')
        self.handle = np.median(handle_points,axis=0)
        self.pivot = self.handle+self.rotation@(np.array(self.prior['hinge_pivot_m'])-np.array(self.prior['closed_handle_center_m']))
        self.axis = self.rotation@np.array(self.prior['hinge_axis'])
        self.front = self.rotation@np.array([0., -1, 0])
        grasp = np.array(self.prior['handle_frame_from_palm'])
        self.grip_position = self.handle + self.rotation@grasp[:3,3]
        self.grip_rotation = self.rotation@grasp[:3,:3]
        self.initial = self.d.site('right_wrist_reference').xpos.copy()
        self.initial_R = self.d.site('right_wrist_reference').xmat.reshape(3,3).copy()
        self.raised = self.initial + [-.03, 0, .07]
        folded = {n:float(self.original_posture[self.actuator_ids[n]]) for n in self.open_q}
        end, end_R = self.arc(1.)
        self.plan = [
            ('raise',2.,self.raised,self.initial_R,folded),
            ('approach',6.,self.grip_position+self.front*.06,self.grip_rotation,self.open_q),
            # Curl while approaching the bar. Keeping the thumb fully open
            # until the final palm pose makes its distal link hit the case.
            ('align',4.,self.grip_position,self.grip_rotation,self.prior['nominal_grip_q']),
            ('close',3.,self.grip_position,self.grip_rotation,self.closed_q),
            ('lift',8.,end,end_R,self.closed_q),
            ('hold',2.,end,end_R,self.closed_q),
            ('release',2.,end,end_R,self.open_q),
            ('withdraw',3.,end+self.front*.08,end_R,self.open_q),
            ('clear',6.,self.raised,self.initial_R,folded),
            ('return',3.,self.initial,self.initial_R,folded)]
        previous, previous_R = self.initial, self.initial_R
        seed = self.d.qpos[self.ik.qa].copy()
        worst = [0.,0.]
        for name, _, goal, rot, _ in self.plan:
            rotations = Slerp([0,1],Rotation.from_matrix([previous_R,rot]))
            for u in np.linspace(0,1,51):
                v = u*u*(3-2*u)
                target, target_R = self.arc(v) if name=='lift' else (previous+v*(goal-previous),rotations([v]).as_matrix()[0])
                seed, pe, re = self.ik.solve(self.d,target,target_R,seed)
                worst = [max(worst[0],pe),max(worst[1],re)]
                if pe>.003 or re>.035:
                    raise RuntimeError(f'Observed cover IK preflight failed in {name}: {pe:.5f} m, {re:.5f} rad')
            previous, previous_R = goal, rot
        self.previous_position, self.previous_rotation, self.previous_q = self.initial,self.initial_R,folded
        self.phase,self.phase_started = 0,t
        self.balance.palm_rotations = {'right':self.initial_R}
        self.events.append(dict(state='observed_instrument_registered',time_s=t,
                                estimated_handle_m=self.handle.tolist(),estimated_hinge_m=self.pivot.tolist(),
                                estimated_rotation=self.rotation.tolist(),accepted_frames=len(recent),
                                preflight_max_position_error_m=worst[0],preflight_max_rotation_error_rad=worst[1],
                                handle_depth_points=[o['handle_fit']['cylinder_points'] for o in recent],
                                source='native_rgb_depth_key_row_and_observed_handle_cylinder'))

    def arc(self, u):
        rot = Rotation.from_rotvec(self.axis*(-np.pi/3)*u).as_matrix()
        return self.pivot+rot@(self.grip_position-self.pivot),rot@self.grip_rotation

    def recover(self, t, reason):
        self.failure = reason
        current = self.d.site('right_wrist_reference').xpos.copy()
        rotation = self.d.site('right_wrist_reference').xmat.reshape(3,3).copy()
        actual = {n:float(self.d.joint(n).qpos[0]) for n in self.open_q}
        folded = {n:float(self.original_posture[self.actuator_ids[n]]) for n in self.open_q}
        self.plan = [('release_abort',2.,current,rotation,self.open_q),
                     ('withdraw_abort',3.,current+self.front*.08,rotation,self.open_q),
                     ('clear_abort',6.,self.raised,self.initial_R,folded),
                     ('return_abort',3.,self.initial,self.initial_R,folded)]
        self.previous_position,self.previous_rotation,self.previous_q = current,rotation,actual
        self.phase,self.phase_started,self.reached_since = 0,t,None
        self.grip_effort[:] = 0
        self.wrist_integral[:] = 0
        self.events.append(dict(state='recovery_started',time_s=t,reason=reason))

    def update(self, obs):
        if set(obs)!=self.fields:raise ValueError('Non-sensor field in FTIR actor input')
        t=float(obs['time_s']);detection=None
        if t+1e-8>=self.next_control:
            touch=np.asarray(obs['right_touch_n'],dtype=float)
            if touch.shape!=(7,) or not np.isfinite(touch).all() or np.any(touch<0):
                raise ValueError('Invalid hand tactile observation')
            self.last_touch=dict(index_n=float(sum(touch[:3])),thumb_n=float(sum(touch[3:])))
            dt=.01 if self.last_time is None else t-self.last_time
            self.filtered_load += (1-np.exp(-dt/.05))*(np.array(list(self.last_touch.values()))-self.filtered_load)
            self.estimate.update({k:v for k,v in obs.items() if k not in {'rgb','right_touch_n'}})
            if obs['rgb'] is not None and obs['depth'] is not None:
                detection=self.vision.observe(obs['rgb'],obs['depth'])
                if detection and detection['accepted']:
                    self.total_accepted+=1
                    if self.plan is None:
                        detection['handle_fit']=observe_handle(self.m,self.d,obs['depth'],detection,self.prior)
                        if detection['handle_fit']['accepted']:self.observations.append(detection)
            if self.plan is None and t>=2 and len(self.observations)>=8:self.make_plan(t)
            if self.plan is None and t>5:raise RuntimeError('FTIR controls and handle were not observed reliably')
            # Transfer the COM smoothly from the prepared stance to the
            # support center instead of commanding an initial acceleration.
            settle=float(np.clip(t/2.,0,1));settle=settle*settle*(3-2*settle)
            self.balance.com_target=self.initial_com+settle*(self.centered_com-self.initial_com)
            targets=None;posture=self.original_posture.copy();hand_target=None;force_active=False;forces=None
            if self.plan is not None and not self.finished:
                name,duration,goal,rotation,hand=self.plan[self.phase]
                u=float(np.clip((t-self.phase_started)/duration,0,1));smooth=u*u*(3-2*u)
                target,target_R=self.arc(smooth) if name=='lift' else (
                    self.previous_position+smooth*(goal-self.previous_position),
                    Slerp([0,1],Rotation.from_matrix([self.previous_rotation,rotation]))([smooth]).as_matrix()[0])
                hand_target={n:self.previous_q[n]+smooth*(v-self.previous_q[n]) for n,v in hand.items()}
                for n,v in hand_target.items():posture[self.actuator_ids[n]]=v
                seed=self.d.qpos[self.ik.qa] if self.latest_ik is None else self.latest_ik
                q,pe,re=self.ik.solve(self.d,target,target_R,seed)
                if pe>.003 or re>.035:
                    if name!='release_abort':raise RuntimeError(f'Cover arm target infeasible in {name}: {pe:.5f} m, {re:.5f} rad')
                    # Opening the fingers must remain possible when a body
                    # adjustment makes the old recovery wrist pose unreachable.
                    q=self.d.qpos[self.ik.qa].copy()
                    target=self.d.site('right_wrist_reference').xpos.copy()
                    target_R=self.d.site('right_wrist_reference').xmat.reshape(3,3).copy()
                self.latest_ik=q;posture[self.arm_actuators]=q
                self.balance.palm_rotations={'right':target_R};targets={'right':target}
                contact=min(self.last_touch.values())>.15
                if name=='close':
                    if np.min(self.filtered_load)>=4.5:
                        if self.grasp_since is None:self.grasp_since=t
                        if t-self.grasp_since>=.2:self.grasp_confirmed=True
                    else:self.grasp_since=None;self.grasp_confirmed=False
                force_active=name in {'close','lift','hold'} and not self.failure
                if force_active:
                    ramp=min(1.,max(0.,(t-self.phase_started)/1.5)) if name=='close' else 1.
                    low,high=6.*ramp,10.
                    force_error=np.maximum(0.,low-self.filtered_load)-np.maximum(0.,self.filtered_load-high)
                    self.grip_effort=np.clip(self.grip_effort+.08*dt*force_error,0.,.65)
                    # Loaded finger contacts push the compliant wrist away
                    # from the bar. Correct measured wrist error through
                    # robot motors; no force is written to the instrument.
                    error=target-self.d.site('right_wrist_reference').xpos
                    self.wrist_integral=np.clip(self.wrist_integral+500.*dt*error,-8.,8.)
                    compensation=np.clip(500.*error+self.wrist_integral,-10.,10.)
                    forces={'right':compensation}
                    self.wrist_load_compensation=dict(force_n=compensation.tolist(),integral_n=self.wrist_integral.tolist(),position_error_m=error.tolist())
                else:
                    self.grip_effort[:]=0;self.wrist_integral[:]=0
                    self.wrist_load_compensation=None
                self.grip_control=dict(filtered_load_n=self.filtered_load.tolist(),additional_effort_nm=self.grip_effort.tolist(),active=force_active)
                if name in {'lift','hold'}:
                    if contact:self.lost_since=None
                    elif self.lost_since is None:self.lost_since=t
                position_error=float(np.linalg.norm(goal-self.d.site('right_wrist_reference').xpos))
                rotation_error=float(np.linalg.norm(Rotation.from_matrix(rotation@self.d.site('right_wrist_reference').xmat.reshape(3,3).T).as_rotvec()))
                self.commanded_pose=dict(phase=name,target_m=target.tolist(),rotation=target_R.tolist(),
                                         endpoint_position_error_m=position_error,endpoint_rotation_error_rad=rotation_error,
                                         estimated_wrist_m=self.d.site('right_wrist_reference').xpos.tolist())
                reason=None
                if max(self.last_touch.values())>15:reason='Finger normal load exceeded 15 N development limit'
                if name=='close' and t-self.phase_started>duration+3 and not self.grasp_confirmed:reason='Opposed grip load was not established'
                if self.lost_since is not None and t-self.lost_since>.3:reason='Opposed contact was lost during cover lift'
                if not self.failure and reason:
                    self.recover(t,reason)
                else:
                    ready=(self.grasp_confirmed if name=='close' else name in {'hold','release','release_abort'} or (position_error<.006 and rotation_error<.05))
                    # End closing once the measured grip is established.
                    # Continuing a timed curl can roll a narrow pad off the
                    # bar even after both contacts already carry the load.
                    if name=='close' and self.grasp_confirmed:
                        hand=dict(hand_target)
                        for phase in range(self.phase+1,len(self.plan)):
                            if self.plan[phase][0] in {'lift','hold'}:
                                self.plan[phase]=(*self.plan[phase][:4],dict(hand))
                    if (u>=1 or name=='close' and self.grasp_confirmed) and ready:
                        if self.reached_since is None:self.reached_since=t
                        if t-self.reached_since>=.15:
                            self.events.append(dict(state=name+'_endpoint',time_s=t,position_error_m=position_error,
                                                    rotation_error_rad=rotation_error,touch=self.last_touch))
                            self.previous_position,self.previous_rotation,self.previous_q=goal.copy(),rotation.copy(),dict(hand)
                            if name=='release_abort':
                                self.previous_position=self.d.site('right_wrist_reference').xpos.copy()
                                self.previous_rotation=self.d.site('right_wrist_reference').xmat.reshape(3,3).copy()
                                withdraw=self.plan[self.phase+1]
                                self.plan[self.phase+1]=(withdraw[0],withdraw[1],self.previous_position+self.front*.08,self.previous_rotation.copy(),withdraw[4])
                            self.phase+=1;self.phase_started=t;self.reached_since=None
                            if self.phase==len(self.plan):self.finished=True
                    elif t-self.phase_started>duration+5:
                        if not self.failure:self.recover(t,'Robot pose did not reach '+name)
                        else:raise RuntimeError('Recovery pose did not reach '+name)
            torque=self.balance.torque(targets=targets,contact_forces=forces,posture=posture,dt=dt)
            # Bounded finger motor impedance supplies grip force. No force is
            # applied to the device, base, or any unactuated state directly.
            if hand_target is not None:
                for n in ['right_index_1_joint','right_thumb_1_joint','right_thumb_2_joint']:
                    a=self.actuator_ids[n];joint=self.m.joint(n).id
                    effort=4.*(hand_target[n]-self.d.qpos[self.m.jnt_qposadr[joint]])-.035*self.d.qvel[self.m.jnt_dofadr[joint]]
                    extra=self.grip_effort[0] if n=='right_index_1_joint' else self.grip_effort[1] if n=='right_thumb_2_joint' else 0.
                    torque[a]+=np.clip(np.clip(effort,-.4,.4)+extra,-.8,.8)
            self.last_torque=np.clip(torque,self.m.actuator_ctrlrange[:,0],self.m.actuator_ctrlrange[:,1])
            self.last_time=t;self.next_control=(round(t*100)+1)/100
        return dict(torque=self.last_torque,error=None,policy_state='finished' if self.finished else
                    'observe' if self.plan is None else self.plan[self.phase][0],policy_complete=self.finished,
                    policy_failure=self.failure,events=self.events,accepted_key_observations=self.total_accepted,
                    observation=detection,touch=self.last_touch,grip_control=self.grip_control,wrist_load_compensation=self.wrist_load_compensation,grasp_contact_confirmed=self.grasp_confirmed,commanded_pose=self.commanded_pose,
                    estimated_root_position_m=self.d.qpos[:3].tolist())


def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True)
    p.add_argument('--initial-xy',nargs=2,type=float,default=[5.95,-5.35])
    p.add_argument('--prior',default='/model/policy/cover_grasp_prior.json');a=p.parse_args()
    m=mujoco.MjModel.from_xml_path(a.model);actor=CoverActor(m,a.initial_xy,a.prior)
    while True:
        try:packet=pickle.load(sys.stdin.buffer)
        except EOFError:break
        try:response=actor.update(packet)
        except Exception as error:response=dict(torque=np.zeros(m.nu),error=str(error))
        pickle.dump(response,sys.stdout.buffer,protocol=5);sys.stdout.buffer.flush()
        if response['error']:break


if __name__=='__main__':main()
