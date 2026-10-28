"""Independent motor replay for a short development stepping probe."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(source,folder):
    source,folder=Path(source).resolve(),Path(folder).resolve()
    output=folder/'physical_review.json'
    if output.exists():raise FileExistsError(output)
    contract=json.loads((folder/'contract.json').read_text())
    result=json.loads((folder/'result.json').read_text())
    model_path=source/'world.xml'
    if sha(model_path)!=contract['source_hashes'][str(model_path)]:
        raise ValueError('Declared laboratory model changed')
    trace=dict(np.load(folder/'trace.npz'))
    if sha(folder/'trace.npz')!=result['trace_sha256']:
        raise ValueError('Declared motor trace changed')
    m=mujoco.MjModel.from_xml_path(str(model_path));d=mujoco.MjData(m)
    d.qpos[:]=trace['qpos'][0];d.qvel[:]=trace['qvel'][0]
    d.time=float(trace['time'][0]);mujoco.mj_forward(m,d)
    initial_foot_rotations=[d.site(s+'_sole').xmat.reshape(3,3).copy() for s in ['left','right']]
    d.qacc_warmstart[:]=trace['qacc_warmstart'][0]
    def under(body,name):
        root=m.body(name).id
        while body and body!=root:body=int(m.body_parentid[body])
        return body==root
    robot={g for g in range(m.ngeom) if under(int(m.geom_bodyid[g]),'pelvis')}
    feet={g for g in robot if any(under(int(m.geom_bodyid[g]),s+'_ankle_roll_link') for s in ['left','right'])}
    imported=json.loads((source/'laboratory_import.json').read_text())
    floors={m.geom(p['geom']).id for p in imported['parts'] if p['source_part'] in {'indoor_floor','annex_floor','outdoor_floor','outdoor_access_path'}}
    max_q=max_v=max_tilt=0.
    min_height=float('inf');min_load=float('inf')
    violations=[];external=False;max_limit=0.;contacts={}
    for i,t in enumerate(trace['time'][:-1]):
        max_q=max(max_q,float(np.max(abs(d.qpos-trace['qpos'][i]))))
        max_v=max(max_v,float(np.max(abs(d.qvel-trace['qvel'][i]))))
        min_height=min(min_height,float(d.qpos[2]))
        d.ctrl[:]=trace['ctrl'][i];mujoco.mj_step(m,d)
        max_tilt=max(max_tilt,float(np.arccos(np.clip(d.body('pelvis').xmat.reshape(3,3)[2,2],-1,1))))
        external|=bool(np.any(d.xfrc_applied) or np.any(d.qfrc_applied))
        load=0.
        for j,c in enumerate(d.contact):
            a,b=map(int,c.geom)
            if not ({a,b}&robot):continue
            sole=(a in feet and b in floors) or (b in feet and a in floors)
            force=np.zeros(6);mujoco.mj_contactForce(m,d,j,force)
            if sole:load+=abs(float(force[0]))
            pair=tuple(sorted([m.geom(a).name,m.geom(b).name]))
            row=contacts.setdefault(pair,dict(first_time_s=float(t),minimum_distance_m=0.,maximum_force_n=0.))
            row['minimum_distance_m']=min(row['minimum_distance_m'],float(c.dist))
            row['maximum_force_n']=max(row['maximum_force_n'],abs(float(force[0])))
            bound=.001 if sole else .00002
            if c.dist < -bound and len(violations)<50:
                violations.append(dict(time_s=float(t),parts=list(pair),distance_m=float(c.dist),bound_m=bound))
        if t>.5:min_load=min(min_load,load)
    max_q=max(max_q,float(np.max(abs(d.qpos-trace['qpos'][-1]))))
    max_v=max(max_v,float(np.max(abs(d.qvel-trace['qvel'][-1]))))
    for j in range(m.njnt):
        if m.jnt_limited[j] and under(int(m.jnt_bodyid[j]),'pelvis'):
            q=trace['qpos'][:,m.jnt_qposadr[j]];lo,hi=m.jnt_range[j]
            max_limit=max(max_limit,float(np.max(np.maximum(lo-q,q-hi))))
    displacement=trace['qpos'][-1,:2]-trace['qpos'][0,:2]
    requested=np.array(contract['goal_xy_m'])-np.array(contract['initial_xy_m'])
    checks=dict(attempt_finished=result['status']=='finished_pending_independent_review',
                two_feet_stepped=result['completed_steps']>=2,
                requested_displacement=bool(np.linalg.norm(displacement-requested)<.03),
                exact_motor_replay=max_q<1e-9 and max_v<1e-8,
                no_external_forces=not external,
                no_unintended_or_excess_contact=not violations,
                source_joint_limits=max_limit<.01,
                source_motor_limits=bool(np.all(trace['ctrl']>=m.actuator_ctrlrange[:,0]-1e-9) and np.all(trace['ctrl']<=m.actuator_ctrlrange[:,1]+1e-9)),
                upright_supported=min_height>.65 and max_tilt<.2 and min_load>100,
                no_numerical_warnings=not np.any(d.warning.number))
    turn_review=None
    if contract.get('operation') in {'in_place_turn', 'turn_then_translation'}:
        requested_yaw=float(contract['relative_yaw_rad'])
        q=trace['qpos'][:,3:7]
        headings=np.unwrap(np.arctan2(2*(q[:,0]*q[:,3]+q[:,1]*q[:,2]),1-2*(q[:,2]**2+q[:,3]**2)))
        final=trace['time']>=trace['time'][-1]-1.
        relative=headings-headings[0]
        error=float(np.max(abs(relative[final]-requested_yaw)))
        angular_speed=float(np.max(np.linalg.norm(trace['qvel'][final,3:6],axis=1)))
        mujoco.mj_kinematics(m,d)
        rotation=Rotation.from_rotvec([0.,0.,requested_yaw]).as_matrix()
        foot_errors=[float(np.linalg.norm(Rotation.from_matrix(rotation@initial@d.site(side+'_sole').xmat.reshape(3,3).T).as_rotvec()))
                     for side,initial in zip(['left','right'],initial_foot_rotations)]
        checks.update(requested_heading=error<.02,both_soles_reached_heading=max(foot_errors)<.02,
                      settled_final_angular_speed=angular_speed<.03)
        turn_review=dict(requested_relative_yaw_rad=requested_yaw,final_relative_yaw_rad=float(relative[-1]),
                         maximum_final_heading_error_rad=error,final_sole_orientation_errors_rad=foot_errors,
                         maximum_final_angular_speed_rad_s=angular_speed,
                         heading_tolerance_rad=.02)
        if contract['operation']=='turn_then_translation':
            handoffs = [e for e in result['events'] if e['state']=='continuous_turn_walk_handoff']
            checks['one_continuous_turn_walk_handoff'] = len(handoffs)==1
            checks['uninterrupted_physics_clock'] = bool(np.allclose(np.diff(trace['time']),m.opt.timestep,rtol=0,atol=1e-9))
            checks['walk_completed_after_turn'] = len(handoffs)==1 and result['completed_steps']-handoffs[0]['completed_turn_steps']>=2
            if len(handoffs)==1:
                moving = trace['time']>=handoffs[0]['time_s']
                walk_heading_error = float(np.max(abs(relative[moving]-requested_yaw)))
                checks['new_heading_preserved_during_walk'] = walk_heading_error<.03
                turn_review['maximum_heading_error_during_walk_rad'] = walk_heading_error
    report=dict(passed=all(checks.values()),checks=checks,maximum_replay_position_error=max_q,
                maximum_replay_velocity_error=max_v,displacement_m=displacement.tolist(),
                minimum_pelvis_height_m=min_height,maximum_pelvis_tilt_rad=max_tilt,
                minimum_sole_load_n=min_load,maximum_joint_limit_excess_rad=max_limit,
                contacts=[dict(parts=list(k),**v) for k,v in contacts.items()],first_violations=violations,
                model_sha256=sha(model_path),trace_sha256=sha(folder/'trace.npz'),verifier_sha256=sha(__file__),
                turn_review=turn_review,
                qualified_skill=False,qualified_paper_branch=False,
                scope='Physical replay of a short stepping probe. No process isolation, full approach or experimental manipulation qualification.')
    output.write_text(json.dumps(report,indent=2)+'\n')
    shutil.copyfile(__file__,folder/Path(__file__).name)
    print(json.dumps({k:v for k,v in report.items() if k not in {'contacts','first_violations'}}),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('folder');a=p.parse_args()
    if not verify(a.source,a.folder)['passed']:raise SystemExit(1)
