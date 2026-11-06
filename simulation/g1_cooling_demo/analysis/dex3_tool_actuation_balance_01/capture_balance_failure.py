"""Diagnostic entry point: retain a rejected actor-owned balance problem.

Executed inside the existing read-only actor sandbox, with the same sensor
input and frozen actor modules. No failed answer reaches a motor. The extra
error payload is consumed only by the external diagnostic recorder.
"""
import pickle
import runpy

import conic_balance


original_solve = conic_balance.solve
original_dump = pickle.dump
rejected = None


def capture(P, q, A, lower, upper):
    global rejected
    try:
        return original_solve(P, q, A, lower, upper)
    except RuntimeError:
        rejected = dict(P=P.toarray(), q=q.copy(), A=A.toarray(),
                        lower=lower.copy(), upper=upper.copy())
        raise


def forward(value, *args, **kwargs):
    if isinstance(value, dict) and value.get('error') and rejected is not None:
        value = dict(value, diagnostic_balance_problem=rejected)
    return original_dump(value, *args, **kwargs)


conic_balance.solve = capture
pickle.dump = forward
runpy.run_path('/actor/visual_tool_actor.py', run_name='__main__')
