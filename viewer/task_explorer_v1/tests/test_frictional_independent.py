"""Independent, byte-pinned frictional viewer audit against supplied release ZIPs.

No adapter, generator, package validator, or projection helper is imported.
The companion oracle was extracted directly from the two immutable release
ZIPs and each member checked against this checkout. Portable runs retain all
member, byte, and SHA-256 pins. Hostile projections are serialized in memory.
These tests check faithful static inspection, not real hardware, scientific
replication, receipt authentication, source rereading, or pressure qualification.
"""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import unittest
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('SCIENCEGYM_ROOT', str(HERE.parents[2]))).resolve()
VIEW = ROOT / 'viewer/task_explorer_v1'
ORACLE = json.loads((HERE / 'frictional_frozen_oracle.json').read_text())
PACKAGES = ORACLE['packages']
OP_IDS = [f'R{i:02}' for i in range(1, 13)]
BRANCH_IDS = [f'B{i:02}' for i in range(1, 10)]
ALIASES = {'evaluator_reference.json': 'acceptance', 'lineage_contract.json': 'lineage'}
REFERENCE_ROUTES = {
    'OPERATIONS_REFERENCE': ('operations.json', 'operation_inventory', False),
    'PREPARATION_REFERENCE': ('preparation_routes.json', 'preparation_reference', True),
    'CONTROLS_REFERENCE': ('controls_and_repeats.json', 'controls_reference', True),
    'FAILURE_REFERENCE': ('failure_and_closeout.json', 'failure_reference', True),
    'BINDINGS_REFERENCE': ('shared_binding_contract.json', 'bindings_reference', True),
    'OUTCOMES_REFERENCE': ('source_outcomes_reference.json', 'source_outcomes_reference', True),
    'HOLD_QUALIFICATION': ('unknown_inputs.json', 'qualification_hold', True),
}
FAMILY_KEYS = set('id label title doi color family_scope family_scope_label source_commit '
    'source_archive_sha256 asset_archive_sha256 source_folder source_link_mode source_publication '
    'status source_warnings visibility actor_projection_implemented operations routes evidence context '
    'dependencies source_files default_route default_route_basis asset_links asset_boundary summary_counts'.split())
OP_KEYS = set('id title stage actions objects pre post acceptance recovery sources unknowns provenance '
    'loop detail source_file source_pointer display_action_ownership display_mapping_basis'.split())
ROUTE_KEYS = set('id label route_kind metadata_only nodes basis detail source_file source_pointer navigation_basis'.split())


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical_digest(value):
    return digest(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())


def same_json(actual, expected):
    """Exact JSON values/types, including false versus zero and 1 versus 1.0."""
    return json.dumps(actual, sort_keys=True, ensure_ascii=False, allow_nan=False) == json.dumps(
        expected, sort_keys=True, ensure_ascii=False, allow_nan=False)


def decode_shared(pooled):
    """Strict independent pool decoder rejects malformed, boolean and cyclic refs."""
    assert isinstance(pooled, dict), 'Object family required'
    pool = pooled.get('shared', [])
    assert isinstance(pool, list), 'Pool must be an array'
    def expand(value, stack=()):
        if isinstance(value, dict):
            if '$shared' in value:
                assert set(value) == {'$shared'}, 'Mixed pooled reference'
                index = value['$shared']
                assert type(index) is int and 0 <= index < len(pool), 'Invalid pooled index'
                assert index not in stack, 'Cyclic pooled reference'
                return expand(pool[index], stack + (index,))
            return {key: expand(child, stack) for key, child in value.items()}
        if isinstance(value, list):
            return [expand(child, stack) for child in value]
        return value
    return {key: expand(value) for key, value in pooled.items() if key != 'shared'}


def resolve_pointer(document, pointer):
    if not pointer:
        return document
    assert pointer.startswith('/'), 'Absolute JSON pointer required'
    for token in pointer[1:].split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        document = document[int(token)] if isinstance(document, list) else document[token]
    return document


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.get('children', []))


def get_route(family, route_id):
    return next(route for route in family['routes'] if route['id'] == route_id)


def audit_raw(raw):
    assert set(raw) == set(PACKAGES)
    for kind, package in PACKAGES.items():
        assert set(raw[kind]) == set(package['files']), kind + ' exact member set'
        for name, expected in package['files'].items():
            value = raw[kind][name]
            assert len(value) == expected['bytes'], kind + '/' + name + ' bytes'
            assert digest(value) == expected['sha256'], kind + '/' + name + ' SHA256'
    return True


