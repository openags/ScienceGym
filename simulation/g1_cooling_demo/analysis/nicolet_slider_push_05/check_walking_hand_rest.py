"""Screen the walking hand posture and regress unchanged default interfaces."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
ROOT = BASE.parents[1]
sys.path.insert(0, str(BASE))
from ftir_hand import initialize, mimic, rest_hand_pose
from walking_actor import WalkingActor


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def main():
    output = HERE/'walking_hand_rest_review.json'
    if output.exists():
        raise FileExistsError(output)
    run = BASE/'runs/ftir_approach_01'
    plant = mujoco.MjModel.from_xml_path(str(run/'world.xml'))
    data = mujoco.MjData(plant)
    initial = np.array(json.loads((run/'staging.json').read_text())['initial_qpos'])
    robot = set()
    for body in range(plant.nbody):
        parent = body
        while parent and plant.body(parent).name != 'pelvis':
            parent = int(plant.body_parentid[parent])
        if parent:
            robot.add(body)

    def contacts():
        rows = []
        for contact in data.contact:
            a, b = map(int, contact.geom)
            bodies = [int(plant.geom_bodyid[g]) for g in [a, b]]
            if not any(body in robot for body in bodies) or contact.dist >= -1e-6:
                continue
            rows.append(dict(parts=[plant.geom(a).name, plant.geom(b).name],
                             distance_m=float(contact.dist), self_contact=all(body in robot for body in bodies)))
        return rows

    data.qpos[:] = initial
    mujoco.mj_forward(plant, data)
    original = contacts()
    for name, value in rest_hand_pose().items():
        data.joint(name).qpos[0] = value
    mimic(plant, data)
    mujoco.mj_forward(plant, data)
    folded = contacts()
    checks = dict(folded_hand_initial_contacts_within_unchanged_bound=not any(
        not r['self_contact'] or r['distance_m'] < -.00002 for r in folded))
    model = mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'))
    legacy_hand_path = run/'source_snapshot/ftir_hand.py'
    legacy_hand = module('legacy_initial_hand', legacy_hand_path)
    checks['default_station_initialization_identical'] = bool(np.array_equal(initialize(model).qpos, legacy_hand.initialize(model).qpos))
    legacy_walk_path = run/'source_snapshot/walking_actor.py'
    legacy_walk = module('legacy_walking_hand', legacy_walk_path)
    old = legacy_walk.WalkingActor(model, BASE/'locomotion_policy')
    current = WalkingActor(model, BASE/'locomotion_policy')
    source_sensors = BASE/'runs/laboratory_walking_07/sensor_observations.npz'
    sensors = np.load(source_sensors)
    packet = {k:sensors[k][0] for k in ['time_s', 'joint_position', 'joint_velocity', 'imu_quaternion', 'imu_gyro']}
    packet['depth'] = None
    a, _ = old.torque(packet)
    b, _ = current.torque(packet)
    checks['default_first_walking_torques_identical'] = bool(np.array_equal(a, b))
    selected = WalkingActor(model, BASE/'locomotion_policy', hand_pose=rest_hand_pose())
    checks['selected_hand_targets_are_declared_rest_pose'] = all(
        selected.hand_target[i] == rest_hand_pose()[model.joint(model.actuator_trnid[j,0]).name]
        for i,j in enumerate(selected.hand_motors))
    deps = [Path(__file__), BASE/'ftir_hand.py', BASE/'walking_actor.py', BASE/'ftir_approach_actor.py',
            legacy_hand_path, legacy_walk_path, run/'world.xml', run/'controller_model/world.xml',
            run/'staging.json', source_sensors, BASE/'locomotion_policy/policy.onnx', BASE/'locomotion_policy/deploy.yaml']
    report = dict(passed=all(checks.values()), checks=checks,
                  original_contacts=original, selected_rest_contacts=folded,
                  selected_pose=rest_hand_pose(), candidate_initial_qpos=data.qpos.tolist(),
                  maximum_default_torque_difference=float(np.max(abs(a-b))),
                  source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
                  scope='Static initial-pose clearance and default-interface regression. No executed walking with the new hand posture, manipulation or reliability credit.')
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'], checks=checks,
                         original_contacts=len(original), selected_contacts=len(folded))), flush=True)
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
