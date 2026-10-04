"""Original positive and hostile symbolic tests with arbitrary synthetic values."""
import unittest,copy
import contract as c
class ContractTests(unittest.TestCase):
 def rejects(self,f,*a):
  with self.assertRaises(c.ContractError):f(*a)
 def policy(self):return dict(policy_id='synthetic-policy',frozen_at=0,specimen_count=1,run_count=2,day_count=1,order_digest='order',metrics_digest='metrics',uncertainty_digest='uncertainty',stopping_digest='stop',budget_digest='budget',role='independent_policy',synthetic_only=True)
 def prep(self):return dict(stock_lot_id='lot',output_stock_lot_id='lot',drawing_revision='drawing',output_drawing_revision='drawing',job_id='job',completed_job_id='job',sample_id='sample',carrier_id='carrier',reference_id='reference',completed=True,inspected=True,safe_release=True,role='independent_fabrication',synthetic_only=True)
 def transfer(self):
  a=dict(sample_id='sample',carrier_id='carrier',stock_lot_id='lot',drawing_revision='drawing',station_id='S01',slot_id='rack',revision=0,history=['received'],mounted=False,acquiring=False,supported=True,synthetic_only=True)
  b=dict(a,station_id='S03',slot_id='dock',revision=1,history=['received','transfer'])
  r=dict(sample_id='sample',carrier_id='carrier',from_station='S01',from_slot='rack',to_station='S03',to_slot='dock',source_occupant='carrier',destination_empty=True,safe_release=True,retention=True,transform_revision='transform',role='independent_custody',synthetic_only=True)
  return a,b,r
 def ready(self,mode='photon'):
  curr=dict(epoch_id='e1',detector_mode=mode,controller_revision='ctrl',source_revision='src',configuration_id='config1',synthetic_only=True)
  r=dict(curr,receipt_id='ready',valid_interval=[0,10],allowed_branches=['B04','B05','B06','B07','B08'] if mode=='photon' else ['B02','B03'],role='independent_readiness',interlocked=True,calibration_digest='cal',uncertainty_digest='unc')
  return r,curr,'B04' if mode=='photon' else 'B03',2
 def lease(self):return dict(action='acquire',station_id='S03',lease_id='lease',run_id='run',purpose='acquisition',safe_release=False,role='independent_lease',synthetic_only=True)
 def change(self):
  old=self.ready()[1];new=dict(old,epoch_id='e2',configuration_id='config2',detector_mode='analog');r=dict(old_epoch='e1',new_epoch='e2',safe_idle=True,active_acquisition_lease=False,readiness_invalidated=True,role='independent_configuration_change',synthetic_only=True);return old,new,r
 def ledger(self,mode='photon'):
  displays=[dict(display_id='display'+str(i),pattern_digest='mask'+str(i),coefficient_id='coefficient'+str(i//2),sign=1 if i%2==0 else -1) for i in range(4)]
  m=dict(run_id='run',sample_id='sample',epoch_id='epoch',detector_mode=mode,encoding='hadamard',matrix_digest='matrix',normalization_id='norm',physical_display_convention='complementary_pairs',expected_displays=displays,declared_coefficients=2,synthetic_only=True)
  rows=[dict(x,raw_id='raw'+str(i),run_id='run',sample_id='sample',epoch_id='epoch',detector_mode=mode,dmd_index=i,controller_index=i,detector_index=i,time=i+.1,exposure=.01,value=i+2,unit='count' if mode=='photon' else 'ADC_unit',overload=False,missing=False,evidence_kind='synthetic_observation',synthetic_only=True) for i,x in enumerate(displays)]
  return m,rows,'epoch'
 def mapping(self):return dict(sensor_kind='spatial_diagnostic',sensor_id='camera',registration_digest='reg',epoch_id='epoch',empty_dock=True,object_removed=True,all_on_hash='all',uncorrected_pump_hash='uncorrected',corrected_pump_hash='corrected',representative_sfg_hash='sfg',valid_pixel_mask_hash='mask',near_zero_excluded=True,coverage_policy_digest='coverage',uncertainty_digest='unc',role='independent_spatial_diagnostic',synthetic_only=True)
 def analyses(self):
  a={k:k for k in ['result_id','raw_digest','matrix_digest','calibration_digest','correction_digest','software_digest','parameters_digest','reference_digest','metrics_digest','uncertainty_digest','residual_digest']};a.update(weights_digest=None,role='independent_analysis',kind='synthetic_analysis',synthetic_only=True);b=dict(a,result_id='denoised',weights_digest='weights',software_digest='software2',residual_digest='residual2');return a,b
 def repeats(self):return self.policy(),[dict(run_id='run'+str(i),sample_id='sample',day_id='day',reload_id='reload'+str(i),calibration_epoch='epoch',policy_id='synthetic-policy',independent_unit='acquisition_run',physical_display_count=4,frame_count=1,raw_manifest_digest='raw'+str(i),status='accepted_synthetic',synthetic_only=True) for i in range(2)]
 def retry(self):
  a=dict(run_id='run1',attempt_id='a1',sample_id='sample',series_id='series',raw_ids=['r1','r2'],prior_failure_id='failure',policy_id='policy',synthetic_only=True);b=dict(a,run_id='run2',attempt_id='a2',raw_ids=['r3','r4']);return a,b
 def closed(self):return dict(disposition='closed_synthetic',branch_status={b:'complete_synthetic' for b in c.BRANCHES},active_leases=[],dock_occupied=False,safe_access_observed=True,all_samples_accounted=True,custody='storage_or_quarantine',archive_complete=True,failed_records_retained=True,robot_outside_enclosure=True,synthetic_only=True)
 def test_policy_valid(self):self.assertTrue(c.campaign_policy(self.policy(),1)['prospective_policy_valid_synthetic'])
 def test_policy_post_outcome(self):p=self.policy();p['frozen_at']=2;self.rejects(c.campaign_policy,p,1)
 def test_policy_missing_counts(self):
  for k in ['specimen_count','run_count','day_count']:
   for v in [None,0,True,-1]:p=self.policy();p[k]=v;self.rejects(c.campaign_policy,p,1)
 def test_policy_actor_authority(self):p=self.policy();p['role']='actor';self.rejects(c.campaign_policy,p,1)
 def test_preparation_valid(self):self.assertFalse(c.preparation(self.prep())['robot_performed_fabrication'])
 def test_preparation_wrong_lineage(self):
  for k in ['output_stock_lot_id','output_drawing_revision','completed_job_id']:p=self.prep();p[k]='wrong';self.rejects(c.preparation,p)
 def test_request_not_completion(self):p=self.prep();p['role']='request';self.rejects(c.preparation,p)
 def test_preparation_missing_observation(self):
  for k in ['completed','inspected','safe_release']:p=self.prep();p[k]=False;self.rejects(c.preparation,p)
 def test_preparation_truthy_boolean(self):p=self.prep();p['safe_release']=1;self.rejects(c.preparation,p)
 def test_custody_valid(self):self.assertTrue(c.custody_transfer(*self.transfer())['custody_valid_synthetic'])
 def test_custody_loaded(self):
  for k in ['mounted','acquiring']:a,b,r=self.transfer();a[k]=True;self.rejects(c.custody_transfer,a,b,r)
 def test_custody_unsafe(self):
  for k in ['safe_release','retention','destination_empty']:a,b,r=self.transfer();r[k]=False;self.rejects(c.custody_transfer,a,b,r)
 def test_custody_wrong_receipt(self):
  for k in ['sample_id','carrier_id','from_station','from_slot','to_station','to_slot','source_occupant']:a,b,r=self.transfer();r[k]='wrong';self.rejects(c.custody_transfer,a,b,r)
 def test_custody_changes_parent(self):
  for k in ['sample_id','carrier_id','stock_lot_id','drawing_revision']:a,b,r=self.transfer();b[k]='wrong';self.rejects(c.custody_transfer,a,b,r)
 def test_custody_reset_history(self):a,b,r=self.transfer();b['history']=['new'];self.rejects(c.custody_transfer,a,b,r)
 def test_custody_skip_revision(self):a,b,r=self.transfer();b['revision']=3;self.rejects(c.custody_transfer,a,b,r)
 def test_custody_unsupported(self):a,b,r=self.transfer();b['supported']=False;self.rejects(c.custody_transfer,a,b,r)
 def test_current_readiness(self):self.assertTrue(c.readiness(*self.ready())['ready_synthetic'])
 def test_readiness_stale_each_revision(self):
  for k in ['epoch_id','detector_mode','controller_revision','source_revision','configuration_id']:r,s,b,t=self.ready();s[k]='changed';self.rejects(c.readiness,r,s,b,t)
 def test_readiness_wrong_branch(self):r,s,b,t=self.ready();self.rejects(c.readiness,r,s,'B03',t)
 def test_readiness_expired(self):r,s,b,t=self.ready();self.rejects(c.readiness,r,s,b,11)
 def test_readiness_without_interlock(self):r,s,b,t=self.ready();r['interlocked']=False;self.rejects(c.readiness,r,s,b,t)
 def test_readiness_no_branch_authorization(self):r,s,b,t=self.ready();r['allowed_branches']=['B05'];self.rejects(c.readiness,r,s,b,t)
 def test_readiness_request_not_authority(self):r,s,b,t=self.ready();r['role']='request';self.rejects(c.readiness,r,s,b,t)
 def b05policy(self):return dict(branch_id='B05',epoch_id='e1',readiness_id='ready',detector_mode='photon',exposure_policy_digest='exposure',budget_policy_digest='budget',provenance='approved_authored_departure',role='independent_branch_policy',synthetic_only=True)
 def test_b05_explicit_mode_not_source_equivalence(self):r,s,b,t=self.ready();self.assertFalse(c.readiness(r,s,'B05',t,self.b05policy())['source_equivalence_established'])
 def test_b05_no_implicit_inheritance(self):r,s,b,t=self.ready();self.rejects(c.readiness,r,s,'B05',t)
 def test_b05_wrong_policy_epoch(self):r,s,b,t=self.ready();p=self.b05policy();p['epoch_id']='old';self.rejects(c.readiness,r,s,'B05',t,p)
 def test_b05_missing_exposure(self):r,s,b,t=self.ready();p=self.b05policy();p['exposure_policy_digest']=None;self.rejects(c.readiness,r,s,'B05',t,p)
 def test_b05_no_spatial_camera(self):r,s,b,t=self.ready();r['detector_mode']=s['detector_mode']='spatial_diagnostic';p=self.b05policy();p['detector_mode']='spatial_diagnostic';self.rejects(c.readiness,r,s,'B05',t,p)
 def test_lease_exclusive(self):r=self.lease();s=c.lease_transition({},r);self.rejects(c.lease_transition,s,r)
 def test_lease_close(self):r=self.lease();s=c.lease_transition({},r);r.update(action='release',safe_release=True);self.assertEqual(c.lease_transition(s,r),{})
 def test_lease_wrong_owner(self):r=self.lease();s=c.lease_transition({},r);r.update(action='release',safe_release=True,run_id='wrong');self.rejects(c.lease_transition,s,r)
 def test_lease_unobserved_safe(self):r=self.lease();s=c.lease_transition({},r);r.update(action='release');self.rejects(c.lease_transition,s,r)
 def test_change_requires_new_readiness(self):self.assertTrue(c.configuration_change(*self.change())['fresh_readiness_required'])
 def test_change_without_safe_idle(self):a,b,r=self.change();r['safe_idle']=False;self.rejects(c.configuration_change,a,b,r)
 def test_change_during_acquisition(self):a,b,r=self.change();r['active_acquisition_lease']=True;self.rejects(c.configuration_change,a,b,r)
 def test_change_cannot_keep_old_readiness(self):a,b,r=self.change();r['readiness_invalidated']=False;self.rejects(c.configuration_change,a,b,r)
 def test_change_cannot_reuse_epoch(self):a,b,r=self.change();b['epoch_id']=a['epoch_id'];r['new_epoch']=a['epoch_id'];self.rejects(c.configuration_change,a,b,r)
 def test_ledger_photon(self):self.assertEqual(c.pattern_ledger(*self.ledger())['physical_displays'],4)
 def test_ledger_analog(self):self.assertEqual(c.pattern_ledger(*self.ledger('analog'))['signed_coefficients'],2)
 def test_ledger_missing_display(self):m,r,e=self.ledger();r.pop();self.rejects(c.pattern_ledger,m,r,e)
 def test_ledger_extra_display(self):m,r,e=self.ledger();r.append(r[0]);self.rejects(c.pattern_ledger,m,r,e)
 def test_ledger_counter_bijection(self):
  for k in ['dmd_index','controller_index','detector_index']:m,r,e=self.ledger();r[1][k]=0;self.rejects(c.pattern_ledger,m,r,e)
 def test_ledger_wrong_raw_lineage(self):
  for k in ['run_id','sample_id','epoch_id','detector_mode','display_id','pattern_digest','coefficient_id']:m,r,e=self.ledger();r[1][k]='wrong';self.rejects(c.pattern_ledger,m,r,e)
 def test_ledger_duplicate_raw(self):m,r,e=self.ledger();r[1]['raw_id']=r[0]['raw_id'];self.rejects(c.pattern_ledger,m,r,e)
 def test_ledger_overload_missing(self):
  for k in ['overload','missing']:m,r,e=self.ledger();r[1][k]=True;self.rejects(c.pattern_ledger,m,r,e)
 def test_ledger_source_outcome_as_sensor(self):m,r,e=self.ledger();r[1]['evidence_kind']='source_reference';self.rejects(c.pattern_ledger,m,r,e)
 def test_ledger_photon_not_integer(self):
  for v in [1.2,-1,True]:m,r,e=self.ledger();r[1]['value']=v;self.rejects(c.pattern_ledger,m,r,e)
 def test_ledger_wrong_units(self):m,r,e=self.ledger();r[1]['unit']='photons_per_pulse';self.rejects(c.pattern_ledger,m,r,e)
 def test_ledger_stale_epoch(self):m,r,e=self.ledger();self.rejects(c.pattern_ledger,m,r,'changed')
 def test_ledger_nonadjacent_pairs(self):m,r,e=self.ledger();m['expected_displays'][1]['coefficient_id']='other';r[1]['coefficient_id']='other';self.rejects(c.pattern_ledger,m,r,e)
 def test_ledger_same_mask_not_complement(self):m,r,e=self.ledger();m['expected_displays'][1]['pattern_digest']='mask0';r[1]['pattern_digest']='mask0';self.rejects(c.pattern_ledger,m,r,e)
 def test_ledger_wrong_coefficient_count(self):m,r,e=self.ledger();m['declared_coefficients']=4;self.rejects(c.pattern_ledger,m,r,e)
 def test_ledger_timing_order(self):m,r,e=self.ledger();r[1]['time']=r[0]['time'];self.rejects(c.pattern_ledger,m,r,e)
 def test_ledger_zero_exposure(self):m,r,e=self.ledger();r[1]['exposure']=0;self.rejects(c.pattern_ledger,m,r,e)
 def test_ledger_random_unresolved_convention(self):m,r,e=self.ledger();m.update(encoding='random',physical_display_convention=None);self.rejects(c.pattern_ledger,m,r,e)
 def bundle(self):
  m,rows,e=self.ledger();r,curr,b,t=self.ready();curr['epoch_id']=r['epoch_id']=e;lease={'lease_id':'lease','run_id':'run','purpose':'acquisition'};return [b,m,rows,curr,r,lease,'sample',t]
 def test_acquisition_bundle(self):self.assertTrue(c.acquisition_bundle(*self.bundle())['bundle_valid_synthetic'])
 def test_bundle_wrong_current_mode(self):a=self.bundle();a[3]['detector_mode']=a[4]['detector_mode']='analog';self.rejects(c.acquisition_bundle,*a)
 def test_bundle_wrong_current_sample(self):a=self.bundle();a[6]='other';self.rejects(c.acquisition_bundle,*a)
 def test_bundle_wrong_lease_run(self):a=self.bundle();a[5]['run_id']='other';self.rejects(c.acquisition_bundle,*a)
 def test_bundle_wrong_lease_purpose(self):a=self.bundle();a[5]['purpose']='configuration_change';self.rejects(c.acquisition_bundle,*a)
 def test_bundle_stale_manifest_epoch(self):a=self.bundle();a[3]['epoch_id']=a[4]['epoch_id']='new-epoch';self.rejects(c.acquisition_bundle,*a)
 def test_b07_requires_random(self):a=self.bundle();a[0]='B07';self.rejects(c.acquisition_bundle,*a)
 def test_b04_requires_hadamard(self):a=self.bundle();a[1]['encoding']='random';self.rejects(c.acquisition_bundle,*a)
 def test_bundle_expired_raw_events(self):a=self.bundle();a[4]['valid_interval']=[0,2];self.rejects(c.acquisition_bundle,*a)
 def test_bundle_exposure_crosses_expiry(self):a=self.bundle();a[2][-1]['exposure']=20;self.rejects(c.acquisition_bundle,*a)
 def test_bundle_before_calibration(self):a=self.bundle();a[4]['valid_interval']=[1,10];self.rejects(c.acquisition_bundle,*a)
 def test_mapping(self):self.assertFalse(c.mapping_evidence(self.mapping())['full_set_sfg_proved'])
 def test_mapping_bucket_rejected(self):r=self.mapping();r['sensor_kind']='bucket';self.rejects(c.mapping_evidence,r)
 def test_mapping_requires_empty_dock(self):r=self.mapping();r['empty_dock']=False;self.rejects(c.mapping_evidence,r)
 def test_mapping_requires_no_object(self):r=self.mapping();r['object_removed']=False;self.rejects(c.mapping_evidence,r)
 def test_mapping_near_zero(self):r=self.mapping();r['near_zero_excluded']=False;self.rejects(c.mapping_evidence,r)
 def test_mapping_distinct_sfg(self):r=self.mapping();r['representative_sfg_hash']=r['uncorrected_pump_hash'];self.rejects(c.mapping_evidence,r)
 def test_analysis_pair(self):self.assertTrue(c.analysis_pair(*self.analyses())['paired_provenance_valid_synthetic'])
 def test_analysis_pair_mismatched_parents(self):
  for k in ['raw_digest','matrix_digest','calibration_digest','correction_digest','reference_digest','metrics_digest','uncertainty_digest']:a,b=self.analyses();b[k]='other';self.rejects(c.analysis_pair,a,b)
 def test_analysis_missing_weights(self):a,b=self.analyses();b['weights_digest']=None;self.rejects(c.analysis_pair,a,b)
 def test_analysis_source_truth(self):a,b=self.analyses();b['kind']='source_outcome';self.rejects(c.analysis_pair,a,b)
 def test_repeats(self):self.assertEqual(c.repeat_ledger(*self.repeats())['independent_runs'],2)
 def test_repeats_physical_displays_not_n(self):p,r=self.repeats();r[0]['physical_display_count']=1000;self.assertEqual(c.repeat_ledger(p,r)['independent_runs'],2)
 def test_repeats_pulse_n_rejected(self):p,r=self.repeats();r[0]['independent_unit']='pulse';self.rejects(c.repeat_ledger,p,r)
 def test_repeats_changed_policy(self):p,r=self.repeats();r[0]['policy_id']='new';self.rejects(c.repeat_ledger,p,r)
 def test_repeats_duplicate_run(self):p,r=self.repeats();r[1]['run_id']=r[0]['run_id'];self.rejects(c.repeat_ledger,p,r)
 def test_repeats_missing_failed_run(self):p,r=self.repeats();r.pop();self.rejects(c.repeat_ledger,p,r)
 def test_repeats_extra_sample(self):p,r=self.repeats();r[1]['sample_id']='replacement';self.rejects(c.repeat_ledger,p,r)
 def test_retry(self):self.assertTrue(c.retry(*self.retry())['failure_preserved'])
 def test_retry_reused_evidence(self):
  for k in ['run_id','attempt_id','raw_ids']:a,b=self.retry();b[k]=a[k];self.rejects(c.retry,a,b)
 def test_retry_policy_changed(self):a,b=self.retry();b['policy_id']='other';self.rejects(c.retry,a,b)
 def test_retry_failure_erased(self):a,b=self.retry();b['prior_failure_id']='other';self.rejects(c.retry,a,b)
 def test_retry_replacement(self):a,b=self.retry();b['sample_id']='new';self.rejects(c.retry,a,b);b['series_id']='new-series';self.assertTrue(c.retry(a,b)['failure_preserved'])
 def test_closed(self):self.assertTrue(c.closeout(self.closed())['fully_closed_synthetic'])
 def test_closed_with_blocked_analysis(self):r=self.closed();r['branch_status']['B07']='blocked';x=c.closeout(r);self.assertTrue(x['fully_closed_synthetic']);self.assertFalse(x['all_branch_metadata_complete'])
 def test_closed_missing_branch(self):r=self.closed();del r['branch_status']['B08'];self.rejects(c.closeout,r)
 def test_closed_dock_occupied(self):r=self.closed();r['dock_occupied']=True;self.rejects(c.closeout,r)
 def test_closed_open_lease(self):r=self.closed();r['active_leases']=['lease'];self.rejects(c.closeout,r)
 def test_closed_no_safe_observation(self):r=self.closed();r['safe_access_observed']=False;self.rejects(c.closeout,r)
 def test_closed_dropped_evidence(self):
  for k in ['all_samples_accounted','archive_complete','failed_records_retained']:r=self.closed();r[k]=False;self.rejects(c.closeout,r)
 def test_supported_hold(self):r=self.closed();r.update(disposition='supported_hold',dock_occupied=True,safe_access_observed=False,active_leases=['lease'],custody='observed_supported_hold');self.assertFalse(c.closeout(r)['fully_closed_synthetic'])
 def test_hold_preserves_occupied_lease(self):r=self.closed();r.update(disposition='supported_hold',dock_occupied=True,custody='observed_supported_hold');self.rejects(c.closeout,r)
 def test_hold_not_phantom_storage(self):r=self.closed();r['disposition']='supported_hold';self.rejects(c.closeout,r)
 def test_hold_robot_outside(self):r=self.closed();r.update(disposition='supported_hold',custody='observed_supported_hold',robot_outside_enclosure=False);self.rejects(c.closeout,r)
 def test_all_finite_fixtures(self):
  self.assertEqual(len(c.FIXTURE_IDS),10)
  for fid in c.FIXTURE_IDS:f=c.fixture(fid);x=c.evaluate(f['events'],f['registry'],fid);self.assertTrue(x['contract_passed']);self.assertEqual(x['validated_runnable_whole_paper_tasks'],0)
 def test_fixture_unknown(self):self.rejects(c.fixture,'ALL_BRANCHES:PHYSICAL_SUCCESS')
 def test_actor_extra_fields(self):
  for k in ['success','sensor_value','safe_state','qualification','raw_count']:f=c.fixture(c.FIXTURE_IDS[0]);f['events'][0][k]=True;self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_actor_forged_registry(self):f=c.fixture(c.FIXTURE_IDS[0]);next(iter(f['registry'].values()))['payload']['physical_qualified']=True;self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_actor_missing_event(self):f=c.fixture(c.FIXTURE_IDS[0]);f['events'].pop();self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_actor_duplicate(self):f=c.fixture(c.FIXTURE_IDS[0]);f['events'][1]=f['events'][0];self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_actor_reordered(self):f=c.fixture(c.FIXTURE_IDS[0]);f['events'][0],f['events'][1]=f['events'][1],f['events'][0];self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_actor_wrong_evidence(self):f=c.fixture(c.FIXTURE_IDS[0]);f['events'][1]['evidence_id']=f['events'][0]['evidence_id'];self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_finite_hostile(self):
  for x in [True,None,'1',float('nan'),float('inf'),10**10000]:self.rejects(c.finite,x)
 def test_no_physical_defaults(self):self.assertTrue(all(u['physical_default'] is None for u in c.read('unknown_parameters.json')['unknowns']))
 def test_rate_branch_separation(self):self.assertEqual(c.BRANCHES['B03']['detector_mode'],'analog');self.assertTrue(all('source_rate_reference_Hz_approx' not in x for x in c.BRANCHES['B04']['condition_slots']))
 def test_b05_unknown(self):self.assertIsNone(c.BRANCHES['B05']['detector_mode']);self.assertIn('U14',c.scope_holds('R13',['physical_execution'])['unresolved'])
 def test_hold_always_accountable(self):self.assertTrue(c.scope_holds('R21',['physical_execution'])['can_record_safe_hold'])
if __name__=='__main__':unittest.main()
