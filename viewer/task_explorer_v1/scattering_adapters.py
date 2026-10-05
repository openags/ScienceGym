"""Lossless anomalous-scattering inspector. Static original design; no actuation."""
import hashlib
import json
from paired_adapters import clone, read, context_key, contract, absent

PACKAGES = {'scattering': 'scattering_operations_v2'}
SOURCE_COMMIT = None  # Archive/file identities, not an invented public commit.
TASK_ARCHIVE_SHA256 = '02cf39abb287bed41d282a4996a50d51630713c98d4b9adf244452c8fd06f74b'
ASSET_ARCHIVE_SHA256 = '241e32c2812a2ed534044a99ecc380c67c5e2e26f9d7a12255b599233d1acb78'
ASSET_PACKAGE = 'scattering_scene_assets_v1'
BOUNDARY = ('Whole-paper DESIGN only; zero validated runnable whole-paper tasks. '
    'Read-only author/evaluator inspection, not an actor context, acoustic controller, simulation or scientific reproduction. '
    'Source facts, authored requirements, finite synthetic checks and original illustrative geometry remain separate. '
    'Operation memberships do not create chronology; only exact source dependency and lifecycle contracts constrain order. '
    'Required receipts, outputs and completion evidence are obligations, never observed outcomes. HOLD_QUALIFICATION remains active.')
WARNINGS = ('Five experimental branches B01–B05 and four numerical-review extensions A01–A04 remain distinct. '
    'Three preparation/calibration records and one authored closeout are separate supporting scope. '
    'Fourteen symbolic operations, eleven scene groups and thirty-two anchors describe one paper-level design. '
    'The reported apparatus is a suspended torsion pendulum, not free-flight levitation. M1 and M2 have thirty cells; M3 has twenty; cell counts are not independent replicates. '
    'Source repeat counts remain unknown and prospective counts remain null. Eight ambiguities and sixteen unresolved-input groups stay explicit. '
    'Screen pixels, angles, displacement, force, modeled force per length and normalized force remain separate; reported trends are not success thresholds. '
    'Experimental 8 cm and self-guiding numerical 12 cm separations are distinct historical facts, never operating defaults. '
    'Requests do not prove completion or safe release. Current scoped calibration, sign and clock transformations, typed raw data, failed attempts and accepted supported custody remain required. '
    'Fabrication, acoustic/electrical actuation, laser calibration, source motion and safe release remain closed qualified services. '
    'Upstream review read eight main pages, eight SI pages, the media-description sheet and five tables with 152 entries. Three movies were decoded and 6/6/5 frames sampled, not continuously reviewed. '
    'Additional supporting data, code and CAD remain unread; bounded update checking is not exhaustive. This integration does not reread papers or prove mathematics. '
    'No physical execution, acoustic actuation, simulation, qualified motion, exposure-safety certification or scientific reproduction is supplied.')


def occurrence(identifier, filename, pointer):
    return {'type': 'op', 'id': identifier, 'meta': {'source_file': filename, 'source_pointer': pointer,
        'source_node': identifier, 'meaning': 'Exact authored task membership; not execution or inferred chronology'}}


def route(identifier, label, kind, detail, filename, pointer, members=()):
    nodes = []
    if members:
        nodes.append({'type': 'obligations', 'label': 'Exact operation membership; no adjacency chronology',
                      'ordered': False, 'children': list(members), 'meta': {'order': BOUNDARY}})
    nodes.append(contract('Exact source scope and obligations', detail, filename, pointer))
    return {'id': identifier, 'label': label, 'route_kind': kind, 'metadata_only': not bool(members),
            'nodes': nodes, 'basis': BOUNDARY, 'detail': clone(detail), 'source_file': filename,
            'source_pointer': pointer, 'navigation_basis': 'Authored inspection label; no added scientific branch, qualification or result'}


