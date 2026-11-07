"""Run an isolated full-G1 tool pickup attempt in the existing laboratory.

Starts at an explicitly authored pregrasp. This does not grant perception,
approach, task-branch or repeated-reliability qualification.
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

from hand_touch import read as read_touch
from isolation import prepare
from observations import robot_joints

HERE = Path(__file__).resolve().parent


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def plain(value):
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, np.generic): return value.item()
    raise TypeError(type(value).__name__)


def run(station, output, duration):
    station, output = Path(station).resolve(), Path(output).resolve()
    review = json.loads((station/'review.json').read_text())
    assert review['passed_initial_scene_checks']
    contract = json.loads((station/'contract.json').read_text())
    assert sha(station/'contract.json') == review['contract_sha256']
    assert sha(station/'world.xml') == contract['plant_sha256']
    assert sha(station/'robot_predictor.xml') == contract['predictor_sha256']
    inputs = json.loads((station/'model_inputs.json').read_text())
    assert sha(station/'model_inputs.json') == contract['inputs_sha256']
    for name, digest in inputs.items(): assert sha(name) == digest
    output.mkdir(parents=True, exist_ok=False)
    snapshot = output/'source_snapshot'; snapshot.mkdir()
    for name in ['run_tool_grasp.py', 'tool_grasp_actor.py', 'balance.py', 'conic_balance.py',
                 'observations.py', 'hand_touch.py', 'isolation.py', 'isolation_probe.py']:
        shutil.copyfile(HERE/name, snapshot/name)
    for name in ['world.xml', 'model_inputs.json']:
        shutil.copyfile(station/name, output/name)
    (output/'controller_model').mkdir()
    shutil.copyfile(station/'robot_predictor.xml', output/'controller_model/world.xml')
    model = mujoco.MjModel.from_xml_path(str(output/'world.xml')); data = mujoco.MjData(model)
    data.qpos[:] = contract['initial_qpos']; data.qvel[:] = contract['initial_qvel']
    mujoco.mj_forward(model, data)
    robot = mujoco.MjModel.from_xml_path(str(output/'controller_model/world.xml'))
    rd = mujoco.MjData(robot)
    for j in range(robot.njnt): rd.joint(robot.joint(j).name).qpos[:] = data.joint(robot.joint(j).name).qpos
    assert model.nu == robot.nu == 41
    prior_dir = output/'policy_source'; prior_dir.mkdir()
    prior_path = prior_dir/'tool_prior.json'
    prior_path.write_text(json.dumps(dict(initial_robot_qpos=rd.qpos.tolist(),
        scope='Authored robot initial posture and map origin only; no tool pose or plant object state',
        vision_and_approach_qualified=False), indent=2)+'\n')
    command = [sys.executable, str(HERE/'tool_grasp_actor.py'), '--model', str(output/'controller_model/world.xml')]
    command, environment, isolation = prepare(output, output/'controller_model/world.xml', command,
        extra_modules=['tool_grasp_actor.py', 'conic_balance.py'], policy_files=[prior_path])
    dt = float(model.opt.timestep); stride = round(.001/dt)
    assert abs(stride*dt-.001) < 1e-12
    run_contract = dict(scope=__doc__, station_review_sha256=sha(station/'review.json'),
        station_contract_sha256=sha(station/'contract.json'), model_sha256=sha(output/'world.xml'),
        model_inputs_sha256=sha(output/'model_inputs.json'), duration_limit_s=duration,
        physics_period_s=dt, control_period_s=.001, balance_period_s=.01,
        initial_qpos=data.qpos.tolist(), initial_qvel=data.qvel.tolist(),
        actor_access_isolated=isolation['passed'], controller_fields=sorted(__import__('tool_grasp_actor').ToolActor.fields),
        inferred_control=dict(closure_speed_m_s=.0005, hold_force_proxy_n=.6,
            first_contact_force_proxy_n=.04, contact_entry_force_proxy_n=.05,
            lift_height_m=.03, pinch_center_correction_limit_m=.02,
            pad_geometry_is_not_measured_pressure_centroid=True, hardware_force_calibration_claimed=False),
        physical_acceptance=dict(minimum_actual_tool_lift_m=.02, minimum_lift_hold_s=.5,
            minimum_bilateral_finger_load_n=.2, minimum_bilateral_contact_s=1.,
            maximum_hand_tool_penetration_m=.00025, maximum_passive_support_penetration_m=.00025,
            maximum_other_penetration_m=.00002, maximum_sole_penetration_m=.001,
            maximum_source_joint_limit_excess_rad=.001, minimum_pelvis_height_m=.6,
            minimum_upright_cosine=.85, maximum_normal_force_n=4.,
            minimum_loaded_tip_closure_m=.001, released_tip_gap_target_m=.008,
            released_tip_gap_tolerance_m=.0001, maximum_replay_error=1e-10),
        allowed_tool_contact_bodies=['right_index_force_sensor_2', 'right_index_force_sensor_3',
            'right_thumb_force_sensor_3', 'right_thumb_force_sensor_4', 'right_index_2', 'right_thumb_4'],
        qualified_grasp=False, qualified_paper_branch=False)
    (output/'contract.json').write_text(json.dumps(run_contract, indent=2)+'\n')
    names = [model.joint(j).name for j in robot_joints(model)]
    records, sensors, responses = [], [], []
    failure = None; response = {}; started = time.monotonic()
    with (output/'actor_stderr.log').open('wb') as log, (output/'monitor.jsonl').open('w') as monitor:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, env=environment)
        try:
            for i in range(round(duration/dt)):
                if i % stride == 0:
                    packet = dict(time_s=float(data.time),
                        joint_position=np.array([data.sensor(n+'_encoder').data[0] for n in names]),
                        joint_velocity=np.array([data.sensor(n+'_velocity').data[0] for n in names]),
                        imu_quaternion=data.sensor('imu_orientation').data.copy(),
                        imu_gyro=data.sensor('imu_angular_velocity').data.copy(), right_touch_n=read_touch(data))
                    sensors.append(packet)
                    pickle.dump(packet, process.stdin, protocol=5); process.stdin.flush()
                    response = pickle.load(process.stdout)
                    responses.append({k: v for k, v in response.items() if k != 'events'})
                    if response['error']: raise RuntimeError(response['error'])
                    data.ctrl[:] = response['torque']
                    if i % (stride*10) == 0:
                        monitor.write(json.dumps(dict(time_s=float(data.time), **{k: v for k, v in response.items()
                            if k not in {'torque', 'requested_joint_position', 'events'}}), default=plain)+'\n'); monitor.flush()
                records.append((float(data.time), data.qpos.copy(), data.qvel.copy(), data.ctrl.copy(), data.qacc_warmstart.copy()))
                if response.get('complete'): break
                mujoco.mj_step(model, data)
                if not np.isfinite(data.qpos).all() or np.any(data.warning.number): raise RuntimeError('Physics numerical failure')
                if data.qpos[2] < .6 or data.body('pelvis').xmat.reshape(3, 3)[2, 2] < .85: raise RuntimeError('Body support lost')
                if np.any(data.xfrc_applied) or np.any(data.qfrc_applied): raise RuntimeError('Unexpected external applied force')
                if i % round(.5/dt) == 0:
                    print('tool', round(float(data.time), 3), response.get('phase'),
                          'wall_s', round(time.monotonic()-started, 1), flush=True)
            if not response.get('complete'): failure = 'Duration exhausted before the attempt ended'
            elif response.get('failure'): failure = response['failure']
        except Exception as error:
            failure = str(error); print('failed', failure, flush=True)
        finally:
            process.stdin.close()
            try: process.wait(timeout=15)
            except subprocess.TimeoutExpired: process.kill(); process.wait()
    if not records or abs(records[-1][0]-data.time) > 1e-12:
        records.append((float(data.time), data.qpos.copy(), data.qvel.copy(), data.ctrl.copy(), data.qacc_warmstart.copy()))
    np.savez_compressed(output/'trace.npz', **{k: np.asarray([r[i] for r in records])
        for i, k in enumerate(['time', 'qpos', 'qvel', 'ctrl', 'qacc_warmstart'])})
    if sensors: np.savez_compressed(output/'sensors.npz', **{k: np.asarray([r[k] for r in sensors]) for k in sensors[0]})
    (output/'responses.pkl').write_bytes(pickle.dumps(responses, protocol=5))
    (output/'events.json').write_text(json.dumps(response.get('events', []), indent=2)+'\n')
    result = dict(scope=__doc__, status='failed' if failure else 'attempt_finished_pending_independent_verification',
        failure=failure, simulated_seconds=float(data.time), wall_seconds=time.monotonic()-started,
        environment='existing_complete_laboratory', contract_sha256=sha(output/'contract.json'),
        trace_sha256=sha(output/'trace.npz'), sensors_sha256=sha(output/'sensors.npz') if sensors else None,
        responses_sha256=sha(output/'responses.pkl'), actor_access_isolated=isolation['passed'],
        physics_warning_counts=data.warning.number.tolist(), qualified_grasp=False, qualified_paper_branch=False)
    (output/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('station'); p.add_argument('output')
    p.add_argument('--duration', type=float, default=20.); a = p.parse_args()
    if run(a.station, a.output, a.duration)['status'] == 'failed': raise SystemExit(1)
