"""Evaluate the coupon pose actually reported by an isolated recorded actor.

Native object state is used only by this offline evaluator. It checks the first
four-frame accepted pose and observation gate, then reports later object drift
separately. It does not validate sample handling or replace full physics and
controller replay. The future sample operation must obtain fresh observations.
"""
import argparse
import json
from pathlib import Path
import pickle
import shutil

import mujoco
import numpy as np

from build_tool_station import sha
from runtime_collision_plugins import load_collision_plugins


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    run,out=a.run.resolve(),a.output.resolve()
    result=json.loads((run/'result.json').read_text());contract=json.loads((run/'contract.json').read_text())
    assert contract['observed_optical_coupon_required_before_approach']
    assert sha(run/'contract.json')==result['contract_sha256']
    for name in ['trace','sensors']:
        assert sha(run/(name+'.npz'))==result[name+'_sha256']
    assert sha(run/'responses.pkl')==result['responses_sha256']
    assert sha(run/'camera_index.json')==result['camera_index_sha256']
    assert sha(run/'world.xml')==contract['model_sha256']
    index=json.loads((run/'camera_index.json').read_text())
    with np.load(run/'sensors.npz') as z:
        times=z['time_s'].copy();frame_ids=z['camera_frame_id'].copy()
    responses=pickle.loads((run/'responses.pkl').read_bytes())
    assert len(responses)==len(times)
    first=next(i for i,r in enumerate(responses) if r.get('observed_optical_coupon') is not None)
    accepted=responses[first]['observed_optical_coupon']
    frames=np.flatnonzero(frame_ids[:first+1]>=0)[-4:]
    assert len(frames)==4 and accepted['observed_frames']==4
    assert all(responses[i]['latest_optical_coupon_report']['candidate_found'] for i in frames)
    for i in frames:
        record=index[int(frame_ids[i])]
        assert abs(record['time_s']-float(times[i]))<1e-9
        assert sha(run/record['file'])==record['sha256']
    out.mkdir(parents=True,exist_ok=False)
    for name in [Path(__file__).name,'build_tool_station.py','runtime_collision_plugins.py']:
        shutil.copyfile(Path(__file__).with_name(name),out/name)
    load_collision_plugins(contract.get('collision_plugins',[]))
    m=mujoco.MjModel.from_xml_path(str(run/'world.xml'));d=mujoco.MjData(m)
    gid=m.geom('optical_copper_witness').id;mid=m.geom_dataid[gid]
    vertices=m.mesh_vert[m.mesh_vertadr[mid]:m.mesh_vertadr[mid]+m.mesh_vertnum[mid]].copy()
    body=m.body('optical_witness_white').id;camera=m.camera('head_depth').id
    requested=[float(times[i]) for i in frames]+[float(times[first]),float(times[-1])]
    with np.load(run/'trace.npz') as z:
        trace_times=z['time'];ids=[int(np.argmin(abs(trace_times-t))) for t in requested]
        assert max(abs(trace_times[i]-t) for i,t in zip(ids,requested))<1e-8
        states=z['qpos'][ids].copy()
    def truth(q):
        d.qpos[:]=q;mujoco.mj_forward(m,d)
        points=vertices@d.geom_xmat[gid].reshape(3,3).T+d.geom_xpos[gid]
        center=(points.min(axis=0)+points.max(axis=0))/2
        normal=d.xmat[body].reshape(3,3)[:,2].copy()
        if normal@(d.cam_xpos[camera]-center)<0:normal=-normal
        return center,normal
    rows=[]
    for q,i in zip(states[:4],frames):
        center,normal=truth(q);observed=responses[i]['latest_optical_coupon_report']['candidate']
        rows.append(dict(time_s=float(times[i]),frame_id=int(frame_ids[i]),
            center_error_m=float(np.linalg.norm(np.asarray(observed['center_m'])-center)),
            normal_error_rad=float(np.arccos(np.clip(np.asarray(observed['normal_toward_camera'])@normal,-1.,1.)))))
    center,normal=truth(states[-2]);final_center,final_normal=truth(states[-1])
    error=float(np.linalg.norm(np.asarray(accepted['center_m'])-center))
    angle=float(np.arccos(np.clip(np.asarray(accepted['normal_toward_camera'])@normal,-1.,1.)))
    first_approach=next(i for i,r in enumerate(responses) if r['phase']=='approach')
    checks=dict(four_native_frames=all(frame_ids[i]>=0 for i in frames),
        approach_waited_for_pose=first_approach>=first,
        accepted_center_within_one_millimetre=error<=.001,
        accepted_normal_within_five_degrees=angle<=np.deg2rad(5),
        no_unobserved_yaw_or_coating_claim=not accepted['yaw_observable'] and not accepted['coating_side_observed'])
    report=dict(scope=__doc__,checks={k:bool(v) for k,v in checks.items()},
        passed_initial_runtime_observation=bool(all(checks.values())),
        first_accepted_time_s=float(times[first]),first_approach_time_s=float(times[first_approach]),
        accepted_pose=accepted,accepted_center_error_m=error,accepted_normal_error_rad=angle,
        observed_frame_diagnostics=rows,
        source_center_at_acceptance_m=center.tolist(),source_normal_at_acceptance=normal.tolist(),
        later_object_center_drift_m=float(np.linalg.norm(final_center-center)),
        later_object_normal_drift_rad=float(np.arccos(np.clip(final_normal@normal,-1.,1.))),
        final_time_s=float(times[-1]),later_pose_tracking_qualified=False,
        result_sha256=sha(run/'result.json'),contract_sha256=sha(run/'contract.json'),
        trace_sha256=result['trace_sha256'],responses_sha256=result['responses_sha256'],
        camera_index_sha256=result['camera_index_sha256'],
        source_sha256={p.name:sha(p) for p in out.glob('*.py')},
        full_controller_and_physics_replay_required=True,qualified_robot_handling=False,
        qualified_paper_branch=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
    if not report['passed_initial_runtime_observation']:raise SystemExit(1)


if __name__=='__main__':main()
