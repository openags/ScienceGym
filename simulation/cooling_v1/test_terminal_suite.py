"""Nominal, counterexample and numerical-refinement terminal jig campaign."""
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
from test_terminal_mechanism import run
from world import HERE
from trace_store import sha


def case(args):
    name,options,expected=args
    directory=HERE/'runs/terminal_mechanism_tests'/name
    if directory.exists():raise ValueError('Preserve earlier mechanism records before rerunning: '+str(directory))
    result=run(directory,**options)
    passed=result['retained']==expected and result['numerics_passed'] and result['source_unchanged']
    return dict(case=name,passed=passed,expected_retained=expected,observed_retained=result['retained'],
        status=result['status'],result_sha256=sha(directory/'result.json'),
        result='runs/terminal_mechanism_tests/'+name+'/result.json',events=result['events'],
        maximum_solver_iterations=result['maximum_solver_iterations'])


def main():
    cases=[('nominal',{},True),('opposing_bank',{'pin':44},True),
           ('half_step',{'dt':.00005},True),('noslip_refinement',{'noslip':10},True),
           ('missing_clamp',{'clamp':False},False),('missing_bit',{'bit':False},False),
           ('no_thread_friction',{'friction':False},False),('regularized_creep',{'noslip':0},False)]
    with ProcessPoolExecutor(max_workers=4) as pool:rows=list(pool.map(case,cases))
    comparisons=[]
    selected=rows[0]
    def clamped(row):return next((e for e in row['events'] if e['event']=='clamped'),None)
    def released(row):return next((e for e in row['events'] if e['event']=='driver_released'),None)
    for index in [1,2,3]:
        a,b=clamped(selected),clamped(rows[index]);c,d=released(selected),released(rows[index])
        if not all([a,b,c,d]):comparisons.append(dict(case=rows[index]['case'],passed=False,reason='missing clamp/release event'));continue
        travel=abs(a['advance_m']-b['advance_m']);force=abs(c['normal_N']-d['normal_N'])
        comparisons.append(dict(case=rows[index]['case'],passed=travel<.00001 and force<.2,
            clamp_travel_difference_m=travel,released_normal_difference_N=force))
    report=dict(passed=all(r['passed'] for r in rows+comparisons),cases=rows,refinement=comparisons,
        input_sha256={n:sha(HERE/n) for n in ['test_terminal_suite.py','test_terminal_mechanism.py','terminal_mechanism.py']},
        scope='Guided-driver tests of a selected passive terminal mechanism, two pin banks, timestep/NoSlip refinement, missing hardware and friction counterexamples. No Panda manipulation, full wire route, fine-wire transition or electronics qualification.',whole_paper_validated=False)
    (HERE/'terminal_mechanism_tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print('TERMINAL SUITE',report['passed'],flush=True);return report['passed']


if __name__=='__main__':raise SystemExit(0 if main() else 1)
