"""Reproduce and independently verify the bounded A25 mechanical episode."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from trace_store import sha
from verify_bath import verify
from world import HERE

CASES = [
    ('nominal', 'runs/bath', []),
    ('seed_1', 'runs/bath_tests/seed_1', ['--seed', '1']),
    ('missing_handle', 'runs/bath_tests/missing_handle', ['--case', 'missing_handle']),
    ('blocked_key', 'runs/bath_tests/blocked_key', ['--case', 'blocked_key']),
]


def main(execute=False):
    rows = []
    for name, relative, arguments in CASES:
        expected = name if name in {'missing_handle', 'blocked_key'} else 'nominal'
        if execute:
            process = subprocess.run([sys.executable, str(HERE/'run_bath.py'),
                                      '--out', relative, *arguments],
                                     env=dict(os.environ, MUJOCO_GL='egl'))
            # Fault runs intentionally return nonzero; their evidence must
            # still pass the independent check of the specified failure.
            if expected == 'nominal' and process.returncode:
                raise RuntimeError('Nominal execution failed: '+name)
        directory = HERE/relative
        report = verify(directory, expected)
        rows.append(dict(case=name, directory=relative, passed=report['passed'],
                         checks=len(report['checks']), expected=expected,
                         result_sha256=sha(directory/'result.json'),
                         verification_sha256=sha(directory/'verification.json')))
        print(name, report['passed'], len(report['checks']), flush=True)
    summary = dict(passed=all(row['passed'] for row in rows), cases=rows,
                   verifier_sha256=sha(HERE/'verify_bath.py'),
                   suite_sha256=sha(Path(__file__)), whole_paper_validated=False,
                   scope='Continuous lid handling and three physical keys; excludes fluids, loads, probes, wiring and electronic/thermal state.')
    (HERE/'BATH_VERIFICATION.json').write_text(json.dumps(summary, indent=2)+'\n')
    return summary['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    raise SystemExit(0 if main(parser.parse_args().execute) else 1)
