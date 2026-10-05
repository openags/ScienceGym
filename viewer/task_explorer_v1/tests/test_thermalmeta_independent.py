"""Independent thermalmeta fidelity audit, using only frozen ZIP/source bytes.

No adapter, generator, runtime guard, or package validator is imported. The
companion oracle was extracted from the supplied ZIPs; portable runs retain
exact member, byte and SHA-256 pins. Hostile inputs are in-memory only.
This checks faithful static display and conservative boundaries, not physics,
receipt authentication, source rereading, or experimental qualification.
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
ORACLE = json.loads((HERE / 'thermalmeta_frozen_oracle.json').read_text())
PACKAGES = ORACLE['packages']
STAGES = [f'P{i:02}' for i in range(1, 21)]
FAMILIES = ['CLOAK', 'ROTATOR45', 'CONCENTRATOR18']
CELLS = [f'COND_{family}_{orientation}' for family in FAMILIES for orientation in ['X', 'Y']]
BRANCHES = [f'B{i:02}' for i in range(1, 13)]
CHILDREN = ['B05_FEATURE', 'B05_MATERIAL', 'B09_ROTATOR', 'B09_CONCENTRATOR',
            'B10_THERMOTICS', 'B10_LAMINATE', 'B10_CONVERSION', 'B10_CIRCULAR',
            'B10_MAPPING', 'B10_UNION', 'B10_HEAT', 'B10_METRICS']
FAMILY_KEYS = set('id label title doi color family_scope family_scope_label source_commit '
    'source_archive_sha256 asset_archive_sha256 source_folder source_link_mode source_publication '
    'status source_warnings visibility actor_projection_implemented operations routes evidence context '
    'dependencies source_files default_route default_route_basis asset_links asset_boundary summary_counts'.split())
OP_KEYS = set('id title stage actions objects pre post acceptance recovery sources unknowns provenance '
    'loop detail source_file source_pointer display_action_ownership display_mapping_basis'.split())
ROUTE_KEYS = set('id label route_kind metadata_only nodes basis detail source_file source_pointer navigation_basis'.split())


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def same_json(actual, expected):
    """Exact JSON values/types, preserving false versus zero and integers versus floats."""
    return json.dumps(actual, sort_keys=True, ensure_ascii=False, allow_nan=False) == json.dumps(
        expected, sort_keys=True, ensure_ascii=False, allow_nan=False)


def decode_shared(pooled):
    """Independent strict decoder: reject malformed, bool, cyclic and mixed refs."""
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
    for kind, package in PACKAGES.items():
        assert set(raw[kind]) == set(package['files']), kind + ' exact membership'
        for name, expected in package['files'].items():
            value = raw[kind][name]
            assert len(value) == expected['bytes'], kind + '/' + name + ' bytes'
            assert digest(value) == expected['sha256'], kind + '/' + name + ' SHA256'


def audit_core_bindings(task, assets, raw):
    """Current byte-level reciprocal manifests and exact static stage bindings."""
    assert raw['task']['PAIR_SEAL.json'] == raw['asset']['PAIR_SEAL.json']
    assert raw['task']['scene_binding_contract.json'] == raw['asset']['scene_binding_contract.json']
    seal = task['PAIR_SEAL.json']
    assert seal['task_content_manifest_sha256'] == digest(raw['task']['CONTENT_MANIFEST.json'])
    assert seal['scene_content_manifest_sha256'] == digest(raw['asset']['CONTENT_MANIFEST.json'])
    assert seal['shared_binding_sha256'] == digest(raw['task']['scene_binding_contract.json'])
    assert seal['task_content_manifest_sha256'] == 'd968ca5cd1a4148842e3c3e4495865bd9b82ff40919083337b9c5a457ff76fac'
    assert seal['scene_content_manifest_sha256'] == '86e46c29f5f94d57b62ae22c51ade7d803fd11b0bab2d7ba28797a3484796ea3'
    assert seal['shared_binding_sha256'] == '1bf845101a77aa329fb27e75f7ecd43357fbafd9f78cadf5458e3d23dae2cc4c'
    assert seal['paper_design_units'] == 1 and seal['validated_runnable_scientific_tasks'] == 0
    assert seal['physical_or_scientific_execution_validated'] is False
    assert seal['source_qualification_holds_resolved'] is False
    for kind, documents, count in [('task', task, 41), ('asset', assets, 48)]:
        members = documents['CONTENT_MANIFEST.json']['files']
        names = [m['path'] for m in members]
        assert len(names) == len(set(names)) == count
        assert names == sorted(names)
        assert set(names) == set(raw[kind]) - {'CONTENT_MANIFEST.json', 'PAIR_SEAL.json'}
        for member in members:
            b = raw[kind][member['path']]
            assert member['bytes'] == len(b) and member['sha256'] == digest(b)
    for stem in ['source_conflicts', 'source_facts', 'station_contracts', 'unknown_inputs']:
        assert raw['asset'][stem + '_snapshot.json'] == raw['task'][stem + '.json']
    binding = task['scene_binding_contract.json']
    assert binding['default_state'] == 'HOLD_UNQUALIFIED'
    for name in ['physical_actuation_enabled', 'hardware_commands_allowed',
                 'physics_simulation_performed', 'geometry_interface_qualified']:
        assert binding[name] is False
    groups = binding['assets']
    assert [g['asset_id'] for g in groups] == [f'A{i:02}' for i in range(1, 11)]
    anchors = binding['anchors']
    assert len({a['anchor_id'] for a in anchors}) == len(anchors) == 25
    assert all(a['mode'] == 'static_evidence_only' and a['physical_actuation_enabled'] is False for a in anchors)
    assert [s['stage_id'] for s in binding['stage_bindings']] == STAGES
    for stage, linked in zip(task['operations.json']['stages'], binding['stage_bindings']):
        assert linked['stage_id'] == stage['id']
        assert linked['title'] == stage['title']
        assert linked['asset_ids'] == stage['scene_asset_ids']
        assert linked['anchor_id'] == stage['scene_anchor_id']
        assert linked['mode'] == 'static_evidence_only'
        assert linked['anchor_id'] in {a['anchor_id'] for a in anchors}
        assert set(linked['asset_ids']) <= {g['asset_id'] for g in groups}
    assert [v['condition_id'] for v in binding['condition_views']] == CELLS
    for source_family in task['sample_contract.json']['families']:
        cells = [v for v in binding['condition_views'] if v['sample_family_id'] == source_family['sample_family_id']]
        assert [v['orientation'] for v in cells] == ['X', 'Y']
        assert {v['specimen_id'] for v in cells} == {source_family['specimen_id']}
        assert all(v['independent_specimen_claim'] is False for v in cells)
        assert all(v['profile_number_to_orientation_status'] == 'authored_visual_selector_not_source_verified' for v in cells)
    objects = assets['scene_manifest.json']['objects']
    names = [o['name'] for o in objects]
    assert len(names) == len(set(names))
    assert {a['object_name'] for a in anchors} <= set(names)
    assert {g['asset_root_object'] for g in groups} <= set(names)
    assert all(v['root_object'] in names for v in binding['condition_views'])
    return True


def audit_source_boundaries(task, assets):
    """Document-specific invariants supplement recursive byte-pinned fidelity."""
    identity = task['task.json']
    assert identity['paper']['doi'] == '10.1038/s41467-024-49630-1'
    assert identity['accepted_paper_design_units'] == 1
    assert identity['validated_runnable_scientific_tasks'] == identity['actual_experiments_performed'] == 0
    for key in ['physical_execution_enabled', 'numerical_physics_enabled', 'source_reproduction_claim']:
        assert identity[key] is False
    assert identity['source_condition_ids'] == CELLS
    assert identity['source_replication_counts'] == 'not reported'
    sample = task['sample_contract.json']
    assert [f['sample_family_id'] for f in sample['families']] == FAMILIES
    assert sample['source_independent_n'] is None and sample['source_technical_n'] is None
    assert [c for f in sample['families'] for c in f['conditions']] == CELLS
    assert all('no manufactured specimen exists' in f['identity_kind'] for f in sample['families'])
    repeats = task['controls_and_repeats.json']
    assert repeats['no_fabricated_counts'] is True
    assert len(repeats['authored_proposal']) == 6
    assert 'conditions, not replicates' in repeats['reported']['orientations']
    branches = task['branches.json']
    assert [b['id'] for b in branches['families']] == BRANCHES
    assert [b['id'] for b in branches['child_branches']] == CHILDREN
    assert set(branches['execution_status']) == set(BRANCHES + CHILDREN)
    assert set(branches['execution_status'].values()) == {'unexecuted; evidence registration only'}
    assert branches['one_paper_unit'] is True
    stages = task['operations.json']['stages']
    assert [s['id'] for s in stages] == STAGES
    assert all(s['status'] == 'authored_contract_not_executed' and s['commands_enabled'] is False for s in stages)
    assert [s['id'] for s in stages if s['execution_surface'] == 'receipt_only_closed_service'] == [
        'P04', 'P05', 'P06', 'P07', 'P09', 'P11', 'P12', 'P13', 'P14', 'P15']
    assert stages[14]['depends_on'] == [], 'Emergency safe release cannot depend on successful data acquisition'
    failures = task['operations.json']['failure_edges']
    assert [(e['from'], e['to']) for e in failures] == [
        ('P11', 'P15'), ('P12', 'P15'), ('P13', 'P15'), ('P14', 'P15'),
        ('P15', 'SERVICE_CUSTODY_HOLD'), ('SERVICE_CUSTODY_HOLD', 'P15')]
    assert task['lifecycle_contract.json']['release_failure_target'] == 'SERVICE_CUSTODY_HOLD'
    assert 'timeout' in task['lifecycle_contract.json']['no_implicit_release']
    assert 'Never successful' in task['lifecycle_contract.json']['administrative_incomplete_closeout']
    assert task['preparation_contract.json']['closed_service_only'] is True
    assert task['preparation_contract.json']['cross_family_substitution_allowed'] is False
    assert [x['id'] for x in task['source_conflicts.json']] == [f'C{i:02}' for i in range(1, 10)]
    assert all(x['resolved'] is False for x in task['source_conflicts.json'])
    assert [x['id'] for x in task['unknown_inputs.json']] == [f'U{i:02}' for i in range(1, 14)]
    assert all(x['may_be_invented'] is False for x in task['unknown_inputs.json'])
    analysis = task['analysis_contract.json']
    assert analysis['implementation_status'] == 'not implemented; no metric or PDE/geometry solver executed'
    assert analysis['no_monotonic_feature_assertion'] is True
    assert analysis['metric_holds']['arbitrary_domain_mapping'] == ['C02', 'C08', 'C09', 'U13']
    assert 'never substitute zero' in analysis['zero_denominator']
    observations = task['observation_contract.json']
    assert observations['observed_data_present'] is False and observations['temperature_arrays_present'] is False
    assert 'transversely' in observations['profile_source_rules']['rotator']
    assert 'align with' in observations['profile_source_rules']['cloak_and_concentrator']
    assert '45-minute interval is context only' in observations['stability_rule']
    outcome = task['source_outcomes_reference.json']
    assert 'never evaluator acceptance thresholds' in outcome['status']
    assert outcome['numerical']['cloak_reference']['RTD_Y_percent'] == 1.37
    assert outcome['numerical']['cloak_reference']['RTD_X_percent'] == 1.27
    assert 'Y-direction only' in outcome['numerical']['cloak_core_sweep']['source']
    assert 'Not acquired' in outcome['experimental']['raw_numeric_curves']
    release = task['RELEASE_BOUNDARY.json']
    for key in ['hardware_adapter_implemented', 'robot_motion_qualified', 'physical_simulator_implemented',
                'numerical_solver_implemented', 'raw_experimental_data_available', 'source_code_or_CAD_included',
                'operating_recipes_included']:
        assert release[key] is False
    assert release['qualification_required_before_any_real_operation'] is True
    assert release['safe_handling_parameters'].startswith('Unknown.')
    assert release['validated_runnable_whole_paper_tasks'] == 0
    assert task['agent_visible.json']['source_outcome_targets_visible'] is False
    assert 'No scientific-score' in task['agent_visible.json']['scoring']
    controls = assets['static_controls.json']
    assert controls['state'] == 'HOLD_UNQUALIFIED' and controls['side_effects'] is False
    assert controls['hardware_adapter'] is controls['network_transport'] is None
    assert controls['actuator_commands'] == [] and set(controls['default_telemetry'].values()) == {None}
    assert assets['STATUS.json']['independent_physical_specimen_count'] is None
    assert assets['STATUS.json']['synthetic_specimen_identity_count'] == 3
    assert assets['contact_contract.json']['fit_or_force_qualified'] is False
    assert all(c['physical_fit_qualified'] is False for c in assets['contact_contract.json']['contacts'])
    return True


def audit(family, task, assets, raw):
    """Independent source-document oracle, reused against hostile projections."""
    assert set(family) == FAMILY_KEYS, 'No added telemetry or executable surface'
    aliases = {'evaluator_reference.json': 'acceptance', 'lineage_contract.json': 'lineage'}
    expected = {aliases.get(name, name[:-5]): doc for name, doc in task.items()}
    assert len(expected) == 29 and len(assets) == 27
    expected['static_assets'] = assets
    assert same_json(family['context'], expected), 'All 29 task and 27 asset JSON documents remain recursively lossless'
    expected_sources = {}
    for kind, documents in [('task', task), ('asset', assets)]:
        folder = PACKAGES[kind]['folder']
        for name in documents:
            display = name if kind == 'task' else 'static_assets/' + name
            expected_sources[display] = {'url': '../../' + folder + '/' + name,
                'repository_path': folder + '/' + name, 'sha256': digest(raw[kind][name])}
    assert family['source_files'] == expected_sources, 'Exact recursive source provenance and links'
    assert family['id'] == 'thermalmeta' and family['family_scope'] == 'paper_level_design'
    assert family['doi'] == task['task.json']['paper']['doi']
    assert family['title'] == task['task.json']['paper']['title']
    assert family['visibility'] == 'author_evaluator_reference_only'
    assert family['actor_projection_implemented'] is False
    assert family['source_commit'] is None
    assert family['source_archive_sha256'] == PACKAGES['task']['archive_sha256']
    assert family['asset_archive_sha256'] == PACKAGES['asset']['archive_sha256']
    assert family['source_folder'] == '../../tasks/thermalmeta_operations_v2/'
    assert family['source_link_mode'] == 'repository_relative_frozen_local_snapshot'
    assert 'remote publication is not asserted' in family['source_publication']
    assert family['default_route'] == 'HOLD_UNQUALIFIED'
    assert 'metadata-only' in family['default_route_basis']
    stages = task['operations.json']['stages']
    assert [op['id'] for op in family['operations']] == STAGES
    for i, (source, op) in enumerate(zip(stages, family['operations'])):
        assert set(op) == OP_KEYS, source['id'] + ' no extra command/result fields'
        assert same_json(op['detail'], source), source['id'] + ' exact stage'
        assert op['source_file'] == 'operations.json' and op['source_pointer'] == f'/stages/{i}'
        assert op['title'] == source['title']
        assert op['stage'] == source['station_id']
        assert op['actions'] == [source['title']]
        assert same_json(op['objects'], {key: source[key] for key in ('input', 'scene_asset_ids', 'scene_anchor_id')})
        assert same_json(op['pre'], {key: source[key] for key in ('depends_on', 'gate')})
        assert same_json(op['acceptance'], {key: source[key] for key in ('output', 'required_receipt_fields')})
        assert op['recovery'] == source['failure_route']
        assert same_json(op['provenance'], {key: source[key] for key in ('role', 'status', 'evidence_class',
            'route_id', 'source_proposal_id', 'execution_surface', 'commands_enabled')})
        assert op['unknowns'] == {'mapping': 'All source conflicts and unresolved inputs remain in exact context; '
                                            'no per-stage unknown mapping is invented.'}
        assert op['post'] == ('No observed post-state field supplied; inspect the exact source contract. '
                              'No value or command is inferred.'), 'Source outputs are obligations, not observations'
        assert op['loop'] is None, 'No fabricated repetition counts'
        assert op['sources'] == [], 'No invented per-stage fact attribution'
        assert 'no additional action or hardware command is invented' in op['display_action_ownership']
        assert 'never observed' in op['display_mapping_basis']
    assert family['summary_counts'] == {
        'source_coverage_families': 12, 'source_child_scopes': 12, 'physical_device_families': 3,
        'condition_views': 6, 'authored_reference_views': 5, 'metadata_only_hold_views': 2,
        'source_json_documents': 29, 'asset_json_documents': 27, 'operation_templates': 20,
        'source_evidence_entries': 15, 'source_ambiguities': 9, 'unresolved_input_groups': 13,
        'authored_control_proposals': 6, 'symbolic_loops': 6, 'scene_groups': 10,
        'symbolic_anchors': 25, 'task_content_files': 41, 'asset_content_files': 48}
    assert len(family['routes']) == 37
    routes = {r['id']: r for r in family['routes']}
    references = {
        'OPERATIONS_REFERENCE': 'operations.json',
        'PREPARATION_REFERENCE': 'preparation_contract.json',
        'CONTROLS_REFERENCE': 'controls_and_repeats.json',
        'OUTCOMES_REFERENCE': 'source_outcomes_reference.json',
        'BINDINGS_REFERENCE': 'scene_binding_contract.json',
        'HOLD_UNQUALIFIED': 'scene_binding_contract.json',
        'SERVICE_CUSTODY_HOLD': 'lifecycle_contract.json',
    }
    assert set(routes) == set(BRANCHES + CHILDREN + CELLS) | set(references)
    matrix = task['coverage_matrix.json']['stages']
    for i, branch in enumerate(task['branches.json']['families']):
        r = routes[branch['id']]
        assert r['source_file'] == 'branches.json' and r['source_pointer'] == f'/families/{i}'
        assert r['detail'] == branch
        assert r['route_kind'] == branch['evidence_class']
        expected_members = [(row['stage_id'], f'/stages/{j}/stage_id')
                            for j, row in enumerate(matrix) if branch['id'] in row['branch_ids']]
        nodes = [n for n in walk(r['nodes']) if n['type'] == 'op']
        assert [n['id'] for n in nodes] == [x[0] for x in expected_members], branch['id'] + ' exact source coverage membership'
        assert r['metadata_only'] is False
        for node, (_, pointer) in zip(nodes, expected_members):
            assert node['meta']['source_file'] == 'coverage_matrix.json'
            assert node['meta']['source_pointer'] == pointer
    for i, child in enumerate(task['branches.json']['child_branches']):
        r = routes[child['id']]
        assert r['detail'] == child
        assert r['route_kind'] == 'source_child_scope'
        assert r['source_file'] == 'branches.json' and r['source_pointer'] == f'/child_branches/{i}'
        assert r['metadata_only'] is True
        assert not any(n['type'] == 'op' for n in walk(r['nodes'])), 'Child coverage does not invent parent-stage membership'
    for i, cell in enumerate(task['scene_binding_contract.json']['condition_views']):
        r = routes[cell['condition_id']]
        assert r['detail'] == cell
        assert r['route_kind'] == 'static_condition_reference'
        assert r['source_file'] == 'scene_binding_contract.json' and r['source_pointer'] == f'/condition_views/{i}'
        assert r['metadata_only'] is True
        assert not any(n['type'] == 'op' for n in walk(r['nodes'])), 'Design cells are not specimen/operation executions'
    reference_kinds = {
        'OPERATIONS_REFERENCE': 'operation_inventory', 'PREPARATION_REFERENCE': 'preparation_reference',
        'CONTROLS_REFERENCE': 'controls_reference', 'OUTCOMES_REFERENCE': 'source_outcomes_reference',
        'BINDINGS_REFERENCE': 'bindings_reference', 'HOLD_UNQUALIFIED': 'qualification_hold',
        'SERVICE_CUSTODY_HOLD': 'failure_hold'}
    for route_id, filename in references.items():
        r = routes[route_id]
        assert r['source_file'] == filename and r['source_pointer'] == ''
        assert r['route_kind'] == reference_kinds[route_id]
        assert r['detail'] == task[filename]
        assert r['metadata_only'] is (route_id != 'OPERATIONS_REFERENCE')
        nodes = [n for n in walk(r['nodes']) if n['type'] == 'op']
        assert [n['id'] for n in nodes] == (STAGES if route_id == 'OPERATIONS_REFERENCE' else [])
        if route_id == 'OPERATIONS_REFERENCE':
            for i, node in enumerate(nodes):
                assert node['meta']['source_file'] == 'operations.json'
                assert node['meta']['source_pointer'] == f'/stages/{i}/id'
    for r in routes.values():
        assert set(r) == ROUTE_KEYS, r['id'] + ' no added execution/result fields'
        assert same_json(resolve_pointer(task[r['source_file']], r['source_pointer']), r['detail'])
        assert 'no added scientific branch' in r['navigation_basis']
        assert 'zero validated runnable whole-paper tasks' in r['basis']
        assert 'HOLD_UNQUALIFIED' in r['basis']
        assert len(r['nodes']) == (1 if r['metadata_only'] else 2)
        contracts = 0
        for n in walk(r['nodes']):
            assert n['type'] in {'op', 'obligations', 'condition'}, 'No invented branch/cycle nodes'
            meta = n.get('meta', {})
            if n['type'] == 'op':
                assert set(n) == {'type', 'id', 'meta'}
                expected_meta = {'source_file', 'source_pointer', 'source_node', 'meaning'}
                if r['id'] in BRANCHES:
                    expected_meta.add('coverage_record')
                    assert meta['coverage_record'] == resolve_pointer(task['coverage_matrix.json'],
                                                                     meta['source_pointer'].rsplit('/', 1)[0])
                assert set(meta) == expected_meta
                assert resolve_pointer(task[meta['source_file']], meta['source_pointer']) == n['id'] == meta['source_node']
                assert ('not execution or inferred chronology' in meta['meaning'] or
                        'no execution or adjacency chronology' in meta['meaning'])
            else:
                assert set(n) == {'type', 'label', 'ordered', 'children', 'meta'}
                assert n['ordered'] is False, 'Coverage must not add chronology'
                if n['type'] == 'condition':
                    contracts += 1
                    assert n['children'] == []
                    assert set(meta) == {'source_file', 'source_pointer', 'source_contract'}
                    assert meta['source_file'] == r['source_file'] and meta['source_pointer'] == r['source_pointer']
                    assert same_json(meta['source_contract'], r['detail'])
                else:
                    assert set(meta) == {'order'} and 'does not create chronology' in meta['order']
        assert contracts == 1
    assert 'no new telemetry' in routes['OUTCOMES_REFERENCE']['label']
    assert 'NO' in routes['HOLD_UNQUALIFIED']['label']
    assert 'CUSTODY' in routes['SERVICE_CUSTODY_HOLD']['label']
    assert same_json(family['evidence'], {fact['id']: fact for fact in task['source_facts.json']['facts']})
    # Every dependency remains a whole source document, with no inferred graph.
    dependencies = family['dependencies']
    assert 'display_rule' in dependencies
    for name, value in dependencies.items():
        if name != 'display_rule':
            assert name + '.json' in task and same_json(value, task[name + '.json']), name + ' exact dependency document'
    assert 'Exact dependency, loop, failure and custody contracts remain authoritative' in dependencies['display_rule']
    assert {'operations', 'preparation_contract', 'lineage_contract', 'lifecycle_contract',
            'sample_contract', 'observation_contract', 'analysis_contract', 'failure_catalog',
            'coverage_matrix', 'display_rule'} == set(dependencies)
    assert family['source_warnings'] in family['status']
    for phrase in ['not six independent specimens', 'source independent and technical counts remain unknown',
                   'analytical/numerical source scope with no execution', 'Nine source conflicts',
                   '2-norm versus squared-error', 'Eq.16 residual index', '3.0 versus curve endpoint 2.5',
                   'physical-unit/absolute-flux uncertainties', 'not silently repaired',
                   'No optimizer, FEM solver or metric computation',
                   'never measured episode telemetry, rewards or success thresholds',
                   'authored visual selectors', '45-minute interval', 'historical context',
                   'per-specimen chain', 'closed qualified services', 'does not reread publications',
                   'Administrative closeout cannot release custody or claim success']:
        assert phrase in family['source_warnings'], 'Missing boundary: ' + phrase
    for phrase in ['zero validated runnable whole-paper tasks', 'Read-only author/evaluator inspection',
                   'never observed outcomes', 'HOLD_UNQUALIFIED']:
        assert phrase in family['status'], 'Missing status boundary: ' + phrase
    for phrase in ['illustrative and unqualified', 'No source-exact CAD']:
        assert phrase in family['asset_boundary']
    links = ['README.md', 'previews/preview_01_overview.png',
             'previews/preview_02_condition_views.png', 'previews/preview_03_guarded_services.png']
    assert len(family['asset_links']) == 4
    for link, name in zip(family['asset_links'], links):
        assert set(link) == {'label', 'path', 'url', 'sha256'}
        assert link['path'] == PACKAGES['asset']['folder'] + '/' + name
        assert link['url'] == '../../' + link['path']
        assert link['sha256'] == digest(raw['asset'][name])
    return True


class FrozenThermalmetaOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = {kind: {name: (ROOT / p['folder'] / name).read_bytes() for name in p['files']}
                   for kind, p in PACKAGES.items()}
        audit_raw(cls.raw)
        cls.task = {n: json.loads(b) for n, b in cls.raw['task'].items() if n.endswith('.json')}
        cls.assets = {n: json.loads(b) for n, b in cls.raw['asset'].items() if n.endswith('.json')}
        cls.pooled = json.loads((VIEW / 'data/thermalmeta.json').read_text())
        cls.family = decode_shared(cls.pooled)

    def test_01_exact_package_membership_and_bytes(self):
        for kind, p in PACKAGES.items():
            folder = ROOT / p['folder']
            names = {f.relative_to(folder).as_posix() for f in folder.rglob('*')
                     if f.is_file() and '__pycache__' not in f.parts}
            self.assertEqual(names, set(p['files']))
        audit_raw(self.raw)

    def test_02_frozen_zip_oracles_when_available(self):
        explicit = os.environ.get('SCIENCEGYM_RELEASE_ARCHIVES')
        for kind, p in PACKAGES.items():
            if not explicit:
                continue  # Portable runs always retain exact byte/member pins above.
            archive = Path(explicit) / p['archive']
            self.assertTrue(archive.is_file(), 'Explicit immutable release ZIP unavailable')
            b = archive.read_bytes()
            self.assertEqual(len(b), p['archive_bytes'])
            self.assertEqual(digest(b), p['archive_sha256'])
            with zipfile.ZipFile(archive) as z:
                names = [n for n in z.namelist() if not n.endswith('/')]
                self.assertEqual(len(names), len(set(names)))
                self.assertEqual(len(names), p['archive_members'])
                self.assertEqual(set(names), {p['archive_prefix'] + n for n in p['files']})
                for name, raw in self.raw[kind].items():
                    self.assertEqual(z.read(p['archive_prefix'] + name), raw)

    def test_03_reciprocal_manifests_binding_and_identity(self):
        self.assertTrue(audit_core_bindings(self.task, self.assets, self.raw))

    def test_04_source_boundaries_and_all_ambiguities(self):
        self.assertTrue(audit_source_boundaries(self.task, self.assets))

    def test_05_hostile_raw_core_and_pool_changes(self):
        for kind, name in [('task', 'source_conflicts.json'), ('asset', 'geometry/thermalmeta_lab.glb')]:
            bad = {k: dict(v) for k, v in self.raw.items()}
            bad[kind][name] += b' '
            with self.subTest(raw=kind + '/' + name), self.assertRaises(AssertionError):
                audit_raw(bad)
        for key in ['task_content_manifest_sha256', 'scene_content_manifest_sha256', 'shared_binding_sha256']:
            bad = copy.deepcopy(self.task)
            bad['PAIR_SEAL.json'][key] = '0' * 64
            with self.subTest(seal=key), self.assertRaises(AssertionError):
                audit_core_bindings(bad, self.assets, self.raw)
        for pooled in [
            {'shared': [], 'x': {'$shared': 0}},
            {'shared': ['x'], 'x': {'$shared': -1}},
            {'shared': ['x'], 'x': {'$shared': True}},
            {'shared': ['x'], 'x': {'$shared': 0, 'extra': 1}},
            {'shared': [{'$shared': 0}], 'x': {'$shared': 0}},
            {'shared': [{'$shared': 1}, {'$shared': 0}], 'x': {'$shared': 1}},
        ]:
            with self.subTest(pool=pooled), self.assertRaises(AssertionError):
                decode_shared(pooled)
        decoded = decode_shared({'shared': [{'a': [1]}], 'x': {'$shared': 0}, 'y': {'$shared': 0}})
        decoded['x']['a'].append(2)
        self.assertEqual(decoded['y'], {'a': [1]}, 'References must not alias')

    def test_06_js_registration_matches_json(self):
        prefix = 'window.SCIENCEGYM_DATA=window.SCIENCEGYM_DATA||{};window.SCIENCEGYM_DATA["thermalmeta"]='
        js = (VIEW / 'data/thermalmeta.js').read_text()
        self.assertTrue(js.startswith(prefix))
        self.assertEqual(json.loads(js[len(prefix):].strip().removesuffix(';')), self.pooled)
        self.assertIn('data/thermalmeta.js', (VIEW / 'index.html').read_text())


    def test_07_all_source_json_and_projection_fidelity(self):
        self.assertTrue(audit(self.family, self.task, self.assets, self.raw))

    def test_08_every_recursive_source_document_mutation_rejected(self):
        count = 0
        for key in self.family['context']:
            if key == 'static_assets':
                continue
            bad = copy.deepcopy(self.family)
            bad['context'].pop(key)
            with self.subTest(task_document=key), self.assertRaises(AssertionError):
                audit(bad, self.task, self.assets, self.raw)
            count += 1
        for name in self.assets:
            bad = copy.deepcopy(self.family)
            bad['context']['static_assets'][name] = {'original_document_lost': True}
            with self.subTest(asset_document=name), self.assertRaises(AssertionError):
                audit(bad, self.task, self.assets, self.raw)
            count += 1
        self.assertEqual(count, 56)

    def test_09_hostile_projection_changes_rejected(self):
        mutations = {
            'invent_temperature_telemetry': lambda f: f.update(measurements=[{'temperature': 37}]),
            'enable_actor': lambda f: f.update(actor_projection_implemented=True),
            'claim_unverified_commit': lambda f: f.update(source_commit='0' * 40),
            'stale_task_archive': lambda f: f.update(source_archive_sha256='0' * 64),
            'stale_asset_archive': lambda f: f.update(asset_archive_sha256='0' * 64),
            'default_runs_powered_stage': lambda f: f.update(default_route='B01'),
            'count_cells_as_families': lambda f: f['summary_counts'].update(physical_device_families=6),
            'count_child_scope_as_experiment': lambda f: f['summary_counts'].update(source_coverage_families=24),
            'drop_review_provenance': lambda f: f['source_files'].pop('review/independent_task_review.json'),
            'wrong_asset_hash': lambda f: f['source_files']['static_assets/PAIR_SEAL.json'].update(sha256='0' * 64),
            'wrong_source_url': lambda f: f['source_files']['operations.json'].update(url='../../tasks/thermalmeta_operations_v1/operations.json'),
            'wrong_stage_pointer': lambda f: f['operations'][4].update(source_pointer='/stages/5'),
            'invent_action': lambda f: f['operations'][10].update(actions=['set_heat(37)']),
            'false_to_zero_in_context': lambda f: f['context']['RELEASE_BOUNDARY'].update(hardware_adapter_implemented=0),
            'false_to_zero_in_display': lambda f: f['operations'][10]['provenance'].update(commands_enabled=0),
            'float_for_source_integer': lambda f: f['context']['task'].update(accepted_paper_design_units=1.0),
            'enable_commands': lambda f: f['operations'][10]['provenance'].update(commands_enabled=True),
            'source_outcome_as_post': lambda f: f['operations'][13].update(post={'RTD_Y_percent': 1.37}),
            'output_obligation_as_receipt': lambda f: f['operations'][13]['acceptance'].update(received=True),
            'source_percentage_as_threshold': lambda f: f['operations'][17]['acceptance'].update(RTD_Y_max=1.37),
            'omit_receipt_fields': lambda f: f['operations'][14]['acceptance']['required_receipt_fields'].clear(),
            'infer_repeat_three': lambda f: f['operations'][15].update(loop={'count': 3}),
            'invent_stage_fact_attribution': lambda f: f['operations'][10].update(sources=['F01']),
            'invent_unknown_mapping': lambda f: f['operations'][10].update(unknowns=[]),
            'release_depends_on_acquisition': lambda f: f['operations'][14]['pre'].update(depends_on=['P14']),
            'erase_release_failure': lambda f: f['operations'][14].update(recovery='Automatically retrieve'),
            'invent_dependency_graph': lambda f: f['dependencies'].update(edges=[['P14', 'P15']]),
            'erase_custody_hold': lambda f: f['dependencies']['lifecycle_contract'].update(release_failure_target='P16'),
            'cross_family_preparation': lambda f: f['dependencies']['preparation_contract'].update(cross_family_substitution_allowed=True),
            'duplicate_route': lambda f: f['routes'].append(copy.deepcopy(f['routes'][0])),
            'omit_coverage_stage': lambda f: get_route(f, 'B01')['nodes'][0]['children'].pop(),
            'invent_coverage_chronology': lambda f: get_route(f, 'B01')['nodes'][0].update(ordered=True),
            'wrong_coverage_pointer': lambda f: get_route(f, 'B01')['nodes'][0]['children'][0]['meta'].update(source_pointer='/stages/0/stage_id'),
            'wrong_coverage_record': lambda f: get_route(f, 'B01')['nodes'][0]['children'][0]['meta']['coverage_record'].update(branch_ids=['B10']),
            'numerical_scope_as_experiment': lambda f: get_route(f, 'B05').update(route_kind='source-reported experiment'),
            'child_inherits_parent_stages': lambda f: get_route(f, 'B10_HEAT')['nodes'].append({'type': 'op', 'id': 'P19'}),
            'condition_runs_stage': lambda f: get_route(f, 'COND_CLOAK_Y').update(metadata_only=False),
            'source_outcomes_executable': lambda f: get_route(f, 'OUTCOMES_REFERENCE').update(metadata_only=False),
            'hide_outcome_boundary': lambda f: get_route(f, 'OUTCOMES_REFERENCE').update(label='Measured experiment results'),
            'activate_qualification_hold': lambda f: get_route(f, 'HOLD_UNQUALIFIED').update(metadata_only=False),
            'hold_has_live_operation': lambda f: get_route(f, 'SERVICE_CUSTODY_HOLD')['nodes'].append({'type': 'op', 'id': 'P16'}),
            'resolve_source_conflict': lambda f: f['context']['source_conflicts'][0].update(resolved=True),
            'repair_equation_transcription': lambda f: f['context']['source_conflicts'][1].update(observation='Equation 16 uses e1'),
            'discard_adiabatic_ambiguity': lambda f: f['context']['source_conflicts'].pop(),
            'invent_unknown_physical_interface': lambda f: f['context']['unknown_inputs'][9].update(may_be_invented=True),
            'six_independent_specimens': lambda f: f['context']['sample_contract'].update(source_independent_n=6),
            'two_technical_repeats': lambda f: f['context']['sample_contract'].update(source_technical_n=2),
            'mark_numerical_execution': lambda f: f['context']['branches']['execution_status'].update(B10_HEAT='completed'),
            'invent_monotonic_success': lambda f: f['context']['analysis_contract'].update(no_monotonic_feature_assertion=False),
            'mark_temperature_observed': lambda f: f['context']['observation_contract'].update(temperature_arrays_present=True),
            'promote_source_outcome_reward': lambda f: f['context']['agent_visible'].update(source_outcome_targets_visible=True),
            'enable_thermal_hardware': lambda f: f['context']['RELEASE_BOUNDARY'].update(hardware_adapter_implemented=True),
            'add_actuator_command': lambda f: f['context']['static_assets']['static_controls.json']['actuator_commands'].append('heat'),
            'invent_static_temperature': lambda f: f['context']['static_assets']['static_controls.json']['default_telemetry'].update(temperature=37),
            'pretend_physical_fit': lambda f: f['context']['static_assets']['contact_contract.json'].update(fit_or_force_qualified=True),
            'source_verified_profile_selector': lambda f: f['context']['scene_binding_contract']['condition_views'][0].update(profile_number_to_orientation_status='source_verified'),
            'stale_pair_seal': lambda f: f['context']['PAIR_SEAL'].update(shared_binding_sha256='0' * 64),
            'drop_fact': lambda f: f['evidence'].pop('F01'),
            'hide_warning': lambda f: f.update(source_warnings='Runnable heating demonstration'),
            'substitute_static_asset': lambda f: f['asset_links'][0].update(sha256='0' * 64),
        }
        for name, mutate in mutations.items():
            bad = copy.deepcopy(self.family)
            mutate(bad)
            with self.subTest(mutation=name), self.assertRaises((AssertionError, KeyError, TypeError)):
                audit(bad, self.task, self.assets, self.raw)
        self.assertEqual(len(mutations), 60)

    def test_10_source_specific_hostile_semantics_rejected(self):
        mutations = {
            'six_specimens': lambda t, a: t['sample_contract.json'].update(source_independent_n=6),
            'metric_implemented': lambda t, a: t['analysis_contract.json'].update(implementation_status='implemented'),
            'silent_conflict_resolution': lambda t, a: t['source_conflicts.json'][0].update(resolved=True),
            'source_values_as_rewards': lambda t, a: t['agent_visible.json'].update(source_outcome_targets_visible=True),
            'powered_failure_bypasses_release': lambda t, a: t['operations.json']['failure_edges'][0].update(to='P16'),
            'release_waits_for_data': lambda t, a: t['operations.json']['stages'][14].update(depends_on=['P14']),
            'numerical_branch_complete': lambda t, a: t['branches.json']['execution_status'].update(B05='executed'),
            'unknown_robot_fit': lambda t, a: a['contact_contract.json'].update(fit_or_force_qualified=True),
            'source_value_as_temperature': lambda t, a: a['static_controls.json']['default_telemetry'].update(temperature=37),
        }
        for name, mutate in mutations.items():
            t, a = copy.deepcopy(self.task), copy.deepcopy(self.assets)
            mutate(t, a)
            with self.subTest(mutation=name), self.assertRaises(AssertionError):
                audit_source_boundaries(t, a)


if __name__ == '__main__':
    unittest.main()
