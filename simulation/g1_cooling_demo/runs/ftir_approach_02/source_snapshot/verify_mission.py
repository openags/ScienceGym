"""Check continuity, sensor-estimate error and contacts across the joined task."""
import argparse
import hashlib
import json
from pathlib import Path
import mujoco
import numpy as np


def verify(folder):
    folder=Path(folder);result=json.loads((folder/'result.json').read_text())
    trace=dict(np.load(folder/'trace.npz'));model=mujoco.MjModel.from_xml_path(str(folder/'world.xml'))
    data=mujoco.MjData(model);checks=[]
    def check(name,value,**details):checks.append(dict(name=name,passed=bool(value),**details))
    check('joined_task_completed',result['status']=='completed' and result['actor_last_output'].get('policy_complete',False))
    check('declared_start_preserved',np.array_equal(trace['qpos'][0],json.loads((folder/'staging.json').read_text())['initial_qpos']))
    dt=np.diff(trace['time'])
    # Early runner versions recorded the identical terminal state twice.
    # Preserve the raw record, accepting only an exactly identical final sample.
    terminal_duplicate=bool(len(dt) and dt[-1]==0 and all(np.array_equal(trace[key][-1],trace[key][-2]) for key in ['qpos','qvel','ctrl','qacc_warmstart']))
    clock=dt[:-1] if terminal_duplicate else dt
    check('continuous_physics_clock',bool(len(clock)) and np.allclose(clock,model.opt.timestep,atol=1e-9,rtol=0),identical_terminal_duplicate=terminal_duplicate)
    events=result['actor_last_output'].get('mission_events',[])
    starts=[e for e in events if e['state']=='begin_depth_localization']
    stable=[e for e in events if e['state']=='stationary_control_stable']
    start=starts[0]['time_s'] if starts else None
    check('observed_controller_handoff',len(starts)==len(stable)==1 and stable[0]['time_s']==start if starts and stable else False)
    if start is not None:
        index=np.searchsorted(trace['time'],start)
        travel=float(np.linalg.norm(trace['qpos'][index,:2]-trace['qpos'][0,:2]))
        check('robot_walked_to_workstation',travel>.5,displacement_before_manipulation_m=travel)
        observations=json.loads((folder/'policy_observations.json').read_text())
        before_raise=[e for e in result['actor_last_output'].get('policy_events',[]) if e['state']=='raise']
        usable=[o for o in observations if o['capture_time_s']>=start and before_raise and o['time_s']<=before_raise[0]['time_s']+1e-8]
        check('fresh_depth_localization_after_walking',len(usable)>=8,observations=len(usable))
    estimates=json.loads((folder/'actor_pose_estimates.json').read_text())
    indices=np.searchsorted(trace['time'],[e['time_s'] for e in estimates])
    position=np.array([e['estimated_root_position_m'] for e in estimates])
    error=np.linalg.norm(position[:,:2]-trace['qpos'][indices,:2],axis=1)
    check('recorded_map_estimate_within_five_cm',float(error.max())<.05,maximum_xy_error_m=float(error.max()))
    imported=json.loads((folder/'laboratory_import.json').read_text())
    floors={model.geom(p['geom']).id for p in imported['parts'] if p['instance']=='architecture' and 'floor' in p['source_part']}
    robot=set()
    for i in range(1,model.nbody):
        root=i
        while model.body_parentid[root]>0:root=int(model.body_parentid[root])
        if model.body(root).name=='pelvis':robot.add(i)
    tray=model.body('carrier_tray').id;unexpected={};minimum_height=2.
    for i in range(len(trace['time'])):
        data.qpos[:]=trace['qpos'][i];data.qvel[:]=trace['qvel'][i];mujoco.mj_forward(model,data)
        minimum_height=min(minimum_height,float(data.body('pelvis').xpos[2]))
        for c in data.contact:
            a,b=int(c.geom1),int(c.geom2);ra,rb=int(model.geom_bodyid[a]) in robot,int(model.geom_bodyid[b]) in robot
            if ra==rb:continue
            own,other=(a,b) if ra else (b,a)
            feet=model.body(model.geom_bodyid[own]).name in {'left_ankle_roll_link','right_ankle_roll_link'}
            allowed=(feet and other in floors) or (start is not None and trace['time'][i]>=start and model.geom_bodyid[other]==tray)
            if not allowed:
                pair=model.geom(own).name+' / '+model.geom(other).name
                if pair not in unexpected:unexpected[pair]=dict(first_time_s=float(trace['time'][i]),minimum_distance_m=float(c.dist))
                unexpected[pair]['minimum_distance_m']=min(unexpected[pair]['minimum_distance_m'],float(c.dist))
    check('only_floor_support_and_intended_tray_contact',not unexpected,unexpected=unexpected,samples=len(trace['time']))
    replay=folder/'transport_verification.json'
    check('independent_transport_and_motor_replay_passed',replay.exists() and json.loads(replay.read_text())['passed'])
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,minimum_pelvis_height_m=minimum_height,
                verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),trace_sha256=hashlib.sha256((folder/'trace.npz').read_bytes()).hexdigest(),
                scope='One continuous bench-approach and tray subtask; initial map-pose prior and inferred stance remain assumptions; no paper branch or campaign qualification')
    (folder/'mission_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder');args=parser.parse_args()
    if not verify(args.folder)['passed']:raise SystemExit(1)
