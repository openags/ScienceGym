"""Find a tweezer-shaped RGB-D component without simulator object state.

Inputs are camera pixels, robot-derived camera calibration, a fixed bench map
and declared object dimensions. The dark-material threshold is a provisional
appearance prior; this module does not establish grasp-pose accuracy.
"""
import numpy as np
from scipy.ndimage import label


def detect(rgb, depth, world_from_depth_camera, world_from_rgb_camera, depth_fovy, rgb_fovy, bounds):
    rgb=np.asarray(rgb);depth=np.asarray(depth,dtype=float)
    h,w=depth.shape;rh,rw=rgb.shape[:2]
    fy=h/(2*np.tan(np.deg2rad(depth_fovy/2)))
    y,x=np.mgrid[:h,:w]
    local=np.stack([(x+.5-w/2)*depth/fy,-(y+.5-h/2)*depth/fy,-depth],axis=-1)
    D=np.asarray(world_from_depth_camera);C=np.asarray(world_from_rgb_camera)
    world=local@D[:3,:3].T+D[:3,3]
    color_local=(world-C[:3,3])@C[:3,:3]
    z=-color_local[:,:,2];f=rh/(2*np.tan(np.deg2rad(rgb_fovy/2)))
    u=np.rint(rw/2-.5+f*color_local[:,:,0]/np.maximum(z,1e-9)).astype(int)
    v=np.rint(rh/2-.5-f*color_local[:,:,1]/np.maximum(z,1e-9)).astype(int)
    valid=np.isfinite(depth)&(depth>.05)&(depth<2)&(z>.05)&(u>=0)&(u<rw)&(v>=0)&(v<rh)
    lower,upper=np.asarray(bounds)
    valid &= np.all((world>=lower)&(world<=upper),axis=-1)
    intensity=np.full((h,w),255.,dtype=float)
    intensity[valid]=rgb[v[valid],u[valid],:3].mean(axis=1)
    mask=valid&(intensity<42.)
    labels,count=label(mask,structure=np.ones((3,3)))
    rows=[];clouds={}
    for k in range(1,count+1):
        points=world[labels==k]
        if len(points)<60:continue
        center=points.mean(axis=0)
        eig,axes=np.linalg.eigh(np.cov((points-center).T));axes=axes[:,::-1]
        local=(points-center)@axes
        lo,hi=np.quantile(local,[.01,.99],axis=0);span=hi-lo
        checks=dict(length=.09<span[0]<.16,width=.003<span[1]<.03,thickness=span[2]<.02)
        row=dict(component=k,points=len(points),center_m=center.tolist(),principal_axes=axes.tolist(),
            observed_spans_m=span.tolist(),checks={k:bool(v) for k,v in checks.items()})
        rows.append(row);clouds[k]=points
    candidates=sorted([r for r in rows if all(r['checks'].values())],key=lambda r:-r['points'])
    result=dict(scope=__doc__,candidate_found=bool(candidates),components=rows,
        source='Native RGB intensity registered onto native depth; own-robot camera frames and fixed bench bounds',
        appearance_threshold_uint8=42.,qualified_grasp_pose=False)
    if candidates:
        result['candidate']=candidates[0]
        return result,clouds[candidates[0]['component']]
    return result,np.empty((0,3))
