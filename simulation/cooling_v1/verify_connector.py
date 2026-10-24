"""Recompute mating, release, withdrawal and lead integrity from saved states."""
import argparse
import json
from pathlib import Path
import numpy as np
import mujoco
import extended_device_assets  # Register the source-meter visual namespace.
from device_assets import load
from trace_store import load_trace,sha
from support_observation import support_load


def verify(directory,expected='nominal'):
    directory=Path(directory);result=json.loads((directory/'result.json').read_text())
    checks=[]
    def check(name,passed,**values):checks.append(dict(name=name,passed=bool(passed),**values))
    changed=[]
    for name,digest in result['input_sha256'].items():
        path=directory/name if name=='workcell.xml' else directory/result['source_archive']/name
        if sha(path)!=digest:changed.append(name)
    check('archived_input_pins',not changed,changed=changed)
    trace=load_trace(directory,result['artifacts_sha256']['physics_trace.npz']);times=trace['time']
    check('finite_trace',all(np.isfinite(x).all() for x in trace.values()))
    check('continuous_clock',np.all(np.diff(times)>0) and np.max(np.diff(times))<=.001001,
          maximum_interval_s=float(np.max(np.diff(times))))
    check('trace_reaches_end',abs(times[-1]-result['simulated_seconds'])<.001001)
    model=load(directory/'workcell.xml');model.opt.disableflags|=int(mujoco.mjtDisableBit.mjDSBL_WARMSTART);data=mujoco.MjData(model)
    plug=model.body('plug').id
    check('only_robot_actuated',model.nu==8 and all(model.jnt_bodyid[j]<plug for j in model.actuator_trnid[:7,0]))
    check('no_attachment_weld',not any(t==mujoco.mjtEq.mjEQ_WELD for t in model.eq_type))
    check('one_continuous_lead',model.nflex==1 and abs(float(model.flexedge_length0.sum())-.6)<1e-5,
          rest_length_m=float(model.flexedge_length0.sum()))
    leaf_stiffness=[float(model.jnt_stiffness[model.joint('leaf_compression_'+str(i)).id]) for i in range(4)]
    check('passive_contact_leaves',leaf_stiffness==([0.]*4 if expected=='missing_spring' else [2500.]*4))
    check('bounded_gripper_command',np.max(abs(trace['ctrl'][:,7]))<=40.000001)
    address=int(model.joint('plug_free').qposadr[0]);positions=trace['qpos'][:,address:address+3]
    speed=np.linalg.norm(np.diff(positions,axis=0),axis=1)/np.diff(times)
    check('sampled_payload_continuity',np.max(speed)<1.,max_speed_m_s=float(np.max(speed)))
    maximum=0.;worst=0.
    for i in range(len(times)):
        data.qpos[:]=trace['qpos'][i];mujoco.mj_kinematics(model,data);mujoco.mj_comPos(model,data);mujoco.mj_flex(model,data)
        strain=float(np.max(abs(data.flexedge_length/model.flexedge_length0-1)))
        if strain>maximum:maximum=strain;worst=float(times[i])
    check('lead_length_throughout',maximum<.01,max_edge_strain=maximum,worst_time_s=worst)
    def observe(at):
        i=int(np.argmin(abs(times-at)));data.qpos[:]=trace['qpos'][i];data.qvel[:]=trace['qvel'][i];data.ctrl[:]=trace['ctrl'][i]
        mujoco.mj_forward(model,data);entry=np.array(result['configuration']['entry_m']);tip=data.site('plug_tip').xpos
        leaf=0.;socket=0.;fingers={};unintended=0.
        for j,c in enumerate(data.contact):
            names=[model.body(int(model.geom_bodyid[g])).name if g>=0 else 'lead' for g in c.geom]
            force=np.zeros(6);mujoco.mj_contactForce(model,data,j,force);normal=max(0.,float(force[0]))
            if any(n.startswith('jack_') for n in names):
                if any(n=='plug' or n.startswith('plug_leaf_') for n in names):socket+=normal
                if any(n in {'left_finger','right_finger'} for n in names):unintended+=normal
            if 'jack_'+result['configuration']['port'] in names and any(n.startswith('plug_leaf_') for n in names):leaf+=normal
            if 'plug' in names:
                for n in set(names)&{'left_finger','right_finger'}:fingers[n]=fingers.get(n,0.)+normal
        return dict(time_s=float(times[i]),depth_m=float(tip[1]-entry[1]),lateral_m=float(np.linalg.norm((tip-entry)[[0,2]])),
            leaf_normal_N=leaf,socket_normal_N=socket,finger_N=fingers,unintended_finger_socket_N=unintended,
            speed=float(np.linalg.norm(data.body('plug').cvel)))
    events={e['label']:e for e in result['observations']}
    release=observe(events['plug_released_in_socket']['time_s']) if 'plug_released_in_socket' in events else None
    if expected=='nominal':
        check('completed_execution',result['status']=='passed',failure=result.get('failure'))
        expected_events=['grasp_and_lift_observed','plug_aligned_before_entry','plug_released_in_socket','plug_withdrawn','plug_returned']
        check('complete_ordered_chain',[e['label'] for e in result['observations']]==expected_events)
        if release:
            check('released_contact_retention',.009<release['depth_m']<.011 and release['lateral_m']<.0003
                  and release['leaf_normal_N']>.1 and sum(release['finger_N'].values())<.01 and release['speed']<.03,**release)
        else:check('released_contact_retention',False)
        if 'plug_withdrawn' in events:
            observation=observe(events['plug_withdrawn']['time_s'])
            check('axial_withdrawal',observation['depth_m']<-.06 and observation['leaf_normal_N']<.01
                  and all(observation['finger_N'].get(n,0)>.03 for n in ['left_finger','right_finger']),**observation)
        else:check('axial_withdrawal',False)
        observation=observe(times[-1]);load_obs=support_load(model,data,'plug','plug_stand')
        error=float(np.linalg.norm(data.body('plug').xpos-result['configuration']['park_m']))
        check('returned_and_released',error<.002 and sum(observation['finger_N'].values())<.01 and observation['speed']<.03
              and load_obs['vertical_force_n']>.5*load_obs['body_weight_n'],error_m=error,load=load_obs,**observation)
    elif expected=='missing_spring':
        stopping=events.get('socket_force_limit');final_observation=observe(times[-1])
        retained_failure=release is not None and (release['leaf_normal_N']<=.1 or release['lateral_m']>=.0003)
        load_failure=stopping is not None and stopping['normal_force_N']>stopping['limit_N'] and final_observation['socket_normal_N']>1.
        check('missing_spring_fault_detected',result['status']=='failed' and
              ('retained insertion' in result['failure'] or '5 N stop bound' in result['failure']))
        check('fault_is_physical',retained_failure or load_failure,release=release,stop=stopping,final_observation=final_observation)
        check('no_success_after_fault','plug_returned' not in events)
    elif expected=='blocked_bore':
        check('force_stop_detected',result['status']=='failed' and '5 N stop bound' in result['failure'])
        observation=observe(times[-1])
        check('stopped_before_neighbor_contact',observation['unintended_finger_socket_N']<.05,**observation)
        check('no_false_retained_insertion',release is None)
    else:raise ValueError('Unknown expected case')
    report=dict(passed=all(c['passed'] for c in checks),expected=expected,checks=checks,
        result_sha256=sha(directory/'result.json'),verifier_sha256=sha(Path(__file__)),engine_version=mujoco.__version__,
        whole_paper_validated=False,electrical_continuity_validated=False,
        scope='One selected cabled plug: contact mating, release, withdrawal, return and fault detection. No complete heater circuit.')
    (directory/'verification.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory');parser.add_argument('--expected',choices=['nominal','missing_spring','blocked_bore'],default='nominal');args=parser.parse_args()
    result=verify(args.directory,args.expected)
    print(json.dumps(dict(passed=result['passed'],checks=len(result['checks']),failed=[c for c in result['checks'] if not c['passed']]),indent=2))
    raise SystemExit(0 if result['passed'] else 1)
