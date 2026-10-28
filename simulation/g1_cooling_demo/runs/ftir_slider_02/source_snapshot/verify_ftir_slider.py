"""Independent motor replay and contact checks for a G1 sliding-window push.

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


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(folder):
    folder = Path(folder).resolve()
    result = json.loads((folder/'result.json').read_text())
    trace = dict(np.load(folder/'trace.npz'))
    m = mujoco.MjModel.from_xml_path(str(folder/'world.xml'))
    d = mujoco.MjData(m)
    d.qpos[:] = trace['qpos'][0];d.qvel[:] = trace['qvel'][0]
    d.time = float(trace['time'][0]);mujoco.mj_forward(m,d)
    d.qacc_warmstart[:] = trace['qacc_warmstart'][0]

    def under(body, name):
        root = m.body(name).id
        while body and body != root:body = int(m.body_parentid[body])
        return body == root

    robot = {i for i in range(m.ngeom) if under(int(m.geom_bodyid[i]), 'pelvis')}
    feet = {i for i in robot if any(under(int(m.geom_bodyid[i]), side+'_ankle_roll_link') for side in ['left','right'])}
    imported = json.loads((folder/'laboratory_import.json').read_text())
    floor = {m.geom(p['geom']).id for p in imported['parts'] if p['source_part'] in
             {'indoor_floor','annex_floor','outdoor_floor','outdoor_access_path'}}
    if not floor:raise ValueError('No source laboratory floors found')
    pad={i for i in robot if m.body(m.geom_bodyid[i]).name=='right_index_force_sensor_3'}
    grip={m.geom(g).id for p in imported['parts'] if p['instance']=='nicolet' and p['source_part']=='sample_access_slider_grip'
          for g in [p['geom']]+p.get('contact_geoms',[])}
    if not grip:raise ValueError('No source sliding-window grip geometry')
    slider_qa=int(m.joint('nicolet_door_slide').qposadr[0])
    intended_slide=0.;intended_time=0.
    key_qa = [int(m.joint('nicolet_key_slide_'+str(i)).qposadr[0]) for i in range(4)]
    contact_pairs = {};violations = [];support = []
    max_q = max_v = 0.;external = False;max_tilt = 0.;min_height = float('inf')
    thresholds = dict(key_return_m=.00005, unintended_penetration_m=.00002,
                      sole_penetration_m=.001, maximum_body_tilt_rad=.2,
                      final_yaw_error_rad=.02, maximum_final_yaw_velocity_rad_s=.03,
                      intended_pad_penetration_m=.00025, minimum_final_slide_m=.065,maximum_final_slide_m=.075,
                      minimum_pad_driven_displacement_m=.050,minimum_pad_contact_s=.5)
    for index in range(len(trace['time'])-1):
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
        foot_load = 0.;intended=False
        for ci,c in enumerate(d.contact):
            a,b = map(int,c.geom)
            if a not in robot and b not in robot:continue
            sole = (a in feet and b in floor) or (b in feet and a in floor)
            target=(a in pad and b in grip) or (b in pad and a in grip)
            force = np.zeros(6);mujoco.mj_contactForce(m,d,ci,force)
            if sole:foot_load += abs(float(force[0]))
            if target and force[0]>.05:intended=True
            pair = tuple(sorted([m.geom(a).name,m.geom(b).name]))
            value = contact_pairs.setdefault(pair,dict(minimum_distance_m=0.,maximum_normal_force_n=0.,first_time_s=t))
            value['minimum_distance_m'] = min(value['minimum_distance_m'],float(c.dist))
            value['maximum_normal_force_n'] = max(value['maximum_normal_force_n'],abs(float(force[0])))
            tolerance = thresholds['sole_penetration_m'] if sole else thresholds['intended_pad_penetration_m'] if target else thresholds['unintended_penetration_m']
            if c.dist < -tolerance:
                if len(violations)<50:violations.append(dict(time_s=t,parts=list(pair),distance_m=float(c.dist),allowed_m=tolerance))
        if intended:
            intended_slide+=max(0.,float(d.qpos[slider_qa]-trace['qpos'][index,slider_qa]));intended_time+=m.opt.timestep
        if t>.5:support.append(foot_load)
        if index%2500==0:print('verify_slider',index,'/',len(trace['time']),flush=True)
    max_q = max(max_q,float(np.max(abs(d.qpos-trace['qpos'][-1]))))
    max_v = max(max_v,float(np.max(abs(d.qvel-trace['qvel'][-1]))))
    travel = trace['qpos'][:,key_qa]
    final_mask=trace['time']>=trace['time'][-1]-2
    yaw=m.joint('waist_yaw_joint')
    final_yaw=trace['qpos'][final_mask,int(yaw.qposadr[0])]
    final_yaw_velocity=trace['qvel'][final_mask,int(yaw.dofadr[0])]
    accepted=int(result.get('actor_last_output',{}).get('accepted_key_observations',0))
    hinge=m.joint('nicolet_cover_hinge');slide=m.joint('nicolet_door_slide')
    max_hinge=float(np.max(abs(trace['qpos'][:,int(hinge.qposadr[0])])))
    max_slide=float(np.max(abs(trace['qpos'][:,int(slide.qposadr[0])])))
    slide_values=trace['qpos'][:,slider_qa];final_slide=slide_values[final_mask]
    robot_limit_excess=0.
    for j in range(m.njnt):
        if m.jnt_limited[j] and under(int(m.jnt_bodyid[j]),'pelvis'):
            q=trace['qpos'][:,m.jnt_qposadr[j]];low,high=m.jnt_range[j]
            robot_limit_excess=max(robot_limit_excess,float(np.max(np.maximum(low-q,q-high))))
    checks = dict(
        attempt_finished=result['status']=='attempt_finished_pending_independent_slider_verification',
        exact_motor_replay=max_q<1e-9 and max_v<1e-8,
        no_external_forces=not external,
        no_device_actuators=all(under(int(m.jnt_bodyid[j]),'pelvis') for j in m.actuator_trnid[:,0]),
        controls_observed=accepted>=8,
        torso_reached_approach_orientation=bool(np.max(abs(final_yaw+.2))<thresholds['final_yaw_error_rad'] and np.max(abs(final_yaw_velocity))<thresholds['maximum_final_yaw_velocity_rad_s']),
        all_keys_untouched=bool(np.max(abs(travel))<thresholds['key_return_m']),
        cover_remained_closed=max_hinge<np.deg2rad(.5),
        window_reached_requested_gap=bool(np.min(final_slide)>=thresholds['minimum_final_slide_m'] and np.max(final_slide)<=thresholds['maximum_final_slide_m']),
        window_stops_respected=bool(np.min(slide_values)>-.00005 and np.max(slide_values)<.10405),
        window_displacement_driven_by_intended_pad=intended_slide>=thresholds['minimum_pad_driven_displacement_m'] and intended_time>=thresholds['minimum_pad_contact_s'],
        only_robot_mimic_equalities=all(m.eq_type[i]==mujoco.mjtEq.mjEQ_JOINT and under(int(m.jnt_bodyid[m.eq_obj1id[i]]),'pelvis') and under(int(m.jnt_bodyid[m.eq_obj2id[i]]),'pelvis') for i in range(m.neq)),
        key_stops_respected=bool(np.min(travel)>-.00005 and np.max(travel)<.00035),
        source_motor_limits_respected=bool(np.all(trace['ctrl']>=m.actuator_ctrlrange[:,0]-1e-9) and
                                          np.all(trace['ctrl']<=m.actuator_ctrlrange[:,1]+1e-9)),
        source_robot_joint_limits_respected=robot_limit_excess<.01,
        no_unintended_or_excess_contact=not violations,
        upright_supported=bool(min_height>.65 and max_tilt<thresholds['maximum_body_tilt_rad'] and support and min(support)>100),
        no_numerical_warnings=not np.any(d.warning.number),
    )
    report = dict(passed=all(checks.values()),checks=checks,thresholds=thresholds,
        states=len(trace['time']),maximum_replay_position_error=max_q,maximum_replay_velocity_error=max_v,
        maximum_key_travel_m=np.max(travel,axis=0).tolist(),final_key_travel_m=travel[-1].tolist(),
        accepted_key_observations=accepted,pad_driven_displacement_m=intended_slide,pad_contact_time_s=intended_time,final_slider_travel_m=float(slide_values[-1]),maximum_cover_angle_rad=max_hinge,maximum_slider_travel_m=max_slide,minimum_pelvis_height_m=min_height,maximum_body_tilt_rad=max_tilt,
        maximum_robot_joint_limit_excess_rad=robot_limit_excess,
        minimum_sole_normal_load_n=min(support) if support else None,
        contacts=[dict(parts=list(k),**v) for k,v in contact_pairs.items()],first_violations=violations,
        model_sha256=sha(folder/'world.xml'),trace_sha256=sha(folder/'trace.npz'),verifier_sha256=sha(__file__),
        qualified_skill=False,qualified_paper_branch=False,
        scope='One 70 mm passive sliding-window push and return attempt from authored setup. No executed walking, full cover opening, sensor calibration, reliability campaign or branch qualification.')
    (folder/'physical_slider_review.json').write_text(json.dumps(report,indent=2)+'\n')
    shutil.copyfile(__file__,folder/'verify_ftir_slider.py')
    print(json.dumps({k:report[k] for k in ['passed','checks','accepted_key_observations']}),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');a=p.parse_args()
    if not verify(a.folder)['passed']:raise SystemExit(1)
