"""Independent, offline wetting fidelity and hostile-mutation checks.

Run from repository root:
  python3 -B -m unittest discover -s viewer/task_explorer_v1/tests -p test_wetting_independent.py -v

Expectations come directly from the frozen source documents, not adapter maps.
Hash baselines were independently read from local commit 23799405e6a68909a769c98285de5f22231965bc.
No browser, network, solver, device, source workbook or scientific task is run.
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
import xml.etree.ElementTree as ET

VIEWER = Path(__file__).resolve().parents[1]
REPO = VIEWER.parents[1]
TASKS = Path(os.environ.get('SCIENCEGYM_TASKS', str(REPO / 'tasks')))
PACKAGE = TASKS / 'wetting_operations_v2'
ASSETS = TASKS.parent / 'assets' / 'wetting_scene_assets_v1'
PIN = '23799405e6a68909a769c98285de5f22231965bc'
sys.path.insert(0, str(VIEWER))
import wetting_adapters as subject

ALIASES = {'unknown_parameters.json': 'unknowns', 'evaluator_reference.json': 'acceptance',
           'lineage_contract.json': 'lineage'}
EARLIER = tuple('acoustic actuator_metrology afm_metrology atmospheric_optics beaded bianisotropic chiral cold_shape cooling dispim edge emvp fibre gear granular_assembly horn_acoustics hydrogel_optical laser_control lockable_origami martian_geophysics mechanical_backprop mechanical_logic microscopy origami_memory perovskite prismatic ring_origami solar_water sucrose_metrology thermal_jamming thermoelectric transistor varactor wavefront woven'.split())
EARLIER_DIGEST = '28812bfd777164893e6e887b3b96a5fec90f0085c20487765f84a64c69c6a097'
# Prior aggregate remains historical; the metadata-maintenance receipt binds current bytes.
HISTORICAL_PRE_MAINTENANCE_PACKAGE_DIGEST = '3a565c060b8c0c600a0df0f31e6796d2b076afdc24372b80f1cc6e4e1b08b66e'
FROZEN_PACKAGE_DIGEST = '68dff13f5091160c05f27dd4fc96d75d14023de9639881f61e82a13ea58c788b'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def strict(value):
    """Keep bool/int/float, null, array order and key presence distinctions."""
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
    if not pointer.startswith('/'):
        raise AssertionError('Not an RFC6901 pointer: ' + pointer)
    for token in pointer[1:].split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        document = document[int(token)] if isinstance(document, list) else document[token]
    return document


def index(records):
    return {record['id']: record for record in records}


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


class WettingIndependentFidelityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = {path.relative_to(PACKAGE).as_posix(): read(path)
                    for path in sorted(PACKAGE.rglob('*.json'))}
        cls.payload = read(VIEWER / 'data/wetting.json')
        cls.view = unpack(cls.payload)

    def assertStrictEqual(self, left, right, message=None):
        self.assertEqual(strict(left), strict(right), message)

    def test_01_counts_and_typed_route_classes(self):
        f = self.view
        self.assertEqual((len(f['operations']), len(f['routes']), len(f['source_files']), len(f['evidence'])),
                         (74, 17, 33, 16))
        self.assertEqual(collections.Counter(r['route_kind'] for r in f['routes']),
                         {'design_only': 1, 'closed_service': 10, 'external_service': 1,
                          'measurement_analysis': 1, 'numerical': 1, 'analysis': 1,
                          'closeout': 1, 'qualification_hold': 1})
        self.assertEqual({r['id'] for r in f['routes']},
                         {'R%02d' % n for n in range(16)} | {'HOLD_QUALIFICATION'})
        for name, count in {'source_branches': 16, 'source_json_documents': 33,
                            'scene_groups': 12, 'symbolic_anchors': 61,
                            'source_evidence_entries': 16, 'source_conflicts': 10,
                            'unresolved_input_groups': 25, 'source_reported_control_records': 9}.items():
            self.assertEqual(f['summary_counts'][name], count, name)

    def test_02_all_source_documents_reconstruct_with_exact_types(self):
        f = self.view
        self.assertEqual(len(self.docs), 33)
        self.assertEqual(set(f['source_files']), set(self.docs))
        reconstructed = {name: f['context'][ALIASES.get(name, name.removesuffix('.json'))]
                         for name in self.docs}
        self.assertStrictEqual(reconstructed, self.docs)
        self.assertEqual(set(f['context']),
                         {ALIASES.get(name, name.removesuffix('.json')) for name in self.docs})
        self.assertIn('review/INDEPENDENT_REVIEW.json', reconstructed)

    def test_03_every_operation_pointer_and_display_field_is_exact(self):
        originals = self.docs['operations.json']['operations']
        self.assertStrictEqual([o['detail'] for o in self.view['operations']], originals)
        for position, (shown, original) in enumerate(zip(self.view['operations'], originals)):
            with self.subTest(operation=original['id']):
                self.assertEqual(shown['source_file'], 'operations.json')
                self.assertEqual(shown['source_pointer'], '/operations/' + str(position))
                self.assertStrictEqual(resolve(self.docs[shown['source_file']], shown['source_pointer']), shown['detail'])
                for display, source in [('id', 'id'), ('title', 'description'), ('stage', 'route_id'),
                                        ('objects', 'asset_ids'), ('recovery', 'failure_transition'),
                                        ('sources', 'source_evidence_ids'), ('unknowns', 'unknown_ids')]:
                    self.assertStrictEqual(shown[display], original[source])
                self.assertStrictEqual(shown['actions'], [original['description']])
                self.assertStrictEqual(shown['pre'], {k: original[k] for k in
                    ('predecessor_operation_ids', 'requires_route_outputs_from', 'required_context')})
                self.assertStrictEqual(shown['acceptance'], {k: original[k] for k in
                    ('required_record_type', 'evidence_role', 'required_context')})
                self.assertStrictEqual(shown['provenance'], {k: original[k] for k in
                    ('step_origin', 'source_is_robot_protocol')})
                self.assertIsNone(shown['loop'])
                self.assertIn('No post-state field supplied', shown['post'])
                self.assertIn('not an observed post-state', shown['display_mapping_basis'])
                self.assertIn('not a paper quotation', shown['display_title_basis'])
                self.assertIs(original['source_is_robot_protocol'], False)
                self.assertIs(original['physical_implemented'], False)
                self.assertEqual(original['step_origin'], 'independently_authored_robot_task_design')

    def test_04_routes_and_every_nested_contract_pointer_resolve(self):
        branches = self.docs['branches.json']['branches']
        self.assertEqual(len(branches), 16)
        for position, branch in enumerate(branches):
            shown = route(self.view, branch['id'])
            self.assertStrictEqual(shown['detail'], branch)
            self.assertEqual(shown['source_pointer'], '/branches/' + str(position))
            self.assertEqual(members(shown), branch['route_operation_ids'])
            self.assertEqual(shown['source_file'], 'branches.json')
            self.assertIs(shown['metadata_only'], False)
        all_members = []
        for shown in self.view['routes']:
            self.assertStrictEqual(shown['detail'], resolve(self.docs[shown['source_file']], shown['source_pointer']))
            all_members.extend(members(shown))
            for node in nodes(shown['nodes']):
                if node['type'] != 'op':
                    self.assertIs(node['ordered'], False)
                    self.assertNotEqual(node['type'], 'loop')
                if node['type'] == 'condition':
                    meta = node['meta']
                    self.assertStrictEqual(meta['source_contract'], resolve(self.docs[meta['source_file']], meta['source_pointer']))
        self.assertEqual(collections.Counter(all_members), collections.Counter(o['id'] for o in self.view['operations']))

    def test_05_hold_is_metadata_only_and_never_an_operation(self):
        f = self.view
        self.assertEqual(f['default_route'], 'HOLD_QUALIFICATION')
        hold = route(f, f['default_route'])
        self.assertIs(hold['metadata_only'], True)
        self.assertEqual(hold['route_kind'], 'qualification_hold')
        self.assertEqual(members(hold), [])
        self.assertNotIn('HOLD_QUALIFICATION', index(f['operations']))
        self.assertEqual(len(hold['nodes']), 1)
        self.assertEqual(hold['nodes'][0]['type'], 'condition')
        self.assertStrictEqual(hold['detail'], self.docs['episode_input_contract.json'])
        self.assertIs(hold['detail']['physical_runtime_available'], False)
        self.assertIn('success', hold['detail']['forbidden_actor_fields'])
        self.assertIn('sensor values', hold['detail']['forbidden_actor_fields'])

    def test_06_dependencies_keep_applicable_material_ancestry_and_closeout(self):
        f = self.view
        for name in ('dependencies', 'preparation_routes', 'lifecycle_contract', 'lineage_contract',
                     'transport_routes', 'recovery_boundaries'):
            self.assertStrictEqual(f['dependencies'][name], self.docs[name + '.json'])
        d = f['context']['dependencies']
        self.assertEqual(d['routes']['R03'], ['R01', 'R02'])
        self.assertIn('not that every experiment uses both silicone families', d['logical_note'])
        self.assertIn('never waits for analysis success', d['scientific_dependency_rule'])
        self.assertEqual({e['from'] for e in d['failure_or_abort_edges']}, {'R%02d' % n for n in range(15)})
        for edge in d['failure_or_abort_edges']:
            self.assertEqual(edge['to'], 'R15')
            self.assertIn('not a declaration that analysis dependencies passed', edge['meaning'])
        for branch in self.docs['branches.json']['branches']:
            self.assertEqual(branch['depends_on'], d['routes'][branch['id']])
            self.assertEqual(branch['applicability'], 'Only relevant material/cohort ancestors, not every silicone family')
            self.assertIs(branch['closeout_reachable_on_abort'], True)
        self.assertEqual(op(f, 'R15_O01')['pre']['predecessor_operation_ids'], [])
        for shown in f['operations']:
            if shown['stage'] == 'R15':
                self.assertEqual(shown['pre']['requires_route_outputs_from'], [])
                self.assertIn('held_contained', shown['detail']['closure_rule'])
        rules = f['context']['lifecycle_contract']['closure_rules']
        self.assertIn('Request is not safe-state evidence', rules)
        self.assertIn('Unknown isolation remains held_contained', rules)
        for edge in f['context']['lifecycle_contract']['failure_edges']:
            self.assertIs(edge['scientific_success_required'], False)

    def test_07_material_receipts_age_and_specimen_ancestry_remain_distinct(self):
        c = self.view['context']
        materials = index(c['material_cards']['cards'])
        self.assertEqual(set(materials), {'PDMS_9:1', 'PDMS_30:1', 'PDMS_50:1', 'CY_5:6', 'CY_9:10'})
        for name, card in materials.items():
            self.assertEqual(card['preparation_route'], 'R01' if name.startswith('PDMS') else 'R02')
            self.assertEqual(card['age_window_weeks'], [1, 3] if name.startswith('PDMS') else [2, 3])
            self.assertIs(card['new_physical_specimen_available'], False)
            self.assertIn('not file mtime or a simulated timer', card['age_requires'])
        prep = c['preparation_routes']
        self.assertIn('zero local preparation credit', index(prep['routes'])['PREPARED_INPUT']['meaning'])
        self.assertEqual(prep['coupon_rule'], 'A slide film cannot be relabelled a tensile coupon')
        self.assertEqual(prep['pattern_rule'], 'Material preparation and external patterning are distinct receipts')
        self.assertIn('Failure, exclusion and retry records remain visible; no overwriting failed run with its replacement.', c['lineage']['event_invariants'])
        self.assertTrue({'droplet_id', 'film_id', 'surface_spot_id', 'acquisition_id', 'raw_file_hash'} <= set(c['lineage']['identity_fields']))

    def test_08_controls_and_repeats_do_not_multiply_independent_specimens(self):
        c = self.view['context']
        controls = index(c['controls_and_repeats']['source_reported'])
        self.assertEqual(len(controls), 9)
        self.assertEqual(len(c['controls_and_repeats']['authored_not_reported']), 4)
        self.assertEqual(controls['CTRL_MACRO']['repeat'], 'Nine independent measurements per displayed curve')
        self.assertIn('do not prove54 separate film specimens', controls['CTRL_MACRO']['caution'])
        self.assertEqual(controls['CTRL_PHASE']['repeat'], '44individual drying experiments')
        self.assertIn('No uniform allocation assumed', controls['CTRL_PHASE']['caution'])
        self.assertIn('within-droplet correlated', controls['CTRL_MICRO']['caution'])
        outcomes = c['source_outcomes']
        self.assertEqual(outcomes['analysis_reference']['mechanism_plot'],
                         {'CY5:6': {'droplets_N': 4, 'timepoints': 24}, 'CY9:10': {'droplets_N': 5, 'timepoints': 38}})
        self.assertEqual([x['N'] for x in outcomes['mechanical']['relaxation']], [7, 5, 6, 6])
        self.assertIn('does not explicitly label these independent', outcomes['analysis_reference']['phase_N_semantics'])
        self.assertIn('Repeated frames/timepoints cannot increase independent droplet/sample counts.', c['lineage']['event_invariants'])

    def test_09_hazardous_patterning_remains_closed_external_receipt(self):
        f = self.view
        self.assertEqual(route(f, 'R07')['route_kind'], 'external_service')
        self.assertEqual(members(route(f, 'R07')), ['R07_O01', 'R07_O02', 'R07_O03', 'R07_O04'])
        self.assertEqual(op(f, 'R07_O01')['acceptance']['evidence_role'], 'request_acknowledgement')
        self.assertEqual(op(f, 'R07_O02')['acceptance']['required_record_type'], 'sealed_patterned_sample_and_containment_receipt')
        self.assertEqual(op(f, 'R07_O04')['acceptance']['required_record_type'], 'hazardous_controls_exclusion_audit')
        self.assertIn('Keep synthesis, ink handling and high-voltage deposition absent', op(f, 'R07_O04')['actions'][0])
        boundary = f['context']['nonmanual_scope']
        self.assertIs(boundary['all_services_unimplemented'], True)
        self.assertIn('No quantum-dot synthesis, ink handling, HV deposition recipe', boundary['R07_boundary'])
        self.assertIn('no operational quantum-dot synthesis or NanoDrip recipe', route(f, 'R07')['detail']['qualification_gate'])
        for oid in members(route(f, 'R07')):
            self.assertIn('G_NO_CONTROL', op(f, oid)['detail']['guard_ids'])
            self.assertIn('G_CONTAINMENT', op(f, oid)['detail']['guard_ids'])

    def test_10_source_access_is_not_inflated(self):
        access = self.view['context']['source_access_audit']
        self.assertIn('M000-M125', access['MAIN']['read'])
        self.assertEqual(access['MAIN']['figure_pixel_inspection'], list(range(1, 7)))
        self.assertEqual(access['SI']['written_pages_read'], list(range(1, 16)))
        self.assertEqual(access['SI']['figures_visually_inspected'], list(range(1, 14)))
        self.assertEqual(access['SI']['visually_inspected_pdf_pages'], [2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14])
        self.assertEqual(access['VIDEO']['sampled_seconds'], [0, 10, 20, 30, 40, 50])
        self.assertIn('No continuous playback', access['VIDEO']['read_status'])
        self.assertIs(access['VIDEO']['not_a_measurement_record'], True)
        self.assertIs(access['SOURCE_DATA']['numeric_cells_read'], False)
        self.assertIs(access['SOURCE_DATA']['raw_data_reanalysis'], False)
        self.assertEqual(len(access['SOURCE_DATA']['workbook_sheet_names_inspected']), 28)
        self.assertNotIn('Supplementary Figure 9', access['SOURCE_DATA']['workbook_sheet_names_inspected'])
        self.assertIn('not acquired or run', access['EXTERNAL_DEPENDENCIES']['code'])

    def test_11_numerical_inference_and_observation_have_separate_roles(self):
        f = self.view
        self.assertEqual(route(f, 'R13')['route_kind'], 'numerical')
        self.assertEqual(route(f, 'R14')['route_kind'], 'analysis')
        self.assertIn('never direct observations', op(f, 'R13_O02')['actions'][0])
        self.assertIn('never relabel the inferred field as a captured reference image', op(f, 'R13_O04')['actions'][0])
        self.assertEqual(op(f, 'R13_O05')['acceptance']['required_record_type'], 'qualified_inverse_FE_input_output_receipt')
        self.assertIn('do not use displacement-field tangents as the current-surface tangent', op(f, 'R14_O03')['actions'][0])
        self.assertEqual(op(f, 'R14_O05')['acceptance']['required_record_type'], 'conditional_equilibrium_comparison')
        self.assertIn('Ogden FE inversion', f['context']['analysis_contracts']['not_implemented'])
        outcomes = f['context']['source_outcomes']
        for key in ('reference_only', 'not_acceptance_targets', 'not_actor_visible'):
            self.assertIs(outcomes[key], True)
        self.assertIs(outcomes['new_observations'], False)
        self.assertIs(outcomes['prior_literature_moduli']['not_new_measurement'], True)
        self.assertIn('rad/s', f['context']['lineage']['measurement_units']['angular_frequency'])
        self.assertIn('physical triangular areas', f['context']['analysis_contracts']['integration_boundary'])

    def test_12_conflicts_unknowns_and_evidence_remain_claim_local(self):
        f = self.view
        conflicts = index(f['context']['source_conflicts']['conflicts'])
        unknowns = index(f['context']['unknowns']['unknowns'])
        self.assertEqual(set(conflicts), {'C%02d' % n for n in range(1, 11)})
        self.assertEqual(set(unknowns), {'U%02d' % n for n in range(1, 26)})
        self.assertEqual(set(f['evidence']), {'E%02d' % n for n in range(1, 17)})
        self.assertStrictEqual(f['evidence'], index(self.docs['evidence_map.json']['records']))
        for conflict in conflicts.values():
            self.assertEqual(conflict['state'], 'UNRESOLVED_OR_SCOPE_DISTINCTION')
            self.assertIn('Block only affected calculation', conflict['block_policy'])
            self.assertIn('Safe-state and archive never depend on resolution', conflict['block_policy'])
        self.assertIn('220', conflicts['C01']['source_a'])
        self.assertIn('228', conflicts['C01']['source_b'])
        self.assertIn('measured, literature-derived', conflicts['C04']['policy'])
        for unknown in unknowns.values():
            self.assertEqual(unknown['state'], 'unresolved_not_defaulted')
            self.assertIs(unknown['safe_closeout_exception'], True)
            self.assertIs(unknown['not_a_global_design_block'], True)
        for shown in f['operations']:
            d = shown['detail']
            self.assertTrue(set(d['source_evidence_ids']) <= set(f['evidence']))
            self.assertTrue(set(d['unknown_ids']) <= set(unknowns))
            self.assertTrue(set(d['conflict_ids']) <= set(conflicts))
            self.assertTrue(set(d['predecessor_operation_ids']) <= set(index(f['operations'])))

    def test_13_task_to_original_scene_bindings_and_unqualified_anchors(self):
        f = self.view
        plan = f['context']['asset_binding_plan']
        self.assertEqual(plan['asset_pack_id'], 'wetting_transition_scene_assets_v1')
        self.assertEqual(ASSETS.name, 'wetting_scene_assets_v1')
        groups = {x['asset_id']: x for x in plan['assets']}
        canonical = {x['asset_id'] + '.' + anchor for x in plan['assets'] for anchor in x['required_anchor_ids']}
        self.assertEqual((len(groups), len(canonical)), (12, 61))
        anchors = read(ASSETS / 'affordances.json')['anchors']
        self.assertEqual({a['asset_id'] + '.' + a['anchor_id'] for a in anchors}, canonical)
        for anchor in anchors:
            self.assertEqual(anchor['coordinate_status'], 'authored_unqualified')
            self.assertIsNone(anchor['physical_qualified_transform'])
            self.assertIs(anchor['physical_execution'], False)
            self.assertIs(anchor['physical_grasp_enabled'], False)
        concrete = {b['operation_id']: b for b in read(ASSETS / 'operation_bindings.json')['bindings']}
        self.assertEqual(set(concrete), set(index(f['operations'])))
        for authored in plan['operation_bindings']:
            binding = concrete[authored['operation_id']]
            for key, value in authored.items():
                self.assertStrictEqual(binding[key], value, (authored['operation_id'], key))
        for shown in f['operations']:
            d = shown['detail']
            self.assertTrue(set(d['anchor_ids']) <= canonical)
            for aid in d['asset_ids']:
                self.assertIn(d['id'], groups[aid]['bind_operation_ids'])
            self.assertEqual(concrete[d['id']]['anchor_ids'], d['anchor_ids'])
            self.assertIs(concrete[d['id']]['physical_motion_qualified'], False)
            self.assertIs(concrete[d['id']]['physics_implemented'], False)

    def test_14_links_are_local_hash_bound_without_remote_publication_claim(self):
        f = self.view
        self.assertEqual(f['source_commit'], PIN)
        self.assertEqual(f['source_link_mode'], 'repository_relative_frozen_local_snapshot')
        self.assertIn('remote publication is not asserted', f['source_publication'])
        self.assertEqual(f['source_folder'], '../../tasks/wetting_operations_v2/')
        for name, entry in f['source_files'].items():
            self.assertEqual(entry['repository_path'], 'tasks/wetting_operations_v2/' + name)
            self.assertEqual(entry['url'], '../../tasks/wetting_operations_v2/' + name)
            self.assertEqual((VIEWER / entry['url']).resolve(), (PACKAGE / name).resolve())
            self.assertEqual(entry['sha256'], hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest())
        self.assertEqual({x['path'] for x in f['asset_links']},
                         {'assets/wetting_scene_assets_v1/' + name for name in
                          ('README.md', 'evidence/dimensions.png', 'evidence/handling.png', 'evidence/overview.png')})
        for entry in f['asset_links']:
            self.assertEqual(entry['url'], '../../' + entry['path'])
            self.assertEqual(entry['sha256'], hashlib.sha256((VIEWER / entry['url']).read_bytes()).hexdigest())

    def test_15_json_javascript_markdown_and_svg_expose_all_routes(self):
        js = (VIEWER / 'data/wetting.js').read_text()
        encoded = js.split('["wetting"]=', 1)[1].rsplit(';', 1)[0]
        self.assertStrictEqual(json.loads(encoded), self.payload)
        text = (VIEWER / 'docs/wetting.md').read_text()
        self.assertIn(self.view['source_warnings'], text)
        self.assertIn('unordered source inventory', text)
        for shown in self.view['routes']:
            self.assertIn('## ' + shown['id'] + ' ', text)
        for shown in self.view['operations']:
            self.assertIn('`' + shown['id'] + '`', text)
            self.assertIn(shown['title'], text)
        for href in re.findall(r'\]\(([^)]+)\)', text):
            if not href.startswith(('https:', 'http:', '#')):
                self.assertTrue((VIEWER / 'docs' / href.split('#', 1)[0]).is_file()
                                or (VIEWER / 'docs' / href.split('#', 1)[0]).is_dir(), href)
        spec = importlib.util.spec_from_file_location('independent_wetting_builder', VIEWER / 'build.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        for shown in self.view['routes']:
            candidate = copy.deepcopy(self.view)
            candidate['default_route'] = shown['id']
            rendered = builder.svg(candidate)
            tree = ET.fromstring(rendered)
            self.assertNotIn('marker-end=', rendered)
            self.assertIn('No adjacency arrows', rendered)
            self.assertIn('0 validated runnable whole-paper tasks', rendered)
            texts = [n.text or '' for n in tree.findall('.//{http://www.w3.org/2000/svg}text')]
            displayed = [t.split(' · ')[1] for t in texts if re.match(r'^\d+ · R\d\d_O\d\d$', t)]
            self.assertEqual(displayed, members(shown))
        ET.parse(VIEWER / 'diagrams/wetting.svg')

    def test_16_design_only_and_author_evaluator_boundary(self):
        f = self.view
        self.assertEqual(f['family_scope'], 'paper_level_design')
        self.assertEqual(f['visibility'], 'author_evaluator_reference_only')
        self.assertIs(f['actor_projection_implemented'], False)
        boundary = f['context']['RELEASE_BOUNDARY']
        self.assertIs(boundary['whole_paper_design_accounted_for'], True)
        for key in ('whole_paper_execution_complete', 'physical_execution', 'physical_simulation',
                    'scientific_reproduction', 'exact_geometry_validated'):
            self.assertIs(boundary[key], False)
        self.assertEqual(boundary['validated_runnable_whole_paper_tasks'], 0)
        self.assertIn('no real physics, safe grasp or robot motion', f['source_warnings'])
        self.assertIn('Read-only author/evaluator inspection', f['status'])
        self.assertTrue(subject.validate_projection(copy.deepcopy(f), PACKAGE))

    def test_17_previous_35_families_have_all_140_frozen_outputs(self):
        paths = ['viewer/task_explorer_v1/' + folder + '/' + family + extension
                 for family in EARLIER
                 for folder, extension in [('data', '.json'), ('data', '.js'), ('docs', '.md'), ('diagrams', '.svg')]]
        self.assertEqual((len(EARLIER), len(paths)), (35, 140))
        self.assertEqual(digest_files(REPO, paths), EARLIER_DIGEST)

    def test_18_current_metadata_revision_bytes_are_pinned(self):
        paths = []
        for directory in (PACKAGE, ASSETS):
            for path in directory.rglob('*'):
                if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                    paths.append(path.relative_to(TASKS.parent).as_posix())
        self.assertEqual(len(paths), 86)
        self.assertEqual(digest_files(TASKS.parent, paths), FROZEN_PACKAGE_DIGEST)


class WettingIndependentHostileMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pristine = unpack(read(VIEWER / 'data/wetting.json'))

    def assertRejected(self, mutate):
        candidate = copy.deepcopy(self.pristine)
        before = strict(candidate)
        mutate(candidate)
        self.assertNotEqual(strict(candidate), before, 'Hostile fixture must actually change the projection')
        with self.assertRaises(ValueError):
            subject.validate_projection(candidate, PACKAGE)
        self.assertEqual(strict(self.pristine), before, 'Validation must not mutate the pristine fixture')


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


# Independently authored attacks alter both obvious fields and less visible source context.
# They are projection mutations only, never changes to immutable packages.
MUTATIONS = {
    'omit_nested_independent_review': lambda f: f['context'].pop('review/INDEPENDENT_REVIEW'),
    'omit_an_operation': lambda f: f['operations'].pop(),
    'duplicate_an_operation': lambda f: f['operations'].append(copy.deepcopy(f['operations'][0])),
    'invent_hold_operation': lambda f: f['operations'].append({'id': 'HOLD_QUALIFICATION'}),
    'activate_hold_navigation': lambda f: route(f, 'HOLD_QUALIFICATION').update(metadata_only=False),
    'insert_operation_in_hold': lambda f: route(f, 'HOLD_QUALIFICATION')['nodes'].append('R07_O01'),
    'omit_route': lambda f: f['routes'].pop(3),
    'invent_route_chronology': lambda f: route(f, 'R03')['nodes'][0].update(ordered=True),
    'reorder_route_membership': lambda f: route(f, 'R09')['nodes'][0]['children'].reverse(),
    'wrong_operation_source_pointer': lambda f: op(f, 'R13_O04').update(source_pointer='/operations/0'),
    'wrong_contract_source_pointer': lambda f: route(f, 'R07')['nodes'][1]['meta'].update(source_pointer='/branches/6'),
    'invent_observed_post_state': lambda f: op(f, 'R07_O01').update(post={'safe': True, 'completed': True}),
    'promote_request_to_measurement': lambda f: op(f, 'R07_O01')['acceptance'].update(evidence_role='independent_scoped_record'),
    'replace_authored_action': lambda f: op(f, 'R13_O04').update(actions=['Load an observed reference image']),
    'erase_required_predecessor': lambda f: op(f, 'R13_O04')['pre'].update(predecessor_operation_ids=[]),
    'add_all_material_and_gate': lambda f: op(f, 'R09_O01')['pre'].update(requires_route_outputs_from=['R01', 'R02', 'R03', 'R08']),
    'closeout_waits_for_scientific_success': lambda f: op(f, 'R15_O01')['pre'].update(requires_route_outputs_from=['R14']),
    'physical_route_credit': lambda f: route(f, 'R07')['detail'].update(physical_implemented=True),
    'invent_qd_control_action': lambda f: op(f, 'R07_O04').update(actions=['Enable the external preparation controls']),
    'remove_closed_service_boundary': lambda f: f['context']['nonmanual_scope'].pop('R07_boundary'),
    'claim_services_implemented': lambda f: f['context']['nonmanual_scope'].update(all_services_unimplemented=False),
    'erase_prepared_input_no_credit': lambda f: f['context']['preparation_routes']['routes'][1].update(meaning='Prepared inputs complete local fabrication'),
    'swap_material_age_lineage': lambda f: f['context']['material_cards']['cards'][0].update(preparation_route='R02', age_window_weeks=[2, 3]),
    'count_timepoints_as_droplets': lambda f: f['context']['source_outcomes']['analysis_reference']['mechanism_plot']['CY5:6'].update(droplets_N=24),
    'invent_44_condition_matrix': lambda f: f['context']['controls_and_repeats']['source_reported'][5].update(repeat='44 independent uniform conditions'),
    'resolve_thickness_conflict': lambda f: f['context']['source_conflicts']['conflicts'][0].update(state='RESOLVED', source_a='228 micrometres'),
    'make_unknown_a_default': lambda f: f['context']['unknowns']['unknowns'][0].update(state='qualified_default', value=1),
    'claim_full_movie_review': lambda f: f['context']['source_access_audit']['VIDEO'].update(read_status='Continuously reviewed in full'),
    'claim_workbook_cells_read': lambda f: f['context']['source_access_audit']['SOURCE_DATA'].update(numeric_cells_read=True),
    'invent_missing_si9_workbook': lambda f: f['context']['source_access_audit']['SOURCE_DATA']['workbook_sheet_names_inspected'].append('Supplementary Figure 9'),
    'collapse_inferred_into_measured_everywhere': lambda f: rewrite_every_string(f, 'inferred', 'measured'),
    'make_reference_outcomes_acceptance_targets': lambda f: f['context']['source_outcomes'].update(not_acceptance_targets=False),
    'claim_new_observations': lambda f: f['context']['source_outcomes'].update(new_observations=True),
    'change_physical_units': lambda f: f['context']['lineage']['measurement_units'].update(angular_frequency='Hz'),
    'alter_independent_fit_roles': lambda f: op(f, 'R14_O03')['acceptance'].update(required_record_type='single_combined_ridge_fit'),
    'remove_integration_conflict': lambda f: op(f, 'R14_O04')['detail'].update(conflict_ids=[]),
    'unknown_anchor': lambda f: op(f, 'R07_O02')['detail']['anchor_ids'].append('A04.live_control'),
    'drop_asset_binding': lambda f: f['context']['asset_binding_plan']['operation_bindings'].pop(),
    'invent_qualified_scene_geometry': lambda f: f['context']['asset_binding_plan']['assets'][0].update(physical_geometry_validated=True),
    'corrupt_source_hash': lambda f: f['source_files']['branches.json'].update(sha256='0' * 64),
    'corrupt_original_asset_hash': lambda f: f['asset_links'][0].update(sha256='f' * 64),
    'replace_local_link_with_remote_claim': lambda f: f['source_files']['branches.json'].update(url='https://example.invalid/published/branches.json'),
    'traversal_in_source_link': lambda f: f['source_files']['branches.json'].update(url='../../../../branches.json'),
    'invent_remote_publication': lambda f: f.update(source_publication='Published and verified on remote'),
    'remove_source_evidence': lambda f: f['evidence'].pop('E16'),
    'change_false_boolean_to_zero': lambda f: f.update(actor_projection_implemented=0),
    'change_integer_count_to_float': lambda f: f['summary_counts'].update(source_branches=16.0),
    'expose_actor_context': lambda f: f.update(visibility='actor_visible', actor_projection_implemented=True),
    'inflate_validated_runnable_count': lambda f: f['context']['RELEASE_BOUNDARY'].update(validated_runnable_whole_paper_tasks=1),
}


def hostile_test(mutate):
    def test(self):
        self.assertRejected(mutate)
    return test


for name, mutation in MUTATIONS.items():
    setattr(WettingIndependentHostileMutationTests, 'test_reject_' + name, hostile_test(mutation))


if __name__ == '__main__':
    unittest.main()
