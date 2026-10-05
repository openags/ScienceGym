"""Side-effect-free semantic checks for a static review scene. Never emits device commands."""
import json
from pathlib import Path
CONTRACT=json.loads((Path(__file__).parent/'shared_binding_contract.json').read_text())
ANCHORS={t['anchor_id'] for a in CONTRACT['assets'] for t in a['anchors']}
ROUTES={r['route_id']:r for r in CONTRACT['route_bindings']}
PHYSICAL_ACTIONS={'move','grasp','release','set_current','set_field','cool','heat','rewire','open_service','fabricate','execute_path','actuate','start_acquisition'}

def evaluate_request(route_id, anchor_id, action, evidence=None):
    """Check a proposed evidence-only operation. Returned status grants no physical permission."""
    evidence={} if evidence is None else evidence
    if not isinstance(route_id,str) or not isinstance(anchor_id,str) or not isinstance(action,str) or not isinstance(evidence,dict):
        return {'status':'REJECTED','reasons':['invalid_input_schema'],'physical_permission':False,'commands_emitted':[]}
    errors=[]
    for field in ('region','measurement_category','reference_id','bath'):
        if field in evidence and not isinstance(evidence[field],str):
            return {'status':'REJECTED','reasons':['invalid_evidence_field_schema:'+field],'physical_permission':False,'commands_emitted':[]}
    if route_id not in ROUTES: errors.append('unknown_route')
    if anchor_id not in ANCHORS: errors.append('unknown_anchor')
    elif route_id in ROUTES and anchor_id not in ROUTES[route_id]['target_anchor_ids']: errors.append('anchor_not_bound_to_route')
    if action in PHYSICAL_ACTIONS or action not in {'inspect_geometry','register_evidence','propose_service_request'}: errors.append('physical_or_unknown_action_disabled')
    if evidence.get('hardware_commands') or evidence.get('actuation_enabled'): errors.append('actuation_disabled')
    if evidence.get('measurement_category') in {'synthetic','source_reported','digitized_source_plot'} and evidence.get('treated_as_new_measurement'): errors.append('invalid_measurement_provenance')
    if evidence.get('source_outcome_success_threshold'): errors.append('source_outcome_is_not_threshold')
    if evidence.get('physical_chip_count',1)!=1: errors.append('one_physical_chip')
    expected_regions={'AS02.array1_region':{'Array1'},'AS02.array2_region':{'Array2'},'AS02.hall_bar_region':{'HB'},'AS03.subarray_topology':{'Array1','Array2'},'AS03.whole_device_topology':{'whole_device'}}
    region=evidence.get('region')
    if anchor_id in expected_regions and region is not None and region not in expected_regions[anchor_id]: errors.append('region_anchor_identity_mismatch')
    if region is None and anchor_id in expected_regions and len(expected_regions[anchor_id])==1: region=next(iter(expected_regions[anchor_id]))
    if anchor_id.startswith('AS07.'):
        if evidence.get('reference_id','REF-100-OIL')!='REF-100-OIL' or evidence.get('reference_ohms',100)!=100 or evidence.get('bath','oil')!='oil': errors.append('reference_anchor_identity_mismatch')
    if anchor_id.startswith('AS08.'):
        if evidence.get('reference_id','REF-12K9-AIR')!='REF-12K9-AIR' or evidence.get('reference_ohms',12900)!=12900 or evidence.get('bath','air')!='air': errors.append('reference_anchor_identity_mismatch')
    if anchor_id=='AS03.subarray_topology' and (evidence.get('elements',118)!=118 or evidence.get('nominal_ohms_approx',109)!=109): errors.append('generic_subarray_identity_conflated')
    if region in {'Array1','Array2'}:
        if evidence.get('elements',118)!=118 or evidence.get('nominal_ohms_approx',109)!=109: errors.append('subarray_identity_conflated')
    if region=='whole_device':
        if evidence.get('elements',236)!=236 or evidence.get('nominal_ohms_approx',219)!=219: errors.append('whole_device_identity_conflated')
    if evidence.get('reference_id')=='REF-100-OIL' and (evidence.get('reference_ohms',100)!=100 or evidence.get('bath','oil')!='oil'): errors.append('reference_identity_conflated')
    if evidence.get('reference_id')=='REF-12K9-AIR' and (evidence.get('reference_ohms',12900)!=12900 or evidence.get('bath','air')!='air'): errors.append('reference_identity_conflated')
    if evidence.get('execute_eq3') or evidence.get('execute_eq4') or evidence.get('execute_source_loop_expansion'): errors.append('source_analysis_qualification_hold')
    if evidence.get('geometry_as_qualified_interface') or evidence.get('source_value_as_safety_limit'): errors.append('unqualified_geometry_or_limit')
    if evidence.get('duplicate_shared_instrument_lease'): errors.append('shared_instrument_lease_conflict')
    if evidence.get('infer_safe_from_icon') or evidence.get('infer_safe_from_timer') or evidence.get('infer_safe_from_stop_command'): errors.append('independent_safe_evidence_required')
    if evidence.get('bare_chip_manipulation'): errors.append('protected_carrier_only')
    if errors:return {'status':'REJECTED','reasons':errors,'physical_permission':False,'commands_emitted':[]}
    if action=='propose_service_request':return {'status':'HOLD_UNQUALIFIED','reasons':['qualified_provider_receipt_required','no_dispatch_implementation'],'physical_permission':False,'commands_emitted':[]}
    return {'status':'EVIDENCE_ONLY_ACCEPTED','reasons':[],'physical_permission':False,'commands_emitted':[]}

def check_closeout(receipt):
    """Metadata completeness only. External evidence authenticity is not established here."""
    if not isinstance(receipt,dict):
        return {'status':'HOLD','missing':['invalid_receipt_schema'],'physical_permission':False,'commands_emitted':[]}
    required=CONTRACT['safe_release_requires']
    missing=[k for k in required if not isinstance(receipt.get(k),dict) or receipt[k].get('independently_observed') is not True or not isinstance(receipt[k].get('evidence_id'),str) or not receipt[k].get('evidence_id','').strip() or not isinstance(receipt[k].get('provider_id'),str) or not receipt[k].get('provider_id','').strip()]
    if receipt.get('pending_service_jobs') is not False:missing.append('pending_service_jobs')
    if not isinstance(receipt.get('custody_acceptance_id'),str) or not receipt.get('custody_acceptance_id','').strip():missing.append('custody_acceptance_id')
    return {'status':'HOLD' if missing else 'METADATA_COMPLETE_NOT_PHYSICAL_AUTHORIZATION','missing':missing,'physical_permission':False,'commands_emitted':[]}
