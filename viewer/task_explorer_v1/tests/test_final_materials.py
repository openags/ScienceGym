"""Independent source reconstruction and boundary checks for final-materials views.

The inverse maps and source expectations below are deliberately not imported
from the adapter. A successful self-comparison alone cannot prove fidelity.
"""
import collections
import copy
import hashlib
import json
import re
import unittest
import xml.etree.ElementTree as ET

from test_semantics import ROOT, TASKS, builder, get, ids
import final_materials_adapters as materials

KEYS = ('horn_acoustics', 'mechanical_logic', 'cold_shape')
SOURCE_COMMIT = '26f402e4be797a91edce8253e4ed45bed6e01e7c'
# operations, inspection records, physical records, unknown groups, controls, JSON files
EXPECTED = {'horn_acoustics': (44, 14, 5, 17, 3, 28),
            'mechanical_logic': (55, 26, 14, 15, 5, 26),
            'cold_shape': (76, 38, 32, 19, 8, 32)}
COMMON = {'title': 'title', 'actions': 'actions', 'preconditions': 'pre',
          'postconditions': 'post', 'observable_completion': 'acceptance',
          'evidence_ids': 'sources', 'failure_handling': 'recovery',
          'unknown_parameter_ids': 'unknowns', 'authorship': 'provenance'}
INVERSE = {'horn_acoustics': {**COMMON, 'station_id': 'stage', 'object_roles': 'objects'},
           'mechanical_logic': {**COMMON, 'location_id': 'stage', 'target_asset_roles': 'objects'},
           'cold_shape': {'title': 'title', 'station_id': 'stage', 'robot_actions': 'actions',
                          'objects': 'objects', 'preconditions': 'pre', 'postconditions': 'post',
                          'observable_completion': 'acceptance', 'source_evidence_ids': 'sources',
                          'failure_recovery': 'recovery', 'unknown_parameter_ids': 'unknowns',
                          'authored_translation': 'provenance'}}
ALIASES = {'unknown_parameters.json': 'unknowns', 'evaluator_reference.json': 'acceptance',
           'lineage_contract.json': 'lineage'}


def package(key): return TASKS / (key + '_operations_v2')
def raw(key, name): return json.loads((package(key) / name).read_text())
def byid(records): return {r['id']: r for r in records}
def route(f, identifier): return byid(f['routes'])[identifier]
def nodes(r): return [n for n, _ in builder.walk(r['nodes'])]
def loops(r): return [n for n in nodes(r) if n['type'] == 'loop']
def pointer(document, path):
    for token in path.split('/')[1:]:
        token = token.replace('~1', '/').replace('~0', '~')
        document = document[int(token)] if isinstance(document, list) else document[token]
    return document


def inverse_operation(key, operation):
    result = {'id': operation['id'], **copy.deepcopy(operation['detail'])}
    for original, normalized in INVERSE[key].items(): result[original] = copy.deepcopy(operation[normalized])
    return result


class FinalMaterialsBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.families = {key: get(key) for key in KEYS}

    def test_exact_inventory_and_prior_nineteen_unchanged_counts(self):
        manifest = [r for r in json.loads((ROOT / 'manifest.json').read_text())['families'] if r['id'] not in ('atmospheric_optics', 'afm_metrology', 'martian_geophysics', 'transistor', 'laser_control', 'solar_water', 'sucrose_metrology', 'actuator_metrology')]
        self.assertEqual((len(manifest), sum(r['routes'] for r in manifest), sum(r['operations'] for r in manifest)),
                         (24, 541, 2189))
        old = [r for r in manifest if r['id'] not in ('gear', 'hydrogel_optical') and r['id'] not in KEYS]
        self.assertEqual((len(old), sum(r['routes'] for r in old), sum(r['operations'] for r in old)),
                         (19, 386, 1838))
        for key, (ops, records, physical, unknowns, controls, files) in EXPECTED.items():
            f = self.families[key]
            self.assertEqual((len(f['operations']), len(f['routes']), len(f['source_files'])), (ops, records, files))
            self.assertEqual(f['summary_counts']['physical_records'], physical)
            self.assertEqual(f['summary_counts']['unresolved_input_groups'], unknowns)
            self.assertEqual(f['summary_counts']['control_records'], controls)
            self.assertEqual(len(byid(f['routes'])), records)
            self.assertNotIn('WHOLE_PAPER_PRACTICAL', byid(f['routes']))

    def test_read_only_boundaries_and_nonmanual_metadata_only(self):
        for f in self.families.values():
            self.assertEqual(f['visibility'], 'author_evaluator_reference_only')
            self.assertIs(f['actor_projection_implemented'], False)
            self.assertIn('not an actor projection', f['status'])
            for r in f['routes']:
                self.assertIn('not an actor projection', r['basis'])
                self.assertEqual(r['metadata_only'], not bool(ids(r['nodes'])))
                if r['route_kind'] != 'physical':
                    self.assertEqual(ids(r['nodes']), [])
                    self.assertTrue(r['metadata_only'])

    def test_membership_not_chronology_and_no_expanded_repeats(self):
        shown_loops = collections.Counter()
        for key, f in self.families.items():
            for r in f['routes']:
                if r['route_kind'] != 'physical': continue
                self.assertEqual(r['nodes'][0]['type'], 'obligations')
                self.assertIs(r['nodes'][0]['ordered'], False)
                self.assertEqual(ids(r['nodes']), r['detail']['operation_ids'])
                self.assertEqual(len(ids(r['nodes'])), len(set(ids(r['nodes']))))
                for n in loops(r):
                    self.assertIs(n['symbolic'], True)
                    self.assertIs(n['ordered'], False)
                    self.assertEqual(n['children'], [])
                    shown_loops[key] += 1
        self.assertEqual(dict(shown_loops), {'horn_acoustics': 4, 'mechanical_logic': 13, 'cold_shape': 224})
        self.assertEqual({k: f['summary_counts']['symbolic_loop_contracts'] for k, f in self.families.items()},
                         {'horn_acoustics': 4, 'mechanical_logic': 6, 'cold_shape': 7})

    def test_all_78_svg_variants_match_operation_rows_without_arrows(self):
        count = 0
        for f in self.families.values():
            for r in f['routes']:
                candidate = copy.deepcopy(f); candidate['default_route'] = r['id']
                svg = builder.svg(candidate); root = ET.fromstring(svg)
                text = [x.text or '' for x in root.findall('.//{http://www.w3.org/2000/svg}text')]
                badges = [x.split(' · ', 1)[1].split(' · ', 1)[0] for x in text if re.match(r'^\d+ · ', x)]
                self.assertEqual([x for x in badges if x in byid(f['operations'])], ids(r['nodes']))
                self.assertNotIn('marker-end=', svg)
                self.assertIn('0 validated runnable whole-paper tasks', svg)
                self.assertIn('unresolved inputs block execution', svg)
                for warning in {'horn_acoustics': ['focusing/splitting numerical', 'not specimen replicates'],
                                'mechanical_logic': ['source_complete=false', 'nine actual movies remain uninspected'],
                                'cold_shape': ['CLOSED QUALIFIED SERVICES ONLY', 'source workbook unread', 'not independent validation']}[f['id']]:
                    self.assertIn(warning, svg)
                count += 1
        self.assertEqual(count, 78)

    def test_json_javascript_and_immutable_source_links(self):
        for key, f in self.families.items():
            js = (ROOT / 'data' / (key + '.js')).read_text().split('[' + json.dumps(key) + ']=', 1)[1].rsplit(';', 1)[0]
            self.assertEqual(json.loads(js), json.loads((ROOT / 'data' / (key + '.json')).read_text()))
            self.assertEqual(f['source_commit'], SOURCE_COMMIT)
            folder = 'https://github.com/openags/ScienceGym/blob/' + SOURCE_COMMIT + '/tasks/' + key + '_operations_v2/'
            self.assertEqual(f['source_folder'], folder)
            for name, record in f['source_files'].items():
                self.assertEqual(record['url'], folder + name)
                self.assertRegex(record['sha256'], r'^[0-9a-f]{64}$')

    def test_horn_numerical_and_physical_and_derived_contexts_distinct(self):
        f = self.families['horn_acoustics']
        self.assertEqual(collections.Counter(r['route_kind'] for r in f['routes']), {'physical': 5, 'numerical': 9})
        self.assertEqual({r['id'] for r in f['routes'] if r['route_kind'] == 'numerical'},
                         {r['branch_id'] for r in f['context']['nonmanual_scope']['branches']})
        self.assertEqual(route(f, 'B_COMPARE_CLOSE')['detail']['kind'], 'physical_and_analysis_closure')
        self.assertIn('DERIVED ANALYSIS CLOSURE', route(f, 'B_COMPARE_CLOSE')['label'])
        self.assertIs(f['context']['control_packages']['numerical_controls_are_physical'], False)
        outcomes = f['context']['source_outcomes']
        self.assertEqual((len(outcomes['physical']), len(outcomes['numerical'])), (1, 2))
        self.assertEqual(outcomes['SI_Table_2']['kind'], 'published_averaged_complex_reference')
        self.assertIs(outcomes['SI_Table_2']['raw_ten_readouts_available'], False)
        counts = f['context']['branch_policy']['counts']
        self.assertEqual((counts['physical_measurement_conditions'], counts['points_per_condition'], counts['readouts_per_point']), (2, 190, 10))
        self.assertEqual(counts['derived_minimum_valid_readouts_for_one_pair'], 3800)
        self.assertIsNone(counts['independent_specimen_replicates'])
        self.assertIsNone(counts['independent_campaign_replicates'])
        self.assertIn('not additional source-supplied raw observations', counts['counts_note'])
        self.assertEqual(collections.Counter(o['detail']['actor'] for o in f['operations']),
                         {'robot': 40, 'analysis_service': 3, 'automated_printer': 1})

    def test_remm_source_complete_and_uninspected_media_stay_false(self):
        f = self.families['mechanical_logic']; context = f['context']
        for name in ('STATUS', 'provenance', 'source_access_audit', 'RELEASE_BOUNDARY'):
            self.assertIs(context[name]['source_complete'], False, name)
        audit = context['source_access_audit']
        self.assertIs(audit['complete_full_source_packet'], False)
        self.assertEqual(audit['main']['panels'], 'uninspected')
        self.assertEqual(audit['movies']['contents'], 'uninspected')
        self.assertEqual(audit['movies']['count'], 9)
        self.assertIn('source_complete is false', f['source_warnings'])
        self.assertIs(context['nonmanual_scope']['numerical_to_physical_promotion_allowed'], False)
        self.assertEqual(collections.Counter(r['route_kind'] for r in f['routes']),
                         {'physical': 14, 'numerical': 7, 'reference': 3, 'proposal': 1, 'extension': 1})
        for r in f['routes'][14:]:
            self.assertIs(r['detail']['executed_here'], False)
            self.assertIsNone(r['detail']['physical_branch_id'])
        self.assertEqual(route(f, 'MICROSCALE_MEMS')['route_kind'], 'proposal')
        self.assertEqual(route(f, 'STORAGE_READ_REWRITE')['route_kind'], 'extension')

    def test_cold_shape_fits_cycles_and_unread_sources_remain_distinct(self):
        f = self.families['cold_shape']; context = f['context']
        self.assertEqual(collections.Counter(r['route_kind'] for r in f['routes']), {'physical': 32, 'numerical': 4, 'analysis': 2})
        for name in ('N_DMA_FIT', 'N_RATE_FIT'):
            r = route(f, name)
            self.assertEqual(r['route_kind'], 'analysis')
            self.assertEqual(r['detail']['classification'], 'numerical_or_analytical_only')
            self.assertEqual(r['detail']['status'], 'specified_not_run')
            self.assertIn('not an additional source branch', r['display_classification_basis'])
            self.assertEqual(ids(r['nodes']), [])
        self.assertIs(context['nonmanual_scope']['promotion_to_physical_evidence_allowed'], False)
        self.assertIs(context['STATUS']['ancillary_movies_inspected'], False)
        self.assertIs(context['STATUS']['source_data_workbook_inspected'], False)
        self.assertEqual(context['source_access_audit']['read_scope']['movie_bytes'], 0)
        self.assertIs(context['source_access_audit']['read_scope']['source_workbook'], False)
        self.assertEqual(route(f, 'MEMORY_TEN_CYCLES')['detail']['source_cycles'], 10)
        self.assertEqual(route(f, 'HINGE_FORTY_CYCLES')['detail']['source_cycles'], 40)
        self.assertIn('not independent specimen counts', context['control_packages']['replication'])
        self.assertEqual(f['dependencies']['simulation_edges_to_physical'], [])
        self.assertEqual(context['mock_contract']['live_evidence_acceptance'], False)

    def test_cold_shape_closed_services_never_flatten_into_robot_actions(self):
        f = self.families['cold_shape']; operations = byid(f['operations'])
        self.assertEqual(collections.Counter(o['detail']['actor'] for o in f['operations']),
                         {'robot': 58, 'qualified_closed_service': 9, 'analysis_worker': 9})
        for op in f['operations']:
            self.assertIsInstance(op['actions'], list)
            self.assertIn('service_process', op['detail'])
            self.assertIn('source_fact', op['detail'])
            self.assertEqual(op['detail']['execution_mode'], 'static_design_only')
            self.assertIn('occurrence_bindings_required', op['detail'])
            if op['detail']['actor'] == 'qualified_closed_service':
                self.assertTrue(op['detail']['service_process'])
                self.assertNotEqual(op['actions'], op['detail']['service_process'])
        stations = byid(f['context']['station_contracts']['stations'])
        for station in stations.values(): self.assertIs(station['implemented'], False)
        for identifier, text in [('WS_RESIN', 'opening, mixing and waste-contact'),
                                 ('WS_PRINT', 'resin exposure, UV'), ('WS_THERMAL', 'hot media'),
                                 ('WS_ELECTRIC', 'EGaIn handling')]:
            self.assertIn(text, stations[identifier]['boundary'])
        for prefix in ('RESIN', 'PRINT', 'TENSILE', 'DMA', 'MEMORY', 'DEFORM', 'THERMAL', 'FILL'):
            waiting = operations[prefix + '_WAIT']
            self.assertIn('guard_closed', waiting['pre'])
            self.assertTrue(waiting['detail']['conditional_postconditions'])
            self.assertIn('safe_to_unload', json.dumps(waiting['detail']['conditional_postconditions']))

    def test_no_source_execution_readiness_promoted(self):
        for key, f in self.families.items():
            status = f['context']['STATUS']
            if key == 'horn_acoustics':
                self.assertIs(status['physical_execution'], False)
                self.assertIs(status['scientific_simulation'], False)
                self.assertIs(f['context']['source_access_audit']['robot_execution_ready'], False)
            else:
                for field in ('physical_recipe_complete', 'scene_built', 'physical_simulation_run',
                              'robot_execution_run', 'scientific_replication_supported'):
                    self.assertIs(status[field], False)
            self.assertTrue(f['context']['unknowns']['unknowns'])
            self.assertTrue(f['context']['lineage'])
            self.assertTrue(f['context']['source_conflicts'])


