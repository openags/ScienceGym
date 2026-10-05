import sys,unittest,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
from scene_guards import evaluate_request,check_closeout,CONTRACT,PHYSICAL_ACTIONS
class GuardTests(unittest.TestCase):
 def probe(self,evidence,route='R12',anchor='AS09.raw_evidence',action='register_evidence'):
  r=evaluate_request(route,anchor,action,evidence);self.assertEqual(r['status'],'REJECTED');self.assertFalse(r['physical_permission']);self.assertEqual(r['commands_emitted'],[])
 def test_01_all_physical_actions_disabled(self):
  for a in PHYSICAL_ACTIONS:self.probe({},action=a)
 def test_02_unknown_anchor(self):self.probe({},anchor='AS99.control')
 def test_03_unknown_route(self):self.probe({},route='R99')
 def test_04_wrong_route_target(self):self.probe({},anchor='AS01.carrier_identity')
 def test_05_source_as_measured(self):self.probe({'measurement_category':'source_reported','treated_as_new_measurement':True})
 def test_06_synthetic_as_measured(self):self.probe({'measurement_category':'synthetic','treated_as_new_measurement':True})
 def test_07_digitized_as_measured(self):self.probe({'measurement_category':'digitized_source_plot','treated_as_new_measurement':True})
 def test_08_source_reward(self):self.probe({'source_outcome_success_threshold':True})
 def test_09_specimen_duplication(self):self.probe({'physical_chip_count':236})
 def test_10_subarray_count_conflation(self):self.probe({'region':'Array1','elements':236})
 def test_11_subarray_resistance_conflation(self):self.probe({'region':'Array2','nominal_ohms_approx':219})
 def test_12_whole_count_conflation(self):self.probe({'region':'whole_device','elements':118})
 def test_13_whole_resistance_conflation(self):self.probe({'region':'whole_device','nominal_ohms_approx':109})
 def test_14_reference_100_wrong_value(self):self.probe({'reference_id':'REF-100-OIL','reference_ohms':12900})
 def test_15_reference_100_wrong_bath(self):self.probe({'reference_id':'REF-100-OIL','bath':'air'})
 def test_16_reference_12k9_wrong_value(self):self.probe({'reference_id':'REF-12K9-AIR','reference_ohms':100})
 def test_17_reference_12k9_wrong_bath(self):self.probe({'reference_id':'REF-12K9-AIR','bath':'oil'})
 def test_18_eq3_hold(self):self.probe({'execute_eq3':True})
 def test_19_eq4_hold(self):self.probe({'execute_eq4':True})
 def test_20_loop_hold(self):self.probe({'execute_source_loop_expansion':True})
 def test_21_unqualified_geometry(self):self.probe({'geometry_as_qualified_interface':True})
 def test_22_source_not_safe_limit(self):self.probe({'source_value_as_safety_limit':True})
 def test_23_shared_lease(self):self.probe({'duplicate_shared_instrument_lease':True})
 def test_24_green_icon_not_safe(self):self.probe({'infer_safe_from_icon':True})
 def test_25_timer_not_safe(self):self.probe({'infer_safe_from_timer':True})
 def test_26_stop_not_safe(self):self.probe({'infer_safe_from_stop_command':True})
 def test_27_bare_chip(self):self.probe({'bare_chip_manipulation':True})
 def test_28_commands(self):self.probe({'hardware_commands':['set_field']})
 def test_29_actuation(self):self.probe({'actuation_enabled':True})
 def test_30_all_routes_evidence_only(self):
  for x in CONTRACT['route_bindings']:
   for a in x['target_anchor_ids']:
    r=evaluate_request(x['route_id'],a,'inspect_geometry');self.assertEqual(r['status'],'EVIDENCE_ONLY_ACCEPTED');self.assertFalse(r['physical_permission'])
 def test_31_service_request_never_dispatches(self):
  self.assertEqual(evaluate_request('R05','AS06.ccc_comparison_receipt','propose_service_request')['status'],'HOLD_UNQUALIFIED')
 def test_32_empty_closeout_holds(self):self.assertEqual(check_closeout({})['status'],'HOLD')
 def test_33_bool_closeout_not_evidence(self):
  self.assertEqual(check_closeout({k:True for k in CONTRACT['safe_release_requires']})['status'],'HOLD')
 def test_34_complete_metadata_still_not_permission(self):
  r={k:{'independently_observed':True,'evidence_id':'TEST-ONLY','provider_id':'TEST-ONLY'} for k in CONTRACT['safe_release_requires']};r.update(pending_service_jobs=False,custody_acceptance_id='TEST-ONLY');out=check_closeout(r);self.assertEqual(out['status'],'METADATA_COMPLETE_NOT_PHYSICAL_AUTHORIZATION');self.assertFalse(out['physical_permission'])
 def test_35_malformed_request(self):
  for value in [[],1,'bad',True]:self.assertEqual(evaluate_request('R12','AS09.raw_evidence','inspect_geometry',value)['status'],'REJECTED')
 def test_36_malformed_receipt(self):
  for value in [[],1,'bad',True,None]:self.assertEqual(check_closeout(value)['status'],'HOLD')
 def test_37_malformed_evidence_fields(self):
  for field in ['region','measurement_category','reference_id','bath']:
   for value in [[],{},1,True,None]:self.assertEqual(evaluate_request('R12','AS09.raw_evidence','inspect_geometry',{field:value})['status'],'REJECTED')
 def test_38_unknown_pending_state_holds(self):
  r={k:{'independently_observed':True,'evidence_id':'TEST-ONLY','provider_id':'TEST-ONLY'} for k in CONTRACT['safe_release_requires']};r.update(pending_service_jobs=None,custody_acceptance_id='TEST-ONLY');self.assertEqual(check_closeout(r)['status'],'HOLD')
 def test_39_reference_anchor_swap(self):
  self.probe({'reference_id':'REF-100-OIL','reference_ohms':100,'bath':'oil'},'R11','AS08.reference_12k9_identity')
  self.probe({'reference_id':'REF-12K9-AIR','reference_ohms':12900,'bath':'air'},'R06','AS07.reference_100_identity')
 def test_40_array_region_anchor_swap(self):
  self.probe({'region':'Array2'},'R04','AS02.array1_region')
  self.probe({'region':'Array1'},'R04','AS02.array2_region')
 def test_41_hall_bar_anchor_swap(self):self.probe({'region':'whole_device'},'R04','AS02.hall_bar_region')
 def test_42_whole_topology_anchor_swap(self):self.probe({'region':'Array1'},'R13','AS03.whole_device_topology')
 def test_43_anchor_resistance_without_region(self):self.probe({'nominal_ohms_approx':219},'R04','AS02.array1_region')
 def test_44_generic_subarray_anchor_invariant(self):
  for route in ['R04','R05','R13']:
   for e in [{'elements':236},{'nominal_ohms_approx':219}]:self.probe(e,route,'AS03.subarray_topology')
if __name__=='__main__':unittest.main(verbosity=2)
