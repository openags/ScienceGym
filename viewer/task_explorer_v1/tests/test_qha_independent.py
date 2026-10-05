"""Independent QHA viewer audit using frozen release bytes as its only oracle.

The companion qha_frozen_oracle.json was extracted from the two supplied ZIPs,
not from viewer code. No adapter, generator, package validator, or projection
helper is imported. ZIPs are checked when available; portable checkouts retain
an exact per-file SHA-256/byte oracle. Hostile changes are in-memory only.
This audits fidelity and boundaries, not physics, experimental replication,
publication rereading, receipt authentication, or real-world qualification.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import unittest
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('SCIENCEGYM_ROOT', str(HERE.parents[2]))).resolve()
VIEW = ROOT / 'viewer/task_explorer_v1'
MANIFEST = json.loads((HERE / 'qha_frozen_oracle.json').read_text())
PACKAGES = MANIFEST['packages']
ALIASES = {'evaluator_reference.json': 'acceptance', 'lineage_contract.json': 'lineage'}
OP_IDS = [f'R{i:02}' for i in range(15)]
BRANCH_IDS = ['PREP', 'CHAR', 'DIRECT', 'TRANSFER_HB', 'TRANSFER_ARRAYS',
              'DIRECT_HB', 'OFF_PLATEAU', 'HIGH_BIAS', 'EXTERNAL', 'ANALYSIS', 'CLOSE']
REFERENCE_ROUTES = {
    'OPERATIONS_REFERENCE': ('operations.json', 'operation_inventory', False),
    'CONTROLS_REFERENCE': ('controls_and_repeats.json', 'controls_reference', True),
    'FAILURE_REFERENCE': ('failure_and_closeout.json', 'failure_reference', True),
    'BINDINGS_REFERENCE': ('shared_binding_contract.json', 'bindings_reference', True),
    'OUTCOMES_REFERENCE': ('source_outcomes_reference.json', 'source_outcomes_reference', True),
    'HOLD_QUALIFICATION': ('release_boundary.json', 'qualification_hold', True),
}
DEPENDENCY_DOCS = ['workflow', 'material_and_sample_dependencies', 'lineage_contract',
                   'measurement_contract', 'failure_and_closeout', 'station_contracts',
                   'identity_contract', 'device_lease_contract']
COUNTS = {
    'authored_coverage_branches': 11, 'authored_reference_views': 5,
    'metadata_only_hold_views': 1, 'source_json_documents': 40,
    'asset_json_documents': 28, 'operation_templates': 15,
    'source_evidence_entries': 29, 'source_ambiguities': 18,
    'reported_outcomes': 14, 'unresolved_input_groups': 20, 'controls': 14,
    'scene_groups': 11, 'symbolic_anchors': 32, 'task_core_files': 41, 'asset_core_files': 30,
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


def decode_shared(pooled):
    """Independent strict decoder; no adapter helpers or eval, and no object aliasing."""
    pool = pooled.get('shared', [])
    def expand(value, stack=()):
        if isinstance(value, dict):
            if '$shared' in value:
                assert set(value) == {'$shared'}, 'Malformed pooled reference'
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
    assert pointer.startswith('/'), 'JSON pointer must be absolute'
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
    for kind, package in PACKAGES.items():
        assert set(raw[kind]) == set(package['files']), kind + ' exact package membership'
        for name, expected in package['files'].items():
            value = raw[kind][name]
            assert len(value) == expected['bytes'], kind + '/' + name + ' byte count'
            assert digest(value) == expected['sha256'], kind + '/' + name + ' SHA256'


def audit_core_bindings(task, assets, raw):
    """Check reciprocal current semantic cores, including byte-level snapshots."""
    tc = task['task_semantic_core_manifest.json']
    ac = assets['scene_core_manifest.json']
    assert len(tc['files']) == 41 and len(ac['files']) == 30
    for kind, core, key in [('task', tc, 'semantic_core_sha256'), ('asset', ac, 'core_sha256')]:
        assert core[key] == canonical_digest(core['files']), kind + ' canonical core hash'
        names = [item['path'] for item in core['files']]
        assert len(names) == len(set(names)) and names == sorted(names), kind + ' unique core members'
        for item in core['files']:
            b = raw[kind][item['path']]
            assert item['bytes'] == len(b) and item['sha256'] == digest(b), item['path']
    assert raw['task']['task_semantic_core_manifest.json'] == raw['asset']['paired_task_core_manifest.json']
    assert raw['task']['shared_binding_contract.json'] == raw['asset']['shared_binding_contract.json']
    for paired in [task['paired_asset_reference.json'], assets['paired_task_reference.json']]:
        assert paired['task_core_sha256'] == tc['semantic_core_sha256']
        assert paired['asset_core_sha256'] == ac['core_sha256']
        assert paired['task_core_manifest_sha256'] == digest(raw['task']['task_semantic_core_manifest.json'])
        assert paired['shared_contract_sha256'] == digest(raw['task']['shared_binding_contract.json'])
    assert task['paired_asset_reference.json']['asset_archive'] == {
        'filename': PACKAGES['asset']['archive'], 'bytes': PACKAGES['asset']['archive_bytes'],
        'sha256': PACKAGES['asset']['archive_sha256']}
    for name in assets:
        if name.endswith('_snapshot.json'):
            original = name.replace('_snapshot.json', '.json')
            assert raw['asset'][name] == raw['task'][original], name + ' unchanged snapshot'
    binding = task['shared_binding_contract.json']
    groups = binding['assets']
    assert [g['asset_id'] for g in groups] == [f'AS{i:02}' for i in range(1, 12)]
    anchors = [anchor['anchor_id'] for group in groups for anchor in group['anchors']]
    assert len(anchors) == len(set(anchors)) == 32
    inventory = assets['asset_inventory.json']['assets']
    assert [g['asset_id'] for g in inventory] == [g['asset_id'] for g in groups]
    for group, inv in zip(groups, inventory):
        assert inv['root'] == group['asset_root_object']
        assert inv['routes'] == group['route_ids'] and inv['stations'] == group['station_ids']
        assert inv['qualified_inputs_needed'] == group['qualified_inputs_needed']
        assert [{k: a[k] for k in ('anchor_id', 'object_name', 'mode', 'physical_actuation_enabled')}
                for a in inv['anchors']] == group['anchors']
        assert inv['source_cad'] is False and inv['physical_actuation_enabled'] is False
        assert inv['qualification_state'] == 'HOLD_UNQUALIFIED'
    objects = assets['scene_manifest.json']['objects']
    assert len({o['name'] for o in objects}) == len(objects)
    assert {o['anchor_id'] for o in objects if o['anchor_id'] is not None} == set(anchors)
    assert {o['name'] for o in objects if o['name'] in {g['asset_id'] for g in groups}} == {g['asset_id'] for g in groups}
    op_bindings = binding['route_bindings']
    assert [b['route_id'] for b in op_bindings] == OP_IDS
    for op, linked in zip(task['operations.json']['operations'], op_bindings):
        assert linked['asset_ids'] == op['asset_ids']
        assert linked['target_anchor_ids'] == op['anchor_ids']
        assert linked['station_ids'] == op['stations']
        assert linked['mode'] == 'evidence_only' and linked['physical_actuation_enabled'] is False
        assert set(op['anchor_ids']) <= set(anchors)
    return True


def audit_sanitized_lineage(task, assets, raw):
    """Corroborate public cleanup lineage; never disclose recovered native bytes."""
    original_task_core = 'cb8d06d71946eeacfdb9e5284c52eeff17d937fcdc7f37ed7a1f8311ba14a9f0'
    original_manifest = '1732ecbab50f883bd6ebc82cceb03aaf6e2d459e2ee2fa6b830e3aea20f19af9'
    original_binding = 'd86dc8699ca1bf8fe2c552d318e5e5eac8a6b613a27ed87d4cab56b2f8d7b86d'
    assert task['task_semantic_core_manifest.json']['semantic_core_sha256'] == original_task_core
    assert digest(raw['task']['task_semantic_core_manifest.json']) == original_manifest
    assert digest(raw['task']['shared_binding_contract.json']) == original_binding
    preserved = MANIFEST['original_revision_preserved_files']
    assert len(preserved['task']) == 47 and len(preserved['asset']) == 14
    for kind, files in preserved.items():
        for name, pin in files.items():
            assert len(raw[kind][name]) == pin['bytes'] and digest(raw[kind][name]) == pin['sha256'], name
    lineage = task['review/SANITIZED_REPIN_LINEAGE.json']
    assert lineage['protected_task_core_sha256'] == original_task_core
    assert lineage['protected_task_core_manifest_sha256'] == original_manifest
    assert lineage['protected_shared_binding_sha256'] == original_binding
    assert lineage['runtime_semantics_changed'] is False and lineage['source_facts_changed'] is False
    assert lineage['qualification'] == 'HOLD_QUALIFICATION'
    check = task['review/SANITIZED_REPIN_REVIEW.json']
    assert check['protected_files_byte_identical'] == 41
    assert check['runtime_semantics_unchanged'] is True and check['source_facts_unchanged'] is True
    acceptance = raw['asset']['review/independent_clean_revision.json']
    for record in [task['paired_asset_reference.json'], check]:
        pin = record['native_sanitization_acceptance'] if 'native_sanitization_acceptance' in record else record['asset_sanitization_acceptance']
        assert pin == {'filename': 'independent_clean_revision.json', 'bytes': len(acceptance), 'sha256': digest(acceptance)}
    revision = assets['sanitized_revision.json']
    assert revision['logical_asset_package'] == 'qha_scene_assets_v1'
    assert revision['revision'] == 'qha_scene_assets_v2_clean'
    assert revision['old_delivered_archives_overwritten'] is False
    assert revision['physical_actuation_enabled'] is False
    native_hash = digest(raw['asset']['geometry/qha_lab.blend'])
    assert revision['sanitized_native_sha256'] == native_hash
    assert revision['baseline_native_sha256'] != native_hash
    for pin in revision['unchanged_files']:
        assert pin['unchanged_from_baseline'] is True
        assert pin['bytes'] == len(raw['asset'][pin['path']])
        assert pin['sha256'] == digest(raw['asset'][pin['path']])
    scan = assets['review/deep_buffer_scan.json']
    assert scan['compressed_sha256'] == native_hash
    assert scan['fixed_char_arrays_checked'] == 6055
    assert scan['fields_with_nonzero_tail'] == 0
    assert scan['path_issues'] == scan['unsupported_layouts'] == scan['unclassified_nonzero_tails'] == []
    assert scan['strict_path_privacy_pass'] is True and scan['contents_redacted'] is True
    cleanup = assets['review/deep_buffer_cleanup.json']
    assert cleanup['destination_sha256'] == native_hash
    assert cleanup['changed_buffer_count'] == 36
    assert cleanup['bytes_outside_declared_buffers_identical'] is True
    assert cleanup['sdna_sha256_unchanged'] is True
    assert cleanup['raw_buffer_contents_disclosed'] is False
    assert cleanup['post_scan_summary'] == {k: v for k, v in scan.items() if k != 'fields'}
    independent = assets['review/independent_clean_revision.json']
    assert independent['native']['sha256'] == native_hash
    assert independent['post_nul_nonzero_tail_findings'] == 0
    assert independent['unsupported_layouts'] == 0
    assert independent['all_bytes_outside_changed_buffers_identical'] is True
    assert independent['active_scene_string_values_unchanged'] is True
    assert independent['GLB_and_three_PNGs_byte_identical'] is True
    assert independent['scientific_snapshots_binding_guards_scene_manifest_and_inventory_byte_identical'] is True
    assert independent['export_audit_privacy']['actual_private_path_or_secret_matches'] == 0
    assert independent['export_audit_privacy']['raw_private_fragments_in_this_report'] is False
    equivalence = assets['review/native_equivalence.json']
    assert equivalence['semantic_sha256_before'] == equivalence['semantic_sha256_after']
    assert equivalence['before_and_after_snapshot_equal'] is True
    metadata = assets['public_metadata_audit.json']
    assert metadata['deep_fixed_char_arrays_checked'] == 6055
    assert metadata['deep_nonzero_tails'] == 0 and metadata['deep_path_issues'] == []
    assert metadata['private_metadata_findings'] == []
    assert metadata['native_decompressed_private_paths_absent'] is True
    assert task['release_boundary.json']['paper_design_count'] == 1, 'Cleanup earns no additional scientific-design credit'
    return True


def audit(family, task, assets, raw):
    """Source-document semantic oracle, reused against hostile in-memory copies."""
    assert set(family) == FAMILY_KEYS, 'No extra generated telemetry or executable surface'
    expected = {ALIASES.get(name, name[:-5]): document for name, document in task.items()}
    assert len(expected) == 40 and len(assets) == 28
    expected['static_assets'] = assets
    assert family['context'] == expected, 'All 40 task and 28 asset JSON documents remain lossless'
    expected_sources = {}
    for kind, documents in [('task', task), ('asset', assets)]:
        folder = PACKAGES[kind]['folder']
        for name in documents:
            display_name = name if kind == 'task' else 'static_assets/' + name
            expected_sources[display_name] = {'url': '../../' + folder + '/' + name,
                'repository_path': folder + '/' + name, 'sha256': digest(raw[kind][name])}
    assert family['source_files'] == expected_sources, 'Exact source provenance and links'
    assert family['id'] == 'qha' and family['family_scope'] == 'paper_level_design'
    assert family['doi'] == task['source_facts.json']['paper_doi'] == '10.1038/s41467-022-34680-0'
    assert family['title'] == task['source_packet_reference.json']['scientific_record']['title']
    assert family['visibility'] == 'author_evaluator_reference_only'
    assert family['actor_projection_implemented'] is False
    assert family['source_commit'] is None
    assert family['source_archive_sha256'] == PACKAGES['task']['archive_sha256']
    assert family['asset_archive_sha256'] == PACKAGES['asset']['archive_sha256']
    assert family['source_folder'] == '../../tasks/qha_operations_v2/'
    assert family['source_link_mode'] == 'repository_relative_frozen_local_snapshot'
    assert 'remote publication is not asserted' in family['source_publication']
    assert family['summary_counts'] == COUNTS
    assert family['default_route'] == 'HOLD_QUALIFICATION'
    assert 'metadata-only' in family['default_route_basis']
    rawops = task['operations.json']['operations']
    assert [op['id'] for op in rawops] == OP_IDS
    assert [op['id'] for op in family['operations']] == OP_IDS
    for index, (source, op) in enumerate(zip(rawops, family['operations'])):
        assert set(op) == OP_KEYS, source['id'] + ' no added result or command fields'
        assert op['detail'] == source, source['id'] + ' lossless operation'
        assert op['source_file'] == 'operations.json' and op['source_pointer'] == f'/operations/{index}'
        assert resolve_pointer(task[op['source_file']], op['source_pointer']) == source
        assert op['title'] == source['name']
        assert op['stage'] == ', '.join(source['stations'])
        assert op['actions'] == [source['action']]
        assert op['objects'] == {key: source[key] for key in ('asset_ids', 'anchor_ids')}
        assert op['pre'] == {key: source[key] for key in ('depends_on', 'guards')}
        assert op['post'] == ('No observed post-state field supplied; inspect the exact source contract. '
                              'No value or command is inferred.'), 'Obligations must not become observations'
        assert op['acceptance'] == {key: source[key] for key in ('required_evidence', 'completion')}
        assert op['recovery'] == source['failure_closeout']
        assert op['unknowns'] == source['unresolved_inputs']
        assert op['provenance'] == {key: source[key] for key in (
            'origin', 'kind', 'action_interface', 'physical_execution_enabled', 'receipt_authentication')}
        assert op['sources'] == [], 'Do not invent per-operation source-fact associations'
        assert op['loop'] is None, 'Do not invent acquisition repeats'
        assert 'no live device control' in op['display_action_ownership']
        assert 'requirements, never observed' in op['display_mapping_basis']
        assert source['physical_execution_enabled'] is False
        assert source['action_interface'] == {'allowed_keys': ['operation_id', 'evidence_ids'],
                                              'numeric_or_hardware_arguments_allowed': False}
    branches = task['branches.json']['branches']
    assert [branch['id'] for branch in branches] == BRANCH_IDS
    routes = family['routes']
    assert [route['id'] for route in routes] == BRANCH_IDS + list(REFERENCE_ROUTES)
    assert len(routes) == 17
    for index, branch in enumerate(branches):
        route = routes[index]
        assert route['detail'] == branch
        assert route['route_kind'] == 'authored_coverage_branch' and route['metadata_only'] is False
        assert route['source_file'] == 'branches.json' and route['source_pointer'] == f'/branches/{index}'
        nodes = [node for node in walk(route['nodes']) if node['type'] == 'op']
        assert [node['id'] for node in nodes] == branch['operations'], branch['id'] + ' exact membership'
        for i, node in enumerate(nodes):
            assert node['meta']['source_file'] == 'branches.json'
            assert node['meta']['source_pointer'] == f'/branches/{index}/operations/{i}'
        assert branch['repeat_count'] is None and branch['planned_conditions'] is None
        assert branch['initial_state'] == 'held_qualification'
    for route_id, (filename, kind, metadata_only) in REFERENCE_ROUTES.items():
        route = get_route(family, route_id)
        assert route['source_file'] == filename and route['source_pointer'] == ''
        assert route['route_kind'] == kind and route['metadata_only'] is metadata_only
        assert route['detail'] == task[filename]
        nodes = [node for node in walk(route['nodes']) if node['type'] == 'op']
        assert [node['id'] for node in nodes] == (OP_IDS if route_id == 'OPERATIONS_REFERENCE' else [])
        if route_id == 'OPERATIONS_REFERENCE':
            for i, node in enumerate(nodes):
                assert node['meta']['source_file'] == 'operations.json'
                assert node['meta']['source_pointer'] == f'/operations/{i}/id'
    for route in routes:
        assert set(route) == ROUTE_KEYS, route['id'] + ' no added execution or outcome fields'
        assert resolve_pointer(task[route['source_file']], route['source_pointer']) == route['detail']
        assert 'no added scientific branch' in route['navigation_basis']
        assert 'zero validated runnable whole-paper tasks' in route['basis']
        assert 'HOLD_QUALIFICATION remains active' in route['basis']
        assert len(route['nodes']) == (2 if not route['metadata_only'] else 1)
        contracts = 0
        for node in walk(route['nodes']):
            assert node['type'] in {'op', 'obligations', 'condition'}, 'No invented branch/cycle nodes'
            meta = node.get('meta', {})
            if node['type'] == 'op':
                assert set(node) == {'type', 'id', 'meta'}
                assert set(meta) == {'source_file', 'source_pointer', 'source_node', 'meaning'}
                assert resolve_pointer(task[meta['source_file']], meta['source_pointer']) == node['id'] == meta['source_node']
                assert 'not execution or inferred chronology' in meta['meaning']
            else:
                assert set(node) == {'type', 'label', 'ordered', 'children', 'meta'}
                assert node['ordered'] is False, 'Membership must not imply chronology'
                if node['type'] == 'condition':
                    contracts += 1
                    assert node['children'] == []
                    assert set(meta) == {'source_file', 'source_pointer', 'source_contract'}
                    assert meta['source_file'] == route['source_file'] and meta['source_pointer'] == route['source_pointer']
                    assert meta['source_contract'] == route['detail']
                else:
                    assert set(meta) == {'order'} and 'do not create chronology' in meta['order']
        assert contracts == 1
    assert 'never new measurement telemetry' in get_route(family, 'OUTCOMES_REFERENCE')['label']
    assert 'NO INSTRUMENT OPERATION' in get_route(family, 'HOLD_QUALIFICATION')['label']
    assert family['evidence'] == {fact['id']: fact for fact in task['source_facts.json']['facts']}
    assert set(family['dependencies']) == set(DEPENDENCY_DOCS) | {'display_rule'}
    for name in DEPENDENCY_DOCS:
        assert family['dependencies'][name] == task[name + '.json'], name + ' exact dependency/lifecycle contract'
    assert 'only exact dependency and lifecycle contracts' in family['dependencies']['display_rule']
    warning = family['source_warnings']
    for phrase in ['118-element parallel subarray', 'R_K/236, approximately 109 ohm',
                   'whole 236-element device', 'R_K/118, approximately 219 ohm',
                   'never generated measurement telemetry, actor reward or success thresholds',
                   'null repeat counts and null planned conditions', 'five-edge comparison graph',
                   'independently of analysis success', 'closed qualified services',
                   'never operating defaults', 'does not reread publications']:
        assert phrase in warning, 'Missing boundary: ' + phrase
    for phrase in ['zero validated runnable whole-paper tasks', 'Read-only author/evaluator inspection',
                   'never observed states', 'HOLD_QUALIFICATION remains active']:
        assert phrase in family['status'], 'Missing status boundary: ' + phrase
    assert warning in family['status']
    for phrase in ['illustrative and unqualified', 'No source-exact CAD', 'scientific measurement']:
        assert phrase in family['asset_boundary']
    expected_links = ['README.md', 'previews/preview_01_overview.png',
                      'previews/preview_02_specimen.png', 'previews/preview_03_services.png']
    assert len(family['asset_links']) == 4
    for link, name in zip(family['asset_links'], expected_links):
        assert set(link) == {'label', 'path', 'url', 'sha256'}
        assert link['path'] == PACKAGES['asset']['folder'] + '/' + name
        assert link['url'] == '../../' + link['path']
        assert link['sha256'] == digest(raw['asset'][name])
    return True


class FrozenQHAOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = {kind: {name: (ROOT / package['folder'] / name).read_bytes()
                          for name in package['files']} for kind, package in PACKAGES.items()}
        audit_raw(cls.raw)  # Never bless altered source bytes by deriving expectations from them.
        cls.task = {name: json.loads(b) for name, b in cls.raw['task'].items() if name.endswith('.json')}
        cls.assets = {name: json.loads(b) for name, b in cls.raw['asset'].items() if name.endswith('.json')}
        cls.pooled = json.loads((VIEW / 'data/qha.json').read_text())
        cls.family = decode_shared(cls.pooled)

    def test_01_exact_frozen_package_membership_and_bytes(self):
        for kind, package in PACKAGES.items():
            folder = ROOT / package['folder']
            names = {p.relative_to(folder).as_posix() for p in folder.rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts}
            self.assertEqual(names, set(package['files']))
        audit_raw(self.raw)

    def test_02_supplied_zip_oracles_when_available(self):
        # CI/export remains portable; exact per-file byte pins always run above.
        # SCIENCEGYM_RELEASE_ARCHIVES makes missing release ZIPs a hard failure for a release audit.
        explicit = os.environ.get('SCIENCEGYM_RELEASE_ARCHIVES')
        search = [Path(explicit)] if explicit else []
        for kind, package in PACKAGES.items():
            found = next((folder / package['archive'] for folder in search
                          if (folder / package['archive']).is_file()), None)
            if explicit:
                self.assertIsNotNone(found, 'Requested immutable ZIP oracle unavailable')
            if found is None:
                continue
            data = found.read_bytes()
            self.assertEqual(len(data), package['archive_bytes'])
            self.assertEqual(digest(data), package['archive_sha256'])
            with zipfile.ZipFile(found) as archive:
                names = [name for name in archive.namelist() if not name.endswith('/')]
                self.assertEqual(len(names), len(set(names)))
                expected = {package['archive_prefix'] + name for name in package['files']}
                self.assertEqual(set(names), expected)
                for name, raw in self.raw[kind].items():
                    self.assertEqual(archive.read(package['archive_prefix'] + name), raw)

    def test_03_all_source_json_and_projection_fidelity(self):
        self.assertTrue(audit(self.family, self.task, self.assets, self.raw))

    def test_04_current_reciprocal_cores_and_binding_bijections(self):
        self.assertTrue(audit_core_bindings(self.task, self.assets, self.raw))

    def test_04b_sanitized_lineage_and_preserved_scientific_semantics(self):
        self.assertTrue(audit_sanitized_lineage(self.task, self.assets, self.raw))

    def test_05_source_topology_and_identity_never_conflated(self):
        identity = self.task['identity_contract.json']
        regions = identity['electrical_regions']
        self.assertEqual([r['region_id'] for r in regions], ['Array1', 'Array2', 'HB'])
        for region in regions[:2]:
            self.assertEqual(region['parallel_elements'], 118)
            self.assertEqual(region['nominal_resistance_source'], 'R_K/236, about 109 ohm')
        self.assertEqual(identity['whole_series_array'], {'composed_regions': ['Array1', 'Array2'],
            'total_elements': 236, 'nominal_resistance_source': 'R_K/118, about 219 ohm',
            'independent_sample': False})
        invariants = self.task['shared_binding_contract.json']['identity_invariants']
        for key, expected in {'physical_chip_count': 1, 'subarray_count': 2,
            'elements_per_subarray': 118, 'total_elements': 236, 'subarray_nominal_ohms_approx': 109,
            'whole_device_nominal_ohms_approx': 219, 'subarray_nominal_formula': 'R_K/236',
            'whole_device_nominal_formula': 'R_K/118', 'oil_reference_ohms': 100,
            'air_reference_ohms': 12900, 'references_interchangeable': False,
            'source_results_are_measurement_evidence': False,
            'source_results_are_success_thresholds': False}.items():
            self.assertEqual(invariants[key], expected)

    def test_06_exact_graph_and_independent_closeout(self):
        ops = self.task['operations.json']['operations']
        edges = self.task['workflow.json']['dependency_edges']
        self.assertEqual(edges, [{'from': dependency, 'to': op['id']}
                                 for op in ops for dependency in op['depends_on']])
        self.assertEqual(len(edges), 20)
        self.assertEqual(ops[14]['depends_on'], ['R03'])
        self.assertNotIn({'from': 'R13', 'to': 'R14'}, edges)
        self.assertTrue(self.task['workflow.json']['analysis_may_not_delay_physical_safety'])
        self.assertEqual(self.task['workflow.json']['actual_started_jobs'], [])
        self.assertEqual(self.task['workflow.json']['actual_closed_jobs'], [])
        self.assertEqual(self.task['device_lease_contract.json']['initial_leases'], [])
        graph = self.task['cross_device_measurements.json']['source_graph']
        self.assertEqual(len(graph['nodes']), 4)
        self.assertEqual(len(graph['direct_edges']), 5)
        self.assertEqual(graph['connected_graph_independent_cycle_count'], 2)
        self.assertEqual(graph['simple_closed_loop_count'], 3)
        self.assertEqual(len(graph['direct_edges']) - len(graph['nodes']) + 1, 2)
        self.assertFalse(any(set(edge['listed_pair']) == {'on-chip Hall bar', 'Array2'}
                             for edge in graph['direct_edges']))
        branches = {b['id']: b for b in self.task['branches.json']['branches']}
        self.assertFalse(branches['OFF_PLATEAU']['optional_physical_execution'])
        self.assertTrue(branches['HIGH_BIAS']['optional_physical_execution'])
        self.assertTrue(branches['EXTERNAL']['optional_physical_execution'])

    def test_07_observations_rewards_repeats_and_analysis_stay_unperformed(self):
        outcome = self.task['source_outcomes_reference.json']
        self.assertEqual(outcome['classification'], 'author_reported_outcomes_not_new_measurements_or_success_thresholds')
        self.assertEqual([o['id'] for o in outcome['outcomes']], [f'O{i:02}' for i in range(1, 15)])
        self.assertEqual([f['id'] for f in self.task['source_facts.json']['facts']], [f'F{i:02}' for i in range(1, 30)])
        self.assertEqual([c['id'] for c in self.task['source_conflicts.json']['items']], [f'C{i:02}' for i in range(1, 19)])
        self.assertEqual(len(self.task['controls_and_repeats.json']['controls']), 14)
        self.assertEqual(len(self.task['unknown_inputs.json']['items']), 20)
        self.assertTrue(all(v is None for v in self.task['repeat_contract.json']['unit_counts'].values()))
        measurement = self.task['measurement_contract.json']
        self.assertEqual(measurement['new_measurements'], [])
        self.assertFalse(measurement['numeric_measurement_generator'])
        self.assertIsNone(measurement['analysis_implementation'])
        self.assertEqual(self.task['analysis_holds.json']['resolutions'], [])
        self.assertEqual(self.task['analysis_holds.json']['approved_algorithms'], [])
        self.assertEqual(len(self.task['analysis_holds.json']['holds']), 6)
        release = self.task['release_boundary.json']
        self.assertEqual(release['paper_design_count'], 1)
        self.assertEqual(release['validated_runnable_whole_paper_tasks'], 0)
        for key in ['hardware_actions', 'physical_simulations', 'scientific_reproductions']:
            self.assertEqual(release[key], 0)
        for key in ['physical_execution_enabled', 'physical_observations_generated',
                    'numerical_analysis_implemented', 'source_outcomes_used_for_reward',
                    'production_receipt_authentication_implemented', 'publisher_assets_exported', 'exact_source_CAD']:
            self.assertIs(release[key], False)
        self.assertIsNone(release['all_thresholds_and_repeat_defaults'])
        safety = self.task['safety_boundaries.json']
        self.assertEqual(len(safety['closed_services']), 5)
        self.assertFalse(safety['physical_execution_enabled'])
        self.assertEqual(safety['default'], 'HOLD_QUALIFICATION')

    def test_08_source_review_attribution_and_raw_data_limits(self):
        access = self.task['source_access_audit.json']
        self.assertEqual([(s['id'], s['pages']) for s in access['sources']], [('MAIN', 9), ('SI', 4)])
        for source in access['sources']:
            self.assertEqual(source['written_pages_read'], list(range(1, source['pages'] + 1)))
            self.assertEqual(source['rendered_pages_visually_inspected'], list(range(1, source['pages'] + 1)))
            self.assertFalse(source['exported'])
        source = self.task['source_packet_reference.json']
        self.assertFalse(source['raw_data_acquired'])
        self.assertFalse(source['publisher_originals_exported'])
        self.assertEqual(len(source['retained_files']), 17)
        for item in source['retained_files']:
            data = self.raw['task'][item['path']]
            self.assertEqual(item['bytes'], len(data))
            self.assertEqual(item['sha256'], digest(data))
        self.assertEqual(self.task['source_update_status.json']['crossmark_status'], 'UNKNOWN')

    def test_09_data_js_json_and_registration(self):
        js = (VIEW / 'data/qha.js').read_text()
        prefix = 'window.SCIENCEGYM_DATA=window.SCIENCEGYM_DATA||{};window.SCIENCEGYM_DATA["qha"]='
        self.assertTrue(js.startswith(prefix))
        self.assertEqual(json.loads(js[len(prefix):].strip().removesuffix(';')), self.pooled)
        self.assertIn('data/qha.js', (VIEW / 'index.html').read_text())

    def test_10_every_source_document_mutation_is_rejected(self):
        count = 0
        for context_key in self.family['context']:
            if context_key == 'static_assets':
                continue
            value = copy.deepcopy(self.family)
            value['context'].pop(context_key)
            with self.subTest(task_document=context_key), self.assertRaises(AssertionError):
                audit(value, self.task, self.assets, self.raw)
            count += 1
        for filename in self.assets:
            value = copy.deepcopy(self.family)
            value['context']['static_assets'][filename] = {'lost_original_document': True}
            with self.subTest(asset_document=filename), self.assertRaises(AssertionError):
                audit(value, self.task, self.assets, self.raw)
            count += 1
        self.assertEqual(count, 68)

    def test_11_hostile_projection_mutations_are_rejected(self):
        def route(f, id):
            return get_route(f, id)
        mutations = {
            'invent_generated_telemetry': lambda f: f.update(measurements=[{'value': 0.033}]),
            'promote_actor_projection': lambda f: f.update(actor_projection_implemented=True),
            'publish_unverified_commit': lambda f: f.update(source_commit='0' * 40),
            'stale_task_archive': lambda f: f.update(source_archive_sha256='0' * 64),
            'stale_asset_archive': lambda f: f.update(asset_archive_sha256='0' * 64),
            'default_runs_measurement': lambda f: f.update(default_route='DIRECT'),
            'count_reference_as_branch': lambda f: f['summary_counts'].update(authored_coverage_branches=16),
            'drop_review_provenance': lambda f: f['source_files'].pop('review/INDEPENDENT_REVIEW.json'),
            'stale_static_hash': lambda f: f['source_files']['static_assets/scene_core_manifest.json'].update(sha256='0' * 64),
            'wrong_local_source_link': lambda f: f['source_files']['operations.json'].update(url='../../tasks/qha_operations_v1/operations.json'),
            'wrong_operation_pointer': lambda f: f['operations'][4].update(source_pointer='/operations/5'),
            'unapproved_numeric_argument': lambda f: f['operations'][4]['provenance']['action_interface'].update(numeric_or_hardware_arguments_allowed=True),
            'enable_live_service': lambda f: f['operations'][4]['provenance'].update(physical_execution_enabled=True),
            'source_outcome_as_post_state': lambda f: f['operations'][5].update(post={'value': 0.033, 'uncertainty': 0.082}),
            'source_outcome_as_acceptance': lambda f: f['operations'][5]['acceptance'].update(reward_target=0.033),
            'receipt_requirement_becomes_receipt': lambda f: f['operations'][3]['acceptance'].update(received=True),
            'drop_required_evidence': lambda f: f['operations'][7]['acceptance']['required_evidence'].clear(),
            'invent_three_repeats': lambda f: f['operations'][5].update(loop={'count': 3}),
            'invent_fact_mapping': lambda f: f['operations'][5].update(sources=['F14']),
            'erase_failure_closeout': lambda f: f['operations'][14].update(recovery='Automatically release'),
            'closeout_waits_for_analysis': lambda f: f['operations'][14]['pre'].update(depends_on=['R13']),
            'invent_universal_dependencies': lambda f: f['dependencies'].update(edges=[['R00', 'R14']]),
            'dependency_drop': lambda f: f['dependencies']['workflow']['dependency_edges'].pop(),
            'lease_release_on_timeout': lambda f: f['dependencies']['device_lease_contract'].update(on_communications_loss='Release all leases'),
            'duplicate_coverage_route': lambda f: f['routes'].append(copy.deepcopy(f['routes'][0])),
            'erase_operation_membership': lambda f: route(f, 'PREP')['nodes'][0]['children'].pop(),
            'invent_route_chronology': lambda f: route(f, 'PREP')['nodes'][0].update(ordered=True),
            'wrong_membership_pointer': lambda f: route(f, 'PREP')['nodes'][0]['children'][0]['meta'].update(source_pointer='/branches/1/operations/0'),
            'coverage_as_observation': lambda f: route(f, 'DIRECT').update(route_kind='completed_observation'),
            'source_outcome_as_acquired_branch': lambda f: route(f, 'OUTCOMES_REFERENCE').update(metadata_only=False),
            'hide_outcome_boundary': lambda f: route(f, 'OUTCOMES_REFERENCE').update(label='Measured results'),
            'activate_qualification_hold': lambda f: route(f, 'HOLD_QUALIFICATION').update(metadata_only=False),
            'hold_runs_operation': lambda f: route(f, 'HOLD_QUALIFICATION')['nodes'].append({'type': 'op', 'id': 'R05'}),
            'silently_resolve_conflicts': lambda f: f['context']['source_conflicts'].update(items=[]),
            'pretend_acquired_measurements': lambda f: f['context']['measurement_contract'].update(new_measurements=[{'value': 0.033}]),
            'misidentify_whole_device': lambda f: f['context']['identity_contract']['whole_series_array'].update(nominal_resistance_source='109 ohm'),
            'independent_chip_count_from_readings': lambda f: f['context']['repeat_contract']['unit_counts'].update(physical_chip=53),
            'promote_statistical_cycles': lambda f: f['context']['cross_device_measurements']['source_graph'].update(connected_graph_independent_cycle_count=3),
            'discard_closed_services': lambda f: f['context']['safety_boundaries'].update(closed_services=[]),
            'approve_equations': lambda f: f['context']['analysis_holds'].update(approved_algorithms=['Allan']),
            'mark_source_outcomes_as_success': lambda f: f['context']['release_boundary'].update(source_outcomes_used_for_reward=True),
            'stale_task_core_projection': lambda f: f['context']['task_semantic_core_manifest'].update(semantic_core_sha256='0' * 64),
            'stale_asset_core_projection': lambda f: f['context']['static_assets']['scene_core_manifest.json'].update(core_sha256='0' * 64),
            'drop_source_fact': lambda f: f['evidence'].pop('F29'),
            'change_source_fact': lambda f: f['evidence']['F01'].update(claim='Whole device has 109 ohm resistance'),
            'erase_boundary_warning': lambda f: f.update(source_warnings='Runnable live instrument task'),
            'source_asset_substitution': lambda f: f['asset_links'][0].update(sha256='0' * 64),
        }
        for name, mutate in mutations.items():
            value = copy.deepcopy(self.family)
            mutate(value)
            with self.subTest(mutation=name), self.assertRaises((AssertionError, KeyError, TypeError)):
                audit(value, self.task, self.assets, self.raw)
        self.assertEqual(len(mutations), 47)

    def test_12_hostile_raw_core_and_pool_mutations_are_rejected(self):
        for kind, name in [('task', 'source_facts.json'), ('asset', 'geometry/qha_lab.glb')]:
            hostile = {k: dict(v) for k, v in self.raw.items()}
            hostile[kind][name] = hostile[kind][name] + b' '
            with self.subTest(raw=kind + '/' + name), self.assertRaises(AssertionError):
                audit_raw(hostile)
        for name in ['task_core_sha256', 'asset_core_sha256', 'task_core_manifest_sha256', 'shared_contract_sha256']:
            hostile = copy.deepcopy(self.assets)
            hostile['paired_task_reference.json'][name] = '0' * 64
            with self.subTest(pin=name), self.assertRaises(AssertionError):
                audit_core_bindings(self.task, hostile, self.raw)
        for pooled in [
            {'x': {'$shared': 1}, 'shared': [None]},
            {'x': {'$shared': -1}, 'shared': [None]},
            {'x': {'$shared': True}, 'shared': [None, None]},
            {'x': {'$shared': 0, 'value': 10}, 'shared': [None]},
            {'x': {'$shared': 0}, 'shared': [{'$shared': 0}]},
        ]:
            with self.subTest(pool=pooled), self.assertRaises(AssertionError):
                decode_shared(pooled)


    def test_13_hostile_sanitized_lineage_mutations_are_rejected(self):
        mutations = {
            'changed_runtime_semantics': lambda t, a: t['review/SANITIZED_REPIN_LINEAGE.json'].update(runtime_semantics_changed=True),
            'changed_source_facts': lambda t, a: t['review/SANITIZED_REPIN_LINEAGE.json'].update(source_facts_changed=True),
            'stale_native_acceptance': lambda t, a: t['paired_asset_reference.json']['native_sanitization_acceptance'].update(sha256='0' * 64),
            'stale_native_revision': lambda t, a: a['sanitized_revision.json'].update(sanitized_native_sha256='0' * 64),
            'nonzero_native_tail': lambda t, a: a['review/deep_buffer_scan.json'].update(fields_with_nonzero_tail=1),
            'unsupported_native_layout': lambda t, a: a['review/deep_buffer_scan.json'].update(unsupported_layouts=['unverified']),
            'unredacted_buffer_contents': lambda t, a: a['review/deep_buffer_cleanup.json'].update(raw_buffer_contents_disclosed=True),
            'scene_equivalence_changed': lambda t, a: a['review/native_equivalence.json'].update(semantic_sha256_after='0' * 64),
            'changed_active_scene': lambda t, a: a['review/independent_clean_revision.json'].update(active_scene_string_values_unchanged=False),
            'privacy_evidence_lost': lambda t, a: a['public_metadata_audit.json'].update(private_metadata_findings=['unresolved']),
            'cleanup_as_new_design': lambda t, a: t['release_boundary.json'].update(paper_design_count=2),
        }
        for name, mutate in mutations.items():
            task, assets = copy.deepcopy(self.task), copy.deepcopy(self.assets)
            mutate(task, assets)
            with self.subTest(mutation=name), self.assertRaises((AssertionError, KeyError, TypeError)):
                audit_sanitized_lineage(task, assets, self.raw)
        self.assertEqual(len(mutations), 11)


if __name__ == '__main__':
    unittest.main(verbosity=2)