@unittest.skipUnless(TASKS, 'SCIENCEGYM_TASKS not set; exact source reconstruction not run')
class FinalMaterialsSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.families = {key: get(key) for key in KEYS}
        cls.adapted = {key: materials.adapt(package(key), key) for key in KEYS}

    def test_independent_inverse_reconstructs_all_175_operation_records(self):
        count = 0
        for key, f in self.families.items():
            original = raw(key, 'operations.json')['operations']
            self.assertEqual([o['id'] for o in f['operations']], [o['id'] for o in original])
            for i, (op, source) in enumerate(zip(f['operations'], original)):
                self.assertEqual(inverse_operation(key, op), source, (key, op['id']))
                self.assertEqual((op['source_file'], op['source_pointer']), ('operations.json', '/operations/' + str(i)))
                self.assertEqual(pointer(raw(key, op['source_file']), op['source_pointer']), source)
                self.assertIs(op['loop'], None)
                count += 1
        self.assertEqual(count, 175)

    def test_all_86_original_json_documents_reconstruct_and_hash_exactly(self):
        count = 0
        for key, f in self.families.items():
            names = {p.relative_to(package(key)).as_posix() for p in package(key).rglob('*.json')}
            self.assertEqual(set(f['source_files']), names)
            reconstructed = {name: copy.deepcopy(f['context'][ALIASES.get(name, name[:-5])])
                             for name in names if name not in ('operations.json', 'branches.json', 'dependencies.json')}
            reconstructed['operations.json'] = {**copy.deepcopy(f['context']['operation_policy']),
                                                'operations': [inverse_operation(key, op) for op in f['operations']]}
            reconstructed['branches.json'] = {**copy.deepcopy(f['context']['branch_policy']),
                                              'branches': [copy.deepcopy(r['detail']) for r in f['routes'] if r['source_file'] == 'branches.json']}
            reconstructed['dependencies.json'] = f['dependencies']
            self.assertEqual(set(reconstructed), names)
            for name in sorted(names):
                self.assertEqual(reconstructed[name], raw(key, name), (key, name))
                self.assertEqual(f['source_files'][name]['sha256'], hashlib.sha256((package(key) / name).read_bytes()).hexdigest(), (key, name))
                count += 1
        self.assertEqual(count, 86)

    def test_all_routes_and_nested_contracts_resolve_exact_source_pointers(self):
        routes_seen = contracts_seen = 0
        for key, f in self.families.items():
            for r in f['routes']:
                self.assertEqual(r['detail'], pointer(raw(key, r['source_file']), r['source_pointer']), (key, r['id']))
                routes_seen += 1
                for n in nodes(r):
                    meta = n.get('meta', {})
                    if 'source_contract' in meta:
                        self.assertEqual(meta['source_contract'], pointer(raw(key, meta['source_file']), meta['source_pointer']), (key, r['id']))
                        contracts_seen += 1
        self.assertEqual(routes_seen, 78)
        self.assertGreater(contracts_seen, 300)

    def test_each_membership_and_control_scope_matches_source(self):
        for key, f in self.families.items():
            control_document = raw(key, 'control_packages.json')
            control_field = 'controls' if key == 'cold_shape' else 'packages'
            scope_field = {'horn_acoustics': 'required_branches', 'mechanical_logic': 'branches', 'cold_shape': 'scope'}[key]
            for source in raw(key, 'branches.json')['branches']:
                r = route(f, source['id'])
                self.assertEqual(ids(r['nodes']), source['operation_ids'])
                if r['route_kind'] == 'physical':
                    expected = [c for c in control_document[control_field]
                                if isinstance(c[scope_field], list) and source['id'] in c[scope_field]]
                    self.assertEqual(r['controls'], expected)
            # Descriptive/global controls stay exact rather than acquiring invented branch scope.
            self.assertEqual(f['context']['control_packages'], control_document)

    def test_horn_source_repeats_condition_scopes_and_one_of_unchanged(self):
        key = 'horn_acoustics'; f = self.families[key]
        original = raw(key, 'dependencies.json')
        for source in raw(key, 'branches.json')['branches'][:5]:
            r = route(f, source['id'])
            self.assertEqual([n['meta']['source_contract'] for n in loops(r)], source['loops'])
            shown = [n['meta']['source_contract'] for n in nodes(r)
                     if n.get('meta', {}).get('source_file') == 'dependencies.json']
            self.assertEqual(shown, original['condition_scoped_edges'])
        one_of = next(r for r in f['dependencies']['conditional_requirements'] if r['operation_id'] == 'CONDITION_START')
        self.assertEqual(one_of, {'operation_id': 'CONDITION_START', 'one_of': ['PANEL_ABSENT', 'PANEL_INSTALL'], 'condition_bound': True})
        self.assertEqual(f['context']['geometry_reference'], raw(key, 'geometry_reference.json'))
        self.assertEqual(f['context']['execution_contract'], raw(key, 'execution_contract.json'))

    def test_remm_only_source_scoped_loops_apply(self):
        key = 'mechanical_logic'; f = self.families[key]
        for source in raw(key, 'branches.json')['branches']:
            expected = [loop for loop in raw(key, 'dependencies.json')['loops'] if source['id'] in loop['branch_ids']]
            shown = [n['meta']['source_contract'] for n in loops(route(f, source['id']))]
            self.assertEqual(shown, expected)
            for loop in shown:
                self.assertIsNone(loop['repeat_count'])
                self.assertIs(loop['empty_schedule_allowed'], False)
        self.assertEqual(f['context']['state_contract'], raw(key, 'state_contract.json'))
        self.assertEqual(f['context']['lineage'], raw(key, 'lineage_contract.json'))

    def test_cold_shape_exact_phase_gates_and_catalog_not_universal_execution(self):
        key = 'cold_shape'; f = self.families[key]
        requirements = {r['branch_id']: r for r in raw(key, 'condition_requirements.json')['branches']}
        catalog = raw(key, 'dependencies.json')['loops']
        for source in raw(key, 'branches.json')['branches']:
            r = route(f, source['id']); phase_node = r['nodes'][1]; catalog_node = r['nodes'][2]
            self.assertEqual(phase_node['meta']['source_contract'], requirements[source['id']])
            self.assertIs(phase_node['meta']['source_contract']['nonempty_instance_schedule_required'], True)
            self.assertIn('never all loops to every branch', catalog_node['label'])
            self.assertEqual([n['meta']['source_contract'] for n in loops(r)], catalog)
            self.assertEqual(r['nodes'][3]['meta']['source_contract'], raw(key, 'station_contracts.json'))
        self.assertEqual(byid(catalog)['L_TEN']['count'], 10)
        self.assertEqual(byid(catalog)['L_FORTY']['count'], 40)
        self.assertIsNone(byid(catalog)['L_REPLICATES']['count'])
        self.assertEqual(f['context']['state_contract'], raw(key, 'state_contract.json'))

    def test_evidence_retains_full_provenance_records(self):
        for key, f in self.families.items():
            source = raw(key, 'provenance.json')['evidence']
            self.assertEqual(f['evidence'], byid(source) if isinstance(source, list) else source)
            self.assertEqual(f['context']['provenance'], raw(key, 'provenance.json'))

    def test_bundled_decoded_payload_equals_fresh_validated_projection(self):
        for key, f in self.families.items():
            self.assertEqual({name: value for name, value in f.items() if name != 'shared'}, self.adapted[key])
            self.assertEqual(materials.projection(package(key), key), self.adapted[key])
            self.assertTrue(materials.validate_projection(self.adapted[key], package(key)))

    def reject(self, key, mutation):
        candidate = copy.deepcopy(self.adapted[key]); mutation(candidate)
        with self.assertRaises(ValueError): materials.validate_projection(candidate, package(key))

    def test_reject_lost_reordered_or_chronological_membership(self):
        for key in KEYS:
            self.reject(key, lambda f: f['routes'][0]['nodes'][0]['children'].pop())
            self.reject(key, lambda f: f['routes'][0]['nodes'][0]['children'].reverse())
            self.reject(key, lambda f: f['routes'][0]['nodes'][0].__setitem__('ordered', True))

    def test_reject_nonmanual_promoted_to_physical_or_acquisition(self):
        for key in KEYS:
            self.reject(key, lambda f: f['routes'][-1]['nodes'].append('PLAN'))
            self.reject(key, lambda f: f['routes'][-1].__setitem__('route_kind', 'physical'))
            self.reject(key, lambda f: f['routes'][-1].__setitem__('metadata_only', False))

    def test_reject_operation_payload_and_authorship_changes(self):
        for key in KEYS:
            self.reject(key, lambda f: f['operations'][0]['actions'].append('invented physical execution'))
            self.reject(key, lambda f: f['operations'][0].__setitem__('provenance', 'source-reported robot action'))
            self.reject(key, lambda f: f['operations'][0]['detail'].__setitem__('execution_mode', 'ready_to_execute'))

    def test_reject_missing_original_contexts_and_gates(self):
        fields = ('unknowns', 'acceptance', 'lineage', 'control_packages', 'source_outcomes', 'source_conflicts',
                  'source_access_audit', 'station_contracts', 'episode_input_contract', 'agent_visible', 'RELEASE_BOUNDARY')
        for key in KEYS:
            for field in fields:
                with self.subTest(key=key, field=field):
                    self.reject(key, lambda f, field=field: f['context'].pop(field))

    def test_reject_source_pins_hashes_and_omitted_json_files(self):
        for key in KEYS:
            self.reject(key, lambda f: f.__setitem__('source_commit', '0' * 40))
            self.reject(key, lambda f: f['source_files'].pop('provenance.json'))
            self.reject(key, lambda f: f['source_files']['operations.json'].__setitem__('sha256', '0' * 64))
            self.reject(key, lambda f: f['source_files']['operations.json'].__setitem__('url', 'https://example.invalid/moving-main'))

    def test_reject_expanded_loops_and_fabricated_default_counts(self):
        for key in KEYS:
            self.reject(key, lambda f: loops(f['routes'][0])[0]['children'].append('PLAN'))
            self.reject(key, lambda f: loops(f['routes'][0])[0].__setitem__('symbolic', False))
        for key, field in [('mechanical_logic', 'repeat_count'), ('cold_shape', 'count')]:
            self.reject(key, lambda f, field=field: f['dependencies']['loops'][0].__setitem__(field, 1))

    def test_reject_controls_and_lineage_facts_changed(self):
        for key in KEYS:
            def drop_control(f):
                next(r for r in f['routes'] if r.get('controls'))['controls'].pop()
            self.reject(key, drop_control)
            self.reject(key, lambda f: f['context']['lineage'].clear())
            self.reject(key, lambda f: f['context']['unknowns']['unknowns'].pop())

    def test_reject_horn_incompatible_states_and_derived_data_as_raw(self):
        self.reject('horn_acoustics', lambda f: f['dependencies']['conditional_requirements'][0].__setitem__('one_of', ['PANEL_ABSENT', 'PANEL_INSTALL', 'ANY']))
        self.reject('horn_acoustics', lambda f: f['dependencies']['condition_scoped_edges'][0].__setitem__('condition', 'both'))
        self.reject('horn_acoustics', lambda f: f['context']['source_outcomes']['SI_Table_2'].__setitem__('raw_ten_readouts_available', True))
        self.reject('horn_acoustics', lambda f: f['context']['branch_policy']['counts'].__setitem__('independent_specimen_replicates', 10))
        self.reject('horn_acoustics', lambda f: f['context']['control_packages'].__setitem__('numerical_controls_are_physical', True))

    def test_reject_remm_source_completion_and_inspected_movie_inventions(self):
        for field in ('STATUS', 'provenance', 'source_access_audit', 'RELEASE_BOUNDARY'):
            self.reject('mechanical_logic', lambda f, field=field: f['context'][field].__setitem__('source_complete', True))
        self.reject('mechanical_logic', lambda f: f['context']['source_access_audit']['main'].__setitem__('panels', 'inspected'))
        self.reject('mechanical_logic', lambda f: f['context']['source_access_audit']['movies'].__setitem__('contents', 'inspected'))
        self.reject('mechanical_logic', lambda f: f['dependencies']['loops'][2].__setitem__('empty_schedule_allowed', True))

    def test_reject_cold_shape_open_service_or_removed_safe_release_gate(self):
        self.reject('cold_shape', lambda f: byid(f['operations'])['RESIN_WAIT']['detail'].__setitem__('actor', 'robot'))
        self.reject('cold_shape', lambda f: byid(f['operations'])['RESIN_WAIT']['detail']['service_process'].clear())
        self.reject('cold_shape', lambda f: byid(f['operations'])['RESIN_WAIT']['detail']['conditional_postconditions'].clear())
        self.reject('cold_shape', lambda f: byid(f['context']['station_contracts']['stations'])['WS_RESIN'].__setitem__('boundary', 'Open mixing by robot'))
        self.reject('cold_shape', lambda f: byid(f['context']['station_contracts']['stations'])['WS_THERMAL'].__setitem__('implemented', True))

    def test_reject_cold_shape_empty_schedule_missing_phase_or_cycle_promotion(self):
        self.reject('cold_shape', lambda f: f['context']['condition_requirements']['branches'][0].__setitem__('nonempty_instance_schedule_required', False))
        self.reject('cold_shape', lambda f: route(f, 'MEMORY_COLD')['detail']['phase_order'].pop())
        self.reject('cold_shape', lambda f: route(f, 'MEMORY_TEN_CYCLES')['detail'].__setitem__('source_independent_sample_count', 10))
        self.reject('cold_shape', lambda f: byid(f['dependencies']['loops'])['L_FORTY'].__setitem__('count', 1))
        self.reject('cold_shape', lambda f: route(f, 'N_DMA_FIT')['detail'].__setitem__('classification', 'independent_physical_validation'))
        self.reject('cold_shape', lambda f: f['context']['STATUS'].__setitem__('ancillary_movies_inspected', True))

    def test_reject_fabricated_runtime_or_validated_execution(self):
        for key in KEYS:
            self.reject(key, lambda f: f.__setitem__('actor_projection_implemented', True))
            self.reject(key, lambda f: f.__setitem__('visibility', 'actor_runtime'))
            self.reject(key, lambda f: f['context'].__setitem__('execution_receipt', {'success': True}))


if __name__ == '__main__': unittest.main()
