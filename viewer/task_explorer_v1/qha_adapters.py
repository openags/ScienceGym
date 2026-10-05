"""Lossless graphene quantum Hall array inspector; original static design only."""
import hashlib
import json
from paired_adapters import clone, read, context_key, contract, absent

PACKAGES = {'qha': 'qha_operations_v2'}
SOURCE_COMMIT = None
TASK_ARCHIVE_SHA256 = '511c17d13242c9b063157a927559fbeb049b0830234ec5dd83fa3cd3a8406d31'
ASSET_ARCHIVE_SHA256 = 'f9aad46761b8f422fccf19009038b282d3aefd5f11b6905d7502ca7a06e87b9a'
ASSET_PACKAGE = 'qha_scene_assets_v1'
BOUNDARY = ('Whole-paper DESIGN only; zero validated runnable whole-paper tasks. '
    'Read-only author/evaluator inspection, not an actor context, instrument controller, simulation or scientific reproduction. '
    'Source facts, authored requirements, finite synthetic checks and original illustrative geometry remain separate. '
    'Operation memberships do not create chronology; only exact dependency and lifecycle contracts constrain order. '
    'Required receipts and completion evidence remain obligations, never observed states. HOLD_QUALIFICATION remains active.')
WARNINGS = ('Fifteen authored stages R00–R14 and eleven coverage branches describe one paper-level design. '
    'Eleven original scene groups and thirty-two symbolic anchors are illustrative and unqualified. '
    'Each 118-element parallel subarray has nominal resistance R_K/236, approximately 109 ohm. '
    'The whole 236-element device connects two subarrays in series, R_K/118, approximately 219 ohm. '
    'Subarrays, the whole device, a separate Hall bar and external references must retain separate identities. '
    'Twenty-nine source facts, eighteen ambiguities and fourteen author-reported outcomes are reference material, never generated measurement telemetry, actor reward or success thresholds. '
    'Twenty unresolved-input groups, fourteen controls, null repeat counts and null planned conditions remain explicit. '
    'The five-edge comparison graph is distinct from acquired edges, which may remain empty, partial, failed or held. '
    'Disputed loop algebra and Eq. 1 remain unresolved; pooled precision, Allan-limited per-set uncertainty and standard offsets are distinct. '
    'R09 nonquantizing controls remain required design coverage without requiring unsafe acquisition. R10/R11 optional acquisition stays separate from design coverage. '
    'R14 joins every actually started service job after R03, including partial failures, independently of analysis success. '
    'Microfabrication, cryogenics, magnetic fields, electrical work and precision instruments remain closed qualified services. '
    'Source ranges and reported maxima are historical facts, never operating defaults. '
    'Upstream review read and visually inspected nine main pages and four SI pages, with all main-table cells. '
    'Raw data, source code, CAD and optional peer review remain unread. No video was listed in the inspected technical inventory. '
    'This integration does not reread publications, recompute source results or resolve scientific inconsistencies. '
    'No physical execution, hardware control, electrical or physics simulation, qualified motion, new scientific measurements or scientific reproduction is supplied.')


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
    raw = docs['operations.json']['operations']; paper = docs['source_packet_reference.json']['scientific_record']
    folder = '../../tasks/' + p.name + '/'; afolder = '../../assets/' + ASSET_PACKAGE + '/'
    operations = []
    for i, o in enumerate(raw):
        operations.append({'id': o['id'], 'title': o['name'], 'stage': ', '.join(o['stations']), 'actions': [o['action']],
            'objects': {k: clone(o[k]) for k in ('asset_ids', 'anchor_ids')},
            'pre': {'depends_on': clone(o['depends_on']), 'guards': clone(o['guards'])},
            'post': absent('observed post-state'),
            'acceptance': {k: clone(o[k]) for k in ('required_evidence', 'completion')},
            'recovery': o['failure_closeout'], 'sources': [], 'unknowns': clone(o['unresolved_inputs']),
            'provenance': {k: clone(o[k]) for k in ('origin', 'kind', 'action_interface', 'physical_execution_enabled', 'receipt_authentication')},
            'loop': None, 'detail': clone(o), 'source_file': 'operations.json', 'source_pointer': '/operations/' + str(i),
            'display_action_ownership': 'Original authored symbolic service/evidence boundary; no live device control.',
            'display_mapping_basis': 'Evidence and completion fields are requirements, never observed post-state or success.'})
    f = {'id': 'qha', 'label': 'Graphene quantum Hall arrays', 'title': paper['title'], 'doi': paper['doi'], 'color': '#8bc8b4',
         'family_scope': 'paper_level_design', 'family_scope_label': 'WHOLE-PAPER DESIGN',
         'source_commit': SOURCE_COMMIT, 'source_archive_sha256': TASK_ARCHIVE_SHA256, 'asset_archive_sha256': ASSET_ARCHIVE_SHA256,
         'source_folder': folder, 'source_link_mode': 'repository_relative_frozen_local_snapshot',
         'source_publication': 'Archive and per-file hashes identify provenance; remote publication is not asserted by these identifiers. The repository commit establishes publication status.',
         'status': BOUNDARY + ' ' + WARNINGS, 'source_warnings': WARNINGS,
         'visibility': 'author_evaluator_reference_only', 'actor_projection_implemented': False,
         'operations': operations, 'routes': [], 'evidence': {e['id']: clone(e) for e in docs['source_facts.json']['facts']},
         'context': {**{context_key(name): clone(value) for name, value in docs.items()}, 'static_assets': clone(assets)},
         'dependencies': {'display_rule': BOUNDARY, **{name: clone(docs[name + '.json']) for name in
             ('workflow', 'material_and_sample_dependencies', 'lineage_contract', 'measurement_contract', 'failure_and_closeout', 'station_contracts', 'identity_contract', 'device_lease_contract')}},
         'source_files': {name: {'url': folder + name, 'repository_path': 'tasks/' + p.name + '/' + name,
             'sha256': hashlib.sha256((p / name).read_bytes()).hexdigest()} for name in docs},
         'default_route': docs['release_boundary.json']['physical_default'],
         'default_route_basis': 'Exact real-world default rendered as a metadata-only qualification hold; no operation or qualification is invented.',
         'asset_links': [], 'asset_boundary': 'Original editable static scene and rendered illustrations only. Geometry, anchors, dimensions and interfaces are illustrative and unqualified. No source-exact CAD, robot motion, electrical or physics simulation, instrument operation or scientific measurement is supplied.'}
    f['source_files'].update({'static_assets/' + name: {'url': afolder + name, 'repository_path': 'assets/' + ASSET_PACKAGE + '/' + name,
        'sha256': hashlib.sha256((ap / name).read_bytes()).hexdigest()} for name in assets})
    for i, b in enumerate(docs['branches.json']['branches']):
        pointer = '/branches/' + str(i)
        f['routes'].append(route(b['id'], b['id'] + ' · ' + b['purpose'].replace('_', ' '),
            'authored_coverage_branch', b, 'branches.json', pointer,
            [occurrence(oid, 'branches.json', pointer + '/operations/' + str(j)) for j, oid in enumerate(b['operations'])]))
    f['routes'].append(route('OPERATIONS_REFERENCE', 'COMPLETE STAGE INVENTORY · exact dependencies remain authoritative',
        'operation_inventory', docs['operations.json'], 'operations.json', '',
        [occurrence(o['id'], 'operations.json', '/operations/' + str(i) + '/id') for i, o in enumerate(raw)]))
    for identifier, label, kind, filename in [
        ('CONTROLS_REFERENCE', 'CONTROLS AND REPEATS · no inferred independent n', 'controls_reference', 'controls_and_repeats.json'),
        ('FAILURE_REFERENCE', 'FAILED ATTEMPTS AND SAFE CLOSEOUT · all actually started jobs', 'failure_reference', 'failure_and_closeout.json'),
        ('BINDINGS_REFERENCE', 'STATIC ASSET BINDINGS · illustrative and unqualified', 'bindings_reference', 'shared_binding_contract.json'),
        ('OUTCOMES_REFERENCE', 'AUTHOR-REPORTED OUTCOMES · never new measurement telemetry', 'source_outcomes_reference', 'source_outcomes_reference.json'),
        (f['default_route'], 'DEFAULT QUALIFICATION HOLD · NO INSTRUMENT OPERATION', 'qualification_hold', 'release_boundary.json')]:
        f['routes'].append(route(identifier, label, kind, docs[filename], filename, ''))
    plan = docs['shared_binding_contract.json']
    f['summary_counts'] = {'authored_coverage_branches': len(docs['branches.json']['branches']),
        'authored_reference_views': 5, 'metadata_only_hold_views': 1, 'source_json_documents': len(docs), 'asset_json_documents': len(assets),
        'operation_templates': len(raw), 'source_evidence_entries': len(f['evidence']), 'source_ambiguities': len(docs['source_conflicts.json']['items']),
        'reported_outcomes': len(docs['source_outcomes_reference.json']['outcomes']),
        'unresolved_input_groups': len(docs['unknown_inputs.json']['items']), 'controls': len(docs['controls_and_repeats.json']['controls']),
        'scene_groups': len(plan['assets']), 'symbolic_anchors': len({a['anchor_id'] for b in plan['assets'] for a in b['anchors']}),
        'task_core_files': len(docs['task_semantic_core_manifest.json']['files']), 'asset_core_files': len(assets['scene_core_manifest.json']['files'])}
    for name in ['README.md', 'previews/preview_01_overview.png', 'previews/preview_02_specimen.png', 'previews/preview_03_services.png']:
        f['asset_links'].append({'label': 'Original editable static 3D guide' if name == 'README.md' else 'Static render: ' + name.split('/')[-1].removesuffix('.png'),
            'path': 'assets/' + ASSET_PACKAGE + '/' + name, 'url': afolder + name, 'sha256': hashlib.sha256((ap / name).read_bytes()).hexdigest()})
    return f


