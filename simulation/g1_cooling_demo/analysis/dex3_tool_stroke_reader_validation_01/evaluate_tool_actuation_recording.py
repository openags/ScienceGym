"""Measure a fresh recording's tool stroke through exact native-window replay.

The actor receives none of these measurements. This supplements, rather than
replaces, the full-run contact, isolated-controller and source-limit reviews.
A passing stroke is neither specimen handling nor repeated skill qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time
import zipfile

import mujoco
import numpy as np


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def rows(archive, name, first=None, stop=None):
    """Read only needed rows from a compressed, C-ordered numeric NPZ member."""
    with archive.open(name + '.npy') as stream:
        version = np.lib.format.read_magic(stream)
        reader = {(1, 0): np.lib.format.read_array_header_1_0,
                  (2, 0): np.lib.format.read_array_header_2_0}[version]
        shape, fortran, dtype = reader(stream)
        assert shape and not fortran and not dtype.hasobject
        start, end = 0 if first is None else first, shape[0] if stop is None else stop
        assert 0 <= start <= end <= shape[0]
        row_bytes = int(np.prod(shape[1:], dtype=np.int64)) * dtype.itemsize
        stream.seek(start * row_bytes, 1)
        raw = stream.read((end - start) * row_bytes)
        assert len(raw) == (end - start) * row_bytes
        return np.frombuffer(raw, dtype=dtype).reshape((end - start,) + shape[1:]).copy()


def longest(mask, dt):
    edges = np.diff(np.r_[False, mask, False].astype(np.int8))
    starts, stops = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    return float(np.max(stops - starts) * dt) if len(starts) else 0.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recording', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    run, out = args.recording.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, out / Path(__file__).name)
    started = time.monotonic()
    result = json.loads((run / 'result.json').read_text())
    contract = json.loads((run / 'contract.json').read_text())
    assert sha(run / 'contract.json') == result['contract_sha256']
    assert sha(run / 'trace.npz') == result['trace_sha256']
    assert sha(run / 'world.xml') == contract['model_sha256']
    limits, physical = contract['tool_actuation_contract'], contract['physical_acceptance']
    events = json.loads((run / 'events.json').read_text())
    changes = [event for event in events if 'phase' in event]
    active = {'hold', 'tool_squeeze', 'tool_reopen'}
    begin = next(event['time_s'] for event in changes if event['phase'] == 'hold')
    end = next((event['time_s'] for event in changes
                if event['time_s'] > begin and event['phase'] not in active), result['simulated_seconds'])
    with zipfile.ZipFile(run / 'trace.npz') as archive:
        all_times = rows(archive, 'time')
        first, stop = np.searchsorted(all_times, [begin - 1e-8, end - 1e-8])
        stop = min(int(stop), len(all_times) - 1)
        times = all_times[first:stop + 1]
        q, v, warm, commands = [rows(archive, name, int(first), stop + 1)
                                for name in ['qpos', 'qvel', 'qacc_warmstart', 'ctrl']]
    assert len(times) > 1
    plugins = contract.get('collision_plugins', [])
    if plugins:
        from frozen_collision_plugins import load, require_stateless
        load(plugins, contract['source_snapshot_sha256']['frozen_collision_plugins.py'])
    m = mujoco.MjModel.from_xml_path(str(run / 'world.xml'))
    if plugins:
        require_stateless(m)
    dt = float(m.opt.timestep)
    assert np.max(abs(np.diff(times) - dt)) < 1e-8
    d = mujoco.MjData(m)
    d.qpos[:], d.qvel[:], d.time = q[0], v[0], float(times[0])
    mujoco.mj_forward(m, d)
    d.qacc_warmstart[:] = warm[0]
    tool = {m.body('tweezer').id}
    for body in range(m.nbody):
        if m.body_parentid[body] in tool:
            tool.add(body)
    allowed = {m.body(name).id for name in contract['allowed_tool_contact_bodies']}
    rest = mujoco.MjData(m)
    rest.qpos[:] = q[0]
    for joint in range(m.njnt):
        if int(m.jnt_bodyid[joint]) in tool and m.jnt_type[joint] == mujoco.mjtJoint.mjJNT_HINGE:
            rest.qpos[m.jnt_qposadr[joint]] = 0.
    mujoco.mj_kinematics(m, rest)
    root = m.body('tweezer').id
    endpoints = []
    for label, sign in [('negative', -1.), ('positive', 1.)]:
        tip = max((body for body in tool if m.body(body).name.startswith(label + '_beam_')),
                  key=lambda body: m.body(body).name)
        point = rest.xpos[root] + rest.xmat[root].reshape(3, 3) @ np.array([-.130, sign * .004, 0.])
        endpoints.append((tip, rest.xmat[tip].reshape(3, 3).T @ (point - rest.xpos[tip])))
    phase_times = np.array([event['time_s'] for event in changes])
    phase_names = np.array([event['phase'] for event in changes])
    phases = phase_names[np.searchsorted(phase_times, times[:-1] + 1e-8, side='right') - 1]
    assert set(phases) <= active
    n = len(phases)
    forces, positions = np.zeros((n, 3)), np.zeros((n, 3))
    other, gap = np.zeros(n), np.zeros(n)
    q_error = v_error = 0.
    external_force_seen = False
    for i in range(n):
        d.ctrl[:] = commands[i]
        mujoco.mj_step(m, d)
        q_error = max(q_error, float(np.max(abs(d.qpos - q[i + 1]))))
        v_error = max(v_error, float(np.max(abs(d.qvel - v[i + 1]))))
        if max(q_error, v_error) > physical['maximum_replay_error']:
            raise RuntimeError('Tool-stroke window does not replay exactly at ' + str(times[i]))
        external_force_seen |= bool(np.any(d.xfrc_applied) or np.any(d.qfrc_applied))
        # mj_step's contact solution and Cartesian transforms describe this
        # interval's starting state; qpos/qvel above describe its next state.
        for ci, contact in enumerate(d.contact):
            bodies = {int(m.geom_bodyid[g]) for g in contact.geom}
            if sum(int(m.geom_bodyid[g]) in tool for g in contact.geom) != 1:
                continue
            wrench = np.zeros(6)
            mujoco.mj_contactForce(m, d, ci, wrench)
            load = max(0., float(wrench[0]))
            if bodies & allowed:
                name = m.body(next(iter(bodies & allowed))).name
                finger = next(k for k, word in enumerate(['thumb', 'index', 'middle']) if word in name)
                forces[i, finger] += load
            else:
                other[i] += load
        tips = [d.xpos[body] + d.xmat[body].reshape(3, 3) @ point for body, point in endpoints]
        gap[i] = np.linalg.norm(tips[1] - tips[0])
        wrist = d.site('right_wrist_reference')
        positions[i] = wrist.xmat.reshape(3, 3).T @ (d.body('tweezer').xpos - wrist.xpos)
        if i % max(1, round(1. / dt)) == 0:
            print('native_tool_stroke', round(float(times[i]), 3), phases[i],
                  'gap_mm', round(float(gap[i] * 1000), 3), flush=True)
    native = out / 'tool_actuation_native.npz'
    np.savez_compressed(native, time_s=times[:-1], phase=phases, force_n=forces,
                        other_tool_contact_load_n=other, tip_gap_m=gap, tool_wrist_position_m=positions)
    loaded = ((forces[:, 0] > physical['minimum_thumb_load_n']) &
              (forces[:, 1:].min(axis=1) > physical['minimum_each_opposing_finger_load_n']))
    drift = np.linalg.norm(positions - positions[0], axis=1)
    safe = ((forces.max(axis=1) <= physical['maximum_normal_force_n']) &
            (other <= physical['maximum_unintended_hand_tool_load_n']) &
            (drift <= limits['maximum_tool_wrist_translation_drift_m']))
    metrics = {}
    for phase, target in [('hold', gap >= limits['minimum_open_tip_gap_m']),
                          ('tool_squeeze', gap <= limits['maximum_squeezed_tip_gap_m']),
                          ('tool_reopen', gap >= limits['minimum_open_tip_gap_m'])]:
        selected = phases == phase
        metrics[phase] = dict(samples=int(selected.sum()),
            longest_gap_dwell_s=longest(selected & safe & target, dt),
            longest_three_finger_loaded_gap_dwell_s=longest(selected & loaded & safe & target, dt),
            minimum_tip_gap_m=float(gap[selected].min()) if selected.any() else None,
            maximum_tip_gap_m=float(gap[selected].max()) if selected.any() else None,
            native_three_finger_loaded_s=float((selected & loaded).sum() * dt))
    ordered = [event['phase'] for event in changes if event['phase'] in
               {'tool_squeeze', 'tool_reopen', 'lower', 'finished'}]
    dwell = limits['force_target_dwell_s'] - dt / 2
    checks = dict(exact_native_window_replay=max(q_error, v_error) <= physical['maximum_replay_error'],
        fresh_attempt_finished_without_error=result['failure'] is None and changes[-1]['phase'] == 'finished',
        squeeze_reopen_lower_order=ordered[:3] == ['tool_squeeze', 'tool_reopen', 'lower'],
        open_before_squeeze=metrics['hold']['longest_gap_dwell_s'] >= dwell,
        closed_while_retained=metrics['tool_squeeze']['longest_gap_dwell_s'] >= dwell,
        reopened_while_retained=metrics['tool_reopen']['longest_gap_dwell_s'] >= dwell,
        original_three_finger_contact_duration=float(loaded.sum() * dt) >= physical['minimum_three_finger_contact_s'],
        grasp_position_retained=bool(drift.max() <= limits['maximum_tool_wrist_translation_drift_m']),
        bounded_finger_load=bool(forces.max() <= physical['maximum_normal_force_n']),
        no_external_tool_support=bool(other.max() <= physical['maximum_unintended_hand_tool_load_n']),
        no_applied_external_force=not external_force_seen,
        no_numerical_warnings=not bool(np.any(d.warning.number)))
    report = dict(scope=__doc__, recording=str(run), source_result_sha256=sha(run / 'result.json'),
        source_contract_sha256=sha(run / 'contract.json'), source_trace_sha256=result['trace_sha256'],
        source_events_sha256=sha(run / 'events.json'), evaluator_sha256=sha(__file__),
        native_sha256=sha(native), sample_period_s=dt, samples=n,
        window_start_s=float(times[0]), window_end_s=float(times[-1]),
        max_q_replay_error=q_error, max_v_replay_error=v_error, checks=checks, metrics=metrics,
        maximum_finger_force_n=float(forces.max()), maximum_external_tool_load_n=float(other.max()),
        maximum_tool_wrist_translation_drift_m=float(drift.max()),
        passed_recorded_tool_stroke=all(checks.values()),
        full_run_reviews_required=['physical_review.json', 'controller_replay.json', 'source_limit_review.json'],
        qualified_tool_actuation=False, qualified_specimen_handling=False, qualified_paper_branch=False,
        wall_seconds=time.monotonic() - started)
    (out / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed_recorded_tool_stroke'], metrics=metrics,
                          failed_checks=[key for key, value in checks.items() if not value])), flush=True)
    if not report['passed_recorded_tool_stroke']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