def projection(p):
    docs = {n.relative_to(p).as_posix(): read(p, n.relative_to(p).as_posix()) for n in sorted(p.rglob('*.json'))}
    ap = p.parent.parent / 'assets' / ASSET_PACKAGE
    assets = {n.relative_to(ap).as_posix(): read(ap, n.relative_to(ap).as_posix()) for n in sorted(ap.rglob('*.json'))}
    raw = docs['operations.json']['operations']; paper = docs['provenance.json']['paper']
    folder = '../../tasks/' + p.name + '/'; afolder = '../../assets/' + ASSET_PACKAGE + '/'
    operations = []
    for i, o in enumerate(raw):
        operations.append({'id': o['id'], 'title': o['name'], 'stage': o['station_id'], 'actions': [o['action']],
            'objects': {k: clone(o[k]) for k in ('asset_ids', 'anchor_ids')}, 'pre': o['precondition'],
            'post': absent('observed post-state'),
            'acceptance': {k: clone(o[k]) for k in ('required_receipt_types', 'required_outputs', 'completion_evidence', 'guard')},
            'recovery': o['on_failure'], 'sources': [],
            'unknowns': {'mapping': 'Exact branch blocking_unknowns and complete unknown ledger remain in context; no per-operation source mapping is invented.'},
            'provenance': {k: clone(o[k]) for k in ('origin', 'kind', 'action_interface', 'physical_execution_enabled', 'receipt_authentication')},
            'loop': None, 'detail': clone(o), 'source_file': 'operations.json', 'source_pointer': '/operations/' + str(i),
            'display_action_ownership': 'Original authored symbolic service/evidence boundary; no live device control.',
            'display_mapping_basis': 'Completion evidence, receipts and outputs are requirements, never observed post-state or success.'})
    f = {'id': 'scattering', 'label': 'Anomalous acoustic scattering', 'title': paper['title'], 'doi': paper['doi'], 'color': '#79bdcf',
         'family_scope': 'paper_level_design', 'family_scope_label': 'WHOLE-PAPER DESIGN',
         'source_commit': SOURCE_COMMIT, 'source_archive_sha256': TASK_ARCHIVE_SHA256, 'asset_archive_sha256': ASSET_ARCHIVE_SHA256,
         'source_folder': folder, 'source_link_mode': 'repository_relative_frozen_local_snapshot',
         'source_publication': 'Archive and per-file hashes identify provenance; remote publication is not asserted by these identifiers. The repository commit establishes publication status.',
         'status': BOUNDARY + ' ' + WARNINGS, 'source_warnings': WARNINGS,
         'visibility': 'author_evaluator_reference_only', 'actor_projection_implemented': False,
         'operations': operations, 'routes': [], 'evidence': {e['id']: clone(e) for e in docs['source_evidence.json']['facts']},
         'context': {**{context_key(name): clone(value) for name, value in docs.items()}, 'static_assets': clone(assets)},
         'dependencies': {'display_rule': BOUNDARY, **{name: clone(docs[name + '.json']) for name in
             ('workflow', 'material_and_sample_dependencies', 'lineage_contract', 'measurement_contract', 'failure_contract', 'station_contracts')}},
         'source_files': {name: {'url': folder + name, 'repository_path': 'tasks/' + p.name + '/' + name,
             'sha256': hashlib.sha256((p / name).read_bytes()).hexdigest()} for name in docs},
         'default_route': docs['STATUS.json']['physical_default'],
         'default_route_basis': 'Exact real-world default rendered as a metadata-only qualification hold; no operation or qualification is invented.',
         'asset_links': [], 'asset_boundary': 'Original editable static scene and rendered illustrations only. Geometry, anchors, dimensions and interfaces are illustrative and unqualified. No source-exact CAD, robot motion, physics, acoustic actuation or scientific measurement is supplied.'}
    f['source_files'].update({'static_assets/' + name: {'url': afolder + name, 'repository_path': 'assets/' + ASSET_PACKAGE + '/' + name,
        'sha256': hashlib.sha256((ap / name).read_bytes()).hexdigest()} for name in assets})
    for i, b in enumerate(docs['branches.json']['branches']):
        pointer = '/branches/' + str(i)
        f['routes'].append(route(b['id'], b['source_reported_kind'].upper().replace('_', ' ') + ' · ' + b['name'],
            b['source_reported_kind'], b, 'branches.json', pointer,
            [occurrence(oid, 'branches.json', pointer + '/operation_ids/' + str(j)) for j, oid in enumerate(b['operation_ids'])]))
    f['routes'].append(route('OPERATIONS_REFERENCE', 'COMPLETE OPERATION INVENTORY · dependencies remain authoritative',
        'operation_inventory', docs['operations.json'], 'operations.json', '',
        [occurrence(o['id'], 'operations.json', '/operations/' + str(i) + '/id') for i, o in enumerate(raw)]))
    for identifier, label, kind, filename in [
        ('CONTROLS_REFERENCE', 'CONTROLS AND REPEATS · no inferred independent n', 'controls_reference', 'controls_and_repeats.json'),
        ('FAILURE_REFERENCE', 'FAILED ATTEMPTS AND SAFE CUSTODY · no automatic retry', 'failure_reference', 'failure_contract.json'),
        ('BINDINGS_REFERENCE', 'STATIC ASSET BINDINGS · illustrative and unqualified', 'bindings_reference', 'shared_binding_contract.json'),
        (f['default_route'], 'DEFAULT QUALIFICATION HOLD · NO ACTUATION', 'qualification_hold', 'STATUS.json')]:
        f['routes'].append(route(identifier, label, kind, docs[filename], filename, ''))
    plan = docs['shared_binding_contract.json']
    f['summary_counts'] = {'source_scope_branches': len(docs['branches.json']['branches']), 'physical_experimental_branches': 5,
        'numerical_review_extensions': 4, 'preparation_calibration_branches': 3, 'authored_closeout_branches': 1,
        'authored_reference_views': 4, 'metadata_only_hold_views': 1, 'source_json_documents': len(docs), 'asset_json_documents': len(assets),
        'operation_templates': len(raw), 'source_evidence_entries': len(f['evidence']), 'source_ambiguities': len(docs['source_conflicts.json']['records']),
        'unresolved_input_groups': len(docs['unknowns.json']['unknowns']), 'controls': len(docs['controls_and_repeats.json']['controls']),
        'scene_groups': len(plan['asset_groups']), 'symbolic_anchors': len({a for b in plan['asset_groups'] for a in b['anchor_ids']}),
        'task_pinned_asset_hashes': len(docs['paired_asset_reference.json']['stable_scene_files']),
        'asset_pinned_task_hashes': len(assets['paired_task_core_reference.json']['files'])}
    for name in ['README.md', 'preview_01_overview.png', 'preview_02_preparation.png', 'preview_03_metrology.png']:
        f['asset_links'].append({'label': 'Original editable static 3D guide' if name == 'README.md' else 'Static render: ' + name.removesuffix('.png'),
            'path': 'assets/' + ASSET_PACKAGE + '/' + name, 'url': afolder + name, 'sha256': hashlib.sha256((ap / name).read_bytes()).hexdigest()})
    return f


