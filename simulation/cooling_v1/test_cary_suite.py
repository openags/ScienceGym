"""Reproduce the main lid cycle, physical fault stops and time-step check."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from world import HERE
from verify_cary import verify
from trace_store import sha
CASES=[('nominal','runs/cary',[]),('seed_1','runs/cary_tests/seed_1',['--seed','1']),('missing_pull','runs/cary_tests/missing_pull',['--case','missing_pull']),('locked_slide','runs/cary_tests/locked_slide',['--case','locked_slide']),('half_step','runs/cary_tests/half_step',['--timestep','.0005'])]

def main(execute=False):
 rows=[];results={}
 for name,directory,arguments in CASES:
  expected=name if name in {'missing_pull','locked_slide'} else 'nominal'
  if execute:
   process=subprocess.run([sys.executable,str(HERE/'run_cary.py'),'--out',directory,*arguments],env=dict(os.environ,MUJOCO_GL='egl'))
   if expected=='nominal' and process.returncode:raise RuntimeError('Cary execution failed: '+name)
  path=HERE/directory;report=verify(path,expected);results[name]=json.loads((path/'result.json').read_text())
  rows.append(dict(case=name,directory=directory,passed=report['passed'],checks=len(report['checks']),expected=expected,result_sha256=sha(path/'result.json'),verification_sha256=sha(path/'verification.json')))
  print(name,report['passed'],len(report['checks']),flush=True)
 nominal=[e['travel_m'] for e in results['nominal']['observations'] if e['label']=='cary_lid_released'];refined=[e['travel_m'] for e in results['half_step']['observations'] if e['label']=='cary_lid_released'];delta=max((abs(a-b) for a,b in zip(nominal,refined)),default=float('inf'))
 refinement=dict(passed=len(nominal)==len(refined)==2 and delta<.0005,nominal_timestep_s=results['nominal']['configuration']['timestep_s'],refined_timestep_s=results['half_step']['configuration']['timestep_s'],maximum_released_position_difference_m=delta,tolerance_m=.0005)
 summary=dict(passed=all(r['passed'] for r in rows) and refinement['passed'],cases=rows,refinement=refinement,verifier_sha256=sha(HERE/'verify_cary.py'),suite_sha256=sha(Path(__file__)),whole_paper_validated=False,scope='Passive main sliding lid: opening, released retention, regrasp and closure. The front panel, extension, accessory, specimen and optical workflows remain separate obligations.')
 (HERE/'CARY_VERIFICATION.json').write_text(json.dumps(summary,indent=2)+'\n');return summary['passed']
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');raise SystemExit(0 if main(p.parse_args().execute) else 1)
