"""Lossless thermal meta-device inspection; original static design, no heat flow."""
import hashlib
import json
from paired_adapters import clone, read, context_key, contract, absent

PACKAGES = {'thermalmeta': 'thermalmeta_operations_v2'}
SOURCE_COMMIT = None
TASK_ARCHIVE_SHA256 = 'ab5092829fdabb3beaf3bd9a3d48901fba50c3fade5bab586bccc135a795886e'
ASSET_ARCHIVE_SHA256 = '7652f8cac76f27f1ce9d1f7f8d3f22bf73b0950cd685bd96962f48113be1e8e9'
ASSET_PACKAGE = 'thermalmeta_scene_assets_v1'
BOUNDARY = ('Whole-paper DESIGN only; zero validated runnable whole-paper tasks. '
    'Read-only author/evaluator inspection, not an actor context, controller, numerical solver or physical simulation. '
    'Source facts, authored requirements, finite symbolic tests and original illustrative geometry stay separate. '
    'Unordered coverage membership does not create chronology. Exact dependency, loop, failure and custody contracts remain authoritative. '
    'Required outputs and receipts are obligations, never observed outcomes; HOLD_UNQUALIFIED remains active.')
WARNINGS = ('Twenty authored stages P01–P20 describe one paper-level design. Twelve coverage families and twelve child scopes remain distinct. '
    'Three physical reference device families, CLOAK, ROTATOR45 and CONCENTRATOR18, each have X/Y condition views. '
    'These six cells and static views are not six independent specimens; source independent and technical counts remain unknown. '
    'B01–B04 retain reported experimental/media scope; B05–B10 and their children retain analytical/numerical source scope with no execution. '
    'B11/B12 are authored controls/reliability, not newly claimed source experiments. '
    'Nine source conflicts and thirteen unresolved-input groups remain held. The 2-norm versus squared-error ambiguity, Eq.16 residual index, '
    'coarsest cloak label 3.0 versus curve endpoint 2.5, and physical-unit/absolute-flux uncertainties are not silently repaired. '
    'The source method mixes analytical and iterative numerical elements. No optimizer, FEM solver or metric computation is implemented. '
    'Fifteen source facts and all reported experimental/numerical outcomes are reference material, never measured episode telemetry, rewards or success thresholds. '
    'K1/R1/C1 to X and K2/R2/C2 to Y are authored visual selectors; only the parallel/transverse profile relation is source-reported. '
    'A reported 37-degree-Celsius boundary and 45-minute interval are historical context, not commands or safe-release criteria. '
    'Preparation remains a per-specimen chain; supplier lots and common jobs never replace family-specific design, lattice, intermediate and final-specimen parents. '
    'Six repeat/reorientation/rework/control/next-preparation loops remain unexpanded and require approved plans plus safe release. '
    'Every powered failure or stop at P11–P14 routes to P15; indeterminate release retains SERVICE_CUSTODY_HOLD. Administrative closeout cannot release custody or claim success. '
    'Fabrication, casting, thermal, wet and electrical work stay closed qualified services. Nominal source dimensions and original illustrative shapes do not qualify geometry, grasps or robot motion. '
    'Upstream review covered ten main pages, twelve SI pages, five main and seven SI figures, nine SI notes and six sampled frames per movie across three decoded movies. '
    'Movies were not continuously reviewed or calibrated to raw acquisition time. Zenodo README was read; matrices, source code, raw experimental data and optional peer review remain unread. '
    'This integration does not reread publications, recompute results or reproduce science. No heat-flow telemetry, new scientific measurement or physical execution is supplied.')


def occurrence(identifier, filename, pointer, membership=None):
    meta = {'source_file': filename, 'source_pointer': pointer, 'source_node': identifier,
            'meaning': 'Exact authored coverage membership; no execution or adjacency chronology'}
    if membership is not None: meta['coverage_record'] = clone(membership)
    return {'type': 'op', 'id': identifier, 'meta': meta}


def route(identifier, label, kind, detail, filename, pointer, members=()):
    nodes = []
    if members:
        nodes.append({'type': 'obligations', 'label': 'Exact coverage membership; no adjacency chronology',
                      'ordered': False, 'children': list(members), 'meta': {'order': BOUNDARY}})
    nodes.append(contract('Exact source scope and obligations', detail, filename, pointer))
    return {'id': identifier, 'label': label, 'route_kind': kind, 'metadata_only': not bool(members),
            'nodes': nodes, 'basis': BOUNDARY, 'detail': clone(detail), 'source_file': filename,
            'source_pointer': pointer, 'navigation_basis': 'Authored inspection label; no added scientific branch, qualification or result'}


