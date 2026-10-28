"""Diagnose key registration with corrected depth at retained robot poses.

The observer receives RGB, depth and proprioception. Device geometry is used
after prediction to measure registration error, never to correct the actor.
These counterfactual images are not a new physical execution.
"""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import inspect_visible_surfaces as v
import mujoco
import numpy as np
from ftir_slider_vision import SliderObservation
from sensor_rendering import depth_renderer
from key_plane_refinement_candidate import KeyRowObservation
v.KeyRowObservation=KeyRowObservation


def main():
    run=v.BASE/'runs/ftir_approach_09';out=Path(__file__).with_name('refined_key_registration_09.json')
    if out.exists():raise FileExistsError(out)
    m=mujoco.MjModel.from_xml_path(str(run/'world.xml'));d=mujoco.MjData(m)
    cm=mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'));cd=v.initialize_slider(cm)
    estimate=v.StateEstimate(cm,cd);keys=v.KeyRowObservation(cm,cd)
    prior=json.loads((run/'policy_source/slider_push_prior.json').read_text())
    closed=SliderObservation(cm,cd,run/'policy_source/slider_push_prior.json',run/'object_shape_source/nicolet_passive_dynamics.glb')
    sensors=dict(np.load(run/'sensor_observations.npz'));trace=dict(np.load(run/'trace.npz'))
    renderer=depth_renderer(m,360,640);option=mujoco.MjvOption();option.geomgroup[3]=0;option.sitegroup[:]=0
    rows=[]
    try:
        for time in [134.5,136.5,137.2,137.3,137.8,138.4,138.6,225.5]:
            i=int(np.argmin(abs(sensors['time_s']-time)));ti=max(0,int(np.argmin(abs(trace['time']-time)))-1)
            d.qpos[:]=trace['qpos'][ti];mujoco.mj_forward(m,d)
            renderer.update_scene(d,camera='head_depth',scene_option=option);depth=renderer.render().copy()
            rgb=v.frame(run,'head_rgb_index.json','chunks',time)
            packet={k:sensors[k][i] for k in ['time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro']}
            packet['depth']=depth;estimate.update(packet)
            key=keys.observe(rgb,depth);fit=closed.observe(depth,key)
            if not key or not key['accepted']:raise ValueError('Key row rejected')
            # Evaluation begins after both observations above.
            tc=m.camera('head_depth').id;pc=cm.camera('head_depth').id
            transform=d.cam_xmat[tc].reshape(3,3)@cd.cam_xmat[pc].reshape(3,3).T
            normal=-np.array(prior['keys'][0]['inward_axis']);normal/=np.linalg.norm(normal)
            known=[]
            for index,k in enumerate(prior['keys']):
                body=d.body('nicolet_key_'+str(index))
                point=body.xpos+body.xmat.reshape(3,3)@(normal*prior['key_cap_thickness_m']/2)
                known.append((point-d.cam_xpos[tc])@transform+cd.cam_xpos[pc])
            known=np.array(known)
            observed=np.array([key['buttons'][k['label']] for k in prior['keys']])
            truth_normal=(d.body('nicolet_key_0').xmat.reshape(3,3)@normal)@transform
            error=observed-known
            normal_error=float(np.arccos(np.clip(np.dot(key['outward_normal'],truth_normal),-1.,1.)))
            row=dict(time_s=time,waist_yaw_rad=float(cd.joint('waist_yaw_joint').qpos[0]),
                     key_observation=key,grip_observation=fit,
                     evaluated_key_errors_m=error.tolist(),
                     evaluated_key_plane_errors_m=(error@truth_normal).tolist(),
                     evaluated_key_normal_error_rad=normal_error)
            rows.append(row);print(json.dumps(row),flush=True)
    finally:renderer.close()
    report=dict(scope=__doc__,rows=rows,physical_execution=False,source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(__file__).with_name('key_plane_refinement_candidate.py'),v.BASE/'ftir_vision.py',v.BASE/'ftir_slider_vision.py',v.BASE/'sensor_rendering.py',run/'trace.npz',run/'world.xml']})
    out.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
