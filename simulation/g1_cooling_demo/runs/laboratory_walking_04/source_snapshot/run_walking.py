"""Record an isolated official-policy walking compatibility trial in the lab."""
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

from isolation import prepare
from world import build, initialize, HERE
from walking_actor import SDK_JOINTS


def run(folder, duration=14, speed=.2, gains='training', hold_heading=False):
    folder = Path(folder).resolve(); folder.mkdir(parents=True,exist_ok=True)
    if any(folder.iterdir()): raise ValueError('Use a new empty trial directory')
    snapshot = folder/'source_snapshot'; snapshot.mkdir()
    for path in HERE.glob('*.py'): shutil.copyfile(path, snapshot/path.name)
    policy = HERE/'locomotion_policy'
    shutil.copytree(policy, folder/'policy_source')
    model_path = build(folder, laboratory=True, tray=False)
    control_path = build(folder/'controller_model', laboratory=True, tray=False, map_only=True)
    if gains == 'training':
        for path in [model_path, control_path]:
            xml = ET.parse(path)
            for node in xml.findall('.//joint'):
                if node.get('name') in SDK_JOINTS:
                    node.set('armature','.01')
            xml.write(path,encoding='unicode')
    adaptation = dict(gains=gains,body_joint_rotor_inertia_kg_m2=.01 if gains=='training' else .001,
        source='locomotion_policy/reference/training_models.py: UNITREE_G1_29DOF_CFG' if gains=='training' else 'locomotion_policy/deploy.yaml',
        body_inertias_unchanged=True,hand_rotor_inertias_unchanged=True)
    (folder/'actuator_adaptation.json').write_text(json.dumps(adaptation,indent=2)+'\n')
    model = mujoco.MjModel.from_xml_path(str(model_path)); data = initialize(model)
    # Stand in the existing east-west front aisle, facing towards +lab X.
    # This is declared initial staging, not a motion or relocation during run.
    data.qpos[:2] = [-.52, .7]  # lab X=3.0, Y=1.50
    data.qpos[3:7] = [2**-.5,0,0,-2**-.5]
    # Joint names are a published robot convention, not object state.
    legs = [s+'_'+j+'_joint' for s in ['left','right']
            for j in ['hip_pitch','hip_roll','hip_yaw','knee','ankle_pitch','ankle_roll']]
    names = legs+['waist_'+j+'_joint' for j in ['yaw','roll','pitch']]
    names += [s+'_'+j+'_joint' for s in ['left','right']
              for j in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow','wrist_roll','wrist_pitch','wrist_yaw']]
    cfg = yaml.safe_load((policy/'deploy.yaml').read_text())
    initial = np.empty(29); initial[cfg['joint_ids_map']] = cfg['default_joint_pos']
    for name, value in zip(names,initial): data.joint(name).qpos[0] = value
    mujoco.mj_forward(model,data)
    data.qpos[2] -= min(data.site(s+'_sole').xpos[2] for s in ['left','right'])
    mujoco.mj_forward(model,data)
    staging = dict(lab_xy_m=[3.,1.5],lab_yaw_rad=0.,source='Authored initial staging in existing aisle',
                   initial_qpos=data.qpos.tolist(),velocity_schedule='0-2 s stand, 2-10 s forward, then stop',speed_m_s=speed)
    (folder/'staging.json').write_text(json.dumps(staging,indent=2)+'\n')
    receipt_path = folder/'laboratory_import.json'
    imported = json.loads(receipt_path.read_text())
    imported['initial_staging'] = [dict(instance='g1',laboratory_xy_m=[3.,1.5],yaw_rad=0.,basis=staging['source'])]
    receipt_path.write_text(json.dumps(imported,indent=2)+'\n')
    command = [sys.executable,str(HERE/'walking_actor.py'),'--model',str(control_path),'--speed',str(speed),'--gains',gains]
    if hold_heading: command.append('--hold-heading')
    command,environment,receipt = prepare(folder,control_path,command,extra_modules=['walking_actor.py'],
        policy_files=[policy/'deploy.yaml',policy/'policy.onnx'])
    log = open(folder/'actor_stderr.log','w')
    process = subprocess.Popen(command, env=environment, stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,close_fds=True)
    joints = [model.joint(j).name for j in range(model.njnt) if model.jnt_type[j]==mujoco.mjtJoint.mjJNT_HINGE]
    records, sensors, outputs = [], [], []
    failure = None; started = time.monotonic()
    try:
        for i in range(round(duration/model.opt.timestep)):
            packet = dict(time_s=float(data.time),joint_position=np.array([data.sensor(n+'_encoder').data[0] for n in joints]),
                          joint_velocity=np.array([data.sensor(n+'_velocity').data[0] for n in joints]),
                          imu_quaternion=data.sensor('imu_orientation').data.copy(),imu_gyro=data.sensor('imu_angular_velocity').data.copy(),depth=None)
            pickle.dump(packet,process.stdin,protocol=5);process.stdin.flush();response=pickle.load(process.stdout)
            if response['error']: raise RuntimeError(response['error'])
            data.ctrl[:] = response['torque']
            records.append((float(data.time),data.qpos.copy(),data.qvel.copy(),data.ctrl.copy(),data.qacc_warmstart.copy()))
            sensors.append({k:v for k,v in packet.items() if k!='depth'})
            outputs.append(response['commanded_velocity'])
            mujoco.mj_step(model,data)
            if not np.isfinite(data.qpos).all() or np.any(data.warning.number): raise RuntimeError('Physics numerical failure')
            up = data.xmat[model.body('pelvis').id].reshape(3,3)[2,2]
            if data.qpos[2]<.5 or up<.75: raise RuntimeError('Walking support lost')
            if i%500==0: print('walking',round(float(data.time),3),'xyz',np.round(data.qpos[:3],3).tolist(),'wall_s',round(time.monotonic()-started,1),flush=True)
    except Exception as error:
        failure = str(error); print('failed',failure,flush=True)
    finally:
        process.stdin.close()
        try: process.wait(timeout=15)
        except subprocess.TimeoutExpired: process.kill();process.wait()
        log.close()
    records.append((float(data.time),data.qpos.copy(),data.qvel.copy(),data.ctrl.copy(),data.qacc_warmstart.copy()))
    np.savez_compressed(folder/'trace.npz',**{k:np.array([r[i] for r in records]) for i,k in enumerate(['time','qpos','qvel','ctrl','qacc_warmstart'])})
    if sensors: np.savez_compressed(folder/'sensor_observations.npz',**{k:np.array([r[k] for r in sensors]) for k in sensors[0]},command=np.asarray(outputs))
    result = dict(completed=failure is None,failure=failure,simulated_seconds=float(data.time),
                  environment='existing_complete_laboratory',actor_access_isolated=receipt['passed'],
                  actor_isolation_sha256=hashlib.sha256((folder/'actor_isolation.json').read_bytes()).hexdigest(),
                  actor_exit_code=process.returncode,initial_qpos=staging['initial_qpos'],final_qpos=data.qpos.tolist(),
                  commanded_speed_m_s=speed,trace_hz=1/model.opt.timestep,policy_hz=1/cfg['step_dt'],
                  actuator_adaptation=adaptation,
                  imu_heading_hold=hold_heading,
                  qualified_skill=False,whole_paper_validated=False,
                  scope='Official velocity-policy compatibility trial with current G1/Inspire; no navigation, carrying or campaign credit')
    (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--duration',type=float,default=14)
    parser.add_argument('--speed',type=float,default=.2);parser.add_argument('--gains',choices=['training','deploy'],default='training');parser.add_argument('--hold-heading',action='store_true');args=parser.parse_args()
    if not run(args.out,args.duration,args.speed,args.gains,args.hold_heading)['completed']: raise SystemExit(1)
