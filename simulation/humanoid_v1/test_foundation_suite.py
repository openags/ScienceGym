"""Reproducible body-foundation cases; no manipulation admission is implied."""
import argparse
from datetime import datetime, timezone
import json
import subprocess
import sys
import numpy as np
from world import HERE, sha
from verify_foundation import verify

CASES = [('nominal', []), ('seed_1', ['--seed', '1']), ('half_step', ['--timestep', '.0005']),
         ('motors_off', ['--case', 'motors_off']), ('no_floor', ['--case', 'no_floor'])]


def suite(execute=False):
    rows = []; results = {}
    for name, flags in CASES:
        directory = HERE / 'runs' / name
        if execute:
            if directory.exists():
                archive = HERE / 'runs/debug' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ_') + name)
                archive.parent.mkdir(parents=True, exist_ok=True); directory.rename(archive)
            process = subprocess.run([sys.executable, str(HERE / 'run_foundation.py'), '--out', str(directory), *flags])
            if name not in {'no_floor', 'motors_off'} and process.returncode:
                raise RuntimeError('Body-foundation run failed: ' + name)
        report = verify(directory)
        rows.append(dict(case=name, passed=report['passed'], checks=len(report['checks']),
                         directory='runs/' + name, result_sha256=sha(directory / 'result.json'),
                         verification_sha256=sha(directory / 'verification.json')))
        results[name] = json.loads((directory / 'result.json').read_text())
        print(name, report['passed'], flush=True)
    with np.load(HERE / 'runs/nominal/physics_trace.npz') as archive: nominal = {k: archive[k] for k in archive.files}
    with np.load(HERE / 'runs/half_step/physics_trace.npz') as archive: refined = {k: archive[k] for k in archive.files}
    q = np.column_stack([np.interp(nominal['time'], refined['time'], refined['qpos'][:, k]) for k in range(refined['qpos'].shape[1])])
    root_difference = float(np.max(np.linalg.norm(nominal['qpos'][:, :3] - q[:, :3], axis=1)))
    joint_difference = float(np.max(abs(nominal['qpos'][:, 7:] - q[:, 7:])))
    q[:, 3:7] /= np.linalg.norm(q[:, 3:7], axis=1)[:, None]
    angle_difference = float(np.max(2 * np.arccos(np.clip(abs(np.sum(nominal['qpos'][:, 3:7] * q[:, 3:7], axis=1)), -1, 1))))
    refinement = dict(passed=root_difference < .003 and joint_difference < .01 and angle_difference < .005,
                      maximum_root_translation_difference_m=root_difference, translation_tolerance_m=.003,
                      maximum_joint_difference_rad=joint_difference, joint_tolerance_rad=.01,
                      maximum_root_rotation_difference_rad=angle_difference, rotation_tolerance_rad=.005,
                      nominal_timestep_s=results['nominal']['configuration']['timestep_s'],
                      refined_timestep_s=results['half_step']['configuration']['timestep_s'])
    summary = dict(passed=all(r['passed'] for r in rows) and refinement['passed'], cases=rows,
                   refinement=refinement, verifier_sha256=sha(HERE / 'verify_foundation.py'),
                   suite_sha256=sha(HERE / 'test_foundation_suite.py'),
                   hand_model_present=False, manipulation_accepted=False, whole_paper_validated=False,
                   scope='Body-only standing and unloaded bilateral wrist motion. Exact Dex5-S model and full manipulation remain unimplemented.')
    (HERE / 'FOUNDATION_VERIFICATION.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2), flush=True)
    return summary['passed']


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--execute', action='store_true')
    raise SystemExit(0 if suite(p.parse_args().execute) else 1)
