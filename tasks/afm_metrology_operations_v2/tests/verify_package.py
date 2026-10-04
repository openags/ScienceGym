"""Static cross-reference checks plus explicitly synthetic happy paths."""
import json,sys
from pathlib import Path
from contract import fixture,validate
R=Path(__file__).resolve().parents[1]
def load(n):return json.loads((R/n).read_text())
def verify():
 errors=[]
 def check(v,m):
  if not v:errors.append(m)
 branches=load('branches.json')['branches'];ops=load('operations.json')['operations'];ev=load('provenance.json')['evidence'];unknown=load('unknown_parameters.json')['parameters']
 for name,items in [('branch',branches),('operation',ops),('evidence',ev),('unknown',unknown)]:check(len({i['id'] for i in items})==len(items),'duplicate '+name)
 bid={b['id'] for b in branches};oid={x['id'] for x in ops};eid={x['id'] for x in ev};uid={x['id'] for x in unknown}
 check(len(branches)==8,'branch count changed without review');check(len(ops)==27,'operation count changed')
 for b in branches:
  check(set(b['operation_ids'])<=(oid),'operation cross-reference')
  check(set(b['depends_on'])<=bid,'dependency cross-reference')
  check(set(b['source_evidence_ids'])<=eid,'evidence cross-reference')
  check(set(b['unknown_parameter_ids'])<=uid,'unknown cross-reference')
  check(b['session_teardown_operation_id'] in oid,'missing session teardown')
  check(b['calibration_reusable_between_episodes'] is False,'calibration reuse claim')
  check(b['physical_execution_implemented'] is False,'execution scope claim')
  errors.extend(validate(*fixture([b['id']])))
 errors.extend(validate(*fixture(list(bid))))
 for c in load('coverage_matrix.json')['coverage']:check(c['source_evidence_id'] in eid and set(c['branch_ids'])<=bid,'coverage cross-reference')
 conflicts=load('source_conflicts.json')['conflicts'];check(len(conflicts)==8 and all(c['resolved'] is False for c in conflicts),'conflict silently resolved')
 check('k_eff - k_c' in str(conflicts),'printed equation conflict missing')
 for p in load('preparation_routes.json')['routes']:check(p['complete_source_recipe'] is False and p['historical_route_complete'] is False,'fabrication closure invented')
 boundary=load('RELEASE_BOUNDARY.json')
 for k in ['whole_historical_route_complete','source_fabrication_complete','robot_execution_ready','real_device_actuation','physical_simulation','numerical_reproduction','source_pixels_exported','source_text_dump_exported','raw_source_data_included']:check(boundary[k] is False,'invalid release claim '+k)
 actor=load('agent_visible.json')
 check(set(actor)=={'schema_version','task','allowed_branch_ids','action_keys','visible_observations','safety_rules','not_supplied','execution_mode'},'actor schema widened')
 check(actor['action_keys']==['event_id','job_id','phase'],'actor supplies evaluator evidence')
 check(set(actor['allowed_branch_ids'])==bid,'actor branch inventory mismatch')
 check(load('operations.json')['operation_count']==len(ops),'operation count mismatch')
 check(load('coverage_matrix.json')['coverage_count']==len(load('coverage_matrix.json')['coverage']),'coverage count mismatch')
 return sorted(set(errors))
if __name__=='__main__':
 e=verify();print(json.dumps({'passed':not e,'errors':e,'scope':'static design and synthetic contracts'}));sys.exit(bool(e))
