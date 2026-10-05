"""Independent static review tests. No device access, physics, or observations.
Run: PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s review -p 'test_independent_contract.py' -v
"""
import copy
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RETAINED = {
    'source_facts.json': '9e572b4d7b6517973f01d8b3a1be3b0e2f4c83d56f639d8558407a6ec3f44914',
    'source_conflicts.json': '26bfa3f076ee36dac3d0899909b9f1c0c88c09e331436799de55692341a10b3f',
    'source_outcomes_reference.json': '1e2238ac7807675d84eb462d64a0f9f7c5c4ccf8492b8d014e1e7dcaf392b1d3',
    'source_table_inventory.json': '27cbda1c1d142f9faba9ee2e241b59dee6ed9843bad69b54f3fa875b537289a5',
    'source_update_status.json': '307ba2723ff7cc18373af5fd70278b2b037f185309746b7d0ede51cafacea810',
    'source_access_audit.json': '141d96c066cd9668c15fde3622a320a676c14f3448b748ab714bb06eb6bc5557',
    'coverage_map.json': 'fdb8647b81698cd089a82521cd4e2cc6cccc60154f7d0a98b6e3509304d88e59',
    'station_contracts.json': 'e1b612e38f5ca8f05183e2d56d7ef22ad384b93be0b64a3c20f13a0566811caa',
    'lineage_contract.json': '7f1817db3ddfcac2414918bf209798574df5d016eac14d8a6b0fc40089d0bca0',
    'sample_custody.json': '6a116876c96403b2fe6e0de55fafec86f3fb54f41efcb40b95cb3a57a74430fc',
    'controls_and_repeats.json': 'ebdb105225830883d07d549a9973628ac2f6b81b2919400dd983c391e78d1f37',
    'cross_device_measurements.json': '6810bc4ce4d14f82b3b7f8d01ecb9edeefa9fd3f93661f750912e551a7161a93',
    'material_and_sample_dependencies.json': '370cf6e650fbc0d61544bd4c8df1e27e09b9d70ceb56ec574efeda8cafd5bd89',
    'failure_and_closeout.json': '5b6847c42c553ed6b4c2cffea51ed1dbe3474a20c3ee3b0e59097deb35fc6753',
    'unknown_inputs.json': 'bc37b451889de2a48ad7246644234a7ce4c37ecf62165644ee85b1fdf1eed83d',
    'route_proposal.json': '3b9976a433dd6913c5720240503dddda136b048694964d3f3b22761f9df0c6b6',
    'asset_requirements.json': '286b9f40eb4a0a77b3ebe50b4761dd92e441fd4c698c33561400909285eb0de4',
}

def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))

def topology_violations(identity):
    """Independent negative-test oracle, deliberately not production code."""
    errors = []
    regions = {r['region_id']: r for r in identity['electrical_regions']}
    if set(regions) != {'Array1', 'Array2', 'HB'}:
        errors.append('regions')
    for key in ('Array1', 'Array2'):
        if regions.get(key, {}).get('parallel_elements') != 118:
            errors.append('subarray_elements')
        if regions.get(key, {}).get('nominal_resistance_source') != 'R_K/236, about 109 ohm':
            errors.append('subarray_resistance')
    if {r.get('physical_parent') for r in regions.values()} != {'QHA_CHIP'}:
        errors.append('single_chip')
    whole = identity['whole_series_array']
    if set(whole['composed_regions']) != {'Array1', 'Array2'} or whole['total_elements'] != 236:
        errors.append('whole_topology')
    if whole['nominal_resistance_source'] != 'R_K/118, about 219 ohm':
        errors.append('whole_resistance')
    if whole['independent_sample'] is not False:
        errors.append('pseudo_replication')
    refs = {r['logical_id']: r for r in identity['external_reference_roles']}
    if set(refs) != {'REF100', 'REF12K9'}:
        errors.append('reference_identity')
    if refs.get('REF100', {}).get('bath_role') != 'OIL100' or refs.get('REF12K9', {}).get('bath_role') != 'AIR12K9':
        errors.append('reference_baths')
    return errors