def audit_core_bindings(task, assets, raw):
    tc, ac = task['task_core_manifest.json'], assets['scene_core_manifest.json']
    assert tc['core_sha256'] == '53b34fa314bd5af659f60eb1265edbca2f3c813a60843248d96e989b1f6dee2c'
    assert ac['core_sha256'] == '8e3174e17fbd5567e971b3eb19ad3aaf598fb959e7318e428e4c014b11ce756b'
    for kind, core, count in [('task', tc, 42), ('asset', ac, 36)]:
        assert core['core_sha256'] == canonical_digest(core['files'])
        names = [r['path'] for r in core['files']]
        assert len(names) == len(set(names)) == count and names == sorted(names)
        for row in core['files']:
            payload = raw[kind][row['path']]
            assert len(payload) == row['bytes'] and digest(payload) == row['sha256']
    for t, a in [('task_core_manifest.json', 'paired_task_core_manifest.json'),
                 ('paired_scene_core_manifest.json', 'scene_core_manifest.json'),
                 ('shared_binding_contract.json', 'shared_binding_contract.json'),
                 ('scene_task_contract.json', 'shared_binding_contract.json'),
                 ('semantic_core.json', 'semantic_core.json')]:
        assert raw['task'][t] == raw['asset'][a]
    pair = task['asset_binding_plan.json']; ref = assets['paired_task_reference.json']
    assert pair['task_core_sha256'] == ref['task_core_sha256'] == tc['core_sha256']
    assert pair['scene_core_sha256'] == ref['scene_core_sha256'] == ac['core_sha256']
    binding = task['shared_binding_contract.json']; semantic = task['semantic_core.json']
    assert canonical_digest(binding) == pair['semantic_core_sha256'] == semantic['shared_binding_contract_sha256']
    assert digest(raw['task']['semantic_core.json']) == ref['semantic_core_file_sha256']
    assert binding['branch_ids'] == BRANCH_IDS and binding['route_ids'] == OP_IDS
    assert binding['unknown_ids'] == [f'U{i:02}' for i in range(1,21)]
    assert binding['station_ids'] == [f'ST{i:02}' for i in range(1,7)]
    assert binding['asset_ids'] == [f'A{i:02}' for i in range(1,9)]
    assert binding['model_implemented'] is False and binding['physical_execution_enabled'] is False
    assert len(binding['asset_groups']) == 8 and len(binding['stations']) == 6
    anchors = binding['anchors']; anchor_ids = {a['anchor_id'] for a in anchors}
    assert len(anchors) == len(anchor_ids) == 32
    assert all(a['kind'] == 'evidence_only_proxy' and a['physical_motion_target'] is False for a in anchors)
    inventory = assets['asset_inventory.json']
    assert inventory['asset_groups'] == binding['asset_groups']
    assert inventory['anchors'] == anchors
    for k,v in [('route_count',12),('station_count',6),('asset_group_count',8),('anchor_count',32)]:
        assert type(inventory[k]) is int and inventory[k] == v
    ops = task['operations.json']['operations']
    assert semantic['route_dependencies'] == {o['id']: o['depends_on'] for o in ops}
    for op, row in zip(ops,binding['route_bindings']):
        assert same_json(row, {'route_id':op['id'],'station_ids':[op['station']],
            'branch_ids':op['branch_ids'],'asset_ids':op['asset_ids'],
            'anchor_ids':op['anchor_ids'],'depends_on':op['depends_on']})
        assert set(op['anchor_ids']) <= anchor_ids
    return True


