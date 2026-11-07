"""Screen a declared arm hold on retained gait poses before new execution."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import mujoco
import numpy as np

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
ROOT=BASE.parents[1]
sys.path.insert(0,str(BASE))
from ftir_hand import walking_shoulder_pose,rest_hand_pose,mimic
from walking_actor import WalkingActor,SDK_JOINTS


def main():
    out=HERE/'walking_shoulder_clearance.json'
    if out.exists():raise FileExistsError(out)
    run=BASE/'runs/ftir_approach_02'
    m=mujoco.MjModel.from_xml_path(str(run/'world.xml'));d=mujoco.MjData(m)
    trace=dict(np.load(run/'trace.npz'))
    robot=set()
    for b in range(m.nbody):
        parent=b
        while parent and m.body(parent).name!='pelvis':parent=int(m.body_parentid[parent])
        if parent:robot.add(b)
    def unexpected():
        rows=[]
        for c in d.contact:
            a,b=map(int,c.geom);ba,bb=int(m.geom_bodyid[a]),int(m.geom_bodyid[b])
            if ba not in robot and bb not in robot:continue
            if c.dist>=-.00002:continue
            names=[m.geom(a).name,m.geom(b).name]
            if any('_sole_contact_' in str(n) for n in names):continue
            # Authored floor collision pieces carry the original ankle mesh.
            own=ba if ba in robot else bb
            other=b if ba in robot else a
            if m.body(own).name in {'left_ankle_roll_link','right_ankle_roll_link'} and other in floor:continue
            rows.append(dict(parts=names,distance_m=float(c.dist)))
        return rows
    imported=json.loads((run/'laboratory_import.json').read_text())
    floor={m.geom(p['geom']).id for p in imported['parts'] if p['source_part'] in
           {'indoor_floor','annex_floor','outdoor_floor','outdoor_access_path'}}
    original=[];proposed=[];sampled=0
    for i in range(0,len(trace['time']),25):
        if trace['time'][i]>6.:break
        sampled+=1;d.qpos[:]=trace['qpos'][i];mujoco.mj_forward(m,d)
        for row in unexpected():original.append(dict(time_s=float(trace['time'][i]),**row))
        for name,value in rest_hand_pose().items():d.joint(name).qpos[0]=value
        for side,sign in [('left',1.),('right',-1.)]:
            joint=d.joint(side+'_shoulder_roll_joint')
            joint.qpos[0]=sign*max(.4,sign*joint.qpos[0])
        mimic(m,d);mujoco.mj_forward(m,d)
        for row in unexpected():proposed.append(dict(time_s=float(trace['time'][i]),**row))
    model=mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'))
    old_path=run/'source_snapshot/walking_actor.py'
    spec=importlib.util.spec_from_file_location('retained_walking_arm',old_path)
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    before=old.WalkingActor(model,BASE/'locomotion_policy')
    after=WalkingActor(model,BASE/'locomotion_policy')
    sensors=dict(np.load(run/'sensor_observations.npz'));maximum=0.
    for i,t in enumerate(sensors['time_s']):
        if t>1.:break
        packet={k:sensors[k][i] for k in ['time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro']}
        packet['depth']=None
        a,_=before.torque(packet);b,_=after.torque(packet)
        maximum=max(maximum,float(np.max(abs(a-b))))
    selected=WalkingActor(model,BASE/'locomotion_policy',hand_pose=rest_hand_pose(),minimum_shoulder_abduction=.4)
    packet={k:sensors[k][0] for k in ['time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro']};packet['depth']=None
    torque,_=selected.torque(packet)
    sdk=np.empty(29);sdk[selected.order]=selected.target
    rejected=[]
    for minimum in [-1.,100.]:
        try:WalkingActor(model,BASE/'locomotion_policy',minimum_shoulder_abduction=minimum)
        except ValueError:rejected.append(True)
        else:rejected.append(False)
    checks=dict(original_hip_hand_issue_reproduced=any(any('hip_' in n for n in r['parts']) and any('thumb_' in n for n in r['parts']) for r in original),
                proposed_sampled_pose_has_no_unintended_contact=not proposed,
                unchanged_default_velocity_policy=maximum==0.,
                sdk_shoulder_targets_respect_clearance=all(sign*sdk[SDK_JOINTS.index(side+'_shoulder_roll_joint')]>=.4-1e-8 for side,sign in [('left',1.),('right',-1.)]),
                selected_torques_finite_and_bounded=bool(np.isfinite(torque).all() and np.all(torque>=model.actuator_ctrlrange[:,0]) and np.all(torque<=model.actuator_ctrlrange[:,1])),
                invalid_clearance_angles_rejected=all(rejected))
    deps=[Path(__file__),BASE/'ftir_hand.py',BASE/'walking_actor.py',BASE/'ftir_approach_actor.py',BASE/'run_ftir_press.py',old_path,run/'trace.npz',run/'world.xml',run/'controller_model/world.xml',run/'sensor_observations.npz']
    result=dict(passed=all(checks.values()),checks=checks,sampled_body_poses=sampled,original_contacts=original,proposed_contacts=proposed,
                proposed_shoulder_boundary=walking_shoulder_pose(),maximum_default_torque_difference=maximum,
                source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
                scope='Counterfactual kinematic screen on retained gait poses and default-interface regression. This does not execute or qualify the changed walking controller; dynamics, all-state collisions and support still require a new trial.')
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['passed','checks','sampled_body_poses','maximum_default_torque_difference']}),flush=True)
    if not result['passed']:raise SystemExit(1)


if __name__=='__main__':main()
