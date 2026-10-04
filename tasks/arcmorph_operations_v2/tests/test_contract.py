"""Author synthetic guard tests; source outcomes are not used as fixtures."""
import unittest,copy
import contract as c
class ContractTests(unittest.TestCase):
 def rejects(self,fn,*args):
  with self.assertRaises(c.ContractError):fn(*args)
 def custody(self):return {'stock_id':'s','specimen_id':'p','family_id':'PP','drawing_revision':'d','carrier_id':'k','station_id':'a','revision':0,'history':['baseline'],'mounted':False,'loaded':False,'supported':True,'synthetic_only':True}
 def service(self):return dict(stock_id='s',output_parent_stock_id='s',job_id='j',completed_job_id='j',drawing_revision='d',output_drawing_revision='d',receipt_role='independent_completion',completed=True,safe_release=True,supported=True,synthetic_only=True)
 def folds(self):
  p=dict(plan_id='p',family_id='PP',drawing_revision='d',edges=['e1','e2','e3'],depends_on={'e1':[],'e2':['e1'],'e3':['e2']},synthetic_only=True)
  rs=[dict(edge_id=e,plan_id='p',drawing_revision='d',actions=['support','engage','bounded_fold','release','inspect'],inspection='accepted_synthetic',receipt_id='r'+e,synthetic_only=True) for e in p['edges']];return p,rs
 def lease(self):return dict(action='acquire',device_id='device',lease_id='lease',specimen_id='p',job_id='j',safe_release=False,supported=True,synthetic_only=True)
 def pair(self):
  current={k:k+'@r1' for k in ['front_camera','front_lens','front_mount','side_camera','side_lens','side_mount','fixture','height_reference','scale_reference']}
  cal=dict(calibration_id='cal',revisions=copy.deepcopy(current),reference_ids=[current['height_reference'],current['scale_reference']],valid_interval=[0,10],role='independent_calibration',synthetic_only=True)
  t=dict(token_id='token',specimen_id='p',configuration_revision='H1',calibration_id='cal',lock_interval=[1,9],active=True,all_locks=True,stable=True,synthetic_only=True)
  rows=[dict(capture_id=role+'-capture',camera_id=current[role+'_camera'],lens_id=current[role+'_lens'],view_role=role,specimen_id='p',configuration_revision='H1',token_id='token',calibration_id='cal',file_hash=c.digest(role),time=2+i,quality_ok=True,evidence_kind='synthetic_observation',synthetic_only=True) for i,role in enumerate(['front','side'])]
  return rows,t,cal,current
 def um(self,r):return c.unmount(r,{'fixture_kind':r['fixture_kind'],'fixture_id':'fixture','specimen_id':'p','lease_id':'lease','mounted':True})
 def release(self):return dict(fixture_kind='rigid',fixture_id='fixture',specimen_id='p',operation_id='R30',lease_id='lease',load_removed=True,safe_release=True,supported=True,mounts_detached=True,fixture_empty=True,carrier_occupied=True,token_invalidated=True,synthetic_only=True)
 def ledger(self):return [dict(series_id='series',specimen_id='p',stock_id='s',configuration_id='H'+str(i),attempt_id='a'+str(i),pair_id='pair'+str(i),kind='source_aligned_slot',synthetic_only=True) for i in range(8)]
 def obs(self):return dict(pair_id='pair',raw_hashes=[c.digest('front'),c.digest('side')],height=.5,interior_radius=.8,exterior_radius=.9,uncertainties={'height':.01,'interior_radius':.02,'exterior_radius':.02},units='m',method_id='synthetic-method',kind='synthetic_observation',synthetic_only=True)
 def retry_records(self):
  a=dict(attempt_id='a1',specimen_id='p',series_id='series',token_id='t1',capture_ids=['c1','c2'],raw_hashes=[c.digest('c1'),c.digest('c2')],previous_failure_id='failure',synthetic_only=True)
  b=dict(a,attempt_id='a2',token_id='t2',capture_ids=['c3','c4'],raw_hashes=[c.digest('c3'),c.digest('c4')]);return a,b
 def closed(self):return dict(disposition='closed_synthetic',loaded=False,mounted=False,open_leases=[],supported=True,transported_to_storage=True,station_inventory_complete=True,evidence_archive_complete=True,selected_route_status={'PP_RIGID':'complete_synthetic'},synthetic_only=True)
 def test_36_finite_fixtures(self):
  self.assertEqual(len(c.FIXTURE_IDS),36)
  for fid in c.FIXTURE_IDS:
   with self.subTest(fid=fid):
    f=c.fixture(fid);r=c.evaluate(f['events'],f['registry'],fid);self.assertTrue(r['contract_passed']);self.assertEqual(r['validated_runnable_whole_paper_tasks'],0);self.assertFalse(r['physical_execution'])
 def test_unknown_fixture_rejected(self):self.rejects(c.fixture,'PP:SUCCESS')
 def test_extra_actor_fields(self):
  for key in ['success','sensor_value','safe_release','source_radius','qualification']:
   f=c.fixture('PP_RIGID:METADATA_OK');f['events'][0][key]=True;self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_registry_forgery(self):
  f=c.fixture('CS1:METADATA_OK');next(iter(f['registry'].values()))['payload']['physical_qualified']=True;self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_all_context_mutations(self):
  for key in c.CONTEXT:
   f=c.fixture('PP_RIGID:METADATA_OK');next(iter(f['registry'].values()))['context'][key]='forged';self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_missing_event(self):
  f=c.fixture('CS1:METADATA_OK');f['events'].pop();self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_duplicate_event(self):
  f=c.fixture('CS1:METADATA_OK');f['events'][1]=f['events'][0];self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_reordered_event(self):
  f=c.fixture('CS1:METADATA_OK');f['events'][0],f['events'][1]=f['events'][1],f['events'][0];self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_evidence_substitution(self):
  f=c.fixture('CS1:METADATA_OK');f['events'][1]['evidence_id']=f['events'][0]['evidence_id'];self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_synthetic_no_source_values(self):
  for fid in c.FIXTURE_IDS:
   f=c.fixture(fid);self.assertTrue(all(r['payload']['source_outcome_used'] is False for r in f['registry'].values()))
 def test_all_transport_occurrences_bound(self):
  for fid in c.FIXTURE_IDS:
   f=c.fixture(fid)
   for r in f['registry'].values():
    if r['operation_id']=='R03':self.assertTrue(r['payload']['transport_binding']['unmounted_and_unloaded_required']);self.assertIn('object_id',r['payload']['transport_binding'])
 def test_pp_eight_one_specimen(self):
  f=c.fixture('PP_RIGID:METADATA_OK');rs=[r for r in f['registry'].values() if r['operation_id']=='R18'];self.assertEqual(len(rs),8);self.assertEqual(len({r['context']['specimen_id'] for r in rs}),1)
 def test_shear_no_analysis_claim(self):
  f=c.fixture('PP_SHEAR:METADATA_OK');self.assertNotIn('R25',[e['operation_id'] for e in f['events']])
 def test_custody_good(self):
  a=self.custody();b=dict(a,station_id='b',revision=1,history=['baseline','transfer']);self.assertTrue(c.custody_transition(a,b)['custody_valid_synthetic'])
 def test_no_loaded_transport(self):
  a=self.custody();a['loaded']=True;b=dict(a,station_id='b',revision=1,history=['baseline','transfer']);self.rejects(c.custody_transition,a,b)
 def test_no_mounted_transport(self):
  a=self.custody();a['mounted']=True;b=dict(a,station_id='b',revision=1,history=['baseline','transfer']);self.rejects(c.custody_transition,a,b)
 def test_custody_history_cannot_reset(self):
  a=self.custody();b=dict(a,revision=1,history=['new']);self.rejects(c.custody_transition,a,b)
 def test_custody_parent_cannot_change(self):
  for k in ['stock_id','specimen_id','family_id','drawing_revision']:
   a=self.custody();b=dict(a,revision=1,history=['baseline','new']);b[k]='other';self.rejects(c.custody_transition,a,b)
 def test_custody_revision_monotonic(self):
  a=self.custody();b=dict(a,history=['baseline','new']);self.rejects(c.custody_transition,a,b)
 def test_carrier_cannot_switch_in_flight(self):
  a=self.custody();b=dict(a,station_id='b',carrier_id='other',revision=1,history=['baseline','new']);self.rejects(c.custody_transition,a,b)
 def test_unsupported_custody(self):
  a=self.custody();b=dict(a,supported=False,revision=1,history=['baseline','new']);self.rejects(c.custody_transition,a,b)
 def test_service_handoff(self):self.assertTrue(c.service_handoff(self.service())['synthetic_handoff_valid'])
 def test_service_request_not_completion(self):r=self.service();r['receipt_role']='request';self.rejects(c.service_handoff,r)
 def test_service_lineage_fields(self):
  for k in ['output_parent_stock_id','completed_job_id','output_drawing_revision']:
   r=self.service();r[k]='wrong';self.rejects(c.service_handoff,r)
 def test_service_without_release(self):r=self.service();r['safe_release']=False;self.rejects(c.service_handoff,r)
 def test_service_boolean_exact(self):r=self.service();r['completed']=1;self.rejects(c.service_handoff,r)
 def test_fold_complete(self):self.assertTrue(c.fold_ledger(*self.folds())['fold_ledger_complete'])
 def test_fold_order(self):p,r=self.folds();r.reverse();self.rejects(c.fold_ledger,p,r)
 def test_fold_missing_edge(self):p,r=self.folds();r.pop();self.rejects(c.fold_ledger,p,r)
 def test_fold_duplicate(self):p,r=self.folds();r[1]=copy.deepcopy(r[0]);self.rejects(c.fold_ledger,p,r)
 def test_fold_omits_support(self):p,r=self.folds();r[0]['actions'].pop(0);self.rejects(c.fold_ledger,p,r)
 def test_fold_wrong_drawing(self):p,r=self.folds();r[0]['drawing_revision']='other';self.rejects(c.fold_ledger,p,r)
 def test_fold_bad_inspection(self):p,r=self.folds();r[0]['inspection']='damaged';self.rejects(c.fold_ledger,p,r)
 def test_fold_cyclic_dependency(self):p,r=self.folds();p['depends_on']['e1']=['e3'];self.rejects(c.fold_ledger,p,r)
 def test_lease_exclusive(self):r=self.lease();s=c.lease_transition({},r);self.rejects(c.lease_transition,s,r)
 def test_lease_release(self):r=self.lease();s=c.lease_transition({},r);r.update(action='release',safe_release=True);self.assertEqual(c.lease_transition(s,r),{})
 def test_lease_wrong_specimen(self):r=self.lease();s=c.lease_transition({},r);r.update(action='release',safe_release=True,specimen_id='other');self.rejects(c.lease_transition,s,r)
 def test_lease_missing_safe_release(self):r=self.lease();s=c.lease_transition({},r);r.update(action='release');self.rejects(c.lease_transition,s,r)
 def test_lease_unique_id(self):r=self.lease();s=c.lease_transition({},r);r['device_id']='other';self.rejects(c.lease_transition,s,r)
 def test_pair_valid(self):self.assertTrue(c.capture_pair(*self.pair())['pair_valid_synthetic'])
 def test_pair_changed_revision_each_key(self):
  for k in self.pair()[3]:
   rows,t,cal,current=self.pair();current[k]='changed';self.rejects(c.capture_pair,rows,t,cal,current)
 def test_pair_stale_token(self):rows,t,cal,current=self.pair();t['active']=False;self.rejects(c.capture_pair,rows,t,cal,current)
 def test_pair_unlocked(self):rows,t,cal,current=self.pair();t['all_locks']=False;self.rejects(c.capture_pair,rows,t,cal,current)
 def test_pair_unstable(self):rows,t,cal,current=self.pair();t['stable']=False;self.rejects(c.capture_pair,rows,t,cal,current)
 def test_pair_fields_mismatch(self):
  for k in ['specimen_id','configuration_revision','token_id','calibration_id','camera_id','lens_id']:
   rows,t,cal,current=self.pair();rows[1][k]='wrong';self.rejects(c.capture_pair,rows,t,cal,current)
 def test_pair_single_view(self):rows,t,cal,current=self.pair();rows.pop();self.rejects(c.capture_pair,rows,t,cal,current)
 def test_pair_duplicate_role(self):rows,t,cal,current=self.pair();rows[1]['view_role']='front';self.rejects(c.capture_pair,rows,t,cal,current)
 def test_pair_reused_hash(self):rows,t,cal,current=self.pair();rows[1]['file_hash']=rows[0]['file_hash'];self.rejects(c.capture_pair,rows,t,cal,current)
 def test_pair_outside_lock(self):rows,t,cal,current=self.pair();rows[1]['time']=9.5;self.rejects(c.capture_pair,rows,t,cal,current)
 def test_pair_outside_calibration(self):rows,t,cal,current=self.pair();cal['valid_interval']=[0,2.5];self.rejects(c.capture_pair,rows,t,cal,current)
 def test_pair_source_substitution(self):rows,t,cal,current=self.pair();rows[0]['evidence_kind']='source_reference';self.rejects(c.capture_pair,rows,t,cal,current)
 def test_pair_blurred(self):rows,t,cal,current=self.pair();rows[1]['quality_ok']=False;self.rejects(c.capture_pair,rows,t,cal,current)
 def test_two_references(self):rows,t,cal,current=self.pair();cal['reference_ids']=['r','r'];self.rejects(c.capture_pair,rows,t,cal,current)
 def test_unmount_correct(self):self.assertTrue(self.um(self.release())['lease_may_close_synthetic'])
 def test_unmount_wrong_fixture(self):r=self.release();r['fixture_kind']='corner';self.rejects(self.um,r)
 def test_corner_unmount(self):r=self.release();r.update(fixture_kind='corner',operation_id='R22');self.assertTrue(self.um(r)['lease_may_close_synthetic'])
 def test_unmount_each_required_evidence(self):
  for k in ['load_removed','safe_release','supported','mounts_detached','fixture_empty','carrier_occupied','token_invalidated']:
   r=self.release();r[k]=False;self.rejects(self.um,r)
 def test_eight_states_one_specimen(self):r=c.repeat_ledger(self.ledger());self.assertEqual((r['distinct_specimens'],r['configuration_slots'],r['accepted_pairs']),(1,8,8))
 def test_repeat_is_not_independent_specimen(self):r=self.ledger();r.append(dict(r[0],attempt_id='again',pair_id='again',kind='authored_technical_repeat'));self.assertEqual(c.repeat_ledger(r)['distinct_specimens'],1)
 def test_replacement_cannot_continue_series(self):r=self.ledger();r[-1]['specimen_id']='new';self.rejects(c.repeat_ledger,r)
 def test_repeat_wrong_parent(self):r=self.ledger();r[-1]['stock_id']='new';self.rejects(c.repeat_ledger,r)
 def test_duplicate_pair(self):r=self.ledger();r[-1]['pair_id']=r[0]['pair_id'];self.rejects(c.repeat_ledger,r)
 def test_separate_radii(self):self.assertTrue(c.observables(self.obs())['observables_separated'])
 def test_source_values_not_observation(self):r=self.obs();r['kind']='source_reference';self.rejects(c.observables,r)
 def test_negative_radius(self):r=self.obs();r['interior_radius']=-1;self.rejects(c.observables,r)
 def test_swapped_radii(self):r=self.obs();r['interior_radius']=2;self.rejects(c.observables,r)
 def test_uncertainty_missing(self):r=self.obs();del r['uncertainties']['height'];self.rejects(c.observables,r)
 def test_uncertainty_zero(self):r=self.obs();r['uncertainties']['height']=0;self.rejects(c.observables,r)
 def test_model_field_rejected(self):r=self.obs();r['model_radius']=2;self.rejects(c.observables,r)
 def test_near_flat_discrepancy_retained(self):r=self.obs();r.update(interior_radius=20,exterior_radius=30);self.assertFalse(c.observables(r)['curve_agreement_tested'])
 def test_retry_good(self):self.assertTrue(c.retry(*self.retry_records())['failure_preserved'])
 def test_retry_old_token(self):a,b=self.retry_records();b['token_id']=a['token_id'];self.rejects(c.retry,a,b)
 def test_retry_old_hash(self):a,b=self.retry_records();b['raw_hashes'][0]=a['raw_hashes'][0];self.rejects(c.retry,a,b)
 def test_retry_failure_deleted(self):a,b=self.retry_records();b['previous_failure_id']='other';self.rejects(c.retry,a,b)
 def test_retry_replacement_new_series(self):a,b=self.retry_records();b['specimen_id']='new';self.rejects(c.retry,a,b);b['series_id']='new-series';self.assertTrue(c.retry(a,b)['failure_preserved'])
 def test_closed(self):self.assertTrue(c.closeout(self.closed())['fully_closed_synthetic'])
 def test_closed_cannot_be_loaded(self):r=self.closed();r['loaded']=True;self.rejects(c.closeout,r)
 def test_closed_cannot_be_mounted(self):r=self.closed();r['mounted']=True;self.rejects(c.closeout,r)
 def test_closed_open_lease(self):r=self.closed();r['open_leases']=['lease'];self.rejects(c.closeout,r)
 def test_closed_missing_inventory(self):r=self.closed();r['station_inventory_complete']=False;self.rejects(c.closeout,r)
 def test_closed_unattempted_branch(self):r=self.closed();r['selected_route_status']['CS1']='unattempted';self.rejects(c.closeout,r)
 def test_hold_accounting(self):r=self.closed();r.update(disposition='supported_hold',loaded=True,mounted=True,open_leases=['l'],transported_to_storage=False,selected_route_status={'PP_RIGID':'held'});self.assertFalse(c.closeout(r)['fully_closed_synthetic'])
 def test_hold_cannot_transport(self):r=self.closed();r.update(disposition='supported_hold',loaded=True);self.rejects(c.closeout,r)
 def test_hold_must_preserve_evidence(self):r=self.closed();r.update(disposition='supported_hold',transported_to_storage=False,evidence_archive_complete=False);self.rejects(c.closeout,r)
 def test_conflicts_local_model(self):self.assertEqual(c.scope_holds('R16','PP',['model_comparison'])['conflicts'],[]);self.assertIn('C10',c.scope_holds('R25','PP',['model_comparison'])['conflicts'])
 def test_geometry_conflict_family(self):self.assertIn('C01',c.scope_holds('R04','PP',['source_matched_geometry'])['conflicts']);self.assertNotIn('C01',c.scope_holds('R04','CS1',['source_matched_geometry'])['conflicts'])
 def test_extended_geometry_conflict(self):self.assertIn('C04',c.scope_holds('R07','CS2',['source_matched_geometry'])['conflicts']);self.assertNotIn('C04',c.scope_holds('R07','CS1',['source_matched_geometry'])['conflicts'])
 def test_raw_correspondence_local(self):self.assertEqual(c.scope_holds('R25','PP',['source_raw_correspondence'])['conflicts'],['C07'])
 def test_closeout_record_never_requires_model(self):r=c.scope_holds('R24','PP',['model_comparison']);self.assertEqual(r['conflicts'],[]);self.assertTrue(r['can_record_supported_hold']);self.assertFalse(r['can_perform_physical_action'])
 def test_no_invented_numeric_defaults(self):self.assertTrue(all(x['physical_default'] is None for x in c.UNKNOWNS.values()))
 def test_finite_hostile(self):
  for x in [True,False,'1',None,float('nan'),float('inf'),-float('inf'),10**10000]:self.rejects(c.finite,x)
 def test_registry_huge_integer(self):f=c.fixture('CS1:METADATA_OK');next(iter(f['registry'].values()))['payload']['extra']=10**10000;self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
if __name__=='__main__':unittest.main()