def audit_source_boundaries(task, assets):
    release = task['RELEASE_BOUNDARY.json']
    assert type(release['paper_level_designs']) is int and release['paper_level_designs'] == 1
    assert type(release['runnable_whole_paper_experiments']) is int and release['runnable_whole_paper_experiments'] == 0
    assert release['physical_qualification'] == 'HOLD_QUALIFICATION' and release['qualification_holds'] == 20
    for key in ['hardware_operation','robot_execution','fluid_simulation','raw_data_reproduced',
                'source_code_run','scientific_reproduction','github_writes','source_media_exported']:
        assert release[key] is False
    prov = task['provenance.json']
    assert prov['paper']['doi'] == '10.1038/ncomms1289'
    assert prov['source_license'] == 'CC BY-NC-SA 3.0 Unported'
    assert prov['source_license_url'] == 'https://creativecommons.org/licenses/by-nc-sa/3.0/'
    assert 'separate rights' in prov['third_party_images']
    assert all(r['exported'] is False for r in prov['source_receipts'])
    unknowns = task['unknown_inputs.json']
    assert unknowns['default_resolution_state'] == 'UNRESOLVED'
    assert [u['id'] for u in unknowns['unknowns']] == [f'U{i:02}' for i in range(1,21)]
    branches = task['branches.json']['branches']
    assert [b['id'] for b in branches] == BRANCH_IDS
    assert all(b['scientific_execution'] == 'UNRUN' for b in branches)
    assert 'Viscosity' in branches[5]['name'] and 'granular-fracturing' in branches[6]['name']
    assert 'External-comparison context' in branches[7]['evidence_type']
    assert 'no task-count increment' in branches[7]['translation_boundary']
    assert 'model' in branches[8]['evidence_type']
    ops = task['operations.json']['operations']
    assert [o['id'] for o in ops] == OP_IDS
    assert all(o['device_command_implemented'] is False and o['physical_execution_authority'] is False for o in ops)
    assert all(o['actor_action'] == 'Select operation_id and independently supplied evidence_id only' for o in ops)
    assert ops[6]['branch_ids'] == ['B06','B07']
    assert ops[10]['depends_on'] == [] and ops[10]['repeatable_by_job'] is True
    assert 'including failures, before R08-R10' in ops[10]['dependency_rule']
    assert ops[11]['depends_on'] == ['R10'] and 'no single global R11 token' in ops[11]['dependency_rule']
    life = task['lifecycle_contract.json']
    assert life['default'] == 'HOLD_QUALIFICATION'
    assert 'all job closeouts' in life['final_rule'] and 'two digital validation attempts' in life['retry_rule']
    assert life['final_science_states'] == {b: ('SOURCE_CONTEXT_ONLY' if b in ['B08','B09'] else 'UNRUN') for b in BRANCH_IDS}
    conflicts = task['source_conflicts.json']['conflicts_and_extraction_hazards']
    assert [c['id'] for c in conflicts] == ['C01','C02','C03','C04']
    assert any('1.0 ml/min' in o for o in conflicts[0]['observations'])
    assert any('0.1 ml/min' in o for o in conflicts[0]['observations'])
    assert 'do not silently revise' in conflicts[0]['handling']
    assert 'not a published correction' in conflicts[1]['classification']
    assert 'before numerical implementation' in conflicts[1]['handling']
    controls = task['controls_and_repeats.json']['reported']
    assert len(controls) == 9 and '100-fold' in controls[3]['control']
    assert 'Within-pattern sampling' in controls[6]['limit']
    assert task['analysis_contracts.json']['numerical_morphometry_implemented'] is False
    assert task['source_outcomes_reference.json']['numeric_reproduction'] is False
    assert len(task['source_outcomes_reference.json']['outcomes']) == 8
    assert len(task['source_facts.json']['facts']) == 22
    custody = task['sample_custody.json']
    assert len(custody['identity_fields']) == 18
    assert 'same grain microstate' in custody['custody_rules'][1]
    assert 'Do not assume reset/reuse' in custody['custody_rules'][2]
    scene = assets['scene_manifest.json']
    assert scene['physical_actuation_enabled'] is False and scene['scientific_simulation_performed'] is False
    assert 'SOURCE_SCALE' in scene['scale_boundary'] and 'illustrative' in scene['scale_boundary']
    ap = assets['provenance.json']
    assert ap['original_assets_and_code_license'] == 'Apache-2.0'
    assert 'CC BY-NC-SA 3.0' in ap['source_rights'] and 'not relicensed' in ap['source_rights']
    for key in ['no_copied_publisher_figures','no_source_movie_frames','no_source_CAD_or_code','no_external_texture_images']:
        assert ap[key] is True
    for key in ['source_model_implemented','physical_simulation_performed','hardware_action_performed']:
        assert ap[key] is False
    return True


