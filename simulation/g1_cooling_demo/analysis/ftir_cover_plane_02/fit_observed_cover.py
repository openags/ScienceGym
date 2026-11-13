"""Offline sensor-only cover-plane predictions, saved before held-out review.

Use the observed static key/handle registration, head depth and robot sensors.
There is no moving-device pose or segmentation input to the plane fit.
"""
import hashlib
import json
from pathlib import Path
import sys

import mujoco
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/'simulation/g1_cooling_demo';sys.path.insert(0,str(BASE))
from ftir_hand import initialize_cover
from observations import StateEstimate
from depth_io import load


def fit(model,data,depth,pivot,rotation,previous_angle):
    h,w=depth.shape;camera=model.camera('head_depth').id
    fy=h/(2*np.tan(np.deg2rad(model.cam_fovy[camera])/2));y,x=np.mgrid[:h,:w]
    camera_points=np.stack([(x+.5-w/2)*depth/fy,-(y+.5-h/2)*depth/fy,-depth],axis=-1)
    valid=np.isfinite(depth)&(depth>.05)&(depth<2)
    world=camera_points[valid]@data.cam_xmat[camera].reshape(3,3).T+data.cam_xpos[camera]
    local=(world-pivot)@rotation
    radius=np.linalg.norm(local[:,1:],axis=1)
    keep=(abs(local[:,0])<.115)&(local[:,1]<.012)&(local[:,2]>-.004)&(radius>.04)&(radius<.28)
    local=local[keep]
    polar=-np.arctan2(local[:,2],-local[:,1]);local=local[abs(polar-previous_angle)<.12]
    if len(local)<150:return dict(accepted=False,reason='insufficient_depth',points=len(local))
    yz=local[:,1:];rng=np.random.default_rng(846);best=None
    for _ in range(300):
        a,b=yz[rng.choice(len(yz),2,replace=False)];delta=b-a;length=np.linalg.norm(delta)
        if length<.05:continue
        normal=np.array([-delta[1],delta[0]])/length
        if normal[1]<0:normal=-normal
        angle=-np.arctan2(normal[0],normal[1]);offset=float(a@normal)
        if not -np.pi/2<=angle<=.03 or abs(offset)>.005 or abs(angle-previous_angle)>.08:continue
        inside=abs(yz@normal-offset)<.0002
        if inside.sum()<150:continue
        span_x=float(np.ptp(local[inside,0]));span_r=float(np.ptp(yz[inside]@np.array([normal[1],-normal[0]])))
        if span_x<.08 or span_r<.08:continue
        if best is None or inside.sum()>best[0]:best=int(inside.sum()),inside
    if best is None:return dict(accepted=False,reason='no_supported_hinge_plane',points=len(local))
    selected=yz[best[1]];center=selected.mean(axis=0);_,_,vh=np.linalg.svd(selected-center,full_matrices=False)
    normal=vh[-1];normal*=1 if normal[1]>0 else -1;offset=float(center@normal)
    residual=abs(yz@normal-offset);inside=residual<.0002
    return dict(accepted=True,angle_rad=float(-np.arctan2(normal[0],normal[1])),offset_m=offset,
                points=int(inside.sum()),span_x_m=float(np.ptp(local[inside,0])),maximum_inlier_error_m=float(max(residual[inside])))


def main():
    folder=BASE/'runs/ftir_cover_08';out=Path(__file__).resolve().parent
    model=mujoco.MjModel.from_xml_path(str(folder/'controller_model/world.xml'))
    data=initialize_cover(model);estimate=StateEstimate(model,data)
    result=json.loads((folder/'result.json').read_text())
    event=next(e for e in result['actor_last_output']['events'] if e['state']=='observed_instrument_registered')
    pivot=np.array(event['estimated_hinge_m']);rotation=np.array(event['estimated_rotation'])
    sensors=np.load(folder/'sensor_observations.npz');rows=[];previous_angle=0.
    for t,depth in load(folder):
        if t<14 or t>22:continue
        i=np.argmin(abs(sensors['time_s']-t));packet={k:sensors[k][i] for k in sensors.files if k!='right_touch_n'};packet['depth']=None
        estimate.update(packet);prediction=fit(model,data,depth,pivot,rotation,previous_angle)
        if prediction['accepted']:previous_angle=prediction['angle_rad']
        row=dict(time_s=float(t),**prediction);rows.append(row);print(json.dumps(row),flush=True)
    predictions=out/'predictions.json';predictions.write_text(json.dumps(dict(scope=__doc__,run=folder.name,rows=rows),indent=2)+'\n')
    # Read evaluator truth only after predictions are serialized.
    plant=mujoco.MjModel.from_xml_path(str(folder/'world.xml'));trace=np.load(folder/'trace.npz');qa=plant.joint('nicolet_cover_hinge').qposadr[0]
    errors=[]
    for row in rows:
        if not row['accepted']:continue
        i=np.argmin(abs(trace['time']-row['time_s']));actual=float(trace['qpos'][i,qa]);errors.append(dict(time_s=row['time_s'],observed_angle_deg=np.rad2deg(row['angle_rad']),actual_angle_deg=np.rad2deg(actual),error_deg=np.rad2deg(row['angle_rad']-actual)))
    review=dict(scope='Held-out angle comparison; no actor feedback or physical success claim.',predictions_sha256=hashlib.sha256(predictions.read_bytes()).hexdigest(),rows=errors,
                maximum_absolute_error_deg=max([abs(r['error_deg']) for r in errors],default=None))
    (out/'held_out_review.json').write_text(json.dumps(review,indent=2)+'\n');print('review',review['maximum_absolute_error_deg'],flush=True)


if __name__=='__main__':main()
