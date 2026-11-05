"""Evaluate one initial native camera observation, keeping truth outside detection.

Only frame zero is accepted: later frames require their actual robot sensor
state. This is a perception diagnostic, not runtime handling qualification.
"""
import argparse
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from build_tool_station import sha
from optical_coupon_observation import detect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('output', type=Path)
    a = parser.parse_args()
    run, out = a.run.resolve(), a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    for name in [Path(__file__).name, 'optical_coupon_observation.py']:
        shutil.copyfile(Path(__file__).with_name(name), out/name)
    prior = json.loads((run/'policy_source/tool_prior.json').read_text())
    contract = json.loads((run/'contract.json').read_text())
    m = mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'))
    d = mujoco.MjData(m)
    d.qpos[:] = prior['initial_robot_qpos']
    # mj_forward includes mj_camlight; kinematics alone leaves camera frames
    # unset and would invalidate the image-to-world reconstruction.
    mujoco.mj_forward(m, d)
    def camera(name):
        i = m.camera(name).id
        T = np.eye(4)
        T[:3, :3], T[:3, 3] = d.cam_xmat[i].reshape(3, 3), d.cam_xpos[i]
        return T, float(m.cam_fovy[i])
    D, df = camera('head_depth')
    C, cf = camera('head_rgb')
    g = m.geom('lab_part_1514').id
    k = m.geom_dataid[g]
    vertices = m.mesh_vert[m.mesh_vertadr[k]:m.mesh_vertadr[k]+m.mesh_vertnum[k]]
    vertices = vertices@d.geom_xmat[g].reshape(3, 3).T+d.geom_xpos[g]
    lo, hi = vertices.min(axis=0), vertices.max(axis=0)
    lo[2] = hi[2]+.002
    hi[2] += .18
    frame = run/'camera_frames/00000.npz'
    with np.load(frame) as z:
        observation = detect(z['head_rgb'], z['head_depth'], D, C, df, cf, [lo, hi])
    # Separate evaluator: native object truth is never passed to detect().
    plant = mujoco.MjModel.from_xml_path(str(run/'world.xml'))
    truth = mujoco.MjData(plant)
    truth.qpos[:], truth.qvel[:] = contract['initial_qpos'], contract['initial_qvel']
    mujoco.mj_forward(plant, truth)
    gid = plant.geom('optical_copper_witness').id
    mid = plant.geom_dataid[gid]
    vertices = plant.mesh_vert[plant.mesh_vertadr[mid]:plant.mesh_vertadr[mid]+plant.mesh_vertnum[mid]]
    vertices = vertices@truth.geom_xmat[gid].reshape(3, 3).T+truth.geom_xpos[gid]
    source_center = (vertices.min(axis=0)+vertices.max(axis=0))/2
    normal = truth.body('optical_witness_white').xmat.reshape(3, 3)[:, 2]
    if np.dot(normal, D[:3, 3]-source_center)<0:
        normal = -normal
    error = angle = None
    if observation['candidate_found']:
        candidate = observation['candidate']
        error = float(np.linalg.norm(np.asarray(candidate['center_m'])-source_center))
        angle = float(np.arccos(np.clip(np.dot(candidate['normal_toward_camera'], normal), -1, 1)))
    checks = dict(unique_observed_candidate=observation['candidate_found'],
        center_within_one_millimetre=error is not None and error<=.001,
        normal_within_five_degrees=angle is not None and angle<=np.deg2rad(5))
    checks = {key:bool(value) for key,value in checks.items()}
    report = dict(scope=__doc__, observation=observation, checks=checks,
        passed_initial_observation=all(checks.values()), center_error_m=error, normal_error_rad=angle,
        evaluator_source_center_m=source_center.tolist(), evaluator_source_normal=normal.tolist(),
        normal_semantics='Copper plane normal toward the camera; coating side is not inferred from a rim detection',
        frame_sha256=sha(frame), model_sha256=sha(run/'world.xml'),
        contract_sha256=sha(run/'contract.json'), predictor_sha256=sha(run/'controller_model/world.xml'),
        prior_sha256=sha(run/'policy_source/tool_prior.json'),
        source_sha256={p.name:sha(p) for p in out.glob('*.py')},
        actor_receives_truth=False, runtime_manipulation_qualified=False)
    (out/'review.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
