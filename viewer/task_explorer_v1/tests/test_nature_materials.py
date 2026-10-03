"""Independent inverse reconstruction and adversarial checks for Nature views.

Source expectations and inverse maps are deliberately independent of the adapter.
Bundled checks run offline; exact reconstruction explicitly requires source tasks.
"""
import collections
import copy
import hashlib
import json
import re
import unittest
import xml.etree.ElementTree as ET

from test_semantics import ROOT, TASKS, builder, get, ids
import nature_materials_adapters as materials

KEYS = ('gear', 'hydrogel_optical')
SOURCE_COMMIT = '9e490ae5d3380121df7be1c18d4de35aac8508c5'
EXPECTED = {'gear': (69, 37, 29), 'hydrogel_optical': (107, 40, 35)}
INVERSE = {
    'gear': {'station_id': 'stage', 'objects': 'objects', 'preconditions': 'pre',
             'postconditions': 'post', 'completion_evidence': 'acceptance',
             'source_evidence_ids': 'sources', 'unknown_input_ids': 'unknowns',
             'translation_kind': 'provenance'},
    'hydrogel_optical': {'title': 'title', 'station_id': 'stage', 'objects': 'objects',
                        'robot_actions': 'actions', 'preconditions': 'pre',
                        'postconditions': 'post', 'source_evidence_ids': 'sources',
                        'unknown_parameter_ids': 'unknowns', 'authored_translation': 'provenance'}}
ALIASES = {'unknown_parameters.json': 'unknowns', 'evaluator_reference.json': 'acceptance',
           'lineage_contract.json': 'lineage'}


def package(key): return TASKS / (key + '_operations_v2')
def raw(key, name): return json.loads((package(key) / name).read_text())
def byid(records): return {r['id']: r for r in records}
def route(f, identifier): return byid(f['routes'])[identifier]
def nodes(r): return [n for n, _ in builder.walk(r['nodes'])]
def pointer(document, path):
    for token in path.split('/')[1:]:
        token = token.replace('~1', '/').replace('~0', '~')
        document = document[int(token)] if isinstance(document, list) else document[token]
    return document


def inverse_operation(key, operation):
    result = {'id': operation['id'], **copy.deepcopy(operation['detail'])}
    for original, normalized in INVERSE[key].items():
        result[original] = copy.deepcopy(operation[normalized])
    recovery = 'failure_and_recovery' if key == 'gear' else 'failure_recovery'
    result[recovery] = copy.deepcopy(operation['recovery'][0])
    if key == 'gear': result['action'] = copy.deepcopy(operation['actions'][0])
    return result


class NatureMaterialsBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.families = {key: get(key) for key in KEYS}

    def test_exact_inventory_and_prior_twenty_two_counts(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text())['families']
        self.assertEqual((len(manifest), sum(r['routes'] for r in manifest), sum(r['operations'] for r in manifest)),
                         (24, 541, 2189))
        old = [r for r in manifest if r['id'] not in KEYS]
        self.assertEqual((len(old), sum(r['routes'] for r in old), sum(r['operations'] for r in old)), (22, 464, 2013))
        for key, expected in EXPECTED.items():
            f = self.families[key]
            self.assertEqual((len(f['operations']), len(f['routes']), len(f['source_files'])), expected)
            self.assertEqual(len(byid(f['routes'])), expected[1])
        self.assertEqual(collections.Counter(r['route_kind'] for r in self.families['gear']['routes']),
                         {'physical': 18, 'preparation': 8, 'numerical': 7, 'analysis': 2, 'illustrative': 2})
        self.assertEqual(collections.Counter(r['route_kind'] for r in self.families['hydrogel_optical']['routes']),
                         {'physical': 36, 'numerical': 1, 'theory': 1, 'analysis': 1, 'compatibility': 1})

    def test_visibility_and_nonmanual_namespace_boundaries(self):
        for key, f in self.families.items():
            self.assertEqual(f['visibility'], 'author_evaluator_reference_only')
            self.assertIs(f['actor_projection_implemented'], False)
            self.assertIn('not an actor projection', f['status'])
            for r in f['routes']:
                self.assertEqual(r['metadata_only'], not bool(ids(r['nodes'])))
                self.assertIn('not an actor projection', r['basis'])
                self.assertFalse(any(n['type'] == 'loop' for n in nodes(r)))
                if key == 'gear' and r['route_kind'] == 'numerical':
                    self.assertEqual(ids(r['nodes']), ['NUMERICAL_CONFIG', 'NUMERICAL_RUN', 'NUMERICAL_REPORT'])
                    self.assertIs(r['nodes'][0]['ordered'], False)
                elif r['route_kind'] in ('illustrative', 'theory', 'compatibility') or (key == 'hydrogel_optical' and r['route_kind'] != 'physical'):
                    self.assertEqual(ids(r['nodes']), [])

    def test_scalar_wrappers_and_authored_absence_not_source_acceptance(self):
        for key, f in self.families.items():
            for op in f['operations']:
                self.assertEqual(len(op['recovery']), 1)
                self.assertIsInstance(op['recovery'][0], str)
                self.assertIs(op['loop'], None)
                if key == 'gear':
                    self.assertEqual(len(op['actions']), 1)
                    self.assertIsInstance(op['actions'][0], str)
                    self.assertIn('source supplies no title', op['display_title_basis'])
                else:
                    self.assertIn('No completion_evidence field supplied', op['acceptance'][0])
                    self.assertIn('not a new source acceptance predicate', op['acceptance_display_basis'])
                    self.assertIs(op['detail']['physical_execution_implemented'], False)
                    self.assertEqual(op['detail']['execution_mode'], 'static_design_only')

    def test_hydro_membership_cycles_and_distinct_lineages(self):
        f = self.families['hydrogel_optical']
        self.assertEqual(f['dependencies']['service_phase_order'], ['LOAD', 'VERIFY', 'HANDOFF', 'READOUT', 'UNLOAD', 'COMMIT'])
        for r in f['routes'][:36]:
            self.assertEqual(r['nodes'][0]['type'], 'obligations')
            self.assertIs(r['nodes'][0]['ordered'], False)
            self.assertEqual(ids(r['nodes']), r['detail']['operation_ids'])
            self.assertEqual(len(ids(r['nodes'])), len(set(ids(r['nodes']))))
            self.assertIsNone(r['detail']['source_independent_specimens'])
            self.assertIs(r['detail']['execution_ready'], False)
            self.assertIn('CTRL_BASELINE', byid(r['controls']))
        self.assertEqual(route(f, 'LATTICE_CYCLES')['detail']['source_cycles'], 27)
        self.assertEqual(route(f, 'IMAGE_CYCLES')['detail']['source_cycles'], 25)
        self.assertEqual(route(f, 'ANGLE_IMAGE_MAIN')['detail']['condition_axes']['specimen_class'], ['main_100x100_10000_units'])
        self.assertEqual(route(f, 'ANGLE_IMAGE_VIDEO')['detail']['condition_axes']['specimen_class'], ['video9_150x180_27000_units'])
        self.assertIn('single constant', route(f, 'N_FITS')['detail']['reason'])
        self.assertIs(f['context']['source_outcomes']['universal_acceptance_limits'], False)

    def test_gear_families_counts_and_geometry_remain_scoped(self):
        f = self.families['gear']; families = byid(f['context']['material_cards']['specimen_families'])
        self.assertEqual(len(families), 19)
        for name, shape in [('F_MICRO_TAIJI_BUILD', [5, 6]), ('F_MICRO_TAIJI_COMP', [4, 4]),
                            ('F_MICRO_TAIJI_ACT', [5, 5]), ('F_TAIJI_VIDEO1', [4, 4])]:
            self.assertEqual(families[name]['array_shape'], shape)
            self.assertEqual(families[name]['actual_specimen_ids'], [])
            self.assertIs(families[name]['historical_identity_inferred'], False)
        for r in f['routes'][:18]:
            self.assertIsNone(r['detail']['repeat_count'])
            self.assertIsNone(r['detail']['independent_specimen_count'])
            if r['id'] == 'IMPACT':
                self.assertEqual(r['detail']['conditions']['source_angles_deg'], [0, 7.5, 15, 22.5, 30])
                self.assertNotIn('default', r['detail']['conditions'])
            else:
                self.assertIsNone(r['detail']['conditions']['default'])
            self.assertIs(r['detail']['conditions']['nonempty'], True)
            self.assertIs(r['detail']['condition_transition']['label_only_change_allowed'], False)
        self.assertIn('terminal after each impact', route(f, 'IMPACT')['detail']['destructive_allocation'])
        self.assertEqual(route(f, 'MICRO_TAIJI_ACT')['detail']['motor_configuration']['count'], 4)
        self.assertEqual(route(f, 'MICRO_PLANET_ACT')['detail']['motor_configuration']['count'], 5)
        self.assertEqual(f['context']['source_outcomes']['modulus_error_bars'], 'fit-window variability; not between-specimen SD')
        self.assertTrue(all(c['status'] == 'preserved_unresolved' for c in f['context']['source_conflicts']['conflicts']))

    def test_access_gaps_and_closed_service_ownership(self):
        gear = self.families['gear']; hydro = self.families['hydrogel_optical']
        self.assertIs(gear['context']['source_access_audit']['full_motion_videos_inspected'], False)
        self.assertTrue(all(v['frames_inspected'] == 8 and not v['full_motion_review'] for v in gear['context']['source_access_audit']['videos']))
        audit = hydro['context']['source_access_audit']
        self.assertEqual((audit['extended_data_captions_read'], audit['extended_data_images_inspected']), (4, 0))
        self.assertIs(audit['source_complete_for_entire_paper'], False)
        self.assertIn('accelerated 20 times', audit['video_scope'])
        self.assertIs(hydro['context']['STATUS']['extended_data_images_visually_verified'], False)
        stations = hydro['context']['station_contracts']['stations']
        self.assertEqual(sum(s['closed_service'] for s in stations), 17)
        for s in stations:
            self.assertIs(s['implemented'], False)
            if s['closed_service']: self.assertIn('released_to_handle', s['safe_exchange_readbacks'])
        ops = byid(hydro['operations'])
        for prefix in ('FORM', 'PRINT', 'GEL_CURE', 'CURE', 'THERMAL'):
            self.assertIn('safe-release-to-handle', ' '.join(ops[prefix + '_UNLOAD']['actions']))
            self.assertIn('previous_phase_receipt', ops[prefix + '_READOUT']['pre'])
            self.assertIn('event_authority', ops[prefix + '_HANDOFF']['detail']['required_receipts'])
            self.assertNotEqual(ops[prefix + '_HANDOFF']['actions'], ops[prefix + '_HANDOFF']['detail']['service_process'])
        for f in (gear, hydro): self.assertIs(f['context']['STATUS']['robot_execution_ready'], False)

    def test_all_77_svg_variants_preserve_rows_and_order_boundaries(self):
        count = 0
        for key, f in self.families.items():
            for r in f['routes']:
                candidate = copy.deepcopy(f); candidate['default_route'] = r['id']
                svg = builder.svg(candidate); root = ET.fromstring(svg)
                texts = [x.text or '' for x in root.findall('.//{http://www.w3.org/2000/svg}text')]
                badges = [x.split(' · ', 1)[1].split(' · ', 1)[0] for x in texts if re.match(r'^\d+ · ', x)]
                self.assertEqual([x for x in badges if x in byid(f['operations'])], ids(r['nodes']))
                self.assertIn('0 validated runnable whole-paper tasks', svg)
                if key == 'hydrogel_optical' or r['route_kind'] not in ('physical', 'preparation'):
                    self.assertNotIn('marker-end=', svg)
                elif len(ids(r['nodes'])) > 1: self.assertIn('marker-end=', svg)
                if key == 'hydrogel_optical': self.assertIn('CLOSED QUALIFIED SERVICES ONLY', svg)
                count += 1
        self.assertEqual(count, 77)

    def test_json_javascript_and_pinned_source_links(self):
        for key, f in self.families.items():
            js = (ROOT / 'data' / (key + '.js')).read_text().split('[' + json.dumps(key) + ']=', 1)[1].rsplit(';', 1)[0]
            self.assertEqual(json.loads(js), json.loads((ROOT / 'data' / (key + '.json')).read_text()))
            self.assertEqual(f['source_commit'], SOURCE_COMMIT)
            folder = 'https://github.com/openags/ScienceGym/blob/' + SOURCE_COMMIT + '/tasks/' + key + '_operations_v2/'
            self.assertEqual(f['source_folder'], folder)
            for name, record in f['source_files'].items():
                self.assertEqual(record['url'], folder + name)
                self.assertRegex(record['sha256'], r'^[0-9a-f]{64}$')


