"""Independently check one sensor-based unloaded aisle arrival and its physics."""
import argparse
import json
from pathlib import Path
import pickle

import numpy as np

from run_dex3_walking import sha
from verify_dex3_walking import verify


def review(folder):
    folder = Path(folder)
    contract = json.loads((folder / 'contract.json').read_text())
    limits = contract['waypoint']
    verify(folder)
    physical = json.loads((folder / 'walking_review.json').read_text())
    with (folder / 'responses.pkl').open('rb') as stream:
        responses = pickle.load(stream)
    trace = dict(np.load(folder / 'trace.npz'))
    sensors = dict(np.load(folder / 'sensors.npz'))
    indices = np.rint(sensors['time_s'] / contract['physics_period_s']).astype(int)
    estimates = np.asarray([r['navigation_position_m'] for r in responses])
    actual_xy = trace['qpos'][indices, :2]
    errors = np.linalg.norm(estimates[:, :2] - actual_xy, axis=1)
    last = responses[-1]
    stop_at = last['navigation_stop_at_s']
    final_error = float(np.linalg.norm(trace['qpos'][-1, :2] - limits['goal_xy_m']))
    def yaw(q):
        w, x, y, z = q
        return np.arctan2(2*(w*z+x*y),1-2*(y*y+z*z))
    heading_delta = yaw(trace['qpos'][-1, 3:7])-yaw(np.asarray(contract['initial_qpos'])[3:7])
    heading_error = float(abs(np.arctan2(np.sin(heading_delta),np.cos(heading_delta))))
    if stop_at is not None:
        settled = trace['time'] >= stop_at + limits['settling_delay_after_stop_s']
        speed = np.linalg.norm(trace['qvel'][settled, :2], axis=1)
        maximum_speed = float(speed.max()) if len(speed) else None
        settled_duration = float(trace['time'][-1] - stop_at - limits['settling_delay_after_stop_s'])
    else:
        maximum_speed, settled_duration = None, 0.
    checks = dict(native_physics_and_controller_checks=physical['passed'],
        sensor_actor_reported_arrival=last['navigation_stage'] == 'arrived',
        actual_final_waypoint=final_error <= limits['maximum_final_position_error_m'],
        actual_final_heading=heading_error <= limits['maximum_final_heading_error_rad'],
        bounded_odometry_error=float(errors.max()) <= limits['maximum_odometry_error_m'],
        stopped_without_restart=stop_at is not None and all(np.max(abs(r['commanded_velocity'])) == 0.
            for r, t in zip(responses, sensors['time_s']) if t >= stop_at),
        actual_settled_speed=maximum_speed is not None and maximum_speed <= limits['maximum_settled_speed_m_s'],
        sufficient_settled_duration=settled_duration >= limits['minimum_settled_duration_s'])
    report = dict(scope=__doc__, passed=all(checks.values()), checks=checks,
        contract_sha256=sha(folder / 'contract.json'), trace_sha256=sha(folder / 'trace.npz'),
        responses_sha256=sha(folder / 'responses.pkl'), physical_review_sha256=sha(folder / 'walking_review.json'),
        verifier_sha256=sha(__file__), final_actual_waypoint_error_m=final_error,
        final_actual_heading_error_rad=heading_error,
        maximum_odometry_error_m=float(errors.max()), reported_stop_at_s=stop_at,
        maximum_actual_settled_speed_m_s=maximum_speed, settled_duration_s=settled_duration,
        qualified_repeated_navigation=False, qualified_station_manipulation=False, qualified_paper_branch=False)
    (folder / 'waypoint_review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder')
    review(p.parse_args().folder)
