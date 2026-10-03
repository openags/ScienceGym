"""Original static design and synthetic bookkeeping validator. No physical model or device driver."""
import hashlib,json,math
from pathlib import Path
DOI='10.1038/s41467-021-27608-7'
PHYSICAL={'MACRO_SIGNAL','MEMORY_PREP','NORMAL_TEST','SMALL_TEST','MEMORY_TEST','ARRAY_PREP','NOR','NOT','OR','AND','DEFECT_ROUTING','VOLATILE_STORAGE','MECHANICAL_NOR','MESOSCALE_FAB'}
NONMANUAL={'FEM_MODEL','NAND','PLANAR_NOR','HALF_ADDER','LARGE_CROSSOVER','COMPACT_CROSSOVER','SR_LATCH','SEQUENTIAL_STRATEGY','PERFECT_ROUTING','ROLLER_ARRAY','MICROSCALE_MEMS','STORAGE_READ_REWRITE'}
REQUIRED=['operations.json','branches.json','provenance.json','unknown_parameters.json','coverage_matrix.json','nonmanual_scope.json','state_contract.json','lineage_contract.json','station_contracts.json','transport_routes.json','control_packages.json','episode_input_contract.json','agent_visible.json','evaluator_reference.json','source_access_audit.json','source_outcomes.json','source_conflicts.json','asset_needs.json','material_cards.json','design_assumptions.json','mock_contract.json','dependencies.json','STATUS.json','RELEASE_BOUNDARY.json']
class ContractError(ValueError):pass
def need(test,message):
 if not test:raise ContractError(message)
def unique(rows):
 ids=[r['id'] for r in rows];need(len(ids)==len(set(ids)),'duplicate ID');return set(ids)
def load_package(path):return {p.name:json.loads(p.read_text()) for p in Path(path).glob('*.json')}
def dag(nodes,edges):
 graph={n:[] for n in nodes}
 for a,b in edges:need(a in graph and b in graph,'unknown graph node');graph[a].append(b)
 def visit(n,stack,done):
  need(n not in stack,'dependency cycle')
  if n in done:return
  for m in graph[n]:visit(m,stack|{n},done)
  done.add(n)
 done=set()
 for n in nodes:visit(n,set(),done)
