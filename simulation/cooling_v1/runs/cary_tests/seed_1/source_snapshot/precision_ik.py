"""Tight kinematic convergence for thin edges; actuation remains dynamic."""
import numpy as np
import mujoco
from scipy.spatial.transform import Rotation
from control import ExecutionFailure,DOWN


def solve(self,xyz,rotation=DOWN):
    k=self.kin;m=self.model;k.qpos[:]=self.data.qpos
    jp=np.zeros((3,m.nv));jr=np.zeros((3,m.nv))
    for _ in range(300):
        mujoco.mj_kinematics(m,k);mujoco.mj_comPos(m,k)
        error=np.r_[np.asarray(xyz)-k.site_xpos[self.site],Rotation.from_matrix(rotation@k.site_xmat[self.site].reshape(3,3).T).as_rotvec()*.4]
        if np.linalg.norm(error)<.00001:return k.qpos[:7].copy()
        mujoco.mj_jacSite(m,k,jp,jr,self.site)
        j=np.vstack([jp[:,:7],jr[:,:7]*.4])
        dq=j.T@np.linalg.solve(j@j.T+np.eye(6)*.00002,error)
        k.qpos[:7]=np.clip(k.qpos[:7]+np.clip(dq,-.1,.1),m.jnt_range[:7,0]+.005,m.jnt_range[:7,1]-.005)
    if np.linalg.norm(error)<.001:return k.qpos[:7].copy()
    raise ExecutionFailure('Precision IK unreachable: '+str(np.asarray(xyz).tolist()))
