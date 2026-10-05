"""Author finite fixtures, positive paths and adversarial bookkeeping checks."""
import copy, unittest
import contract as C

def receipt(f, kind):return next(r for r in f['records'] if r['kind']==kind)
class AuthorContractTests(unittest.TestCase):
 def reject(self, operation, change, branch='B01'):
  f=C.fixture(branch,operation);a=C.action_for(operation,f);change(f,a)
  with self.assertRaises(C.ContractError):C.check(a,f)
 def test_all_thirteen_experimental_operations_for_all_five_branches(self):
  for branch in C.EXPERIMENTS:
   for operation in C.OPERATIONS:
    if operation=='R11':continue
    with self.subTest(branch=branch,operation=operation):
     f=C.fixture(branch,operation);r=C.check(C.action_for(operation,f),f)
     self.assertEqual(r['status'],'SYNTHETIC_ACCEPT');self.assertFalse(r['physical_execution_enabled']);self.assertEqual(r['real_world_state'],'HOLD_QUALIFICATION')
 def test_four_numerical_source_review_paths(self):
  for branch in C.NUMERICAL:
   f=C.fixture(branch,'R11');self.assertEqual(C.check(C.action_for('R11',f),f)['status'],'SYNTHETIC_ACCEPT')
 def test_actor_cannot_supply_values_or_qualification(self):
  for key,value in [('physical_execution_enabled',True),('qualified',True),('repeat_count',2),('observations',{}),('receipt',{})]:
   self.reject('R07',lambda f,a:a.update({key:value}))
 def test_unknown_duplicate_or_missing_evidence(self):
  for ids in ([],['unregistered'],['plan_receipt','plan_receipt']):self.reject('R07',lambda f,a:a.update(evidence_ids=ids))
 def test_unregistered_or_wrong_role_issuer(self):
  for issuer in ('actor','safety_synthetic_authority'):
   self.reject('R07',lambda f,a:receipt(f,'calibration').update(issuer=issuer))
 def test_command_acknowledgement_cannot_be_observation(self):
  for status in ('requested','acknowledged','pending'):
   self.reject('R08',lambda f,a:receipt(f,'source_observed').update(status=status))
 def test_every_scope_field_is_bound(self):
  for key in C.SCOPE:self.reject('R07',lambda f,a:receipt(f,'calibration')['scope'].update({key:'foreign'}))
 def test_receipt_times_are_finite_and_current(self):
  for field,value in [('observed_at',101),('valid_until',99),('observed_at',float('nan')),('valid_until',float('inf')),('observed_at',True)]:
   self.reject('R07',lambda f,a:receipt(f,'calibration').update({field:value}))
 def test_receipt_schema_exact(self):
  self.reject('R07',lambda f,a:receipt(f,'calibration').update(authenticated=True))
 def test_real_evidence_never_authenticated_by_mock(self):
  self.reject('R07',lambda f,a:receipt(f,'calibration').update(synthetic=False))
 def test_missing_plan_repeats_not_inferred(self):
  for n in (None,0,-1,True,2.0):
   def change(f,a):f['plan']['repeat_count']=n;receipt(f,'plan')['payload']['repeat_count']=n
   self.reject('R07',change)
 def test_frames_points_cells_are_not_repeats(self):
  for unit in ('frame','movie_frame','cell','point'):
   def change(f,a):f['plan']['repeat_unit']=unit;receipt(f,'plan')['payload']['repeat_unit']=unit
   self.reject('R07',change)
 def test_source_outcome_not_a_pass_constant(self):
  def change(f,a):f['plan']['scientific_thresholds']={'paper_match':True};receipt(f,'plan')['payload']['scientific_thresholds']={'paper_match':True}
  self.reject('R07',change)
 def test_array_membership_and_rejected_identity_preserved(self):
  self.reject('R04',lambda f,a:receipt(f,'array')['payload'].update(member_ids=['x','x']))
  self.reject('R04',lambda f,a:receipt(f,'array')['payload'].update(rejected_ids=['synthetic_member_a']))
 def test_support_and_lease_required(self):
  for key,val in [('accepted',False),('supported',False),('exclusive_lease','foreign'),('lease_retained',False)]:
   self.reject('R05',lambda f,a:receipt(f,'support')['payload'].update({key:val}))
 def test_custody_does_not_move_before_receiver_acceptance(self):
  self.reject('R03',lambda f,a:receipt(f,'custody')['payload'].update(receiver_accepted=False))
 def test_calibration_invalidations_hold(self):
  for event in ('remount','array_replacement','optics_moved','clock_break','support_fault'):
   self.reject('R07',lambda f,a:receipt(f,'calibration')['payload'].update(invalidations=[event]))
 def test_no_lever_arm_inference(self):
  self.reject('R06',lambda f,a:receipt(f,'calibration')['payload'].update(effective_lever_inferred_from_rod=True))
 def test_sign_coordinate_and_unit_holds(self):
  for key,val in [('sign_tested',False),('source_unit','m'),('response_unit','deg'),('separate_transforms',False)]:
   self.reject('R06',lambda f,a:receipt(f,'coordinates')['payload'].update({key:val}))
 def test_clock_alignment_and_continuity(self):
  self.reject('R06',lambda f,a:receipt(f,'clock')['payload'].update(residual_error=0.03))
  self.reject('R06',lambda f,a:receipt(f,'clock')['payload'].update(continuous_epoch=False))
 def test_unknown_service_and_duplicate_admission_hold(self):
  self.reject('R07',lambda f,a:receipt(f,'capture_ready')['payload'].update(observed_service_status='UNKNOWN'))
  self.reject('R07',lambda f,a:receipt(f,'capture_ready')['payload'].update(duplicate_request=True))
 def test_numerical_branches_cannot_enter_physical_route(self):
  for operation in C.OPERATIONS:
   if operation in ('R01','R11'):continue
   self.reject(operation,lambda f,a:None,'A03')
 def test_requested_pose_is_not_observed(self):
  for branch in ('B04','B05'):
   self.reject('R08',lambda f,a:receipt(f,'measurement')['payload'].update(source_pose_kind='commanded'),branch)
 def test_measurement_lost_tracking_and_force_laundering(self):
  for key,val in [('tracking_valid',False),('physical_quantity','force'),('unit','N'),('calibration_current',False)]:
   self.reject('R08',lambda f,a:receipt(f,'measurement')['payload'].update({key:val}))
 def test_full_phases_and_condition_inventory(self):
  self.reject('R08',lambda f,a:receipt(f,'measurement')['payload'].update(phases=['on']))
  self.reject('R08',lambda f,a:receipt(f,'measurement')['payload'].update(conditions=['condition_alpha']),'B05')
 def test_analysis_raw_hash_and_failure_retention(self):
  self.reject('R09',lambda f,a:receipt(f,'analysis')['payload'].update(raw_parent_hashes=['0'*64]))
  self.reject('R09',lambda f,a:receipt(f,'analysis')['payload'].update(failed_attempts_retained=False))
 def test_baseline_must_be_camera_raw_parent(self):
  self.reject('R09',lambda f,a:receipt(f,'baseline')['payload'].update(raw_parent_id='raw_source_synthetic'))
 def test_flip_needs_distinct_mount_and_calibration(self):
  self.reject('R09',lambda f,a:receipt(f,'analysis')['payload']['orientation_pair'].update(mount_epochs=['same','same']),'B03')
 def test_every_safety_domain_is_independent_observed(self):
  for kind in C.SAFE:
   for key,val in [('observed_safe',False),('independent',False),('command_only',True),('safe_access_qualified',False)]:
    self.reject('R12',lambda f,a:receipt(f,kind)['payload'].update({key:val}))
 def test_closeout_cannot_omit_failed_or_pending_attempts(self):
  self.reject('R14',lambda f,a:receipt(f,'archive')['payload'].update(attempt_ids=[]))
  self.reject('R12',lambda f,a:f['attempts'][0].update(status='UNCERTAIN'))
 def test_unknown_final_custody_blocks_completion(self):
  self.reject('R14',lambda f,a:receipt(f,'archive')['payload'].update(final_custody={}))
 def test_quarantine_is_valid_accepted_closeout(self):
  f=C.fixture('B01','R14');receipt(f,'custody_return')['payload']['final_state']='QUARANTINED_ACCEPTED';receipt(f,'archive')['payload']['final_custody'][f['context']['specimen_id']]['state']='QUARANTINED_ACCEPTED'
  self.assertEqual(C.check(C.action_for('R14',f),f)['status'],'SYNTHETIC_ACCEPT')
 def test_store_does_not_alias_input_or_output(self):
  f=C.fixture();store=C.EvidenceStore(f['records']);rid=f['records'][0]['id'];f['records'][0]['payload'].clear();first=store.get(rid);self.assertTrue(first['payload']);first['payload'].clear();self.assertTrue(store.get(rid)['payload'])
 def test_admission_and_downstream_are_distinct_stages(self):
  f=C.fixture('B01','R07')
  with self.assertRaises(C.ContractError):C.check(C.action_for('R08',f),f)
  f=C.fixture('B01','R08')
  with self.assertRaises(C.ContractError):C.check(C.action_for('R07',f),f)
 def test_frozen_operation_receipt_contract_matches_code(self):
  import json
  from pathlib import Path
  ops=json.loads((Path(__file__).resolve().parents[1]/'operations.json').read_text())['operations']
  for op in ops:self.assertEqual(set(op['required_receipt_types']),set(C.KINDS[op['id']]))
if __name__=='__main__':unittest.main()
