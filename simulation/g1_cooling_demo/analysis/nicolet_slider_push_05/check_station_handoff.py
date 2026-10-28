"""Regress a station controller handoff with sensor-derived pose and global time."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
ROOT = BASE.parents[1]
sys.path.insert(0, str(BASE))
from ftir_slider_scan_actor import SliderScanActor
from ftir_slider_observed_actor import ObservedSliderActor
from ftir_slider_posture import initialize_slider
from observations import StateEstimate
from depth_io import load as load_depth


def main():
    output = HERE/'station_handoff_regression.json'
    if output.exists():
        raise FileExistsError(output)
    run = BASE/'runs/ftir_slider_06'
    model = mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'))
    legacy_path = run/'source_snapshot/ftir_slider_scan_actor.py'
    spec = importlib.util.spec_from_file_location('legacy_station_scan', legacy_path)
    legacy_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy_module)
    old = legacy_module.SliderScanActor(model, [5.95, -5.2])
    default = SliderScanActor(model, [5.95, -5.2])
    checks = dict(default_initial_pose_unchanged=bool(np.array_equal(old.d.qpos, default.d.qpos)),
                  default_foot_anchors_unchanged=bool(np.array_equal(old.estimate.anchors, default.estimate.anchors)))
    sensors = np.load(run/'sensor_observations.npz')
    frames = np.load(run/'head_rgb_chunks/000000.npz')
    depths = {round(float(t), 4):z.copy() for t,z in load_depth(run) if abs(t) < 1e-6 or abs(t-1.8) < 1e-6}

    def packet_at(t):
        i = int(np.argmin(abs(sensors['time_s']-t)))
        packet = {k:sensors[k][i] for k in sensors.files}
        packet['depth'] = depths[round(t, 4)]
        packet['rgb'] = frames['rgb'][int(np.argmin(abs(frames['time']-t)))]
        return packet

    first = {k:v for k,v in packet_at(0.).items() if k != 'right_touch_n'}
    old_response = old.update(first)
    default_response = default.update(first)
    checks['default_first_motor_torques_identical'] = bool(np.array_equal(old_response['torque'], default_response['torque']))
    supplied = initialize_slider(model, [5.95, -5.2])
    estimate = StateEstimate(model, supplied)
    native = packet_at(1.8)
    estimate.update({k:v for k,v in native.items() if k not in {'rgb', 'right_touch_n'}})
    before = supplied.qpos.copy()
    anchors = np.array([supplied.site(s+'_sole').xpos.copy() for s in ['left', 'right']])
    actor = ObservedSliderActor(model, [5.95, -5.2],
        run/'policy_source/slider_push_prior.json', run/'object_shape_source/nicolet_passive_dynamics.glb',
        initial_state=supplied, started_at=20.)
    checks['sensor_pose_preserved_at_construction'] = actor.d is supplied and bool(np.array_equal(before, actor.d.qpos))
    checks['sensor_foot_anchors_preserved'] = bool(np.array_equal(anchors, actor.estimate.anchors))
    delayed = dict(native, time_s=20.)
    response = actor.update(delayed)
    checks['global_time_does_not_trigger_initial_timeout'] = response['error'] is None and response['policy_state'] == 'observe'
    checks['handoff_does_not_claim_completion'] = not response['policy_complete']
    checks['handoff_torques_finite_and_bounded'] = bool(np.isfinite(response['torque']).all() and
        np.all(response['torque'] >= model.actuator_ctrlrange[:, 0]) and
        np.all(response['torque'] <= model.actuator_ctrlrange[:, 1]))
    checks['no_robot_pose_reset_on_first_sensor_update'] = bool(np.max(abs(actor.d.qpos-before)) < 1e-9)
    rejected = False
    try:
        actor.update(dict(delayed, time_s=19.))
    except ValueError as error:
        rejected = str(error) == 'Observation predates station handoff'
    checks['pre_handoff_packet_rejected'] = rejected
    deps = [Path(__file__), BASE/'ftir_slider_scan_actor.py', BASE/'ftir_slider_actor.py',
            BASE/'ftir_slider_observed_actor.py', legacy_path, run/'controller_model/world.xml',
            run/'sensor_observations.npz', run/'head_depth_index.json', run/'head_rgb_index.json']
    report = dict(passed=all(checks.values()), checks=checks,
                  maximum_default_torque_difference=float(np.max(abs(old_response['torque']-default_response['torque']))),
                  handoff_initial_root_estimate_m=before[:3].tolist(),
                  first_update_root_estimate_m=response['estimated_root_position_m'],
                  source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
                  scope='Controller-construction and clock regression using retained native sensor pose. The global handoff time is a test fixture; no walking or physical handoff execution is claimed.')
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
