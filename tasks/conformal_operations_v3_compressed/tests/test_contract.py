"""Author tests of arbitrary synthetic metadata; not physical qualification."""
import unittest,copy
import contract as c
class ContractTests(unittest.TestCase):
 def setUp(self):self.r=c.synthetic_registry();self.ctx=copy.deepcopy(c.CTX)
 def test_full_pinned_replay(self):
  r=c.evaluate(c.synthetic_messages());self.assertEqual(r['operation_templates_checked'],16);self.assertFalse(r['physical_execution']);self.assertEqual(r['validated_runnable_whole_paper_tasks'],0)
 def test_supported_hold_failure_closeout(self):self.assertTrue(c.closeout(c.synthetic_closeout(True)))
 def test_safe_return_failure_closeout(self):self.assertTrue(c.closeout(c.synthetic_closeout(False)))
 def test_actor_inject_sensor_rejected(self):
  m=c.synthetic_messages();m[8]['safe_state']=True
  with self.assertRaises(c.GuardError):c.evaluate(m)
 def test_actor_reorder_rejected(self):
  m=c.synthetic_messages();m[2],m[3]=m[3],m[2]
  with self.assertRaises(c.GuardError):c.evaluate(m)
 def test_actor_duplicate_rejected(self):
  m=c.synthetic_messages();m[1]['event_id']=m[0]['event_id']
  with self.assertRaises(c.GuardError):c.evaluate(m)
 def test_actor_evidence_rejected(self):
  m=c.synthetic_messages();m[0]['evidence_id']='invented'
  with self.assertRaises(c.GuardError):c.evaluate(m)
 def test_modified_registry_rejected(self):
  self.r['R13']['fit_squared_residual']=0
  with self.assertRaises(c.GuardError):c.evaluate(c.synthetic_messages(),self.r)
 def test_truncated_replay(self):
  with self.assertRaises(c.GuardError):c.evaluate(c.synthetic_messages()[:-1])
 def test_request_is_not_completion(self):
  self.r['R02']['status']='requested'
  with self.assertRaises(c.GuardError):c.preparation(self.r['R02'],self.ctx)
 def test_wrong_specimen_preparation(self):
  self.r['R02']['context']['specimen_id']='different'
  with self.assertRaises(c.GuardError):c.preparation(self.r['R02'],self.ctx)
 def test_bridge_explicit_treatment_policy(self):
  x=self.r['R04'];x['context']['branch_id']='B03';self.ctx['branch_id']='B03';x['bridge_treatment_policy_id']='bridge-approved';self.assertTrue(c.contact(x,self.ctx))
 def test_bridge_cannot_inherit_foot_treatment(self):
  x=self.r['R04'];x['context']['branch_id']='B03';self.ctx['branch_id']='B03'
  with self.assertRaises(c.GuardError):c.contact(x,self.ctx)
 def test_qualified_treatment_complete(self):
  x=self.r['R04'];x.update(method='qualified_service_treatment',material_identity='approved-material',sds_review_id='sds',application_service_id='service',cleanup_policy_id='cleanup',closed_qualified_service=True);self.assertTrue(c.contact(x,self.ctx))
 def test_qualified_treatment_missing_identity(self):
  x=self.r['R04'];x.update(method='qualified_service_treatment',material_identity=None,sds_review_id='sds',application_service_id='service',cleanup_policy_id='cleanup',closed_qualified_service=True)
  with self.assertRaises(c.GuardError):c.contact(x,self.ctx)
 def test_aborted_loading_only_retained(self):
  x=self.r['R09'];x['frames']=x['frames'][:1];x['expected_frame_ids']=['f0'];x['machine_event_ids']=['m0'];x.update(aborted=True,failure_id='failure',partial_data_retained=True);self.assertTrue(c.acquisition(x,self.ctx))
 def test_frames_mapped_but_missing(self):
  self.r['R09']['frames'].pop()
  with self.assertRaises(c.GuardError):c.acquisition(self.r['R09'],self.ctx)
 def test_wrong_frame_clock(self):
  self.r['R09']['frames'][1]['machine_time']=99
  with self.assertRaises(c.GuardError):c.acquisition(self.r['R09'],self.ctx)
 def test_frame_wrong_run(self):
  self.r['R09']['frames'][0]['run_id']='foreign'
  with self.assertRaises(c.GuardError):c.acquisition(self.r['R09'],self.ctx)
 def test_frame_unload_removed(self):
  self.r['R09']['frames'][1]['phase']='loading'
  with self.assertRaises(c.GuardError):c.acquisition(self.r['R09'],self.ctx)
 def test_frame_inverted_phase_order(self):
  self.r['R09']['frames'][0]['phase']='unloading';self.r['R09']['frames'][1]['phase']='loading'
  with self.assertRaises(c.GuardError):c.acquisition(self.r['R09'],self.ctx)
 def test_frame_duplicate_expected(self):
  self.r['R09']['expected_frame_ids']=['f0','f0']
  with self.assertRaises(c.GuardError):c.acquisition(self.r['R09'],self.ctx)
 def test_raw_not_retained(self):
  self.r['R09']['frames'][1]['retained_original']=False
  with self.assertRaises(c.GuardError):c.acquisition(self.r['R09'],self.ctx)
 def test_recovery_reuse_qualified(self):
  self.r['R10'].update(disposition='reuse_qualified',recovery_acceptance_receipt_id='accepted',recovery_criteria_passed=True);self.assertTrue(c.recovery(self.r['R10'],self.ctx))
 def test_recovery_reuse_unqualified(self):
  self.r['R10']['disposition']='reuse_qualified'
  with self.assertRaises(c.GuardError):c.recovery(self.r['R10'],self.ctx)
 def test_replacement_full_preparation(self):
  self.r['R11'].update(new_specimen_id='new-specimen',preparation_reentry=['R02','R03','R04'],old_preparation_receipts_reused=False);self.assertTrue(c.fixture_change(self.r['R11'],self.ctx))
 def test_replacement_missing_preparation(self):
  self.r['R11']['new_specimen_id']='new-specimen'
  with self.assertRaises(c.GuardError):c.fixture_change(self.r['R11'],self.ctx)
 def test_changed_treatment_reentry(self):
  self.r['R11'].update(treatment_or_conditioning_changed=True,preparation_reentry=['R03','R04']);self.assertTrue(c.fixture_change(self.r['R11'],self.ctx))
 def test_changed_treatment_missing_reentry(self):
  self.r['R11']['treatment_or_conditioning_changed']=True
  with self.assertRaises(c.GuardError):c.fixture_change(self.r['R11'],self.ctx)
 def test_geometry_verified_with_receipt(self):
  self.r['R13'].update(global_geometry_status='verified_by_qualified_method',global_geometry_receipt_id='geometry',global_geometry_claim=True);self.assertTrue(c.analysis(self.r['R13'],self.ctx))
 def test_geometry_verified_without_receipt(self):
  self.r['R13']['global_geometry_status']='verified_by_qualified_method'
  with self.assertRaises(c.GuardError):c.analysis(self.r['R13'],self.ctx)
 def test_detF_nan(self):
  self.r['R13']['detF_min']=float('nan')
  with self.assertRaises(c.GuardError):c.analysis(self.r['R13'],self.ctx)
 def test_nonmanual_physical_claim(self):
  self.r['R14']['branch_status']['B08']='physical_completed'
  with self.assertRaises(c.GuardError):c.nonmanual(self.r['R14'])
 def test_frames_as_repeats(self):
  self.r['R15']['unit']='frames'
  with self.assertRaises(c.GuardError):c.repeats(self.r['R15'],self.r['R01'])
 def test_missing_branch_repeat(self):
  self.r['R15']['runs'].pop()
  with self.assertRaises(c.GuardError):c.repeats(self.r['R15'],self.r['R01'])
 def test_retry_fresh_preserved(self):
  old={'attempt_id':'a','run_id':'r','raw_manifest_digest':'raw','failure_id':'fail','policy_id':'policy'};p={'new_attempt_id':'b','new_run_id':'s','new_raw_manifest_digest':'newraw','prior_failure_id':'fail','current_calibration_id':'cal','policy_id':'policy','old_raw_retained':True,'authorized_by_frozen_plan':True};self.assertTrue(c.retry(p,old))
 def test_retry_reuses_run_rejected(self):
  old={'attempt_id':'a','run_id':'r','raw_manifest_digest':'raw','failure_id':'fail','policy_id':'policy'};p={'new_attempt_id':'b','new_run_id':'r','new_raw_manifest_digest':'newraw','prior_failure_id':'fail','current_calibration_id':'cal','policy_id':'policy','old_raw_retained':True,'authorized_by_frozen_plan':True}
  with self.assertRaises(c.GuardError):c.retry(p,old)
 def test_hold_not_safe_return(self):
  x=c.synthetic_closeout(True);x['execution_complete']=True
  with self.assertRaises(c.GuardError):c.closeout(x)
 def test_hold_retains_open_lease(self):
  x=c.synthetic_closeout(True);x['active_leases']=[]
  with self.assertRaises(c.GuardError):c.closeout(x)
 def test_safe_return_occupied(self):
  x=c.synthetic_closeout();x['station_occupied']=True
  with self.assertRaises(c.GuardError):c.closeout(x)

