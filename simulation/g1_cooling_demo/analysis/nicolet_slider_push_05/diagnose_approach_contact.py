"""Post-run contact tracking diagnosis; never used by the robot actor."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import mujoco
import numpy as np


def main(folder, output):
    folder, output = Path(folder).resolve(), Path(output)
    if output.exists():raise FileExistsError(output)
    result=json.loads((folder/'result.json').read_text())
    events=result['actor_last_output']['events']
    solution=next(e['solution'] for e in events if e['state']=='observed_geometry_path_planned')
    sys.dont_write_bytecode=True
    sys.path.insert(0,str(folder/'actor_bundle/code'))
    from ftir_hand import PointingHand
    model=mujoco.MjModel.from_xml_path(str(folder/'world.xml'));data=mujoco.MjData(model)
    hand=PointingHand(model,solution['candidate']['hand_q'])
    rotation=np.array(solution['contact_palm_rotation'])
    normal=np.array(solution['outward_normal']);axis=np.array(solution['direction'])
    heights=(hand.pad_vertices@rotation.T)@normal
    pad=hand.pad_vertices[heights<heights.min()+2e-5].mean(axis=0)
    trace=dict(np.load(folder/'trace.npz'))
    responses={round(r['time_s'],6):r for r in json.loads((folder/'actor_responses.json').read_text())}
    slider=int(model.joint('nicolet_door_slide').qposadr[0]);rows=[]
    for line in (folder/'actor_monitor.jsonl').read_text().splitlines():
        row=json.loads(line)
        if row.get('policy_state') not in {'seek_contact','push','withdraw_abort'}:continue
        t=row['time_s'];command=row.get('commanded_pose')
        if command is None:continue
        i=int(np.argmin(abs(trace['time']-t)))
        data.qpos[:]=trace['qpos'][i];mujoco.mj_kinematics(model,data)
        point=hand.observed_contact_point(data,pad)
        p=np.array(command['position_m']);r=np.array(command['rotation']);target=p+r@pad
        wrist=data.site('right_wrist_reference')
        est=responses[round(t,6)].get('estimated_root_position_m')
        rows.append(dict(time_s=t,phase=row['policy_state'],slider_position_m=float(data.qpos[slider]),
                         desired_displacement_m=float((p-np.array(solution['contact_palm_position_m']))@axis),
                         pad_error_normal_m=float((target-point)@normal),
                         pad_error_axial_m=float((target-point)@axis),
                         wrist_error_normal_m=float((p-wrist.xpos)@normal),
                         commanded_normal_offset_m=command['normal_offset_m'],
                         estimated_root_error_m=None if est is None else (np.asarray(est)-data.qpos[:3]).tolist(),
                         index_joint_rad=[float(data.joint('right_index_'+str(k)+'_joint').qpos[0]) for k in [1,2]],
                         touch=row['touch']))
    report=dict(candidate_id=solution['candidate']['id'],handoff=[e for e in events if e['state']=='continuous_station_handoff'],
                recovery=[e for e in events if e['state']=='recovery_started'],rows=rows,
                maximum_slider_travel_m=float(np.max(trace['qpos'][:,slider])),
                source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                               [Path(__file__),folder/'trace.npz',folder/'result.json',folder/'actor_monitor.jsonl',
                                folder/'actor_responses.json',folder/'actor_bundle/code/ftir_hand.py']},
                scope='Truth-side diagnosis after execution. No force inference from geometric forward kinematics; no controller input or acceptance threshold changed.')
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['candidate_id','recovery','maximum_slider_travel_m']}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');p.add_argument('output');a=p.parse_args();main(a.folder,a.output)
