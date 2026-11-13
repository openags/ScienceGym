"""Compare stationary COM targets in the own-robot inverse-dynamics model.

Only declared initial pose and robot parameters enter the candidate solve.
Completed native reports provide a separate diagnosis of previous collisions.
This is an equilibrium calculation, not physical execution or qualification.
"""
import argparse
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from dex3_ftir_actor import Dex3FTIRActor
from run_dex3_ftir_press import sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    model_path = args.run/'controller_model/world.xml'
    setup_path = args.run/'policy_source/robot_setup.json'
    model = mujoco.MjModel.from_xml_path(str(model_path))
    setup = json.loads(setup_path.read_text())
    assert model.nu == 43 and model.neq == 0
    candidates = []
    for mode in ['sole_center', 'initial']:
        actor = Dex3FTIRActor(model, dict(setup, com_target_mode=mode))
        actor.balance.com_target = actor.com_goal.copy()
        torque = actor.balance.torque(posture=actor.original_posture,
                                     posture_weights=actor.posture_weights, dt=.01)
        solution = actor.balance.previous
        wrench = solution[model.nv:model.nv+12].reshape(2, 6)
        local = np.array([np.r_[rotation.T@value[:3], rotation.T@value[3:]]
                          for rotation, value in zip(actor.balance.foot_rotations, wrench)])
        feet = []
        for side, value in zip(['left', 'right'], local):
            force, moment = value[:3], value[3:]
            cop = np.array([-moment[1], moment[0]])/force[2]
            feet.append(dict(side=side, local_wrench=value.tolist(), cop_xy_m=cop.tolist(),
                within_original_bounds=bool(5. <= force[2] <= 800.
                    and np.max(abs(force[:2])) <= .6*force[2]
                    and abs(cop[0]) <= .07 and abs(cop[1]) <= .025
                    and abs(moment[2]) <= .012*force[2])))
        candidates.append(dict(mode=mode, requested_com_shift_m=(actor.com_goal-actor.com_start).tolist(),
            predicted_acceleration_norm=float(np.linalg.norm(solution[:model.nv])), feet=feet,
            maximum_motor_effort_fraction=float(np.max(abs(torque)/model.actuator_ctrlrange[:, 1])),
            solver=actor.balance.solver_diagnostics))
    prior_path = args.run/'physical_press_review.json'
    prior = json.loads(prior_path.read_text())
    report = dict(scope=__doc__, candidates=candidates,
        initial_com_equilibrium_supported=bool(candidates[1]['predicted_acceleration_norm'] < .001
            and all(f['within_original_bounds'] for f in candidates[1]['feet'])),
        earlier_torso_contacts=[c for c in prior['contacts']
            if any('torso_link_collision' in n for n in c['parts'])],
        source_model_sha256=sha(model_path), source_setup_sha256=sha(setup_path),
        prior_native_review_sha256=sha(prior_path), physical_execution=False,
        qualified_ftir_press=False, source_sha256={})
    for name in [Path(__file__).name, 'dex3_ftir_actor.py', 'balance.py', 'conic_balance.py']:
        source = Path(__file__).with_name(name)
        shutil.copyfile(source, args.output/name)
        report['source_sha256'][name] = sha(source)
    (args.output/'review.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)
    if not report['initial_com_equilibrium_supported']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
