"""Independent reconstruction checks for three read-only assembly-family views."""
import collections
import copy
import hashlib
import json
import re
import unittest
import xml.etree.ElementTree as ET
from test_semantics import ROOT, TASKS, builder, get, ids
import assembly_adapters as assembly

KEYS = ('granular_assembly', 'beaded', 'thermal_jamming')
EXPECTED = {'granular_assembly': (42, 32, 26, 31, 16), 'beaded': (70, 30, 21, 35, 15), 'thermal_jamming': (33, 16, 13, 27, 16)}
# Independent inverse mapping, deliberately not imported from adapter constants.
COMMON = {'label': 'title', 'station': 'stage', 'robot_actions': 'actions', 'manipulated_objects_and_tools': 'objects',
          'preconditions': 'pre', 'completion_state': 'post', 'completion_evidence': 'acceptance',
          'source_refs': 'sources', 'required_unknowns': 'unknowns', 'failure_handling': 'recovery'}
INVERSE = {'granular_assembly': {**COMMON, 'provenance': 'provenance'},
           'thermal_jamming': {**COMMON, 'provenance_class': 'provenance'},
           'beaded': {'title': 'title', 'location_id': 'stage', 'actions': 'actions', 'manipulated_objects': 'objects',
                      'preconditions': 'pre', 'postconditions': 'post', 'success_evidence': 'acceptance', 'evidence_ids': 'sources',
                      'unknown_parameter_ids': 'unknowns', 'recovery': 'recovery', 'provenance': 'provenance'}}
ALIASES = {'unknown_parameters.json': 'unknowns', 'evaluator_reference.json': 'acceptance', 'lineage_contract.json': 'lineage'}

def raw(key, name): return json.loads((TASKS / (key + '_operations_v2') / name).read_text())
def byid(records): return {r['id']: r for r in records}
def route(f, name): return byid(f['routes'])[name]
def nodes(r): return [n for n, _ in builder.walk(r['nodes'])]
def pointer(document, path):
    for token in path.split('/')[1:]:
        token = token.replace('~1', '/').replace('~0', '~')
        document = document[int(token)] if isinstance(document, list) else document[token]
    return document


class AssemblyBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.families = {k: get(k) for k in KEYS}

    def test_counts_and_all_prior_sixteen(self):
        manifest = [r for r in json.loads((ROOT / 'manifest.json').read_text())['families'] if r['id'] not in ('atmospheric_optics', 'afm_metrology', 'martian_geophysics', 'transistor', 'laser_control', 'solar_water', 'sucrose_metrology', 'actuator_metrology', 'woven', 'lockable_origami', 'varactor', 'wetting', 'arcmorph', 'midinfrared', 'conformal', 'scattering')]
        self.assertEqual((len(manifest), sum(r['routes'] for r in manifest), sum(r['operations'] for r in manifest)), (24, 541, 2189))
        old = [r for r in manifest if r['id'] not in ('gear', 'hydrogel_optical') and r['id'] not in KEYS and r['id'] not in ('horn_acoustics', 'mechanical_logic', 'cold_shape')]
        self.assertEqual((len(old), sum(r['routes'] for r in old), sum(r['operations'] for r in old)), (16, 308, 1693))
        for key, (ops, records, physical, unknowns, controls) in EXPECTED.items():
            f = self.families[key]
            self.assertEqual((len(f['operations']), len(f['routes'])), (ops, records))
            self.assertEqual(f['summary_counts']['physical_records'], physical)
            self.assertEqual(f['summary_counts']['unresolved_input_groups'], unknowns)
            self.assertEqual(f['summary_counts']['control_records'], controls)

    def test_no_execution_projection_or_nonmanual_steps(self):
        for f in self.families.values():
            self.assertEqual(f['visibility'], 'author_evaluator_reference_only')
            self.assertFalse(f['actor_projection_implemented'])
            self.assertIn('not an actor projection', f['status'])
            for r in f['routes']:
                self.assertIn('not an actor projection', r['basis'])
                self.assertEqual(r['metadata_only'], not bool(ids(r['nodes'])))
                if r['source_file'] == 'nonmanual_scope.json':
                    self.assertEqual(ids(r['nodes']), []); self.assertNotEqual(r['route_kind'], 'physical')

    def test_every_svg_variant_matches_all_display_rows(self):
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
                count += 1
        self.assertEqual(count, 78)

    def test_json_javascript_and_immutable_source_pins(self):
        for key, f in self.families.items():
            js = (ROOT / 'data' / (key + '.js')).read_text().split('[' + json.dumps(key) + ']=', 1)[1].rsplit(';', 1)[0]
            self.assertEqual(json.loads(js), json.loads((ROOT / 'data' / (key + '.json')).read_text()))
            self.assertEqual(f['source_commit'], '41c4c52cfcf9d5b222404f2fd7ed9d6553f807cb')
            self.assertRegex(f['source_commit'], r'^[0-9a-f]{40}$')
            for name, entry in f['source_files'].items(): self.assertEqual(entry['url'], f['source_folder'] + name)

    def test_memberships_never_infer_adjacency_or_expand_unknown_repeats(self):
        for key in ('granular_assembly', 'thermal_jamming'):
            for r in self.families[key]['routes']:
                if r['route_kind'] != 'physical': continue
                self.assertEqual(r['nodes'][0]['type'], 'obligations')
                self.assertIs(r['nodes'][0]['ordered'], False)
                self.assertEqual(ids(r['nodes']), r['detail']['operation_ids'])
                for n in nodes(r):
                    if n['type'] == 'loop':
                        self.assertEqual(n['children'], []); self.assertIs(n['symbolic'], True)

    def test_beaded_all_choices_and_unexpanded_counts_are_distinct(self):
        f = self.families['beaded']; counts = collections.Counter()
        for r in f['routes']:
            for n in nodes(r):
                meta = n.get('meta', {}); src = meta.get('source_node', meta.get('source_attributes', {}))
                if 'type' in src: counts[src['type']] += 1
                if src.get('type') == 'choice':
                    self.assertIs(n['ordered'], False); self.assertIn('Exclusive alternatives', n['label'])
                if src.get('type') == 'loop': self.assertIs(n['symbolic'], True)
        self.assertEqual(dict(counts), {'operation': 741, 'sequence': 337, 'loop': 135, 'choice': 82, 'dispatch': 1})
        campaign = route(f, 'WHOLE_PAPER_PRACTICAL')
        self.assertEqual(campaign['route_kind'], 'campaign')
        self.assertEqual(ids(campaign['nodes']), ['QUARANTINE'])
        self.assertIn('Conditional recovery only', campaign['nodes'][1]['label'])

    def test_thermal_section_ids_are_navigation_only(self):
        f = self.families['thermal_jamming']
        for r in f['routes'][13:]:
            self.assertTrue(r['id'].startswith('SCOPE_'))
            self.assertIn('not a new scientific branch', r['detail']['display_identifier_basis'])
            self.assertEqual(r['detail']['source_section'], f['context']['nonmanual_scope'][r['source_pointer'][1:]])

    def test_all_operation_device_fields_retained_separately(self):
        for key in ('granular_assembly', 'thermal_jamming'):
            for op in self.families[key]['operations']:
                self.assertIsInstance(op['actions'], list)
                self.assertIn('device_actions', op['detail'])
        for op in self.families['beaded']['operations']:
            self.assertIn('tools', op['detail']); self.assertIn('device_handoff', op['detail'])
            self.assertFalse(op['detail']['feasibility']['physics_validated'])


