"""Evaluate recorded plant states and independently replay motor commands.

This verifier never sends results to the actor. Passing these checks concerns
one tray development episode, not the paper's skill/campaign qualification.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import mujoco


def verify(folder):
    folder=Path(folder).resolve();m=mujoco.MjModel.from_xml_path(str(folder/'world.xml'));d=mujoco.MjData(m)
    tr=np.load(folder/'trace.npz');result=json.loads((folder/'result.json').read_text());checks=[]
    def check(name,value,**details):checks.append(dict(name=name,passed=bool(value),**details))
    check('recorded_executor_finished',result['status']=='completed')
    check('floating_root_without_weld',m.jnt_type[0]==mujoco.mjtJoint.mjJNT_FREE and not np.any(m.eq_type==mujoco.mjtEq.mjEQ_WELD))
    check('motors_drive_hinges_only',all(m.jnt_type[j]==mujoco.mjtJoint.mjJNT_HINGE for j in m.actuator_trnid[:,0]))
    check('source_snapshots_match',all(hashlib.sha256((folder/'source_snapshot'/name).read_bytes()).hexdigest()==sha for name,sha in result['source_sha256'].items()))
    check('torque_limits',np.all(tr['ctrl']>=m.actuator_ctrlrange[:,0]-1e-9) and np.all(tr['ctrl']<=m.actuator_ctrlrange[:,1]+1e-9))
    check('standing_throughout',np.min(tr['qpos'][:,2])>.6 and np.max(np.linalg.norm(tr['qpos'][:,4:6],axis=1))<.2)
    qa=m.joint('tray_free').qposadr[0];pos=tr['qpos'][:,qa:qa+3];initial=pos[0];maximum=float(pos[:,2].max()-initial[2])
    check('tray_lift_at_least_7cm',maximum>=.07,actual_m=maximum,threshold_m=.07)
    check('tray_horizontal_transfer_at_least_4cm',np.linalg.norm(pos[-1,:2]-initial[:2])>=.04,actual_m=float(np.linalg.norm(pos[-1,:2]-initial[:2])))
    last=tr['time']>=tr['time'][-1]-1
    check('tray_stable_after_release',np.max(np.linalg.norm(tr['qvel'][last,m.joint('tray_free').dofadr[0]:][:,:6],axis=1))<.01)
    check('placed_on_table_height',abs(pos[-1,2]-.9)<.005,final_m=pos[-1].tolist())
    d.qpos[:]=tr['qpos'][-1];d.qvel[:]=tr['qvel'][-1];mujoco.mj_forward(m,d)
    traybody=m.body('carrier_tray').id;table=m.geom('bench_top').id;hand_contact=False;table_contact=False
    for c in d.contact:
        a,b=int(c.geom1),int(c.geom2)
        if m.geom_bodyid[a]!=traybody and m.geom_bodyid[b]!=traybody:continue
        other=b if m.geom_bodyid[a]==traybody else a
        table_contact|=other==table
        hand_contact|=m.geom_bodyid[other]!=0
    check('released_from_hands_on_table',table_contact and not hand_contact)
    # Start once, apply held torque commands, and integrate all 19,000 steps.
    # No resets, target pose assignments, or recorded-state corrections occur.
    d=mujoco.MjData(m);d.qpos[:]=tr['qpos'][0];d.qvel[:]=tr['qvel'][0]
    if 'qacc_warmstart' in tr:d.qacc_warmstart[:]=tr['qacc_warmstart'][0]
    mujoco.mj_forward(m,d);maxerr=0.;maxvel=0.
    for i in range(len(tr['time'])-1):
        d.ctrl[:]=tr['ctrl'][i]
        steps=round(float(tr['time'][i+1]-tr['time'][i])/m.opt.timestep)
        for _ in range(steps):mujoco.mj_step(m,d)
        maxerr=max(maxerr,float(np.max(abs(d.qpos-tr['qpos'][i+1]))))
        maxvel=max(maxvel,float(np.max(abs(d.qvel-tr['qvel'][i+1]))))
    check('continuous_motor_replay_matches',maxerr<1e-7 and maxvel<1e-6,max_qpos_error=maxerr,max_qvel_error=maxvel)
    check('no_external_applied_forces',not np.any(d.xfrc_applied) and not np.any(d.qfrc_applied))
    check('separate_sensor_actor',result['actor_process_separate'] and set(result['actor_input_fields'])=={'time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro','depth'})
    payload=dict(passed=all(x['passed'] for x in checks),checks=checks,scope='Single empty-tray contact development episode only.',qualified_paper_branches=0,whole_paper_validated=False,
        limitations=['Idealized camera and IMU; fixed-foot state estimate.','Initial depth localization followed by timed motor targets; no grasp-success feedback policy.','No hardened process sandbox or sensor-calibration qualification.','No filled-tray, walking, assembly, cable, thin-film, recovery or campaign qualification.'],
        metrics=dict(duration_s=float(tr['time'][-1]),lift_m=maximum,transfer_m=float(np.linalg.norm(pos[-1,:2]-initial[:2]))),
        files={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in ['world.xml','trace.npz','result.json']})
    (folder/'verification.json').write_text(json.dumps(payload,indent=2)+'\n')
    plot=dict(time=tr['time'][::10].tolist(),tray_height_cm=((pos[::10,2]-initial[2])*100).tolist(),tray_y_cm=((pos[::10,1]-initial[1])*100).tolist())
    (folder/'plot.json').write_text(json.dumps(plot)+'\n')
    print(json.dumps(payload,indent=2));return payload


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');a=p.parse_args();verify(a.folder)
