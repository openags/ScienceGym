"""Screen declared tool placements for a rigid-heel three-finger grasp.

The original tool, hand and tray geometry are unchanged. Translations are
author-authored initial conditions, never an executed rearrangement. A static
clearance result requires a separate unactuated support run and a fresh fit.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
import time

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

from fit_dex3_tweezer import ROOT, SOURCE, TOOL, SourceHand, NAMES, digest, load_support


def run(fit_path, output, extent_mm=2, step_mm=2, yaw_extent=20, yaw_step=2):
    started = time.monotonic()
    fit_path, output = Path(fit_path).resolve(), Path(output).resolve()
    if not 0 < step_mm <= extent_mm <= 12:
        raise ValueError('Declare a bounded local placement search')
    fit = json.loads(fit_path.read_text())
    assert fit['contract_sha256'] == digest(fit_path.parent / 'contract.json')
    fit_contract = json.loads((fit_path.parent / 'contract.json').read_text())
    assert fit_contract['middle_finger_rigid_heel_support']
    for name, expected in fit_contract['source_hashes'].items():
        assert digest(ROOT / name) == expected, name
    trials_path = fit_path.parent / 'trials.json'
    trials = json.loads(trials_path.read_text())
    candidates = [(i, x) for i, x in enumerate(trials)
                  if all(v for k, v in x['checks'].items() if k != 'tray_clearance')]
    assert candidates
    candidates = sorted(candidates, key=lambda pair: (-pair[1]['tray_gap_m'], pair[1]['cost']))[:1]
    if not 0 < yaw_step <= yaw_extent <= 45: raise ValueError('Bounded yaw search required')
    support_path = TOOL / 'tray_support_12/review.json'
    support = json.loads(support_path.read_text())
    _, W, obstacles, support_receipt = load_support(support_path, ROOT)
    model = mujoco.MjModel.from_xml_path(str(support_path.parent / 'support.xml'))
    data = mujoco.MjData(model)
    initial = np.asarray(support['full_final_qpos'])
    tray = model.body('carrier_tray').id
    tool_root = model.body('tweezer').id
    tool_bodies = {tool_root}
    for b in range(model.nbody):
        if int(model.body_parentid[b]) in tool_bodies:
            tool_bodies.add(b)
    hand = SourceHand()
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, output / Path(__file__).name)
    files = [fit_path, trials_path, fit_path.parent / 'contract.json',
             support_path, support_path.parent / 'contract.json',
             support_path.parent / 'support.xml', output / Path(__file__).name,
             SOURCE / 'fit_cover_grasp.py', TOOL / 'support_geometry.py']
    contract = dict(scope=__doc__, source_hashes={str(p.relative_to(ROOT)): digest(p) for p in files},
                    support=support_receipt, extent_mm=extent_mm, step_mm=step_mm,
                    yaw_extent_deg=yaw_extent, yaw_step_deg=yaw_step,
                    rotation_center='Retained free-tool root at the rigid heel',
                    minimum_hand_tray_clearance_m=.001,
                    maximum_tool_tray_penetration_m=.00025,
                    maximum_other_penetration_m=.00002,
                    initial_placement_only=True, qualified_grasp=False)
    (output / 'contract.json').write_text(json.dumps(contract, indent=2) + '\n')
    rows = []
    values = np.arange(-extent_mm, extent_mm + step_mm / 2, step_mm) / 1000
    for yaw in np.arange(-yaw_extent, yaw_extent + yaw_step/2, yaw_step):
        for dx,dy in [(x,y) for x in values for y in values]:
            delta = np.array([dx, dy, 0.])
            data.qpos[:] = initial
            root = data.joint('tweezer_free').qpos[:3].copy()
            rotation = Rotation.from_euler('z', yaw, degrees=True)
            transform = np.eye(4); transform[:3,:3] = rotation.as_matrix()
            transform[:3,3] = root + delta - transform[:3,:3] @ root
            data.joint('tweezer_free').qpos[:3] += delta
            q = data.joint('tweezer_free').qpos[3:7].copy()
            result_q = (rotation * Rotation.from_quat(np.r_[q[1:],q[0]])).as_quat()
            data.joint('tweezer_free').qpos[3:7] = np.r_[result_q[3],result_q[:3]]
            mujoco.mj_forward(model, data)
            bad = []
            for c in data.contact:
                bodies = [int(model.geom_bodyid[g]) for g in c.geom]
                tool_tray = tray in bodies and any(b in tool_bodies for b in bodies)
                # The ordinary tray/bench support retains the original support bound.
                bench = any(model.geom(int(g)).name == 'bench' for g in c.geom)
                bound = .00025 if tool_tray or bench else .00002
                if c.dist < -bound:
                    bad.append(dict(parts=[model.geom(int(g)).name for g in c.geom],
                                    penetration_m=-float(c.dist), bound_m=bound))
            shifted = np.linalg.inv(W) @ transform @ W
            for index, candidate in candidates:
                q = [candidate['q'][n] for n in NAMES]
                S = shifted @ np.asarray(candidate['source_tool_from_wrist'])
                for name, T in hand.forward(q).items():
                    hand.manager.set_transform(name, S @ T)
                collides, pairs = hand.manager.in_collision_other(obstacles, return_names=True)
                gap = float(hand.manager.min_distance_other(obstacles))
                passed = not bad and not collides and gap > .001
                rows.append(dict(trial_index=index, world_translation_m=delta.tolist(),
                                 world_yaw_deg=float(yaw), world_transform=transform.tolist(),
                                 translation_norm_m=float(np.linalg.norm(delta)),
                                 hand_tray_gap_m=gap,
                                 hand_tray_intersections=[list(x) for x in sorted(pairs)],
                                 excessive_initial_contacts=bad, passed_static=passed))
        print('screened', len(rows), 'placements; accepted', sum(x['passed_static'] for x in rows), flush=True)
    good = sorted((x for x in rows if x['passed_static']),
                  key=lambda x: (x['translation_norm_m'] + .001*abs(x['world_yaw_deg']), -x['hand_tray_gap_m'], x['trial_index']))
    report = dict(scope=__doc__, contract_sha256=digest(output / 'contract.json'),
                  tested=len(rows), accepted_count=len(good), selected=good[0] if good else None,
                  candidates=good, rows=rows, seconds=time.monotonic()-started,
                  support_dynamics_checked=False, full_body_checked=False,
                  qualified_grasp=False, qualified_paper_branch=False)
    (output / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['tested','accepted_count','selected','seconds']}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('fit'); p.add_argument('output')
    p.add_argument('--extent-mm', type=float, default=2)
    p.add_argument('--step-mm', type=float, default=2)
    p.add_argument('--yaw-extent',type=float,default=20)
    p.add_argument('--yaw-step',type=float,default=2)
    a = p.parse_args(); run(a.fit, a.output, a.extent_mm, a.step_mm, a.yaw_extent, a.yaw_step)
