"""Independently verify saved flexible-cover grasp/place/retrieve runs."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from load_model import load
from evaluate_cover import evaluate
from world import HERE
from trace_store import load_trace
from audit_film_trace import audit
from recorded_source import recorded_source


def main():
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    checks=[]
    for name in ['cover','cover_tests/seed_1','cover_tests/seed_2']:
        path=HERE/'runs'/name;receipt=json.loads((path/'result.json').read_text());errors=[]
        for file,pin in receipt['input_sha256'].items():
            source=path/file if file=='workcell.xml' else recorded_source(file,pin)
            if sha(source)!=pin:errors.append('input mismatch: '+file)
        for file,pin in receipt['artifacts_sha256'].items():
            if file=='physics_trace.npz':continue
            if sha(path/file)!=pin:errors.append('artifact mismatch: '+file)
        trace=load_trace(path,receipt['artifacts_sha256']['physics_trace.npz']);model=load(path/'workcell.xml')
        robot=SimpleNamespace(model=model,trace=list(zip(trace['time'],trace['qpos'],trace['qvel'],trace['ctrl'])))
        assessment=evaluate(robot,receipt['checkpoints'])
        geometry_path=path/'film_geometry_verification.json'
        geometry=json.loads(geometry_path.read_text()) if geometry_path.exists() else {}
        if not (geometry.get('source_trace_sha256')==receipt['artifacts_sha256']['physics_trace.npz']
                and geometry.get('workcell_sha256')==sha(path/'workcell.xml')
                and geometry.get('verifier_sha256')==sha(HERE/'audit_film_trace.py')
                and geometry.get('geometry_sha256')==sha(HERE/'film_geometry.py')):
            geometry=audit(path)
        lifts=[x for x in receipt['observations'] if x['label']=='cover_lifted']
        checks.append(dict(case=name,passed=not errors and receipt['status']=='passed' and assessment['passed'] and geometry['passed'] and len(lifts)==2,
                           errors=errors,independent_assessment=assessment,
                           film_geometry=dict(passed=geometry['passed'],failed_samples=geometry['failed_samples'],
                               report='runs/'+name+'/film_geometry_verification.json',
                               sha256=sha(path/'film_geometry_verification.json')),
                           receipt_sha256=sha(path/'result.json'),seed=receipt['seed']))
        print(name,checks[-1]['passed'],flush=True)
    report=json.loads((HERE/'membrane_tests.json').read_text())
    # The membrane suite carries its own source hashes; these must match the
    # model used by the handling runs rather than a later substituted membrane.
    inputs=report.get('input_sha256',{})
    checks.append(dict(case='membrane_tests',passed=report['passed'] and bool(inputs) and all(sha(HERE/p)==s for p,s in inputs.items()),receipt_sha256=sha(HERE/'membrane_tests.json')))
    result=dict(passed=all(x['passed'] for x in checks),checks=checks,verifier_sha256=sha(Path(__file__)),
                source_resolver_sha256=sha(HERE/'recorded_source.py'),whole_paper_validated=False,
                scope='Two-layer membrane cover transfer and retrieval in a separate fixture, three arm initializations, support counterexamples and triangle/solid intersection checks. Earlier force-only acceptance is superseded.')
    (HERE/'COVER_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    return result['passed']


if __name__=='__main__':raise SystemExit(0 if main() else 1)
