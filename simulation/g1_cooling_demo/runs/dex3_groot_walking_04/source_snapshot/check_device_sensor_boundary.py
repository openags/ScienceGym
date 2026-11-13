"""Check robot encoder compatibility and absence of passive-device channels."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np
from observations import robot_joints


def check(folder):
    folder=Path(folder).resolve(); root=Path(__file__).resolve().parents[2]
    source=root/'assets/unitree_g1_inspire_v1/simulation/robot.xml'
    reference=mujoco.MjModel.from_xml_path(str(source))
    expected=[reference.joint(i).name for i in robot_joints(reference)]
    model=mujoco.MjModel.from_xml_path(str(folder/'world.xml'))
    names=[model.joint(i).name for i in robot_joints(model)]
    data=mujoco.MjData(model);mujoco.mj_forward(model,data)
    def read():
        return np.array([data.sensor(n+suffix).data[0] for n in names for suffix in ['_encoder','_velocity']])
    before=read()
    device=[i for i in range(model.njnt) if model.joint(i).name.startswith('nicolet_')]
    for j in device:
        data.qpos[model.jnt_qposadr[j]]=float(np.mean(model.jnt_range[j]))
        data.qvel[model.jnt_dofadr[j]]=.123
    mujoco.mj_forward(model,data)
    unchanged=np.array_equal(before,read())
    checks=dict(robot_joint_names_match_source=names==expected and len(names)==53,
                six_device_joints_excluded=len(device)==6 and not any(n.startswith('nicolet_') for n in names),
                device_position_velocity_change_does_not_change_encoder_packet=unchanged)
    report=dict(passed=all(checks.values()),checks=checks,robot_joint_names=names,
                robot_joint_count=len(names),passive_device_joint_count=len(device),
                source_robot_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                plant_sha256=hashlib.sha256((folder/'world.xml').read_bytes()).hexdigest(),
                observations_source_sha256=hashlib.sha256((Path(__file__).parent/'observations.py').read_bytes()).hexdigest(),
                scope='Encoder enumeration and counterfactual device-state check, not a replacement for process isolation.')
    (folder/'encoder_boundary_check.json').write_text(json.dumps(report,indent=2)+'\n')
    shutil.copyfile(__file__,folder/'check_device_sensor_boundary.py')
    shutil.copyfile(Path(__file__).parent/'observations.py',folder/'source_snapshot/observations.py')
    print(json.dumps({k:v for k,v in report.items() if k!='robot_joint_names'},indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');args=p.parse_args()
    if not check(args.folder)['passed']:raise SystemExit(1)
