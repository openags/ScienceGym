"""Inspect terminal FTIR tracking from the recorded robot sensors and plan.

This reconstructs the fixed-sole estimate for the final packet. It is not a
physical continuation or an independent key-displacement measurement.
"""
import argparse
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

from dex3_ftir_hand import Dex3PointingHand, POINTING
from observations import StateEstimate
from verify_dex3_ftir_controller import sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('run', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    result = json.loads((a.run/'result.json').read_text())
    assert sha(a.run/'sensors.npz') == result['sensors_sha256']
    assert sha(a.run/'events.json') == result['events_sha256']
    m = mujoco.MjModel.from_xml_path(str(a.run/'controller_model/world.xml'))
    d = mujoco.MjData(m)
    setup = json.loads((a.run/'policy_source/robot_setup.json').read_text())
    d.qpos[:7] = setup['root_qpos']
    for name, value in setup['joints'].items():
        d.joint(name).qpos[0] = value
    mujoco.mj_forward(m, d)
    estimate = StateEstimate(m, d)
    with np.load(a.run/'sensors.npz') as data:
        packet = {k:data[k][-1] for k in data.files if k != 'camera_frame_id'}
    packet['depth'] = None
    estimate.update(packet)
    events = json.loads((a.run/'events.json').read_text())
    plan = next(e['plan'] for e in events if e.get('kind') == 'sensor_target_selected')
    normal, rotation = np.asarray(plan['normal']), np.asarray(plan['wrist_rotation'])
    target = np.asarray(plan['contact_wrist_m'])-.001*normal
    material = np.asarray(plan['wrist_local_contact_m'])
    wrist = d.site('right_wrist_reference')
    tip = Dex3PointingHand(m).observed_contact_point(d, material)
    limits = []
    for j in m.actuator_trnid[:, 0]:
        value = float(d.qpos[m.jnt_qposadr[j]])
        low, high = m.jnt_range[j]
        margin = min(value-low, high-value)
        if margin < .03:
            limits.append(dict(joint=m.joint(j).name, position_rad=value, margin_rad=float(margin)))
    report = dict(scope=__doc__, time_s=float(packet['time_s']), recorded_failure=result['failure'],
        wrist_error_m=(wrist.xpos-target).tolist(),
        wrist_rotation_error_rad=Rotation.from_matrix(rotation@wrist.xmat.reshape(3, 3).T).as_rotvec().tolist(),
        fingertip_error_m=(tip-target-rotation@material).tolist(),
        hand_posture_error_rad={n:float(d.joint(n).qpos[0]-v) for n, v in POINTING.items()},
        near_source_joint_limits=limits, source_result_sha256=sha(a.run/'result.json'),
        sensors_sha256=result['sensors_sha256'], events_sha256=result['events_sha256'],
        source_sha256=sha(__file__), physical_continuation_executed=False, qualified_ftir_press=False)
    shutil.copyfile(__file__, a.output/Path(__file__).name)
    (a.output/'review.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
