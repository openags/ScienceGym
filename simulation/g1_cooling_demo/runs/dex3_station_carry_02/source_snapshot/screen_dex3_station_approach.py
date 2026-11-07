"""Static full-room clearance screen for walking toward the existing tool bench.

These authored placements are geometric diagnostics, never executed travel.
The walking posture and two lateral deviations are checked; moving-leg swept
clearance and controller handoff require fresh native execution.
"""
import argparse
import json
from pathlib import Path

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

from observations import robot_joints
from run_dex3_walking import sha


def screen(walking, station, output):
    walking, station, output = map(Path, (walking, station, output))
    output.mkdir(parents=True, exist_ok=False)
    w = json.loads((walking / 'contract.json').read_text())
    s = json.loads((station / 'contract.json').read_text())
    model = mujoco.MjModel.from_xml_path(str(walking / 'world.xml'))
    data = mujoco.MjData(model)
    root = model.body('pelvis').id
    robot = set()
    for body in range(model.nbody):
        ancestor = body
        while ancestor and ancestor != root:
            ancestor = int(model.body_parentid[ancestor])
        if ancestor == root:
            robot.add(body)
    imported = json.loads((walking / 'laboratory_import.json').read_text())
    floors = {part['geom'] for part in imported['parts'] if part['source_part'] in
              {'indoor_floor', 'annex_floor', 'outdoor_floor', 'outdoor_access_path'}}
    goal = np.asarray(s['initial_qpos'])[:2]
    quaternion = np.asarray(s['initial_qpos'])[3:7]
    orientation = Rotation.from_quat(quaternion[[1, 2, 3, 0]])
    forward = orientation.apply([1., 0., 0.])[:2]
    lateral = orientation.apply([0., 1., 0.])[:2]
    start = goal - 1.4 * forward
    rows = []
    for fraction in np.linspace(0., 1., 29):
        for sideways in [-.08, 0., .08]:
            data.qpos[:] = w['initial_qpos']
            data.qpos[:2] = start + fraction * (goal-start) + sideways * lateral
            data.qpos[3:7] = quaternion
            mujoco.mj_forward(model, data)
            data.qpos[2] -= min(data.site(side + '_sole').xpos[2] for side in ['left', 'right'])
            mujoco.mj_forward(model, data)
            bad = []
            for contact in data.contact:
                if not {int(model.geom_bodyid[g]) for g in contact.geom} & robot:
                    continue
                names = [model.geom(int(g)).name for g in contact.geom]
                foot_floor = any('ankle_roll_link_collision' in name for name in names) and bool(set(names) & floors)
                bound = w['physical_acceptance']['maximum_sole_penetration_m' if foot_floor else 'maximum_other_penetration_m']
                if contact.dist < -bound:
                    bad.append(dict(geoms=names, penetration_m=-float(contact.dist), bound_m=bound))
            rows.append(dict(path_fraction=float(fraction), lateral_offset_m=sideways,
                base_xy_m=data.qpos[:2].tolist(), clear=not bad, unexpected_contacts=bad))
    report = dict(scope=__doc__, walking_model_sha256=sha(walking / 'world.xml'),
        walking_contract_sha256=sha(walking / 'contract.json'),
        station_contract_sha256=sha(station / 'contract.json'), script_sha256=sha(__file__),
        authored_start_xy_m=start.tolist(), authored_goal_xy_m=goal.tolist(),
        authored_quaternion_wxyz=quaternion.tolist(), samples=rows,
        static_screen_passed=all(row['clear'] for row in rows),
        qualified_navigation=False, qualified_station_arrival=False, qualified_paper_branch=False)
    (output / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(static_screen_passed=report['static_screen_passed'],
        clear_samples=sum(row['clear'] for row in rows), total_samples=len(rows),
        first_failures=[row for row in rows if not row['clear']][:3])), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('walking')
    p.add_argument('station')
    p.add_argument('output')
    a = p.parse_args()
    screen(a.walking, a.station, a.output)
