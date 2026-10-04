"""Synthetic bookkeeping tests; no experiment, measurement or simulation occurs."""
import copy, unittest
from contract import BRANCHES,closure,fixture,validate,digest
class ContractTests(unittest.TestCase):
 def setUp(self):self.ctx,self.events=fixture(list(BRANCHES),'whole_paper_design')
 def rejected(self):self.assertFalse(validate(self.ctx,self.events)['passed'])
 def test_valid_whole_paper(self):self.assertTrue(validate(self.ctx,self.events)['passed'])
 def test_valid_selected_branches(self):
  for b in BRANCHES:
   with self.subTest(branch=b):
    c,e=fixture([b]);self.assertTrue(validate(c,e)['passed'])
 def test_valid_physical_campaign(self):
  c,e=fixture([b for b in BRANCHES if BRANCHES[b]['classification']!='numerical_analysis'],'whole_physical_campaign');self.assertTrue(validate(c,e)['passed'])
 def test_empty_trace(self):self.events=[];self.rejected()
 def test_empty_selection(self):self.ctx['selected_branches']=[];self.rejected()
 def test_unknown_selection(self):self.ctx['selected_branches']=['UNKNOWN'];self.rejected()
 def test_duplicate_selection(self):self.ctx['selected_branches'].append('SEM');self.rejected()
 def test_missing_dependency(self):self.ctx['plans'].pop('GLASS');self.rejected()
 def test_missing_control(self):self.ctx['controls'].pop('CTRL_SAFE_RELEASE');self.rejected()
 def test_whole_paper_omission(self):self.ctx,self.events=fixture(['SEM'],'whole_paper_design');self.rejected()
 def test_physical_campaign_omission(self):self.ctx,self.events=fixture(['PELLET'],'whole_physical_campaign');self.rejected()
 def test_missing_phase(self):self.events.pop();self.rejected()
 def test_duplicate_phase(self):self.events.append(copy.deepcopy(self.events[-1]));self.rejected()
 def test_reordered_phase(self):self.events[0],self.events[1]=self.events[1],self.events[0];self.rejected()
 def test_event_pressure_command(self):self.events[0]['pressure_setpoint']=19;self.rejected()
 def test_event_temperature_command(self):self.events[0]['temperature_setpoint']=2220;self.rejected()
 def test_event_open_guard(self):self.events[0]['guard_closed']=False;self.rejected()
 def test_event_real_release(self):self.events[0]['safe_release']=True;self.rejected()
 def test_event_source_outcomes(self):self.events[0]['actor_values']={'target':'paper_value'};self.rejected()
 def test_event_copied_hash(self):self.events[0]['record_hash']=self.events[-1]['record_hash'];self.rejected()
 def test_event_unknown_job(self):self.events[0]['job_id']='other';self.rejected()
 def test_real_mode(self):self.ctx['fixture_only']=False;self.rejected()
 def test_claim_authentication(self):self.ctx['production_authentication_available']=True;self.rejected()
 def test_actor_targets_exposed(self):self.ctx['actor_source_targets_exposed']=True;self.rejected()
 def test_nan(self):self.ctx['plans']['SEM']['instance_count']=float('nan');self.rejected()
 def test_infinite(self):self.events[0]['sequence']=float('inf');self.rejected()
 def test_bool_sequence(self):self.events[0]['sequence']=True;self.rejected()
 def test_bool_instance_count(self):self.ctx['plans']['SEM']['instance_count']=True;self.rejected()
 def test_bool_event_version(self):self.events[0]['input_version']=True;self.rejected()
 def test_numeric_false_record(self):self.ctx['records']['REC_SEM']['physical_observation']=0;self.rejected()
 def test_numeric_false_control(self):self.ctx['controls']['CTRL_RECORD']['real_control_pass']=0;self.rejected()
 def test_numeric_false_card(self):self.ctx['cards']['U_THERMAL']['real_qualification']=0;self.rejected()
 def test_numeric_destructive_retirement(self):self.ctx['lineage']['synthetic_SECTION']['destructive_parent_retired']=1;self.rejected()
 def test_bool_lineage_version(self):self.ctx['lineage']['synthetic_SEM']['input_version']=True;self.rejected()
 def test_numeric_false_event(self):self.events[0]['real_execution']=0;self.rejected()
 def test_numeric_false_record_rehashed(self):
  self.ctx['records']['REC_SEM']['physical_observation']=0
  h=digest(self.ctx['records']['REC_SEM']);self.ctx['jobs']['J_SEM']['record_hash']=h
  for e in self.events:
   if e['job_id']=='J_SEM':e['record_hash']=h
  self.rejected()
 def test_numeric_true_control(self):self.ctx['controls']['CTRL_RECORD']['passed_shape_check']=1;self.rejected()
 def test_bool_version(self):self.ctx['jobs']['J_SEM']['input_version']=True;self.rejected()
 def test_replication_fabricated(self):self.ctx['plans']['SEM']['count_origin']='source_replication';self.rejected()
 def test_zero_instances(self):self.ctx['plans']['SEM']['instance_count']=0;self.rejected()
 def test_unbounded_instances(self):self.ctx['plans']['SEM']['instance_count']=1000000;self.rejected()
 def test_missing_card(self):self.ctx['cards'].pop('U_THERMAL');self.rejected()
 def test_real_qualification(self):self.ctx['cards']['U_THERMAL']['real_qualification']=True;self.rejected()
 def test_guessed_parent_map(self):self.ctx['cards']['U_PARENTMAP']['binding']={'S3631':'MA-17'};self.rejected()
 def test_crossed_powder_route(self):self.ctx['allocations']['EXSITU_S8293']['material_route']='glass';self.rejected()
 def test_source_ids_swapped(self):self.ctx['allocations']['MO_EXSITU']['cohort_ids']=['H5898','H5897'];self.rejected()
 def test_destroyed_parent_reuse(self):self.ctx['lineage']['synthetic_SECTION']['destructive_parent_retired']=False;self.rejected()
 def test_region_collapse(self):self.ctx['lineage']['synthetic_SEM']['region_id']='single_mean';self.rejected()
 def test_missing_archive(self):self.ctx['archive']['record_ids'].pop();self.rejected()
 def test_missing_cleanup(self):self.ctx['archive']['cleanup_complete']=False;self.rejected()
 def test_forged_calibration(self):self.ctx['jobs']['J_SEM']['calibration_id']='other';self.rejected()
 def test_crossed_parent(self):self.ctx['jobs']['J_GLASS']['parents']=['J_MA17'];self.rejected()
 def test_open_service(self):self.ctx['jobs']['J_RUN_S3631']['closed_service']=False;self.rejected()
 def test_digital_claims_physical_service(self):self.ctx['jobs']['J_LIQUID_EOS']['closed_service']=True;self.rejected()
 def test_physical_claim(self):self.ctx['records']['REC_SEM']['physical_observation']=True;self.rejected()
 def test_model_reproduced(self):self.ctx['records']['REC_LIQUID_EOS']['numerical_reproduction']=True;self.rejected()
 def test_fake_measurement(self):self.ctx['records']['REC_ACOUSTIC']['measurement_values']={'Vs':0};self.rejected()
 def test_new_unretained_attempt(self):self.ctx['records']['REC_SEM']['attempt_ids'].append('A0_failure');self.rejected()
 def test_missing_attempt(self):self.ctx['records']['REC_SEM']['attempt_ids']=[];self.rejected()
 def test_unregistered_failure(self):self.ctx['records']['REC_SEM']['failures']=['failure'];self.rejected()
 def test_tuple_phase_order(self):self.ctx['plans']['SEM']['phase_order']=tuple(self.ctx['plans']['SEM']['phase_order']);self.rejected()
 def test_tuple_parent_ids(self):self.ctx['lineage']['synthetic_SEM']['parent_ids']=tuple(self.ctx['lineage']['synthetic_SEM']['parent_ids']);self.rejected()
 def test_tuple_regions(self):self.ctx['records']['REC_SEM']['policy']['regions']=tuple(self.ctx['records']['REC_SEM']['policy']['regions']);self.rejected()
 def test_nonstring_nested_key(self):self.ctx['records']['REC_SEM']['policy'][1]='bad';self.rejected()
 def test_set_container(self):self.ctx['selected_branches']=set(self.ctx['selected_branches']);self.rejected()
 def test_malformed_context(self):
  for value in [None,[],1,'bad']:
   with self.subTest(value=value):self.assertFalse(validate(value,self.events)['passed'])
 def test_malformed_events(self):
  for value in [None,{},1,'bad']:
   with self.subTest(value=value):self.assertFalse(validate(self.ctx,value)['passed'])
 def test_malformed_jobs(self):self.ctx['jobs']=[];self.rejected()
 def test_malformed_event(self):self.events[0]=[];self.rejected()
 def test_numerical_not_physical_count(self):
  self.assertEqual(BRANCHES['LIQUID_EOS']['classification'],'numerical_analysis')
  self.assertEqual(BRANCHES['SEM']['classification'],'qualified_measurement')

def add_conflict_test(cid):
 def test(self):self.ctx['conflicts'][cid]='resolved';self.rejected()
 setattr(ContractTests,'test_block_resolution_'+cid,test)
for cid in ['C01','C02','C03','C04','C05','C06','C07','C08','C09','C10']:add_conflict_test(cid)
def add_policy_test(key):
 def test(self):self.ctx['records']['REC_COMPARE']['policy'][key]='incorrect';self.rejected()
 setattr(ContractTests,'test_policy_'+key,test)
for k in ['temperature_correction','sample_identity_conflict','nominal_correction_final_separate','missing_shear','secondary_echo','S3631_melt_origin','H6050_temperature','spot_count_unit','regions','mode_methods','redox','parent_assignment','model_scope','Monte_Carlo_variants','main_pixels']:add_policy_test(k)
if __name__=='__main__':unittest.main()
