"""Independent review of the stated offline design/integrity scope only.

These tests do not execute a machine, numerical model, or research campaign.
"""
from copy import deepcopy
from pathlib import Path
import ast
import json
import math
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
import contract as c


def document(name):
    return json.loads((ROOT / name).read_text())


class IndependentDesign(unittest.TestCase):
    def test_source_route_coverage(self):
        # Independently mapped from the source auditor's 29 design requirements.
        mapping = {
            'R01': ['GENERATIVE_GEOMETRY'],
            'R02': ['FULL_FABRICATION'],
            'R03': ['BASE_MATERIAL_TENSION'],
            'R04': ['BASE_MATERIAL_TENSION'],
            'R05': ['FULL_FABRICATION'],
            'R06': ['FULL_FABRICATION'],
            'R07': ['PROTOTYPE_RECONFIGURATION'],
            'R08': ['FINITE_SIZE_PLANAR_N4'],
            'R09': ['FINITE_SIZE_STACKING_N4'],
            'R10': ['FINITE_SIZE_N4_N6'],
            'R11': ['COMPRESS_N4_A2'],
            'R12': ['COMPRESS_N4_AO'],
            'R13': ['COMPRESS_N6_A3'],
            'R14': ['COMPRESS_N6_A2O'],
            'R15': ['DENSITY_SCALING_N4'],
            'R16': ['CYCLIC_N4_A2'],
            'R17': ['CYCLIC_N6_A3'],
            'R18': ['MULTIDIRECTIONAL_N4'],
            'R19': ['MIXED_MODES_N4'],
            'R20': ['RUBBER_BAND_CONTROL'],
            'R21': ['LOAD_BEARING_DEMONSTRATIONS'],
            'R22': ['KINEMATIC_MOBILITY'],
            'R23': ['MODE_ENUMERATION'],
            'R24': ['MOST_PACKED_TESSELLATION', 'MACROCHAIN_TESSELLATION'],
            'R25': ['RIGIDITY_LOCKED', 'TOPOLOGY_SYMMETRY'],
            'R26': ['RUC_GEOMETRY'],
            'R27': ['RELATIVE_DENSITY', 'POISSON_RATIO'],
            'R28': ['INPLANE_ENERGY_N4', 'INPLANE_ENERGY_N6'],
            'R29': ['OUTPLANE_ENERGY_N4'],
        }
        self.assertEqual(set(mapping), {'R%02d' % i for i in range(1, 30)})
        self.assertEqual({b for branches in mapping.values() for b in branches}, set(c.BRANCHES))

    def test_fixture_operations_match_bidirectional_memberships(self):
        ops = {o['id']: o for o in document('operations.json')['operations']}
        for fid in c.FIXTURE_IDS:
            f = c.fixture(fid)
            bid = f['context']['branch_id']
            if bid not in c.BRANCHES:  # Explicit generic scoped-hold fixtures.
                continue
            for event in f['events']:
                with self.subTest(fixture=fid, operation=event['operation_id']):
                    self.assertIn(event['operation_id'], c.BRANCHES[bid]['operation_ids'])
                    self.assertIn(bid, ops[event['operation_id']]['branch_ids'])
        for bid, branch in c.BRANCHES.items():
            for oid in branch['operation_ids']:
                self.assertIn(bid, ops[oid]['branch_ids'])
        for oid, op in ops.items():
            for bid in op['branch_ids']:
                self.assertIn(oid, c.BRANCHES[bid]['operation_ids'])

    def test_geometry_review_does_not_require_its_own_release(self):
        ops = {o['id']: o for o in document('operations.json')['operations']}
        self.assertNotIn('released geometry', ops['VERIFY_GEOMETRY']['precondition'].lower())
        f = c.fixture('FULL_FABRICATION:FULL:GOOD')
        order = [e['operation_id'] for e in f['events']]
        self.assertLess(order.index('VERIFY_GEOMETRY'), order.index('RELEASE_DESIGN'))
        self.assertLess(order.index('RELEASE_DESIGN'), order.index('REQUEST_CUT'))

    def test_coupon_and_origami_preparation_are_distinct(self):
        coupon = c.fixture('BASE_MATERIAL_TENSION:FULL:GOOD')
        coupon_ops = [e['operation_id'] for e in coupon['events']]
        self.assertIn('REQUEST_CUT', coupon_ops)
        self.assertIn('VERIFY_CUT', coupon_ops)
        self.assertFalse({'REQUEST_FOLD', 'REQUEST_STACK_BOND', 'VERIFY_CURE',
                          'REQUEST_RECONFIGURATION'} & set(coupon_ops))
        origami = [e['operation_id'] for e in c.fixture('FULL_FABRICATION:FULL:GOOD')['events']]
        for op in ['VERIFY_CUT', 'REQUEST_FOLD', 'VERIFY_FOLD', 'REQUEST_STACK_BOND', 'VERIFY_STACK_BOND', 'VERIFY_CURE']:
            self.assertIn(op, origami)
        prepared = c.fixture('COMPRESS_N4_A2:PREPARED:GOOD')
        self.assertNotIn('REQUEST_CUT', [e['operation_id'] for e in prepared['events']])
        self.assertFalse(c.evaluate(prepared['events'], prepared['receipts'], prepared['fixture_id'])['synthetic_preparation_lineage_checked'])

    def test_source_gauges_grids_and_independent_counts(self):
        p = {x['id']: x['facts'] for x in document('source_parameters.json')['parameters']}
        self.assertEqual((p['P_COUPON']['crosshead_gauge_mm'], p['P_COUPON']['dic_gauge_mm']), (180, 20))
        self.assertEqual(p['P_FINITE_GRID']['planar_tessellation_grid'], [[i, i] for i in [1, 3, 5, 7, 9]])
        self.assertEqual(p['P_FINITE_GRID']['N4_stack_layer_grid'], [1, 2, 4, 6, 8])
        self.assertEqual(p['P_COUNTS']['main_compression_curve_independent_samples'], 3)
        self.assertEqual(p['P_COUNTS']['finite_size_per_geometry_independent_samples'], 5)
        self.assertEqual(p['P_COUNTS']['density_per_scale_independent_samples'], 5)
        self.assertEqual((p['P_COUNTS']['N4_reported_cycles'], p['P_COUNTS']['N6_reported_cycles']), (10, 4))

    def test_movies_and_demonstrations_cannot_be_machine_trials(self):
        evidence = {e['id']: e for e in document('evidence_map.json')['evidence']}
        coverage = document('coverage_matrix.json')['supplementary_videos']
        for i in range(4, 11):
            self.assertEqual(evidence['V' + str(i)]['media_kind'], 'numerical_animation')
            for bid in coverage['V' + str(i)]:
                self.assertEqual(c.BRANCHES[bid]['execution_class'], 'external_model_metadata')
        b = c.BRANCHES['LOAD_BEARING_DEMONSTRATIONS']
        self.assertEqual(b['execution_class'], 'source_only_gated')
        self.assertEqual(set(b['operation_ids']), {'REGISTER_INPUTS', 'ARCHIVE_RECORDS', 'CLEAN_STATION'})

    def test_all_conflicts_stay_visible_and_local(self):
        conflicts = document('source_conflicts.json')['conflicts']
        self.assertEqual({x['id'] for x in conflicts}, {'C%02d' % i for i in range(1, 12)})
        for conflict in conflicts:
            self.assertEqual(conflict['status'], 'UNRESOLVED_OR_SCOPE_DISTINCTION')
            self.assertTrue(conflict['branch_ids'])
            self.assertTrue(set(conflict['branch_ids']) <= set(c.BRANCHES))
            self.assertTrue(conflict['required_handling'])

    def test_actor_projection_and_no_execution_claims(self):
        actor = document('agent_visible.json')
        self.assertFalse(actor['can_declare_measurement'])
        self.assertFalse(actor['can_declare_service_qualification'])
        self.assertFalse(actor['can_supply_physical_observation'])
        self.assertFalse(actor['source_outcomes_exposed'])
        self.assertEqual(document('episode_input_contract.json')['actor_event_fields'], ['event_id', 'operation_id', 'evidence_id'])
        boundary = document('RELEASE_BOUNDARY.json')
        self.assertEqual(boundary['actor_visible_allowlist'], ['agent_visible.json'])
        self.assertEqual(boundary['validated_runnable_whole_paper_tasks'], 0)
        for key in ['physical_execution', 'numerical_execution', 'scientific_reproduction', 'whole_paper_execution_complete', 'exact_geometry_validated']:
            self.assertIs(boundary[key], False)

    def test_scene_binding_is_original_static_plan(self):
        assets = document('asset_binding_plan.json')['scene_assets']
        self.assertEqual(len(assets), 11)
        self.assertEqual(sum(len(a['required_anchor_ids']) for a in assets), 53)
        self.assertTrue(all(a['physical_geometry_validated'] is False for a in assets))
        bound = [o for a in assets for o in a['bind_operation_ids']]
        self.assertEqual(len(bound), 60)
        self.assertEqual(len(set(bound)), 60)

    def test_contract_has_no_device_network_or_solver_imports(self):
        tree = ast.parse((ROOT / 'tests' / 'contract.py').read_text())
        allowed = {'copy', 'decimal', 'pathlib', 'hashlib', 'json', 'math'}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertTrue({n.name for n in node.names} <= allowed)
            elif isinstance(node, ast.ImportFrom):
                self.assertIn(node.module, allowed)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, {'eval', 'exec', '__import__'})


