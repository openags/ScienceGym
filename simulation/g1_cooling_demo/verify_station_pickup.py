"""Join independent walking, station handoff and actual pickup evidence.

Run the frozen attempt's controller and continuous-physics replay first. This
review checks that those results belong to one uninterrupted trace and that
arrival, posture preparation and sensor-based manipulation occur in order.
It cannot qualify a paper branch, tool actuation, or repeated reliability.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pickle

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def verify(folder):
    folder = Path(folder).resolve()
    read = lambda name: json.loads((folder / name).read_text())
    contract, result = read('contract.json'), read('result.json')
    assert contract['actor_module'] == 'station_pickup_actor'
    for name, key in [('trace.npz', 'trace_sha256'), ('responses.pkl', 'responses_sha256'),
                      ('contract.json', 'contract_sha256'), ('events.json', 'events_sha256')]:
        assert sha(folder / name) == result[key]
    assert sha(folder / 'world.xml') == contract['model_sha256']
    assert sha(folder / 'policy_source/preparation_targets.json') == contract['preparation_targets_sha256']
    physical, controller, limits = [read(name) for name in
        ['physical_review.json', 'controller_replay.json', 'source_limit_review.json']]
    assert physical['source_trace_sha256'] == limits['trace_sha256'] == result['trace_sha256']
    assert physical['verifier_sha256'] == controller['verifier_sha256'] == sha(folder / 'source_snapshot/verify_tool_grasp.py')
    events = read('events.json')
    responses = pickle.loads((folder / 'responses.pkl').read_bytes())
    sensor = dict(np.load(folder / 'sensors.npz'))
    trace = dict(np.load(folder / 'trace.npz'))
    marks = {name: [e for e in events if e.get('kind') == name] for name in
        ['station_arrived', 'station_posture_ready', 'sensor_based_pickup_handoff', 'observed_tool_plan']}
    complete_sequence = all(len(rows) == 1 for rows in marks.values())
    metrics = {}
    arrival_ok = posture_ok = step_ok = sequence_ok = False
    m = mujoco.MjModel.from_xml_path(str(folder / 'world.xml'))
    d = mujoco.MjData(m)
    if complete_sequence:
        times = [marks[name][0]['time_s'] for name in marks]
        sequence_ok = bool(np.all(np.diff(times) > 0.))
        indices = [int(np.argmin(abs(trace['time']-t))) for t in times]
        actual_times = trace['time'][indices]
        sequence_ok &= bool(np.max(abs(actual_times-times)) <= m.opt.timestep+1e-9)
        waypoint = contract['waypoint']
        position = trace['qpos'][indices[0], :2]
        position_error = float(np.linalg.norm(position-np.asarray(waypoint['goal_xy_m'])))
        quat = trace['qpos'][indices[0], 3:7]
        facing = Rotation.from_quat(quat[[1, 2, 3, 0]]).apply([1., 0., 0.])[:2]
        reference = np.asarray(contract['evaluation_forward_world_xy'])
        # Explicit 2-D determinant avoids NumPy versions that only accept
        # three-dimensional inputs to cross(); the heading metric is unchanged.
        signed_area = reference[0]*facing[1] - reference[1]*facing[0]
        heading_error = float(abs(np.arctan2(signed_area, reference@facing)))
        settled = (trace['time'] >= times[0]-1.) & (trace['time'] <= times[0])
        arrival_speed = float(np.max(np.linalg.norm(trace['qvel'][settled, :2], axis=1)))
        arrival_ok = (position_error <= waypoint['maximum_final_position_error_m']
            and heading_error <= waypoint['maximum_final_heading_error_rad']
            and arrival_speed <= waypoint['maximum_settled_speed_m_s'])
        targets = read('policy_source/preparation_targets.json')
        qa = [m.joint(n).qposadr[0] for n in targets]
        va = [m.joint(n).dofadr[0] for n in targets]
        posture_error = float(np.max(abs(trace['qpos'][indices[1], qa]-list(targets.values()))))
        posture_speed = float(np.max(abs(trace['qvel'][indices[1], va])))
        handoff = contract['station_handoff']
        posture_ok = (posture_error <= handoff['maximum_preparation_error_rad']
                      and posture_speed <= handoff['maximum_preparation_joint_speed_rad_s'])
        sole_heights = []
        for i in range(0, indices[0]+1, max(1, round(.01/m.opt.timestep))):
            d.qpos[:] = trace['qpos'][i]
            mujoco.mj_kinematics(m, d)
            sole_heights.append([float(d.site(side+'_sole').xpos[2]) for side in ['left', 'right']])
        foot_lifts = np.max(np.asarray(sole_heights)-sole_heights[0], axis=0)
        step_ok = bool(np.all(foot_lifts > .01))
        metrics.update(arrival_position_error_m=position_error, arrival_heading_error_rad=heading_error,
            maximum_last_second_arrival_speed_m_s=arrival_speed,
            prepared_joint_error_rad=posture_error, prepared_joint_speed_rad_s=posture_speed,
            maximum_each_sole_lift_before_arrival_m=foot_lifts.tolist(), stage_times_s=times)
    pickup_rows = [i for i, r in enumerate(responses) if r.get('mission_phase') == 'pickup']
    if pickup_rows:
        i = pickup_rows[0]
        if 'wrist_observed_m' in responses[i]:
            k = int(np.argmin(abs(trace['time']-sensor['time_s'][i])))
            d.qpos[:] = trace['qpos'][k]
            mujoco.mj_kinematics(m, d)
            metrics['first_pickup_wrist_estimation_error_m'] = float(np.linalg.norm(
                d.site('right_wrist_reference').xpos-np.asarray(responses[i]['wrist_observed_m'])))
    checks = dict(controller_replay=controller['passed'], continuous_physics_and_tool_outcome=physical['passed'],
        source_motor_limits=limits['passed'], uninterrupted_stage_order=sequence_ok,
        actual_station_arrival=arrival_ok, actual_preparation_posture=posture_ok,
        both_feet_lift_before_arrival=step_ok,
        controller_attempt_completed=bool(responses and responses[-1].get('complete') and
                                         not responses[-1].get('failure') and result['failure'] is None),
        no_return_to_walking=bool(pickup_rows and all(r.get('mission_phase') == 'pickup'
                                                   for r in responses[pickup_rows[0]:])))
    report = dict(scope=__doc__, passed=all(checks.values()), checks=checks, metrics=metrics,
        trace_sha256=result['trace_sha256'], contract_sha256=result['contract_sha256'],
        physical_review_sha256=sha(folder / 'physical_review.json'),
        controller_review_sha256=sha(folder / 'controller_replay.json'),
        source_limits_review_sha256=sha(folder / 'source_limit_review.json'), verifier_sha256=sha(__file__),
        qualified_repeated_navigation=False, qualified_repeated_grasp=False, qualified_paper_branch=False)
    (folder / 'station_pickup_review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)
    return report['passed']


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder')
    a = p.parse_args()
    if not verify(a.folder):
        raise SystemExit(1)
