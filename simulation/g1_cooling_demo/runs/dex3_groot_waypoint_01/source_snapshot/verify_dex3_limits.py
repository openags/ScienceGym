"""Check recorded G1/three-finger commands and speeds against pinned sources."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'analysis/g1_dex3_comparison_01/g1_29dof_with_hand_rev_1_0.urdf'
BUILDER_SHA=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(folder):
    folder=Path(folder).resolve();result=json.loads((folder/'result.json').read_text())
    contract=json.loads((folder/'contract.json').read_text())
    assert contract['hand_kind']=='unitree_three_finger'
    assert sha(folder/'trace.npz')==result['trace_sha256']
    assert sha(folder/'world.xml')==contract['model_sha256']
    m=mujoco.MjModel.from_xml_path(str(folder/'world.xml'));trace=np.load(folder/'trace.npz')
    qvel=trace['qvel'];commands=trace['ctrl'];source=ET.parse(SOURCE).getroot();rows=[]
    assert commands.shape[1]==m.nu==43
    for a,j in enumerate(m.actuator_trnid[:,0]):
        name=m.joint(j).name;limit=source.find(f"joint[@name='{name}']/limit")
        assert limit is not None and m.jnt_type[j]==mujoco.mjtJoint.mjJNT_HINGE
        speed=float(limit.get('velocity'));effort=float(limit.get('effort'))
        peak_speed=float(np.max(abs(qvel[:,m.jnt_dofadr[j]])))
        peak_motor=float(np.max(abs(commands[:,a]*m.actuator_gear[a,0])))
        peak_command_excess=float(max(np.max(m.actuator_ctrlrange[a,0]-commands[:,a]),np.max(commands[:,a]-m.actuator_ctrlrange[a,1]),0.))
        rows.append(dict(joint=name,source_velocity_rad_s=speed,source_effort_nm=effort,
                         maximum_recorded_speed_rad_s=peak_speed,maximum_commanded_torque_nm=peak_motor,
                         command_range_excess=peak_command_excess,
                         velocity_passed=peak_speed<=speed+1e-3,
                         torque_passed=peak_motor<=effort+1e-9 and peak_command_excess<=1e-9))
    report=dict(scope=__doc__,passed=all(r['velocity_passed'] and r['torque_passed'] for r in rows),
                source_urdf_sha256=sha(SOURCE),trace_sha256=result['trace_sha256'],world_sha256=sha(folder/'world.xml'),
                rows=rows,velocity_tolerance_rad_s=.001,torque_tolerance_nm=1e-9,verifier_sha256=BUILDER_SHA,
                controller_only_motor_commands=True,actual_motor_dynamics_calibrated=False,qualified_grasp=False)
    (folder/'source_limit_review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],failures=[r for r in rows if not(r['velocity_passed'] and r['torque_passed'])])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');run(p.parse_args().folder)
