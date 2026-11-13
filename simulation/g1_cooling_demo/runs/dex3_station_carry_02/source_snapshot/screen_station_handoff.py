"""Inspect proposed free-space preparation after the recorded station approach.

This offline screen uses the evaluated plant pose, never an actor input. It
checks interpolated robot geometry and renders the actual native camera view.
It does not establish stability, swept-path safety or successful manipulation.
"""
import argparse
import json
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image

from run_dex3_walking import sha
from tool_cameras import ToolCameras
from walking_actor import SDK_JOINTS


def screen(walking, source, output):
    walking, source, output = map(Path, (walking, source, output))
    output.mkdir(parents=True, exist_ok=False)
    contract = json.loads((walking / 'contract.json').read_text())
    result = json.loads((walking / 'result.json').read_text())
    prior = json.loads((source / 'policy_source/tool_prior.json').read_text())
    assert sha(walking / 'world.xml') == contract['model_sha256']
    m = mujoco.MjModel.from_xml_path(str(walking / 'world.xml'))
    d = mujoco.MjData(m)
    predictor = mujoco.MjModel.from_xml_path(str(source / 'controller_model/world.xml'))
    target_q = np.asarray(prior['initial_robot_qpos'])
    targets = {predictor.joint(j).name: float(target_q[predictor.jnt_qposadr[j]])
               for j in predictor.actuator_trnid[:, 0]}
    root = m.body('pelvis').id
    robot = {root}
    for b in range(m.nbody):
        if int(m.body_parentid[b]) in robot:
            robot.add(b)
    imported = json.loads((walking / 'laboratory_import.json').read_text())
    floors = {p['geom'] for p in imported['parts'] if p['source_part'] in
              {'indoor_floor', 'annex_floor', 'outdoor_floor', 'outdoor_access_path'}}
    initial = np.asarray(result['final_qpos'])
    cameras = ToolCameras(m)
    rows = []
    try:
        for mode in ['hands_only', 'upper_only', 'waist_and_upper']:
            names = [n for n in targets if '_hand_' in n]
            if mode != 'hands_only':
                names += SDK_JOINTS[15:]
            if mode == 'waist_and_upper':
                names += SDK_JOINTS[12:15]
            qa = np.array([m.joint(n).qposadr[0] for n in names])
            goal = np.array([targets[n] for n in names])
            for fraction in np.linspace(0., 1., 41):
                d.qpos[:] = initial
                d.qpos[qa] = initial[qa] + fraction * (goal - initial[qa])
                d.qvel[:] = 0.
                mujoco.mj_forward(m, d)
                bad = []
                for c in d.contact:
                    if not {int(m.geom_bodyid[g]) for g in c.geom} & robot:
                        continue
                    labels = [m.geom(int(g)).name for g in c.geom]
                    sole = any('ankle_roll_link_collision' in n for n in labels) and bool(set(labels) & floors)
                    bound = contract['physical_acceptance'][
                        'maximum_sole_penetration_m' if sole else 'maximum_other_penetration_m']
                    if c.dist < -bound:
                        bad.append(dict(geoms=labels, penetration_m=-float(c.dist), bound_m=bound))
                rows.append(dict(mode=mode, fraction=float(fraction), clear=not bad, contacts=bad))
                if fraction in (0., 1.):
                    frames = cameras.read(d)
                    stem = mode + ('_initial' if fraction == 0. else '_prepared')
                    np.savez_compressed(output / (stem + '.npz'), **frames)
                    Image.fromarray(frames['head_rgb']).save(output / (stem + '.png'))
    finally:
        cameras.close()
    report = dict(scope=__doc__, model_sha256=sha(walking / 'world.xml'),
        source_result_sha256=sha(walking / 'result.json'),
        source_tool_prior_sha256=sha(source / 'policy_source/tool_prior.json'),
        script_sha256=sha(__file__), samples=rows,
        modes={mode: all(r['clear'] for r in rows if r['mode'] == mode)
               for mode in ['hands_only', 'upper_only', 'waist_and_upper']},
        qualified_handoff=False, qualified_paper_branch=False)
    (output / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(modes=report['modes'], first_failures=[r for r in rows if not r['clear']][:4])))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('walking')
    p.add_argument('source')
    p.add_argument('output')
    a = p.parse_args()
    screen(a.walking, a.source, a.output)
