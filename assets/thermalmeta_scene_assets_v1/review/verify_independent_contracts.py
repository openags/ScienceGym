"""Independent paired-contract and source-boundary checks; expects sibling accepted packages."""
import json,pathlib,hashlib,ast
P=pathlib.Path(__file__).resolve().parents[1];A=P.parent/'next-experimental-review-20261005';T=P.parent/'thermalmeta_operations_v2'
def read(p):return json.loads(p.read_text())
C=read(P/'scene_binding_contract.json');R={'scope':'Accepted source-review snapshots and paired static task/asset consistency','checks':[]}
def check(name,value,detail=None):R['checks'].append({'name':name,'passed':bool(value),'detail':detail})
for f in ['source_facts','source_conflicts','unknown_inputs','asset_requirements','station_contracts','coverage_map','route_proposal']:
 check('accepted_snapshot_'+f,read(P/(f+'_snapshot.json'))==read(A/(f+'.json')))
check('exact_paired_binding_contract',C==read(T/'scene_binding_contract.json'))
check('exact_20_stage_ids',{x['stage_id'] for x in C['stage_bindings']}=={f'P{i:02}' for i in range(1,21)} and len(C['stage_bindings'])==20)
check('exact_10_asset_ids',{x['asset_id'] for x in C['assets']}=={f'A{i:02}' for i in range(1,11)} and len(C['assets'])==10)
check('exact_25_anchor_ids',len(C['anchors'])==len({x['anchor_id'] for x in C['anchors']})==25)
source_stages=read(A/'route_proposal.json')['stages'];operations=read(T/'operations.json')['stages']
check('accepted_route_order_and_titles',[(x['stage_id'],x['title']) for x in C['stage_bindings']]==[(x['id'],x['title']) for x in source_stages])
check('paired_operation_scene_bindings',all(o['scene_anchor_id']==s['anchor_id'] and set(o['scene_asset_ids'])==set(s['asset_ids']) and not o['commands_enabled'] for o,s in zip(operations,C['stage_bindings'])))
assets={x['asset_id'] for x in C['assets']};anchors={x['anchor_id']:x for x in C['anchors']};stages={x['stage_id'] for x in C['stage_bindings']}
check('all_stages_bound_to_valid_assets_and_anchors',all(set(s['asset_ids'])<=assets and s['anchor_id'] in anchors and anchors[s['anchor_id']]['asset_id'] in s['asset_ids'] for s in C['stage_bindings']))
b=read(P/'branch_asset_coverage.json');cov=read(A/'coverage_map.json');expected={x['id'] for k in ['families','child_branches'] for x in cov[k]}
check('all_24_source_branches_bound',len(b['branch_bindings'])==24 and {x['branch_id'] for x in b['branch_bindings']}==expected)
check('branch_references_exist_and_remain_unrun',all(set(x['asset_ids'])<=assets and set(x['anchor_ids'])<=set(anchors) and set(x['stage_ids'])<=stages and x['executed'] is False and x['scientific_results_present'] is False for x in b['branch_bindings']))
reverse={a:[x['branch_id'] for x in b['branch_bindings'] if a in x['asset_ids']] for a in assets}
check('branch_reverse_map_consistent',reverse==b['reverse_asset_bindings'])
check('preparation_asset_explicitly_covered',b['additional_preparation_assets']==['A03'])
check('default_hold_no_hardware_no_physics',C['default_state']=='HOLD_UNQUALIFIED' and all(C[k] is False for k in ['physical_actuation_enabled','hardware_commands_allowed','physics_simulation_performed','geometry_interface_qualified']))
check('all_9_source_conflicts_held',len(read(P/'source_conflicts_snapshot.json'))==9 and all(x['resolved'] is False for x in read(P/'source_conflicts_snapshot.json')))
check('all_13_unknowns_not_invented',len(read(P/'unknown_inputs_snapshot.json'))==13 and all(x['may_be_invented'] is False for x in read(P/'unknown_inputs_snapshot.json')))
check('nominal_source_envelope_mm',C['source_dimensions_nominal_mm']==[120,120,4.5])
conds=C['condition_views'];check('six_views_three_shared_synthetic_specimens',len(conds)==6 and len({x['specimen_id'] for x in conds})==3 and all(len({x['specimen_id'] for x in conds if x['sample_family_id']==f})==1 and {x['orientation'] for x in conds if x['sample_family_id']==f}=={'X','Y'} for f in {x['sample_family_id'] for x in conds}))
check('profile_number_mapping_explicitly_authored',all(x['profile_number_to_orientation_status']=='authored_visual_selector_not_source_verified' for x in conds) and 'not an independently verified' in C['profile_mapping_boundary'])
controls=read(P/'static_controls.json');check('no_runtime_adapter_or_telemetry',controls['hardware_adapter'] is None and controls['network_transport'] is None and controls['actuator_commands']==[] and all(v is None for v in controls['default_telemetry'].values()))
pro=read(P/'provenance.json')['original_authorship'];check('original_art_and_no_source_code_geometry_or_physics',all(pro[k] is False for k in ['source_CAD_or_masks_used','publisher_figures_or_frames_used','scientific_code_used','physics_run']))
tree=ast.parse((P/'scene_guards.py').read_text());mods={x.names[0].name.split('.')[0] for x in ast.walk(tree) if isinstance(x,ast.Import)}|{x.module.split('.')[0] for x in ast.walk(tree) if isinstance(x,ast.ImportFrom)}
check('guard_uses_only_local_metadata_imports',mods<={'json','pathlib','sys'},sorted(mods))
check('no_guard_dynamic_execution_or_io_calls',not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in {'exec','eval','compile','__import__','open'} for n in ast.walk(tree)))
R['passed']=all(x['passed'] for x in R['checks']);R['passed_check_count']=sum(x['passed'] for x in R['checks']);R['total_check_count']=len(R['checks']);R['guard_sha256']=hashlib.sha256((P/'scene_guards.py').read_bytes()).hexdigest();R['binding_contract_sha256']=hashlib.sha256((P/'scene_binding_contract.json').read_bytes()).hexdigest()
(P/'review/independent_contract_audit.json').write_text(json.dumps(R,indent=2)+'\n');print(json.dumps({'passed':R['passed'],'checks':len(R['checks']),'failures':[x['name'] for x in R['checks'] if not x['passed']]}))
if not R['passed']:raise SystemExit(1)