def validate_projection(f, p):
    if json.dumps(f, sort_keys=True, ensure_ascii=False, allow_nan=False) != json.dumps(projection(p), sort_keys=True, ensure_ascii=False, allow_nan=False):
        raise ValueError('QHA projection omitted, changed or invented a source contract or display boundary')
    if len({o['id'] for o in f['operations']}) != 15 or len({r['id'] for r in f['routes']}) != len(f['routes']):
        raise ValueError('Duplicate or missing operation/route')
    ap = p.parent.parent / 'assets' / ASSET_PACKAGE
    pair = read(p, 'paired_asset_reference.json'); ref = read(ap, 'paired_task_reference.json')
    if pair['asset_archive']['sha256'] != ASSET_ARCHIVE_SHA256: raise ValueError('Scene archive pin changed')
    for base, filename, pin in [(p, 'task_semantic_core_manifest.json', 'task_core_sha256'), (ap, 'scene_core_manifest.json', 'asset_core_sha256')]:
        core = read(base, filename)
        digest = hashlib.sha256(json.dumps(core['files'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        if digest != core.get('core_sha256', core.get('semantic_core_sha256')) or digest != pair[pin] or digest != ref[pin]:
            raise ValueError('Reciprocal semantic core digest changed')
        for item in core['files']:
            name = item.get('path', item.get('file')); data = (base / name).read_bytes()
            if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']: raise ValueError('Paired core file changed: ' + name)
    for name, aname in [('shared_binding_contract.json', 'shared_binding_contract.json'), ('task_semantic_core_manifest.json', 'paired_task_core_manifest.json')]:
        if (p / name).read_bytes() != (ap / aname).read_bytes(): raise ValueError('Shared bytes differ: ' + name)
    for key, name in [('task_core_manifest_sha256', 'task_semantic_core_manifest.json'), ('shared_contract_sha256', 'shared_binding_contract.json')]:
        if hashlib.sha256((p / name).read_bytes()).hexdigest() != pair[key] or pair[key] != ref[key]: raise ValueError('Shared pin mismatch')
    return True


def adapt_qha(p):
    f = projection(p); validate_projection(f, p); return f
