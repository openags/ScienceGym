"""Independently screen the observed FTIR arm route in full plant geometry.

This author-side check does not feed geometry or a route into the controller.
The final press is checked only to the observed surface; key motion and contact
response must be established by the subsequent fresh physical trial.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from carry_tool_actor import declared_sole_support, public_support_prior
from ftir_hand import ArmIK


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source_run', type=Path)
    p.add_argument('frame', type=Path)
    p.add_argument('plan_review', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    report = json.loads(a.plan_review.read_text())
    assert report['passed'] and report['observed_frame_sha256'] == sha(a.frame)
    plan = report['plan']
    m = mujoco.MjModel.from_xml_path(str(a.source_run/'world.xml'))
    d = mujoco.MjData(m)
    with np.load(a.frame) as f:
        initial = f['authored_qpos'].copy()
    d.qpos[:] = initial
    ik = ArmIK(m)
    robot = {m.body('pelvis').id}
    for b in range(m.nbody):
        if int(m.body_parentid[b]) in robot:
            robot.add(b)
    support = public_support_prior(m, json.loads((a.source_run/'laboratory_import.json').read_text()), .001)
    violations, samples = [], 0

    def check(arm, phase, fraction):
        nonlocal samples
        samples += 1
        d.qpos[:] = initial
        d.qpos[ik.qa] = arm
        mujoco.mj_kinematics(m, d)
        mujoco.mj_comPos(m, d)
        mujoco.mj_collision(m, d)
        contacts = [dict(parts=[m.geom(int(g)).name for g in c.geom], distance_m=float(c.dist))
            for c in d.contact if c.dist < -.00002
            and any(int(m.geom_bodyid[int(g)]) in robot for g in c.geom)
            and not declared_sole_support(m, c, support)]
        if contacts:
            violations.append(dict(phase=phase, fraction=float(fraction), contacts=contacts))
        return not contacts

    path = np.asarray(plan['arm_path_rad'])
    for index, (start, end) in enumerate(zip(path[:-1], path[1:])):
        for u in np.linspace(0., 1., max(2, int(np.ceil(np.linalg.norm(end-start)/.008))+1)):
            if not check(start+u*(end-start), 'approach_'+str(index), u):
                break
        if violations:
            break
    if not violations:
        seed = path[-1]
        normal = np.asarray(plan['normal'])
        target = np.asarray(plan['contact_wrist_m'])
        rotation = np.asarray(plan['wrist_rotation'])
        for gap in np.linspace(.03, 0., 61):
            q, pe, re = ik.solve(d, target+gap*normal, rotation, seed)
            if pe > .001 or re > .025:
                violations.append(dict(phase='contact_approach', gap_m=float(gap),
                    position_error_m=pe, rotation_error_rad=re))
                break
            if not check(q, 'contact_approach', 1-gap/.03):
                break
            seed = q
    output = dict(scope=__doc__, passed=not violations, samples=samples, first_violations=violations,
        plan_review_sha256=sha(a.plan_review), frame_sha256=sha(a.frame),
        model_sha256=sha(a.source_run/'world.xml'), source_sha256=sha(__file__),
        physical_execution=False, qualified_ftir_press=False)
    shutil.copyfile(__file__, a.output/Path(__file__).name)
    (a.output/'review.json').write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps(output), flush=True)
    if not output['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