def validate_projection(f, p):
    if json.dumps(f, sort_keys=True, ensure_ascii=False, allow_nan=False) != json.dumps(projection(p), sort_keys=True, ensure_ascii=False, allow_nan=False):
        raise ValueError('Scattering projection omitted, changed or invented a source contract or display boundary')
    ids = [o['id'] for o in f['operations']]
    if len(set(ids)) != 14 or len({r['id'] for r in f['routes']}) != len(f['routes']): raise ValueError('Duplicate or missing operation/route')
    ap = p.parent.parent / 'assets' / ASSET_PACKAGE
    pair = read(p, 'paired_asset_reference.json')
    if pair['scene_archive']['sha256'] != ASSET_ARCHIVE_SHA256: raise ValueError('Scene archive pin changed')
    for name, pin in pair['stable_scene_files'].items():
        data = (ap / name).read_bytes()
        if len(data) != pin['bytes'] or hashlib.sha256(data).hexdigest() != pin['sha256']: raise ValueError('Task-pinned asset changed: ' + name)
    ref = read(ap, 'paired_task_core_reference.json')
    if hashlib.sha256(json.dumps(ref['files'], sort_keys=True, separators=(',', ':')).encode()).hexdigest() != ref['semantic_core_sha256']:
        raise ValueError('Task semantic core digest changed')
    if ref['semantic_core_sha256'] != pair['task_semantic_core_sha256']: raise ValueError('Task/scene core identity mismatch')
    for pin in ref['files']:
        data = (p / pin['path']).read_bytes()
        if len(data) != pin['bytes'] or hashlib.sha256(data).hexdigest() != pin['sha256']: raise ValueError('Scene-pinned task changed: ' + pin['path'])
    if (p / 'shared_binding_contract.json').read_bytes() != (ap / 'asset_binding_contract.json').read_bytes(): raise ValueError('Shared bindings differ')
    return True


def adapt_scattering(p):
    f = projection(p); validate_projection(f, p); return f
