"""Independent source-bound fidelity and adversarial projection checks; no execution."""
import copy
import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from test_semantics import ROOT, TASKS, builder, get, ids
import acoustic_adapters as acoustic

KEYS = ('wavefront', 'bianisotropic', 'edge')
EXPECTED = {'wavefront': (69, 18, 10, 8, 15, 45),
            'bianisotropic': (42, 14, 3, 11, 18, 46), 'edge': (46, 14, 7, 3, 14, 51)}

def routes(f): return {r['id']: r for r in f['routes']}
def raw(key, filename): return json.loads((TASKS / acoustic.PACKAGES[key] / filename).read_text())

class AcousticBundleTests(unittest.TestCase):
    def test_exact_counts_and_route_kinds(self):
        for key, (nops, nroutes, physical, numerical, unknown, edges) in EXPECTED.items():
            f = get(key)
            self.assertEqual((len(f['operations']), len(f['routes'])), (nops, nroutes))
            self.assertEqual(sum(r['route_kind'] == 'physical' for r in f['routes']), physical)
            self.assertEqual(sum(r['route_kind'] == 'numerical' for r in f['routes']), numerical)
            self.assertEqual(len(f['context']['unknowns']['unknowns']), unknown)
            self.assertEqual(len(f['dependencies']['edges']), edges)
        f = get('edge')
        self.assertEqual(sum(r['route_kind'] == 'prerequisite' for r in f['routes']), 3)
        self.assertEqual(sum(r['route_kind'] == 'campaign' for r in f['routes']), 1)

    def test_total_counts_and_existing_ten_preserved(self):
        manifest = [r for r in json.loads((ROOT / 'manifest.json').read_text())['families'] if r['id'] not in ('atmospheric_optics', 'afm_metrology', 'martian_geophysics', 'transistor', 'laser_control', 'solar_water', 'sucrose_metrology', 'actuator_metrology', 'woven', 'lockable_origami', 'varactor', 'wetting', 'arcmorph', 'midinfrared')]
        self.assertEqual((len(manifest), sum(r['routes'] for r in manifest), sum(r['operations'] for r in manifest)), (24, 541, 2189))
        old = [r for r in manifest if r['id'] not in (*KEYS, 'origami_memory', 'ring_origami', 'mechanical_backprop', 'granular_assembly', 'beaded', 'thermal_jamming', 'horn_acoustics', 'mechanical_logic', 'cold_shape', 'gear', 'hydrogel_optical')]
        self.assertEqual((len(old), sum(r['routes'] for r in old), sum(r['operations'] for r in old)), (10, 202, 1376))

    def test_all_new_svg_routes_are_unordered_and_parse(self):
        for key in KEYS:
            f = get(key)
            for r in f['routes']:
                candidate = copy.deepcopy(f); candidate['default_route'] = r['id']; text = builder.svg(candidate)
                ET.fromstring(text)
                self.assertNotIn('marker-end=', text)
                self.assertIn('No adjacency arrows', text)
                self.assertIn('NUMERICAL / THEORY', text)

    def test_no_physical_operations_in_metadata_only_numerical_routes(self):
        for key in ('wavefront', 'edge'):
            for r in get(key)['routes']:
                if r['route_kind'] == 'numerical':
                    self.assertEqual(ids(r['nodes']), [])
                    self.assertIn('NOT RUN', r['label'])

    def test_bianisotropic_numerical_actors(self):
        f = get('bianisotropic'); operations = {o['id']: o for o in f['operations']}
        for r in f['routes']:
            if r['route_kind'] == 'numerical':
                self.assertTrue(all(operations[oid]['detail']['kind'] == 'digital_job' for oid in ids(r['nodes'])))
        self.assertEqual({r['id'] for r in f['routes'] if r['route_kind'] == 'physical'}, {'PREPARE_60', 'QUALIFY_GUIDE', 'MEASURE_60'})

    def test_repeated_edge_transfers_and_exclusive_preparation(self):
        r = routes(get('edge'))
        self.assertEqual(ids(r['F_GUIDE']['nodes']).count('TRANSFER'), 4)
        choice = r['F_TARGET']['nodes'][0]
        self.assertEqual(choice['type'], 'choice'); self.assertFalse(choice['ordered'])
        manufactured, supplied = choice['children']
        self.assertIn('TARGET_PROCESS', ids([manufactured]))
        self.assertNotIn('TARGET_PROCESS', ids([supplied])); self.assertIn('TARGET_RECEIVE', ids([supplied]))
        self.assertEqual(ids([supplied]).count('TRANSFER'), 2)

    def test_campaign_closure_is_conditional_accounting(self):
        r = routes(get('edge'))['WHOLE_PAPER']
        self.assertEqual(r['route_kind'], 'campaign')
        self.assertEqual(r['nodes'][1]['type'], 'choice')
        self.assertEqual(ids([r['nodes'][1]['children'][0]]), r['detail']['required_closure_operation_ids'])
        self.assertEqual(ids([r['nodes'][1]['children'][1]]), r['detail']['abort_closure_operation_ids'])
        self.assertNotIn('MEASURE_POINT', ids(r['nodes']))

    def test_loop_counts_stay_null_or_source_values(self):
        self.assertTrue(all(l['repeat_count'] is None for l in get('wavefront')['dependencies']['loops']))
        b = routes(get('bianisotropic'))
        self.assertEqual([b[k]['detail']['loops'][0]['cell_count'] for k in ['GA_60', 'GA_70', 'GA_80']], [11, 4, 4])
        self.assertEqual(sum(len(r['detail'].get('loops', [])) for r in b.values()), 7)
        self.assertEqual(b['MEASURE_60']['detail']['loops'][1]['values'], [1, 2, 3, 4])
        self.assertIsNone(b['MEASURE_60']['detail']['independent_specimen_count'])
        loops = get('edge')['context']['branch_policy']['loops']
        self.assertEqual(loops[0]['count'], 4); self.assertTrue(all(l['count'] is None for l in loops[1:]))

    def test_loop_nodes_never_expand_additional_operations(self):
        for key in KEYS:
            for r in get(key)['routes']:
                for node, _ in builder.walk(r['nodes']):
                    if node['type'] == 'loop': self.assertEqual(node['children'], []); self.assertTrue(node['symbolic'])

    def test_actor_and_execution_boundary(self):
        for key in KEYS:
            f = get(key)
            self.assertEqual(f['visibility'], 'author_evaluator_reference_only')
            self.assertIs(f['actor_projection_implemented'], False)
            self.assertIn('no actor projection', f['status'])
            self.assertIn('RELEASE_BOUNDARY', f['context']); self.assertIn('source_outcomes', f['context'])
            self.assertNotIn('actor_payload', f)
        self.assertEqual(get('wavefront')['context']['agent_visible']['public_file_allowlist'], ['agent_visible.json'])

    def test_source_conflicts_complete(self):
        for key, field, count in [('wavefront', 'conflicts', 5), ('bianisotropic', 'records', 6), ('edge', 'conflicts', 8)]:
            self.assertEqual(len(get(key)['context']['source_conflicts'][field]), count)

    def test_unknowns_have_no_invented_defaults(self):
        for key, field in [('wavefront', 'default'), ('bianisotropic', 'value'), ('edge', 'default')]:
            self.assertTrue(all(u[field] is None for u in get(key)['context']['unknowns']['unknowns']))

    def test_known_source_scope_caveats_remain(self):
        wave = json.dumps(get('wavefront')['context'], ensure_ascii=False)
        bia = json.dumps(get('bianisotropic')['context'], ensure_ascii=False)
        edge = json.dumps(get('edge')['context'], ensure_ascii=False)
        for term in ['3000', 'historical', '20', '25', 'single', 'double']: self.assertIn(term, wave)
        for term in ['97', '89', '81', 'complex', 'install_epoch', 'U15']: self.assertIn(term, bia)
        for term in ['0.6', '1.6', '0.8', 'upper', 'source_byte_sha256']: self.assertIn(term, edge)

    def test_json_js_and_source_pins(self):
        for key in KEYS:
            f = get(key); self.assertEqual(f['source_commit'], acoustic.ACOUSTIC_COMMIT)
            for name, entry in f['source_files'].items():
                self.assertEqual(entry['url'], f['source_folder'] + name)
                self.assertIn(acoustic.ACOUSTIC_COMMIT, entry['url'])
            raw_json = json.loads((ROOT / 'data' / (key + '.json')).read_text())
            payload = (ROOT / 'data' / (key + '.js')).read_text().split('[' + json.dumps(key) + ']=', 1)[1].rsplit(';', 1)[0]
            self.assertEqual(raw_json, json.loads(payload))

