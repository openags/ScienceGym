"""Independent offline ArcMorph viewer fidelity and hostile-mutation checks.

Run from the repository root:
  python3 -B -m unittest discover -s viewer/task_explorer_v1/tests -p test_arcmorph_independent.py -v

Expectations are derived from frozen task/asset JSON, never adapter constants.
Baseline bytes were independently hashed before the ArcMorph adapter existed.
This review reads local contracts only: no source publication reread, simulation,
hardware execution, raw-data reanalysis or remote publication is asserted.
"""
import collections
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

VIEWER = Path(__file__).resolve().parents[1]
REPO = VIEWER.parents[1]
TASKS = Path(os.environ.get('SCIENCEGYM_TASKS', str(REPO / 'tasks')))
PACKAGE = TASKS / 'arcmorph_operations_v2'
ASSETS = TASKS.parent / 'assets' / 'arcmorph_scene_assets_v1'
TASK_ZIP_SHA256 = 'e4507f5bd837cbedf6d63f38e6a5b88097983bdcacc487dd12ac8d37be1a6b41'
ASSET_ZIP_SHA256 = 'fa089646f79274c0e75d4525babba76d7977d2fe09b3dfd9275f92a5d025ebae'
BASE_COMMIT = '4152571bcd56cf10387ba36df913b790873c018d'
EARLIER = tuple('acoustic actuator_metrology afm_metrology atmospheric_optics beaded bianisotropic chiral cold_shape cooling dispim edge emvp fibre gear granular_assembly horn_acoustics hydrogel_optical laser_control lockable_origami martian_geophysics mechanical_backprop mechanical_logic microscopy origami_memory perovskite prismatic ring_origami solar_water sucrose_metrology thermal_jamming thermoelectric transistor varactor wavefront wetting woven'.split())
EARLIER_DIGEST = 'c8d32636b3f7944888cb4a4879c503d3445b689f758af1eb2163d5a9371d8c3d'
FROZEN_PACKAGE_DIGEST = '2b8f55eab0a1dd8b10e521741acdcf4b676600d77594d331f8e45b1c8cd577e9'
ALIASES = {'unknown_parameters.json': 'unknowns', 'evaluator_reference.json': 'acceptance',
           'lineage_contract.json': 'lineage'}
