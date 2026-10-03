"""Independent EmVP source-fidelity tests; no execution or scientific fixtures.

Run from the repository root with:
    SCIENCEGYM_TASKS=tasks python -B viewer/task_explorer_v1/tests/test_emvp.py
"""
import collections
import copy
import hashlib
import json
import unittest
import xml.etree.ElementTree as ET

from test_semantics import ROOT, TASKS, builder, get, ids


CONTEXT_FILES = {
    'unknowns': 'unknown_parameters.json',
    'acceptance': 'evaluator_reference.json',
    'lineage': 'lineage_contract.json',
    **{name: name + '.json' for name in [
        'control_packages', 'material_cards', 'asset_needs', 'source_conflicts',
        'source_outcomes', 'agent_visible', 'RELEASE_BOUNDARY',
        'episode_input_contract', 'station_contracts', 'mock_contract',
        'coverage_matrix', 'nonmanual_scope', 'source_access_audit',
        'provenance', 'STATUS',
    ]},
    'independent_source_audit': 'independent_source_audit/audit.json',
}


def records(items):
    return {item['id']: item for item in items}


class EmvpBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.family = get('emvp')
        cls.routes = records(cls.family['routes'])
        cls.operations = records(cls.family['operations'])
        cls.controls = records(cls.family['context']['control_packages']['packages'])

    def test_exact_public_counts_and_no_added_whole_paper_route(self):
        self.assertEqual(len(self.family['routes']), 19)
        self.assertEqual(len(self.routes), 19)
        self.assertEqual(len(self.family['operations']), 53)
        self.assertEqual(len(self.operations), 53)
        self.assertEqual(len(self.family['context']['branch_policy']['practical_families']), 5)
        self.assertEqual(len(self.controls), 15)
        self.assertEqual(len(self.family['context']['unknowns']['unknowns']), 30)
        self.assertEqual(len(self.family['evidence']), 30)
        self.assertEqual(self.family['default_route'], 'POSITIVE_HELIX')
        self.assertNotIn('WHOLE_PAPER_PRACTICAL', self.routes)

    def test_every_definition_is_inspectable_without_added_occurrences(self):
        visible = {identifier for route in self.routes.values() for identifier in ids(route['nodes'])}
        self.assertEqual(visible, set(self.operations))
        for route in self.routes.values():
            source = route['detail']
            expected = ([identifier for condition in source['condition_routes']
                         for identifier in condition['operation_ids']]
                        if 'condition_routes' in source else source['operation_ids'])
            with self.subTest(configuration=route['id']):
                self.assertEqual(ids(route['nodes']), expected)
                self.assertEqual(set(expected), set(source['operation_ids']))
                for node in route['nodes'][1:]:
                    self.assertEqual(ids([node]), [], 'Comparison coverage must not duplicate operation bodies')

    def test_all_membership_groups_are_unordered_and_loops_are_symbolic(self):
        for route in self.routes.values():
            for node, _ in builder.walk(route['nodes']):
                if 'children' in node:
                    with self.subTest(configuration=route['id'], label=node['label']):
                        self.assertIs(node['ordered'], False)
                        if node['type'] == 'loop':
                            self.assertIs(node['symbolic'], True)
                            self.assertEqual(ids([node]), [])

    def test_every_svg_view_has_no_adjacency_arrows(self):
        views = [(ROOT / 'diagrams' / 'emvp.svg').read_text()]
        views += [builder.svg(dict(self.family, default_route=route['id']))
                  for route in self.routes.values()]
        self.assertEqual(len(views), 20)
        for index, text in enumerate(views):
            with self.subTest(view=index):
                self.assertNotIn('marker-end=', text)
                self.assertFalse(any('marker-end' in element.attrib
                                     for element in ET.fromstring(text).iter()))
                self.assertIn('No chronological adjacency edges are inferred', text)
                self.assertIn('19 configurations', text)

    def test_declared_dependencies_are_not_replaced_by_display_adjacency(self):
        dependency = self.family['dependencies']
        self.assertEqual(len(dependency['edges']), 44)
        self.assertEqual(len(dependency['conditional_edges']), 6)
        self.assertEqual(sum(len(group['edges']) for group in dependency['conditional_edges']), 25)
        membership = self.routes['POSITIVE_HELIX']['detail']['operation_ids']
        for target in ['O_EMB_SETUP', 'O_VAM_SETUP']:
            self.assertGreater(membership.index('O_GEOMETRY'), membership.index(target))
            self.assertIn(['O_GEOMETRY', target], dependency['edges'])
        for field in ['instantiation', 'per_occurrence_rules', 'forbidden_inference']:
            self.assertTrue(dependency[field])
        self.assertIn('both endpoint templates', dependency['instantiation'])
        self.assertIn('Any lawful order', '\n'.join(dependency['per_occurrence_rules']))

    def test_cage_dispatch_keeps_exact_three_separate_conditions(self):
        cage = self.routes['CONTROL_SINGLE_MATERIAL_CAGE']
        dispatch = cage['nodes'][0]
        source_conditions = cage['detail']['condition_routes']
        self.assertEqual(len(source_conditions), 3)
        self.assertEqual(len(dispatch['children']), 3)
        self.assertEqual([node['meta']['condition_id'] for node in dispatch['children']],
                         ['Mat1-only', 'Mat2-only', 'combined-material'])
        for source, node in zip(source_conditions, dispatch['children']):
            with self.subTest(condition=source['condition_id']):
                self.assertEqual(node['children'], source['operation_ids'])
                for key in ['condition_id', 'material_ids', 'required_unknowns']:
                    self.assertEqual(node['meta'][key], source[key])
                self.assertIs(node['ordered'], False)
                selected = set(node['children'])
                if source['condition_id'] == 'combined-material':
                    self.assertIn('O_DEPOSIT_POS', selected)
                    self.assertNotIn('O_VAM_DIRECT', selected)
                    self.assertEqual(source['material_ids'], ['MAT1', 'MAT2'])
                else:
                    self.assertIn('O_VAM_DIRECT', selected)
                    self.assertFalse({'O_DEPOSIT_POS', 'O_DOCK_EMB', 'O_TRANSFER_ALIGN'} & selected)
                    self.assertNotIn('U_TOOLPATH', source['required_unknowns'])
                    self.assertEqual(source['material_ids'],
                                     ['MAT1' if source['condition_id'] == 'Mat1-only' else 'MAT2'])
                    if source['condition_id'] == 'Mat2-only':
                        self.assertNotIn('U_CQ_EDAB', source['required_unknowns'])
        self.assertEqual(len(ids(cage['nodes'])), 62)
        self.assertEqual(len(set(ids(cage['nodes']))), 25)
        self.assertEqual(collections.Counter(ids(cage['nodes']))['O_PLAN'], 3)

    def test_comparison_metadata_is_lossless_without_binding_operation_bodies(self):
        seen = set()
        for route in self.routes.values():
            self.assertEqual([control['id'] for control in route['controls']],
                             route['detail']['control_package_ids'])
            for control, node in zip(route['controls'], route['nodes'][1:]):
                seen.add(control['id'])
                with self.subTest(configuration=route['id'], package=control['id']):
                    self.assertEqual(control, self.controls[control['id']])
                    self.assertEqual(node['meta']['control_package'], control)
                    outer = node['children'][0]
                    inner = outer['children'][0]
                    self.assertEqual(outer['meta']['outer_loop'], control['outer_loop'])
                    self.assertEqual(outer['meta']['replication'], control['replication'])
                    if 'condition_axes' in control:
                        self.assertEqual(outer['meta']['condition_axes'], control['condition_axes'])
                    else:
                        self.assertNotIn('condition_axes', outer['meta'])
                    self.assertEqual(inner['meta'], {key: control[key] for key in [
                        'inner_loop', 'ordered_states', 'within_specimen_sites',
                        'required_outputs', 'loop_semantics'] if key in control})
                    self.assertEqual(ids([outer]), [])
        self.assertEqual(seen, set(self.controls))

    def test_unknown_gates_and_independent_sample_counts_remain_null(self):
        unknowns = records(self.family['context']['unknowns']['unknowns'])
        self.assertEqual(len(unknowns), 30)
        for unknown in unknowns.values():
            self.assertIsNone(unknown['value'], unknown['id'])
            self.assertTrue(unknown['if_missing'])
        for control in self.controls.values():
            self.assertIsNone(control['replication']['independent_specimens_per_condition'])
            self.assertEqual(control['replication']['gate'], 'U_SCHEDULE')
            for axis in control.get('condition_axes', []):
                if axis['values'] is None:
                    self.assertIn(axis['gate'], unknowns)
                else:
                    self.assertTrue(axis['values'])
        self.assertIn('not four specimens', unknowns['U_SCHEDULE']['source_status'])
        self.assertIn('Missing sample counts never mean zero iterations',
                      self.family['context']['control_packages']['coverage_rule'])

    def test_physical_states_and_sites_are_not_independent_specimens(self):
        self.assertEqual(self.controls['C_SPHERE_STATES']['ordered_states'],
                         ['unloaded', '3 g bar applied', 'bar removed'])
        self.assertEqual(self.controls['C_BELLOW_STATES']['ordered_states'],
                         ['baseline', 'qualified negative-pressure program', 'released'])
        sites = self.controls['C_HARDNESS']['within_specimen_sites']
        self.assertEqual(sites['count'], 4)
        self.assertIsNone(sites['independent_specimen_count'])
        self.assertIn('Sample n reported separately from site count',
                      self.controls['C_HARDNESS']['required_outputs'])
        for identifier in ['C_SPHERE_STATES', 'C_BELLOW_STATES', 'C_LATTICE_REGIONS', 'C_HARDNESS']:
            self.assertIn('same specimen, not independent sample loops',
                          self.controls[identifier]['loop_semantics'])
        self.assertIn('Repeated states, images, analysis regions and hardness sites are not independent specimens',
                      self.family['context']['control_packages']['coverage_rule'])

    def test_missing_postconditions_and_object_roles_are_explicit(self):
        for operation in self.operations.values():
            with self.subTest(operation=operation['id']):
                self.assertEqual(operation['post'], [
                    'No postconditions field supplied; completion evidence is shown separately and is not a state-transition receipt'])
                self.assertEqual(operation['objects'], [
                    'No per-operation object-role list supplied; inspect material, station and lineage contracts'])
                self.assertNotEqual(operation['post'], operation['acceptance'])
                self.assertIsNone(operation['loop'])
        self.assertEqual({operation['detail']['kind'] for operation in self.operations.values()},
                         {'researcher_operation', 'qualified_analysis_handoff'})

    def test_no_invented_workflow_or_specimen_route(self):
        self.assertNotIn('O_EXPOSE', ids(self.routes['CONTROL_EMB_FILAMENT']['nodes']))
        direct = set(ids(self.routes['CONTROL_VAM_NEGATIVE']['nodes']))
        self.assertFalse({'O_DEPOSIT_NEG', 'O_FLUSH', 'O_CT_SCAN'} & direct)
        hardness = set(ids(self.routes['SHORE_D_PAIR']['nodes']))
        tensile = set(ids(self.routes['CAST_TENSILE_PAIR']['nodes']))
        self.assertIn('O_VAM_DIRECT', hardness)
        self.assertNotIn('O_CAST', hardness)
        self.assertIn('O_CAST', tensile)
        self.assertFalse({'O_EXPOSE', 'O_SHORE_PROBE'} & tensile)

    def test_context_retains_reference_only_boundaries_and_unresolved_conflicts(self):
        context = self.family['context']
        self.assertEqual(context['source_outcomes']['visibility'],
                         'evaluator_context_only_never_actor_or_reward')
        self.assertEqual(context['acceptance']['visibility'], 'evaluator_only_at_runtime')
        self.assertEqual(context['mock_contract']['scope'], 'Static bookkeeping tests only')
        self.assertIn('Not supplied', context['episode_input_contract']['scientific_backend'])
        self.assertIs(context['provenance']['source_bytes_in_export'], False)
        self.assertIs(context['asset_needs']['publisher_assets_in_export'], False)
        self.assertTrue({'CF_INITIATORS', 'CF_SOLVENT', 'CF_CHIP_TIMINGS', 'CF_PHOTO_CLOCK',
                         'CF_DISTANCE', 'CF_CONTROL_MATERIAL'} <= set(records(context['source_conflicts']['conflicts'])))
        timing = context['source_outcomes']['timing_rows']
        self.assertEqual(len(timing), 10)
        for row in timing[-2:]:
            self.assertEqual(row['physical_chip_assignment'], 'unresolved_source_row_panel_conflict')
        self.assertIn('four hardness sites belong to one sample',
                      json.dumps(context['lineage']).lower())

    def test_malformed_dispatch_is_rejected_without_mutating_input(self):
        original = self.routes['CONTROL_SINGLE_MATERIAL_CAGE']['detail']
        cases = {
            'empty dispatch': lambda value: value.update(condition_routes=[]),
            'duplicate condition': lambda value: value['condition_routes'].append(copy.deepcopy(value['condition_routes'][0])),
            'omitted union member': lambda value: value['operation_ids'].remove('O_DEPOSIT_POS'),
            'invented union member': lambda value: value['condition_routes'][0]['operation_ids'].append('O_NOT_A_TEMPLATE'),
            'empty condition body': lambda value: value['condition_routes'][0].update(operation_ids=[]),
            'duplicate condition operation': lambda value: value['condition_routes'][0]['operation_ids'].append('O_PLAN'),
        }
        for label, mutate in cases.items():
            with self.subTest(case=label):
                changed = copy.deepcopy(original)
                mutate(changed)
                before = copy.deepcopy(changed)
                with self.assertRaises(ValueError):
                    builder.emvp_nodes(changed, [])
                self.assertEqual(changed, before)

    def test_repeated_build_and_svg_do_not_mutate_decoded_source_semantics(self):
        before = copy.deepcopy(self.family)
        for route in self.routes.values():
            configuration = dict(route['detail'], id=route['id'], goal=route['label'])
            self.assertEqual(builder.emvp_nodes(configuration, route['controls']), route['nodes'])
            builder.svg(dict(self.family, default_route=route['id']))
        self.assertEqual(self.family, before)


