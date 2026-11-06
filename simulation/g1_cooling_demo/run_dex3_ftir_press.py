"""Run a fresh isolated G1/Dex3 key press in the unchanged complete laboratory.

Authored initial station and pointing posture receive no navigation/preparation
credit. The controller never receives device state or physics contact truth.
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

from carry_tool_actor import declared_sole_support, public_support_prior
from isolation import prepare
from observations import robot_joints
from sensor_rendering import depth_renderer

HERE = Path(__file__).resolve().parent


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def plain(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def run(source, frame, output, duration, com_lowering=0., leg_posture_weight=1., body_joint_damper=False,
        com_target_mode='sole_center', press_force=.45, press_depth=.001):
    source, frame, out = map(lambda p:Path(p).resolve(), [source, frame, output])
    source_contract = json.loads((source/'contract.json').read_text())
    assert sha(source/'world.xml') == source_contract['model_sha256']
    assert not source_contract.get('collision_plugins')
    out.mkdir(parents=True, exist_ok=False)
    snapshot = out/'source_snapshot'
    snapshot.mkdir()
    modules = ['dex3_ftir_actor.py', 'dex3_ftir_hand.py', 'dex3_ftir_planning.py',
        'ftir_hand.py', 'ftir_vision.py', 'robot_source_meshes.py', 'source_proximity.py',
        'joint_rrt.py', 'tool_approach_planning.py', 'conic_balance.py']
    for name in sorted(set([Path(__file__).name, 'balance.py', 'observations.py',
                           'sensor_rendering.py', 'isolation.py', *modules])):
        shutil.copyfile(HERE/name, snapshot/name)
    for name in ['world.xml', 'laboratory_import.json', 'model_inputs.json']:
        shutil.copyfile(source/name, out/name)
    shutil.copytree(source/'controller_model', out/'controller_model')
    m = mujoco.MjModel.from_xml_path(str(out/'world.xml'))
    d = mujoco.MjData(m)
    assert m.nu == 43 and m.neq == 0 and abs(m.opt.timestep-.0001) < 1e-12
    with np.load(frame) as f:
        d.qpos[:] = f['authored_qpos']
    mujoco.mj_forward(m, d)
    joints = robot_joints(m)
    names = [m.joint(j).name for j in joints]
    robot = {m.body('pelvis').id}
    for b in range(m.nbody):
        if int(m.body_parentid[b]) in robot:
            robot.add(b)
    imported = json.loads((out/'laboratory_import.json').read_text())
    support = public_support_prior(m, imported,
        source_contract['physical_acceptance']['maximum_sole_penetration_m'])
    bad = [dict(parts=[m.geom(int(g)).name for g in c.geom], distance_m=float(c.dist))
        for c in d.contact if c.dist < -.00002
        and any(int(m.geom_bodyid[int(g)]) in robot for g in c.geom)
        and not declared_sole_support(m, c, support)]
    (out/'initial_contact_review.json').write_text(json.dumps(dict(passed=not bad, violations=bad), indent=2)+'\n')
    if bad:
        raise ValueError('Initial robot contacts violate the original bounds')
    policy = out/'policy_source'
    policy.mkdir()
    setup = dict(root_qpos=d.qpos[:7].tolist(),
        joints={m.joint(j).name:float(d.qpos[m.jnt_qposadr[j]]) for j in joints},
        com_lowering_m=com_lowering, leg_posture_weight=leg_posture_weight,
        body_joint_damper=body_joint_damper,
        com_target_mode=com_target_mode,
        press_force_n=press_force,
        press_depth_m=press_depth,
        scope='Authored component starting pose; no executed navigation or preparation')
    setup_path = policy/'robot_setup.json'
    setup_path.write_text(json.dumps(setup, indent=2)+'\n')
    command = [sys.executable, str(HERE/'dex3_ftir_actor.py'), '--model',
        str(out/'controller_model/world.xml'), '--setup', '/model/policy/robot_setup.json']
    command, environment, isolation = prepare(out, out/'controller_model/world.xml',
        command, extra_modules=modules, policy_files=[setup_path])
    thresholds = dict(key_press_m=.00024, key_return_m=.00005, minimum_press_s=.05,
        unintended_penetration_m=.00002, intended_pad_penetration_m=.00025,
        sole_penetration_m=.001, maximum_body_tilt_rad=.2,
        maximum_joint_limit_excess_rad=.01, maximum_replay_q_error=1e-9,
        maximum_replay_v_error=1e-8)
    contract = dict(scope=__doc__, hand_kind='unitree_three_finger',
        task='observed_background_key_press_withdraw_return', model_sha256=sha(out/'world.xml'),
        source_run=str(source), source_contract_sha256=sha(source/'contract.json'),
        authored_frame_sha256=sha(frame), setup_sha256=sha(setup_path),
        initial_qpos=d.qpos.tolist(), initial_qvel=d.qvel.tolist(),
        physical_timestep_s=float(m.opt.timestep), controller_period_s=.001,
        camera_period_s=.1, camera_resolution=[640, 360],
        intended_finger_body='right_hand_index_1_link', intended_key_body='nicolet_key_1',
        intended_key_joint='nicolet_key_slide_1', physical_acceptance=thresholds,
        balance_development=dict(com_lowering_m=com_lowering, leg_posture_weight=leg_posture_weight,
                                body_joint_damper=body_joint_damper, com_target_mode=com_target_mode),
        press_force_feedforward_n=press_force,
        commanded_press_depth_m=press_depth,
        acceptance_basis='Unchanged key travel, dwell, return, contact and support bounds from verify_ftir_press.py; source embodiment rebound to Dex3 index',
        source_sha256={p.name:sha(p) for p in snapshot.iterdir()},
        actor_isolation_sha256=sha(out/'actor_isolation.json'), qualified_ftir_press=False)
    (out/'contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    (out/'camera_frames').mkdir()
    color = mujoco.Renderer(m, height=360, width=640, max_geom=m.ngeom+1000)
    depth = depth_renderer(m, 360, 640)
    option = mujoco.MjvOption()
    option.geomgroup[3] = 0
    option.sitegroup[:] = 0
    stride, camera_stride = round(.001/m.opt.timestep), round(.1/m.opt.timestep)
    records, sensors, responses, cameras, events = [], [], [], [], []
    failure, response = None, {}
    started = time.monotonic()
    with (out/'actor_stderr.log').open('w') as stderr, (out/'monitor.jsonl').open('w') as monitor:
        process = subprocess.Popen(command, env=environment, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=stderr, close_fds=True)
        try:
            for i in range(round(duration/m.opt.timestep)):
                if i % stride == 0:
                    packet = dict(time_s=float(d.time),
                        joint_position=np.array([d.sensor(n+'_encoder').data[0] for n in names]),
                        joint_velocity=np.array([d.sensor(n+'_velocity').data[0] for n in names]),
                        imu_quaternion=d.sensor('imu_orientation').data.copy(),
                        imu_gyro=d.sensor('imu_angular_velocity').data.copy())
                    retained = dict(packet)
                    rgb, z, frame_id = None, None, -1
                    if i % camera_stride == 0:
                        color.update_scene(d, camera='head_rgb', scene_option=option)
                        rgb = color.render().copy()
                        depth.update_scene(d, camera='head_depth', scene_option=option)
                        z = depth.render().copy()
                        frame_id = len(cameras)
                        path = out/'camera_frames'/('%05d.npz' % frame_id)
                        np.savez_compressed(path, rgb=rgb, depth=z)
                        cameras.append(dict(id=frame_id, time_s=float(d.time),
                            file=str(path.relative_to(out)), sha256=sha(path)))
                    packet.update(rgb=rgb, depth=z)
                    retained['camera_frame_id'] = frame_id
                    sensors.append(retained)
                    pickle.dump(packet, process.stdin, protocol=5)
                    process.stdin.flush()
                    response = pickle.load(process.stdout)
                    events = response.get('events', events)
                    responses.append({k:v for k, v in response.items() if k != 'events'})
                    if response['error']:
                        raise RuntimeError(response['error'])
                    d.ctrl[:] = response['torque']
                    if i % camera_stride == 0:
                        monitor.write(json.dumps(dict(time_s=float(d.time),
                            **{k:v for k, v in response.items() if k not in {'torque', 'events'}}), default=plain)+'\n')
                        monitor.flush()
                records.append((float(d.time), d.qpos.copy(), d.qvel.copy(), d.ctrl.copy(), d.qacc_warmstart.copy()))
                if response.get('policy_complete'):
                    break
                mujoco.mj_step(m, d)
                if not np.isfinite(d.qpos).all() or np.any(d.warning.number):
                    raise RuntimeError('Physics numerical failure')
                if d.qpos[2] < .6 or d.body('pelvis').xmat.reshape(3, 3)[2, 2] < .85:
                    raise RuntimeError('Body support lost')
                if np.any(d.xfrc_applied) or np.any(d.qfrc_applied):
                    raise RuntimeError('Unexpected external force')
                if i % round(.5/m.opt.timestep) == 0:
                    print('dex3_ftir', round(float(d.time), 3), response.get('policy_state'),
                          'wall_s', round(time.monotonic()-started, 1), flush=True)
            if not response.get('policy_complete'):
                failure = 'Duration exhausted before the press/return attempt ended'
            elif response.get('policy_failure'):
                failure = response['policy_failure']
        except Exception as error:
            failure = str(error)
            print('failed', failure, flush=True)
        finally:
            process.stdin.close()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            color.close()
            depth.close()
    if not records or abs(records[-1][0]-d.time) > 1e-12:
        records.append((float(d.time), d.qpos.copy(), d.qvel.copy(), d.ctrl.copy(), d.qacc_warmstart.copy()))
    np.savez_compressed(out/'trace.npz', **{k:np.asarray([r[i] for r in records])
        for i, k in enumerate(['time', 'qpos', 'qvel', 'ctrl', 'qacc_warmstart'])})
    np.savez_compressed(out/'sensors.npz', **{k:np.asarray([r[k] for r in sensors]) for k in sensors[0]})
    (out/'responses.pkl').write_bytes(pickle.dumps(responses, protocol=5))
    (out/'events.json').write_text(json.dumps(events, indent=2)+'\n')
    (out/'camera_index.json').write_text(json.dumps(cameras, indent=2)+'\n')
    result = dict(scope=__doc__, status='failed' if failure else 'attempt_finished_pending_independent_switch_verification',
        failure=failure, simulated_seconds=float(d.time), wall_seconds=time.monotonic()-started,
        contract_sha256=sha(out/'contract.json'), model_sha256=sha(out/'world.xml'),
        trace_sha256=sha(out/'trace.npz'), sensors_sha256=sha(out/'sensors.npz'),
        responses_sha256=sha(out/'responses.pkl'), events_sha256=sha(out/'events.json'),
        camera_index_sha256=sha(out/'camera_index.json'), actor_access_isolated=isolation['passed'],
        qualified_ftir_press=False, qualified_paper_branch=False)
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source_run')
    p.add_argument('authored_frame')
    p.add_argument('output')
    p.add_argument('--duration', type=float, default=70.)
    p.add_argument('--com-lowering', type=float, default=0.)
    p.add_argument('--leg-posture-weight', type=float, default=1.)
    p.add_argument('--body-joint-damper', action='store_true')
    p.add_argument('--com-target-mode', choices=['sole_center', 'initial'], default='sole_center')
    p.add_argument('--press-force', type=float, default=.45,
                   help='Normal wrist force feedforward; zero tests pure position control with unchanged switch acceptance')
    p.add_argument('--press-depth', type=float, default=.001,
                   help='Commanded travel beyond the observed key surface in metres; physical key and contact bounds are unchanged')
    a = p.parse_args()
    if run(a.source_run, a.authored_frame, a.output, a.duration,
           a.com_lowering, a.leg_posture_weight, a.body_joint_damper, a.com_target_mode, a.press_force, a.press_depth)['failure']:
        raise SystemExit(1)