@unittest.skipUnless(TASKS, 'SCIENCEGYM_TASKS not set; exact source reconstruction and mutation checks not run')
class NatureMaterialsSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.families = {key: get(key) for key in KEYS}
        cls.adapted = {key: getattr(materials, 'adapt_' + key)(package(key)) for key in KEYS}

    def test_independent_inverse_reconstructs_all_176_operations(self):
        count = 0
        for key, f in self.families.items():
            source = raw(key, 'operations.json')['operations']
            self.assertEqual([o['id'] for o in f['operations']], [o['id'] for o in source])
            for i, (op, original) in enumerate(zip(f['operations'], source)):
                self.assertEqual(inverse_operation(key, op), original, (key, op['id']))
                self.assertEqual((op['source_file'], op['source_pointer']), ('operations.json', '/operations/' + str(i)))
                self.assertEqual(pointer(raw(key, op['source_file']), op['source_pointer']), original)
                count += 1
        self.assertEqual(count, 176)

    def test_all_64_original_json_documents_reconstruct_and_hash_exactly(self):
        count = 0
        for key, f in self.families.items():
            names = {p.relative_to(package(key)).as_posix() for p in package(key).rglob('*.json')}
            self.assertEqual(set(f['source_files']), names)
            reconstructed = {name: copy.deepcopy(f['context'][ALIASES.get(name, name[:-5])])
                             for name in names if name not in ('operations.json', 'branches.json', 'dependencies.json')}
            reconstructed['operations.json'] = {**copy.deepcopy(f['context']['operation_policy']),
                                                'operations': [inverse_operation(key, op) for op in f['operations']]}
            reconstructed['branches.json'] = {**copy.deepcopy(f['context']['branch_policy']),
                                              'branches': [copy.deepcopy(r['detail']) for r in f['routes'] if r['route_kind'] == 'physical']}
            if key == 'gear':
                reconstructed['branches.json']['preparation_routes'] = {
                    r['id']: copy.deepcopy(r['detail']['source_preparation_recipe'])
                    for r in f['routes'] if r['route_kind'] == 'preparation'}
            reconstructed['dependencies.json'] = f['dependencies']
            self.assertEqual(set(reconstructed), names)
            self.assertEqual(set(f['context']), {ALIASES.get(n, n[:-5]) for n in names
                                               if n not in ('operations.json', 'branches.json', 'dependencies.json')} | {'operation_policy', 'branch_policy'})
            for name in sorted(names):
                self.assertEqual(reconstructed[name], raw(key, name), (key, name))
                self.assertEqual(f['source_files'][name]['sha256'], hashlib.sha256((package(key) / name).read_bytes()).hexdigest())
                count += 1
        self.assertEqual(count, 64)

    def test_all_77_routes_and_nested_contracts_resolve_exact_pointers(self):
        count = 0
        for key, f in self.families.items():
            for r in f['routes']:
                expected = pointer(raw(key, r['source_file']), r['source_pointer'])
                actual = r['detail']['source_preparation_recipe'] if r['route_kind'] == 'preparation' else r['detail']
                self.assertEqual(actual, expected, (key, r['id']))
                for n in nodes(r):
                    meta = n.get('meta', {})
                    for field in ('source_node', 'source_contract'):
                        if field in meta:
                            self.assertEqual(meta[field], pointer(raw(key, meta['source_file']), meta['source_pointer']), (key, r['id']))
                count += 1
        self.assertEqual(count, 77)

    def test_gear_ordered_recipe_occurrences_and_transfer_destinations(self):
        f = self.families['gear']; document = raw('gear', 'branches.json')
        recipes = [(r['id'], r['per_condition_operations']) for r in document['branches']]
        recipes.extend(document['preparation_routes'].items())
        transfer_count = 0
        for identifier, entries in recipes:
            r = route(f, identifier); shown = [n for n in nodes(r) if n['type'] == 'op']
            self.assertEqual(ids(r['nodes']), [e['op_id'] for e in entries], identifier)
            self.assertEqual([n['meta']['source_node'] for n in shown], entries, identifier)
            self.assertEqual(len({n['meta']['source_pointer'] for n in shown}), len(entries))
            for entry, node in zip(entries, shown):
                if entry['op_id'] == 'TRANSFER':
                    self.assertEqual(node['meta']['source_node']['destination_station'], entry['destination_station'])
                    transfer_count += 1
        self.assertGreater(transfer_count, 50)
        self.assertEqual(collections.Counter(ids(route(f, 'TAIJI_PLUS')['nodes']))['TRANSFER'], 3)
        self.assertEqual(f['dependencies']['occurrence_key_fields'], raw('gear', 'dependencies.json')['occurrence_key_fields'])

    def test_gear_numerical_namespaces_analysis_parents_and_controls(self):
        f = self.families['gear']; nonmanual = raw('gear', 'nonmanual_scope.json')
        for original in nonmanual['numerical_branches']:
            self.assertEqual(ids(route(f, original['id'])['nodes']), original['operation_ids'])
            self.assertIs(original['executed'], False)
        for original in raw('gear', 'dependencies.json')['analysis_dependencies']:
            r = route(f, original['id'])
            contracts = [n['meta']['source_contract'] for n in nodes(r)
                         if n.get('meta', {}).get('source_file') == 'dependencies.json']
            self.assertEqual(contracts, [original])
        for original in raw('gear', 'branches.json')['branches']:
            expected = [c for c in raw('gear', 'control_packages.json')['packages'] if original['id'] in c['required_branch_ids']]
            self.assertEqual(route(f, original['id'])['controls'], expected)

    def test_hydro_memberships_service_phase_only_and_all_control_scope(self):
        f = self.families['hydrogel_optical']; deps = raw('hydrogel_optical', 'dependencies.json')
        controls = raw('hydrogel_optical', 'control_packages.json')['controls']
        for original in raw('hydrogel_optical', 'branches.json')['branches']:
            r = route(f, original['id'])
            self.assertEqual(ids(r['nodes']), original['operation_ids'])
            self.assertIs(r['nodes'][0]['ordered'], False)
            self.assertEqual(r['nodes'][0]['meta']['order'], original['operation_list_semantics'])
            self.assertEqual(r['controls'], [c for c in controls if c['scope'] in ('all', original['id'])])
            self.assertEqual([n['meta']['source_contract'] for n in nodes(r)
                              if n.get('meta', {}).get('source_file') == 'dependencies.json'], [deps['service_phase_order']])
            for field in ('condition_axes', 'source_cycles', 'source_independent_specimens'):
                self.assertEqual([n['meta']['source_contract'] for n in nodes(r)
                                  if n.get('meta', {}).get('source_pointer', '').endswith('/' + field)], [original[field]])
        self.assertEqual(f['dependencies'], deps)
        self.assertEqual(route(f, 'THREE_D')['detail']['service_ids'], ['SEM', 'CONFOCAL'])
        self.assertEqual(route(f, 'ANGLE_IMAGE_MAIN')['detail']['service_ids'], ['THERMAL', 'POLAR'])

    def test_full_provenance_and_fresh_projection_equal_bundle(self):
        for key, f in self.families.items():
            evidence = raw(key, 'provenance.json')['evidence']
            self.assertEqual(f['evidence'], byid(evidence) if isinstance(evidence, list) else evidence)
            self.assertEqual({k: v for k, v in f.items() if k != 'shared'}, self.adapted[key])
            self.assertEqual(materials.projection(package(key), key), self.adapted[key])
            self.assertTrue(materials.validate_projection(self.adapted[key], package(key)))

    def reject(self, key, mutation):
        candidate = copy.deepcopy(self.adapted[key]); mutation(candidate)
        with self.assertRaises(ValueError): materials.validate_projection(candidate, package(key))

    def test_reject_named_common_payload_context_pointer_and_runtime_mutations(self):
        mutations = {
            'action_changed': lambda f: f['operations'][0]['actions'].append('invented execution'),
            'authorship_promoted': lambda f: f['operations'][0].__setitem__('provenance', 'source-reported robot procedure'),
            'operation_field_lost': lambda f: f['operations'][0]['detail'].pop('actor'),
            'recovery_scalar_lost': lambda f: f['operations'][0].__setitem__('recovery', []),
            'pointer_wrong': lambda f: f['operations'][0].__setitem__('source_pointer', '/operations/1'),
            'route_pointer_wrong': lambda f: f['routes'][0].__setitem__('source_pointer', '/branches/1'),
            'context_missing': lambda f: f['context'].pop('source_conflicts'),
            'service_context_missing': lambda f: f['context'].pop('station_contracts'),
            'access_metadata_lost': lambda f: f['context'].pop('source_access_audit'),
            'lineage_lost': lambda f: f['context']['lineage'].clear(),
            'evidence_lost': lambda f: f['evidence'].clear(),
            'controls_lost': lambda f: next(r for r in f['routes'] if r.get('controls'))['controls'].pop(),
            'source_file_missing': lambda f: f['source_files'].pop('provenance.json'),
            'source_pin_changed': lambda f: f.__setitem__('source_commit', '0' * 40),
            'source_hash_changed': lambda f: f['source_files']['operations.json'].__setitem__('sha256', '0' * 64),
            'source_link_unpinned': lambda f: f['source_files']['operations.json'].__setitem__('url', 'https://example.invalid/main'),
            'actor_visibility': lambda f: f.__setitem__('visibility', 'actor_runtime'),
            'actor_implemented': lambda f: f.__setitem__('actor_projection_implemented', True),
            'fabricated_receipt': lambda f: f['context'].__setitem__('execution_receipt', {'success': True}),
            'readiness_promoted': lambda f: f['context']['STATUS'].__setitem__('robot_execution_ready', True)}
        for key in KEYS:
            for label, mutation in mutations.items():
                with self.subTest(key=key, mutation=label): self.reject(key, mutation)

    def test_reject_named_gear_order_allocation_namespace_geometry_mutations(self):
        mutations = {
            'occurrence_dropped': lambda f: f['routes'][0]['nodes'].pop(2),
            'recipe_reordered': lambda f: f['routes'][0]['nodes'].reverse(),
            'destination_changed': lambda f: f['routes'][0]['nodes'][2]['meta']['source_node'].__setitem__('destination_station', 'WS_CLEAN'),
            'prep_recipe_lost': lambda f: route(f, 'PREP_TAIJI')['detail']['source_preparation_recipe'].pop(),
            'repeat_defaulted': lambda f: f['routes'][0]['detail'].__setitem__('repeat_count', 1),
            'independent_count_invented': lambda f: f['routes'][0]['detail'].__setitem__('independent_specimen_count', 1),
            'empty_conditions_allowed': lambda f: f['routes'][0]['detail']['conditions'].__setitem__('nonempty', False),
            'terminal_impact_reused': lambda f: route(f, 'IMPACT')['detail'].__setitem__('destructive_allocation', 'reuse for next impact'),
            'numerical_physical_substitution': lambda f: route(f, 'N_CONTACT')['nodes'][0]['children'].__setitem__(0, 'LOAD_CYCLE'),
            'numerical_order_invented': lambda f: route(f, 'N_CONTACT')['nodes'][0].__setitem__('ordered', True),
            'analysis_parent_changed': lambda f: f['dependencies']['analysis_dependencies'][0].__setitem__('requires_branch_ids', ['N_CONTACT']),
            'analysis_controls_lost': lambda f: f['dependencies']['analysis_dependencies'][1]['requires_control_package_ids'].pop(),
            'illustration_promoted': lambda f: route(f, 'I_MACRO_VIDEO').__setitem__('route_kind', 'physical'),
            'micro_families_merged': lambda f: byid(f['context']['material_cards']['specimen_families'])['F_MICRO_TAIJI_BUILD'].__setitem__('array_shape', [4, 4]),
            'geometry_conflict_fixed': lambda f: f['context']['source_conflicts']['conflicts'][0].__setitem__('status', 'resolved'),
            'full_motion_invented': lambda f: f['context']['source_access_audit'].__setitem__('full_motion_videos_inspected', True),
            'fit_variability_as_replicates': lambda f: f['context']['source_outcomes'].__setitem__('modulus_error_bars', 'independent specimen SD'),
            'service_ownership_lost': lambda f: f['operations'][0]['detail'].pop('ownership')}
        for label, mutation in mutations.items():
            with self.subTest(mutation=label): self.reject('gear', mutation)

    def test_reject_named_hydro_scope_service_counts_missingness_access_mutations(self):
        mutations = {
            'membership_dropped': lambda f: f['routes'][0]['nodes'][0]['children'].pop(),
            'membership_reordered': lambda f: f['routes'][0]['nodes'][0]['children'].reverse(),
            'chronology_invented': lambda f: f['routes'][0]['nodes'][0].__setitem__('ordered', True),
            'phase_order_changed': lambda f: f['dependencies']['service_phase_order'].reverse(),
            'branch_dependency_lost': lambda f: f['dependencies']['branch_edges'].pop(),
            'global_control_lost': lambda f: f['routes'][0].__setitem__('controls', []),
            'global_control_narrowed': lambda f: byid(f['context']['control_packages']['controls'])['CTRL_BASELINE'].__setitem__('scope', 'BEAM_POWER'),
            'cycle_to_independent_count': lambda f: route(f, 'LATTICE_CYCLES')['detail'].__setitem__('source_independent_specimens', 27),
            'cycle_lineages_merged': lambda f: route(f, 'IMAGE_CYCLES')['detail'].__setitem__('source_cycles', 27),
            'condition_axes_lost': lambda f: route(f, 'BEAM_POWER')['detail']['condition_axes'].clear(),
            'image_lineages_merged': lambda f: route(f, 'ANGLE_IMAGE_VIDEO')['detail']['condition_axes'].__setitem__('specimen_class', ['main_100x100_10000_units']),
            'derived_fit_acquisition': lambda f: route(f, 'N_FITS')['nodes'].append('THERMAL_READOUT'),
            'reference_execution_promoted': lambda f: route(f, 'N_FEA')['detail'].__setitem__('executed', True),
            'service_opened': lambda f: byid(f['context']['station_contracts']['stations'])['WS_FORM'].__setitem__('closed_service', False),
            'safe_release_removed': lambda f: byid(f['context']['station_contracts']['stations'])['WS_THERMAL']['safe_exchange_readbacks'].remove('released_to_handle'),
            'service_process_lost': lambda f: byid(f['operations'])['FORM_HANDOFF']['detail'].__setitem__('service_process', ''),
            'receipt_authority_lost': lambda f: byid(f['operations'])['FORM_READOUT']['detail']['required_receipts'].remove('event_authority'),
            'source_completion_promoted': lambda f: f['context']['source_access_audit'].__setitem__('source_complete_for_entire_paper', True),
            'uninspected_images_promoted': lambda f: f['context']['source_access_audit'].__setitem__('extended_data_images_inspected', 4),
            'video_speed_lost': lambda f: f['context']['source_access_audit'].__setitem__('video_scope', 'full-motion real-time review'),
            'missingness_silently_repaired': lambda f: byid(f['context']['source_conflicts']['conflicts'])['C8'].__setitem__('required_behavior', 'Replace absent samples with zero'),
            'conflict_correction_allowed': lambda f: f['context']['source_conflicts']['conflicts'][0].__setitem__('source_silent_correction_allowed', True)}
        for label, mutation in mutations.items():
            with self.subTest(mutation=label): self.reject('hydrogel_optical', mutation)


if __name__ == '__main__': unittest.main()
