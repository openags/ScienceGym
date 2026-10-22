"""Independent saved-state checks for a contact-driven USB-TC wire cycle."""
import argparse,json
from pathlib import Path
import numpy as np,mujoco
from extended_device_assets import load
from support_observation import support_load
from trace_store import sha,load_trace


def verify(directory,expected='nominal'):
    directory=Path(directory);result=json.loads((directory/'result.json').read_text());checks=[]
    def check(name,passed,**values):checks.append(dict(name=name,passed=bool(passed),**values))
    check('expected_execution_outcome',result['status']==('passed' if expected=='nominal' else 'failed') and result.get('development_limit') is None,failure=result.get('failure'))
    changed=[]
    for name,digest in result['input_sha256'].items():
        path=directory/(name if name=='workcell.xml' else result['source_archive'][name])
        if sha(path)!=digest:changed.append(name)
    check('archived_sources_match',not changed,changed=changed)
    t=load_trace(directory,result['artifacts_sha256']['physics_trace.npz']);times=t['time']
    check('finite_trace',all(np.isfinite(v).all() for v in t.values()))
    check('continuous_clock',len(times)>1 and np.all(np.diff(times)>0) and np.max(np.diff(times))<=.005001,
          samples=len(times),maximum_interval_s=float(np.max(np.diff(times))))
    check('trace_reaches_end',abs(times[-1]-result['simulated_seconds'])<1e-9)
    m=load(directory/'workcell.xml');m.opt.disableflags|=int(mujoco.mjtDisableBit.mjDSBL_WARMSTART);d=mujoco.MjData(m)
    prefix=result['configuration']['terminal']['prefix'];axis=np.array(result['configuration']['terminal']['insertion_axis']);entry=np.array(result['configuration']['entry_m'])
    numerical=result['numerics'];check('numerical_guards',numerical['maximum_solver_iterations']<m.opt.iterations and numerical['solver_limit_steps']==0 and not any(numerical['warnings']),observed=numerical)
    check('only_robot_and_driver_actuated',m.nu==9 and all(m.jnt_bodyid[j]<m.body('mcc_usb_tc').id for i,j in enumerate(m.actuator_trnid[:,0]) if i!=7))
    check('no_payload_weld',not any(v==mujoco.mjtEq.mjEQ_WELD for v in m.eq_type))
    check('bounded_gripper_command',np.max(abs(t['ctrl'][:,7]))<=40.000001)
    check('selected_full_wire_length',m.nflex==1 and abs(float(m.flexedge_length0.sum())+.042-.6)<1e-5,
          total_length_m=float(m.flexedge_length0.sum())+.042)
    address=int(m.joint('wire_free').qposadr[0]);positions=t['qpos'][:,address:address+3]
    speed=np.linalg.norm(np.diff(positions,axis=0),axis=1)/np.diff(times)
    check('sampled_wire_continuity',np.max(speed)<1.,maximum_speed_m_s=float(np.max(speed)))
    advance=m.joint(prefix+'_advance').qposadr[0];turn=m.joint(prefix+'_turn').qposadr[0]
    residual=np.abs(t['qpos'][:,advance]-t['qpos'][:,turn]*.0005/(2*np.pi))
    check('passive_thread_kinematics',float(np.max(residual))<1e-5,maximum_axial_residual_m=float(np.max(residual)))
    maximum=0.;worst=0.
    for i,at in enumerate(times):
        d.qpos[:]=t['qpos'][i];mujoco.mj_kinematics(m,d);mujoco.mj_comPos(m,d);mujoco.mj_flex(m,d)
        strain=float(np.max(abs(d.flexedge_length/m.flexedge_length0-1)))
        if strain>maximum:maximum=strain;worst=float(at)
    check('lead_strain_all_saved_states',maximum<.01,maximum_edge_strain=maximum,worst_time_s=worst)
    def observe(at):
        i=int(np.argmin(abs(times-at)));d.qpos[:]=t['qpos'][i];d.qvel[:]=t['qvel'][i];d.ctrl[:]=t['ctrl'][i];mujoco.mj_forward(m,d)
        clamp=0.;driver=0.;clip=0.;fingers={};axial=0.
        for j,c in enumerate(d.contact):
            if min(c.geom)<0:continue
            names=[m.body(int(m.geom_bodyid[g])).name for g in c.geom];f=np.zeros(6);mujoco.mj_contactForce(m,d,j,f);force=c.frame.reshape(3,3).T@f[:3]
            if {prefix+'_plate','wire'}<=set(names):clamp+=max(0.,float(f[0]))
            if {prefix+'_screw','driver_rotor'}<=set(names):driver+=max(0.,float(f[0]))
            if 'wire' in names:
                other=names[1-names.index('wire')]
                if other in {'left_finger','right_finger'}:
                    fingers[other]=fingers.get(other,0.)+max(0.,float(f[0]));axial+=float(np.dot(force,axis))*(1 if names[1]=='wire' else -1)
                if other.startswith('wire_clip_leaf'):clip+=max(0.,float(f[0]))
        tip=d.site('wire_tip').xpos;return dict(time_s=float(times[i]),depth_m=float(np.dot(tip-entry,axis)),
            clamp_normal_N=clamp,driver_normal_N=driver,clip_normal_N=clip,finger_normal_N=fingers,finger_axial_N=axial,
            screw_advance_m=float(d.qpos[advance]),screw_turn_rad=float(d.qpos[turn]),tip_m=tip.tolist())
    chain=['wire_grasped','wire_inserted_while_held','wire_retained_by_fixture','driver_seated','terminal_tightened','driver_retracted','wire_grasped','wire_pull_checked','driver_seated','terminal_opened','driver_retracted','wire_grasped','wire_withdrawn','wire_returned']
    events=result['observations'];labels=[e['label'] for e in events]
    if expected=='nominal':check('ordered_complete_chain',labels==chain)
    elif expected=='missing_bit':
        check('failed_at_physical_driver_seating',labels==chain[:3] and 'did not seat in the physical slot' in result['failure'])
        bit=m.geom('driver_bit');check('bit_contact_physically_absent',m.geom_contype[bit.id]==0 and m.geom_conaffinity[bit.id]==0)
    elif expected=='missing_clamp':
        check('failed_at_clamp_operation',labels==chain[:4] and ('thread/clamp condition' in result['failure'] or 'axial bound' in result['failure']))
        plate=m.geom(prefix+'_pressure_plate');check('clamp_contact_physically_absent',m.geom_contype[plate.id]==0 and m.geom_conaffinity[plate.id]==0)
    else:raise ValueError(expected)
    for index,event in enumerate(events):
        observation=observe(event['time_s']);check('exact_event_'+str(index),abs(observation['time_s']-event['time_s'])<1e-9)
        label=event['label'];fingers=sum(observation['finger_normal_N'].values())
        if label=='wire_inserted_while_held':check('wire_inserted',.0045<observation['depth_m']<.0055 and fingers>.4,**observation)
        elif label=='wire_retained_by_fixture':check('passive_clip_retention',.004<observation['depth_m']<.006 and observation['clip_normal_N']>.01 and fingers<.01,**observation)
        elif label=='driver_seated':check('physical_driver_seating_'+event['operation'],observation['driver_normal_N']>.05,**observation)
        elif label=='terminal_tightened':check('physical_clamp_load',observation['clamp_normal_N']>=4 and observation['screw_advance_m']<-.001,**observation)
        elif label=='driver_retracted':
            retained=observation['clamp_normal_N']>1 if event['operation']=='tighten' else observation['clamp_normal_N']<.01
            check('driver_withdrawal_'+event['operation'],observation['driver_normal_N']<.01 and retained and fingers<.01,**observation)
        elif label=='terminal_opened':check('clamp_opened',observation['screw_advance_m']>-.00003 and observation['clamp_normal_N']<.01,**observation)
        elif label=='wire_pull_checked':
            start=next(e['time_s'] for e in reversed(events[:index]) if e['label']=='wire_grasped');indices=np.flatnonzero((times>=start)&(times<=event['time_s']));initial=positions[indices[0]]
            displacement=float(np.max(np.linalg.norm(positions[indices]-initial,axis=1)));peak=0.;minimum_clamp=float('inf');held_forces=[]
            for i in indices:
                row=observe(times[i]);peak=max(peak,abs(row['finger_axial_N']));minimum_clamp=min(minimum_clamp,row['clamp_normal_N'])
                if times[i]>=event['time_s']-.29:held_forces.append(abs(row['finger_axial_N']))
            check('physical_one_newton_pull',peak>=1. and displacement<.0002 and minimum_clamp>1. and len(held_forces)>=58 and min(held_forces)>=1.,
                  maximum_pull_N=peak,maximum_displacement_m=displacement,minimum_clamp_N=minimum_clamp,minimum_final_held_force_N=min(held_forces,default=0),held_samples=len(held_forces))
        elif label=='wire_withdrawn':check('released_axial_withdrawal',observation['depth_m']<-.03 and observation['clamp_normal_N']<.01 and fingers>.4,**observation)
        elif label=='wire_returned':
            load_observation=support_load(m,d,'wire','wire_stand');error=float(np.linalg.norm(d.body('wire').xpos-result['configuration']['wire_park_m']))
            end_weight=float(m.body_mass[m.body('wire').id])*9.81
            check('returned_to_support',error<.002 and fingers<.01 and load_observation['vertical_force_n']>.8*end_weight,error_m=error,
                  supported_rigid_end_weight_N=end_weight,tail_support='remaining string is allowed to rest on the bench',load=load_observation,**observation)
    # Independently recompute saved contacts. The 5 ms archive cannot certify
    # the executor's 3 ms contact-gap bound; that finer bound stays a live
    # guard, rather than being falsely promoted to independent evidence.
    grip_indices={int(np.argmin(abs(times-e['time_s']))) for e in result.get('grip_observations',[])}
    arm={'link1','link2','link3','link4','link5','link6','link7','hand'};body_names=[m.body(i).name for i in range(m.nbody)]
    bad=[];grips=[];maximum_clamp=0.;maximum_driver=0.;driving=[]
    for index,e in enumerate(events):
        if e['label']=='driver_seated':
            end=next((n['time_s'] for n in events[index+1:] if n['label'] in {'terminal_tightened','terminal_opened'}),times[-1])
            driving.append((e['time_s'],end))
    normals=[]
    for index,at in enumerate(times):
        d.qpos[:]=t['qpos'][index];d.qvel[:]=t['qvel'][index];d.ctrl[:]=t['ctrl'][index];mujoco.mj_forward(m,d)
        finger={'left_finger':0.,'right_finger':0.};clamp=0.;driver_z=0.
        for j,c in enumerate(d.contact):
            names=[body_names[m.geom_bodyid[g]] if g>=0 else 'wire_extension' for g in c.geom]
            force=np.zeros(6);mujoco.mj_contactForce(m,d,j,force);normal=max(0.,float(force[0]))
            if 'wire' in names:
                other=names[1-names.index('wire')]
                if other in finger:finger[other]+=normal
                if other==prefix+'_plate':clamp+=normal
            if {prefix+'_screw','driver_rotor'}<=set(names):
                world=c.frame.reshape(3,3).T@force[:3];driver_z+=float(world[2])*(1 if names[1]=='driver_rotor' else -1)
            unintended=False
            if set(names)&arm:
                connected=False
                if set(names)&{'link0','left_finger','right_finger'}:
                    other=next(n for n in names if n not in {'link0','left_finger','right_finger'})
                    connected=other=='hand' or (other=='link1' and 'link0' in names)
                if names[0] in arm and names[1] in arm:
                    a,b=m.body(names[0]).id,m.body(names[1]).id;connected=m.body_parentid[a]==b or m.body_parentid[b]==a
                unintended=not connected and normal>2.
            if set(names)&set(finger):
                other=next((n for n in names if n not in finger),None)
                unintended|=other not in {'wire','hand',None} and normal>.02
            if 'driver_rotor' in names:
                other=names[1-names.index('driver_rotor')]
                unintended|=other not in {prefix+'_screw','driver_mount','hand'} and normal>.05
            if unintended and len(bad)<10:bad.append(dict(time_s=float(at),bodies=names,normal_N=normal))
        normals.append([finger['left_finger'],finger['right_finger']]);maximum_clamp=max(maximum_clamp,clamp)
        if any(start<=at<=end for start,end in driving):maximum_driver=max(maximum_driver,abs(driver_z))
        if index in grip_indices:
            body=d.body('wire').xmat.reshape(3,3);wire_axis=body@axis;delta=d.site('tcp').xpos-d.body('wire').xpos
            axial=float(np.dot(delta,wire_axis));radial=float(np.linalg.norm(delta-axial*wire_axis))
            angle=float(np.arccos(np.clip(abs(np.dot(wire_axis,d.body('hand').xmat.reshape(3,3)[:,0])),-1,1)))
            grips.append(dict(index=index,time_s=float(at),axial_m=axial,radial_m=radial,axis_angle_rad=angle))
    check('sampled_unintended_contacts',not bad,failures=bad)
    check('sampled_clamp_load_bound',maximum_clamp<=6.,maximum_N=maximum_clamp)
    if expected=='nominal':check('sampled_driver_axial_bound',maximum_driver<=1.,maximum_N=maximum_driver)
    violations=[];normal_array=np.array(normals)
    for grip in grips:
        k=grip['index'];window=np.flatnonzero((times>=times[k]-.050001)&(times<=times[k]));means=normal_array[window].mean(axis=0)
        if abs(grip['axial_m'])>.0025 or grip['radial_m']>.003 or grip['axis_angle_rad']>.1 or min(means)<.2:
            violations.append(dict(**grip,mean_sampled_normal_N=means.tolist()))
    check('sampled_observed_grasp_geometry',bool(grips) and not violations,observations=len(grips),failures=violations[:10],
          contact_sampling_interval_s=.005,live_three_ms_gap_independently_proven=False)
    report=dict(passed=all(c['passed'] for c in checks),expected=expected,checks=checks,result_sha256=sha(directory/'result.json'),verifier_sha256=sha(Path(__file__)),
                engine_version=mujoco.__version__,whole_paper_validated=False,electrical_continuity_validated=False,
                scope='One 24 AWG extension end and selected passive terminal: insertion, screw operation, robot pull test, withdrawal and return. No paired circuit or fine-wire transition.')
    (directory/'verification.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--expected',choices=['nominal','missing_bit','missing_clamp'],default='nominal');a=p.parse_args();r=verify(a.directory,a.expected)
    print(json.dumps(dict(passed=r['passed'],checks=len(r['checks']),failed=[c for c in r['checks'] if not c['passed']]),indent=2))
    raise SystemExit(0 if r['passed'] else 1)
