"""Compare guarded policy history against the retained source-policy adapter."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import mujoco
import numpy as np

HERE=Path(__file__).resolve().parent;BASE=HERE.parents[1];ROOT=BASE.parents[1]
sys.path.insert(0,str(BASE))
from walking_actor import WalkingActor,SDK_JOINTS
from ftir_hand import walking_arm_pose


def main():
    output=HERE/'raised_arm_policy_history.json'
    if output.exists():raise FileExistsError(output)
    run=BASE/'runs/ftir_approach_02'
    model=mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'))
    old_path=run/'source_snapshot/walking_actor.py'
    spec=importlib.util.spec_from_file_location('source_walking_history',old_path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    old=module.WalkingActor(model,BASE/'locomotion_policy')
    guarded=WalkingActor(model,BASE/'locomotion_policy',arm_pose=walking_arm_pose())
    sensors=dict(np.load(run/'sensor_observations.npz'))
    other=[i for i in range(29) if i not in guarded.arm_targets]
    max_action=max_other=max_arm=0.;packets=0
    for i,t in enumerate(sensors['time_s']):
        if t>6.:break
        packet={k:sensors[k][i] for k in ['time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro']};packet['depth']=None
        old.torque(packet);guarded.torque(packet);packets+=1
        max_action=max(max_action,float(np.max(abs(old.action-guarded.action))))
        max_other=max(max_other,float(np.max(abs(old.target[other]-guarded.target[other]))))
        max_arm=max(max_arm,max(abs(guarded.target[i]-v) for i,v in guarded.arm_targets.items()))
    checks=dict(raw_policy_history_and_network_predictions_unchanged=max_action==0.,
                all_other_processed_joint_targets_unchanged=max_other==0.,
                raised_arm_targets_match_declared_pose=max_arm<1e-8)
    paths=[Path(__file__),BASE/'walking_actor.py',old_path,run/'sensor_observations.npz',BASE/'locomotion_policy/reference/action_manager.h',BASE/'locomotion_policy/reference/observations.h',BASE/'ftir_hand.py']
    result=dict(passed=all(checks.values()),checks=checks,packets=packets,maximum_action_difference=max_action,
                maximum_other_target_difference=max_other,maximum_arm_target_error=max_arm,selected_arm_pose=walking_arm_pose(),
                source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                scope='Adapter regression with identical retained sensor inputs. New physical execution is still required because the raised-arm targets change upper-body motion and subsequent sensor feedback.')
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    if not result['passed']:raise SystemExit(1)


if __name__=='__main__':main()
