"""Independent source and display-boundary tests for the two recent papers.

Expected counts, mappings and scientific distinctions below are independently
read from the task contracts, rather than imported from adapter constants.
These checks inspect static projections; they execute no scientific services.
"""
import collections
import copy
import hashlib
import json
import re
import unittest
import xml.etree.ElementTree as ET

from test_semantics import ROOT, TASKS, builder, get, ids
import recent_paper_adapters as recent

KEYS = ('lockable_origami', 'varactor')
# operations, source branches, inspection views, source JSON, evidence, groups,
# anchors, synthetic fixtures, source conflicts, unresolved groups, controls
EXPECTED = {
    'lockable_origami': (60, 30, 34, 32, 110, 11, 53, 143, 11, 9, 8),
    'varactor': (80, 28, 29, 34, 49, 12, 65, 160, 12, 18, 6),
}
CLASSES = {
    'lockable_origami': {'closed_service': 16, 'external_model_metadata': 12,
                        'design_only': 1, 'source_only_gated': 1},
    'varactor': {'closed_service': 21, 'external_model_metadata': 5,
                'source_context_metadata': 2},
}
KINDS = {'closed_service': 'closed_service', 'external_model_metadata': 'numerical',
         'design_only': 'design_only', 'source_only_gated': 'source_hold',
         'source_context_metadata': 'source_context'}
ALIASES = {'unknown_parameters.json': 'unknowns', 'evaluator_reference.json': 'acceptance',
           'lineage_contract.json': 'lineage'}
PREVIOUS_GENERATED_SHA256 = '74a34abfc1cc1c6b22763a8c7dea3e86ca796facece7348dabd7cb2401a6c7e6'


def package(key): return TASKS / (key + '_operations_v2')
def raw(key, name): return json.loads((package(key) / name).read_text())
def byid(records): return {r['id']: r for r in records}
def route(f, identifier): return byid(f['routes'])[identifier]
def context_key(name): return ALIASES.get(name, name.removesuffix('.json'))
def pointer(document, path):
    for token in path.split('/')[1:]:
        token = token.replace('~1', '/').replace('~0', '~')
        document = document[int(token)] if isinstance(document, list) else document[token]
    return document


class RecentPaperBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.families = {key: get(key) for key in KEYS}

    def test_independently_counted_inventories(self):
        for key, f in self.families.items():
            ops, branches, views, documents, evidence, groups, anchors, fixtures, conflicts, unknowns, controls = EXPECTED[key]
            self.assertEqual((len(f['operations']), len(f['routes']), len(f['source_files']), len(f['evidence'])),
                             (ops, views, documents, evidence))
            self.assertEqual(len(byid(f['routes'])), views)
            self.assertEqual(collections.Counter(b['execution_class'] for b in f['context']['branches']['branches']), CLASSES[key])
            expected = dict(zip(('source_branches', 'source_json_documents', 'source_evidence_entries',
                                 'scene_groups', 'symbolic_anchors', 'synthetic_configurations',
                                 'source_conflicts', 'unresolved_input_groups', 'control_records'),
                                (branches, documents, evidence, groups, anchors, fixtures, conflicts, unknowns, controls)))
            for field, value in expected.items(): self.assertEqual(f['summary_counts'][field], value, (key, field))

    def test_previous_33_family_generated_bytes_are_preserved(self):
        files = sorted(p for directory in ('data', 'docs', 'diagrams')
                       for p in (ROOT / directory).glob('*') if p.is_file()
                       and p.stem not in ('ADAPTERS', 'wetting', 'arcmorph', 'midinfrared', 'conformal', 'scattering', 'qha', 'thermalmeta', 'microsphere') + KEYS)
        self.assertEqual(len(files), 132)
        digest = hashlib.sha256()
        for path in files:
            digest.update(path.relative_to(ROOT).as_posix().encode() + b'\0' + path.read_bytes() + b'\0')
        self.assertEqual(digest.hexdigest(), PREVIOUS_GENERATED_SHA256)

    def test_default_and_global_holds_are_separate_inspection_records(self):
        for key, f in self.families.items():
            branches = byid(f['context']['branches']['branches'])
            self.assertEqual(f['default_route'], 'HOLD_QUALIFICATION')
            self.assertNotIn(f['default_route'], branches)
            default = route(f, f['default_route'])
            self.assertEqual(default['route_kind'], 'qualification_hold')
            self.assertEqual(ids(default['nodes']), ['HOLD_QUALIFICATION'])
            self.assertEqual(default['detail'], f['context']['episode_input_contract'])
            self.assertIn('does not add a scientific branch', f['default_route_basis'])
        origami = self.families['lockable_origami']
        extra = {r['id'] for r in origami['routes'] if r['route_kind'] == 'conditional_recovery'}
        self.assertEqual(extra, {'HOLD_CALIBRATION', 'HOLD_CONFIGURATION', 'HOLD_GEOMETRY'})
        for identifier in extra:
            self.assertEqual(ids(route(origami, identifier)['nodes']), [identifier])
            self.assertEqual(route(origami, identifier)['detail']['branch_ids'], [])
        self.assertEqual(len(self.families['varactor']['routes']), 28 + 1)

    def test_operation_membership_has_no_invented_chronology_or_instances(self):
        for f in self.families.values():
            for branch in f['context']['branches']['branches']:
                r = route(f, branch['id'])
                self.assertEqual(r['detail'], branch)
                self.assertEqual(r['route_kind'], KINDS[branch['execution_class']])
                self.assertEqual(ids(r['nodes']), branch['operation_ids'])
                self.assertEqual(len(ids(r['nodes'])), len(set(ids(r['nodes']))))
                self.assertEqual(r['nodes'][0]['type'], 'obligations')
                self.assertIs(r['nodes'][0]['ordered'], False)
                self.assertIn('conditional', r['nodes'][0]['label'].lower())
                self.assertIn('Membership', branch['operation_ids_semantics'])
                self.assertIn('repeated occurrence', branch['operation_ids_semantics'])
                for node, _ in builder.walk(r['nodes']):
                    if node['type'] != 'op': self.assertIs(node['ordered'], False)
                    if node['type'] == 'condition': self.assertEqual(node['children'], [])
            visible = {oid for r in f['routes'] for oid in ids(r['nodes'])}
            self.assertEqual(visible, set(byid(f['operations'])))

    def test_design_classes_and_conditional_recovery_never_mean_execution(self):
        for f in self.families.values():
            self.assertEqual(f['family_scope'], 'paper_level_design')
            self.assertEqual(f['visibility'], 'author_evaluator_reference_only')
            self.assertIs(f['actor_projection_implemented'], False)
            self.assertNotIn('actor_payload', f)
            self.assertNotIn('execution_receipt', f)
            self.assertIn('Holds and quarantine remain conditional', f['status'])
            self.assertIn('Requests do not establish observations', f['status'])
            for r in f['routes']:
                self.assertIn('no new experiment', r['navigation_basis'])
                if r['source_file'] == 'branches.json':
                    self.assertIs(r['detail']['design_covered'], True)
                    self.assertIs(r['detail']['physical_executed'], False)
                    self.assertIs(r['detail']['numerical_executed'], False)
            boundary = f['context']['RELEASE_BOUNDARY']
            self.assertEqual(boundary['validated_runnable_whole_paper_tasks'], 0)
            for field in ('whole_paper_execution_complete', 'physical_execution', 'numerical_execution',
                          'scientific_reproduction', 'source_files_exported', 'exact_geometry_validated'):
                self.assertIs(boundary[field], False, field)
            agent = f['context']['agent_visible']
            for field in ('source_outcomes_exposed', 'can_declare_measurement',
                          'can_declare_service_qualification', 'can_supply_physical_observation', 'physical_implementation'):
                self.assertIs(agent[field], False)
            self.assertEqual(f['context']['episode_input_contract']['actor_event_fields'],
                             ['event_id', 'operation_id', 'evidence_id'])

    def test_authored_operations_are_not_source_actions_or_observations(self):
        for f in self.families.values():
            for operation in f['operations']:
                original = operation['detail']
                self.assertEqual(operation['provenance'], 'original_authored_contract')
                self.assertEqual(operation['actions'], [original['action']])
                self.assertEqual(operation['pre'], original['precondition'])
                self.assertEqual(operation['acceptance'], original['required_output'])
                self.assertEqual(operation['objects'], original['asset_ids'])
                self.assertEqual(operation['sources'], original['source_evidence_ids'])
                self.assertEqual(operation['recovery'], {'failure': original['failure'], 'recovery': original['recovery']})
                self.assertIn('No post-state field supplied', operation['post'])
                self.assertNotEqual(operation['post'], operation['acceptance'])
                self.assertIs(original['physical_execution_authority'], False)
                self.assertIs(original['device_command_implemented'], False)
                self.assertIn('authored symbolic task action', operation['display_action_ownership'])

    def test_source_evidence_references_and_asset_bindings_resolve(self):
        for f in self.families.values():
            evidence = set(f['evidence'])
            self.assertEqual(f['evidence'], byid(f['context']['evidence_map']['evidence']))
            assets = {a['asset_id']: a for a in f['context']['asset_binding_plan']['scene_assets']}
            bound = [oid for a in assets.values() for oid in a['bind_operation_ids']]
            self.assertEqual(collections.Counter(bound), collections.Counter(o['id'] for o in f['operations']))
            for operation in f['operations']:
                self.assertLessEqual(set(operation['sources']), evidence)
                for asset_id in operation['objects']:
                    self.assertIn(operation['id'], assets[asset_id]['bind_operation_ids'])
            for branch in f['context']['branches']['branches']:
                self.assertLessEqual(set(branch['source_evidence_ids']), evidence)

    def test_origami_independent_specimens_and_cycle_counts_stay_distinct(self):
        context = self.families['lockable_origami']['context']
        parameters = byid(context['source_parameters']['parameters'])
        self.assertEqual(parameters['P_COUNTS']['facts'], {
            'main_compression_curve_independent_samples': 3, 'density_per_scale_independent_samples': 5,
            'finite_size_per_geometry_independent_samples': 5, 'N4_reported_cycles': 10, 'N6_reported_cycles': 4})
        self.assertEqual(parameters['P_FINITE_GRID']['facts']['planar_tessellation_grid'],
                         [[1, 1], [3, 3], [5, 5], [7, 7], [9, 9]])
        self.assertEqual(parameters['P_FINITE_GRID']['facts']['N4_stack_layer_grid'], [1, 2, 4, 6, 8])
        self.assertEqual((parameters['P_COUPON']['facts']['crosshead_gauge_mm'],
                          parameters['P_COUPON']['facts']['dic_gauge_mm']), (180, 20))
        self.assertIn('U_REPEATS', byid(context['unknowns']['gates']))
        self.assertTrue(all(g['status'] == 'OPEN' and 'default' not in g for g in context['unknowns']['gates']))

    def test_origami_open_path_work_mixed_denominators_and_causal_reference(self):
        f = self.families['lockable_origami']; analysis = f['context']['analysis_contracts']
        self.assertIn('signed open-path work', f['source_warnings'])
        self.assertNotIn('signed closed-cycle loss', f['source_warnings'])
        self.assertIn('Measured open-path work differs from closed-loop hysteretic loss', analysis['cyclic'])
        self.assertIn('No forced closure for paperboard permanent set', analysis['cyclic'])
        self.assertIn('Independent first-cycle peak reference fixed before requests; no future-value leakage', analysis['cyclic'])
        self.assertIn('Yield is first qualified peak before densification, not global maximum', analysis['mechanical'])
        self.assertIn('Use configuration 1 modulus and configuration 4 positive channel-area denominator separately', analysis['mixed'])
        self.assertIn('No flow-permeability estimate from area alone', analysis['mixed'])

    def test_origami_coupon_preparation_is_not_folded_or_bonded(self):
        f = self.families['lockable_origami']
        members = ids(route(f, 'BASE_MATERIAL_TENSION')['nodes'])
        self.assertIn('REQUEST_CUT', members)
        for absent in ('REQUEST_FOLD', 'VERIFY_FOLD', 'REQUEST_STACK_BOND', 'VERIFY_STACK_BOND', 'VERIFY_CURE'):
            self.assertNotIn(absent, members)
        prepared = byid(f['context']['preparation_routes']['routes'])['PREPARED']
        self.assertIs(prepared['preparation_credit'], False)
        self.assertIn('cannot reuse yielded/cycled specimens', f['context']['preparation_routes']['destructive_allocation'])

    def test_varactor_stable_specimens_changed_revisions_and_circuit_families(self):
        f = self.families['varactor']; context = f['context']
        shared = context['shared_specimen_contract']
        self.assertIs(shared['same_physical_varactor_pair'], True)
        self.assertEqual(shared['required_stable_fields'], ['varactor_ids', 'material', 'prior_sweep_history'])
        self.assertEqual(shared['required_changed_fields'],
                         ['quantum_device_id', 'module_revision', 'circuit_revision', 'calibration_revision'])
        cards = byid(context['circuit_family_cards']['cards'])
        self.assertEqual(set(cards), {'FIXED_LOAD', 'SQD', 'DQD'})
        self.assertEqual(cards['SQD']['model_inductor_nH'], 320)
        self.assertEqual(cards['SQD']['inductor_part_code'], '0805CS-331')
        self.assertTrue(all(c['manufacturer_nominal_inductor_nH'] is None for c in cards.values()))
        self.assertIn('0805CS-331', f['source_warnings'])
        self.assertNotIn('330 nH component label', f['source_warnings'])
        self.assertNotEqual(cards['SQD']['bias_tee'], cards['DQD']['bias_tee'])
        self.assertEqual(cards['DQD']['matching_series_capacitor_pF'], 20)
        self.assertIsNone(cards['SQD']['matching_series_capacitor_pF'])
        self.assertIs(cards['DQD']['JPA_incorporated'], True)
        self.assertIs(cards['SQD']['JPA_incorporated'], False)
        materials = byid(context['material_cards']['cards'])
        self.assertNotEqual(materials['STO']['termination'], materials['KTO']['termination'])
        self.assertEqual(materials['KTO']['termination'], 'Unspecified')

    def test_varactor_model_measurement_and_counting_limits(self):
        f = self.families['varactor']; context = f['context']
        parameters = byid(context['source_parameters']['parameters'])
        self.assertEqual(parameters['P_THERMAL']['facts'],
                         {'source_lattice_base_mK': 6, 'source_electron_temperature_mK': 12})
        self.assertIn('no guarantee of exact endpoint count or stationarity', parameters['P_STABILITY']['scope'])
        self.assertIn('points, repeated sweeps and times are not independent devices', context['control_packages']['source_repeats'])
        self.assertIn('No intrinsic-loss attribution', context['analysis_contracts']['required_conventions'])
        for identifier in ('DUAL_FREQUENCY_MATCHING', 'MAGNETIC_FIELD_RESPONSE'):
            members = ids(route(f, identifier)['nodes'])
            self.assertNotIn('ANALYZE_SQD_SENSITIVITY', members)
            self.assertEqual(route(f, identifier)['detail']['acquisition_mode'],
                             'SQD-circuit complex reflection and phase; no sideband/charge-sensitivity credit for these scans')
        # The shared generic readout operation is deliberately in the magnetic
        # route; its presence must not erase that branch's narrower acquisition.
        self.assertIn('REQUEST_SQD_READOUT', ids(route(f, 'MAGNETIC_FIELD_RESPONSE')['nodes']))
        self.assertNotIn('REQUEST_SQD_READOUT', ids(route(f, 'DUAL_FREQUENCY_MATCHING')['nodes']))
        self.assertEqual(route(f, 'READOUT_SCALING_PROJECTION')['route_kind'], 'source_context')
        self.assertEqual(route(f, 'REFLECTION_CIRCUIT_FIT')['route_kind'], 'numerical')
        self.assertEqual(byid(context['preparation_routes']['routes'])['PREPARED']['credit'], 'No fabrication credit')

    def test_source_access_limits_are_retained(self):
        audit = self.families['lockable_origami']['context']['source_access_audit']
        self.assertEqual(audit['si_read']['pdf_pages'], 37)
        self.assertEqual(audit['movie_read']['visual_samples_each'], 6)
        self.assertEqual(audit['movie_read']['movies_visually_sampled'], list(range(1, 13)))
        self.assertIs(audit['movie_read']['continuous_playback'], False)
        self.assertEqual(audit['movie_read']['numerical_movies'], list(range(4, 11)))
        self.assertIs(audit['peer_review']['read'], False)
        self.assertIs(audit['peer_review']['authority_for_final_science'], False)
        self.assertTrue(all(s['export'] is False for s in audit['source_files']))
        audit = self.families['varactor']['context']['source_access_audit']
        self.assertIn('main PDF not fetched', audit['main_read']['format'])
        self.assertEqual(audit['si_read']['pdf_pages'], 6)
        self.assertEqual(audit['si_read']['sections'], ['I', 'II', 'III', 'IV'])
        self.assertIn('Cannot establish that an unprovided Section V never existed', audit['limits'])
        self.assertIn('not downloaded or executed', audit['raw_data_access'])
        self.assertEqual(audit['author_code_access'], 'Not ingested')
        self.assertEqual(audit['exact_CAD_access'], 'Not provided')

    def test_json_javascript_relative_links_and_no_false_publication_claim(self):
        for key, f in self.families.items():
            payload = (ROOT / 'data' / (key + '.js')).read_text().split('[' + json.dumps(key) + ']=', 1)[1].rsplit(';', 1)[0]
            self.assertEqual(json.loads(payload), json.loads((ROOT / 'data' / (key + '.json')).read_text()))
            self.assertEqual(f['source_folder'], '../../tasks/' + key + '_operations_v2/')
            self.assertEqual(f['source_link_mode'], 'repository_relative_frozen_local_snapshot')
            self.assertIn('remote publication is not asserted', f['source_publication'])
            for name, record in f['source_files'].items():
                self.assertEqual(record['url'], f['source_folder'] + name)
                self.assertEqual(record['repository_path'], 'tasks/' + key + '_operations_v2/' + name)
                self.assertRegex(record['sha256'], r'^[0-9a-f]{64}$')

    def test_every_route_svg_has_no_causal_arrows_or_execution_credit(self):
        count = 0
        for f in self.families.values():
            for r in f['routes']:
                candidate = copy.deepcopy(f); candidate['default_route'] = r['id']
                svg = builder.svg(candidate)
                root = ET.fromstring(svg)
                texts = [n.text or '' for n in root.findall('.//{http://www.w3.org/2000/svg}text')]
                badges = [t.split(' · ', 1)[1] for t in texts if re.match(r'^\d+ · ', t)]
                self.assertEqual([b for b in badges if b in byid(f['operations'])], ids(r['nodes']))
                self.assertNotIn('marker-end=', svg)
                self.assertIn('0 validated runnable whole-paper tasks', svg)
                self.assertIn('no physical or numerical execution', svg)
                self.assertIn('Hold defaults', svg)
                count += 1
        self.assertEqual(count, 63)


