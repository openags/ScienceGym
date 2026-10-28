"""Independent motor replay and contact review of a passive-cover attempt.

Evaluator truth is read only after execution. It is never an actor input.
Passing one development case does not qualify a skill campaign or branch.
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
    folder=Path(folder).resolve();result=json.loads((folder/'result.json').read_text())
    trace=dict(np.load(folder/'trace.npz'));m=mujoco.MjModel.from_xml_path(str(folder/'world.xml'))
    d=mujoco.MjData(m);d.qpos[:]=trace['qpos'][0];d.qvel[:]=trace['qvel'][0]
    d.time=float(trace['time'][0]);mujoco.mj_forward(m,d);d.qacc_warmstart[:]=trace['qacc_warmstart'][0]
    def under(body,name):
        root=m.body(name).id
        while body and body!=root:body=int(m.body_parentid[body])
        return body==root
    robot={i for i in range(m.ngeom) if under(int(m.geom_bodyid[i]),'pelvis')}
    feet={i for i in robot if any(under(int(m.geom_bodyid[i]),s+'_ankle_roll_link') for s in ['left','right'])}
    digits=[{i for i in robot if m.body(m.geom_bodyid[i]).name.startswith('right_'+digit)} for digit in ['index','thumb']]
    lid={i for i in range(m.ngeom) if under(int(m.geom_bodyid[i]),'nicolet_cover')}
    imported=json.loads((folder/'laboratory_import.json').read_text())
    floor={m.geom(p['geom']).id for p in imported['parts'] if p['source_part'] in
           {'indoor_floor','annex_floor','outdoor_floor','outdoor_access_path'}}
    handle={m.geom(p['geom']).id for p in imported['parts'] if p['instance']=='nicolet' and p['source_part']=='lid_handle_bar'}
    if not floor or not handle:raise ValueError('Source floor or handle geometry is missing')
    qa=int(m.joint('nicolet_cover_hinge').qposadr[0]);angles=trace['qpos'][:,qa]
    thresholds=dict(unintended_robot_penetration_m=.00002,intended_finger_penetration_m=.00025,
                    sole_penetration_m=.001,unintended_device_penetration_m=.000002,
                    minimum_open_angle_rad=.9,minimum_final_open_angle_rad=.85,
                    opposition_cosine_max=-.3,minimum_digit_normal_force_n=.15,
                    minimum_opposed_contact_fraction_during_lift=.95,maximum_body_tilt_rad=.2)
    pairs={};violations=[];support=[];grasp=[];released=[];max_q=max_v=0.
    min_height=float('inf');max_tilt=0.;external=False;max_index=max_thumb=0.
    for k in range(len(trace['time'])-1):
        t=float(trace['time'][k]);max_q=max(max_q,float(np.max(abs(d.qpos-trace['qpos'][k]))))
        max_v=max(max_v,float(np.max(abs(d.qvel-trace['qvel'][k]))));min_height=min(min_height,float(d.qpos[2]))
        d.ctrl[:]=trace['ctrl'][k];mujoco.mj_step(m,d)
        external|=bool(np.any(d.xfrc_applied) or np.any(d.qfrc_applied))
        max_tilt=max(max_tilt,float(np.arccos(np.clip(d.body('pelvis').xmat.reshape(3,3)[2,2],-1,1))))
        normals=np.zeros((2,3));loads=np.zeros(2);foot_load=0.;hand_contact=False
        for ci,c in enumerate(d.contact):
            a,b=map(int,c.geom);in_robot=a in robot or b in robot;in_lid=a in lid or b in lid
            if not in_robot and not in_lid:continue
            sole=(a in feet and b in floor) or (b in feet and a in floor)
            intended=False;force=np.zeros(6);mujoco.mj_contactForce(m,d,ci,force)
            for index,digit in enumerate(digits):
                if (a in digit and b in handle) or (b in digit and a in handle):
                    intended=True;loads[index]+=max(0.,float(force[0]))
                    normals[index]+=max(0.,float(force[0]))*c.frame[:3]*(1 if a in digit else -1)
            if in_robot and not sole and max(0.,float(force[0]))>.01 and (a not in robot or b not in robot):
                hand_contact=True
            if sole:foot_load+=abs(float(force[0]))
            pair=tuple(sorted([m.geom(a).name,m.geom(b).name]))
            item=pairs.setdefault(pair,dict(minimum_distance_m=0.,maximum_normal_force_n=0.,first_time_s=t,last_time_s=t))
            item['minimum_distance_m']=min(item['minimum_distance_m'],float(c.dist));item['last_time_s']=t
            item['maximum_normal_force_n']=max(item['maximum_normal_force_n'],abs(float(force[0])))
            tolerance=thresholds['sole_penetration_m'] if sole else thresholds['intended_finger_penetration_m'] if intended else thresholds['unintended_robot_penetration_m'] if in_robot else thresholds['unintended_device_penetration_m']
            if c.dist < -tolerance and len(violations)<60:
                violations.append(dict(time_s=t,parts=list(pair),distance_m=float(c.dist),allowed_m=tolerance))
        max_index=max(max_index,loads[0]);max_thumb=max(max_thumb,loads[1])
        opposition=float(np.dot(normals[0],normals[1])/max(np.linalg.norm(normals[0])*np.linalg.norm(normals[1]),1e-30))
        opposed=bool(np.min(loads)>.15 and opposition<thresholds['opposition_cosine_max'])
        grasp.append(dict(time_s=t,angle_rad=float(angles[k]),opposed=opposed,
                          index_n=float(loads[0]),thumb_n=float(loads[1]),normal_cosine=opposition))
        if t>.5:support.append(foot_load)
        if t>=trace['time'][-1]-2:released.append(not hand_contact)
        if k%2500==0:print('verify_cover',k,'/',len(trace['time']),flush=True)
    max_q=max(max_q,float(np.max(abs(d.qpos-trace['qpos'][-1]))));max_v=max(max_v,float(np.max(abs(d.qvel-trace['qvel'][-1]))))
    rising=[g for g in grasp if -.9<g['angle_rad']<-.1]
    opposed_fraction=sum(g['opposed'] for g in rising)/len(rising) if rising else 0.
    initial_grasp=any(g['opposed'] and abs(g['angle_rad'])<.1 for g in grasp)
    limits=0.
    for j in range(m.njnt):
        if m.jnt_limited[j] and under(int(m.jnt_bodyid[j]),'pelvis'):
            q=trace['qpos'][:,m.jnt_qposadr[j]];lo,hi=m.jnt_range[j]
            limits=max(limits,float(np.max(np.maximum(lo-q,q-hi))))
    final=angles[trace['time']>=trace['time'][-1]-2]
    checks=dict(attempt_finished=result['status']=='attempt_finished_pending_independent_cover_verification',
                exact_motor_replay=max_q<1e-9 and max_v<1e-8,no_external_forces=not external,
                no_device_actuators=all(under(int(m.jnt_bodyid[j]),'pelvis') for j in m.actuator_trnid[:,0]),
                opposed_grasp_before_lift=initial_grasp,
                opposed_contact_retained_during_lift=opposed_fraction>=thresholds['minimum_opposed_contact_fraction_during_lift'],
                cover_opened=float(np.min(angles))<=-thresholds['minimum_open_angle_rad'],
                cover_remained_open_after_release=bool(np.max(final)<=-thresholds['minimum_final_open_angle_rad']),
                hand_released_and_withdrawn=bool(released and all(released)),
                hinge_stops_respected=bool(np.min(angles)>-np.pi/2-.002 and np.max(angles)<.002),
                source_motor_limits_respected=bool(np.all(trace['ctrl']>=m.actuator_ctrlrange[:,0]-1e-9) and np.all(trace['ctrl']<=m.actuator_ctrlrange[:,1]+1e-9)),
                source_robot_joint_limits_respected=limits<.01,no_unintended_or_excess_contact=not violations,
                upright_supported=bool(min_height>.65 and max_tilt<thresholds['maximum_body_tilt_rad'] and support and min(support)>100),
                no_numerical_warnings=not np.any(d.warning.number))
    report=dict(passed=all(checks.values()),checks=checks,thresholds=thresholds,states=len(trace['time']),
                maximum_open_angle_deg=float(-np.min(angles)*180/np.pi),final_open_angle_deg=float(-angles[-1]*180/np.pi),
                opposed_contact_fraction_during_lift=opposed_fraction,maximum_index_normal_force_n=float(max_index),
                maximum_thumb_normal_force_n=float(max_thumb),minimum_pelvis_height_m=min_height,maximum_body_tilt_rad=max_tilt,
                maximum_robot_joint_limit_excess_rad=limits,minimum_sole_normal_load_n=min(support) if support else None,
                maximum_replay_position_error=max_q,maximum_replay_velocity_error=max_v,
                contacts=[dict(parts=list(k),**v) for k,v in pairs.items()],first_violations=violations,
                model_sha256=sha(folder/'world.xml'),trace_sha256=sha(folder/'trace.npz'),verifier_sha256=sha(__file__),
                qualified_skill=False,qualified_paper_branch=False,scope=__doc__)
    (folder/'cover_contact_samples.json').write_text(json.dumps(grasp,separators=(',',':'))+'\n')
    (folder/'physical_cover_review.json').write_text(json.dumps(report,indent=2)+'\n')
    shutil.copyfile(__file__,folder/'verify_ftir_cover.py')
    print(json.dumps({k:report[k] for k in ['passed','checks','maximum_open_angle_deg','opposed_contact_fraction_during_lift']}),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');a=p.parse_args()
    if not verify(a.folder)['passed']:raise SystemExit(1)
