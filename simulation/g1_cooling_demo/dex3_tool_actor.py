"""Encoder/IMU driven three-finger pickup from a declared initial pregrasp.

Contact points are own-hand material features. Motor-load estimates are
inferred and uncalibrated; object motion and success are independently judged.
"""
import argparse
import json
import pickle
import sys

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

from balance import Balance
from observations import StateEstimate


class ToolActor:
    fields={'time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro'}
    loaded_phases=frozenset({'close','lift','hold','lower'})

    def __init__(self, model, prior):
        self.m=model;self.d=mujoco.MjData(model);self.d.qpos[:]=prior['initial_robot_qpos']
        mujoco.mj_forward(model,self.d);self.estimate=StateEstimate(model,self.d)
        self.balance=Balance(model,self.d);self.balance.rotate_foot_constraints=True;self.balance.solver_backend='clarabel'
        self.balance.pelvis_rotation=self.d.body('pelvis').xmat.reshape(3,3).copy()
        self.com_start=self.d.subtree_com[model.body('pelvis').id].copy();self.com_goal=self.balance.com_target.copy()
        self.names=[model.joint(j).name for j in model.actuator_trnid[:,0]]
        self.qa=model.jnt_qposadr[model.actuator_trnid[:,0]];self.va=model.jnt_dofadr[model.actuator_trnid[:,0]]
        self.hand=np.array([i for i,n in enumerate(self.names) if n.startswith('right_hand_')])
        assert len(self.hand)==7 and model.nu==43 and model.neq==0
        self.drivers=np.array([self.names.index(n) for n in prior['closing_drivers']]);self.signs=np.asarray(prior['closing_signs'])
        self.motor_load_abort_nm=.15
        self.source_driver_effort_nm=np.min(np.max(abs(model.actuator_ctrlrange[self.drivers]),axis=1))
        self.features=[(model.body(r['body']).id,np.asarray(r['point_local_m'])) for r in prior['robot_contact_features']]
        assert len(self.features)==len(self.drivers)==3
        self.initial=self.d.qpos[self.qa].copy();self.command=self.initial.copy()
        ranges=model.jnt_range[model.actuator_trnid[:,0]]
        self.lower=np.maximum(self.initial-.15,ranges[:,0]);self.upper=np.minimum(self.initial+.15,ranges[:,1])
        wrist=self.d.site('right_wrist_reference');self.wrist_position=wrist.xpos.copy();self.wrist_rotation=wrist.xmat.reshape(3,3).copy()
        self.balance.palm_rotations={'right':self.wrist_rotation}
        self.approach_velocity_feedforward=bool(prior.get('approach_velocity_feedforward',False))
        self.previous_wrist_target=self.wrist_position.copy();self.previous_wrist_rotation=self.wrist_rotation.copy()
        self.previous_balance_time=None
        self.weights=np.array([.5,.25,.25]);self.feature_reference=self.midpoint();self.center_offset=np.zeros(3)
        self.filtered=np.zeros(model.nu);self.previous_velocity=None;self.previous_torque=np.zeros(model.nu)
        self.body_torque=np.zeros(model.nu);self.next_balance=0.;self.last_time=None
        self.flags=np.zeros(3,dtype=bool);self.release_since=[None]*3;self.load_since=None;self.lost_since=None
        self.phase='settle';self.phase_started=0.;self.hold_entered=False;self.lift_height=0.;self.abort_height=0.
        self.requested_lift_height=float(prior.get('tool_lift_height_m',.03))
        if not .02<=self.requested_lift_height<=.06:
            raise ValueError('Requested tool lift must be between 20 and 60 mm')
        self.lower_start_height=0.
        self.failure=None;self.events=[];self.release_command=None
        self.release_clear_since=None
        self.release_clearance_started=None;self.withdraw_start_height=0.
        self.close_timeout=float(prior.get('close_timeout_s',6.))
        self.hold_force=np.asarray(prior.get('hold_force_proxy_n',[.6,.3,.3]),dtype=float)
        self.lift_force=np.asarray(prior.get('lift_force_proxy_threshold_n',[.5,.25,.25]),dtype=float)
        assert self.hold_force.shape==self.lift_force.shape==(3,)
        assert np.all(self.lift_force>0) and np.all(self.hold_force>self.lift_force) and max(self.hold_force)<4.
        self.release_extra=float(prior.get('release_extra_opening_rad',.04))
        self.release_load_feedback=bool(prior.get('release_load_feedback',False))
        self.release_preserve_posture=bool(prior.get('release_preserve_posture',False))
        self.release_clearance_height=float(prior.get('release_clearance_height_m',0.))
        if not 0<=self.release_clearance_height<=.004:
            raise ValueError('Release clearance motion must stay within 0 to 4 mm')
        self.release_driver_openings=np.asarray(prior.get('release_driver_openings_rad',
            [self.release_extra]*3),dtype=float)
        self.withdrawal=float(prior.get('post_release_withdrawal_m',.02))
        assert 0<=self.release_extra<=.08 and 0<=self.withdrawal<=.04
        if (self.release_driver_openings.shape!=(3,) or
                not np.isfinite(self.release_driver_openings).all() or
                np.any(self.release_driver_openings<0) or np.any(self.release_driver_openings>.08)):
            raise ValueError('Three driver release openings must each lie within 0 to 0.08 rad')
        self.release_target=self.initial.copy()
        self.release_target[self.drivers]=np.clip(self.initial[self.drivers]-self.signs*self.release_driver_openings,
            self.lower[self.drivers],self.upper[self.drivers])
        # Hand inertias are much smaller than the previous hand's reflected
        # inertia. Bound sampled PD gains in the coupled hand inertia modes.
        # These change motor commands only; no model mass/armature is changed.
        self.hand_selector=np.eye(model.nv)[:,self.va[self.hand]]

    def points(self):
        return np.array([self.d.xpos[b]+self.d.xmat[b].reshape(3,3)@p for b,p in self.features])

    def midpoint(self):
        wrist=self.d.site('right_wrist_reference')
        return wrist.xmat.reshape(3,3).T@(self.weights@self.points()-wrist.xpos)

    def change(self, phase, t):
        if phase=='lower':self.lower_start_height=self.lift_height
        if phase=='release' and self.release_preserve_posture:
            # Opening the distal drivers while resetting a proximal preshape
            # can move the fingertip back into the supported tool. Retain the
            # other four commanded joint angles until the hand is withdrawn.
            # These are own control references, not object/contact truth.
            posture=np.array([a for a in self.hand if a not in self.drivers])
            self.release_target[posture]=self.command[posture]
        if phase=='withdraw':self.withdraw_start_height=self.lift_height
        self.phase=phase;self.phase_started=t;self.events.append(dict(time_s=t,phase=phase))

    def abort(self, reason, t):
        if self.failure is not None:return
        self.failure=reason;self.abort_height=self.lift_height;self.change('abort_lower',t)

    def before_target(self, t, dt):
        """Optional sensor-state motion extension; the plant is never exposed."""

    def balance_torque(self, target, posture, motion):
        return self.balance.torque(targets={'right':target},posture=posture,dt=.01,**motion)

    def hand_load_feedforward(self):
        """Optional own-motor disturbance compensation; no plant contact input."""
        return np.zeros(len(self.hand))

    def update(self, obs):
        if set(obs)!=ToolActor.fields:raise ValueError('Unexpected observation fields')
        if not all(np.isfinite(np.asarray(v)).all() for v in obs.values()):raise ValueError('Nonfinite sensor packet')
        t=float(obs['time_s']);dt=.001 if self.last_time is None else t-self.last_time
        if not .0009999<=dt<=.0010001:raise ValueError('Unexpected control period')
        packet=dict(obs,depth=None);self.estimate.update(packet);m,d=self.m,self.d
        gravity=(d.qfrc_bias-d.qfrc_passive)[self.va]
        mass=np.empty((m.nv,m.nv));mujoco.mj_fullM(m,d,mass)
        if self.previous_velocity is not None:
            predicted=(mass@((d.qvel-self.previous_velocity)/dt))[self.va]+gravity
            self.filtered+=(1-np.exp(-dt/.03))*(self.previous_torque-predicted-self.filtered)
        self.previous_velocity=d.qvel.copy()
        points=self.points();direction=(points[1]+points[2])/2-points[0];direction/=max(np.linalg.norm(direction),1e-12)
        lever=[]
        for i,((b,p),a,sign) in enumerate(zip(self.features,self.drivers,self.signs)):
            jp,jr=np.zeros((3,m.nv)),np.zeros((3,m.nv));mujoco.mj_jac(m,d,jp,jr,points[i],b)
            inward=direction if i==0 else -direction
            lever.append(float(sign*inward@jp[:,self.va[a]]))
        lever=np.asarray(lever)
        if min(lever)<.001:raise RuntimeError('Source contact feature cannot close toward the opposed fingers')
        effort=self.signs*self.filtered[self.drivers];proxy=effort/lever
        self.latest_force_proxy=proxy.copy()
        if max(abs(proxy))>4. or max(abs(effort))>self.motor_load_abort_nm:self.abort('Observed motor load exceeds the development bound',t)
        if self.phase=='settle' and t-self.phase_started>=2.:self.change('close',t)
        if self.phase=='close':
            for i in range(3):
                if not self.flags[i] and proxy[i]>.05:self.flags[i]=True;self.release_since[i]=None
                elif self.flags[i] and proxy[i]<.02:
                    if self.release_since[i] is None:self.release_since[i]=t
                    if t-self.release_since[i]>=.05:self.flags[i]=False
                else:self.release_since[i]=None
            self.hold_entered=self.hold_entered or bool(all(self.flags))
            # The inferred 18 g tool and 0.225 sliding friction require more
            # than mere touch. Require sustained opposed load before lifting.
            if self.hold_entered and np.all(proxy>self.lift_force):
                if self.load_since is None:self.load_since=t
                if t-self.load_since>=getattr(self,'minimum_load_dwell',.5):self.change('lift',t)
            else:self.load_since=None
            if t-self.phase_started>self.close_timeout:self.abort('No sustained three-finger load before grasp timeout',t)
        if self.hold_entered and self.phase in self.loaded_phases:
            if min(proxy)<.02:
                if self.lost_since is None:self.lost_since=t
                if t-self.lost_since>=.2:self.abort('Observed loss of three-finger load',t)
            else:self.lost_since=None
        if self.phase in self.loaded_phases:
            speeds=np.clip(.0005/lever,.001,.015)
            for i,a in enumerate(self.drivers):
                desired_force=self.hold_force[i] if self.hold_entered else .03
                rate=np.clip(1.2*(desired_force*lever[i]-effort[i]),-speeds[i],speeds[i]) if self.hold_entered or self.flags[i] else speeds[i]
                self.command[a]=np.clip(self.command[a]+self.signs[i]*rate*dt,self.lower[a],self.upper[a])
            desired=self.feature_reference-self.midpoint();desired*=min(1.,.02/max(np.linalg.norm(desired),1e-12))
            delta=(1-np.exp(-dt/.05))*(desired-self.center_offset);delta*=min(1.,.006*dt/max(np.linalg.norm(delta),1e-12))
            self.center_offset+=delta
        smooth=lambda x:(lambda u:u*u*(3-2*u))(float(np.clip(x,0,1)))
        elapsed=t-self.phase_started
        if self.phase=='lift':
            self.lift_height=self.requested_lift_height*smooth(elapsed/2.)
            if elapsed>=2.:self.change('hold',t)
        elif self.phase=='hold' and elapsed>=1.:self.change('lower',t)
        elif self.phase in {'lower','abort_lower'}:
            self.lift_height=(self.lower_start_height if self.phase=='lower' else self.abort_height)*(1-smooth(elapsed/2.))
            if elapsed>=2.:self.release_command=self.command.copy();self.change('release',t)
        elif self.phase=='release':
            self.command=self.release_command+smooth(elapsed/2.)*(self.release_target-self.release_command)
            if elapsed>=2.:
                if self.release_clearance_height:
                    # After opening and low own-motor loads, a small upward
                    # retreat clears a finger resting against the supported
                    # beam. The original unloaded gate must still pass before
                    # full withdrawal. No object/support truth is available.
                    if self.release_clearance_started is None and max(abs(proxy))<.05:
                        self.release_clearance_started=t
                    if self.release_clearance_started is not None:
                        self.lift_height=self.release_clearance_height*smooth((t-self.release_clearance_started)/.5)
                if self.release_load_feedback:
                    # Positive closing load asks for more opening; negative
                    # load asks to back away from an opening-side obstruction.
                    # Only own-motor residuals are used. Keep the original
                    # opening envelope, load gate, dwell and timeout unchanged.
                    rate=np.where(abs(proxy)>.015,np.sign(proxy)*.01,0.)
                    self.release_driver_openings=np.clip(self.release_driver_openings+rate*dt,0.,.08)
                    self.release_target[self.drivers]=np.clip(
                        self.initial[self.drivers]-self.signs*self.release_driver_openings,
                        self.lower[self.drivers],self.upper[self.drivers])
                    self.command[self.drivers]=self.release_target[self.drivers]
                if max(abs(proxy))<.015:
                    if self.release_clear_since is None:self.release_clear_since=t
                    if t-self.release_clear_since>=.1:self.change('withdraw',t)
                else:self.release_clear_since=None
                if self.phase=='release' and elapsed>=3.:
                    if self.failure is None:self.failure='Residual finger load after opening for release'
                    self.change('finished',t)
        elif self.phase=='withdraw':
            self.lift_height=self.withdraw_start_height+(self.withdrawal-self.withdraw_start_height)*smooth(elapsed/2.)
            if elapsed>=2.:self.change('rest',t)
        elif self.phase=='rest' and elapsed>=2.:self.change('finished',t)
        self.before_target(t,dt)
        target=self.wrist_position+self.wrist_rotation@self.center_offset+[0.,0.,self.lift_height]
        if t+1e-9>=self.next_balance:
            self.balance.com_target=self.com_start+smooth(t/2.)*(self.com_goal-self.com_start)
            posture=self.initial.copy();posture[self.hand]=self.command[self.hand]
            motion={}
            if self.approach_velocity_feedforward and self.phase=='approach' and self.previous_balance_time is not None:
                # Differences of commanded reference poses, never object or
                # simulator velocities. Average over the actual balance tick
                # so the approach clock's pauses remain reflected in the feedforward.
                period=t-self.previous_balance_time
                if not .0099<=period<=.0101:raise RuntimeError('Unexpected balance reference period')
                velocity=(target-self.previous_wrist_target)/period
                angular=Rotation.from_matrix(self.wrist_rotation@self.previous_wrist_rotation.T).as_rotvec()/period
                motion=dict(target_velocities={'right':velocity},palm_angular_velocities={'right':angular})
            self.body_torque=self.balance_torque(target,posture,motion)
            self.previous_wrist_target=target.copy();self.previous_wrist_rotation=self.wrist_rotation.copy();self.previous_balance_time=t
            self.next_balance=(round(t*100)+1)/100
        inverse_hand_mass=self.hand_selector.T@np.linalg.solve(mass,self.hand_selector)
        inertia_modes,U=np.linalg.eigh(np.linalg.inv(inverse_hand_mass))
        if min(inertia_modes)<=0:raise RuntimeError('Nonpositive hand inertia')
        kp=np.minimum(3.,.25*inertia_modes/dt**2)
        kd=np.minimum(2*np.sqrt(kp*inertia_modes),.4*inertia_modes/dt)
        error=U.T@(self.command-d.qpos[self.qa])[self.hand]
        speed=U.T@d.qvel[self.va[self.hand]]
        torque=self.body_torque.copy();torque[self.hand]=gravity[self.hand]+U@(kp*error-kd*speed)+self.hand_load_feedforward()
        torque=np.clip(torque,m.actuator_ctrlrange[:,0],m.actuator_ctrlrange[:,1]);self.previous_torque=torque.copy();self.last_time=t
        return dict(torque=torque,error=None,phase=self.phase,failure=self.failure,complete=self.phase=='finished',
            requested_joint_position=self.command.copy(),motor_load_nm=effort.copy(),force_proxy_n=proxy.copy(),
            contact_flags=self.flags.copy(),hold_phase_entered=self.hold_entered,wrist_target_m=target.copy(),
            wrist_observed_m=d.site('right_wrist_reference').xpos.copy(),encoder_center_offset_m=self.center_offset.copy(),
            lift_height_m=self.lift_height,events=list(self.events))


def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--prior',default='/model/policy/tool_prior.json');a=p.parse_args()
    actor=ToolActor(mujoco.MjModel.from_xml_path(a.model),json.loads(open(a.prior).read()))
    while True:
        try:obs=pickle.load(sys.stdin.buffer)
        except EOFError:break
        try:response=actor.update(obs)
        except Exception as error:response=dict(torque=np.zeros(actor.m.nu),error=str(error))
        pickle.dump(response,sys.stdout.buffer,protocol=5);sys.stdout.buffer.flush()
        if response['error']:break


if __name__=='__main__':main()
