"""Lossless microsphere optical-imaging inspector; original static design only."""
import hashlib
import json
from pathlib import PurePosixPath
from paired_adapters import clone, read, context_key, contract, absent

PACKAGES = {'microsphere': 'microsphere_operations_v2'}
SOURCE_COMMIT = None
TASK_ARCHIVE_SHA256 = '93adc6a2111ce018a805287dde15726c62c7a7c60d32a73dff277f86a8cf725b'
ASSET_ARCHIVE_SHA256 = '5c85719de93a4a59679e5e04a41eaa9af3b592566d43ad713c075161cf6ca4eb'
ASSET_PACKAGE = 'microsphere_scene_assets_v1'
BOUNDARY = ('Whole-paper DESIGN only; zero validated runnable whole-paper tasks. '
    'Read-only author/evaluator inspection, not an actor context, instrument controller, optical simulation or scientific reproduction. '
    'Source facts, authored requirements, finite synthetic checks and original illustrative geometry remain separate. '
    'Operation memberships do not create chronology; only exact dependency, custody and lifecycle contracts constrain order. '
    'Required outputs and receipts remain obligations, never observed states. HOLD_QUALIFICATION remains active.')
WARNINGS = ('Thirteen authored stages R01–R13 and thirteen source-scope branches describe one paper-level design. '
    'Seven stations, nine original scene groups and thirty-three evidence-only anchors remain illustrative and unqualified. '
    'All sixteen qualification gaps remain held. SOURCE_SCALE actual-size context and SCHEMATIC_ENLARGEMENTS magnified illustrations stay separate; neither is qualified hardware CAD or optical evidence. '
    'The figure-backed 50 nm claim concerns gold/AAO transmission. Cross-mode 50 nm reflection and complex-shape transmission remain text-only source claims, not new measured outcomes. '
    'Star-film SbTe versus GeSbTe composition remains unresolved, and the star-panel sphere diameter is unreported. '
    'Blu-ray line/gap naming, experimental 20 nm versus modeled 40 nm gold, and physical SIL versus modeled geometry remain distinct. '
    'Physical 0.5 mm/80x and 2.5 mm/40x SIL controls are not fully matched pure-shape comparisons. '
    'Object, virtual, detector and SEM coordinate frames require separate calibration and registered lineage. '
    'Reported magnifications, failures and resolution claims are reference context, never generated measurements, acceptance thresholds or rewards. '
    'Repeated frames, multiple spheres and field counts do not establish independent specimen repeats; repeat counts and uncertainty budgets remain null. '
    'Uncoated baselines and coated/contact child states retain provenance; no identical restoration or historical acquisition chronology is assumed. '
    'SEM reference characterization, target preparation, sphere assembly/contact, optical acquisition and cleanup stay closed qualified services. '
    'Failure, rejected attempts, safe closeout and retained custody remain explicit; digital acceptance does not authenticate physical observations or authorize device operation. '
    'Upstream accepted source review read and visually inspected all six main and seven SI pages, four main and six SI figures; no digitization or independent optical-resolution validation occurred. '
    'No movie link was listed on the inspected record; no separate raw-data or source-code package was read or executed. '
    'The official source is free-to-read with 2011 Macmillan all rights reserved; no unrestricted reuse or CC license was established. '
    'Apache-2.0 applies only to original authored materials. No publisher PDFs, images, figure traces, source CAD, code or raw data are bundled. '
    'This integration does not reread publications, resolve source conflicts or reproduce science. No hardware control, new measurement, numerical rerun, physical execution or scientific reproduction is supplied.')
DEPENDENCY_DOCUMENTS = ('dependencies', 'material_and_sample_dependencies', 'preparation_routes', 'lineage_contract',
    'sample_custody', 'lifecycle_contract', 'failure_and_closeout', 'station_contracts', 'cross_device_measurements', 'analysis_contracts')


