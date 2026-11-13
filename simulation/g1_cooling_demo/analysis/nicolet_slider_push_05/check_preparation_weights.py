"""Diagnose the failed posture handoff and test an upper-body tracking task."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
ROOT = BASE.parents[1]
sys.path.insert(0, str(BASE))
from balance import Balance
from observations import robot_joints
from ftir_slider_posture import initialize_slider
from walking_actor import SDK_JOINTS


def main():
    output = HERE/'preparation_weights_regression.json'
    if output.exists():
        raise FileExistsError(output)
    run = BASE/'runs/ftir_approach_01'
    result = json.loads((run/'result.json').read_text())
    sensors = np.load(run/'sensor_observations.npz')
    model = mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'))
    data = mujoco.MjData(model)
    joints = robot_joints(model)
    data.qpos[model.jnt_qposadr[joints]] = sensors['joint_position'][-1]
    data.qvel[model.jnt_dofadr[joints]] = sensors['joint_velocity'][-1]
    data.qpos[3:7] = sensors['imu_quaternion'][-1]
    data.qvel[3:6] = sensors['imu_gyro'][-1]
    data.qpos[:3] = result['actor_last_output']['estimated_root_position_m']
    mujoco.mj_forward(model, data)
    qa = model.jnt_qposadr[model.actuator_trnid[:,0]]
    target = initialize_slider(model).qpos[qa].copy()
    names = [model.joint(j).name for j in model.actuator_trnid[:,0]]
    errors = sorted([dict(joint=n, observed_rad=float(data.qpos[qa[i]]),
                          nominal_rad=float(target[i]), error_rad=float(data.qpos[qa[i]]-target[i]))
                     for i,n in enumerate(names)], key=lambda r:-abs(r['error_rad']))
    legacy_path = run/'source_snapshot/balance.py'
    spec = importlib.util.spec_from_file_location('legacy_preparation_balance', legacy_path)
    legacy_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy_module)
    old = legacy_module.Balance(model, data)
    default = Balance(model, data)
    weighted = Balance(model, data)
    yaw = Rotation.from_quat(data.qpos[[4,5,6,3]]).as_euler('xyz')[2]
    for balance in [old, default, weighted]:
        balance.pelvis_rotation = Rotation.from_euler('z', yaw).as_matrix()
        balance.rotate_foot_constraints = True
    a = old.torque(posture=target)
    b = default.torque(posture=target)
    weights = np.ones(model.nu)
    for i,n in enumerate(names):
        if n not in SDK_JOINTS[:12]:
            weights[i] = 4. if n.startswith('waist_') else 3.
    c = weighted.torque(posture=target, posture_weights=weights)
    effects = []
    for name in ['waist_yaw_joint', 'waist_pitch_joint']:
        i = names.index(name)
        j = model.joint(name)
        dof = int(j.dofadr[0])
        direction = np.sign(target[i]-data.qpos[qa[i]])
        effects.append(dict(joint=name, target_error_rad=float(target[i]-data.qpos[qa[i]]),
                            unweighted_acceleration_rad_s2=float(default.previous[dof]),
                            weighted_acceleration_rad_s2=float(weighted.previous[dof]),
                            acceleration_improvement_toward_target_rad_s2=float((weighted.previous[dof]-default.previous[dof])*direction)))
    invalid_rejected = False
    try:
        Balance(model, data).torque(posture_weights=np.zeros(model.nu))
    except ValueError as error:
        invalid_rejected = str(error) == 'Invalid joint-posture task weights'
    checks = dict(default_torques_identical=bool(np.array_equal(a, b)),
                  torso_tracking_response_improves=all(e['acceleration_improvement_toward_target_rad_s2'] > 0 for e in effects),
                  weighted_torques_finite_and_source_bounded=bool(np.isfinite(c).all() and
                      np.all(c >= model.actuator_ctrlrange[:,0]) and np.all(c <= model.actuator_ctrlrange[:,1])),
                  invalid_weights_rejected=invalid_rejected)
    deps = [Path(__file__), BASE/'balance.py', BASE/'walking_actor.py', BASE/'ftir_approach_actor.py',
            legacy_path, run/'controller_model/world.xml', run/'sensor_observations.npz', run/'result.json']
    report = dict(passed=all(checks.values()), checks=checks,
                  retained_posture_errors=errors, weighted_task_response=effects,
                  maximum_default_torque_difference=float(np.max(abs(a-b))),
                  source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
                  scope='Sensor-state diagnosis and inverse-controller regression. A changed foot stance need not reproduce nominal leg joint angles; the new upper-body task and unchanged support/contact criteria still require full physical execution.')
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'], checks=checks, effects=effects)), flush=True)
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
