"""Diagnose loaded control from an explicitly restored grasp checkpoint.

The frozen isolated actor first consumes every original sensor packet up to
the checkpoint. Physics then starts from a recorded held-tool state. This is
not a continuous pickup/carry recording, independent replay, or skill result.
The separate full run must execute its own pickup and carry without resets.
"""
import argparse
from collections import deque
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

from observations import robot_joints
from verify_tool_grasp import difference


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source_recording');p.add_argument('actor_run');p.add_argument('output')
    p.add_argument('--checkpoint-phase',choices=['close','lift','hold','carry_descend','lower'],default='lower')
    p.add_argument('--measure-prelift-native',action='store_true',
                   help='Record every native contact step in the final prelift window; evaluator only')
    p.add_argument('--diagnose-balance',action='store_true',
                   help='Retain a rejected actor-owned QP; diagnostic wrapper only')
    p.add_argument('--seconds',type=float,default=18.);a=p.parse_args()
    source,run,out=map(lambda x:Path(x).resolve(),[a.source_recording,a.actor_run,a.output])
    out.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(__file__,out/Path(__file__).name)
    contract=json.loads((run/'contract.json').read_text());receipt=json.loads((run/'actor_isolation.json').read_text())
    original=json.loads((source/'result.json').read_text())
    assert contract['task'] in {'visual_pickup_loaded_out_and_back_release','pickup_hold_replace_release','pickup_inspect_replace_release'} and receipt['passed']
    assert sha(run/'world.xml')==contract['model_sha256']==json.loads((source/'contract.json').read_text())['model_sha256']
    for f,key in [('trace.npz','trace_sha256'),('sensors.npz','sensors_sha256'),('responses.pkl','responses_sha256')]:
        assert sha(source/f)==original[key]
    for n,h in receipt['source_modules'].items():assert sha(run/'actor_bundle/code'/n)==h
    source_events=json.loads((source/'events.json').read_text())
    checkpoint=next(e['time_s'] for e in source_events if e.get('phase')==a.checkpoint_phase)
    sensors=dict(np.load(source/'sensors.npz'));index=json.loads((source/'camera_index.json').read_text())
    responses=pickle.loads((source/'responses.pkl').read_bytes())
    row=int(np.argmin(abs(sensors['time_s']-checkpoint)))
    report=dict(scope=__doc__,physical_execution=True,continuous_pickup_carry=False,qualified_carry=False,
        source_result_sha256=sha(source/'result.json'),actor_contract_sha256=sha(run/'contract.json'),
        script_sha256=sha(__file__),checkpoint_time_s=checkpoint,requested_continuation_s=a.seconds)
    report['checkpoint_phase']=a.checkpoint_phase
    report['native_prelift_measurement_requested']=a.measure_prelift_native
    (out/'contract.json').write_text(json.dumps(report,indent=2)+'\n')
    actor=contract['actor_module'];assert actor in {'carry_tool_actor','visual_tool_actor','inspection_tool_actor'}
    command=receipt['command_prefix']+[sys.executable,'/actor/'+actor+'.py','--model','/model/world.xml']
    if a.diagnose_balance:
        wrapper=Path(__file__).with_name('capture_balance_failure.py')
        shutil.copyfile(wrapper,out/wrapper.name)
        command=receipt['command_prefix']+[sys.executable,'-c',wrapper.read_text(),
                                           '--diagnostic-actor',actor,'--model','/model/world.xml']
        report['diagnostic_balance_wrapper_sha256']=sha(wrapper)
    failure=None;records=[];response={};started=time.monotonic();actuation_native=[]
    cameras=None;camera_records=[]
    with (out/'actor_stderr.log').open('wb') as stderr,(out/'monitor.jsonl').open('w') as monitor:
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,env=receipt['environment'])
        def ask(obs):
            pickle.dump(obs,process.stdin,protocol=5);process.stdin.flush()
            value=pickle.load(process.stdout)
            if value.get('error'):
                if a.diagnose_balance and 'diagnostic_balance_problem' in value:
                    problem=out/'rejected_balance_problem.npz'
                    np.savez_compressed(problem,**value['diagnostic_balance_problem'])
                    report['rejected_balance_problem']=dict(file=problem.name,sha256=sha(problem),
                        time_s=float(obs['time_s']),scope='Own-robot estimated balance QP; diagnostic only')
                raise RuntimeError(value['error'])
            return value
        try:
            prefix_error=0.
            for i in range(row):
                obs={k:v[i] for k,v in sensors.items()};frame=int(obs.pop('camera_frame_id'))
                if frame>=0:
                    r=index[frame];assert sha(source/r['file'])==r['sha256']
                    with np.load(source/r['file']) as camera:obs.update({k:camera[k] for k in camera.files})
                else:obs.update(head_rgb=None,head_depth=None)
                response=ask(obs)
                error=difference(responses[i],{k:response[k] for k in responses[i]})
                prefix_error=max(prefix_error,error)
                if error>1e-10:raise RuntimeError('Frozen pickup prefix differs at packet '+str(i))
                if i%10000==0:print('prefix_sensor_packets',i,'of',row,flush=True)
            report.update(prefix_packets_replayed=row,maximum_prefix_response_error=prefix_error)
            trace=np.load(source/'trace.npz');times=trace['time'];k=int(np.argmin(abs(times-checkpoint)))
            m=mujoco.MjModel.from_xml_path(str(run/'world.xml'));d=mujoco.MjData(m)
            q=trace['qpos'];v=trace['qvel'];w=trace['qacc_warmstart']
            d.qpos[:]=q[k];d.qvel[:]=v[k];d.time=float(times[k]);mujoco.mj_forward(m,d);d.qacc_warmstart[:]=w[k]
            # Check one original motor step on a separate state before using
            # the restored checkpoint for the new diagnostic trajectory.
            test=mujoco.MjData(m);test.qpos[:]=q[k];test.qvel[:]=v[k];test.time=float(times[k])
            mujoco.mj_forward(m,test);test.qacc_warmstart[:]=w[k];test.ctrl[:]=trace['ctrl'][k]
            mujoco.mj_step(m,test)
            report['restored_original_step_q_error']=float(np.max(abs(test.qpos-q[k+1])))
            report['restored_original_step_v_error']=float(np.max(abs(test.qvel-v[k+1])))
            del q,v,w;trace.close()
            names=[m.joint(j).name for j in robot_joints(m)];dt=float(m.opt.timestep);stride=round(.001/dt)
            inspection=bool(contract.get('tool_inspection_contract'))
            if inspection:
                from tool_cameras import ToolCameras
                cameras=ToolCameras(m);(out/'camera_frames').mkdir()
                report['camera_source_sha256']={}
                for name in ['tool_cameras.py','sensor_rendering.py']:
                    src=Path(__file__).with_name(name);shutil.copyfile(src,out/name)
                    report['camera_source_sha256'][name]=sha(src)
                report['qualified_held_tool_inspection']=False
            bodies={m.body('tweezer').id}
            for b in range(m.nbody):
                if m.body_parentid[b] in bodies:bodies.add(b)
            allowed={m.body(n).id for n in contract['allowed_tool_contact_bodies']}
            actuation=bool(contract.get('tool_actuation_contract'))
            endpoints={}
            if actuation:
                rest=mujoco.MjData(m);rest.qpos[:]=d.qpos
                for j in range(m.njnt):
                    if int(m.jnt_bodyid[j]) in bodies and m.jnt_type[j]==mujoco.mjtJoint.mjJNT_HINGE:
                        rest.qpos[m.jnt_qposadr[j]]=0.
                mujoco.mj_kinematics(m,rest);root=m.body('tweezer').id
                for label,sign in [('negative',-1.),('positive',1.)]:
                    tip=max((b for b in bodies if m.body(b).name.startswith(label+'_beam_')),key=lambda b:m.body(b).name)
                    point=rest.xpos[root]+rest.xmat[root].reshape(3,3)@np.array([-.130,sign*.004,0.])
                    endpoints[label]=(tip,rest.xmat[tip].reshape(3,3).T@(point-rest.xpos[tip]))
            native_window=deque();previous_phase=None
            preload_window=contract.get('carry_contract',{}).get('minimum_native_loaded_before_lift_s',.5)
            for i in range(round(a.seconds/dt)):
                if i%stride==0:
                    obs=dict(time_s=float(d.time),joint_position=np.array([d.sensor(n+'_encoder').data[0] for n in names]),
                        joint_velocity=np.array([d.sensor(n+'_velocity').data[0] for n in names]),
                        imu_quaternion=d.sensor('imu_orientation').data.copy(),imu_gyro=d.sensor('imu_angular_velocity').data.copy(),
                        head_rgb=None,head_depth=None)
                    if cameras is not None and i%(stride*200)==0 and response.get('phase') in {'inspect_move','inspect_hold','inspect_return'}:
                        frame=cameras.read(d);obs.update(frame)
                        path=out/'camera_frames'/f'{len(camera_records):05d}.npz'
                        np.savez_compressed(path,**frame)
                        camera_records.append(dict(id=len(camera_records),time_s=float(d.time),
                            phase_before_observation=response['phase'],file=str(path.relative_to(out)),sha256=sha(path)))
                    response=ask(obs);d.ctrl[:]=response['torque']
                    if a.measure_prelift_native and response['phase']=='lift' and previous_phase=='close':
                        selected=[v for v in native_window if d.time-preload_window<=v[0]<d.time]
                        loaded_s=sum(v[1] for v in selected)*dt
                        native_path=out/'prelift_native_window.npz'
                        np.savez_compressed(native_path,time_s=np.asarray([v[0] for v in selected]),
                            loaded=np.asarray([v[1] for v in selected],dtype=bool),
                            force_n=np.asarray([v[2] for v in selected]).reshape(-1,3),
                            finger_names=np.asarray(['thumb','index','middle']))
                        report['prelift_native_observation']=dict(time_s=float(d.time),window_s=preload_window,
                            sample_period_s=dt,samples=len(selected),loaded_s=loaded_s,
                            native_window_sha256=sha(native_path),
                            passed_native_window=bool(len(selected)>=round(preload_window/dt)-1 and loaded_s>=preload_window-dt-1e-9),
                            restored_state_diagnostic_only=True)
                    previous_phase=response['phase']
                    records.append((float(d.time),d.qpos.copy(),d.qvel.copy(),d.ctrl.copy()))
                    if response.get('complete'):
                        failure=response.get('failure');break
                mujoco.mj_step(m,d)
                if np.any(d.warning.number) or d.qpos[2]<.6:raise RuntimeError('Physical instability in continuation')
                if np.any(d.xfrc_applied) or np.any(d.qfrc_applied):raise RuntimeError('External force unexpectedly applied')
                monitor_due=i%(stride*10)==0
                record_actuation=actuation and response['phase'] in {'hold','tool_squeeze','tool_reopen'}
                if monitor_due or record_actuation or (a.measure_prelift_native and response['phase']=='close'):
                    forces={n:0. for n in ['thumb','index','middle']}
                    other_tool_load=0.
                    for ci,c in enumerate(d.contact):
                        bs={int(m.geom_bodyid[g]) for g in c.geom}
                        if record_actuation and sum(int(m.geom_bodyid[g]) in bodies for g in c.geom)==1 and not bs&allowed:
                            wrench=np.zeros(6);mujoco.mj_contactForce(m,d,ci,wrench);other_tool_load+=max(0.,float(wrench[0]))
                        if not(bs&bodies and bs&allowed):continue
                        name=m.body(next(iter(bs&allowed))).name;f=next(n for n in forces if n in name)
                        wrench=np.zeros(6);mujoco.mj_contactForce(m,d,ci,wrench);forces[f]+=max(0.,float(wrench[0]))
                    if a.measure_prelift_native and response['phase']=='close':
                        limits=contract['physical_acceptance']
                        loaded=forces['thumb']>limits['minimum_thumb_load_n'] and min(forces['index'],forces['middle'])>limits['minimum_each_opposing_finger_load_n']
                        native_window.append((float(d.time-dt),bool(loaded),
                                              [forces[n] for n in ['thumb','index','middle']]))
                        while native_window and native_window[0][0]<d.time-preload_window-.002:native_window.popleft()
                    if record_actuation:
                        tips=[d.xpos[b]+d.xmat[b].reshape(3,3)@point for b,point in endpoints.values()]
                        wrist=d.site('right_wrist_reference')
                        relative=wrist.xmat.reshape(3,3).T@(d.body('tweezer').xpos-wrist.xpos)
                        actuation_native.append((float(d.time-dt),response['phase'],
                            [forces[n] for n in ['thumb','index','middle']],other_tool_load,
                            float(np.linalg.norm(tips[1]-tips[0])),relative.copy()))
                if monitor_due:
                    monitor.write(json.dumps(dict(time_s=float(d.time-dt),phase=response['phase'],
                        base_m=d.qpos[:3].tolist(),tool_m=d.body('tweezer').xpos.tolist(),
                        actual_finger_force_n=forces,force_proxy_n=np.asarray(response['force_proxy_n']).tolist(),
                        motor_load_nm=np.asarray(response['motor_load_nm']).tolist(),
                        motor_load_abort_nm=response.get('motor_load_abort_nm'),
                        hand_commands_rad={m.joint(m.actuator_trnid[a,0]).name:float(value)
                            for a,value in enumerate(response['requested_joint_position'])
                            if m.joint(m.actuator_trnid[a,0]).name.startswith('right_hand_')},
                        wrist_target_m=np.asarray(response['wrist_target_m']).tolist(),
                        wrist_observed_m=np.asarray(response['wrist_observed_m']).tolist(),
                        walk_phase=response.get('walk_phase')))+'\n');monitor.flush()
                if i%round(.5/dt)==0:print('checkpoint',round(float(d.time),3),response['phase'],'wall_s',round(time.monotonic()-started,1),flush=True)
            report.update(final_time_s=float(d.time),last_phase=response.get('phase'),physics_warnings=d.warning.number.tolist(),
                final_base_xy_error_m=float(np.linalg.norm(d.qpos[:2]-np.asarray(contract['initial_qpos'])[:2])))
        except Exception as exc:failure=type(exc).__name__+': '+str(exc)
        finally:
            process.stdin.close()
            try:process.wait(timeout=15)
            except subprocess.TimeoutExpired:process.kill();process.wait()
            if cameras is not None:cameras.close()
    if records:np.savez_compressed(out/'trace.npz',**{n:np.array([r[i] for r in records]) for i,n in enumerate(['time','qpos','qvel','ctrl'])})
    (out/'events.json').write_text(json.dumps(response.get('events',[]),indent=2)+'\n')
    if camera_records:
        (out/'camera_index.json').write_text(json.dumps(camera_records,indent=2)+'\n')
        report['camera_index_sha256']=sha(out/'camera_index.json')
        report['camera_frames']=len(camera_records)
    if actuation_native:
        native_path=out/'tool_actuation_native.npz'
        np.savez_compressed(native_path,**{name:np.asarray([r[i] for r in actuation_native])
            for i,name in enumerate(['time_s','phase','force_n','other_tool_contact_load_n','tip_gap_m','tool_wrist_position_m'])})
        report['tool_actuation_native']=dict(file=native_path.name,sha256=sha(native_path),
            samples=len(actuation_native),sample_period_s=dt,evaluator_only=True,
            continuous_pickup_and_tool_use=False,qualified_tool_actuation=False)
    report.update(failure=failure,wall_seconds=time.monotonic()-started,
        trace_sha256=sha(out/'trace.npz') if records else None)
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
    if failure:raise SystemExit(1)


if __name__=='__main__':main()
