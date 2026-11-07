"""Independent native replay of one unloaded G1/Dex3 walking attempt.

Checks sensor-only controller reproducibility, unchanged full-scene dynamics,
source motor limits, robot contacts, upright walking and commanded stopping.
It does not qualify carrying, navigation, equipment handling or repetition.
"""
import argparse
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
from run_dex3_walking import sha
from verify_tool_grasp import difference

VERIFIER_SHA = sha(__file__)


def verify(folder):
    folder = Path(folder).resolve()
    result = json.loads((folder / 'result.json').read_text())
    contract = json.loads((folder / 'contract.json').read_text())
    prior = json.loads((folder / 'walking_prior.json').read_text())
    isolation = json.loads((folder / 'actor_isolation.json').read_text())
    for name, key in [('trace.npz', 'trace_sha256'), ('sensors.npz', 'sensors_sha256'),
                      ('responses.pkl', 'responses_sha256'), ('contract.json', 'contract_sha256')]:
        assert sha(folder / name) == result[key]
    assert sha(folder / 'world.xml') == contract['model_sha256']
    assert sha(folder / 'walking_prior.json') == contract['prior_sha256']
    assert sha(folder / 'actor_isolation.json') == contract['actor_isolation_sha256']
    for name, digest in isolation['source_modules'].items():
        assert sha(folder / 'actor_bundle/code' / name) == digest
    assert sha(folder / 'actor_bundle/model/world.xml') == isolation['bundled_model_sha256']
    for item in isolation['input_files']:
        assert sha(folder / item['path']) == item['sha256']
    trace = dict(np.load(folder / 'trace.npz'))
    sensor = dict(np.load(folder / 'sensors.npz'))
    responses = pickle.loads((folder / 'responses.pkl').read_bytes())
    actor_module = contract.get('actor_module', 'dex3_walking_actor')
    assert actor_module in {'dex3_walking_actor', 'groot_walking_actor'}
    command = isolation['command_prefix'] + [sys.executable, '/actor/' + actor_module + '.py', '--model', '/model/world.xml']
    initial_checked = False
    if 'initial_collision_review_sha256' in contract:
        assert sha(folder / 'initial_collision_review.json') == contract['initial_collision_review_sha256']
        initial_checked = json.loads((folder / 'initial_collision_review.json').read_text())['passed']
    controller_error = 0.
    with (folder / 'controller_replay_stderr.log').open('wb') as log:
        actor = subprocess.Popen(command, env=isolation['environment'], stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=log)
        try:
            for i, expected in enumerate(responses):
                packet = {k: v[i] for k, v in sensor.items()}
                packet['depth'] = None
                pickle.dump(packet, actor.stdin, protocol=5)
                actor.stdin.flush()
                actual = pickle.load(actor.stdout)
                controller_error = max(controller_error, difference(actual, expected))
        finally:
            actor.stdin.close()
            try:
                actor.wait(timeout=15)
            except subprocess.TimeoutExpired:
                actor.kill()
                actor.wait()
    m = mujoco.MjModel.from_xml_path(str(folder / 'world.xml'))
    d = mujoco.MjData(m)
    d.qpos[:] = contract['initial_qpos']
    d.qvel[:] = contract['initial_qvel']
    mujoco.mj_forward(m, d)
    joints = robot_joints(m)
    root = m.body('pelvis').id
    robot = set()
    for body in range(m.nbody):
        parent = body
        while parent and parent != root:
            parent = int(m.body_parentid[parent])
        if parent == root:
            robot.add(body)
    imported = json.loads((folder / 'laboratory_import.json').read_text())
    floor = {part['geom'] for part in imported['parts'] if part['source_part'] in
             {'indoor_floor', 'annex_floor', 'outdoor_floor', 'outdoor_access_path'}}
    limits = contract['physical_acceptance']
    qerror = verror = sensor_error = joint_excess = 0.
    min_height = float('inf')
    min_up = 1.
    contact_failures = []
    sole_floor = np.array([d.site(side + '_sole').xpos[2] for side in ['left', 'right']])
    sole_lift = np.zeros(2)
    steps = np.zeros(2, dtype=int)
    airborne = np.zeros(2, dtype=bool)
    max_settled_speed = 0.
    packet_index = 0
    dt = m.opt.timestep
    assert abs(dt - contract['physics_period_s']) < 1e-12
    assert np.max(abs(np.diff(trace['time']) - dt)) < 1e-8
    decimation = round(contract['control_period_s'] / dt)
    started = time.monotonic()
    for i in range(len(trace['time'])):
        qerror = max(qerror, float(np.max(abs(d.qpos - trace['qpos'][i]))))
        verror = max(verror, float(np.max(abs(d.qvel - trace['qvel'][i]))))
        min_height = min(min_height, float(d.qpos[2]))
        min_up = min(min_up, float(d.xmat[root].reshape(3, 3)[2, 2]))
        for j in joints:
            joint_excess = max(joint_excess, float(m.jnt_range[j, 0] - d.qpos[m.jnt_qposadr[j]]),
                               float(d.qpos[m.jnt_qposadr[j]] - m.jnt_range[j, 1]))
        lifts = np.array([d.site(side + '_sole').xpos[2] for side in ['left', 'right']]) - sole_floor
        sole_lift = np.maximum(sole_lift, lifts)
        up = lifts > .01
        steps += up & ~airborne
        airborne = up
        if d.time >= prior['stop_at_s'] + 2.:
            max_settled_speed = max(max_settled_speed, float(np.linalg.norm(d.qvel[:2])))
        for c in d.contact:
            bodies = {int(m.geom_bodyid[g]) for g in c.geom}
            if not bodies & robot:
                continue
            names = [m.geom(int(g)).name for g in c.geom]
            foot_floor = any('ankle_roll_link_collision' in n for n in names) and bool(set(names) & floor)
            bound = limits['maximum_sole_penetration_m'] if foot_floor else limits['maximum_other_penetration_m']
            if c.dist < -bound and len(contact_failures) < 30:
                contact_failures.append(dict(time_s=float(d.time), geoms=names,
                                             penetration_m=-float(c.dist), bound_m=bound))
        if i == len(trace['time']) - 1:
            break
        if i % decimation == 0:
            packet = dict(time_s=float(d.time),
                joint_position=np.array([d.sensor(m.joint(j).name + '_encoder').data[0] for j in joints]),
                joint_velocity=np.array([d.sensor(m.joint(j).name + '_velocity').data[0] for j in joints]),
                imu_quaternion=d.sensor('imu_orientation').data.copy(), imu_gyro=d.sensor('imu_angular_velocity').data.copy())
            expected = {k: v[packet_index] for k, v in sensor.items()}
            sensor_error = max(sensor_error, difference(packet, expected))
            packet_index += 1
        d.ctrl[:] = trace['ctrl'][i]
        mujoco.mj_step(m, d)
        if i % round(.5 / dt) == 0:
            print('verify_dex3_walk', round(float(d.time), 3), 'wall_s', round(time.monotonic() - started, 1), flush=True)
    source_limits = json.loads((folder / 'source_limit_review.json').read_text())
    assert source_limits['trace_sha256'] == result['trace_sha256']
    delta = d.qpos[:2] - np.asarray(contract['initial_qpos'])[:2]
    # The preregistered staging points along world -Y, i.e. laboratory +X.
    forward, lateral = float(-delta[1]), float(abs(delta[0]))
    checks = dict(attempt_completed=result['failure'] is None and abs(d.time - contract['duration_limit_s']) < 1e-8,
        controller_replay_exact=controller_error == 0. and actor.returncode == 0,
        continuous_physics_replay=max(qerror, verror) <= limits['maximum_replay_error'],
        native_sensor_replay=sensor_error == 0. and packet_index == len(responses),
        isolated_actor=isolation['passed'], initial_pose_checked=initial_checked,
        only_robot_motor_commands=m.nu == 43 and all(int(m.jnt_bodyid[j]) in robot for j in m.actuator_trnid[:, 0]),
        no_external_equalities=m.neq == 0,
        no_external_forces=not np.any(d.xfrc_applied) and not np.any(d.qfrc_applied),
        no_numerical_warnings=not np.any(d.warning.number), source_motor_limits=source_limits['passed'],
        source_joint_positions=joint_excess <= limits['maximum_source_joint_limit_excess_rad'],
        upright=min_height >= limits['minimum_pelvis_height_m'] and min_up >= limits['minimum_upright_cosine'],
        robot_contact_bounds=not contact_failures, both_feet_step=bool(np.all(steps >= 2)),
        forward_distance=forward >= contract['required_forward_m'],
        lateral_deviation=lateral <= contract['maximum_lateral_m'],
        commanded_stop=max_settled_speed <= contract['maximum_settled_speed_m_s'])
    report = dict(scope=__doc__, passed=all(checks.values()), checks=checks,
        trace_sha256=result['trace_sha256'], contract_sha256=result['contract_sha256'],
        model_sha256=contract['model_sha256'], verifier_sha256=VERIFIER_SHA,
        maximum_qpos_replay_error=qerror, maximum_qvel_replay_error=verror,
        maximum_sensor_replay_error=sensor_error, controller_replay_error=controller_error,
        compared_sensor_packets=packet_index, minimum_pelvis_height_m=min_height, minimum_upright_cosine=min_up,
        maximum_joint_position_excess_rad=joint_excess, unexpected_contacts=contact_failures,
        steps=steps.tolist(), maximum_sole_lift_m=sole_lift.tolist(),
        forward_m=forward, lateral_m=lateral, maximum_settled_speed_m_s=max_settled_speed,
        qualified_walking=False, qualified_carry=False, qualified_paper_branch=False)
    shutil.copyfile(__file__, folder / 'walking_verifier.py')
    (folder / 'walking_review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder')
    verify(p.parse_args().folder)
