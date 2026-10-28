"""Run a floating G1 key-press attempt in the full lab, with an isolated actor."""
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

from depth_io import save as save_depth
from ftir_hand import initialize, initialize_cover
from ftir_slider_posture import initialize_slider
from isolation import prepare
from observations import robot_joints
from world import build, HERE


def run(out,duration=40,timestep=.002,operation='press',initial_xy=None,slider_prior=None,observe_slider_outcome=False,approach_from=None):
    if operation not in {'press','cover','slider_scan','slider'}:raise ValueError('Unknown FTIR operation')
    if slider_prior is not None and operation!='slider':raise ValueError('A slider prior requires the slider operation')
    if observe_slider_outcome and operation!='slider':raise ValueError('Window outcome observation requires the slider operation')
    walking=approach_from is not None
    if walking and not observe_slider_outcome:raise ValueError('Continuous approach requires observed slider completion')
    cover=operation=='cover'
    scan=operation=='slider_scan'
    slider=operation=='slider'
    touch=cover or slider
    actor_name='ftir_slider_actor.py' if slider else 'ftir_slider_scan_actor.py' if scan else 'ftir_cover_actor.py' if cover else 'ftir_actor.py'
    if observe_slider_outcome:actor_name='ftir_slider_observed_actor.py'
    if walking:actor_name='ftir_approach_actor.py'
    initial_xy=([5.95,-5.20] if scan or slider else [5.95,-5.35] if cover else [5.95,-5.55]) if initial_xy is None else list(map(float,initial_xy))
    if len(initial_xy)!=2 or not np.isfinite(initial_xy).all():raise ValueError('Initial robot map XY must contain two finite values')
    start_xy=list(map(float,approach_from)) if walking else initial_xy
    if len(start_xy)!=2 or not np.isfinite(start_xy).all():raise ValueError('Walking start XY must contain two finite values')
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise ValueError('Use a new empty FTIR attempt directory')
    snapshot=out/'source_snapshot';snapshot.mkdir();pins={}
    for path in HERE.glob('*.py'):
        shutil.copyfile(path,snapshot/path.name);pins[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    path=build(out,timestep=timestep,tray=False,laboratory=True,articulated_ftir=True,
               refined_thumb_contacts=True,sole_contact_time_constant=.004,hand_touch=touch,refined_distal_contacts=cover)
    control=build(out/'controller_model',timestep=timestep,tray=False,laboratory=True,map_only=True,
                  refined_thumb_contacts=True,sole_contact_time_constant=.004,hand_touch=touch)
    if cover or scan or slider:
        # State estimation, arm IK and the balance QP use robot kinematics and
        # explicit body dynamics, never the predictor's contact solver. Keep
        # its source meshes compact; native tactile observations come from
        # the separately simulated full-resolution physical plant.
        predictor=ET.parse(control);option=predictor.getroot().find('option')
        flag=option.find('flag')
        if flag is None:flag=ET.SubElement(option,'flag')
        flag.set('contact','disable');ET.indent(predictor);predictor.write(control,encoding='unicode')
        (out/'controller_model/profile.json').write_text(json.dumps(dict(
            collision_solver_used=False,source_body_dynamics_unchanged=True,physical_plant_contacts_disabled=False,
            hand_touch_available=touch,
            rationale='Robot state/IK/inverse-dynamics predictor; contact solving remains in the separate physical plant.',
            regression='simulation/g1_cooling_demo/analysis/ftir_predictor_contact_01/review.json'),indent=2)+'\n')
    if walking:
        from walking_actor import SDK_JOINTS
        import yaml
        for model_path in [path,control]:
            xml=ET.parse(model_path)
            for node in xml.findall('.//joint'):
                if node.get('name') in SDK_JOINTS:node.set('armature','.01')
            xml.write(model_path,encoding='unicode')
        (out/'actuator_adaptation.json').write_text(json.dumps(dict(
            body_joint_rotor_inertia_kg_m2=.01,body_inertias_unchanged=True,hand_rotor_inertias_unchanged=True,
            source='locomotion_policy/reference/training_models.py: UNITREE_G1_29DOF_CFG',
            scope='The pinned official velocity policy training parameter; not a manufacturer-measured hardware identification.'),indent=2)+'\n')
        profile_path=out/'controller_model/profile.json';profile=json.loads(profile_path.read_text())
        profile.update(source_body_dynamics_unchanged=False,published_training_rotor_inertia_applied=True,
                       actuator_adaptation='../actuator_adaptation.json')
        profile_path.write_text(json.dumps(profile,indent=2)+'\n')
    model=mujoco.MjModel.from_xml_path(str(path))
    if walking:
        data=mujoco.MjData(model);data.qpos[:2]=start_xy
        cfg=yaml.safe_load((HERE/'locomotion_policy/deploy.yaml').read_text())
        initial=np.empty(29);initial[cfg['joint_ids_map']]=cfg['default_joint_pos']
        for name,value in zip(SDK_JOINTS,initial):data.joint(name).qpos[0]=value
        from ftir_hand import mimic
        mimic(model,data);mujoco.mj_forward(model,data)
        data.qpos[2]-=min(data.site(s+'_sole').xpos[2] for s in ['left','right']);mujoco.mj_forward(model,data)
    else:
        data=(initialize_slider if scan or slider else initialize_cover if cover else initialize)(model,initial_xy)
    robot=set()
    for body in range(model.nbody):
        parent=body
        while parent and model.body(parent).name!='pelvis':parent=int(model.body_parentid[parent])
        if parent:robot.add(body)
    initial_contacts=[]
    for contact in data.contact:
        a,b=map(int,contact.geom); bodies=[int(model.geom_bodyid[g]) for g in [a,b]]
        if not any(body in robot for body in bodies) or contact.dist>=-1e-6:continue
        initial_contacts.append(dict(parts=[model.geom(a).name,model.geom(b).name],distance_m=float(contact.dist),
                                     self_contact=all(body in robot for body in bodies)))
    severe=any(not c['self_contact'] or c['distance_m']<-.001 for c in initial_contacts)
    (out/'initial_contact_review.json').write_text(json.dumps(dict(development_start_allowed=not severe,
        contact_free=not initial_contacts,contacts=initial_contacts,
        scope='Reject deep self intersections and any initial environment penetration. Smaller existing hand self contacts remain physical and unqualified.'),indent=2)+'\n')
    if severe:
        result=dict(status='failed',failure='Initial robot collision preflight rejected the setup',simulated_seconds=0.)
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return result
    import_path=out/'laboratory_import.json';imported=json.loads(import_path.read_text())
    lab_transform=np.asarray(imported['lab_from_work']);lab_position=lab_transform@np.r_[data.qpos[:3],1.]
    lab_rotation=lab_transform[:3,:3]@data.body('pelvis').xmat.reshape(3,3)
    imported['initial_staging']=[dict(instance='g1',laboratory_xy_m=lab_position[:2].tolist(),
        yaw_rad=float(np.arctan2(lab_rotation[1,0],lab_rotation[0,0])),
        basis='Authored initial aisle pose before continuous execution' if walking else 'Authored initial FTIR station pose; no walking credit')]
    import_path.write_text(json.dumps(imported,indent=2)+'\n')
    (out/'staging.json').write_text(json.dumps(dict(robot_map_xy_prior_m=start_xy,station_map_xy_goal_m=initial_xy,
        initial_qpos=data.qpos.tolist(),scope='Authored initial aisle pose; the subsequent approach and preparation are executed continuously' if walking else 'Authored robot pose at the FTIR station, not executed walking/preparation',
        target_instruction='Walk to the FTIR station, prepare and localize, push its window, withdraw, confirm its position from RGB-D and return' if walking else 'Observe, push the passive sliding window by 70 mm, withdraw, turn to observe its final position from fresh RGB-D, then return' if observe_slider_outcome else 'Observe, push the passive sliding window by 70 mm, withdraw and return' if slider else 'Observe the key row and turn the torso to the approach orientation' if scan else 'Grasp, open and release the cover with the right hand' if cover else 'Press BACKGROUND with the right index finger and retract',
        cameras='Native head RGB/depth profiles, ideal rendering and uncalibrated nominal source extrinsics'),indent=2)+'\n')
    command=[sys.executable,str(HERE/actor_name),'--model',str(control),'--initial-xy',*map(str,start_xy)]
    if walking:command.extend(['--station-xy',*map(str,initial_xy)])
    modules=['ftir_actor.py','ftir_hand.py','ftir_vision.py'];policies=[];shapes=[]
    if scan:modules.extend([actor_name,'ftir_slider_posture.py'])
    if touch:
        from hand_touch import read as read_touch
    if cover:
        modules.extend([actor_name,'ftir_cover_geometry.py'])
        (out/'policy_source').mkdir()
        prior=out/'policy_source/cover_grasp_prior.json'
        shutil.copyfile(HERE.parents[1]/'assets/nicolet_6700_mechanism_v1/cover_grasp_prior.json',prior)
        policies.append(prior)
    if slider:
        modules.extend(['ftir_slider_actor.py','ftir_slider_scan_actor.py','ftir_slider_posture.py',
                        'ftir_slider_planning.py','ftir_slider_vision.py','ftir_cover_geometry.py',
                        'robot_source_meshes.py','joint_rrt.py','source_proximity.py'])
        if observe_slider_outcome:modules.extend(['ftir_slider_observed_actor.py','ftir_slider_outcome.py'])
        (out/'policy_source').mkdir();(out/'object_shape_source').mkdir()
        prior=out/'policy_source/slider_push_prior.json'
        shape=out/'object_shape_source/nicolet_passive_dynamics.glb'
        root=HERE.parents[1]
        prior_source=root/'assets/nicolet_6700_mechanism_v1/slider_push_prior.json' if slider_prior is None else Path(slider_prior).resolve()
        shutil.copyfile(prior_source,prior)
        shutil.copyfile(root/'assets/nicolet_6700_mechanism_v1/revisions/passive_dynamics/geometry/nicolet_passive_dynamics.glb',shape)
        policies.append(prior);shapes.append(shape)
    if walking:
        modules.extend(['ftir_approach_actor.py','walking_actor.py','odometry.py','map_localization.py'])
        policy=out/'locomotion_policy_source';shutil.copytree(HERE/'locomotion_policy',policy)
        policies.extend([policy/'deploy.yaml',policy/'policy.onnx'])
    command,environment,receipt=prepare(out,control,command,extra_modules=modules,policy_files=policies,shape_files=shapes)
    log=open(out/'actor_stderr.log','w');process=subprocess.Popen(command,env=environment,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,close_fds=True)
    depth_height,depth_width=(360,640) if cover or scan or slider else (180,320)
    (out/'sensor_profile.json').write_text(json.dumps(dict(depth_resolution=[depth_width,depth_height],
        rgb_resolution=[640,360],delivered_frames_per_second=10,ideal_depth=True,extrinsics_calibrated=False,
        source='https://www.realsenseai.com/wp-content/uploads/2023/10/Intel-RealSense-D400-Series-Datasheet-September-2023.pdf',
        note='Head-mounted D435i nominal optics. Cover, window and torso-scan attempts use a supported 640x360 depth image size, sampled at 10 Hz. The older press profile uses a lower-resolution numerical render.'),indent=2)+'\n')
    depth_renderer=mujoco.Renderer(model,height=depth_height,width=depth_width,max_geom=model.ngeom+1000);depth_renderer.enable_depth_rendering()
    color_renderer=mujoco.Renderer(model,height=360,width=640,max_geom=model.ngeom+1000)
    option=mujoco.MjvOption();option.geomgroup[3]=0;option.sitegroup[:]=0
    names=[model.joint(j).name for j in robot_joints(model)]
    records=[];sensors=[];depths=[];colors=[];responses=[];response={};failure=None;complete_time=None
    monitor=open(out/'actor_monitor.jsonl','w') if cover or scan or slider else None
    started=time.monotonic()
    camera_every=round(.1/model.opt.timestep);response_every=round(.01/model.opt.timestep)
    try:
        for i in range(round(duration/model.opt.timestep)):
            depth,rgb=None,None
            if i%camera_every==0:
                depth_renderer.update_scene(data,camera='head_depth',scene_option=option);depth=depth_renderer.render().copy();depths.append((float(data.time),depth))
                color_renderer.update_scene(data,camera='head_rgb',scene_option=option);rgb=color_renderer.render().copy();colors.append((float(data.time),rgb))
            packet=dict(time_s=float(data.time),joint_position=np.array([data.sensor(n+'_encoder').data[0] for n in names]),
                        joint_velocity=np.array([data.sensor(n+'_velocity').data[0] for n in names]),
                        imu_quaternion=data.sensor('imu_orientation').data.copy(),imu_gyro=data.sensor('imu_angular_velocity').data.copy(),depth=depth,rgb=rgb)
            if touch:packet['right_touch_n']=read_touch(data)
            pickle.dump(packet,process.stdin,protocol=5);process.stdin.flush();received=pickle.load(process.stdout)
            if received['error']:raise RuntimeError(received['error'])
            response=received;data.ctrl[:]=response['torque']
            if monitor is not None and i%camera_every==0:
                monitor.write(json.dumps(dict(time_s=float(data.time),**{k:v for k,v in response.items()
                    if k in {'policy_state','policy_failure','touch','grip_control','wrist_load_compensation','grasp_contact_confirmed','commanded_pose'}}))+'\n');monitor.flush()
            records.append((float(data.time),data.qpos.copy(),data.qvel.copy(),data.ctrl.copy(),data.qacc_warmstart.copy()))
            sensors.append({k:v for k,v in packet.items() if k not in {'depth','rgb'}})
            if i%response_every==0:responses.append(dict(time_s=float(data.time),**{k:v for k,v in response.items() if k not in {'torque','events'}}))
            if response['policy_complete']:
                if complete_time is None:complete_time=float(data.time)
                if data.time-complete_time>5:break
            mujoco.mj_step(model,data)
            if not np.isfinite(data.qpos).all() or np.any(data.warning.number):raise RuntimeError('Physics numerical failure')
            if data.qpos[2]<.6 or data.body('pelvis').xmat.reshape(3,3)[2,2]<.85:raise RuntimeError('Body support lost')
            if i%round(1/model.opt.timestep)==0:print('ftir',round(float(data.time),3),response['policy_state'],'root',np.round(data.qpos[:3],3).tolist(),'wall_s',round(time.monotonic()-started,1),flush=True)
        if not response.get('policy_complete'):raise RuntimeError('Duration exhausted before '+operation+'/return attempt ended')
        if response.get('policy_failure'):failure=response['policy_failure']
    except Exception as error:failure=str(error);print('failed',failure,flush=True)
    finally:
        process.stdin.close()
        try:process.wait(timeout=15)
        except subprocess.TimeoutExpired:process.kill();process.wait()
        log.close();depth_renderer.close();color_renderer.close()
        if monitor is not None:monitor.close()
    if not records or abs(records[-1][0]-data.time)>1e-12:
        records.append((float(data.time),data.qpos.copy(),data.qvel.copy(),data.ctrl.copy(),data.qacc_warmstart.copy()))
    np.savez_compressed(out/'trace.npz',**{k:np.array([r[i] for r in records]) for i,k in enumerate(['time','qpos','qvel','ctrl','qacc_warmstart'])})
    if sensors:np.savez_compressed(out/'sensor_observations.npz',**{k:np.array([r[k] for r in sensors]) for k in sensors[0]})
    if depths:save_depth(out,depths)
    if colors:
        directory=out/'head_rgb_chunks';directory.mkdir();chunks=[]
        for start in range(0,len(colors),50):
            part=colors[start:start+50];filename=directory/f'{start:06d}.npz';np.savez_compressed(filename,time=np.array([r[0] for r in part]),rgb=np.array([r[1] for r in part]));chunks.append(dict(path=str(filename.relative_to(out)),frames=len(part),sha256=hashlib.sha256(filename.read_bytes()).hexdigest()))
        (out/'head_rgb_index.json').write_text(json.dumps(dict(camera='head_rgb',frames=len(colors),chunks=chunks),indent=2)+'\n')
    (out/'actor_responses.json').write_text(json.dumps(responses,indent=2)+'\n')
    result=dict(status='failed' if failure else 'attempt_finished_pending_independent_slider_verification' if slider else 'preparation_finished_pending_independent_verification' if scan else 'attempt_finished_pending_independent_cover_verification' if cover else 'attempt_finished_pending_independent_switch_verification',failure=failure,
                simulated_seconds=float(data.time),physics_timestep_s=model.opt.timestep,source_sha256=pins,actor_entry_point=actor_name,
                model_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                actor_isolation_sha256=hashlib.sha256((out/'actor_isolation.json').read_bytes()).hexdigest(),
                actor_access_isolated=receipt['passed'],actor_input_fields=list(sensors[0])+['depth','rgb'] if sensors else [],
                actor_last_output={k:v for k,v in response.items() if k!='torque'},environment='existing_complete_laboratory',
                requires_visual_outcome_confirmation=bool(observe_slider_outcome),
                requires_executed_station_approach=bool(walking),
                setup_credit=False,qualified_skill=False,qualified_paper_branch=False,
                scope='One continuous aisle approach, preparation, observed window push and return attempt; no carrying, complete experiment or qualification' if walking else 'One observed, tactile-gated sliding-window attempt from authored stationary setup' if slider else 'One RGB-D observation and torso preparation attempt; no walking, window manipulation or skill qualification' if scan else 'One tactile-gated cover opening attempt from an authored stationary initial posture' if cover else 'One observed BACKGROUND key press attempt from an authored stationary initial posture')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','failure','simulated_seconds']}),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--duration',type=float,default=40)
    p.add_argument('--timestep',type=float,choices=[.001,.002],default=.002);a=p.parse_args()
    if run(a.out,a.duration,a.timestep)['status']=='failed':raise SystemExit(1)
