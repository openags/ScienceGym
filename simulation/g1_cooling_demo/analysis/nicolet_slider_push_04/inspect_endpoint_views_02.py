"""Evaluate axial-coverage rejection on different retained endpoint geometry.

Run05 robot pose and four new viewing angles follow the run04 false positive.
The physical acceptance limits remain unchanged; boundary false rejections
are retained. The observer is not in the runtime actor.

The changed torso and slider states are evaluator-only counterfactuals. The
observer receives native RGB-D, robot encoders and IMU, never equipment truth.
This does not establish that the viewing postures have been executed safely.
"""
import hashlib
import json
from pathlib import Path
import sys

import mujoco
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
ROOT = BASE.parents[1]
sys.path.insert(0, str(BASE))
from ftir_slider_posture import initialize_slider
from ftir_slider_outcome import SliderRangeObservation
from ftir_vision import KeyRowObservation
from observations import StateEstimate, robot_joints


def main():
    output = HERE/'endpoint_views_02.json'
    if output.exists():
        raise FileExistsError(output)
    run = BASE/'runs/ftir_slider_05'
    result = json.loads((run/'result.json').read_text())
    event = next(e for e in result['actor_last_output']['events'] if 'grip_observations' in e)
    offsets = [o['estimated_slider_offset_m'] for o in event['grip_observations']]
    baseline = float(np.median(offsets))
    cm = mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'))
    cd = initialize_slider(cm, [5.95, -5.20])
    estimate = StateEstimate(cm, cd)
    prior = run/'policy_source/slider_push_prior.json'
    shape = run/'object_shape_source/nicolet_passive_dynamics.glb'
    observer = SliderRangeObservation(cm, cd, prior, shape, event['grip_observations'])
    keys = KeyRowObservation(cm, cd)
    m = mujoco.MjModel.from_xml_path(str(run/'world.xml'))
    m.opt.disableflags |= mujoco.mjtDisableBit.mjDSBL_CONTACT
    d = mujoco.MjData(m)
    trace = np.load(run/'trace.npz')
    final_qpos = trace['qpos'][-1].copy()
    d.qpos[:] = final_qpos
    actual = float(d.joint('nicolet_door_slide').qpos[0])
    names = [m.joint(j).name for j in robot_joints(m)]
    depth_renderer = mujoco.Renderer(m, 360, 640, max_geom=m.ngeom+1000)
    depth_renderer.enable_depth_rendering()
    rgb_renderer = mujoco.Renderer(m, 360, 640, max_geom=m.ngeom+1000)
    option = mujoco.MjvOption()
    option.geomgroup[3] = 0
    option.sitegroup[:] = 0
    images = HERE/'endpoint_view_images_02'
    images.mkdir(exist_ok=True)
    rows = []
    for yaw in [-.425, -.475, -.525, -.575]:
        for travel in [0., .060, .064, .065, .066, .068, .070, .072, .074, .075, .076, .080, .104, actual]:
            d.qpos[:] = final_qpos
            d.joint('waist_yaw_joint').qpos[0] = yaw
            d.joint('nicolet_door_slide').qpos[0] = travel
            d.qvel[:] = 0.
            mujoco.mj_forward(m, d)
            packet = dict(time_s=0., depth=None,
                          joint_position=np.array([d.sensor(n+'_encoder').data[0] for n in names]),
                          joint_velocity=np.array([d.sensor(n+'_velocity').data[0] for n in names]),
                          imu_quaternion=d.sensor('imu_orientation').data.copy(),
                          imu_gyro=d.sensor('imu_angular_velocity').data.copy())
            estimate.update(packet)
            depth_renderer.update_scene(d, camera='head_depth', scene_option=option)
            depth = depth_renderer.render().copy()
            rgb_renderer.update_scene(d, camera='head_rgb', scene_option=option)
            rgb = rgb_renderer.render().copy()
            key_row = keys.observe(rgb, depth)
            outcome = observer.observe(depth, key_row)
            corrected = None
            geometry_ok = False
            if 'estimated_slider_position_m' in outcome:
                corrected = outcome['estimated_slider_position_m']-baseline
                singular = outcome['fit_singular_values']
                geometry_ok = (outcome['inliers'] >= 16 and
                               outcome['inliers']/outcome['points'] >= .8 and
                               outcome['observed_span_m'][0] > .030 and
                               singular[-1] > .05*max(singular[0], 1e-12) and
                               abs(outcome['height_residual_m']) < .0008)
            # Predeclared development guard band strictly INSIDE the physical
            # 65-75 mm requirement. This candidate is not a runtime gate.
            candidate = outcome['accepted']
            name = None
            if travel == .070:
                name = f'counterfactual_70mm_yaw_{yaw:.3f}.png'
                Image.fromarray(rgb).save(images/name)
            row = dict(evaluator_torso_yaw_rad=yaw, evaluator_slider_position_m=travel,
                       expected_inside_physical_window=.065 <= travel <= .075,
                       key_registration_accepted=bool(key_row and key_row['accepted']),
                       outcome=outcome, baseline_corrected_position_m=corrected,
                       geometry_quality_accepted=bool(geometry_ok),
                       development_guard_band_accepted=candidate, image=name)
            rows.append(row)
            print(json.dumps(row), flush=True)
    depth_renderer.close()
    rgb_renderer.close()
    positive = [r for r in rows if r['expected_inside_physical_window']]
    negative = [r for r in rows if not r['expected_inside_physical_window']]
    deps = [Path(__file__), BASE/'ftir_slider_outcome.py', BASE/'ftir_slider_vision.py',
            BASE/'ftir_vision.py', BASE/'observations.py', prior, shape,
            run/'world.xml', run/'controller_model/world.xml', run/'result.json', run/'trace.npz']
    report = dict(rows=rows, initial_observed_closed_offsets_m=offsets,
                  initial_observed_baseline_m=baseline,
                  candidate_guard_band_m=[.066, .074],
                  unchanged_physical_requirement_m=[.065, .075],
                  positive_frames=len(positive), negative_frames=len(negative),
                  candidate_true_acceptances=sum(r['development_guard_band_accepted'] for r in positive),
                  candidate_false_acceptances=sum(r['development_guard_band_accepted'] for r in negative),
                  source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
                  physical_execution=False, runtime_integrated=False, calibrated=False,
                  scope=__doc__)
    output.write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
