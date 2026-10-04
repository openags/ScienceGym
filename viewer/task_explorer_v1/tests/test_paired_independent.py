"""Independent typed source fidelity and boundary tests for paired-task views.

Source expectations deliberately do not import the adapter's maps or constants.
These tests inspect static representations only; no episode or apparatus runs.
"""
import collections
import copy
import hashlib
import json
import unittest
import xml.etree.ElementTree as ET

from test_semantics import ROOT, TASKS, builder, get, ids
import paired_adapters as paired

KEYS = ('laser_control', 'solar_water', 'sucrose_metrology', 'actuator_metrology')
PIN = 'f803612db28652d2e2dd574d8039c36b7136f399'
EXPECTED = {
    'laser_control': (44, 15, 16, 30, 20),
    'solar_water': (34, 15, 15, 30, 24),
    'sucrose_metrology': (37, 7, 12, 28, 12),
    'actuator_metrology': (32, 15, 17, 30, 14),
}
KINDS = {
    'laser_control': {'design_only': 9, 'closed_service': 6, 'failure_hold': 1},
    'solar_water': {'closed_service': 3, 'bounded_physical': 12},
    'sucrose_metrology': {'bounded_physical': 6, 'failure_hold': 1, 'session_teardown': 1, 'conditional_recovery': 4},
    'actuator_metrology': {'numerical': 11, 'preparation': 1, 'bounded_physical': 2, 'failure_hold': 1, 'conditional_recovery': 2},
}
ALIASES = {'unknown_parameters.json': 'unknowns', 'evaluator_reference.json': 'acceptance', 'lineage_contract.json': 'lineage'}
DEFAULTS = {'laser_control': 'QUALIFICATION_HOLD', 'solar_water': 'RECEIPT', 'sucrose_metrology': 'FLOW_HOLD', 'actuator_metrology': 'DIRECTION_HOLD'}


def package(key): return TASKS / (key + '_operations_v2')
def raw(key, filename): return json.loads((package(key) / filename).read_text())
def index(records): return {r['id']: r for r in records}
def canonical(value): return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
def pointer(document, path):
    for token in path.split('/')[1:]:
        token = token.replace('~1', '/').replace('~0', '~')
        document = document[int(token)] if isinstance(document, list) else document[token]
    return document


class PairedIndependentBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.families = {key: get(key) for key in KEYS}

    def test_counts_distinguish_branches_from_inspection_views(self):
        for key, f in self.families.items():
            ops, branches, views, documents, unknowns = EXPECTED[key]
            self.assertEqual((len(f['operations']), len(f['context']['branches']['branches']), len(f['routes']), len(f['source_files'])), (ops, branches, views, documents))
            self.assertEqual(collections.Counter(r['route_kind'] for r in f['routes']), KINDS[key])
            self.assertEqual(f['summary_counts']['unresolved_input_groups'], unknowns)
            self.assertEqual(f['default_route'], DEFAULTS[key])

    def test_navigation_keeps_all_operations_without_invented_adjacency(self):
        for key, f in self.families.items():
            all_ids = {o['id'] for o in f['operations']}
            self.assertEqual(all_ids, {oid for r in f['routes'] for oid in ids(r['nodes'])})
            for r in f['routes']:
                self.assertEqual(r['metadata_only'], not bool(ids(r['nodes'])))
                for node, _ in builder.walk(r['nodes']):
                    if node['type'] != 'op': self.assertIs(node['ordered'], False)
                    self.assertNotEqual(node['type'], 'loop')
                if r['id'].startswith('RECOVERY_'):
                    self.assertEqual(ids(r['nodes']), [r['id'].removeprefix('RECOVERY_')])
                    self.assertEqual(r['route_kind'], 'conditional_recovery')

    def test_typed_defaults_and_activation_exclusions(self):
        for f in self.families.values():
            self.assertEqual(f['visibility'], 'author_evaluator_reference_only')
            self.assertIs(f['actor_projection_implemented'], False)
        laser = self.families['laser_control']
        self.assertEqual(ids(index(laser['routes'])['QUALIFICATION_HOLD']['nodes']), ['REGISTER_INPUTS', 'HOLD_QUALIFICATION', 'ARCHIVE', 'CLEAN_STORE'])
        sucrose = self.families['sucrose_metrology']
        self.assertEqual(set(ids(index(sucrose['routes'])['FLOW_HOLD']['nodes'])), {'ARCHIVE', 'CLEAN_STORE', 'HOLD_FLOW_CONFLICT', 'SAFE_ISOLATE'})
        actuator = self.families['actuator_metrology']
        self.assertEqual(ids(index(actuator['routes'])['DIRECTION_HOLD']['nodes']), ['HOLD_DIRECTION', 'ARCHIVE', 'CLEAN_STORE'])
        self.assertNotIn('REQUEST_INPUT', ids(index(actuator['routes'])['DIRECTION_HOLD']['nodes']))

    def test_laser_source_scope_and_nonmeasurement_channels(self):
        f = self.families['laser_control']; c = f['context']
        self.assertEqual(f['family_scope'], 'paper_level_design')
        self.assertIs(c['RELEASE_BOUNDARY']['whole_paper_design_accounted_for'], True)
        self.assertIs(c['RELEASE_BOUNDARY']['whole_paper_execution_complete'], False)
        self.assertIs(c['control_packages']['source_outcomes_are_thresholds'], False)
        self.assertIs(c['lineage']['reference_channels_separate'], True)
        self.assertIs(c['lineage']['technical_repeats_are_independent_specimens'], False)
        self.assertIs(c['analysis_contracts']['physical_results_computed'], False)
        self.assertEqual(c['episode_input_contract']['default'], 'QUALIFICATION_HOLD')
        self.assertIn('cannot independently prove absolute frequency noise', c['analysis_contracts']['in_loop_interpretation'])
        controls = index(c['control_packages']['controls'])
        self.assertEqual(controls['SIN']['printed_density_kg_m3'], 329)
        self.assertIsNone(controls['DFB_MATCHED']['source_independent_replicate_count'])
        self.assertIs(c['lifecycle_contract']['service_completion_not_execution_by_this_package'], True)

    def test_solar_exclusions_null_unknowns_and_distinct_mass_records(self):
        c = self.families['solar_water']['context']
        self.assertIs(c['branches']['full_paper_complete'], False)
        self.assertIn('all biological operational work', c['nonmanual_scope']['excluded'])
        self.assertIs(c['material_cards']['all_water_nonpotable_for_task_purposes'], True)
        self.assertIs(c['source_outcomes']['potability_claim_allowed'], False)
        for unknown in c['unknowns']['parameters']:
            self.assertIsNone(unknown['value']); self.assertEqual(unknown['status'], 'unresolved')
        self.assertEqual(len(c['source_conflicts']['conflicts']), 14)
        for conflict in c['source_conflicts']['conflicts']:
            self.assertIs(conflict['silently_corrected'], False)
        self.assertIn('Evaporated mass and collected condensate have different raw records', c['lineage']['material_rules'])
        self.assertIs(c['lifecycle_contract']['command_does_not_prove_state'], True)
        self.assertIs(c['lifecycle_contract']['cleaning_invalidates_surface_baselines'], True)
        for control in c['control_packages']['controls']:
            for case in control['cases']:
                self.assertIs(case['physical_setpoints_not_authorized_by_source'], True)
                self.assertEqual(set(case['source_constraints']), set(case['field_provenance']))

    def test_sucrose_profiles_flow_and_session_teardown_are_separate(self):
        f = self.families['sucrose_metrology']; c = f['context']; routes = index(f['routes'])
        profiles = c['station_contracts']['profiles']
        self.assertEqual([(p['id'], p['plate_id'], p['wavelength_nm'], p['plate_height_um']) for p in profiles],
                         [('SPP2_1064', 'SPP2', 1064, 10.34), ('SPP5_1064', 'SPP5', 1064, 25.85), ('SPP5_532', 'SPP5', 532, 25.85)])
        self.assertEqual(c['station_contracts']['reference']['wavelength_nm'], 589.29)
        self.assertEqual(c['station_contracts']['flow']['default'], 'HOLD')
        self.assertIs(c['station_contracts']['flow']['agent_numeric_pump_setting_allowed'], False)
        self.assertEqual(index(c['source_conflicts'])['FLOW_40X']['values'], ['2 cc/min', 'approximately 50 µL/min with 1 mL withdrawal'])
        teardown = ['SAFE_ISOLATE', 'INVALIDATE_CALIBRATION', 'UNDOCK', 'INSPECT', 'ARCHIVE', 'CLEAN_STORE']
        self.assertEqual(ids(routes['SESSION_TEARDOWN']['nodes']), teardown)
        for name in ('CALIBRATE', 'INTERPOLATE', 'REPEATABILITY', 'DRIFT_NOISE'):
            self.assertEqual(routes[name]['detail']['session_teardown_operation_ids'], teardown)
            self.assertNotIn('UNDOCK', ids(routes[name]['nodes']))
            self.assertNotIn('INVALIDATE_CALIBRATION', ids(routes[name]['nodes']))
        self.assertIn('chip stays docked across dependent branches', c['lineage']['custody'])
        self.assertIn('Main figure 2-4 pixels', c['source_access_audit']['unread'])
        self.assertIs(c['analysis_contracts']['source_numeric_outcomes_are_pass_thresholds'], False)
        self.assertIs(c['analysis_contracts']['grid_simulation_implemented'], False)

    def test_actuator_direction_alternatives_projection_and_custody(self):
        f = self.families['actuator_metrology']; c = f['context']; routes = index(f['routes'])
        self.assertEqual(c['source_conflicts']['default_direction_state'], 'UNRESOLVED_HOLD')
        for conflict in c['source_conflicts']['conflicts']:
            self.assertIs(conflict['resolved'], False); self.assertIs(conflict['qualification_gate'], True)
        self.assertEqual(routes['FEM_VALIDATE']['detail']['depends_on'], [])
        self.assertEqual(routes['FEM_VALIDATE']['detail']['alternative_upstream_branches'], ['TRIANGULAR_SEARCH', 'AMORPHOUS_SEARCH'])
        self.assertIn('independently frozen human reference', routes['FEM_VALIDATE']['detail']['input_topology_route'])
        self.assertIs(c['branches']['source_fabrication_completion_credited'], False)
        self.assertIs(c['lineage']['prepared_specimen_does_not_complete_fabrication'], True)
        self.assertIs(c['lineage']['technical_repeats_are_independent_samples'], False)
        projection = index(c['analysis_contracts']['analyses'])['PROJECTED_DISPLACEMENT']
        self.assertIs(projection['negative_output_preserved'], True)
        self.assertIs(projection['input_denominator_must_be_positive'], True)
        self.assertIsNone(projection['source_physical_n'])
        self.assertIs(c['unknowns']['default_qualified'], False)
        self.assertEqual(c['lifecycle_contract']['safe_unmount_order'], ['RELEASE_INPUT', 'VERIFY_UNLOADED', 'UNFIX_BASE', 'RETRIEVE_SPECIMEN'])

    def test_json_javascript_and_docs_remain_consistent(self):
        for key, f in self.families.items():
            js = (ROOT / 'data' / (key + '.js')).read_text().split('[' + json.dumps(key) + ']=', 1)[1].rsplit(';', 1)[0]
            self.assertEqual(canonical(json.loads(js)), canonical(json.loads((ROOT / 'data' / (key + '.json')).read_text())))
            md = (ROOT / 'docs' / (key + '.md')).read_text()
            self.assertIn(f['family_scope_label'], md)
            self.assertIn(f['source_warnings'], md)
            self.assertIn('unordered source inventory', md)
            for r in f['routes']: self.assertIn('## ' + r['id'] + ' ', md)
            for asset in f['asset_links']: self.assertIn(asset['url'], md)

    def test_all_sixty_svg_views_parse_without_chronological_arrows(self):
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
                self.assertEqual([x for x in badges if x in index(f['operations'])], ids(r['nodes']))
                count += 1
        self.assertEqual(count, 60)


