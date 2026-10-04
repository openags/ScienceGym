import copy, unittest
from contract import BRANCHES, cases_for, fixture, validate, digest, plan_for

class PositiveContracts(unittest.TestCase):
 def test_all_branches(self):
  c,e=fixture(list(BRANCHES));r=validate(c,e);self.assertTrue(r['accepted'],r['errors']);self.assertEqual(len(e),3994)
 def test_every_branch_individually(self):
  for b in BRANCHES:
   with self.subTest(branch=b):
    c,e=fixture([b]);r=validate(c,e);self.assertTrue(r['accepted'],r['errors'])
 def test_25_nm_buffer_preserves_50_nm_cap(self):
  c,e=fixture(['STACK'],25);self.assertTrue(validate(c,e)['accepted']);layers=cases_for('STACK',25)
  self.assertEqual([x['thickness'] for x in layers if x['role']=='interstack_buffer'],[25]*9)
  self.assertEqual(layers[-1]['thickness'],50)
 def test_90_ordered_pairs(self):
  rows=cases_for('PAIRS');pairs={(r['driver'],r['loads'][0]) for r in rows};self.assertEqual(len(pairs),90)
  self.assertNotIn((1,1),pairs);self.assertIn((1,7),pairs);self.assertIn((7,1),pairs)
 def test_source_cohorts_remain_separate(self):
  self.assertNotEqual(cases_for('BASELINE')[0]['cohort'],cases_for('DUAL_TRACE')[0]['cohort'])
  self.assertEqual(cases_for('LONG_TERM')[0]['source_devices'],50)
 def test_thermal_removal_and_elapsed_time(self):
  p=plan_for('THERMAL');cool=[x for x in p if x['operation_id']=='COOLDOWN'];self.assertEqual(len(cool),10)
  self.assertTrue(all(x['payload']['duration_s']==21600 for x in cool));self.assertEqual(cool[-1]['payload']['elapsed_s'],218400)
 def test_safe_handoffs_highk(self):
  p=plan_for('HIGHK');station=set(x['payload']['station'] for x in p);self.assertEqual(station,{'storage','fabrication','electrical'})
  self.assertGreater(len({x['payload']['calibration_id'] for x in p}),3)
 def test_numerical_values_not_fabricated(self):
  c,_=fixture(['BASELINE']);self.assertTrue(all(r['payload']['scientific_measurement_values'] is None for r in c['record_store'].values()))

