"""Independent, byte-pinned microsphere viewer audit against supplied release ZIPs.

No adapter, generator, package validator, or projection helper is imported.
The companion oracle was extracted directly from the two immutable release
ZIPs and each member checked against this checkout. Portable runs retain all
member, byte, and SHA-256 pins. Hostile projections are serialized in memory.
These tests check faithful static inspection, not real hardware, scientific
replication, receipt authentication, source rereading, or optical qualification.
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
ORACLE = json.loads((HERE / 'microsphere_frozen_oracle.json').read_text())
PACKAGES = ORACLE['packages']
OP_IDS = [f'R{i:02}' for i in range(1, 14)]
BRANCH_IDS = ['E01', 'E02', 'E03', 'E04', 'C01', 'C02', 'C03', 'E05', 'C04', 'N01', 'N02', 'N03', 'N04']
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
    assert tc['core_sha256'] == 'd35ab048fa38f728dba0b19717b3c52681e462ae6df4e846c9733f522c968dd2'
    assert ac['core_sha256'] == 'b8e56b5120ac3ca3ef66c297c2e3b6ffa2b1ca64f346af8e72916396334bf2a9'
    for kind, core, count in [('task', tc, 41), ('asset', ac, 31)]:
        assert core['core_sha256'] == canonical_digest(core['files']), 'Canonical core digest'
        names = [f['path'] for f in core['files']]
        assert len(names) == len(set(names)) == count and names == sorted(names)
        for member in core['files']:
            value = raw[kind][member['path']]
            assert member['bytes'] == len(value) and member['sha256'] == digest(value)
    assert raw['task']['task_core_manifest.json'] == raw['asset']['paired_task_core_manifest.json']
    assert raw['task']['paired_scene_core_manifest.json'] == raw['asset']['scene_core_manifest.json']
    assert raw['task']['shared_binding_contract.json'] == raw['asset']['shared_binding_contract.json']
    assert same_json(assets['paired_task_core_manifest.json'], tc)
    assert same_json(task['paired_scene_core_manifest.json'], ac)
    paired = assets['paired_task_reference.json']
    assert paired['task_core_sha256'] == tc['core_sha256']
    assert paired['scene_core_sha256'] == ac['core_sha256']
    assert paired['shared_binding_contract_sha256'] == digest(raw['task']['shared_binding_contract.json'])
    assert paired['default_state'] == 'HOLD_QUALIFICATION' and paired['physical_execution_enabled'] is False
    for stem in ['controls_and_repeats', 'source_facts', 'source_conflicts', 'lineage_contract', 'sample_custody', 'unknown_inputs']:
        assert raw['asset'][stem + '_snapshot.json'] == raw['task'][stem + '.json']
    # The immutable snapshot has a different authored wrapper; never silently
    # replace its original classification with the task schema/scope fields.
    station = assets['station_contracts_snapshot.json']
    assert station['stations'] == task['station_contracts.json']['stations']
    assert set(station) == {'classification', 'stations'}
    assert 'Proposed closed-service contracts' in station['classification']
    assert raw['asset']['station_contracts_snapshot.json'] != raw['task']['station_contracts.json']
    binding = task['shared_binding_contract.json']
    assert binding['default_state'] == 'HOLD_QUALIFICATION'
    assert binding['physical_actuation_enabled'] is False and binding['scientific_simulation_performed'] is False
    assert binding['branch_ids'] == BRANCH_IDS
    assert binding['unknown_input_ids'] == [f'U{i:02}' for i in range(1, 17)]
    groups = binding['assets']
    assert [g['asset_id'] for g in groups] == [f'A{i:02}' for i in range(1, 10)]
    assert same_json(assets['asset_inventory.json']['assets'], groups)
    assert assets['asset_inventory.json']['counts'] == {
        'groups': 9, 'routes': 13, 'stations': 7, 'anchors': 33, 'qualification_gaps': 16}
    anchors = [anchor for group in groups for anchor in group['anchors']]
    anchor_ids = [a['anchor_id'] for a in anchors]
    assert len(anchor_ids) == len(set(anchor_ids)) == 33
    assert all(a['mode'] == 'evidence_only' and a['physical_actuation_enabled'] is False for a in anchors)
    objects = assets['scene_manifest.json']['objects']
    assert len({o['name'] for o in objects}) == len(objects)
    assert {o['anchor_id'] for o in objects if o['anchor_id'] is not None} == set(anchor_ids)
    assert {g['asset_root_object'] for g in groups} <= {o['name'] for o in objects}
    bindings = binding['route_bindings']
    assert [b['route_id'] for b in bindings] == OP_IDS
    assert [s['id'] for s in task['station_contracts.json']['stations']] == [f'ST{i:02}' for i in range(1, 8)]
    for op, linked in zip(task['operations.json']['operations'], bindings):
        assert linked['route_id'] == op['id'] and linked['station_ids'] == [op['station']]
        assert linked['asset_ids'] == op['asset_ids'] and linked['target_anchor_ids'] == op['anchor_ids']
        assert linked['branch_ids'] == op['branch_ids']
        assert linked['mode'] == 'evidence_only' and linked['physical_actuation_enabled'] is False
        assert set(op['anchor_ids']) <= set(anchor_ids)
        assert set(op['asset_ids']) <= {g['asset_id'] for g in groups}
    return True


def audit_source_boundaries(task, assets):
    release = task['RELEASE_BOUNDARY.json']
    assert type(release['paper_level_designs']) is int and release['paper_level_designs'] == 1
    assert type(release['validated_runnable_whole_paper_tasks']) is int and release['validated_runnable_whole_paper_tasks'] == 0
    for key in ['physical_execution', 'physical_simulation', 'scientific_reproduction', 'source_reanalysis',
                'source_files_exported', 'hardware_safety_qualified', 'exact_geometry_validated', 'github_writes']:
        assert release[key] is False
    assert task['STATUS.json']['physical_runtime'] == 'unimplemented'
    prov = task['provenance.json']
    assert prov['source']['doi'] == '10.1038/ncomms1211'
    assert 'all rights reserved' in prov['rights'] and 'not a reuse license' in prov['rights']
    assert 'original authored materials only' in prov['license']
    assert task['unknown_inputs.json']['physical_default'] == 'HOLD_QUALIFICATION'
    unknowns = task['unknown_inputs.json']['unknowns']
    assert [u['id'] for u in unknowns] == [f'U{i:02}' for i in range(1, 17)]
    assert all(u['status'] == 'unresolved' and u['rule'] == 'Do not supply guessed operational defaults' for u in unknowns)
    branches = task['branches.json']['branches']
    assert [b['id'] for b in branches] == BRANCH_IDS
    assert [b['initial_state'] for b in branches] == ['HOLD_QUALIFICATION'] * 5 + ['SOURCE_CONTEXT_ONLY'] * 8
    assert all(b['physical_execution_status'] == 'UNRUN' and b['implemented'] is False for b in branches)
    assert [b['source_evidence_type'] for b in branches[:4]] == ['experimental figure-backed'] * 4
    assert branches[7]['id'] == 'E05' and branches[7]['source_evidence_type'] == 'text-only experiment'
    assert 'composition unresolved' in branches[3]['material_or_analysis_scope']
    ops = task['operations.json']['operations']
    assert [o['id'] for o in ops] == OP_IDS
    assert all(o['device_command_implemented'] is False and o['physical_execution_authority'] is False for o in ops)
    assert all(o['actor_action'] == 'Select operation_id and independently supplied evidence_id only' for o in ops)
    assert {o['id']: o['depends_on'] for o in ops} == task['dependencies.json']['stage_dependencies']
    assert ops[6]['branch_ids'] == ['E01', 'E02'] and ops[7]['branch_ids'] == ['E03', 'E04']
    assert 'Do not insert 4.74 um' in ops[7]['rule']
    assert 'uncoated branch' in ops[5]['rule'] and 'restored identically' in ops[5]['rule']
    assert 'not an instruction to force a success' in ops[8]['rule']
    assert 'no invented full Cartesian experiment matrix' in ops[9]['rule']
    assert task['controls_and_repeats.json']['reported_repeat_counts'] is None
    assert task['controls_and_repeats.json']['reported_uncertainty_budget'] is None
    assert len(task['controls_and_repeats.json']['reported_controls']) == 6
    assert task['lifecycle_contract.json']['source_repeats'] is None
    assert task['lifecycle_contract.json']['retry_limit'] == 2
    assert 'not a laboratory test count' in task['lifecycle_contract.json']['retry_limit_origin']
    assert 'never marks scientific execution complete' in task['lifecycle_contract.json']['safe_closeout']
    conflicts = task['source_conflicts.json']['items']
    assert [c['id'] for c in conflicts] == [f'D{i:02}' for i in range(1, 11)]
    assert 'SbTe' in conflicts[0]['evidence'] and 'GeSbTe' in conflicts[0]['evidence']
    assert 'text-only' in conflicts[5]['evidence']
    facts = {f['id']: f for f in task['source_facts.json']['facts']}
    assert list(facts) == [f'F{i:02}' for i in range(1, 28)]
    assert 'does not separately state its sphere diameter' in facts['F03']['claim']
    assert facts['F20']['evidence_class'] == 'reported text-only experimental claim'
    assert 'No corresponding 50 nm reflection' in facts['F20']['claim']
    assert facts['F25']['evidence_class'] == 'reported speculation; no task branch'
    assert 'No biological specimens' in task['source_facts.json']['safe_scope']
    outcomes = task['source_outcomes_reference.json']
    assert len(outcomes['outcomes']) == 6 and outcomes['not_independently_remeasured'] is True
    assert outcomes['no_scientific_reproduction'] is True
    assert 'never executable acceptance thresholds' in outcomes['classification']
    assert '50 nm reflection' in task['analysis_contracts.json']['source_claim_policy']
    assert 'optical objective magnification = added virtual magnification' in task['analysis_contracts.json']['prohibited_equivalences']
    assert task['failure_and_closeout.json']['source_closeout_reported'] is False
    assert task['agent_visible.json']['physical_default'] == 'HOLD_QUALIFICATION'
    assert set(task['agent_visible.json']['allowed_action_schema']) == {'operation_id', 'evidence_id'}
    invariant = task['shared_binding_contract.json']['identity_invariants']
    assert invariant['sphere_diameters_um'] == [1, 3, 4.74, 10, 50]
    assert invariant['star_sphere_diameter_um'] is None
    assert invariant['sil_diameters_mm'] == [0.5, 2.5] and invariant['sil_objective_magnifications'] == [80, 40]
    assert invariant['actual_and_magnified_geometry_separate'] is True
    for key in ['source_results_are_measurement_evidence', 'source_results_are_success_thresholds',
                'nanoscopic_patterns_establish_resolution', 'source_speculation_is_executed_branch']:
        assert invariant[key] is False
    scene = assets['scene_manifest.json']
    assert scene['physical_actuation_enabled'] is False and scene['scientific_simulation_performed'] is False
    assert 'SOURCE_SCALE' in scene['scale_boundary'] and 'SCHEMATIC_ENLARGEMENTS' in scene['scale_boundary']
    objects = {o['name']: o for o in scene['objects']}
    assert objects['A02.diagram_warning']['label_text'] == 'SCHEMATIC ONLY / NO LENGTH SCALE / NOT AN OPTICAL IMAGE'
    assert objects['A02.icon_label_star']['label_text'] == 'STAR FILM ?'
    sphere_names = ['1um', '3um', '4p74um', '10um', '50um']
    for name, diameter in zip(sphere_names, [1, 3, 4.74, 10, 50]):
        obj = objects['A03.source_scale_sphere_' + name]
        assert obj['representation_class'] == 'SOURCE_SCALE'
        assert obj['custom']['reported_diameter_um'] == diameter
        assert all(math.isclose(d, diameter * 1e-6, rel_tol=1e-6) for d in obj['dimensions_m'])
    enlarged = objects['A04.magnified_sphere_40000x']
    assert enlarged['representation_class'] == 'SCHEMATIC_ENLARGEMENTS'
    assert enlarged['custom'] == {'reported_diameter_um': 4.74, 'illustration_magnification': 40000}
    assert all(math.isclose(d, 4.74e-6 * 40000, rel_tol=1e-6) for d in enlarged['dimensions_m'])
    asset_prov = assets['provenance.json']
    for key in ['source_media_used', 'copied_figures_or_traced_geometry', 'publisher_or_author_CAD_code_data_bundled',
                'geometry_qualified_for_physical_use', 'optical_measurements_or_simulation_performed']:
        assert asset_prov[key] is False
    assert asset_prov['original_authorship'] is True
    return True


def audit(family, task, assets, raw):
    """Audit the serialized public projection against independent raw source data."""
    assert set(family) == FAMILY_KEYS, 'No added telemetry/execution surface'
    context = {ALIASES.get(name, name[:-5]): value for name, value in task.items()}
    context['static_assets'] = assets
    assert len(task) == 38 and len(assets) == 30
    assert same_json(family['context'], context), 'All 68 source JSON documents remain recursively lossless'
    sources = {}
    for kind, documents in [('task', task), ('asset', assets)]:
        folder = PACKAGES[kind]['folder']
        for name in documents:
            key = name if kind == 'task' else 'static_assets/' + name
            sources[key] = {'url': '../../' + folder + '/' + name, 'repository_path': folder + '/' + name,
                            'sha256': digest(raw[kind][name])}
    assert same_json(family['source_files'], sources), 'Exact local source paths and hashes'
    assert family['id'] == 'microsphere' and family['family_scope'] == 'paper_level_design'
    assert family['family_scope_label'] == 'WHOLE-PAPER DESIGN'
    assert family['title'] == task['provenance.json']['source']['title']
    assert family['doi'] == '10.1038/ncomms1211'
    assert family['visibility'] == 'author_evaluator_reference_only' and family['actor_projection_implemented'] is False
    assert family['source_commit'] is None
    assert family['source_archive_sha256'] == PACKAGES['task']['archive_sha256']
    assert family['asset_archive_sha256'] == PACKAGES['asset']['archive_sha256']
    assert family['source_folder'] == '../../tasks/microsphere_operations_v2/'
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
        for field, keys in [('objects', ['asset_ids', 'anchor_ids']), ('pre', ['depends_on', 'precondition']),
                            ('acceptance', ['required_output', 'rule']), ('recovery', ['failure', 'recovery']),
                            ('provenance', ['kind', 'device_command_implemented', 'physical_execution_authority', 'actor_action'])]:
            assert same_json(op[field], {key: source[key] for key in keys}), source['id'] + ' exact ' + field
        assert same_json(op['unknowns'], source['unresolved_input_refs'])
        assert op['source_file'] == 'operations.json' and op['source_pointer'] == f'/operations/{i}'
        assert op['post'] == ('No observed post-state field supplied; inspect the exact source contract. '
                              'No value or command is inferred.')
        assert op['sources'] == [] and op['loop'] is None
        assert 'no' in op['display_action_ownership'].lower()
        assert 'never observed' in op['display_mapping_basis']
    routes = family['routes']
    assert [r['id'] for r in routes] == BRANCH_IDS + list(REFERENCE_ROUTES)
    assert len(routes) == 20
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
    expected_counts = {'source_scope_branches': 13, 'authored_reference_views': 6, 'metadata_only_hold_views': 1,
        'source_json_documents': 38, 'asset_json_documents': 30, 'operation_templates': 13, 'source_evidence_entries': 27,
        'source_ambiguities': 10, 'reported_outcomes': 6, 'unresolved_input_groups': 16, 'controls': 6,
        'scene_groups': 9, 'symbolic_anchors': 33, 'stations': 7, 'task_core_files': 41, 'asset_core_files': 31}
    assert same_json(counts, expected_counts)
    assert family['source_warnings'] in family['status']
    for phrase in ['zero validated runnable whole-paper tasks', 'Read-only author/evaluator inspection',
                   'HOLD_QUALIFICATION']:
        assert phrase in family['status']
    warning = family['source_warnings'].lower()
    for phrase in ['text-only', 'reflection', 'transmission', 'sbte', 'gesbte', 'star', 'unreported',
                   'rights', 'source_scale', 'schematic_enlargements', 'not', 'threshold', 'repeat']:
        assert phrase in warning, 'Missing conservative warning: ' + phrase
    for phrase in ['illustrative and unqualified', 'No source-exact CAD']:
        assert phrase in family['asset_boundary']
    names = ['README.md', 'previews/preview_01_overview.png', 'previews/preview_02_targets.png', 'previews/preview_03_services.png']
    assert len(family['asset_links']) == 4
    for link, name in zip(family['asset_links'], names):
        assert set(link) == {'label', 'path', 'url', 'sha256'}
        assert link['path'] == PACKAGES['asset']['folder'] + '/' + name
        assert link['url'] == '../../' + link['path'] and link['sha256'] == digest(raw['asset'][name])
    return True


class FrozenMicrosphereOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = {kind: {name: (ROOT / p['folder'] / name).read_bytes() for name in p['files']}
                   for kind, p in PACKAGES.items()}
        audit_raw(cls.raw)
        cls.task = {name: json.loads(b) for name, b in cls.raw['task'].items() if name.endswith('.json')}
        cls.assets = {name: json.loads(b) for name, b in cls.raw['asset'].items() if name.endswith('.json')}
        cls.pooled = json.loads((VIEW / 'data/microsphere.json').read_text())
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

    def test_04_source_scope_rights_optical_claims_and_geometry_boundaries(self):
        self.assertTrue(audit_source_boundaries(self.task, self.assets))

    def test_05_complete_serialized_projection_matches_source(self):
        self.assertTrue(audit(self.family, self.task, self.assets, self.raw))

    def test_06_js_registration_matches_pooled_json(self):
        prefix = 'window.SCIENCEGYM_DATA=window.SCIENCEGYM_DATA||{};window.SCIENCEGYM_DATA["microsphere"]='
        source = (VIEW / 'data/microsphere.js').read_text()
        self.assertTrue(source.startswith(prefix))
        self.assertTrue(same_json(json.loads(source[len(prefix):].strip().removesuffix(';')), self.pooled))
        self.assertIn('data/microsphere.js', (VIEW / 'index.html').read_text())

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
        self.assertEqual(count, 68)

    def test_08_hostile_serialized_projection_mutations_rejected(self):
        first_node = lambda f: get_route(f, 'E01')['nodes'][0]['children'][0]
        mutations = {
            'invent_telemetry': lambda f: f.update(measurements=[{'resolution_nm': 50}]),
            'activate_actor': lambda f: f.update(actor_projection_implemented=True),
            'claim_remote_commit': lambda f: f.update(source_commit='0' * 40),
            'stale_task_archive': lambda f: f.update(source_archive_sha256='0' * 64),
            'stale_asset_archive': lambda f: f.update(asset_archive_sha256='0' * 64),
            'default_activates_branch': lambda f: f.update(default_route='E01'),
            'wrong_scope': lambda f: f.update(family_scope='validated_task'),
            'count_branches_as_tasks': lambda f: f['summary_counts'].update(operation_templates=20),
            'erase_qualification_gaps': lambda f: f['summary_counts'].update(unresolved_input_groups=0),
            'lose_raw_review': lambda f: f['source_files'].pop(next(k for k in f['source_files'] if k.startswith('review/'))),
            'wrong_source_hash': lambda f: f['source_files']['operations.json'].update(sha256='0' * 64),
            'wrong_asset_hash': lambda f: f['source_files']['static_assets/scene_manifest.json'].update(sha256='0' * 64),
            'remote_source_link': lambda f: f['source_files']['operations.json'].update(url='https://invalid.example/operations.json'),
            'wrong_source_pointer': lambda f: f['operations'][0].update(source_pointer='/operations/1'),
            'rename_stage': lambda f: f['operations'][0].update(stage='ST02'),
            'invent_hardware_action': lambda f: f['operations'][6].update(actions=['set_focus(2.5)']),
            'accept_outcome_as_post': lambda f: f['operations'][6].update(post={'resolution_nm': 50}),
            'make_source_result_threshold': lambda f: f['operations'][6]['acceptance'].update(resolution_max_nm=50),
            'receipt_obligation_received': lambda f: f['operations'][6]['acceptance'].update(received=True),
            'invent_repeat_count': lambda f: f['operations'][6].update(loop={'count': 3}),
            'invent_source_fact_mapping': lambda f: f['operations'][6].update(sources=['F20']),
            'drop_unknown_input': lambda f: f['operations'][7]['unknowns'].clear(),
            'lose_qualified_recovery': lambda f: f['operations'][7]['recovery'].update(recovery='Automatically retune until passing'),
            'enable_device': lambda f: f['operations'][6]['provenance'].update(device_command_implemented=True),
            'enable_physical_authority': lambda f: f['operations'][6]['provenance'].update(physical_execution_authority=True),
            'bool_to_zero_in_display': lambda f: f['operations'][6]['provenance'].update(device_command_implemented=0),
            'bool_to_zero_in_context': lambda f: f['context']['RELEASE_BOUNDARY'].update(physical_execution=0),
            'integer_to_float': lambda f: f['context']['RELEASE_BOUNDARY'].update(paper_level_designs=1.0),
            'resolve_star_composition': lambda f: f['context']['source_conflicts']['items'][0].update(evidence='GeSbTe confirmed'),
            'invent_star_sphere': lambda f: f['context']['shared_binding_contract']['identity_invariants'].update(star_sphere_diameter_um=4.74),
            'upgrade_text_claim': lambda f: f['evidence']['F20'].update(evidence_class='experimental figure-backed'),
            'erase_failed_control': lambda f: f['context']['source_outcomes_reference']['outcomes'].pop(4),
            'license_source_media': lambda f: f['context']['provenance'].update(rights='CC-BY'),
            'qualify_geometry': lambda f: f['context']['static_assets']['provenance.json'].update(geometry_qualified_for_physical_use=True),
            'merge_geometry_scales': lambda f: f['context']['static_assets']['scene_manifest.json']['objects'][0].update(representation_class='SOURCE_SCALE'),
            'invent_dependency_graph': lambda f: f['dependencies'].update(edges=[['R01', 'R02']]),
            'remove_dependency': lambda f: f['dependencies']['dependencies']['stage_dependencies']['R02'].clear(),
            'duplicate_route': lambda f: f['routes'].append(copy.deepcopy(f['routes'][0])),
            'remove_route': lambda f: f['routes'].pop(),
            'wrong_branch_membership': lambda f: get_route(f, 'E01')['nodes'][0]['children'].pop(),
            'forge_membership_pointer': lambda f: first_node(f)['meta'].update(source_pointer='/operations/1/id'),
            'invent_ordering': lambda f: get_route(f, 'E01')['nodes'][0].update(ordered=True),
            'invent_chronology_node': lambda f: get_route(f, 'E01')['nodes'][0].update(type='sequence'),
            'activate_hold': lambda f: get_route(f, 'HOLD_QUALIFICATION')['nodes'].insert(0, copy.deepcopy(first_node(f))),
            'activate_outcome': lambda f: get_route(f, 'OUTCOMES_REFERENCE').update(metadata_only=False),
            'change_reference_contract': lambda f: get_route(f, 'CONTROLS_REFERENCE')['detail'].update(reported_repeat_counts=3),
            'drop_warning': lambda f: f.update(source_warnings='Ready to run'),
            'drop_asset_link': lambda f: f['asset_links'].pop(),
            'stale_preview_hash': lambda f: f['asset_links'][1].update(sha256='0' * 64),
        }
        for label, mutate in mutations.items():
            with self.subTest(mutation=label):
                bad = copy.deepcopy(self.family)
                mutate(bad)
                serialized = json.dumps(bad, ensure_ascii=False, allow_nan=False)
                with self.assertRaises(AssertionError):
                    audit(json.loads(serialized), self.task, self.assets, self.raw)
        self.assertGreaterEqual(len(mutations), 45)

    def test_09_raw_core_and_pool_mutations_rejected(self):
        for kind, name in [('task', 'source_conflicts.json'), ('asset', 'geometry/microsphere_lab.glb'),
                           ('asset', 'geometry/microsphere_lab.blend'), ('asset', 'previews/preview_02_targets.png')]:
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
        for relative in ['data/microsphere.json', 'data/microsphere.js', 'docs/microsphere.md', 'diagrams/microsphere.svg']:
            data = (VIEW / relative).read_bytes()
            rpc_bytes = len(json.dumps({'content': data.decode('utf-8')}, ensure_ascii=True).encode('utf-8')) + 65536
            with self.subTest(file=relative):
                self.assertLess(len(data), 6000000, 'Retain compact source-lossless microsphere package')
                self.assertLess(rpc_bytes, 15 * 1024 * 1024, 'Reserve metadata margin below Git JSON-RPC limit')


if __name__ == '__main__':
    unittest.main(verbosity=2)