@unittest.skipUnless(TASKS, 'SCIENCEGYM_TASKS not set; source comparison not run')
class AcousticSourceTests(unittest.TestCase):
    def test_every_context_json_record_exact(self):
        for key in KEYS:
            f = get(key); p = TASKS / acoustic.PACKAGES[key]
            for path in p.rglob('*.json'):
                name = path.relative_to(p).as_posix()
                if name not in ('operations.json', 'branches.json', 'dependencies.json'):
                    self.assertEqual(f['context'][acoustic.context_key(name)], json.loads(path.read_text()), (key, name))
            self.assertEqual(f['dependencies'], raw(key, 'dependencies.json'))

    def test_every_operation_field_can_reconstruct_source(self):
        for key in KEYS:
            f = get(key)
            for actual, original in zip(f['operations'], raw(key, 'operations.json')['operations']):
                restored = {'id': actual['id'], **actual['detail']}
                for normalized, source in acoustic.FIELDS[key].items(): restored[source] = actual[normalized]
                if key == 'wavefront': restored['authorship'] = actual['provenance']['authorship']
                self.assertEqual(restored, original, (key, original['id']))

    def test_every_route_detail_exact_source_pointer(self):
        for key in KEYS:
            for r in get(key)['routes']:
                self.assertEqual(r['detail'], acoustic.pointer(raw(key, r['source_file']), r['source_pointer']))

    def test_all_loop_metadata_exact(self):
        for key in KEYS:
            f = get(key)
            for r in f['routes']:
                shown = [n['meta']['source_contract'] for n, _ in builder.walk(r['nodes']) if n['type'] == 'loop']
                if key == 'wavefront' and r['route_kind'] == 'physical': self.assertEqual(shown[0]['loops'], raw(key, 'dependencies.json')['loops'])
                if key == 'bianisotropic': self.assertEqual(shown, r['detail'].get('loops', []))
                if key == 'edge':
                    ls = {l['id']: l for l in raw(key, 'branches.json')['loops']}
                    expected = [ls[lid] for lid in r['detail'].get('loop_ids', [])]
                    if r['id'] == 'F_RIG': expected = [ls['L_MIC']]
                    self.assertEqual(shown, expected)

    def test_source_file_inventory_and_hashes_exact(self):
        for key in KEYS:
            f = get(key); p = TASKS / acoustic.PACKAGES[key]
            self.assertEqual(set(f['source_files']), {x.relative_to(p).as_posix() for x in p.rglob('*.json')})
            for name, entry in f['source_files'].items(): self.assertEqual(entry['sha256'], hashlib.sha256((p / name).read_bytes()).hexdigest())

    def test_unpooled_validation_and_rebuild_match(self):
        for key in KEYS:
            f = builder.ADAPTERS[key](TASKS / acoustic.PACKAGES[key])
            acoustic.validate_projection(f, TASKS / acoustic.PACKAGES[key])
            self.assertEqual({k: v for k, v in get(key).items() if k != 'shared'}, f)

    def reject(self, key, mutation):
        f = builder.ADAPTERS[key](TASKS / acoustic.PACKAGES[key]); mutation(f)
        with self.assertRaises(ValueError): acoustic.validate_projection(f, TASKS / acoustic.PACKAGES[key])

    def test_reject_physical_id_in_numerical_disposition(self):
        self.reject('wavefront', lambda f: routes(f)['N_COUPLE']['nodes'][0]['children'].append('ARRAY_LOAD'))

    def test_reject_bianisotropic_branch_mixing(self):
        self.reject('bianisotropic', lambda f: routes(f)['NUM_70']['nodes'][0]['children'].append('POINT_ACQUIRE'))

    def test_reject_physical_relabeling_of_numerics(self):
        self.reject('bianisotropic', lambda f: routes(f)['RETRIEVAL_NUMERICAL'].__setitem__('route_kind', 'physical'))

    def test_reject_target_alternative_merging(self):
        self.reject('edge', lambda f: routes(f)['F_TARGET']['nodes'][0].__setitem__('type', 'obligations'))

    def test_reject_lost_transfer_occurrence(self):
        self.reject('edge', lambda f: routes(f)['F_GUIDE']['nodes'][0]['children'].remove('TRANSFER'))

    def test_reject_invented_default(self):
        for key, field in [('wavefront', 'default'), ('bianisotropic', 'value'), ('edge', 'default')]:
            self.reject(key, lambda f, field=field: f['context']['unknowns']['unknowns'][0].__setitem__(field, 1))

    def test_reject_loop_zero_replacement(self):
        self.reject('wavefront', lambda f: f['dependencies']['loops'][0].__setitem__('repeat_count', 0))
        self.reject('edge', lambda f: routes(f)['NO_OBJECT']['nodes'][2]['meta']['source_contract'].__setitem__('count', 1))

    def test_reject_flattened_branch_scoped_loop(self):
        self.reject('bianisotropic', lambda f: routes(f)['GA_70']['nodes'][1]['meta'].__setitem__('source_contract', routes(f)['GA_60']['detail']['loops'][0]))

    def test_reject_actor_export_and_execution_receipt(self):
        for key in KEYS:
            self.reject(key, lambda f: f.__setitem__('actor_payload', {'source_outcomes': f['context']['source_outcomes']}))
            self.reject(key, lambda f: f.__setitem__('actor_projection_implemented', True))
            self.reject(key, lambda f: f.__setitem__('execution_receipt', {'complete': True}))

    def test_reject_context_or_source_inventory_loss(self):
        self.reject('edge', lambda f: f['context'].pop('source_conflicts'))
        self.reject('wavefront', lambda f: f['source_files'].pop('source_access_audit.json'))

    def test_reject_invented_chronology(self):
        self.reject('edge', lambda f: routes(f)['DISC_2D']['nodes'][0].__setitem__('ordered', True))

    def test_reject_operation_state_or_authorship_rewrite(self):
        self.reject('wavefront', lambda f: f['operations'][0].__setitem__('post', ['executed']))
        self.reject('wavefront', lambda f: f['operations'][0]['provenance'].__setitem__('authorship', 'source_reported_robot_execution'))

    def test_reject_missing_handoff_or_terminal_policy(self):
        self.reject('wavefront', lambda f: routes(f)['APPARATUS']['nodes'].pop())

    def test_reject_campaign_closure_merging(self):
        self.reject('edge', lambda f: routes(f)['WHOLE_PAPER']['nodes'][1].__setitem__('type', 'obligations'))

    def test_reject_lost_numerical_status_label(self):
        self.reject('edge', lambda f: routes(f)['N_FE_1D'].__setitem__('label', 'Measured fields'))

    def test_reject_wrong_source_pin(self):
        self.reject('edge', lambda f: f['source_files']['branches.json'].__setitem__('url', 'https://github.com/openags/ScienceGym/blob/main/tasks/acoustic_edge_operations_v2/branches.json'))

if __name__ == '__main__': unittest.main()
