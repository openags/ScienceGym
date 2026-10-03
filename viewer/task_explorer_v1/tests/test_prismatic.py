"""Independent source-fidelity and symbolic-loop tests for prismatic integration."""
import collections
import copy
import hashlib
import itertools
import json
import unittest
import xml.etree.ElementTree as ET

from test_semantics import ROOT, TASKS, builder, get, ids


TARGET_BODY = ['TARGET_STAGE', 'ACTUATE', 'RELEASE', 'OBSERVE', 'RESET_STATE']


def loop_nodes(nodes, loop_id):
    return [node for node, _ in builder.walk(nodes)
            if node['type'] == 'loop' and node.get('meta', {}).get('loop_id') == loop_id]


class PrismaticBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.family = get('prismatic')
        cls.routes = {route['id']: route for route in cls.family['routes']}

    def one_loop(self, nodes, loop_id):
        found = loop_nodes(nodes, loop_id)
        self.assertEqual(len(found), 1, loop_id)
        return found[0]

    def assert_repetition(self, parent, input_name, body):
        self.assertEqual(len(parent['children']), 1)
        repeat = parent['children'][0]
        self.assertEqual(repeat['type'], 'loop')
        self.assertEqual(repeat['meta']['input'], input_name)
        self.assertIsNone(repeat['meta']['value'])
        self.assertEqual(repeat['children'], body)
        self.assertIs(repeat['ordered'], False)
        self.assertIs(repeat['symbolic'], True)

    def test_twelve_configurations_seven_families_and_49_templates(self):
        self.assertEqual(len(self.routes), 12)
        self.assertEqual(len(self.family['operations']), 49)
        self.assertEqual(len({op['id'] for op in self.family['operations']}), 49)
        self.assertEqual(len(self.family['context']['branch_policy']['families']), 7)
        self.assertEqual(len(self.family['context']['control_packages']['control_packages']), 7)
        self.assertEqual(self.family['default_route'], 'CUBE_HINGE_COMPARISON')

    def test_every_template_is_inspectable_and_quarantine_is_conditional(self):
        visible = {op for route in self.routes.values() for op in ids(route['nodes'])}
        self.assertEqual(visible, {op['id'] for op in self.family['operations']})
        for route in self.routes.values():
            if route['id'] == 'WHOLE_PAPER_PRACTICAL':
                continue
            with self.subTest(route=route['id']):
                self.assertNotIn('QUARANTINE', ids(route['nodes'][0]['children']))
                recovery = route['nodes'][1]
                self.assertEqual(recovery['type'], 'obligations')
                self.assertIn('Conditional recovery', recovery['label'])
                self.assertEqual(recovery['children'], ['QUARANTINE'])
                self.assertEqual(collections.Counter(ids(route['nodes'])),
                                 collections.Counter(route['detail']['operation_ids'] + ['QUARANTINE']))

    def test_cube_material_target_attempt_nesting(self):
        route = self.routes['CUBE_HINGE_COMPARISON']
        material = self.one_loop(route['nodes'], 'hinge_material')
        self.assertEqual(material['meta']['values'], ['mylar', 'elastomer_0p5mm'])
        targets = self.one_loop(material['children'], 'target_attempts')
        self.assertIn(targets, material['children'])
        self.assertEqual(targets['meta']['values'], ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii'])
        self.assert_repetition(targets, 'attempts_per_target', TARGET_BODY)
        self.assertEqual(ids(material['children']), TARGET_BODY + ['TARGET_SUMMARY'])
        self.assertNotIn('CUBE_SWITCH', ids(material['children']))
        switches = [node for node, _ in builder.walk(route['nodes'])
                    if node.get('meta', {}).get('between_conditions') == ['CUBE_SWITCH']
                    and node['type'] == 'obligations']
        self.assertEqual(len(switches), 1)
        self.assertEqual(switches[0]['children'], ['CUBE_SWITCH'])
        grid = route['detail']['loop_expansion']['condition_target_grid']
        self.assertIs(grid['cartesian_product_required'], True)
        self.assertEqual(grid['minimum_distinct_condition_target_cells'], 16)
        self.assertEqual(len(list(itertools.product(grid['conditions'], grid['targets']))), 16)
        self.assertIn('not samples', grid['counts_are'])

    def test_thickness_setup_slots_then_target_attempt_nesting(self):
        route = self.routes['ARRAY_THICKNESS_PAIR']
        thickness = self.one_loop(route['nodes'], 'array_thickness')
        self.assertEqual(thickness['meta']['values'], ['mylar_50um', 'mylar_125um'])
        slots = self.one_loop(thickness['children'], 'array_slots')
        self.assertIn(slots, thickness['children'])
        self.assertEqual(slots['meta']['values'], [list(x) for x in itertools.product(range(2), repeat=3)])
        self.assertEqual(slots['children'], ['ARRAY_PREP', 'ARRAY_JOIN'])
        targets = self.one_loop(thickness['children'], 'target_attempts')
        self.assertIn(targets, thickness['children'])
        self.assertLess(thickness['children'].index(slots), thickness['children'].index(targets))
        self.assertIsNone(targets['meta']['values'])
        self.assertEqual(targets['meta']['targets_from'], 'array_card.bulk_target_ids')
        self.assertIs(targets['meta']['null_target_list_blocks'], True)
        self.assert_repetition(targets, 'attempts_per_target', TARGET_BODY)
        self.assertEqual(ids(thickness['children']),
                         ['ARRAY_PREP', 'ARRAY_JOIN', 'SAMPLE_QC'] + TARGET_BODY +
                         ['TARGET_SUMMARY', 'ARRAY_CLASSIFY'])
        expansion = route['detail']['loop_expansion']
        self.assertEqual(expansion['unit_slots_per_outer'], 8)
        self.assertEqual(expansion['condition_target_grid']['targets_from'], 'array_card.bulk_target_ids')
        self.assertIs(expansion['condition_target_grid']['null_target_list_blocks'], True)
        self.assertIs(expansion['condition_target_grid']['cartesian_product_required'], True)
        self.assertNotIn('ARRAY_THICKNESS', ids(thickness['children']))

    def test_boundary_targets_remain_class_specific(self):
        route = self.routes['ARRAY_BOUNDARY_LONG']
        classes = self.one_loop(route['nodes'], 'target_class')
        self.assertEqual(classes['meta']['values'],
                         ['bulk_compatible', 'edge_or_corner', 'longer_than_one_cell'])
        targets = self.one_loop(classes['children'], 'target_attempts')
        self.assertIn(targets, classes['children'])
        self.assertIsNone(targets['meta']['values'])
        self.assertEqual(targets['meta']['targets_from'], 'array_card.targets_by_class')
        self.assertIs(targets['meta']['null_class_target_list_blocks'], True)
        self.assert_repetition(targets, 'attempts_per_target', TARGET_BODY)
        self.assertNotIn('condition_target_grid', route['detail']['loop_expansion'])

    def test_target_labels_and_repetition_counts_preserved(self):
        labels = {
            'TETRA_REACH_RELEASE': ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii',
                                    'ix', 'x', 'xi', 'xii', 'xiii', 'xiv', 'xv', 'xvi', 'xvii'],
            'SI6_TRUNCATED_CUBE': [str(i) for i in range(1, 12)],
            'SI6_RHOMBICUBOCTAHEDRON': [str(i) for i in range(1, 16)],
        }
        for branch_id, values in labels.items():
            with self.subTest(branch=branch_id):
                targets = self.one_loop(self.routes[branch_id]['nodes'], 'target_attempts')
                self.assertEqual(targets['meta']['values'], values)
                self.assert_repetition(targets, 'attempts_per_target', TARGET_BODY)

    def test_unknown_cardboard_joint_and_target_inputs_remain_null(self):
        for branch_id in ['CARD_TRUNCATED_TETRAHEDRON', 'CARD_TRUNCATED_CUBE', 'CARD_CUBOCTAHEDRON']:
            with self.subTest(branch=branch_id):
                route = self.routes[branch_id]
                joints = self.one_loop(route['nodes'], 'card_joints')
                targets = self.one_loop(route['nodes'], 'target_attempts')
                self.assertIsNone(joints['meta']['values'])
                self.assertEqual(joints['meta']['values_from'], 'geometry_card.joint_ids')
                self.assertEqual(joints['children'], ['CARD_ALIGN', 'CARD_JOIN'])
                self.assertIsNone(targets['meta']['values'])
                self.assert_repetition(targets, 'attempts_per_target', TARGET_BODY)

    def test_unknown_compression_count_is_not_inferred_from_last_five(self):
        route = self.routes['PLA_MYLAR_CYCLIC']
        faces = self.one_loop(route['nodes'], 'face_pairs')
        self.assertIsNone(faces['meta']['values'])
        cycles = self.one_loop(route['nodes'], 'cycles')
        self.assertIsNone(cycles['meta']['count'])
        self.assertEqual(cycles['meta']['count_from'], 'compression_card.total_cycles')
        self.assertEqual(cycles['meta']['minimum_for_summary'], 5)
        self.assertEqual(cycles['children'], ['COMP_LOAD', 'COMP_UNLOAD'])
        self.assertIn('invalid final', cycles['meta']['aggregation'])
        self.assertEqual(collections.Counter(ids(route['nodes']))['COMP_LOAD'], 1)

    def test_unknown_pneumatic_program_count_is_not_four(self):
        route = self.routes['PNEUMATIC_TWO_POUCH']
        programs = self.one_loop(route['nodes'], 'pneumatic_programs')
        self.assertIsNone(programs['meta']['values'])
        self.assertEqual(programs['meta']['values_from'], 'pneumatic_card.program_ids')
        self.assertEqual(len(programs['children']), 1)
        repeat = programs['children'][0]
        self.assertEqual(repeat['type'], 'loop')
        self.assertEqual(repeat['meta']['input'], 'attempts_per_program')
        self.assertIs(repeat['meta']['no_inferred_four_programs'], True)
        self.assertEqual(repeat['children'], ['PNEU_PROGRAM', 'PNEU_ACTUATE', 'PNEU_VENT'])
        self.assertNotIn('count', repeat['meta'])
        self.assertEqual(collections.Counter(ids(route['nodes']))['PNEU_PROGRAM'], 1)

    def test_campaign_dispatch_preserves_all_independent_branch_nodes(self):
        campaign = self.routes['WHOLE_PAPER_PRACTICAL']
        self.assertEqual(len(campaign['nodes']), 1)
        dispatch = campaign['nodes'][0]
        self.assertEqual(dispatch['type'], 'obligations')
        self.assertIs(dispatch['ordered'], False)
        expected_ids = campaign['detail']['loops'][0]['values']
        self.assertEqual(len(expected_ids), 11)
        self.assertEqual([node['meta']['branch_id'] for node in dispatch['children']], expected_ids)
        self.assertEqual(set(expected_ids), set(self.routes) - {'WHOLE_PAPER_PRACTICAL'})
        for node in dispatch['children']:
            with self.subTest(branch=node['meta']['branch_id']):
                self.assertIs(node['ordered'], False)
                self.assertEqual(node['type'], 'obligations')
                self.assertEqual(node['children'], self.routes[node['meta']['branch_id']]['nodes'])

    def test_no_group_claims_execution_order_or_expanded_cardinalities(self):
        for route in self.routes.values():
            for node, _ in builder.walk(route['nodes']):
                if node['type'] == 'op':
                    continue
                with self.subTest(route=route['id'], label=node['label']):
                    self.assertIs(node['ordered'], False)
                    if node['type'] == 'loop':
                        self.assertIs(node['symbolic'], True)

    def test_svg_has_no_adjacency_arrow_for_any_prismatic_route(self):
        texts = [(ROOT / 'diagrams' / 'prismatic.svg').read_text()]
        for route in self.routes.values():
            family = dict(self.family, default_route=route['id'])
            texts.append(builder.svg(family))
        for text in texts:
            self.assertNotIn('marker-end=', text)
            self.assertFalse(any('marker-end' in element.attrib for element in ET.fromstring(text).iter()))

    def test_eight_existing_families_have_unchanged_decoded_semantics(self):
        fixture = json.loads((ROOT / 'tests' / 'earlier_family_semantics.json').read_text())
        self.assertEqual(len(fixture['families']), 8)
        for key, expected in fixture['families'].items():
            with self.subTest(family=key):
                family = get(key)
                family.pop('shared', None)
                canonical = json.dumps(family, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
                canonical = canonical.replace(family['source_commit'], 'SOURCE_COMMIT')
                self.assertEqual(hashlib.sha256(canonical.encode()).hexdigest(), expected)

    def test_all_families_and_source_urls_use_verified_source_snapshot(self):
        commit = '293e32da790303c1a17131e036235f69a5f342e0'
        for key in builder.ADAPTERS:
            family = get(key)
            with self.subTest(family=key):
                expected_commit = builder.source_commit(key)
                self.assertEqual(family['source_commit'], expected_commit)
                self.assertEqual(family['source_folder'],
                                 'https://github.com/openags/ScienceGym/blob/' + expected_commit +
                                 '/tasks/' + builder.package_name(key) + '/')
                for filename, record in family['source_files'].items():
                    self.assertEqual(record['url'], family['source_folder'] + filename)

    def test_manifest_preserves_ten_family_totals(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text())
        self.assertEqual(manifest['commit'], '293e32da790303c1a17131e036235f69a5f342e0')
        self.assertEqual(len(manifest['families']), 24)
        earlier = [f for f in manifest['families'] if f['id'] not in ('wavefront', 'bianisotropic', 'edge', 'origami_memory', 'ring_origami', 'mechanical_backprop', 'granular_assembly', 'beaded', 'thermal_jamming', 'horn_acoustics', 'mechanical_logic', 'cold_shape', 'gear', 'hydrogel_optical')]
        self.assertEqual(len(earlier), 10)
        self.assertEqual(sum(family['routes'] for family in earlier), 202)
        self.assertEqual(sum(family['operations'] for family in earlier), 1376)
        for record in manifest['families']:
            with self.subTest(family=record['id']):
                family = get(record['id'])
                self.assertEqual(record['routes'], len(family['routes']))
                self.assertEqual(record['operations'], len(family['operations']))


@unittest.skipUnless(TASKS, 'SCIENCEGYM_TASKS not set; source comparison not run')
class PrismaticSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = TASKS / 'prismatic_operations_v2'
        cls.family = get('prismatic')
        cls.operations = cls.read('operations.json')
        cls.branches_document = cls.read('branches.json')
        cls.branches = {branch['id']: branch for branch in cls.branches_document['branches']}

    @classmethod
    def read(cls, name):
        return json.loads((cls.source / name).read_text())

    def test_all_operation_fields_and_source_pointers_are_exact(self):
        self.assertEqual([op['id'] for op in self.family['operations']],
                         [op['id'] for op in self.operations['operations']])
        fields = [('title', 'title'), ('location_id', 'stage'), ('actions', 'actions'),
                  ('preconditions', 'pre'), ('postconditions', 'post'), ('recovery', 'recovery'),
                  ('provenance', 'provenance'), ('unknown_parameter_ids', 'unknowns'),
                  ('evidence_ids', 'sources')]
        for index, (original, mapped) in enumerate(zip(self.operations['operations'], self.family['operations'])):
            with self.subTest(operation=original['id']):
                for source_field, target_field in fields:
                    self.assertEqual(mapped[target_field], original[source_field], source_field)
                for key in ['depends_on', 'kind', 'execution_mode', 'unknown_parameter_ids']:
                    self.assertEqual(mapped['detail'][key], original[key], key)
                self.assertEqual(mapped['source_file'], 'operations.json')
                self.assertEqual(mapped['source_pointer'], '/operations/' + str(index))

    def test_branch_details_preserve_complete_original_records(self):
        self.assertEqual([route['id'] for route in self.family['routes']], list(self.branches))
        for index, (original, mapped) in enumerate(zip(self.branches.values(), self.family['routes'])):
            with self.subTest(branch=original['id']):
                self.assertEqual(mapped['label'], original['title'])
                self.assertEqual(mapped['detail'], builder.without(original, {'id', 'title'}))
                self.assertEqual(mapped['source_file'], 'branches.json')
                self.assertEqual(mapped['source_pointer'], '/branches/' + str(index))

    def test_complete_dependency_graph_and_semantic_rules_are_exact(self):
        self.assertEqual(self.family['dependencies'], self.read('dependencies.json'))
        self.assertEqual(len(self.family['dependencies']['edges']), 46)
        self.assertEqual(len(self.family['dependencies']['branch_stage_dependencies']), 8)
        expected = { (dep, op['id']) for op in self.operations['operations'] for dep in op['depends_on'] }
        self.assertEqual({(edge['from'], edge['to']) for edge in self.family['dependencies']['edges']}, expected)

    def test_reference_context_files_are_lossless(self):
        context = self.family['context']
        aliases = {'unknowns': 'unknown_parameters', 'acceptance': 'evaluator_reference',
                   'lineage': 'lineage_contract'}
        names = ['control_packages', 'material_cards', 'asset_needs', 'source_conflicts', 'source_outcomes',
                 'agent_visible', 'RELEASE_BOUNDARY', 'episode_input_contract', 'station_contracts',
                 'mock_contract', 'coverage_matrix', 'nonmanual_scope', 'source_access_audit', 'provenance']
        for key, filename in list(aliases.items()) + [(name, name) for name in names]:
            with self.subTest(context=key):
                self.assertEqual(context[key], self.read(filename + '.json'))
        self.assertEqual(context['independent_source_audit'], self.read('independent_source_audit/audit.json'))
        self.assertEqual(context['branch_policy'], builder.without(self.branches_document, {'branches'}))
        self.assertEqual(context['operation_policy'], builder.without(self.operations, {'operations'}))

    def test_source_control_membership_and_conditions_are_exact(self):
        controls = self.family['context']['control_packages']['control_packages']
        self.assertEqual({item['id'] for item in controls},
                         {'C_COMPRESSION', 'C_RELEASE', 'C_HINGE', 'C_THICKNESS', 'C_FINITE', 'C_SI6', 'C_PNEU'})
        for source, mapped in zip(self.read('control_packages.json')['control_packages'], controls):
            self.assertEqual(source, mapped)
            self.assertNotIn('WHOLE_PAPER_PRACTICAL', mapped['branch_ids'])

    def test_route_controls_are_exact_branch_bindings_and_campaign_union(self):
        controls = self.read('control_packages.json')['control_packages']
        for route in self.family['routes']:
            with self.subTest(branch=route['id']):
                selected = {route['id']}
                if route['id'] == 'WHOLE_PAPER_PRACTICAL':
                    selected = set(self.branches[route['id']]['loops'][0]['values'])
                expected = [control for control in controls if set(control['branch_ids']) & selected]
                self.assertEqual(route['controls'], expected)
                if route['id'].startswith('CARD_'):
                    self.assertEqual(route['controls'], [])
                if route['id'] == 'WHOLE_PAPER_PRACTICAL':
                    self.assertEqual(route['controls'], controls)

    def test_adapter_rebuild_matches_all_emitted_nodes(self):
        adapted = builder.adapt_prismatic(self.source)
        for original, persisted in zip(adapted['routes'], self.family['routes']):
            self.assertEqual(original['nodes'], persisted['nodes'], original['id'])

    def test_unsupported_loop_expansion_type_fails_closed(self):
        branch = copy.deepcopy(self.branches['CUBE_HINGE_COMPARISON'])
        branch['loop_expansion']['type'] = 'invented_flat_product'
        with self.assertRaisesRegex(ValueError, 'Unknown prismatic loop expansion type'):
            builder.prismatic_nodes(branch, self.branches)

    def test_unknown_outer_loop_and_unused_loop_fail_closed(self):
        branch = copy.deepcopy(self.branches['CUBE_HINGE_COMPARISON'])
        branch['loops'][0]['loop_id'] = 'unknown_outer'
        branch['loop_expansion']['outer'] = 'unknown_outer'
        with self.assertRaisesRegex(ValueError, 'Unknown prismatic (outer loop|inner binding)'):
            builder.prismatic_nodes(branch, self.branches)
        branch = copy.deepcopy(self.branches['TETRA_REACH_RELEASE'])
        branch['loops'].append({'loop_id': 'unexpected_loop', 'body': ['PLAN']})
        with self.assertRaisesRegex(ValueError, 'Unmapped prismatic loops'):
            builder.prismatic_nodes(branch, self.branches)

    def test_unsupported_inner_binding_schema_fails_closed(self):
        for branch_id in ['TETRA_REACH_RELEASE', 'CUBE_HINGE_COMPARISON', 'ARRAY_THICKNESS_PAIR',
                          'ARRAY_BOUNDARY_LONG', 'PNEUMATIC_TWO_POUCH']:
            with self.subTest(branch=branch_id):
                branch = copy.deepcopy(self.branches[branch_id])
                branch['loop_expansion']['inner'] = ['invented_replicates']
                with self.assertRaisesRegex(ValueError, 'Unknown prismatic inner binding'):
                    builder.prismatic_nodes(branch, self.branches)

    def test_duplicate_loop_and_mismatched_body_fail_closed(self):
        branch = copy.deepcopy(self.branches['TETRA_REACH_RELEASE'])
        branch['loops'].append(copy.deepcopy(branch['loops'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate prismatic loop ID'):
            builder.prismatic_nodes(branch, self.branches)
        branch = copy.deepcopy(self.branches['TETRA_REACH_RELEASE'])
        branch['loops'][0]['body'][0] = 'NOT_A_DECLARED_TEMPLATE'
        with self.assertRaisesRegex(ValueError, 'one exact membership match'):
            builder.prismatic_nodes(branch, self.branches)

    def test_bad_dispatch_body_and_recursive_dispatch_fail_closed(self):
        branch = copy.deepcopy(self.branches['WHOLE_PAPER_PRACTICAL'])
        branch['loops'][0]['body'] = ['PLAN']
        with self.assertRaisesRegex(ValueError, 'Unknown dispatch body schema'):
            builder.prismatic_nodes(branch, self.branches)
        branch = copy.deepcopy(self.branches['WHOLE_PAPER_PRACTICAL'])
        branch['loops'][0]['values'] = ['WHOLE_PAPER_PRACTICAL']
        with self.assertRaisesRegex(ValueError, 'Recursive campaign dispatch'):
            builder.prismatic_nodes(branch, self.branches)


class PrismaticReplacementTests(unittest.TestCase):
    def test_empty_missing_and_ambiguous_bodies_fail_closed(self):
        replacement = {'type': 'loop', 'children': ['A']}
        for items, body in [(['A'], []), (['A'], ['B']), (['A', 'A'], ['A']),
                            (['A', 'C', 'B'], ['A', 'B'])]:
            with self.subTest(items=items, body=body):
                with self.assertRaisesRegex(ValueError, 'one exact membership match'):
                    builder.prismatic_replace(items, [(body, replacement)])

    def test_exact_body_replacement_preserves_unmatched_membership(self):
        replacement = {'type': 'loop', 'children': ['A', 'B']}
        self.assertEqual(builder.prismatic_replace(['P', 'A', 'B', 'Q'], [(['A', 'B'], replacement)]),
                         ['P', replacement, 'Q'])


if __name__ == '__main__':
    unittest.main()
