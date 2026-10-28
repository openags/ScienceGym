"""Proprioceptive state estimate and depth-only tray observation.

The actor receives joint encoders, an idealized IMU, and camera pixels. Root
translation is estimated from a fixed-foot assumption, not sent by the plant.
The assumption fails under slip; it is not a qualified localization system.
"""
import numpy as np
import mujoco


class StateEstimate:
    def __init__(self,m,d):
        self.m,self.d=m,d
        self.joints=[j for j in range(m.njnt) if m.jnt_type[j]==mujoco.mjtJoint.mjJNT_HINGE]
        self.qa=m.jnt_qposadr[self.joints];self.va=m.jnt_dofadr[self.joints]
        self.anchors=np.array([d.site(s+'_sole').xpos.copy() for s in ['left','right']])

    def update(self,obs):
        assert set(obs)=={'time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro','depth'},'Non-sensor field in actor input'
        m,d=self.m,self.d
        d.qpos[self.qa]=obs['joint_position'];d.qvel[self.va]=obs['joint_velocity']
        d.qpos[3:7]=obs['imu_quaternion'];d.qvel[3:6]=obs['imu_gyro']
        # Only kinematics is needed before recovering root height. Calling the
        # contact solver with a temporary root at zero puts the robot inside
        # the floor and creates thousands of irrelevant collision constraints.
        d.qpos[:3]=0;d.qvel[:3]=0;mujoco.mj_kinematics(m,d)
        feet=np.array([d.site(s+'_sole').xpos.copy() for s in ['left','right']])
        d.qpos[:3]=np.mean(self.anchors-feet,axis=0);mujoco.mj_forward(m,d)
        velocities=[]
        for side in ['left','right']:
            jp=np.zeros((3,m.nv));jr=np.zeros_like(jp);mujoco.mj_jacSite(m,d,jp,jr,m.site(side+'_sole').id)
            velocities.append(jp@d.qvel)
        d.qvel[:3]=-np.mean(velocities,axis=0);mujoco.mj_forward(m,d)

    def tray(self,depth):
        """Find above-table points in a declared workspace, without GT masks."""
        if depth is None:return None
        m,d=self.m,self.d;depth=np.asarray(depth);h,w=depth.shape
        fy=h/(2*np.tan(np.radians(58)/2));fx=fy
        vv,uu=np.mgrid[:h,:w];valid=np.isfinite(depth)&(depth>.05)&(depth<2)
        xyz=np.stack([(uu-w/2)*depth/fx,-(vv-h/2)*depth/fy,-depth],axis=-1)[valid]
        camera=m.camera('head_depth').id
        world=xyz@d.cam_xmat[camera].reshape(3,3).T+d.cam_xpos[camera]
        # Known workbench bounds are a static scene prior, not a target pose.
        selected=world[(world[:,0]>.385)&(world[:,0]<.8)&(abs(world[:,1])<.32)&(world[:,2]>.918)&(world[:,2]<.958)]
        if len(selected)<25:return None
        lo,hi=np.quantile(selected,[.02,.98],axis=0);center=(lo+hi)/2
        if hi[1]-lo[1]<.20:return None
        return dict(center_m=center.tolist(),observed_span_m=(hi-lo).tolist(),points=len(selected),source='head_depth_pixels_and_robot_proprioceptive_estimate')