@unittest.skipUnless(TASKS, 'SCIENCEGYM_TASKS not set; source fidelity and mutations not run')
class PairedIndependentSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.families = {key: get(key) for key in KEYS}
        cls.adapted = {key: paired.adapt(package(key), key) for key in KEYS}

    def test_all_118_source_json_documents_are_preserved_with_strict_types(self):
        count = 0
        for key, f in self.families.items():
            names = {p.relative_to(package(key)).as_posix() for p in package(key).rglob('*.json')}
            self.assertEqual(set(f['source_files']), names)
            for name in names:
                self.assertEqual(canonical(f['context'][ALIASES.get(name, name.removesuffix('.json'))]), canonical(raw(key, name)), (key, name))
                self.assertEqual(f['source_files'][name]['sha256'], hashlib.sha256((package(key) / name).read_bytes()).hexdigest())
                self.assertEqual(f['source_files'][name]['url'], f'https://github.com/openags/ScienceGym/blob/{PIN}/tasks/{key}_operations_v2/{name}')
                count += 1
        self.assertEqual(count, 118)

    def test_all_147_operation_mappings_match_original_shapes(self):
        count = 0
        for key, f in self.families.items():
            originals = raw(key, 'operations.json')['operations']
            self.assertEqual(canonical([o['detail'] for o in f['operations']]), canonical(originals))
            for i, (op, source) in enumerate(zip(f['operations'], originals)):
                self.assertEqual(op['source_pointer'], '/operations/' + str(i))
                self.assertEqual(op['id'], source['id'])
                self.assertIsNone(op['loop'])
                self.assertIn('No post-state field supplied', op['post'])
                if key == 'solar_water':
                    for target, original in [('title', 'title'), ('actions', 'robot_actions'), ('recovery', 'failure_recovery'), ('provenance', 'source_vs_authored'), ('acceptance', 'required_receipt_fields')]:
                        self.assertEqual(canonical(op[target]), canonical(source[original]))
                    self.assertIn('No per-operation objects field supplied', op['objects'])
                else:
                    for target, original in [('objects', 'asset_ids'), ('pre', 'precondition'), ('acceptance', 'required_output'), ('recovery', 'failure'), ('provenance', 'origin')]:
                        self.assertEqual(canonical(op[target]), canonical(source[original]))
                    self.assertIn('No actions field supplied', op['actions'][0])
                self.assertEqual(op['sources'], source.get('source_evidence_ids', []))
                count += 1
        self.assertEqual(count, 147)

    def test_every_route_and_contract_pointer_resolves_exactly(self):
        for key, f in self.families.items():
            source_branches = raw(key, 'branches.json')['branches']
            routes = index(f['routes'])
            for branch in source_branches:
                expected = ([o['id'] for o in raw(key, 'operations.json')['operations'] if branch['id'] in o['branch_ids']]
                            if key == 'laser_control' else branch['operation_ids'])
                self.assertEqual(ids(routes[branch['id']]['nodes']), expected)
                self.assertEqual(canonical(routes[branch['id']]['detail']), canonical(branch))
            for r in f['routes']:
                original = pointer(raw(key, r['source_file']), r['source_pointer'])
                self.assertEqual(canonical(r['detail']['source_record'] if r.get('detail_source_wrapper') else r['detail']), canonical(original))
                for node, _ in builder.walk(r['nodes']):
                    if node['type'] == 'condition':
                        m = node['meta']
                        self.assertEqual(canonical(m['source_contract']), canonical(pointer(raw(key, m['source_file']), m['source_pointer'])))

    def test_source_evidence_namespaces_remain_resolvable_without_fabrication(self):
        for key, f in self.families.items():
            source_map = raw(key, 'provenance.json')['evidence'] if key == 'solar_water' else raw(key, 'evidence_map.json')
            original = source_map['evidence'] if isinstance(source_map, dict) else source_map
            for record in original: self.assertEqual(canonical(f['evidence'][record['id']]), canonical(record))
            for b in raw(key, 'branches.json')['branches']:
                self.assertTrue(set(b['source_evidence_ids']) <= set(f['evidence']))
        f = self.families['laser_control']; source = raw('laser_control', 'evidence_map.json')
        for ref in source['source_reference_ids']:
            self.assertEqual(f['evidence'][ref]['related_evidence_ids'], [e['id'] for e in source['evidence'] if ref in e['sources']])

    def test_paired_asset_links_match_read_only_existing_files_and_hashes(self):
        asset_keys = {'laser_control': 'laser', 'sucrose_metrology': 'sucrose', 'actuator_metrology': 'actuator'}
        for key, f in self.families.items():
            self.assertEqual(f['source_commit'], PIN)
            if key == 'solar_water': self.assertEqual(f['asset_links'], []); continue
            directory = TASKS.parent / 'assets' / (asset_keys[key] + '_scene_assets_v1')
            expected = {'README.md'} | {p.relative_to(directory).as_posix() for p in (directory / 'evidence').glob('*.png')}
            self.assertEqual({a['path'].split('/', 2)[2] for a in f['asset_links']}, expected)
            for asset in f['asset_links']:
                self.assertEqual(asset['url'], f'https://github.com/openags/ScienceGym/blob/{PIN}/' + asset['path'])
                self.assertEqual(asset['sha256'], hashlib.sha256((TASKS.parent / asset['path']).read_bytes()).hexdigest())

    def reject(self, key, mutation):
        candidate = copy.deepcopy(self.adapted[key]); mutation(candidate)
        with self.assertRaises(ValueError): paired.validate_projection(candidate, package(key))

    def test_reject_omissions_fabricated_commands_chronology_and_scope_changes(self):
        mutations = [lambda f: f['operations'].pop(), lambda f: f['routes'].pop(),
                     lambda f: f['operations'][0]['detail'].pop('id'),
                     lambda f: f['operations'][0].__setitem__('actions', ['activate equipment']),
                     lambda f: f['routes'][0]['nodes'][0].__setitem__('ordered', True),
                     lambda f: f['routes'][0]['nodes'][0]['children'].pop(),
                     lambda f: f['context'].__setitem__('lineage', {}),
                     lambda f: f['context'].__setitem__('unknowns', {}),
                     lambda f: f['context'].__setitem__('source_conflicts', {}),
                     lambda f: f.__setitem__('source_commit', 'main'),
                     lambda f: f.__setitem__('visibility', 'actor'),
                     lambda f: f.__setitem__('actor_projection_implemented', True)]
        for key in KEYS:
            for i, mutation in enumerate(mutations):
                with self.subTest(key=key, mutation=i): self.reject(key, mutation)

    def test_reject_boolean_integer_aliases_in_source_and_display(self):
        for key in KEYS:
            with self.subTest(key=key, field='display'):
                self.reject(key, lambda f: f.__setitem__('actor_projection_implemented', 0))
            with self.subTest(key=key, field='source'):
                self.reject(key, lambda f: f['context']['branches']['branches'][0].__setitem__('physical_executed' if key == 'laser_control' else 'physical_execution_implemented', 0))

    def test_reject_hold_profile_lineage_and_fabrication_promotions(self):
        cases = [('laser_control', lambda f: f.__setitem__('default_route', 'DFB1_STABILIZATION')),
                 ('laser_control', lambda f: f['context']['lineage'].__setitem__('reference_channels_separate', False)),
                 ('solar_water', lambda f: f['context']['material_cards'].__setitem__('all_water_nonpotable_for_task_purposes', False)),
                 ('solar_water', lambda f: f['context']['unknowns']['parameters'][0].__setitem__('value', 1)),
                 ('sucrose_metrology', lambda f: f.__setitem__('default_route', 'CALIBRATE')),
                 ('sucrose_metrology', lambda f: f['context']['station_contracts']['profiles'][0].__setitem__('wavelength_nm', 532)),
                 ('sucrose_metrology', lambda f: f['context']['station_contracts']['flow'].__setitem__('agent_numeric_pump_setting_allowed', True)),
                 ('sucrose_metrology', lambda f: index(f['routes'])['INTERPOLATE']['nodes'][0]['children'].append('UNDOCK')),
                 ('actuator_metrology', lambda f: f.__setitem__('default_route', 'PHYSICAL_ORTHOGONAL')),
                 ('actuator_metrology', lambda f: f['context']['source_conflicts'].__setitem__('default_direction_state', 'RESOLVED')),
                 ('actuator_metrology', lambda f: index(f['routes'])['FEM_VALIDATE']['detail'].__setitem__('depends_on', ['TRIANGULAR_SEARCH', 'AMORPHOUS_SEARCH'])),
                 ('actuator_metrology', lambda f: f['context']['lineage'].__setitem__('prepared_specimen_does_not_complete_fabrication', False))]
        for i, (key, mutation) in enumerate(cases):
            with self.subTest(key=key, mutation=i): self.reject(key, mutation)


if __name__ == '__main__': unittest.main()
