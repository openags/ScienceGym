"""One isolated sensor actor for walking to a bench and manipulating its tray."""
import argparse
import pickle
import sys
import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

from balance import Balance
from observations import StateEstimate
from odometry import LegOdometry
from policy import FeedbackPolicy
from tracking import TrayTracker
from walking_actor import WalkingActor
from robot_state import initialize


class MissionActor:
    def __init__(self,model,policy_directory,initial_xy=(-.9,0.),goal_xy=(-.04,0.),parking_envelope=(-.15,.05,.10)):
        self.m=model;self.data=mujoco.MjData(model)
        self.odom=LegOdometry(model,self.data,initial_xy)
        self.walker=WalkingActor(model,policy_directory,speed=.4,gains='training',park=True,stop_at=float('inf'))
        self.goal=np.asarray(goal_xy);self.stage='approach';self.events=[];self.stopped_at=None
        self.parking_envelope=parking_envelope
        self.carrier=None;self.tracker=None;self.last_torque=np.zeros(model.nu)
        self.next_control=0.;self.latest_depth=None;self.latest_depth_time=None
        self.used_depth_time=None;self.last_update=None;self.last_detection=None
        self.initial_com=None;self.com_y=None;self.manipulation_started=None
        self.velocity_ema=np.zeros(3)
        self.prepare_started=None;self.prepare_posture=None

    def start_carrier(self,obs):
        # Re-anchor the controller's internal map estimate using leg odometry.
        # This never changes the physical robot or any object state.
        m,d=self.m,self.data;mujoco.mj_forward(m,d)
        low,high,lateral=self.parking_envelope
        if not (low<d.qpos[0]<high and abs(d.qpos[1])<lateral):
            raise RuntimeError('Estimated parking pose outside bench approach envelope')
        self.estimate=StateEstimate(m,d);self.estimate.update(obs)
        self.balance=Balance(m,d)
        yaw=Rotation.from_quat(obs['imu_quaternion'][[1,2,3,0]]).as_euler('xyz')[2]
        self.balance.pelvis_rotation=Rotation.from_euler('z',yaw).as_matrix()
        self.balance.rotate_foot_constraints=True
        zero=mujoco.MjData(m);mujoco.mj_forward(m,zero)
        self.balance.palm_rotations={s:Rotation.from_euler('x',-45 if s=='left' else 45,degrees=True).as_matrix()
                                    @zero.site(s+'_wrist_reference').xmat.reshape(3,3) for s in ['left','right']}
        self.carrier=FeedbackPolicy({s:d.site(s+'_wrist_reference').xpos.copy() for s in ['left','right']},return_to_source=True,grip_force=15)
        self.tracker=TrayTracker(m,d)
        self.initial_com=self.balance.com_target.copy();self.com_y=float(self.initial_com[1])
        self.manipulation_started=float(obs['time_s']);self.stage='manipulation'
        self.events.append(dict(state='begin_depth_localization',time_s=self.manipulation_started,estimated_map_xy_m=d.qpos[:2].tolist()))
        self.next_control=self.manipulation_started;self.used_depth_time=self.latest_depth_time

    def update(self,obs):
        t=float(obs['time_s'])
        if set(obs)!={'time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro','depth'}:
            raise ValueError('Non-sensor field in actor input')
        if obs['depth'] is not None:self.latest_depth=obs['depth'];self.latest_depth_time=t
        detection=None
        if self.stage=='approach':
            position=self.odom.update(obs)
            self.velocity_ema=.98*self.velocity_ema+.02*self.data.qvel[:3]
            orientation=Rotation.from_quat(obs['imu_quaternion'][[1,2,3,0]])
            forward=orientation.apply([1.,0.,0.]);yaw=np.arctan2(forward[1],forward[0])
            error=self.goal-position[:2]
            # Development braking model, calibrated against retained approach
            # attempts. This is an engineering assumption, not a reliability bound.
            braking_distance=max(.12,.35*max(0.,self.velocity_ema[0]))
            if t>=2 and self.stopped_at is None and error[0]<braking_distance and abs(error[1])<.10 and abs(yaw)<.10:
                self.stopped_at=t;self.walker.stop_at=t
                self.events.append(dict(state='stop_at_bench_approach',time_s=t,estimated_map_xy_m=position[:2].tolist(),estimated_speed_m_s=float(self.velocity_ema[0]),braking_distance_m=float(braking_distance)))
            command=np.zeros(3)
            if t>=2 and self.stopped_at is None:
                forward_command=np.clip(.35+.8*(.35-self.velocity_ema[0]),.26,.4)
                world_velocity=np.array([forward_command if error[0]>.12 else 0.,np.clip(1.8*error[1],-.15,.15),0.])
                command[:2]=orientation.inv().apply(world_velocity)[:2]
                command[2]=np.clip(-1.2*yaw,-.2,.2)
            if self.walker.parking_time is not None and t-self.walker.parking_time>=2:
                if self.prepare_started is None:
                    self.prepare_started=t;self.prepare_posture=self.walker.balance.posture.copy()
                    self.canonical_posture=initialize(self.m).qpos[self.walker.balance.qa].copy()
                    self.events.append(dict(state='prepare_manipulation_posture',time_s=t))
                u=np.clip((t-self.prepare_started)/5,0,1);u=u*u*(3-2*u)
                self.walker.balance.posture=self.prepare_posture+u*(self.canonical_posture-self.prepare_posture)
                if hasattr(self,'canonical_hand_curl'):
                    hand_u=float(np.clip(t-self.prepare_started,0,1));hand_u=hand_u*hand_u*(3-2*hand_u)
                    for i,j in enumerate(self.m.actuator_trnid[:,0]):
                        name=self.m.joint(j).name
                        goal=self.canonical_hand_curl if any(x in name for x in ['index','middle','ring','little']) else .6 if 'thumb_1' in name else .3 if 'thumb_2' in name else None
                        if goal is not None:self.walker.balance.posture[i]=self.prepare_posture[i]+hand_u*(goal-self.prepare_posture[i])
            self.walker.estimated_base_speed=float(np.linalg.norm(self.velocity_ema[:2]))
            self.last_torque,_=self.walker.torque(obs,command_override=command)
            if self.prepare_started is not None and t-self.prepare_started>=7:
                self.events.append(dict(state='stationary_control_stable',time_s=t,parking_time_s=self.walker.parking_time))
                self.start_carrier(obs)
            if t>28 and self.carrier is None:raise RuntimeError('Bench approach or stationary handoff timed out')
        if self.stage=='manipulation' and t+1e-8>=self.next_control:
            packet=dict(obs)
            fresh=self.latest_depth_time is not None and self.latest_depth_time!=self.used_depth_time
            packet['depth']=self.latest_depth if fresh else None
            self.estimate.update(packet)
            detection=self.tracker.observe(packet['depth'])
            relative=t-self.manipulation_started
            targets,forces=self.carrier.update(relative,detection,fresh)
            if fresh:self.used_depth_time=self.latest_depth_time
            requested=self.initial_com[1]+(np.clip((self.carrier.y-self.initial_com[1])*.65,-.05,.05) if hasattr(self.carrier,'y') and not self.carrier.complete else 0.)
            self.com_y+=float(np.clip(requested-self.com_y,-.00015,.00015))
            self.balance.com_target[1]=self.com_y
            dt=.01 if self.last_update is None else t-self.last_update
            self.last_torque=self.balance.torque(targets=targets,forces=forces,dt=dt,supported_mass=getattr(self.carrier,'supported_mass',0.))
            self.last_update=t;self.next_control=(round(t*100)+1)/100
            self.last_detection=detection
        events=[] if self.carrier is None else [dict(e,time_s=e['time_s']+self.manipulation_started) for e in self.carrier.events]
        return dict(torque=self.last_torque,error=None,mission_stage=self.stage,mission_events=self.events,
                    estimated_root_position_m=self.data.qpos[:3].tolist(),stop_at_s=self.stopped_at,
                    parking_time_s=self.walker.parking_time,manipulation_started_s=self.manipulation_started,
                    policy_state='approach' if self.carrier is None else self.carrier.state,
                    policy_phase=0 if self.carrier is None else self.carrier.phase,
                    policy_complete=False if self.carrier is None else self.carrier.complete,
                    policy_events=events,depth_observation=detection,depth_capture_time_s=self.used_depth_time,
                    control_update_time_s=self.last_update)

    def close(self):
        if self.tracker:self.tracker.close()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--model',required=True)
    parser.add_argument('--policy',default='/model/policy');parser.add_argument('--initial-xy',type=float,nargs=2,default=[-.9,0.])
    args=parser.parse_args();model=mujoco.MjModel.from_xml_path(args.model);actor=MissionActor(model,args.policy,args.initial_xy)
    try:
        while True:
            try:packet=pickle.load(sys.stdin.buffer)
            except EOFError:break
            try:response=actor.update(packet)
            except Exception as error:response=dict(torque=np.zeros(model.nu),error=str(error))
            pickle.dump(response,sys.stdout.buffer,protocol=5);sys.stdout.buffer.flush()
            if response['error']:break
    finally:actor.close()


if __name__=='__main__':main()
