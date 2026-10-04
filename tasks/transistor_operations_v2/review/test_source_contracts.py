"""Independent source-contract checks. No publisher pixels or apparatus access."""
import json
import pathlib
import unittest

BASE = pathlib.Path(__file__).resolve().parents[1]
ROOT = BASE if (BASE / 'branches.json').exists() else BASE / 'transistor_operations_v2'
def read(name): return json.loads((ROOT / name).read_text())

class SourceContractReview(unittest.TestCase):
    def test_complete_page_and_section_inventory(self):
        c=read('coverage_matrix.json')
        self.assertEqual([p['pdf_page'] for p in c['pages'] if p['source']=='main'],list(range(1,10)))
        self.assertEqual([p['pdf_page'] for p in c['pages'] if p['source']=='supplement'],list(range(1,54)))
        self.assertEqual({x['id'] for x in c['figures']},{'S'+str(i) for i in range(1,34)})
        self.assertEqual({x['id'] for x in c['tables']},{'S'+str(i) for i in range(1,7)})
        self.assertEqual({x['id'] for x in c['sections']},set(range(1,9)))
        self.assertEqual(c['unread_required_written_portions'],[])
    def test_whole_route_branch_mapping(self):
        expected={1:['PREP'],2:['STACK'],3:['OVERLAP','HIGHK'],4:['CROSSBAR','GATE_LEAKAGE'],5:['STRUCTURAL','SURFACE'],6:['PACKAGE'],7:['BASELINE','MOSCAP'],8:['DUAL_TRACE'],9:['POSITIVE_STRESS'],10:['LONG_TERM'],11:['NBS','NBTS'],12:['THERMAL'],13:['SMALL'],14:['MATERIAL','COUPLING'],15:['PAIRS'],16:['PARALLEL'],17:['DG_TUNE','INV_TUNE']}
        b=read('branches.json')['branches']
        self.assertEqual(len(b),24)
        self.assertEqual({i:sorted(x['id'] for x in b if x['route_group_id']==f'R{i:02d}') for i in range(1,18)}, {i:sorted(v) for i,v in expected.items()})
    def test_layer_topology_and_buffer_disposition(self):
        c=read('layer_contract.json'); layers=c['layers']
        self.assertEqual([x['index'] for x in layers],list(range(1,73)))
        self.assertEqual([x['role'] for x in layers[:2]],['substrate','insulation'])
        for stack in range(1,11):
            block=layers[2+7*(stack-1):2+7*stack]
            self.assertEqual([x['role'] for x in block],['BG','BG_dielectric','channel','source_drain','TG_dielectric','TG','interstack_buffer' if stack<10 else 'final_cap'])
            self.assertEqual([x['source_thickness'] for x in block],[20,25,10,20,25,20,50])
            self.assertEqual({x['stack'] for x in block},{stack})
            self.assertIsNone(block[-1]['execution_thickness_default'])
            self.assertEqual(block[-1]['alternative_main_methods_interstack_nm'],25 if stack<10 else None)
        self.assertEqual(c['interstack_buffer_count'],9);self.assertEqual(c['final_cap_count'],1)
        self.assertIs(c['freestanding_film_transfer_demonstrated'],False)
    def test_ten_conflicts_unresolved(self):
        c=read('source_conflicts.json')
        self.assertEqual({x['id'] for x in c['conflicts']},{f'C{i:02d}' for i in range(1,11)})
        self.assertTrue(all(x['resolved'] is False and x['qualification_gate'] is True for x in c['conflicts']))
        self.assertIs(c['automatic_correction_allowed'],False)
    def test_unknown_settings_have_no_default(self):
        for p in read('unknown_parameters.json')['unknown_parameters']:
            self.assertIsNone(p['value']);self.assertIsNone(p['default']);self.assertIs(p['resolved'],False)
    def test_source_timing_and_geometry(self):
        c={x['id']:x['source_constraints'] for x in read('control_packages.json')['controls']}
        self.assertEqual(c['THERMAL']['stack_order'],list(range(1,11)))
        self.assertEqual(c['THERMAL']['table_temperatures_C'],[25,50,75,100])
        self.assertEqual(c['THERMAL']['nominal_measurement_hold_s'],60)
        self.assertEqual(c['THERMAL']['off_hotplate_cooldown_s'],21600)
        self.assertIs(c['THERMAL']['simultaneous_all_stack_measurement'],False)
        self.assertIs(c['THERMAL']['device_temperature_equals_table'],False)
        for name in ['NBS','NBTS']:
            self.assertEqual([c[name][x] for x in ['VGS_V','VDS_V','duration_s','interval_s']],[-10,5,4000,500])
        self.assertIsNone(c['NBS']['temperature_C']);self.assertEqual(c['NBTS']['temperature_C'],80)
        self.assertEqual([c['SMALL'][x] for x in ['W_um','Lch_nm','Lg_nm']],[1,500,100])
        self.assertIs(c['SMALL']['full_ten_stack_demonstration'],False)
    def test_cohorts_are_not_merged(self):
        c={x['id']:x['source_constraints'] for x in read('control_packages.json')['controls']}
        self.assertEqual([c['BASELINE'][x] for x in ['source_N_per_stack','source_chips','systems_per_chip']],[12,3,4])
        self.assertEqual(c['DUAL_TRACE']['source_devices_per_architecture'],100)
        self.assertEqual(c['POSITIVE_STRESS']['source_devices_per_architecture'],100)
        self.assertEqual(c['LONG_TERM']['source_total_devices_stated'],50)
        self.assertIsNone(c['LONG_TERM']['per_architecture_allocation'])
        self.assertEqual(c['LONG_TERM']['source_duration_days'],200)
        self.assertEqual(c['LONG_TERM']['source_interval_days'],10)
    def test_source_failed_controls_preserved(self):
        c={x['id']:x['source_constraints'] for x in read('control_packages.json')['controls']}
        self.assertEqual(c['HIGHK']['HfO2_ALD_C'],250);self.assertIsNone(c['HIGHK']['Al2O3_ALD_C'])
        self.assertIs(c['HIGHK']['not_a_replacement_for_parylene'],True)
        self.assertIs(c['GATE_LEAKAGE']['source_drain_contacts_present'],False)
        self.assertEqual(c['GATE_LEAKAGE']['source_classification_A'],2e-8)
        self.assertIs(c['GATE_LEAKAGE']['classification_is_not_universal_safety_limit'],True)
    def test_ordered_pairs_and_parallel_loads(self):
        c={x['id']:x['source_constraints'] for x in read('control_packages.json')['controls']}
        pairs=c['PAIRS']['ordered_pairs'];self.assertEqual(len(pairs),90)
        self.assertEqual({(x['driver'],x['load']) for x in pairs},{(d,l) for d in range(1,11) for l in range(1,11) if d!=l})
        self.assertEqual(c['PARALLEL']['load_counts'],list(range(1,10)))
        self.assertEqual(c['PARALLEL']['driver'],1)
        self.assertIs(c['PARALLEL']['all_511_nonempty_subsets_claimed'],False)
    def test_coupling_conflicting_cases_preserved(self):
        c=next(x['source_constraints'] for x in read('control_packages.json')['controls'] if x['id']=='COUPLING')
        self.assertEqual(c['section7_cases']['iii'],{'perturber':'TG1','victim':'BG2'})
        self.assertEqual(c['section7_cases']['iv'],{'perturber':'BG2','victim':'TG1'})
        self.assertEqual(c['caption_conflicting_cases']['iii'],{'perturber':'BG2','victim':'BG1'})
        self.assertIsNone(c['selected_interpretation']);self.assertIsNone(c['source_perturbation_order'])
    def test_distinct_inverter_netlists(self):
        n={x['id']:x for x in read('netlist_contracts.json')['netlists']}
        self.assertEqual(len(n),3)
        ordinary=n['ORDINARY_INVERTER_FIG4']['source_visual_interpretation']
        tuned=n['INDEPENDENT_INVERTER_S31']['source_visual_interpretation']
        self.assertNotEqual(ordinary,tuned)
        self.assertEqual([tuned[x] for x in ['driver_BG','driver_TG','load_TG']],['VBG','VTG1','VTG2'])
        self.assertTrue(all(x['qualification_gate'] for x in n.values()))
    def test_closed_service_and_numerical_boundary(self):
        for x in read('station_contracts.json')['stations']:
            self.assertIs(x['closed_service'],True);self.assertIs(x['recipe_complete'],False);self.assertIsNone(x['real_control_interface'])
        for x in read('analysis_contracts.json')['analyses']:
            self.assertIs(x['implementation_supplied'],False);self.assertIs(x['numerical_reproduction_performed'],False)
        a={x['id']:x for x in read('analysis_contracts.json')['analyses']}
        self.assertTrue({'C02','C03','C04'} <= set(a['TRANSISTOR_METRICS']['conflict_ids']))
        self.assertIs(read('episode_input_contract.json')['production_inputs_accepted_by_mock'],False)

if __name__=='__main__': unittest.main(verbosity=2)
