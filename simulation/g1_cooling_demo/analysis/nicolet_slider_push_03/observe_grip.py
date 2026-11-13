"""Evaluate closed-grip observation on native recorded preparation pixels."""
import hashlib
import json
from pathlib import Path
import sys
import time

import mujoco
import numpy as np

HERE=Path(__file__).resolve().parent;BASE=HERE.parents[1];ROOT=BASE.parents[1]
sys.path.insert(0,str(BASE))
from depth_io import load as load_depth
from ftir_slider_posture import initialize_slider
from ftir_slider_vision import SliderObservation
from ftir_vision import KeyRowObservation
from observations import StateEstimate


def main():
    out=HERE/'grip_observation.json'
    if out.exists():raise FileExistsError(out)
    started=time.monotonic();run=BASE/'runs/ftir_slider_scan_02'
    m=mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'))
    d=initialize_slider(m,[5.95,-5.20]);estimate=StateEstimate(m,d);keys=KeyRowObservation(m,d)
    prior=ROOT/'assets/nicolet_6700_mechanism_v1/slider_push_prior.json'
    shape=ROOT/'assets/nicolet_6700_mechanism_v1/revisions/passive_dynamics/geometry/nicolet_passive_dynamics.glb'
    observer=SliderObservation(m,d,prior,shape)
    sensors=np.load(run/'sensor_observations.npz');colors=np.load(run/'head_rgb_chunks/000000.npz')
    rows=[]
    for t,depth in load_depth(run):
        if t<1.29:continue
        if t>2.01:break
        i=int(np.argmin(abs(sensors['time_s']-t)))
        packet={k:sensors[k][i] for k in sensors.files};packet['depth']=None;estimate.update(packet)
        image=colors['rgb'][int(np.argmin(abs(colors['time']-t)))]
        observation=keys.observe(image,depth)
        grip=observer.observe(depth,observation)
        rows.append(dict(time_s=t,key_row=observation,grip=grip))
        print(round(t,3),grip,flush=True)
    deps=[Path(__file__),BASE/'ftir_slider_vision.py',BASE/'ftir_vision.py',BASE/'ftir_cover_geometry.py',prior,shape,run/'sensor_observations.npz',run/'controller_model/world.xml',run/'head_depth_index.json',run/'head_rgb_index.json']
    report=dict(rows=rows,accepted=sum(r['grip']['accepted'] for r in rows),
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
        scope='Recorded preparation pixels without plant poses or device joints. One closed-window setup only; no open-window discrimination or hardware calibration claim.',
        seconds=time.monotonic()-started)
    out.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