@unittest.skipUnless(TASKS, 'SCIENCEGYM_TASKS not set; exact source checks not run')
class AssemblySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.families = {k: get(k) for k in KEYS}
        cls.adapted = {k: assembly.adapt(TASKS / (k + '_operations_v2'), k) for k in KEYS}

    def test_inverse_operation_fields_reconstruct_every_original(self):
        for key, f in self.families.items():
            source = raw(key, 'operations.json')['operations']
            self.assertEqual([o['id'] for o in f['operations']], [o['id'] for o in source])
            for op, original in zip(f['operations'], source):
                reconstructed = {'id': op['id'], **copy.deepcopy(op['detail'])}
                for name, normalized in INVERSE[key].items(): reconstructed[name] = op[normalized]
                self.assertEqual(reconstructed, original, (key, op['id']))
                self.assertEqual(pointer(raw(key, op['source_file']), op['source_pointer']), original)

    def test_exact_context_all_json_and_hashes(self):
        for key, f in self.families.items():
            package = TASKS / (key + '_operations_v2')
            names = {p.relative_to(package).as_posix() for p in package.rglob('*.json')}
            self.assertEqual(set(f['source_files']), names)
            for name in names:
                self.assertEqual(f['source_files'][name]['sha256'], hashlib.sha256((package / name).read_bytes()).hexdigest())
                if name not in ('operations.json', 'branches.json', 'dependencies.json'):
                    self.assertEqual(f['context'][ALIASES.get(name, name[:-5])], raw(key, name), (key, name))
            self.assertEqual(f['dependencies'], raw(key, 'dependencies.json'))
            self.assertEqual(f['context']['operation_policy'], {k:v for k,v in raw(key,'operations.json').items() if k != 'operations'})
            field = 'branches' if key == 'beaded' else 'configurations'
            self.assertEqual(f['context']['branch_policy'], {k:v for k,v in raw(key,'branches.json').items() if k != field})
            prov = raw(key, 'provenance.json'); evidence = prov.get('evidence', prov.get('references'))
            self.assertEqual(f['evidence'], byid(evidence) if isinstance(evidence, list) else evidence)

    def test_all_routes_exact_source_details(self):
        for key, f in self.families.items():
            for r in f['routes']:
                detail = r['detail']['source_section'] if r['id'].startswith('SCOPE_') else r['detail']
                self.assertEqual(detail, pointer(raw(key, r['source_file']), r['source_pointer']))

    def test_each_membership_dependency_control_repeat_matches_source(self):
        for key in ('granular_assembly', 'thermal_jamming'):
            f = self.families[key]
            controls = raw(key, 'control_packages.json')['control_packages' if key == 'granular_assembly' else 'controls']
            for record in raw(key, 'branches.json')['configurations']:
                r = route(f, record['id']); self.assertEqual(ids(r['nodes']), record['operation_ids'])
                dependencies = next(d for d in raw(key, 'dependencies.json')['routes'] if d['configuration_id'] == record['id'])
                self.assertEqual(r['nodes'][1]['meta']['source_contract'], dependencies)
                self.assertEqual(r['controls'], [byid(controls)[c] for c in record.get('control_package_ids', record.get('required_controls', []))])
                shown = [n['meta']['source_contract'] for n in nodes(r) if n['type'] == 'loop']
                self.assertEqual(shown, [dependencies['repeat_scope']] if 'repeat_scope' in dependencies else dependencies['loop_contracts'])

    def check_tree(self, original, shown, pointer_path):
        meta = shown['meta']; self.assertEqual(meta['source_pointer'], pointer_path)
        self.assertEqual(meta['source_file'], 'routes.json')
        typ = original['type']
        if typ == 'operation':
            self.assertEqual(shown['type'], 'op'); self.assertEqual(shown['id'], original['operation_id'])
            self.assertEqual(meta['source_node'], original); return
        child_field = {'sequence':'steps','loop':'body','choice':'alternatives','dispatch':None}[typ]
        self.assertEqual(meta['source_attributes'], {k:v for k,v in original.items() if k != child_field})
        if typ == 'sequence':
            self.assertIs(shown['ordered'], True); self.assertEqual(len(original['steps']), len(shown['children']))
            for i, (a,b) in enumerate(zip(original['steps'],shown['children'])): self.check_tree(a,b,pointer_path+'/steps/'+str(i))
        elif typ == 'loop':
            self.assertEqual(shown['type'], 'loop'); self.assertIs(shown['symbolic'], True)
            self.assertEqual(len(shown['children']),1); self.check_tree(original['body'],shown['children'][0],pointer_path+'/body')
        elif typ == 'choice':
            self.assertIs(shown['ordered'],False); self.assertEqual(len(original['alternatives']),len(shown['children']))
            for (key,value),arm in zip(original['alternatives'].items(),shown['children']):
                self.assertEqual(arm['meta']['selection'],key);self.assertEqual(len(arm['children']),1)
                self.check_tree(value,arm['children'][0],pointer_path+'/alternatives/'+key.replace('~','~0').replace('/','~1'))
        else:self.assertEqual(shown['children'],[])

    def test_beaded_authoritative_grammar_every_node_and_binding(self):
        f=self.families['beaded']
        for i,original in enumerate(raw('beaded','routes.json')['routes']):
            r=route(f,original['id']);self.check_tree(original['tree'],r['nodes'][0],f'/routes/{i}/tree')
            recovery=r['detail']['conditional_recovery_operation_ids']
            self.assertEqual(r['nodes'][1]['children'],recovery)
            self.assertIs(r['nodes'][1]['ordered'],False)
            self.assertLessEqual(set(ids(r['nodes'])),set(r['detail']['operation_ids'])|set(recovery))

    def test_bundled_decoded_payload_equals_fresh_projection(self):
        for key,f in self.families.items():
            self.assertEqual({k:v for k,v in f.items() if k!='shared'},self.adapted[key])
            self.assertTrue(assembly.validate_projection(self.adapted[key],TASKS/(key+'_operations_v2')))

    def reject(self,key,mutate):
        f=copy.deepcopy(self.adapted[key]);mutate(f)
        with self.assertRaises(ValueError):assembly.validate_projection(f,TASKS/(key+'_operations_v2'))

    def test_reject_reordered_or_dropped_memberships(self):
        for key in ('granular_assembly','thermal_jamming'):
            self.reject(key,lambda f:f['routes'][0]['nodes'][0]['children'].pop())
            self.reject(key,lambda f:f['routes'][0]['nodes'][0].__setitem__('ordered',True))
    def test_reject_changed_controls_unknowns_lineage_facts(self):
        for key in KEYS:
            for field in ('control_packages','unknowns','lineage','source_outcomes','source_conflicts'):
                self.reject(key,lambda f,field=field:f['context'].pop(field))
    def test_reject_lost_source_provenance_and_mutated_operation(self):
        for key in KEYS:
            self.reject(key,lambda f:f['source_files'].pop('provenance.json'))
            self.reject(key,lambda f:f['operations'][0]['actions'].append('fabricated execution'))
    def test_reject_promoted_nonmanual_measurements(self):
        for key in KEYS:
            self.reject(key,lambda f:f['routes'][-1]['nodes'].append('PLAN'))
            self.reject(key,lambda f:f['routes'][-1].__setitem__('route_kind','physical'))
    def test_reject_beaded_lost_choice_arm_or_empty_count(self):
        def change(f,typ,action):
            n=next(n for n in nodes(f['routes'][0]) if n.get('meta',{}).get('source_attributes',{}).get('type')==typ);action(n)
        self.reject('beaded',lambda f:change(f,'choice',lambda n:n['children'].pop()))
        self.reject('beaded',lambda f:change(f,'loop',lambda n:n['meta']['source_attributes'].__setitem__('values',[])))
    def test_reject_beaded_binding_and_campaign_concatenation(self):
        def binding(f):
            n=next(n for n in nodes(f['routes'][0]) if n['type']=='op' and n['id']=='MOVE');n['meta']['source_node']['bindings']['object_ids_from']='invented_same_sample'
        self.reject('beaded',binding)
        self.reject('beaded',lambda f:route(f,'WHOLE_PAPER_PRACTICAL')['nodes'][0]['children'].append('PLAN'))
    def test_reject_thermal_cycle_and_cold_arm_gate_changes(self):
        def change(f):
            d=next(d for d in f['dependencies']['routes'] if d['configuration_id']=='CYCLE_PULL');d['loop_contracts'][0]['last_cycle']='always omit reinsertion'
        self.reject('thermal_jamming',change)
        self.reject('thermal_jamming',lambda f:f['dependencies']['routes'][0].__setitem__('optional_cold_arm',None))
    def test_reject_granular_collision_arm_and_reset_gate_changes(self):
        self.reject('granular_assembly',lambda f:next(d for d in f['dependencies']['routes'] if d['configuration_id']=='TRAPPED_COLLISION').clear())
        self.reject('granular_assembly',lambda f:next(d for d in f['dependencies']['routes'] if d['configuration_id']=='TRAP_REUSE').clear())
    def test_reject_unread_sources_promoted_and_runtime_projection(self):
        for key in KEYS:
            self.reject(key,lambda f:f['context'].__setitem__('source_access_audit',{'all_sources_read':True}))
            self.reject(key,lambda f:f.__setitem__('actor_projection_implemented',True))