class IndependentIntegrity(unittest.TestCase):
    def setUp(self):
        self.fid = 'COMPRESS_N4_A2:FULL:GOOD'
        self.f = c.fixture(self.fid)

    def reject(self, fixture, expected=None):
        with self.assertRaises(c.ContractError):
            c.evaluate(fixture['events'], fixture['receipts'], expected or self.fid)

    def test_all_fixtures_never_score_a_real_campaign(self):
        self.assertEqual(len(c.FIXTURE_IDS), 143)
        for fid in c.FIXTURE_IDS:
            f = c.fixture(fid)
            r = c.evaluate(f['events'], f['receipts'], fid)
            for flag in ['whole_campaign_complete', 'physical_execution', 'numerical_solver_execution',
                         'scientific_reproduction', 'whole_paper_execution_complete', 'source_expected_outcome_used']:
                self.assertIs(r[flag], False, (fid, flag))

    def test_rehashed_raw_tampering_still_rejected(self):
        for receipt in self.f['receipts'].values():
            if receipt['operation_id'] == 'ACQUIRE_RECORDS':
                receipt['payload']['raw']['force_N'][2] = 42
                receipt['payload']['raw_hash'] = c.digest(receipt['payload']['raw'])
        self.f['registry_digest'] = c.digest(self.f['receipts'])
        self.reject(self.f)

    def test_every_receipt_rejects_all_context_revisions(self):
        for rid in self.f['receipts']:
            for key in c.CONTEXT_KEYS:
                f = deepcopy(self.f)
                f['receipts'][rid]['context'][key] = 'foreign-or-stale'
                with self.subTest(receipt=rid, field=key):
                    self.reject(f)

    def test_valid_foreign_registry_is_not_accepted(self):
        for fid in ['COMPRESS_N4_AO:FULL:GOOD', 'COMPRESS_N4_A2:PREPARED:GOOD',
                    'BASE_MATERIAL_TENSION:FULL:GOOD', 'MODEL:KINEMATIC_MOBILITY']:
            self.reject(c.fixture(fid))

    def test_caller_mutation_does_not_change_pinned_registry(self):
        self.f['receipts'][self.f['events'][0]['evidence_id']]['payload']['synthetic_only'] = False
        self.reject(self.f)
        pristine = c.fixture(self.fid)
        self.assertTrue(c.evaluate(pristine['events'], pristine['receipts'], self.fid)['contract_passed'])

    def test_actor_cannot_add_any_observation_or_success_field(self):
        for field, value in [('force_N', 12), ('safe_release_observed', True), ('qualified', True),
                             ('source_expected_outcome', 1.63), ('success', True), ('payload', {})]:
            for index in [0, len(self.f['events']) // 2, len(self.f['events']) - 1]:
                f = deepcopy(self.f)
                f['events'][index][field] = value
                self.reject(f)

    def test_shutdown_ack_cannot_replace_independent_release(self):
        f = deepcopy(self.f)
        ack = next(e for e in f['events'] if e['operation_id'] == 'REQUEST_SAFE_OFF')
        verified = next(e for e in f['events'] if e['operation_id'] == 'VERIFY_SAFE_OFF')
        verified['evidence_id'] = ack['evidence_id']
        self.reject(f)

    def test_undock_before_release_rejected(self):
        f = deepcopy(self.f)
        events = f['events']
        i = next(i for i, e in enumerate(events) if e['operation_id'] == 'VERIFY_SAFE_OFF')
        j = next(i for i, e in enumerate(events) if e['operation_id'] == 'UNDOCK_SAMPLE')
        events[i], events[j] = events[j], events[i]
        self.reject(f)

    def test_equivalent_safe_closure_before_analysis_is_accepted(self):
        f = deepcopy(self.f)
        order = []
        seen = set()
        remaining = list(f['events'])
        preferred = {'REQUEST_SAFE_OFF', 'VERIFY_SAFE_OFF', 'UNDOCK_SAMPLE', 'INSPECT_SAMPLE'}
        while remaining:
            ready = [e for e in remaining if set(f['receipts'][e['evidence_id']]['depends_on']) <= seen]
            self.assertTrue(ready)
            e = sorted(ready, key=lambda e: e['operation_id'] not in preferred)[0]
            remaining.remove(e)
            order.append(e)
            seen.add(e['evidence_id'])
        ops = [e['operation_id'] for e in order]
        self.assertLess(ops.index('VERIFY_SAFE_OFF'), ops.index('ANALYZE_COMPRESSION'))
        self.assertTrue(c.evaluate(order, f['receipts'], self.fid)['contract_passed'])

    def test_failure_routes_cannot_be_good_or_virgin(self):
        for suffix in ['DAMAGED', 'DATA_HOLD', 'ISOLATION_HOLD']:
            fid = 'COMPRESS_N4_A2:FULL:' + suffix
            f = c.fixture(fid)
            result = c.evaluate(f['events'], f['receipts'], fid)
            self.assertFalse(result['synthetic_instance_complete'])
            self.assertFalse(result['virgin_sample_reusable'])
            self.reject(f)
            ops = [e['operation_id'] for e in f['events']]
            if suffix == 'ISOLATION_HOLD':
                self.assertNotIn('UNDOCK_SAMPLE', ops)
                self.assertNotIn('VERIFY_SAFE_OFF', ops)

    def test_numerical_metadata_and_source_context_cannot_measure(self):
        for fid in ['MODEL:' + b for b in c.MODELS] + ['SOURCE:LOAD_BEARING_DEMONSTRATIONS']:
            f = c.fixture(fid)
            self.assertFalse(c.evaluate(f['events'], f['receipts'], fid)['synthetic_measurement_checked'])
            self.assertNotIn('ACQUIRE_RECORDS', [e['operation_id'] for e in f['events']])


class IndependentArithmetic(unittest.TestCase):
    def test_raw_nonfinite_units_images_and_time_reject(self):
        mutations = [
            lambda r: r['force_N'].__setitem__(1, math.nan),
            lambda r: r['time_s'].__setitem__(2, r['time_s'][1]),
            lambda r: r['time_s'].__setitem__(2, -1),
            lambda r: r['displacement_m'].__setitem__(1, -.1),
            lambda r: r['image_ids'].__setitem__(1, r['image_ids'][0]),
            lambda r: r.__setitem__('height_m', True),
            lambda r: r.__setitem__('area_m2', -1),
            lambda r: r['units'].__setitem__('area', 'mm2'),
            lambda r: r['force_N'].pop(),
            lambda r: r.__setitem__('synthetic_only', False),
        ]
        for mutation in mutations:
            raw = c.raw_data('COMPRESS_N4_A2:FULL:GOOD')
            mutation(raw)
            with self.assertRaises(c.ContractError):
                c.raw_check(raw)

    def test_same_law_rescaled_dimensions_have_same_stress_strain(self):
        raw = c.raw_data('COMPRESS_N4_A2:FULL:GOOD')
        scaled = deepcopy(raw)
        scaled['area_m2'] *= 2
        scaled['force_N'] = [2 * v for v in raw['force_N']]
        scaled['height_m'] *= 3
        scaled['displacement_m'] = [3 * v for v in raw['displacement_m']]
        a = c.compression(raw, [1, 2, 3], 4)
        b = c.compression(scaled, [1, 2, 3], 4)
        self.assertAlmostEqual(a['engaged_modulus_Pa'], b['engaged_modulus_Pa'])
        self.assertAlmostEqual(a['yield_first_peak_Pa'], b['yield_first_peak_Pa'])

    def test_first_peak_and_fit_cannot_be_replaced_with_late_data(self):
        raw = c.raw_data('COMPRESS_N4_A2:FULL:GOOD')
        for indices, peak in [([1, 2, 3], 7), ([1, 4], 4), ([1, 1, 2], 4), ([2, 1], 4), ([True, 2], 4)]:
            with self.assertRaises(c.ContractError):
                c.compression(raw, indices, peak)

    def test_md_cd_reference_mismatch_rejects(self):
        raw = c.raw_data('BASE_MATERIAL_TENSION:FULL:GOOD')
        for direction, reference in [('MD', 'CD'), ('CD', 'MD'), ('45deg', '45deg')]:
            with self.assertRaises(c.ContractError):
                c.tensile(raw, [1, 2, 3], direction, reference)

    def test_cycles_reject_overlap_incomplete_history_and_negative_work(self):
        raw = c.raw_data('CYCLIC_N4_A2:FULL:GOOD')
        bad = deepcopy(raw['cycle_segments'])
        bad[1][0] -= 1
        with self.assertRaises(c.ContractError):
            c.cyclic(raw, bad, 10, 10)
        with self.assertRaises(c.ContractError):
            c.cyclic(raw, raw['cycle_segments'][:-1], 10, 9)
        raw['force_N'][3] = 100
        with self.assertRaises(c.ContractError):
            c.cyclic(raw, raw['cycle_segments'], 10, 10)

    def test_unknown_or_nonpositive_normalization_rejects(self):
        for baseline in [0, -1, True, math.nan, math.inf]:
            with self.assertRaises(c.ContractError):
                c.mixed_ratios(5, 2, 10, baseline)
        out = c.mixed_ratios(5, 2, 10, 4)
        self.assertEqual(out['modulus_relative_to_configuration1'], .5)
        self.assertEqual(out['channel_area_relative_to_configuration4'], .5)
        self.assertIs(out['measured_permeability'], False)

    def test_frames_and_single_specimen_do_not_supply_dispersion(self):
        for rows in [[{'sample_id': 'one', 'value': 2}],
                     [{'sample_id': 'one', 'value': 2}, {'sample_id': 'one', 'value': 3}],
                     [{'sample_id': 'one', 'value': 2, 'frame': 0}, {'sample_id': 'two', 'value': 3, 'frame': 1}]]:
            with self.assertRaises(c.ContractError):
                c.specimen_statistics(rows)

    def test_irregular_chain_cannot_be_tessellated(self):
        self.assertTrue(c.compatible_mode(6, 'IRREGULAR', False))
        for N, mode, tiled in [(6, 'IRREGULAR', True), (8, 'IRREGULAR', False),
                               (5, 'AA', True), (6, 'A2O', True), (6, 'AAA', 1)]:
            with self.assertRaises(c.ContractError):
                c.compatible_mode(N, mode, tiled)


if __name__ == '__main__':
    unittest.main()
