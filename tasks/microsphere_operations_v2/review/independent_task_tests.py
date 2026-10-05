#!/usr/bin/env python3
"""Independent offline contract audit. Only original package data are inspected.

Run standalone with the compact accepted original-review snapshot:
python review/independent_task_tests.py
Or add --reference PATH to compare directly with an external accepted review
No hardware, physical simulation, source imagery, or biological work is performed.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = None


def read(name, root=ROOT):
    if root is None:
        snapshot = json.loads((ROOT/'review'/'accepted_reference_contract.json').read_text(encoding='utf-8'))
        return snapshot['source_files'][name]
    return json.loads((root / name).read_text(encoding='utf-8'))


def by_id(items):
    return {item['id']: item for item in items}


class IndependentSourceContractTests(unittest.TestCase):
    def test_01_exact_branch_coverage_and_evidence_classes(self):
        expected = by_id(read('coverage_map.json', REFERENCE)['branches'])
        actual = by_id(read('branches.json')['branches'])
        self.assertEqual(set(actual), set(expected))
        self.assertEqual(len(actual), 13)
        for key, item in actual.items():
            for field, value in expected[key].items():
                self.assertEqual(item[field], value, (key, field))
            self.assertTrue(item['task_design_covered'])
            self.assertEqual(item['physical_execution_status'], 'UNRUN')

    def test_02_original_route_dependencies_and_requirements(self):
        expected = by_id(read('route_proposal.json', REFERENCE)['routes'])
        actual = by_id(read('operations.json')['operations'])
        self.assertEqual(set(actual), set(expected))
        self.assertEqual(len(actual), 13)
        for key, item in actual.items():
            for field, value in expected[key].items():
                if field != 'implemented':
                    self.assertEqual(item[field], value, (key, field))
            self.assertFalse(item['device_command_implemented'])
            self.assertFalse(item['physical_execution_authority'])
        done = set()
        while len(done) < len(actual):
            available = {k for k, v in actual.items() if set(v['depends_on']) <= done} - done
            self.assertTrue(available, 'The operation DAG contains a cycle or unknown dependency')
            done |= available

    def test_03_station_inventory_and_boundaries(self):
        expected = by_id(read('station_contracts.json', REFERENCE)['stations'])
        actual = by_id(read('station_contracts.json')['stations'])
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 7)
        self.assertTrue(all(r['station'] in actual for r in read('operations.json')['operations']))

    def test_04_all_sixteen_qualification_gaps_remain_unresolved(self):
        expected = read('unknown_inputs.json', REFERENCE)
        actual = read('unknown_inputs.json')
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual['unknowns']), 16)
        self.assertEqual(actual['physical_default'], 'HOLD_QUALIFICATION')
        self.assertTrue(all(x['status'] == 'unresolved' for x in actual['unknowns']))
        ids = {x['id'] for x in actual['unknowns']}
        self.assertTrue(all(set(r['unresolved_input_refs']) <= ids for r in read('operations.json')['operations']))

    def test_05_branch_asset_bindings_and_no_lost_branch(self):
        assets = {x['id'] for x in read('asset_requirements.json', REFERENCE)['assets']}
        branches = {x['id'] for x in read('branches.json')['branches']}
        operations = read('operations.json')['operations']
        self.assertEqual(len(assets), 9)
        self.assertEqual(set().union(*(set(r['asset_ids']) for r in operations)), assets)
        self.assertEqual(set().union(*(set(r['branch_ids']) for r in operations)), branches)
        for op in operations:
            self.assertTrue(set(op['asset_ids']) <= assets)
            self.assertTrue(set(op['branch_ids']) <= branches)

    def test_06_source_distinctions_controls_and_lineage_preserved(self):
        for name in ['source_conflicts.json', 'controls_and_repeats.json', 'sample_custody.json',
                     'lineage_contract.json', 'cross_device_measurements.json',
                     'material_and_sample_dependencies.json', 'failure_and_closeout.json',
                     'source_facts.json', 'source_outcomes_reference.json']:
            self.assertEqual(read(name), read(name, REFERENCE), name)

    def test_07_no_fabricated_runnable_or_scientific_counts(self):
        b = read('RELEASE_BOUNDARY.json')
        self.assertEqual(b['paper_level_designs'], 1)
        self.assertEqual(b['validated_runnable_whole_paper_tasks'], 0)
        for key in ['physical_execution', 'physical_simulation', 'scientific_reproduction',
                    'source_reanalysis', 'source_files_exported', 'hardware_safety_qualified',
                    'exact_geometry_validated', 'github_writes']:
            self.assertIs(b[key], False, key)
        self.assertFalse(read('evaluator_reference.json')['source_outcomes_in_reward'])
        self.assertIsNone(read('evaluator_reference.json')['measurement_success'])
        self.assertFalse(read('mock_contract.json')['scientific_measurements_generated'])
        self.assertFalse(read('mock_contract.json')['raw_images_generated'])
        self.assertIsNone(read('design_assumptions.json')['repeat_counts'])
        self.assertIsNone(read('design_assumptions.json')['physical_numeric_defaults'])

    def test_08_distinct_units_and_coordinate_planes(self):
        a = read('analysis_contracts.json')
        self.assertEqual(set(a['planes']), {'FRAME_OBJECT','FRAME_VIRTUAL','FRAME_DETECTOR','FRAME_SEM'})
        self.assertEqual(set(a['units']), {'nm','um','mm','m','pixel','dimensionless'})
        self.assertIn('optical objective magnification = added virtual magnification', a['prohibited_equivalences'])
        self.assertIn('20 nm experimental gold = 40 nm model film', a['prohibited_equivalences'])

    def test_09_actor_interface_and_fixture_scope(self):
        self.assertEqual(set(read('agent_visible.json')['allowed_action_schema']), {'operation_id','evidence_id'})
        self.assertEqual(set(read('episode_input_contract.json')['actor_keys']), {'operation_id','evidence_id'})
        self.assertFalse(read('episode_input_contract.json')['physical_runtime_available'])
        self.assertEqual(read('mock_contract.json')['fixture_origin'], 'independent_fixture')
        self.assertFalse(read('design_assumptions.json')['biological_scope'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference', type=Path, default=REFERENCE)
    args, rest = parser.parse_known_args()
    REFERENCE = args.reference.resolve() if args.reference else None
    unittest.main(argv=[sys.argv[0], *rest])
