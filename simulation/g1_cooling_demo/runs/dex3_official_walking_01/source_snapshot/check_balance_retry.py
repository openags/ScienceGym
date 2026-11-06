"""Regression check against a retained real balance failure and infeasibility."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

import numpy as np
from scipy import sparse


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('diagnostic', type=Path)
    parser.add_argument('original_actor_run', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    run, actor, out = args.diagnostic.resolve(), args.original_actor_run.resolve(), args.output.resolve()
    new_path = Path(__file__).with_name('conic_balance.py')
    old_path = actor/'actor_bundle/code/conic_balance.py'
    isolation = json.loads((actor/'actor_isolation.json').read_text())
    assert sha(old_path) == isolation['source_modules']['conic_balance.py']
    result = json.loads((run/'result.json').read_text())
    pin = result['rejected_balance_problem']
    problem = run/pin['file']
    assert sha(problem) == pin['sha256']
    new, old = module(new_path, 'repaired_balance'), module(old_path, 'original_balance')
    with np.load(problem) as data:
        qp = [sparse.csc_matrix(data[k]) if k in ['P', 'A'] else data[k].copy()
              for k in ['P', 'q', 'A', 'lower', 'upper']]
    try:
        old.solve(*qp)
        raise AssertionError('Original failure not reproduced')
    except RuntimeError as error:
        assert 'AlmostSolved' in str(error)
    answer = new.solve(*qp)
    assert answer.info.status_val == 1 and len(answer.info.attempts) == 2
    ordinary = [sparse.eye(1, format='csc'), np.array([-2.]), sparse.eye(1, format='csc'),
                np.array([0.]), np.array([1.])]
    a, b = old.solve(*ordinary), new.solve(*ordinary)
    assert np.array_equal(a.x, b.x) and np.array_equal(a.y, b.y)
    assert len(b.info.attempts) == 1
    infeasible = [sparse.eye(1, format='csc'), np.zeros(1), sparse.csc_matrix([[1.], [1.]]),
                  np.array([1., -np.inf]), np.array([np.inf, 0.])]
    try:
        new.solve(*infeasible)
        raise AssertionError('Infeasible answer accepted')
    except RuntimeError as error:
        assert 'PrimalInfeasible' in str(error)
    out.mkdir(parents=True, exist_ok=False)
    for path, name in [(Path(__file__), Path(__file__).name), (new_path, 'conic_balance.py'),
                       (old_path, 'original_conic_balance.py')]:
        shutil.copyfile(path, out/name)
    report = dict(scope=__doc__, captured_failure_reproduced=True, captured_problem_repaired=True,
        unchanged_ordinary_answer=True, infeasible_problem_still_rejected=True,
        source_sha256={p.name: sha(p) for p in out.glob('*.py')}, problem_sha256=sha(problem),
        original_actor_isolation_sha256=sha(actor/'actor_isolation.json'),
        attempts=answer.info.attempts, physical_constraints_changed=False,
        tolerances_changed=False, qualified_tool_actuation=False)
    (out/'review.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
