"""Independent frozen-conformal projection and hostile-pair regression tests.

Expectations come from the task/asset records, not adapter projection helpers.
All changed bytes live in temporary copies. These checks establish static
inspection fidelity only, not paper rereading, solver or physical execution.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = (Path(os.environ['SCIENCEGYM_ROOT']).resolve() if 'SCIENCEGYM_ROOT' in os.environ
        else Path(__file__).resolve().parents[3])
VIEWER = ROOT / 'viewer/task_explorer_v1'
TASK = ROOT / 'tasks/conformal_operations_v3_compressed'
ASSET = ROOT / 'assets/conformal_scene_assets_v2_compressed'
sys.path.insert(0, str(VIEWER))
import conformal_adapters as adapter

ALIASES = {'unknown_parameters.json': 'unknowns', 'evaluator_reference.json': 'acceptance',
           'lineage_contract.json': 'lineage'}
ASSET_PINS = {'affordances.json', 'assembly_contract.json', 'asset_inventory.json',
              'asset_metadata.json', 'geometry/conformal_lab.blend',
              'geometry/conformal_lab.glb', 'operation_binding_contract.json',
              'operation_bindings.json', 'semantic_controls.py', 'specimen_geometry.json',
              'states.json'}
TASK_PINS = {'operations.json', 'branches.json', 'unknown_parameters.json',
             'controls_and_repeats.json', 'lineage_contract.json', 'tests/contract.py',
             'tests/verify_pairing.py', 'RELEASE_BOUNDARY.json', 'asset_binding_plan.json'}
REFERENCE_FILES = {'OPERATIONS_REFERENCE': 'operations.json',
                   'PREPARATION_REFERENCE': 'preparation_routes.json',
                   'CONTROLS_REFERENCE': 'controls_and_repeats.json',
                   'RECOVERY_REFERENCE': 'recovery_boundaries.json',
                   'NONMANUAL_REFERENCE': 'nonmanual_scope.json'}
BRANCH_KINDS = {'B01': 'physical_preparation', 'B02': 'physical_experiment',
                'B03': 'physical_experiment', 'B04': 'numerical_source_scope_unexecuted',
                'B05': 'numerical_source_scope_unexecuted',
                'B06': 'analysis_of_physical_and_numerical_data_kept_separate',
                'B07': 'analytical_source_scope_unexecuted',
                'B08': 'numerical_source_scope_unexecuted', 'B09': 'authored_translation'}


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unpool(family, value):
    if isinstance(value, dict):
        if set(value) == {'$shared'}:
            return unpool(family, family['shared'][value['$shared']])
        return {key: unpool(family, item) for key, item in value.items()}
    if isinstance(value, list):
        return [unpool(family, item) for item in value]
    return value


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.get('children', []))


def pointer(document, path):
    if path:
        assert path.startswith('/')
        for token in path[1:].split('/'):
            token = token.replace('~1', '/').replace('~0', '~')
            document = document[int(token)] if isinstance(document, list) else document[token]
    return document


class ConformalIndependent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = {p.relative_to(TASK).as_posix(): load(p) for p in TASK.rglob('*.json')}
        cls.pooled = load(VIEWER / 'data/conformal.json')
        cls.generated = unpool(cls.pooled, cls.pooled)
        cls.live = adapter.adapt_conformal(TASK)
        cls.temp = tempfile.TemporaryDirectory(prefix='conformal-independent-')
        cls.copy_root = Path(cls.temp.name)
        cls.copy_task = cls.copy_root / 'tasks/conformal_operations_v3_compressed'
        cls.copy_asset = cls.copy_root / 'assets/conformal_scene_assets_v2_compressed'
        shutil.copytree(TASK, cls.copy_task)
        shutil.copytree(ASSET, cls.copy_asset)
        cls.families = [cls.live, cls.generated]

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_recursive_json_context_and_source_bytes_are_lossless(self):
        self.assertEqual(len(self.docs), 34)
        expected = {ALIASES.get(name, name.removesuffix('.json')): doc
                    for name, doc in self.docs.items()}
        self.assertEqual(len(expected), len(self.docs), 'No context-key collisions')
        self.assertIn('review/INDEPENDENT_REVIEW', expected)
        for family in self.families:
            self.assertEqual(family['context'], expected)
            self.assertEqual(set(family['source_files']), set(self.docs))
            for name, item in family['source_files'].items():
                with self.subTest(file=name):
                    self.assertEqual(item, {
                        'url': '../../tasks/conformal_operations_v3_compressed/' + name,
                        'repository_path': 'tasks/conformal_operations_v3_compressed/' + name,
                        'sha256': digest(TASK / name)})
                    self.assertEqual(load((VIEWER / item['url']).resolve()), self.docs[name])

    def test_generated_json_js_and_live_projection_agree(self):
        expanded = copy.deepcopy(self.generated)
        expanded.pop('shared')
        self.assertEqual(expanded, self.live)
        js = (VIEWER / 'data/conformal.js').read_text(encoding='utf-8')
        prefix = 'window.SCIENCEGYM_DATA=window.SCIENCEGYM_DATA||{};window.SCIENCEGYM_DATA["conformal"]='
        self.assertTrue(js.startswith(prefix))
        self.assertEqual(json.loads(js[len(prefix):].strip().removesuffix(';')), self.pooled)

    def test_all_16_operations_are_exact_authored_unexecuted_contracts(self):
        raw = self.docs['operations.json']['operations']
        self.assertEqual([o['id'] for o in raw], [f'R{i:02}' for i in range(1, 17)])
        for family in self.families:
            self.assertEqual(len(family['operations']), 16)
            for index, (source, mapped) in enumerate(zip(raw, family['operations'])):
                with self.subTest(operation=source['id']):
                    self.assertEqual(mapped['id'], source['id'])
                    self.assertEqual(mapped['detail'], source)
                    self.assertEqual(mapped['title'], source['name'])
                    self.assertEqual(mapped['stage'], source['station'])
                    self.assertEqual(mapped['actions'], source['substeps'])
                    self.assertEqual(mapped['objects'], {'asset_ids': source['asset_ids'], 'required_inputs': source['inputs']})
                    self.assertEqual(mapped['pre'], source['entry_guards'])
                    self.assertEqual(mapped['post'], 'No observed post-state field supplied; inspect the exact source contract. No value or command is inferred.')
                    self.assertEqual(mapped['acceptance'], {k: source[k] for k in ['outputs', 'observations_to_record', 'evidence_role', 'service_request_is_completion']})
                    self.assertEqual(mapped['recovery'], {'failure_closeout': source['failure_closeout']})
                    self.assertEqual(mapped['unknowns'], source['execution_gaps'])
                    self.assertEqual(mapped['sources'], source['source_anchors'])
                    self.assertEqual(mapped['provenance'], {'classification': 'authored_robot_translation', 'physical_execution_qualified': False, 'runtime': 'unimplemented'})
                    self.assertIs(mapped['loop'], None)
                    self.assertEqual(mapped['source_pointer'], f'/operations/{index}')
                    self.assertEqual(pointer(self.docs[mapped['source_file']], mapped['source_pointer']), source)
                    self.assertIs(source['service_request_is_completion'], False)
                    self.assertIn('not a paper quotation', mapped['display_title_basis'])

    def test_nine_branch_classifications_and_all_membership_pointers(self):
        branches = self.docs['branches.json']['branches']
        self.assertEqual({b['id']: b['classification'] for b in branches}, BRANCH_KINDS)
        self.assertEqual(self.docs['branches.json']['physical_experiment_ids'], ['B02', 'B03'])
        self.assertEqual(self.docs['branches.json']['nonmanual_source_scope_ids'], ['B04', 'B05', 'B07', 'B08'])
        for family in self.families:
            routes = [r for r in family['routes'] if r['source_file'] == 'branches.json']
            self.assertEqual(len(routes), 9)
            self.assertEqual([r['id'] for r in routes if r['route_kind'] == 'physical_experiment'], ['B02', 'B03'])
            for source, route in zip(branches, routes):
                with self.subTest(branch=source['id']):
                    self.assertEqual(route['detail'], source)
                    self.assertEqual(route['route_kind'], BRANCH_KINDS[source['id']])
                    self.assertEqual(pointer(self.docs[route['source_file']], route['source_pointer']), source)
                    nodes = list(walk(route['nodes']))
                    self.assertEqual([n['id'] for n in nodes if n['type'] == 'op'], source['route_operations'])
                    self.assertEqual([n['meta']['source_contract'] for n in nodes if n['type'] == 'condition'], [source])
                    for node in nodes:
                        if node['type'] == 'op':
                            meta = node['meta']
                            self.assertEqual(pointer(self.docs[meta['source_file']], meta['source_pointer']), node['id'])
                            self.assertIn('not execution, chronology or a new specimen', meta['meaning'])
                        else:
                            self.assertIs(node['ordered'], False)
                    if source['id'] in ['B04', 'B05', 'B07', 'B08']:
                        self.assertEqual(source['execution_status'], 'DOCUMENTED_UNEXECUTED')
                        self.assertEqual(source['route_operations'], ['R14'])
                    else:
                        self.assertEqual(source['execution_status'], 'HOLD_QUALIFICATION')

    def test_15_views_five_references_and_nonactivating_default_hold(self):
        for family in self.families:
            routes = {r['id']: r for r in family['routes']}
            self.assertEqual(len(routes), 15)
            self.assertEqual(set(routes), set(BRANCH_KINDS) | set(REFERENCE_FILES) | {'HOLD_QUALIFICATION'})
            self.assertEqual(family['default_route'], 'HOLD_QUALIFICATION')
            self.assertEqual(family['default_route'], self.docs['episode_input_contract.json']['default'])
            self.assertNotIn(family['default_route'], [o['id'] for o in family['operations']])
            for identifier, name in {**REFERENCE_FILES, 'HOLD_QUALIFICATION': 'episode_input_contract.json'}.items():
                route = routes[identifier]
                self.assertEqual(route['detail'], self.docs[name])
                self.assertEqual(route['source_file'], name)
                self.assertEqual(route['source_pointer'], '')
                nodes = list(walk(route['nodes']))
                self.assertEqual([n['meta']['source_contract'] for n in nodes if n['type'] == 'condition'], [self.docs[name]])
                occurrences = [n for n in nodes if n['type'] == 'op']
                if identifier == 'OPERATIONS_REFERENCE':
                    self.assertIs(route['metadata_only'], False)
                    self.assertEqual([n['id'] for n in occurrences], [o['id'] for o in self.docs['operations.json']['operations']])
                    for node in occurrences:
                        self.assertEqual(pointer(self.docs[node['meta']['source_file']], node['meta']['source_pointer']), node['id'])
                else:
                    self.assertIs(route['metadata_only'], True)
                    self.assertEqual(occurrences, [])
            self.assertEqual(sum(n['type'] == 'op' for r in routes.values() for n in walk(r['nodes'])), 47)

    def test_summary_counts_derive_from_separate_source_categories(self):
        expected = {'source_scope_branches': 9, 'physical_experimental_branches': 2,
                    'documented_unexecuted_nonmanual_branches': 4, 'authored_reference_views': 5,
                    'metadata_only_hold_views': 1, 'source_json_documents': 34,
                    'operation_templates': 16, 'source_evidence_entries': 28, 'source_conflicts': 5,
                    'unresolved_input_groups': 16, 'controls': 9, 'stations': 8,
                    'scene_groups': 12, 'symbolic_anchors': 32, 'task_pinned_asset_hashes': 11}
        for family in self.families:
            self.assertEqual(family['summary_counts'], expected)

    def test_unknowns_conflicts_no_guessed_counts_and_source_rates(self):
        for family in self.families:
            context = family['context']
            unknowns = context['unknowns']['unknowns']
            self.assertEqual([u['id'] for u in unknowns], [f'U{i:02}' for i in range(1, 17)])
            for unknown in unknowns:
                self.assertIs(unknown['physical_default'], None)
                self.assertIs(unknown['execution_blocking'], True)
                self.assertIs(unknown['resolution_requires_independent_evidence'], True)
            self.assertEqual([c['id'] for c in context['source_conflicts']['conflicts']], [f'C{i:02}' for i in range(1, 6)])
            conflicts = context['source_conflicts']['conflicts']
            self.assertEqual(conflicts[-1]['reported_Pa_m3'], 125)
            self.assertEqual(conflicts[-1]['arithmetic_result_Pa_m3'], 15.663459025787105)
            controls = context['controls_and_repeats']
            self.assertEqual([c['id'] for c in controls['controls']], [f'K{i:02}' for i in range(1, 10)])
            for key in ['independent_specimens', 'runs_per_condition', 'cycle_order', 'recovery_criterion', 'stopping_rule']:
                self.assertIs(controls['repeat_policy'][key], None)
            self.assertIs(controls['frames_are_not_independent_specimens'], True)
            self.assertIs(context['episode_input_contract']['physical_numeric_defaults'], None)
            for branch, stroke, speed in [(context['branches']['branches'][1], 20, 0.1), (context['branches']['branches'][2], 40, 0.2)]:
                self.assertEqual(branch['source_reference_cycle'], {'stroke_mm': stroke, 'speed_mm_s': speed, 'frames': 400, 'acquisition_fps': 1, 'playback_fps': 30, 'hardware_command': False, 'safety_threshold': False})
            self.assertIn('never operating defaults or independent n', family['source_warnings'])
            self.assertIn('not independent specimens or repeats', family['status'])
            self.assertIn('do not determine an exact specimen topology', family['source_warnings'])

    def test_source_facts_authored_translation_and_results_stay_distinct(self):
        expected = {fact['id']: fact for fact in self.docs['source_parameters.json']['facts']}
        for family in self.families:
            self.assertEqual(family['evidence'], expected)
            self.assertEqual(family['evidence']['F27']['classification'], 'source_media_observation')
            self.assertEqual(family['evidence']['F28']['classification'], 'source_fact_numerical_only')
            self.assertEqual(family['context']['lineage']['classification'], 'authored_robot_translation')
            self.assertEqual(family['visibility'], 'author_evaluator_reference_only')
            self.assertIs(family['actor_projection_implemented'], False)
            outcomes = family['context']['source_outcomes']
            self.assertEqual(outcomes['visibility'], 'evaluator_reference_only')
            self.assertTrue(all(o['not_for_agent_target'] is True for o in outcomes['outcomes']))
            self.assertIs(outcomes['no_new_scientific_result'], True)
            analysis = family['context']['analysis_contracts']
            for key in ['implemented_scientific_solver', 'literature_99_percent_is_global_pass_threshold', 'ideal_alpha_interval_is_safety_limit']:
                self.assertIs(analysis[key], False)
            self.assertIs(analysis['physical_and_numerical_separate'], True)
            self.assertIs(analysis['boundary_inference']['alpha_linear_and_J_area_distinct'], True)
            self.assertIsNone(analysis['fit']['model_order'])
            self.assertIsNone(analysis['boundary_inference']['model_order'])
            self.assertIn('never interior target displacement fitting', analysis['boundary_inference']['input_scope'])
            self.assertEqual(family['context']['nonmanual_scope']['branch_ids'], ['B04', 'B05', 'B07', 'B08'])
            boundary = family['context']['RELEASE_BOUNDARY']
            self.assertEqual(boundary['validated_runnable_whole_paper_tasks'], 0)
            for key in ['whole_paper_execution_complete', 'physical_execution', 'physical_simulation', 'scientific_reproduction', 'source_data_reanalysis', 'source_files_exported', 'exact_geometry_validated', 'hardware_safety_qualified']:
                self.assertIs(boundary[key], False)

    def test_source_access_limits_and_movie_sampling_are_retained(self):
        audit = self.generated['context']['source_access_audit']
        sources = {s['id']: s for s in audit['sources']}
        self.assertEqual([sources[k]['page_count'] for k in ['MAIN', 'SI', 'MEDIA_DESCRIPTION']], [9, 16, 1])
        self.assertEqual(len(audit['media']), 3)
        for media, sample, frames, fps in zip(audit['media'], [[0, 99, 199, 299, 399], [0, 99, 199, 299, 399], [0, 133, 266, 400, 533]], ['400', '400', '534'], ['30/1', '30/1', '10/1']):
            self.assertIs(media['decode_all_frames_succeeded'], True)
            self.assertEqual(media['sampled_frame_numbers'], sample)
            self.assertIn('not continuous full-movie visual analysis', media['visual_review'])
            self.assertEqual(media['technical_metadata']['streams'][0]['nb_frames'], frames)
            self.assertEqual(media['technical_metadata']['streams'][0]['r_frame_rate'], fps)
            self.assertIs(media['exported'], False)
        archive = audit['data_code_archive_status']
        self.assertEqual(archive['read_scope'], 'record metadata only')
        self.assertEqual(len(archive['archives']), 6)
        self.assertTrue(all(a['contents_read'] is False for a in archive['archives']))
        self.assertIs(archive['source_code_executed'], False)
        self.assertIs(archive['final_journal_figure_equivalence_verified'], False)
        self.assertIn('Zenodo archive contents remain unread', self.generated['source_warnings'])
        self.assertIn('No new paper reread', self.generated['source_warnings'])

    def test_preparation_custody_epochs_failure_history_and_dependencies_exact(self):
        for family in self.families:
            for name in ['dependencies', 'preparation_routes', 'lifecycle_contract', 'lineage_contract', 'transport_routes', 'recovery_boundaries']:
                self.assertEqual(family['dependencies'][name], self.docs[name + '.json'])
            self.assertEqual(family['dependencies']['operation_dependencies'], [{'operation_id': o['id'], 'depends_on': o['depends_on']} for o in self.docs['operations.json']['operations']])
            context = family['context']
            self.assertIs(context['preparation_routes']['request_is_completion'], False)
            self.assertIsNone(context['preparation_routes']['service_internal_instructions'])
            self.assertIn('bridge treatment requires an independent declared policy', context['preparation_routes']['powder_scope'])
            self.assertIs(context['lifecycle_contract']['supported_hold_is_execution_complete'], False)
            self.assertIs(context['lifecycle_contract']['failure_requires_analysis_success'], False)
            self.assertIn('Camera movement invalidates geometric calibration', context['lifecycle_contract']['epoch_invalidation'])
            recovery = context['recovery_boundaries']
            self.assertIs(recovery['safe_request_is_safe_observation'], False)
            self.assertIn('immutable failure ID', recovery['failure_ledger'])
            self.assertIn('prior-failure link', recovery['retry'])
            self.assertIn('independently issued unloaded/disarmed and safe-release receipts', recovery['safe_return'])

    def test_all_11_asset_pins_nine_reciprocal_hashes_and_32_anchors(self):
        plan = self.generated['context']['asset_binding_plan']
        pins = plan['final_asset_hashes']
        self.assertEqual(len(pins), 11)
        self.assertEqual({p['path'] for p in pins}, ASSET_PINS)
        for pin in pins:
            self.assertEqual((ASSET / pin['path']).stat().st_size, pin['bytes'])
            self.assertEqual(digest(ASSET / pin['path']), pin['sha256'])
        snapshot = load(ASSET / 'task_binding_snapshot.json')
        self.assertEqual(snapshot['binding_plan'], plan)
        self.assertEqual(snapshot['task_files'], load(ASSET / 'paired_task_receipt.json')['task_files'])
        self.assertEqual(len(snapshot['task_files']), 9)
        self.assertEqual({p['task_file'] for p in snapshot['task_files']}, TASK_PINS)
        for pin in snapshot['task_files']:
            self.assertEqual((TASK / pin['task_file']).stat().st_size, pin['bytes'])
            self.assertEqual(digest(TASK / pin['task_file']), pin['sha256'])
        bindings = load(ASSET / 'operation_binding_contract.json')['operations']
        self.assertEqual(bindings, load(ASSET / 'operation_bindings.json')['bindings'])
        by_id = {o['operation_id']: o for o in bindings}
        anchors = {a['name']: a for a in load(ASSET / 'affordances.json')['anchors']}
        owners = {o['name']: a['id'] for a in load(ASSET / 'asset_inventory.json')['assets'] for o in a['objects']}
        self.assertEqual(len(plan['operation_bindings']), 16)
        operation_anchors = {a for b in plan['operation_bindings'] for a in b['anchor_ids']}
        self.assertEqual(len(operation_anchors), 32)
        self.assertTrue(operation_anchors <= set(anchors))
        self.assertEqual(operation_anchors, {f'ANCHOR.R{i:02}.{role}' for i in range(1, 17) for role in ['primary', 'control']})
        for binding, operation in zip(plan['operation_bindings'], self.docs['operations.json']['operations']):
            scene = by_id[binding['operation_id']]
            self.assertEqual(binding['operation_id'], operation['id'])
            self.assertEqual(binding['asset_ids'], operation['asset_ids'])
            for key in ['asset_ids', 'primary_asset_id', 'primary_target', 'control_target']:
                self.assertEqual(binding[key], scene[key])
            self.assertEqual(binding['root_node_ids'], ['ASSET.' + a for a in binding['asset_ids']])
            self.assertIs(binding['physical_qualified'], False)
            for role in ['primary', 'control']:
                anchor = anchors[scene[role + '_anchor']]
                self.assertEqual(anchor['target_mesh'], scene[role + '_target'])
                self.assertEqual(anchor['owner'], owners[anchor['target_mesh']])
                self.assertEqual(anchor['owner'], binding['primary_asset_id'])
                self.assertEqual(anchor['position_m'], binding['anchor_positions_m'][anchor['name']])
                self.assertIs(anchor['qualified_pose'], False)
                self.assertIs(anchor['physical_execution_enabled'], False)

    def test_local_asset_links_are_exact_original_bytes(self):
        for family in self.families:
            self.assertEqual({a['path'] for a in family['asset_links']}, {'assets/conformal_scene_assets_v2_compressed/' + n for n in ['README.md', 'evidence/overview.png', 'evidence/specimen.png', 'evidence/stations.png']})
            for item in family['asset_links']:
                self.assertEqual(item['url'], '../../' + item['path'])
                self.assertEqual(digest(ROOT / item['path']), item['sha256'])
                self.assertEqual((VIEWER / item['url']).resolve(), ROOT / item['path'])
            self.assertIn('unqualified', family['asset_boundary'])
            self.assertEqual(family['source_link_mode'], 'repository_relative_frozen_local_snapshot')
            self.assertIn('remote publication is not asserted', family['source_publication'])

    def test_hostile_every_source_context_or_hash_omission_is_rejected(self):
        for name in self.docs:
            for container, key in [('context', ALIASES.get(name, name.removesuffix('.json'))), ('source_files', name)]:
                with self.subTest(container=container, file=name):
                    family = copy.deepcopy(self.live)
                    family[container].pop(key)
                    with self.assertRaises(ValueError):
                        adapter.validate_projection(family, TASK)
        for index in range(16):
            family = copy.deepcopy(self.live)
            family['operations'].pop(index)
            with self.subTest(operation=index), self.assertRaises(ValueError):
                adapter.validate_projection(family, TASK)
        for index in range(15):
            family = copy.deepcopy(self.live)
            family['routes'].pop(index)
            with self.subTest(route=index), self.assertRaises(ValueError):
                adapter.validate_projection(family, TASK)

    def test_hostile_semantic_omissions_and_inventions_are_rejected(self):
        probes = {
            'extra_context': lambda f: f['context'].__setitem__('invented', {'qualified': True}),
            'source_hash': lambda f: f['source_files']['operations.json'].__setitem__('sha256', '0' * 64),
            'source_pointer': lambda f: f['operations'][0].__setitem__('source_pointer', '/operations/1'),
            'invented_action': lambda f: f['operations'][8]['actions'].append('Activate unqualified hardware'),
            'outputs_as_observations': lambda f: f['operations'][0].__setitem__('post', f['operations'][0]['acceptance']['outputs']),
            'service_request_as_completion': lambda f: f['operations'][0]['acceptance'].__setitem__('service_request_is_completion', True),
            'live_runtime': lambda f: f['operations'][0]['provenance'].__setitem__('runtime', 'executed'),
            'physical_qualification': lambda f: f['operations'][0]['provenance'].__setitem__('physical_execution_qualified', True),
            'source_as_authored': lambda f: f['evidence']['F06'].__setitem__('classification', 'authored_robot_translation'),
            'authored_as_source': lambda f: f['operations'][0]['provenance'].__setitem__('classification', 'source_fact'),
            'chronology': lambda f: f['routes'][0]['nodes'][0].__setitem__('ordered', True),
            'branch_member_order': lambda f: f['routes'][0]['nodes'][0]['children'].reverse(),
            'false_third_experiment': lambda f: f['routes'][0].__setitem__('route_kind', 'physical_experiment'),
            'theory_executed': lambda f: f['routes'][6]['detail'].__setitem__('execution_status', 'EXECUTED'),
            'default_activation': lambda f: f.__setitem__('default_route', 'B02'),
            'hold_operation': lambda f: f['operations'].append({'id': 'HOLD_QUALIFICATION'}),
            'repeat_n': lambda f: f['context']['controls_and_repeats']['repeat_policy'].__setitem__('independent_specimens', 1),
            'control_lost': lambda f: f['context']['controls_and_repeats']['controls'].pop(),
            'unknown_default': lambda f: f['context']['unknowns']['unknowns'][0].__setitem__('physical_default', 1),
            'powder_invented': lambda f: f['context']['unknowns']['unknowns'][3].__setitem__('detail', 'Powder identified and qualified'),
            'conflict_silently_repaired': lambda f: f['context']['source_conflicts']['conflicts'][-1].__setitem__('reported_Pa_m3', 15.663459025787105),
            'hardware_rate_default': lambda f: f['context']['branches']['branches'][1]['source_reference_cycle'].__setitem__('hardware_command', True),
            'playback_as_acquisition': lambda f: f['context']['branches']['branches'][1]['source_reference_cycle'].__setitem__('acquisition_fps', 30),
            'sampled_as_continuous': lambda f: f['context']['source_access_audit']['media'][0].__setitem__('visual_review', 'Entire movie visually reviewed'),
            'archive_read_invented': lambda f: f['context']['source_access_audit']['data_code_archive_status']['archives'][0].__setitem__('contents_read', True),
            'lineage_lost': lambda f: f['context']['lineage']['chain'].remove('phase_id'),
            'failed_history_lost': lambda f: f['context']['recovery_boundaries'].__setitem__('failure_ledger', 'Discard failed attempts'),
            'stale_epoch_accepted': lambda f: f['context']['lifecycle_contract']['epoch_invalidation'].clear(),
            'safe_request_is_evidence': lambda f: f['context']['recovery_boundaries'].__setitem__('safe_request_is_safe_observation', True),
            'hold_is_complete': lambda f: f['context']['lifecycle_contract'].__setitem__('supported_hold_is_execution_complete', True),
            'source_outcome_target': lambda f: f['context']['source_outcomes']['outcomes'][0].__setitem__('not_for_agent_target', False),
            'actor_loader': lambda f: f.__setitem__('actor_projection_implemented', True),
            'scientific_credit': lambda f: f['context']['RELEASE_BOUNDARY'].__setitem__('validated_runnable_whole_paper_tasks', 1),
            'source_reanalysis': lambda f: f['context']['RELEASE_BOUNDARY'].__setitem__('source_data_reanalysis', True),
            'anchor_owner': lambda f: f['context']['asset_binding_plan']['operation_bindings'][0].__setitem__('primary_asset_id', 'A01'),
            'anchor_position': lambda f: f['context']['asset_binding_plan']['operation_bindings'][0]['anchor_positions_m']['ANCHOR.R01.primary'].__setitem__(0, 0),
            'asset_physical_claim': lambda f: f.__setitem__('asset_boundary', 'Exact qualified physical geometry'),
            'branch_count_inflation': lambda f: f['summary_counts'].__setitem__('physical_experimental_branches', 9),
            'remote_publication_claim': lambda f: f.__setitem__('source_publication', 'Remote commit published'),
        }
        for name, mutate in probes.items():
            with self.subTest(probe=name):
                family = copy.deepcopy(self.live)
                mutate(family)
                with self.assertRaises(ValueError):
                    adapter.validate_projection(family, TASK)

    def test_each_task_pinned_asset_rejects_byte_only_mutation(self):
        for name in sorted(ASSET_PINS):
            path = self.copy_asset / name
            original = path.read_bytes()
            try:
                path.write_bytes(original + b'\n')
                with self.subTest(asset=name), self.assertRaisesRegex(ValueError, 'Task-pinned scene file changed'):
                    adapter.adapt_conformal(self.copy_task)
            finally:
                path.write_bytes(original)

    def test_each_asset_pinned_task_rejects_byte_only_mutation(self):
        for name in sorted(TASK_PINS):
            path = self.copy_task / name
            original = path.read_bytes()
            try:
                path.write_bytes(original + b'\n')
                with self.subTest(task=name), self.assertRaisesRegex(ValueError, 'Asset-pinned task file changed'):
                    adapter.adapt_conformal(self.copy_task)
            finally:
                path.write_bytes(original)

    def test_snapshot_binding_contract_mutation_is_rejected(self):
        path = self.copy_asset / 'task_binding_snapshot.json'
        original = path.read_bytes()
        try:
            snapshot = json.loads(original)
            snapshot['binding_plan']['operation_bindings'][0]['primary_target'] = 'wrong.target'
            path.write_text(json.dumps(snapshot), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Task/asset snapshot mismatch'):
                adapter.adapt_conformal(self.copy_task)
        finally:
            path.write_bytes(original)

    def test_snapshot_reciprocal_pin_omission_duplicate_and_invention_rejected(self):
        path = self.copy_asset / 'task_binding_snapshot.json'
        original = path.read_bytes()
        probes = {
            'all_omitted': lambda s: s.__setitem__('task_files', []),
            'one_omitted': lambda s: s['task_files'].pop(),
            'duplicate': lambda s: s['task_files'].__setitem__(0, copy.deepcopy(s['task_files'][1])),
            'invented': lambda s: s['task_files'].append({'task_file': 'README.md', 'bytes': (self.copy_task / 'README.md').stat().st_size, 'sha256': digest(self.copy_task / 'README.md')}),
        }
        for name, mutate in probes.items():
            try:
                snapshot = json.loads(original)
                mutate(snapshot)
                path.write_text(json.dumps(snapshot), encoding='utf-8')
                with self.subTest(probe=name), self.assertRaises(ValueError):
                    adapter.adapt_conformal(self.copy_task)
            finally:
                path.write_bytes(original)

    def test_deleted_reciprocal_pins_cannot_hide_changed_operation_bytes(self):
        snapshot_path = self.copy_asset / 'task_binding_snapshot.json'
        operation_path = self.copy_task / 'operations.json'
        before_snapshot, before_operations = snapshot_path.read_bytes(), operation_path.read_bytes()
        try:
            snapshot = json.loads(before_snapshot)
            snapshot['task_files'] = []
            snapshot_path.write_text(json.dumps(snapshot), encoding='utf-8')
            operations = json.loads(before_operations)
            operations['operations'][0]['name'] = 'Forged operation with reciprocal pins removed'
            operation_path.write_text(json.dumps(operations), encoding='utf-8')
            with self.assertRaises(ValueError):
                adapter.adapt_conformal(self.copy_task)
        finally:
            snapshot_path.write_bytes(before_snapshot)
            operation_path.write_bytes(before_operations)


    def test_coordinated_task_and_reciprocal_hash_rewrite_is_rejected(self):
        snapshot_path = self.copy_asset / 'task_binding_snapshot.json'
        operation_path = self.copy_task / 'operations.json'
        before_snapshot, before_operations = snapshot_path.read_bytes(), operation_path.read_bytes()
        try:
            operations = json.loads(before_operations)
            operations['operations'][0]['name'] = 'Forged operation with rewritten reciprocal hash'
            operation_path.write_text(json.dumps(operations), encoding='utf-8')
            snapshot = json.loads(before_snapshot)
            pin = next(p for p in snapshot['task_files'] if p['task_file'] == 'operations.json')
            pin.update(bytes=operation_path.stat().st_size, sha256=digest(operation_path))
            snapshot_path.write_text(json.dumps(snapshot), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Frozen asset binding snapshot changed'):
                adapter.adapt_conformal(self.copy_task)
        finally:
            snapshot_path.write_bytes(before_snapshot)
            operation_path.write_bytes(before_operations)


if __name__ == '__main__':
    unittest.main(verbosity=2)
