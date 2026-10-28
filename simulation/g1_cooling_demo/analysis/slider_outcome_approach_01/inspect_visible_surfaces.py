"""Compare native-depth fits with public CAD faces visible from the camera.

Offline diagnosis only. Recorded closed observations establish the baseline;
no device pose or joint position enters either candidate fit. All start fits
and their objective values are retained, including rejected alternatives.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))
import mujoco
import numpy as np
import trimesh
from scipy.optimize import least_squares
from ftir_cover_geometry import register
from ftir_slider_outcome import SliderRangeObservation
from ftir_slider_posture import initialize_slider
from ftir_vision import KeyRowObservation
from observations import StateEstimate


def frame(run, name, key, time, depth=False):
    rows=json.loads((run/name).read_text())[key]
    for row in rows:
        with np.load(run/row['path']) as a:
            indexes=np.flatnonzero(abs(a['time']-time)<1e-7)
            if not len(indexes):continue
            if depth:
                raw=a['bytes'];pixels=raw.transpose(1,2,3,0).copy().view('<f4').reshape(raw.shape[1:])
            else:pixels=a['rgb']
            return pixels[indexes[0]].copy()
    raise ValueError('Native frame missing')


def main(run, time, output):
    run, output=Path(run), Path(output)
    if output.exists():raise FileExistsError(output)
    events=json.loads((run/'result.json').read_text())['actor_last_output']['events']
    baseline=next(e['grip_observations'] for e in events if 'grip_observations' in e)
    cm=mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'))
    cd=initialize_slider(cm)
    with np.load(run/'sensor_observations.npz') as a:
        i=int(np.argmin(abs(a['time_s']-time)))
        if abs(a['time_s'][i]-time)>1e-7:raise ValueError('Sensor timestamp missing')
        packet={k:a[k][i] for k in ['time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro']}
    depth=frame(run,'head_depth_index.json','parts',time,True)
    rgb=frame(run,'head_rgb_index.json','chunks',time)
    packet['depth']=depth;StateEstimate(cm,cd).update(packet)
    keys=KeyRowObservation(cm,cd).observe(rgb,depth)
    observer=SliderRangeObservation(cm,cd,run/'policy_source/slider_push_prior.json',
                                    run/'object_shape_source/nicolet_passive_dynamics.glb',baseline)
    original=observer.observe(depth,keys)
    if not keys or not keys['accepted']:raise ValueError('Key registration rejected')
    R,t=register(keys,observer.prior)
    h,w=depth.shape;camera=cm.camera('head_depth').id
    focal=h/(2*np.tan(np.deg2rad(cm.cam_fovy[camera])/2))
    y,x=np.mgrid[:h,:w];good=np.isfinite(depth)&(depth>.05)&(depth<2.)
    p=np.stack([(x+.5-w/2)*depth/focal,-(y+.5-h/2)*depth/focal,-depth],axis=-1)[good]
    local=(p@cd.cam_xmat[camera].reshape(3,3).T+cd.cam_xpos[camera]-t)@R
    mask=(abs(local[:,0]-observer.center[0])<.035)&(abs(local[:,1]-observer.center[1])<.008)
    mask&=(local[:,2]>observer.bounds[0,2]+.0004)&(local[:,2]<observer.bounds[1,2]+.001)
    selected=local[mask];millimetres=(selected-observer.center)*1000.
    camera_local=((cd.cam_xpos[camera]-t)@R-observer.center)*1000.
    mesh=observer.mesh
    visible=np.einsum('ij,ij->i',mesh.face_normals,camera_local-mesh.triangles_center)>0
    front=trimesh.Trimesh(vertices=mesh.vertices,faces=mesh.faces[visible],process=False)
    rows=[]
    for label,surface in [('all_faces',mesh),('camera_facing_faces',front)]:
        def residual(offset):
            return trimesh.proximity.closest_point(surface,millimetres-np.r_[0.,offset])[1]
        for start in [-6.,-4.,-2.,0.,2.,4.,6.]:
            fit=least_squares(residual,[start,0.],bounds=([-7.,-1.],[7.,1.]),loss='soft_l1',f_scale=.15,max_nfev=70)
            errors=residual(fit.x);inliers=errors<.25
            singular=np.linalg.svd(fit.jac,compute_uv=False)
            span=np.ptp(selected[inliers],axis=0) if np.any(inliers) else np.zeros(3)
            position=.070+fit.x[0]/1000.-observer.baseline
            quality=(inliers.sum()>=16 and inliers.mean()>=.8 and span[0]>.030
                     and singular[-1]>.05*max(singular[0],1e-12) and abs(fit.x[1])<.8)
            accepted=quality and span[1]>=observer.minimum_axial_span and span[2]>=observer.minimum_height_span and .066<=position<=.074
            rows.append(dict(surface=label,start_offset_mm=start,fit_offset_mm=fit.x.tolist(),
                             mean_squared_residual_mm2=float(np.mean(errors**2)),robust_cost=float(fit.cost),
                             points=len(selected),inliers=int(inliers.sum()),span_m=span.tolist(),
                             singular_values=singular.tolist(),corrected_position_m=float(position),
                             same_thresholds_accepted=bool(accepted)))
    report=dict(scope=__doc__,run=str(run),time_s=time,original=original,rows=rows,
                camera_in_grip_frame_mm=camera_local.tolist(),mesh_faces=len(mesh.faces),visible_faces=int(visible.sum()),
                source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),run/'result.json',run/'sensor_observations.npz',run/'head_rgb_index.json',run/'head_depth_index.json',BASE/'ftir_slider_vision.py',BASE/'ftir_slider_outcome.py']})
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(original=original,rows=rows)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('time',type=float);p.add_argument('output');a=p.parse_args()
    main(a.run,a.time,a.output)
