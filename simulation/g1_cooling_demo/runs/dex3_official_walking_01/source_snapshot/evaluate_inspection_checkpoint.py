"""Replay physical motion and native camera observations of an inspection probe.

This is a restored-state diagnostic, not a continuous pickup qualification.
The evaluator reconstructs camera calibration from robot sensors, reruns the
actor's appearance detector, and uses segmentation only to reject false tool
associations after inference. No evaluator data enters the controller.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time

import mujoco
import numpy as np
import trimesh

from observations import StateEstimate, robot_joints
from tool_cameras import ToolCameras
from tool_observation import detect


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def pose(obj):
    T=np.eye(4);T[:3,:3]=obj.xmat.reshape(3,3);T[:3,3]=obj.xpos
    return T


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['diagnostic','actor_run','source_recording','output']:
        p.add_argument(name,type=Path)
    a=p.parse_args();run,actor,source,out=[getattr(a,k).resolve() for k in
        ['diagnostic','actor_run','source_recording','output']]
    result=json.loads((run/'result.json').read_text())
    contract=json.loads((actor/'contract.json').read_text())
    isolation=json.loads((actor/'actor_isolation.json').read_text())
    original=json.loads((source/'result.json').read_text())
    assert contract['task']=='pickup_inspect_replace_release'
    assert result['actor_contract_sha256']==sha(actor/'contract.json')
    assert result['trace_sha256']==sha(run/'trace.npz')
    assert contract['model_sha256']==sha(actor/'world.xml')
    assert result['source_result_sha256']==sha(source/'result.json')
    assert original['trace_sha256']==sha(source/'trace.npz')
    assert isolation['passed']
    helper_names=['observations.py','tool_observation.py','tool_cameras.py','sensor_rendering.py']
    use_held_detector=contract['tool_inspection_contract'].get('held_observation_method')=='depth_with_own_robot_surface_exclusion'
    if use_held_detector:helper_names+=['held_tool_observation.py','tool_pose.py','robot_source_meshes.py']
    for name in helper_names:
        assert sha(Path(__file__).with_name(name))==isolation['source_modules'][name]
    trace=dict(np.load(run/'trace.npz'))
    with np.load(source/'trace.npz') as original_trace:
        k=int(np.argmin(abs(original_trace['time']-trace['time'][0])))
        warm=original_trace['qacc_warmstart'][k].copy()
    m=mujoco.MjModel.from_xml_path(str(actor/'world.xml'));d=mujoco.MjData(m)
    d.qpos[:]=trace['qpos'][0];d.qvel[:]=trace['qvel'][0];d.time=float(trace['time'][0])
    mujoco.mj_forward(m,d);d.qacc_warmstart[:]=warm
    dt=float(m.opt.timestep);stride=round(.001/dt)
    assert np.max(abs(np.diff(trace['time'])-.001))<1e-8
    prior=json.loads((actor/'actor_bundle/model/policy/tool_prior.json').read_text())
    pm=mujoco.MjModel.from_xml_path(str(actor/'actor_bundle/model/world.xml'))
    pd=mujoco.MjData(pm);pd.qpos[:]=prior['initial_robot_qpos'];mujoco.mj_forward(pm,pd)
    estimate=StateEstimate(pm,pd)
    mesh_path=actor/'actor_bundle/model/known_objects/tool_shape.glb'
    assert sha(mesh_path)==prior['tool_shape_sha256']
    mesh=trimesh.load(mesh_path,force='scene',process=False).to_geometry()
    held_detector=None
    if use_held_detector:
        from held_tool_observation import HeldToolObservation
        from robot_source_meshes import robot_source_meshes
        robot_meshes=robot_source_meshes(pm,visual_groups=(1,2))
        held_detector=HeldToolObservation(mesh,robot_meshes)
    names=[m.joint(j).name for j in robot_joints(m)]
    robot,tool={m.body('pelvis').id},{m.body('tweezer').id}
    for b in range(m.nbody):
        if m.body_parentid[b] in robot:robot.add(b)
        if m.body_parentid[b] in tool:tool.add(b)
    allowed={m.body(n).id for n in contract['allowed_tool_contact_bodies']}
    tray=m.body('carrier_tray').id;limits=contract['physical_acceptance']
    imported=json.loads((actor/'laboratory_import.json').read_text())
    floor={p['geom'] for p in imported['parts'] if p['source_part'] in
        {'indoor_floor','annex_floor','outdoor_floor','outdoor_access_path'}}
    bench={p['geom'] for p in imported['parts'] if p['source_part']=='ftir_bench_worktop'}
    events=json.loads((run/'events.json').read_text())
    phases=[e for e in events if 'phase' in e]
    times=np.array([e['time_s'] for e in phases])
    observations={round(e['time_s'],6):e['report'] for e in events if e.get('kind')=='held_tool_observation'}
    frames=json.loads((run/'camera_index.json').read_text()) if (run/'camera_index.json').exists() else []
    if frames:assert sha(run/'camera_index.json')==result['camera_index_sha256']
    frame_by_time={round(f['time_s'],6):f for f in frames}
    cameras=ToolCameras(m);old=m.vis.quality.offsamples;m.vis.quality.offsamples=0
    segment=mujoco.Renderer(m,height=480,width=640,max_geom=m.ngeom+1000)
    m.vis.quality.offsamples=old;segment.enable_segmentation_rendering()
    tool_geoms=np.flatnonzero(np.isin(m.geom_bodyid,list(tool)))
    qa=m.jnt_qposadr[m.actuator_trnid[:,0]];ranges=m.jnt_range[m.actuator_trnid[:,0]]
    max_q=max_v=max_rgb=max_depth=max_force=max_other=max_joint=0.
    contacts=[];rows=[];loaded_s=0.;held_inspection_s=0.;external=False;warnings=False
    out.mkdir(parents=True,exist_ok=False)
    for name in [Path(__file__).name,*helper_names]:
        shutil.copyfile(Path(__file__).with_name(name),out/name)
    started=time.monotonic()
    try:
        for i,t in enumerate(trace['time']):
            max_q=max(max_q,float(np.max(abs(d.qpos-trace['qpos'][i]))))
            max_v=max(max_v,float(np.max(abs(d.qvel-trace['qvel'][i]))))
            frame_record=frame_by_time.get(round(float(t),6))
            if frame_record is not None:
                path=run/frame_record['file'];assert sha(path)==frame_record['sha256']
                actual=cameras.read(d)
                with np.load(path) as saved:
                    rgb_error=int(np.max(abs(actual['head_rgb'].astype(int)-saved['head_rgb'].astype(int))))
                    depth_identical=bool(np.array_equal(actual['head_depth'],saved['head_depth']))
                    depth_error=0. if depth_identical else float(np.max(abs(actual['head_depth']-saved['head_depth'])))
                    if not np.isfinite(depth_error):depth_error=float('inf')
                max_rgb=max(max_rgb,rgb_error);max_depth=max(max_depth,depth_error)
                segment.update_scene(d,camera='head_depth',scene_option=cameras.option)
                seg=segment.render().copy()
                tool_mask=np.isin(seg[:,:,0],tool_geoms)&(seg[:,:,1]==int(mujoco.mjtObj.mjOBJ_GEOM))
                row=dict(time_s=float(t),rgb_error=rgb_error,depth_error_m=depth_error,
                         depth_identical=depth_identical,
                         visible_tool_depth_pixels=int(tool_mask.sum()),actor_inspected=round(float(t),6) in observations)
                if row['actor_inspected']:
                    estimate.update(dict(time_s=float(d.time),
                        joint_position=np.array([d.sensor(n+'_encoder').data[0] for n in names]),
                        joint_velocity=np.array([d.sensor(n+'_velocity').data[0] for n in names]),
                        imu_quaternion=d.sensor('imu_orientation').data.copy(),
                        imu_gyro=d.sensor('imu_angular_velocity').data.copy(),depth=None))
                    calibration=[]
                    for name in ['head_depth','head_rgb']:
                        cid=pm.camera(name).id;T=np.eye(4)
                        T[:3,:3]=pd.cam_xmat[cid].reshape(3,3);T[:3,3]=pd.cam_xpos[cid]
                        calibration.append((T,float(pm.cam_fovy[cid])))
                    (D,df),(C,cf)=calibration
                    expected=pose(pd.site('right_wrist_reference'))@np.linalg.inv(prior['grasp_geometry']['source_tool_from_wrist'])
                    points=mesh.vertices@expected[:3,:3].T+expected[:3,3]
                    bounds=[points.min(0)-.02,points.max(0)+.02]
                    if held_detector is not None:
                        proposal,component,pixels=held_detector.detect(actual['head_depth'],D,df,expected,
                            {name:pose(pd.body(name)) for name in robot_meshes})
                    else:
                        proposal,component=detect(actual['head_rgb'],actual['head_depth'],D,C,df,cf,bounds,prior['appearance_threshold_uint8'])
                    association=0.
                    if len(component):
                        if held_detector is not None:
                            v,u=pixels.T
                        else:
                            local=(component-D[:3,3])@D[:3,:3];z=-local[:,2]
                            fy=480/(2*np.tan(np.deg2rad(df/2)))
                            u=np.rint(320-.5+fy*local[:,0]/z).astype(int)
                            v=np.rint(240-.5-fy*local[:,1]/z).astype(int)
                        assert np.all((u>=0)&(u<640)&(v>=0)&(v<480))
                        association=float(tool_mask[v,u].mean())
                    recorded=observations[round(float(t),6)]
                    row.update(candidate_found=proposal['candidate_found'],component_points=len(component),
                        true_tool_fraction=association,
                        detector_record_matches=(proposal==recorded['proposal'] and len(component)==recorded['component_points']),
                        segmentation_supplied_to_detector=False)
                rows.append(row)
            if i==len(trace['time'])-1:break
            phase=phases[max(0,int(np.searchsorted(times,float(t),side='right')-1))]['phase']
            d.ctrl[:]=trace['ctrl'][i]
            for _ in range(stride):
                mujoco.mj_step(m,d)
                external |= bool(np.any(d.xfrc_applied) or np.any(d.qfrc_applied))
                warnings |= bool(np.any(d.warning.number))
                max_joint=max(max_joint,float(np.max(np.maximum(ranges[:,0]-d.qpos[qa],d.qpos[qa]-ranges[:,1]))))
                forces={'thumb':0.,'index':0.,'middle':0.};other=0.
                for ci,c in enumerate(d.contact):
                    bs={int(m.geom_bodyid[g]) for g in c.geom};gn=[m.geom(int(g)).name for g in c.geom]
                    if not bs&(robot|tool|{tray}):continue
                    load=np.zeros(6);mujoco.mj_contactForce(m,d,ci,load)
                    normal=max(0.,float(load[0]))
                    if len(bs&tool)==1 and bs&allowed:
                        body=m.body(next(iter(bs&allowed))).name
                        forces[next(n for n in forces if n in body)]+=normal
                        bound=limits['maximum_hand_tool_penetration_m']
                    elif bs&tool and (tray in bs or set(gn)&bench):
                        bound=limits['maximum_passive_support_penetration_m']
                    elif tray in bs and set(gn)&bench:bound=limits['maximum_passive_support_penetration_m']
                    elif any('ankle_roll_link_collision' in n for n in gn) and set(gn)&floor:
                        bound=limits['maximum_sole_penetration_m']
                    else:bound=limits['maximum_other_penetration_m']
                    if len(bs&tool)==1 and bs&robot and not bs&allowed:other+=normal
                    if c.dist < -bound and len(contacts)<30:
                        contacts.append(dict(time_s=float(d.time-dt),parts=gn,penetration_m=-float(c.dist),bound_m=bound))
                max_force=max(max_force,max(forces.values()));max_other=max(max_other,other)
                loaded=forces['thumb']>limits['minimum_thumb_load_n'] and min(forces['index'],forces['middle'])>limits['minimum_each_opposing_finger_load_n']
                if loaded:
                    loaded_s+=dt
                    if phase=='inspect_hold':held_inspection_s+=dt
            if i%500==0:print('replay',round(float(t),3),'wall_s',round(time.monotonic()-started,1),flush=True)
    finally:
        cameras.close();segment.close()
    inspected=[r for r in rows if r['actor_inspected']]
    associated=[r for r in inspected if r.get('candidate_found') and r['true_tool_fraction']>=.9]
    wanted=['inspect_move','inspect_hold','inspect_return','lower','release','withdraw','rest','finished']
    observed=[e['phase'] for e in phases if e['time_s']>=trace['time'][0] and e['phase']!='hold']
    spec=contract['tool_inspection_contract']
    checks=dict(attempt_completed_without_error=result.get('failure') is None and result.get('last_phase')=='finished',
        inspection_and_return_sequence=observed==wanted,
        exact_continuation_replay=max(max_q,max_v)<=limits['maximum_replay_error'],
        exact_native_camera_replay=bool(rows) and max_rgb==0 and all(r['depth_identical'] for r in rows),
        independent_detector_replay=bool(inspected) and all(r['detector_record_matches'] for r in inspected),
        sufficient_observation_frames=len(inspected)>=spec['minimum_observation_frames'],
        sufficient_true_tool_detections=len(associated)>=spec['minimum_detected_frames'],
        retained_loaded_inspection=held_inspection_s>=limits['minimum_lift_hold_s'],
        original_contact_bounds=not contacts,
        bounded_finger_load=max_force<=limits['maximum_normal_force_n'],
        no_unintended_hand_tool_load=max_other<=limits['maximum_unintended_hand_tool_load_n'],
        original_source_joint_ranges=max_joint<=limits['maximum_source_joint_limit_excess_rad'],
        no_external_forces=not external,no_numerical_warnings=not warnings)
    report=dict(scope=__doc__,source_result_sha256=sha(run/'result.json'),actor_contract_sha256=sha(actor/'contract.json'),
        trace_sha256=result['trace_sha256'],source_sha256={p.name:sha(p) for p in out.glob('*.py')},
        checks=checks,passed_inspection_diagnostic=all(checks.values()),maximum_q_replay_error=max_q,
        maximum_v_replay_error=max_v,maximum_rgb_error=max_rgb,maximum_depth_error_m=max_depth,
        maximum_finger_force_n=max_force,maximum_unintended_hand_tool_load_n=max_other,
        maximum_source_joint_range_excess_rad=max_joint,three_finger_loaded_s=loaded_s,
        loaded_inspection_s=held_inspection_s,contact_failures=contacts,frames=rows,
        minimum_true_tool_association_fraction=.9,association_evaluator_only=True,
        continuous_pickup_qualification=False,controller_continuation_replay_verified=False,
        qualified_held_tool_inspection=False,qualified_paper_branch=False,qualified_tip_pose=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed_inspection_diagnostic'],failed_checks=[k for k,v in checks.items() if not v])))
    if not report['passed_inspection_diagnostic']:raise SystemExit(1)


if __name__=='__main__':main()
