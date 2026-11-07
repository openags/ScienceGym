"""Recompute contact-driven cover access from archived physical states."""
import argparse,json
from pathlib import Path
import numpy as np,mujoco
from optical_assets import load
from trace_store import sha,load_trace


def verify(directory,expected='nominal'):
    directory=Path(directory);result=json.loads((directory/'result.json').read_text());checks=[]
    def check(name,passed,**values):checks.append(dict(name=name,passed=bool(passed),**values))
    check('expected_execution_outcome',result['case']==expected and result['status']==('passed' if expected=='nominal' else 'failed'),failure=result['failure'])
    changed=[]
    for name,digest in result['input_sha256'].items():
        path=directory/(name if name=='workcell.xml' else result['source_archive'][name])
        if sha(path)!=digest:changed.append(name)
    check('archived_input_hashes',not changed,changed=changed)
    t=load_trace(directory,result['artifacts_sha256']['physics_trace.npz']);times=t['time']
    check('finite_saved_states',all(np.isfinite(v).all() for v in t.values()))
    check('continuous_clock',len(times)>1 and np.all(np.diff(times)>0) and np.max(np.diff(times))<=.005001,
          samples=len(times),maximum_interval_s=float(np.max(np.diff(times))))
    check('trace_reaches_end',abs(times[-1]-result['simulated_seconds'])<1e-9)
    m=load(directory/'workcell.xml');m.opt.disableflags|=int(mujoco.mjtDisableBit.mjDSBL_WARMSTART);d=mujoco.MjData(m)
    hinge=m.joint('spectrometer_lid_hinge');slider=m.joint('sample_slider_travel');angle=t['qpos'][:,hinge.qposadr[0]]
    check('passive_cover_and_slider',hinge.id not in m.actuator_trnid[:,0] and slider.id not in m.actuator_trnid[:,0] and m.nu==8)
    check('no_attachment_weld',not any(v==mujoco.mjtEq.mjEQ_WELD for v in m.eq_type))
    check('bounded_gripper_command',np.max(abs(t['ctrl'][:,7]))<=40.000001)
    check('numerical_guards',result['maximum_solver_iterations']<m.opt.iterations and not any(result['warnings']),
          maximum_solver_iterations=result['maximum_solver_iterations'],limit=m.opt.iterations,warnings=result['warnings'])
    speed=np.max(abs(np.diff(angle)/np.diff(times)))
    check('continuous_hinge_motion',speed<2.,maximum_sampled_speed_rad_s=float(speed))
    slider_travel=np.max(abs(t['qpos'][:,slider.qposadr[0]]))
    check('slider_remains_closed_for_cover_cycle',slider_travel<.0001,maximum_travel_m=float(slider_travel))
    check('selected_hinge_friction_recorded',abs(float(m.dof_frictionloss[hinge.dofadr[0]])-result['configuration']['selected_hinge_friction_Nm'])<1e-12)
    body_names=[m.body(i).name for i in range(m.nbody)];observations=[];bad=[];maximum_finger=0.;maximum_case=0.;worst_overlap=0.
    arm={'link1','link2','link3','link4','link5','link6','link7','hand'}
    for index,at in enumerate(times):
        d.qpos[:]=t['qpos'][index];d.qvel[:]=t['qvel'][index];d.ctrl[:]=t['ctrl'][index];mujoco.mj_forward(m,d)
        fingers={'left_finger':0.,'right_finger':0.};case=0.;overlap=0.
        for j,c in enumerate(d.contact):
            names=[body_names[m.geom_bodyid[g]] for g in c.geom];normal=None
            def force():
                f=np.zeros(6);mujoco.mj_contactForce(m,d,j,f);return max(0.,float(f[0]))
            if 'spectrometer_lid' in names:
                for side in set(names)&set(fingers):fingers[side]+=force()
                if 'nicolet' in names:case=max(case,force());overlap=min(overlap,float(c.dist))
            if (names[0] in arm)!=(names[1] in arm):
                other=names[1] if names[0] in arm else names[0]
                if other not in {'link0','left_finger','right_finger'} and force()>2 and c.dist<0 and len(bad)<10:
                    bad.append(dict(time_s=float(at),bodies=names,normal_N=force(),overlap_m=float(c.dist)))
        maximum_finger=max(maximum_finger,*fingers.values());maximum_case=max(maximum_case,case);worst_overlap=min(worst_overlap,overlap)
        observations.append(dict(fingers=fingers,case_N=case))
    check('sampled_arm_clearance',not bad,failures=bad)
    check('cover_case_clearance',maximum_case<=10 and worst_overlap>=-.0001,maximum_contact_N=maximum_case,maximum_overlap_m=-worst_overlap)
    if expected=='nominal':check('selected_finger_force_bound',maximum_finger<=25.,maximum_per_finger_N=maximum_finger)
    events=result['observations'];labels=[e['label'] for e in events]
    chain=['spectrometer_cover_grasped','spectrometer_cover_positioned','spectrometer_cover_released']*2
    if expected=='nominal':check('complete_ordered_chain',labels==chain)
    elif expected=='missing_handle':
        check('missing_handle_rejected_before_grasp',not events and 'bilateral grip lost' in result['failure'])
        check('handle_physically_absent',not any((m.geom(i).name or '').startswith('spectrometer_handle_') for i in range(m.ngeom)))
    elif expected=='locked_hinge':
        check('locked_hinge_rejected_before_opening',labels==['spectrometer_cover_grasped'] and np.max(abs(angle))<.001)
        check('physical_hinge_stop',np.max(abs(m.jnt_range[hinge.id]-[-.0001,0]))<1e-12)
    else:raise ValueError(expected)
    for number,event in enumerate(events):
        k=int(np.argmin(abs(times-event['time_s'])));row=observations[k];forces=row['fingers']
        check('exact_event_'+str(number),abs(times[k]-event['time_s'])<1e-9)
        if event['label']=='spectrometer_cover_grasped':
            check('bilateral_handle_grasp_'+str(number),min(forces.values())>.1,normal_forces_N=forces)
        elif event['label']=='spectrometer_cover_positioned':
            check('contact_driven_position_'+str(number),abs(angle[k]-event['target_rad'])<.025 and min(forces.values())>.1,
                  actual_angle_rad=float(angle[k]),target_rad=event['target_rad'],normal_forces_N=forces)
        elif event['label']=='spectrometer_cover_released':
            indices=np.flatnonzero((times>=times[k]-.99)&(times<=times[k]));error=float(np.max(abs(angle[indices]-event['target_rad'])))
            finger_force=max(sum(observations[i]['fingers'].values()) for i in indices)
            check('passive_retention_after_release_'+str(number),error<.01 and finger_force<.01 and len(indices)>=198,
                  maximum_angle_error_rad=error,maximum_finger_N=finger_force,samples=len(indices))
    report=dict(passed=all(c['passed'] for c in checks),expected=expected,checks=checks,result_sha256=sha(directory/'result.json'),
                verifier_sha256=sha(Path(__file__)),engine_version=mujoco.__version__,whole_paper_validated=False,
                scope='Bare instrument hinged-cover opening and return with selected mechanical parameters. Sliding-window operation, optical accessory installation and specimen transfer remain separate obligations.')
    (directory/'verification.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--expected',choices=['nominal','missing_handle','locked_hinge'],default='nominal');a=p.parse_args();r=verify(a.directory,a.expected)
    print(json.dumps(dict(passed=r['passed'],checks=len(r['checks']),failed=[c for c in r['checks'] if not c['passed']]),indent=2))
    raise SystemExit(0 if r['passed'] else 1)
