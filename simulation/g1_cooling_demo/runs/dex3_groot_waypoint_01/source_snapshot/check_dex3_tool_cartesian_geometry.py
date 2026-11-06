"""Check coordinated finger Jacobians against independent finite differences."""
import argparse
import json
from pathlib import Path

import mujoco
import numpy as np

from dex3_tool_actor import ToolActor
from run_dex3_walking import sha


def check(candidate, checkpoint, output):
    candidate, checkpoint, output = map(Path, (candidate, checkpoint, output))
    output.mkdir(parents=True, exist_ok=False)
    prior = json.loads((candidate / 'policy_source/tool_prior.json').read_text())
    model = mujoco.MjModel.from_xml_path(str(candidate / 'controller_model/world.xml'))
    plant = mujoco.MjModel.from_xml_path(str(candidate / 'world.xml'))
    actor = ToolActor(model, prior)
    trace = dict(np.load(checkpoint / 'trace.npz'))
    epsilon = 1e-6
    rows = []
    for t in [55.992, 63., 66.789]:
        index = int(np.argmin(abs(trace['time'] - t)))
        actor.d.qpos[:7] = trace['qpos'][index, :7]
        for joint in model.actuator_trnid[:, 0]:
            source_joint = plant.joint(model.joint(int(joint)).name).id
            actor.d.qpos[model.jnt_qposadr[joint]] = trace['qpos'][index, plant.jnt_qposadr[source_joint]]
        mujoco.mj_forward(model, actor.d)
        _, matrices, _ = actor.coordinated_finger_state(actor.points())
        for i, pair in enumerate(actor.finger_pairs):
            numerical = np.zeros((2, 2))
            for column, motor in enumerate(pair):
                address = actor.qa[motor]
                before = actor.d.qpos[address]
                endpoints = []
                for sign in [-1., 1.]:
                    actor.d.qpos[address] = before + sign * epsilon
                    mujoco.mj_forward(model, actor.d)
                    wrist = actor.d.site('right_wrist_reference')
                    point = actor.tool_axes_from_wrist @ wrist.xmat.reshape(3, 3).T @ (actor.points()[i] - wrist.xpos)
                    endpoints.append(np.array([(1. if i == 0 else -1.) * point[1], point[2]]))
                numerical[:, column] = (endpoints[1] - endpoints[0]) / (2 * epsilon)
                actor.d.qpos[address] = before
                mujoco.mj_forward(model, actor.d)
            rows.append(dict(time_s=float(trace['time'][index]), finger=['thumb', 'index', 'middle'][i],
                analytic=matrices[i].tolist(), finite_difference=numerical.tolist(),
                maximum_error_m_per_rad=float(np.max(abs(matrices[i] - numerical))),
                condition_number=float(np.linalg.cond(matrices[i]))))
    passed = all(row['maximum_error_m_per_rad'] < 1e-8 and row['condition_number'] < 100. for row in rows)
    report = dict(scope=__doc__, passed=passed, samples=rows, epsilon_rad=epsilon,
        actor_sha256=sha(Path(__file__).with_name('dex3_tool_actor.py')), checker_sha256=sha(__file__),
        prior_sha256=sha(candidate / 'policy_source/tool_prior.json'),
        controller_model_sha256=sha(candidate / 'controller_model/world.xml'),
        source_trace_sha256=sha(checkpoint / 'trace.npz'),
        qualified_force_observer=False, qualified_tool_actuation=False, qualified_paper_branch=False)
    (output / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=passed, compared_matrices=len(rows),
        maximum_error_m_per_rad=max(r['maximum_error_m_per_rad'] for r in rows),
        maximum_condition_number=max(r['condition_number'] for r in rows))), flush=True)
    if not passed:
        raise SystemExit(1)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('candidate')
    p.add_argument('checkpoint')
    p.add_argument('output')
    a = p.parse_args()
    check(a.candidate, a.checkpoint, a.output)
