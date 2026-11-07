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

import mujoco
import numpy as np

from depth_io import save as save_depth
from ftir_hand import initialize
from isolation import prepare
from observations import robot_joints
from world import build, HERE


def run(out,duration=40,timestep=.002):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise ValueError('Use a new empty press attempt directory')
    snapshot=out/'source_snapshot';snapshot.mkdir();pins={}
    for path in HERE.glob('*.py'):
        shutil.copyfile(path,snapshot/path.name);pins[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    path=build(out,timestep=timestep,tray=False,laboratory=True,articulated_ftir=True,
               refined_thumb_contacts=True,sole_contact_time_constant=.004)
    control=build(out/'controller_model',timestep=timestep,tray=False,laboratory=True,map_only=True,
                  refined_thumb_contacts=True,sole_contact_time_constant=.004)
    model=mujoco.MjModel.from_xml_path(str(path));data=initialize(model)
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
    initial_xy=[5.95,-5.55]
    (out/'staging.json').write_text(json.dumps(dict(robot_map_xy_prior_m=initial_xy,
        initial_qpos=data.qpos.tolist(),scope='Authored robot pose at the FTIR station, not executed walking/preparation',
        target_instruction='Press BACKGROUND with the right index finger and retract',
        cameras='Native head RGB/depth profiles, ideal rendering and uncalibrated nominal source extrinsics'),indent=2)+'\n')
    command=[sys.executable,str(HERE/'ftir_actor.py'),'--model',str(control),'--initial-xy',*map(str,initial_xy)]
    command,environment,receipt=prepare(out,control,command,extra_modules=['ftir_actor.py','ftir_hand.py','ftir_vision.py'])
    log=open(out/'actor_stderr.log','w');process=subprocess.Popen(command,env=environment,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,close_fds=True)
    depth_renderer=mujoco.Renderer(model,height=180,width=320,max_geom=model.ngeom+1000);depth_renderer.enable_depth_rendering()
    color_renderer=mujoco.Renderer(model,height=360,width=640,max_geom=model.ngeom+1000)
    option=mujoco.MjvOption();option.geomgroup[3]=0;option.sitegroup[:]=0
    names=[model.joint(j).name for j in robot_joints(model)]
    records=[];sensors=[];depths=[];colors=[];responses=[];response={};failure=None;complete_time=None
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
            pickle.dump(packet,process.stdin,protocol=5);process.stdin.flush();received=pickle.load(process.stdout)
            if received['error']:raise RuntimeError(received['error'])
            response=received;data.ctrl[:]=response['torque']
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
        if not response.get('policy_complete'):raise RuntimeError('Duration exhausted before press/return attempt ended')
        if response.get('policy_failure'):failure=response['policy_failure']
    except Exception as error:failure=str(error);print('failed',failure,flush=True)
    finally:
        process.stdin.close()
        try:process.wait(timeout=15)
        except subprocess.TimeoutExpired:process.kill();process.wait()
        log.close();depth_renderer.close();color_renderer.close()
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
    result=dict(status='failed' if failure else 'attempt_finished_pending_independent_switch_verification',failure=failure,
                simulated_seconds=float(data.time),physics_timestep_s=model.opt.timestep,source_sha256=pins,actor_entry_point='ftir_actor.py',
                model_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                actor_isolation_sha256=hashlib.sha256((out/'actor_isolation.json').read_bytes()).hexdigest(),
                actor_access_isolated=receipt['passed'],actor_input_fields=list(sensors[0])+['depth','rgb'] if sensors else [],
                actor_last_output={k:v for k,v in response.items() if k!='torque'},environment='existing_complete_laboratory',
                setup_credit=False,qualified_skill=False,qualified_paper_branch=False,
                scope='One observed BACKGROUND key press attempt from an authored stationary initial posture')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','failure','simulated_seconds']}),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--duration',type=float,default=40)
    p.add_argument('--timestep',type=float,choices=[.001,.002],default=.002);a=p.parse_args()
    if run(a.out,a.duration,a.timestep)['status']=='failed':raise SystemExit(1)
