"""Check horizontal map registration while retaining floor-anchored height.

The three-axis predecessor introduced up to 6.54 mm vertical bias. This
variant fits X/Y only, preserving the standing leg/known-floor height prior.
The unchanged 8 mm residual gate is not a guarantee of final pose accuracy.

Only the estimated robot map translation is perturbed. Retained native depth
and proprioception enter the fitter; plant root truth is reviewed afterwards.
These are localization diagnostics, not executed walking or calibration.
"""
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
from map_localization import MapLocalization
from ftir_slider_posture import initialize_slider
from observations import StateEstimate
from depth_io import load as load_depth


def main():
    output = HERE/'station_map_registration_xy.json'
    if output.exists():
        raise FileExistsError(output)
    run = BASE/'runs/ftir_slider_06'
    model = mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'))
    data = initialize_slider(model, [5.95, -5.20])
    estimate = StateEstimate(model, data)
    legacy_path = BASE/'runs/laboratory_mission_14/source_snapshot/map_localization.py'
    spec = importlib.util.spec_from_file_location('legacy_station_registration', legacy_path)
    legacy_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy_module)
    legacy = legacy_module.MapLocalization(model, data)
    default = MapLocalization(model, data)
    unchanged = bool(np.array_equal(legacy.rays, default.rays) and
                     np.array_equal(legacy.render(5), default.render(5)))
    legacy.close()
    default.close()
    fitter = MapLocalization(model, data, width=640, height=360, pixel_center=.5, translation_axes=(0,1))
    sensors = np.load(run/'sensor_observations.npz')
    times = [.8, 2.7, 107.0]
    depths = {round(float(t), 4):z.copy() for t,z in load_depth(run) if any(abs(t-s)<1e-6 for s in times)}
    rows = []
    for t in times:
        i = int(np.argmin(abs(sensors['time_s']-t)))
        packet = {k:sensors[k][i] for k in ['time_s', 'joint_position', 'joint_velocity', 'imu_quaternion', 'imu_gyro']}
        packet['depth'] = None
        for offset in [[0., 0., 0.], [.025, 0., 0.], [0., -.025, 0.], [.020, -.020, 0.]]:
            estimate.update(packet)
            baseline = data.qpos[:3].copy()
            data.qpos[:3] += offset
            mujoco.mj_kinematics(model, data)
            mujoco.mj_camlight(model, data)
            before = data.qpos[:3].copy()
            result = fitter.register(depths[round(t, 4)])
            row = dict(sensor_time_s=t, synthetic_estimate_offset_m=offset,
                       initial_sensor_estimate_m=baseline.tolist(), before_registration_m=before.tolist(),
                       final_estimate_m=data.qpos[:3].tolist(), registration=result)
            rows.append(row)
            print(json.dumps(row), flush=True)
    fitter.close()
    # Review truth only after every prediction is fixed.
    trace = np.load(run/'trace.npz')
    for row in rows:
        index = max(0, int(np.argmin(abs(trace['time']-row['sensor_time_s'])))-1)
        truth = trace['qpos'][index, :3]
        row['evaluator_root_position_m'] = truth.tolist()
        row['initial_position_error_m'] = float(np.linalg.norm(np.array(row['before_registration_m'])-truth))
        row['final_position_error_m'] = float(np.linalg.norm(np.array(row['final_estimate_m'])-truth))
    accepted = [r for r in rows if r['registration']['accepted']]
    deps = [Path(__file__), BASE/'map_localization.py', BASE/'observations.py', legacy_path,
            run/'controller_model/world.xml', run/'trace.npz', run/'sensor_observations.npz', run/'head_depth_index.json']
    report = dict(default_legacy_rays_and_map_render_unchanged=unchanged,
                  rows=rows, accepted=len(accepted), cases=len(rows),
                  floor_height_from_proprioception_preserved=all(abs(r['before_registration_m'][2]-r['final_estimate_m'][2])<1e-12 for r in rows),
                  maximum_accepted_position_error_m=max((r['final_position_error_m'] for r in accepted), default=None),
                  source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
                  scope=__doc__)
    output.write_text(json.dumps(report, indent=2)+'\n')
    if not unchanged:
        raise SystemExit('Default localization behavior changed')


if __name__ == '__main__':
    main()
