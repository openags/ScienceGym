"""Original static and synthetic-bookkeeping checks. Not a physics/robot engine."""
import copy
import json
import math
import pathlib
import re

DOI = '10.1038/ncomms6553'
SCHEMA = 'acoustic_wavefront_paper_task.v1'
MEASUREMENT_BRANCHES = {'NORMAL_INCIDENCE','BANDWIDTH','OBLIQUE_SWEEP','RADIATION_PATTERNS','NEAR_FIELD','NEGATIVE_REFRACTION'}
class ContractError(ValueError):
    pass

def require(value, message):
    if not value:
        raise ContractError(message)

def nonempty(value):
    return isinstance(value, str) and bool(value.strip())

def ids(items, label):
    result = [x['id'] for x in items]
    require(len(result) == len(set(result)), 'duplicate ' + label)
    return set(result)

def load_package(root):
    return {p.name: json.loads(p.read_text()) for p in pathlib.Path(root).glob('*.json')}

def validate_package(d):
    required = {'operations.json','branches.json','provenance.json','unknown_parameters.json','dependencies.json','transport_routes.json','station_contracts.json','nonmanual_scope.json','coverage_matrix.json','source_outcomes.json','agent_visible.json','evaluator_reference.json','episode_input_contract.json','lineage_contract.json','STATUS.json','source_conflicts.json','mock_contract.json','state_contract.json'}
    require(required <= d.keys(), 'missing contract file')
    for name, data in d.items():
        if name not in {'EXPORT_ALLOWLIST.json','VERIFICATION.json'}:
            require(data.get('doi') == DOI and data.get('schema_version') == SCHEMA, 'identity/schema: ' + name)
    ops = d['operations.json']['operations']; bs = d['branches.json']['branches']
    op_ids = ids(ops, 'operation'); branch_ids = ids(bs, 'branch')
    ev_ids = set(d['provenance.json']['evidence'])
    unknowns = d['unknown_parameters.json']['unknowns']; unknown_ids = ids(unknowns, 'unknown')
    stations = ids(d['station_contracts.json']['stations'], 'station')
    require(d['operations.json']['operation_count'] == len(ops), 'operation count')
    require(d['branches.json']['branch_count'] == len(bs), 'branch count')
    require(len(unknowns) == 15 and all(u['default'] is None for u in unknowns), 'invented unknown default')
    require(all(c['defaults'] is None and c['unknown_id'] in unknown_ids and c['required_fields'] for c in d['episode_input_contract.json']['cards']), 'input card gate')
    for op in ops:
        require(op['kind'] in {'hands_on','transport','device_autonomous','analysis'}, 'operation kind')
        require(op['location_id'] in stations | {'between_stations'}, 'operation station')
        require(set(op['evidence_ids']) <= ev_ids, 'operation evidence')
        require(set(op['unknown_parameter_ids']) <= unknown_ids, 'operation unknown')
        for k in ['preconditions','actions','postconditions','target_asset_roles']:
            require(op[k] and all(nonempty(x) for x in op[k]), 'empty operation ' + k)
        require(nonempty(op['failure_handling']) and nonempty(op['observable_completion']), 'missing observable/failure contract')
        require(op['execution_mode'] == 'static_design_only', 'execution promotion')
    for b in bs:
        require(b['operation_ids'] and set(b['operation_ids']) <= op_ids, 'branch operations')
        require(set(b['source_evidence_ids']) <= ev_ids and set(b['unknown_parameter_ids']) <= unknown_ids, 'branch source/gate')
        require(set(b['required_branch_ids']) <= branch_ids and b['id'] not in b['required_branch_ids'], 'branch dependency')
    op_map={o['id']:o for o in ops}
    for b in bs:
        own={u for oid in b['operation_ids'] for u in op_map[oid]['unknown_parameter_ids']}
        require(own <= set(b['direct_unknown_parameter_ids']) <= set(b['unknown_parameter_ids']), 'branch operation gate omitted')
        for parent in b['required_branch_ids']:
            pb=next(x for x in bs if x['id']==parent)
            require(set(pb['unknown_parameter_ids']) <= set(b['unknown_parameter_ids']), 'prerequisite gate omitted')
    require('dimensional_accepted' in op_map['ASM_LAYOUT']['preconditions'], 'dimensional acceptance bypass')
    require('array_revision_qualified' not in op_map['ASM_QC']['postconditions'], 'unconditional array acceptance')
    require('cell_acceptance_recorded' not in op_map['PART_CHANNEL']['postconditions'], 'unconditional cell acceptance')
    require('scan_complete' in op_map['FFT']['preconditions'], 'partial grid promoted')
    for name,state in [('PART_DIM','dimensional_accepted'),('PART_CHANNEL','cell_acceptance_recorded'),('CAL_REVIEW','calibration_valid'),('GRID_FAR','next_point_selected'),('SCAN_COMMIT','records_committed'),('ANGLE_FIT','derived_results_available')]:
        require(any(x['produce']==state for x in op_map[name].get('conditional_postconditions',[])), 'missing conditional state bridge')
    graph = {b['id']: b['required_branch_ids'] for b in bs}
    def visit(n, path):
        require(n not in path, 'branch dependency cycle')
        for p in graph[n]: visit(p, path | {n})
    for n in graph: visit(n, set())
    dependency_graph = {o: [] for o in op_ids}
    for e in d['dependencies.json']['edges']:
        require(e['source'] in op_ids and e['target'] in op_ids, 'operation dependency reference')
        dependency_graph[e['source']].append(e['target'])
    def visit_op(n, path):
        require(n not in path, 'operation dependency cycle')
        for nxt in dependency_graph[n]: visit_op(nxt, path | {n})
    for n in op_ids: visit_op(n, set())
    loops = d['dependencies.json']['loops']; ids(loops, 'loop')
    require(len(loops) == 7 and all(l['repeat_count'] is None and set(l['operation_ids']) <= op_ids for l in loops), 'loop default/reference')
    for r in d['transport_routes.json']['routes']:
        require(r['from_station'] in stations and r['to_station'] in stations, 'transport station')
        require(r['operation_id'] == 'MOVE' and r['geometry'] is None and r['payload_roles'], 'transport contract')
    coverage = d['coverage_matrix.json']
    require({c['branch_id'] for c in coverage['physical_coverage']} == branch_ids, 'physical coverage omission')
    for c in coverage['physical_coverage']:
        b = next(b for b in bs if b['id'] == c['branch_id'])
        require(c['operation_ids'] == b['operation_ids'], 'coverage drift')
    numbers = d['nonmanual_scope.json']['items']; nids = ids(numbers, 'numerical')
    require({c['id'] for c in coverage['nonmanual_coverage']} == nids, 'numerical coverage omission')
    require(len(numbers) == 8 and not d['nonmanual_scope.json']['numerical_to_physical_promotion_allowed'], 'numerical promotion')
    require(all(n['classification'] == 'numerical_or_theoretical_only' and n['disposition'] == 'specified_not_run' and not n['operation_ids'] and set(n['evidence_ids']) <= ev_ids for n in numbers), 'numerical status')
    require('N_COUPLE' in nids and all('COUPLE' not in b['id'] for b in bs), 'physical corrugated guide invention')
    source_outcomes = d['source_outcomes.json']
    require(source_outcomes['visibility'] == 'evaluator_reference_only' and source_outcomes['not_actor_input'], 'outcome exposure')
    outcomes = {x['id']:x for x in source_outcomes['outcomes']}
    for key, angle, value in [('S_MAIN_20',20,27.8),('S_MAIN_10',10,89.0),('S_SI_LOSSY_25',25,27.8)]:
        x = outcomes[key]
        require(x['incident_angle_deg'] == angle and x['value'] == value and x['data_class'] == 'source_simulation', 'loss-angle/source class conflict')
    actor = d['agent_visible.json']
    require(actor['visibility'] == 'actor_public_contract' and actor['loader_implemented'] is False, 'actor readiness')
    require(actor.get('public_file_allowlist')==['agent_visible.json'], 'unsafe actor file allowlist')
    require(d['provenance.json'].get('visibility')=='authoring_and_evaluator_reference_only', 'provenance answer exposure')
    forbidden = {'provenance.json','source_conflicts.json','source_outcomes.json','evaluator_reference.json','future_sensor_values','hidden_fault_labels'}
    require(forbidden <= set(actor['forbidden_inputs']) and not forbidden.intersection(actor['public_inputs']), 'actor leakage')
    require(not any(k in actor for k in ['outcomes','reference_operation_sequence','hidden_faults','expected_angles','expected_scattering']), 'actor answer leakage')
    B = {b['id']:b for b in bs}
    require(B['BANDWIDTH']['conditions']['frequency_hz'] == [2800,3000,3200], 'band conditions')
    require(B['RADIATION_PATTERNS']['conditions']['incident_angle_deg'] == [5,20,35], 'polar conditions')
    require(B['NEAR_FIELD']['conditions']['incident_angle_deg'] == [25] and 'GRID_NEAR' in B['NEAR_FIELD']['operation_ids'] and 'GRID_FAR' not in B['NEAR_FIELD']['operation_ids'], 'near-field route')
    for bid in ['OBLIQUE_SWEEP','RADIATION_PATTERNS','NEAR_FIELD','NEGATIVE_REFRACTION']:
        require(B[bid]['conditions'].get('historical_acquisition_frequency_hz') is None and B[bid]['conditions'].get('frequency_assignment_provenance')=='task_authored_reference_frequency_not_explicit_historical_fact','inferred historical frequency promoted')
    require(B['NEGATIVE_REFRACTION']['conditions']['incident_angle_deg'] == [45], 'negative incidence')
    require(B['OBLIQUE_SWEEP']['conditions']['incident_angle_schedule_deg'] is None, 'invented angle schedule')
    require(B['ASSEMBLE_ARRAYS']['conditions']['transmissive_layers'] == 2, 'omitted transmission layer')
    status = d['STATUS.json']
    for key, value in [('operation_count',len(ops)),('physical_route_count',len(bs)),('numerical_route_count',len(numbers)),('unknown_gate_count',len(unknowns)),('transport_route_count',len(d['transport_routes.json']['routes'])),('loop_count',len(loops))]:
        require(status[key] == value, 'status count ' + key)
    for key in ['physical_recipe_complete','scene_built','physical_simulation_run','robot_execution_run','acoustic_solver_run','public_write_performed','source_data_included']:
        require(status[key] is False, 'unearned status ' + key)
    require(coverage['required_source_closure'] and not coverage['complete_physical_recipe'] and not coverage['raw_historical_data_obtained'], 'source/readiness distinction')
    source_files = d['provenance.json']['source_files']
    require([(s['id'],s['pages']) for s in source_files] == [('main',5),('supplement',5)], 'source inventory')
    expected_hashes={'main':'3f1363e3db05f0e86a9b81f4dd63a0f6e1067d43794ceef6d220710de458164d','supplement':'26e9fd7eaeaf7918c5097657479d2b0aeee5f03fe5157b197bb222a66ffae964'}
    require(all(s['sha256']==expected_hashes[s['id']] for s in source_files),'source hash drift')
    return {'operations':len(ops),'physical_routes':len(bs),'numerical_routes':len(numbers),'gates':len(unknowns),'loops':len(loops),'transport_routes':len(d['transport_routes.json']['routes'])}