@unittest.skipUnless(TASKS, 'SCIENCEGYM_TASKS not set; source comparisons not run')
class RecentPaperSourceTests(unittest.TestCase):
    def test_all_source_json_contexts_are_exact(self):
        for key in KEYS:
            f = get(key); p = package(key)
            expected = {x.relative_to(p).as_posix() for x in p.rglob('*.json')}
            self.assertEqual(set(f['source_files']), expected)
            for name in expected:
                # JSON serialization also distinguishes booleans from integers;
                # Python container equality alone would accept False == 0.
                self.assertEqual(json.dumps(f['context'][context_key(name)], sort_keys=True, allow_nan=False),
                                 json.dumps(raw(key, name), sort_keys=True, allow_nan=False), (key, name))
                self.assertEqual(f['source_files'][name]['sha256'], hashlib.sha256((p / name).read_bytes()).hexdigest())
            for name in ('dependencies', 'preparation_routes', 'lifecycle_contract', 'transport_routes'):
                self.assertEqual(f['dependencies'][name], raw(key, name + '.json'))

    def test_every_operation_and_route_retains_exact_source_pointer(self):
        for key in KEYS:
            f = get(key)
            self.assertEqual([o['detail'] for o in f['operations']], raw(key, 'operations.json')['operations'])
            for record in f['operations'] + f['routes']:
                self.assertEqual(record['detail'], pointer(raw(key, record['source_file']), record['source_pointer']))
            for r in f['routes']:
                for node, _ in builder.walk(r['nodes']):
                    metadata = node.get('meta', {})
                    if 'source_contract' in metadata:
                        self.assertEqual(metadata['source_contract'], pointer(raw(key, metadata['source_file']), metadata['source_pointer']))

    def test_scene_ids_anchors_and_operation_bindings_match_immutable_snapshots(self):
        for key in KEYS:
            f = get(key); plan = f['context']['asset_binding_plan']
            ap = TASKS.parent / 'assets' / (key + '_scene_assets_v1')
            snapshot = json.loads((ap / 'task_binding_snapshot.json').read_text())
            bindings = json.loads((ap / 'operation_bindings.json').read_text())
            affordances = json.loads((ap / 'affordances.json').read_text())
            self.assertEqual(plan['binding_status'], 'STATIC_SCENE_BOUND')
            self.assertNotEqual(plan['binding_status'], snapshot['binding_status'])
            before = {a['asset_id']: a for a in snapshot['scene_assets']}
            anchors = {(a['asset_id'], a['anchor_id']) for a in affordances['anchors']}
            for asset in plan['scene_assets']:
                self.assertIs(asset['asset_available'], True)
                self.assertIs(before[asset['asset_id']]['asset_available'], False)
                self.assertIs(asset['physical_geometry_validated'], False)
                for field in ('required_anchor_ids', 'bind_operation_ids', 'role'):
                    self.assertEqual(asset[field], before[asset['asset_id']][field])
                self.assertTrue(all((asset['asset_id'], a) in anchors for a in asset['required_anchor_ids']))
            self.assertEqual(collections.Counter(b['operation_id'] for b in bindings['bindings']),
                             collections.Counter(o['id'] for o in f['operations']))
            self.assertIs(bindings['does_not_implement_task_services'], True)
            for binding in bindings['bindings']:
                for field in ('physical_execution', 'energy_enabled', 'source_geometry_validated', 'request_is_observation'):
                    self.assertIs(binding[field], False)
                self.assertIsNone(binding['qualified_transform'])

    def test_asset_links_and_hashes_resolve_to_existing_static_artifacts(self):
        for key in KEYS:
            f = get(key)
            self.assertEqual(len(f['asset_links']), 4)
            for link in f['asset_links']:
                path = TASKS.parent / link['path']
                self.assertTrue(path.is_file())
                self.assertEqual(link['url'], '../../' + link['path'])
                self.assertEqual(link['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_unpooled_projection_rebuild_matches_generated_bundle(self):
        for key in KEYS:
            f = recent.projection(package(key), key)
            self.assertTrue(recent.validate_projection(f, package(key)))
            self.assertEqual(f, {k: v for k, v in get(key).items() if k != 'shared'})

    def reject(self, key, mutation):
        f = recent.projection(package(key), key); mutation(f)
        with self.assertRaises(ValueError): recent.validate_projection(f, package(key))

    def test_reject_branch_loss_extra_operation_or_invented_chronology(self):
        for key in KEYS:
            self.reject(key, lambda f: f['routes'].pop(0))
            self.reject(key, lambda f: f['routes'][0]['nodes'][0].__setitem__('ordered', True))
            self.reject(key, lambda f: f['routes'][0]['nodes'][0]['children'].append('HOLD_QUALIFICATION'))
            self.reject(key, lambda f: f['routes'][0]['nodes'][0]['children'].pop())

    def test_reject_default_or_global_hold_loss_and_conditional_promotion(self):
        for key in KEYS:
            self.reject(key, lambda f: f.__setitem__('default_route', f['routes'][0]['id']))
            self.reject(key, lambda f: route(f, 'HOLD_QUALIFICATION').__setitem__('route_kind', 'closed_service'))
        self.reject('lockable_origami', lambda f: f['routes'].remove(route(f, 'HOLD_CONFIGURATION')))
        self.reject('lockable_origami', lambda f: route(f, 'FULL_FABRICATION')['nodes'][0].__setitem__('label', 'Required successful trajectory'))

    def test_reject_execution_authority_actor_payload_and_provenance_rewrite(self):
        for key in KEYS:
            self.reject(key, lambda f: f.__setitem__('actor_projection_implemented', True))
            self.reject(key, lambda f: f.__setitem__('actor_payload', f['context']['source_outcomes']))
            self.reject(key, lambda f: f.__setitem__('execution_receipt', {'success': True}))
            self.reject(key, lambda f: f['operations'][0].__setitem__('provenance', 'source_reported_robot_action'))
            self.reject(key, lambda f: f['operations'][0].__setitem__('post', f['operations'][0]['acceptance']))
            self.reject(key, lambda f: f['operations'][0]['detail'].__setitem__('physical_execution_authority', True))

    def test_reject_unknown_default_source_scope_or_immutable_receipt_edits(self):
        self.reject('lockable_origami', lambda f: f['context']['unknowns']['gates'][0].__setitem__('default', 1))
        self.reject('varactor', lambda f: f['context']['unknowns']['unknowns'][0].__setitem__('default', 1))
        self.reject('lockable_origami', lambda f: f['context']['source_access_audit']['movie_read'].__setitem__('continuous_playback', True))
        self.reject('varactor', lambda f: f['context']['source_access_audit']['si_read']['sections'].append('V'))
        for key in KEYS:
            self.reject(key, lambda f: f['context']['VERIFICATION'].__setitem__('physical_execution', True))
            self.reject(key, lambda f: f['context']['RELEASE_BOUNDARY'].__setitem__('physical_execution', 0))
            self.reject(key, lambda f: f['context']['review/INDEPENDENT_REVIEW'].__setitem__('status', 'PASSED_EXECUTION'))

    def test_reject_scientific_distinction_collapses(self):
        self.reject('lockable_origami', lambda f: byid(f['context']['source_parameters']['parameters'])['P_COUPON']['facts'].__setitem__('dic_gauge_mm', 180))
        self.reject('lockable_origami', lambda f: f['context']['analysis_contracts']['cyclic'].__setitem__(1, 'Measured closed-loop loss'))
        self.reject('varactor', lambda f: byid(f['context']['circuit_family_cards']['cards'])['SQD'].__setitem__('model_inductor_nH', 330))
        self.reject('varactor', lambda f: f['context']['shared_specimen_contract'].__setitem__('same_physical_varactor_pair', False))
        self.reject('varactor', lambda f: route(f, 'READOUT_SCALING_PROJECTION').__setitem__('route_kind', 'closed_service'))

    def test_reject_source_evidence_asset_or_publication_fabrication(self):
        for key in KEYS:
            self.reject(key, lambda f: f['operations'][0]['sources'].append('UNKNOWN_EVIDENCE'))
            self.reject(key, lambda f: f['context']['asset_binding_plan']['scene_assets'][0].__setitem__('physical_geometry_validated', True))
            self.reject(key, lambda f: f['source_files'].pop('source_conflicts.json'))
            self.reject(key, lambda f: f['source_files']['branches.json'].__setitem__('url', 'https://github.com/openags/ScienceGym/blob/main/tasks/branches.json'))
            self.reject(key, lambda f: f['asset_links'][0].__setitem__('sha256', '0' * 64))


if __name__ == '__main__': unittest.main()