sys.path.insert(0, str(VIEWER))
import arcmorph_adapters as subject


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def strict(value):
    """Keep booleans distinct from integers and integers distinct from floats."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def unpack(payload):
    registry = payload.get('shared', [])
    def expand(value):
        if isinstance(value, list):
            return [expand(item) for item in value]
        if isinstance(value, dict):
            if set(value) == {'$shared'}:
                return expand(registry[value['$shared']])
            return {key: expand(item) for key, item in value.items()}
        return value
    return {key: expand(value) for key, value in payload.items() if key != 'shared'}


def resolve(document, pointer):
    if pointer == '':
        return document
    if not isinstance(pointer, str) or not pointer.startswith('/'):
        raise AssertionError('Not an RFC6901 source pointer: ' + repr(pointer))
    for token in pointer[1:].split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        document = document[int(token)] if isinstance(document, list) else document[token]
    return document


def index(records, key='id'):
    return {record[key]: record for record in records}


def nodes(items):
    for item in items:
        if isinstance(item, str):
            yield {'type': 'op', 'id': item}
        else:
            yield item
            yield from nodes(item.get('children', []))


def members(route):
    return [node['id'] for node in nodes(route['nodes']) if node['type'] == 'op']


def op(view, identifier):
    return next(item for item in view['operations'] if item['id'] == identifier)


def route(view, identifier):
    return next(item for item in view['routes'] if item['id'] == identifier)


def digest_files(base, paths):
    entries = [path + '\0' + hashlib.sha256((base / path).read_bytes()).hexdigest() + '\n'
               for path in sorted(paths)]
    return hashlib.sha256(''.join(entries).encode('utf-8')).hexdigest()


class ArcMorphIndependentFidelityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = {path.relative_to(PACKAGE).as_posix(): read(path)
                    for path in sorted(PACKAGE.rglob('*.json'))}
        cls.payload = read(VIEWER / 'data/arcmorph.json')
        cls.view = unpack(cls.payload)
        cls.assets = {path.relative_to(ASSETS).as_posix(): read(path)
                      for path in sorted(ASSETS.rglob('*.json'))}

    def assertStrictEqual(self, left, right, message=None):
        self.assertEqual(strict(left), strict(right), message)

    def test_01_all_33_source_documents_reconstruct_with_exact_types(self):
        self.assertEqual(len(self.docs), 33)
        self.assertEqual(set(self.view['source_files']), set(self.docs))
        expected = {ALIASES.get(name, name.removesuffix('.json')): doc
                    for name, doc in self.docs.items()}
        self.assertStrictEqual(self.view['context'], expected)
        self.assertIn('review/INDEPENDENT_REVIEW', self.view['context'])

    def test_02_all_31_operation_templates_keep_every_source_field(self):
        originals = self.docs['operations.json']['operations']
        self.assertEqual(len(originals), 31)
        self.assertEqual([o['id'] for o in originals], ['R%02d' % n for n in range(31)])
        self.assertStrictEqual([o['detail'] for o in self.view['operations']], originals)
        for position, (shown, original) in enumerate(zip(self.view['operations'], originals)):
            with self.subTest(operation=original['id']):
                self.assertEqual(shown['source_file'], 'operations.json')
                self.assertEqual(shown['source_pointer'], '/operations/' + str(position))
                self.assertStrictEqual(resolve(self.docs[shown['source_file']], shown['source_pointer']), shown['detail'])
                self.assertEqual(set(shown['detail']), set(original))
                for display, source in [('id', 'id'), ('title', 'interaction'), ('stage', 'station'),
                                        ('pre', 'preconditions'), ('post', 'postconditions'),
                                        ('sources', 'source_fact_ids'), ('unknowns', 'unknown_ids')]:
                    self.assertStrictEqual(shown[display], original[source])
                self.assertStrictEqual(shown['actions'], [original['interaction']])
                self.assertStrictEqual(shown['objects'], {key: original[key] for key in ('object', 'asset_ids')})
                self.assertStrictEqual(shown['acceptance'], {key: original[key] for key in
                    ('completion_evidence', 'required_record_type', 'evidence_role')})
                self.assertStrictEqual(shown['recovery'], {key: original[key] for key in
                    ('failure_response', 'failure_transition')})
                self.assertStrictEqual(shown['provenance'], {key: original[key] for key in
                    ('provenance_class', 'actor', 'source_is_robot_protocol', 'physical_implemented')})
                self.assertIsNone(shown['loop'])
                self.assertIn('not a paper quotation', shown['display_title_basis'])
                self.assertIn('not observed states or completion receipts', shown['display_mapping_basis'])
                self.assertIs(original['physical_implemented'], False)
                self.assertIs(original['source_is_robot_protocol'], False)
                self.assertEqual(original['provenance_class'], 'authored_robot_translation')
        self.assertIs(self.docs['operations.json']['template_is_occurrence'], False)

    def test_03_route_source_pointers_cover_all_branch_contracts(self):
        branches = self.docs['branches.json']
        expected = {}
        for key in ('physical_routes', 'auxiliary_routes', 'nonmanual_dispositions'):
            for position, branch in enumerate(branches[key]):
                expected[branch['id']] = (key, position, branch)
        self.assertEqual(len(branches['physical_routes']), 7)
        self.assertEqual(len(branches['auxiliary_routes']), 2)
        self.assertEqual(len(branches['nonmanual_dispositions']), 6)
        self.assertEqual({r['id'] for r in self.view['routes']}, set(expected) | {'HOLD_QUALIFICATION'})
        for identifier, (key, position, branch) in expected.items():
            with self.subTest(route=identifier):
                shown = route(self.view, identifier)
                self.assertEqual(shown['source_file'], 'branches.json')
                self.assertEqual(shown['source_pointer'], '/' + key + '/' + str(position))
                self.assertStrictEqual(shown['detail'], branch)
        for shown in self.view['routes']:
            self.assertStrictEqual(shown['detail'], resolve(self.docs[shown['source_file']], shown['source_pointer']))
            for node in nodes(shown['nodes']):
                if node['type'] != 'op' and 'source_file' in node.get('meta', {}):
                    meta = node['meta']
                    payload_keys = {'source_contract', 'source_node'} & set(meta)
                    self.assertEqual(len(payload_keys), 1)
                    self.assertStrictEqual(meta[next(iter(payload_keys))], resolve(self.docs[meta['source_file']], meta['source_pointer']))

    def test_04_four_cardstock_families_preserve_groups_and_duplicate_occurrences(self):
        for original in self.docs['branches.json']['physical_routes'][:4]:
            shown = route(self.view, original['id'])
            self.assertStrictEqual(shown['detail']['state_slots'], ['ground', 'rigid', 'sheared'])
            expected = original['dependencies'] + [oid for group in original['operation_groups'].values() for oid in group]
            self.assertEqual(members(shown), expected)
            self.assertEqual(collections.Counter(members(shown))['R03'], 7)
            self.assertEqual(collections.Counter(members(shown))['R28'], 3)
            self.assertIn('number of physical samples and repeats not specified', shown['detail']['repeat_policy'])
            self.assertIn('qualified recovery check', shown['detail']['order_policy'])

    def test_05_eight_polymer_configurations_remain_one_symbolic_state_loop(self):
        original = index(self.docs['branches.json']['physical_routes'])['PP_RIGID']
        shown = route(self.view, 'PP_RIGID')
        loops = [node for node in nodes(shown['nodes']) if node['type'] == 'loop']
        self.assertEqual(len(loops), 1)
        loop = loops[0]
        self.assertEqual([node['id'] for node in nodes(loop['children']) if node['type'] == 'op'], original['state_loop']['per_instance'])
        self.assertEqual(collections.Counter(members(shown))['R13'], 1)
        self.assertEqual(collections.Counter(members(shown))['R16'], 1)
        self.assertEqual(collections.Counter(members(shown))['R17'], 1)
        self.assertStrictEqual(shown['detail']['state_loop'], original['state_loop'])
        self.assertEqual([x['id'] for x in original['state_loop']['instances']], ['H%02d' % n for n in range(1, 9)])
        self.assertStrictEqual([x['source_height_cm'] for x in original['state_loop']['instances']], [31.5, 32, 33, 34, 35, 36, 37, 37.5])
        self.assertIs(original['state_loop']['same_specimen_required'], True)
        self.assertIn('not eight specimens or technical repeats', original['repeat_policy'])
        self.assertIn('does not establish the historical chronology', original['state_loop']['state_order'])

    def test_06_polymer_preparation_and_qualitative_sequences_keep_source_order(self):
        originals = index(self.docs['branches.json']['physical_routes'])
        for identifier in ('PP_PREP', 'PP_SHEAR'):
            original = originals[identifier]
            shown = route(self.view, identifier)
            expected = [x for x in original['dependencies'] if x.startswith('R') and x[1:].isdigit()] + original['operation_sequence']
            self.assertEqual(members(shown), expected)
        self.assertEqual(collections.Counter(members(route(self.view, 'PP_PREP')))['R03'], 3)
        self.assertIn('source identity between quantitative and qualitative branches is not inferred', originals['PP_SHEAR']['allocation'])

    def test_07_hold_and_nonmanual_dispositions_have_no_invented_operations(self):
        self.assertEqual(self.view['default_route'], 'HOLD_QUALIFICATION')
        hold = route(self.view, 'HOLD_QUALIFICATION')
        self.assertIs(hold['metadata_only'], True)
        self.assertEqual(members(hold), [])
        self.assertStrictEqual(hold['detail'], self.docs['episode_input_contract.json'])
        self.assertNotIn('HOLD_QUALIFICATION', index(self.view['operations']))
        for original in self.docs['branches.json']['nonmanual_dispositions']:
            shown = route(self.view, original['id'])
            self.assertIs(shown['metadata_only'], True)
            self.assertEqual(members(shown), [])
        self.assertIs(hold['detail']['physical_runtime_available'], False)
        self.assertIs(hold['detail']['null_blocks_execution'], True)

    def test_08_replication_slots_theory_and_observation_remain_separate(self):
        c = self.view['context']
        repeats = c['controls_and_repeats']
        self.assertStrictEqual([repeats[k] for k in ('source_quantitative_specimens', 'source_quantitative_sets', 'source_configurations')], [1, 1, 8])
        self.assertIsNone(repeats['source_technical_repeats_per_configuration'])
        self.assertIsNone(repeats['authored_repeat_default'])
        self.assertIn('12 cardstock state slots are evidential slots', repeats['qualitative_counts'])
        outcomes = c['source_outcomes']
        self.assertEqual(len(outcomes['rows']), 8)
        self.assertEqual(outcomes['visibility'], 'reviewer_and_future_evaluator_only')
        self.assertEqual(outcomes['data_class'], 'published_observations_not_benchmark_targets')
        self.assertEqual(outcomes['units'], 'cm')
        self.assertIn('not the coarse-grained theoretical radius', outcomes['limits'][1])
        self.assertIn('Do not expose this file to an actor', outcomes['limits'][2])
        facts = index(c['source_parameters']['facts'])
        self.assertIs(facts['F08']['reported']['not_physical_specimen_defaults'], True)
        self.assertIs(facts['F06']['reported']['quantitative_shear_validation'], False)
        self.assertIsNone(facts['F06']['reported']['load_magnitude'])
        self.assertEqual(c['analysis_contracts']['observables'], ['height', 'interior_radius', 'exterior_radius'])
        self.assertIs(c['analysis_contracts']['analysis_hold_does_not_erase_acquisition'], True)

    def test_09_all_conflicts_and_unknowns_remain_scoped_and_unresolved(self):
        c = self.view['context']
        conflicts = index(c['source_conflicts']['conflicts'])
        unknowns = index(c['unknowns']['unknowns'])
        self.assertEqual(set(conflicts), {'C%02d' % n for n in range(1, 11)})
        self.assertEqual(set(unknowns), {'U%02d' % n for n in range(1, 15)})
        for item in conflicts.values():
            self.assertEqual(item['status'], 'open')
            self.assertIn('Hold only affected', item['block_policy'])
            self.assertIn('actor cannot self-certify', item['resolution_authority'])
        for item in unknowns.values():
            self.assertIsNone(item['default'])
            self.assertIsNone(item['physical_default'])
            self.assertIn('never generated scene geometry or actor assertion', item['resolution_authority'])
        self.assertEqual(conflicts['C01']['family_scope'], ['PP'])
        self.assertEqual(conflicts['C04']['family_scope'], ['CS2'])
        self.assertEqual(conflicts['C07']['claim_scope'], ['source_raw_correspondence'])
        self.assertIn('383.65', conflicts['C01']['observation'])
        self.assertIn('383.63', conflicts['C01']['observation'])
        for shown in self.view['operations']:
            self.assertTrue(set(shown['detail']['conflict_ids']) <= set(conflicts))
            self.assertTrue(set(shown['detail']['unknown_ids']) <= set(unknowns))

    def test_10_evidence_preserves_all_ten_source_facts(self):
        self.assertStrictEqual(self.view['evidence'], index(self.docs['evidence_map.json']['facts']))
        self.assertEqual(set(self.view['evidence']), {'F%02d' % n for n in range(1, 11)})
        for shown in self.view['operations']:
            self.assertTrue(set(shown['detail']['source_fact_ids']) <= set(self.view['evidence']))
        self.assertIs(self.view['evidence']['F10']['reported']['archive_not_reviewed'], True)

    def test_11_safe_closeout_and_lineage_never_depend_on_scientific_success(self):
        c = self.view['context']
        for edge in c['lifecycle_contract']['failure_edges']:
            self.assertIs(edge['scientific_success_required'], False)
            self.assertEqual(edge['to'], 'SAFE_HOLD_OR_QUALIFIED_RELEASE')
        release = c['recovery_boundaries']['release_selection']
        self.assertEqual(release['corner_fixture'], 'R19 then R22')
        self.assertEqual(release['rigid_fixture'], 'R19 then R30')
        self.assertIn('no storage transfer', c['recovery_boundaries']['closeout'])
        self.assertIn('no backfilled calibration', strict(c['recovery_boundaries']))
        self.assertIn('Replacing measured values by target or literature values', strict(c['dependencies']))
        self.assertIn('camera_or_lens_or_reference_or_fixture_change', c['dependencies']['revision_invalidation'])
        self.assertIn('source/destination/carrier/object binding', strict(c['lifecycle_contract']))
        self.assertIs(c['preparation_routes']['no_service_shortcut'], True)
        self.assertEqual(c['preparation_routes']['fold_operation'], 'R07')
        self.assertIsNone(c['preparation_routes']['all_limits_default'])
        self.assertIs(c['nonmanual_scope']['all_services_unimplemented'], True)

    def test_12_source_access_does_not_claim_a_new_publication_or_archive_review(self):
        c = self.view['context']
        audit = index(c['source_access_audit']['sources'])
        self.assertEqual(audit['MAIN']['all_text_pages_read'], list(range(1, 13)))
        self.assertEqual(audit['SI']['all_text_pages_read'], list(range(1, 23)))
        self.assertIn('archive bytes not acquired', audit['DATA']['status'])
        self.assertIn('Archive byte/checksum verification', audit['DATA']['not_claimed'])
        self.assertIs(c['source_access_audit']['readiness']['source_code_execution'], False)
        self.assertIs(c['provenance']['source_media_exported'], False)
        self.assertIn('Raw archive not read', c['provenance']['source_review_scope'])
        self.assertIs(c['source_access_audit']['rights']['no_relicense_claim'], True)

    def test_13_concrete_primary_and_control_targets_match_all_task_operations(self):
        plan = self.view['context']['asset_binding_plan']
        self.assertStrictEqual(plan, self.assets['task_binding_snapshot.json'])
        authored = index(plan['operation_bindings'], 'operation_id')
        concrete = index(self.assets['operation_bindings.json']['operations'], 'operation_id')
        anchors = index(self.assets['affordances.json']['anchors'], 'anchor_id')
        self.assertEqual((len(authored), len(concrete), len(anchors)), (31, 31, 66))
        for original in self.docs['operations.json']['operations']:
            oid = original['id']
            with self.subTest(operation=oid):
                for key in ('asset_ids', 'primary_asset_id', 'primary_target', 'control_target'):
                    self.assertStrictEqual(original[key], authored[oid][key])
                    if key == 'asset_ids':
                        # Frozen task and scene order differ at R19; membership is the cross-package contract.
                        self.assertEqual(collections.Counter(original[key]), collections.Counter(concrete[oid][key]))
                    else:
                        self.assertStrictEqual(original[key], concrete[oid][key])
                self.assertStrictEqual(original['anchor_ids'], authored[oid]['anchor_ids'])
                self.assertEqual(original['primary_target'], anchors[concrete[oid]['primary_anchor']]['target_object'])
                self.assertEqual(original['control_target'], anchors[concrete[oid]['control_anchor']]['target_object'])
                self.assertIs(authored[oid]['physical_qualified'], False)
                self.assertIs(concrete[oid]['physical_execution_enabled'], False)
                self.assertIsNone(concrete[oid]['qualified_pose'])
        self.assertEqual(op(self.view, 'R06')['detail']['primary_target'], 'fab.load_dock')
        self.assertIn('does not transport the sheet to A12', plan['R06_station_policy'])
        self.assertEqual(plan['family_aliases'], {'PP1': 'PP'})

    def test_14_six_fixture_selectors_and_unqualified_anchor_coordinates_are_exact(self):
        plan = self.view['context']['asset_binding_plan']
        selectors = plan['contextual_anchor_bindings']
        self.assertEqual([(x['operation_id'], x['actual_fixture_class']) for x in selectors], [
            ('R19', 'rigid_metrology'), ('R19', 'corner_load'), ('R19', 'rigid_demo'),
            ('R22', 'corner_load'), ('R30', 'rigid_metrology'), ('R30', 'rigid_demo')])
        anchors = index(self.assets['affordances.json']['anchors'], 'anchor_id')
        parts = {p['scene_object']: (asset['asset_id'], p)
                 for asset in self.assets['asset_inventory.json']['assets'] for p in asset['parts']}
        for anchor in anchors.values():
            self.assertIsNone(anchor['qualified_pose'])
            self.assertIs(anchor['physical_execution_enabled'], False)
            owner, part = parts[anchor['target_object']]
            self.assertEqual(anchor['asset_id'], owner)
            self.assertStrictEqual(anchor['translation_m'], part['translation_m'])
        for selector in selectors:
            self.assertIn(selector['anchor_id'], anchors)
        self.assertIn('R30 cannot release a corner-load fixture', plan['contextual_anchor_policy'])
        self.assertIs(plan['nominal_anchor_is_motion_permission'], False)

    def test_15_nine_task_pinned_scene_hashes_and_original_illustration_boundary(self):
        pins = self.docs['review/INDEPENDENT_REVIEW.json']['observed_sibling_contract_hashes']
        self.assertEqual(set(pins), {'operation_binding_contract.json', 'operation_bindings.json',
            'asset_metadata.json', 'affordances.json', 'variants.json', 'asset_inventory.json',
            'specimen_topology.json', 'semantic_controls.py', 'states.json'})
        self.assertEqual(len(pins), 9)
        for name, expected in pins.items():
            self.assertEqual(hashlib.sha256((ASSETS / name).read_bytes()).hexdigest(), expected, name)
        metadata = self.assets['asset_metadata.json']
        for key in ('physical_geometry_validated', 'physical_execution_enabled', 'scientific_success',
                    'source_pixels_or_CAD_used', 'raw_archive_or_code_read'):
            self.assertIs(metadata[key], False)
        self.assertEqual(metadata['original_geometry_license'], 'Apache-2.0')
        self.assertIn('nominal generator inputs', metadata['dimension_semantics'])
        self.assertIsNone(metadata['dimensional_hold']['resolution'])
        self.assertIs(metadata['dimensional_hold']['fabrication_from_source_dimensions_allowed'], False)
        states = self.assets['states.json']
        self.assertEqual(len(states['guard_invariants']), 18)
        self.assertIn('R13 configuration candidates require the PP specimen family and rigid_metrology fixture kind', states['guard_invariants'][-1])
        self.assertIn('R27 remains metadata-only and unimplemented', states['guard_invariants'][-1])
        for key, value in states['claims'].items():
            self.assertIs(value, key == 'semantic_tests_only')

    def test_16_local_source_links_are_hash_bound_without_remote_publication_claim(self):
        f = self.view
        self.assertEqual(f['source_commit'], BASE_COMMIT)
        self.assertEqual(f['source_link_mode'], 'repository_relative_frozen_local_snapshot')
        self.assertIn('remote publication is not asserted', f['source_publication'])
        self.assertEqual(f['source_folder'], '../../tasks/arcmorph_operations_v2/')
        for name, entry in f['source_files'].items():
            self.assertEqual(entry['repository_path'], 'tasks/arcmorph_operations_v2/' + name)
            self.assertEqual(entry['url'], '../../tasks/arcmorph_operations_v2/' + name)
            self.assertEqual((VIEWER / entry['url']).resolve(), (PACKAGE / name).resolve())
            self.assertEqual(entry['sha256'], hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest())
        self.assertEqual({x['path'] for x in f['asset_links']}, {'assets/arcmorph_scene_assets_v1/' + name
            for name in ('README.md', 'evidence/handling.png', 'evidence/metrology.png', 'evidence/overview.png')})
        for entry in f['asset_links']:
            self.assertEqual(entry['url'], '../../' + entry['path'])
            self.assertTrue(entry['path'].startswith('assets/arcmorph_scene_assets_v1/'))
            self.assertEqual(hashlib.sha256((VIEWER / entry['url']).read_bytes()).hexdigest(), entry['sha256'])
        self.assertEqual(self.assets['paired_task_receipt.json']['task_archive_sha256'], TASK_ZIP_SHA256)

    def test_17_design_only_and_author_evaluator_visibility(self):
        f = self.view
        self.assertEqual(f['family_scope'], 'paper_level_design')
        self.assertEqual(f['visibility'], 'author_evaluator_reference_only')
        self.assertIs(f['actor_projection_implemented'], False)
        self.assertEqual(f['context']['acceptance']['actor_visible_allowlist'], ['agent_visible.json'])
        boundary = f['context']['RELEASE_BOUNDARY']
        self.assertStrictEqual(boundary['validated_runnable_whole_paper_tasks'], 0)
        for key in ('whole_paper_execution_complete', 'physical_execution', 'physical_simulation',
                    'scientific_reproduction', 'source_data_reanalysis', 'source_files_exported',
                    'exact_geometry_validated', 'hardware_safety_qualified', 'source_math_validated',
                    'repository_changes', 'remote_writes'):
            self.assertIs(boundary[key], False)
        self.assertTrue(subject.validate_projection(copy.deepcopy(f), PACKAGE))

    def test_18_json_and_javascript_are_equivalent_and_markdown_links_resolve(self):
        js = (VIEWER / 'data/arcmorph.js').read_text(encoding='utf-8')
        encoded = js.split('["arcmorph"]=', 1)[1].rsplit(';', 1)[0]
        self.assertStrictEqual(json.loads(encoded), self.payload)
        markdown = (VIEWER / 'docs/arcmorph.md').read_text(encoding='utf-8')
        self.assertIn(self.view['source_warnings'], markdown)
        for shown in self.view['routes']:
            self.assertIn('## ' + shown['id'] + ' ', markdown)
        for shown in self.view['operations']:
            self.assertIn('`' + shown['id'] + '`', markdown)
            self.assertIn(shown['title'], markdown)
        for href in re.findall(r'\]\(([^)]+)\)', markdown):
            if not href.startswith(('https:', 'http:', '#')):
                self.assertTrue((VIEWER / 'docs' / href.split('#', 1)[0]).exists(), href)
        ET.parse(VIEWER / 'diagrams/arcmorph.svg')

    def test_19_previous_36_families_have_all_144_byte_identical_outputs(self):
        paths = ['viewer/task_explorer_v1/' + folder + '/' + family + extension
                 for family in EARLIER
                 for folder, extension in [('data', '.json'), ('data', '.js'), ('docs', '.md'), ('diagrams', '.svg')]]
        self.assertEqual((len(EARLIER), len(paths)), (36, 144))
        self.assertEqual(digest_files(REPO, paths), EARLIER_DIGEST)

    def test_20_all_88_frozen_task_and_asset_files_are_byte_identical(self):
        paths = [path.relative_to(TASKS.parent).as_posix()
                 for directory in (PACKAGE, ASSETS) for path in directory.rglob('*')
                 if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc']
        self.assertEqual(len(paths), 88)
        self.assertEqual(digest_files(TASKS.parent, paths), FROZEN_PACKAGE_DIGEST)


    def test_21_counts_and_typed_inspection_views_are_not_paper_or_trial_counts(self):
        f = self.view
        self.assertEqual((len(f['operations']), len(f['routes']), len(f['source_files']), len(f['evidence'])), (31, 16, 33, 10))
        self.assertEqual(collections.Counter(r['route_kind'] for r in f['routes']), {
            'physical_design': 7, 'analysis': 1, 'conditional_closeout': 1,
            'nonmanual_reference': 6, 'qualification_hold': 1})
        self.assertStrictEqual(f['summary_counts'], {
            'physical_design_records': 7, 'analysis_records': 1, 'conditional_closeout_records': 1,
            'nonmanual_reference_records': 6, 'qualification_hold_records': 1,
            'physical_route_families': 7, 'source_json_documents': 33, 'scene_groups': 12,
            'symbolic_anchors': 66, 'source_evidence_entries': 10, 'source_conflicts': 10,
            'unresolved_input_groups': 14, 'source_quantitative_specimens': 1, 'source_configurations': 8})

    def test_22_every_occurrence_has_its_own_exact_source_pointer(self):
        all_ids = set()
        for shown in self.view['routes']:
            pointers = []
            for node in nodes(shown['nodes']):
                if node['type'] != 'op':
                    continue
                meta = node['meta']
                self.assertEqual(meta['source_file'], 'branches.json')
                self.assertStrictEqual(meta['source_node'], node['id'])
                self.assertStrictEqual(resolve(self.docs['branches.json'], meta['source_pointer']), node['id'])
                self.assertTrue(meta['source_pointer'].startswith(shown['source_pointer'] + '/'))
                pointers.append(meta['source_pointer'])
                all_ids.add(node['id'])
            self.assertEqual(len(pointers), len(set(pointers)), shown['id'])
        self.assertEqual(all_ids, {'R%02d' % n for n in range(31)})

    def test_23_cardstock_phase_containers_are_unordered_with_exact_ordered_bodies(self):
        for position, original in enumerate(self.docs['branches.json']['physical_routes'][:4]):
            shown = route(self.view, original['id'])
            ptr = '/physical_routes/' + str(position) + '/operation_groups'
            group = next(n for n in nodes(shown['nodes']) if n.get('meta', {}).get('source_pointer') == ptr)
            self.assertEqual(group['type'], 'obligations')
            self.assertIs(group['ordered'], False)
            self.assertStrictEqual(group['meta']['source_node'], original['operation_groups'])
            self.assertStrictEqual(group['meta']['state_slots'], original['state_slots'])
            self.assertEqual(group['meta']['order'], original['order_policy'])
            self.assertEqual(len(group['children']), len(original['operation_groups']))
            for phase, (name, body) in zip(group['children'], original['operation_groups'].items()):
                self.assertEqual(phase['type'], 'sequence')
                self.assertIs(phase['ordered'], True)
                self.assertEqual(phase['meta']['source_pointer'], ptr + '/' + name)
                self.assertStrictEqual(phase['meta']['source_node'], body)
                self.assertEqual([n['id'] for n in phase['children']], body)
        loop = first_node(self.view, 'PP_RIGID', 'loop')
        self.assertIs(loop['symbolic'], True)
        self.assertIs(loop['ordered'], True)
        self.assertEqual(loop['meta']['source_pointer'], '/physical_routes/5/state_loop')
        self.assertStrictEqual(loop['meta']['source_node'], self.docs['branches.json']['physical_routes'][5]['state_loop'])

    def test_24_closeout_fixture_alternatives_remain_conditional_and_unselected(self):
        shown = route(self.view, 'CLOSEOUT')
        self.assertEqual(shown['route_kind'], 'conditional_closeout')
        root = shown['nodes'][0]
        self.assertEqual(root['type'], 'obligations')
        self.assertIs(root['ordered'], False)
        choices = [n for n in nodes(shown['nodes']) if n['type'] == 'choice']
        self.assertEqual(len(choices), 1)
        choice = choices[0]
        self.assertIs(choice['ordered'], False)
        self.assertEqual([n['id'] for n in choice['children']], ['R22', 'R30'])
        self.assertEqual(choice['meta']['selection_rule'], self.docs['branches.json']['auxiliary_routes'][1]['selection_rule'])
        self.assertNotIn('selected', choice)
        self.assertNotIn('selected_arm', choice)
        self.assertNotIn('default_arm', choice)
        self.assertEqual([n['id'] for n in root['children'] if n['type'] == 'op'], ['R19', 'R23', 'R24'])
        self.assertEqual(members(shown), self.docs['branches.json']['auxiliary_routes'][1]['operations'])

    def test_25_all_16_svg_views_preserve_occurrences_without_adjacency_arrows(self):
        spec = importlib.util.spec_from_file_location('independent_arcmorph_builder', VIEWER / 'build.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        for shown in self.view['routes']:
            with self.subTest(route=shown['id']):
                candidate = copy.deepcopy(self.view)
                candidate['default_route'] = shown['id']
                rendered = builder.svg(candidate)
                tree = ET.fromstring(rendered)
                self.assertNotIn('marker-end=', rendered)
                self.assertIn('no cross-phase chronology', rendered)
                self.assertIn('0 validated runnable whole-paper tasks', rendered)
                texts = [n.text or '' for n in tree.findall('.//{http://www.w3.org/2000/svg}text')]
                displayed = [t.split(' · ')[1] for t in texts if re.match(r'^\d+ · R\d\d$', t)]
                self.assertEqual(displayed, members(shown))
                for record in self.view['routes']:
                    self.assertIn(record['id'], texts)

    def test_26_validator_rejects_each_corrupt_task_pinned_scene_file(self):
        pins = self.docs['review/INDEPENDENT_REVIEW.json']['observed_sibling_contract_hashes']
        original_read = Path.read_bytes
        for name in pins:
            target = (ASSETS / name).resolve()
            def corrupted_read(path):
                value = original_read(path)
                return value + b'\ncorrupted independent fixture\n' if path.resolve() == target else value
            with self.subTest(file=name), mock.patch.object(Path, 'read_bytes', corrupted_read):
                with self.assertRaisesRegex(ValueError, 'Task-pinned scene file changed'):
                    subject.validate_projection(copy.deepcopy(self.view), PACKAGE)

    def test_27_dependency_views_retain_complete_original_documents(self):
        for name in ('dependencies', 'preparation_routes', 'lifecycle_contract', 'lineage_contract',
                     'transport_routes', 'recovery_boundaries'):
            self.assertStrictEqual(self.view['dependencies'][name], self.docs[name + '.json'])


class ArcMorphIndependentHostileMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pristine = unpack(read(VIEWER / 'data/arcmorph.json'))

    def assertRejected(self, mutate):
        candidate = copy.deepcopy(self.pristine)
        before = strict(candidate)
        mutate(candidate)
        self.assertNotEqual(strict(candidate), before, 'Hostile fixture must really change the projection')
        mutated = strict(candidate)
        with self.assertRaises(ValueError):
            subject.validate_projection(candidate, PACKAGE)
        self.assertEqual(strict(candidate), mutated, 'Validation must not silently repair hostile input')
        self.assertEqual(strict(self.pristine), before, 'Validation must not mutate the pristine fixture')

    def test_reject_nonfinite_numbers_without_normalization(self):
        for value in (float('nan'), float('inf'), float('-inf')):
            candidate = copy.deepcopy(self.pristine)
            route(candidate, 'PP_RIGID')['detail']['state_loop']['instances'][0]['source_height_cm'] = value
            before = repr(candidate)
            with self.subTest(value=value), self.assertRaises(ValueError):
                subject.validate_projection(candidate, PACKAGE)
            self.assertEqual(repr(candidate), before)

    def test_reject_wrong_top_level_types(self):
        for candidate in (None, False, 0, 0.0, '', [], [self.pristine]):
            with self.subTest(kind=type(candidate).__name__), self.assertRaises(ValueError):
                subject.validate_projection(candidate, PACKAGE)


def first_node(view, identifier, kind):
    return next(n for n in nodes(route(view, identifier)['nodes']) if n['type'] == kind)


def source_node(view, route_id, pointer):
    return next(n for n in nodes(route(view, route_id)['nodes']) if n.get('meta', {}).get('source_pointer') == pointer)


def rewrite_every_string(value, old, new):
    if isinstance(value, dict):
        for key in value:
            if isinstance(value[key], str):
                value[key] = value[key].replace(old, new)
            else:
                rewrite_every_string(value[key], old, new)
    elif isinstance(value, list):
        for position, item in enumerate(value):
            if isinstance(item, str):
                value[position] = item.replace(old, new)
            else:
                rewrite_every_string(item, old, new)


MUTATIONS = {
    'change_display_title': lambda f: op(f, 'R13').update(title='Experiment completed'),
    'change_display_station': lambda f: op(f, 'R13').update(stage='corner load fixture'),
    'change_display_action': lambda f: op(f, 'R13').update(actions=['Enable robot motion']),
    'change_display_objects': lambda f: op(f, 'R13')['objects'].update(asset_ids=['A11']),
    'remove_display_precondition': lambda f: op(f, 'R13')['pre'].pop(),
    'invent_observed_poststate': lambda f: op(f, 'R13').update(post={'completed': True, 'measured_height': 32}),
    'change_display_acceptance': lambda f: op(f, 'R18')['acceptance'].update(required_record_type='single_unlocked_photo'),
    'promote_request_receipt_role': lambda f: op(f, 'R04')['acceptance'].update(evidence_role='measured_success'),
    'remove_failure_response': lambda f: op(f, 'R19')['recovery'].pop('failure_response'),
    'remove_failure_transition': lambda f: op(f, 'R19')['recovery'].pop('failure_transition'),
    'change_display_provenance': lambda f: op(f, 'R13')['provenance'].update(provenance_class='source_robot_protocol'),
    'omit_display_source_fact': lambda f: op(f, 'R13')['sources'].pop(),
    'omit_display_unknown': lambda f: op(f, 'R13')['unknowns'].pop(),
    'invent_template_loop_count': lambda f: op(f, 'R13').update(loop={'repeats': 8}),
    'erase_authored_obligation_label': lambda f: op(f, 'R13').update(display_mapping_basis='Observed physical states'),
    'invent_cross_phase_chronology': lambda f: source_node(f, 'CS1', '/physical_routes/0/operation_groups').update(ordered=True),
    'flatten_cardstock_phase_group': lambda f: source_node(f, 'CS1', '/physical_routes/0/operation_groups').update(type='sequence'),
    'deduplicate_repeated_transfer': lambda f: source_node(f, 'CS1', '/physical_routes/0/operation_groups/prepare')['children'].pop(5),
    'reverse_phase_body': lambda f: source_node(f, 'CS1', '/physical_routes/0/operation_groups/prepare')['children'].reverse(),
    'omit_source_phase_group': lambda f: source_node(f, 'CS1', '/physical_routes/0/operation_groups')['children'].pop(),
    'wrong_occurrence_pointer': lambda f: source_node(f, 'CS1', '/physical_routes/0/operation_groups/prepare')['children'][5]['meta'].update(source_pointer='/physical_routes/0/operation_groups/prepare/1'),
    'wrong_occurrence_source_node': lambda f: source_node(f, 'CS1', '/physical_routes/0/operation_groups/prepare')['children'][5]['meta'].update(source_node='R13'),
    'wrong_group_source_pointer': lambda f: source_node(f, 'CS1', '/physical_routes/0/operation_groups/prepare')['meta'].update(source_pointer='/physical_routes/1/operation_groups/prepare'),
    'wrong_group_source_node': lambda f: source_node(f, 'CS1', '/physical_routes/0/operation_groups/prepare')['meta']['source_node'].pop(),
    'instantiate_symbolic_loop': lambda f: first_node(f, 'PP_RIGID', 'loop').update(symbolic=False),
    'drop_loop_instance': lambda f: first_node(f, 'PP_RIGID', 'loop')['meta']['source_node']['instances'].pop(),
    'integer_height_as_float': lambda f: first_node(f, 'PP_RIGID', 'loop')['meta']['source_node']['instances'][1].update(source_height_cm=32.0),
    'selected_closeout_alternative': lambda f: first_node(f, 'CLOSEOUT', 'choice').update(selected_arm='R22'),
    'require_both_fixture_releases': lambda f: first_node(f, 'CLOSEOUT', 'choice').update(type='sequence', ordered=True),
    'erase_fixture_selection_rule': lambda f: first_node(f, 'CLOSEOUT', 'choice')['meta'].pop('selection_rule'),
    'remove_unmount_alternative': lambda f: first_node(f, 'CLOSEOUT', 'choice')['children'].pop(),
    'string_boolean_node_order': lambda f: first_node(f, 'CLOSEOUT', 'choice').update(ordered='false'),
    'integer_boolean_node_order': lambda f: first_node(f, 'CLOSEOUT', 'choice').update(ordered=0),
    'array_as_mapping': lambda f: op(f, 'R13').update(pre={'0': op(f, 'R13')['pre'][0]}),
    'missing_post_field': lambda f: op(f, 'R13').pop('post'),
    'count_integer_as_float': lambda f: f['summary_counts'].update(physical_route_families=7.0),
    'corrupt_task_pinned_scene_digest': lambda f: f['context']['review/INDEPENDENT_REVIEW']['observed_sibling_contract_hashes'].update(**{'states.json': '0' * 64}),
    'remove_task_pinned_guard_file': lambda f: f['context']['review/INDEPENDENT_REVIEW']['observed_sibling_contract_hashes'].pop('semantic_controls.py'),
    'change_source_commit_pin': lambda f: f.update(source_commit='0' * 40),
    'add_actor_access_to_acceptance': lambda f: f['context']['acceptance']['actor_visible_allowlist'].append('source_outcomes.json'),
    'omit_nested_review': lambda f: f['context'].pop('review/INDEPENDENT_REVIEW'),
    'omit_source_document': lambda f: f['source_files'].pop('controls_and_repeats.json'),
    'add_spurious_source_document': lambda f: f['context'].update(invented_source={'executed': True}),
    'omit_operation': lambda f: f['operations'].pop(),
    'duplicate_operation': lambda f: f['operations'].append(copy.deepcopy(f['operations'][0])),
    'invent_hold_operation': lambda f: f['operations'].append({'id': 'HOLD_QUALIFICATION'}),
    'wrong_operation_pointer': lambda f: op(f, 'R13').update(source_pointer='/operations/0'),
    'omit_hidden_operation_field': lambda f: op(f, 'R13')['detail'].pop('scope_rule'),
    'invent_operation_field': lambda f: op(f, 'R13')['detail'].update(completed=True),
    'activate_hold': lambda f: route(f, 'HOLD_QUALIFICATION').update(metadata_only=False),
    'add_operation_to_hold': lambda f: route(f, 'HOLD_QUALIFICATION')['nodes'].append('R13'),
    'promote_nonmanual_to_operation': lambda f: route(f, 'N06')['nodes'].append('R13'),
    'omit_route': lambda f: f['routes'].pop(3),
    'wrong_route_pointer': lambda f: route(f, 'CS2').update(source_pointer='/physical_routes/0'),
    'swap_cardstock_family_slots': lambda f: route(f, 'CS1')['detail'].update(state_slots=['ground', 'sheared', 'rigid']),
    'flatten_symbolic_loop': lambda f: first_node(f, 'PP_RIGID', 'loop').update(type='group'),
    'reorder_loop_operations': lambda f: first_node(f, 'PP_RIGID', 'loop')['children'].reverse(),
    'duplicate_loop_into_eight_trials': lambda f: first_node(f, 'PP_RIGID', 'loop').update(children=first_node(f, 'PP_RIGID', 'loop')['children'] * 8),
    'change_loop_target_height': lambda f: route(f, 'PP_RIGID')['detail']['state_loop']['instances'][0].update(source_height_cm=32),
    'claim_eight_specimens': lambda f: f['context']['controls_and_repeats'].update(source_quantitative_specimens=8),
    'claim_eight_repeats': lambda f: f['context']['controls_and_repeats'].update(source_technical_repeats_per_configuration=8),
    'default_new_repeats': lambda f: f['context']['controls_and_repeats'].update(authored_repeat_default=1),
    'allow_specimen_replacement_within_loop': lambda f: route(f, 'PP_RIGID')['detail']['state_loop'].update(same_specimen_required=False),
    'turn_qualitative_into_quantitative': lambda f: f['evidence']['F06']['reported'].update(quantitative_shear_validation=True),
    'invent_corner_load': lambda f: f['evidence']['F06']['reported'].update(load_magnitude=1),
    'promote_numerical_geometry_to_default': lambda f: f['evidence']['F08']['reported'].update(not_physical_specimen_defaults=False),
    'make_source_outcomes_acceptance_targets': lambda f: f['context']['source_outcomes'].update(data_class='benchmark_acceptance_targets'),
    'expose_source_outcomes': lambda f: f['context']['source_outcomes'].update(visibility='actor_visible'),
    'replace_radius_by_theoretical_value': lambda f: f['context']['source_outcomes']['rows'][0].update(exterior_radius=6.525),
    'change_source_units': lambda f: f['context']['source_outcomes'].update(units='m'),
    'resolve_dimensional_conflict': lambda f: f['context']['source_conflicts']['conflicts'][0].update(status='resolved'),
    'globalize_family_local_conflict': lambda f: f['context']['source_conflicts']['conflicts'][0].update(family_scope=['ALL']),
    'erase_raw_correspondence_conflict': lambda f: f['context']['source_conflicts']['conflicts'].pop(6),
    'supply_unknown_default': lambda f: f['context']['unknowns']['unknowns'][0].update(default=0),
    'supply_physical_default': lambda f: f['context']['unknowns']['unknowns'][0].update(physical_default=True),
    'claim_archive_reread': lambda f: f['evidence']['F10']['reported'].update(archive_not_reviewed=False),
    'claim_source_code_executed': lambda f: f['context']['source_access_audit']['readiness'].update(source_code_execution=True),
    'claim_physical_operation': lambda f: op(f, 'R13')['detail'].update(physical_implemented=True),
    'claim_source_robot_protocol': lambda f: op(f, 'R13')['detail'].update(source_is_robot_protocol=True),
    'bypass_per_edge_folding': lambda f: f['context']['preparation_routes'].update(no_service_shortcut=False),
    'erase_camera_revision_invalidation': lambda f: f['context']['dependencies']['revision_invalidation'].pop('camera_or_lens_or_reference_or_fixture_change'),
    'closeout_requires_scientific_success': lambda f: f['context']['lifecycle_contract']['failure_edges'][0].update(scientific_success_required=True),
    'cross_fixture_unmount': lambda f: f['context']['recovery_boundaries']['release_selection'].update(corner_fixture='R19 then R30'),
    'erase_conditional_closeout': lambda f: route(f, 'CLOSEOUT')['detail'].pop('selection_rule'),
    'relabel_r06_as_transport': lambda f: op(f, 'R06')['detail'].update(primary_target='inspection.rest_dock'),
    'switch_r13_to_corner_target': lambda f: op(f, 'R13')['detail'].update(primary_target='qual.corner.base'),
    'change_control_target': lambda f: op(f, 'R19')['detail'].update(control_target='rig.plate_control.0'),
    'erase_contextual_fixture_selector': lambda f: f['context']['asset_binding_plan']['contextual_anchor_bindings'].pop(),
    'swap_contextual_fixture_class': lambda f: f['context']['asset_binding_plan']['contextual_anchor_bindings'][0].update(actual_fixture_class='corner_load'),
    'unknown_anchor': lambda f: op(f, 'R13')['detail']['anchor_ids'].append('ANCHOR.live.robot'),
    'unknown_asset': lambda f: op(f, 'R13')['detail']['asset_ids'].append('A99'),
    'drop_task_binding': lambda f: f['context']['asset_binding_plan']['operation_bindings'].pop(),
    'qualify_nominal_binding': lambda f: f['context']['asset_binding_plan']['operation_bindings'][0].update(physical_qualified=True),
    'nominal_anchor_grants_motion': lambda f: f['context']['asset_binding_plan'].update(nominal_anchor_is_motion_permission=True),
    'alter_polymer_alias': lambda f: f['context']['asset_binding_plan'].update(family_aliases={'PP1': 'CS1'}),
    'qualify_scene_geometry': lambda f: f['context']['asset_binding_plan']['assets'][0].update(physical_geometry_validated=True),
    'corrupt_source_hash': lambda f: f['source_files']['branches.json'].update(sha256='0' * 64),
    'corrupt_asset_hash': lambda f: f['asset_links'][0].update(sha256='f' * 64),
    'replace_local_link_with_remote': lambda f: f['source_files']['branches.json'].update(url='https://example.invalid/published/branches.json'),
    'source_link_traversal': lambda f: f['source_files']['branches.json'].update(url='../../../../branches.json'),
    'invent_remote_publication': lambda f: f.update(source_publication='Published and verified remotely'),
    'omit_evidence': lambda f: f['evidence'].pop('F10'),
    'false_boolean_as_integer_zero': lambda f: f.update(actor_projection_implemented=0),
    'nested_false_boolean_as_integer_zero': lambda f: op(f, 'R13')['detail'].update(physical_implemented=0),
    'true_boolean_as_integer_one': lambda f: route(f, 'PP_RIGID')['detail']['state_loop'].update(same_specimen_required=1),
    'integer_as_float': lambda f: f['context']['controls_and_repeats'].update(source_configurations=8.0),
    'integer_as_boolean': lambda f: f['context']['controls_and_repeats'].update(source_quantitative_specimens=True),
    'null_as_empty_string': lambda f: f['context']['controls_and_repeats'].update(authored_repeat_default=''),
    'expose_actor_projection': lambda f: f.update(visibility='actor_visible', actor_projection_implemented=True),
    'inflate_runnable_count': lambda f: f['context']['RELEASE_BOUNDARY'].update(validated_runnable_whole_paper_tasks=1),
    'rewrite_all_unqualified_claims': lambda f: rewrite_every_string(f, 'unqualified', 'qualified'),
}


def hostile_test(mutate):
    def test(self):
        self.assertRejected(mutate)
    return test


for name, mutation in MUTATIONS.items():
    setattr(ArcMorphIndependentHostileMutationTests, 'test_reject_' + name, hostile_test(mutation))


if __name__ == '__main__':
    unittest.main()
