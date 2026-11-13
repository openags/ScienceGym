"""Separate camera-frame drift from coupon fitting error in a recorded run.

The truth-camera substitution is an offline attribution diagnostic only. It
cannot be used by the actor or counted as corrected perception performance.
"""
import argparse
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from build_tool_station import sha
from observations import StateEstimate


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path);p.add_argument('observation_review',type=Path)
    p.add_argument('output',type=Path);a=p.parse_args()
    run=a.run.resolve();report=json.loads(a.observation_review.read_text())
    result=json.loads((run/'result.json').read_text());contract=json.loads((run/'contract.json').read_text())
    assert sha(run/'result.json')==report['result_sha256']
    assert sha(run/'contract.json')==report['contract_sha256']==result['contract_sha256']
    assert sha(run/'trace.npz')==report['trace_sha256']==result['trace_sha256']
    assert sha(run/'sensors.npz')==result['sensors_sha256']
    assert sha(run/'world.xml')==contract['model_sha256']
    assert sha(Path(__file__).with_name('observations.py'))==contract['source_snapshot_sha256']['observations.py']
    assert sha(run/'policy_source/tool_prior.json')==contract['controller_prior_sha256']
    prior=json.loads((run/'policy_source/tool_prior.json').read_text());t=report['first_accepted_time_s']
    m=mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'));d=mujoco.MjData(m)
    d.qpos[:]=prior['initial_robot_qpos'];mujoco.mj_forward(m,d);est=StateEstimate(m,d)
    with np.load(run/'sensors.npz') as z:
        k=int(np.argmin(abs(z['time_s']-t)))
        assert abs(z['time_s'][k]-t)<1e-9
        obs={key:z[key][k] for key in ['time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro']}
    est.update(dict(obs,depth=None));cid=m.camera('head_depth').id
    C=d.cam_xpos[cid].copy();R=d.cam_xmat[cid].reshape(3,3).copy()
    plant=mujoco.MjModel.from_xml_path(str(run/'world.xml'));truth=mujoco.MjData(plant)
    with np.load(run/'trace.npz') as z:
        k=int(np.argmin(abs(z['time']-t)));assert abs(z['time'][k]-t)<1e-8
        truth.qpos[:]=z['qpos'][k]
    mujoco.mj_forward(plant,truth);cid=plant.camera('head_depth').id
    TC=truth.cam_xpos[cid];TR=truth.cam_xmat[cid].reshape(3,3)
    center=np.asarray(report['accepted_pose']['center_m']);diagnostic=(center-C)@R@TR.T+TC
    a.output.mkdir(parents=True,exist_ok=False)
    for name in [Path(__file__).name,'observations.py','build_tool_station.py']:
        shutil.copyfile(Path(__file__).with_name(name),a.output/name)
    output=dict(scope=__doc__,source_review_sha256=sha(a.observation_review),
        source_result_sha256=sha(run/'result.json'),source_trace_sha256=result['trace_sha256'],
        source_sensor_sha256=result['sensors_sha256'],time_s=t,
        estimated_camera_position_m=C.tolist(),actual_camera_position_m=TC.tolist(),
        camera_translation_error_m=(C-TC).tolist(),
        original_accepted_center_error_m=report['accepted_center_error_m'],
        diagnostic_truth_camera_center_error_m=float(np.linalg.norm(diagnostic-np.asarray(report['source_center_at_acceptance_m']))),
        interpretation='A substantial part of the world-coordinate error comes from fixed-foot camera translation estimation; the aggregate four-frame pose is transformed at its acceptance time only',
        proposed_actor_input='Use observed static laboratory geometry to check camera/map alignment; no evaluator pose or measured error may enter the actor',
        actor_modified=False,perception_qualified=False,qualified_paper_branch=False,
        source_sha256={p.name:sha(p) for p in a.output.glob('*.py')})
    (a.output/'review.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output),flush=True)


if __name__=='__main__':main()
