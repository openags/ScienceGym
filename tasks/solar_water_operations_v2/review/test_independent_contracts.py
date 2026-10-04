"""Independent bounded-design invariants. No hardware or scientific simulation.

Run: python -m unittest discover -s review -p 'test_independent_contracts.py' -v
Tests intentionally check the model against its declared contracts, rather than
only mutate a fixture and compare it with the same fixture generator.
"""
from pathlib import Path
import copy
import importlib.util
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('independent_subject', ROOT / 'tests' / 'contract.py')
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)

def read(name):
    return json.loads((ROOT / name).read_text())

def records(context, operation=None, branch=None):
    return [p for p in context['record_store'].values()
            if (operation is None or p['operation_id'] == operation)
            and (branch is None or p['branch_id'] == branch)]

class IndependentContracts(unittest.TestCase):
    def test_boundary_and_actual_result_are_design_only(self):
        c, events = subject.fixture()
        result = subject.validate(c, events)
        self.assertEqual(result['scope'], 'synthetic_contract_only')
        for key in ('full_paper_complete', 'physical_execution_performed',
                    'physics_simulation_performed', 'scientific_replication'):
            self.assertIs(result[key], False)
        self.assertIs(c['biological_operations_included'], False)
        self.assertIs(c['production_authority'], False)
        self.assertTrue(all(p['scientific_measurement_values'] is None for p in records(c)))
        self.assertTrue(all(p['elapsed_physical_seconds'] is None for p in records(c)))

    def test_exact_fourteen_unresolved_conflicts(self):
        conflicts = read('source_conflicts.json')['conflicts']
        self.assertEqual([c['id'] for c in conflicts], ['C' + str(i) for i in range(1, 15)])
        self.assertTrue(all(c['status'] == 'unresolved' and c['silently_corrected'] is False for c in conflicts))
        self.assertIn('kg/m2/h', conflicts[2]['source_statement_a'])
        self.assertIn('kg/m2/s', conflicts[2]['source_statement_b'])
        self.assertIn('horizontal', conflicts[1]['source_statement_a'])
        self.assertIn('vertical', conflicts[1]['source_statement_b'])

    def test_enthalpy_remains_a_model_inference(self):
        outcome = next(o for o in read('source_outcomes.json')['outcomes'] if o['id'] == 'O_ENTHALPY')
        self.assertIs(outcome['acceptance_threshold'], False)
        self.assertIn('not direct calorimetry', outcome['interpretation'])
        self.assertIs(read('analysis_contracts.json')['implemented'], False)
        self.assertIsNone(read('evaluator_reference.json')['scientific_success_score'])

    def test_source_geometry_is_not_robot_geometry(self):
        cases = next(x['cases'] for x in read('control_packages.json')['controls'] if x['id'] == 'ASSEMBLE')
        for case in cases:
            self.assertIs(case['physical_setpoints_not_authorized_by_source'], True)
            self.assertIs(case['source_constraints']['geometry_not_robot_asset'], True)
        self.assertTrue(all(p['value'] is None for p in read('unknown_parameters.json')['parameters']))
        self.assertTrue(all(s['execution_adapter'] is None for s in read('station_contracts.json')['stations']))

    def test_actor_events_cannot_supply_results(self):
        c, events = subject.fixture(['DARK'])
        events[0]['scientific_measurement_values'] = [1220]
        with self.assertRaises(ValueError):
            subject.validate(c, events)

    def test_cross_episode_actor_replay_is_rejected(self):
        _, events_a = subject.fixture(['BIFACIAL'], 'independent_episode_A')
        context_b, _ = subject.fixture(['BIFACIAL'], 'independent_episode_B')
        with self.assertRaises(ValueError, msg='Episode A actor actions must not satisfy episode B'):
            subject.validate(context_b, events_a)

    def test_raw_records_are_bound_to_episode(self):
        c, _ = subject.fixture(['DARK'], 'independent_episode_C')
        for payload in records(c):
            self.assertEqual(payload.get('episode_id'), c['episode_id'],
                             'Operation receipt must retain its episode identity')

    def test_parent_release_inventory_matches_child_input(self):
        c, _ = subject.fixture(['BIFACIAL'])
        for job_id, job in c['jobs'].items():
            for parent in job['parents']:
                released = parent['released_target_records']
                for item in c['input_inventory'][job_id]:
                    self.assertTrue(any(all(r.get(k) == v for k, v in item.items()) for r in released),
                                    (job_id, item['coupon_id']))
                self.assertEqual(parent['parent_release_inventory_hash'],
                                 subject.digest(c['release_inventories'][parent['job_id']]))

    def test_assembly_service_intake_contains_every_assembled_coupon(self):
        c, _ = subject.fixture(['BIFACIAL'])
        jobs = [k for k, j in c['jobs'].items() if j['branch_id'] == 'ASSEMBLE']
        self.assertEqual(len(jobs), 1)
        intake_ids = {x['coupon_id'] for x in c['input_inventory'][jobs[0]] if x['coupon_id'] is not None}
        for service in records(c, 'ASSEMBLY_SERVICE', 'ASSEMBLE'):
            emitted = {x['coupon_id'] for x in service['detail']['released_assemblies'] if x['coupon_id'] is not None}
            self.assertLessEqual(emitted, intake_ids,
                                 'Assembly output cannot appear without a registered assembly intake')

    def test_bifacial_rear_flux_is_bound_to_current_exposure(self):
        c, _ = subject.fixture(['BIFACIAL'])
        for flux in records(c, 'REAR_FLUX_ACQUIRE', 'BIFACIAL'):
            self.assertTrue(flux['light_active'],
                            'Current rear-flux acquisition precedes light configuration/activation')
            self.assertTrue(flux['interlocks_current'])

    def test_wet_light_has_geometry_matched_dark_and_new_water(self):
        c, _ = subject.fixture()
        by_case = {}
        for p in records(c):
            by_case.setdefault((p['branch_id'], p['case_id']), []).append(p)
        for (branch, case), phases in by_case.items():
            if branch not in {'HORIZONTAL', 'VERTICAL', 'ANGLE', 'BIFACIAL', 'OUTDOOR', 'CONDENSATE'}:
                continue
            light = next(p for p in phases if p['operation_id'] == 'LIGHT_ACQUIRE')
            dark = next(p for p in phases if p['operation_id'] == 'DARK_ACQUIRE')
            self.assertLess(phases.index(dark), phases.index(light))
            for field in ('coupon_id', 'surface_state_revision', 'setup_revision', 'mount_revision', 'calibration_id'):
                self.assertEqual(dark[field], light[field], (branch, case, field))
            self.assertNotEqual(dark['water_lot_id'], light['water_lot_id'])

    def test_cleaning_creates_new_surface_version(self):
        c, _ = subject.fixture(['REUSE'])
        cleaned = records(c, 'CLEANING_SERVICE', 'REUSE')[0]
        first = records(c, 'RECEIVE', 'REUSE')[0]
        after = records(c, 'METROLOGY_SERVICE', 'REUSE')[0]
        self.assertGreater(cleaned['coupon_version'], first['coupon_version'])
        self.assertGreater(cleaned['surface_state_revision'], first['surface_state_revision'])
        self.assertEqual(after['surface_state_revision'], cleaned['surface_state_revision'])
        self.assertIsNotNone(after['calibration_id'])

    def test_all_retrievals_follow_independent_safe_clearance(self):
        c, _ = subject.fixture()
        for p in records(c):
            if p['operation_id'] in {'DISCONNECT', 'RETRIEVE'}:
                self.assertTrue(p['independent_safe_state'])
                self.assertFalse(p['light_active'])

    def test_wet_front_camera_clock_not_playback_clock(self):
        case = next(x['cases'][0] for x in read('control_packages.json')['controls'] if x['id'] == 'WET_FRONT')
        self.assertEqual(case['source_constraints']['source_acquisition_fps'], 200)
        self.assertEqual(case['source_constraints']['published_playback_slowdown'], 10)
        analysis = next(x for x in read('analysis_contracts.json')['analyses'] if x['id'] == 'wet_front')
        self.assertTrue(any('never acquisition time' in g for g in analysis['guards']))

    def test_each_selected_route_has_exact_parent_material_records(self):
        for branch in subject.BRANCHES:
            with self.subTest(branch=branch):
                c, _ = subject.fixture([branch])
                for job_id, job in c['jobs'].items():
                    for parent in job['parents']:
                        released = parent['released_target_records']
                        for item in c['input_inventory'][job_id]:
                            self.assertTrue(any(all(r.get(k) == v for k, v in item.items()) for r in released))

    def test_assembly_service_invalidates_prior_calibration(self):
        c, _ = subject.fixture(['BIFACIAL'])
        phases = records(c, branch='ASSEMBLE')
        for i, service in enumerate(phases):
            if service['operation_id'] != 'ASSEMBLY_SERVICE':
                continue
            self.assertIsNone(service['calibration_id'])
            self.assertEqual(service['detail']['mounted_object_role'],
                             'independent_batch_carrier_not_downstream_device')
            self.assertEqual(phases[i + 1]['operation_id'], 'REGISTER_GEOMETRY')
            self.assertEqual(phases[i + 2]['operation_id'], 'CALIBRATE')
            self.assertIsNotNone(phases[i + 2]['calibration_id'])

    def test_source_sweep_does_not_authorize_real_setpoints(self):
        cases = next(x['cases'] for x in read('control_packages.json')['controls'] if x['id'] == 'HORIZONTAL')
        self.assertEqual(len(cases), 10)
        pairs = {(c['source_constraints']['material'], c['source_constraints']['source_concentration_suns']) for c in cases}
        self.assertEqual(pairs, {(material, sun) for material in ('bulk_water', 'processed_coupon') for sun in range(1, 6)})
        for case in cases:
            self.assertIsNone(case['source_constraints']['actual_station_setpoint'])
            self.assertTrue(case['physical_setpoints_not_authorized_by_source'])

    def test_excluded_or_unknown_branch_cannot_be_selected(self):
        for branch in ('BIOLOGY', 'CONTAMINANT_PREPARATION', 'LASER_FABRICATION', 'UNKNOWN'):
            with self.subTest(branch=branch), self.assertRaises(ValueError):
                subject.fixture([branch])

    def test_condensate_mass_record_is_distinct_from_evaporation(self):
        c, _ = subject.fixture(['CONDENSATE'])
        light = records(c, 'LIGHT_ACQUIRE', 'CONDENSATE')[0]
        condensate = records(c, 'CONDENSATE_ACQUIRE', 'CONDENSATE')[0]
        self.assertIsNotNone(condensate['collector_id'])
        self.assertIn('collector_mass_g', condensate['raw_columns'])
        self.assertNotIn('collector_mass_g', light['raw_columns'])
        self.assertTrue(condensate['detail']['mass_loss_is_not_collection'])

if __name__ == '__main__':
    unittest.main()
