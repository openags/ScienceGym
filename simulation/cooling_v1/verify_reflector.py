"""Recheck contact-operated release/lock and solar geometry from saved states."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import mujoco
from device_assets import load
from trace_store import load_trace,sha


def limb_intersections(sample,height):
    a,e=np.deg2rad([sample['azimuth_deg'],sample['elevation_deg']])
    sun=np.array([np.cos(e)*np.sin(a),np.cos(e)*np.cos(a),np.sin(e)])
    u=np.array([np.cos(a),-np.sin(a),0]);v=np.cross(sun,u)
    angle=np.arange(180)*2*np.pi/180;alpha=np.deg2rad(.2666)
    rays=sun[None,:]*np.cos(alpha)+(np.cos(angle)[:,None]*u+np.sin(angle)[:,None]*v)*np.sin(alpha)
    return height*rays[:,:2]/rays[:,2,None]


def verify(directory,require_all=True):
    directory=Path(directory);result=json.loads((directory/'result.json').read_text());checks=[]
    def check(name,passed,**values):checks.append(dict(name=name,passed=bool(passed),**values))
    check('completed_execution',result['status']=='passed',failure=result.get('failure'))
    changed=[n for n,digest in result['input_sha256'].items() if sha(directory/n if n=='workcell.xml' else directory/'source_snapshot'/n)!=digest]
    check('archived_input_pins',not changed,changed=changed)
    solar_file=directory/'source_snapshot/selected_solar_path.json';solar=json.loads(solar_file.read_text())
    check('solar_input_pin',sha(solar_file)==result['configuration']['source_solar_path_sha256'])
    trace=load_trace(directory,result['artifacts_sha256']['physics_trace.npz']);times=trace['time']
    model=load(directory/'workcell.xml');model.opt.disableflags |= int(mujoco.mjtDisableBit.mjDSBL_WARMSTART);data=mujoco.MjData(model)
    check('finite_continuous_trace',all(np.isfinite(v).all() for v in trace.values()) and np.all(np.diff(times)>0) and np.max(np.diff(times))<.010001)
    check('only_robot_actuators',model.nu==8)
    check('no_payload_weld',not any(model.eq_type==mujoco.mjtEq.mjEQ_WELD))
    for name in ['carriage_x','carriage_y','retainer_travel','brake_lift']:
        joint=model.joint(name);q=trace['qpos'][:,joint.qposadr[0]];bounds=model.jnt_range[joint.id]
        violation=float(max(0,bounds[0]-q.min(),q.max()-bounds[1]))
        check('mechanical_stop_'+name,violation<.00005,maximum_penetration_m=violation,observed_range_m=[float(q.min()),float(q.max())])
    released=[e for e in result['observations'] if e['label']=='retainer_released'];locked=[e for e in result['observations'] if e['label']=='carriage_locked']
    expected=list(range(len(solar['samples']))) if require_all else result['selected_command_indices']
    check('all_scheduled_adjustments',[e['command_index'] for e in released]==expected and [e['command_index'] for e in locked]==expected,expected=len(expected),release_count=len(released),lock_count=len(locked))
    def observe(event):
        i=int(np.argmin(abs(times-event['time_s'])));data.qpos[:]=trace['qpos'][i];data.qvel[:]=trace['qvel'][i];data.ctrl[:]=trace['ctrl'][i];mujoco.mj_forward(model,data)
        brake=0.;fingers=0.
        for j,c in enumerate(data.contact):
            if min(c.geom)<0:continue
            names={model.body(int(model.geom_bodyid[g])).name for g in c.geom};force=np.zeros(6);mujoco.mj_contactForce(model,data,j,force)
            if names=={'track','brake_shoe'}:brake+=force[0]
            if names&{'carriage','retainer_button'} and names&{'left_finger','right_finger'}:fingers+=force[0]
        return dict(time_s=float(times[i]),brake_lift_m=float(data.joint('brake_lift').qpos[0]),brake_contact_N=float(brake),finger_contact_N=float(fingers))
    errors=[]
    origin=np.array(result['configuration']['emitter_origin_m'])
    for event in released:
        observation=observe(event)
        check('release_'+str(event['command_index']),observation['brake_lift_m']>.0015 and observation['brake_contact_N']<.05 and observation['finger_contact_N']>1,**observation)
    for event in locked:
        observation=observe(event);target=origin+np.array(solar['samples'][event['command_index']]['position_m'])-[0,0,.003]
        error=float(np.linalg.norm(data.body('carriage').xpos-target));errors.append(error)
        check('lock_'+str(event['command_index']),observation['brake_lift_m']<.0001 and observation['brake_contact_N']>1 and observation['finger_contact_N']<.01 and error<.001,position_error_m=error,**observation)
    if locked:
        # Sampled ray geometry uses actual recorded carriage coordinates.
        # The time between successive commands is an explicit process wait;
        # no four-hour mechanical stability evidence is inferred from it.
        positions=[]
        for q in trace['qpos']:
            data.qpos[:]=q;mujoco.mj_kinematics(model,data);positions.append(data.body('carriage').xpos.copy())
        positions=np.array(positions);command=np.minimum(np.searchsorted([e['time_s'] for e in locked],times),len(locked)-1)
        margin=np.inf
        for n,event in enumerate(locked):
            actual=positions[command==n];rays=limb_intersections(solar['samples'][event['command_index']],.15)+origin[:2]
            if len(actual):margin=min(margin,float(.03-.025-np.linalg.norm(actual[:,None,:2]-rays[None,:,:],axis=2).max()))
        check('sampled_shadow_during_each_adjustment',margin>0,minimum_margin_m=margin,limb_rays=180,
              interpretation='Actual recorded positions with the indexed command sun direction; long waits require retained-pose assumption')
        nominal=solar['geometry_checks']['tracked_zero_order_hold_min_margin_m']
        check('retained_pose_wait_shadow_bound',max(errors)<.001 and nominal>0,max_position_error_m=max(errors),minimum_bound_m=nominal,
              conditional_on='Carriage retains its observed locked pose during the external process wait')
    report=dict(passed=all(r['passed'] for r in checks),checks=checks,whole_paper_validated=False,
                scope='Recorded carriage release, slide and relock at scheduled solar positions; no installation or full branch credit',
                verifier_sha256=sha(Path(__file__)),result_sha256=sha(directory/'result.json'),engine_version=mujoco.__version__)
    (directory/'verification.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory');parser.add_argument('--subset',action='store_true');args=parser.parse_args()
    result=verify(args.directory,not args.subset);print(json.dumps(dict(passed=result['passed'],checks=len(result['checks']),failed=[r for r in result['checks'] if not r['passed']]),indent=2));raise SystemExit(0 if result['passed'] else 1)
