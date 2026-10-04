"""Static structural checks; no source/hardware/data validation implied."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
def read(n):return json.loads((ROOT/n).read_text())
def verify(root=ROOT):
 root=Path(root);checks=[]
 def load(n):return json.loads((root/n).read_text())
 def ck(name,value):
  if not value:raise ValueError(name)
  checks.append(name)
 o=load('operations.json')['operations'];r=load('branches.json')['branches'];a=load('asset_binding_plan.json');e=load('evidence_map.json')['records'];c=load('source_conflicts.json')['conflicts'];u=load('unknown_parameters.json')['unknowns']
 op={x['id']:x for x in o};routes={x['id']:x for x in r};ev={x['id'] for x in e};assets={x['asset_id']:x for x in a['assets']};anchors={x['asset_id']+'.'+k for x in a['assets'] for k in x['required_anchor_ids']}
 ck('16 exact routes',set(routes)=={f'R{i:02}' for i in range(16)})
 ck('74 unique operations',len(o)==len(op)==74)
 ck('exact operation identity set',set(op)=={f'R{i:02}_O{j:02}' for i,n in enumerate([4,5,4,4,5,5,5,4,4,6,4,6,4,5,5,4]) for j in range(1,n+1)})
 ck('12 assets and 61 anchors',len(assets)==12 and len(anchors)==61)
 ck('16 source evidence records',len(ev)==16)
 ck('10 cautions retained',len(c)==10 and {x['id'] for x in c}=={f'C{i:02}' for i in range(1,11)})
 ck('25 missing inputs retained',len(u)==25 and {x['id'] for x in u}=={f'U{i:02}' for i in range(1,26)})
 ck('every source referenced',set().union(*(set(x['source_evidence_ids']) for x in r))==ev)
 ck('exact route ownership',all([x['id'] for x in o if x['route_id']==b['id']]==b['route_operation_ids'] for b in r))
 ck('every operation source linked',all(set(x['source_evidence_ids'])<=ev and x['source_evidence_ids'] for x in o))
 ck('every operation authored',all(x['step_origin']=='independently_authored_robot_task_design' and x['source_is_robot_protocol'] is False and x['physical_implemented'] is False for x in o))
 ck('no actor observation authority',all(x['actor_event_fields']==['event_id','operation_id','evidence_id'] for x in o))
 ck('every operation asset bound',len(a['operation_bindings'])==74 and {x['operation_id'] for x in a['operation_bindings']}==set(op))
 ck('bindings match operation contract',all(b['anchor_ids']==op[b['operation_id']]['anchor_ids'] and b['asset_id'] in op[b['operation_id']]['asset_ids'] and b['guard_ids']==op[b['operation_id']]['guard_ids'] for b in a['operation_bindings']))
 ck('all bound anchors exist',all(set(b['anchor_ids'])<=anchors for b in a['operation_bindings']))
 ck('all required anchors used',set().union(*(set(b['anchor_ids']) for b in a['operation_bindings']))==anchors)
 ck('all guards defined',all(set(b['guard_ids'])<=set(a['guard_definitions']) for b in a['operation_bindings']))
 ck('physical geometry never qualified',all(x['physical_geometry_validated'] is False for x in a['assets']))
 ck('conflicts map to real operations',all(x['operation_ids'] and set(x['operation_ids'])<=set(op) and x['scope_tags'] for x in c))
 ck('conflict backlinks exact',all(set(x['conflict_ids'])=={k['id'] for k in c if x['id'] in k['operation_ids']} for x in o))
 ck('qualification backlinks exact',all(set(x['unknown_ids'])=={k['id'] for k in u if x['id'] in k['operation_ids']} for x in o))
 ck('operation materials scoped to route',all(x['material_ids'] and set(x['material_ids'])<=set(routes[x['route_id']]['material_ids']) for x in o))
 ck('detection limit material isolated',op['R11_O06']['material_ids']==['PDMS_30:1'] and op['R11_O05']['material_ids']==['CY_5:6','CY_9:10'])
 ck('mandatory control guards',all({'G_AUTHORITY','G_LINEAGE','G_QUALIFICATION','G_SOURCE_SCOPE','G_SCALE','G_NO_CONTROL'}<=set(x['guard_ids']) for x in o))
 ck('unknowns map to real operations',all(x['safe_closeout_exception'] is True and set(x['operation_ids'])<=set(op) for x in u))
 ck('safe closeout never blocked',all(not x['conflict_ids'] and not x['unknown_ids'] and not x['requires_route_outputs_from'] for x in o if x['route_id']=='R15'))
 ck('all failure edges retained',len(load('lifecycle_contract.json')['failure_edges'])==16 and all(x['closeout_reachable_on_abort'] for x in r))
 visiting=set();done=set()
 def visit(n):
  if n in visiting:raise ValueError('route cycle')
  if n in done:return
  visiting.add(n)
  for d in routes[n]['depends_on']:ck('valid dependency '+n+' '+d,d in routes);visit(d)
  visiting.remove(n);done.add(n)
 for n in routes:visit(n)
 ck('DAG all routes',len(done)==16)
 ck('coverage includes each route',set().union(*(set(x['routes']) for x in load('coverage_matrix.json')['coverage']))==set(routes))
 ck('actor has no outcomes',load('agent_visible.json')['source_outcomes_exposed'] is False and load('agent_visible.json')['can_declare_observation'] is False)
 ck('actor only visible file',load('evaluator_reference.json')['actor_visible_allowlist']==['agent_visible.json'])
 scope=load('RELEASE_BOUNDARY.json');ck('zero execution scope',scope['validated_runnable_whole_paper_tasks']==0 and all(scope[k] is False for k in ('whole_paper_execution_complete','physical_execution','physical_simulation','scientific_reproduction','source_files_exported','exact_geometry_validated')))
 audit=load('source_access_audit.json');ck('movie sampled honestly',audit['VIDEO']['sampled_seconds']==[0,10,20,30,40,50]);ck('workbook cells unread',audit['SOURCE_DATA']['numeric_cells_read'] is False and audit['SOURCE_DATA']['raw_data_reanalysis'] is False)
 ck('written SI read',audit['SI']['written_pages_read']==list(range(1,16)))
 ck('separate detection-limit branch',any('PDMS30' in x['required_record_type'] for x in o if x['route_id']=='R11'))
 ck('source-only receding reference', 'source_only' in op['R09_O06']['required_record_type'])
 ck('P1 separate fit preserved','P1_and_Ur_Uz' in op['R14_O03']['required_record_type'])
 ck('hazardous route external only',routes['R07']['kind']=='external_service_only' and load('nonmanual_scope.json')['all_services_unimplemented'] is True)
 return {'passed':True,'check_count':len(checks),'checks':checks,'physical_execution':False,'scientific_reproduction':False}
if __name__=='__main__':
 try:print(json.dumps(verify(),indent=2))
 except (ValueError,KeyError) as e:print(str(e));sys.exit(1)
