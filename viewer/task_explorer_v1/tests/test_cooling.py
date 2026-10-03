"""Independent directional-cooling adapter regression tests, without execution.

Run from the repository root with:
    SCIENCEGYM_TASKS=tasks python -B viewer/task_explorer_v1/tests/test_cooling.py
"""
import collections
import copy
import hashlib
import json
import unittest
import xml.etree.ElementTree as ET

from test_semantics import ROOT, TASKS, builder, decode, get, ids


CONTEXT_FILES = {
    'unknowns': 'unknown_parameters.json',
    'acceptance': 'evaluator_reference.json',
    'lineage': 'lineage_contract.json',
    **{name: name + '.json' for name in [
        'control_packages', 'material_cards', 'asset_needs', 'source_conflicts',
        'source_outcomes', 'agent_visible', 'RELEASE_BOUNDARY',
        'episode_input_contract', 'station_contracts', 'mock_contract',
        'coverage_matrix', 'nonmanual_scope', 'source_access_audit',
        'provenance', 'STATUS', 'VERIFICATION',
    ]},
    'independent_review': 'independent_review/audit.json',
}
OPERATION_FIELDS = {
    'id': 'id', 'title': 'title', 'location_id': 'stage',
    'operator_actions': 'actions', 'manipulated_objects': 'objects',
    'preconditions': 'pre', 'postconditions': 'post',
    'completion_evidence': 'acceptance', 'recovery': 'recovery',
    'unknown_parameter_ids': 'unknowns', 'provenance': 'provenance',
    'evidence_ids': 'sources',
}
MAP_ROUTES = {'MAP_CLEAR_DAY', 'MAP_CLEAR_NIGHT', 'MAP_HAZY_NOON'}
EXPECTED_LOOPS = {
    'BUILD_PAIR': {'L_REPEAT'},
    'CALIBRATE': {'L_REPEAT'},
    'OPT_HEMISPHERICAL': {'L_OPT', 'L_REPEAT'},
    'OPT_ANGULAR': {'L_ANGLE', 'L_REPEAT'},
    'ENVIRONMENT': {'L_REPEAT'},
    'TRACKED_STAGNATION': {'L_TRACK', 'L_REPEAT'},
    'PID_POWER': {'L_TRACK', 'L_PID', 'L_REPEAT'},
    'FIXED_LDPE': {'L_REPEAT'},
    'MAP_CLEAR_DAY': {'L_TRACK', 'L_MAP', 'L_REPEAT'},
    'MAP_CLEAR_NIGHT': {'L_MAP', 'L_REPEAT'},
    'MAP_HAZY_NOON': {'L_TRACK', 'L_MAP', 'L_REPEAT'},
}


def records(items):
    return {item['id']: item for item in items}


def loops(route):
    return [node for node, _ in builder.walk(route['nodes']) if node['type'] == 'loop']


class CoolingBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.family = get('cooling')
        cls.routes = records(cls.family['routes'])
        cls.operations = records(cls.family['operations'])
        cls.controls = records(cls.family['context']['control_packages']['control_packages'])

    def test_exact_source_scope_without_synthetic_whole_paper_route(self):
        self.assertEqual(self.family['id'], 'cooling')
        self.assertEqual(self.family['default_route'], 'TRACKED_STAGNATION')
        self.assertEqual(len(self.family['operations']), 56)
        self.assertEqual(len(self.operations), 56)
        self.assertEqual(len(self.family['routes']), 11)
        self.assertEqual(set(self.routes), set(EXPECTED_LOOPS))
        self.assertEqual(len(self.family['dependencies']['loops']), 6)
        self.assertEqual(len(self.controls), 10)
        self.assertEqual(len(self.family['evidence']), 15)
        self.assertNotIn('WHOLE_PAPER_PRACTICAL', self.routes)
        self.assertTrue(self.family['source_folder'].endswith('/directional_cooling_operations_v2/'))

    def test_every_template_visible_once_per_declared_route_membership(self):
        visible = {identifier for route in self.routes.values() for identifier in ids(route['nodes'])}
        self.assertEqual(visible, set(self.operations))
        for route in self.routes.values():
            with self.subTest(route=route['id']):
                membership = route['detail']['operation_ids']
                self.assertEqual(len(membership), len(set(membership)))
                self.assertEqual(ids(route['nodes']), membership)
                self.assertEqual(collections.Counter(ids(route['nodes'])), collections.Counter(membership))
                group = route['nodes'][0]
                self.assertEqual(group['type'], 'obligations')
                self.assertIs(group['ordered'], False)
                self.assertEqual(group['children'], membership)
                for node in route['nodes'][1:]:
                    self.assertEqual(ids([node]), [], 'Symbolic coverage must not add operation occurrences')

    def test_loop_metadata_is_exact_symbolic_and_never_an_operation_body(self):
        declared = records(self.family['dependencies']['loops'])
        for route in self.routes.values():
            actual = loops(route)
            with self.subTest(route=route['id']):
                self.assertEqual(len(actual), len(EXPECTED_LOOPS[route['id']]))
                self.assertEqual({node['meta']['loop']['id'] for node in actual}, EXPECTED_LOOPS[route['id']])
                for node in actual:
                    source_loop = declared[node['meta']['loop']['id']]
                    self.assertEqual(node['meta']['loop'], source_loop)
                    self.assertIs(node['symbolic'], True)
                    self.assertIs(node['ordered'], False)
                    self.assertEqual(ids([node]), [])
                    self.assertFalse(any(child['type'] == 'loop'
                                         for child, depth in builder.walk(node.get('children', []))))
                    self.assertIsInstance(source_loop['count'], str)
                    self.assertNotIn('count', node, 'No invented numeric loop expansion')

    def test_map_conditions_and_global_allocation_are_not_nested_new_runs(self):
        for route in self.routes.values():
            declared = {node['meta']['loop']['id']: node for node in loops(route)}
            with self.subTest(route=route['id']):
                repeat = declared['L_REPEAT']
                self.assertEqual(repeat['meta']['loop']['body'], ['PLAN', 'COMPARE'])
                self.assertIn('samples/sessions distinct', repeat['meta']['loop']['count'])
                self.assertEqual(ids([repeat]), [])
                if route['id'] in MAP_ROUTES:
                    map_loop = declared['L_MAP']
                    self.assertIn('three source conditions as separate branches', map_loop['meta']['loop']['count'])
                    self.assertEqual(ids([map_loop]), [])
                    self.assertEqual(collections.Counter(ids(route['nodes']))['MAP_LOG'], 1)

    def test_all_groups_are_unordered_and_every_svg_has_no_adjacency_arrows(self):
        views = [(ROOT / 'diagrams' / 'cooling.svg').read_text()]
        for route in self.routes.values():
            for node, _ in builder.walk(route['nodes']):
                if 'children' in node:
                    self.assertIs(node['ordered'], False, (route['id'], node['label']))
            views.append(builder.svg(dict(self.family, default_route=route['id'])))
        for index, text in enumerate(views):
            with self.subTest(view=index):
                self.assertNotIn('marker-end=', text)
                self.assertFalse(any('marker-end' in element.attrib for element in ET.fromstring(text).iter()))

    def test_all_fourteen_unknowns_remain_null_blocking_inputs(self):
        unknowns = records(self.family['context']['unknowns']['unknowns'])
        self.assertEqual(set(unknowns), {'U_SCENE', 'U_GEOM', 'U_FAB', 'U_ALLOC', 'U_CAL',
                                      'U_OPT', 'U_WIRING', 'U_ACQ', 'U_OUTDOOR', 'U_PID',
                                      'U_ANALYSIS', 'U_MAP', 'U_CLEAN', 'U_RAW'})
        for unknown in unknowns.values():
            self.assertIsNone(unknown['default'], unknown['id'])
            self.assertIn('block affected operations', unknown['execution_gate'])
        self.assertIn('Null is unknown, never zero', self.family['context']['unknowns']['unknown_rule'])
        for operation in self.operations.values():
            self.assertTrue(set(operation['unknowns']) <= set(unknowns), operation['id'])
        for route in self.routes.values():
            self.assertTrue(set(route['detail']['unknown_parameter_ids']) <= set(unknowns), route['id'])
        for card in self.family['context']['episode_input_contract']['cards']:
            self.assertIsNone(card['defaults'], card['id'])

    def test_control_bindings_are_exact_and_do_not_resolve_sample_counts(self):
        for route in self.routes.values():
            with self.subTest(route=route['id']):
                self.assertEqual(route['controls'], [self.controls[key] for key in route['detail']['control_ids']])
        repetition = self.family['context']['control_packages']['repetition_policy']
        for field in ['independent_specimens', 'independent_sessions', 'technical_repeats']:
            self.assertIsNone(repetition[field])
        self.assertEqual(repetition['required_input'], 'allocation_card')
        self.assertEqual(repetition['forbidden_equivalences'], [
            'two colors = n2 each', 'seven sensors = seven specimens',
            'timepoints = independent replicates', 'heater targets = independent experiments'])
        for route_id in ['BUILD_PAIR', 'TRACKED_STAGNATION', 'PID_POWER', 'FIXED_LDPE']:
            allocation = self.routes[route_id]['detail']['device_allocation']
            self.assertEqual(allocation['count'], 2)
            self.assertEqual(allocation['conditions'], ['white', 'black'])
            self.assertIn('independent repeat count remains episode input', allocation['meaning'])
        for route_id in MAP_ROUTES:
            self.assertEqual(self.routes[route_id]['detail']['device_allocation'],
                             {'count': 1, 'conditions': ['white'], 'source': 'E_MAP'})

    def test_conditional_night_and_fixed_routes_have_no_tracking_invention(self):
        night = self.routes['MAP_CLEAR_NIGHT']
        self.assertNotIn('TRACK_ADJUST', ids(night['nodes']))
        self.assertNotIn('L_TRACK', {node['meta']['loop']['id'] for node in loops(night)})
        self.assertIn('no sun-tracking action is required at night', night['detail']['notes'])
        fixed = self.routes['FIXED_LDPE']
        self.assertIn('BAND_CHECK', ids(fixed['nodes']))
        self.assertNotIn('TRACK_ADJUST', ids(fixed['nodes']))
        self.assertIn('FIXED_QC', ids(fixed['nodes']))
        self.assertIn('two component changes', self.controls['C_FIXED']['qualification'])
        for route_id in MAP_ROUTES - {'MAP_CLEAR_NIGHT'}:
            self.assertIn('TRACK_ADJUST', ids(self.routes[route_id]['nodes']))
        gates = self.family['dependencies']['conditional_gates']
        self.assertEqual(len(gates), 8)
        map_gate = next(gate for gate in gates if gate['operation'] == 'MAP_LOG')
        self.assertIn('daytime shading or verified night', map_gate['requires'])
        fixed_gate = next(gate for gate in gates if gate['operation'] == 'FIXED_QC')
        self.assertIn('old ASSEMBLY_QC cannot satisfy', fixed_gate['requires'])

    def test_declared_dependencies_retain_receipts_and_scoped_handoffs(self):
        dependencies = self.family['dependencies']
        self.assertEqual(len(dependencies['edges']), 62)
        edges = {(edge['from'], edge['to']) for edge in dependencies['edges']}
        expected = {(predecessor, operation['id']) for operation in self.operations.values()
                    for predecessor in operation['detail']['depends_on']}
        self.assertEqual(edges, expected)
        self.assertIn('not required immediate adjacency', dependencies['semantics'])
        self.assertIn('explicit scoped handoff', dependencies['semantics'])
        self.assertIn(('ASSEMBLY_QC', 'FIXED_SWAP'), edges)
        self.assertNotIn('ASSEMBLY_QC', ids(self.routes['FIXED_LDPE']['nodes']))
        self.assertIn(('CAL_UNLOAD', 'MAP_ATTACH'), edges)
        self.assertNotIn('CAL_UNLOAD', ids(self.routes['MAP_CLEAR_DAY']['nodes']))
        for route in self.routes.values():
            self.assertIn('named documented outside-scope handoff', route['detail']['preparation_policy'])

    def test_transport_templates_are_not_autoexpanded_or_counted_as_receipts(self):
        move = self.operations['MOVE']
        self.assertEqual(move['detail']['source_station_id'], 'runtime_origin_station')
        self.assertEqual(move['detail']['target_station_id'], 'runtime_destination_station')
        self.assertIn('physical MOVE instance', self.family['dependencies']['transport_rule'])
        for route in self.routes.values():
            self.assertEqual(collections.Counter(ids(route['nodes']))['MOVE'], 1, route['id'])
        for operation_id in ['OPT_REFERENCE', 'OPT_MOUNT', 'OPT_SCAN', 'OPT_UNLOAD']:
            operation = self.operations[operation_id]
            self.assertEqual(operation['stage'], 'WS_OPTICAL_ACTIVE')
            self.assertEqual(operation['detail']['station_options'], ['WS_UVVIS', 'WS_FTIR'])
            self.assertIn('MOVE required before changing stations', operation['detail']['station_binding'])
        for operation_id in ['STOP_SAFE', 'UNMOUNT']:
            self.assertEqual(self.operations[operation_id]['stage'], 'WS_ACTIVE')
            self.assertEqual(self.operations[operation_id]['detail']['source_station_id'], 'runtime_active_station')

    def test_source_timing_constants_do_not_create_counts_or_extended_sessions(self):
        constants = self.family['context']['episode_input_contract']['source_temporal_constants']
        self.assertEqual(constants['map_run_s'], 3600)
        self.assertEqual(constants['PID_step_s'], 300)
        self.assertEqual(constants['PID_summary_final_s'], 120)
        self.assertEqual(constants['weather_sample_period_s'], 300)
        self.assertIn('baseline timing within it is not specified', constants['scope_notes']['map_run_s'])
        self.assertIn('not automatically every branch', constants['scope_notes']['stagnation_lid_initial_s'])
        self.assertIn('not determine other sampling rates', self.controls['C_ENV']['qualification'])
        self.assertIn('rather than automatically adding another hour', '\n'.join(self.operations['MAP_LOG']['actions']))
        self.assertIn('within its one-hour total session', '\n'.join(self.operations['LID_BASELINE']['actions']))
        pid = next(loop for loop in self.family['dependencies']['loops'] if loop['id'] == 'L_PID')
        self.assertIsInstance(pid['count'], str)
        self.assertIn('nonempty bounded target schedule', pid['count'])

    def test_operation_actions_and_device_process_remain_separate_design_contracts(self):
        for operation in self.operations.values():
            with self.subTest(operation=operation['id']):
                self.assertTrue(operation['actions'])
                self.assertTrue(operation['objects'])
                self.assertTrue(operation['detail']['tools_or_interfaces'])
                self.assertTrue(operation['detail']['device_process'])
                self.assertEqual(operation['detail']['actor'], 'mobile_human_like_robot_operator')
                self.assertEqual(operation['detail']['execution_mode'], 'design_only')
                self.assertEqual(operation['provenance']['fine_actions'], 'task_authored_not_source_robot_trajectory')
                self.assertIsNone(operation['loop'])
                self.assertNotEqual(operation['acceptance'], operation['post'])

    def test_reference_only_boundaries_and_outcome_provenance_are_retained(self):
        context = self.family['context']
        self.assertEqual(context['operation_policy']['visibility'], 'evaluator_reference_only')
        self.assertEqual(context['acceptance']['visibility'], 'evaluator_reference_only')
        self.assertIs(context['source_outcomes']['not_actor_rewards'], True)
        self.assertIn('source_outcomes.json', context['agent_visible']['forbidden'])
        self.assertIs(context['agent_visible']['implemented_runtime_loader'], False)
        self.assertIs(context['episode_input_contract']['implemented_loader'], False)
        self.assertEqual(context['mock_contract']['status'], 'design_only_no_mock_engine')
        for key in ['physical_simulation', 'robot_execution', 'publisher_bytes', 'source_data']:
            self.assertIs(context['RELEASE_BOUNDARY'][key], False)
        self.assertIs(context['STATUS']['execution_performed'], False)
        self.assertIs(context['STATUS']['simulation_performed'], False)
        self.assertEqual(context['independent_review']['verdict'], 'accepted_for_task_design_publication')
        self.assertEqual({item['id'] for item in context['source_conflicts']['items']},
                         {'SC_HEIGHT', 'SC_UNCERTAINTY'})

    def test_emitted_javascript_and_json_payloads_match(self):
        text = (ROOT / 'data' / 'cooling.js').read_text()
        payload = text.split('["cooling"]=', 1)[1].rsplit(';', 1)[0]
        self.assertEqual(json.loads(payload), json.loads((ROOT / 'data' / 'cooling.json').read_text()))

    def test_pinned_source_commit_uses_directional_cooling_package(self):
        commit = '9a9472b996145ff7f7a4c138c7477b4e734d8835'
        self.assertEqual(self.family['source_commit'], commit)
        self.assertEqual(self.family['source_folder'],
                         'https://github.com/openags/ScienceGym/blob/' + commit +
                         '/tasks/directional_cooling_operations_v2/')
        for filename, source in self.family['source_files'].items():
            self.assertEqual(source['url'], self.family['source_folder'] + filename)

    def test_invalid_membership_and_loop_scopes_fail_without_mutation(self):
        route = self.routes['OPT_HEMISPHERICAL']
        original = dict(route['detail'], id=route['id'], title=route['label'])
        cases = {
            'empty membership': lambda branch, dep: branch.update(operation_ids=[]),
            'duplicate member': lambda branch, dep: branch['operation_ids'].append('PLAN'),
            'duplicate loop ID': lambda branch, dep: dep['loops'].append(copy.deepcopy(dep['loops'][0])),
            'missing loop': lambda branch, dep: dep['loops'].pop(),
            'unknown loop': lambda branch, dep: dep['loops'][0].update(id='L_INVENTED'),
            'missing scoped loop member': lambda branch, dep: branch['operation_ids'].remove('OPT_SCAN'),
        }
        for label, mutate in cases.items():
            with self.subTest(case=label):
                branch = copy.deepcopy(original)
                dependencies = copy.deepcopy(self.family['dependencies'])
                mutate(branch, dependencies)
                before = copy.deepcopy((branch, dependencies))
                with self.assertRaises(ValueError):
                    builder.cooling_nodes(branch, dependencies)
                self.assertEqual((branch, dependencies), before)

    def test_svg_rendering_does_not_mutate_source_semantics(self):
        before = copy.deepcopy(self.family)
        for route in self.routes.values():
            branch = dict(route['detail'], id=route['id'], title=route['label'])
            self.assertEqual(builder.cooling_nodes(branch, self.family['dependencies']), route['nodes'])
            builder.svg(dict(self.family, default_route=route['id']))
        self.assertEqual(self.family, before)


