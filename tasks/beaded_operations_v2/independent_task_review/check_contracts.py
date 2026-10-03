import json,pathlib,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def load(n):return json.loads((ROOT/n).read_text())
D={n:load(n+'.json') for n in ['operations','branches','routes','provenance','unknown_parameters','station_contracts','source_conflicts','source_access_audit','RELEASE_BOUNDARY','episode_input_contract','lineage_contract']}
O={x['id']:x for x in D['operations']['operations']};B={x['id']:x for x in D['branches']['branches']};R={x['id']:x['tree'] for x in D['routes']['routes']};E={x['id'] for x in D['provenance']['evidence']};U={x['id'] for x in D['unknown_parameters']['unknown_parameters']};S={x['id'] for x in D['station_contracts']['stations']}|set(D['station_contracts']['dynamic_stations'])
def nodes(x):
 if isinstance(x,dict):
  yield x
  for y in x.values():yield from nodes(y)
 elif isinstance(x,list):
  for y in x:yield from nodes(y)
def ops(t):return [n for n in nodes(t) if n.get('type')=='operation']
def seq(t):return [n['operation_id'] for n in ops(t)]
checks=[]
def check(n,ok):checks.append({'check':n,'passed':bool(ok)})
check('Unique operation/branch/route IDs',len(O)==D['operations']['operation_count'] and len(B)==D['branches']['branch_count'] and set(B)==set(R))
check('All operation evidence and gate references resolve',all(set(o['evidence_ids'])<=E and set(o['unknown_parameter_ids'])<=U for o in O.values()))
check('All fixed/dynamic operation workstation references resolve',all(o['location_id'] in S and o['source_workstation'] in S and o['target_workstation'] in S for o in O.values()))
check('All route operation IDs resolve',all(n['operation_id'] in O for t in R.values() for n in ops(t)))
check('Hands-on robot grounding nonempty',all(all(o.get(k) for k in ['actor','actions','manipulated_objects','tools','preconditions','postconditions','success_evidence']) for o in O.values() if o['kind']=='hands_on'))
check('Device process has robot setup/unload mapping',all(o.get('device_handoff') and o['device_handoff']['robot_setup'] in O and o['device_handoff']['robot_unload'] in O for o in O.values() if o['kind']=='device_process'))
check('Weaving has actual component manipulations',all(x in O for x in ['STAGE','PART_QC','THREAD_PREP','BEAD_ALIGN','THREAD_PASS','LOOP_SEAT','WEAVE_AUDIT']))
check('Every leaf route requires part-origin accounting',all(any(n.get('loop_id')=='required_prepared_parts' for n in nodes(t)) for rid,t in R.items() if rid!='WHOLE_PAPER_PRACTICAL'))
check('Supplied objects cannot claim robot preparation credit',all('does not earn' in n.get('semantics','') for t in R.values() for n in nodes(t) if n.get('type')=='choice' and 'qualified_supplied_part' in n.get('alternatives',{})))
check('Drilled acetal stock is a required role','acetal_bead_lots_with_matched_drilled_holes' in B['SHELL_SIZE_CONTROL']['required_preparation_roles'])
check('SMA program is before connection/state/bending',all(seq(R['SMA_BEAM_BENDING']).index('SMA_PROGRAM')<seq(R['SMA_BEAM_BENDING']).index(x) for x in ['SMA_CONNECT','SMA_STATE','SMA_BEND']))
check('SMA touch requires explicit off and cool receipts',{'power_off_confirmed','cool_state_confirmed'}<=set(O['SMA_DISCONNECT']['preconditions']))
state=next(n for n in nodes(R['SMA_BEAM_BENDING']) if n.get('loop_id')=='state_cycles')
check('SMA counts allocated by cycle IDs rather than multiplied per beam',state.get('values') is None and 'cycle_ids' in state.get('values_from','') and 'campaign' in B['SMA_BEAM_BENDING']['source_condition_constraints']['cycle_total_scope'])
ax=next(n for n in nodes(R['THREAD_MODULUS']) if n.get('loop_id')=='axial_trials')
check('Axial trials use assigned coupon/spacing IDs',ax.get('values') is None and 'axial_trial_ids' in ax.get('values_from',''))
fr=next(n for n in ops(R['FIXED_RING_FRICTION']) if n['operation_id']=='PULLEY_ROUTE')['bindings']
check('Friction end roles are one mass and one tester',fr.get('hanging_mass_end_count')==1 and fr.get('end_role_map')=={'A':'hanging_mass_via_pulley','B':'tester_sensor_grip_via_pulley'})
check('Shell role has two independently identified hanging masses',all(next(n for n in ops(R[r]) if n['operation_id']=='PULLEY_ROUTE')['bindings'].get('hanging_mass_end_count')==2 for r in ['SHELL_NITINOL','SHELL_NYLON']))
ch=next(n for n in nodes(R['CHAIN_DILATION']) if n.get('loop_id')=='chain_cells')
check('Mechanical chain is source ordered with three cycles per ring',ch.get('values')==list(range(1,16)) and ch.get('order')=='ascending_from_free_end_required' and any(n.get('loop_id')=='cycles' and n.get('values')==[1,2,3] for n in nodes(ch)))
check('CT eight-cell chain is not the mechanical fifteen-cell chain',B['CT_CHAIN8']['source_condition_constraints']['cells']==8 and B['CHAIN_DILATION']['source_condition_constraints']['cells']==15)
check('CT service hands back physical custody',all(all(x in seq(R[r]) for x in ['CT_MOUNT','CT_STATE','CT_HANDOFF','CT_SCAN','CT_RECEIVE']) for r in ['CT_SHELL','CT_RINGS','CT_CHAIN8','CT_COLUMN_STATES']))
check('Whole-paper dispatcher names exactly the leaf routes',set(R['WHOLE_PAPER_PRACTICAL']['selected_branch_ids'])==set(R)-{'WHOLE_PAPER_PRACTICAL'})
check('Known conflicts and unavailable table evidence preserved',len(D['source_conflicts']['conflicts'])>=7 and 'not recovered' in D['source_access_audit']['main']['tables_1_2'])
check('No source-byte or robot-feasibility validation invented',all(not s['locally_byte_complete'] and s['current_source_sha256'] is None for s in D['provenance']['sources']) and all(not any(o['feasibility'].values()) for o in O.values()))
check('Actor projection excludes reference routes and outcomes',{'operations.json','routes.json','source_outcomes.json'}<=set(D['RELEASE_BOUNDARY']['withhold']) and not D['RELEASE_BOUNDARY']['runtime_loader_implemented'])
check('Part preparation does not use sample alias before sample allocation',all('$sample_or_stock_id' not in json.dumps(n['body']) for t in R.values() for n in nodes(t) if n.get('loop_id')=='required_prepared_parts'))
check('Analysis handoffs preserve physical sample location',all(o.get('physical_sample_transfer') is False and 'preserve_last_physical_sample_location' in o.get('location_semantics','') for o in O.values() if o['kind']=='analysis'))
res={'scope':'Independent source-bounded task-design structure and typed-route review only; not execution, physics or real device-safety validation.','passed':sum(c['passed'] for c in checks),'total':len(checks),'checks':checks,'reviewed_file_sha256':{n+'.json':hashlib.sha256((ROOT/(n+'.json')).read_bytes()).hexdigest() for n in D}}
(ROOT/'independent_task_review/contract_check_results.json').write_text(json.dumps(res,indent=2));print(json.dumps({'passed':res['passed'],'total':res['total'],'failures':[c['check'] for c in checks if not c['passed']]},indent=2));raise SystemExit(not all(c['passed'] for c in checks))
