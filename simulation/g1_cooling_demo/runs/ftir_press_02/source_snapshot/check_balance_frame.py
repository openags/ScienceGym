"""Regression: yawing a recorded physical state must preserve motor torques."""
import argparse
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation
from balance import Balance


def check(source, output):
    source, output = Path(source), Path(output)
    model=mujoco.MjModel.from_xml_path(str(source/'controller_model/world.xml'))
    trace=dict(np.load(source/'trace.npz'));idx=np.searchsorted(trace['time'],6.602)
    differences={}
    for rotated_limits in [False,True]:
        torques=[]
        for angle in [0,np.pi/2]:
            data=mujoco.MjData(model);data.qpos[:]=trace['qpos'][idx];data.qvel[:]=trace['qvel'][idx]
            rotation=Rotation.from_euler('z',angle)
            data.qpos[:3]=rotation.apply(data.qpos[:3]);data.qvel[:3]=rotation.apply(data.qvel[:3])
            quat=(rotation*Rotation.from_quat(data.qpos[[4,5,6,3]])).as_quat();data.qpos[3:7]=quat[[3,0,1,2]]
            mujoco.mj_forward(model,data)
            controller=Balance(model,data);forward=data.body('pelvis').xmat.reshape(3,3)[:,0]
            controller.pelvis_rotation=Rotation.from_euler('z',np.arctan2(forward[1],forward[0])).as_matrix()
            controller.rotate_foot_constraints=rotated_limits
            torques.append(controller.torque())
        differences['rotated_sole_limits' if rotated_limits else 'legacy_world_limits']=float(abs(torques[0]-torques[1]).max())
    report=dict(passed=differences['rotated_sole_limits']<1e-6 and differences['legacy_world_limits']>1e-3,
                source_run=str(source),source_time_s=float(trace['time'][idx]),rotation_deg=90,
                maximum_motor_torque_difference_nm=differences,
                balance_source_sha256=hashlib.sha256(Path(__file__).with_name('balance.py').read_bytes()).hexdigest(),
                check_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source');parser.add_argument('output');args=parser.parse_args()
    if not check(args.source,args.output)['passed']:raise SystemExit(1)
