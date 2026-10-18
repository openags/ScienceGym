"""Verify saved layer runs and recompute physical checkpoint predicates."""
import hashlib
import json
from types import SimpleNamespace
import numpy as np
from load_model import load
from evaluate_continuous import evaluate
from world import HERE
from recorded_source import recorded_source


def main():
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    checks=[]
    for name in ['continuous','continuous_tests/seed_1','continuous_tests/seed_2']:
        path=HERE/'runs'/name;receipt=json.loads((path/'result.json').read_text())
        errors=[]
        for file,pin in receipt['input_sha256'].items():
            source=path/file if file=='workcell.xml' else recorded_source(file,pin)
            if sha(source)!=pin:errors.append('input mismatch: '+file)
        for file,pin in receipt['artifacts_sha256'].items():
            if sha(path/file)!=pin:errors.append('artifact mismatch: '+file)
        trace=np.load(path/'physics_trace.npz');model=load(path/'workcell.xml')
        robot=SimpleNamespace(model=model,trace=list(zip(trace['time'],trace['qpos'],trace['qvel'],trace['ctrl'])))
        times=[x['time_s'] for x in receipt['observations'] if x['label']=='assembled_layers_observed']
        assessment=evaluate(robot,receipt['targets'],times)
        lifts=[x for x in receipt['observations'] if x['label']=='edge_lift_observed']
        row=dict(case=name,passed=not errors and receipt['status']=='passed' and assessment['passed'] and len(lifts)==13,
                 receipt_sha256=sha(path/'result.json'),errors=errors,independent_assessment=assessment,
                 grasp_transfer_cycles=len(lifts),seed=receipt['seed'],simulated_seconds=receipt['simulated_seconds'])
        checks.append(row);print(name,row['passed'],flush=True)
    for name in ['continuous_geometry_checks.json','continuous_fault_tests.json']:
        report=json.loads((HERE/name).read_text());valid=report['passed']
        if 'input_sha256' in report:
            valid &= all(sha(recorded_source(n,pin))==pin for n,pin in report['input_sha256'].items())
        if 'input_xml_sha256' in report:valid &= sha(HERE/'runs/continuous/workcell.xml')==report['input_xml_sha256']
        checks.append(dict(case=name,passed=valid,receipt_sha256=sha(HERE/name)))
    result=dict(passed=all(x['passed'] for x in checks),checks=checks,whole_paper_validated=False,
                scope='Three initial arm perturbations of the same six rigid-layer assembly and return, seven geometry checks and four physical counterexamples; no film, sensor, reflector or complete paper qualification',
                verifier_sha256=sha(HERE/'verify_continuous.py'),source_resolver_sha256=sha(HERE/'recorded_source.py'))
    (HERE/'CONTINUOUS_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    return result['passed']


if __name__=='__main__':raise SystemExit(0 if main() else 1)
