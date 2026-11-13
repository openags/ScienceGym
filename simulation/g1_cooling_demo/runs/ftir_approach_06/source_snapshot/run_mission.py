"""Continuous laboratory approach, stationary handoff and tray manipulation."""
import argparse
import hashlib
import json
from pathlib import Path
import pickle
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
import yaml
from depth_io import save as save_depth
from isolation import prepare
from observations import robot_joints
from walking_actor import SDK_JOINTS
from world import build,initialize,HERE


def run(folder,duration=110,registered=False,pose_aware=False):
    folder=Path(folder).resolve();folder.mkdir(parents=True,exist_ok=True)
    if any(folder.iterdir()):raise ValueError('Use a new empty mission directory')
    snapshots=folder/'source_snapshot';snapshots.mkdir();pins={}
    for path in HERE.glob('*.py'):
        shutil.copyfile(path,snapshots/path.name);pins[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    policy=HERE/'locomotion_policy';shutil.copytree(policy,folder/'policy_source')
    model_path=build(folder,laboratory=True,tray=True,payload='spatula')
    control_path=build(folder/'controller_model',laboratory=True,tray=False,map_only=True)
    for path in [model_path,control_path]:
        xml=ET.parse(path)
        for node in xml.findall('.//joint'):
            if node.get('name') in SDK_JOINTS:node.set('armature','.01')
        xml.write(path,encoding='unicode')
    model=mujoco.MjModel.from_xml_path(str(model_path));data=initialize(model)
    initial_xy=[-.9,0.];data.qpos[:2]=initial_xy
    cfg=yaml.safe_load((policy/'deploy.yaml').read_text());initial=np.empty(29)
    initial[cfg['joint_ids_map']]=cfg['default_joint_pos']
    for name,value in zip(SDK_JOINTS,initial):data.joint(name).qpos[0]=value
    mujoco.mj_forward(model,data);data.qpos[2]-=min(data.site(s+'_sole').xpos[2] for s in ['left','right']);mujoco.mj_forward(model,data)
    staging=dict(initial_qpos=data.qpos.tolist(),initial_map_xy_prior_m=initial_xy,
                 laboratory_xy_m=[3.7,1.12],laboratory_yaw_rad=float(np.pi/2),
                 goal='White assembly bench approach, then depth-localized tray transport and return',
                 setup_scope='Authored initial placement; spatula preloaded; no execution credit for setup')
    (folder/'staging.json').write_text(json.dumps(staging,indent=2)+'\n')
    imported=json.loads((folder/'laboratory_import.json').read_text())
    imported['initial_staging'][0]=dict(instance='g1',laboratory_xy_m=[3.7,1.12],yaw_rad=float(np.pi/2),basis=staging['setup_scope'])
    (folder/'laboratory_import.json').write_text(json.dumps(imported,indent=2)+'\n')
    adaptation=dict(source='Pinned UNITREE_G1_29DOF_CFG training configuration',body_joint_rotor_inertia_kg_m2=.01,body_inertias_unchanged=True,hand_rotor_inertias_unchanged=True)
    (folder/'actuator_adaptation.json').write_text(json.dumps(adaptation,indent=2)+'\n')
    actor_script='pose_mission_actor.py' if pose_aware else 'registered_mission_actor.py' if registered else 'mission_actor.py'
    command=[sys.executable,str(HERE/actor_script),'--model',str(control_path),'--initial-xy',*map(str,initial_xy)]
    modules=['walking_actor.py','odometry.py','mission_actor.py']
    if registered or pose_aware:modules+=['registered_mission_actor.py','map_localization.py']
    shape_files=[]
    if pose_aware:
        import trimesh
        modules+=['pose_mission_actor.py','pose_tracking.py','pose_policy.py','tray_pose.py']
        source=HERE.parents[1]/'assets/cooling_lab_v1/geometry/buerkle_4208_0022.glb'
        shape=trimesh.load(source,force='scene').to_geometry();prior=folder/'object_shape_source';prior.mkdir()
        target=prior/'tray_geometry.npz';np.savez_compressed(target,vertices=shape.vertices,faces=shape.faces);shape_files=[target]
        (folder/'shape_prior.json').write_text(json.dumps(dict(asset=str(source.relative_to(HERE.parents[1])),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),array_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),contains_placement=False,contains_runtime_state=False),indent=2)+'\n')
    command,environment,receipt=prepare(folder,control_path,command,extra_modules=modules,policy_files=[policy/'deploy.yaml',policy/'policy.onnx'],shape_files=shape_files)
    error_log=open(folder/'actor_stderr.log','w')
    process=subprocess.Popen(command,env=environment,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=error_log,close_fds=True)
    renderer=mujoco.Renderer(model,height=180,width=320,max_geom=max(10000,model.ngeom+1000));renderer.enable_depth_rendering()
    option=mujoco.MjvOption();option.geomgroup[3]=0;option.sitegroup[:]=0
    joints=[model.joint(j).name for j in robot_joints(model)]
    records=[];sensors=[];depths=[];observations=[];estimates=[];response={};failure=None;complete_time=None
    started=time.monotonic()
    try:
        for i in range(round(duration/model.opt.timestep)):
            depth=None
            if i%50==0:
                renderer.update_scene(data,camera='head_depth',scene_option=option);depth=renderer.render().copy();depths.append((float(data.time),depth))
            packet=dict(time_s=float(data.time),joint_position=np.array([data.sensor(n+'_encoder').data[0] for n in joints]),
                        joint_velocity=np.array([data.sensor(n+'_velocity').data[0] for n in joints]),imu_quaternion=data.sensor('imu_orientation').data.copy(),
                        imu_gyro=data.sensor('imu_angular_velocity').data.copy(),depth=depth)
            pickle.dump(packet,process.stdin,protocol=5);process.stdin.flush();received=pickle.load(process.stdout)
            if received['error']:raise RuntimeError(received['error'])
            response=received;data.ctrl[:]=response['torque']
            records.append((float(data.time),data.qpos.copy(),data.qvel.copy(),data.ctrl.copy(),data.qacc_warmstart.copy()))
            sensors.append({k:v for k,v in packet.items() if k!='depth'})
            if i%5==0:estimates.append(dict(time_s=float(data.time),estimated_root_position_m=response['estimated_root_position_m'],mission_stage=response['mission_stage']))
            if response['depth_observation'] is not None:
                observations.append(dict(time_s=float(data.time),state=response['policy_state'],phase=response['policy_phase'],observation=response['depth_observation'],capture_time_s=response['depth_capture_time_s']))
            if response['policy_complete']:
                if complete_time is None:complete_time=float(data.time)
                if data.time-complete_time>8:break
            mujoco.mj_step(model,data)
            if not np.isfinite(data.qpos).all() or np.any(data.warning.number):raise RuntimeError('Physics numerical failure')
            if data.qpos[2]<.6 or data.xmat[model.body('pelvis').id].reshape(3,3)[2,2]<.85:raise RuntimeError('Body support lost')
            if i%500==0:print('mission',round(float(data.time),3),response['mission_stage'],response['policy_state'],'root',np.round(data.qpos[:3],3).tolist(),'wall_s',round(time.monotonic()-started,1),flush=True)
        if not response.get('policy_complete'):raise RuntimeError('Duration exhausted before task completion')
    except Exception as error:failure=str(error);print('failed',failure,flush=True)
    finally:
        process.stdin.close()
        try:process.wait(timeout=15)
        except subprocess.TimeoutExpired:process.kill();process.wait()
        error_log.close();renderer.close()
    if not records or abs(records[-1][0]-data.time)>1e-12:
        records.append((float(data.time),data.qpos.copy(),data.qvel.copy(),data.ctrl.copy(),data.qacc_warmstart.copy()))
    np.savez_compressed(folder/'trace.npz',**{key:np.array([r[i] for r in records]) for i,key in enumerate(['time','qpos','qvel','ctrl','qacc_warmstart'])})
    if sensors:np.savez_compressed(folder/'sensor_observations.npz',**{key:np.array([r[key] for r in sensors]) for key in sensors[0]})
    if depths:save_depth(folder,depths)
    (folder/'policy_observations.json').write_text(json.dumps(observations,indent=2)+'\n')
    (folder/'actor_pose_estimates.json').write_text(json.dumps(estimates,indent=2)+'\n')
    result=dict(status='failed' if failure else 'completed',failure=failure,simulated_seconds=float(data.time),
                environment='existing_complete_laboratory',mission='approach_and_tray',actor_process_separate=True,actor_access_isolated=receipt['passed'],
                actor_isolation_sha256=hashlib.sha256((folder/'actor_isolation.json').read_bytes()).hexdigest(),actor_entry_point=actor_script,
                source_sha256=pins,actor_input_fields=list(sensors[0])+['depth'] if sensors else [],
                actor_last_output={k:v for k,v in response.items() if k!='torque'},return_to_source=True,payload_present=True,payload_kind='spatula',
                actuator_adaptation=adaptation,whole_paper_validated=False,qualified_skill=False,
                scope='Continuous bench approach and tray transport, with initial map-pose prior and inferred stance; no full-paper or reliability qualification')
    (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],failure=failure,simulated_seconds=result['simulated_seconds'],last_policy=response.get('policy_state'))),flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--duration',type=float,default=110);parser.add_argument('--registered',action='store_true');parser.add_argument('--pose-aware',action='store_true');args=parser.parse_args()
    if run(args.out,args.duration,args.registered,args.pose_aware)['status']!='completed':raise SystemExit(1)
