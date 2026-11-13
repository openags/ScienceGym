"""Screen loaded support-transfer geometry from a failed actor's sensor estimate.

The plant and its recorded poses are not loaded. Joint encoders, IMU and the
previously reproduced actor estimate initialize this own-robot calculation.
Candidate poses are authored planning diagnostics, never executed states.
"""
import argparse
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

from observations import robot_joints
from run_dex3_ftir_press import sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('run', type=Path)
    p.add_argument('diagnosis', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    diagnostic = json.loads(a.diagnosis.read_text())
    assert diagnostic['reproduced_recorded_failure']
    assert sha(a.run/'sensors.npz') == diagnostic['source_sensors_sha256']
    assert sha(a.run/'result.json') == diagnostic['source_result_sha256']
    sample = diagnostic['final_balance_sample']
    model_path = a.run/'actor_bundle/model/world.xml'
    m = mujoco.MjModel.from_xml_path(str(model_path))
    assert m.nu == 43 and m.neq == 0
    d = mujoco.MjData(m)
    joints = robot_joints(m)
    with np.load(a.run/'sensors.npz') as sensors:
        assert abs(float(sensors['time_s'][-1])-sample['time_s']) < 1e-8
        d.qpos[m.jnt_qposadr[joints]] = sensors['joint_position'][-1]
        d.qpos[3:7] = sensors['imu_quaternion'][-1]
    d.qpos[:3] = sample['estimated_root_m']
    mujoco.mj_forward(m, d)
    pelvis = m.body('pelvis').id
    assert np.max(abs(d.subtree_com[pelvis]-sample['com_m'])) < 1e-8
    initial = d.qpos.copy()
    initial_rotation = Rotation.from_quat(initial[3:7], scalar_first=True)
    moving = [j for j in m.actuator_trnid[:, 0] if '_hand_' not in m.joint(j).name]
    qa = m.jnt_qposadr[moving]
    feet = [m.site(side+'_sole').id for side in ['left', 'right']]
    foot_positions = d.site_xpos[feet].copy()
    foot_rotations = d.site_xmat[feet].reshape(2, 3, 3).copy()
    wrist = m.site('right_wrist_reference').id
    wrist_relative = d.site_xpos[wrist]-d.qpos[:3]
    wrist_rotation = d.site_xmat[wrist].reshape(3, 3).copy()
    start = np.r_[initial[:3], np.zeros(3), initial[qa]]
    lower = np.r_[initial[:3]-.3, [-.15]*3, m.jnt_range[moving, 0]+.01]
    upper = np.r_[initial[:3]+.3, [.15]*3, m.jnt_range[moving, 1]-.01]
    if np.any(start < lower) or np.any(start > upper):
        raise ValueError('Recorded terminal estimate is outside the original planning margin')

    def pose(x):
        d.qpos[:] = initial
        d.qpos[:3] = x[:3]
        d.qpos[3:7] = (initial_rotation*Rotation.from_rotvec(x[3:6])).as_quat(scalar_first=True)
        d.qpos[qa] = x[6:]
        mujoco.mj_kinematics(m, d)
        mujoco.mj_comPos(m, d)

    def errors(x, target):
        pose(x)
        foot_rotation = np.concatenate([Rotation.from_matrix(goal@actual.T).as_rotvec()
            for goal, actual in zip(foot_rotations, d.site_xmat[feet].reshape(2, 3, 3))])
        return dict(feet_position=(d.site_xpos[feet]-foot_positions).ravel(),
                    feet_rotation=foot_rotation,
                    wrist_position=d.site_xpos[wrist]-d.qpos[:3]-wrist_relative,
                    wrist_rotation=Rotation.from_matrix(wrist_rotation@d.site_xmat[wrist].reshape(3, 3).T).as_rotvec(),
                    com=d.subtree_com[pelvis]-target)

    rows, states = [], []
    for side in [1, 0]:
        direction = foot_positions[1-side, :2]-foot_positions[side, :2]
        direction /= np.linalg.norm(direction)
        for lowering in [0., .02, .04]:
            target = np.r_[foot_positions[side, :2]+.01*direction, sample['com_target_m'][2]-lowering]
            for rotation_mode in ['fixed', 'adjustable']:
                def residual(x):
                    e = errors(x, target)
                    return np.r_[1000*e['feet_position'], 200*e['feet_rotation'],
                        1000*e['wrist_position'], 200*e['wrist_rotation'], 1000*e['com'],
                        (200 if rotation_mode == 'fixed' else .1)*x[3:6], .01*(x-start)]
                result = least_squares(residual, start, bounds=(lower, upper), max_nfev=180,
                                       ftol=1e-10, xtol=1e-10, gtol=1e-9)
                e = errors(result.x, target)
                tilt = float(np.arccos(np.clip(d.body('pelvis').xmat.reshape(3, 3)[2, 2], -1, 1)))
                bounds = dict(feet_position=.001, feet_rotation=.005, wrist_position=.002,
                              wrist_rotation=.025, com=.004)
                norms = {k:float(np.linalg.norm(v)) for k, v in e.items()}
                clear = all(norms[k] <= bound for k, bound in bounds.items()) and tilt < .2
                if rotation_mode == 'fixed':
                    clear = clear and np.linalg.norm(result.x[3:6]) < .005
                states.append(d.qpos.copy())
                row = dict(support_side=['left', 'right'][side], additional_com_lowering_m=lowering,
                    pelvis_rotation_mode=rotation_mode, geometric_constraints_satisfied=bool(clear),
                    residual_norms=norms, pelvis_delta_rotation_rad=result.x[3:6].tolist(),
                    pelvis_tilt_rad=tilt, target_com_m=target.tolist(), evaluations=result.nfev,
                    index=len(states)-1)
                rows.append(row)
                print(json.dumps(row), flush=True)
    np.savez_compressed(a.output/'candidate_poses.npz', qpos=np.asarray(states), initial=initial)
    report = dict(scope=__doc__, candidates=rows, source_model_sha256=sha(model_path),
        source_diagnosis_sha256=sha(a.diagnosis), source_sensors_sha256=diagnostic['source_sensors_sha256'],
        source_sha256=sha(__file__), candidate_poses_sha256=sha(a.output/'candidate_poses.npz'),
        source_joint_margin_rad=.01, physical_execution=False, collision_clearance_verified=False,
        qualified_carry=False)
    shutil.copyfile(__file__, a.output/Path(__file__).name)
    (a.output/'review.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
