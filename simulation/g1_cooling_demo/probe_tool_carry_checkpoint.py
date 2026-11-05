"""Diagnose loaded control from an explicitly restored grasp checkpoint.

The frozen isolated actor first consumes every original sensor packet up to
the checkpoint. Physics then starts from a recorded held-tool state. This is
not a continuous pickup/carry recording, independent replay, or skill result.
The separate full run must execute its own pickup and carry without resets.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pickle
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
    p.add_argument('--seconds',type=float,default=18.);a=p.parse_args()
    source,run,out=map(lambda x:Path(x).resolve(),[a.source_recording,a.actor_run,a.output])
    out.mkdir(parents=True,exist_ok=False)
    contract=json.loads((run/'contract.json').read_text());receipt=json.loads((run/'actor_isolation.json').read_text())
    original=json.loads((source/'result.json').read_text())
    assert contract['task']=='visual_pickup_loaded_out_and_back_release' and receipt['passed']
    assert sha(run/'world.xml')==contract['model_sha256']==json.loads((source/'contract.json').read_text())['model_sha256']
    for f,key in [('trace.npz','trace_sha256'),('sensors.npz','sensors_sha256'),('responses.pkl','responses_sha256')]:
        assert sha(source/f)==original[key]
    for n,h in receipt['source_modules'].items():assert sha(run/'actor_bundle/code'/n)==h
    source_events=json.loads((source/'events.json').read_text())
    checkpoint=next(e['time_s'] for e in source_events if e.get('phase')=='lower')
    sensors=dict(np.load(source/'sensors.npz'));index=json.loads((source/'camera_index.json').read_text())
    responses=pickle.loads((source/'responses.pkl').read_bytes())
    row=int(np.argmin(abs(sensors['time_s']-checkpoint)))
    report=dict(scope=__doc__,physical_execution=True,continuous_pickup_carry=False,qualified_carry=False,
        source_result_sha256=sha(source/'result.json'),actor_contract_sha256=sha(run/'contract.json'),
        script_sha256=sha(__file__),checkpoint_time_s=checkpoint,requested_continuation_s=a.seconds)
    (out/'contract.json').write_text(json.dumps(report,indent=2)+'\n')
    command=receipt['command_prefix']+[sys.executable,'/actor/carry_tool_actor.py','--model','/model/world.xml']
    failure=None;records=[];response={};started=time.monotonic()
    with (out/'actor_stderr.log').open('wb') as stderr,(out/'monitor.jsonl').open('w') as monitor:
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,env=receipt['environment'])
        def ask(obs):
            pickle.dump(obs,process.stdin,protocol=5);process.stdin.flush()
            value=pickle.load(process.stdout)
            if value.get('error'):raise RuntimeError(value['error'])
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
            bodies={m.body('tweezer').id}
            for b in range(m.nbody):
                if m.body_parentid[b] in bodies:bodies.add(b)
            allowed={m.body(n).id for n in contract['allowed_tool_contact_bodies']}
            for i in range(round(a.seconds/dt)):
                if i%stride==0:
                    obs=dict(time_s=float(d.time),joint_position=np.array([d.sensor(n+'_encoder').data[0] for n in names]),
                        joint_velocity=np.array([d.sensor(n+'_velocity').data[0] for n in names]),
                        imu_quaternion=d.sensor('imu_orientation').data.copy(),imu_gyro=d.sensor('imu_angular_velocity').data.copy(),
                        head_rgb=None,head_depth=None)
                    response=ask(obs);d.ctrl[:]=response['torque']
                    records.append((float(d.time),d.qpos.copy(),d.qvel.copy(),d.ctrl.copy()))
                    if response.get('complete'):
                        failure=response.get('failure');break
                mujoco.mj_step(m,d)
                if np.any(d.warning.number) or d.qpos[2]<.6:raise RuntimeError('Physical instability in continuation')
                if np.any(d.xfrc_applied) or np.any(d.qfrc_applied):raise RuntimeError('External force unexpectedly applied')
                if i%(stride*10)==0:
                    forces={n:0. for n in ['thumb','index','middle']}
                    for ci,c in enumerate(d.contact):
                        bs={int(m.geom_bodyid[g]) for g in c.geom}
                        if not(bs&bodies and bs&allowed):continue
                        name=m.body(next(iter(bs&allowed))).name;f=next(n for n in forces if n in name)
                        wrench=np.zeros(6);mujoco.mj_contactForce(m,d,ci,wrench);forces[f]+=max(0.,float(wrench[0]))
                    monitor.write(json.dumps(dict(time_s=float(d.time-dt),phase=response['phase'],
                        base_m=d.qpos[:3].tolist(),tool_m=d.body('tweezer').xpos.tolist(),
                        actual_finger_force_n=forces,force_proxy_n=np.asarray(response['force_proxy_n']).tolist(),
                        walk_phase=response.get('walk_phase')))+'\n');monitor.flush()
                if i%round(.5/dt)==0:print('checkpoint',round(float(d.time),3),response['phase'],'wall_s',round(time.monotonic()-started,1),flush=True)
            report.update(final_time_s=float(d.time),last_phase=response.get('phase'),physics_warnings=d.warning.number.tolist())
        except Exception as exc:failure=type(exc).__name__+': '+str(exc)
        finally:
            process.stdin.close()
            try:process.wait(timeout=15)
            except subprocess.TimeoutExpired:process.kill();process.wait()
    if records:np.savez_compressed(out/'trace.npz',**{n:np.array([r[i] for r in records]) for i,n in enumerate(['time','qpos','qvel','ctrl'])})
    (out/'events.json').write_text(json.dumps(response.get('events',[]),indent=2)+'\n')
    report.update(failure=failure,wall_seconds=time.monotonic()-started,
        trace_sha256=sha(out/'trace.npz') if records else None)
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
    if failure:raise SystemExit(1)


if __name__=='__main__':main()
