import unittest
from copy import deepcopy
from contract import *

def evaluate(receipts,op=None):
 return MetadataContract(SyntheticStore(receipts)).review({'operation_id':op or receipts[0]['operation_id'],'evidence_ids':[r['id']for r in receipts]})
def header(kind,op,id=None):return {'id':id or 'SYNTHETIC_'+kind,'origin':'synthetic_evaluator_fixture','provider':'SYNTHETIC_QUALIFIED_PROVIDER','status':'accepted','operation_id':op,'kind':kind}
def custody(op='R02'):
 c=header('custody',op);c.update({k:'SYNTHETIC_'+k for k in ['event_id','sample_id','chip_id','from_custodian','to_custodian','from_support','to_support','carrier_id','condition_before','condition_after','orientation_evidence','acceptance_id']});c.update({'receiver_accepted':True,'receiving_support_observed':True,'identity_occupancy_observed':True,'releases_previous_support':False,'unresolved_hazards':[],'support_observed_at':'2000-01-01T00:00:00Z','accepted_at':'2000-01-01T00:00:01Z'});return c

def characterization():
 r=header('characterization','R04');r.update({'chip_id':'SYNTHETIC_CHIP','mount_id':'SYNTHETIC_MOUNT','configuration_revision':'SYNTHETIC_CONFIG','region_chip_ids':{x:'SYNTHETIC_CHIP' for x in ['HB','Array1','Array2']},'path_receipts':{x:'SYNTHETIC_'+x for x in ['HB_Rxx','HB_Rxy','HB_contacts','subarray_transition','subarray_magnetotransport','voltmeter_offset','noise_floor']},'calibration_receipt_id':'SYNTHETIC_CAL','terminal_map_revision':'SYNTHETIC_MAP','source_outcome_ids':[],'scientific_values':None,'apparent_plateau_certifies_quantization':False,'HB_density_is_direct_subarray_measurement':False});return r

def analysis(op='R12'):
 r=header('analysis',op);r.update({'raw_bundle_ids':['SYNTHETIC_BUNDLE'],'raw_source_class':'synthetic_metadata_only','source_outcome_ids':[],'unresolved_equation_holds':[],'qualified_method_revision':'SYNTHETIC_APPROVED_METADATA_METHOD','numerical_analysis_performed':False,'covariance_record':'SYNTHETIC_COV','exclusion_log':'SYNTHETIC_EXCLUDE','source_graph_edge_ids':['E01','E02','E03','E04','E05'],'acquired_direct_edge_ids':[],'edge_statuses':{f'E{i:02d}':'held_qualification' for i in range(1,6)},'simple_loop_count':3,'independent_cycle_count':2,'derived_paths_are_independent':False,'claims_exact_absolute_quantization':False,'branch_statuses':{'R09':'held_qualification','R10':'unattempted','R11':'unattempted'}});return r

