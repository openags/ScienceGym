"""Compare numerical settings on one retained, rejected balance QP.

Every case solves the identical objective and physical constraints with the
original full-accuracy tolerances. No answer here actuates the robot.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import clarabel
import numpy as np
from scipy import sparse


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('diagnostic', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    run, out = args.diagnostic.resolve(), args.output.resolve()
    result = json.loads((run / 'result.json').read_text())
    record = result['rejected_balance_problem']
    problem = run / record['file']
    assert sha(problem) == record['sha256']
    assert clarabel.__version__ == '0.11.1'
    with np.load(problem) as data:
        P, q, A, lower, upper = [data[k].copy() for k in ['P', 'q', 'A', 'lower', 'upper']]
    P = sparse.triu(P).tocsc()
    A = sparse.csc_matrix(A)
    equal = np.isfinite(lower) & (lower == upper)
    high, low = np.isfinite(upper) & ~equal, np.isfinite(lower) & ~equal
    transformed = sparse.vstack([A[equal], A[high], -A[low]], format='csc')
    bound = np.r_[lower[equal], upper[high], -lower[low]]
    ne, nh, nl = int(equal.sum()), int(high.sum()), int(low.sum())
    cones = [clarabel.ZeroConeT(ne), clarabel.NonnegativeConeT(nh + nl)]
    full = P + P.T - sparse.diags(P.diagonal())
    options = [
        ('original', {}),
        ('refine_regularization', dict(static_regularization_constant=1e-10, iterative_refinement_max_iter=20)),
        ('refine_regularization_12', dict(static_regularization_constant=1e-12, iterative_refinement_max_iter=20)),
        ('equilibrate_30', dict(equilibrate_max_iter=30)),
        ('shorter_interior_steps', dict(max_step_fraction=.95)),
    ]
    rows = []
    for name, changed in options:
        settings = clarabel.DefaultSettings()
        settings.verbose = False
        settings.max_threads = 1
        settings.tol_gap_abs = settings.tol_gap_rel = settings.tol_feas = 1e-9
        for key, value in changed.items():
            setattr(settings, key, value)
        solver = clarabel.DefaultSolver(P, q, transformed, bound, cones, settings)
        answer = solver.solve()
        x, z = np.asarray(answer.x), np.asarray(answer.z)
        dual = np.zeros(len(lower))
        dual[equal] = z[:ne]
        dual[high] = z[ne:ne+nh]
        dual[low] -= z[ne+nh:]
        projected = A @ x
        violation = float(max(0., np.max(lower - projected), np.max(projected - upper)))
        stationarity = float(np.max(abs(full @ x + q + A.T @ dual)))
        info = solver.get_info()
        passed = bool(answer.status == clarabel.SolverStatus.Solved and
                      np.isfinite(np.r_[x, dual]).all() and violation <= 1e-6)
        row = dict(name=name, changed_settings=changed, status=str(answer.status),
            iterations=answer.iterations, original_constraint_violation=violation,
            original_stationarity=stationarity, primal_residual=info.res_primal,
            dual_residual=info.res_dual, gap_absolute=info.gap_abs,
            gap_relative=info.gap_rel, objective=float(.5*x@(full@x) + q@x),
            original_acceptance_passed=passed)
        rows.append(row)
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, out / Path(__file__).name)
    report = dict(scope=__doc__, source_result_sha256=sha(run/'result.json'),
        problem_sha256=record['sha256'], source_sha256=sha(__file__), rows=rows,
        physical_constraints_changed=False, original_tolerances_changed=False,
        qualified_robot_operation=False)
    (out/'review.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(rows))


if __name__ == '__main__':
    main()
