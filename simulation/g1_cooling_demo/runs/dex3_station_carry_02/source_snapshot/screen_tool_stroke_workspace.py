"""Compare source-mesh grasp candidates' coordinated finger workspace.

This necessary kinematic screen advances the same own-hand material points
inward while retaining their tangent coordinate. It does not move a simulated
tool, infer grasp success, or qualify contact forces and dynamic retention.
"""
import argparse
import json
from pathlib import Path

import mujoco
import numpy as np
from scipy.optimize import least_squares

from run_dex3_walking import sha


def screen(fit_path, output):
    fit_path, output = Path(fit_path), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    fit = json.loads(fit_path.read_text())
    model_path = Path(__file__).parent / 'analysis/g1_dex3_comparison_01/hand_inspection.xml'
    m = mujoco.MjModel.from_xml_path(str(model_path))
    d = mujoco.MjData(m)
    pairs = [('thumb_1', 'thumb_2'), ('index_1', 'index_0'), ('middle_1', 'middle_0')]
    results = []
    for index, candidate in enumerate(fit['candidates']):
        S = np.asarray(candidate['source_tool_from_wrist'])
        qa = [np.array([m.joint('right_hand_'+name+'_joint').qposadr[0] for name in pair]) for pair in pairs]
        joints = [np.array([m.joint('right_hand_'+name+'_joint').id for name in pair]) for pair in pairs]
        for name, value in candidate['q'].items():
            d.joint(name).qpos[0] = value
        mujoco.mj_forward(m, d)
        initial = d.qpos.copy()
        points = [np.asarray(c['point_hand_local_m']) for c in candidate['contacts']]
        bodies = [m.body(c['part']).id for c in candidate['contacts']]
        signs = [1. if c['side'] == 'negative' else -1. for c in candidate['contacts']]

        def point(k):
            own = d.xpos[bodies[k]] + d.xmat[bodies[k]].reshape(3, 3) @ points[k]
            return S[:3, :3] @ own + S[:3, 3]

        start_points = [point(k) for k in range(3)]
        previous = [initial[a].copy() for a in qa]
        rows = []
        for distance in np.linspace(0., .003, 61):
            solved = []
            for k in range(3):
                lower = np.maximum(m.jnt_range[joints[k], 0]+.01, initial[qa[k]]-[.25, .15])
                upper = np.minimum(m.jnt_range[joints[k], 1]-.01, initial[qa[k]]+[.25, .15])
                target = start_points[k][1:].copy()
                target[0] += signs[k] * distance

                def residual(x):
                    d.qpos[qa[k]] = x
                    mujoco.mj_kinematics(m, d)
                    return (point(k)[1:] - target) / .001

                optimum = least_squares(residual, np.clip(previous[k], lower, upper),
                    bounds=(lower, upper), ftol=1e-10, xtol=1e-10, gtol=1e-10, max_nfev=100)
                previous[k] = optimum.x.copy()
                d.qpos[qa[k]] = optimum.x
                mujoco.mj_kinematics(m, d)
                solved.append(dict(finger=pairs[k][0].split('_')[0],
                    residual_m=float(np.linalg.norm(point(k)[1:] - target)),
                    joint_position_rad=optimum.x.tolist(),
                    joint_margin_rad=float(np.min(np.r_[optimum.x-lower, upper-optimum.x]))))
            rows.append(dict(inward_distance_m=float(distance), fingers=solved,
                reachable=all(row['residual_m'] <= .00002 for row in solved)))
        contiguous = []
        for row in rows:
            if not row['reachable']:
                break
            contiguous.append(row['inward_distance_m'])
        results.append(dict(candidate_index=index, original_joint_positions=candidate['q'],
            continuous_inward_workspace_m=max(contiguous, default=0.), samples=rows))
    report = dict(scope=__doc__, fit_sha256=sha(fit_path), hand_model_sha256=sha(model_path),
        script_sha256=sha(__file__), contact_tangent_error_bound_m=.00002,
        driver_excursion_rad=.25, companion_excursion_rad=.15, source_joint_margin_rad=.01,
        candidates=results, qualified_tool_actuation=False, qualified_paper_branch=False)
    (output / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps([dict(candidate_index=r['candidate_index'],
        continuous_inward_workspace_mm=1000*r['continuous_inward_workspace_m'])
        for r in sorted(results, key=lambda r: -r['continuous_inward_workspace_m'])]), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('fit')
    p.add_argument('output')
    a = p.parse_args()
    screen(a.fit, a.output)
