"""Independent source reconstruction, display invariants and adversarial fixtures."""
import collections
import copy
import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from test_semantics import ROOT, TASKS, builder, get, ids
import crossdisciplinary_adapters as cross

KEYS = ('atmospheric_optics', 'afm_metrology', 'martian_geophysics', 'transistor')
PIN = '990f98529182af0ddd03fba53587b0931630de96'
COUNTS = {'atmospheric_optics': (196, 28, 34), 'afm_metrology': (27, 8, 21),
          'martian_geophysics': (254, 38, 38), 'transistor': (44, 24, 42)}
KINDS = {'atmospheric_optics': {'physical': 7, 'analysis': 13, 'numerical': 8, 'prospective': 3, 'reference': 3},
         'afm_metrology': {'physical': 8, 'bounded_fabrication': 2, 'session_teardown': 1, 'numerical': 4, 'prospective': 6},
         'martian_geophysics': {'physical': 26, 'analysis': 4, 'numerical': 7, 'data_curation': 1},
         'transistor': {'physical': 24, 'numerical': 7, 'prospective': 6, 'excluded': 5}}
ALIASES = {'unknown_parameters.json': 'unknowns', 'evaluator_reference.json': 'acceptance', 'lineage_contract.json': 'lineage'}
def package(key): return TASKS / (key + '_operations_v2')
def raw(key, filename): return json.loads((package(key) / filename).read_text())
def byid(records): return {r['id']: r for r in records}
def pointer(document, path):
    for part in path.split('/')[1:]:
        part = part.replace('~1', '/').replace('~0', '~')
        document = document[int(part)] if isinstance(document, list) else document[part]
    return document

class CrossdisciplinaryBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.families = {key: get(key) for key in KEYS}

    def test_global_and_unchanged_historical_counts(self):
        records = [r for r in json.loads((ROOT / 'manifest.json').read_text())['families'] if r['id'] not in ('laser_control', 'solar_water', 'sucrose_metrology', 'actuator_metrology', 'woven', 'lockable_origami', 'varactor', 'wetting', 'arcmorph', 'midinfrared')]
        self.assertEqual((len(records), sum(x['operations'] for x in records), sum(x['routes'] for x in records)), (28, 2710, 676))
        old = [x for x in records if x['id'] not in KEYS]
        self.assertEqual((len(old), sum(x['operations'] for x in old), sum(x['routes'] for x in old)), (24, 2189, 541))

    def test_exact_typed_route_counts_and_distinct_source_branch_counts(self):
        for key, f in self.families.items():
            operations, branches, routes = COUNTS[key]
            self.assertEqual((len(f['operations']), f['summary_counts']['source_branches'], len(f['routes'])), (operations, branches, routes))
            self.assertEqual(collections.Counter(r['route_kind'] for r in f['routes']), KINDS[key])

    def test_all_521_operation_definitions_are_navigable_without_expansion(self):
        for key, f in self.families.items():
            self.assertEqual(set(o['id'] for o in f['operations']), {oid for r in f['routes'] for oid in ids(r['nodes'])})
            for r in f['routes']:
                self.assertEqual(r['metadata_only'], not bool(ids(r['nodes'])))
                if r['source_file'] == 'branches.json': self.assertEqual(ids(r['nodes']), r['detail']['operation_ids'])
                self.assertFalse(any(n['type'] == 'loop' for n, _ in builder.walk(r['nodes'])))
                for n, _ in builder.walk(r['nodes']):
                    if n['type'] == 'obligations': self.assertIs(n['ordered'], False)

    def test_all_135_svg_variants_keep_membership_and_no_adjacency(self):
        count = 0
        for key, f in self.families.items():
            for r in f['routes']:
                candidate = copy.deepcopy(f); candidate['default_route'] = r['id']
                svg = builder.svg(candidate); tree = ET.fromstring(svg)
                self.assertNotIn('marker-end=', svg)
                self.assertIn('No adjacency arrows', svg)
                self.assertIn('0 validated runnable whole-paper tasks', svg)
                texts = [x.text or '' for x in tree.findall('.//{http://www.w3.org/2000/svg}text')]
                badges = [x.split(' · ')[1] for x in texts if x[:2].isdigit() and ' · ' in x]
                self.assertEqual([x for x in badges if x in byid(f['operations'])], ids(r['nodes']))
                count += 1
        self.assertEqual(count, 135)

    def test_read_only_visibility_and_original_operation_detail(self):
        for f in self.families.values():
            self.assertEqual(f['visibility'], 'author_evaluator_reference_only')
            self.assertIs(f['actor_projection_implemented'], False)
            for op in f['operations']:
                self.assertEqual(op['id'], op['detail']['id'])
                self.assertIsInstance(op['actions'], list)
                self.assertIsNone(op['loop'])
                self.assertIn('absence notices', op['display_mapping_basis'])

    def test_source_pins_json_js_equality_and_markdown_boundaries(self):
        for key, f in self.families.items():
            self.assertEqual(f['source_commit'], PIN)
            for name, record in f['source_files'].items(): self.assertEqual(record['url'], f'https://github.com/openags/ScienceGym/blob/{PIN}/tasks/{key}_operations_v2/{name}')
            js = (ROOT / 'data' / (key + '.js')).read_text().split('[' + json.dumps(key) + ']=', 1)[1].rsplit(';', 1)[0]
            self.assertEqual(json.loads(js), json.loads((ROOT / 'data' / (key + '.json')).read_text()))
            md = (ROOT / 'docs' / (key + '.md')).read_text()
            self.assertIn(f['source_warnings'], md)
            self.assertIn('unordered source inventory', md)
            for r in f['routes']: self.assertIn('## ' + r['id'] + ' ', md)

    def test_atmospheric_source_gap_mount_and_data_scope(self):
        f = self.families['atmospheric_optics']
        self.assertIn('source_complete_for_entire_paper=false', f['status'])
        self.assertIs(f['context']['source_access_audit']['main_figures_pixel_inspected'], False)
        self.assertIs(f['context']['STATUS']['main_direct_byte_identity_hold_preserved'], True)
        self.assertIn('mount_lease_contract', f['context'])
        self.assertEqual(byid(f['routes'])['TIS']['route_kind'], 'analysis')
        self.assertTrue(all(r['detail']['source_independent_replicates'] is None for r in f['routes'] if r['source_file'] == 'branches.json'))

    def test_afm_retained_probe_teardown_and_incomplete_fabrication(self):
        f = self.families['afm_metrology']
        self.assertIn('not full fabrication', f['status'])
        self.assertNotIn('dependencies.json', f['source_files']); self.assertEqual(f['dependencies'], {})
        for r in f['routes'][:8]:
            self.assertIs(r['detail']['calibration_reusable_between_episodes'], False)
            self.assertIsNone(r['detail']['default_repeat_count'])
            self.assertIn('Only the target or coupon', r['detail']['branch_tail_scope'])
        for identifier in ('PREP_ARRAY', 'PREP_CYLINDER'):
            r = byid(f['routes'])[identifier]
            self.assertEqual(r['route_kind'], 'bounded_fabrication')
            self.assertIs(r['detail']['complete_source_recipe'], False)
            self.assertIs(r['detail']['historical_route_complete'], False)
        self.assertEqual(ids(byid(f['routes'])['SESSION_TEARDOWN']['nodes']), ['FINAL_SESSION_TEARDOWN'])

    def test_martian_conflicts_qualification_and_typed_nonphysical_records(self):
        f = self.families['martian_geophysics']
        self.assertIs(f['context']['nonmanual_scope']['qualification_owned_by_facility'], True)
        self.assertIs(f['context']['episode_input_contract']['hazard_parameter_payloads_allowed'], False)
        self.assertIs(f['context']['episode_input_contract']['unresolved_source_conflicts_block_physical_binding'], True)
        self.assertEqual(byid(f['routes'])['ARCHIVE']['route_kind'], 'data_curation')
        self.assertTrue(all(r['detail']['source_independent_replicates'] is None for r in f['routes']))
        for op in f['operations']: self.assertEqual(op['actions'], [op['detail']['action']])

    def test_transistor_lifecycle_inventory_safe_zero_and_missing_defaults(self):
        f = self.families['transistor']
        self.assertIsNone(f['context']['control_packages']['unspecified_step_or_dwell_defaults'])
        self.assertIn('Commands never prove safe state', f['context']['lifecycle_contract']['safe_state_principle'])
        for r in f['routes'][:24]:
            self.assertIn('Unordered', r['detail']['operation_ids_semantics'])
            self.assertIsNone(r['detail']['default_repeat_count'])
            self.assertEqual(r['controls'][0]['id'], r['id'])
            self.assertEqual(r['nodes'][-1]['meta']['source_contract'], f['context']['lifecycle_contract'])

