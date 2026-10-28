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
    solver=clarabel.DefaultSolver(P,q,transformed,bound,cones,settings)
    answer=solver.solve()
    x=np.asarray(answer.x);z=np.asarray(answer.z)
    dual=np.zeros(len(lower));dual[equal]=z[:ne]
    dual[high]=z[ne:ne+nh];dual[low]-=z[ne+nh:]
    projected=A@x
    violation=float(max(0.,np.max(lower-projected),np.max(projected-upper)))
    full=P+P.T-sparse.diags(P.diagonal())
    stationarity=float(np.max(abs(full@x+q+A.T@dual)))
    info=SimpleNamespace(status='clarabel:'+str(answer.status),
                         status_val=1 if answer.status==clarabel.SolverStatus.Solved else 0,
                         iter=answer.iterations,prim_res=violation,dual_res=stationarity)
    if (info.status_val!=1 or not np.isfinite(np.r_[x,dual]).all() or violation>1e-6):
        raise RuntimeError('Conic balance QP rejected: '+str(vars(info)))
    return SimpleNamespace(x=x,y=dual,info=info)