def audit(family, task, assets, raw):
    """Audit the serialized public projection against independent raw source data."""
    assert set(family) == FAMILY_KEYS, 'No added telemetry/execution surface'
    context = {ALIASES.get(name, name[:-5]): value for name, value in task.items()}
    context['static_assets'] = assets
    assert len(task) == 38 and len(assets) == 35
    assert same_json(family['context'], context), 'All 73 source JSON documents remain recursively lossless'
    sources = {}
    for kind, documents in [('task', task), ('asset', assets)]:
        folder = PACKAGES[kind]['folder']
        for name in documents:
            key = name if kind == 'task' else 'static_assets/' + name
            sources[key] = {'url': '../../' + folder + '/' + name, 'repository_path': folder + '/' + name,
                            'sha256': digest(raw[kind][name])}
    assert same_json(family['source_files'], sources), 'Exact local source paths and hashes'
    assert family['id'] == 'frictional' and family['family_scope'] == 'paper_level_design'
    assert family['family_scope_label'] == 'WHOLE-PAPER DESIGN'
    assert family['title'] == task['provenance.json']['paper']['title']
    assert family['doi'] == '10.1038/ncomms1289'
    assert family['visibility'] == 'author_evaluator_reference_only' and family['actor_projection_implemented'] is False
    assert family['source_commit'] is None
    assert family['source_archive_sha256'] == PACKAGES['task']['archive_sha256']
    assert family['asset_archive_sha256'] == PACKAGES['asset']['archive_sha256']
    assert family['source_folder'] == '../../tasks/frictional_operations_v2/'
    assert family['source_link_mode'] == 'repository_relative_frozen_local_snapshot'
    assert 'remote publication is not asserted' in family['source_publication']
    assert family['default_route'] == 'HOLD_QUALIFICATION' and 'metadata-only' in family['default_route_basis']
    ops = task['operations.json']['operations']
    assert [op['id'] for op in family['operations']] == OP_IDS
    for i, (op, source) in enumerate(zip(family['operations'], ops)):
        assert set(op) == OP_KEYS
        assert same_json(op['detail'], source), source['id'] + ' exact full operation'
        assert op['title'] == source['name'] and op['stage'] == source['station']
        assert op['actions'] == [source['name']]
        for field, keys in [('objects', ['asset_ids', 'anchor_ids']), ('pre', ['depends_on', 'dependency_rule']),
                            ('acceptance', ['required_output', 'gate']), 
                            ('provenance', ['status_semantics', 'device_command_implemented', 'physical_execution_authority', 'actor_action'])]:
            assert same_json(op[field], {key: source[key] for key in keys if key in source}), source['id'] + ' exact ' + field
        assert same_json(op['unknowns'], source['unknown_refs'])
        assert op['source_file'] == 'operations.json' and op['source_pointer'] == f'/operations/{i}'
        assert op['post'] == ('No observed post-state field supplied; inspect the exact source contract. '
                              'No value or command is inferred.')
        assert op['recovery'] == ('No per-operation recovery; inspect exact family failure_and_closeout and lifecycle contracts field supplied; inspect the exact source contract. No value or command is inferred.')
        assert op['sources'] == [] and op['loop'] is None
        assert 'no' in op['display_action_ownership'].lower()
        assert 'never observed' in op['display_mapping_basis']
    routes = family['routes']
    assert [r['id'] for r in routes] == BRANCH_IDS + list(REFERENCE_ROUTES)
    assert len(routes) == 16
    for i, branch in enumerate(task['branches.json']['branches']):
        route = routes[i]
        assert same_json(route['detail'], branch)
        assert route['source_file'] == 'branches.json' and route['source_pointer'] == f'/branches/{i}'
        assert route['route_kind'] == 'source_scope_branch' and route['metadata_only'] is False
        members = [op for op in ops if branch['id'] in op['branch_ids']]
        nodes = [n for n in walk(route['nodes']) if n['type'] == 'op']
        assert [n['id'] for n in nodes] == [op['id'] for op in members], branch['id'] + ' source-derived membership'
        for node, member in zip(nodes, members):
            index = OP_IDS.index(member['id'])
            assert node['meta']['source_file'] == 'operations.json'
            assert node['meta']['source_pointer'] == f'/operations/{index}/branch_ids/{member["branch_ids"].index(branch["id"])}'
            assert node['meta']['operation_source_pointer'] == f'/operations/{index}/id'
            assert node['meta']['source_node'] == branch['id']
    for route_id, (filename, kind, metadata_only) in REFERENCE_ROUTES.items():
        route = get_route(family, route_id)
        assert route['source_file'] == filename and route['source_pointer'] == ''
        assert route['route_kind'] == kind and route['metadata_only'] is metadata_only
        assert same_json(route['detail'], task[filename])
        nodes = [n for n in walk(route['nodes']) if n['type'] == 'op']
        assert [n['id'] for n in nodes] == (OP_IDS if route_id == 'OPERATIONS_REFERENCE' else [])
    for route in routes:
        assert set(route) == ROUTE_KEYS
        assert same_json(resolve_pointer(task[route['source_file']], route['source_pointer']), route['detail'])
        assert 'no added scientific branch' in route['navigation_basis']
        assert 'zero validated runnable whole-paper tasks' in route['basis']
        assert 'HOLD_QUALIFICATION' in route['basis']
        assert len(route['nodes']) == (1 if route['metadata_only'] else 2)
        contracts = 0
        for node in walk(route['nodes']):
            assert node['type'] in {'op', 'obligations', 'condition'}, 'No invented conditional, repeat, or run nodes'
            meta = node.get('meta', {})
            if node['type'] == 'op':
                assert set(node) == {'type', 'id', 'meta'}
                expected_meta = {'source_file', 'source_pointer', 'source_node', 'meaning'}
                if route['id'] in BRANCH_IDS:
                    expected_meta.add('operation_source_pointer')
                    assert resolve_pointer(task[meta['source_file']], meta['operation_source_pointer']) == node['id']
                    assert meta['source_node'] == route['id']
                else:
                    assert meta['source_node'] == node['id']
                assert set(meta) == expected_meta
                assert resolve_pointer(task[meta['source_file']], meta['source_pointer']) == meta['source_node']
                assert 'not execution or inferred chronology' in meta['meaning']
            else:
                assert set(node) == {'type', 'label', 'ordered', 'children', 'meta'}
                assert node['ordered'] is False
                if node['type'] == 'condition':
                    contracts += 1
                    assert node['children'] == [] and set(meta) == {'source_file', 'source_pointer', 'source_contract'}
                    assert meta['source_file'] == route['source_file'] and meta['source_pointer'] == route['source_pointer']
                    assert same_json(meta['source_contract'], route['detail'])
                else:
                    assert set(meta) == {'order'} and 'chronology' in meta['order']
        assert contracts == 1
    assert 'telemetry' in get_route(family, 'OUTCOMES_REFERENCE')['label']
    assert 'NO' in get_route(family, 'HOLD_QUALIFICATION')['label']
    assert same_json(family['evidence'], {f['id']: f for f in task['source_facts.json']['facts']})
    dependencies = family['dependencies']
    assert 'display_rule' in dependencies
    for name, value in dependencies.items():
        if name != 'display_rule':
            assert name + '.json' in task and same_json(value, task[name + '.json']), 'Exact dependency source ' + name
    assert {'display_rule', 'dependencies', 'material_and_sample_dependencies', 'preparation_routes', 'lineage_contract',
            'sample_custody', 'lifecycle_contract', 'failure_and_closeout', 'station_contracts',
            'cross_device_measurements', 'analysis_contracts'} == set(dependencies)
    assert 'chronology' in dependencies['display_rule']
    counts = family['summary_counts']
    expected_counts = {'source_scope_branches': 9, 'authored_reference_views': 6, 'metadata_only_hold_views': 1,
        'source_json_documents': 38, 'asset_json_documents': 35, 'operation_templates': 12, 'source_evidence_entries': 22,
        'source_ambiguities': 4, 'reported_outcomes': 8, 'unresolved_input_groups': 20, 'controls': 9,
        'scene_groups': 8, 'symbolic_anchors': 32, 'stations': 6, 'task_core_files': 42, 'asset_core_files': 36}
    assert same_json(counts, expected_counts)
    assert family['source_warnings'] in family['status']
    for phrase in ['zero validated runnable whole-paper tasks', 'Read-only author/evaluator inspection',
                   'HOLD_QUALIFICATION']:
        assert phrase in family['status']
    warning = family['source_warnings'].lower()
    for phrase in ['coral-rate', '0.1', '1.0', 'boyle', 'reviewer inference', 'viscosity', 'granular fracture',
                   'borrowed', 'cc by-nc-sa', 'apache-2.0', 'r11', 'r12', 'source_scale', 'twenty', 'not', 'threshold', 'repeat']:
        assert phrase in warning, 'Missing conservative warning: ' + phrase
    for phrase in ['illustrative', 'No fluid simulation', 'never physical motion targets']:
        assert phrase in family['asset_boundary']
    names = ['README.md', 'previews/preview_01_overview.png', 'previews/preview_02_closed_service.png', 'previews/preview_03_evidence.png']
    assert len(family['asset_links']) == 4
    for link, name in zip(family['asset_links'], names):
        assert set(link) == {'label', 'path', 'url', 'sha256'}
        assert link['path'] == PACKAGES['asset']['folder'] + '/' + name
        assert link['url'] == '../../' + link['path'] and link['sha256'] == digest(raw['asset'][name])
    return True


class FrozenFrictionalOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = {kind: {name: (ROOT / p['folder'] / name).read_bytes() for name in p['files']}
                   for kind, p in PACKAGES.items()}
        audit_raw(cls.raw)
        cls.task = {name: json.loads(b) for name, b in cls.raw['task'].items() if name.endswith('.json')}
        cls.assets = {name: json.loads(b) for name, b in cls.raw['asset'].items() if name.endswith('.json')}
        cls.pooled = json.loads((VIEW / 'data/frictional.json').read_text())
        cls.family = decode_shared(cls.pooled)

    def test_01_frozen_source_membership_and_exact_bytes(self):
        for kind, p in PACKAGES.items():
            names = {file.relative_to(ROOT / p['folder']).as_posix() for file in (ROOT / p['folder']).rglob('*')
                     if file.is_file() and '__pycache__' not in file.parts}
            self.assertEqual(names, set(p['files']))
        self.assertTrue(audit_raw(self.raw))

    def test_02_supplied_archives_when_requested(self):
        explicit = os.environ.get('SCIENCEGYM_RELEASE_ARCHIVES')
        if not explicit:
            return  # Exact member-byte pins remain mandatory for portable checkouts.
        for kind, p in PACKAGES.items():
            archive = Path(explicit) / p['archive']
            self.assertTrue(archive.is_file(), 'Explicit immutable release ZIP missing')
            data = archive.read_bytes()
            self.assertEqual(len(data), p['archive_bytes'])
            self.assertEqual(digest(data), p['archive_sha256'])
            with zipfile.ZipFile(archive) as z:
                names = [n for n in z.namelist() if not n.endswith('/')]
                self.assertEqual(len(names), len(set(names)))
                self.assertEqual(len(names), p['archive_members'])
                self.assertEqual(set(names), {p['archive_prefix'] + n for n in p['files']})
                for name, value in self.raw[kind].items():
                    self.assertEqual(z.read(p['archive_prefix'] + name), value)

    def test_03_reciprocal_cores_and_binding_bijections(self):
        self.assertTrue(audit_core_bindings(self.task, self.assets, self.raw))

    def test_04_source_scope_rights_pressure_fluid_and_custody_boundaries(self):
        self.assertTrue(audit_source_boundaries(self.task, self.assets))

    def test_05_complete_serialized_projection_matches_source(self):
        self.assertTrue(audit(self.family, self.task, self.assets, self.raw))

    def test_06_js_registration_matches_pooled_json(self):
        prefix = 'window.SCIENCEGYM_DATA=window.SCIENCEGYM_DATA||{};window.SCIENCEGYM_DATA["frictional"]='
        source = (VIEW / 'data/frictional.js').read_text()
        self.assertTrue(source.startswith(prefix))
        self.assertTrue(same_json(json.loads(source[len(prefix):].strip().removesuffix(';')), self.pooled))
        self.assertIn('data/frictional.js', (VIEW / 'index.html').read_text())

    def test_07_every_recursive_document_loss_rejected(self):
        count = 0
        for key in self.family['context']:
            if key != 'static_assets':
                bad = copy.deepcopy(self.family)
                bad['context'].pop(key)
                with self.subTest(task_document=key), self.assertRaises(AssertionError):
                    audit(json.loads(json.dumps(bad)), self.task, self.assets, self.raw)
                count += 1
        for name in self.assets:
            bad = copy.deepcopy(self.family)
            bad['context']['static_assets'][name] = {'source_document_lost': True}
            with self.subTest(asset_document=name), self.assertRaises(AssertionError):
                audit(json.loads(json.dumps(bad)), self.task, self.assets, self.raw)
            count += 1
        self.assertEqual(count, 73)

    def test_08_hostile_serialized_projection_mutations_rejected(self):
        first_node = lambda f: get_route(f, 'B01')['nodes'][0]['children'][0]
        mutations = {
            'invent_telemetry': lambda f: f.update(measurements=[{'pressure': 50}]),
            'activate_actor': lambda f: f.update(actor_projection_implemented=True),
            'claim_remote_commit': lambda f: f.update(source_commit='0' * 40),
            'stale_task_archive': lambda f: f.update(source_archive_sha256='0' * 64),
            'stale_asset_archive': lambda f: f.update(asset_archive_sha256='0' * 64),
            'default_activates_branch': lambda f: f.update(default_route='B01'),
            'wrong_scope': lambda f: f.update(family_scope='validated_task'),
            'count_branches_as_tasks': lambda f: f['summary_counts'].update(operation_templates=20),
            'erase_qualification_holds': lambda f: f['summary_counts'].update(unresolved_input_groups=0),
            'lose_raw_review': lambda f: f['source_files'].pop('review/independent_review.json'),
            'wrong_source_hash': lambda f: f['source_files']['operations.json'].update(sha256='0' * 64),
            'wrong_asset_hash': lambda f: f['source_files']['static_assets/scene_manifest.json'].update(sha256='0' * 64),
            'remote_source_link': lambda f: f['source_files']['operations.json'].update(url='https://invalid.example/operations.json'),
            'wrong_source_pointer': lambda f: f['operations'][0].update(source_pointer='/operations/1'),
            'rename_station': lambda f: f['operations'][0].update(stage='ST02'),
            'invent_hardware_action': lambda f: f['operations'][6].update(actions=['set_pressure(2.5)']),
            'invent_poststate': lambda f: f['operations'][6].update(post='Completed'),
            'invent_receipt': lambda f: f['operations'][6]['acceptance'].update(receipt='authenticated'),
            'drop_unknowns': lambda f: f['operations'][6].update(unknowns=[]),
            'invent_recovery': lambda f: f['operations'][6].update(recovery='reset and rerun'),
            'invent_loop': lambda f: f['operations'][6].update(loop={'count':20}),
            'bool_to_zero': lambda f: f['operations'][6]['provenance'].update(device_command_implemented=0),
            'integer_to_float': lambda f: f['context']['RELEASE_BOUNDARY'].update(paper_level_designs=1.0),
            'select_coral_rate': lambda f: f['context']['source_conflicts']['conflicts_and_extraction_hazards'][0].update(observations=['1.0 only']),
            'repair_boyle': lambda f: f['context']['source_conflicts']['conflicts_and_extraction_hazards'][1].update(classification='resolved'),
            'drop_viscosity': lambda f: f['routes'].pop(5),
            'drop_high_filling': lambda f: f['routes'].pop(6),
            'promote_borrowed': lambda f: f['context']['branches']['branches'][7].update(scientific_execution='COMPLETE'),
            'model_execution': lambda f: f['context']['shared_binding_contract'].update(model_implemented=True),
            'erase_failed_history': lambda f: f['context']['failure_and_closeout'].update(failure_cases=[]),
            'license_source_media': lambda f: f['context']['provenance'].update(source_license='Apache-2.0'),
            'qualify_geometry': lambda f: f['context']['static_assets']['scene_manifest.json'].update(physical_actuation_enabled=True),
            'drop_custody': lambda f: f['dependencies']['sample_custody'].update(identity_fields=[]),
            'global_r11_dependency': lambda f: f['operations'][10]['pre'].update(depends_on=['R10']),
            'global_r11_token': lambda f: f['operations'][11]['pre'].update(dependency_rule='one R11 token closes everything'),
            'fake_retry_count': lambda f: f['dependencies']['lifecycle_contract'].update(retry_rule='twenty experiments'),
            'invent_dependency_graph': lambda f: f['dependencies'].update(edges=[['R10','R11']]),
            'duplicate_route': lambda f: f['routes'].append(copy.deepcopy(f['routes'][0])),
            'remove_route': lambda f: f['routes'].pop(),
            'wrong_membership': lambda f: get_route(f,'B01')['nodes'][0]['children'].pop(),
            'forge_membership_pointer': lambda f: first_node(f)['meta'].update(source_pointer='/operations/1/id'),
            'invent_ordering': lambda f: get_route(f,'B01')['nodes'][0].update(ordered=True),
            'invent_chronology_node': lambda f: get_route(f,'B01')['nodes'][0].update(type='sequence'),
            'activate_hold': lambda f: get_route(f,'HOLD_QUALIFICATION')['nodes'].insert(0,copy.deepcopy(first_node(f))),
            'activate_outcome': lambda f: get_route(f,'OUTCOMES_REFERENCE').update(metadata_only=False),
            'change_reference_contract': lambda f: get_route(f,'CONTROLS_REFERENCE')['detail'].update(reported_repeat_counts=3),
            'drop_warning': lambda f: f.update(source_warnings='Ready to run'),
            'drop_asset_link': lambda f: f['asset_links'].pop(),
            'stale_preview_hash': lambda f: f['asset_links'][1].update(sha256='0'*64),
        }
        for label, mutate in mutations.items():
            with self.subTest(mutation=label):
                bad = copy.deepcopy(self.family); mutate(bad)
                with self.assertRaises(AssertionError):
                    audit(json.loads(json.dumps(bad,ensure_ascii=False,allow_nan=False)),self.task,self.assets,self.raw)
        self.assertGreaterEqual(len(mutations),45)

    def test_09_raw_core_and_pool_mutations_rejected(self):
        for kind, name in [('task', 'source_conflicts.json'), ('asset', 'geometry/frictional_lab.glb'),
                           ('asset', 'geometry/frictional_lab.blend'), ('asset', 'previews/preview_02_closed_service.png')]:
            bad = {k: dict(v) for k, v in self.raw.items()}
            bad[kind][name] += b' '
            with self.subTest(raw=kind + '/' + name), self.assertRaises(AssertionError):
                audit_raw(bad)
        for kind, filename in [('task', 'task_core_manifest.json'), ('asset', 'scene_core_manifest.json')]:
            documents = copy.deepcopy(self.task if kind == 'task' else self.assets)
            documents[filename]['files'][0]['sha256'] = '0' * 64
            with self.subTest(core=kind), self.assertRaises(AssertionError):
                audit_core_bindings(documents if kind == 'task' else self.task,
                                    documents if kind == 'asset' else self.assets, self.raw)
        for pooled in [
            {'shared': [], 'x': {'$shared': 0}}, {'shared': ['x'], 'x': {'$shared': -1}},
            {'shared': ['x'], 'x': {'$shared': True}}, {'shared': ['x'], 'x': {'$shared': 0.0}},
            {'shared': ['x'], 'x': {'$shared': '0'}}, {'shared': ['x'], 'x': {'$shared': 0, 'extra': 1}},
            {'shared': [{'$shared': 0}], 'x': {'$shared': 0}},
            {'shared': [{'$shared': 1}, {'$shared': 0}], 'x': {'$shared': 1}},
            {'shared': {}, 'x': 1},
        ]:
            with self.subTest(pool=pooled), self.assertRaises(AssertionError):
                decode_shared(pooled)
        decoded = decode_shared({'shared': [{'a': [1]}], 'x': {'$shared': 0}, 'y': {'$shared': 0}})
        decoded['x']['a'].append(2)
        self.assertEqual(decoded['y'], {'a': [1]}, 'Decoded references must not alias')
        bad = copy.deepcopy(self.pooled)
        bad['actor_projection_implemented'] = True
        with self.assertRaises(AssertionError):
            audit(decode_shared(json.loads(json.dumps(bad))), self.task, self.assets, self.raw)

    def test_10_generated_files_fit_publication_rpc_budget(self):
        for relative in ['data/frictional.json', 'data/frictional.js', 'docs/frictional.md', 'diagrams/frictional.svg']:
            data = (VIEW / relative).read_bytes()
            rpc_bytes = len(json.dumps({'content': data.decode('utf-8')}, ensure_ascii=True).encode('utf-8')) + 65536
            with self.subTest(file=relative):
                self.assertLess(len(data), 6000000, 'Retain compact source-lossless frictional package')
                self.assertLess(rpc_bytes, 15 * 1024 * 1024, 'Reserve metadata margin below Git JSON-RPC limit')


if __name__ == '__main__':
    unittest.main(verbosity=2)
