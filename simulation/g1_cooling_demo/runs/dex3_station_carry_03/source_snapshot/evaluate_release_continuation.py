"""Compare native hand limits across an exact-prefix release diagnostic.

Only the retained continuation is assessed. Full contact, released support,
fresh continuous carrying and repeatability still require their own evidence.
"""
import argparse
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
import zipfile

import mujoco
import numpy as np

from evaluate_tool_actuation_recording import rows, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['diagnostic', 'candidate', 'source_recording', 'output']:
        p.add_argument(name, type=Path)
    a = p.parse_args()
    run, candidate, source, out = [getattr(a, name).resolve() for name in
                                   ['diagnostic', 'candidate', 'source_recording', 'output']]
    result = json.loads((run / 'result.json').read_text())
    contract = json.loads((candidate / 'contract.json').read_text())
    original = json.loads((source / 'result.json').read_text())
    assert result['actor_contract_sha256'] == sha(candidate / 'contract.json')
    assert result['source_result_sha256'] == sha(source / 'result.json')
    evidence = result['hand_native']
    assert evidence['sha256'] == sha(run / evidence['file'])
    assert original['trace_sha256'] == sha(source / 'trace.npz')
    assert contract['model_sha256'] == sha(candidate / 'world.xml') == sha(source / 'world.xml')
    with np.load(run / evidence['file']) as native:
        t, phases, names, q, v, commands = [native[key].copy() for key in
            ['time_s', 'phase', 'joint_names', 'position_rad', 'velocity_rad_s', 'command_nm']]
    assert len(t) == evidence['samples'] and len(t) > 1
    assert q.shape == v.shape == commands.shape == (len(t), len(names))
    assert np.isfinite(np.r_[t, q.ravel(), v.ravel(), commands.ravel()]).all()
    dt = evidence['sample_period_s']
    assert np.max(abs(np.diff(t) - dt)) < 1e-8
    source_urdf = Path(__file__).parent / 'analysis/g1_dex3_comparison_01/g1_29dof_with_hand_rev_1_0.urdf'
    urdf = ET.parse(source_urdf).getroot()
    m = mujoco.MjModel.from_xml_path(str(candidate / 'world.xml'))
    joints = np.array([m.joint(str(name)).id for name in names])
    actuators = np.array([np.flatnonzero(m.actuator_trnid[:, 0] == j).item() for j in joints])
    with zipfile.ZipFile(source / 'trace.npz') as archive:
        times = rows(archive, 'time')
        first = int(np.argmin(abs(times - t[0])))
        assert np.max(abs(times[first:first + len(t)] - t)) < 1e-8
        old_q = rows(archive, 'qpos', first, first + len(t))[:, m.jnt_qposadr[joints]]
        old_v = rows(archive, 'qvel', first, first + len(t))[:, m.jnt_dofadr[joints]]
        old_ctrl = rows(archive, 'ctrl', first, first + len(t))[:, actuators]
    events = json.loads((run / 'events.json').read_text())
    release = next(event['time_s'] for event in events if event.get('phase') == 'release')
    prior = t < release - 1e-8
    assert prior.any() and (phases == 'release').any()
    before_error = max(float(np.max(abs(actual[prior] - old[prior])))
                       for actual, old in [(q, old_q), (v, old_v), (commands, old_ctrl)])
    measurements = []
    for k, name in enumerate(names):
        limit = urdf.find(f"joint[@name='{name}']/limit")
        speed, effort = float(limit.get('velocity')), float(limit.get('effort'))
        peak = int(np.argmax(abs(v[:, k])))
        control = commands[:, k]
        motor = control * m.actuator_gear[actuators[k], 0]
        position_excess = max(float(np.max(float(limit.get('lower')) - q[:, k])),
                              float(np.max(q[:, k] - float(limit.get('upper')))), 0.)
        measurements.append(dict(joint=str(name), source_velocity_rad_s=speed, source_effort_nm=effort,
            maximum_speed_rad_s=float(abs(v[peak, k])), peak_time_s=float(t[peak]),
            peak_phase=str(phases[peak]), baseline_maximum_speed_rad_s=float(np.max(abs(old_v[:, k]))),
            maximum_commanded_torque_nm=float(np.max(abs(motor))),
            maximum_joint_limit_excess_rad=position_excess,
            velocity_passed=bool(np.max(abs(v[:, k])) <= speed + .001),
            torque_passed=bool(np.max(abs(motor)) <= effort + 1e-9 and
                np.all(control >= m.actuator_ctrlrange[actuators[k], 0] - 1e-9) and
                np.all(control <= m.actuator_ctrlrange[actuators[k], 1] + 1e-9)),
            position_passed=position_excess <= contract['physical_acceptance']['maximum_source_joint_limit_excess_rad']))
    checks = dict(prefix_sensor_responses_exact=result['maximum_prefix_response_error'] == 0.,
        restored_original_step_exact=max(result['restored_original_step_q_error'], result['restored_original_step_v_error']) <= 1e-10,
        native_hand_state_and_commands_unchanged_before_release=before_error <= 1e-10,
        continuation_without_runtime_error=result['failure'] is None,
        source_hand_velocity_limits=all(row['velocity_passed'] for row in measurements),
        source_hand_torque_limits=all(row['torque_passed'] for row in measurements),
        source_hand_position_limits=all(row['position_passed'] for row in measurements))
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, out / Path(__file__).name)
    helper = Path(__file__).with_name('evaluate_tool_actuation_recording.py')
    shutil.copyfile(helper, out / helper.name)
    report = dict(scope=__doc__, checks=checks, measurements=measurements,
        source_result_sha256=sha(source / 'result.json'), source_trace_sha256=original['trace_sha256'],
        diagnostic_result_sha256=sha(run / 'result.json'), candidate_contract_sha256=sha(candidate / 'contract.json'),
        source_urdf_sha256=sha(source_urdf), evaluator_sha256=sha(__file__), helper_sha256=sha(helper),
        native_sha256=evidence['sha256'], before_release_maximum_error=before_error,
        sample_period_s=dt, samples=len(t), window_start_s=float(t[0]), window_end_s=float(t[-1]),
        release_time_s=release, passed_release_limit_diagnostic=all(checks.values()),
        full_release_completed=result.get('last_phase') == 'finished',
        qualified_carry=False, qualified_paper_branch=False)
    (out / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed_release_limit_diagnostic'], measurements=measurements,
                         failed_checks=[key for key, value in checks.items() if not value])), flush=True)
    if not report['passed_release_limit_diagnostic']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
