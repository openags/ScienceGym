"""Register native depth to the actor's static map using projective ICP.

Inputs are pixels, encoders/IMU in the actor data, and the public static map.
Robot pixels are masked by the actor's own geometry. No plant contacts,
object poses, segmentation labels or evaluator references are consumed.
"""
import mujoco
import numpy as np


class MapLocalization:
    def __init__(self,model,data,width=320,height=180,pixel_center=0.):
        self.m,self.d=model,data
        self.width,self.height=int(width),int(height)
        if self.width!=width or self.height!=height or min(self.width,self.height)<=0 or pixel_center not in (0.,.5):
            raise ValueError('Invalid depth registration image geometry')
        self.renderer=mujoco.Renderer(model,height=self.height,width=self.width,max_geom=max(10000,model.ngeom+1000))
        self.renderer.enable_depth_rendering();self.option=mujoco.MjvOption();self.option.sitegroup[:]=0
        self.groups=model.geom_group.copy();self.layer=self.groups.copy()
        robot=set()
        for i in range(1,model.nbody):
            root=i
            while model.body_parentid[root]>0:root=int(model.body_parentid[root])
            if model.body(root).name=='pelvis':robot.add(i)
        for i in range(model.ngeom):
            if self.groups[i]!=3:self.layer[i]=4 if int(model.geom_bodyid[i]) in robot else 5
        self.camera=model.camera('head_depth').id
        h,w=self.height,self.width;fy=h/(2*np.tan(np.radians(float(model.cam_fovy[self.camera]))/2));v,u=np.mgrid[:h,:w]
        self.rays=np.stack([(u+pixel_center-w/2)/fy,-(v+pixel_center-h/2)/fy,-np.ones((h,w))],axis=-1)

    def close(self):self.renderer.close()

    def render(self,layer):
        try:
            self.m.geom_group[:]=self.layer;self.option.geomgroup[:]=0;self.option.geomgroup[layer]=1
            self.renderer.update_scene(self.d,camera='head_depth',scene_option=self.option)
            return self.renderer.render().copy()
        finally:self.m.geom_group[:]=self.groups

    def register(self,depth,iterations=8):
        depth=np.asarray(depth);assert depth.shape==(self.height,self.width)
        m,d=self.m,self.d;initial=d.qpos[:3].copy();history=[]
        robot_depth=self.render(4)
        for iteration in range(iterations):
            expected=self.render(5)
            camera_points=self.rays*expected[:,:,None]
            dx=(np.roll(camera_points,-1,axis=1)-np.roll(camera_points,1,axis=1))*.5
            dy=(np.roll(camera_points,-1,axis=0)-np.roll(camera_points,1,axis=0))*.5
            normal=np.cross(dx,dy);length=np.linalg.norm(normal,axis=-1)
            normal/=np.maximum(length,1e-12)[:,:,None]
            valid=np.isfinite(depth)&(depth>.15)&(depth<4)&(expected>.15)&(expected<4)&(abs(depth-expected)<.12)&(length>1e-8)
            valid&=~((robot_depth<4)&(robot_depth<expected+.03))
            # Reject depth edges instead of treating silhouette gradients as planes.
            for axis in [0,1]:
                valid&=(abs(np.roll(expected,1,axis=axis)-expected)<.03)&(abs(np.roll(expected,-1,axis=axis)-expected)<.03)
            valid[:2]=False;valid[-2:]=False;valid[:,:2]=False;valid[:,-2:]=False
            sample=np.zeros_like(valid);sample[::2,::2]=True;valid&=sample
            rotation=d.cam_xmat[self.camera].reshape(3,3)
            normals=normal[valid]@rotation.T
            difference=(self.rays*(depth-expected)[:,:,None])[valid]@rotation.T
            residual=np.einsum('ij,ij->i',normals,difference)
            weight=np.minimum(1.,.008/np.maximum(abs(residual),1e-9))
            lhs=(normals*weight[:,None]).T@normals;rhs=-(normals*weight[:,None]).T@residual
            eigen=np.linalg.eigvalsh(lhs)
            if len(residual)<150 or eigen[0]<1.:
                d.qpos[:3]=initial;mujoco.mj_kinematics(m,d);mujoco.mj_camlight(m,d)
                return dict(accepted=False,reason='insufficient_static_geometry',points=len(residual),eigenvalues=eigen.tolist(),iterations=history)
            step=np.linalg.solve(lhs+np.eye(3)*1e-4,rhs)
            norm=float(np.linalg.norm(step));step*=min(1.,.025/max(norm,1e-12))
            history.append(dict(points=len(residual),median_residual_m=float(np.median(abs(residual))),step_m=step.tolist(),eigenvalues=eigen.tolist()))
            d.qpos[:3]+=step;mujoco.mj_kinematics(m,d);mujoco.mj_camlight(m,d)
            if np.linalg.norm(d.qpos[:3]-initial)>.12:
                d.qpos[:3]=initial;mujoco.mj_kinematics(m,d);mujoco.mj_camlight(m,d)
                return dict(accepted=False,reason='correction_outside_local_basin',iterations=history)
            if norm<.0001:break
        correction=d.qpos[:3]-initial
        accepted=bool(history and history[-1]['median_residual_m']<.008)
        position=d.qpos[:3].copy()
        if not accepted:d.qpos[:3]=initial;mujoco.mj_kinematics(m,d);mujoco.mj_camlight(m,d)
        return dict(accepted=accepted,position_m=position.tolist(),correction_m=correction.tolist(),iterations=history,source='native_depth_static_map_projective_registration')
