"""Compare sensor-only leg odometry with a retained native walking trajectory.

Plant position is used only here for independent error measurement. The estimator
receives own sensors and the explicitly declared initial map position.
"""
import argparse
import json
from pathlib import Path

import mujoco
import numpy as np

from odometry import LegOdometry
from run_dex3_walking import sha


def evaluate(run, output):
    run, output = Path(run), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    result = json.loads((run / 'result.json').read_text())
    contract = json.loads((run / 'contract.json').read_text())
    for name, field in [('trace.npz', 'trace_sha256'), ('sensors.npz', 'sensors_sha256')]:
        assert sha(run / name) == result[field]
    sensors = dict(np.load(run / 'sensors.npz'))
    trace = dict(np.load(run / 'trace.npz'))
    model = mujoco.MjModel.from_xml_path(str(run / 'controller_model/world.xml'))
    data = mujoco.MjData(model)
    estimator = LegOdometry(model, data, contract['initial_qpos'][:2])
    estimates = []
    for i in range(len(sensors['time_s'])):
        packet = {key: value[i] for key, value in sensors.items()}
        estimates.append(estimator.update(dict(packet, depth=None)))
    estimates = np.asarray(estimates)
    indices = np.rint(sensors['time_s'] / contract['physics_period_s']).astype(int)
    assert np.max(abs(trace['time'][indices] - sensors['time_s'])) < 1e-8
    truth = trace['qpos'][indices, :3]
    errors = estimates - truth
    np.savez_compressed(output / 'positions.npz', time_s=sensors['time_s'],
                        estimated_position_m=estimates, evaluator_position_m=truth)
    report = dict(scope=__doc__, source_run=str(run), trace_sha256=result['trace_sha256'],
        sensors_sha256=result['sensors_sha256'], estimator_sha256=sha(Path(__file__).with_name('odometry.py')),
        evaluator_sha256=sha(__file__), samples=len(estimates), declared_initial_xy=contract['initial_qpos'][:2],
        maximum_xy_error_m=float(np.linalg.norm(errors[:, :2], axis=1).max()),
        final_xy_error_m=float(np.linalg.norm(errors[-1, :2])),
        final_xy_error_vector_m=errors[-1, :2].tolist(),
        maximum_height_error_m=float(abs(errors[:, 2]).max()),
        estimated_forward_m=float(estimates[0, 1] - estimates[-1, 1]),
        actual_forward_m=float(truth[0, 1] - truth[-1, 1]),
        stance_switches=estimator.switches, position_record_sha256=sha(output / 'positions.npz'),
        qualified_navigation=False, qualified_station_arrival=False, qualified_paper_branch=False)
    (output / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'stance_switches'}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('run')
    p.add_argument('output')
    a = p.parse_args()
    evaluate(a.run, a.output)