@unittest.skipUnless(TASKS, 'SCIENCEGYM_TASKS not set; exact source reconstruction and mutations not run')
class CrossdisciplinarySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.families = {key: get(key) for key in KEYS}
        cls.adapted = {key: cross.adapt(package(key), key) for key in KEYS}

    def test_every_source_json_document_reconstructs_exactly_and_hashes_match(self):
        for key, f in self.families.items():
            names = {p.relative_to(package(key)).as_posix() for p in package(key).rglob('*.json')}
            self.assertEqual(set(f['source_files']), names)
            for name in names:
                if name == 'operations.json': rebuilt = {**f['context']['operation_policy'], 'operations': [o['detail'] for o in f['operations']]}
                elif name == 'branches.json': rebuilt = {**f['context']['branch_policy'], 'branches': [r['detail'] for r in f['routes'] if r['source_file'] == name]}
                elif name == 'dependencies.json': rebuilt = f['dependencies']
                else: rebuilt = f['context'][ALIASES.get(name, name.removesuffix('.json'))]
                self.assertEqual(rebuilt, raw(key, name), (key, name))
                self.assertEqual(f['source_files'][name]['sha256'], hashlib.sha256((package(key) / name).read_bytes()).hexdigest())

    def test_every_operation_display_mapping_matches_source_without_default_settings(self):
        for key, f in self.families.items():
            original = raw(key, 'operations.json')['operations']
            self.assertEqual([o['detail'] for o in f['operations']], original)
            for i, (op, source) in enumerate(zip(f['operations'], original)):
                self.assertEqual(op['source_pointer'], '/operations/' + str(i))
                actions = source.get('robot_actions', source.get('actions', source.get('action')))
                self.assertEqual(op['actions'], actions if isinstance(actions, list) else [actions])
                for field, choices in [('pre', ('preconditions', 'pre_state')), ('post', ('postconditions', 'post_state')),
                                       ('acceptance', ('completion_evidence', 'required_receipts', 'required_receipt_fields'))]:
                    values = [source[name] for name in choices if name in source]
                    if values: self.assertEqual(op[field], values[0])
                    else: self.assertIn('No value is inferred', op[field])

    def test_every_route_and_metadata_pointer_matches_exact_source(self):
        for key, f in self.families.items():
            for r in f['routes']:
                original = pointer(raw(key, r['source_file']), r['source_pointer'])
                self.assertEqual(r['detail'].get('source_record') if r.get('detail_source_wrapper') else r['detail'], original)
                for n, _ in builder.walk(r['nodes']):
                    if n['type'] == 'condition':
                        meta = n['meta']; self.assertEqual(meta['source_contract'], pointer(raw(key, meta['source_file']), meta['source_pointer']))

    def reject(self, key, mutation):
        f = copy.deepcopy(self.adapted[key]); mutation(f)
        with self.assertRaises(ValueError): cross.validate_projection(f, package(key))

    def test_reject_common_source_loss_visibility_and_chronology_mutations(self):
        mutations = {
            'operation_lost': lambda f: f['operations'].pop(),
            'source_operation_field_lost': lambda f: f['operations'][0]['detail'].pop('id'),
            'normalized_action_invented': lambda f: f['operations'][0].__setitem__('actions', ['run apparatus']),
            'branch_lost': lambda f: f['routes'].pop(0),
            'branch_membership_lost': lambda f: f['routes'][0]['nodes'][0]['children'].pop(),
            'chronology_invented': lambda f: f['routes'][0]['nodes'][0].__setitem__('ordered', True),
            'unknowns_erased': lambda f: f['context'].__setitem__('unknowns', {}),
            'conflicts_erased': lambda f: f['context'].__setitem__('source_conflicts', {}),
            'lineage_erased': lambda f: f['context'].__setitem__('lineage', {}),
            'episode_erased': lambda f: f['context'].__setitem__('episode_input_contract', {}),
            'controls_erased': lambda f: f['routes'][0].__setitem__('controls', []),
            'pin_changed': lambda f: f.__setitem__('source_commit', 'main'),
            'actor_visibility_promoted': lambda f: f.__setitem__('visibility', 'actor'),
            'execution_invented': lambda f: f.__setitem__('actor_projection_implemented', True),
        }
        for key in KEYS:
            for name, mutation in mutations.items():
                with self.subTest(key=key, mutation=name): self.reject(key, mutation)

    def test_reject_atmospheric_mount_scope_count_and_access_promotions(self):
        mutations = [lambda f: f['context'].__setitem__('mount_lease_contract', {}),
                     lambda f: byid(f['routes'])['TIS'].__setitem__('route_kind', 'physical'),
                     lambda f: f['routes'][0]['detail'].__setitem__('source_independent_replicates', 1),
                     lambda f: f['context']['source_access_audit'].__setitem__('main_figures_pixel_inspected', True),
                     lambda f: f['context']['STATUS'].__setitem__('main_direct_byte_identity_hold_preserved', False)]
        for i, mutation in enumerate(mutations):
            with self.subTest(mutation=i): self.reject('atmospheric_optics', mutation)

    def test_reject_afm_fabrication_teardown_custody_and_repeat_promotions(self):
        mutations = [lambda f: byid(f['routes'])['PREP_ARRAY']['detail'].__setitem__('complete_source_recipe', True),
                     lambda f: byid(f['routes'])['PREP_CYLINDER'].__setitem__('route_kind', 'physical'),
                     lambda f: byid(f['routes'])['SESSION_TEARDOWN']['nodes'][0]['children'].clear(),
                     lambda f: f['routes'][0]['detail'].__setitem__('calibration_reusable_between_episodes', True),
                     lambda f: f['routes'][0]['detail'].__setitem__('branch_tail_scope', 'Retrieve calibrated array after every branch'),
                     lambda f: f['routes'][0]['detail'].__setitem__('default_repeat_count', 1088)]
        for i, mutation in enumerate(mutations):
            with self.subTest(mutation=i): self.reject('afm_metrology', mutation)

    def test_reject_martian_hazard_analysis_observation_and_lineage_promotions(self):
        mutations = [lambda f: f['context']['episode_input_contract'].__setitem__('hazard_parameter_payloads_allowed', True),
                     lambda f: f['context']['episode_input_contract'].__setitem__('unresolved_source_conflicts_block_physical_binding', False),
                     lambda f: byid(f['routes'])['SOLIDUS_FIT'].__setitem__('route_kind', 'physical'),
                     lambda f: byid(f['routes'])['XRAY'].__setitem__('route_kind', 'physical'),
                     lambda f: f['routes'][0]['detail'].__setitem__('source_independent_replicates', 10000),
                     lambda f: f['operations'][0]['detail'].__setitem__('actor_may_command_hazard', True)]
        for i, mutation in enumerate(mutations):
            with self.subTest(mutation=i): self.reject('martian_geophysics', mutation)

    def test_reject_transistor_lifecycle_damage_safety_defaults_and_cohort_promotions(self):
        mutations = [lambda f: f['context']['lifecycle_contract']['routes']['HIGHK'].clear(),
                     lambda f: f['context']['lifecycle_contract']['routes']['THERMAL'].reverse(),
                     lambda f: f['context']['control_packages'].__setitem__('unspecified_step_or_dwell_defaults', 1),
                     lambda f: f['context'].__setitem__('netlist_contracts', {}),
                     lambda f: f['context'].__setitem__('layer_contract', {}),
                     lambda f: f['routes'][0]['detail'].__setitem__('default_repeat_count', 90),
                     lambda f: f['context']['lifecycle_contract'].__setitem__('safe_state_principle', 'Commands prove safe state')]
        for i, mutation in enumerate(mutations):
            with self.subTest(mutation=i): self.reject('transistor', mutation)

if __name__ == '__main__': unittest.main()
