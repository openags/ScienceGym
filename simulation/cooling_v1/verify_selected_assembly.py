"""Independently inspect the seven-layer trace and exact paper-step receipts."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import mujoco
from load_model import load
from support_observation import support_load,designated_surfaces
from evaluate_cover import measure
from trace_store import load_trace,sha
from audit_film_trace import audit


def verify(directory):
    directory=Path(directory);result=json.loads((directory/'result.json').read_text())
    checks=[]
    def check(name,passed,**values):checks.append(dict(name=name,passed=bool(passed),**values))
    check('completed_episode',result['status']=='passed',failure=result.get('failure'))
    changed=[]
    for name,digest in result['input_sha256'].items():
        source=directory/(name if name=='workcell.xml' else result['source_archive'][name])
        if sha(source)!=digest:changed.append(name)
    check('archived_inputs_match',not changed,changed=changed)
    for name,digest in result['artifacts_sha256'].items():
        if name!='physics_trace.npz':check('artifact_'+name,sha(directory/name)==digest)
    trace=load_trace(directory,result['artifacts_sha256']['physics_trace.npz']);time=trace['time']
    check('finite_trace',all(np.isfinite(value).all() for value in trace.values()))
    check('continuous_clock',len(time)>1 and np.all(np.diff(time)>0) and np.max(np.diff(time))<.005001,
          samples=len(time),maximum_interval_s=float(np.max(np.diff(time))))
    check('episode_reaches_reported_end',abs(time[-1]-result['simulated_seconds'])<.005001)
    model=load(directory/'workcell.xml')
    numerics=result.get('numerics') or {}
    check('no_numerical_warning_or_solver_exhaustion',bool(numerics)
          and not any(numerics.get('warnings',[1])) and numerics.get('solver_limit_steps',1)==0
          and numerics.get('maximum_solver_iterations',model.opt.iterations)<model.opt.iterations,
          observed=numerics,solver_iteration_limit=model.opt.iterations)
    # Observations jump between saved checkpoints; no previous checkpoint's
    # constraint solution is a valid warm start for the next one.
    model.opt.disableflags |= int(mujoco.mjtDisableBit.mjDSBL_WARMSTART)
    data=mujoco.MjData(model)
    check('actuators_only_on_robot',model.nu==8 and all(model.jnt_bodyid[j]<model.body('foam_lower').id for j in model.actuator_trnid[:7,0]))
    check('no_attachment_weld',not any(t==mujoco.mjtEq.mjEQ_WELD for t in model.eq_type))
    check('both_deformable_sheets',model.nflex==2)
    check('gripper_force_limit',np.max(abs(trace['ctrl'][:,7]))<=40.000001)
    receipts=json.loads((directory/'step_receipts.json').read_text())
    expected=['BASE.03','EMITTER.02','EMITTER.03','SHIELD.02','SHIELD.03','SHIELD.04']
    check('all_six_bindings_executed',[r['step_id'] for r in receipts]==expected)
    previous=None;previous_end=-1;instances=set()
    for receipt in receipts:
        row={k:v for k,v in receipt.items() if k!='receipt_sha256'}
        digest=hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        check('receipt_'+receipt['step_id'],digest==receipt['receipt_sha256'] and receipt['previous_receipt_sha256']==previous
              and receipt['time_start_s']>=previous_end and receipt['time_end_s']>receipt['time_start_s']
              and receipt['physics_step_end']>receipt['physics_step_start'] and not receipt['campaign_qualified'])
        previous=digest;previous_end=receipt['time_end_s'];instances.add(receipt['scene_instance_id'])
        for edge in ['before','after']:
            at=receipt['time_start_s' if edge=='before' else 'time_end_s'];index=int(np.argmin(abs(time-at)))
            digest=hashlib.sha256()
            for v in [trace['qpos'][index],trace['qvel'][index],trace['ctrl'][index],np.array([time[index]])]:digest.update(np.asarray(v,dtype='<f8').tobytes())
            check(receipt['step_id']+'_'+edge+'_state',abs(time[index]-at)<1e-9 and digest.hexdigest()==receipt[edge+'_state_sha256'])
        for item in receipt['objects']:
            check(receipt['step_id']+'_object_'+item['role'],model.body(item['role']).id==item['body_id']
                  and item['instance_id']==receipt['scene_instance_id']+'::'+item['role'])
    check('single_persistent_scene',len(instances)==1)
    def state(at):
        i=int(np.argmin(abs(time-at)));data.qpos[:]=trace['qpos'][i];data.qvel[:]=trace['qvel'][i];data.ctrl[:]=trace['ctrl'][i]
        mujoco.mj_forward(model,data);return float(time[i])
    # Observe every recorded release/retention check, not only the final image.
    for event in result['observations']:
        if event['label'] not in ['support_observed','cover_support_observed']:continue
        at=state(event['time_s'])
        if event['label']=='cover_support_observed':
            support=event['support'];target=result['targets']['cover']['assembled' if support=='pe_tube' else 'park']
            observation=measure(model,data,np.array(target),support)
            check('cover_support',observation['passed'],time_s=at,support=support,observation=observation)
        else:
            name=event['body'];target=np.array(event['target']);support=event['support']
            body=data.body(name);error=float(np.linalg.norm(body.xpos-target));tilt=float(np.arccos(np.clip(body.xmat[8],-1,1)));speed=float(np.linalg.norm(body.cvel))
            load_observation=support_load(model,data,name,support,designated_surfaces(name,support))
            three_shims=name!='shield' or support!='assembly_base' or len(load_observation['loaded_support_geoms'])>=3
            check('rigid_support_'+name,error<.003 and tilt<.035 and speed<.03 and three_shims
                  and load_observation['vertical_force_n']>.8*load_observation['body_weight_n'],
                  time_s=at,support=support,error_m=error,tilt_rad=tilt,speed=speed,load=load_observation)
    # Sampled motion is checked for each physical body, and membrane lengths
    # for every saved state. This explicitly does not prove unsampled extrema.
    for name in result['targets']:
        address=int(model.joint(name+'_free').qposadr[0]);xyz=trace['qpos'][:,address:address+3]
        speed=np.linalg.norm(np.diff(xyz,axis=0),axis=1)/np.diff(time)
        check('sampled_continuity_'+name,np.max(speed)<1.,maximum_speed_m_s=float(np.max(speed)))
    maximum=0.;worst_time=0.
    for i in range(len(time)):
        data.qpos[:]=trace['qpos'][i];mujoco.mj_kinematics(model,data);mujoco.mj_comPos(model,data);mujoco.mj_flex(model,data)
        strain=float(np.max(abs(data.flexedge_length/model.flexedge_length0-1)))
        if strain>maximum:maximum=strain;worst_time=float(time[i])
    check('membrane_strain_throughout',maximum<.01,maximum_edge_strain=maximum,worst_time_s=worst_time)
    geometry=audit(directory)
    check('film_does_not_cross_tube_solids',geometry['passed'],failed_samples=geometry['failed_samples'],
          report_sha256=sha(directory/'film_geometry_verification.json'),tolerance_m=geometry['tolerance_m'])
    lifts=[e for e in result['observations'] if e['label']=='edge_lift_observed']
    cover_lifts=[e for e in result['observations'] if e['label']=='cover_lifted']
    check('rigid_transfer_count',len(lifts)==13,observed=len(lifts))
    check('cover_transfer_count',len(cover_lifts)==2,observed=len(cover_lifts))
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,whole_paper_validated=False,
                scope='Continuous seven-layer assembly and return; six locally bound paper steps. Frame fabrication, film bonding, leads, paired apparatus and other branches remain outside this record.',
                verifier_sha256=sha(Path(__file__)),result_sha256=sha(directory/'result.json'),engine_version=mujoco.__version__)
    (directory/'verification.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory');args=parser.parse_args();report=verify(args.directory)
    print(json.dumps(dict(passed=report['passed'],checks=len(report['checks']),failed=[r for r in report['checks'] if not r['passed']]),indent=2))
    raise SystemExit(0 if report['passed'] else 1)
