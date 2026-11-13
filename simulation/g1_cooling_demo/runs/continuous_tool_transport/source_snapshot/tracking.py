"""Depth foreground tracking against the robot's own estimated model.

The background render contains the robot and the known empty workbench only.
It is not simulator segmentation: target geometry and target state are absent.
"""
import numpy as np
import mujoco

class TrayTracker:
    def __init__(self,model,data):
        self.m,self.d=model,data
        self.renderer=mujoco.Renderer(model,height=180,width=320);self.renderer.enable_depth_rendering()
        self.option=mujoco.MjvOption();self.option.geomgroup[3]=0;self.option.sitegroup[:]=0
        self.last_mask=None
    def close(self):self.renderer.close()
    def observe(self,depth):
        if depth is None:return None
        self.renderer.update_scene(self.d,camera='head_depth',scene_option=self.option)
        expected=self.renderer.render();depth=np.asarray(depth);h,w=depth.shape
        fy=h/(2*np.tan(np.radians(58)/2));v,u=np.mgrid[:h,:w]
        foreground=np.isfinite(depth)&(depth>.05)&(depth<2)&(depth<expected-.008)
        camera=self.m.camera('head_depth').id
        pixels=np.stack([(u-w/2)*depth/fy,-(v-h/2)*depth/fy,-depth],axis=-1)
        world=pixels@self.d.cam_xmat[camera].reshape(3,3).T+self.d.cam_xpos[camera]
        foreground &= (world[:,:,0]>.385)&(world[:,:,0]<.8)&(abs(world[:,:,1])<.34)&(world[:,:,2]>.912)&(world[:,:,2]<1.18)
        self.last_mask=foreground
        cloud=world[foreground]
        if len(cloud)<30:return None
        lo,hi=np.quantile(cloud,[.05,.95],axis=0)
        # At the lifted pitch the camera can see only a narrow front wall.
        # Width and residual evidence remain usable; X span is not a gate.
        if hi[1]-lo[1]<.18:return None
        return dict(center_m=((lo+hi)/2).tolist(),low_m=lo.tolist(),high_m=hi.tolist(),points=len(cloud),source='depth_residual_against_proprioceptive_robot_model')