def validate_package(p):
 for f in REQUIRED:need(f in p,'missing '+f)
 for f,d in p.items():need(d.get('doi')==DOI,'wrong DOI '+f)
 status=p['STATUS.json'];audit=p['source_access_audit.json']
 for f in ['source_complete','complete_full_source_packet','physical_recipe_complete','scene_built','physical_simulation_run','robot_execution_run','scientific_replication_supported','public_write_performed']:need(status.get(f) is False,'unsupported readiness '+f)
 need(audit['source_complete'] is False and audit['complete_full_source_packet'] is False,'source promotion')
 need(audit['main']['panels']=='uninspected' and audit['movies']['contents']=='uninspected','unread source promotion')
 need('stopped' in audit['main']['pdf'] and 'no_retry' in audit['main']['pdf'],'access stop lost')
 ops=p['operations.json']['operations'];oi=unique(ops);need(len(ops)==p['operations.json']['operation_count'],'operation count')
 br=p['branches.json']['branches'];bi=unique(br);need(bi==PHYSICAL,'physical scope change');need(len(br)==p['branches.json']['branch_count'],'branch count')
 gates=unique(p['unknown_parameters.json']['unknowns']);evidence=set(p['provenance.json']['evidence']);stations=unique(p['station_contracts.json']['stations'])
 for u in p['unknown_parameters.json']['unknowns']:need(u['default'] is None and u['status']=='unresolved','invented unknown value')
 ob={o['id']:o for o in ops};bb={b['id']:b for b in br}
 for o in ops:
  for field in ['actions','target_asset_roles','preconditions','postconditions','observable_completion','failure_handling']:need(bool(o[field]),'empty operation '+field)
  need(o['location_id'] in stations|{'between_stations'},'unknown station');need(o['execution_mode']=='static_design_only','operation promoted')
  need(set(o['evidence_ids'])<=evidence,'unknown evidence');need(set(o['unknown_parameter_ids'])<=gates,'unknown gate')
 for b in br:
  need(set(b['terminal_operation_ids'])<=set(b['operation_ids']),'terminal membership lost');need(set(b['operation_ids'])<=oi,'unknown operation');need(set(b['source_evidence_ids'])<=evidence,'unknown branch evidence');need(set(b['required_branch_ids'])<=bi,'unknown prerequisite')
  local={g for i in b['operation_ids'] for g in ob[i]['unknown_parameter_ids']}
  need(local<=set(b['direct_unknown_parameter_ids']),'operation gate lost');need(set(b['unknown_parameter_ids'])<=gates,'unknown branch gate')
 dag(bi,[(r,b['id']) for b in br for r in b['required_branch_ids']])
 def closure(i):return set(bb[i]['direct_unknown_parameter_ids'])|set().union(*(closure(r) for r in bb[i]['required_branch_ids']))
 for b in br:need(closure(b['id'])<=set(b['unknown_parameter_ids']),'transitive gate lost')
 dag(oi,[(e['source'],e['target']) for e in p['dependencies.json']['edges']])
 for loop in p['dependencies.json']['loops']:need(loop['repeat_count'] is None and loop['empty_schedule_allowed'] is False,'invented repeat or empty success')
 nm=p['nonmanual_scope.json'];need(not nm['numerical_to_physical_promotion_allowed'],'numerical promotion');need(unique(nm['dispositions'])==NONMANUAL,'nonmanual omission')
 for x in nm['dispositions']:need(x['physical_branch_id'] is None and x['executed_here'] is False,'numerical executed')
 coverage=p['coverage_matrix.json'];need(len(coverage['physical_coverage'])==11,'physical coverage omission');need({x['id'] for x in coverage['nonmanual_coverage']}==NONMANUAL,'numerical coverage omission')
 need(set().union(*(set(x['branch_ids']) for x in coverage['physical_coverage']))==PHYSICAL,'uncovered physical branch')
 actor=p['agent_visible.json'];need(actor['public_file_allowlist']==['agent_visible.json'],'actor file leakage');need(set(actor)=={'schema_version','doi','visibility','public_file_allowlist','public_inputs','excluded','actor_goal','runtime_loader'},'actor hidden-answer field')
 need(not any(x.endswith('.json') for x in actor['public_inputs']),'actor document leakage')
 state=p['state_contract.json'];need(state['switch']==dict(maximum_active_rows=3,initial_active_rows=0,store_active_rows=2),'switch semantics changed');need(state['volatile_storage']['pair_size']==2 and state['volatile_storage']['hold_requires_continuous_excitation'],'volatile semantics changed')
 need(state['signal']['type']=='monostable' and state['instruction_memory']['type']=='bistable','memory type collapse')
 out=p['source_outcomes.json'];need(out['numerical_cases']['NAND']['hardware_setting'] is False and out['numerical_cases']['NOR_model']['hardware_setting'] is False,'FEM force promoted')
 need(out['numerical_cases']['LARGE_CROSSOVER']['elements']==176 and out['numerical_cases']['COMPACT_CROSSOVER']['elements']==25,'crossovers merged')
 need(out['numerical_cases']['SR_LATCH']['invalid_input']==[1,1],'latch invalid input hidden')
 for route in p['transport_routes.json']['routes']:need(route['geometry'] is None,'invented transport geometry');need(route['source_station'] in stations and route['target_station'] in stations,'transport station')
 for a in p['asset_needs.json']['assets']:need(a['readiness']=='not_built' and a['geometry'] is None,'asset promotion')
 return dict(operations=len(ops),physical_routes=len(br),nonmanual=len(NONMANUAL),gates=len(gates))

