"""Check surface-load virtual work and unchanged legacy controller output."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
ROOT = BASE.parents[1]
sys.path.insert(0, str(BASE))
from balance import Balance
from ftir_hand import ArmIK, PointingHand, mimic
from ftir_slider_posture import initialize_slider


def main():
    output = HERE/'surface_load_regression_02.json'
    if output.exists():
        raise FileExistsError(output)
    run = BASE/'runs/ftir_slider_scan_02'
    model = mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'))
    model.opt.disableflags |= mujoco.mjtDisableBit.mjDSBL_CONTACT
    old_source = run/'source_snapshot/balance.py'
    spec = importlib.util.spec_from_file_location('retained_balance', old_source)
    old = importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    a = initialize_slider(model);b = initialize_slider(model)
    new_torque = Balance(model, a).torque()
    old_torque = old.Balance(model, b).torque()
    plan = json.loads((HERE/'sensor_plan.json').read_text())
    data = mujoco.MjData(model);data.qpos[:] = plan['estimated_initial_qpos']
    solution = plan['plan'];ik = ArmIK(model)
    for name, value in solution['candidate']['hand_q'].items():
        data.joint(name).qpos[0] = value
    q, pe, re = ik.solve(data, np.array(solution['contact_palm_position_m']),
                         np.array(solution['contact_palm_rotation']),
                         np.array(solution['entry_path'][-1]))
    if pe > .003 or re > .035:
        raise ValueError('Contact fixture IK did not converge')
    data.qpos[ik.qa] = q;mimic(model, data);mujoco.mj_forward(model, data)
    hand = PointingHand(model);normal = np.array(solution['outward_normal'])
    rotation = np.array(solution['contact_palm_rotation'])
    height = (hand.pad_vertices@rotation.T)@normal
    point_local = hand.pad_vertices[height < height.min()+2e-5].mean(axis=0)
    point = hand.observed_contact_point(data, point_local)
    controller = Balance(model, data)
    jacobian, _ = controller.jacobian(point, model.body('right_index_force_sensor_3').id)
    velocity = np.random.default_rng(619).normal(0, .2, model.nv)
    delta = 1e-7;future = mujoco.MjData(model);future.qpos[:] = data.qpos
    mujoco.mj_integratePos(model, future.qpos, velocity, delta)
    mujoco.mj_kinematics(model, future)
    finite_velocity = (hand.observed_contact_point(future, point_local)-point)/delta
    force = -normal*2
    joint_power = float(velocity@(jacobian[:3].T@force))
    surface_power = float(finite_velocity@force)
    wrist = data.site('right_wrist_reference')
    wrist_jacobian, _ = controller.jacobian(wrist.xpos, int(model.site_bodyid[wrist.id]))
    fingers = []
    for name in ['right_index_1_joint', 'right_index_2_joint']:
        i = int(model.joint(name).dofadr[0])
        fingers.append(dict(joint=name, at_pad_nm=float((jacobian[:3].T@force)[i]),
                            at_wrist_nm=float((wrist_jacobian[:3].T@force)[i])))
    empty_difference = float(np.max(abs(new_torque-old_torque)))
    velocity_error = float(np.linalg.norm(finite_velocity-jacobian[:3]@velocity))
    power_error = abs(joint_power-surface_power)
    deps = [Path(__file__), BASE/'balance.py', BASE/'ftir_slider_actor.py', old_source,
            HERE/'sensor_plan.json', run/'controller_model/world.xml']
    report = dict(no_surface_load_bit_identical=bool(np.array_equal(new_torque, old_torque)),
        maximum_empty_load_torque_difference=empty_difference,
        contact_jacobian_velocity_error_m_s=velocity_error, virtual_work_error_w=power_error,
        finger_generalized_loads=fingers,
        passed=empty_difference == 0 and velocity_error < 1e-7 and power_error < 1e-7,
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
        scope='Model-load algebra and unchanged default-controller regression only; no physical push result.')
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
