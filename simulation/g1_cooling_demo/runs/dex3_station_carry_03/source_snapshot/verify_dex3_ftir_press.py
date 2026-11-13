"""Independent motor replay and contact checks for one G1/Dex3 FTIR key attempt.

The evaluator reads plant truth after execution. Its output is never an actor
input. Passing does not qualify an acquisition, a skill campaign or a branch.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from observations import robot_joints
from sensor_rendering import depth_renderer


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(folder):
    folder = Path(folder).resolve()
    result = json.loads((folder/'result.json').read_text())
    contract = json.loads((folder/'contract.json').read_text())
    assert sha(folder/'contract.json') == result['contract_sha256']
    assert sha(folder/'trace.npz') == result['trace_sha256']
    assert sha(folder/'world.xml') == contract['model_sha256']
    assert contract['intended_finger_body'] == 'right_hand_index_1_link'
    trace = dict(np.load(folder/'trace.npz'))
    m = mujoco.MjModel.from_xml_path(str(folder/'world.xml'))
    assert m.nu == 43 and m.neq == 0
    d = mujoco.MjData(m)
    d.qpos[:] = trace['qpos'][0];d.qvel[:] = trace['qvel'][0]
    d.time = float(trace['time'][0]);mujoco.mj_forward(m,d)
    d.qacc_warmstart[:] = trace['qacc_warmstart'][0]
    sensor = dict(np.load(folder/'sensors.npz'))
    assert sha(folder/'sensors.npz') == result['sensors_sha256']
    assert sha(folder/'camera_index.json') == result['camera_index_sha256']
    camera_index = json.loads((folder/'camera_index.json').read_text())
    for entry in camera_index:
        assert sha(folder/entry['file']) == entry['sha256']
    sensor_names = [m.joint(j).name for j in robot_joints(m)]
    color = mujoco.Renderer(m, height=360, width=640, max_geom=m.ngeom+1000)
    depth = depth_renderer(m, 360, 640)
    option = mujoco.MjvOption()
    option.geomgroup[3] = 0
    option.sitegroup[:] = 0
    compared_sensors = compared_images = 0
    sensor_error = rgb_error = depth_error = 0.

    def compare_packet():
        nonlocal compared_sensors, compared_images, sensor_error, rgb_error, depth_error
        i = compared_sensors
        if i == len(sensor['time_s']) or abs(float(d.time)-float(sensor['time_s'][i])) > 1e-8:
            return
        packet = dict(time_s=float(d.time),
            joint_position=np.array([d.sensor(n+'_encoder').data[0] for n in sensor_names]),
            joint_velocity=np.array([d.sensor(n+'_velocity').data[0] for n in sensor_names]),
            imu_quaternion=d.sensor('imu_orientation').data.copy(),
            imu_gyro=d.sensor('imu_angular_velocity').data.copy())
        for key, value in packet.items():
            sensor_error = max(sensor_error, float(np.max(abs(np.asarray(value)-sensor[key][i]))))
        frame_id = int(sensor['camera_frame_id'][i])
        if frame_id >= 0:
            entry = camera_index[frame_id]
            assert entry['id'] == frame_id and abs(entry['time_s']-float(d.time)) < 1e-8
            with np.load(folder/entry['file']) as frame:
                color.update_scene(d, camera='head_rgb', scene_option=option)
                rgb_error = max(rgb_error, float(np.max(abs(color.render().astype(float)-frame['rgb'].astype(float)))))
                depth.update_scene(d, camera='head_depth', scene_option=option)
                depth_error = max(depth_error, float(np.max(abs(depth.render()-frame['depth']))))
            compared_images += 1
        compared_sensors += 1

    def under(body, name):
        root = m.body(name).id
        while body and body != root:body = int(m.body_parentid[body])
        return body == root

    robot = {i for i in range(m.ngeom) if under(int(m.geom_bodyid[i]), 'pelvis')}
    feet = {i for i in robot if any(under(int(m.geom_bodyid[i]), side+'_ankle_roll_link') for side in ['left','right'])}
    pad = {i for i in robot if m.body(m.geom_bodyid[i]).name == 'right_hand_index_1_link'}
    key = {i for i in range(m.ngeom) if m.body(m.geom_bodyid[i]).name == 'nicolet_key_1'}
    imported = json.loads((folder/'laboratory_import.json').read_text())
    floor = {m.geom(p['geom']).id for p in imported['parts'] if p['source_part'] in
             {'indoor_floor','annex_floor','outdoor_floor','outdoor_access_path'}}
    if not floor:raise ValueError('No source laboratory floors found')
    key_qa = [int(m.joint('nicolet_key_slide_'+str(i)).qposadr[0]) for i in range(4)]
    contact_pairs = {};violations = [];press_times = [];support = []
    max_q = max_v = 0.;external = False;max_tilt = 0.;min_height = float('inf')
    thresholds = contract['physical_acceptance']
    for index in range(len(trace['time'])-1):
        compare_packet()
        t = float(trace['time'][index])
        max_q = max(max_q,float(np.max(abs(d.qpos-trace['qpos'][index]))))
        max_v = max(max_v,float(np.max(abs(d.qvel-trace['qvel'][index]))))
        height = float(d.qpos[2]);min_height = min(min_height,height)
        # Contacts, body frames and forces returned by mj_step correspond to
        # this pre-integration state; compare the integrated state next loop.
        d.ctrl[:] = trace['ctrl'][index]
        mujoco.mj_step(m,d)
        external |= bool(np.any(d.xfrc_applied) or np.any(d.qfrc_applied))
        tilt = float(np.arccos(np.clip(d.body('pelvis').xmat.reshape(3,3)[2,2],-1,1)))
        max_tilt = max(max_tilt,tilt)
        intended = False;foot_load = 0.
        for ci,c in enumerate(d.contact):
            a,b = map(int,c.geom)
            if a not in robot and b not in robot:continue
            sole = (a in feet and b in floor) or (b in feet and a in floor)
            touch = (a in pad and b in key) or (b in pad and a in key)
            force = np.zeros(6);mujoco.mj_contactForce(m,d,ci,force)
            if sole:foot_load += abs(float(force[0]))
            if touch and force[0]>.01:intended = True
            pair = tuple(sorted([m.geom(a).name,m.geom(b).name]))
            value = contact_pairs.setdefault(pair,dict(minimum_distance_m=0.,maximum_normal_force_n=0.,first_time_s=t))
            value['minimum_distance_m'] = min(value['minimum_distance_m'],float(c.dist))
            value['maximum_normal_force_n'] = max(value['maximum_normal_force_n'],abs(float(force[0])))
            tolerance = thresholds['sole_penetration_m'] if sole else thresholds['intended_pad_penetration_m'] if touch else thresholds['unintended_penetration_m']
            if c.dist < -tolerance:
                if len(violations)<50:violations.append(dict(time_s=t,parts=list(pair),distance_m=float(c.dist),allowed_m=tolerance))
        if intended and trace['qpos'][index,key_qa[1]]>=thresholds['key_press_m']:press_times.append(t)
        if t>.5:support.append(foot_load)
        if index%25000==0:print('verify_press',index,'/',len(trace['time']),flush=True)
    max_q = max(max_q,float(np.max(abs(d.qpos-trace['qpos'][-1]))))
    max_v = max(max_v,float(np.max(abs(d.qvel-trace['qvel'][-1]))))
    compare_packet()
    color.close()
    depth.close()
    held = longest = 0.;previous = None
    for t in press_times:
        held = held+m.opt.timestep if previous is not None and t-previous<1.5*m.opt.timestep else m.opt.timestep
        longest = max(longest,held);previous = t
    travel = trace['qpos'][:,key_qa]
    final = travel[trace['time']>=trace['time'][-1]-2]
    robot_limit_excess=0.
    for j in range(m.njnt):
        if m.jnt_limited[j] and under(int(m.jnt_bodyid[j]),'pelvis'):
            q=trace['qpos'][:,m.jnt_qposadr[j]];low,high=m.jnt_range[j]
            robot_limit_excess=max(robot_limit_excess,float(np.max(np.maximum(low-q,q-high))))
    checks = dict(
        attempt_finished=result['status']=='attempt_finished_pending_independent_switch_verification',
        exact_motor_replay=max_q<thresholds['maximum_replay_q_error'] and max_v<thresholds['maximum_replay_v_error'],
        native_sensor_replay=compared_sensors==len(sensor['time_s']) and sensor_error<=1e-10,
        native_camera_replay=compared_images==len(camera_index)>0 and rgb_error==0. and depth_error<=1e-7,
        no_external_forces=not external,
        no_device_actuators=all(under(int(m.jnt_bodyid[j]),'pelvis') for j in m.actuator_trnid[:,0]),
        key_depressed_by_intended_finger=longest>=thresholds['minimum_press_s'],
        other_keys_untouched=bool(np.max(abs(travel[:,[0,2,3]]))<thresholds['key_return_m']),
        key_stops_respected=bool(np.min(travel)>-.00005 and np.max(travel)<.00035),
        source_motor_limits_respected=bool(np.all(trace['ctrl']>=m.actuator_ctrlrange[:,0]-1e-9) and
                                          np.all(trace['ctrl']<=m.actuator_ctrlrange[:,1]+1e-9)),
        source_robot_joint_limits_respected=robot_limit_excess<thresholds['maximum_joint_limit_excess_rad'],
        key_returned=bool(np.max(abs(final[:,1]))<thresholds['key_return_m']),
        no_unintended_or_excess_contact=not violations,
        upright_supported=bool(min_height>.65 and max_tilt<thresholds['maximum_body_tilt_rad'] and support and min(support)>100),
        no_numerical_warnings=not np.any(d.warning.number),
    )
    report = dict(passed=all(checks.values()),checks=checks,thresholds=thresholds,
        compared_sensor_packets=compared_sensors, compared_camera_frames=compared_images,
        maximum_sensor_error=sensor_error, maximum_rgb_error=rgb_error, maximum_depth_error=depth_error,
        states=len(trace['time']),maximum_replay_position_error=max_q,maximum_replay_velocity_error=max_v,
        maximum_key_travel_m=np.max(travel,axis=0).tolist(),final_key_travel_m=travel[-1].tolist(),
        longest_pressed_with_pad_contact_s=longest,minimum_pelvis_height_m=min_height,maximum_body_tilt_rad=max_tilt,
        maximum_robot_joint_limit_excess_rad=robot_limit_excess,
        minimum_sole_normal_load_n=min(support) if support else None,
        contacts=[dict(parts=list(k),**v) for k,v in contact_pairs.items()],first_violations=violations,
        model_sha256=sha(folder/'world.xml'),trace_sha256=sha(folder/'trace.npz'),verifier_sha256=sha(__file__),
        qualified_skill=False,qualified_paper_branch=False,
        scope='One key-press attempt from authored setup. No acquisition outcome, sensor accuracy or repeatability qualification.')
    (folder/'physical_press_review.json').write_text(json.dumps(report,indent=2)+'\n')
    shutil.copyfile(__file__,folder/'verify_dex3_ftir_press.py')
    print(json.dumps({k:report[k] for k in ['passed','checks','maximum_key_travel_m','longest_pressed_with_pad_contact_s']}),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');a=p.parse_args()
    if not verify(a.folder)['passed']:raise SystemExit(1)
