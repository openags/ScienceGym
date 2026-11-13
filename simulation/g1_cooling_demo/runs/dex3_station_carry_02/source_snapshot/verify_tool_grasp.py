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


def carry_reference_index(contract, events, times):
    """Select a recorded stance, excluding preceding unloaded travel.

    The handoff event is checked against frozen isolated-controller replay.
    Missing, duplicate or off-grid handoffs cannot establish a carry origin.
    Historical standalone carrying contracts retain their initial stance.
    """
    reference = contract['carry_contract'].get('reference_state', 'initial_state')
    if reference == 'initial_state':
        return 0
    if reference != 'sensor_based_pickup_handoff' or contract.get('actor_module') != 'station_pickup_actor':
        raise ValueError('Unsupported carrying reference state')
    marks = [e for e in events if e.get('kind') == reference]
    if len(marks) != 1 or not np.isfinite(marks[0]['time_s']):
        return None
    index = int(np.argmin(abs(times-marks[0]['time_s'])))
    if abs(float(times[index])-marks[0]['time_s']) > 1e-8:
        return None
    return index


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


def controller(folder, report_name='controller_replay.json'):
    if Path(report_name).name != report_name or not report_name.endswith('.json'):
        raise ValueError('Controller report must be a JSON filename within the recording')
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
    for item in receipt.get('input_files', []):
        assert sha(folder/item['path']) == item['sha256']
    actor = contract.get('actor_module', 'tool_grasp_actor')
    assert actor in {'tool_grasp_actor', 'dex3_tool_actor','visual_tool_actor','carry_tool_actor','station_pickup_actor'}
    visual=bool(contract.get('observed_approach',False));camera_index=[]
    if visual:
        assert sha(folder/'camera_index.json')==result['camera_index_sha256']
        camera_index=json.loads((folder/'camera_index.json').read_text())
        for row in camera_index:assert sha(folder/row['file'])==row['sha256']
    command = receipt['command_prefix']+[sys.executable, '/actor/'+actor+'.py', '--model', '/model/world.xml']
    error = 0.; compared = 0; failure = None;camera_frames_replayed=0
    retained_events = []; response = {}; event_error = None
    with (folder/(Path(report_name).stem+'_stderr.log')).open('wb') as log:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, env=receipt['environment'])
        try:
            for i, expected in enumerate(responses):
                packet = {k: v[i] for k, v in sensor.items()}
                if visual:
                    frame=int(packet.pop('camera_frame_id'))
                    if frame>=0:
                        entry=camera_index[frame]
                        assert entry['id']==frame and abs(entry['time_s']-float(packet['time_s']))<1e-9
                        with np.load(folder/entry['file']) as values:packet.update({k:values[k] for k in values.files})
                        camera_frames_replayed+=1
                    else:packet.update(head_rgb=None,head_depth=None)
                pickle.dump(packet, process.stdin, protocol=5); process.stdin.flush()
                response = pickle.load(process.stdout)
                # Match the recorder: terminal exception replies may omit
                # events, while its event file retains the last actual list.
                if 'events' in response:
                    retained_events = response['events']
                actual = {k: v for k, v in response.items() if k != 'events'}
                error = max(error, difference(expected, actual)); compared += 1
                if response['error']: break
            expected_events = json.loads((folder/'events.json').read_text())
            # Older tool recordings predate the result-level event digest.
            # Still compare their full history against the replayed actor;
            # report the missing historical pin instead of inventing one.
            if result.get('events_sha256') is not None:
                assert sha(folder/'events.json') == result['events_sha256']
            event_error = difference(expected_events, retained_events)
            error = max(error, event_error)
        except Exception as exc: failure = str(exc)
        finally:
            process.stdin.close()
            try: process.wait(timeout=15)
            except subprocess.TimeoutExpired: process.kill(); process.wait()
    report = dict(passed=failure is None and compared == len(responses) == len(sensor['time_s']) and error < 1e-10,
        failure=failure, compared=compared, responses=len(responses), sensor_packets=len(sensor['time_s']),
        maximum_response_error=None if not np.isfinite(error) else error,
        final_event_history_error=None if event_error is None or not np.isfinite(event_error) else event_error,
        event_history_sha256=sha(folder/'events.json'),
        event_history_pinned_by_recording=result.get('events_sha256') is not None,
        recorded_actor_error=response.get('error'), recorded_execution_failure=result['failure'],
        replayed_frozen_isolated_actor=True, verifier_sha256=VERIFIER_SHA256, qualified_grasp=False)
    if visual:
        report.update(camera_frames_replayed=camera_frames_replayed,camera_frames_recorded=len(camera_index))
        report['passed']=bool(report['passed'] and camera_frames_replayed==len(camera_index)>0)
    (folder/report_name).write_text(json.dumps(report, indent=2)+'\n')
    return report


