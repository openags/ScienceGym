"""Replay recorded sensor packets to inspect a proposed loaded-walking handoff.

This host-side diagnostic checks policy equivalence up to the new carrying
stage and sampled loaded-arm geometry. It neither moves a physical payload
nor supplies carrying, isolation or repeated-reliability qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pickle
import shutil
import traceback

import mujoco
import numpy as np

from carry_tool_actor import ToolActor
from verify_tool_grasp import difference


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('recording');p.add_argument('output');a=p.parse_args()
    run=Path(a.recording).resolve();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
    source=out/'source';source.mkdir()
    modules=['check_tool_carry_handoff.py','carry_tool_actor.py','visual_tool_actor.py','dex3_tool_actor.py',
        'balance.py','conic_balance.py','observations.py','quasistatic_walking.py','tool_approach_planning.py',
        'tool_observation.py','tool_pose.py','source_proximity.py','robot_source_meshes.py','ftir_hand.py','joint_rrt.py']
    for n in modules:shutil.copyfile(Path(__file__).parent/n,source/n)
    report=dict(scope=__doc__,qualified_carry=False,physical_execution=False,
                source_sha256={f.name:sha(f) for f in source.iterdir()},source_result_sha256=sha(run/'result.json'))
    try:
        result=json.loads((run/'result.json').read_text())
        for f,key in [('sensors.npz','sensors_sha256'),('responses.pkl','responses_sha256'),('camera_index.json','camera_index_sha256')]:
            assert sha(run/f)==result[key]
        prior=json.loads((run/'policy_source/tool_prior.json').read_text())
        prior.update(carry_distance_m=.12,tool_shape_path=str(run/'object_shape_source/tool_shape.glb'))
        model=mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'));actor=ToolActor(model,prior)
        sensors=dict(np.load(run/'sensors.npz'));responses=pickle.loads((run/'responses.pkl').read_bytes())
        index=json.loads((run/'camera_index.json').read_text());maximum=0.;compared=0
        for i,expected in enumerate(responses):
            obs={k:v[i] for k,v in sensors.items()};frame=int(obs.pop('camera_frame_id'))
            if frame>=0:
                row=index[frame];assert sha(run/row['file'])==row['sha256']
                with np.load(run/row['file']) as camera:obs.update({k:camera[k] for k in camera.files})
            else:obs.update(head_rgb=None,head_depth=None)
            response=actor.update(obs)
            if actor.guard is not None:
                report.update(handoff_time_s=float(obs['time_s']),handoff_phase=actor.phase,
                              handoff_failure=actor.failure,handoff_clearance=actor.carry_clearance)
                break
            actual={k:response[k] for k in expected};error=difference(expected,actual)
            maximum=max(maximum,error);compared+=1
            if error>1e-10:raise RuntimeError('Pre-carry policy changed at packet '+str(i))
        report.update(compared_prefix_packets=compared,maximum_prefix_response_error=maximum)
        if actor.guard is None:raise RuntimeError('No loaded carry handoff reached')
        rows=[];q=actor.d.qpos.copy();ik=actor.planner.ik
        start=actor.return_wrist+actor.wrist_rotation@actor.center_offset+[0.,0.,actor.lift_height]
        raised=start+[0.,0.,.05];retracted=raised+actor.withdraw_delta
        for name,a0,b0 in [('raise',start,raised),('retract',raised,retracted)]:
            for u in np.linspace(0.,1.,int(np.ceil(np.linalg.norm(b0-a0)/.002))+1):
                actor.guard.d.qpos[:]=q;mujoco.mj_forward(model,actor.guard.d)
                joints,pe,re=ik.solve(actor.guard.d,a0+u*(b0-a0),actor.wrist_rotation,q[ik.qa])
                q[ik.qa]=joints
                clearance=actor.guard.check(q)
                row=dict(segment=name,fraction=float(u),position_error_m=pe,rotation_error_rad=re,clearance=clearance)
                rows.append(row)
                if pe>.001 or re>.025 or not clearance['clear']:break
            if pe>.001 or re>.025 or not clearance['clear']:break
        report['sampled_arm_path']=rows
        report['passed']=bool(actor.failure is None and rows and rows[-1]['segment']=='retract' and rows[-1]['fraction']==1. and
                              all(r['position_error_m']<=.001 and r['rotation_error_rad']<=.025 and r['clearance']['clear'] for r in rows))
        np.savez_compressed(out/'handoff.npz',robot_estimated_qpos=actor.d.qpos,
            proposed_retracted_qpos=q,wrist_start=start,wrist_raised=raised,wrist_retracted=retracted)
    except Exception as exc:
        report.update(passed=False,error=str(exc),traceback=traceback.format_exc())
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','sampled_arm_path']}),flush=True)
    if not report['passed']:raise SystemExit(1)


if __name__=='__main__':main()