def validate_record(r,c,allow_synthetic=False):
 """Validate consistency only. Context dictionaries do not authenticate instruments."""
 required=['record_id','branch_id','case_id','attempt_id','specimen_ids','assembly_revision','program_revision','setup_revision','calibration_id','reset_receipt_id','raw_sha256','timestamp_utc','data_class','quality','synthetic_fixture','receipt_id']
 for key in required:need(key in r,'missing '+key)
 need(r['synthetic_fixture'] is True and allow_synthetic,'this checker only certifies synthetic bookkeeping')
 need(r['data_class']=='synthetic_observation','wrong data class');need(r['branch_id'] in PHYSICAL,'not a physical branch')
 need(r['quality']=='accepted','nonaccepted record');need(r['specimen_ids'] and len(r['specimen_ids'])==len(set(r['specimen_ids'])),'empty/duplicate specimens')
 for s in r['specimen_ids']:need(c['objects'].get(s)==r['assembly_revision'],'missing/stale specimen revision');need(s not in c.get('quarantined',[]),'quarantined specimen')
 need(r['program_revision']==c.get('current_program_revision'),'stale program revision')
 need(r['setup_revision']==c.get('current_setup_revision'),'stale setup revision')
 need(r['calibration_id'] in c['calibrations'] and c['calibrations'][r['calibration_id']]==r['setup_revision'],'stale calibration')
 need(isinstance(r['raw_sha256'],str) and len(r['raw_sha256'])==64 and all(x in '0123456789abcdef' for x in r['raw_sha256']),'invalid raw hash')
 receipt=c['receipts'].get(r['receipt_id']);need(receipt is not None,'missing receipt')
 for k in required:need(receipt.get(k)==r[k],'receipt mismatch '+k)
 need(receipt.get('limits_respected') is True,'unsafe event')
 need(r['record_id'] not in c['previous_records'],'record overwrite')
 if r.get('predecessor_id'):
  old=c['previous_records'].get(r['predecessor_id']);need(old is not None and old['attempt_id']!=r['attempt_id'],'retry lost predecessor/new identity')
 reset=c['resets'].get(r['reset_receipt_id']);need(reset is not None,'reset missing')
 need(reset['case_id']==r['case_id'] and reset['attempt_id']==r['attempt_id'] and reset['verified_zero'] is True and reset['setup_revision']==r['setup_revision'],'stale or failed reset')
 if r['branch_id'] in {'NOR','NOT','OR','AND','MECHANICAL_NOR'}:
  arity=1 if r['branch_id']=='NOT' else 2
  need(len(r.get('input_bits',[]))==arity and all(type(x) is int and x in (0,1) for x in r['input_bits']),'invalid input bits')
  need(r.get('observed_input_bits')==r['input_bits'],'actual input mismatch')
  need(type(r.get('output_bit')) is int and r['output_bit'] in (0,1),'ambiguous output')
  need(r.get('input_event_index',1)<r.get('output_event_index',0),'output before inputs')
  need(r.get('mask_verified') is True,'mask not verified')
  need(r.get('excitation_origin')=='hardware_qualification_card','FEM excitation promoted')
  if r['branch_id']!='MECHANICAL_NOR':
   need(bool(r.get('row_events')),'missing row history')
   for e in r['row_events']:need(len(e['active_rows'])<=3 and len(e['active_rows'])==len(set(e['active_rows'])) and e['within_limits'] is True,'invalid active row event')
   need(receipt.get('row_events')==r['row_events'],'row receipt mismatch')
  for k in ['input_bits','observed_input_bits','output_bit','input_event_index','output_event_index','mask_verified','excitation_origin']:need(receipt.get(k)==r[k],'logic receipt mismatch')
 if r['branch_id']=='VOLATILE_STORAGE':
  need(set(r.get('storage_pair_ids',[]))<=set(r['specimen_ids']),'storage identities missing from lineage')
  need(len(r.get('storage_pair_ids',[]))==2 and len(set(r['storage_pair_ids']))==2,'not two storage elements')
  need(len(r.get('storage_rows',[]))==2 and abs(r['storage_rows'][0]-r['storage_rows'][1])==1,'rows not adjacent')
  need(r.get('baseline_phase')=='post_write_pre_upstream_release','incorrect retention baseline')
  need(r.get('baseline_hold_epoch')==r.get('hold_epoch') and r.get('hold_epoch') is not None,'wrong hold epoch')
  continuity=r.get('hold_continuity_receipt');need(isinstance(continuity,dict) and continuity.get('hold_epoch')==r['hold_epoch'] and continuity.get('uninterrupted') is True and continuity.get('rows')==r['storage_rows'],'no continuous two-row hold evidence')
  need(continuity.get('coverage')=='post_write_through_after_read' and continuity.get('source')=='event_stream','incomplete hold interval evidence')
  need(receipt.get('hold_continuity_receipt')==continuity,'hold continuity receipt mismatch')
  samples=r.get('hold_samples',[]);need(bool(samples),'no hold observations')
  for x in samples:need(x['rows']==r['storage_rows'] and x['powered'] is True and x['within_limits'] is True,'interrupted/unsafe hold')
  need(r.get('upstream_released') is True,'upstream not released')
  for bits in [r.get('before_pair'),r.get('after_pair')]:need(isinstance(bits,list) and len(bits)==2 and all(type(x) is int and x in (0,1) for x in bits),'ambiguous pair')
  for k in ['storage_pair_ids','storage_rows','baseline_phase','baseline_hold_epoch','hold_epoch','hold_samples','upstream_released','before_pair','after_pair']:need(receipt.get(k)==r[k],'storage receipt mismatch')
 need(r.get('custody_receipt_id') in c['custody'],'missing custody')
 return True

