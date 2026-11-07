"""Independent motor replay and physical checks for a laboratory walking trial."""
import argparse
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation


def verify(folder):
    folder = Path(folder).resolve()
    model = mujoco.MjModel.from_xml_path(str(folder/'world.xml'))
    trace = np.load(folder/'trace.npz'); result = json.loads((folder/'result.json').read_text())
    imported = json.loads((folder/'laboratory_import.json').read_text())
    checks = []
    def check(name, value, **details): checks.append(dict(name=name,passed=bool(value),**details))
    check('executor_completed',result['completed'] and result['actor_exit_code']==0)
    check('floating_body_motor_torques_only',sum(model.jnt_type==mujoco.mjtJoint.mjJNT_FREE)==1
          and not np.any(model.eq_type==mujoco.mjtEq.mjEQ_WELD)
          and all(model.jnt_type[j]==mujoco.mjtJoint.mjJNT_HINGE for j in model.actuator_trnid[:,0]))
    check('motor_limits',np.all(trace['ctrl']>=model.actuator_ctrlrange[:,0]-1e-9)
          and np.all(trace['ctrl']<=model.actuator_ctrlrange[:,1]+1e-9))
    identities = [r['id'] for r in imported['imported_instances'] if r['id']!='architecture'] if imported['imported_instances'] and 'id' in imported['imported_instances'][0] else []
    if not identities: identities = [r['instance'] for r in imported['imported_instances'] if r['instance']!='architecture']
    identities += [r['instance'] for r in imported['dynamic_bindings']]
    check('all_81_source_assets_present',len(identities)==len(set(identities))==81)
    q = trace['qpos']
    rotations = Rotation.from_quat(q[:,[4,5,6,3]])
    up = rotations.apply([0.,0.,1.])[:,2]
    check('upright_throughout',q[:,2].min()>.65 and up.min()>.9,
          minimum_height_m=float(q[:,2].min()),maximum_tilt_deg=float(np.degrees(np.arccos(np.clip(up.min(),-1,1)))))
    initial_forward = rotations[0].apply([1.,0.,0.])[:2]
    delta = q[-1,:2]-q[0,:2]
    forward = float(delta@initial_forward)
    sideways = float(abs(delta@np.array([-initial_forward[1],initial_forward[0]])))
    check('forward_motion_exceeds_one_metre',forward>1.,forward_m=forward)
    check('stays_within_aisle_direction',sideways<.25,lateral_m=sideways)
    stopped = trace['time']>=12.
    stop_speed = float(np.max(np.linalg.norm(trace['qvel'][stopped,:2],axis=1))) if stopped.any() else float('inf')
    check('stops_after_command',stop_speed<.15,maximum_speed_after_12_s_m_s=stop_speed)
    data = mujoco.MjData(model); data.qpos[:]=q[0];data.qvel[:]=trace['qvel'][0]
    mujoco.mj_forward(model,data);data.qacc_warmstart[:]=trace['qacc_warmstart'][0]
    floors = {model.geom(r['geom']).id for r in imported['parts']
              if r['instance']=='architecture' and 'floor' in r['source_part']}
    robot = set()
    for i in range(1,model.nbody):
        root = i
        while model.body_parentid[root]>0: root=int(model.body_parentid[root])
        if model.body(root).name=='pelvis': robot.add(i)
    unexpected = set(); foot_heights=[]; qerr=0.;verr=0.
    for i in range(len(trace['time'])-1):
        data.ctrl[:]=trace['ctrl'][i]
        for _ in range(round(float(trace['time'][i+1]-trace['time'][i])/model.opt.timestep)):
            mujoco.mj_step(model,data)
        qerr=max(qerr,float(abs(data.qpos-q[i+1]).max()))
        verr=max(verr,float(abs(data.qvel-trace['qvel'][i+1]).max()))
        foot_heights.append([data.site(s+'_sole').xpos[2] for s in ['left','right']])
        for contact in data.contact:
            a,b=int(contact.geom1),int(contact.geom2)
            ra,rb=int(model.geom_bodyid[a]) in robot,int(model.geom_bodyid[b]) in robot
            if ra==rb: continue
            other,own=(b,a) if ra else (a,b)
            if other not in floors or model.body(model.geom_bodyid[own]).name not in {'left_ankle_roll_link','right_ankle_roll_link'}:
                unexpected.add((model.geom(own).name,model.geom(other).name))
    check('continuous_motor_replay_matches',qerr<1e-7 and verr<1e-6,max_qpos_error=qerr,max_qvel_error=verr)
    check('only_feet_contact_laboratory_floor',not unexpected,unexpected_pairs=sorted(unexpected))
    check('no_applied_body_support',not np.any(data.xfrc_applied) and not np.any(data.qfrc_applied))
    heights=np.asarray(foot_heights);steps=[]
    for j in range(2):
        elevated=(heights[:,j]>.015)&(trace['time'][1:]>2)&(trace['time'][1:]<10)
        begins=np.flatnonzero(elevated&~np.r_[False,elevated[:-1]])
        ends=np.flatnonzero(elevated&~np.r_[elevated[1:],False])
        steps.append(sum(trace['time'][b+1]-trace['time'][a+1]>.05 for a,b in zip(begins,ends)))
    check('both_feet_take_steps',all(n>=2 for n in steps),steps=[int(n) for n in steps],maximum_sole_height_m=heights.max(axis=0).tolist())
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,
                verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                trace_sha256=hashlib.sha256((folder/'trace.npz').read_bytes()).hexdigest(),
                scope='One unloaded, time-commanded compatibility run; no navigation, carrying or repeatability qualification')
    (folder/'walking_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder');args=parser.parse_args()
    if not verify(args.folder)['passed']: raise SystemExit(1)