MUTATIONS={
'R01':{'frozen_before_outcomes':False,'outcomes_seen':1,'independent_specimens':True,'runs_per_condition':0,'repeat_unit':'frames','reset_policy_id':None,'repeat_until_good':True},
'R02':{'closed_qualified_service':False,'dimensions_accepted':False,'condition_accepted':False,'source_cad_inferred_from_figure':True,'pad_layout_revision':None,'safe_release_receipt_id':None},
'R03':{'locked':False,'geometry_verified':False,'drawing_revision':None},
'R04':{'history_retained':False,'condition_accepted':False,'unknown_powder_handling':True,'method':'unknown-powder'},
'R05':{'destination_empty':False,'supported':False,'retained':False,'safe_release_observed':False,'moving_or_loaded':True,'grasp_surface':'hinge','source_carrier':'foreign'},
'R06':{'interlock_ready':False,'fixture_locked':False,'source_stroke_as_safety_limit':True,'qualified_limits':False,'force_limit':0,'speed_limit':float('inf'),'contact_zero_id':'ref'},
'R07':{'field_of_view_accepted':False,'focus_accepted':False,'visible_square_ids':[],'source_accuracy_used_as_calibration':True},
'R08':{'capture_ready':False,'buffer_ready':False,'mechanics_ready':False,'active_resources':['S05'],'foreign_leases':['foreign'],'machine_start_time':4,'clock_scale':0,'phase_policy':['loading']},
'R09':{'drop_events_accounted':False,'source_400_forced':True,'source_playback_as_acquisition_clock':True,'clock_scale':0},
'R10':{'unloaded_observed':False,'disarmed_observed':False,'new_conditioning_state_id':'synthetic-state-1','history_retained':False,'virgin_restored_by_unload':True,'completed_cycle_count':0},
'R11':{'disarmed_observed':False,'active_leases':['S05'],'new_fixture_id':'synthetic-foot','new_configuration_epoch':1,'invalidated':['mechanics'],'new_run_id':'synthetic-run-1','history_retained':False},
'R12':{'raw_immutable':False,'rejected_tracks_retained':False,'outcome_driven_filtering':True,'retained_phases':['unloading'],'source_code_inspected_or_independent_validated':False},
'R13':{'modality':'numerical','policy_frozen_before_outcomes':False,'resolved_conflicts':[],'silent_source_correction':True,'area_variable':'alpha','linear_variable':'J_area','detF_min':-1,'local_inversion_or_collapse':True,'global_geometry_claim':True,'boundary_closed':False,'simply_connected_domain':False,'boundary_sampling_qualified':False,'boundary_alpha_min':0,'interior_displacements_used_for_inference_fit':True,'gauge_source':'interior_optimized','fit_coefficient_count':30,'boundary_coefficient_count':10,'conditioning_accepted':False,'fit_squared_displacement':0,'inference_squared_residual':-1,'fit_result_id':'inference','global_99_percent_threshold':True,'ideal_alpha_as_safety_limit':True},
'R14':{'conflicts':['C01'],'source_archives_inspected':True,'source_solver_executed':True,'physical_actuator_invented':True,'printed_units_preserved':False,'final_figure_equivalence':'verified'},
'R15':{'failed_runs_retained':False,'order_policy_followed_or_deviation_recorded':False,'specimen_ids':[],'policy_id':'other'},
'R16':{'raw_and_failures_retained':False,'scientific_success_required':True,'physical_execution_claim':True,'whole_paper_success_claim':True,'safe_release_observed':False,'destination_identity_verified':False}}
FUNCS={'R01':c.policy,'R02':c.preparation,'R03':c.fixture,'R04':c.contact,'R05':c.custody,'R06':c.mechanics,'R07':c.imaging,'R08':c.arming,'R09':c.acquisition,'R10':c.recovery,'R11':c.fixture_change,'R12':c.tracking,'R13':c.analysis,'R14':c.nonmanual,'R15':c.repeats,'R16':c.closeout}
def mutation_test(op,key,value):
 def test(self):
  r=c.synthetic_registry();r[op][key]=value;fn=FUNCS[op];args=([r[op],r['R01']] if op=='R15' else [r[op]] if op in ('R01','R14','R16') else [r[op],copy.deepcopy(c.CTX)])
  with self.assertRaises(c.GuardError):fn(*args)
 return test
for op,fields in MUTATIONS.items():
 for key,value in fields.items():setattr(ContractTests,'test_mutation_'+op+'_'+key,mutation_test(op,key,value))
if __name__=='__main__':unittest.main()
