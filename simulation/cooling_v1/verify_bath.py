"""Independently recompute lid support and physical AC150 key operations.

This certifies only the observed mechanical episode. Water filling, submerged
load handling, device electronics and thermal calibration need separate proof.
"""
import argparse,json
from pathlib import Path
import numpy as np
import mujoco
from bath_assets import load
from support_observation import support_load
from trace_store import load_trace,sha


def verify(directory,expected='nominal'):
    directory=Path(directory);result=json.loads((directory/'result.json').read_text());checks=[]
    def check(name,passed,**values):checks.append(dict(name=name,passed=bool(passed),**values))
    if expected=='nominal':check('complete_execution',result['status']=='passed' and result.get('development_limit') is None,failure=result.get('failure'))
    else:check('fault_execution_rejected',result['status']=='failed' and result.get('case')==expected,failure=result.get('failure'))
    changed=[]
    for name,digest in result['input_sha256'].items():
        path=directory/(name if name=='workcell.xml' else result['source_archive'][name])
        if sha(path)!=digest:changed.append(name)
    check('archived_sources_match',not changed,changed=changed)
    trace=load_trace(directory,result['artifacts_sha256']['physics_trace.npz']);times=trace['time'];q=trace['qpos']
    check('finite_trace',all(np.isfinite(value).all() for value in trace.values()))
    check('continuous_clock',len(times)>1 and np.all(np.diff(times)>0) and np.max(np.diff(times))<=.005001,
          samples=len(times),maximum_interval_s=float(np.max(np.diff(times))))
    check('trace_reaches_end',abs(times[-1]-result['simulated_seconds'])<1e-9)
    m=load(directory/'workcell.xml');m.opt.disableflags|=int(mujoco.mjtDisableBit.mjDSBL_WARMSTART);d=mujoco.MjData(m)
    check('solver_guard',result['maximum_solver_iterations']<m.opt.iterations and not any(result['warnings']),
          maximum_solver_iterations=result['maximum_solver_iterations'],limit=m.opt.iterations,warnings=result['warnings'])
    check('robot_only_actuation',m.nu==8 and all(m.jnt_bodyid[j]<m.body('bath_lid').id for j in m.actuator_trnid[:7,0]))
    check('no_payload_weld',not any(t==mujoco.mjtEq.mjEQ_WELD for t in m.eq_type))
    check('bounded_gripper',np.max(abs(trace['ctrl'][:,7]))<=40.000001)
    address=int(m.joint('bath_lid_free').qposadr[0]);positions=q[:,address:address+3]
    speed=np.linalg.norm(np.diff(positions,axis=0),axis=1)/np.diff(times)
    check('lid_motion_continuous',float(np.max(speed))<1.,maximum_sampled_speed_m_s=float(np.max(speed)))
    retained=any(e['label']=='bath_lid_load_transferred' for e in result['observations'])
    lid_chain=['bath_lid_grasped']+(['bath_lid_load_transferred'] if retained else [])+['bath_lid_supported']
    chain=lid_chain+['physical_button_press','bath_key_released']*3+lid_chain
    events=result['observations']
    if expected=='nominal':check('ordered_complete_chain',[e['label'] for e in events]==chain)
    elif expected=='missing_handle':check('no_false_lift',not events and 'bilateral grip lost' in result['failure'])
    elif expected=='blocked_key':check('no_false_key_success',[e['label'] for e in events]==lid_chain+['bath_key_force_stop'])
    else:raise ValueError(expected)
    def observe(at):
        i=int(np.argmin(abs(times-at)));d.qpos[:]=q[i];d.qvel[:]=trace['qvel'][i];d.ctrl[:]=trace['ctrl'][i];mujoco.mj_forward(m,d)
        return i
    def contacts(body):
        found={}
        for i,c in enumerate(d.contact):
            names=[m.body(int(m.geom_bodyid[g])).name for g in c.geom]
            if body not in names:continue
            f=np.zeros(6);mujoco.mj_contactForce(m,d,i,f);other=names[1-names.index(body)];found[other]=found.get(other,0.)+max(0.,float(f[0]))
        return found
    previous_support=np.array(result['configuration']['lid_closed_body_m'])
    for number,event in enumerate(events):
        i=observe(event['time_s']);check('exact_event_'+str(number),abs(times[i]-event['time_s'])<1e-9)
        if event['label']=='bath_lid_grasped':
            forces=contacts('bath_lid');lift=float(d.body('bath_lid').xpos[2]-previous_support[2])
            check('bilateral_lift_'+str(number),lift>.08 and all(forces.get(n,0)>.1 for n in ['left_finger','right_finger']),
                  lift_m=lift,normal_forces_N=forces)
        elif event['label']=='bath_lid_load_transferred':
            observation=support_load(m,d,'bath_lid',event['support']);forces=contacts('bath_lid')
            retained=(sum(forces.get(n,0) for n in ['left_finger','right_finger'])>.1 if event.get('retention')=='relaxed_handle_contact'
                      else all(forces.get(n,0)>.1 for n in ['left_finger','right_finger']))
            check('retained_load_transfer_'+str(number),observation['vertical_force_n']>.5*observation['body_weight_n']
                  and retained,retention=event.get('retention','bilateral_handle'),load=observation,normal_forces_N=forces)
        elif event['label']=='bath_lid_supported':
            support=event['support'];target=np.array(result['configuration']['lid_park_body_m' if support=='lid_stand' else 'lid_closed_body_m'])
            body=d.body('bath_lid');error=float(np.linalg.norm(body.xpos-target));tilt=float(np.arccos(np.clip(body.xmat[8],-1,1)))
            load_observation=support_load(m,d,'bath_lid',support);forces=contacts('bath_lid');motion=float(np.linalg.norm(body.cvel))
            check('supported_release_'+support,error<.002 and tilt<.035 and motion<.03
                  and load_observation['vertical_force_n']>.8*load_observation['body_weight_n'] and sum(forces.get(n,0) for n in ['left_finger','right_finger'])<.01,
                  error_m=error,tilt_rad=tilt,speed=motion,load=load_observation,normal_forces_N=forces)
            previous_support=target
        elif event['label']=='physical_button_press':
            name=event['body'];key=next(k for k in result['configuration']['keys'] if k['physical_body']==name)
            travel=float(d.joint(name+'_travel').qpos[0]);forces=contacts(name)
            check('physical_press_'+str(number),travel>.75*key['travel_m'] and travel<key['travel_m']+.0001 and forces.get('button_probe',0)>.01,
                  body=name,travel_m=travel,normal_forces_N=forces)
        elif event['label']=='bath_key_released':
            travel=float(d.joint(event['body']+'_travel').qpos[0]);check('key_return_'+str(number),abs(travel)<.0001,travel_m=travel)
    pressed=[e['body'] for e in events if e['label']=='physical_button_press']
    if expected=='nominal':check('dry_bath_control_sequence',pressed==['bath_key_standby','bath_key_escape','bath_key_standby'])
    elif expected=='missing_handle':
        observe(times[-1]);forces=contacts('bath_lid');error=float(np.linalg.norm(d.body('bath_lid').xpos-result['configuration']['lid_closed_body_m']))
        check('missing_handle_is_physical',sum(forces.get(n,0) for n in ['left_finger','right_finger'])<.01 and error<.002
              and not any((m.geom(i).name or '').startswith('lid_handle_segment_') for i in range(m.ngeom)),position_error_m=error,normal_forces_N=forces)
    elif expected=='blocked_key':
        observe(times[-1]);forces=contacts('bath_key_standby');travel=float(d.joint('bath_key_standby_travel').qpos[0]);joint=m.joint('bath_key_standby_travel')
        check('blocked_key_is_physical',forces.get('button_probe',0)>1.8 and travel<.0002 and abs(m.jnt_range[joint.id,1]-.0001)<1e-12,
              normal_forces_N=forces,travel_m=travel,mechanical_stop_m=float(m.jnt_range[joint.id,1]))
    other=[]
    for key in result['configuration']['keys']:
        joint=m.joint(key['physical_body']+'_travel');maximum=float(np.max(np.abs(q[:,joint.qposadr[0]])))
        allowed=set(pressed)|({'bath_key_standby'} if expected=='blocked_key' else set())
        if key['physical_body'] not in allowed:other.append(maximum)
        check('passive_key_'+key['id'],float(m.jnt_stiffness[joint.id])==800 and joint.id not in m.actuator_trnid[:,0])
    check('neighbour_keys_untouched',max(other,default=0)<.0001,maximum_other_travel_m=max(other,default=0))
    # Recompute every 5 ms saved contact state, independently of live guards.
    arm={'link1','link2','link3','link4','link5','link6','link7','hand'};worst=0.;worst_at=0.;bad=[];maximum_finger=0.;finger_at=0.
    body_names=[m.body(i).name for i in range(m.nbody)]
    for index,at in enumerate(times):
        d.qpos[:]=q[index];d.qvel[:]=trace['qvel'][index];d.ctrl[:]=trace['ctrl'][index];mujoco.mj_forward(m,d)
        fingers={'left_finger':0.,'right_finger':0.}
        for j,c in enumerate(d.contact):
            names=[body_names[m.geom_bodyid[g]] for g in c.geom]
            if 'bath_lid' in names and set(names)&set(fingers):
                force=np.zeros(6);mujoco.mj_contactForce(m,d,j,force)
                for side in set(names)&set(fingers):fingers[side]+=max(0.,float(force[0]))
            if (names[0] in arm)==(names[1] in arm):continue
            other=names[1] if names[0] in arm else names[0]
            if other in {'link0','left_finger','right_finger','button_probe'}:continue
            force=np.zeros(6);mujoco.mj_contactForce(m,d,j,force)
            if force[0]>worst:worst=float(force[0]);worst_at=float(at)
            if force[0]>2. and c.dist<0 and len(bad)<10:bad.append(dict(time_s=float(at),bodies=names,force_N=float(force[0]),overlap_m=float(c.dist)))
        if max(fingers.values())>maximum_finger:maximum_finger=max(fingers.values());finger_at=float(at)
    check('sampled_arm_clearance',not bad,maximum_unintended_force_N=worst,worst_time_s=worst_at,failures=bad)
    check('sampled_lid_finger_force_bound',maximum_finger<=25.,maximum_per_finger_normal_N=maximum_finger,worst_time_s=finger_at)
    report=dict(passed=all(c['passed'] for c in checks),expected=expected,checks=checks,result_sha256=sha(directory/'result.json'),
                verifier_sha256=sha(Path(__file__)),engine_version=mujoco.__version__,whole_paper_validated=False,
                scope='One continuous mechanical lid/open/park/key/regrasp/close episode. No filling, block/probe loading, electronics or thermal-calibration acceptance.')
    (directory/'verification.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory');parser.add_argument('--expected',choices=['nominal','missing_handle','blocked_key'],default='nominal');args=parser.parse_args();report=verify(args.directory,args.expected)
    print(json.dumps(dict(passed=report['passed'],checks=len(report['checks']),failed=[c for c in report['checks'] if not c['passed']]),indent=2))
    raise SystemExit(0 if report['passed'] else 1)
