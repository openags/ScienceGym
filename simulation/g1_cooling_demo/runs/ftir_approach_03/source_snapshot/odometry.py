"""Leg odometry from encoders/IMU and an explicit initial map-pose prior.

The lower sole is assumed to support the robot on a level floor. This does not
measure contact or detect slip; its error is evaluated outside the actor.
"""
import mujoco
import numpy as np


class LegOdometry:
    def __init__(self,model,data,initial_xy):
        self.m,self.d=model,data
        self.initial_xy=np.asarray(initial_xy,dtype=float)
        self.joints=[j for j in range(model.njnt) if model.jnt_type[j]==mujoco.mjtJoint.mjJNT_HINGE]
        self.qa=model.jnt_qposadr[self.joints];self.va=model.jnt_dofadr[self.joints]
        self.soles=[model.site(s+'_sole').id for s in ['left','right']]
        self.anchors=None;self.stance=0;self.previous=None;self.previous_time=None;self.switches=[]

    def update(self,obs):
        if set(obs)!={'time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro','depth'}:
            raise ValueError('Non-sensor field in actor input')
        m,d=self.m,self.d;t=float(obs['time_s'])
        d.qpos[self.qa]=obs['joint_position'];d.qvel[self.va]=obs['joint_velocity']
        d.qpos[3:7]=obs['imu_quaternion'];d.qvel[3:6]=obs['imu_gyro']
        d.qpos[:3]=0;d.qvel[:3]=0;mujoco.mj_kinematics(m,d)
        feet=d.site_xpos[self.soles].copy()
        if self.anchors is None:
            self.anchors=feet.copy();self.anchors[:,:2]+=self.initial_xy
            self.stance=int(np.argmin(feet[:,2]));xy=self.initial_xy.copy()
        else:
            xy=self.anchors[self.stance,:2]-feet[self.stance,:2]
            other=1-self.stance
            if feet[other,2]<feet[self.stance,2]-.003:
                self.anchors[other,:2]=xy+feet[other,:2]
                self.stance=other;self.switches.append(dict(time_s=t,stance=other))
        position=np.r_[xy,-min(feet[:,2])]
        if self.previous_time is not None and t>self.previous_time:
            d.qvel[:3]=(position-self.previous)/(t-self.previous_time)
        d.qpos[:3]=position
        self.previous=position.copy();self.previous_time=t
        mujoco.mj_kinematics(m,d)
        return position.copy()
