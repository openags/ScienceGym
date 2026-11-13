"""CAD pose tracking using only the same depth foreground as the sensor actor."""
import numpy as np
from tracking import TrayTracker
from tray_pose import TrayPose


class RigidTrayTracker(TrayTracker):
    def __init__(self,model,data,shape_path):
        super().__init__(model,data)
        shape=np.load(shape_path);self.pose=TrayPose(shape['vertices'],shape['faces'])
        self.last_fit=None;self.accepted=0;self.rejected=0
    def observe(self,depth):
        if depth is None:return None
        super().observe(depth)
        depth=np.asarray(depth);h,w=depth.shape;fy=h/(2*np.tan(np.radians(58)/2));v,u=np.mgrid[:h,:w]
        pixels=np.stack([(u+.5-w/2)*depth/fy,-(v+.5-h/2)*depth/fy,-depth],axis=-1)
        camera=self.m.camera('head_depth').id
        world=pixels@self.d.cam_xmat[camera].reshape(3,3).T+self.d.cam_xpos[camera]
        self.last_fit=self.pose.estimate(world[self.last_mask])
        if not self.last_fit['accepted']:self.rejected+=1;return None
        self.accepted+=1;return self.last_fit
