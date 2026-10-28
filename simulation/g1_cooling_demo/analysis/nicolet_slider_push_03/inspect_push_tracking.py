"""Compare commanded wrist and fingertip tracking in a retained plant trace."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent;BASE = HERE.parents[1];ROOT = BASE.parents[1]
sys.path.insert(0, str(BASE))
from ftir_hand import PointingHand


def main(folder):
    folder = Path(folder).resolve();out = HERE/(folder.name+'_tracking.json')
    if out.exists():raise FileExistsError(out)
    trace = dict(np.load(folder/'trace.npz'))
    result = json.loads((folder/'result.json').read_text())
    solution = next(e['solution'] for e in result['actor_last_output']['events'] if 'solution' in e)
    normal = np.array(solution['outward_normal']);direction = np.array(solution['direction'])
    rotation = np.array(solution['contact_palm_rotation'])
    m = mujoco.MjModel.from_xml_path(str(folder/'world.xml'));d = mujoco.MjData(m)
    hand = PointingHand(m);heights = (hand.pad_vertices@rotation.T)@normal
    pad = hand.pad_vertices[heights < heights.min()+2e-5].mean(axis=0)
    slide = int(m.joint('nicolet_door_slide').qposadr[0])
    rows = []
    for line in (folder/'actor_monitor.jsonl').read_text().splitlines():
        record = json.loads(line);t = record['time_s']
        if not 45 <= t <= 48.51:continue
        command = record['commanded_pose'];p = np.array(command['position_m']);r = np.array(command['rotation'])
        i = int(np.argmin(abs(trace['time']-t)))
        d.qpos[:] = trace['qpos'][i];mujoco.mj_kinematics(m,d)
        wrist = d.site('right_wrist_reference');actual = hand.observed_contact_point(d,pad)
        target = p+r@pad;error = target-actual
        rotation_effect = (r-wrist.xmat.reshape(3,3))@pad
        rows.append(dict(time_s=t,phase=record['policy_state'],
            slider_position_m=float(d.qpos[slide]),
            desired_pad_displacement_along_slider_m=float((p-np.array(solution['contact_palm_position_m']))@direction),
            pad_error_normal_m=float(error@normal),pad_error_slide_direction_m=float(error@direction),
            wrist_error_normal_m=float((p-wrist.xpos)@normal),
            rotation_effect_normal_m=float(rotation_effect@normal),
            wrist_rotation_error_rad=float(np.linalg.norm(Rotation.from_matrix(r@wrist.xmat.reshape(3,3).T).as_rotvec())),
            index_q=[float(d.joint('right_index_'+str(k)+'_joint').qpos[0]) for k in [1,2]],
            load=record['touch']))
    report = dict(rows=rows,force_axis_component_n=float(-2*normal@direction),
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),folder/'trace.npz',folder/'result.json',folder/'actor_monitor.jsonl']},
        scope='Post-run truth-side geometry diagnosis, not a controller input or causal proof.')
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'rows':len(rows),'output':str(out)}),flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');main(p.parse_args().folder)
