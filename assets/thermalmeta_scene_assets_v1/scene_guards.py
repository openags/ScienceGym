"""Fail-closed, side-effect-free metadata checks. Never operates equipment or certifies evidence."""
import json, pathlib
C=json.loads((pathlib.Path(__file__).parent/'scene_binding_contract.json').read_text())
STAGES={x['stage_id']:x for x in C['stage_bindings']}
CONDITIONS={x['condition_id']:x for x in C['condition_views']}
ACTIONS={'inspect_geometry','inspect_condition','register_evidence','propose_service_request'}
FIELDS={'condition_id':str,'sample_family_id':str,'orientation':str,'specimen_id':str,'design_id':str,'design_revision':str,'profile_id':str,'profile_direction':str,'category':str,'evidence_id':str,'source_reference_only':bool,'synthetic_demo':bool,'geometry_qualified':bool,'use_as_measured':bool,'use_as_threshold':bool,'release_from_elapsed_time':bool,'release_from_stop':bool,'physical_actuation_enabled':bool,'metric_convention_resolved':bool,'mapping_index_resolved':bool,'feature_label_resolved':bool,'flux_units_resolved':bool,'numeric_metric_claim':bool,'absolute_flux_claim':bool,'profile_mapping_source_verified':bool}
def result(status,reasons):
 return {'status':status,'reasons':reasons,'physical_permission':False,'commands_emitted':[],'external_state_changed':False,'evidence_authenticity_established':False}
def evaluate_request(stage_id,anchor_id,action,evidence=None):
 if not all(type(v) is str for v in [stage_id,anchor_id,action]):return result('REJECTED',['invalid_request_schema'])
 if evidence is None:evidence={}
 if type(evidence) is not dict:return result('REJECTED',['invalid_evidence_schema'])
 errors=[]
 if stage_id not in STAGES:errors.append('unknown_stage')
 elif anchor_id!=STAGES[stage_id]['anchor_id']:errors.append('anchor_not_bound_to_stage')
 if action not in ACTIONS:errors.append('physical_or_unknown_action_disabled')
 for k,v in evidence.items():
  if k not in FIELDS:errors.append('unknown_evidence_field:'+str(k))
  elif type(v) is not FIELDS[k]:errors.append('invalid_evidence_field:'+k)
 if errors:return result('REJECTED',errors)
 for f in ['geometry_qualified','use_as_measured','use_as_threshold','release_from_elapsed_time','release_from_stop','physical_actuation_enabled','profile_mapping_source_verified']:
  if evidence.get(f) is True:errors.append('unqualified_or_unsupported_claim:'+f)
 if action=='inspect_condition' and 'condition_id' not in evidence:errors.append('condition_identity_required')
 if 'condition_id' in evidence:
  con=CONDITIONS.get(evidence['condition_id'])
  if con is None:errors.append('unknown_condition')
  else:
   for f in ['sample_family_id','orientation','specimen_id','design_id','design_revision','profile_id','profile_direction']:
    if f in evidence and evidence[f]!=con[f]:errors.append('condition_identity_mismatch:'+f)
   if evidence.get('synthetic_demo') is False:errors.append('demo_identity_is_not_real_specimen_evidence')
 elif any(f in evidence for f in ['sample_family_id','orientation','specimen_id','design_id','design_revision','profile_id','profile_direction']):errors.append('unbound_condition_identity')
 if evidence.get('category') not in {None,'source_reported','synthetic_demo','external_unverified_receipt'}:errors.append('unsupported_evidence_category')
 if evidence.get('category')=='source_reported' and evidence.get('source_reference_only') is not True:errors.append('source_reference_boundary_required')
 if action=='register_evidence' and (not evidence.get('evidence_id','').strip() or 'category' not in evidence):errors.append('evidence_identity_and_category_required')
 if evidence.get('numeric_metric_claim') and not evidence.get('metric_convention_resolved'):errors.append('metric_convention_hold')
 if evidence.get('absolute_flux_claim') and not evidence.get('flux_units_resolved'):errors.append('flux_units_hold')
 # This static package cannot release scientific claims, even if input self-attests resolved.
 if evidence.get('numeric_metric_claim') or evidence.get('absolute_flux_claim'):errors.append('static_scene_cannot_certify_scientific_claim')
 if errors:return result('REJECTED',errors)
 if action=='propose_service_request':return result('HOLD_UNQUALIFIED',['qualified_provider_required','no_dispatch_implementation'])
 return result('EVIDENCE_ONLY_ACCEPTED',[])
def check_release(receipt):
 """Checks metadata shape only; never authorizes retrieval, rotation, reseating or disposal."""
 if type(receipt) is not dict:return result('HOLD',['invalid_receipt_schema'])
 allowed=set(C['safe_release_requires'])|{'pending_service_jobs','specimen_id','run_id','provider_id'}
 errs=['unknown_receipt_field:'+str(k) for k in receipt if k not in allowed]
 for k in C['safe_release_requires']:
  v=receipt.get(k)
  if type(v) is not dict or set(v)!={'evidence_id','provider_id','independently_observed'} or type(v.get('evidence_id')) is not str or not v.get('evidence_id','').strip() or type(v.get('provider_id')) is not str or not v.get('provider_id','').strip() or v.get('independently_observed') is not True:errs.append('missing_or_invalid:'+k)
 for k in ['specimen_id','run_id','provider_id']:
  if type(receipt.get(k)) is not str or not receipt.get(k,'').strip():errs.append('missing_or_invalid:'+k)
 if receipt.get('pending_service_jobs') is not False:errs.append('service_custody_retained')
 return result('HOLD' if errs else 'METADATA_COMPLETE_NOT_PHYSICAL_AUTHORIZATION',errs)
if __name__=='__main__':
 import sys
 try:
  value=json.load(sys.stdin)
  if type(value) is not dict or set(value)-{'stage_id','anchor_id','action','evidence'}:out=result('REJECTED',['invalid_request_schema'])
  else:out=evaluate_request(**value)
 except (TypeError,ValueError,KeyError):out=result('REJECTED',['invalid_request_schema'])
 print(json.dumps(out,sort_keys=True))
