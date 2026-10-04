"""Validate original design references and semantic source boundaries, offline."""
from pathlib import Path
import json,re,sys
from contract import BRANCHES,fixture,validate,plan_for,strict_equal
ROOT=Path(__file__).resolve().parents[1]
def unique(pairs):
 d={}
 for k,v in pairs:
  if k in d:raise ValueError('duplicate JSON key '+k)
  d[k]=v
 return d

def read(path):return json.loads(path.read_text(),object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('invalid number')))

def verify(root=ROOT):
 errors=[]
 def ck(v,msg):
  if not v:errors.append(msg)
 docs={}
 for p in root.rglob('*.json'):
  if p.is_symlink():errors.append('symlink not allowed');continue
  try:docs[p.relative_to(root).as_posix()]=read(p)
  except Exception as e:errors.append(str(e))
 required=['branches.json','operations.json','source_conflicts.json','control_packages.json','layer_contract.json','coverage_matrix.json','analysis_contracts.json','netlist_contracts.json','lifecycle_contract.json','RELEASE_BOUNDARY.json','agent_visible.json','mock_contract.json']
 for f in required:ck(f in docs,'missing '+f)
 if errors:return errors
 bs=docs['branches.json']['branches'];ops=docs['operations.json']['operations'];opids={x['id'] for x in ops};ids={x['id'] for x in bs}
 ck(len(ids)==len(bs)==24,'branch inventory');ck(len(opids)==len(ops),'duplicate operation')
 routes={x['route_group_id'] for x in bs};ck(routes=={f'R{i:02}' for i in range(1,18)},'route group completeness')
 us={u['id'] for u in docs['unknown_parameters.json']['unknown_parameters']};cs={c['id'] for c in docs['source_conflicts.json']['conflicts']}
 ck(cs=={f'C{i:02}' for i in range(1,11)},'conflict inventory')
 for b in bs:
  ck(set(b['operation_ids'])<=opids,'invalid operation ref '+b['id']);ck(set(b['unknown_parameter_ids'])<=us,'invalid card ref '+b['id']);ck(set(b['conflict_ids'])<=cs,'invalid conflict ref '+b['id']);ck(set(b['depends_on'])<=ids,'invalid dependency '+b['id'])
  ck(b['physical_execution_implemented'] is False,'physical claim')
 for c in docs['source_conflicts.json']['conflicts']:ck(c['resolved'] is False and c['qualification_gate'] is True,'conflict gate weakened')
 layer=docs['layer_contract.json'];rows=layer['layers'];ck([x['index'] for x in rows]==list(range(1,73)),'layer sequence');ck(sum(x['role']=='interstack_buffer' for x in rows)==9,'buffer count');ck(rows[-1]['role']=='final_cap' and rows[-1]['source_thickness']==50 and rows[-1]['alternative_main_methods_interstack_nm'] is None,'final cap scope')
 cv=docs['coverage_matrix.json'];ck(len(cv['pages'])==62 and all(x['written_read'] is True for x in cv['pages']),'source read coverage');ck({x['pdf_page'] for x in cv['pages'] if x['source']=='main'}==set(range(1,10)),'main pages');ck({x['pdf_page'] for x in cv['pages'] if x['source']=='supplement'}==set(range(1,54)),'SI pages');ck(len(cv['figures'])==33 and len(cv['tables'])==6 and len(cv['sections'])==8,'SI inventory')
 cp={x['id']:x['source_constraints'] for x in docs['control_packages.json']['controls']};pairs=cp['PAIRS']['ordered_pairs'];ck(len(pairs)==90 and len({(x['driver'],x['load']) for x in pairs})==90 and all(x['driver']!=x['load'] for x in pairs),'ordered pairs');ck(cp['GATE_LEAKAGE']['source_drain_contacts_present'] is False,'gate-only contacts');ck(cp['SMALL']['full_ten_stack_demonstration'] is False,'small-device scope');ck(cp['LONG_TERM']['per_architecture_allocation'] is None,'long-term allocation invented')
 ck(cp['COUPLING']['selected_interpretation'] is None,'source coupling caption silently repaired');ck(cp['STACK']['selected_buffer_nm'] is None,'buffer default')
 rb=docs['RELEASE_BOUNDARY.json'];ck(all(rb[k] is False for k in ['real_actuation_implemented','physical_simulation_run','numerical_reproduction_run','source_complete_for_robot_execution','publisher_assets_included','external_writes_performed_by_task_author']),'release boundary')
 av=docs['agent_visible.json'];ck(av['source_outcomes_exposed'] is False and av['can_declare_measurement_success'] is False,'actor oracle exposure')
 for a in docs['analysis_contracts.json']['analyses']:ck(a['implementation_supplied'] is False and a['numerical_reproduction_performed'] is False,'analysis overclaim')
 for p in root.rglob('*'):
  if p.is_file() and p.suffix in ['.json','.md','.py']:
   text=p.read_text();ck(not re.search('[\u3400-\u9fff]',text),'non-English CJK text '+p.name);ck(('/'+'workspace/'+'shared/') not in text and ('/'+'workspace/'+'scratch/') not in text,'private source path export '+p.name)
 c,e=fixture(list(BRANCHES));r=validate(c,e);ck(r['accepted'],'all-branch fixture rejected')
 return errors
if __name__=='__main__':
 errors=verify();print(json.dumps({'passed':not errors,'errors':errors,'scope':'static design and synthetic fixture only'},indent=2));raise SystemExit(bool(errors))
