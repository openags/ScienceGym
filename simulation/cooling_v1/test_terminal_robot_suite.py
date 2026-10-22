"""Reproduce and independently assess the complete physical terminal cycle."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from world import HERE
from verify_terminal_robot import verify
from trace_store import sha

CASES=[('nominal','runs/terminal',[]),('seed_1','runs/terminal_tests/seed_1',['--seed','1']),
       ('missing_bit','runs/terminal_tests/missing_bit',['--no-bit']),
       ('missing_clamp','runs/terminal_tests/missing_clamp',['--no-clamp']),
       ('half_step','runs/terminal_tests/half_step',['--timestep','.00005'])]

def main(execute=False):
 rows=[];reports={};results={}
 for name,relative,arguments in CASES:
  expected=name if name in {'missing_bit','missing_clamp'} else 'nominal'
  if execute:
   process=subprocess.run([sys.executable,str(HERE/'run_terminal.py'),'--out',relative,*arguments],env=dict(os.environ,MUJOCO_GL='egl'))
   if expected=='nominal' and process.returncode:raise RuntimeError('Nominal terminal execution failed: '+name)
  directory=HERE/relative;report=verify(directory,expected);reports[name]=report;results[name]=json.loads((directory/'result.json').read_text())
  rows.append(dict(case=name,directory=relative,passed=report['passed'],checks=len(report['checks']),expected=expected,
                   result_sha256=sha(directory/'result.json'),verification_sha256=sha(directory/'verification.json')))
  print(name,report['passed'],len(report['checks']),flush=True)
 def measurement(case,check,key):return next(c for c in reports[case]['checks'] if c['name']==check)[key]
 differences={}
 for label,check,key,tolerance in [('insertion_depth','wire_inserted','depth_m',.0001),
                                  ('clamp_load','physical_clamp_load','clamp_normal_N',.5),
                                  ('return_position_error','returned_to_support','error_m',.0005)]:
  nominal=measurement('nominal',check,key);refined=measurement('half_step',check,key)
  differences[label]=dict(nominal=nominal,half_step=refined,absolute_difference=abs(nominal-refined),tolerance=tolerance,passed=abs(nominal-refined)<tolerance)
 refinement=dict(passed=all(v['passed'] for v in differences.values()),nominal_timestep_s=results['nominal']['configuration'].get('timestep_s',.0001),refined_timestep_s=results['half_step']['configuration']['timestep_s'],comparisons=differences)
 summary=dict(passed=all(r['passed'] for r in rows) and refinement['passed'],cases=rows,refinement=refinement,
              verifier_sha256=sha(HERE/'verify_terminal_robot.py'),suite_sha256=sha(Path(__file__)),whole_paper_validated=False,
              scope='One 0.6 m conductor: insertion, fixture retention, threaded clamp, 1 N pull, reopening, withdrawal and return. Full paired circuit assembly remains separate.')
 (HERE/'TERMINAL_ROBOT_VERIFICATION.json').write_text(json.dumps(summary,indent=2)+'\n');return summary['passed']

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');raise SystemExit(0 if main(p.parse_args().execute) else 1)
