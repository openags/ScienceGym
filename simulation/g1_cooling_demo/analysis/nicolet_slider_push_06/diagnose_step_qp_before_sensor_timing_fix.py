"""Reproduce the failed sensor-only QP and compare numerical conditioning.

No physical plant is advanced and no candidate receives execution credit.
"""
import hashlib
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode=True
import mujoco
import numpy as np
import osqp
from scipy import sparse

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
sys.path.insert(0,str(BASE))
from observations import robot_joints
from quasistatic_walking import QuasistaticWalker
import balance


def main():
    output=HERE/'step_qp_diagnosis.json'
    if output.exists():raise FileExistsError(output)
    run=BASE/'analysis/quasistatic_walk_03'
    source=BASE/'runs/ftir_approach_06'
    model=mujoco.MjModel.from_xml_path(str(source/'controller_model/world.xml'))
    data=mujoco.MjData(model)
    contract=json.loads((run/'contract.json').read_text())
    actor=QuasistaticWalker(model,data,contract['initial_xy_m'],contract['goal_xy_m'])
    native=dict(np.load(run/'sensor_observations.npz'))
    original=osqp.OSQP
    latest={}
    class Capture:
        def __init__(self):self.inner=original()
        def setup(self,**kwargs):
            latest.clear();latest['problem']=dict(kwargs);self.inner.setup(**kwargs)
        def warm_start(self,**kwargs):
            latest['warm']={k:v.copy() for k,v in kwargs.items()};self.inner.warm_start(**kwargs)
        def solve(self,**kwargs):return self.inner.solve(**kwargs)
    balance.osqp.OSQP=Capture
    failed=None
    try:
        for i,t in enumerate(native['time_s']):
            packet={k:v[i] for k,v in native.items()};packet['depth']=None
            actor.torque(packet)
        # The failing packet was not accepted into the motor trace. Recover
        # it from the recorded final plant state for this diagnostic only.
        plant=mujoco.MjModel.from_xml_path(str(source/'world.xml'));pd=mujoco.MjData(plant)
        trace=dict(np.load(run/'trace.npz'))
        pd.qpos[:]=trace['qpos'][-1];pd.qvel[:]=trace['qvel'][-1]
        pd.time=float(trace['time'][-1]);mujoco.mj_forward(plant,pd)
        names=[plant.joint(j).name for j in robot_joints(plant)]
        packet=dict(time_s=pd.time,joint_position=np.array([pd.sensor(n+'_encoder').data[0] for n in names]),
                    joint_velocity=np.array([pd.sensor(n+'_velocity').data[0] for n in names]),
                    imu_quaternion=pd.sensor('imu_orientation').data.copy(),imu_gyro=pd.sensor('imu_angular_velocity').data.copy(),depth=None)
        actor.torque(packet)
    except RuntimeError as error:failed=str(error)
    finally:balance.osqp.OSQP=original
    if failed is None:raise RuntimeError('The failed QP was not reproduced')
    base=latest['problem'];warm=latest.get('warm',{})
    sparse.save_npz(HERE/'step_failure_P.npz',base['P'])
    sparse.save_npz(HERE/'step_failure_A.npz',base['A'])
    np.savez_compressed(HERE/'step_failure_vectors.npz',q=base['q'],l=base['l'],u=base['u'],**warm)
    variants=[{},dict(adaptive_rho_interval=25),dict(rho=.01,adaptive_rho_interval=25),
              dict(rho=.001,adaptive_rho_interval=25),dict(scaling=30,adaptive_rho_interval=25),
              dict(sigma=1e-5,adaptive_rho_interval=25)]
    rows=[]
    for changes in variants:
        solver=original();settings=dict(base,**changes)
        solver.setup(**settings)
        if warm:solver.warm_start(**warm)
        started=time.monotonic();result=solver.solve(raise_error=False)
        rows.append(dict(settings=changes,status=result.info.status,iterations=result.info.iter,
                         primal_residual=result.info.prim_res,dual_residual=result.info.dual_res,
                         wall_seconds=time.monotonic()-started))
    report=dict(reproduced_failure=failed,variants=rows,
                unchanged_settings=dict(eps_abs=base['eps_abs'],eps_rel=base['eps_rel'],max_iter=base['max_iter']),
                scope='Numerical diagnosis on one retained constrained problem. Physical bounds and task requirements unchanged. No walking execution credit.',
                hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),BASE/'balance.py',BASE/'quasistatic_walking.py',run/'trace.npz',run/'sensor_observations.npz']})
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':main()