def validate_record(r, context, allow_synthetic=False):
    """Checks supplied receipts; does not authenticate devices or read hardware."""
    require(allow_synthetic or not r.get('synthetic_fixture'), 'synthetic record is not live evidence')
    require(r.get('data_class') == 'measurement_raw', 'source/model result is not measured raw data')
    required = ['record_id','run_id','attempt_id','branch_id','condition_key','setup_signature','calibration_id','calibration_signature','grid_id','point_key','environment_id','timestamp_utc','raw_sha256','quality','acquisition_receipt']
    require(all(nonempty(r.get(k)) for k in required), 'missing record field')
    require(r['branch_id'] in MEASUREMENT_BRANCHES | {'QUALIFY_CHAIN'}, 'nonmeasurement branch')
    require(re.fullmatch(r'[0-9a-f]{64}',r['raw_sha256']) is not None, 'raw hash format')
    require(re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ',r['timestamp_utc']) is not None, 'UTC timestamp')
    for key in ['angle_deg','frequency_hz','gradient_multiple_2pi_rad_per_m']:
        require(type(r.get(key)) in (int,float) and math.isfinite(r[key]), 'nonfinite record parameter')
    require(r.get('gradient_reference_frequency_hz') == 3000, 'missing gradient frequency reference')
    require(r['frequency_hz']>0 and r['gradient_multiple_2pi_rad_per_m'] in {0,3.3,6.7}, 'condition parameter')
    known={'NORMAL_INCIDENCE':([0,3.3,6.7],[0],[3000]),'BANDWIDTH':([3.3],[0],[2800,3000,3200]),'RADIATION_PATTERNS':([6.7],[5,20,35],[3000]),'NEAR_FIELD':([6.7],[25],[3000]),'NEGATIVE_REFRACTION':([6.7],[45],[3000])}
    if r['branch_id'] in known:
        g,a,f=known[r['branch_id']]
        require(r['gradient_multiple_2pi_rad_per_m'] in g and r['angle_deg'] in a and r['frequency_hz'] in f,'branch condition mismatch')
    if r['branch_id']=='OBLIQUE_SWEEP':
        require(r['gradient_multiple_2pi_rad_per_m']==6.7 and r['frequency_hz']==3000, 'oblique specimen/frequency mismatch')
        require(r['angle_deg'] in context.get('angle_schedules',{}).get('OBLIQUE_SWEEP',[]), 'oblique angle outside declared schedule')
    require(r['quality'] in {'accepted','rejected','incomplete'}, 'quality disposition')
    if r['gradient_multiple_2pi_rad_per_m'] == 0:
        require(r.get('sample_id') is None and r.get('assembly_revision') is None, 'empty reference hides specimen')
    else:
        require(nonempty(r.get('sample_id')) and nonempty(r.get('assembly_revision')), 'missing physical sample/revision')
        require(context['objects'].get(r['sample_id']) == r['assembly_revision'], 'stale or invented assembly')
    require(isinstance(r.get('position'),list) and len(r['position'])==2 and all(type(x) in (int,float) and math.isfinite(x) for x in r['position']), 'actual position missing')
    require(context['calibrations'].get(r['calibration_id']) == r['setup_signature'] == r['calibration_signature'], 'calibration scope mismatch')
    require(r.get('record_role') in {'baseline','specimen_measurement'}, 'missing record role')
    if r['record_role']=='baseline':
        require(r['gradient_multiple_2pi_rad_per_m']==0 and r.get('sample_id') is None and r.get('assembly_revision') is None, 'baseline is not empty')
        require(r.get('reference_id') is None and r.get('reference_signature') is None, 'bootstrap reference must be absent')
    else:
        require(nonempty(r.get('reference_id')) and nonempty(r.get('reference_signature')), 'specimen missing reference')
        require(context['references'].get(r['reference_id']) == r['setup_signature'] == r['reference_signature'], 'reference scope mismatch')
    require(r['environment_id'] in context['environments'], 'missing ambient record')
    receipt=context['acquisitions'].get(r['acquisition_receipt'])
    require(isinstance(receipt,dict), 'missing acquisition receipt')
    for key in ['gradient_multiple_2pi_rad_per_m','gradient_reference_frequency_hz','record_role','reference_id','reference_signature','calibration_id','calibration_signature','environment_id','raw_sha256','sample_id','assembly_revision','setup_signature','point_key','angle_deg','frequency_hz','branch_id','condition_key','run_id','attempt_id','quality','grid_id','position']:
        require(receipt.get(key)==r.get(key), 'receipt mismatch: '+key)
    require(receipt.get('outputs_within_limits') is True and receipt.get('actual_position_verified') is True, 'unsafe or unverified acquisition')
    require(r.get('transport_receipt_ids') and set(r['transport_receipt_ids']) <= set(context['transports']), 'missing physical movement provenance')
    if r.get('predecessor_id'):
        require(r['predecessor_id'] in context['previous_records'], 'missing retry predecessor')
        old=context['previous_records'][r['predecessor_id']]
        require(old['record_id']!=r['record_id'] and old['attempt_id']!=r['attempt_id'], 'retry overwrites identity')
        require(old['quality']!='accepted', 'retry erases accepted record')
    return True

def validate_coverage(selected, schedules, records, resolved_gates, package, context, allow_synthetic=False):
    """Acquisition bookkeeping only; preparation and cleanup need other receipts."""
    require(selected and len(selected)==len(set(selected)), 'empty/duplicate selected routes')
    require(set(selected) <= MEASUREMENT_BRANCHES, 'unsupported acquisition route')
    branches={b['id']:b for b in package['branches.json']['branches']}
    for b in selected:
        require(schedules.get(b) and len(schedules[b])==len(set(schedules[b])), 'empty/duplicate schedule')
        for u in branches[b]['unknown_parameter_ids']:
            require(resolved_gates.get(u) is True, 'unresolved execution gate: '+u)
    require(records and len({r['record_id'] for r in records})==len(records), 'empty/duplicate records')
    seen=set()
    for r in records:
        require(r['branch_id'] in selected, 'unselected branch record')
        validate_record(r,context,allow_synthetic)
        require(r['quality']=='accepted','failed measurement is not completion')
        seen.add((r['branch_id'],r['condition_key']))
    expected={(b,k) for b in selected for k in schedules[b]}
    require(seen==expected,'incomplete or extra condition coverage')
    plan=[x for x in context.get('condition_manifest',[]) if x['branch_id'] in selected]
    plan_keys=[(x['branch_id'],x['condition_key']) for x in plan]
    require(len(plan_keys)==len(set(plan_keys)) and set(plan_keys)==expected,'missing/duplicate structured condition manifest')
    by_key={(x['branch_id'],x['condition_key']):x for x in plan}
    for r in records:
        target=by_key[(r['branch_id'],r['condition_key'])]
        for field in ['angle_deg','frequency_hz','gradient_multiple_2pi_rad_per_m','gradient_reference_frequency_hz','sample_id','assembly_revision','grid_id']:
            require(field in target and r.get(field)==target[field],'condition manifest mismatch: '+field)
    planned_points={tuple(x) for x in context.get('expected_trace_keys',[]) if x[0] in selected}
    require(planned_points and {(b,k) for b,k,p in planned_points}==expected,'missing declared grid/repeat plan')
    actual_points={(r['branch_id'],r['condition_key'],r['point_key']) for r in records}
    require(actual_points==planned_points,'incomplete or extra grid/repeat coverage')
    return True

def validate_transport(receipt, object_locations):
    require(receipt.get('entity_ids') and len(receipt['entity_ids'])==len(set(receipt['entity_ids'])),'empty/duplicate transport payload')
    require(receipt['from_station'] != receipt['to_station'], 'transport same endpoint')
    require(all(object_locations.get(i)==receipt['from_station'] for i in receipt['entity_ids']), 'teleported transport origin')
    for key in ['outputs_safe','tethers_disengaged','supported','path_qualified','destination_clear','destination_identity_verified']:
        require(receipt.get(key) is True, 'unsafe transport: '+key)
    return True
