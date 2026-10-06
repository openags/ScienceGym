"""Pure metadata guard for original static frictional-fluid review assets.
SPDX-License-Identifier: Apache-2.0
No device dispatch, fluid solver, chemical preparation or file/network mutation.
"""
import json,math
from pathlib import Path
CONTRACT=json.loads((Path(__file__).parent/'shared_binding_contract.json').read_text())
ROUTES={r['route_id']:r for r in CONTRACT['route_bindings']}
ANCHORS={a['anchor_id']:a for a in CONTRACT['anchors']}
ACTIONS={'inspect_geometry','select_evidence','propose_service_request'}
BOOLS={'actuation_enabled','hardware_operation','direct_powder_handling','fabricate_cell','mix_recipe','set_pressure','open_enclosure','execute_fluid_model','execute_boyle_model','repair_boyle_sign','assign_coral_rate','source_as_new_data','render_as_fluid_evidence','geometry_as_qualified_interface','clear_qualification_gaps','infer_safe_from_icon','infer_safe_from_timer','break_glass','normalized_phi_is_absolute_fraction','reservoir_volume_is_total_compliance','pump_rate_is_burst_rate','movie_time_is_experiment_time','sparse_grid_is_complete_factorial','twenty_widths_are_independent_preparations','source_threshold_is_universal','context_counts_as_experiment','promote_source_media_rights'}
STRINGS={'station_id','branch_id','material_id','state_id','evidence_class','anchor_station_id'}
FIELDS=BOOLS|STRINGS|{'hardware_commands','plate_thickness_mm'}

def result(status,reasons):return {'status':status,'reasons':reasons,'physical_permission':False,'scientific_measurement_established':False,'commands_emitted':[],'qualification_holds':list(CONTRACT['unknown_ids'])}

def evaluate_request(route_id,anchor_id,action,evidence=None):
 if evidence is None:evidence={}
 if not all(type(x) is str for x in [route_id,anchor_id,action]) or type(evidence) is not dict:return result('REJECTED',['invalid_input_schema'])
 errors=[]
 if set(evidence)-FIELDS:errors.append('unknown_evidence_fields')
 if any(k in evidence and type(evidence[k]) is not bool for k in BOOLS):errors.append('invalid_boolean_schema')
 if any(k in evidence and type(evidence[k]) is not str for k in STRINGS):errors.append('invalid_string_schema')
 if 'hardware_commands' in evidence and (type(evidence['hardware_commands']) is not list or evidence['hardware_commands']!=[]):errors.append('hardware_commands_disabled')
 if 'plate_thickness_mm' in evidence and (type(evidence['plate_thickness_mm']) not in {int,float} or (type(evidence['plate_thickness_mm']) is float and not math.isfinite(evidence['plate_thickness_mm']))):errors.append('invalid_numeric_schema')
 if route_id not in ROUTES:errors.append('unknown_route')
 if anchor_id not in ANCHORS:errors.append('unknown_anchor')
 elif route_id in ROUTES and anchor_id not in ROUTES[route_id]['anchor_ids']:errors.append('anchor_not_bound_to_route')
 if action not in ACTIONS:errors.append('physical_or_unknown_action_disabled')
 if errors:return result('REJECTED',errors)
 r=ROUTES[route_id];a=ANCHORS[anchor_id]
 if 'branch_id' in evidence and evidence['branch_id'] not in r['branch_ids']:errors.append('branch_route_mismatch')
 if 'station_id' in evidence and evidence['station_id'] not in r['station_ids']:errors.append('station_route_mismatch')
 if 'anchor_station_id' in evidence and evidence['anchor_station_id']!=a['station_id']:errors.append('anchor_station_mismatch')
 for k,values in [('material_id',CONTRACT['material_ids']),('state_id',CONTRACT['state_taxonomy']),('evidence_class',CONTRACT['evidence_classes'])]:
  if k in evidence and evidence[k] not in values:errors.append('unknown_'+k)
 if any(evidence.get(k) is True for k in BOOLS):errors.append('unsafe_or_unqualified_claim')
 if 'plate_thickness_mm' in evidence:
  thickness=evidence['plate_thickness_mm']
  if thickness not in {10,19}:errors.append('unknown_source_cell_variant')
  if anchor_id in {'A02.cell_10mm','A02.cell_19mm'} and thickness!={'A02.cell_10mm':10,'A02.cell_19mm':19}[anchor_id]:errors.append('source_cell_anchor_mismatch')
 if errors:return result('REJECTED',errors)
 if action=='propose_service_request':return result('HOLD_QUALIFICATION',['closed_qualified_service_required','no_dispatch_implementation','all_20_source_gaps_retained'])
 return result('EVIDENCE_ONLY_ACCEPTED',[])

def check_closeout(receipt):
 """Validate final aggregate R12 archive metadata only, never gate per-job R11.
 A completed or failed job may request R11 safe closeout while other jobs remain open.
 This structural validator authenticates no receipt and emits no commands.
 """
 required={'independent_safe_state','contained_material','supported_carrier','receiver_custody','inspection_disposition','archive_record','no_pending_service_jobs'}
 if type(receipt) is not dict or set(receipt)-required:return result('HOLD',['invalid_closeout_schema'])
 missing=[]
 for k in required-{'no_pending_service_jobs'}:
  v=receipt.get(k)
  if type(v) is not dict or set(v)!={'evidence_id','provider_id','independently_observed'} or v.get('independently_observed') is not True or any(type(v.get(x)) is not str or not v[x].strip() for x in ['evidence_id','provider_id']):missing.append(k)
 if receipt.get('no_pending_service_jobs') is not True:missing.append('no_pending_service_jobs')
 return result('HOLD' if missing else 'METADATA_COMPLETE_NOT_PHYSICAL_AUTHORIZATION',sorted(missing))
