"""Measure outcome-gate acceptance across eight retained observation poses."""
import hashlib
import json
from pathlib import Path
import sys

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1];ROOT = BASE.parents[1]
sys.path.insert(0, str(BASE))
from ftir_slider_posture import initialize_slider
from ftir_slider_outcome import SliderTargetObservation
from ftir_vision import KeyRowObservation
from observations import StateEstimate
from depth_io import load as load_depth


def main():
    output = HERE/'open_target_sequence.json'
    if output.exists():raise FileExistsError(output)
    run = BASE/'runs/ftir_slider_scan_02'
    model = mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'))
    data = initialize_slider(model);estimate = StateEstimate(model, data)
    sensors = np.load(run/'sensor_observations.npz')
    prior = ROOT/'assets/nicolet_6700_mechanism_v1/slider_push_prior.json'
    shape = ROOT/'assets/nicolet_6700_mechanism_v1/revisions/passive_dynamics/geometry/nicolet_passive_dynamics.glb'
    observer = SliderTargetObservation(model, data, prior, shape, .070)
    keys = KeyRowObservation(model, data)
    plant = mujoco.MjModel.from_xml_path(str(run/'world.xml'))
    plant.opt.disableflags |= mujoco.mjtDisableBit.mjDSBL_CONTACT
    state = mujoco.MjData(plant);trace = np.load(run/'trace.npz')
    depths = {round(t, 4):z for t,z in load_depth(run)}
    saved = np.load(run/'head_rgb_chunks/000000.npz')
    depth_renderer = mujoco.Renderer(plant, 360, 640, max_geom=plant.ngeom+1000)
    depth_renderer.enable_depth_rendering()
    rgb_renderer = mujoco.Renderer(plant, 360, 640, max_geom=plant.ngeom+1000)
    option = mujoco.MjvOption();option.geomgroup[3] = 0;option.sitegroup[:] = 0
    rows = []
    for t in np.arange(1.3, 2.001, .1):
        i = int(np.argmin(abs(sensors['time_s']-t)))
        packet = {k:sensors[k][i] for k in sensors.files};packet['depth'] = None
        estimate.update(packet)
        j = int(np.argmin(abs(trace['time']-t)))-1
        state.qpos[:] = trace['qpos'][j];state.qvel[:] = trace['qvel'][j]
        original = float(state.joint('nicolet_door_slide').qpos[0])
        for travel in [original, .0163, .064, .070, .076]:
            state.joint('nicolet_door_slide').qpos[0] = travel
            mujoco.mj_forward(plant, state)
            depth_renderer.update_scene(state, camera='head_depth', scene_option=option)
            depth = depth_renderer.render().copy()
            rgb_renderer.update_scene(state, camera='head_rgb', scene_option=option)
            rgb = rgb_renderer.render().copy()
            if travel == original:
                recorded_rgb = saved['rgb'][int(np.argmin(abs(saved['time']-t)))]
                if not np.array_equal(depth, depths[round(t,4)]) or not np.array_equal(rgb, recorded_rgb):
                    raise ValueError('Original native sensor reconstruction mismatch')
            detection = keys.observe(rgb, depth)
            outcome = observer.observe(depth, detection)
            row = dict(sensor_time_s=float(sensors['time_s'][i]),
                       evaluator_slider_position_m=travel, expected_at_target=travel == .070,
                       outcome=outcome)
            rows.append(row);print(json.dumps(row), flush=True)
    depth_renderer.close();rgb_renderer.close()
    targets = [r for r in rows if r['expected_at_target']]
    controls = [r for r in rows if not r['expected_at_target']]
    deps = [Path(__file__), BASE/'ftir_slider_outcome.py', BASE/'ftir_slider_vision.py',
            prior, shape, run/'world.xml', run/'controller_model/world.xml',
            run/'sensor_observations.npz', run/'trace.npz']
    report = dict(rows=rows, at_target_frames=len(targets),
        accepted_at_target_frames=sum(r['outcome']['accepted'] for r in targets),
        incorrect_acceptances=sum(r['outcome']['accepted'] for r in controls),
        control_frames=len(controls),
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
        original_native_sensor_arrays_reconstructed_exactly=True,
        scope='Temporal development measurement of unchanged target gate, including rejected at-target frames. No runtime integration, executed push or calibration credit.')
    output.write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':main()
