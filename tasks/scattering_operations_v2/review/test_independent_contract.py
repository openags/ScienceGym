"""Independent finite metadata probes; no physics, equipment or real receipts."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('scattering_independent_contract', ROOT / 'tests' / 'contract.py')
C = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(C)


def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def record(fixture, kind):
    return next(item for item in fixture['records'] if item['kind'] == kind)


def payload(fixture, kind):
    return record(fixture, kind)['payload']


def run(operation, fixture):
    return C.check(C.action_for(operation, fixture), fixture)


class IndependentDesignTests(unittest.TestCase):
    def test_exact_paper_level_scope_and_held_physical_default(self):
        boundary = read('release_boundary.json')
        for key, expected in {'paper_design_count': 1, 'reported_experimental_branch_count': 5,
                              'source_numerical_review_branch_count': 4, 'preparation_branch_count': 3,
                              'actual_hardware_actions': 0, 'physical_simulations': 0,
                              'scientific_reproductions': 0}.items():
            self.assertEqual(boundary[key], expected)
        self.assertEqual(boundary['physical_default'], 'HOLD_QUALIFICATION')
        for key in ('physical_execution_enabled', 'whole_paper_execution_complete',
                    'publisher_assets_exported', 'exact_source_CAD', 'production_authentication_implemented'):
            self.assertIs(boundary[key], False)
        self.assertIsNone(boundary['all_thresholds_and_repeat_defaults'])

    def test_complete_distinct_branch_and_operation_inventories(self):
        branches = read('branches.json')['branches']
        expected = {'P01', 'P02', 'P03', 'B01', 'B02', 'B03', 'B04', 'B05', 'A01', 'A02', 'A03', 'A04', 'CLOSE'}
        self.assertEqual({item['id'] for item in branches}, expected)
        self.assertEqual(len(branches), len(expected))
        operations = read('operations.json')['operations']
        self.assertEqual({item['id'] for item in operations}, {'R%02d' % i for i in range(1, 15)})
        self.assertEqual(len(operations), 14)
        for item in branches:
            self.assertFalse(item['physical_executed'])
            self.assertFalse(item['numerical_executed'])
            self.assertIsNone(item['default_repeat_count'])
            self.assertIsNone(item['required_source_outcome_for_success'])
            self.assertTrue(set(item['operation_ids']) <= {op['id'] for op in operations})
        self.assertEqual({item['id'] for item in branches if item['source_reported_kind'] == 'numerical_review_only'},
                         {'A01', 'A02', 'A03', 'A04'})

    def test_operations_have_only_symbolic_actions_and_retain_failure_route(self):
        for operation in read('operations.json')['operations']:
            self.assertEqual(operation['origin'], 'original_authored_robot_task_design')
            self.assertFalse(operation['physical_execution_enabled'])
            self.assertEqual(set(operation['action_interface']['allowed_keys']), {'operation_id', 'evidence_ids'})
            self.assertFalse(operation['action_interface']['numeric_or_hardware_arguments_allowed'])
            self.assertEqual(tuple(operation['required_receipt_types']), C.KINDS[operation['id']])
            self.assertIn('lease', operation['on_failure'])
            self.assertIn('without blind retry', operation['on_failure'])

    def test_whole_program_coverage_links_resolve(self):
        branches = read('branches.json')['branches']
        branch_ids = {item['id'] for item in branches}
        facts = {item['id'] for item in read('source_evidence.json')['facts']}
        unknowns = {item['id'] for item in read('unknowns.json')['unknowns']}
        controls = {item['id'] for item in read('controls_and_repeats.json')['controls']}
        self.assertEqual(facts, {'F%02d' % i for i in range(1, 27)})
        self.assertEqual(controls, {'K%02d' % i for i in range(1, 13)})
        for branch in branches:
            self.assertTrue(set(branch['source_facts']) <= facts)
            self.assertTrue(set(branch['blocking_unknowns']) <= unknowns)
            self.assertTrue(set(branch['controls']) <= controls)
        coverage = read('coverage_map.json')
        self.assertTrue(coverage['source_complete_for_final_main_and_required_written_supplements'])
        self.assertFalse(coverage['complete_raw_data_or_code_review'])
        self.assertTrue(coverage['no_unreported_experiment_inferred'])
        covered = set()
        for item in coverage['records']:
            self.assertTrue(item['covered'])
            self.assertTrue(set(item['mapped_routes']) <= branch_ids)
            covered.update(item['mapped_routes'])
        self.assertEqual(covered, branch_ids)

    def test_unresolved_input_and_source_conflict_ledgers_preserved(self):
        unknowns = read('unknowns.json')
        self.assertEqual(unknowns['default_resolution'], 'HOLD_QUALIFICATION')
        self.assertEqual({item['id'] for item in unknowns['unknowns']}, {'U%02d' % i for i in range(1, 17)})
        for item in unknowns['unknowns']:
            if item['id'] != 'U16':
                self.assertFalse(item['resolved'])
        conflicts = read('source_conflicts.json')
        self.assertFalse(conflicts['silent_repair_allowed'])
        self.assertEqual({item['id'] for item in conflicts['records']}, {'C%02d' % i for i in range(1, 9)})

    def test_source_model_and_media_are_not_measured_force(self):
        facts = {item['id']: item for item in read('source_evidence.json')['facts']}
        for key in ('F13', 'F16', 'F17', 'F18', 'F19', 'F20', 'F21', 'F22'):
            self.assertEqual(facts[key]['evidence_kind'], 'numerical_or_theoretical')
        self.assertEqual(facts['F23']['evidence_kind'], 'media_description')
        self.assertEqual(facts['F24']['evidence_kind'], 'media_observation')
        self.assertIn('zero lateral force', facts['F13']['claim'])
        self.assertIn('not zero total', facts['F13']['claim'])
        self.assertIn('two-dimensional static-object', facts['F17']['claim'])
        self.assertIn('not a matched geometry', facts['F17']['claim'])
        self.assertIn('not reported', facts['F11']['claim'])
        self.assertFalse(read('evaluator_reference.json')['source_outcome_reward'])

    def test_source_table_inventory_retains_exact_counts_types_and_hashes(self):
        inventory = read('source_table_inventory.json')
        expected = {
            'M1': (30, '0a8812fe2a65d8951c4d696b93a0adb64754c5d928976e4436c5364ca691b30c'),
            'M2': (30, '6ef47abd0f4ed0e0f54e7cc9d73cccb0768758cd39dc82e156141c4e223249e7'),
            'M3': (20, '3e8749e5d308f9213d25aa80d69ad5337630de984f2f0d47465997eec945df4d'),
            'COILED_ANALYTICAL': (36, '39609b24537b24b23e7377de89996c55dd6dab4a48539f48263cb400b05e23ac'),
            'COILED_OPTIMIZED': (36, '37dc9d41b30872c3d24acba0f8313e2d2f6cf0de1f70c215d82160e39382f770')}
        self.assertEqual(inventory['total_entries_visually_checked'], 152)
        self.assertFalse(inventory['exported_values'])
        self.assertEqual({item['id'] for item in inventory['tables']}, set(expected))
        for item in inventory['tables']:
            self.assertEqual((item['entry_count'], item['values_sha256']), expected[item['id']])
            self.assertEqual(item['reported_status'], 'numerical_only_design' if item['id'].startswith('COILED') else 'fabricated_design')
            self.assertNotIn('values', item)

    def test_no_inferred_repeat_count_or_sample_identity(self):
        control = read('controls_and_repeats.json')
        for key in ('source_independent_specimen_count', 'source_independent_repeat_count', 'prospective_default_repeat_count'):
            self.assertIsNone(control[key])
        workflow = read('workflow.json')
        self.assertIsNone(workflow['numeric_condition_defaults'])
        self.assertIsNone(workflow['repeat_count_default'])
        self.assertTrue(workflow['no_forced_scientific_branch_order'])
        self.assertTrue(workflow['no_physical_execution'])
        binding = read('shared_binding_contract.json')
        self.assertEqual({item['design_id'] for item in binding['sample_families']}, {'M1', 'M2', 'M3'})
        for item in binding['sample_families']:
            for key in ('runtime_specimen_id', 'runtime_carrier_id', 'independent_specimen_count'):
                self.assertIsNone(item[key])

    def test_actor_view_does_not_claim_hidden_security_or_receipt_authority(self):
        actor = read('agent_visible.json')
        evaluator = read('evaluator_reference.json')
        self.assertEqual(set(actor['allowed_action_keys']), {'operation_id', 'evidence_ids'})
        self.assertFalse(actor['source_numeric_outcomes_visible'])
        self.assertFalse(actor['evaluator_receipt_internals_visible'])
        self.assertFalse(actor['physical_execution_enabled'])
        self.assertIsNone(actor['default_repeat_count'])
        self.assertTrue(evaluator['public_development_reference'])
        self.assertFalse(evaluator['production_hidden_split_implemented'])
        self.assertIn('Not implemented', evaluator['evidence_authentication'])

    def test_operation_asset_bindings_have_no_dangling_or_duplicate_anchors(self):
        binding = read('shared_binding_contract.json')
        assets = {item['asset_id']: item for item in binding['asset_groups']}
        self.assertEqual(set(assets), {'AS%02d' % i for i in range(1, 12)})
        anchors = [anchor for item in assets.values() for anchor in item['anchor_ids']]
        self.assertEqual(len(anchors), len(set(anchors)))
        operations = {item['id']: item for item in read('operations.json')['operations']}
        for item in binding['operation_bindings']:
            self.assertIn(item['operation_id'], operations)
            self.assertTrue(set(item['asset_ids']) <= set(assets))
            self.assertTrue(set(item['anchor_ids']) <= set(anchors))
            operation = operations[item['operation_id']]
            self.assertEqual(operation['asset_ids'], item['asset_ids'])
            self.assertEqual(operation['anchor_ids'], item['anchor_ids'])
        self.assertEqual(binding['qualification']['default_state'], 'HOLD_QUALIFICATION')
        self.assertFalse(binding['qualification']['physical_execution_enabled'])

    def test_complete_written_coverage_does_not_claim_continuous_movie_review(self):
        coverage = read('read_coverage.json')
        for key in ('MAIN', 'SI'):
            self.assertEqual(coverage[key]['pages_read'], list(range(1, 9)))
            self.assertEqual(coverage[key]['pages_visually_inspected'], list(range(1, 9)))
        self.assertFalse(coverage['MOVIES']['continuous_visual_review'])
        self.assertFalse(coverage['MOVIES']['audio_review'])
        self.assertTrue(all(not item['exported'] for item in read('provenance.json')['source_documents']))

    def test_safe_closeout_requires_observed_states_and_known_custody(self):
        failure = read('failure_contract.json')
        self.assertTrue(failure['no_automatic_retries'])
        self.assertTrue(failure['commands_are_not_observations'])
        self.assertTrue(failure['failure_is_not_scientific_zero'])
        self.assertTrue(failure['unknown_final_custody_blocks_normal_completion'])
        station = read('station_contracts.json')
        self.assertFalse(station['exclusive_lease']['branch_end_is_session_end'])
        self.assertFalse(station['receipt_policy']['request_is_receipt'])
        self.assertFalse(station['receipt_policy']['receipt_authenticity_implemented'])


class IndependentGuardTests(unittest.TestCase):
    def reject(self, operation, fixture):
        with self.assertRaises(C.ContractError):
            run(operation, fixture)

    def mutate_payload(self, operation, kind, mutations, branch='B01'):
        for key, value in mutations:
            fixture = C.fixture(branch, operation=operation)
            payload(fixture, kind)[key] = value
            with self.subTest(branch=branch, operation=operation, kind=kind, key=key, value=value):
                self.reject(operation, fixture)

    def test_positive_fixtures_remain_synthetic_and_held(self):
        for branch in C.EXPERIMENTS:
            for operation in ('R01', 'R02', 'R03', 'R04', 'R05', 'R06', 'R07', 'R08', 'R09', 'R10', 'R12', 'R13', 'R14'):
                with self.subTest(branch=branch, operation=operation):
                    result = run(operation, C.fixture(branch, operation=operation))
                    self.assertEqual(result['status'], 'SYNTHETIC_ACCEPT')
                    self.assertEqual(result['real_world_state'], 'HOLD_QUALIFICATION')
                    self.assertFalse(result['physical_execution_enabled'])
                    self.assertFalse(result['scientific_reproduction'])
        for branch in C.NUMERICAL:
            self.assertEqual(run('R11', C.fixture(branch, operation='R11'))['status'], 'SYNTHETIC_ACCEPT')

    def test_missing_receipt_for_each_operation_rejected(self):
        for operation, kinds in C.KINDS.items():
            branch = 'A01' if operation == 'R11' else 'B01'
            for kind in kinds:
                fixture = C.fixture(branch, operation=operation)
                fixture['records'] = [item for item in fixture['records'] if item['kind'] != kind]
                with self.subTest(operation=operation, kind=kind):
                    self.reject(operation, fixture)

    def test_each_scope_identifier_and_epoch_mismatch_rejected(self):
        for key in C.SCOPE:
            for kind in C.KINDS['R07']:
                fixture = C.fixture()
                record(fixture, kind)['scope'][key] = 'foreign_' + key
                with self.subTest(key=key, kind=kind):
                    self.reject('R07', fixture)

    def test_receipt_authority_status_real_claim_and_validity_rejected(self):
        for key, value in [('issuer', 'actor'), ('issuer', 'review_synthetic_authority'), ('status', 'requested'),
                           ('status', 'acknowledged'), ('synthetic', False), ('observed_at', 101),
                           ('valid_until', 99), ('observed_at', True), ('valid_until', float('nan'))]:
            fixture = C.fixture()
            record(fixture, 'calibration')[key] = value
            with self.subTest(key=key, value=value):
                self.reject('R07', fixture)

    def test_context_cannot_enable_physical_execution_or_wrong_design(self):
        for key, value in [('synthetic', False), ('physical_execution_enabled', True), ('now', float('inf')),
                           ('now', True), ('branch_id', 'B99'), ('design_id', 'M3'), ('mount_epoch', '')]:
            fixture = C.fixture()
            fixture['context'][key] = value
            with self.subTest(key=key, value=value):
                self.reject('R07', fixture)

    def test_actor_injection_unknown_ids_duplicates_and_extra_receipts_rejected(self):
        fixture = C.fixture()
        for key, value in [('approved', True), ('synthetic', True), ('payload', {'observed_safe': True}),
                           ('physical_execution_enabled', True), ('context', fixture['context']), ('numeric_value', 1)]:
            action = C.action_for('R07', fixture)
            action[key] = value
            with self.subTest(key=key), self.assertRaises(C.ContractError):
                C.check(action, fixture)
        for ids in [['does_not_exist'], ['plan_receipt', 'plan_receipt'], [], 'plan_receipt']:
            with self.subTest(ids=ids), self.assertRaises(C.ContractError):
                C.check({'operation_id': 'R07', 'evidence_ids': ids}, fixture)
        action = C.action_for('R07', fixture)
        action['evidence_ids'].append('archive_receipt')
        with self.assertRaises(C.ContractError):
            C.check(action, fixture)

    def test_evaluator_store_is_deep_copied_and_rejects_duplicate_ids(self):
        fixture = C.fixture()
        store = C.EvidenceStore(fixture['records'])
        old = store.get('plan_receipt')
        fixture['records'][1]['payload']['approved'] = False
        self.assertEqual(store.get('plan_receipt'), old)
        returned = store.get('plan_receipt')
        returned['payload']['approved'] = False
        self.assertEqual(store.get('plan_receipt'), old)
        duplicate = copy.deepcopy(fixture['records'])
        duplicate.append(copy.deepcopy(duplicate[0]))
        with self.assertRaises(C.ContractError):
            C.EvidenceStore(duplicate)

    def test_missing_prospective_independent_repeat_plan_rejected(self):
        mutations = [('approved', False), ('prospective', False), ('synthetic', False), ('repeat_count', None),
                     ('repeat_count', 0), ('repeat_count', True), ('repeat_count', 2.0), ('repeat_unit', 'frame'),
                     ('repeat_unit', 'unit_cell'), ('repeat_unit', 'plot_marker'), ('conditions', []),
                     ('conditions', ['same', 'same']), ('scientific_thresholds', {'paper_transition': 22}),
                     ('exclusion_policy', ''), ('branch_id', 'B05'), ('plan_id', 'foreign_plan')]
        for key, value in mutations:
            fixture = C.fixture()
            fixture['plan'][key] = value
            record(fixture, 'plan')['payload'] = copy.deepcopy(fixture['plan'])
            with self.subTest(key=key, value=value):
                self.reject('R07', fixture)
        fixture = C.fixture()
        fixture['plan'] = None
        self.reject('R07', fixture)

    def test_calibration_sign_units_geometry_and_clock_constraints(self):
        self.mutate_payload('R07', 'calibration', [('current', False), ('sign_tested', False), ('uncertainty', False),
            ('optical_transform', False), ('torsion_geometry', False), ('effective_lever_inferred_from_rod', True),
            ('invalidations', ['remounted']), ('invalidations', ['array_member_replaced']),
            ('invalidations', ['optics_moved']), ('qualified_scope', 'paper_reference')])
        self.mutate_payload('R07', 'coordinates', [('sign_tested', False), ('source_unit', 'm'),
            ('response_unit', 'deg'), ('separate_transforms', False), ('mapping_id', '')])
        self.mutate_payload('R07', 'clock', [('clock_ids', ['camera_clock']), ('continuous_epoch', False),
            ('synchronization_evidence', ''), ('residual_error', 1), ('residual_error', -1),
            ('approved_tolerance', None), ('approved_tolerance', float('nan')), ('residual_error', True)])

    def test_array_fabrication_and_supported_custody_failures_rejected(self):
        self.mutate_payload('R07', 'array', [('membership_revision', 'stale'), ('current_characterization', False),
            ('drift_accepted', False), ('member_ids', []), ('member_ids', ['duplicate', 'duplicate']),
            ('rejected_ids', ['synthetic_member_a'])])
        self.mutate_payload('R07', 'fabrication', [('design_id', 'M3'), ('inert_released', False),
            ('qa_accepted', False), ('grooves_clear', False), ('batch_id', '')])
        self.mutate_payload('R07', 'custody', [('receiver_accepted', False), ('supported', False),
            ('occupancy_known', False), ('specimen_id', 'other'), ('carrier_id', 'other'),
            ('previous_holder', 'unknown'), ('support_receipt', ''), ('condition_record', '')])
        self.mutate_payload('R07', 'support', [('accepted', False), ('supported', False),
            ('exclusive_lease', 'foreign'), ('lease_retained', False)])

    def test_uncertain_or_duplicate_admission_rejected(self):
        self.mutate_payload('R07', 'capture_ready', [('actual_ready', False), ('observed_service_status', 'UNKNOWN'),
            ('observed_service_status', 'REQUESTED'), ('duplicate_request', True)])
        fixture = C.fixture()
        fixture['attempts'].append({'attempt_id': fixture['context']['attempt_id']})
        self.reject('R07', fixture)
        fixture = C.fixture()
        fixture['completed_operations'].remove('R06')
        self.reject('R07', fixture)

    def test_numerical_branches_cannot_enter_physical_workflow(self):
        for branch in C.NUMERICAL:
            for operation in ('R03', 'R04', 'R05', 'R06', 'R07', 'R08', 'R09', 'R10', 'R12', 'R13', 'R14'):
                with self.subTest(branch=branch, operation=operation):
                    self.reject(operation, C.fixture(branch, operation=operation))
        self.mutate_payload('R11', 'source_numerical', [('solver_executed', True), ('physical_experiment', True),
            ('evidence_type', 'measured_force'), ('branch_id', 'B01'), ('source_locator', '')], branch='A01')

    def test_source_commands_and_partial_on_off_trace_rejected(self):
        self.mutate_payload('R08', 'source_observed', [('observed', False), ('evidence_type', 'command'),
            ('command_only', True), ('events', []), ('events', 'command_ack')])
        self.mutate_payload('R08', 'measurement', [('observed_source_state', False), ('tracking_valid', False),
            ('phases', ['on']), ('terminal_status', 'UNKNOWN'), ('terminal_status', 'RUNNING')])

    def test_raw_lineage_quantity_and_plan_completeness_constraints(self):
        self.mutate_payload('R08', 'measurement', [('raw_ids', []), ('raw_hashes', ['z' * 64, 'b' * 64]),
            ('raw_hashes', ['a' * 64]), ('retained_unmodified', False), ('physical_quantity', 'force'),
            ('unit', 'N'), ('unit', 'N/m'), ('transform_chain', ['pixels_to_force']), ('sign_tested', False),
            ('clock_aligned', False), ('calibration_current', False), ('uncertainty_record', '')])
        for branch in ('B02', 'B05'):
            self.mutate_payload('R08', 'measurement', [('conditions', ['condition_alpha']),
                ('conditions', ['condition_beta', 'condition_alpha'])], branch)

    def test_pose_readback_requires_existing_raw_parent(self):
        for branch in ('B04', 'B05'):
            self.mutate_payload('R08', 'measurement', [('source_pose_kind', 'commanded'), ('pose_raw_id', ''),
                ('pose_raw_id', 'unregistered_raw_parent')], branch)

    def test_measurement_cannot_bypass_current_clock_calibration_or_sign_receipts(self):
        for kind, key, value in [('calibration', 'current', False), ('calibration', 'invalidations', ['remount']),
                                 ('coordinates', 'sign_tested', False), ('clock', 'continuous_epoch', False),
                                 ('clock', 'residual_error', 1)]:
            self.mutate_payload('R08', kind, [(key, value)], 'B04')
            self.mutate_payload('R09', kind, [(key, value)], 'B04')
        self.mutate_payload('R08', 'measurement', [('device_clock_ids', ['unknown_clock'])], 'B04')

    def test_baseline_parent_and_analysis_raw_hashes_must_match(self):
        self.mutate_payload('R09', 'baseline', [('raw_parent_id', 'unknown_raw'), ('matched_epoch', False),
            ('subtraction_keeps_parents', False), ('raw_parent_id', 'raw_source_synthetic')])
        self.mutate_payload('R09', 'analysis', [('raw_parent_ids', ['unknown_raw']), ('raw_parent_hashes', ['c' * 64]),
            ('failed_attempts_retained', False), ('exclusions_recorded', False), ('filter_policy', ''),
            ('uncertainty_record', ''), ('source_outcome_target', 22), ('repeat_unit', 'frame'),
            ('independent_repeat_count', True), ('independent_repeat_count', 1)])

    def test_orientation_pair_rejects_reused_or_missing_epochs(self):
        for key, value in [('same_specimen_id', 'other'), ('orientations', ['original', 'original']),
                           ('mount_epochs', ['same', 'same']), ('mount_epochs', ['only_one']),
                           ('calibration_epochs', ['same', 'same']), ('signed_comparison_approved', False)]:
            fixture = C.fixture('B03', operation='R09')
            payload(fixture, 'analysis')['orientation_pair'][key] = value
            with self.subTest(key=key):
                self.reject('R09', fixture)

    def test_terminal_status_reconfiguration_and_failure_retention(self):
        self.mutate_payload('R10', 'attempt_terminal', [('attempt_id', 'other'), ('state', 'UNKNOWN'),
            ('state', 'RUNNING'), ('observed', False)])
        fixture = C.fixture(operation='R10')
        payload(fixture, 'attempt_terminal').update(reconfiguration_requested=True, safe_hold_and_requalification_required=False)
        self.reject('R10', fixture)
        for operation in ('R12', 'R14'):
            for key, value in [('status', 'UNKNOWN'), ('status', 'RUNNING'), ('raw_retained', False), ('failure_retained', False)]:
                fixture = C.fixture(operation=operation)
                fixture['attempts'][0][key] = value
                with self.subTest(operation=operation, key=key):
                    self.reject(operation, fixture)

    def test_four_independent_observed_safe_states_required(self):
        for kind in C.SAFE:
            self.mutate_payload('R12', kind, [('observed_safe', False), ('independent', False), ('command_only', True),
                ('scope', 'planned_configuration'), ('safe_access_qualified', False)])
            fixture = C.fixture(operation='R12')
            record(fixture, kind)['issuer'] = 'measurement_synthetic_authority'
            self.reject('R12', fixture)

    def test_return_quarantine_and_archive_preserve_every_admitted_specimen(self):
        self.mutate_payload('R13', 'custody_return', [('receiver_accepted', False), ('supported', False),
            ('occupancy_known', False), ('final_state', 'DISPOSED'), ('independent_access_release', False),
            ('previous_holder', 'unknown'), ('condition_record', '')])
        fixture = C.fixture(operation='R13')
        payload(fixture, 'custody_return')['final_state'] = 'QUARANTINED_ACCEPTED'
        self.assertEqual(run('R13', fixture)['status'], 'SYNTHETIC_ACCEPT')
        self.mutate_payload('R14', 'archive', [('attempt_ids', []), ('all_raw_retained', False),
            ('failed_records_retained', False), ('unknown_science_preserved', False), ('final_custody', {})])
        fixture = C.fixture(operation='R14')
        fixture['admitted_specimens'].append('missing_specimen')
        self.reject('R14', fixture)
        fixture = C.fixture(operation='R14')
        fixture['attempts'][0]['specimen_id'] = 'unregistered_specimen'
        self.reject('R14', fixture)
        for key, value in [('state', 'UNKNOWN'), ('receiver_accepted', False), ('occupancy_known', False),
                           ('condition_record', ''), ('holder', '')]:
            fixture = C.fixture(operation='R14')
            payload(fixture, 'archive')['final_custody'][fixture['context']['specimen_id']][key] = value
            with self.subTest(key=key):
                self.reject('R14', fixture)

    def test_return_and_archive_recheck_current_observed_safety(self):
        for operation in ('R13', 'R14'):
            for kind in C.SAFE:
                with self.subTest(operation=operation, kind=kind):
                    self.mutate_payload(operation, kind, [('observed_safe', False), ('independent', False),
                                                         ('command_only', True), ('safe_access_qualified', False)])

    def test_archive_cannot_relabel_unaccepted_return_or_its_holder(self):
        self.mutate_payload('R14', 'custody_return', [('receiver_accepted', False), ('occupancy_known', False),
            ('independent_access_release', False), ('to_holder', 'foreign_holder'), ('condition_record', 'foreign_condition')])
        fixture = C.fixture(operation='R14')
        final = payload(fixture, 'archive')['final_custody'][fixture['context']['specimen_id']]
        final['state'] = 'QUARANTINED_ACCEPTED'
        self.reject('R14', fixture)

    def test_physical_context_cannot_drop_admitted_specimen_identity(self):
        for operation in ('R07', 'R08', 'R09', 'R10', 'R12', 'R13', 'R14'):
            fixture = C.fixture(operation=operation)
            fixture['admitted_specimens'] = []
            with self.subTest(operation=operation):
                self.reject(operation, fixture)

    def test_unresolved_prior_attempt_blocks_new_admission(self):
        for status in ('PENDING', 'RUNNING', 'UNCERTAIN'):
            fixture = C.fixture(operation='R07')
            fixture['attempts'][0]['status'] = status
            with self.subTest(status=status):
                self.reject('R07', fixture)

    def test_downstream_actions_require_exact_current_admitted_attempt(self):
        for operation in ('R08', 'R09', 'R10'):
            fixture = C.fixture(operation=operation)
            fixture['attempts'] = [item for item in fixture['attempts'] if item['attempt_id'] != fixture['context']['attempt_id']]
            with self.subTest(operation=operation, case='not_admitted'):
                self.reject(operation, fixture)
            for field in ('branch_id', 'plan_id', 'mount_epoch', 'calibration_epoch', 'array_revision', 'lease_id'):
                fixture = C.fixture(operation=operation)
                current = next(item for item in fixture['attempts'] if item['attempt_id'] == fixture['context']['attempt_id'])
                current['scope'][field] = 'foreign'
                with self.subTest(operation=operation, field=field):
                    self.reject(operation, fixture)

    def test_current_terminal_status_cannot_be_relabelled(self):
        for operation in ('R08', 'R09', 'R10'):
            fixture = C.fixture(operation=operation)
            current = next(item for item in fixture['attempts'] if item['attempt_id'] == fixture['context']['attempt_id'])
            current['status'] = 'FAILED'
            with self.subTest(operation=operation):
                self.reject(operation, fixture)
        for key, value in [('status', 'UNCERTAIN'), ('raw_retained', False), ('failure_retained', False)]:
            fixture = C.fixture(operation='R13')
            fixture['attempts'][0][key] = value
            with self.subTest(operation='R13', key=key):
                self.reject('R13', fixture)

    def test_typed_raw_stream_hash_kind_clock_and_interval_joins(self):
        for key, value in [('id', 'unregistered'), ('sha256', 'f' * 64), ('kind', 'source_rendered_frame'),
                           ('clock_id', 'unknown'), ('observed_interval', [95, 90]),
                           ('observed_interval', [-1, 90]), ('observed_interval', [90, 101]),
                           ('specimen_id', 'other_specimen'), ('mount_epoch', 'other_mount')]:
            fixture = C.fixture('B04', operation='R08')
            payload(fixture, 'measurement')['streams'][0][key] = value
            with self.subTest(key=key, value=value):
                self.reject('R08', fixture)
        fixture = C.fixture('B04', operation='R08')
        measurement = payload(fixture, 'measurement')
        measurement['device_clock_ids'] = ['foreign_camera', 'foreign_source']
        for stream in measurement['streams']:
            stream['clock_id'] = 'foreign_camera' if stream['kind'] == 'camera_pixels' else 'foreign_source'
        for event in payload(fixture, 'source_observed')['events']:
            event['clock_id'] = 'foreign_source'
        self.reject('R08', fixture)

    def test_source_events_join_raw_stream_clocks_and_observed_intervals(self):
        for key, value in [('raw_id', 'missing_raw'), ('raw_id', 'raw_camera_synthetic'),
                           ('clock_id', 'camera_clock'), ('observed_time', 99), ('observed_time', -1),
                           ('observed_time', float('nan')), ('state', 'REQUESTED_ON')]:
            fixture = C.fixture(operation='R08')
            payload(fixture, 'source_observed')['events'][0][key] = value
            with self.subTest(key=key, value=value):
                self.reject('R08', fixture)
        fixture = C.fixture(operation='R08')
        events = payload(fixture, 'source_observed')['events']
        events[1]['event_id'] = events[0]['event_id']
        self.reject('R08', fixture)
        fixture = C.fixture(operation='R08')
        payload(fixture, 'source_observed')['events'].reverse()
        self.reject('R08', fixture)

    def test_repeat_records_need_independent_identity_and_raw_binding(self):
        self.mutate_payload('R09', 'analysis', [('repeat_records', None), ('repeat_records', [])])
        for key, value in [('repeat_unit', 'frame'), ('specimen_id', 'foreign'), ('mount_epoch', 'foreign'),
                           ('calibration_epoch', 'foreign'), ('trial_id', 'foreign'),
                           ('raw_parent_id', 'raw_source_synthetic'), ('raw_parent_id', 'missing_raw'),
                           ('status', 'UNKNOWN')]:
            fixture = C.fixture(operation='R09')
            payload(fixture, 'analysis')['repeat_records'][0][key] = value
            with self.subTest(key=key, value=value):
                self.reject('R09', fixture)
        for field in ('repeat_unit_id', 'raw_parent_id', 'trial_id'):
            fixture = C.fixture(operation='R09')
            repeats = payload(fixture, 'analysis')['repeat_records']
            repeats[1][field] = repeats[0][field]
            with self.subTest(field=field):
                self.reject('R09', fixture)

    def test_flip_pair_must_join_qualified_raw_orientation_and_current_endpoint(self):
        for key, value in [('raw_parent_ids', ['raw_source_synthetic', 'raw_events_synthetic']),
                           ('raw_parent_ids', ['raw_camera_synthetic', 'raw_camera_synthetic']),
                           ('mount_epochs', ['foreign_before', 'foreign_after']),
                           ('calibration_epochs', ['foreign_before', 'foreign_after'])]:
            fixture = C.fixture('B03', operation='R09')
            payload(fixture, 'analysis')['orientation_pair'][key] = value
            with self.subTest(key=key):
                self.reject('R09', fixture)
        fixture = C.fixture('B03', operation='R09')
        payload(fixture, 'measurement')['streams'][1]['orientation'] = 'original'
        self.reject('R09', fixture)

    def test_malformed_actor_shapes_fail_closed_without_escaping_guard(self):
        fixture = C.fixture()
        for action in (None, [], {'operation_id': 'R07'}, {'operation_id': [], 'evidence_ids': []},
                       {'operation_id': 'R07', 'evidence_ids': [None]},
                       {'operation_id': 'R07', 'evidence_ids': [{}]}):
            with self.subTest(action=action), self.assertRaises(C.ContractError):
                C.check(action, fixture)

    def test_calibration_epoch_inventory_scope_time_and_ancestry(self):
        self.mutate_payload('R07', 'calibration', [('qualified_epochs', []), ('qualified_epochs', None)])
        for branch, operation in [('B01', 'R07'), ('B03', 'R09')]:
            for key, value in [('specimen_id', 'foreign'), ('array_revision', 'foreign'),
                               ('configuration_epoch', 'foreign'), ('sign_tested', False),
                               ('uncertainty', False), ('evidence_ref', ''), ('evidence_ref', True),
                               ('qualified_interval', [101, 110]), ('qualified_interval', [0, 50]),
                               ('qualified_interval', [110, 80])]:
                fixture = C.fixture(branch, operation=operation)
                current = next(item for item in payload(fixture, 'calibration')['qualified_epochs']
                               if item['calibration_epoch'] == fixture['context']['calibration_epoch'])
                current[key] = value
                with self.subTest(branch=branch, operation=operation, key=key, value=value):
                    self.reject(operation, fixture)
        fixture = C.fixture('B03', operation='R09')
        epochs = payload(fixture, 'calibration')['qualified_epochs']
        payload(fixture, 'calibration')['qualified_epochs'] = [item for item in epochs
            if item['calibration_epoch'] == fixture['context']['calibration_epoch']]
        self.reject('R09', fixture)
        fixture = C.fixture('B03', operation='R09')
        epochs = payload(fixture, 'calibration')['qualified_epochs']
        epochs.append(copy.deepcopy(epochs[0]))
        self.reject('R09', fixture)

    def test_cross_specimen_aggregation_is_explicitly_held(self):
        for operation in ('R02', 'R07', 'R08', 'R09'):
            fixture = C.fixture(operation=operation)
            fixture['plan']['repeat_unit'] = 'specimen'
            record(fixture, 'plan')['payload'] = copy.deepcopy(fixture['plan'])
            with self.subTest(operation=operation, case='multiple_specimen_repeats'):
                self.reject(operation, fixture)
            fixture = C.fixture(operation=operation)
            fixture['plan']['repeat_bindings'][1]['specimen_id'] = 'other_specimen'
            record(fixture, 'plan')['payload'] = copy.deepcopy(fixture['plan'])
            with self.subTest(operation=operation, case='foreign_specimen_binding'):
                self.reject(operation, fixture)

    def test_evidence_references_are_identifiers_not_truthy_flags(self):
        cases = [('R07', 'fabrication', 'batch_id', 'B01'),
                 ('R07', 'coordinates', 'mapping_id', 'B01'),
                 ('R07', 'clock', 'synchronization_evidence', 'B01'),
                 ('R08', 'measurement', 'uncertainty_record', 'B01'),
                 ('R09', 'analysis', 'filter_policy', 'B01'),
                 ('R09', 'analysis', 'uncertainty_record', 'B01'),
                 ('R11', 'source_numerical', 'source_locator', 'A01')]
        for operation, kind, key, branch in cases:
            self.mutate_payload(operation, kind, [(key, True), (key, 1), (key, ['claim'])], branch)


if __name__ == '__main__':
    unittest.main()
