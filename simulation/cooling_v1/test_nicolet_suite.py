"""Reproduce the bounded cover cycle, two physical faults and half-step run."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from world import HERE
from verify_nicolet import verify
from trace_store import sha

CASES=[('nominal','runs/nicolet',[]),('seed_1','runs/nicolet_tests/seed_1',['--seed','1']),
       ('missing_handle','runs/nicolet_tests/missing_handle',['--case','missing_handle']),
       ('locked_hinge','runs/nicolet_tests/locked_hinge',['--case','locked_hinge']),
       ('half_step','runs/nicolet_tests/half_step',['--timestep','.0005'])]


def main(execute=False):
    rows=[];results={}
    for name,relative,arguments in CASES:
        expected=name if name in {'missing_handle','locked_hinge'} else 'nominal'
        if execute:
            process=subprocess.run([sys.executable,str(HERE/'run_nicolet.py'),'--out',relative,*arguments],env=dict(os.environ,MUJOCO_GL='egl'))
            if expected=='nominal' and process.returncode:raise RuntimeError('Nominal optical execution failed: '+name)
        directory=HERE/relative;report=verify(directory,expected);results[name]=json.loads((directory/'result.json').read_text())
        rows.append(dict(case=name,directory=relative,passed=report['passed'],checks=len(report['checks']),expected=expected,
                         result_sha256=sha(directory/'result.json'),verification_sha256=sha(directory/'verification.json')))
        print(name,report['passed'],len(report['checks']),flush=True)
    nominal=[e['angle_rad'] for e in results['nominal']['observations'] if e['label']=='spectrometer_cover_released']
    refined=[e['angle_rad'] for e in results['half_step']['observations'] if e['label']=='spectrometer_cover_released']
    delta=max((abs(a-b) for a,b in zip(nominal,refined)),default=float('inf'))
    refinement=dict(passed=len(nominal)==len(refined)==2 and delta<.0005,
                    nominal_timestep_s=results['nominal']['configuration']['timestep_s'],
                    refined_timestep_s=results['half_step']['configuration']['timestep_s'],maximum_released_angle_difference_rad=delta)
    summary=dict(passed=all(r['passed'] for r in rows) and refinement['passed'],cases=rows,refinement=refinement,
                 verifier_sha256=sha(HERE/'verify_nicolet.py'),suite_sha256=sha(Path(__file__)),whole_paper_validated=False,
                 scope='Passive hinged-cover opening and initial-state return, selected window retention and two mechanical fault rejections. Sliding-window operation, accessories, specimen handling and optics remain separate.')
    (HERE/'NICOLET_VERIFICATION.json').write_text(json.dumps(summary,indent=2)+'\n');return summary['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');raise SystemExit(0 if main(p.parse_args().execute) else 1)
