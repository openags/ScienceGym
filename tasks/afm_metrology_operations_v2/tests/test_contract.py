import copy, unittest
from contract import fixture,validate,B

class ContractTests(unittest.TestCase):
 def test_every_branch(self):
  for b in B:
   with self.subTest(branch=b):self.assertEqual(validate(*fixture([b])),[])
 def test_all_branches(self):self.assertEqual(validate(*fixture(list(B))),[])
 def rejected(self,edit):
  c,e=fixture(list(B));edit(c,e);self.assertTrue(validate(c,e))
 def test_production_and_whole_history_claims(self):
  for field in ['production_authority','whole_historical_route_complete','scientific_replication']:
   self.rejected(lambda c,e,f=field:c.__setitem__(f,True))
 def test_missing_qualification_cards(self):self.rejected(lambda c,e:c['cards'].pop('U_CONTACT'))
 def test_stale_qualification_card(self):self.rejected(lambda c,e:c['cards']['U_CAMERA'].__setitem__('revision','old'))
 def test_missing_fabricated_input(self):self.rejected(lambda c,e:c['input_qualification'].__setitem__('prefabricated_array',False))
 def test_fabrication_completion_invented(self):self.rejected(lambda c,e:c['input_qualification'].__setitem__('fabrication_performed',True))
 def test_dependency_omission(self):self.rejected(lambda c,e:c['jobs'].pop('ARRAY_CAL'))
 def test_dependency_rewrite(self):self.rejected(lambda c,e:c['jobs']['ARROW_RASTER'].__setitem__('parents',[]))
 def test_changed_optics_invalidates_calibration(self):self.rejected(lambda c,e:c['jobs']['ARROW_LINE']['binding'].__setitem__('setup_version','Olympus_swapped_in'))
 def test_crossed_target_and_specimen(self):
  for field in ['target_id','region_id','specimen_id','carrier_id','mount_version','calibration_id','metric']:
   self.rejected(lambda c,e,f=field:c['jobs']['ARROW_RASTER']['binding'].__setitem__(f,'wrong'))
 def test_omit_or_duplicate_events(self):
  self.rejected(lambda c,e:e.pop());self.rejected(lambda c,e:e.insert(2,copy.deepcopy(e[1])))
 def test_actor_spoof(self):self.rejected(lambda c,e:e[0].__setitem__('success',True))
 def test_contact_acquisition_guard(self):
  def edit(c,e):
   o=next(x for x in c['observations'].values() if x['phase'].startswith('ACQUIRE:'));o['stationary']=False
  self.rejected(edit)
 def test_contact_move_guard(self):
  def edit(c,e):
   o=next(x for x in c['observations'].values() if x['phase'].startswith('MOVE:'));o['contact_state']='contact'
  self.rejected(edit)
 def test_withdraw_is_not_release(self):
  def edit(c,e):
   o=next(x for x in c['observations'].values() if x['phase'].startswith('VERIFY_RELEASE:'));o['force_release_measured']=False
  self.rejected(edit)
 def test_release_phase_omission(self):
  def edit(c,e):e.pop(next(i for i,x in enumerate(e) if x['phase'].startswith('VERIFY_RELEASE:')))
  self.rejected(edit)
 def test_no_baseline(self):
  def edit(c,e):e.pop(next(i for i,x in enumerate(e) if x['phase']=='BASELINE'))
  self.rejected(edit)
 def test_bad_observation_bindings(self):
  for field,val in [('binding',{}),('attempt_id','old'),('authority','actor'),('record_hash','bad'),('source_kind','observed_experiment'),('support_retained',False),('damage_state','unknown'),('baseline_current',False)]:
   self.rejected(lambda c,e,f=field,v=val:c['observations']['EV1'].__setitem__(f,v))
 def test_missing_terminal_evidence(self):
  for phase,key in [('INSPECT','inspection_current'),('ARCHIVE','archive_complete'),('CLEAN_STORE','cleanup_complete')]:
   def edit(c,e,p=phase,k=key):next(o for o in c['observations'].values() if o['phase']==p)[k]=False
   self.rejected(edit)
 def test_wrong_metric_for_single_optics(self):
  def edit(c,e):next(o for o in c['observations'].values() if o['job_id']=='SINGLE_OPTICS')['source_metric_used']='main_normalized_brightness'
  self.rejected(edit)
 def test_reduced_fixture_not_source_scan(self):self.rejected(lambda c,e:c['jobs']['ARROW_RASTER']['schedule'].__setitem__('full_source_scan',True))
 def test_conflict_omission(self):self.rejected(lambda c,e:c['source_conflicts_preserved'].remove('C_SCALE'))
 def test_contact_exchange_and_unknown_state(self):
  for phase in ['DOCK','MOUNT','REGISTER','SETUP_CHECK','CAL_FIT']:
   for state in ['contact','unknown']:
    def edit(c,e,p=phase,v=state):next(o for o in c['observations'].values() if o['phase']==p)['contact_state']=v
    self.rejected(edit)
 def test_probe_target_custody_separate(self):
  def edit(c,e):next(o for o in c['observations'].values() if o['phase']=='FINAL_PROBE_RETRIEVE')['custody_asset_role']='exchange_specimen'
  self.rejected(edit)
 def test_final_probe_cleanup_and_cal_invalidation_required(self):
  for phase in ['FINAL_PROBE_RETRIEVE','FINAL_PROBE_INSPECT','FINAL_CAL_INVALIDATE','FINAL_SESSION_ARCHIVE','FINAL_SESSION_CLEAN_STORE']:
   def edit(c,e,p=phase):e.pop(next(i for i,x in enumerate(e) if x['phase']==p))
   self.rejected(edit)
 def test_early_calibration_invalidation_rejected(self):
  def edit(c,e):next(o for o in c['observations'].values() if o['phase']=='CLEAN_STORE')['calibration_invalidated']=True
  self.rejected(edit)
 def test_unsettled_mount_rejected(self):
  def edit(c,e):next(o for o in c['observations'].values() if o['phase']=='MOUNT')['stationary']=False
  self.rejected(edit)
 def test_episode_replay_rejected(self):
  self.rejected(lambda c,e:c.__setitem__('episode_id','synthetic_episode_other'))
  self.rejected(lambda c,e:c['jobs']['ARROW_RASTER'].__setitem__('episode_id','synthetic_episode_other'))
  self.rejected(lambda c,e:c['observations']['EV1'].__setitem__('episode_id','synthetic_episode_other'))
 def test_extra_context_rejected(self):
  for key in ['actor_targets_exposed','physical_execution','unknown']:
   self.rejected(lambda c,e,k=key:c.__setitem__(k,True))
 def test_distinct_episode_records(self):
  a,ea=fixture(['ARROW_RASTER'],'synthetic_episode_A');b,eb=fixture(['ARROW_RASTER'],'synthetic_episode_B')
  self.assertEqual(validate(a,ea),[]);self.assertEqual(validate(b,eb),[])
  a['observations']['EV1']=b['observations']['EV1'];self.assertTrue(validate(a,ea))
 def test_boolean_numeric_type_confusion_rejected(self):
  self.rejected(lambda c,e:c['cards']['U_CAMERA'].__setitem__('qualified_for_fixture_only',1))
  self.rejected(lambda c,e:c['input_qualification'].__setitem__('fabrication_performed',0))
  def edit(c,e):
   for j in c['jobs'].values():j['binding']['specimen_version']=True
   for o in c['observations'].values():o['binding']['specimen_version']=True
  self.rejected(edit)
 def test_malformed_fails_closed(self):
  for c,e in [(None,[]),({},[]),([],None),({'selected_branches':False},[])]:self.assertTrue(validate(c,e))
if __name__=='__main__':unittest.main()