def occurrence(identifier, filename, pointer, membership=None, operation_pointer=None):
    meta = {'source_file': filename, 'source_pointer': pointer,
        'source_node': identifier if membership is None else membership,
        'meaning': 'Exact authored operation branch membership; not execution or inferred chronology'}
    if operation_pointer is not None: meta['operation_source_pointer'] = operation_pointer
    return {'type': 'op', 'id': identifier, 'meta': meta}


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
    raw = docs['operations.json']['operations']; paper = docs['provenance.json']['source']
    folder = '../../tasks/' + p.name + '/'; afolder = '../../assets/' + ASSET_PACKAGE + '/'
    operations = []
    for i, o in enumerate(raw):
        operations.append({'id': o['id'], 'title': o['name'], 'stage': o['station'], 'actions': [o['name']],
            'objects': {k: clone(o[k]) for k in ('asset_ids', 'anchor_ids')},
            'pre': {k: clone(o[k]) for k in ('depends_on', 'precondition')},
            'post': absent('observed post-state'),
            'acceptance': {k: clone(o[k]) for k in ('required_output', 'rule')},
            'recovery': {k: clone(o[k]) for k in ('failure', 'recovery')}, 'sources': [], 'unknowns': clone(o['unresolved_input_refs']),
            'provenance': {k: clone(o[k]) for k in ('kind', 'device_command_implemented', 'physical_execution_authority', 'actor_action')},
            'loop': None, 'detail': clone(o), 'source_file': 'operations.json', 'source_pointer': '/operations/' + str(i),
            'display_action_ownership': 'Exact authored operation name rendered as navigation; no live device control or additional command is supplied.',
            'display_mapping_basis': 'Required outputs and rules remain obligations, never observed post-state, authenticated receipts or scientific success.'})
    f = {'id': 'microsphere', 'label': 'Microsphere optical imaging', 'title': paper['title'], 'doi': paper['doi'], 'color': '#79becf',
         'family_scope': 'paper_level_design', 'family_scope_label': 'WHOLE-PAPER DESIGN',
         'source_commit': SOURCE_COMMIT, 'source_archive_sha256': TASK_ARCHIVE_SHA256, 'asset_archive_sha256': ASSET_ARCHIVE_SHA256,
         'source_folder': folder, 'source_link_mode': 'repository_relative_frozen_local_snapshot',
         'source_publication': 'Archive and per-file hashes identify provenance; remote publication is not asserted by these identifiers. The repository commit establishes publication status.',
         'status': BOUNDARY + ' ' + WARNINGS, 'source_warnings': WARNINGS,
         'visibility': 'author_evaluator_reference_only', 'actor_projection_implemented': False,
         'operations': operations, 'routes': [], 'evidence': {e['id']: clone(e) for e in docs['source_facts.json']['facts']},
         'context': {**{context_key(name): clone(value) for name, value in docs.items()}, 'static_assets': clone(assets)},
         'dependencies': {'display_rule': BOUNDARY, **{name: clone(docs[name + '.json']) for name in DEPENDENCY_DOCUMENTS}},
         'source_files': {name: {'url': folder + name, 'repository_path': 'tasks/' + p.name + '/' + name,
             'sha256': hashlib.sha256((p / name).read_bytes()).hexdigest()} for name in docs},
         'default_route': docs['shared_binding_contract.json']['default_state'],
         'default_route_basis': 'Exact task/scene default rendered as a metadata-only qualification hold; no operation or qualification is invented.',
         'asset_links': [], 'asset_boundary': 'Original editable static scene and three original rendered illustrations only. Actual-size SOURCE_SCALE objects and magnified SCHEMATIC_ENLARGEMENTS remain separate. Geometry, anchors, supports, dimensions and interfaces are illustrative and unqualified; rendered patterns never establish optical resolution. No source-exact CAD, qualified motion/contact, optical simulation, instrument operation or scientific measurement is supplied.'}
    f['source_files'].update({'static_assets/' + name: {'url': afolder + name, 'repository_path': 'assets/' + ASSET_PACKAGE + '/' + name,
        'sha256': hashlib.sha256((ap / name).read_bytes()).hexdigest()} for name in assets})
    for i, b in enumerate(docs['branches.json']['branches']):
        members = [occurrence(o['id'], 'operations.json', '/operations/' + str(j) + '/branch_ids/' + str(o['branch_ids'].index(b['id'])), b['id'], '/operations/' + str(j) + '/id')
                   for j, o in enumerate(raw) if b['id'] in o['branch_ids']]
        f['routes'].append(route(b['id'], b['id'] + ' · ' + b['name'], 'source_scope_branch', b, 'branches.json', '/branches/' + str(i), members))
    f['routes'].append(route('OPERATIONS_REFERENCE', 'COMPLETE STAGE INVENTORY · exact dependencies remain authoritative',
        'operation_inventory', docs['operations.json'], 'operations.json', '',
        [occurrence(o['id'], 'operations.json', '/operations/' + str(i) + '/id') for i, o in enumerate(raw)]))
    for identifier, label, kind, filename in [
        ('PREPARATION_REFERENCE', 'PREPARATION AND LINEAGE · closed qualified services', 'preparation_reference', 'preparation_routes.json'),
        ('CONTROLS_REFERENCE', 'CONTROLS AND REPEATS · no inferred independent n', 'controls_reference', 'controls_and_repeats.json'),
        ('FAILURE_REFERENCE', 'FAILED ATTEMPTS AND SAFE CLOSEOUT · preserve custody', 'failure_reference', 'failure_and_closeout.json'),
        ('BINDINGS_REFERENCE', 'STATIC ASSET BINDINGS · actual-size and magnified contexts separate', 'bindings_reference', 'shared_binding_contract.json'),
        ('OUTCOMES_REFERENCE', 'AUTHOR-REPORTED OUTCOMES · never new measurement telemetry', 'source_outcomes_reference', 'source_outcomes_reference.json'),
        (f['default_route'], 'DEFAULT QUALIFICATION HOLD · NO INSTRUMENT OPERATION', 'qualification_hold', 'unknown_inputs.json')]:
        f['routes'].append(route(identifier, label, kind, docs[filename], filename, ''))
    binding = docs['shared_binding_contract.json']
    f['summary_counts'] = {'source_scope_branches': len(docs['branches.json']['branches']),
        'authored_reference_views': 6, 'metadata_only_hold_views': 1, 'source_json_documents': len(docs), 'asset_json_documents': len(assets),
        'operation_templates': len(raw), 'stations': len(docs['station_contracts.json']['stations']),
        'source_evidence_entries': len(f['evidence']), 'source_ambiguities': len(docs['source_conflicts.json']['items']),
        'reported_outcomes': len(docs['source_outcomes_reference.json']['outcomes']),
        'unresolved_input_groups': len(docs['unknown_inputs.json']['unknowns']), 'controls': len(docs['controls_and_repeats.json']['reported_controls']),
        'scene_groups': len(binding['assets']), 'symbolic_anchors': len({a['anchor_id'] for b in binding['assets'] for a in b['anchors']}),
        'task_core_files': len(docs['task_core_manifest.json']['files']), 'asset_core_files': len(assets['scene_core_manifest.json']['files'])}
    for name in ['README.md', 'previews/preview_01_overview.png', 'previews/preview_02_targets.png', 'previews/preview_03_services.png']:
        f['asset_links'].append({'label': 'Original editable static 3D guide' if name == 'README.md' else 'Static render: ' + name.split('/')[-1].removesuffix('.png'),
            'path': 'assets/' + ASSET_PACKAGE + '/' + name, 'url': afolder + name, 'sha256': hashlib.sha256((ap / name).read_bytes()).hexdigest()})
    return f


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def validate_projection(f, p):
    if canonical(f) != canonical(projection(p)):
        raise ValueError('Microsphere projection omitted, changed or invented a source contract or display boundary')
    if len({o['id'] for o in f['operations']}) != 13 or len({r['id'] for r in f['routes']}) != 20:
        raise ValueError('Duplicate or missing operation/route')
    ap = p.parent.parent / 'assets' / ASSET_PACKAGE
    pair = read(p, 'asset_binding_plan.json'); ref = read(ap, 'paired_task_reference.json')
    for base, filename, pin in [(p, 'task_core_manifest.json', 'task_core_sha256'), (ap, 'scene_core_manifest.json', 'scene_core_sha256')]:
        core = read(base, filename)
        records = core['files']
        if records != sorted(records, key=lambda r: r['path']) or len({r['path'] for r in records}) != len(records):
            raise ValueError('Invalid paired core inventory')
        digest = hashlib.sha256(canonical(records)).hexdigest()
        if digest != core['core_sha256'] or digest != pair[pin] or digest != ref[pin]:
            raise ValueError('Reciprocal semantic core digest changed')
        for item in records:
            name = item['path']; path = PurePosixPath(name); local = base / name
            if path.is_absolute() or str(path) != name or any(s in ('', '.', '..') for s in path.parts) or '\\' in name:
                raise ValueError('Unsafe core path')
            if local.is_symlink() or not local.is_file() or not local.resolve().is_relative_to(base.resolve()):
                raise ValueError('Invalid core file')
            data = local.read_bytes()
            if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
                raise ValueError('Paired core file changed: ' + name)
    for name, aname in [('shared_binding_contract.json', 'shared_binding_contract.json'),
                        ('task_core_manifest.json', 'paired_task_core_manifest.json'),
                        ('paired_scene_core_manifest.json', 'scene_core_manifest.json')]:
        if (p / name).read_bytes() != (ap / aname).read_bytes(): raise ValueError('Shared bytes differ: ' + name)
    binding = read(p, 'shared_binding_contract.json')
    if hashlib.sha256((p / 'shared_binding_contract.json').read_bytes()).hexdigest() != ref['shared_binding_contract_sha256']:
        raise ValueError('Shared binding byte pin changed')
    if hashlib.sha256(canonical(binding)).hexdigest() != pair['semantic_core_sha256']:
        raise ValueError('Shared semantic pin changed')
    by_id = {r['route_id']: r for r in binding['route_bindings']}
    for o in f['operations']:
        raw = o['detail']; b = by_id[o['id']]
        if any(raw[k] != b[k] for k in ('asset_ids', 'branch_ids')) or [raw['station']] != b['station_ids'] or raw['anchor_ids'] != b['target_anchor_ids']:
            raise ValueError('Operation binding changed')
    return True


def adapt_microsphere(p):
    f = projection(p); validate_projection(f, p); return f
