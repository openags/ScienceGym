"""Record every attempted G1 contact rollout, including failed attempts."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse,json,time,pickle,subprocess,sys,shutil,hashlib
from pathlib import Path
import numpy as np
import mujoco
from scipy.spatial.transform import Rotation
from world import build,initialize,HERE
from balance import Balance


def run(out,duration=5,tray=False,sensor_actor=False):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise ValueError('Use a new attempt directory')
    snapshot=out/'source_snapshot';snapshot.mkdir()
    pins={}
    for source in HERE.glob('*.py'):
        shutil.copy2(source,snapshot/source.name);pins[source.name]=hashlib.sha256(source.read_bytes()).hexdigest()
    path=build(out,tray=tray);m=mujoco.MjModel.from_xml_path(str(path));d=initialize(m)
    # Controller model contains only robot DOFs. Environment state is kept out
    # of its data structure; sensor transport is added separately.
    control_path=build(out/'controller_model',tray=False);cm=mujoco.MjModel.from_xml_path(str(control_path));cd=initialize(cm)
    control=Balance(cm,cd);zero=mujoco.MjData(cm);mujoco.mj_forward(cm,zero)
    control.palm_rotations={s:Rotation.from_euler('x',-45 if s=='left' else 45,degrees=True).as_matrix()@zero.site(s+'_wrist_reference').xmat.reshape(3,3) for s in ['left','right']}
    begin={s:cd.site(s+'_wrist_reference').xpos.copy() for s in ['left','right']}
    process=None;depth_renderer=None;sensor_records=[];last_actor=None;depth_frames=[]
    joints=[j for j in range(m.njnt) if m.jnt_type[j]==mujoco.mjtJoint.mjJNT_HINGE]
    if sensor_actor:
        process=subprocess.Popen([sys.executable,str(HERE/'actor.py'),'--model',str(control_path)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=open(out/'actor_stderr.log','w'))
        depth_renderer=mujoco.Renderer(m,height=180,width=320);depth_renderer.enable_depth_rendering()
        render_option=mujoco.MjvOption();render_option.geomgroup[3]=0;render_option.sitegroup[:]=0
    records=[];failure=None;events=[];start=time.monotonic()
    def event(name):events.append(dict(name=name,time_s=float(d.time)));print(name,round(d.time,3),flush=True)
    event('initial')
    try:
        for i in range(round(duration/m.opt.timestep)):
            if i%5==0:
                if sensor_actor:
                    depth=None
                    if i%50==0:
                        depth_renderer.update_scene(d,camera='head_depth',scene_option=render_option);depth=depth_renderer.render().copy();depth_frames.append((float(d.time),depth))
                    obs=dict(time_s=float(d.time),joint_position=np.array([d.sensor(m.joint(j).name+'_encoder').data[0] for j in joints]),
                        joint_velocity=np.array([d.sensor(m.joint(j).name+'_velocity').data[0] for j in joints]),
                        imu_quaternion=d.sensor('imu_orientation').data.copy(),imu_gyro=d.sensor('imu_angular_velocity').data.copy(),depth=depth)
                    pickle.dump(obs,process.stdin,protocol=5);process.stdin.flush();last_actor=pickle.load(process.stdout)
                    sensor_records.append({k:v for k,v in obs.items() if k!='depth'})
                    if last_actor['error']:raise RuntimeError('Sensor actor: '+last_actor['error'])
                    d.ctrl[:]=last_actor['torque']
                    records.append((float(d.time),d.qpos.copy(),d.qvel.copy(),d.ctrl.copy(),d.qacc_warmstart.copy()))
                    mujoco.mj_step(m,d)
                    if not np.isfinite(d.qpos).all() or np.any(d.warning.number):raise RuntimeError('Physics numerical failure')
                    if d.qpos[2]<.6 or np.linalg.norm(d.qpos[4:6])>.2:raise RuntimeError('Standing stability lost')
                    if i%500==0:print('sensor_step',i,'detections',last_actor['depth_detections'],'target',last_actor['observed_target'],flush=True)
                    continue
                cd.qpos[:]=d.qpos[:cm.nq];cd.qvel[:]=d.qvel[:cm.nv];mujoco.mj_forward(cm,cd)
                targets=None;forces=None
                if duration>5:
                    lift=np.clip((d.time-2)/3,0,1);lift=lift*lift*(3-2*lift)
                    forward=np.clip((d.time-6)/3,0,1);forward=forward*forward*(3-2*forward)
                    def ramp(start,end):
                        t=np.clip((d.time-start)/(end-start),0,1);return t*t*(3-2*t)
                    down=ramp(10,13);close=ramp(14,16);up=ramp(18,21);transfer=ramp(22,25);release_down=ramp(26,29);open_hand=ramp(30,32);retreat=ramp(33,36)
                    targets={s:begin[s]+np.array([(.51-begin[s][0])*forward-.025*transfer-(.51-begin[s][0])*retreat,
                        ((.20-abs(begin[s][1]))*lift-.052*close+.055*open_hand)* (1 if s=='left' else -1)+.06*transfer,
                        (1.04-begin[s][2])*lift-.110*down+.09*up-.09*release_down+.10*retreat]) for s in begin}
                    forces={s:[0,(-1 if s=='left' else 1)*15*close*(1-open_hand),0] for s in begin}
                d.ctrl[:]=control.torque(targets=targets,forces=forces)
                records.append((float(d.time),d.qpos.copy(),d.qvel.copy(),d.ctrl.copy(),d.qacc_warmstart.copy()))
            mujoco.mj_step(m,d)
            if not np.isfinite(d.qpos).all() or np.any(d.warning.number):raise RuntimeError('Physics numerical failure')
            if d.qpos[2]<.6:raise RuntimeError('Standing height lost')
            if np.linalg.norm(d.qpos[4:6])>.2:raise RuntimeError('Standing tilt lost')
            if i%500==0:print('step',i,'z',round(float(d.qpos[2]),4),'tray',np.round(d.body('carrier_tray').xpos,4).tolist() if tray else None,'wall',round(time.monotonic()-start,1),flush=True)
        event('finished')
    except Exception as e:failure=str(e);event('failed');print(failure,flush=True)
    if process:
        process.stdin.close();process.wait(timeout=15)
    if depth_renderer:depth_renderer.close()
    records.append((float(d.time),d.qpos.copy(),d.qvel.copy(),d.ctrl.copy(),d.qacc_warmstart.copy()))
    np.savez_compressed(out/'trace.npz',**{k:np.array([r[i] for r in records]) for i,k in enumerate(['time','qpos','qvel','ctrl','qacc_warmstart'])})
    if sensor_records:np.savez_compressed(out/'sensor_observations.npz',**{k:np.array([r[k] for r in sensor_records]) for k in sensor_records[0]})
    if depth_frames:np.savez_compressed(out/'head_depth.npz',time=np.array([r[0] for r in depth_frames]),depth=np.array([r[1] for r in depth_frames]))
    result=dict(status='completed' if failure is None else 'failed',failure=failure,simulated_seconds=float(d.time),wall_seconds=time.monotonic()-start,
        events=events,palm_positions={s:d.site(s+'_wrist_reference').xpos.tolist() for s in begin},maximum_qp_iterations=(last_actor or {}).get('maximum_qp_iterations',control.max_iter),
        sensor_isolation_qualified=False,manipulation_qualified=False,whole_paper_validated=False,
        scope='G1/Inspire floating-base contact development; simulator proprioception diagnostic, not sensor-only campaign qualification.')
    result.update(source_sha256=pins,actor_process_separate=sensor_actor,actor_last_output={k:v for k,v in (last_actor or {}).items() if k!='torque'},actor_input_fields=list(sensor_records[0])+['depth'] if sensor_records else [])
    if sensor_actor:result['scope']='Native head depth and encoder/IMU actor in a separate process; inferred sensor and contact parameters, fixed-foot state estimate; full task and sensor calibration not qualified.'
    if tray:
        qa=m.joint('tray_free').qposadr[0];trajectory=np.array([r[1][qa:qa+3] for r in records]);result['tray_motion']=dict(initial_m=trajectory[0].tolist(),final_m=trajectory[-1].tolist(),maximum_height_m=float(trajectory[:,2].max()),lift_detected=bool(trajectory[:,2].max()>trajectory[0,2]+.07))
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--duration',type=float,default=5);p.add_argument('--tray',action='store_true');p.add_argument('--sensor-actor',action='store_true');a=p.parse_args();run(a.out,a.duration,a.tray,a.sensor_actor)