def physics(folder):
    result = json.loads((folder/'result.json').read_text()); contract = json.loads((folder/'contract.json').read_text())
    assert sha(folder/'contract.json') == result['contract_sha256']
    assert sha(folder/'trace.npz') == result['trace_sha256']
    assert sha(folder/'sensors.npz') == result['sensors_sha256']
    assert sha(folder/'world.xml') == contract['model_sha256']
    trace = dict(np.load(folder/'trace.npz')); sensor = dict(np.load(folder/'sensors.npz'))
    plugins = contract.get('collision_plugins', [])
    if plugins:
        from frozen_collision_plugins import load, require_stateless
        load(plugins, contract['source_snapshot_sha256']['frozen_collision_plugins.py'])
    m = mujoco.MjModel.from_xml_path(str(folder/'world.xml')); d = mujoco.MjData(m)
    if plugins: require_stateless(m)
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
    visual=bool(contract.get('observed_approach',False));cameras=None;camera_index=[]
    camera_depth_error=0.;camera_rgb_error=0.;compared_camera_frames=0
    if visual:
        from tool_cameras import ToolCameras
        from sensor_rendering import depth_renderer
        assert sha(Path(__file__).parent/'tool_cameras.py')==contract['camera_contract']['renderer_sha256']
        assert sha(Path(__file__).parent/'sensor_rendering.py')==contract['camera_contract']['depth_helper_sha256']
        assert sha(folder/'camera_index.json')==result['camera_index_sha256']
        camera_index=json.loads((folder/'camera_index.json').read_text())
        for row in camera_index:assert sha(folder/row['file'])==row['sha256']
        cameras=ToolCameras(m)
    encoder_names = [m.joint(j).name for j in range(m.njnt) if int(m.jnt_bodyid[j]) in robot and m.jnt_type[j] == mujoco.mjtJoint.mjJNT_HINGE]
    qerr = verr = sensor_error = max_pen = support_pen = max_force = joint_excess = 0.
    bilateral = held_lift = final_support = 0.; min_gap = float('inf'); peak_height = 0.; unexpected_load = 0.
    unexpected = []; samples = []; released = []; minimum_height = float('inf'); minimum_upright = 1.
    carrying=contract.get('task')=='visual_pickup_loaded_out_and_back_release'
    if carrying:
        carry_limits=contract['carry_contract']
        carry_events=json.loads((folder/'events.json').read_text())
        assert sha(folder/'events.json') == result['events_sha256']
        carry_origin_index=carry_reference_index(contract,carry_events,trace['time'])
        carry_reference_valid=carry_origin_index is not None
        carry_origin_index=0 if carry_origin_index is None else carry_origin_index
        carry_reference=mujoco.MjData(m)
        carry_reference.qpos[:]=trace['qpos'][carry_origin_index]
        mujoco.mj_kinematics(m,carry_reference)
        carry_origin_xy=trace['qpos'][carry_origin_index,:2].copy()
        carry_phases={e['phase']:e['time_s'] for e in carry_events if 'phase' in e}
        carry_start=carry_phases.get('carry_preload',carry_phases.get('carry_raise',float('inf')))
        carry_end=carry_phases.get('lower',float(trace['time'][-1]))
        forward=carry_reference.body('pelvis').xmat.reshape(3,3)[:2,0].copy();forward/=np.linalg.norm(forward)
        sole_ids=[m.site(s+'_sole').id for s in ['left','right']]
        sole_floor=carry_reference.site_xpos[sole_ids,2].copy();sole_lifts=np.zeros(2)
        base_excursion=0.;lost_load=0.;maximum_lost_load=0.;held_carry_s=0.
        wrist_tool_initial=None;wrist_tool_drift=0.
        wrist_rotation_initial=None;wrist_rotation_change=0.
        prelift_loaded_s=0.
        first_lift=carry_phases.get('lift',float('inf'))
    started = time.monotonic(); compared_sensors = 0
    def observe():
        packet = dict(time_s=float(d.time), joint_position=np.array([d.sensor(n+'_encoder').data[0] for n in encoder_names]),
            joint_velocity=np.array([d.sensor(n+'_velocity').data[0] for n in encoder_names]),
            imu_quaternion=d.sensor('imu_orientation').data.copy(), imu_gyro=d.sensor('imu_angular_velocity').data.copy())
        if not dex3:
            packet['right_touch_n'] = np.array([d.sensor(n+'_touch').data[0] for n in
                ['right_index_force_sensor_'+str(k) for k in range(1,4)]+['right_thumb_force_sensor_'+str(k) for k in range(1,5)]])
        return packet
    def compare_packet(row):
        nonlocal sensor_error,compared_sensors,camera_depth_error,camera_rgb_error,compared_camera_frames
        expected={k:v[row] for k,v in sensor.items() if k!='camera_frame_id'}
        sensor_error=max(sensor_error,difference(expected,observe()));compared_sensors+=1
        if visual and int(sensor['camera_frame_id'][row])>=0:
            frame=int(sensor['camera_frame_id'][row]);entry=camera_index[frame]
            assert entry['id']==frame and abs(entry['time_s']-float(d.time))<1e-8
            actual=cameras.read(d)
            with np.load(folder/entry['file']) as expected:
                camera_rgb_error=max(camera_rgb_error,float(np.max(abs(actual['head_rgb'].astype(float)-expected['head_rgb'].astype(float)))))
                camera_depth_error=max(camera_depth_error,float(np.max(abs(actual['head_depth']-expected['head_depth']))))
            compared_camera_frames+=1
    for i in range(len(trace['time'])-1):
        if i % stride == 0 and compared_sensors < len(sensor['time_s']):
            compare_packet(compared_sensors)
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
        if carrying and carry_limits.get('preload_before_lift'):
            window=carry_limits['minimum_native_loaded_before_lift_s']
            if first_lift-window<=trace['time'][i]<first_lift and loaded:prelift_loaded_s+=dt
        max_force = max(max_force, max(forces.values()))
        height = float(trace['qpos'][i, qtool+2]-initial_z); peak_height = max(peak_height, height)
        if loaded and height >= limits['minimum_actual_tool_lift_m'] and support_force < .01: held_lift += dt
        if carrying and carry_start<=trace['time'][i]<carry_end:
            held=loaded and height>=limits['minimum_actual_tool_lift_m'] and support_force<.01
            lost_load=0. if held else lost_load+dt
            maximum_lost_load=max(maximum_lost_load,lost_load)
            if held:
                held_carry_s+=dt
                base_excursion=max(base_excursion,float(-forward@(trace['qpos'][i,:2]-carry_origin_xy)))
                sole_lifts=np.maximum(sole_lifts,d.site_xpos[sole_ids,2]-sole_floor)
            wrist=d.site('right_wrist_reference')
            relative=wrist.xmat.reshape(3,3).T@(d.body('tweezer').xpos-wrist.xpos)
            if wrist_tool_initial is None:wrist_tool_initial=relative.copy()
            wrist_tool_drift=max(wrist_tool_drift,float(np.linalg.norm(relative-wrist_tool_initial)))
            rotation=wrist.xmat.reshape(3,3)
            if wrist_rotation_initial is None:wrist_rotation_initial=rotation.copy()
            angle=float(np.arccos(np.clip((np.trace(rotation@wrist_rotation_initial.T)-1.)/2.,-1.,1.)))
            wrist_rotation_change=max(wrist_rotation_change,angle)
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
        compare_packet(len(sensor['time_s'])-1)
    if cameras is not None:cameras.close()
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
        assert contract['task'] in {'pickup_hold_replace_release','visual_pickup_loaded_out_and_back_release'} and limits['require_loaded_tool_closure'] is False
        del checks['loaded_tool_closure']
        del checks['bilateral_contact']
        checks['three_finger_contact'] = bilateral >= limits['minimum_three_finger_contact_s']
    if visual:
        checks['native_camera_replay']=compared_camera_frames==len(camera_index)>0 and camera_rgb_error==0. and camera_depth_error<=1e-7
        events=json.loads((folder/'events.json').read_text())
        phases={e['phase']:e['time_s'] for e in events if 'phase' in e}
        plans=[e for e in events if e.get('kind')=='observed_tool_plan']
        checks['observed_approach_before_grasp']=bool(len(plans)==1 and
            phases.get('approach',float('inf'))<phases.get('settle',-1)<phases.get('close',-1) and
            sum(e['time_s']<=phases.get('approach',-1) for e in camera_index)>=4)
    if carrying:
        expected=['carry_raise','carry_retract','carry_walk_out','carry_pause','carry_walk_back',
                  'carry_align','carry_extend','carry_descend','lower','release','withdraw','rest','finished']
        if carry_limits.get('withdrawal_mode')=='body_translation':
            assert carry_limits['arm_withdrawal_m']==0.
            expected=[p for p in expected if p not in {'carry_retract','carry_extend'}]
            checks['held_wrist_orientation_stable']=(wrist_rotation_initial is not None and
                wrist_rotation_change<=carry_limits['maximum_wrist_rotation_change_rad'])
        times=[carry_phases.get(p,float('nan')) for p in expected]
        checks.update(carry_reference_established=carry_reference_valid,
            loaded_route_order=bool(np.isfinite(times).all() and np.all(np.diff(times)>0.)),
            base_moved_while_tool_held=base_excursion>=carry_limits['minimum_actual_base_excursion_m'],
            both_feet_stepped_while_tool_held=bool(np.all(sole_lifts>=carry_limits['minimum_each_sole_lift_m'])),
            carry_load_continuity=held_carry_s>0. and maximum_lost_load<=carry_limits['maximum_contiguous_lost_load_s'],
            carried_tool_wrist_drift=wrist_tool_initial is not None and wrist_tool_drift<=carry_limits['maximum_tool_wrist_position_drift_m'],
            returned_base=bool(carry_reference_valid and np.linalg.norm(trace['qpos'][-1,:2]-carry_origin_xy)<=carry_limits['maximum_final_base_xy_error_m']),
            returned_tool=bool(np.linalg.norm(trace['qpos'][-1,qtool:qtool+3]-trace['qpos'][0,qtool:qtool+3])<=carry_limits['maximum_final_tool_position_error_m']))
        if carry_limits.get('preload_before_lift'):
            configs=[e for e in carry_events if e.get('kind')=='carrying_force_before_lift']
            checks['carry_preload_before_lift']=bool(len(configs)==1 and
                carry_phases.get('close',float('inf'))<=configs[0]['time_s']<first_lift and
                prelift_loaded_s>=carry_limits['minimum_native_loaded_before_lift_s']-dt-1e-9)
        elif carry_limits.get('preload_force_increase'):
            checks['carry_preload_before_motion']=carry_phases.get('carry_preload',float('inf'))<carry_phases.get('carry_raise',-1.)
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
    if visual:report.update(compared_camera_frames=compared_camera_frames,maximum_rgb_error_uint8=camera_rgb_error,
        maximum_depth_error_m=camera_depth_error,qualified_approach=False)
    if carrying:
        report.update(qualified_carry=False,carry_metrics=dict(base_excursion_while_held_m=base_excursion,
            maximum_sole_lifts_while_held_m=sole_lifts.tolist(),held_carry_s=held_carry_s,
            maximum_contiguous_lost_load_s=maximum_lost_load,maximum_tool_wrist_position_drift_m=wrist_tool_drift))
        report['carry_metrics'].update(reference_state=carry_limits.get('reference_state','initial_state'),
            reference_established=carry_reference_valid,
            reference_time_s=float(trace['time'][carry_origin_index]) if carry_reference_valid else None,
            reference_base_xy_m=carry_origin_xy.tolist() if carry_reference_valid else None)
        if carry_limits.get('preload_before_lift'):report['carry_metrics']['native_prelift_loaded_s']=prelift_loaded_s
        if carry_limits.get('withdrawal_mode')=='body_translation':
            report['carry_metrics']['maximum_wrist_rotation_change_rad']=wrist_rotation_change
    np.savez_compressed(folder/'physical_samples.npz', samples=np.asarray(samples))
    (folder/'physical_review.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('folder'); p.add_argument('--controller-only', action='store_true')
    p.add_argument('--physics-only', action='store_true')
    p.add_argument('--controller-report', default='controller_replay.json',
                   help='Separate report filename for an explicitly revised controller review')
    a = p.parse_args(); folder = Path(a.folder).resolve()
    if not a.physics_only: print(json.dumps(controller(folder, a.controller_report)), flush=True)
    if not a.controller_only: print(json.dumps(physics(folder)), flush=True)
