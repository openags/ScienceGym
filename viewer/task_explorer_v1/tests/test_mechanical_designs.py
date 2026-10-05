"""Independent source-bound mechanical design review; never executes a task.

SCIENCEGYM_TASKS=/path/to/tasks python -B -m unittest discover -s tests \
    -p test_mechanical_designs.py -v
"""
import collections
import copy
import hashlib
import json
import re
import unittest
import xml.etree.ElementTree as ET

from test_semantics import ROOT, TASKS, builder, get, ids
import mechanical_adapters as mechanical

PACKAGES = {
    'origami_memory': 'origami_memory_operations_v2',
    'ring_origami': 'ring_origami_operations_v2',
    'mechanical_backprop': 'mechanical_backprop_operations_v2',
}
EXPECTED = {
    'origami_memory': (55, 15, {'physical': 10, 'campaign': 1, 'numerical': 1, 'proposal': 3}, 20, 38),
    'ring_origami': (59, 21, {'physical': 14, 'campaign': 1, 'prerequisite': 3, 'numerical': 1, 'analysis': 1, 'proposal': 1}, 16, 8),
    'mechanical_backprop': (46, 24, {'physical': 9, 'campaign': 1, 'numerical': 13, 'proposal': 1}, 18, 31),
}
# Independent inverse mapping: do not import the adapter's FIELDS mapping.
COMMON = {'title': 'title', 'actions': 'actions', 'manipulated_objects_tools': 'objects',
          'preconditions': 'pre', 'completion_state': 'post', 'evidence_ids': 'sources',
          'recoveries': 'recovery', 'unknown_parameter_ids': 'unknowns', 'provenance': 'provenance'}
INVERSE = {
    'origami_memory': {**COMMON, 'location_id': 'stage'},
    'mechanical_backprop': {**COMMON, 'source_station': 'stage'},
    'ring_origami': {'station_id': 'stage', 'action': 'actions', 'objects': 'objects',
                     'preconditions': 'pre', 'completion_evidence': 'acceptance',
                     'source_evidence_ids': 'sources', 'failure_and_recovery': 'recovery',
                     'unknown_input_ids': 'unknowns'},
}
ALIASES = {'unknown_parameters.json': 'unknowns', 'evaluator_reference.json': 'acceptance', 'lineage_contract.json': 'lineage'}


def records(xs): return {x['id']: x for x in xs}
def raw(key, filename): return json.loads((TASKS / PACKAGES[key] / filename).read_text())
def route(f, identifier): return records(f['routes'])[identifier]
def nodes(r): return [n for n, _ in builder.walk(r['nodes'])]
def pointer(document, path):
    for token in path.split('/')[1:]:
        token = token.replace('~1', '/').replace('~0', '~')
        document = document[int(token)] if isinstance(document, list) else document[token]
    return document

def context_key(filename): return ALIASES.get(filename, filename[:-5])


class MechanicalBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.families = {key: get(key) for key in PACKAGES}

    def test_exact_counts_and_route_kinds(self):
        for key, (ops, count, kinds, unknowns, dependencies) in EXPECTED.items():
            with self.subTest(key=key):
                f = self.families[key]
                self.assertEqual((len(f['operations']), len(f['routes'])), (ops, count))
                self.assertEqual(dict(collections.Counter(r['route_kind'] for r in f['routes'])), kinds)
                self.assertEqual(len(f['context']['unknowns']['parameters' if key == 'ring_origami' else 'unknowns']), unknowns)
                self.assertEqual(len(f['dependencies']['rules' if key == 'ring_origami' else 'edges']), dependencies)
                self.assertEqual(f['summary_counts']['unresolved_input_groups'], unknowns)

    def test_global_totals_and_unchanged_earlier_thirteen_counts(self):
        manifest = [r for r in json.loads((ROOT / 'manifest.json').read_text())['families'] if r['id'] not in ('atmospheric_optics', 'afm_metrology', 'martian_geophysics', 'transistor', 'laser_control', 'solar_water', 'sucrose_metrology', 'actuator_metrology', 'woven', 'lockable_origami', 'varactor', 'wetting', 'arcmorph', 'midinfrared', 'conformal', 'scattering')]
        self.assertEqual((len(manifest), sum(x['routes'] for x in manifest), sum(x['operations'] for x in manifest)), (24, 541, 2189))
        older = [x for x in manifest if x['id'] not in {*PACKAGES, 'granular_assembly', 'beaded', 'thermal_jamming', 'horn_acoustics', 'mechanical_logic', 'cold_shape', 'gear', 'hydrogel_optical'}]
        self.assertEqual((len(older), sum(x['routes'] for x in older), sum(x['operations'] for x in older)), (13, 248, 1533))

    def test_all_sixty_svg_route_variants_parse_and_preserve_operation_rows(self):
        checked = 0
        for key, f in self.families.items():
            for r in f['routes']:
                with self.subTest(key=key, route=r['id']):
                    candidate = copy.deepcopy(f); candidate['default_route'] = r['id']
                    svg = builder.svg(candidate); root = ET.fromstring(svg)
                    text = [x.text or '' for x in root.findall('.//{http://www.w3.org/2000/svg}text')]
                    badges = [x for x in text if re.match(r'^\d+ · ', x)]
                    operation_badges = [x.split(' · ', 1)[1].split(' · ', 1)[0] for x in badges
                                        if x.split(' · ', 1)[1].split(' · ', 1)[0] in records(f['operations'])]
                    self.assertEqual(operation_badges, ids(r['nodes']))
                    self.assertIn(r['id'], svg)
                    self.assertIn('0 validated runnable whole-paper tasks', svg)
                    self.assertNotIn('marker-end=', svg)
                    for n in nodes(r):
                        source = n.get('meta', {}).get('source_node', {})
                        if not isinstance(source, dict): continue
                        if source.get('transfer_id'): self.assertIn(source['transfer_id'], svg)
                        bindings = source.get('bindings', {})
                        if bindings.get('phase_id'): self.assertIn('phase: ' + bindings['phase_id'], svg)
                        if bindings.get('active_force_role'): self.assertIn(bindings['active_force_role'], svg)
                    checked += 1
        self.assertEqual(checked, 60)

    def test_no_execution_or_actor_projection(self):
        for f in self.families.values():
            self.assertEqual(f['visibility'], 'author_evaluator_reference_only')
            self.assertIs(f['actor_projection_implemented'], False)
            self.assertIn('not an actor projection', f['status'])
            self.assertNotIn('execution_receipt', f); self.assertNotIn('actor_payload', f)
            for r in f['routes']:
                self.assertIn('not an actor projection', r['basis'])
                if r['source_file'] == 'nonmanual_scope.json':
                    self.assertEqual(ids(r['nodes']), [])
                    self.assertIs(r['metadata_only'], True)
                    self.assertNotEqual(r['route_kind'], 'physical')

    def test_all_actions_are_lists_and_ring_completion_evidence_is_separate(self):
        for f in self.families.values():
            for op in f['operations']: self.assertIsInstance(op['actions'], list)
        for op in self.families['ring_origami']['operations']:
            self.assertEqual(len(op['actions']), 1)
            self.assertIn('completion evidence is separate', op['post'][0])
            self.assertIn('display_title_basis', op['detail'])

    def test_unknown_counts_not_zero_or_source_repetition_defaults(self):
        for key in ('origami_memory', 'mechanical_backprop'):
            self.assertTrue(all(x['value'] is None for x in self.families[key]['context']['unknowns']['unknowns']))
        self.assertTrue(all(x['status'] == 'unresolved' for x in self.families['ring_origami']['context']['unknowns']['parameters']))
        memory = [r for r in self.families['origami_memory']['routes'] if r['route_kind'] == 'physical']
        self.assertTrue(all(r['detail']['source_repetition_count'] is None for r in memory))
        backprop = [r for r in self.families['mechanical_backprop']['routes'] if r['route_kind'] == 'physical']
        self.assertTrue(all(r['detail']['source_repetition_count'] == 3 and r['detail']['source_specimen_count'] is None for r in backprop))

    def test_distinct_video_requiredness_and_specific_ring_gate(self):
        a = self.families['origami_memory']['context']['source_access_audit']['movies']
        self.assertEqual([x['movie'] for x in a if x['status'] == 'downloaded_sampled_frames_inspected'], [1, 5])
        self.assertEqual(sum('unread' in x['status'] for x in a), 5)
        self.assertTrue(all('Not essential' in x['requiredness'] for x in a if 'unread' in x['status']))
        ring = self.families['ring_origami']; videos = ring['context']['source_access_audit']['movies']
        self.assertEqual(len(videos), 12); self.assertTrue(all(x['status'] == 'unread' for x in videos))
        self.assertIs(videos[8]['method_bearing'], True)
        gate = records(ring['context']['unknowns']['parameters'])['U_MOVIES']
        self.assertIn('authored substitute motion card', gate['missing'])
        b = self.families['mechanical_backprop']['context']['source_access_audit']['movies']
        self.assertEqual(len(b), 5)
        self.assertTrue(all(x['status'] == 'unviewed_description_read' and x['requiredness'].startswith('not_required_for_physical_task_contract') for x in b))

    def test_ring_torque_measured_parent_chain_and_partial_result(self):
        f = self.families['ring_origami']
        for identifier in ('TRI_TORSION', 'QUAD_TORSION'):
            r = route(f, identifier); dep = r['detail']['upstream_measurement_dependency']
            self.assertEqual(len(dep['allowed_sources']), 2); self.assertEqual(len(dep['disallowed']), 4)
            self.assertIn('partial', dep['missing_policy'])
            self.assertIn('ANALYZE_TORQUE', ids(r['nodes']))
            self.assertTrue(any(n.get('meta', {}).get('source_contract') == dep for n in nodes(r)))
        self.assertEqual(len(f['context']['lineage']['semi_experimental_torque_required_parents']), 4)
        self.assertEqual(f['context']['lineage']['raw_derived_separation'], ['measured', 'image_derived', 'semi_experimental', 'analytical_model', 'source_reference', 'mock'])
        self.assertEqual(route(f, 'N_TORQUE_DERIVATION')['route_kind'], 'analysis')
        self.assertIn('directly measured', records(f['context']['control_packages']['packages'])['C_TORSION']['forbidden'])

    def test_backprop_training_and_physical_measurement_stay_distinct(self):
        f = self.families['mechanical_backprop']; operations = records(f['operations'])
        self.assertEqual(operations['TRAIN_RUN']['detail']['actor'], 'analysis_service')
        self.assertIn('never mutate printed specimen', ' '.join(operations['TRAIN_RUN']['actions']))
        for identifier in ('N_BEHAV_TRAIN', 'N_REG_TRAIN', 'N_IRIS_TRAIN', 'N_SWITCH', 'N_DAMAGE'):
            self.assertEqual(route(f, identifier)['route_kind'], 'numerical')
            self.assertEqual(ids(route(f, identifier)['nodes']), [])
        self.assertEqual(route(f, 'N_FUTURE')['route_kind'], 'proposal')
        self.assertIn('No physical self-updating lattice', route(f, 'N_SWITCH')['detail']['disposition'])
        projection = f['context']['agent_visible']
        self.assertEqual(len(projection['selected_goal_templates']), 9)
        self.assertIn('anonymous', ' '.join(projection['blinded_projection_rules']))

    def test_origami_reset_retention_and_nonmanual_boundaries(self):
        f = self.families['origami_memory']; r = records(f['routes'])
        self.assertIn('reset to 00', r['WHOLE_PAPER_CAMPAIGN']['detail']['serial_handoff'])
        self.assertEqual(r['TWO_BIT_01_TO_10']['detail']['condition_card']['coupled_epoch_input'], 'first_bit_only')
        rules = records(f['dependencies']['branch_stage_dependencies'])
        self.assertIn('does not require force-torque acquisition', rules['D_MANUAL']['rule'])
        self.assertIn('actual grip release', rules['D_MANUAL_RELEASE']['rule'])
        self.assertEqual(r['N_TORQUE_READ']['route_kind'], 'proposal')
        self.assertEqual(r['N_FREQ']['route_kind'], 'proposal')
        self.assertEqual(r['N_NETWORK']['route_kind'], 'proposal')
        self.assertIn('never creates a global cyclic DAG', f['dependencies']['loop_expansion'])

    def test_payloads_equal_and_pinned_source_urls(self):
        for key, f in self.families.items():
            bundled = json.loads((ROOT / 'data' / (key + '.json')).read_text())
            js = (ROOT / 'data' / (key + '.js')).read_text().split('[' + json.dumps(key) + ']=', 1)[1].rsplit(';', 1)[0]
            self.assertEqual(json.loads(js), bundled)
            self.assertEqual(f['source_commit'], '43a185dacb02a979148bee93d5d9559e569086f3')
            for name, entry in f['source_files'].items(): self.assertEqual(entry['url'], f['source_folder'] + name)


