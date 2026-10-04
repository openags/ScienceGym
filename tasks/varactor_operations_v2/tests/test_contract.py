"""Original author tests: finite bookkeeping and arithmetic, never real science."""
import unittest,math
from copy import deepcopy
import contract as c
from verify_package import verify
class ContractTests(unittest.TestCase):
 def test_all_finite_fixtures(self):
  for fid in c.FIXTURE_IDS:
   with self.subTest(fid=fid):
    f=c.fixture(fid);r=c.evaluate(f['events'],f['receipts'],fid);self.assertTrue(r['contract_passed']);self.assertFalse(r['physical_execution']);self.assertFalse(r['whole_campaign_complete']);self.assertFalse(r['scientific_reproduction'])
 def test_structural_package(self):self.assertEqual(verify(),[])
 def test_operations_bound_exactly(self):
  assets=c.read('asset_binding_plan.json')['scene_assets'];o=[x for a in assets for x in a['bind_operation_ids']];self.assertEqual(len(o),len(set(o)));self.assertEqual(set(o),set(c.OPERATIONS))
 def test_fixture_operation_membership(self):
  for fid in c.FIXTURE_IDS:
   if fid.startswith(('HOLD:','MODEL:','CONTEXT:')):continue
   f=c.fixture(fid);self.assertTrue(set(x['operation_id'] for x in f['events'])<=set(c.BRANCHES[f['context']['branch_id']]['operation_ids']))
 def sample(self):return c.fixture('SQD_SIDEBAND_READOUT:PREPARED:GOOD')
 def test_actor_cannot_declare_success(self):
  f=self.sample();f['events'][0]['success']=True
  with self.assertRaises(c.ContractError):c.evaluate(f['events'],f['receipts'],f['fixture_id'])
 def test_registry_forgery(self):
  f=self.sample();next(iter(f['receipts'].values()))['payload']['role']='actor_observation'
  with self.assertRaises(c.ContractError):c.evaluate(f['events'],f['receipts'],f['fixture_id'])
 def test_replayed_receipt(self):
  f=self.sample();f['events'][1]['evidence_id']=f['events'][0]['evidence_id']
  with self.assertRaises(c.ContractError):c.evaluate(f['events'],f['receipts'],f['fixture_id'])
 def test_duplicate_event(self):
  f=self.sample();f['events'][1]=deepcopy(f['events'][0])
  with self.assertRaises(c.ContractError):c.evaluate(f['events'],f['receipts'],f['fixture_id'])
 def test_missing_event(self):
  f=self.sample();f['events'].pop()
  with self.assertRaises(c.ContractError):c.evaluate(f['events'],f['receipts'],f['fixture_id'])
 def test_reverse_order(self):
  f=self.sample();f['events'].reverse()
  with self.assertRaises(c.ContractError):c.evaluate(f['events'],f['receipts'],f['fixture_id'])
 def test_unknown_fixture(self):
  with self.assertRaises(c.ContractError):c.fixture('REAL')
 def test_cross_fixture(self):
  f=self.sample();g=c.fixture('DQD_JPA_COMPARISON:PREPARED:GOOD')
  with self.assertRaises(c.ContractError):c.evaluate(f['events'],g['receipts'],f['fixture_id'])
 def test_every_revision_tamper_rejected(self):
  for key in c.CONTEXT_KEYS:
   f=self.sample();next(iter(f['receipts'].values()))['context'][key]='forged'
   with self.subTest(key=key),self.assertRaises(c.ContractError):c.evaluate(f['events'],f['receipts'],f['fixture_id'])
 def test_request_not_observation(self):
  f=self.sample();r=next(r for r in f['receipts'].values() if r['operation_id']=='REQUEST_SAFE_OFF');self.assertEqual(r['payload']['role'],'request_acknowledgement');r['payload']['safe_release_observed']=True
  with self.assertRaises(c.ContractError):c.evaluate(f['events'],f['receipts'],f['fixture_id'])
 def test_isolation_hold_no_undock(self):
  f=c.fixture('FIXED_LOAD_STO:PREPARED:ISOLATION_HOLD');ids=[e['operation_id'] for e in f['events']];self.assertNotIn('UNDOCK_MODULE',ids);self.assertNotIn('STORE_SAMPLE',ids)
 def test_prepared_no_fabrication_credit(self):
  f=self.sample();r=c.evaluate(f['events'],f['receipts'],f['fixture_id']);self.assertFalse(r['synthetic_preparation_lineage_checked']);self.assertFalse(any(e['operation_id']=='REQUEST_BACK_METAL' for e in f['events']))
 def test_full_has_fabrication(self):
  f=c.fixture('DQD_CAPACITANCE_SENSITIVITY:FULL:GOOD');ids=[e['operation_id'] for e in f['events']];self.assertIn('VERIFY_LIFT_OFF',ids);self.assertIn('VERIFY_SECOND_LITHOGRAPHY',ids);self.assertIn('VERIFY_MODULE_ASSEMBLY',ids)
 def test_comparison_has_both_material_preparations(self):
  f=c.fixture('STO_KTO_COMPARISON:FULL:GOOD');self.assertEqual(sum(e['operation_id']=='RECEIVE_CRYSTAL' for e in f['events']),2)
 def test_independent_analysis_safety_order(self):
  f=self.sample();events=f['events'];start=next(i for i,e in enumerate(events) if e['operation_id']=='REQUEST_SAFE_OFF');end=next(i for i,e in enumerate(events) if e['operation_id']=='ARCHIVE_RECORDS');first=next(i for i,e in enumerate(events) if e['operation_id']=='VALIDATE_RECORDS');reordered=events[:first]+events[start:end]+events[first:start]+events[end:];self.assertTrue(c.evaluate(reordered,f['receipts'],f['fixture_id'])['contract_passed'])
 def test_model_is_not_solver(self):
  f=c.fixture('MODEL:REFLECTION_CIRCUIT_FIT');r=c.evaluate(f['events'],f['receipts'],f['fixture_id']);self.assertTrue(r['numerical_metadata_checked']);self.assertFalse(r['numerical_solver_execution'])
 def test_reflection_matched(self):
  r=c.reflection(50,0,50);self.assertEqual(r['magnitude'],0);self.assertFalse(r['phase_defined'])
 def test_reflection_complex(self):
  r=c.reflection(50,50,50);self.assertAlmostEqual(r['real'],.2);self.assertAlmostEqual(r['imag'],.4)
 def test_series_capacitance(self):self.assertAlmostEqual(c.series_capacitance(2,2),1)
 def test_loss_is_upper_bound(self):
  r=c.loss_bound(1,1e-12,1e6);self.assertAlmostEqual(r['tan_delta_upper_bound'],2*math.pi*1e-6);self.assertFalse(r['intrinsic_loss_measured'])
 def test_snr_power_convention(self):self.assertAlmostEqual(c.snr_from_power(100,1)['dB'],20)
 def test_sensitivity_convention(self):self.assertAlmostEqual(c.sensitivity(2,20,2,'F')['value'],.1)
 def test_quadrature_snr(self):
  r=c.quadrature_snr(2,[-1,0,1]);self.assertEqual(r['power_ratio'],4);self.assertIsNone(r['independent_device_count'])
 def test_stability_drift_is_not_erased(self):
  r=c.stability({'time_s':[0,1,2],'x':[0,1,2],'y':[0,0,0],'units':{'time':'s','quadrature':'dimensionless'},'synthetic_only':True});self.assertEqual(r['x_drift_per_s'],1);self.assertFalse(r['no_drift_claimed'])
 def test_hysteresis_coordinate_alignment(self):
  a={'direction':'forward','history_id':'a','samples':[{'coordinate_id':'1','minimum_magnitude':.2},{'coordinate_id':'2','minimum_magnitude':.3}],'synthetic_only':True};b={'direction':'reverse','history_id':'b','samples':[{'coordinate_id':'2','minimum_magnitude':.1},{'coordinate_id':'1','minimum_magnitude':.1}],'synthetic_only':True};r=c.hysteresis(a,b);self.assertAlmostEqual(r['differences']['1'],.1);self.assertFalse(r['history_erased'])
 def test_circuit_cards(self):
  for card in c.read('circuit_family_cards.json')['cards']:self.assertTrue(c.circuit_card(card,card['id'])['source_card_matches'])
 def test_circuit_family_cannot_swap(self):
  cards=c.read('circuit_family_cards.json')['cards']
  with self.assertRaises(c.ContractError):c.circuit_card(cards[1],'DQD')
 def test_dqd_series_missing(self):
  card=deepcopy(c.read('circuit_family_cards.json')['cards'][2]);card['matching_series_capacitor_pF']=None
  with self.assertRaises(c.ContractError):c.circuit_card(card,'DQD')
 def test_sqd_inductor_not_silently_corrected(self):
  card=deepcopy(c.read('circuit_family_cards.json')['cards'][1]);card['model_inductor_nH']=330
  with self.assertRaises(c.ContractError):c.circuit_card(card,'SQD')