@unittest.skipUnless(TASKS, 'SCIENCEGYM_TASKS not set; source comparison not run')
class CoolingSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = TASKS / 'directional_cooling_operations_v2'
        cls.documents = {path.relative_to(cls.package).as_posix(): json.loads(path.read_text())
                         for path in cls.package.rglob('*.json')}
        cls.family = get('cooling')

    def test_every_operation_field_is_losslessly_mapped_with_exact_pointer(self):
        original = self.documents['operations.json']['operations']
        self.assertEqual([operation['id'] for operation in self.family['operations']],
                         [operation['id'] for operation in original])
        for index, (source, mapped) in enumerate(zip(original, self.family['operations'])):
            with self.subTest(operation=source['id']):
                for source_key, target_key in OPERATION_FIELDS.items():
                    self.assertEqual(mapped[target_key], source[source_key], source_key)
                for key, value in source.items():
                    if key not in OPERATION_FIELDS:
                        self.assertEqual(mapped['detail'][key], value, key)
                self.assertEqual(mapped['source_file'], 'operations.json')
                self.assertEqual(mapped['source_pointer'], '/operations/' + str(index))

    def test_every_branch_field_membership_and_control_is_exact(self):
        original = self.documents['branches.json']['branches']
        controls = records(self.documents['control_packages.json']['control_packages'])
        self.assertEqual([route['id'] for route in self.family['routes']], [route['id'] for route in original])
        for index, (source, route) in enumerate(zip(original, self.family['routes'])):
            with self.subTest(route=source['id']):
                self.assertEqual(route['label'], source['title'])
                self.assertEqual(route['detail'], {key: value for key, value in source.items()
                                                  if key not in {'id', 'title'}})
                self.assertEqual(ids(route['nodes']), source['operation_ids'])
                self.assertEqual(route['controls'], [controls[key] for key in source['control_ids']])
                self.assertEqual(route['source_file'], 'branches.json')
                self.assertEqual(route['source_pointer'], '/branches/' + str(index))

    def test_context_and_dependencies_are_lossless(self):
        for key, filename in CONTEXT_FILES.items():
            with self.subTest(context=key):
                self.assertEqual(self.family['context'][key], self.documents[filename])
        self.assertEqual(self.family['context']['branch_policy'],
                         {key: value for key, value in self.documents['branches.json'].items() if key != 'branches'})
        self.assertEqual(self.family['context']['operation_policy'],
                         {key: value for key, value in self.documents['operations.json'].items() if key != 'operations'})
        self.assertEqual(self.family['dependencies'], self.documents['dependencies.json'])

    def test_evidence_locators_and_source_urls_are_exact(self):
        provenance = self.documents['provenance.json']
        expected = {key: dict(value, url=provenance['source_ids'][value['source_id']])
                    for key, value in provenance['evidence'].items()}
        self.assertEqual(self.family['evidence'], expected)
        self.assertEqual(self.family['title'], provenance['title'])
        self.assertEqual(self.family['doi'], provenance['doi'])
        for operation in self.family['operations']:
            self.assertTrue(set(operation['sources']) <= set(expected), operation['id'])
        for route in self.family['routes']:
            self.assertTrue(set(route['detail']['source_evidence_ids']) <= set(expected), route['id'])

    def test_all_six_source_loops_are_retained_without_invented_expansion(self):
        declared = self.documents['dependencies.json']['loops']
        seen = set()
        for route in self.family['routes']:
            expected = [loop for loop in declared if set(loop['body']) <= set(route['detail']['operation_ids'])]
            mapped = [node['meta']['loop'] for node in loops(route)]
            with self.subTest(route=route['id']):
                self.assertEqual(mapped, expected)
            seen.update(loop['id'] for loop in mapped)
        self.assertEqual(seen, {loop['id'] for loop in declared})

    def test_recursive_source_inventory_hashes_and_pointers_match_actual_bytes(self):
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

    def test_reviewed_source_package_still_matches_export_allowlist(self):
        allowlist = self.documents['EXPORT_ALLOWLIST.json']
        self.assertIs(allowlist['self_hash_excluded'], True)
        self.assertEqual(set(allowlist['sha256']), set(allowlist['files']) - {'EXPORT_ALLOWLIST.json'})
        for filename, expected_hash in allowlist['sha256'].items():
            with self.subTest(file=filename):
                self.assertEqual(hashlib.sha256((self.package / filename).read_bytes()).hexdigest(), expected_hash)

    def test_rebuild_and_pooling_are_deterministic_without_source_mutation(self):
        before = {path.relative_to(self.package).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in self.package.rglob('*') if path.is_file() and '__pycache__' not in path.parts}
        rebuilt = builder.adapt_cooling(self.package)
        generated = copy.deepcopy(self.family)
        generated.pop('shared', None)
        self.assertEqual(rebuilt, generated)
        self.assertEqual(builder.adapt_cooling(self.package), rebuilt)
        pooled = builder.unique_shared(copy.deepcopy(rebuilt))
        unpacked = decode(pooled, pooled)
        unpacked.pop('shared', None)
        self.assertEqual(unpacked, rebuilt)
        after = {path.relative_to(self.package).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in self.package.rglob('*') if path.is_file() and '__pycache__' not in path.parts}
        self.assertEqual(after, before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
