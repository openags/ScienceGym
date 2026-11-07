"""Independently replay passive-thread jig states and the recorded pull load."""
import argparse
import json
from pathlib import Path
import numpy as np
import mujoco
from trace_store import sha
from world import HERE


def verify(directory,expected='nominal'):
    directory=Path(directory);result=json.loads((directory/'result.json').read_text());checks=[]
    def check(name,passed,**values):checks.append(dict(name=name,passed=bool(passed),**values))
    check('archived_sources',all(sha(directory/result['source_archive'][n])==digest for n,digest in result['source_sha256'].items()))
    check('artifact_hashes',all(sha(directory/n)==digest for n,digest in result['artifact_sha256'].items()))
    check('sources_stable_during_execution',result['source_unchanged'])
    trace=np.load(directory/'physics_trace.npz');times=trace['time'];model=mujoco.MjModel.from_xml_path(str(directory/'workcell.xml'))
    model.opt.disableflags|=int(mujoco.mjtDisableBit.mjDSBL_WARMSTART);data=mujoco.MjData(model)
    check('finite_trace',all(np.isfinite(trace[n]).all() for n in trace.files))
    check('clock_and_terminal_state',np.all(np.diff(times)>0) and np.max(np.diff(times))<.005001 and abs(times[-1]-result['simulated_seconds'])<1e-9,
        samples=len(times),largest_interval_s=float(np.max(np.diff(times))))
    check('no_solver_warning_or_exhaustion',not any(result['warnings']) and result['solver_cap_steps']==0 and result['maximum_solver_iterations']<model.opt.iterations)
    check('only_the_driver_actuated',model.nu==2 and {model.joint(int(j)).name for j in model.actuator_trnid[:,0]}=={'driver_z','driver_spin'})
    check('free_wire_without_attachment',model.jnt_type[model.joint('wire_free').id]==mujoco.mjtJoint.mjJNT_FREE and
          model.neq==2 and all(t==mujoco.mjtEq.mjEQ_JOINT for t in model.eq_type))
    prefix=result['configuration']['prefix'];pitch=result['configuration']['thread_pitch_m']
    q=lambda name:trace['qpos'][:,int(model.joint(name).qposadr[0])]
    thread=np.max(abs(q(prefix+'_advance')-pitch*q(prefix+'_turn')/(2*np.pi)))
    capture=np.max(abs(q(prefix+'_plate_slide')-q(prefix+'_advance')))
    check('observed_helical_and_captive_relations',thread<.00001 and capture<.00001,thread_error_m=float(thread),plate_error_m=float(capture))
    axis=np.array(result['configuration']['insertion_axis'],float);loads=trace['wire_xfrc']
    zero=np.linalg.norm(loads,axis=1)<1e-10;pull=np.linalg.norm(loads-np.r_[-axis,np.zeros(3)],axis=1)<1e-10
    check('only_declared_one_newton_pull',np.all(zero|pull))
    events={e['event']:e for e in result['events']}
    wire=model.body('wire').id
    def observe(at):
        i=int(np.argmin(abs(times-at)));check('exact_event_state_'+str(at),abs(times[i]-at)<1e-9)
        data.qpos[:]=trace['qpos'][i];data.qvel[:]=trace['qvel'][i];data.ctrl[:]=trace['ctrl'][i];data.xfrc_applied[:]=0;data.xfrc_applied[wire]=loads[i]
        mujoco.mj_forward(model,data);normal=0.;driver=0.
        for j,c in enumerate(data.contact):
            names={model.geom(g).name for g in c.geom};force=np.zeros(6);mujoco.mj_contactForce(model,data,j,force)
            if {prefix+'_pressure_plate','wire_conductor'}<=names:normal+=force[0]
            if 'driver_bit' in names:driver+=force[0]
        return dict(clamp_normal_N=float(normal),driver_contact_N=float(driver),wire_m=data.body('wire').xpos.copy(),
            advance_m=float(data.joint(prefix+'_advance').qpos[0]),turn_rad=float(data.joint(prefix+'_turn').qpos[0]),xfrc=loads[i].copy())
    positive=expected in {'nominal','opposing_bank','half_step','noslip_refinement'}
    if positive:
        check('complete_retention_test',result['status']=='done' and result['retained'] and list(events)==['clamped','driver_released','pull_started','pull_complete'])
        for name in ['clamped','driver_released','pull_started','pull_complete']:
            if name not in events:check('required_event_'+name,False)
        if all(n in events for n in ['clamped','driver_released','pull_started','pull_complete']):
            tightened=observe(events['clamped']['time']);released=observe(events['driver_released']['time'])
            start=observe(events['pull_started']['time']);end=observe(events['pull_complete']['time'])
            check('contact_driven_thread_motion',tightened['turn_rad']<-2*np.pi and tightened['advance_m']<-.001 and tightened['clamp_normal_N']>3.5,
                turn_rad=tightened['turn_rad'],travel_m=tightened['advance_m'],normal_N=tightened['clamp_normal_N'])
            check('passive_retention_after_driver_release',released['clamp_normal_N']>1 and released['driver_contact_N']<.01,
                normal_N=released['clamp_normal_N'],driver_contact_N=released['driver_contact_N'])
            address=int(model.joint('wire_free').qposadr[0]);mask=times>=events['pull_started']['time']
            displacement=float(np.max(np.linalg.norm(trace['qpos'][mask,address:address+3]-start['wire_m'],axis=1)))
            check('one_second_physical_pull',events['pull_complete']['time']-events['pull_started']['time']>=1 and
                np.all(pull[times>events['pull_started']['time']]) and displacement<.0002 and end['clamp_normal_N']>1 and end['driver_contact_N']<.01,
                maximum_displacement_m=displacement,final_normal_N=end['clamp_normal_N'])
    elif expected in {'missing_clamp','missing_bit'}:
        check('missing_hardware_rejected',result['status']=='no_clamp_force' and not result['retained'] and 'clamped' not in events)
        if expected=='missing_clamp':
            g=model.geom(prefix+'_pressure_plate').id;check('clamp_removed_from_contact',model.geom_contype[g]==0 and model.geom_conaffinity[g]==0)
        else:
            g=model.geom('driver_bit').id;check('bit_removed_from_contact',model.geom_contype[g]==0 and model.geom_conaffinity[g]==0)
        final=observe(times[-1]);check('no_wire_clamping_contact',final['clamp_normal_N']<.01,normal_N=final['clamp_normal_N'])
    elif expected in {'no_thread_friction','regularized_creep'}:
        check('retention_failure_rejected',result['status']=='pull_out' and not result['retained'] and 'wire_pulled_out' in events)
        check('declared_failure_model',float(model.dof_frictionloss[model.joint(prefix+'_turn').dofadr[0]])==0 if expected=='no_thread_friction' else model.opt.noslip_iterations==0)
        if 'driver_released' in events and 'pull_started' in events:
            released=observe(events['driver_released']['time']);start=observe(events['pull_started']['time']);end=observe(times[-1])
            displacement=float(np.linalg.norm(end['wire_m']-start['wire_m']))
            check('observed_preload_loss_and_pullout',released['clamp_normal_N']<1 and displacement>.002,
                released_normal_N=released['clamp_normal_N'],pull_displacement_m=displacement)
    else:raise ValueError('Unknown expected case '+expected)
    report=dict(passed=all(c['passed'] for c in checks),expected=expected,checks=checks,result_sha256=sha(directory/'result.json'),
        verifier_sha256=sha(Path(__file__)),engine_version=mujoco.__version__,whole_paper_validated=False,
        scope='Recomputed selected terminal jig mechanics and recorded external pull. This does not qualify robot execution or an electrical/thermocouple path.')
    (directory/'verification.json').write_text(json.dumps(report,indent=2)+'\n');return report


def suite():
    record=json.loads((HERE/'terminal_mechanism_tests.json').read_text());rows=[]
    for case in record['cases']:
        directory=(HERE/case['result']).parent;report=verify(directory,case['case'])
        rows.append(dict(case=case['case'],passed=report['passed'],verification=str((directory/'verification.json').relative_to(HERE)),verification_sha256=sha(directory/'verification.json')))
        print(case['case'],report['passed'],[c['name'] for c in report['checks'] if not c['passed']],flush=True)
    result=dict(passed=record['passed'] and all(r['passed'] for r in rows),cases=rows,executor_suite_sha256=sha(HERE/'terminal_mechanism_tests.json'),
        verifier_sha256=sha(Path(__file__)),whole_paper_validated=False,scope='Independent mechanism-jig checks, not a complete manipulation or electronics receipt.')
    (HERE/'TERMINAL_MECHANISM_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',nargs='?');p.add_argument('--expected',default='nominal');a=p.parse_args()
    report=verify(a.directory,a.expected) if a.directory else suite();print('MECHANISM VERIFICATION',report['passed']);raise SystemExit(0 if report['passed'] else 1)
