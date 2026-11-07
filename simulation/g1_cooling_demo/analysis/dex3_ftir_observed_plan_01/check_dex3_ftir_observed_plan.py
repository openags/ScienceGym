"""Check a sensor-derived FTIR approach using the isolated robot/map model.

The author projects only the robot's declared initial pose into the planner.
Instrument geometry and object truth are excluded from the planning model.
This is a planning diagnostic, not a dynamic trial or isolation attestation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from dex3_ftir_planning import ObservedKeyApproach
from ftir_vision import KeyRowObservation
from observations import robot_joints


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source_run', type=Path)
    p.add_argument('frame', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    plant = mujoco.MjModel.from_xml_path(str(a.source_run/'world.xml'))
    model_path = a.source_run/'controller_model/world.xml'
    m = mujoco.MjModel.from_xml_path(str(model_path))
    d = mujoco.MjData(m)
    assert sum(m.jnt_type == mujoco.mjtJoint.mjJNT_FREE) == 1
    assert not any((m.body(i).name or '').startswith('lab_') and m.body(i).name != 'lab_architecture'
                   for i in range(m.nbody))
    with np.load(a.frame) as f:
        q, rgb, depth = f['authored_qpos'], f['rgb'], f['depth']
    d.qpos[:7] = q[:7]
    for j in robot_joints(m):
        name = m.joint(j).name
        d.qpos[m.jnt_qposadr[j]] = q[plant.joint(name).qposadr[0]]
    mujoco.mj_forward(m, d)
    detection = KeyRowObservation(m, d).observe(rgb, depth)
    if not detection or not detection['accepted']:
        raise ValueError('No native observation of all four keys')
    planner = ObservedKeyApproach(m, d, depth)
    plan = planner.build(detection)
    setup = dict(root_qpos=d.qpos[:7].tolist(),
        joints={m.joint(j).name:float(d.qpos[m.jnt_qposadr[j]]) for j in robot_joints(m)},
        scope='Authored component starting pose, no navigation or preparation credit')
    (a.output/'robot_setup.json').write_text(json.dumps(setup, indent=2)+'\n')
    sources = {}
    for name in [Path(__file__).name, 'dex3_ftir_planning.py', 'dex3_ftir_hand.py',
                 'ftir_hand.py', 'ftir_vision.py', 'robot_source_meshes.py',
                 'source_proximity.py', 'joint_rrt.py', 'tool_approach_planning.py']:
        src = Path(__file__).with_name(name)
        shutil.copyfile(src, a.output/name)
        sources[name] = sha(src)
    report = dict(scope=__doc__, passed=plan['planned'], plan=plan, observation=detection,
        controller_model_sha256=sha(model_path), observed_frame_sha256=sha(a.frame),
        source_sha256=sources, physical_execution=False, qualified_ftir_press=False)
    (a.output/'review.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(passed=plan['planned'], attempts=plan.get('attempts'),
        reason=plan.get('reason'), detail=plan.get('detail'),
        path_vertices=len(plan.get('arm_path_rad', [])))), flush=True)
    if not plan['planned']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
