"""Static design consistency only, never execution or scientific validation."""
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[1]
def verify(root=R):
 r=Path(root);errors=[]
 def load(name):return json.loads((r/name).read_text())
 def check(x,m):
  if not x:errors.append(m)
 try:
  b=load('branches.json');o=load('operations.json');a=load('asset_binding_plan.json');u=load('unknown_parameters.json')
  ids={x['id'] for x in b['branches']};ops={x['id'] for x in o['operations']};assets={x['asset_id'] for x in a['scene_assets']};unknowns={x['id'] for x in u['parameters']};evidence={x['id'] for x in load('evidence_map.json')}
  check(len(ids)==b['branch_count']==7,'branch count/duplicates');check(len(ops)==len(o['operations']),'operation duplicates');check(len(assets)==6,'scene asset count')
  for row in b['branches']:
   check(set(row['depends_on'])<=ids,'dangling dependency');check(row['id'] not in row['depends_on'],'self dependency')
   check(set(row['operation_ids'])<=ops,'missing operation');check(set(row['unknown_parameter_ids'])<=unknowns,'unknown qualifier');check(set(row['source_evidence_ids'])<=evidence,'missing evidence')
   check(row['physical_execution_implemented'] is False and row['whole_paper_complete'] is False,'invalid branch claims')
  for row in o['operations']:
   check(bool(row['asset_ids']) and set(row['asset_ids'])<=assets,'unbound operation '+row['id']);check(row['device_command_implemented'] is False,'actuator claim')
  for row in a['scene_assets']:
   check(set(row['bind_operation_ids'])<=ops,'asset references absent operation');check(len(set(row['required_anchor_ids']))==len(row['required_anchor_ids']),'duplicate anchor');check(row['physical_geometry_validated'] is False,'physical geometry claim')
  check({x['id'] for x in load('source_conflicts.json')}=={'FLOW_40X','PRECISION_NOT_ACCURACY','PLATE_LABEL_SWAP','REPEAT_COUNT','SPP5_SEM','GRID_DISCRETIZATION','DATA_AVAILABILITY_VERSION','SECTION_REFERENCE'},'source conflict loss')
  check(load('station_contracts.json')['flow']['default']=='HOLD','default flow not held');check(load('station_contracts.json')['flow']['production_execution'] is False,'production pump enabled')
  actor=load('agent_visible.json');check(actor['evaluation_information_included'] is False,'actor leak');check(actor['action_keys']==['event_id','job_id','phase'],'actor observation authority')
  check(load('coverage_matrix.json')['whole_paper_completed']==0,'whole-paper inflation');check(load('analysis_contracts.json')['source_numeric_outcomes_are_pass_thresholds'] is False,'source result pass threshold')
  check(load('provenance.json')['source_asset_reuse'] is False,'source asset reuse')
  from contract import fixture,validate
  for profile in ['SPP2_1064','SPP5_1064','SPP5_532']:
   for branch in ids:check(not validate(*fixture([branch],profile)),'invalid fixture '+branch+profile)
 except (OSError,ValueError,KeyError,TypeError) as ex:errors.append('static read/schema error: '+str(ex))
 return errors
if __name__=='__main__':
 e=verify();print(json.dumps(dict(passed=not e,errors=e,scope='static bounded design consistency')));sys.exit(bool(e))