@unittest.skipUnless(TASKS, 'SCIENCEGYM_TASKS not set; source comparison not run')
class MechanicalSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.families = {key: get(key) for key in PACKAGES}
        cls.adapted = {key: mechanical.adapt(TASKS / package, key) for key, package in PACKAGES.items()}

    def test_every_operation_field_reconstructs_exact_source(self):
        for key, f in self.families.items():
            source = raw(key, 'operations.json')['operations']
            self.assertEqual([x['id'] for x in f['operations']], [x['id'] for x in source])
            for op, original in zip(f['operations'], source):
                restored = {'id': op['id'], **copy.deepcopy(op['detail'])}
                if key == 'ring_origami': restored.pop('display_title_basis')
                for source_field, normalized in INVERSE[key].items():
                    restored[source_field] = op[normalized][0] if key == 'ring_origami' and source_field == 'action' else op[normalized]
                self.assertEqual(restored, original, (key, original['id']))
                self.assertEqual(pointer(raw(key, op['source_file']), op['source_pointer']), original)

    def test_every_json_context_and_source_hash_is_exact(self):
        for key, f in self.families.items():
            p = TASKS / PACKAGES[key]
            names = {x.relative_to(p).as_posix() for x in p.rglob('*.json')}
            self.assertEqual(set(f['source_files']), names)
            for name in names:
                self.assertEqual(f['source_files'][name]['sha256'], hashlib.sha256((p / name).read_bytes()).hexdigest(), (key, name))
                if name not in ('operations.json', 'branches.json', 'dependencies.json'):
                    self.assertEqual(f['context'][context_key(name)], raw(key, name), (key, name))
            self.assertEqual(f['dependencies'], raw(key, 'dependencies.json'))
            self.assertEqual(f['context']['operation_policy'], {k: v for k, v in raw(key, 'operations.json').items() if k != 'operations'})
            self.assertEqual(f['context']['branch_policy'], {k: v for k, v in raw(key, 'branches.json').items() if k != 'branches'})
            evidence = raw(key, 'provenance.json')['evidence']
            self.assertEqual(f['evidence'], records(evidence) if isinstance(evidence, list) else evidence)

    def test_every_route_detail_and_source_occurrence_pointer_is_exact(self):
        for key, f in self.families.items():
            for r in f['routes']:
                self.assertEqual(r['detail'], pointer(raw(key, r['source_file']), r['source_pointer']))
                for n in nodes(r):
                    meta = n.get('meta', {})
                    if 'source_node' in meta:
                        self.assertEqual(meta['source_node'], pointer(raw(key, meta['source_file']), meta['source_pointer']))

    def test_all_bundled_data_matches_fresh_unpooled_projection(self):
        for key, f in self.families.items():
            self.assertEqual({k: v for k, v in f.items() if k != 'shared'}, self.adapted[key])
            self.assertTrue(mechanical.validate_projection(self.adapted[key], TASKS / PACKAGES[key]))

    def test_origami_membership_and_each_unexpanded_loop_exact(self):
        f = self.families['origami_memory']; source = raw('origami_memory', 'branches.json')
        for original in source['branches']:
            r = route(f, original['id']); member = r['nodes'][0]
            self.assertEqual(member['type'], 'obligations'); self.assertIs(member['ordered'], False)
            self.assertEqual(member['children'], original['operation_ids'])
            self.assertEqual(ids(r['nodes']), original['operation_ids'])
            loops = [n for n in nodes(r) if n['type'] == 'loop']
            self.assertEqual([n['meta']['source_contract'] for n in loops], original['loops'] + [source['shared_preparation_loops']])
            self.assertTrue(all(n['children'] == [] and n['symbolic'] is True for n in loops))

    def check_ring_grammar(self, source, shown, bindings, path):
        self.assertEqual(len(source), len(shown), path)
        for i, (item, n) in enumerate(zip(source, shown)):
            meta = n['meta']; loc = path + '/' + str(i)
            self.assertEqual(meta['source_file'], 'branches.json'); self.assertEqual(meta['source_pointer'], loc)
            self.assertEqual(meta['source_node'], item)
            if isinstance(item, str):
                self.assertEqual(n['type'], 'op'); self.assertEqual(n['id'], bindings[item] if item.startswith('@') else item)
                if item.startswith('@'): self.assertEqual(meta['macro_binding'], {item: bindings[item]})
            elif 'operation' in item:
                self.assertEqual((n['type'], n['id']), ('op', item['operation']))
            elif 'concurrent' in item:
                self.assertEqual(n['type'], 'obligations'); self.assertIs(n['ordered'], False)
                self.check_ring_grammar(item['concurrent'], n['children'], bindings, loc + '/concurrent')
            else:
                self.assertIn('loop', item); self.assertEqual(n['type'], 'loop')
                self.assertIs(n['symbolic'], True); self.assertIs(n['ordered'], True)
                body = n['children']; post = item.get('postprocess')
                if isinstance(post, dict):
                    condition = body[-1]; body = body[:-1]
                    self.assertEqual(condition['type'], 'condition')
                    self.assertEqual(condition['meta']['source_contract'], post)
                    self.check_ring_grammar(post['body'], condition['children'], bindings, loc + '/postprocess/body')
                self.check_ring_grammar(item['body'], body, bindings, loc + '/body')

    def test_ring_schema_native_macros_concurrency_and_preparation_grammar(self):
        source = raw('ring_origami', 'branches.json'); f = self.families['ring_origami']
        for i, original in enumerate(source['branches']):
            r = route(f, original['id']); p = '/branches/' + str(i)
            self.check_ring_grammar(original['assembly_operations'], r['nodes'][1]['children'], {}, p + '/assembly_operations')
            outer = r['nodes'][2]; transition, trial = outer['children']
            self.assertEqual(outer['meta']['conditions'], original['conditions'])
            self.assertEqual(transition['meta']['source_contract'], original['condition_transition'])
            self.assertEqual(trial['meta']['source_contract'], original['trial_loop'])
            self.assertIs(outer['symbolic'], True); self.assertIs(trial['symbolic'], True)
            self.check_ring_grammar(original['test_body'], trial['children'], original['operation_bindings'], p + '/test_body')
            self.check_ring_grammar(original['closure_operations'], r['nodes'][3]['children'], {}, p + '/closure_operations')
        for key, original in source['preparation_routes'].items():
            self.check_ring_grammar(original['steps'], route(f, key)['nodes'][0]['children'], {}, '/preparation_routes/' + key + '/steps')
        self.assertEqual(route(f, 'WHOLE_PAPER_CAMPAIGN')['detail'], source['campaign'])

    def test_ring_conditions_remain_unexpanded_and_concurrent_constraints_exact(self):
        f = self.families['ring_origami']; source = raw('ring_origami', 'branches.json')
        self.assertEqual(sum(len(x['conditions']) for x in source['branches']), 58)
        for b in source['branches']:
            r = route(f, b['id'])
            self.assertEqual(r['nodes'][2]['meta']['condition_expansion_contract'], source['condition_expansion_contract'])
            expected = [x for x in b['test_body'] if isinstance(x, dict) and 'concurrent' in x]
            shown = [n['meta']['source_node'] for n in nodes(r) if 'concurrent' in n.get('meta', {}).get('source_node', {})]
            self.assertEqual(shown, expected)
        self.assertEqual(len(route(f, 'MORPHOLOGY_I')['detail']['conditions']), 4)
        self.assertIsNone(route(f, 'ARRAY_TENSION')['detail']['source_repetition_count'])

    def check_backprop_grammar(self, source, shown, transfers, path):
        self.assertEqual(len(source), len(shown), path)
        for i, (item, n) in enumerate(zip(source, shown)):
            loc = path + '/' + str(i); meta = n['meta']
            self.assertEqual(meta['source_file'], 'reference_routes.json')
            self.assertEqual(meta['source_pointer'], loc); self.assertEqual(meta['source_node'], item)
            if item['kind'] == 'operation': self.assertEqual((n['type'], n['id']), ('op', item['operation_id']))
            elif item['kind'] == 'transfer':
                transfer = transfers[item['transfer_id']]
                self.assertEqual((n['type'], n['id']), ('op', transfer['operation_id']))
                self.assertEqual(meta['transfer_contract'], transfer)
            else:
                self.assertIn(item['kind'], ('repeat', 'for_each'))
                self.assertEqual(n['type'], 'loop'); self.assertIs(n['symbolic'], True); self.assertIs(n['ordered'], True)
                self.check_backprop_grammar(item['body'], n['children'], transfers, loc + '/body')

    def test_backprop_exact_typed_trees_bindings_transfers_and_nesting(self):
        f = self.families['mechanical_backprop']; source = raw('mechanical_backprop', 'reference_routes.json')
        counts = collections.Counter(); transfers = records(source['transfers'])
        for i, original in enumerate(source['routes']):
            r = route(f, original['branch_id']); wrapper = r['nodes'][0]
            self.assertEqual(wrapper['meta']['source_contract'], original)
            self.assertEqual(wrapper['meta']['semantics'], source['semantics'])
            self.check_backprop_grammar(original['body'], wrapper['children'], transfers, '/routes/' + str(i) + '/body')
            counts.update(n['meta']['source_node']['kind'] for n in nodes(r) if 'source_node' in n.get('meta', {}))
        self.assertEqual(counts, {'operation': 387, 'transfer': 90, 'repeat': 9, 'for_each': 1})
        campaign = route(f, 'WHOLE_PAPER_CAMPAIGN')
        self.assertEqual(campaign['nodes'][0]['meta']['source_contract'], source['campaign'])

    def test_backprop_gradient_phases_repeated_ids_and_zero_mass_nested_loop(self):
        f = self.families['mechanical_backprop']
        for name in ('GRADIENT_SEPARATE', 'GRADIENT_SAME'):
            repeated = [n for n in nodes(route(f, name)) if n['type'] == 'loop'][0]
            body = repeated['children']; self.assertEqual(len(body), 18)
            self.assertEqual([n['id'] for n in body][8], 'ADJOINT_COMPUTE')
            self.assertEqual(body[-1]['id'], 'PAIR_GRADIENT')
            for n in body[:8]: self.assertEqual(n['meta']['source_node']['bindings'], {'phase_id': 'forward', 'active_force_role': 'forward_only'})
            for n in body[9:17]: self.assertEqual(n['meta']['source_node']['bindings'], {'phase_id': 'adjoint', 'active_force_role': 'adjoint_only'})
            self.assertEqual(ids([repeated]).count('CAPTURE'), 2)
        r = route(f, 'REGRESSION_SWEEP'); loops = [n for n in nodes(r) if n['type'] == 'loop']
        self.assertEqual(len(loops), 2); self.assertIn(loops[1], loops[0]['children'])
        self.assertEqual(loops[1]['meta']['source_node']['values'], [0, 2, 4, 6, 8, 10, 12])
        self.assertEqual(ids([loops[1]]).count('CAPTURE'), 1)
        self.assertIn('capture a real image', f['context']['reference_routes']['semantics']['zero_mass'])

    def reject(self, key, change):
        f = copy.deepcopy(self.adapted[key]); change(f)
        with self.assertRaises(ValueError): mechanical.validate_projection(f, TASKS / PACKAGES[key])

    def test_adversarial_actor_payload_receipt_and_visibility(self):
        for key in PACKAGES:
            for change in (lambda f: f.__setitem__('actor_projection_implemented', True),
                           lambda f: f.__setitem__('actor_payload', {'source_outcomes': f['context']['source_outcomes']}),
                           lambda f: f.__setitem__('execution_receipt', {'complete': True}),
                           lambda f: f.__setitem__('visibility', 'actor_visible')):
                with self.subTest(key=key, change=change): self.reject(key, change)

    def test_adversarial_nonmanual_promotion_and_physical_steps(self):
        for key, identifier in [('origami_memory', 'N_FREQ'), ('ring_origami', 'N_MODEL'), ('mechanical_backprop', 'N_DAMAGE')]:
            self.reject(key, lambda f: route(f, identifier).__setitem__('route_kind', 'physical'))
            self.reject(key, lambda f: route(f, identifier)['nodes'][0]['children'].append(f['operations'][0]['id']))

    def test_adversarial_operation_context_and_source_hash_mutations(self):
        for key in PACKAGES:
            for change in (lambda f: f['operations'][0].__setitem__('actions', ['executed']),
                           lambda f: f['context'].pop('source_conflicts'),
                           lambda f: f['source_files'].pop('source_access_audit.json'),
                           lambda f: f['source_files']['operations.json'].__setitem__('sha256', '0' * 64),
                           lambda f: f['source_files']['branches.json'].__setitem__('url', 'https://example.com/unpinned')):
                self.reject(key, change)

    def test_adversarial_unknown_defaults_and_movie_requiredness(self):
        for key in ('origami_memory', 'mechanical_backprop'):
            self.reject(key, lambda f: f['context']['unknowns']['unknowns'][0].__setitem__('value', 0))
        self.reject('ring_origami', lambda f: records(f['context']['unknowns']['parameters'])['U_MOVIES'].__setitem__('status', 'resolved'))
        self.reject('mechanical_backprop', lambda f: f['context']['source_access_audit']['movies'][0].__setitem__('status', 'viewed'))

    def test_adversarial_origami_order_loop_reset_and_specimen_counts(self):
        self.reject('origami_memory', lambda f: route(f, 'ONE_BIT_TORQUE')['nodes'][0].__setitem__('ordered', True))
        self.reject('origami_memory', lambda f: route(f, 'ONE_BIT_TORQUE')['detail'].__setitem__('source_repetition_count', 0))
        self.reject('origami_memory', lambda f: route(f, 'WHOLE_PAPER_CAMPAIGN')['detail'].__setitem__('serial_handoff', 'implicit reset'))
        self.reject('origami_memory', lambda f: route(f, 'SINGLE_BISTABLE')['nodes'][1]['children'].append('COMPRESSION_ACQUIRE'))

    def test_adversarial_ring_macro_concurrency_postprocess_and_torque(self):
        def macro(f):
            next(n for n in nodes(route(f, 'ELEMENT_RESPONSE')) if 'macro_binding' in n.get('meta', {}))['id'] = 'MOUNT_ARRAY'
        def concurrent(f):
            next(n for n in nodes(route(f, 'ARRAY_TENSION')) if 'concurrent' in n.get('meta', {}).get('source_node', {}))['ordered'] = True
        def conditional(f):
            next(n for n in nodes(route(f, 'PREP_THICK')) if n['type'] == 'condition')['type'] = 'group'
        def torque(f): route(f, 'TRI_TORSION')['detail']['upstream_measurement_dependency']['allowed_sources'].append('theoretical curve')
        for change in (macro, concurrent, conditional, torque): self.reject('ring_origami', change)
        self.reject('ring_origami', lambda f: route(f, 'N_TORQUE_DERIVATION').__setitem__('label', 'Directly measured torque'))

    def test_adversarial_backprop_binding_transfer_tree_and_self_update(self):
        def binding(f):
            next(n for n in nodes(route(f, 'GRADIENT_SEPARATE')) if n.get('meta', {}).get('source_node', {}).get('bindings', {}).get('phase_id') == 'adjoint')['meta']['source_node']['bindings']['active_force_role'] = 'forward_plus_adjoint'
        def transfer(f):
            next(n for n in nodes(route(f, 'GRADIENT_SEPARATE')) if 'transfer_contract' in n.get('meta', {}))['meta']['transfer_contract']['target_station'] = 'WS_TEST'
        def unnest(f):
            loops = [n for n in nodes(route(f, 'REGRESSION_SWEEP')) if n['type'] == 'loop']; loops[0]['children'].remove(loops[1])
        def zero(f):
            next(n for n in nodes(route(f, 'REGRESSION_SWEEP')) if n.get('meta', {}).get('source_node', {}).get('kind') == 'for_each')['meta']['source_node']['values'].remove(0)
        def update(f): records(f['operations'])['TRAIN_RUN']['actions'].append('Update physical printed spring constants')
        for change in (binding, transfer, unnest, zero, update): self.reject('mechanical_backprop', change)

    def test_adversarial_campaign_pooling_summary_and_source_tree_loss(self):
        self.reject('mechanical_backprop', lambda f: route(f, 'WHOLE_PAPER_CAMPAIGN')['nodes'][0]['meta']['source_contract']['branch_ids'].pop())
        self.reject('ring_origami', lambda f: f['summary_counts'].__setitem__('physical_records', 58))
        self.reject('mechanical_backprop', lambda f: f['context'].pop('reference_routes'))


if __name__ == '__main__': unittest.main()
