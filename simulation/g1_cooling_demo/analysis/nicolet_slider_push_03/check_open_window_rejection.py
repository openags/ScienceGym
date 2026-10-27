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
    out=HERE/'grip_open_window_controls.json'
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
    d.qpos[:]=trace['qpos'][j]
    depth_renderer=mujoco.Renderer(m,360,640,max_geom=m.ngeom+1000);depth_renderer.enable_depth_rendering()
    rgb_renderer=mujoco.Renderer(m,360,640,max_geom=m.ngeom+1000)
    option=mujoco.MjvOption();option.geomgroup[3]=0;option.sitegroup[:]=0
    images=HERE/'grip_control_images';images.mkdir(exist_ok=True);rows=[]
    for travel in [0.,.004,.010,.030,.070,.104]:
        d.joint('nicolet_door_slide').qpos[0]=travel;mujoco.mj_forward(m,d)
        depth_renderer.update_scene(d,camera='head_depth',scene_option=option);depth=depth_renderer.render().copy()
        rgb_renderer.update_scene(d,camera='head_rgb',scene_option=option);rgb=rgb_renderer.render().copy()
        observed_keys=keys.observe(rgb,depth);grip=observer.observe(depth,observed_keys)
        name=f'window_{travel:.3f}.png';Image.fromarray(rgb).save(images/name)
        rows.append(dict(evaluator_slider_travel_m=travel,expected_closed=travel==0.,
                         key_row=observed_keys,grip=grip,image=name,passed=grip['accepted']==(travel==0.)))
        print(travel,grip,flush=True)
    depth_renderer.close();rgb_renderer.close()
    deps=[Path(__file__),BASE/'ftir_slider_vision.py',prior,shape,run/'world.xml',run/'controller_model/world.xml',run/'trace.npz',run/'sensor_observations.npz']
    report=dict(rows=rows,passed=all(r['passed'] for r in rows),seconds=time.monotonic()-started,
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
        physical_execution=False,
        scope='Synthetic open-window render controls at one retained robot posture. Slider position is evaluator-only; observer receives native pixels and robot proprioception, not the controlled joint.')
    out.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