# These are different input failure cases, each discovered and run as its own test.
NEGATIVES={
'reflection_bool':lambda:c.reflection(True,0,50),'reflection_bad_z0':lambda:c.reflection(1,0,0),'reflection_nan':lambda:c.reflection(float('nan'),0,50),'reflection_active':lambda:c.reflection(-1,0,50),
'series_zero':lambda:c.series_capacitance(0,1),'series_underflow':lambda:c.series_capacitance(5e-324,5e-324),'snr_zero_noise':lambda:c.snr_from_power(1,0),'snr_underflow':lambda:c.snr_from_power(5e-324,1e308),
'sensitivity_bad_unit':lambda:c.sensitivity(1,1,1,'aF'),'sensitivity_bad_bandwidth':lambda:c.sensitivity(1,1,-1,'F'),'sensitivity_underflow':lambda:c.sensitivity(5e-324,0,2,'F'),'sensitivity_overflow':lambda:c.sensitivity(1,1e308,1,'F'),'sensitivity_bool_factor':lambda:c.sensitivity(1,1,1,'F',True),
'quadrature_zero_noise':lambda:c.quadrature_snr(2,[1,1]),'quadrature_zero_signal':lambda:c.quadrature_snr(0,[-1,0,1]),'quadrature_infinity':lambda:c.quadrature_snr(2,[1,float('inf')]),
'phase_magnitude_only':lambda:c.phase_regime({'regime':'matched','evidence_kind':'magnitude_only','phase_record_id':'x','calibration_revision':'c','expected_calibration_revision':'c'}),
'phase_empty_calibration':lambda:c.phase_regime({'regime':'matched','evidence_kind':'independent_phase','phase_record_id':'x','calibration_revision':'','expected_calibration_revision':''}),
'phase_null_calibration':lambda:c.phase_regime({'regime':'matched','evidence_kind':'independent_phase','phase_record_id':'x','calibration_revision':None,'expected_calibration_revision':None}),
'stability_reverse_time':lambda:c.stability({'time_s':[2,1,0],'x':[0,1,2],'y':[0,0,0],'units':{'time':'s','quadrature':'dimensionless'},'synthetic_only':True}),
'stability_mismatched_arrays':lambda:c.stability({'time_s':[0,1,2],'x':[0,1],'y':[0,0,0],'units':{'time':'s','quadrature':'dimensionless'},'synthetic_only':True})}
def make_negative(fn):
 def test(self):
  with self.assertRaises(c.ContractError):fn()
 return test
for name,fn in NEGATIVES.items():setattr(ContractTests,'test_reject_'+name,make_negative(fn))
if __name__=='__main__':unittest.main()
