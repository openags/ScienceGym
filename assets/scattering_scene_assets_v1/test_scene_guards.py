"""Deterministic negative checks for the static scene adapter."""
import copy,json
from pathlib import Path
from scene_guards import evaluate
ROOT=Path(__file__).resolve().parent
request={'physical_execution_enabled':False,'operation_id':'R03','anchor_id':'AS02.M1.carrier_acceptance','action':'set_synthetic_visual_state','evidence_kind':'synthetic_fixture','claims_real_observation':False,'branch_id':'B01','science_type':'experimental_source_review','coordinate_mapping_status':'explicit_synthetic_test_mapping','family_id':'GROOVE_M1','supported':True,'custody_holder':'SYNTHETIC_HOLDER','occupancy':'known_synthetic','retained_lease':'SYNTHETIC_LEASE','configuration_epoch':'SYNTHETIC_E1','calibration_configuration_epoch':'SYNTHETIC_E1','observed_safe_fixture':{'acoustic_off':True,'beam_safe':True,'motion_safe':True,'support_safe':True}}
results=[]
def check(name,r,expected):
 out=evaluate(r);assert out['status']==expected,(name,out)
 assert out['physical_execution_enabled'] is False and out['hardware_commands']==[]
 results.append({'test':name,'result':'PASS','status':out['status'],'reason':out.get('reason')})
check('synthetic_visual_state_only',request,'SYNTHETIC_VISUAL_STATE_ONLY')
for key,val,name in [
 ('physical_execution_enabled',True,'physical_actuation_blocked'),('physical_execution_enabled',None,'missing_disabled_flag_blocked'),
 ('operation_id','R99','unknown_operation_blocked'),('anchor_id','AS10.return_acceptance','cross_operation_anchor_blocked'),
 ('action','emit_ultrasound','acoustic_request_blocked'),('action','move_robot','robot_motion_blocked'),('action','align_laser','live_optics_blocked'),
 ('evidence_kind','real_observation','unsupported_real_observation_blocked'),('claims_real_observation',True,'synthetic_claim_laundering_blocked'),
 ('branch_id','A01','numerical_experiment_conflation_blocked'),('branch_id',None,'missing_branch_blocked'),('branch_id','B99','unknown_branch_blocked'),('branch_id',[],'malformed_branch_blocked'),('operation_id',{},'malformed_operation_blocked'),('anchor_id',[],'malformed_anchor_blocked'),('custody_holder',{},'malformed_holder_blocked'),('retained_lease',{},'malformed_lease_blocked'),('configuration_epoch',{},'malformed_epoch_blocked'),('branch_id','B04','wrong_branch_design_blocked'),('coordinate_mapping_status',None,'unresolved_sign_mapping_blocked'),
 ('family_id','GROOVE_M3','wrong_design_family_blocked'),('supported',False,'unsupported_transfer_blocked'),
 ('custody_holder',None,'unknown_custody_blocked'),('occupancy',None,'unknown_occupancy_blocked'),('retained_lease',None,'missing_lease_blocked'),
 ('calibration_configuration_epoch','SYNTHETIC_OLD','stale_calibration_blocked'),('command_ack_only',True,'command_ack_safety_shortcut_blocked'),
 ('auto_retry',True,'blind_retry_blocked'),('force_newtons',1.0,'unqualified_force_output_blocked'),('pressure_field',[[1]],'acoustic_field_generation_blocked'),('hardware_commands',['move_robot'],'contradictory_hardware_command_blocked'),('scientific_physics_implemented',True,'contradictory_science_claim_blocked'),('real_observation',True,'unrecognized_real_observation_field_blocked'),('branch_id','P02','preparation_branch_route_mismatch_blocked')]:
 r=copy.deepcopy(request);r[key]=val;check(name,r,'HOLD_QUALIFICATION')
for field in ('acoustic_off','beam_safe','motion_safe','support_safe'):
 r=copy.deepcopy(request);r['observed_safe_fixture'][field]=False;check('missing_'+field+'_blocked',r,'HOLD_QUALIFICATION')
r=copy.deepcopy(request);r.update(branch_id='A01',science_type='numerical_source_review')
check('numerical_review_specimen_handling_blocked',r,'HOLD_QUALIFICATION')
r=copy.deepcopy(request);r.update(operation_id='R11',anchor_id='AS11.analysis_record')
check('experimental_branch_numerical_route_blocked',r,'HOLD_QUALIFICATION')
r={'physical_execution_enabled':False,'operation_id':'R11','anchor_id':'AS11.analysis_record','action':'inspect_anchor'}
check('numerical_inspection_stays_nonphysical',r,'STATIC_REVIEW_ONLY')
(ROOT/'guard_test_results.json').write_text(json.dumps({'tests':results,'passed':len(results),'failed':0,'hardware_commands_emitted':0,'physical_execution_enabled':False},indent=2)+'\n')
print(json.dumps({'passed':len(results),'failed':0}))
