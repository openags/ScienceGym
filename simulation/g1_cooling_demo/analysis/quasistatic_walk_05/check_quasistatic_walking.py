"""Development integration probe in the retained full lab; no isolation credit.

The controller API receives native encoders/IMU only. This in-process probe is
not the separate-process isolation or full-paper acceptance test.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
import mujoco
import numpy as np

from balance import Balance
from observations import robot_joints
from quasistatic_walking import QuasistaticWalker


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(source, output, seconds=24.):
    source, output = Path(source).resolve(),Path(output).resolve()
    output.mkdir(parents=True,exist_ok=True)
    if any(output.iterdir()):
        raise FileExistsError(output)
    for name in ['balance.py','quasistatic_walking.py','check_quasistatic_walking.py']:
        shutil.copyfile(Path(__file__).parent/name,output/name)
    model = mujoco.MjModel.from_xml_path(str(source/'world.xml'))
    data = mujoco.MjData(model)
    data.qpos[:] = json.loads((source/'staging.json').read_text())['initial_qpos']
    mujoco.mj_forward(model,data)
    predictor = mujoco.MjModel.from_xml_path(str(source/'controller_model/world.xml'))
    estimate = mujoco.MjData(predictor)
    start = data.qpos[:2].copy()
    goal = start+np.array([.12,0.])
    actor = QuasistaticWalker(predictor,estimate,start,goal)
    names = [model.joint(j).name for j in robot_joints(model)]
    contract = dict(initial_xy_m=start.tolist(),goal_xy_m=goal.tolist(),duration_s=seconds,
                    maximum_step_length_m=.12,swing_clearance_m=.055,
                    support_assumption='Level floor; encoder/IMU kinematics; no measured sole force',
                    scope='One short stepping development probe, in the original laboratory. No sensor-isolation, navigation, manipulation or reliability qualification.',
                    source_hashes={str(p):sha(p) for p in [source/'world.xml',source/'controller_model/world.xml',source/'staging.json',*output.glob('*.py')]})
    (output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    old_path = source/'source_snapshot/balance.py'
    spec = importlib.util.spec_from_file_location('old_balance_probe',old_path)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    records, sensors, states = [],[],[]
    failure = None
    regression = None
    max_inactive_wrench = 0.
    try:
        for i in range(round(seconds/model.opt.timestep)):
            packet = dict(time_s=float(data.time),
                          joint_position=np.array([data.sensor(n+'_encoder').data[0] for n in names]),
                          joint_velocity=np.array([data.sensor(n+'_velocity').data[0] for n in names]),
                          imu_quaternion=data.sensor('imu_orientation').data.copy(),
                          imu_gyro=data.sensor('imu_angular_velocity').data.copy(),depth=None)
            if i == 0:
                actor.estimate.update(packet)
                before,after = old.Balance(predictor,estimate),Balance(predictor,estimate)
                a,b = before.torque(),after.torque()
                invalid_rejected = False
                try:
                    after.torque(support_feet=[False,False])
                except ValueError:
                    invalid_rejected = True
                regression = dict(default_torque_maximum_difference_nm=float(np.max(abs(a-b))),
                                  empty_support_rejected=invalid_rejected,
                                  original_source_sha256=sha(old_path))
                if np.max(abs(a-b))>1e-10 or not invalid_rejected:
                    raise RuntimeError('Stationary balance compatibility regression')
            data.ctrl[:],_ = actor.torque(packet)
            if not actor.estimate.support.all():
                for foot in np.flatnonzero(~actor.estimate.support):
                    wrench = actor.balance.previous[predictor.nv+6*foot:predictor.nv+6*(foot+1)]
                    max_inactive_wrench = max(max_inactive_wrench,float(np.max(abs(wrench))))
            records.append((float(data.time),data.qpos.copy(),data.qvel.copy(),data.ctrl.copy(),data.qacc_warmstart.copy()))
            sensors.append({k:v for k,v in packet.items() if k!='depth'})
            if i%50 == 0:
                states.append(dict(time_s=float(data.time),phase=actor.phase,steps=actor.steps,
                                   estimated_position_m=estimate.qpos[:3].tolist(),
                                   support_feet=actor.estimate.support.tolist()))
            mujoco.mj_step(model,data)
            if i%500 == 0:
                print('quasistatic',round(data.time,3),actor.phase,'steps',actor.steps,'root',data.qpos[:3].round(4).tolist(),flush=True)
            if np.any(data.warning.number) or data.qpos[2]<.65 or data.body('pelvis').xmat.reshape(3,3)[2,2]<np.cos(.3):
                raise RuntimeError('Development body-support stop')
            if actor.finished and data.time-actor.parking_time>=2.:
                break
        if not actor.finished:
            raise RuntimeError('Duration exhausted before short walk settled')
    except Exception as error:
        failure = str(error)
        print('failed',failure,flush=True)
    records.append((float(data.time),data.qpos.copy(),data.qvel.copy(),data.ctrl.copy(),data.qacc_warmstart.copy()))
    np.savez_compressed(output/'trace.npz',**{k:np.array([r[i] for r in records]) for i,k in enumerate(['time','qpos','qvel','ctrl','qacc_warmstart'])})
    if sensors:
        np.savez_compressed(output/'sensor_observations.npz',**{k:np.array([r[k] for r in sensors]) for k in sensors[0]})
    result = dict(status='failed' if failure else 'finished_pending_independent_review',failure=failure,
                  simulated_seconds=float(data.time),completed_steps=actor.steps,events=actor.events,
                  final_position_m=data.qpos[:3].tolist(),regression=regression,
                  maximum_inactive_foot_model_wrench=max_inactive_wrench,
                  controller_states=states,trace_sha256=sha(output/'trace.npz'),
                  qualified_skill=False,qualified_paper_branch=False)
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in {'events','controller_states'}}),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('source')
    p.add_argument('output')
    p.add_argument('--seconds',type=float,default=24.)
    a=p.parse_args()
    if run(a.source,a.output,a.seconds)['status']=='failed':
        raise SystemExit(1)
