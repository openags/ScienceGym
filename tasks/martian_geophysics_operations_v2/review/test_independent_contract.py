"""Independent adversarial synthetic custody-contract review. No science execution."""
from pathlib import Path
import sys,unittest,copy
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'tests'))
import contract as c
class IndependentContract(unittest.TestCase):
 def reject(self,fn,selected=None):
  x,e=c.fixture(selected or ['SEM']);fn(x,e);r=c.validate(x,e);self.assertFalse(r['passed'],r)
  self.assertIs(r['real_execution'],False);self.assertIs(r['source_conflicts_resolved'],False)
 def test_whole_paper_baseline(self):self.assertTrue(c.validate(*c.fixture(list(c.BRANCHES),'whole_paper_design'))['passed'])
 def test_whole_physical_baseline(self):
  ids=[k for k,b in c.BRANCHES.items() if b['classification']!='numerical_analysis'];self.assertTrue(c.validate(*c.fixture(ids,'whole_physical_campaign'))['passed'])
 def test_control_shape_bool_as_int(self):self.reject(lambda x,e:next(iter(x['controls'].values())).__setitem__('passed_shape_check',1))
 def test_control_real_false_as_zero(self):self.reject(lambda x,e:next(iter(x['controls'].values())).__setitem__('real_control_pass',0))
 def test_card_qualification_false_as_zero(self):self.reject(lambda x,e:next(iter(x['cards'].values())).__setitem__('real_qualification',0))
 def test_plan_count_int_as_bool(self):self.reject(lambda x,e:next(iter(x['plans'].values())).__setitem__('instance_count',True))
 def test_plan_count_int_as_float(self):self.reject(lambda x,e:next(iter(x['plans'].values())).__setitem__('instance_count',1.0))
 def test_lineage_version_int_as_bool(self):self.reject(lambda x,e:next(iter(x['lineage'].values())).__setitem__('input_version',True))
 def test_lineage_version_int_as_float(self):self.reject(lambda x,e:next(iter(x['lineage'].values())).__setitem__('output_version',2.0))
 def test_tuple_plan_phases_rejected(self):self.reject(lambda x,e:x['plans']['INTAKE'].__setitem__('phase_order',tuple(x['plans']['INTAKE']['phase_order'])))
 def test_tuple_lineage_parents_rejected(self):self.reject(lambda x,e:x['lineage']['synthetic_PRECURSOR'].__setitem__('parent_ids',tuple(x['lineage']['synthetic_PRECURSOR']['parent_ids'])))
 def test_tuple_record_regions_rejected(self):self.reject(lambda x,e:x['records']['REC_INTAKE']['policy'].__setitem__('regions',tuple(x['records']['REC_INTAKE']['policy']['regions'])))
 def test_lineage_destructive_true_as_int(self):self.reject(lambda x,e:x['lineage']['synthetic_SECTION'].__setitem__('destructive_parent_retired',1))
 def test_event_version_int_as_bool(self):self.reject(lambda x,e:e[0].__setitem__('input_version',True))
 def test_event_output_version_int_as_float(self):self.reject(lambda x,e:e[0].__setitem__('output_version',2.0))
 def test_event_false_as_zero(self):self.reject(lambda x,e:e[0].__setitem__('real_execution',0))
 def rehash(self,x,e,b):
  rid='REC_'+b;h=c.digest(x['records'][rid]);x['jobs']['J_'+b]['record_hash']=h
  for v in e:
   if v['record_id']==rid:v['record_hash']=h
 def mutate_record(self,key,val,policy=False,b='INTAKE'):
  def f(x,e):
   r=x['records']['REC_'+b];(r['policy'] if policy else r)[key]=val;self.rehash(x,e,b)
  return f
 def test_record_false_as_zero_rehashed(self):self.reject(self.mutate_record('physical_observation',0))
 def test_record_numerical_false_as_zero_rehashed(self):self.reject(self.mutate_record('numerical_reproduction',0))
 def test_policy_boolean_as_integer_rehashed(self):self.reject(self.mutate_record('nominal_correction_final_separate',1,True))
 def test_policy_missing_shear_rehashed(self):self.reject(self.mutate_record('missing_shear','zero_velocity',True,'ACOUSTIC'))
 def test_policy_buffer_echo_rehashed(self):self.reject(self.mutate_record('secondary_echo','sample_shear',True,'ACOUSTIC'))
 def test_policy_spot_to_run_rehashed(self):self.reject(self.mutate_record('spot_count_unit','independent_runs',True))
 def test_source_measurement_injection_rehashed(self):self.reject(self.mutate_record('measurement_values',{'solidus_K':2200}))
 def test_real_observation_claim_rehashed(self):self.reject(self.mutate_record('physical_observation',True))
 def test_real_execution_mode(self):self.reject(lambda x,e:x.__setitem__('fixture_only',False))
 def test_production_auth_claim(self):self.reject(lambda x,e:x.__setitem__('production_authentication_available',True))
 def test_actor_targets_leak(self):self.reject(lambda x,e:x.__setitem__('actor_source_targets_exposed',True))
 def test_actor_parameter_injection(self):self.reject(lambda x,e:e[0].__setitem__('actor_values',{'pressure':18}))
 def test_unknown_event_parameter(self):self.reject(lambda x,e:e[0].__setitem__('temperature_program','forbidden'))
 def test_self_consistent_wrong_calibration(self):
  def f(x,e):
   x['jobs']['J_INTAKE']['calibration_id']='stale'
   for q in e:
    if q['job_id']=='J_INTAKE':q['calibration_id']='stale'
  self.reject(f)
 def test_guessed_parent_map(self):self.reject(lambda x,e:x['cards']['U_PARENTMAP'].__setitem__('binding',{'S3631':'MA-17'}))
 def test_graphite_wrong_material_route(self):
  def f(x,e):
   x['allocations']['GRAPHITE_FEED']['material_route']='registered_physical';x['lineage']['synthetic_GRAPHITE_FEED']['material_route']='registered_physical'
  self.reject(f)
 def test_region_merge(self):self.reject(lambda x,e:x['lineage']['synthetic_SEM'].__setitem__('region_id','pooled'))
 def test_parent_retirement_removed(self):self.reject(lambda x,e:x['lineage']['synthetic_SECTION'].__setitem__('destructive_parent_retired',False))
 def test_unsafe_service_release(self):self.reject(lambda x,e:e[0].__setitem__('safe_release','safe'))
 def test_unknown_context_payload(self):self.reject(lambda x,e:x.__setitem__('external_job_url','https://example.invalid'))
 def test_deleted_parent_branch(self):self.reject(lambda x,e:x['plans'].pop('PRECURSOR'))
 def test_duplicate_phase_even_renumbered(self):
  def f(x,e):
   e.insert(2,copy.deepcopy(e[1]))
   for i,q in enumerate(e,1):q['event_id']='EV_'+str(i);q['sequence']=i
  self.reject(f)
 def test_trace_before_parent_closes(self):
  def f(x,e):
   index=next(i for i,q in enumerate(e) if q['branch_id']=='PRECURSOR');q=e.pop(index);e.insert(1,q)
   for i,q in enumerate(e,1):q['event_id']='EV_'+str(i);q['sequence']=i
  self.reject(f)
 def test_all_conflicts_reject_resolution(self):
  for k in c.CONFLICTS:
   with self.subTest(conflict=k):self.reject(lambda x,e,k=k:x['conflicts'].__setitem__(k,'resolved'))
 def test_nonfinite_value(self):self.reject(lambda x,e:e[0].__setitem__('actor_values',float('nan')))
 def test_failure_cannot_be_discarded(self):self.reject(self.mutate_record('failures',[{'attempt_id':'unarchived'}]))
 def test_h6050_cannot_invent_thermocouple(self):self.reject(self.mutate_record('H6050_temperature','thermocouple_measured',True,'EXSITU_H6050'))
 def test_calculated_melt_cannot_be_direct_epma(self):self.reject(self.mutate_record('S3631_melt_origin','direct_EPMA_spots',True,'EPMA'),['MODES'])
 def test_numeric_model_cannot_be_observation(self):self.reject(self.mutate_record('model_scope','physical_experiment',True,'BML_VOLUME'),['BML_VOLUME'])
for bid in c.BRANCHES:
 def run(self,bid=bid):
  r=c.validate(*c.fixture([bid]));self.assertTrue(r['passed'],r);self.assertEqual(r['status'],'synthetic_contract_pass');self.assertIs(r['real_execution'],False)
 setattr(IndependentContract,'test_baseline_'+bid.lower(),run)
if __name__=='__main__':unittest.main(verbosity=2)