def projection(p):
    docs = {n.relative_to(p).as_posix(): read(p, n.relative_to(p).as_posix()) for n in sorted(p.rglob('*.json'))}
    ap = p.parent.parent / 'assets' / ASSET_PACKAGE
    assets = {n.relative_to(ap).as_posix(): read(ap, n.relative_to(ap).as_posix()) for n in sorted(ap.rglob('*.json'))}
    raw = docs['operations.json']['stages']; paper = docs['task.json']['paper']; binding = docs['scene_binding_contract.json']
    folder = '../../tasks/' + p.name + '/'; afolder = '../../assets/' + ASSET_PACKAGE + '/'
    operations = []
    for i, o in enumerate(raw):
        operations.append({'id': o['id'], 'title': o['title'], 'stage': o['station_id'], 'actions': [o['title']],
            'objects': {k: clone(o[k]) for k in ('input', 'scene_asset_ids', 'scene_anchor_id')},
            'pre': {'depends_on': clone(o['depends_on']), 'gate': o['gate']},
            'post': absent('observed post-state'),
            'acceptance': {k: clone(o[k]) for k in ('output', 'required_receipt_fields')},
            'recovery': o['failure_route'], 'sources': [],
            'unknowns': {'mapping': 'All source conflicts and unresolved inputs remain in exact context; no per-stage unknown mapping is invented.'},
            'provenance': {k: clone(o[k]) for k in ('role', 'status', 'evidence_class', 'route_id', 'source_proposal_id', 'execution_surface', 'commands_enabled')},
            'loop': None, 'detail': clone(o), 'source_file': 'operations.json', 'source_pointer': '/stages/' + str(i),
            'display_action_ownership': 'Exact authored stage title rendered as navigation; no additional action or hardware command is invented.',
            'display_mapping_basis': 'Source input, gate, required output and receipt fields remain obligations, never observed post-state or success.'})
    f = {'id': 'thermalmeta', 'label': 'Thermal meta-devices', 'title': paper['title'], 'doi': paper['doi'], 'color': '#dfb07a',
         'family_scope': 'paper_level_design', 'family_scope_label': 'WHOLE-PAPER DESIGN',
         'source_commit': SOURCE_COMMIT, 'source_archive_sha256': TASK_ARCHIVE_SHA256, 'asset_archive_sha256': ASSET_ARCHIVE_SHA256,
         'source_folder': folder, 'source_link_mode': 'repository_relative_frozen_local_snapshot',
         'source_publication': 'Archive and per-file hashes identify provenance; remote publication is not asserted by these identifiers. The repository commit establishes publication status.',
         'status': BOUNDARY + ' ' + WARNINGS, 'source_warnings': WARNINGS,
         'visibility': 'author_evaluator_reference_only', 'actor_projection_implemented': False,
         'operations': operations, 'routes': [], 'evidence': {e['id']: clone(e) for e in docs['source_facts.json']['facts']},
         'context': {**{context_key(name): clone(value) for name, value in docs.items()}, 'static_assets': clone(assets)},
         'dependencies': {'display_rule': BOUNDARY, **{name: clone(docs[name + '.json']) for name in
             ('operations', 'coverage_matrix', 'lifecycle_contract', 'preparation_contract', 'lineage_contract', 'sample_contract', 'observation_contract', 'analysis_contract', 'failure_catalog')}},
         'source_files': {name: {'url': folder + name, 'repository_path': 'tasks/' + p.name + '/' + name,
             'sha256': hashlib.sha256((p / name).read_bytes()).hexdigest()} for name in docs},
         'default_route': binding['default_state'],
         'default_route_basis': 'Exact scene/task default rendered as a metadata-only unqualified hold; no qualification or physical operation is invented.',
         'asset_links': [], 'asset_boundary': 'Original editable static scene and three rendered illustrations only. Geometry, anchors, carrier/fixture shapes and interfaces remain illustrative and unqualified. No source-exact CAD, robot motion, heating, heat-flow telemetry, physical simulation or scientific measurement is supplied.'}
    f['source_files'].update({'static_assets/' + name: {'url': afolder + name, 'repository_path': 'assets/' + ASSET_PACKAGE + '/' + name,
        'sha256': hashlib.sha256((ap / name).read_bytes()).hexdigest()} for name in assets})
    for i, b in enumerate(docs['branches.json']['families']):
        members = [occurrence(c['stage_id'], 'coverage_matrix.json', '/stages/' + str(j) + '/stage_id', c)
                   for j, c in enumerate(docs['coverage_matrix.json']['stages']) if b['id'] in c['branch_ids']]
        f['routes'].append(route(b['id'], b['id'] + ' · ' + b['coverage'], b['evidence_class'], b, 'branches.json', '/families/' + str(i), members))
    for i, b in enumerate(docs['branches.json']['child_branches']):
        f['routes'].append(route(b['id'], b['id'] + ' · ' + b['scope'], 'source_child_scope', b, 'branches.json', '/child_branches/' + str(i)))
    for i, c in enumerate(binding['condition_views']):
        f['routes'].append(route(c['condition_id'], c['condition_id'] + ' · static view; no independent specimen claim',
            'static_condition_reference', c, 'scene_binding_contract.json', '/condition_views/' + str(i)))
    f['routes'].append(route('OPERATIONS_REFERENCE', 'COMPLETE STAGE INVENTORY · dependencies and loops remain authoritative',
        'operation_inventory', docs['operations.json'], 'operations.json', '',
        [occurrence(o['id'], 'operations.json', '/stages/' + str(i) + '/id') for i, o in enumerate(raw)]))
    for identifier, label, kind, filename in [
        ('PREPARATION_REFERENCE', 'PER-SPECIMEN PREPARATION · no pooled ancestry', 'preparation_reference', 'preparation_contract.json'),
        ('CONTROLS_REFERENCE', 'CONTROLS AND REPEATS · no inferred independent n', 'controls_reference', 'controls_and_repeats.json'),
        ('OUTCOMES_REFERENCE', 'AUTHOR-REPORTED OUTCOMES · no new telemetry', 'source_outcomes_reference', 'source_outcomes_reference.json'),
        ('BINDINGS_REFERENCE', 'STATIC ASSET BINDINGS · illustrative and unqualified', 'bindings_reference', 'scene_binding_contract.json'),
        (docs['lifecycle_contract.json']['release_failure_target'], 'SERVICE CUSTODY HOLD · no release by timeout or administrative closure', 'failure_hold', 'lifecycle_contract.json'),
        (f['default_route'], 'DEFAULT UNQUALIFIED HOLD · NO HEATING', 'qualification_hold', 'scene_binding_contract.json')]:
        f['routes'].append(route(identifier, label, kind, docs[filename], filename, ''))
    f['summary_counts'] = {'source_coverage_families': len(docs['branches.json']['families']), 'source_child_scopes': len(docs['branches.json']['child_branches']),
        'physical_device_families': len(docs['sample_contract.json']['families']), 'condition_views': len(binding['condition_views']),
        'authored_reference_views': 5, 'metadata_only_hold_views': 2, 'source_json_documents': len(docs), 'asset_json_documents': len(assets),
        'operation_templates': len(raw), 'source_evidence_entries': len(f['evidence']), 'source_ambiguities': len(docs['source_conflicts.json']),
        'unresolved_input_groups': len(docs['unknown_inputs.json']), 'authored_control_proposals': len(docs['controls_and_repeats.json']['authored_proposal']),
        'symbolic_loops': len(docs['operations.json']['loops']), 'scene_groups': len(binding['assets']), 'symbolic_anchors': len(binding['anchors']),
        'task_content_files': len(docs['CONTENT_MANIFEST.json']['files']), 'asset_content_files': len(assets['CONTENT_MANIFEST.json']['files'])}
    for name in ['README.md', 'previews/preview_01_overview.png', 'previews/preview_02_condition_views.png', 'previews/preview_03_guarded_services.png']:
        f['asset_links'].append({'label': 'Original editable static 3D guide' if name == 'README.md' else 'Static render: ' + name.split('/')[-1].removesuffix('.png'),
            'path': 'assets/' + ASSET_PACKAGE + '/' + name, 'url': afolder + name, 'sha256': hashlib.sha256((ap / name).read_bytes()).hexdigest()})
    return f


