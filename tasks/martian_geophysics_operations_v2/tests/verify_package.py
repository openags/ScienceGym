"""Read-only structural audit; no report mutation or source acquisition."""
from pathlib import Path
import json,sys,re
sys.path.insert(0,str(Path(__file__).parent))
from contract import ROOT,load,BRANCHES,closure,CONFLICTS

def unique(pairs):
 out={}
 for k,v in pairs:
  if k in out:raise ValueError('duplicate JSON key')
  out[k]=v
 return out

def verify(root=ROOT):
 root=Path(root)
 def load(name):return json.loads((root/name).read_text())
 BRANCHES={b['id']:b for b in load('branches.json')['branches']}
 CONFLICTS={c['id']:c for c in load('source_conflicts.json')['conflicts']}
 def closure(selected):
  visited=set();active=set()
  def visit(b):
   if b not in BRANCHES or b in active:raise ValueError('unknown or cyclic dependency')
   if b in visited:return
   active.add(b)
   for d in BRANCHES[b]['required_branch_ids']:visit(d)
   active.remove(b);visited.add(b)
  for b in selected:visit(b)
  return visited
 errors=[]
 def check(ok,msg):
  if not ok:errors.append(msg)
 for p in root.rglob('*.json'):
  try:json.loads(p.read_text(),object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite')))
  except Exception:errors.append('invalid JSON '+p.name)
 ops=load('operations.json')['operations'];opids={x['id'] for x in ops}
 ev={x['id'] for x in load('provenance.json')['evidence']};uids={x['id'] for x in load('unknown_parameters.json')['unknowns']};stations={x['id'] for x in load('station_contracts.json')['stations']}
 check(len(opids)==len(ops),'duplicate operation id')
 check(len(BRANCHES)==load('branches.json')['branch_count'],'branch count mismatch')
 check(len(ops)==load('operations.json')['operation_count'],'operation count mismatch')
 for b in BRANCHES.values():
  check(set(b['operation_ids'])<=opids,'missing operation '+b['id'])
  check(set(b['source_evidence_ids'])<=ev,'missing evidence '+b['id'])
  check(set(b['unknown_parameter_ids'])<=uids,'missing unknown '+b['id'])
  check(b['station_id'] in stations,'unknown station '+b['id'])
  check(b['execution_ready'] is False,'execution claim '+b['id'])
  check(b['expected_results_actor_visible'] is False,'actor targets '+b['id'])
  check(set(b['conflict_ids'])<=set(CONFLICTS),'unknown conflict')
  check(len(b['operation_ids'])==len(b['phase_order']),'phase count mismatch')
  for d in b['required_branch_ids']:check(b['id'] not in closure([d]),'dependency cycle')
 for o in ops:
  check(o['actor_may_command_hazard'] is False,'hazard exposed')
  check(o['branch_id'] in BRANCHES,'unknown operation branch')
 check(set(CONFLICTS)=={'C'+str(i).zfill(2) for i in range(1,11)},'conflict coverage')
 check(all(c['status']=='unresolved' and c['actor_can_resolve'] is False for c in CONFLICTS.values()),'conflict erased')
 coverage=load('coverage_matrix.json')
 check({x['source_unit'] for x in coverage['coverage']}==ev,'source coverage mismatch')
 check({r['route_id'] for r in coverage['routes']}=={'R'+str(i).zfill(2) for i in range(1,14)},'route coverage mismatch')
 check(all(r['branch_ids'] for r in coverage['routes']),'unmapped route')
 for r in coverage['coverage']:check(set(r['branch_ids'])<=set(BRANCHES),'coverage unknown branch')
 access=load('source_access_audit.json');boundary=load('RELEASE_BOUNDARY.json')
 check(access['main_and_extended_data_pixels_verified'] is False,'pixel gap erased')
 check(access['source_complete_for_entire_paper'] is False,'full-source overclaim')
 check(boundary['physical_simulation_run'] is False and boundary['real_actuation_implemented'] is False,'runtime claim')
 check(boundary['temperature_correction_sign_resolved'] is False and boundary['H5897_H5898_assignment_resolved'] is False,'blocking conflict erased')
 check(load('agent_visible.json')['source_outcomes_included'] is False,'actor outcome boundary')
 for p in root.rglob('*'):
  if p.is_file() and p.suffix in ['.md','.json','.py']:
   s=p.read_text()
   check(not any('\u4e00'<=c<='\u9fff' for c in s),'non-English prose '+p.name)
   check(not any(x in s for x in ['/'+'workspace'+'/','/'+'tmp'+'/']),'private absolute path '+p.name)
 return errors
if __name__=='__main__':
 errors=verify();print(json.dumps({'check':'static_package','passed':not errors,'errors':errors,'branches':len(BRANCHES),'operations':len(load('operations.json')['operations']),'source_routes':13,'conflicts':10,'physical_execution':False},indent=2));raise SystemExit(bool(errors))
