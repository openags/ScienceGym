"""Lossless frictional fluid-design inspector; original static design only."""
import hashlib
import json
from pathlib import PurePosixPath
from paired_adapters import clone, read, context_key, contract, absent

PACKAGES = {'frictional': 'frictional_operations_v2'}
SOURCE_COMMIT = None
TASK_ARCHIVE_SHA256 = '5de7cb60d93d5bacf5323b80df57c699b35a4e26ea0e6e0a285b69fd90370b7f'
ASSET_ARCHIVE_SHA256 = '625f08857d9c32babeb91214a5a9c44258a98625446eec3f82b8f9d45d1570a0'
ASSET_PACKAGE = 'frictional_scene_assets_v1'
BOUNDARY = ('Whole-paper DESIGN only; zero validated runnable whole-paper tasks. '
    'Read-only author/evaluator inspection, not an actor context, pressure operating procedure, hardware controller, fluid simulation or scientific reproduction. '
    'Source facts, authored requirements, finite synthetic checks and original illustrative geometry remain separate. '
    'Operation memberships do not create chronology; only exact dependency, custody and lifecycle contracts constrain order. '
    'Required outputs and receipts remain obligations, never observed states. HOLD_QUALIFICATION remains active.')
WARNINGS = ('Twelve authored evidence routes R01–R12 and nine source-scope branches describe one paper-level design. '
    'Six stations, eight original scene groups and thirty-two evidence-only anchors remain illustrative and unqualified. '
    'All twenty qualification holds remain unresolved. SOURCE_SCALE dimensions are source context, never qualified apparatus, pressure ratings or motion targets. '
    'Coral-rate C01 retains 0.1 versus 1.0 ml/min with each provenance; no rate is silently selected or assigned to an operating command. '
    'The Boyle-law C02 intermediate-sign inconsistency remains a reviewer inference, not a published correction or repaired numerical model. '
    'Viscosity-rate scaling B06 and high-filling granular fracture B07 remain required separate branches with unresolved preparation and repeat evidence. '
    'Granular fracture never means breaking the glass cell. B08 borrowed porous-medium comparisons remain attributed external context; B09 analytical context is unimplemented. '
    'Normalized phi is not absolute volume fraction; reservoir volume is not total compliance; pump rate is not instantaneous burst flow; movie file time is not experiment time. '
    'Sparse illustrated conditions are not a complete factorial schedule, and twenty local width measurements are not twenty independent preparations. '
    'Theoretical lower bounds, observed crossover, sensitivity and measurement uncertainty remain distinct; source outcomes never become measured results, success thresholds or rewards. '
    'Material, dispersion, aliquot, cell, loaded/settled/spent child state, run, clock, calibration and service-job identities retain exact custody. No reset or same-cell microstate restoration is assumed. '
    'R11 is repeatable per registered job, including failures, and may precede aggregate R08–R10 while other jobs remain open. R12 requires all route dispositions and every job closeout; there is no global R11 token. '
    'Contained preparation, cell qualification, pressure measurement, safe release and cleanup remain closed qualified services. Hash checks neither authenticate service receipts nor inspect external raw records. '
    'Upstream accepted source review covered eight final pages, five figures, nine equations and both movie descriptions. Both movies were decoded, with nine and eleven sampled file-time frames inspected, not continuously or against raw experiment time. '
    'No raw numeric dataset or external cited references were reviewed. This integration does not reread publications, resolve conflicts or reproduce science. '
    'Source material retains CC BY-NC-SA 3.0 Unported terms; third-party Figure 5 imagery retains separate provenance and rights. Apache-2.0 applies only to original authored materials. '
    'No publisher PDF, source text/figure, movie/frame, borrowed photograph, source CAD, source code or raw dataset is bundled. No hardware control, new measurement, numerical rerun, physical execution or scientific reproduction is supplied.')
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
    raw = docs['operations.json']['operations']; paper = docs['provenance.json']['paper']
    folder = '../../tasks/' + p.name + '/'; afolder = '../../assets/' + ASSET_PACKAGE + '/'
    operations = []
    for i, o in enumerate(raw):
        operations.append({'id': o['id'], 'title': o['name'], 'stage': o['station'], 'actions': [o['name']],
            'objects': {k: clone(o[k]) for k in ('asset_ids', 'anchor_ids')},
            'pre': {k: clone(o[k]) for k in ('depends_on', 'dependency_rule') if k in o},
            'post': absent('observed post-state'),
            'acceptance': {k: clone(o[k]) for k in ('required_output', 'gate')},
            'recovery': absent('per-operation recovery; inspect exact family failure_and_closeout and lifecycle contracts'), 'sources': [], 'unknowns': clone(o['unknown_refs']),
            'provenance': {k: clone(o[k]) for k in ('status_semantics', 'device_command_implemented', 'physical_execution_authority', 'actor_action')},
            'loop': None, 'detail': clone(o), 'source_file': 'operations.json', 'source_pointer': '/operations/' + str(i),
            'display_action_ownership': 'Exact authored operation name rendered as navigation; no live device control or additional command is supplied.',
            'display_mapping_basis': 'Required outputs and rules remain obligations, never observed post-state, authenticated receipts or scientific success.'})
    f = {'id': 'frictional', 'label': 'Frictional fluid dynamics', 'title': paper['title'], 'doi': paper['doi'], 'color': '#d1ad75',
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
         'default_route': docs['lifecycle_contract.json']['default'],
         'default_route_basis': 'Exact task lifecycle default rendered as a metadata-only qualification hold; no operation or qualification is invented.',
         'asset_links': [], 'asset_boundary': 'Original editable static scene and three original rendered illustrations only. SOURCE_SCALE cell dimensions retain reported context, not qualified pressure-cell CAD. Generic supports, enclosed services and five morphology tokens are original illustrative proxies. Anchors are evidence selectors, never physical motion targets. No fluid simulation, pressure operating procedure, observed pattern or scientific measurement is supplied.'}
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
        ('BINDINGS_REFERENCE', 'STATIC ASSET BINDINGS · evidence anchors, not pressure-qualified hardware', 'bindings_reference', 'shared_binding_contract.json'),
        ('OUTCOMES_REFERENCE', 'AUTHOR-REPORTED OUTCOMES · never new measurement telemetry', 'source_outcomes_reference', 'source_outcomes_reference.json'),
        (f['default_route'], 'DEFAULT QUALIFICATION HOLD · NO PRESSURE OR HARDWARE OPERATION', 'qualification_hold', 'unknown_inputs.json')]:
        f['routes'].append(route(identifier, label, kind, docs[filename], filename, ''))
    binding = docs['shared_binding_contract.json']
    f['summary_counts'] = {'source_scope_branches': len(docs['branches.json']['branches']),
        'authored_reference_views': 6, 'metadata_only_hold_views': 1, 'source_json_documents': len(docs), 'asset_json_documents': len(assets),
        'operation_templates': len(raw), 'stations': len(docs['station_contracts.json']['stations']),
        'source_evidence_entries': len(f['evidence']), 'source_ambiguities': len(docs['source_conflicts.json']['conflicts_and_extraction_hazards']),
        'reported_outcomes': len(docs['source_outcomes_reference.json']['outcomes']),
        'unresolved_input_groups': len(docs['unknown_inputs.json']['unknowns']), 'controls': len(docs['controls_and_repeats.json']['reported']),
        'scene_groups': len(binding['asset_groups']), 'symbolic_anchors': len({a['anchor_id'] for a in binding['anchors']}),
        'task_core_files': len(docs['task_core_manifest.json']['files']), 'asset_core_files': len(assets['scene_core_manifest.json']['files'])}
    for name in ['README.md', 'previews/preview_01_overview.png', 'previews/preview_02_closed_service.png', 'previews/preview_03_evidence.png']:
        f['asset_links'].append({'label': 'Original editable static 3D guide' if name == 'README.md' else 'Static render: ' + name.split('/')[-1].removesuffix('.png'),
            'path': 'assets/' + ASSET_PACKAGE + '/' + name, 'url': afolder + name, 'sha256': hashlib.sha256((ap / name).read_bytes()).hexdigest()})
    return f


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def validate_projection(f, p):
    if canonical(f) != canonical(projection(p)):
        raise ValueError('Frictional projection omitted, changed or invented a source contract or display boundary')
    if len({o['id'] for o in f['operations']}) != 12 or len({r['id'] for r in f['routes']}) != 16:
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
                        ('paired_scene_core_manifest.json', 'scene_core_manifest.json'),
                        ('semantic_core.json', 'semantic_core.json'), ('scene_task_contract.json', 'shared_binding_contract.json')]:
        if (p / name).read_bytes() != (ap / aname).read_bytes(): raise ValueError('Shared bytes differ: ' + name)
    binding = read(p, 'shared_binding_contract.json')
    semantic = read(p, 'semantic_core.json')
    if hashlib.sha256((p / 'semantic_core.json').read_bytes()).hexdigest() != ref['semantic_core_file_sha256']:
        raise ValueError('Semantic core byte pin changed')
    if hashlib.sha256(canonical(binding)).hexdigest() != semantic['shared_binding_contract_sha256']:
        raise ValueError('Shared binding semantic pin changed')
    if hashlib.sha256(canonical(binding)).hexdigest() != pair['semantic_core_sha256']:
        raise ValueError('Shared semantic pin changed')
    by_id = {r['route_id']: r for r in binding['route_bindings']}
    for o in f['operations']:
        raw = o['detail']; b = by_id[o['id']]
        if any(raw[k] != b[k] for k in ('asset_ids', 'branch_ids', 'depends_on')) or [raw['station']] != b['station_ids'] or raw['anchor_ids'] != b['anchor_ids']:
            raise ValueError('Operation binding changed')
    return True


def adapt_frictional(p):
    f = projection(p); validate_projection(f, p); return f