class ContractTests(unittest.TestCase):
 def test_positive_measurement_families(self):
  for op,pair in [('R05',('Array1','Array2')),('R06',('HB','REF100')),('R07',('Array1','REF100')),('R07',('Array2','REF100')),('R08',('HB','Array1')),('R09',('Array1','Array2')),('R09',('Array1','REF100')),('R09',('Array2','REF100')),('R10',('Array1','Array2')),('R11',('Array1','REF12K9')),('R11',('Array2','REF12K9'))]:
   with self.subTest(op=op,pair=pair):
    r=evaluate(list(measurement_fixture(op,pair)));self.assertEqual(r['status'],'SYNTHETIC_METADATA_ACCEPTED');self.assertFalse(r['physical_execution_enabled']);self.assertEqual(r['physical_qualification'],'HOLD_QUALIFICATION')
 def test_every_measurement_field_required(self):
  for key in MEASUREMENT_FIELDS+LIST_FIELDS+['physical_resource_ids','per_device_current_records','per_device_power_records','reference_baths','bath_stability_record_ids','region_chip_ids']:
   with self.subTest(key=key):
    rs=list(measurement_fixture('R06',('HB','REF100')));rs[0].pop(key)
    with self.assertRaises((ContractError,KeyError)):evaluate(rs)
 def test_measurement_negatives(self):
  mutations={'ratio_direction':'Array2/Array1','ratio_units':'ohm','new_observation':True,'scientific_values':[0.033],'source_outcome_ids':['O01'],'source_derived_threshold':True,'reference_id':'Array1','field_sign':'unknown','region_chip_ids':{'Array1':'OTHER','Array2':'SYNTHETIC_CHIP'},'per_device_current_records':{'Array1':'R'},'per_device_power_records':{'Array2':'R'},'raw_timestamps':['2000-01-02T00:00:00Z'],'independent_chip_count':45,'bundle_hash':'not hash','lease_ids':['DOES_NOT_EXIST'],'physical_resource_ids':['ST03'],'end':'1999-01-01T00:00:00Z'}
  for key,val in mutations.items():
   with self.subTest(key=key):
    rs=list(measurement_fixture());rs[0][key]=val
    with self.assertRaises(ContractError):evaluate(rs)
 def test_calibration_negatives(self):
  mutations={'configuration_revision':'OTHER','method_revision':'OTHER','sample_mount_id':'OTHER','terminal_map_revision':'OTHER','calibration_ids':['OTHER'],'instrument_ids':['OTHER'],'valid_until':'2000-01-01T00:00:01Z','valid_from':'2000-01-01T00:00:01Z','after_check':None,'before_check':None,'reference_change':True,'configuration_change':True}
  for key,val in mutations.items():
   with self.subTest(key=key):
    rs=list(measurement_fixture());rs[1][key]=val
    with self.assertRaises(ContractError):evaluate(rs)
 def test_lease_negatives(self):
  for key,val in {'lease_id':'OTHER','lease_owner':'OTHER','job_id':'OTHER','custodian_id':'OTHER','sample_mount_id':'OTHER','chip_id':'OTHER','resources':['ST03'],'resource_ids_are_physical':False,'conflicting_owners':['OTHER'],'release_requested':True}.items():
   with self.subTest(key=key):
    rs=list(measurement_fixture());rs[2][key]=val
    with self.assertRaises(ContractError):evaluate(rs)
 def test_untrusted_sources(self):
  for key,val in {'origin':'source_reported','provider':'ACTOR_ASSERTED','status':'pending','operation_id':'R06'}.items():
   with self.subTest(key=key):
    rs=list(measurement_fixture());rs[0][key]=val
    with self.assertRaises(ContractError):evaluate(rs,'R05')
 def test_no_numeric_or_inline_action(self):
  rs=list(measurement_fixture());c=MetadataContract(SyntheticStore(rs));base={'operation_id':'R05','evidence_ids':[r['id']for r in rs]}
  for key,val in {'current':3,'field':5,'temperature':2.1,'command':'run','receipt':rs[0],'hardware_endpoint':'device'}.items():
   with self.subTest(key=key):
    a=deepcopy(base);a[key]=val
    with self.assertRaises(ContractError):c.review(a)
 def test_unknown_duplicate_and_inline_receipts(self):
  rs=list(measurement_fixture());c=MetadataContract(SyntheticStore(rs))
  for ids in [[],['UNKNOWN'],['SYNTHETIC_M','SYNTHETIC_M'],[rs[0]]]:
   with self.subTest(ids=ids):
    with self.assertRaises(ContractError):c.review({'operation_id':'R05','evidence_ids':ids})
 def test_store_is_copied(self):
  rs=list(measurement_fixture());c=MetadataContract(SyntheticStore(rs));rs[0]['source_outcome_ids']=['O01'];self.assertEqual(c.review({'operation_id':'R05','evidence_ids':['SYNTHETIC_M','SYNTHETIC_C','SYNTHETIC_L']})['status'],'SYNTHETIC_METADATA_ACCEPTED')
 def test_missing_lease_rejected(self):
  rs=list(measurement_fixture())[:2]
  with self.assertRaises(ContractError):evaluate(rs)
 def test_no_invented_HB_Array2_edge(self):
  with self.assertRaises(ContractError):evaluate(list(measurement_fixture('R08',('HB','Array2'))))
 def test_reference_baths_separate(self):
  for op,pair,k in [('R06',('HB','REF100'),'REF100'),('R11',('Array1','REF12K9'),'REF12K9')]:
   with self.subTest(op=op):
    rs=list(measurement_fixture(op,pair));rs[0]['reference_baths'][k]='WRONG'
    with self.assertRaises(ContractError):evaluate(rs)
 def test_screen_SD_not_Allan(self):
  for key,val in [('uncertainty_semantics','Allan_SEM'),('allan_used',True),('performance_test_permit',None)]:
   with self.subTest(key=key):
    rs=list(measurement_fixture('R10'));rs[0][key]=val
    with self.assertRaises(ContractError):evaluate(rs)
 def test_external_identity_not_guessed(self):
  for key,val in [('runtime_region_evidence',None),('source_SI4_identity_resolved',True)]:
   with self.subTest(key=key):
    rs=list(measurement_fixture('R11',('Array1','REF12K9')));rs[0][key]=val
    with self.assertRaises(ContractError):evaluate(rs)
 def test_positive_characterization(self):self.assertEqual(evaluate([characterization()])['status'],'SYNTHETIC_METADATA_ACCEPTED')
 def test_characterization_paths(self):
  for key in characterization()['path_receipts']:
   with self.subTest(key=key):
    r=characterization();r['path_receipts'].pop(key)
    with self.assertRaises(ContractError):evaluate([r])
 def test_characterization_claim_limits(self):
  for key,val in [('apparent_plateau_certifies_quantization',True),('HB_density_is_direct_subarray_measurement',True),('region_chip_ids',{'HB':'OTHER'}),('source_outcome_ids',['O01'])]:
   with self.subTest(key=key):
    r=characterization();r[key]=val
    with self.assertRaises(ContractError):evaluate([r])
 def test_scope_positive(self):
  r=header('scope','R00');r.update({'plan_id':'SYNTHETIC_PLAN','unknowns_resolved_in_fixture':True});self.assertEqual(evaluate([r])['status'],'SYNTHETIC_METADATA_ACCEPTED')
 def test_custody_positive(self):self.assertEqual(evaluate([custody()])['status'],'SYNTHETIC_METADATA_ACCEPTED')
 def test_custody_negative(self):
  for key,val in [('receiver_accepted',False),('receiving_support_observed',False),('identity_occupancy_observed',False),('releases_previous_support',True),('unresolved_hazards',['unknown']),('accepted_at','1999-01-01T00:00:00Z'),('condition_before',None)]:
   with self.subTest(key=key):
    r=custody();r[key]=val
    with self.assertRaises(ContractError):evaluate([r])
 def test_preparation_not_skipped(self):
  c=custody('R01')
  with self.assertRaises(ContractError):evaluate([c])
  p=header('preparation','R01');p.update({k:'SYNTHETIC_'+k for k in ['supplier_lot','wafer_die_id','process_revision','contact_release','doping_release','encapsulation_condition','release_id']});p.update({'chip_id':c['chip_id'],'specialist_release_accepted':True,'process_recipe':None});self.assertEqual(evaluate([c,p])['status'],'SYNTHETIC_METADATA_ACCEPTED')
  p['process_recipe']='operating recipe'
  with self.assertRaises(ContractError):evaluate([c,p])
 def test_positive_analysis_metadata(self):
  for op in ['R12','R13']:self.assertEqual(evaluate([analysis(op)])['status'],'SYNTHETIC_METADATA_ACCEPTED')
 def test_analysis_holds_and_covariance(self):
  for key,val in [('unresolved_equation_holds',['C05']),('unresolved_equation_holds',['C13']),('unresolved_equation_holds',['C04']),('qualified_method_revision',None),('covariance_record',None),('source_outcome_ids',['O14']),('numerical_analysis_performed',True),('independent_cycle_count',3),('derived_paths_are_independent',True),('claims_exact_absolute_quantization',True),('branch_statuses',{})]:
   with self.subTest(key=key,val=val):
    r=analysis('R13');r[key]=val
    with self.assertRaises(ContractError):evaluate([r])
 def test_partial_failed_closeout_positive(self):self.assertEqual(evaluate([closeout_fixture()])['status'],'SYNTHETIC_METADATA_ACCEPTED')
 def test_closeout_negative(self):
  for key,val in [('terminal_acknowledged_jobs',['SYNTHETIC_JOB_A']),('pending_jobs',['OTHER']),('analysis_success_required',True),('safe_basis','stop_requested'),('safe_basis','green_icon'),('safe_basis','elapsed_timer'),('custody_accepted',False),('storage_accepted',False),('lease_release_ack',False),('branch_statuses',{}),('physical_release_performed',True),('post_condition_id',None)]:
   with self.subTest(key=key,val=val):
    r=closeout_fixture();r[key]=val
    with self.assertRaises(ContractError):evaluate([r])
 def test_every_safe_channel_required(self):
  for key in SAFE_CHANNELS:
   with self.subTest(key=key):
    r=closeout_fixture();r['independent_safety_evidence'].pop(key)
    with self.assertRaises(ContractError):evaluate([r])
 def test_same_receipt_all_safety_channels_rejected(self):
  r=closeout_fixture();r['independent_safety_evidence']={x:'SYNTHETIC_OBS_SAME' for x in SAFE_CHANNELS}
  with self.assertRaises(ContractError):evaluate([r])

if __name__=='__main__':unittest.main()
