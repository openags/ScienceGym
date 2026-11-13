"""Test the existing official body policy in the unchanged complete Dex3 lab.

The robot is staged in the existing front aisle before time zero. Objects and
plant dynamics remain identical to the source run. Only motor torques advance
the state after initialization; no carrying or navigation credit is granted.
"""
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
import yaml

from isolation import prepare
from observations import robot_joints
from walking_actor import SDK_JOINTS

HERE = Path(__file__).resolve().parent


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def run(source, folder, duration=12., speed=.2, stop_at=8.):
    source, folder = Path(source).resolve(), Path(folder).resolve()
    folder.mkdir(parents=True, exist_ok=False)
    source_contract = json.loads((source / 'contract.json').read_text())
    assert sha(source / 'world.xml') == source_contract['model_sha256']
    assert source_contract['hand_kind'] == 'unitree_three_finger'
    policy = HERE / 'locomotion_policy'
    provenance = json.loads((policy / 'SOURCE.json').read_text())
    for item in provenance['files']:
        assert sha(policy / item['path']) == item['sha256']
    snapshot = folder / 'source_snapshot'
    snapshot.mkdir()
    for p in HERE.glob('*.py'):
        shutil.copyfile(p, snapshot / p.name)
    shutil.copytree(policy, folder / 'policy_source')
    shutil.copytree(source / 'controller_model', folder / 'controller_model')
    for name in ['world.xml', 'laboratory_import.json']:
        shutil.copyfile(source / name, folder / name)
    m = mujoco.MjModel.from_xml_path(str(folder / 'world.xml'))
    d = mujoco.MjData(m)
    d.qpos[:] = source_contract['initial_qpos']
    d.qvel[:] = source_contract['initial_qvel']
    cfg = yaml.safe_load((policy / 'deploy.yaml').read_text())
    initial = np.empty(29)
    initial[cfg['joint_ids_map']] = cfg['default_joint_pos']
    for name, value in zip(SDK_JOINTS, initial):
        d.joint(name).qpos[0] = value
    joints = robot_joints(m)
    hands = [j for j in joints if '_hand_' in m.joint(j).name]
    hand_pose = {}
    for j in hands:
        # An open, interior source joint posture, fixed before this attempt.
        target = float(np.clip(0., m.jnt_range[j, 0] + .03, m.jnt_range[j, 1] - .03))
        d.qpos[m.jnt_qposadr[j]] = target
        hand_pose[m.joint(j).name] = target
    d.qpos[:2] = [-.52, .7]  # lab (3.0, 1.5), same existing front aisle
    d.qpos[3:7] = [2**-.5, 0., 0., -2**-.5]
    mujoco.mj_forward(m, d)
    d.qpos[2] -= min(d.site(s + '_sole').xpos[2] for s in ['left', 'right'])
    mujoco.mj_forward(m, d)
    prior = dict(speed_m_s=speed, stop_at_s=stop_at, control_period_s=.001, hand_pose=hand_pose)
    (folder / 'walking_prior.json').write_text(json.dumps(prior, indent=2) + '\n')
    command = [sys.executable, str(HERE / 'dex3_walking_actor.py'), '--model', str(folder / 'controller_model/world.xml')]
    command, environment, isolation = prepare(folder, folder / 'controller_model/world.xml', command,
        extra_modules=['walking_actor.py', 'dex3_walking_actor.py'],
        policy_files=[policy / 'deploy.yaml', policy / 'policy.onnx', folder / 'walking_prior.json'])
    contract = dict(scope=__doc__, hand_kind='unitree_three_finger', model_sha256=sha(folder / 'world.xml'),
        source_contract_sha256=sha(source / 'contract.json'), initial_qpos=d.qpos.tolist(), initial_qvel=d.qvel.tolist(),
        physics_period_s=m.opt.timestep, control_period_s=.001, duration_limit_s=duration,
        policy_source_sha256=sha(policy / 'SOURCE.json'), prior_sha256=sha(folder / 'walking_prior.json'),
        actor_isolation_sha256=sha(folder / 'actor_isolation.json'),
        source_snapshot_sha256={p.name: sha(p) for p in snapshot.glob('*.py')},
        authored_initial_staging=dict(lab_xy_m=[3., 1.5], lab_yaw_rad=0., existing_aisle=True),
        physical_acceptance=source_contract['physical_acceptance'],
        required_forward_m=1., maximum_lateral_m=.3, maximum_settled_speed_m_s=.05,
        qualified_walking=False, qualified_carry=False, qualified_paper_branch=False)
    (folder / 'contract.json').write_text(json.dumps(contract, indent=2) + '\n')
    log = (folder / 'actor_stderr.log').open('w')
    actor = subprocess.Popen(command, env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=log, close_fds=True)
    records, sensors, responses = [], [], []
    failure = None
    response = {}
    started = time.monotonic()
    decimation = round(.001 / m.opt.timestep)
    assert abs(decimation * m.opt.timestep - .001) < 1e-12
    try:
        for i in range(round(duration / m.opt.timestep)):
            if i % decimation == 0:
                packet = dict(time_s=float(d.time),
                    joint_position=np.array([d.sensor(m.joint(j).name + '_encoder').data[0] for j in joints]),
                    joint_velocity=np.array([d.sensor(m.joint(j).name + '_velocity').data[0] for j in joints]),
                    imu_quaternion=d.sensor('imu_orientation').data.copy(),
                    imu_gyro=d.sensor('imu_angular_velocity').data.copy(), depth=None)
                pickle.dump(packet, actor.stdin, protocol=5)
                actor.stdin.flush()
                response = pickle.load(actor.stdout)
                sensors.append({k: v for k, v in packet.items() if k != 'depth'})
                responses.append(response)
                if response['error']:
                    raise RuntimeError(response['error'])
                d.ctrl[:] = response['torque']
            records.append((float(d.time), d.qpos.copy(), d.qvel.copy(), d.ctrl.copy(), d.qacc_warmstart.copy()))
            mujoco.mj_step(m, d)
            if not np.isfinite(d.qpos).all() or np.any(d.warning.number):
                raise RuntimeError('Physics numerical failure')
            if d.qpos[2] < .5 or d.xmat[m.body('pelvis').id].reshape(3, 3)[2, 2] < .75:
                raise RuntimeError('Walking support lost')
            if i % round(.5 / m.opt.timestep) == 0:
                print('dex3_walk', round(float(d.time), 3), 'xyz', np.round(d.qpos[:3], 3).tolist(),
                      'wall_s', round(time.monotonic() - started, 1), flush=True)
    except Exception as error:
        failure = type(error).__name__ + ': ' + str(error)
        print('failed', failure, flush=True)
    finally:
        actor.stdin.close()
        try:
            actor.wait(timeout=15)
        except subprocess.TimeoutExpired:
            actor.kill()
            actor.wait()
        log.close()
    records.append((float(d.time), d.qpos.copy(), d.qvel.copy(), d.ctrl.copy(), d.qacc_warmstart.copy()))
    np.savez_compressed(folder / 'trace.npz', **{k: np.array([row[i] for row in records])
        for i, k in enumerate(['time', 'qpos', 'qvel', 'ctrl', 'qacc_warmstart'])})
    if sensors:
        np.savez_compressed(folder / 'sensors.npz', **{k: np.array([row[k] for row in sensors]) for k in sensors[0]})
    with (folder / 'responses.pkl').open('wb') as stream:
        pickle.dump(responses, stream, protocol=5)
    result = dict(scope=__doc__, failure=failure, simulated_seconds=float(d.time), actor_exit_code=actor.returncode,
        final_qpos=d.qpos.tolist(), policy_evaluations=response.get('policy_evaluations'),
        trace_sha256=sha(folder / 'trace.npz'), contract_sha256=sha(folder / 'contract.json'),
        responses_sha256=sha(folder / 'responses.pkl'), sensors_sha256=sha(folder / 'sensors.npz'),
        qualified_walking=False, qualified_carry=False, qualified_paper_branch=False)
    (folder / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source')
    p.add_argument('folder')
    p.add_argument('--duration', type=float, default=12.)
    p.add_argument('--speed', type=float, default=.2)
    p.add_argument('--stop-at', type=float, default=8.)
    a = p.parse_args()
    if run(a.source, a.folder, a.duration, a.speed, a.stop_at)['failure']:
        raise SystemExit(1)
