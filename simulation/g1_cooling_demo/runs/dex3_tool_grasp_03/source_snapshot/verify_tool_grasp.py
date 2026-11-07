"""Independently replay and evaluate a recorded full-G1 tool attempt.

The evaluator reads plant truth. Its verdict is never supplied to the actor.
A passing single attempt would still not grant repeated skill qualification.
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


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# Capture the bytes actually loaded, not a possibly edited file at report time.
VERIFIER_SHA256 = sha(__file__)


def difference(a, b):
    if isinstance(a, dict):
        if not isinstance(b, dict) or set(a) != set(b): return float('inf')
        return max([difference(a[k], b[k]) for k in a]+[0.])
    if isinstance(a, (list, tuple)):
        if not isinstance(b, (list, tuple)) or len(a) != len(b): return float('inf')
        return max([difference(x, y) for x, y in zip(a, b)]+[0.])
    if isinstance(a, np.ndarray):
        try:
            aa, bb = np.asarray(a), np.asarray(b)
            if aa.shape != bb.shape: return float('inf')
            if aa.dtype.kind == 'b': return 0. if np.array_equal(aa, bb) else float('inf')
            return float(np.max(abs(aa-bb), initial=0.))
        except (TypeError, ValueError): return float('inf')
    if isinstance(a, (float, int, np.number)) and not isinstance(a, bool): return abs(float(a)-float(b))
    return 0. if a == b else float('inf')


def controller(folder):
    result = json.loads((folder/'result.json').read_text())
    contract = json.loads((folder/'contract.json').read_text())
    assert sha(folder/'contract.json') == result['contract_sha256']
    assert sha(folder/'sensors.npz') == result['sensors_sha256']
    assert sha(folder/'responses.pkl') == result['responses_sha256']
    sensor = dict(np.load(folder/'sensors.npz'))
    # This is a locally generated, hash-pinned run artifact, not untrusted input.
    responses = pickle.loads((folder/'responses.pkl').read_bytes())
    receipt = json.loads((folder/'actor_isolation.json').read_text())
    if 'actor_isolation_sha256' in contract:
        assert sha(folder/'actor_isolation.json') == contract['actor_isolation_sha256']
        assert sha(folder/'policy_source/tool_prior.json') == contract['controller_prior_sha256']
        for name,digest in contract['source_snapshot_sha256'].items(): assert sha(folder/'source_snapshot'/name)==digest
    for name, digest in receipt['source_modules'].items(): assert sha(folder/'actor_bundle/code'/name) == digest
    assert sha(folder/'actor_bundle/model/world.xml') == receipt['bundled_model_sha256']
    actor = contract.get('actor_module', 'tool_grasp_actor')
    assert actor in {'tool_grasp_actor', 'dex3_tool_actor'}
    command = receipt['command_prefix']+[sys.executable, '/actor/'+actor+'.py', '--model', '/model/world.xml']
    error = 0.; compared = 0; failure = None
    with (folder/'controller_replay_stderr.log').open('wb') as log:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, env=receipt['environment'])
        try:
            for i, expected in enumerate(responses):
                packet = {k: v[i] for k, v in sensor.items()}
                pickle.dump(packet, process.stdin, protocol=5); process.stdin.flush()
                response = pickle.load(process.stdout)
                actual = {k: v for k, v in response.items() if k != 'events'}
                error = max(error, difference(expected, actual)); compared += 1
                if response['error']: break
            expected_events = json.loads((folder/'events.json').read_text())
            error = max(error, difference(expected_events, response.get('events', [])))
        except Exception as exc: failure = str(exc)
        finally:
            process.stdin.close()
            try: process.wait(timeout=15)
            except subprocess.TimeoutExpired: process.kill(); process.wait()
    report = dict(passed=failure is None and compared == len(responses) == len(sensor['time_s']) and error < 1e-10,
        failure=failure, compared=compared, responses=len(responses), sensor_packets=len(sensor['time_s']),
        maximum_response_error=None if not np.isfinite(error) else error,
        replayed_frozen_isolated_actor=True, verifier_sha256=VERIFIER_SHA256, qualified_grasp=False)
    (folder/'controller_replay.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def physics(folder):
    result = json.loads((folder/'result.json').read_text()); contract = json.loads((folder/'contract.json').read_text())
    assert sha(folder/'contract.json') == result['contract_sha256']
    assert sha(folder/'trace.npz') == result['trace_sha256']
    assert sha(folder/'world.xml') == contract['model_sha256']
    trace = dict(np.load(folder/'trace.npz')); sensor = dict(np.load(folder/'sensors.npz'))
    m = mujoco.MjModel.from_xml_path(str(folder/'world.xml')); d = mujoco.MjData(m)
    d.qpos[:] = trace['qpos'][0]; d.qvel[:] = trace['qvel'][0]; mujoco.mj_forward(m, d)
    d.qacc_warmstart[:] = trace['qacc_warmstart'][0]
    robot = {m.body('pelvis').id}; tool = {m.body('tweezer').id}
    for b in range(m.nbody):
        if m.body_parentid[b] in robot: robot.add(b)
        if m.body_parentid[b] in tool: tool.add(b)
    allowed = {m.body(n).id for n in contract['allowed_tool_contact_bodies']}
    tray = m.body('carrier_tray').id
    imported_path = folder/'laboratory_import.json'
    if imported_path.exists():
        assert sha(imported_path) == contract['laboratory_import_sha256']
    else: imported_path = Path(__file__).parent/'runs/ftir_approach_11/laboratory_import.json'
    imported = json.loads(imported_path.read_text())
    floor = {p['geom'] for p in imported['parts'] if p['source_part'] in {'indoor_floor', 'annex_floor', 'outdoor_floor', 'outdoor_access_path'}}
    bench = {p['geom'] for p in imported['parts'] if p['source_part'] == 'ftir_bench_worktop'}
    # Define physical material endpoints from the undeformed tool, not from
    # the already settled or grasped shape whose gap is being evaluated.
    rest = mujoco.MjData(m); rest.qpos[:] = trace['qpos'][0]
    for j in range(m.njnt):
        if int(m.jnt_bodyid[j]) in tool and m.jnt_type[j] == mujoco.mjtJoint.mjJNT_HINGE:
            rest.qpos[m.jnt_qposadr[j]] = 0.
    mujoco.mj_kinematics(m, rest); endpoints = {}
    root = m.body('tweezer').id
    for label, sign in [('negative', -1.), ('positive', 1.)]:
        b = max((b for b in tool if m.body(b).name.startswith(label+'_beam_')), key=lambda b: m.body(b).name)
        point = rest.xpos[root]+rest.xmat[root].reshape(3, 3)@np.array([-.130, sign*.004, 0.])
        endpoints[label] = (b, rest.xmat[b].reshape(3, 3).T@(point-rest.xpos[b]))
    joint = m.joint('tweezer_free'); qtool = int(joint.qposadr[0]); vtool = int(joint.dofadr[0])
    initial_z = float(trace['qpos'][0, qtool+2]); dt = float(m.opt.timestep)
    limits = contract['physical_acceptance']; stride = round(contract['control_period_s']/dt)
    dex3 = contract.get('hand_kind') == 'unitree_three_finger'
    encoder_names = [m.joint(j).name for j in range(m.njnt) if int(m.jnt_bodyid[j]) in robot and m.jnt_type[j] == mujoco.mjtJoint.mjJNT_HINGE]
    qerr = verr = sensor_error = max_pen = support_pen = max_force = joint_excess = 0.
    bilateral = held_lift = final_support = 0.; min_gap = float('inf'); peak_height = 0.; unexpected_load = 0.
    unexpected = []; samples = []; released = []; minimum_height = float('inf'); minimum_upright = 1.
    started = time.monotonic(); compared_sensors = 0
    def observe():
        packet = dict(time_s=float(d.time), joint_position=np.array([d.sensor(n+'_encoder').data[0] for n in encoder_names]),
            joint_velocity=np.array([d.sensor(n+'_velocity').data[0] for n in encoder_names]),
            imu_quaternion=d.sensor('imu_orientation').data.copy(), imu_gyro=d.sensor('imu_angular_velocity').data.copy())
        if not dex3:
            packet['right_touch_n'] = np.array([d.sensor(n+'_touch').data[0] for n in
                ['right_index_force_sensor_'+str(k) for k in range(1,4)]+['right_thumb_force_sensor_'+str(k) for k in range(1,5)]])
        return packet
    for i in range(len(trace['time'])-1):
        if i % stride == 0 and compared_sensors < len(sensor['time_s']):
            row = compared_sensors
            observed = observe()
            sensor_error = max(sensor_error, difference({k: v[row] for k, v in sensor.items()}, observed)); compared_sensors += 1
        d.ctrl[:] = trace['ctrl'][i]; mujoco.mj_step(m, d)
        qerr = max(qerr, float(np.max(abs(d.qpos-trace['qpos'][i+1]))))
        verr = max(verr, float(np.max(abs(d.qvel-trace['qvel'][i+1]))))
        forces = {'index': 0., 'thumb': 0., **({'middle': 0.} if dex3 else {})}; support_force = 0.
        for ci, c in enumerate(d.contact):
            bs = [int(m.geom_bodyid[g]) for g in c.geom]; names = [m.geom(int(g)).name for g in c.geom]
            if not (set(bs)&(robot|tool|{tray})): continue
            is_tool = [b in tool for b in bs]; load = np.zeros(6); mujoco.mj_contactForce(m, d, ci, load)
            if sum(is_tool) == 1 and bool(set(bs)&robot) and not bool(set(bs)&allowed):
                unexpected_load = max(unexpected_load, max(0., float(load[0])))
            if sum(is_tool) == 1 and bool(set(bs)&allowed):
                body = next(m.body(b).name for b in bs if b in allowed)
                forces[next(f for f in forces if f in body)] += max(0., float(load[0]))
                max_pen = max(max_pen, -float(c.dist)); bound = limits['maximum_hand_tool_penetration_m']
            elif bool(set(bs)&tool) and (tray in bs or bool(set(names)&bench)):
                support_force += max(0., float(load[0])); support_pen = max(support_pen, -float(c.dist))
                bound = limits['maximum_passive_support_penetration_m']
            elif tray in bs and bool(set(names)&bench):
                bound = limits['maximum_passive_support_penetration_m']
            elif any('ankle_roll_link_collision' in n for n in names) and bool(set(names)&floor):
                bound = limits['maximum_sole_penetration_m']
            else: bound = limits['maximum_other_penetration_m']
            if c.dist < -bound and len(unexpected) < 30:
                unexpected.append(dict(time_s=float(trace['time'][i]), parts=names, penetration_m=-float(c.dist), bound_m=bound))
        loaded = (forces['thumb'] > limits['minimum_thumb_load_n'] and
                  min(forces['index'],forces['middle']) > limits['minimum_each_opposing_finger_load_n']) if dex3 else min(forces.values()) > limits['minimum_bilateral_finger_load_n']
        if loaded: bilateral += dt
        max_force = max(max_force, max(forces.values()))
        height = float(trace['qpos'][i, qtool+2]-initial_z); peak_height = max(peak_height, height)
        if loaded and height >= limits['minimum_actual_tool_lift_m'] and support_force < .01: held_lift += dt
        points = {label: d.xpos[b]+d.xmat[b].reshape(3, 3)@point for label, (b, point) in endpoints.items()}
        gap = float(np.linalg.norm(points['positive']-points['negative']))
        if loaded: min_gap = min(min_gap, gap)
        if trace['time'][i] >= trace['time'][-1]-1.:
            released.append(gap)
            if (support_force >= limits.get('minimum_final_tool_support_force_n', .15)
                and max(forces.values()) <= limits.get('maximum_released_finger_force_n', .02)
                and np.linalg.norm(trace['qvel'][i, vtool:vtool+3]) <= limits.get('maximum_final_tool_speed_m_s', .005)):
                final_support += dt
        minimum_height = min(minimum_height, float(trace['qpos'][i, 2]))
        minimum_upright = min(minimum_upright, float(d.body('pelvis').xmat.reshape(3, 3)[2, 2]))
        for j in range(m.njnt):
            if m.jnt_limited[j] and int(m.jnt_bodyid[j]) in robot:
                value = trace['qpos'][i, m.jnt_qposadr[j]]
                joint_excess = max(joint_excess, m.jnt_range[j, 0]-value, value-m.jnt_range[j, 1])
        if i % stride == 0: samples.append([float(trace['time'][i]), height, gap, forces['index'], forces['thumb'], support_force]+([forces['middle']] if dex3 else []))
        if i % round(.5/dt) == 0: print('verify_tool', round(float(d.time), 3), 'wall_s', round(time.monotonic()-started, 1), flush=True)
    if compared_sensors == len(sensor['time_s'])-1 and abs(float(sensor['time_s'][-1])-d.time) < 1e-9:
        observed = observe()
        sensor_error = max(sensor_error, difference({k: v[-1] for k, v in sensor.items()}, observed)); compared_sensors += 1
    checks = dict(attempt_completed=result['failure'] is None,
        exact_continuous_physics_replay=len(trace['time']) > 1 and max(qerr, verr) <= limits['maximum_replay_error'],
        native_sensor_replay=sensor_error <= 1e-10 and compared_sensors == len(sensor['time_s']),
        only_robot_actuators=all(int(m.jnt_bodyid[j]) in robot for j in m.actuator_trnid[:, 0]) and m.nu == contract.get('actuator_count',41),
        only_robot_equalities=all(int(m.jnt_bodyid[j]) in robot for j in np.r_[m.eq_obj1id, m.eq_obj2id]),
        no_external_forces=not np.any(d.xfrc_applied) and not np.any(d.qfrc_applied),
        no_numerical_warnings=not any(d.warning.number), contact_bounds=not unexpected,
        bilateral_contact=bilateral >= limits['minimum_bilateral_contact_s'],
        tool_lifted_while_held=held_lift >= limits['minimum_lift_hold_s'],
        loaded_tool_closure=min_gap <= .008-limits['minimum_loaded_tip_closure_m'],
        released_gap_recovers=bool(released) and max(abs(g-.008) for g in released) <= limits['released_tip_gap_tolerance_m'],
        released_stable_support=final_support >= limits.get('final_released_support_hold_s', 1.)-dt*1.1,
        source_joint_limits=joint_excess <= limits['maximum_source_joint_limit_excess_rad'],
        supported_upright=minimum_height >= limits['minimum_pelvis_height_m'] and minimum_upright >= limits['minimum_upright_cosine'],
        bounded_finger_load=max_force <= limits['maximum_normal_force_n'])
    checks['no_unintended_hand_tool_load'] = unexpected_load <= limits.get('maximum_unintended_hand_tool_load_n', .05)
    if dex3:
        assert contract['task'] == 'pickup_hold_replace_release' and limits['require_loaded_tool_closure'] is False
        del checks['loaded_tool_closure']
        del checks['bilateral_contact']
        checks['three_finger_contact'] = bilateral >= limits['minimum_three_finger_contact_s']
    report = dict(scope=__doc__, passed=bool(all(checks.values())), checks={k: bool(v) for k, v in checks.items()},
        max_q_replay_error=qerr, max_v_replay_error=verr, max_sensor_replay_error=sensor_error,
        compared_sensor_packets=compared_sensors, bilateral_contact_s=bilateral, held_lift_s=held_lift,
        peak_tool_height_change_m=peak_height, minimum_loaded_tip_gap_m=None if not np.isfinite(min_gap) else min_gap,
        final_released_support_s=final_support, maximum_finger_force_n=max_force,
        maximum_unintended_hand_tool_load_n=unexpected_load,
        maximum_joint_limit_excess_rad=float(joint_excess), unintended_contacts=unexpected,
        source_model_sha256=sha(folder/'world.xml'), source_trace_sha256=sha(folder/'trace.npz'),
        verifier_sha256=VERIFIER_SHA256, qualified_grasp=False, qualified_paper_branch=False)
    if dex3:
        report['three_finger_contact_s'] = report.pop('bilateral_contact_s')
        report['tool_use_closure_evaluated'] = False
    np.savez_compressed(folder/'physical_samples.npz', samples=np.asarray(samples))
    (folder/'physical_review.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('folder'); p.add_argument('--controller-only', action='store_true')
    p.add_argument('--physics-only', action='store_true'); a = p.parse_args(); folder = Path(a.folder).resolve()
    if not a.physics_only: print(json.dumps(controller(folder)), flush=True)
    if not a.controller_only: print(json.dumps(physics(folder)), flush=True)
