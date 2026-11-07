"""Offline candidate: separate a supported lower plane before fitting the grip.

The bounded fit estimates visible grip displacement from unposed object CAD.
It does not read a simulated joint, segmentation mask or scene-object pose.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
import trimesh

from ftir_cover_geometry import register


class PlaneFilteredSliderObservation:
    def __init__(self,model,data,prior_path,shape_path):
        self.m,self.d=model,data
        self.prior=json.loads(Path(prior_path).read_text())
        if hashlib.sha256(Path(shape_path).read_bytes()).hexdigest()!=self.prior['source_shape_sha256']:
            raise ValueError('Known slider geometry changed')
        scene=trimesh.load(shape_path,force='scene',process=False)
        T,key=scene.graph['sample_access_slider_grip']
        self.mesh=scene.geometry[key].copy();self.mesh.apply_transform(T)
        self.center=self.mesh.bounds.mean(0)
        self.bounds=self.mesh.bounds.copy()
        self.mesh.apply_translation(-self.center);self.mesh.apply_scale(1000.)

    def observe(self,depth,key_observation):
        if depth is None or not key_observation or not key_observation['accepted']:
            return dict(accepted=False,reason='missing_key_registration_or_depth')
        R,t=register(key_observation,self.prior)
        depth=np.asarray(depth);h,w=depth.shape;camera=self.m.camera('head_depth').id
        focal=h/(2*np.tan(np.deg2rad(self.m.cam_fovy[camera])/2))
        y,x=np.mgrid[:h,:w];good=np.isfinite(depth)&(depth>.05)&(depth<2.)
        points=np.stack([(x+.5-w/2)*depth/focal,-(y+.5-h/2)*depth/focal,-depth],axis=-1)[good]
        world=points@self.d.cam_xmat[camera].reshape(3,3).T+self.d.cam_xpos[camera]
        local=(world-t)@R
        # Exclude the lower window surface and the front cover strip. The
        # grip's interior span is used to avoid its two rounded end faces.
        mask=(abs(local[:,0]-self.center[0])<.035)&(abs(local[:,1]-self.center[1])<.008)
        mask&=(local[:,2]>self.bounds[0,2]+.0004)&(local[:,2]<self.bounds[1,2]+.001)
        selected=local[mask]
        raw_count=len(selected);removed=0;plane_z=None
        lower=selected[selected[:,2]<self.center[2],2]
        if len(lower)>=16:
            candidate=min(lower,key=lambda z:-int(np.sum(abs(selected[:,2]-z)<.00025)))
            near=abs(selected[:,2]-candidate)<.00025
            if near.sum()>=16 and near.mean()>=.3 and np.ptp(selected[near,0])>.030:
                above=selected[:,2]>candidate+.00025
                removed=int((~above).sum());plane_z=float(candidate)
                selected=selected[above]
        if len(selected)<16:return dict(accepted=False,reason='insufficient_grip_depth',points=len(selected))
        millimetres=(selected-self.center)*1000.
        def residual(offset):
            query=millimetres-np.r_[0.,offset]
            _,distances,_=trimesh.proximity.closest_point(self.mesh,query)
            return distances
        starts=[np.array([v,0.]) for v in [-4.,-2.,0.,2.,4.]]
        fits=[least_squares(residual,s,bounds=([-7.,-1.],[7.,1.]),loss='soft_l1',f_scale=.15,max_nfev=70) for s in starts]
        fit=min(fits,key=lambda f:float(np.mean(residual(f.x)**2)))
        errors=residual(fit.x);inliers=errors<.25
        singular=np.linalg.svd(fit.jac,compute_uv=False)
        span=np.ptp(selected[inliers],axis=0) if np.any(inliers) else np.zeros(3)
        accepted=(int(inliers.sum())>=16 and float(np.mean(inliers))>=.8 and
                  span[0]>.030 and singular[-1]>.05*max(singular[0],1e-12) and
                  abs(fit.x[0])<2. and abs(fit.x[1])<.8)
        return dict(accepted=bool(accepted),reason=None if accepted else 'grip_fit_or_closed_position_rejected',
                    points=len(selected),inliers=int(inliers.sum()),observed_span_m=span.tolist(),
                    unfiltered_roi_points=raw_count,removed_lower_plane_points=removed,lower_plane_height_m=plane_z,
                    estimated_slider_offset_m=float(fit.x[0]/1000.),height_residual_m=float(fit.x[1]/1000.),
                    median_residual_m=float(np.median(errors)/1000.),maximum_inlier_residual_m=float(errors[inliers].max()/1000.) if np.any(inliers) else None,
                    fit_singular_values=singular.tolist(),
                    source='native_depth_registered_by_observed_control_row_and_public_grip_CAD')
