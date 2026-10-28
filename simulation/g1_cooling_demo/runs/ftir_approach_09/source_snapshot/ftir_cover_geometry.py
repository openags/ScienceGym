"""Register object-relative geometry, then observe the actual cylindrical grip."""
import numpy as np
from scipy.optimize import least_squares


def register(observation, prior):
    normal=np.array(observation['outward_normal']);normal/=np.linalg.norm(normal)
    row=np.array(observation['row_direction']);row-=row.dot(normal)*normal;row/=np.linalg.norm(row)
    known_normal=-np.array(prior['keys'][0]['inward_axis']);known_row=np.array([1.,0,0])
    basis=lambda r,n:np.column_stack([r,np.cross(n,r),n])
    rotation=basis(row,normal)@basis(known_row,known_normal).T
    source=np.array([k['center_m'] for k in prior['keys']])+known_normal*prior['key_cap_thickness_m']/2
    points=np.array([observation['buttons'][k['label']] for k in prior['keys']])
    translation=np.mean(points-source@rotation.T,axis=0)
    return rotation,translation


def observe_handle(model,data,depth,observation,prior):
    """Fit the known-radius bar to depth pixels without segmentation or truth.

    The key row supplies the cylinder axis and a bounded search region. A
    circle fit in the orthogonal plane refines its center in two dimensions;
    translation along the uniform bar remains the key-row estimate.
    """
    rotation,translation=register(observation,prior)
    center=translation+rotation@np.array(prior['closed_handle_center_m'])
    depth=np.asarray(depth);h,w=depth.shape;camera=model.camera('head_depth').id
    fy=h/(2*np.tan(np.deg2rad(model.cam_fovy[camera])/2));y,x=np.mgrid[:h,:w]
    points=np.stack([(x+.5-w/2)*depth/fy,-(y+.5-h/2)*depth/fy,-depth],axis=-1)
    good=np.isfinite(depth)&(depth>.05)&(depth<2)
    world=points[good]@data.cam_xmat[camera].reshape(3,3).T+data.cam_xpos[camera]
    local=(world-center)@rotation
    local=local[(abs(local[:,0])<.030)&(abs(local[:,1])<.012)&(abs(local[:,2])<.012)]
    if len(local)<16:return dict(accepted=False,reason='insufficient_handle_depth',points=len(local))
    yz=local[:,1:];radius=prior['handle_radius_m'];rng=np.random.default_rng(4109)
    candidates=[np.zeros(2)]
    for _ in range(240):
        a,b=yz[rng.choice(len(yz),2,replace=False)];delta=b-a;distance=np.linalg.norm(delta)
        if not .0002<distance<2*radius:continue
        normal=np.array([-delta[1],delta[0]])/distance
        offset=normal*np.sqrt(radius*radius-distance*distance/4)
        for c in [(a+b)/2+offset,(a+b)/2-offset]:
            if np.linalg.norm(c)<.006:candidates.append(c)
    best=None
    for candidate in candidates:
        residual=abs(np.linalg.norm(yz-candidate,axis=1)-radius);inside=residual<.00015
        score=(int(inside.sum()),-float(np.median(residual)))
        if best is None or score>best[0]:best=score,candidate,inside
    if best[2].sum()<16:return dict(accepted=False,reason='cylinder_not_supported',points=len(yz))
    selected=yz[best[2]]
    fit=least_squares(lambda c:np.linalg.norm(selected-c,axis=1)-radius,best[1],
                      bounds=([-.006,-.006],[.006,.006]),loss='soft_l1',f_scale=.00005)
    residual=abs(np.linalg.norm(yz-fit.x,axis=1)-radius);inside=residual<.00015
    vectors=yz[inside]-fit.x;direction=vectors/np.linalg.norm(vectors,axis=1)[:,None]
    spread=float(np.arccos(np.clip(np.min(direction@direction.T),-1,1)))
    axial_span=float(np.ptp(local[inside,0]))
    if inside.sum()<16 or spread<.35 or axial_span<.035 or np.linalg.norm(fit.x)>.005:
        return dict(accepted=False,reason='handle_fit_degenerate',points=int(inside.sum()),
                    angular_span_rad=spread,axial_span_m=axial_span)
    correction=rotation@np.r_[0.,fit.x]
    return dict(accepted=True,handle_m=(center+correction).tolist(),
                translation_m=(translation+correction).tolist(),rotation=rotation.tolist(),
                correction_m=correction.tolist(),cylinder_points=int(inside.sum()),
                angular_span_rad=spread,axial_span_m=axial_span,
                maximum_inlier_residual_m=float(np.max(residual[inside])),
                source='head_depth_cylinder_surface_with_key_row_axis_prior')
