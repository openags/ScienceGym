"""Render explicit open-window counterfactuals to test the closed-grip gate.

These are labeled geometry/sensor diagnostics, never motor-execution evidence.
Only the native rendered images and robot sensors enter the tested observer.
"""
import hashlib
import json
from pathlib import Path
import sys
import time

import mujoco
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent;BASE=HERE.parents[1];ROOT=BASE.parents[1]
sys.path.insert(0,str(BASE))
from ftir_slider_posture import initialize_slider
from ftir_slider_vision import SliderObservation
from ftir_vision import KeyRowObservation
from observations import StateEstimate


def main():
    out=HERE/'grip_open_window_controls_02.json'
    if out.exists():raise FileExistsError(out)
    started=time.monotonic();run=BASE/'runs/ftir_slider_scan_02'
    cm=mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'))
    cd=initialize_slider(cm,[5.95,-5.20]);estimate=StateEstimate(cm,cd)
    sensors=np.load(run/'sensor_observations.npz');i=int(np.argmin(abs(sensors['time_s']-1.8)))
    packet={k:sensors[k][i] for k in sensors.files};packet['depth']=None;estimate.update(packet)
    prior=ROOT/'assets/nicolet_6700_mechanism_v1/slider_push_prior.json'
    shape=ROOT/'assets/nicolet_6700_mechanism_v1/revisions/passive_dynamics/geometry/nicolet_passive_dynamics.glb'
    observer=SliderObservation(cm,cd,prior,shape);keys=KeyRowObservation(cm,cd)
    m=mujoco.MjModel.from_xml_path(str(run/'world.xml'));m.opt.disableflags|=mujoco.mjtDisableBit.mjDSBL_CONTACT
    d=mujoco.MjData(m);trace=np.load(run/'trace.npz');j=int(np.argmin(abs(trace['time']-1.8)))
    # mj_step exposes pre-integration camera/encoder frames while qpos has
    # already advanced. Reconstruct the frame that produced the delivered
    # sensors, not the next integrated pose (a 2 ms mismatch in control 01).
    j-=1
    d.qpos[:]=trace['qpos'][j];d.qvel[:]=trace['qvel'][j];d.time=float(trace['time'][j])
    original_slide=float(d.joint('nicolet_door_slide').qpos[0])
    from depth_io import load as load_depth
    recorded_depth=next(z for t,z in load_depth(run) if abs(t-1.8)<1e-8)
    saved=np.load(run/'head_rgb_chunks/000000.npz');recorded_rgb=saved['rgb'][int(np.argmin(abs(saved['time']-1.8)))]
    reconstruction=None
    depth_renderer=mujoco.Renderer(m,360,640,max_geom=m.ngeom+1000);depth_renderer.enable_depth_rendering()
    rgb_renderer=mujoco.Renderer(m,360,640,max_geom=m.ngeom+1000)
    option=mujoco.MjvOption();option.geomgroup[3]=0;option.sitegroup[:]=0
    images=HERE/'grip_control_images_02';images.mkdir(exist_ok=True);rows=[]
    for travel in [original_slide,.004,.010,.030,.070,.104]:
        d.joint('nicolet_door_slide').qpos[0]=travel;mujoco.mj_forward(m,d)
        depth_renderer.update_scene(d,camera='head_depth',scene_option=option);depth=depth_renderer.render().copy()
        rgb_renderer.update_scene(d,camera='head_rgb',scene_option=option);rgb=rgb_renderer.render().copy()
        if travel==original_slide:
            reconstruction=dict(source_state_time_s=float(trace['time'][j]),delivered_sensor_time_s=float(sensors['time_s'][i]),
                                maximum_depth_difference_m=float(np.max(abs(depth-recorded_depth))),
                                differing_rgb_elements=int(np.count_nonzero(rgb!=recorded_rgb)),
                                maximum_rgb_difference=int(np.max(abs(rgb.astype(int)-recorded_rgb.astype(int)))))
            if not np.array_equal(depth,recorded_depth) or not np.array_equal(rgb,recorded_rgb):
                raise ValueError('Native sensor-frame reconstruction does not match recorded pixels: '+json.dumps(reconstruction))
        observed_keys=keys.observe(rgb,depth);grip=observer.observe(depth,observed_keys)
        name=f'window_{travel:.3f}.png';Image.fromarray(rgb).save(images/name)
        rows.append(dict(evaluator_slider_travel_m=travel,expected_closed=travel==original_slide,
                         key_row=observed_keys,grip=grip,image=name,passed=grip['accepted']==(travel==original_slide)))
        print(travel,grip,flush=True)
    depth_renderer.close();rgb_renderer.close()
    deps=[Path(__file__),BASE/'ftir_slider_vision.py',prior,shape,run/'world.xml',run/'controller_model/world.xml',run/'trace.npz',run/'sensor_observations.npz']
    report=dict(sensor_frame_reconstruction=reconstruction,rows=rows,passed=all(r['passed'] for r in rows),seconds=time.monotonic()-started,
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
        physical_execution=False,
        scope='Synthetic open-window render controls at one retained robot posture. Slider position is evaluator-only; observer receives native pixels and robot proprioception, not the controlled joint.')
    out.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