def validate_projection(f, p):
    if json.dumps(f, sort_keys=True, ensure_ascii=False, allow_nan=False) != json.dumps(projection(p), sort_keys=True, ensure_ascii=False, allow_nan=False):
        raise ValueError('Thermalmeta projection omitted, changed or invented a source contract or display boundary')
    if len({o['id'] for o in f['operations']}) != 20 or len({r['id'] for r in f['routes']}) != len(f['routes']):
        raise ValueError('Duplicate or missing operation/route')
    ap = p.parent.parent / 'assets' / ASSET_PACKAGE; seal = read(p, 'PAIR_SEAL.json')
    if (p / 'PAIR_SEAL.json').read_bytes() != (ap / 'PAIR_SEAL.json').read_bytes(): raise ValueError('Reciprocal seal bytes differ')
    if (p / 'scene_binding_contract.json').read_bytes() != (ap / 'scene_binding_contract.json').read_bytes(): raise ValueError('Shared binding bytes differ')
    for base, field in [(p, 'task_content_manifest_sha256'), (ap, 'scene_content_manifest_sha256')]:
        if hashlib.sha256((base / 'CONTENT_MANIFEST.json').read_bytes()).hexdigest() != seal[field]: raise ValueError('Content manifest pin mismatch')
        for item in read(base, 'CONTENT_MANIFEST.json')['files']:
            data = (base / item['path']).read_bytes()
            if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']: raise ValueError('Sealed content changed: ' + item['path'])
    if hashlib.sha256((p / 'scene_binding_contract.json').read_bytes()).hexdigest() != seal['shared_binding_sha256']: raise ValueError('Shared binding pin mismatch')
    return True


def adapt_thermalmeta(p):
    f = projection(p); validate_projection(f, p); return f
