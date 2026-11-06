"""Test the existing official body policy in the unchanged complete Dex3 lab.

The robot is staged in the existing front aisle before time zero. The default
plant is byte-identical to the source. An optional authored sole-contact time
constant creates a new, separately evaluated contact-response candidate; it
does not change geometry, masses, limits or acceptance. Only motor torques
advance the state after initialization; no carrying or navigation credit is granted.
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
import xml.etree.ElementTree as ET

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


def run(source, folder, duration=12., speed=.2, stop_at=8., hand_posture='open', minimum_shoulder_abduction=None,
        policy_family='unitree', sole_time_constant=None, waypoint_forward=None, station_approach=False,
        station_pickup=False):
    if station_pickup and not station_approach:
        raise ValueError('Continuous station pickup requires the existing-station approach')
    if station_approach and waypoint_forward is None:
        raise ValueError('An authored station approach requires the sensor-based waypoint mode')
    if waypoint_forward is not None and (policy_family != 'groot' or not 1. <= waypoint_forward <= 3.):
        raise ValueError('This unloaded aisle waypoint trial requires Groot and a 1 to 3 m declared goal')
    if waypoint_forward is not None and duration < stop_at + 3.5:
        raise ValueError('Reserve at least 3.5 seconds after the approach timeout for stopping checks')
    source, folder = Path(source).resolve(), Path(folder).resolve()
    folder.mkdir(parents=True, exist_ok=False)
    source_contract = json.loads((source / 'contract.json').read_text())
    assert sha(source / 'world.xml') == source_contract['model_sha256']
    assert source_contract['hand_kind'] == 'unitree_three_finger'
    policy = HERE / ('locomotion_policy' if policy_family == 'unitree' else 'locomotion_groot_policy')
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
    contact_revision = None
    if sole_time_constant is not None:
        if not .001 <= sole_time_constant <= .02:
            raise ValueError('Sole contact time constant must be between 1 and 20 ms')
        xml = ET.parse(folder / 'world.xml')
        imported = json.loads((folder / 'laboratory_import.json').read_text())
        floors = {part['geom'] for part in imported['parts'] if part['source_part'] in
                  {'indoor_floor', 'annex_floor', 'outdoor_floor', 'outdoor_access_path'}}
        changed = []
        # Explicit contact pairs override geom solref. The earlier geom-only
        # candidate left all 32 sole/floor pairs unchanged and had no effect.
        for pair in xml.findall('contact/pair'):
            names = [pair.get('geom1', ''), pair.get('geom2', '')]
            if any('ankle_roll_link_collision' in name for name in names) and set(names) & floors:
                before = pair.get('solref', '0.02 1')
                pair.set('solref', f'{sole_time_constant:g} 1')
                changed.append(dict(geoms=names, previous_solref=before, candidate_solref=pair.get('solref')))
        assert len(changed) == 32
        xml.write(folder / 'world.xml', encoding='unicode')
        contact_revision = dict(scope='Authored numerical contact-response candidate, not a measured sole material constant',
            changed=changed, source_world_sha256=source_contract['model_sha256'],
            candidate_world_sha256=sha(folder / 'world.xml'), geometry_masses_and_actuators_changed=False,
            acceptance_changed=False, physical_response_changed=True,
            basis='The unchanged official-policy trial exceeds the 1 mm sole penetration bound at landing. Revise the effective explicit sole/floor pairs, preserving all other contacts and the 100 us integrator step.',
            contact_parameter_reference='https://mujoco.readthedocs.io/en/stable/XMLreference.html#contact-pair')
        (folder / 'contact_response_revision.json').write_text(json.dumps(contact_revision, indent=2) + '\n')
    m = mujoco.MjModel.from_xml_path(str(folder / 'world.xml'))
    d = mujoco.MjData(m)
    d.qpos[:] = source_contract['initial_qpos']
    d.qvel[:] = source_contract['initial_qvel']
    cfg = yaml.safe_load((HERE / 'locomotion_policy/deploy.yaml').read_text())
    initial = np.empty(29)
    initial[cfg['joint_ids_map']] = cfg['default_joint_pos']
    if policy_family == 'groot':
        body_cfg = yaml.safe_load((policy / 'policy.yaml').read_text())
        initial[:15] = body_cfg['default_angles']
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
    if hand_posture == 'folded':
        fingers = dict(thumb_0=0., thumb_1=.3, thumb_2=1., index_0=-1., index_1=-1.2,
                       middle_0=-1., middle_1=-1.2)
        for side, sign in [('left', 1.), ('right', -1.)]:
            for finger, value in fingers.items():
                name = side + '_hand_' + finger + '_joint'
                hand_pose[name] = sign * value
                d.joint(name).qpos[0] = sign * value
    if minimum_shoulder_abduction is not None:
        for side, sign in [('left', 1.), ('right', -1.)]:
            d.joint(side + '_shoulder_roll_joint').qpos[0] = sign * max(.25, minimum_shoulder_abduction)
    station_goal = np.asarray(source_contract['initial_qpos'])[:2].copy()
    station_quaternion = np.asarray(source_contract['initial_qpos'])[3:7].copy()
    if station_approach:
        facing = np.zeros(3)
        mujoco.mju_rotVecQuat(facing,np.array([1.,0.,0.]),station_quaternion)
        facing = facing[:2]/np.linalg.norm(facing[:2])
        d.qpos[:2] = station_goal-waypoint_forward*facing
        d.qpos[3:7] = station_quaternion
    else:
        d.qpos[:2] = [-.52, .7]  # lab (3.0, 1.5), same existing front aisle
        d.qpos[3:7] = [2**-.5, 0., 0., -2**-.5]
    mujoco.mj_forward(m, d)
    d.qpos[2] -= min(d.site(s + '_sole').xpos[2] for s in ['left', 'right'])
    mujoco.mj_forward(m, d)
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
    if sole_time_constant is not None:
        pairs = []
        for i in range(m.npair):
            names = [m.geom(int(m.pair_geom1[i])).name, m.geom(int(m.pair_geom2[i])).name]
            if any('ankle_roll_link_collision' in name for name in names) and set(names) & floor:
                pairs.append(dict(geoms=names, solref=m.pair_solref[i].tolist()))
        def sole_contacts(data):
            return [dict(geoms=[m.geom(int(g)).name for g in c.geom], solref=c.solref.tolist())
                    for c in data.contact
                    if any('ankle_roll_link_collision' in m.geom(int(g)).name for g in c.geom)
                    and {m.geom(int(g)).name for g in c.geom} & floor]
        initial_contacts = sole_contacts(d)
        # At exact sole/floor tangency there may be no active constraint yet.
        # A separate unactuated probe checks the first physical contact; its
        # state is discarded and never replaces this attempt's initial state.
        probe = mujoco.MjData(m)
        probe.qpos[:], probe.qvel[:] = d.qpos, d.qvel
        mujoco.mj_forward(m, probe)
        active = sole_contacts(probe)
        while not active and probe.time < .05:
            mujoco.mj_step(m, probe)
            active = sole_contacts(probe)
        effective = dict(scope='Compiled pairs and a separate unactuated first-contact probe',
            model_sha256=sha(folder / 'world.xml'), requested_solref=[sole_time_constant, 1.],
            compiled_pairs=pairs, active_initial_contacts=initial_contacts,
            separate_probe_time_s=float(probe.time), separate_probe_contacts=active,
            probe_state_used_by_execution=False,
            passed=len(pairs) == 32 and bool(active) and all(
                np.allclose(row['solref'], [sole_time_constant, 1.], rtol=0., atol=1e-12)
                for row in pairs + active))
        (folder / 'effective_contact_response.json').write_text(json.dumps(effective, indent=2) + '\n')
        if not effective['passed']:
            raise ValueError('The requested sole response is not active in the native contact model')
    contacts = []
    for contact in d.contact:
        if not {int(m.geom_bodyid[g]) for g in contact.geom} & robot:
            continue
        names = [m.geom(int(g)).name for g in contact.geom]
        foot_floor = any('ankle_roll_link_collision' in name for name in names) and bool(set(names) & floor)
        bound = source_contract['physical_acceptance'][
            'maximum_sole_penetration_m' if foot_floor else 'maximum_other_penetration_m']
        if contact.dist < -bound:
            contacts.append(dict(geoms=names, penetration_m=-float(contact.dist), bound_m=bound))
    joint_excess = max([max(float(m.jnt_range[j, 0] - d.qpos[m.jnt_qposadr[j]]),
                           float(d.qpos[m.jnt_qposadr[j]] - m.jnt_range[j, 1])) for j in joints] + [0.])
    initial_review = dict(scope='Pre-run native collision and source joint-position gate; no motion qualification',
        passed=not contacts and joint_excess <= source_contract['physical_acceptance']['maximum_source_joint_limit_excess_rad'],
        unexpected_contacts=contacts, maximum_joint_excess_rad=joint_excess,
        initial_qpos=d.qpos.tolist(), model_sha256=sha(folder / 'world.xml'))
    (folder / 'initial_collision_review.json').write_text(json.dumps(initial_review, indent=2) + '\n')
    if not initial_review['passed']:
        raise RuntimeError('Authored initial pose fails collision or joint-position gate')
    prior = dict(speed_m_s=speed, stop_at_s=stop_at, control_period_s=.001, hand_pose=hand_pose,
                 minimum_shoulder_abduction_rad=minimum_shoulder_abduction, hand_posture=hand_posture,
                 target_body_pose_rad=[float(d.joint(name).qpos[0]) for name in SDK_JOINTS],
                 policy_family=policy_family)
    if waypoint_forward is not None:
        prior.update(initial_map_xy_m=d.qpos[:2].tolist(),
                     waypoint_goal_xy_m=(station_goal if station_approach else d.qpos[:2]+[0.,-waypoint_forward]).tolist())
    (folder / 'walking_prior.json').write_text(json.dumps(prior, indent=2) + '\n')
    actor_module = 'dex3_walking_actor' if policy_family == 'unitree' else 'groot_walking_actor'
    extra_modules = ['walking_actor.py', 'odometry.py', actor_module + '.py']
    policy_files = sorted(p for p in policy.iterdir() if p.suffix in {'.onnx', '.yaml'}) + [folder / 'walking_prior.json']
    shapes = []
    if station_pickup:
        actor_module = 'station_pickup_actor'
        extra_modules += [actor_module+'.py', 'visual_tool_actor.py', 'dex3_tool_actor.py',
            'conic_balance.py', 'tool_observation.py', 'tool_pose.py', 'tool_approach_planning.py',
            'ftir_hand.py', 'joint_rrt.py', 'robot_source_meshes.py', 'source_proximity.py',
            'tool_cameras.py', 'sensor_rendering.py', 'map_localization.py']
        tool_prior = json.loads((source / 'policy_source/tool_prior.json').read_text())
        authored_pose = np.asarray(tool_prior.pop('initial_robot_qpos'))
        predictor = mujoco.MjModel.from_xml_path(str(folder / 'controller_model/world.xml'))
        selected_names = SDK_JOINTS[12:] + [predictor.joint(j).name for j in predictor.actuator_trnid[:, 0]
                                          if '_hand_' in predictor.joint(j).name]
        preparation_targets = {name: float(authored_pose[predictor.joint(name).qposadr[0]]) for name in selected_names}
        tool_prior['scope'] = 'Unposed tool/grasp geometry and authored controller parameters; robot pose is estimated online after station arrival'
        for name, values in [('tool_prior.json', tool_prior), ('preparation_targets.json', preparation_targets)]:
            path = folder / 'policy_source' / name
            path.write_text(json.dumps(values, indent=2) + '\n')
            policy_files.append(path)
        (folder / 'object_shape_source').mkdir()
        shape = folder / 'object_shape_source/tool_shape.glb'
        shutil.copyfile(source / 'object_shape_source/tool_shape.glb', shape)
        assert sha(shape) == tool_prior['tool_shape_sha256']
        shapes = [shape]
    command = [sys.executable, str(HERE / (actor_module + '.py')), '--model', str(folder / 'controller_model/world.xml')]
    command, environment, isolation = prepare(folder, folder / 'controller_model/world.xml', command,
        extra_modules=extra_modules, policy_files=policy_files, shape_files=shapes)
    contract = dict(scope=__doc__, hand_kind='unitree_three_finger', model_sha256=sha(folder / 'world.xml'),
        source_contract_sha256=sha(source / 'contract.json'), initial_qpos=d.qpos.tolist(), initial_qvel=d.qvel.tolist(),
        physics_period_s=m.opt.timestep, control_period_s=.001, duration_limit_s=duration,
        policy_source_sha256=sha(policy / 'SOURCE.json'), prior_sha256=sha(folder / 'walking_prior.json'),
        actor_module=actor_module, policy_family=policy_family,
        contact_response_revision=contact_revision,
        actor_isolation_sha256=sha(folder / 'actor_isolation.json'),
        initial_collision_review_sha256=sha(folder / 'initial_collision_review.json'),
        source_snapshot_sha256={p.name: sha(p) for p in snapshot.glob('*.py')},
        authored_initial_staging=dict(lab_xy_m=[3., 1.5], lab_yaw_rad=0., existing_aisle=True),
        physical_acceptance=source_contract['physical_acceptance'],
        required_forward_m=1., maximum_lateral_m=.3, maximum_settled_speed_m_s=.05,
        qualified_walking=False, qualified_carry=False, qualified_paper_branch=False)
    if waypoint_forward is not None:
        contract['waypoint']=dict(scope='Unloaded aisle arrival using encoders/IMU and a declared initial map pose',
            initial_map_xy_m=prior['initial_map_xy_m'],goal_xy_m=prior['waypoint_goal_xy_m'],
            maximum_final_position_error_m=.15,maximum_odometry_error_m=.10,
            maximum_final_heading_error_rad=.10,
            maximum_settled_speed_m_s=.05,settling_delay_after_stop_s=2.,
            minimum_settled_duration_s=1.,equipment_arrival_qualified=False)
    if station_approach:
        contract['authored_initial_staging']=dict(world_xy_m=d.qpos[:2].tolist(),
            quaternion_wxyz=d.qpos[3:7].tolist(),scope='Authored start behind the existing tool-station pose; no object state changed')
        contract['evaluation_forward_world_xy']=facing.tolist()
        contract['waypoint']['scope']='Sensor-based approach to the existing tool-station pose; manipulation is not yet included'
    if station_pickup:
        for key in ['task', 'actuator_count', 'inferred_control', 'allowed_tool_contact_bodies',
                    'observed_approach', 'camera_contract', 'tool_shape_sha256']:
            contract[key] = source_contract[key]
        contract.update(scope='Uninterrupted sensor-only station arrival, free-space preparation and visual tool pickup in the original complete laboratory',
            laboratory_import_sha256=sha(folder / 'laboratory_import.json'),
            balance_period_s=.01, actor_access_isolated=isolation['passed'],
            controller_prior_sha256=sha(folder / 'policy_source/tool_prior.json'),
            preparation_targets_sha256=sha(folder / 'policy_source/preparation_targets.json'),
            qualified_grasp=False, qualified_approach=False,
            station_handoff=dict(balance_blend_duration_s=2., preparation_duration_s=8.,
                preparation_settle_dwell_s=1., maximum_preparation_error_rad=.04,
                maximum_preparation_joint_speed_rad_s=.08, maximum_preparation_root_speed_m_s=.03,
                preparation_timeout_s=22., registration_timeout_s=34.,
                initial_pickup_pose_source='Only own sensors, leg odometry and static-map RGB-D registration',
                robot_or_object_pose_writes_after_initialization=False))
        contract['camera_contract'] = dict(contract['camera_contract'], capture_phase=['localize', 'observe'])
        contract['waypoint']['scope'] = 'Sensor-based arrival before continuous preparation and pickup; evaluated separately from grasp success'
    (folder / 'contract.json').write_text(json.dumps(contract, indent=2) + '\n')
    log = (folder / 'actor_stderr.log').open('w')
    actor = subprocess.Popen(command, env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=log, close_fds=True)
    records, sensors, responses = [], [], []
    cameras = None
    frame_index, retained_events = [], []
    if station_pickup:
        from tool_cameras import ToolCameras
        cameras = ToolCameras(m)
        (folder / 'camera_frames').mkdir()
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
                retained = {k: v for k, v in packet.items() if k != 'depth'}
                if station_pickup:
                    packet.pop('depth')
                    frame_id = -1
                    if i % (decimation*200) == 0 and response.get('phase') in {'localize', 'observe'}:
                        frames = cameras.read(d)
                        frame_id = len(frame_index)
                        path = folder / 'camera_frames' / f'{frame_id:05d}.npz'
                        np.savez_compressed(path, **frames)
                        frame_index.append(dict(id=frame_id, time_s=float(d.time),
                                                file=str(path.relative_to(folder)), sha256=sha(path)))
                    else:
                        frames = dict(head_rgb=None, head_depth=None)
                    packet.update(frames)
                    retained['camera_frame_id'] = frame_id
                pickle.dump(packet, actor.stdin, protocol=5)
                actor.stdin.flush()
                response = pickle.load(actor.stdout)
                sensors.append(retained)
                responses.append({k: v for k, v in response.items() if k != 'events'})
                retained_events = response.get('events', retained_events)
                if response['error']:
                    raise RuntimeError(response['error'])
                d.ctrl[:] = response['torque']
            records.append((float(d.time), d.qpos.copy(), d.qvel.copy(), d.ctrl.copy(), d.qacc_warmstart.copy()))
            if station_pickup and response.get('complete'):
                if response.get('failure'):
                    failure = response['failure']
                break
            mujoco.mj_step(m, d)
            if not np.isfinite(d.qpos).all() or np.any(d.warning.number):
                raise RuntimeError('Physics numerical failure')
            if d.qpos[2] < .5 or d.xmat[m.body('pelvis').id].reshape(3, 3)[2, 2] < .75:
                raise RuntimeError('Walking support lost')
            if i % round(.5 / m.opt.timestep) == 0:
                print('dex3_walk', round(float(d.time), 3), 'xyz', np.round(d.qpos[:3], 3).tolist(),
                      'phase', response.get('phase'), 'wall_s', round(time.monotonic() - started, 1), flush=True)
        if station_pickup and not response.get('complete'):
            failure = 'Duration exhausted before the continuous station attempt ended'
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
        if cameras is not None:
            cameras.close()
    if not records or abs(records[-1][0]-d.time) > 1e-12:
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
    if station_pickup:
        def plain(value):
            if isinstance(value, np.ndarray):
                return value.tolist()
            if isinstance(value, np.generic):
                return value.item()
            raise TypeError(type(value).__name__)
        (folder / 'events.json').write_text(json.dumps(retained_events, indent=2, default=plain) + '\n')
        (folder / 'camera_index.json').write_text(json.dumps(frame_index, indent=2) + '\n')
        result.update(scope=contract['scope'], camera_index_sha256=sha(folder / 'camera_index.json'),
                      events_sha256=sha(folder / 'events.json'), final_phase=response.get('phase'),
                      qualified_grasp=False)
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
    p.add_argument('--hand-posture', choices=['open', 'folded'], default='open')
    p.add_argument('--minimum-shoulder-abduction', type=float)
    p.add_argument('--policy-family', choices=['unitree', 'groot'], default='unitree')
    p.add_argument('--sole-contact-time-constant', type=float)
    p.add_argument('--waypoint-forward', type=float)
    p.add_argument('--station-approach', action='store_true')
    p.add_argument('--station-pickup', action='store_true')
    a = p.parse_args()
    if run(a.source, a.folder, a.duration, a.speed, a.stop_at, a.hand_posture,
           a.minimum_shoulder_abduction, a.policy_family, a.sole_contact_time_constant,a.waypoint_forward,a.station_approach,a.station_pickup)['failure']:
        raise SystemExit(1)
