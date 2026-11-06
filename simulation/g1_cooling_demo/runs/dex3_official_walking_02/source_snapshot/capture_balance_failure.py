"""Diagnostic entry point: retain a rejected actor-owned balance problem.

Executed inside the existing read-only actor sandbox, with the same sensor
input and frozen actor modules. No failed answer reaches a motor. The extra
error payload is consumed only by the external diagnostic recorder.
"""
import argparse
import pickle
import runpy
import sys

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
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--diagnostic-actor', default='visual_tool_actor',
                    choices=['visual_tool_actor', 'carry_tool_actor', 'inspection_tool_actor'])
args, remaining = parser.parse_known_args()
sys.argv = [sys.argv[0], *remaining]
runpy.run_path('/actor/' + args.diagnostic_actor + '.py', run_name='__main__')
