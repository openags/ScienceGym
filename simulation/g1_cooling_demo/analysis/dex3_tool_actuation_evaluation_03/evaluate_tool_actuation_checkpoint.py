"""Evaluate native tool-gap/load evidence from a restored-state diagnostic.

The evaluator consumes plant-only measurements, never controller claims about
tip closure. Passing is limited to the recorded continuation; a fresh pickup,
independent full-physics replay and repeated trials remain separate obligations.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def longest(mask, dt):
    edges = np.diff(np.r_[False, mask, False].astype(np.int8))
    starts, stops = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    return float(np.max(stops - starts) * dt) if len(starts) else 0.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('diagnostic', type=Path)
    parser.add_argument('actor_run', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    run, actor, out = args.diagnostic.resolve(), args.actor_run.resolve(), args.output.resolve()
    result = json.loads((run / 'result.json').read_text())
    contract = json.loads((actor / 'contract.json').read_text())
    assert sha(actor / 'contract.json') == result['actor_contract_sha256']
    evidence = result['tool_actuation_native']
    assert sha(run / evidence['file']) == evidence['sha256']
    with np.load(run / evidence['file']) as data:
        t, phases, forces, other, gap, positions = [data[key].copy() for key in
            ['time_s', 'phase', 'force_n', 'other_tool_contact_load_n',
             'tip_gap_m', 'tool_wrist_position_m']]
    dt = float(evidence['sample_period_s'])
    n = len(t)
    assert n == evidence['samples'] and n > 1 and dt > 0
    assert forces.shape == positions.shape == (n, 3)
    assert phases.shape == other.shape == gap.shape == (n,)
    assert np.isfinite(np.r_[t, forces.ravel(), other, gap, positions.ravel()]).all()
    assert np.max(abs(np.diff(t) - dt)) < 1e-8
    assert set(phases) <= {'hold', 'tool_squeeze', 'tool_reopen'}
    limits, physical = contract['tool_actuation_contract'], contract['physical_acceptance']
    loaded = ((forces[:, 0] > physical['minimum_thumb_load_n']) &
              (forces[:, 1:].min(axis=1) > physical['minimum_each_opposing_finger_load_n']))
    safe = ((forces.max(axis=1) <= physical['maximum_normal_force_n']) &
            (other <= physical['maximum_unintended_hand_tool_load_n']))
    drift = np.linalg.norm(positions - positions[0], axis=1)
    safe &= drift <= limits['maximum_tool_wrist_translation_drift_m']
    open_tip = gap >= limits['minimum_open_tip_gap_m']
    closed_tip = gap <= limits['maximum_squeezed_tip_gap_m']
    dwell = float(limits['force_target_dwell_s'])
    metrics = {}
    for phase, target_gap in [('hold', open_tip), ('tool_squeeze', closed_tip), ('tool_reopen', open_tip)]:
        selected = phases == phase
        metrics[phase] = dict(samples=int(selected.sum()),
            longest_gap_dwell_s=longest(selected & safe & target_gap, dt),
            longest_loaded_gap_dwell_s=longest(selected & loaded & safe & target_gap, dt),
            native_three_finger_loaded_s=float((selected & loaded).sum() * dt),
            minimum_tip_gap_m=float(gap[selected].min()) if selected.any() else None,
            maximum_tip_gap_m=float(gap[selected].max()) if selected.any() else None,
            minimum_finger_load_n=forces[selected].min(axis=0).tolist() if selected.any() else None)
    events = json.loads((run / 'events.json').read_text())
    ordered = [e.get('phase') for e in events if e.get('phase') in
               {'tool_squeeze', 'tool_reopen', 'lower', 'finished'}]
    checks = dict(continuation_finished_without_error=result.get('failure') is None,
        squeeze_then_reopen_then_lower=ordered[:3] == ['tool_squeeze', 'tool_reopen', 'lower'],
        completed_release_and_withdrawal=result.get('last_phase') == 'finished',
        open_before_squeeze=metrics['hold']['longest_gap_dwell_s'] >= dwell - dt / 2,
        closed_while_held=metrics['tool_squeeze']['longest_gap_dwell_s'] >= dwell - dt / 2,
        reopened_while_held=metrics['tool_reopen']['longest_gap_dwell_s'] >= dwell - dt / 2,
        original_three_finger_contact_duration=float(loaded.sum() * dt) >= physical['minimum_three_finger_contact_s'],
        tool_grasp_position_retained=bool(drift.max() <= limits['maximum_tool_wrist_translation_drift_m']),
        bounded_finger_load=bool(forces.max() <= physical['maximum_normal_force_n']),
        no_unintended_external_tool_support=bool(other.max() <= physical['maximum_unintended_hand_tool_load_n']))
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, out / Path(__file__).name)
    report = dict(scope=__doc__, diagnostic=str(run), actor_run=str(actor),
        source_result_sha256=sha(run / 'result.json'), native_sha256=evidence['sha256'],
        actor_contract_sha256=sha(actor / 'contract.json'), evaluator_sha256=sha(__file__),
        sample_period_s=dt, samples=n, metrics=metrics, checks=checks,
        maximum_tool_wrist_translation_drift_m=float(drift.max()),
        passed_actuation_diagnostic=all(checks.values()),
        continuous_pickup_and_tool_use=False, qualified_tool_actuation=False,
        qualified_specimen_handling=False, qualified_paper_branch=False)
    (out / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed_actuation_diagnostic'], metrics=metrics,
                         failed_checks=[k for k, v in checks.items() if not v])))
    if not report['passed_actuation_diagnostic']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