def validate_transport(t,c):
 need(bool(t.get('payload_ids')) and len(t['payload_ids'])==len(set(t['payload_ids'])),'empty/duplicate payload')
 for k in ['supported','outputs_isolated','tethers_released','path_qualified','destination_verified','post_transport_integrity']:need(t.get(k) is True,'transport fails '+k)
 for x in t['payload_ids']:need(c.get(x)==t['origin'],'origin custody mismatch')
 need(t['origin']!=t['destination'],'same-station transport');return True

def validate_coverage(selected,schedules,records,gates,p,c,allow_synthetic=False):
 need(bool(selected) and len(selected)==len(set(selected)),'empty/duplicate selection');need(set(selected)<=PHYSICAL,'invalid route selection')
 bb={b['id']:b for b in p['branches.json']['branches']}
 ids=[]
 for b in selected:
  need(bool(schedules.get(b)),'empty schedule')
  need(len(schedules[b])==len(set(schedules[b])),'duplicate case schedule')
  required_bits=bb[b]['conditions'].get('required_input_cases')
  if required_bits is not None:
   need(len(schedules[b])>=len(required_bits),'incomplete truth table schedule')
  for g in bb[b]['unknown_parameter_ids']:need(gates.get(g) is True,'unresolved gate '+g)
  rr=[r for r in records if r['branch_id']==b]
  need({r['case_id'] for r in rr}==set(schedules[b]),'missing or extra condition')
  if required_bits is not None:need({tuple(r.get('input_bits',[])) for r in rr}=={tuple(bits) for bits in required_bits},'truth input coverage mismatch')
  for r in rr:validate_record(r,c,allow_synthetic=allow_synthetic);ids.append(r['record_id'])
 need(len(ids)==len(set(ids)),'duplicate record')
 # Route-level completion excludes prerequisite preparation unless current receipts prove it.
 for b in selected:
  for required in bb[b]['required_branch_ids']:need(required in c.get('qualified_handoffs',[]),'missing preparation handoff')
 need(c.get('cleanup_verified') is True,'cleanup missing');return True

def validate_export(root,p):
 root=Path(root);allow=p['EXPORT_ALLOWLIST.json'];files=allow['files'];need(len(files)==len(set(files)),'duplicate allowlist')
 actual={str(x.relative_to(root)) for x in root.rglob('*') if x.is_file()};need(actual==set(files),'unlisted or missing file')
 for name in files:
  path=Path(name);need(not path.is_absolute() and '..' not in path.parts,'unsafe allowlist path');need(path.suffix in {'.json','.md','.py'},'source/binary export')
  if name not in {'EXPORT_ALLOWLIST.json','VERIFICATION.json'}:need(hashlib.sha256((root/name).read_bytes()).hexdigest()==allow['payload_sha256'].get(name),'hash drift '+name)
 return True
