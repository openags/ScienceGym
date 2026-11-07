"""Identify actual joint tracking errors at a stopped preparation attempt.

Reads the recorded encoder packet and authored target, without changing a
controller, physical trajectory or acceptance threshold. Full contact replay
and a fresh corrected execution remain separate requirements.
"""
import argparse
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def diagnose(folder, output):
    folder, output = Path(folder), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    result = json.loads((folder / 'result.json').read_text())
    contract = json.loads((folder / 'contract.json').read_text())
    targets = json.loads((folder / 'policy_source/preparation_targets.json').read_text())
    assert sha(folder / 'contract.json') == result['contract_sha256']
    assert sha(folder / 'sensors.npz') == result['sensors_sha256']
    assert sha(folder / 'world.xml') == contract['model_sha256']
    m = mujoco.MjModel.from_xml_path(str(folder / 'world.xml'))
    from observations import robot_joints
    names = [m.joint(j).name for j in robot_joints(m)]
    with np.load(folder / 'sensors.npz') as sensor:
        positions, velocities = sensor['joint_position'][-1], sensor['joint_velocity'][-1]
        time_s = float(sensor['time_s'][-1])
    assert abs(time_s-result['simulated_seconds']) < .0011
    rows = []
    for name, target in targets.items():
        i = names.index(name)
        actual = float(positions[i])
        assert abs(actual-result['final_qpos'][m.joint(name).qposadr[0]]) < 1e-8
        rows.append(dict(joint=name, target_rad=target, actual_rad=actual,
            error_rad=actual-target, speed_rad_s=float(velocities[i])))
    rows.sort(key=lambda row: -abs(row['error_rad']))
    bound = contract['station_handoff']['maximum_preparation_error_rad']
    report = dict(scope=__doc__, result_sha256=sha(folder / 'result.json'),
        sensor_sha256=result['sensors_sha256'], contract_sha256=result['contract_sha256'],
        script_sha256=sha(__file__), time_s=time_s, failure=result['failure'],
        target_error_bound_rad=bound, joint_rows=rows,
        joints_outside_posture_bound=[row['joint'] for row in rows if abs(row['error_rad']) >= bound],
        maximum_selected_joint_speed_rad_s=max(abs(row['speed_rad_s']) for row in rows),
        physical_acceptance_changed=False, qualified_handoff=False, qualified_paper_branch=False)
    (output / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(failure=result['failure'], largest_joint_error=rows[0],
        joints_outside_posture_bound=report['joints_outside_posture_bound'])), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder')
    p.add_argument('output')
    a = p.parse_args()
    diagnose(a.folder, a.output)
