"""Regress unchanged calls and check the fingertip task in the public model."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import mujoco
import numpy as np

HERE=Path(__file__).resolve().parent;BASE=HERE.parents[1];ROOT=BASE.parents[1]
sys.path.insert(0,str(BASE))
from balance import Balance
from ftir_slider_posture import initialize_slider
from ftir_hand import PointingHand, ArmIK, mimic


def main():
    output=HERE/'point_task_regression.json'
    if output.exists():raise FileExistsError(output)
    run=BASE/'runs/ftir_slider_03'
    m=mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'))
    old_source=run/'source_snapshot/balance.py'
    spec=importlib.util.spec_from_file_location('retained_balance',old_source)
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    a=initialize_slider(m);b=initialize_slider(m)
    old_torque=old.Balance(m,a).torque();new_torque=Balance(m,b).torque()
    plan_path=HERE.parent/'nicolet_slider_push_03/sensor_plan.json'
    plan=json.loads(plan_path.read_text());solution=plan['plan']
    data=mujoco.MjData(m);data.qpos[:]=plan['estimated_initial_qpos']
    for name,value in solution['candidate']['hand_q'].items():data.joint(name).qpos[0]=value
    ik=ArmIK(m);rotation=np.array(solution['contact_palm_rotation'])
    q,pe,re=ik.solve(data,np.array(solution['contact_palm_position_m']),rotation,
                     np.array(solution['entry_path'][-1]))
    if pe>.003 or re>.035:raise ValueError('Fixture IK failed')
    data.qpos[ik.qa]=q;mimic(m,data);mujoco.mj_forward(m,data)
    hand=PointingHand(m);normal=np.array(solution['outward_normal'])
    heights=(hand.pad_vertices@rotation.T)@normal
    pad=hand.pad_vertices[heights<heights.min()+2e-5].mean(axis=0)
    point=hand.observed_contact_point(data,pad);body='right_index_force_sensor_3'
    jac,_=Balance(m,data).jacobian(point,m.body(body).id)
    velocity=np.random.default_rng(721).normal(0,.2,m.nv)
    future=mujoco.MjData(m);future.qpos[:]=data.qpos;epsilon=1e-7
    mujoco.mj_integratePos(m,future.qpos,velocity,epsilon);mujoco.mj_kinematics(m,future)
    finite=(hand.observed_contact_point(future,pad)-point)/epsilon
    velocity_error=float(np.linalg.norm(finite-jac[:3]@velocity))
    controllers=[];torques=[];accels=[]
    for displacement in [np.zeros(3),normal*.001]:
        controller=Balance(m,data)
        torque=controller.torque(point_targets=[dict(body=body,point=point,target=point+displacement)])
        controllers.append(controller);torques.append(torque)
        accels.append(jac[:3]@controller.previous[:m.nv])
    correction=float((accels[1]-accels[0])@normal)
    bounded=all(np.all(t>=m.actuator_ctrlrange[:,0]-1e-9) and np.all(t<=m.actuator_ctrlrange[:,1]+1e-9) for t in torques)
    rejected=False
    try:Balance(m,data).torque(point_targets=[dict(body=body,point=point,target=[np.nan,0,0])])
    except ValueError:rejected=True
    checks=dict(default_calls_bit_identical=bool(np.array_equal(old_torque,new_torque)),
                encoder_point_jacobian_matches_finite_difference=velocity_error<1e-7,
                requested_outward_point_shift_increases_outward_acceleration=correction>0,
                commanded_torques_within_source_bounds=bool(bounded),nonfinite_target_rejected=rejected)
    deps=[Path(__file__),BASE/'balance.py',BASE/'ftir_slider_actor.py',old_source,plan_path,
          run/'controller_model/world.xml']
    report=dict(passed=all(checks.values()),checks=checks,
        maximum_default_torque_difference=float(np.max(abs(old_torque-new_torque))),
        point_jacobian_velocity_error_m_s=velocity_error,
        outward_acceleration_change_m_s2=correction,
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
        scope='Public-model controller regression. Does not establish contact stability, physical execution or slider success.')
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
    if not report['passed']:raise SystemExit(1)


if __name__=='__main__':main()
