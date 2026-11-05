"""Screen level-wrist withdrawal paths using a saved sensor-derived handoff.

This diagnostic changes no controller or physical model. It tests source-limit
IK only; every candidate still needs source geometry and loaded execution
checks. Saved handoff positions are reconstructed sensor estimates, not plant
object poses. The 0.10 m backward withdrawal is preserved in every candidate.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

from ftir_hand import ArmIK


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recording')
    parser.add_argument('handoff')
    parser.add_argument('output')
    parser.add_argument('--rotation-grid', action='store_true',
                        help='Screen combined wrist rotations at the original height and retreat')
    args = parser.parse_args()
    run, handoff, out = map(Path, [args.recording, args.handoff, args.output])
    out.mkdir(parents=True, exist_ok=False)
    model_file = run / 'controller_model/world.xml'
    state_file = handoff / 'handoff.npz'
    model = mujoco.MjModel.from_xml_path(str(model_file.resolve()))
    data = mujoco.MjData(model)
    state = np.load(state_file)
    initial = state['robot_estimated_qpos'].copy()
    data.qpos[:] = initial
    mujoco.mj_kinematics(model, data)
    rotation = data.site('right_wrist_reference').xmat.reshape(3, 3).copy()
    start = state['wrist_start'].copy()
    body_rotation = data.body('pelvis').xmat.reshape(3, 3)
    forward = body_rotation[:, 0].copy()
    forward[2] = 0.
    forward /= np.linalg.norm(forward)
    lateral = np.cross([0., 0., 1.], forward)
    ik = ArmIK(model)
    rows = []
    if args.rotation_grid:
        vectors = sorted(itertools.product([-.4, -.2, 0., .2, .4], repeat=3),
                         key=lambda v: (np.linalg.norm(v), v))
        configurations = [(.05, 0., np.asarray(v)) for v in vectors]
    else:
        configurations = [(h, y, np.zeros(3)) for h in [.025, .05, .075, .10, .125, .15]
                          for y in [0., -.025, .025, -.05, .05, -.075, .075, -.10, .10]]
    for height, sideways, rotation_vector in configurations:
            raised = start + [0., 0., height]
            end = raised - .10 * forward + sideways * lateral
            q = initial.copy()
            paths = {}
            pe_max = re_max = 0.
            margin_min = float('inf')
            failure = None
            for label, a, b in [('raise', start, raised), ('retract', raised, end)]:
                path = []
                for u in np.linspace(0., 1., 51):
                    data.qpos[:] = q
                    target_rotation = rotation @ Rotation.from_rotvec(
                        rotation_vector * (u if label == 'retract' else 0.)).as_matrix()
                    goal, pe, re = ik.solve(data, a + u * (b - a), target_rotation, q[ik.qa])
                    q[ik.qa] = goal
                    margin = float(np.min(np.minimum(goal - ik.low, ik.high - goal)))
                    pe_max, re_max = max(pe_max, pe), max(re_max, re)
                    margin_min = min(margin_min, margin)
                    path.append(goal.tolist())
                    if pe > .001 or re > .025 or margin < .08:
                        failure = dict(segment=label, fraction=float(u),
                                       position_error_m=pe, rotation_error_rad=re,
                                       joint_margin_rad=margin)
                        break
                paths[label] = path
                if failure:
                    break
            row = dict(additional_height_m=height, lateral_offset_m=sideways,
                       rotation_vector_rad=rotation_vector.tolist(),
                       backward_withdrawal_m=.10, maximum_position_error_m=pe_max,
                       maximum_rotation_error_rad=re_max,
                       minimum_joint_margin_rad=margin_min, failure=failure,
                       ik_passed=failure is None)
            if failure is None:
                row.update(joint_paths=paths, end_position_m=end.tolist())
            rows.append(row)
            print(json.dumps({k: v for k, v in row.items() if k != 'joint_paths'}), flush=True)
    result = dict(scope=__doc__, source_model_sha256=sha(model_file),
                  source_handoff_sha256=sha(state_file), script_sha256=sha(__file__),
                  ik_source_sha256=sha(Path(__file__).with_name('ftir_hand.py')),
                  collision_checked=False, physical_execution=False,
                  qualified_carry=False, candidates=rows)
    (out / 'review.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