class IndependentStaticContract(unittest.TestCase):
    def test_01_exact_accepted_annotations(self):
        for name, expected in EXPECTED_RETAINED.items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected)
        provenance = {r['path']: r['sha256'] for r in read('source_packet_reference.json')['retained_files']}
        self.assertEqual(provenance, EXPECTED_RETAINED)

    def test_02_complete_counts_and_unique_ids(self):
        for filename, field, prefix, count in [
            ('source_facts.json', 'facts', 'F', 29), ('source_conflicts.json', 'items', 'C', 18),
            ('source_outcomes_reference.json', 'outcomes', 'O', 14), ('unknown_inputs.json', 'items', 'U', 20),
            ('station_contracts.json', 'stations', 'ST', 8), ('asset_requirements.json', 'requirements', 'AS', 11)]:
            self.assertEqual([r['id'] for r in read(filename)[field]], [f'{prefix}{i:02d}' for i in range(1, count + 1)])
        self.assertEqual(len(read('source_table_inventory.json')['main_tables'][0]['rows']), 9)

    def test_03_identity_positive(self):
        self.assertEqual(topology_violations(read('identity_contract.json')), [])

    def test_04_identity_mutants_rejected(self):
        original = read('identity_contract.json')
        mutants = []
        m = copy.deepcopy(original); m['whole_series_array']['nominal_resistance_source'] = 'R_K/236, about 109 ohm'; mutants.append(m)
        m = copy.deepcopy(original); m['electrical_regions'][0]['parallel_elements'] = 236; mutants.append(m)
        m = copy.deepcopy(original); m['electrical_regions'][1]['physical_parent'] = 'SECOND_CHIP'; mutants.append(m)
        m = copy.deepcopy(original); m['whole_series_array']['independent_sample'] = True; mutants.append(m)
        m = copy.deepcopy(original); m['external_reference_roles'][1]['bath_role'] = 'OIL100'; mutants.append(m)
        for m in mutants:
            self.assertTrue(topology_violations(m))

    def test_05_complete_operations_preserve_source_route(self):
        ops = read('operations.json')['operations']
        self.assertEqual([r['id'] for r in ops], [f'R{i:02d}' for i in range(15)])
        original = read('route_proposal.json')['steps']
        for source, op in zip(original, ops):
            for key, value in source.items():
                self.assertEqual(op[key], value, (op['id'], key))
            self.assertIs(op['physical_execution_enabled'], False)
            self.assertEqual(op['action_interface']['allowed_keys'], ['operation_id', 'evidence_ids'])
            self.assertIs(op['action_interface']['numeric_or_hardware_arguments_allowed'], False)

    def test_06_dependency_graph_acyclic_and_closeout_independent(self):
        ops = {o['id']: o for o in read('operations.json')['operations']}
        seen, active = set(), set()
        def visit(n):
            self.assertNotIn(n, active)
            if n in seen: return
            active.add(n)
            for dep in ops[n]['depends_on']:
                self.assertIn(dep, ops); visit(dep)
            active.remove(n); seen.add(n)
        for n in ops: visit(n)
        self.assertEqual(ops['R14']['depends_on'], ['R03'])
        wf = read('workflow.json')
        self.assertIs(wf['analysis_may_not_delay_physical_safety'], True)
        self.assertEqual(wf['actual_started_jobs'], [])
        self.assertEqual(wf['actual_closed_jobs'], [])
        self.assertEqual(set(wf['initial_operation_states'].values()), {'held_qualification'})

    def test_07_comparison_graph_and_covariance(self):
        graph = read('cross_device_measurements.json')['source_graph']
        self.assertEqual(len(graph['nodes']), 4)
        edges = {frozenset(e['listed_pair']) for e in graph['direct_edges']}
        self.assertEqual(len(edges), 5)
        self.assertEqual(edges, {frozenset(p) for p in [
            ('Array1', 'Array2'), ('on-chip Hall bar', '100-ohm standard'),
            ('Array1', '100-ohm standard'), ('Array2', '100-ohm standard'), ('on-chip Hall bar', 'Array1')]})
        self.assertEqual(graph['connected_graph_independent_cycle_count'], 2)
        self.assertEqual(graph['simple_closed_loop_count'], 3)

    def test_08_optional_branches_remain_held(self):
        branches = read('branches.json')['branches']
        self.assertEqual({b['id'] for b in branches if b['optional_physical_execution']}, {'HIGH_BIAS', 'EXTERNAL'})
        self.assertEqual({op for b in branches for op in b['operations']}, {f'R{i:02d}' for i in range(15)})
        for branch in branches:
            self.assertEqual(branch['initial_state'], 'held_qualification')
            self.assertIsNone(branch['planned_conditions'])
            self.assertIsNone(branch['repeat_count'])

    def test_09_printed_analysis_holds_not_repaired(self):
        analysis = read('analysis_holds.json')
        self.assertEqual(analysis['default'], 'ANALYSIS_HOLD')
        self.assertEqual(analysis['approved_algorithms'], [])
        self.assertEqual(analysis['resolutions'], [])
        holds = {h['id']: h for h in analysis['holds']}
        self.assertIn('C05', holds['AH_ALLAN_INPUT']['source_conflicts'])
        self.assertIn('C13', holds['AH_ALLAN_ERROR']['source_conflicts'])
        self.assertIn('C04', holds['AH_LOOP']['source_conflicts'])
        self.assertIn('R12', holds['AH_ALLAN_INPUT']['blocks'])
        self.assertIn('R13', holds['AH_LOOP']['blocks'])
        self.assertIsNone(read('measurement_contract.json')['analysis_implementation'])

    def test_10_independent_repeats_have_no_fabricated_counts(self):
        repeat = read('repeat_contract.json')
        self.assertEqual(set(repeat['independent_units']), {'fabrication_lot', 'physical_chip', 'cooldown', 'remount', 'qualified_provider_or_lab'})
        self.assertTrue(all(n is None for n in repeat['unit_counts'].values()))
        self.assertIn('CCC_reading', repeat['within_run_units'])
        self.assertEqual(len(read('controls_and_repeats.json')['controls']), 14)

    def test_11_measurement_lineage_required(self):
        measurement = read('measurement_contract.json')
        self.assertEqual(measurement['new_measurements'], [])
        self.assertIs(measurement['numeric_measurement_generator'], False)
        expected = {'immutable_bundle_hash', 'provider_id', 'job_id', 'physical_chip_id', 'region_ids',
            'carrier_id', 'mount_id', 'custodian_id', 'lease_ids', 'calibration_ids', 'method_revision',
            'configuration_revision', 'reference_device_id', 'test_device_id', 'ratio_direction',
            'per_device_current_records', 'per_device_power_records', 'acquisition_start', 'acquisition_end',
            'raw_timestamps', 'polarity_cycle_ids', 'per_reading_SD_record_ids', 'uncertainty_semantics',
            'covariance_dependency_ids', 'exclusion_log_id', 'fault_flag_ids', 'repeat_unit_ids'}
        self.assertLessEqual(expected, set(measurement['required_metadata']))

    def test_12_calibration_and_device_leases(self):
        fields = set(read('calibration_contract.json')['required_fields'])
        self.assertLessEqual({'valid_from', 'valid_until', 'physical_resource_id', 'configuration_revision',
            'calibration_revision', 'method_revision', 'terminal_map_revision', 'before_check_id', 'after_check_id'}, fields)
        lease = read('device_lease_contract.json')
        self.assertEqual(lease['initial_leases'], [])
        self.assertIn('physical_resource_id', lease['rule'])
        self.assertIn('atomically', lease['rule'])
        self.assertIn('Retain', lease['on_communications_loss'])

    def test_13_independent_closeout_and_custody(self):
        closeout = read('failure_and_closeout.json')
        self.assertEqual(len(closeout['failures']), 10)
        self.assertEqual(len(closeout['required_independent_closeout_observations']), 5)
        self.assertIn('per-branch complete/partial/failed/held/unattempted labels', closeout['final_receipt'])
        custody = read('sample_custody.json')
        self.assertIn('Last accepted support/custodian', custody['release_rule'])

    def test_14_release_boundaries(self):
        boundary = read('release_boundary.json')
        for key in ('physical_execution_enabled', 'production_receipt_authentication_implemented',
                    'physical_observations_generated', 'publisher_assets_exported', 'exact_source_CAD',
                    'numerical_analysis_implemented', 'source_outcomes_used_for_reward'):
            self.assertIs(boundary[key], False, key)
        for key in ('validated_runnable_whole_paper_tasks', 'hardware_actions', 'physical_simulations', 'scientific_reproductions'):
            self.assertEqual(boundary[key], 0, key)
        self.assertIsNone(boundary['all_thresholds_and_repeat_defaults'])
        self.assertEqual(boundary['paper_design_count'], 1)

    def test_15_actor_view_has_no_reported_outcome_targets(self):
        actor = read('agent_visible.json')
        self.assertIs(actor['physical_execution_enabled'], False)
        self.assertIs(actor['source_context_in_actor_view'], False)
        self.assertEqual(actor['action_keys'], ['operation_id', 'evidence_ids'])
        self.assertEqual(read('evaluator_reference.json')['actor_files'], ['agent_visible.json'])
        for op in actor['operations']:
            self.assertEqual(set(op), {'id', 'name', 'required_evidence'})


    def test_16_exact_scene_binding_and_all_anchors(self):
        contract = read('shared_binding_contract.json')
        self.assertEqual(hashlib.sha256((ROOT / 'shared_binding_contract.json').read_bytes()).hexdigest(),
                         'd86dc8699ca1bf8fe2c552d318e5e5eac8a6b613a27ed87d4cab56b2f8d7b86d')
        self.assertEqual([a['asset_id'] for a in contract['assets']], [f'AS{i:02d}' for i in range(1, 12)])
        anchors = [a for asset in contract['assets'] for a in asset['anchors']]
        self.assertEqual(len(anchors), 32)
        self.assertEqual(len({a['anchor_id'] for a in anchors}), 32)
        for anchor in anchors:
            self.assertEqual(anchor['mode'], 'evidence_only')
            self.assertIs(anchor['physical_actuation_enabled'], False)
        bindings = {r['route_id']: r for r in contract['route_bindings']}
        for operation in read('operations.json')['operations']:
            binding = bindings[operation['id']]
            self.assertEqual(operation['asset_ids'], binding['asset_ids'])
            self.assertEqual(operation['anchor_ids'], binding['target_anchor_ids'])
            self.assertEqual(operation['stations'], binding['station_ids'])
        self.assertIs(contract['non_executable'], True)
        self.assertIs(contract['physics_simulation_performed'], False)
        self.assertIs(contract['electrical_simulation_performed'], False)

if __name__ == '__main__':
    unittest.main()
