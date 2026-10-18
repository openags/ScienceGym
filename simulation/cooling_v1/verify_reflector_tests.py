"""Verify cause-specific faults and measured brake displacement independently."""
import json
from pathlib import Path
import mujoco
import numpy as np
from device_assets import load
from trace_store import load_trace,sha
from world import HERE


def verify():
    checks=[];pins={}
    def check(name,passed,**values):checks.append(dict(name=name,passed=bool(passed),**values))
    nominal=json.loads((HERE/'runs/reflector/result.json').read_text())
    verification=json.loads((HERE/'runs/reflector/verification.json').read_text())
    check('nominal_independent_verification',verification['passed'] and verification['result_sha256']==sha(HERE/'runs/reflector/result.json'))
    for case in ['blocked_release','missing_spring','brake_load']:
        directory=HERE/'runs/reflector_tests'/case;record=json.loads((directory/'result.json').read_text());pins[case]=sha(directory/'result.json')
        changed=[name for name,digest in record['input_sha256'].items() if sha(directory/name if name=='workcell.xml' else directory/'source_snapshot'/name)!=digest]
        check(case+'_archived_inputs',not changed,changed=changed)
        check(case+'_same_nominal_sources',all(record['input_sha256'][n]==nominal['input_sha256'][n] for n in ['reflector_world.py','run_reflector.py','hardware_control.py']))
        for name,digest in record['artifacts_sha256'].items():
            if name!='physics_trace.npz':check(case+'_artifact_'+name,sha(directory/name)==digest)
        trace=load_trace(directory,record['artifacts_sha256']['physics_trace.npz']);times=trace['time']
        check(case+'_continuous_trace',all(np.isfinite(v).all() for v in trace.values()) and np.all(np.diff(times)>0) and np.max(np.diff(times))<.010001)
        model=load(directory/'workcell.xml');model.opt.disableflags |= int(mujoco.mjtDisableBit.mjDSBL_WARMSTART);data=mujoco.MjData(model)
        if case=='blocked_release':
            travel=trace['qpos'][:,model.joint('retainer_travel').qposadr[0]];lift=trace['qpos'][:,model.joint('brake_lift').qposadr[0]]
            check('blocked_release_rejected_before_slide',record['status']=='failed' and record['configuration']['release_blocked'] and
                  'Retainer did not physically release' in record['failure'] and not any(e['label']=='carriage_locked' for e in record['observations']) and
                  np.max(travel)<.00015 and np.max(lift)<.00015,maximum_release_travel_m=float(travel.max()),maximum_brake_lift_m=float(lift.max()))
        elif case=='missing_spring':
            data.qpos[:]=trace['qpos'][-1];data.qvel[:]=trace['qvel'][-1];data.ctrl[:]=trace['ctrl'][-1];mujoco.mj_forward(model,data)
            normal=0.
            for i,c in enumerate(data.contact):
                if min(c.geom)<0:continue
                if {model.body(int(model.geom_bodyid[g])).name for g in c.geom}=={'track','brake_shoe'}:
                    force=np.zeros(6);mujoco.mj_contactForce(model,data,i,force);normal+=force[0]
            check('missing_spring_rejected_before_grasp',record['status']=='failed' and not record['configuration']['brake_enabled'] and
                  'Initial spring brake lacks preload' in record['failure'] and len(record['observations'])==1 and normal<1,observed_preload_N=float(normal))
        else:
            def position(at):
                index=int(np.argmin(abs(times-at)));data.qpos[:]=trace['qpos'][index];mujoco.mj_kinematics(model,data)
                return data.body('carriage').xpos.copy()
            start=position(.6);loaded=position(1.6);settled=position(61.6);overloaded=position(61.8)
            displacement=[float(np.linalg.norm(loaded-start)),float(np.linalg.norm(settled-start)),float(np.linalg.norm(overloaded-settled))]
            check('1_N_shear_retained',displacement[0]<.00025,displacement_m=displacement[0])
            check('60_s_wait_retained',displacement[1]<.00025,displacement_m=displacement[1])
            check('5_N_overload_slips',displacement[2]>.001,displacement_m=displacement[2])
            check('load_report_matches_trace',all(abs(a-b['displacement_m'])<1e-6 for a,b in zip(displacement,record['observations'])))
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,input_result_sha256=pins,
                verifier_sha256=sha(Path(__file__)),whole_paper_validated=False,
                scope='Nominal adjustment plus blocked release, absent preload, retention and overload controls. External force tests are not robot actuation.')
    (HERE/'REFLECTOR_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    report=verify();print(json.dumps(dict(passed=report['passed'],checks=len(report['checks']),failed=[c for c in report['checks'] if not c['passed']]),indent=2))
    raise SystemExit(0 if report['passed'] else 1)
