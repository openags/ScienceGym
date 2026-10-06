"""Independent source-snapshot and semantic-boundary review assertions."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
from contract import ContractError, digest, load_contract
from fixtures import make_fixture

ACCEPTED_SOURCE_MANIFEST = '3a7bc1d7f22fa49069af4cfa1ee9834fd8ce43bbcb52fc751760e79ac0e109ca'
# Exact inherited original annotations from the independently accepted source review.
SOURCE_RECORDS = {
    'controls_and_repeats.json': '3560913d2761841255b141522a30c9c386376e41dda525da1c8cb537fec54dac',
    'cross_device_measurements.json': '703da68dd0956ad28403df86617970d5fd07e2418edd95db7683c48a935f6049',
    'failure_and_closeout.json': '946748e4c1b1ce954110fb316fdba345c6a960ac7cda11e3fb6d5845a863773f',
    'lineage_contract.json': 'e2250a7214ccdab26915a3f0ea6b636b586ac664a514fca8e8e078f9cb2633f1',
    'material_and_sample_dependencies.json': '7636e10ff25e23475d64731075e4c56a71edb010438db3222f45ecbfbc13cfbd',
    'read_coverage.json': 'e0626c7dcd5ea637e093f888b2a4dd09b3d676009d2b2b873671dc0036c27fce',
    'safety_boundaries.json': 'ec429590d7b8303d2d28e2cfeb41371583145d4cec4d2e4e9a3b2ad479670c7a',
    'sample_custody.json': '533151ec6b3a1cf75f98e4b0e0f700e43fe0df053dde01d9d9875854272a006e',
    'source_conflicts.json': '0acc74664428c1a8086e8773f3cacb5654acc0fa19898e1dbf08a9a31c0c3d4d',
    'source_facts.json': '547ea67ae711eaf9336b5f141697432ab30fcd8e2b252451a49b264d4cdb4282',
    'source_outcomes_reference.json': '19ffdb8adf519b9fb7cb29130b1b95ee6268254b1161d771a69175cd5b96dbf4',
    'source_update_status.json': '71a07943b6a758aeabfc0fc43ea0c4456095004b3104a3cda4f3c7d6c1220c07',
    'unknown_inputs.json': '10456853aac4dd6cb25500757bbd3634b3169f00d28020dce31d2827950c1209',
}


def read(name):
    return json.loads((ROOT / name).read_text())


class IndependentSourceBindingTests(unittest.TestCase):
    def test_accepted_source_provenance_pin(self):
        self.assertEqual(read('provenance.json')['accepted_review_manifest_sha256'], ACCEPTED_SOURCE_MANIFEST)
        self.assertEqual(read('provenance.json')['paper']['doi'], '10.1038/ncomms1289')

    def test_inherited_scientific_and_safety_records_are_exact(self):
        for name, expected in SOURCE_RECORDS.items():
            with self.subTest(file=name):
                self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected)

    def test_complete_inventory_and_evidence_only_anchors(self):
        bind = read('shared_binding_contract.json')
        for key, prefix, count in [('branch_ids', 'B', 9), ('route_ids', 'R', 12),
                                   ('station_ids', 'ST', 6), ('asset_ids', 'A', 8),
                                   ('unknown_ids', 'U', 20)]:
            self.assertEqual(bind[key], [prefix + '%02d' % i for i in range(1, count + 1)])
        self.assertEqual(len(bind['anchors']), 32)
        self.assertEqual(len({row['anchor_id'] for row in bind['anchors']}), 32)
        for row in bind['anchors']:
            self.assertEqual(row['kind'], 'evidence_only_proxy')
            self.assertIs(row['physical_motion_target'], False)
        self.assertEqual(bind['world_frame'], {'units': 'm', 'up_axis': 'Z', 'handedness': 'right', 'calibrated': False})

    def test_source_reading_scope_is_bounded(self):
        scope = read('read_coverage.json')
        self.assertEqual([row['page'] for row in scope['main_pages']], list(range(1, 9)))
        self.assertEqual(scope['main_figures'], list(range(1, 6)))
        self.assertEqual(scope['main_equations'], list(range(1, 10)))
        self.assertFalse(scope['raw_numeric_dataset_review'])
        self.assertFalse(scope['external_references_read'])
        self.assertFalse(scope['movie_visual_scope']['continuous_playback'])
        self.assertFalse(scope['movie_visual_scope']['temporal_measurement_validation'])

    def test_nine_branches_preserve_full_independent_inventory(self):
        branches = read('branches.json')
        self.assertEqual([row['id'] for row in branches['branches']], ['B%02d' % i for i in range(1, 10)])
        inventory = {item for group in branches['independent_inventory_crosswalk'].values() for item in group}
        self.assertEqual(inventory, {
            'apparatus_initial_state', 'matched_low_rate_morphologies', 'phi_reservoir_map',
            'morphology_statistics', 'rate_intermittency', 'fluidized_front_corals',
            'resuspended_viscous_fingers', 'viscosity_rate_scaling_control', 'high_phi_fracture',
            'porous_medium_comparison', 'phase_space_synthesis', 'equation_audit'})

    def test_fixture_runs_contain_no_numeric_observations(self):
        _, receipts, _ = make_fixture()
        def scalars(value):
            if isinstance(value, dict):
                for item in value.values():
                    yield from scalars(item)
            elif isinstance(value, list):
                for item in value:
                    yield from scalars(item)
            else:
                yield value
        for route in ('R05', 'R06', 'R07'):
            for run in receipts['REC_' + route]['payload']['runs']:
                self.assertEqual(run['scientific_outcome'], 'not_assessed')
                self.assertTrue(all(type(v) in (str, bool) for v in scalars(run)))
                for field in ('pressure_raw', 'image_raw'):
                    self.assertFalse(run[field]['raw_acquisition'])
                    self.assertEqual(run[field]['record_kind'], 'hash_only_placeholder')

    def test_source_and_fixture_actor_visibility_stay_separate(self):
        actor = read('agent_visible.json')
        self.assertEqual(set(actor['action_schema']['properties']), {'operation_id', 'evidence_id'})
        reference = read('evaluator_reference.json')
        self.assertFalse(reference['actor_visibility'])
        self.assertFalse(reference['source_outcome_is_generated_measurement'])
        self.assertFalse(reference['source_outcome_is_success_threshold'])
        self.assertFalse(reference['metric_values_emitted_by_contract'])

    def test_physical_holds_and_false_capabilities_remain_explicit(self):
        release = read('RELEASE_BOUNDARY.json')
        self.assertEqual(release['qualification_holds'], 20)
        self.assertEqual(release['physical_qualification'], 'HOLD_QUALIFICATION')
        self.assertEqual(release['runnable_whole_paper_experiments'], 0)
        for field in ('hardware_operation', 'robot_execution', 'fluid_simulation',
                      'raw_data_reproduced', 'source_code_run', 'scientific_reproduction',
                      'github_writes', 'source_media_exported'):
            self.assertIs(release[field], False)

    def mutated_contract(self, mutation):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for name in ('operations.json', 'shared_binding_contract.json', 'scene_task_contract.json', 'semantic_core.json'):
            shutil.copyfile(ROOT / name, root / name)
        binding = json.loads((root / 'shared_binding_contract.json').read_text())
        mutation(binding)
        for name in ('shared_binding_contract.json', 'scene_task_contract.json'):
            (root / name).write_text(json.dumps(binding))
        semantic = json.loads((root / 'semantic_core.json').read_text())
        semantic['shared_binding_contract_sha256'] = digest(binding)
        (root / 'semantic_core.json').write_text(json.dumps(semantic))
        return root

    def test_truncated_or_extended_route_bindings_cannot_skip_validation(self):
        for mutation in (lambda b: b['route_bindings'].pop(),
                         lambda b: b.update(route_bindings=[]),
                         lambda b: b['route_bindings'].append(copy.deepcopy(b['route_bindings'][0]))):
            root = self.mutated_contract(mutation)
            with self.assertRaises(ContractError):
                load_contract(root)

    def test_self_consistent_rehash_does_not_authorize_inventory_omissions(self):
        for field in ('branch_ids', 'route_ids', 'station_ids', 'asset_ids', 'material_ids', 'unknown_ids', 'conflict_ids'):
            with self.subTest(field=field):
                root = self.mutated_contract(lambda b, key=field: b[key].pop())
                with self.assertRaises(ContractError):
                    load_contract(root)

    def test_self_consistent_rehash_does_not_authorize_model_or_physical_flags(self):
        for field in ('model_implemented', 'physical_execution_enabled'):
            with self.subTest(field=field):
                root = self.mutated_contract(lambda b, key=field: b.update({key: True}))
                with self.assertRaises(ContractError):
                    load_contract(root)


if __name__ == '__main__':
    unittest.main()
