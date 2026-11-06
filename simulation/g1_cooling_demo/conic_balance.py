"""Solve the unchanged balance QP using a pinned interior-point implementation.

Convert lower/upper linear bounds to equality/nonnegative cones. No physical
constraint is dropped or softened. This module has no simulator or sensor API.
"""
from types import SimpleNamespace

import clarabel
import numpy as np
from scipy import sparse


def solve(P,q,A,lower,upper):
    if clarabel.__version__ != '0.11.1':
        raise RuntimeError('The balance solver requires pinned clarabel==0.11.1')
    P=sparse.triu(P).tocsc();A=sparse.csc_matrix(A)
    q=np.asarray(q,dtype=float);lower=np.asarray(lower,dtype=float);upper=np.asarray(upper,dtype=float)
    if (A.shape!=(len(lower),len(q)) or upper.shape!=lower.shape or
            not np.isfinite(np.r_[P.data,A.data,q]).all() or
            np.isnan(np.r_[lower,upper]).any() or np.any(lower>upper)):
        raise ValueError('Invalid constrained balance problem')
    equal=np.isfinite(lower)&(lower==upper)
    high=np.isfinite(upper)&~equal;low=np.isfinite(lower)&~equal
    transformed=sparse.vstack([A[equal],A[high],-A[low]],format='csc')
    bound=np.r_[lower[equal],upper[high],-lower[low]]
    ne,nh,nl=int(equal.sum()),int(high.sum()),int(low.sum())
    cones=[clarabel.ZeroConeT(ne),clarabel.NonnegativeConeT(nh+nl)]
    settings=clarabel.DefaultSettings()
    settings.verbose=False;settings.max_threads=1
    settings.tol_gap_abs=settings.tol_gap_rel=settings.tol_feas=1e-9
    full=P+P.T-sparse.diags(P.diagonal())
    attempts=[]
    for retry in range(2):
        if retry:
            # Retained tool-actuation QP: the default KKT regularization
            # stalled above the original dual-feasibility tolerance. Retry
            # the identical QP with finer linear-system regularization and
            # refinement. These are numerical settings, not objective terms
            # or relaxed physical constraints. Never accept AlmostSolved.
            settings.static_regularization_constant=1e-10
            settings.iterative_refinement_max_iter=20
        solver=clarabel.DefaultSolver(P,q,transformed,bound,cones,settings)
        answer=solver.solve()
        x=np.asarray(answer.x);z=np.asarray(answer.z)
        dual=np.zeros(len(lower));dual[equal]=z[:ne]
        dual[high]=z[ne:ne+nh];dual[low]-=z[ne+nh:]
        projected=A@x
        violation=float(max(0.,np.max(lower-projected),np.max(projected-upper)))
        stationarity=float(np.max(abs(full@x+q+A.T@dual)))
        info=SimpleNamespace(status='clarabel:'+str(answer.status),
                             status_val=1 if answer.status==clarabel.SolverStatus.Solved else 0,
                             iter=answer.iterations,prim_res=violation,dual_res=stationarity)
        attempts.append(dict(**vars(info),linear_system_retry=bool(retry)))
        if info.status_val==1 and np.isfinite(np.r_[x,dual]).all() and violation<=1e-6:
            info.attempts=attempts
            return SimpleNamespace(x=x,y=dual,info=info)
    info.attempts=attempts
    raise RuntimeError('Conic balance QP rejected: '+str(vars(info)))