@unittest.skipUnless(TASKS, 'SCIENCEGYM_TASKS not set; source comparison not run')
class EmvpSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = TASKS / 'emvp_operations_v2'
        cls.documents = {path.relative_to(cls.package).as_posix(): json.loads(path.read_text())
                         for path in cls.package.rglob('*.json')}
        cls.family = get('emvp')

    def test_every_operation_field_is_exactly_preserved(self):
        source_operations = self.documents['operations.json']['operations']
        self.assertEqual([operation['id'] for operation in self.family['operations']],
                         [operation['id'] for operation in source_operations])
        for index, (source, operation) in enumerate(zip(source_operations, self.family['operations'])):
            with self.subTest(operation=source['id']):
                for source_key, viewer_key in [
                    ('id', 'id'), ('label', 'title'), ('station', 'stage'),
                    ('preconditions', 'pre'), ('completion_evidence', 'acceptance'),
                    ('required_unknowns', 'unknowns'), ('source_refs', 'sources'),
                    ('provenance', 'provenance'), ('recovery', 'recovery'),
                ]:
                    self.assertEqual(operation[viewer_key], source[source_key])
                self.assertEqual(operation['actions'], [source['physical_action']])
                self.assertEqual(operation['detail']['kind'], source['kind'])
                self.assertEqual(operation['source_file'], 'operations.json')
                self.assertEqual(operation['source_pointer'], '/operations/' + str(index))
                self.assertNotIn('postconditions', source)
                self.assertNotIn('target_asset_roles', source)

    def test_every_configuration_field_and_membership_is_exactly_preserved(self):
        configurations = self.documents['branches.json']['configurations']
        self.assertEqual([route['id'] for route in self.family['routes']],
                         [source['id'] for source in configurations])
        controls = records(self.documents['control_packages.json']['packages'])
        for index, (source, route) in enumerate(zip(configurations, self.family['routes'])):
            with self.subTest(configuration=source['id']):
                self.assertEqual(route['label'], source['goal'])
                self.assertEqual(route['detail'], {key: value for key, value in source.items()
                                                  if key not in {'id', 'goal'}})
                self.assertEqual(route['source_file'], 'branches.json')
                self.assertEqual(route['source_pointer'], '/configurations/' + str(index))
                self.assertEqual(route['controls'], [controls[key] for key in source['control_package_ids']])
                expected = ([identifier for condition in source['condition_routes']
                             for identifier in condition['operation_ids']]
                            if 'condition_routes' in source else source['operation_ids'])
                self.assertEqual(ids(route['nodes']), expected)

    def test_context_and_dependencies_are_lossless_copies(self):
        expected = {name: self.documents[filename] for name, filename in CONTEXT_FILES.items()}
        expected['branch_policy'] = {key: value for key, value in self.documents['branches.json'].items()
                                     if key != 'configurations'}
        expected['operation_policy'] = {key: value for key, value in self.documents['operations.json'].items()
                                        if key != 'operations'}
        self.assertEqual(self.family['context'], expected)
        self.assertEqual(self.family['dependencies'], self.documents['dependencies.json'])

    def test_evidence_resolves_every_locator_to_exact_source_document(self):
        provenance = self.documents['provenance.json']
        documents = records(provenance['sources'])
        expected = {locator['id']: dict(locator, source_document=documents[locator['source']],
                                        url=documents[locator['source']]['url'])
                    for locator in provenance['locators']}
        self.assertEqual(self.family['evidence'], expected)
        self.assertEqual(self.family['title'], provenance['title'])
        self.assertEqual(self.family['doi'], provenance['doi'])
        for operation in self.family['operations']:
            self.assertTrue(set(operation['sources']) <= set(expected))
        for route in self.family['routes']:
            self.assertTrue(set(route['detail']['source_refs']) <= set(expected))

    def test_source_inventory_hashes_and_json_pointers_match_actual_bytes(self):
        self.assertEqual(set(self.family['source_files']), set(self.documents))
        for filename, source in self.family['source_files'].items():
            with self.subTest(file=filename):
                self.assertEqual(source['sha256'], hashlib.sha256((self.package / filename).read_bytes()).hexdigest())
                self.assertEqual(source['url'], self.family['source_folder'] + filename)
        for record in self.family['operations'] + self.family['routes']:
            target = self.documents[record['source_file']]
            for part in record['source_pointer'].strip('/').split('/'):
                target = target[int(part)] if isinstance(target, list) else target[part]
            self.assertEqual(target['id'], record['id'])

    def test_source_package_is_unchanged_from_its_export_allowlist(self):
        manifest = self.documents['EXPORT_ALLOWLIST.json']
        for entry in manifest['files']:
            with self.subTest(file=entry['path']):
                payload = (self.package / entry['path']).read_bytes()
                self.assertEqual(len(payload), entry['bytes'])
                self.assertEqual(hashlib.sha256(payload).hexdigest(), entry['sha256'])

    def test_rebuild_and_pooling_preserve_generated_semantics_without_source_mutation(self):
        before = {path.relative_to(self.package).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in self.package.rglob('*') if path.is_file() and '__pycache__' not in path.parts}
        rebuilt = builder.adapt_emvp(self.package)
        generated = copy.deepcopy(self.family)
        generated.pop('shared', None)
        self.assertEqual(rebuilt, generated)
        from test_semantics import decode
        pooled = builder.unique_shared(copy.deepcopy(rebuilt))
        unpacked = decode(pooled, pooled)
        unpacked.pop('shared', None)
        self.assertEqual(unpacked, rebuilt)
        after = {path.relative_to(self.package).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in self.package.rglob('*') if path.is_file() and '__pycache__' not in path.parts}
        self.assertEqual(after, before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
