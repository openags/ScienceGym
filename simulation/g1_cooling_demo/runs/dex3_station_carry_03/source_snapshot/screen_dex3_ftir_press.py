"""Screen Dex3 source-fingertip reach to a native RGB-D observed FTIR key.

This offline authoring screen uses plant geometry only for collision review.
It performs no dynamics and grants no executed preparation or button press.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

from carry_tool_actor import declared_sole_support, public_support_prior
from dex3_ftir_hand import Dex3PointingHand, POINTING
from ftir_hand import ArmIK
from ftir_vision import KeyRowObservation
from joint_rrt import plan as plan_rrt


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model_run', type=Path)
    parser.add_argument('observed_frame', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--lean-rad', nargs='+', type=float, default=[0., .2, .4, .6, .8])
    parser.add_argument('--roll-rad', nargs='+', type=float, default=[0., np.pi, -.5, .5])
    parser.add_argument('--label', choices=['SAMPLE', 'BACKGROUND', 'OK / ENTER', 'STOP'],
                        default='BACKGROUND')
    parser.add_argument('--ik-passes', type=int, default=4)
    parser.add_argument('--rrt', action='store_true')
    args = parser.parse_args()
    run, frame, out = args.model_run.resolve(), args.observed_frame.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    model = mujoco.MjModel.from_xml_path(str(run/'world.xml'))
    data = mujoco.MjData(model)
    with np.load(frame) as observation:
        data.qpos[:] = observation['authored_qpos']
        mujoco.mj_forward(model, data)
        detection = KeyRowObservation(model, data).observe(observation['rgb'], observation['depth'])
    if not detection or not detection['accepted']:
        raise RuntimeError('No accepted native key-row observation')
    hand = Dex3PointingHand(model)
    for name, value in POINTING.items():
        data.joint(name).qpos[0] = value
    initial = data.qpos.copy()
    robot = {model.body('pelvis').id}
    for b in range(model.nbody):
        if int(model.body_parentid[b]) in robot:
            robot.add(b)
    contract = json.loads((run/'contract.json').read_text())
    support = public_support_prior(model, json.loads((run/'laboratory_import.json').read_text()),
        contract['physical_acceptance']['maximum_sole_penetration_m'])
    ik = ArmIK(model)
    normal = np.asarray(detection['outward_normal'])
    center = np.asarray(detection['buttons'][args.label])

    def collisions(q):
        data.qpos[:] = q
        mujoco.mj_kinematics(model, data)
        mujoco.mj_comPos(model, data)
        mujoco.mj_collision(model, data)
        return [dict(parts=[model.geom(int(g)).name for g in c.geom], distance_m=float(c.dist))
            for c in data.contact if c.dist < -2e-5
            and any(int(model.geom_bodyid[int(g)]) in robot for g in c.geom)
            and not declared_sole_support(model, c, support)]

    initial_contacts = collisions(initial)
    rows = []
    selected = None
    for lean in args.lean_rad:
        for roll in args.roll_rad:
            data.qpos[:] = initial
            mujoco.mj_kinematics(model, data)
            wrist, rotation, material = hand.at_surface(center, normal, detection['row_direction'], lean, roll)
            target = wrist+normal*.03
            q = initial[ik.qa].copy()
            for iteration in range(args.ik_passes):
                q, pe, re = ik.solve(data, target, rotation, q)
                if pe <= .0002 and re <= .004:
                    break
            candidate = initial.copy()
            candidate[ik.qa] = q
            contacts = collisions(candidate)
            actual = data.site('right_wrist_reference')
            pe = float(np.linalg.norm(target-actual.xpos))
            re = float(np.linalg.norm(Rotation.from_matrix(
                rotation @ actual.xmat.reshape(3, 3).T).as_rotvec()))
            row = dict(lean_rad=lean, roll_rad=roll, position_error_m=pe,
                rotation_error_rad=re, endpoint_contacts=contacts,
                ik_passes=iteration+1,
                arm_joint_position_rad=q.tolist(),
                arm_joint_margin_rad=np.minimum(q-ik.low, ik.high-q).tolist())
            rows.append(row)
            if pe > .001 or re > .025 or row['endpoint_contacts']:
                continue
            bad = None
            for u in np.linspace(0., 1., 101):
                state = initial+u*(candidate-initial)
                contacts = collisions(state)
                if contacts:
                    bad = dict(fraction=float(u), contacts=contacts)
                    break
            row['interpolated_path_first_contact'] = bad
            path = [initial[ik.qa].copy(), q.copy()] if bad is None else None
            if bad is not None and args.rrt and not initial_contacts:
                def valid(arm):
                    state = initial.copy()
                    state[ik.qa] = arm
                    return not collisions(state)
                path, metrics = plan_rrt(initial[ik.qa], q, ik.low, ik.high, valid,
                                         seed=7363, iterations=3000)
                row['rrt'] = metrics
                if path is not None:
                    bad = None
            if bad is None and not initial_contacts:
                selected = dict(lean_rad=lean, roll_rad=roll, wrist_target_m=target.tolist(),
                    wrist_rotation=rotation.tolist(), wrist_local_material_point_m=material.tolist(),
                    observed_surface_m=center.tolist(), observed_normal=normal.tolist())
                np.savez_compressed(out/'prepared_states.npz', authored_initial_qpos=initial,
                    proposed_approach_qpos=candidate, proposed_arm_path_rad=np.asarray(path))
                break
        if selected is not None:
            break
    pins = {}
    for name in ['screen_dex3_ftir_press.py', 'dex3_ftir_hand.py', 'ftir_hand.py', 'ftir_vision.py',
                 'robot_source_meshes.py', 'carry_tool_actor.py', 'joint_rrt.py']:
        src = Path(__file__).with_name(name)
        shutil.copyfile(src, out/name)
        pins[name] = sha(src)
    report = dict(scope=__doc__, passed=selected is not None, label=args.label,
        initial_contacts=initial_contacts,
        observation=detection, pointing_pose=POINTING, candidates=rows, selected=selected,
        source_model_sha256=sha(run/'world.xml'), source_frame_sha256=sha(frame), source_sha256=pins,
        collision_samples_per_path=101, continuous_swept_volume_certified=False,
        physical_execution=False, qualified_ftir_press=False, qualified_paper_branch=False)
    (out/'review.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'], initial_contacts=initial_contacts,
        selected=selected, candidate_count=len(rows))), flush=True)
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
