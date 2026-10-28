"""Compare default stationary motor commands at retained window-task states."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
import mujoco
import numpy as np

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
sys.path.insert(0,str(BASE))
from balance import Balance


def main():
    output=HERE/'balance_default_regression.json'
    if output.exists():raise FileExistsError(output)
    source=BASE/'runs/ftir_slider_07'
    old_path=source/'source_snapshot/balance.py'
    spec=importlib.util.spec_from_file_location('retained_default_balance',old_path)
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    model=mujoco.MjModel.from_xml_path(str(source/'controller_model/world.xml'))
    plant=mujoco.MjModel.from_xml_path(str(source/'world.xml'))
    trace=dict(np.load(source/'trace.npz'))
    rows=[]
    for time in [0.,10.,30.,50.,60.,80.,100.,110.,117.]:
        index=int(np.argmin(abs(trace['time']-time)))
        data=mujoco.MjData(model)
        data.qpos[:7]=trace['qpos'][index,:7];data.qvel[:6]=trace['qvel'][index,:6]
        for j in range(model.njnt):
            if model.jnt_type[j]!=mujoco.mjtJoint.mjJNT_HINGE:continue
            other=plant.joint(model.joint(j).name)
            data.qpos[model.jnt_qposadr[j]]=trace['qpos'][index,int(other.qposadr[0])]
            data.qvel[model.jnt_dofadr[j]]=trace['qvel'][index,int(other.dofadr[0])]
        mujoco.mj_forward(model,data)
        before,after=old.Balance(model,data),Balance(model,data)
        a,b=before.torque(),after.torque()
        rows.append(dict(time_s=float(trace['time'][index]),maximum_motor_torque_difference_nm=float(np.max(abs(a-b)))))
    report=dict(passed=all(r['maximum_motor_torque_difference_nm']==0. for r in rows),rows=rows,
                scope='Default stationary Balance API on nine actual recorded robot states spanning the observed window task. New stepping behavior is assessed separately.',
                source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),BASE/'balance.py',old_path,source/'trace.npz',source/'controller_model/world.xml']})
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
    if not report['passed']:raise SystemExit(1)


if __name__=='__main__':main()
