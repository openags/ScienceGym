"""Test bound conversion and solve both retained balance convergence failures."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
import numpy as np
from scipy import sparse

HERE=Path(__file__).resolve().parent;BASE=HERE.parents[1]
sys.path.insert(0,str(BASE))
from conic_balance import solve


def main():
    output=HERE/'review.json'
    if output.exists():raise FileExistsError(output)
    A=sparse.csc_matrix([[1.,1.],[1.,0.],[0.,1.]])
    result=solve(sparse.eye(2,format='csc'),np.zeros(2),A,
                 np.array([1.,.2,0.]),np.array([1.,.4,np.inf]))
    checks=dict(known_active_upper_and_lower_bounds=bool(np.max(abs(result.x-[.4,.6]))<1e-7))
    try:
        solve(sparse.eye(2,format='csc'),np.zeros(2),A,
              np.array([1.,2.,0.]),np.array([1.,3.,np.inf]))
    except RuntimeError:checks['infeasible_problem_rejected']=True
    else:checks['infeasible_problem_rejected']=False
    rows=[];deps=[Path(__file__),BASE/'conic_balance.py']
    for folder in [BASE/'analysis/nicolet_slider_push_06',BASE/'analysis/quasistatic_walk_06']:
        pp,ap,vp=[folder/('step_failure_'+n+'.npz') for n in ['P','A','vectors']]
        P,A=sparse.load_npz(pp),sparse.load_npz(ap);v=dict(np.load(vp))
        answer=solve(P,v['q'],A,v['l'],v['u'])
        rows.append(dict(source=str(folder.relative_to(BASE)),**vars(answer.info)))
        checks[folder.name+'_solved_original_problem']=answer.info.status_val==1 and answer.info.prim_res<1e-6
        deps.extend([pp,ap,vp])
    report=dict(passed=all(checks.values()),checks=checks,retained_failures=rows,
                source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
                scope='Numerical solver and constraint-conversion checks. Original physical bounds unchanged; new motion still needs execution and independent replay.')
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
    if not report['passed']:raise SystemExit(1)


if __name__=='__main__':main()
