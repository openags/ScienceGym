"""Inspect recorded joint bounds and grasp posture; no execution qualification.

Kinematic state inspection does not rerun contact dynamics. Any linked sparse
wrench reconstruction retains its own limitations and is not a slip sensor.
"""
import argparse
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    parser.add_argument('--model-run',type=Path)
    parser.add_argument('--times',type=float,nargs='+',required=True)
    parser.add_argument('--output-name',default='carry_state_diagnosis.json')
    args=parser.parse_args();folder=args.folder;model_folder=args.model_run or folder
    if Path(args.output_name).name!=args.output_name:raise ValueError('Output must be a single child filename')
    output=folder/args.output_name
    if output.exists():raise FileExistsError('Preserve existing diagnosis: '+str(output))
    result=json.loads((folder/'result.json').read_text())
    contract=json.loads((model_folder/'contract.json').read_text())
    trace_hash=sha(folder/'trace.npz');model_hash=sha(model_folder/'world.xml')
    assert trace_hash==result['trace_sha256'] and model_hash==contract['model_sha256']
    if args.model_run:assert result['actor_contract_sha256']==sha(model_folder/'contract.json')
    m=mujoco.MjModel.from_xml_path(str(model_folder/'world.xml'));d=mujoco.MjData(m)
    with np.load(folder/'trace.npz') as z:times=z['time'];positions=z['qpos']
    violations=[]
    for j in np.flatnonzero(m.jnt_limited):
        lo,hi=m.jnt_range[j];values=positions[:,m.jnt_qposadr[j]]
        excess=np.maximum(lo-values,values-hi);i=int(np.argmax(excess))
        if excess[i]>0:
            violations.append(dict(joint=m.joint(j).name,range_rad=[float(lo),float(hi)],
                maximum_excess_rad=float(excess[i]),maximum_time_s=float(times[i]),
                first_excess_time_s=float(times[np.flatnonzero(excess>0)[0]])))
    prior_file=model_folder/'policy_source/tool_prior.json'
    prior=json.loads(prior_file.read_text())
    fixed={n:v for n,v in prior['grasp_geometry']['pregrasp_hand_q'].items()
           if n not in prior['closing_drivers']}
    monitor_file=folder/'monitor.jsonl'
    commands=[]
    if monitor_file.exists():
        commands=[r for line in monitor_file.read_text().splitlines()
                  if (r:=json.loads(line)).get('hand_commands_rad')]
    rows=[]
    for t in args.times:
        if not times[0]<=t<=times[-1]:raise ValueError('Sample outside trace')
        i=int(np.argmin(abs(times-t)));d.qpos[:]=positions[i];mujoco.mj_kinematics(m,d)
        mujoco.mj_comPos(m,d)
        wrist=d.site('right_wrist_reference');tool=d.body('tweezer')
        R=wrist.xmat.reshape(3,3)
        reference=fixed;reference_basis='public_pregrasp_reference';reference_time=None
        if commands:
            command=min(commands,key=lambda r:abs(r['time_s']-times[i]))
            if abs(command['time_s']-times[i])<=.02 and all(n in command['hand_commands_rad'] for n in fixed):
                reference={n:command['hand_commands_rad'][n] for n in fixed}
                reference_basis='recorded_hand_command';reference_time=command['time_s']
        com=d.subtree_com[m.body('pelvis').id].copy()
        soles={side:d.site(side+'_sole').xpos.copy() for side in ['left','right']}
        ankles={}
        for side in ['left','right']:
            joint=m.joint(side+'_ankle_roll_joint');value=float(d.qpos[joint.qposadr[0]])
            ankles[side]=dict(position_rad=value,source_bounds_rad=joint.range.tolist(),
                margin_to_source_limit_rad=float(min(value-joint.range[0],joint.range[1]-value)))
        rows.append(dict(time_s=float(times[i]),
            tool_in_wrist_m=(R.T@(tool.xpos-wrist.xpos)).tolist(),
            robot_com_world_m=com.tolist(),sole_centers_world_m={k:v.tolist() for k,v in soles.items()},
            com_relative_to_each_sole_xy_m={k:(com[:2]-v[:2]).tolist() for k,v in soles.items()},
            ankle_roll=ankles,
            hand_reference_basis=reference_basis,hand_reference_time_s=reference_time,
            fixed_hand_posture_error_rad={n:float(d.joint(n).qpos[0]-v) for n,v in reference.items()}))
    report=dict(scope=__doc__,trace_sha256=trace_hash,model_sha256=model_hash,
        script_sha256=sha(__file__),prior_sha256=sha(prior_file),
        source_joint_bound_exceedances=violations,rows=rows,
        fixed_posture_basis='Recorded non-closing-joint commands where available; otherwise public pregrasp reference, not an assertion that the target remained constant',
        balance_scope='Kinematics of recorded plant states only; sole-center offsets do not certify support forces, estimator accuracy or stable walking',
        physical_replay=False,qualified_carry=False,qualified_paper_branch=False)
    wrench=folder/'contact_wrench_diagnosis.json'
    if wrench.exists():
        w=json.loads(wrench.read_text());assert w['trace_sha256']==trace_hash
        report['sparse_wrench_source_sha256']=sha(wrench)
        report['sparse_contact_centers']=[]
        for row in w['rows']:
            R=np.asarray(row['tool_rotation']);p=np.asarray(row['tool_position_m'])
            centers={n:None if f['center_world_m'] is None else
                     (R.T@(np.asarray(f['center_world_m'])-p)).tolist()
                     for n,f in row['fingers'].items()}
            report['sparse_contact_centers'].append(dict(time_s=row['time_s'],tool_frame_centers_m=centers))
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(output=str(output),source_joint_bound_exceedances=violations,rows=rows)),flush=True)


if __name__=='__main__':main()