class NegativeContracts(unittest.TestCase):
 def reject(self,c,e):
  r=validate(c,e);self.assertFalse(r['accepted'],'false acceptance');self.assertTrue(r['errors'])
 def payload(self,c,op):
  o=next(o for o in c['observations'].values() if o['operation_id']==op)
  return o,c['record_store'][o['record_id']]
 def mutate_payload(self,b,op,fn):
  c,e=fixture([b]);o,r=self.payload(c,op);fn(r['payload']);o['record_hash']=digest(r);self.reject(c,e)
 def test_actor_success_injection(self):
  c,e=fixture();e[0]['success']=True;self.reject(c,e)
 def test_actor_observation_injection(self):
  c,e=fixture();e[0]['safe_zero']=True;self.reject(c,e)
 def test_empty_trace(self):
  c,e=fixture();self.reject(c,[])
 def test_missing_cleanup(self):
  c,e=fixture();e.pop();self.reject(c,e)
 def test_missing_safe_zero(self):
  c,e=fixture(['THERMAL']);e.pop(next(i for i,x in enumerate(e) if x['phase'].endswith('VERIFY_SAFE_ZERO')));self.reject(c,e)
 def test_duplicate_event(self):
  c,e=fixture();e[1]=copy.deepcopy(e[0]);self.reject(c,e)
 def test_reordered_event(self):
  c,e=fixture();e[3],e[4]=e[4],e[3];self.reject(c,e)
 def test_fabricated_extra_event(self):
  c,e=fixture();e.append(copy.deepcopy(e[0]));self.reject(c,e)
 def test_missing_observation(self):
  c,e=fixture();c['observations'].pop('EV1');self.reject(c,e)
 def test_extra_observation(self):
  c,e=fixture();c['observations']['fake']=copy.deepcopy(c['observations']['EV1']);self.reject(c,e)
 def test_cross_episode_replay(self):
  c,e=fixture();c['observations']['EV1']['episode_id']='synthetic_episode_other';self.reject(c,e)
 def test_attempt_replay(self):
  c,e=fixture();c['observations']['EV1']['attempt_id']='synthetic_attempt_0';self.reject(c,e)
 def test_carrier_swap(self):
  c,e=fixture();c['observations']['EV1']['carrier_id']='different';self.reject(c,e)
 def test_cohort_merge(self):
  c,e=fixture(['DUAL_TRACE']);c['observations']['EV1']['cohort_id']='baseline_12_per_stack';self.reject(c,e)
 def test_calibration_expired(self):
  c,e=fixture();c['observations']['EV1']['calibration_valid']=False;self.reject(c,e)
 def test_damaged_specimen(self):
  c,e=fixture();c['observations']['EV1']['damage_state']='unknown';self.reject(c,e)
 def test_self_declared_authority(self):
  c,e=fixture();c['observations']['EV1']['authority']='actor';self.reject(c,e)
 def test_unsigned_receipt(self):
  c,e=fixture();c['observations']['EV1']['qualified']=False;self.reject(c,e)
 def test_rejected_receipt(self):
  c,e=fixture();c['observations']['EV1']['accepted']=False;self.reject(c,e)
 def test_missing_card(self):
  c,e=fixture();c['cards'].pop(next(iter(c['cards'])));self.reject(c,e)
 def test_expired_card(self):
  c,e=fixture();c['cards'][next(iter(c['cards']))]['valid']=False;self.reject(c,e)
 def test_conflict_deleted(self):
  c,e=fixture(['BASELINE']);c['source_conflicts_preserved'].remove('C02');self.reject(c,e)
 def test_formula_gate_missing(self):
  c,e=fixture(['BASELINE']);c['conflict_dispositions'].pop('C03');self.reject(c,e)
 def test_formula_silently_corrected(self):
  c,e=fixture(['BASELINE']);c['conflict_dispositions']['C04']['source_resolved']=True;self.reject(c,e)
 def test_buffer_defaults(self):
  c,e=fixture(['STACK']);c['buffer_variant_nm']=None;self.reject(c,e)
 def test_boolean_buffer(self):
  c,e=fixture(['STACK']);c['buffer_variant_nm']=True;self.reject(c,e)
 def test_layer_index_mismatch_after_rehash(self):
  self.mutate_payload('STACK','LAYER_SERVICE',lambda p:p['control'].__setitem__('layer_index',99))
 def test_final_cap_blanket_variant(self):
  c,e=fixture(['STACK'],25);o=next(o for o in c['observations'].values() if o['case_id']=='layer_72');r=c['record_store'][o['record_id']];r['payload']['control']['thickness']=25;o['record_hash']=digest(r);self.reject(c,e)
 def test_thermal_cooldown_skipped_after_rehash(self):
  self.mutate_payload('THERMAL','COOLDOWN',lambda p:p.__setitem__('duration_s',0))
 def test_thermal_not_removed_after_rehash(self):
  self.mutate_payload('THERMAL','COOLDOWN',lambda p:p['detail'].__setitem__('off_hotplate',False))
 def test_live_disconnect_after_rehash(self):
  self.mutate_payload('PAIRS','DISCONNECT',lambda p:p.__setitem__('independent_safe_zero',False))
 def test_live_thermal_removal_after_rehash(self):
  self.mutate_payload('THERMAL','REMOVE_HOTPLATE',lambda p:p.__setitem__('independent_safe_zero',False))
 def test_longterm_fake_elapsed_after_rehash(self):
  self.mutate_payload('LONG_TERM','RETURN_STORAGE',lambda p:p.__setitem__('elapsed_s',999999))
 def test_storage_energized_after_rehash(self):
  self.mutate_payload('LONG_TERM','RETURN_STORAGE',lambda p:p.__setitem__('independent_safe_zero',False))
 def test_highk_no_station_transition_after_rehash(self):
  self.mutate_payload('HIGHK','DIELECTRIC_SERVICE',lambda p:p.__setitem__('station','electrical'))
 def test_highk_stale_mount_after_rehash(self):
  self.mutate_payload('HIGHK','POST_ACQUIRE',lambda p:p.__setitem__('mount_revision',1))
 def test_highk_stale_calibration_after_rehash(self):
  self.mutate_payload('HIGHK','POST_ACQUIRE',lambda p:p.__setitem__('calibration_id','old'))
 def test_stress_history_erased_after_rehash(self):
  self.mutate_payload('NBS','STRESS_SERVICE',lambda p:p.__setitem__('history_after',digest([])))
 def test_stress_time_erased_after_rehash(self):
  self.mutate_payload('POSITIVE_STRESS','STRESS_SERVICE',lambda p:p.__setitem__('duration_s',0))
 def test_bond_ends_reversed_after_rehash(self):
  def change(p):p['detail']['first_end'],p['detail']['second_end']=p['detail']['second_end'],p['detail']['first_end']
  self.mutate_payload('PACKAGE','BOND_SERVICE',change)
 def test_destructive_coupon_relabel_after_rehash(self):
  self.mutate_payload('STRUCTURAL','SECTION_SERVICE',lambda p:p['detail'].__setitem__('destructive',False))
 def test_gate_only_contacts_invented_after_rehash(self):
  self.mutate_payload('GATE_LEAKAGE','ACQUIRE',lambda p:p['control'].__setitem__('contacts_present',True))
 def test_same_stack_driver_load_after_rehash(self):
  self.mutate_payload('PAIRS','VTC',lambda p:p['control'].__setitem__('loads',[p['control']['driver']]))
 def test_wrong_inverter_netlist_after_rehash(self):
  self.mutate_payload('INV_TUNE','VTC',lambda p:p['control'].__setitem__('netlist_id','ORDINARY_INVERTER_FIG4'))
 def test_parallel_duplicate_load_after_rehash(self):
  self.mutate_payload('PARALLEL','VTC',lambda p:p['control'].__setitem__('loads',[2,2]))
 def test_caption_rewire_after_rehash(self):
  self.mutate_payload('COUPLING','PERTURB_POSITIVE',lambda p:p['control'].__setitem__('victim','TG2'))
 def test_wrong_perturbation_after_rehash(self):
  self.mutate_payload('COUPLING','PERTURB_POSITIVE',lambda p:p['detail'].__setitem__('perturbation_V',-10))
 def test_reported_mobility_as_measurement(self):
  self.mutate_payload('BASELINE','TRANSFER',lambda p:p.__setitem__('scientific_measurement_values',{'mobility':15}))
 def test_source_population_claim(self):
  c,e=fixture();c['jobs']['PAIRS']['full_source_population']=True;self.reject(c,e)
 def test_numerical_completion_claim(self):
  c,e=fixture();c['numerical_reproduction']=True;self.reject(c,e)
 def test_physical_authority_claim(self):
  c,e=fixture();c['production_authority']=True;self.reject(c,e)
 def test_replication_claim(self):
  c,e=fixture();c['scientific_replication']=True;self.reject(c,e)
 def test_historical_completion_claim(self):
  c,e=fixture();c['whole_historical_route_complete']=True;self.reject(c,e)
 def test_missing_readout(self):
  c,e=fixture();o=next(o for o in c['observations'].values() if o['operation_id']=='READOUT');o['readout_complete']=False;self.reject(c,e)
 def test_archive_falsely_declared(self):
  c,e=fixture();c['observations']['EV1']['archive_complete']=True;self.reject(c,e)
 def test_record_hash_mismatch(self):
  c,e=fixture();c['observations']['EV1']['record_hash']='0'*64;self.reject(c,e)
 def test_record_reuse(self):
  c,e=fixture();c['observations']['EV2']['record_id']=c['observations']['EV1']['record_id'];self.reject(c,e)
 def test_missing_payload(self):
  c,e=fixture();c['record_store'].pop(next(iter(c['record_store'])));self.reject(c,e)
 def test_nan_payload(self):
  c,e=fixture();next(iter(c['record_store'].values()))['payload']['elapsed_s']=float('nan');self.reject(c,e)
 def test_bool_int_aliases(self):
  for kind in ['card','disposition','job','payload']:
   with self.subTest(kind=kind):
    c,e=fixture(['STACK'])
    if kind=='card':c['cards']['U_AUTHORITY']['valid']=1
    elif kind=='disposition':c['conflict_dispositions']['C01']['source_resolved']=0
    elif kind=='job':c['jobs']['STACK']['full_source_population']=0
    else:
     o,r=self.payload(c,'RECEIVE');r['payload']['specimen_version']=True;o['record_hash']=digest(r)
    self.reject(c,e)
 def test_cleaned_substrate_parent_mismatch(self):
  c,e=fixture(['STACK']);c['jobs']['STACK']['parent_material_bindings'][0]['specimen_id']='other';self.reject(c,e)
 def test_cleaned_substrate_version_mismatch(self):
  c,e=fixture(['STACK']);c['jobs']['STACK']['parent_material_bindings'][0]['released_specimen_version']=1;self.reject(c,e)
 def test_highk_material_specimen_swap(self):
  c,e=fixture(['HIGHK']);o=next(o for o in c['observations'].values() if o['case_id']=='Al2O3' and o['operation_id']=='POST_ACQUIRE');r=c['record_store'][o['record_id']];r['specimen_id']='synthetic_HIGHK_HfO2_specimen';r['payload']['specimen_id']=r['specimen_id'];o['specimen_id']=r['specimen_id'];o['record_hash']=digest(r);self.reject(c,e)
 def test_malformed_shapes(self):
  for c,e in [(None,[]),({},None),({},[]),('bad','bad')]:self.reject(c,e)

if __name__=='__main__':unittest.main()
