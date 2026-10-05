"""Pure metadata guard for an original static microscopy review scene.
SPDX-License-Identifier: Apache-2.0
No hardware/device/network/file mutation occurs in this API. Evidence authenticity is external.
"""
import json
from pathlib import Path
CONTRACT=json.loads((Path(__file__).parent/'shared_binding_contract.json').read_text())
ROUTES={r['route_id']:r for r in CONTRACT['route_bindings']}
ANCHORS={a['anchor_id'] for g in CONTRACT['assets'] for a in g['anchors']}
ACTIONS={'inspect_geometry','select_evidence','propose_service_request'}
FIELDS={'station_id','branch_id','material_id','state_id','plane_id','measurement_category','treated_as_new_measurement','source_outcome_success_threshold','geometry_as_qualified_interface','render_as_resolution_evidence','hardware_commands','actuation_enabled','direct_particle_handling','bare_target_grasp','infer_safe_from_icon','infer_safe_from_timer','star_sphere_diameter_um','target_family','sil_diameter_mm','objective_magnification','assume_coating_reversible','skip_preservation_history','assume_source_spacing_convention','execute_model','clear_qualification_gaps'}
BOOLS={'treated_as_new_measurement','source_outcome_success_threshold','geometry_as_qualified_interface','render_as_resolution_evidence','actuation_enabled','direct_particle_handling','bare_target_grasp','infer_safe_from_icon','infer_safe_from_timer','assume_coating_reversible','skip_preservation_history','assume_source_spacing_convention','execute_model','clear_qualification_gaps'}
STRINGS={'station_id','branch_id','material_id','state_id','plane_id','measurement_category','target_family'}
def result(status,reasons):return {'status':status,'reasons':reasons,'physical_permission':False,'scientific_measurement_established':False,'commands_emitted':[]}
def evaluate_request(route_id,anchor_id,action,evidence=None):
    if evidence is None:evidence={}
    if not all(isinstance(x,str) for x in [route_id,anchor_id,action]) or not isinstance(evidence,dict):return result('REJECTED',['invalid_input_schema'])
    errors=[]
    if set(evidence)-FIELDS:errors.append('unknown_evidence_fields')
    if any(k in evidence and type(evidence[k]) is not bool for k in BOOLS):errors.append('invalid_boolean_schema')
    if any(k in evidence and not isinstance(evidence[k],str) for k in STRINGS):errors.append('invalid_string_schema')
    for k in ['sil_diameter_mm','objective_magnification','star_sphere_diameter_um']:
        if k in evidence and evidence[k] is not None and (type(evidence[k]) not in {int,float} or not __import__('math').isfinite(evidence[k])):errors.append('invalid_numeric_schema')
    if 'hardware_commands' in evidence and evidence['hardware_commands']!=[]:errors.append('hardware_commands_disabled')
    if route_id not in ROUTES:errors.append('unknown_route')
    if anchor_id not in ANCHORS:errors.append('unknown_anchor')
    elif route_id in ROUTES and anchor_id not in ROUTES[route_id]['target_anchor_ids']:errors.append('anchor_not_bound_to_route')
    if action not in ACTIONS:errors.append('physical_or_unknown_action_disabled')
    if errors:return result('REJECTED',errors)
    if 'branch_id' in evidence and evidence['branch_id'] not in ROUTES[route_id]['branch_ids']:errors.append('branch_route_mismatch')
    if 'station_id' in evidence and evidence['station_id'] not in ROUTES[route_id]['station_ids']:errors.append('station_route_mismatch')
    for k,collection in [('branch_id','branch_ids'),('material_id','material_ids'),('state_id','state_ids'),('plane_id','coordinate_plane_ids')]:
        if k in evidence and evidence[k] not in CONTRACT[collection]:errors.append('unknown_'+k)
    if any(evidence.get(k) for k in BOOLS):errors.append('unsafe_or_unqualified_claim')
    if evidence.get('measurement_category') in {'source_reported','render','synthetic','model','text_only','screenshot'} and evidence.get('treated_as_new_measurement'):errors.append('invalid_measurement_provenance')
    if evidence.get('target_family') not in {None,*CONTRACT['identity_invariants']['target_families']}:errors.append('unknown_target_family')
    if (evidence.get('target_family')=='star_film' or anchor_id=='A02.star_identity') and evidence.get('star_sphere_diameter_um') is not None:errors.append('star_sphere_size_unreported')
    if 'sil_diameter_mm' in evidence:
        d=evidence['sil_diameter_mm']
        if d not in {.5,2.5}:errors.append('unknown_sil_identity')
        if d==.5 and evidence.get('objective_magnification',80)!=80:errors.append('sil_objective_identity_mismatch')
        if d==2.5 and evidence.get('objective_magnification',40)!=40:errors.append('sil_objective_identity_mismatch')
        if anchor_id=='A04.sil_0p5mm_identity' and d!=.5:errors.append('sil_anchor_identity_mismatch')
        if anchor_id=='A04.sil_2p5mm_identity' and d!=2.5:errors.append('sil_anchor_identity_mismatch')
    families={'A02.grating_identity':'grating','A02.aao_identity':'gold_aao','A02.disc_identity':'optical_disc','A02.star_identity':'star_film'}
    if anchor_id in families and 'target_family' in evidence and evidence['target_family']!=families[anchor_id]:errors.append('target_anchor_identity_mismatch')
    objective={'A04.sil_0p5mm_identity':80,'A04.sil_2p5mm_identity':40}
    if anchor_id in objective and 'objective_magnification' in evidence and evidence['objective_magnification']!=objective[anchor_id]:errors.append('sil_objective_identity_mismatch')
    expected={'A07.object_frame':'FRAME_OBJECT','A07.virtual_frame':'FRAME_VIRTUAL','A07.detector_frame':'FRAME_DETECTOR'}
    if anchor_id in expected and 'plane_id' in evidence and evidence['plane_id']!=expected[anchor_id]:errors.append('coordinate_plane_conflation')
    if errors:return result('REJECTED',errors)
    if action=='propose_service_request':return result('HOLD_QUALIFICATION',['qualified_service_receipt_required','no_dispatch_implementation','all_16_source_gaps_retained'])
    return result('EVIDENCE_ONLY_ACCEPTED',[])

def check_closeout(receipt):
    required={'independent_safe_state','particle_containment','supported_carrier','receiver_custody','archive_record','no_pending_service_jobs'}
    if not isinstance(receipt,dict) or set(receipt)-required:return result('HOLD',['invalid_closeout_schema'])
    missing=[]
    for k in required-{'no_pending_service_jobs'}:
        v=receipt.get(k)
        if not isinstance(v,dict) or set(v)!={'evidence_id','provider_id','independently_observed'} or v.get('independently_observed') is not True or any(not isinstance(v.get(x),str) or not v[x].strip() for x in ['evidence_id','provider_id']):missing.append(k)
    if receipt.get('no_pending_service_jobs') is not True:missing.append('no_pending_service_jobs')
    return result('HOLD' if missing else 'METADATA_COMPLETE_NOT_PHYSICAL_AUTHORIZATION',sorted(missing))
