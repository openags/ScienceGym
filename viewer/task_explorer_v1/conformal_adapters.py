"""Lossless static conformal design inspector; no mechanics or robot execution."""
import hashlib
import json
from paired_adapters import clone, read, context_key, contract, absent

PACKAGES = {'conformal': 'conformal_operations_v3_compressed'}
SOURCE_COMMIT = 'b43ae101e388c4555c0ec68637b96cee54ce6257'
ASSET_PACKAGE = 'conformal_scene_assets_v2_compressed'
SNAPSHOT_SHA256 = '097445ec4d24cda9674739088747fcdff360d0cbcd26975b2cae5de362de9104'
EXPECTED_TASK_PINS = ('operations.json', 'branches.json', 'unknown_parameters.json', 'controls_and_repeats.json', 'lineage_contract.json', 'tests/contract.py', 'tests/verify_pairing.py', 'RELEASE_BOUNDARY.json', 'asset_binding_plan.json')
EXPECTED_ASSET_PINS = ('affordances.json', 'assembly_contract.json', 'asset_inventory.json', 'asset_metadata.json', 'geometry/conformal_lab.blend', 'geometry/conformal_lab.glb', 'operation_binding_contract.json', 'operation_bindings.json', 'semantic_controls.py', 'specimen_geometry.json', 'states.json')
BOUNDARY = ('Whole-paper DESIGN only; zero validated runnable whole-paper tasks. '
    'Read-only author/evaluator reference, not an actor context, hardware controller, mechanics simulation or scientific reproduction. '
    'Source facts, authored robot contracts, synthetic observations and illustrative geometry remain separate. '
    'Inventories are inspection memberships; only exact dependencies and lifecycle guards constrain order. '
    'Frames, phases, conditions, loading cycles and movie playback are not independent specimens or repeats. '
    'Qualification holds remain active; required outputs and observations are obligations, never observed outcomes.')
WARNINGS = ('Sixteen authored operation templates and nine source-scope branches represent one paper-level design. '
    'Only B02 foot and B03 bridge are physical experimental design routes; B01 is preparation, B06 is analysis, and B09 is authored closeout. '
    'B04, B05, B07 and B08 remain documented, unexecuted numerical or analytical scope. '
    'Four hundred acquired frames at 1 fps and movie playback at 30 fps remain distinct source references, never operating defaults or independent n. '
    'Compression and decompression retain separate evidence; the source does not establish independent specimen or replicate allocation. '
    'The 306 by 64 by 40 mm envelope, 48 by 10 square count and 4.8 mm square size do not determine an exact specimen topology. '
    'Unknown powder identity and bridge contact treatment remain unresolved; fabrication, contact preparation and powered loading remain closed qualified services. '
    'Nine controls, five source conflicts and sixteen unresolved-input groups remain exact. '
    'Linear dilation versus area ratio, hinge-power, stress notation, registration and modulus discrepancies are not silently repaired. '
    'Measured data, nearest conformal fits, boundary-only predictions, finite-element results and numerical animations remain separate. '
    'Independent calibration receipts, current epochs, capture readiness, supported custody, safe-release closeout and failed-attempt ancestry remain required. '
    'Upstream review read nine main pages, sixteen written SI pages and one media-description sheet, with selected figure/equation inspection. '
    'Three movies were fully decoded and five frames each visually sampled, not continuously reviewed. Zenodo archive contents remain unread. '
    'No new paper reread, source-data reanalysis, mathematical proof, physical safety qualification or scientific validation is supplied. '
    'Original scene geometry, interfaces and anchors are illustrative and unqualified; they grant no motion permission.')


def occurrence(identifier, filename, pointer):
    return {'type': 'op', 'id': identifier,
            'meta': {'source_file': filename, 'source_pointer': pointer, 'source_node': identifier,
                     'meaning': 'Exact source-listed operation membership; not execution, chronology or a new specimen'}}


def route(identifier, label, kind, detail, filename, pointer, members=()):
    nodes = []
    if members:
        nodes.append({'type': 'obligations', 'label': 'Exact operation membership; no adjacency chronology',
                      'ordered': False, 'children': list(members),
                      'meta': {'order': BOUNDARY}})
    nodes.append(contract('Exact source scope and obligations', detail, filename, pointer))
    return {'id': identifier, 'label': label, 'route_kind': kind, 'metadata_only': not bool(members),
            'nodes': nodes, 'basis': BOUNDARY, 'detail': clone(detail),
            'source_file': filename, 'source_pointer': pointer,
            'navigation_basis': 'Authored inspection label; no additional scientific branch, qualification or observed result'}


def projection(p):
    docs = {n.relative_to(p).as_posix(): read(p, n.relative_to(p).as_posix()) for n in sorted(p.rglob('*.json'))}
    raw = docs['operations.json']['operations']; paper = docs['provenance.json']['paper']
    folder = '../../tasks/' + p.name + '/'
    operations = []
    for i, o in enumerate(raw):
        operations.append({'id': o['id'], 'title': o['name'], 'stage': o['station'],
            'actions': clone(o['substeps']), 'objects': {'asset_ids': clone(o['asset_ids']), 'required_inputs': clone(o['inputs'])},
            'pre': clone(o['entry_guards']), 'post': absent('observed post-state'),
            'acceptance': {k: clone(o[k]) for k in ('outputs', 'observations_to_record', 'evidence_role', 'service_request_is_completion')},
            'recovery': {k: clone(o[k]) for k in ('failure_closeout',)},
            'sources': clone(o['source_anchors']), 'unknowns': clone(o['execution_gaps']),
            'provenance': {k: clone(o[k]) for k in ('classification', 'physical_execution_qualified', 'runtime')},
            'loop': None, 'detail': clone(o), 'source_file': 'operations.json', 'source_pointer': '/operations/' + str(i),
            'display_title_basis': 'Exact task-package authored operation name; not a paper quotation',
            'display_mapping_basis': 'Entry guards are requirements. Outputs and observations_to_record are required evidence, never observed post-state or success.',
            'display_action_ownership': 'Independently authored symbolic robot/service boundary; no live device control.'})
    f = {'id': 'conformal', 'label': 'Conformal elasticity metamaterials', 'title': 'Conformal elasticity of mechanism-based metamaterials', 'doi': docs['provenance.json']['paper_doi'], 'color': '#a9c983',
         'family_scope': 'paper_level_design', 'family_scope_label': 'WHOLE-PAPER DESIGN',
         'source_commit': SOURCE_COMMIT, 'source_folder': folder,
         'source_link_mode': 'repository_relative_frozen_local_snapshot',
         'source_publication': 'Local freeze commit and per-file hashes identify provenance; remote publication is not asserted by these identifiers. The repository commit establishes publication status.',
         'status': BOUNDARY + ' ' + WARNINGS, 'source_warnings': WARNINGS,
         'visibility': 'author_evaluator_reference_only', 'actor_projection_implemented': False,
         'operations': operations, 'routes': [],
         'evidence': {e['id']: clone(e) for e in docs['source_parameters.json']['facts']},
         'context': {context_key(name): clone(value) for name, value in docs.items()},
         'dependencies': {'display_rule': BOUNDARY, **{name: clone(docs[name + '.json']) for name in
                          ('dependencies', 'preparation_routes', 'lifecycle_contract', 'lineage_contract', 'transport_routes', 'recovery_boundaries')},
                          'operation_dependencies': [{'operation_id': o['id'], 'depends_on': clone(o['depends_on'])} for o in raw]},
         'source_files': {name: {'url': folder + name, 'repository_path': 'tasks/' + p.name + '/' + name,
                                'sha256': hashlib.sha256((p / name).read_bytes()).hexdigest()} for name in docs},
         'default_route': docs['episode_input_contract.json']['default'],
         'default_route_basis': 'Exact metadata-only episode default; no new operation or qualification is invented.',
         'asset_links': [],
         'asset_boundary': 'Original editable static 3D scene and three renders only. Geometry, dimensions, anchors, poses, grasps and interfaces remain illustrative and unqualified. No source-exact CAD, contact model, validated motion, real physics or scientific measurement is supplied.'}
    for i, b in enumerate(docs['branches.json']['branches']):
        pointer = '/branches/' + str(i)
        f['routes'].append(route(b['id'], b['classification'].upper().replace('_', ' ') + ' · ' + b['name'], b['classification'], b, 'branches.json', pointer,
            [occurrence(oid, 'branches.json', pointer + '/route_operations/' + str(j)) for j, oid in enumerate(b['route_operations'])]))
    # Separate authored navigation over exact records. These are not additional experimental branches.
    f['routes'].append(route('OPERATIONS_REFERENCE', 'COMPLETE OPERATION INVENTORY · dependencies remain authoritative',
        'operation_inventory', docs['operations.json'], 'operations.json', '',
        [occurrence(o['id'], 'operations.json', '/operations/' + str(i) + '/id') for i, o in enumerate(raw)]))
    for identifier, label, kind, filename in [
        ('PREPARATION_REFERENCE', 'PREPARATION LINEAGE · closed qualified services', 'preparation_reference', 'preparation_routes.json'),
        ('CONTROLS_REFERENCE', 'CONTROLS AND REPEATS · no inferred independent n', 'controls_reference', 'controls_and_repeats.json'),
        ('RECOVERY_REFERENCE', 'FAILED ATTEMPTS AND SUPPORTED HOLDS · conditional recovery', 'recovery_reference', 'recovery_boundaries.json'),
        ('NONMANUAL_REFERENCE', 'THEORY AND EXTERNAL SERVICES · no execution credit', 'nonmanual_reference', 'nonmanual_scope.json'),
        (f['default_route'], 'DEFAULT QUALIFICATION HOLD · NO ACTIVATION', 'qualification_hold', 'episode_input_contract.json')]:
        f['routes'].append(route(identifier, label, kind, docs[filename], filename, ''))
    plan = docs['asset_binding_plan.json']
    f['summary_counts'] = {'source_scope_branches': len(docs['branches.json']['branches']), 'physical_experimental_branches': len(docs['branches.json']['physical_experiment_ids']), 'documented_unexecuted_nonmanual_branches': len(docs['branches.json']['nonmanual_source_scope_ids']),
        'authored_reference_views': 5, 'metadata_only_hold_views': 1, 'source_json_documents': len(docs),
        'operation_templates': len(raw), 'source_evidence_entries': len(f['evidence']),
        'source_conflicts': len(docs['source_conflicts.json']['conflicts']), 'unresolved_input_groups': len(docs['unknown_parameters.json']['unknowns']),
        'controls': len(docs['controls_and_repeats.json']['controls']), 'stations': len(docs['station_contracts.json']['stations']),
        'scene_groups': len({a for b in plan['operation_bindings'] for a in b['asset_ids']}),
        'symbolic_anchors': len({a for b in plan['operation_bindings'] for a in b['anchor_ids']}),
        'task_pinned_asset_hashes': len(plan['final_asset_hashes'])}
    ap = p.parent.parent / 'assets' / ASSET_PACKAGE
    for name in ['README.md'] + [n.relative_to(ap).as_posix() for n in sorted((ap / 'evidence').glob('*.png'))]:
        if not (ap / name).is_file(): raise ValueError('Missing original static asset: ' + name)
        f['asset_links'].append({'label': 'Original editable static 3D guide' if name == 'README.md' else 'Static render: ' + name.split('/')[-1].removesuffix('.png'),
            'path': 'assets/' + ASSET_PACKAGE + '/' + name, 'url': '../../assets/' + ASSET_PACKAGE + '/' + name,
            'sha256': hashlib.sha256((ap / name).read_bytes()).hexdigest()})
    return f


def validate_projection(f, p):
    if json.dumps(f, sort_keys=True, ensure_ascii=False, allow_nan=False) != json.dumps(projection(p), sort_keys=True, ensure_ascii=False, allow_nan=False):
        raise ValueError('Conformal elasticity projection omitted, changed or invented a source contract or display boundary')
    ids = [o['id'] for o in f['operations']]
    if len(set(ids)) != len(ids): raise ValueError('Duplicate operation')
    if len({r['id'] for r in f['routes']}) != len(f['routes']): raise ValueError('Duplicate inspection route')
    def walk(nodes):
        for node in nodes:
            if node['type'] == 'op': yield node['id']
            yield from walk(node.get('children', []))
    if {oid for r in f['routes'] for oid in walk(r['nodes'])} != set(ids): raise ValueError('Operation coverage mismatch')
    if f['default_route'] in ids: raise ValueError('Hold must not invent an operation')
    ap = p.parent.parent / 'assets' / ASSET_PACKAGE
    pins = f['context']['asset_binding_plan']['final_asset_hashes']
    if sorted(v['path'] for v in pins) != sorted(EXPECTED_ASSET_PINS):
        raise ValueError('Task-pinned asset inventory changed')
    for pin in pins:
        data = (ap / pin['path']).read_bytes()
        if len(data) != pin['bytes'] or hashlib.sha256(data).hexdigest() != pin['sha256']:
            raise ValueError('Task-pinned scene file changed: ' + pin['path'])
    snapshot = read(ap, 'task_binding_snapshot.json')
    if json.dumps(snapshot['binding_plan'], sort_keys=True) != json.dumps(read(p, 'asset_binding_plan.json'), sort_keys=True):
        raise ValueError('Task/asset snapshot mismatch')
    pins = snapshot.get('task_files', [])
    if sorted(v['task_file'] for v in pins) != sorted(EXPECTED_TASK_PINS):
        raise ValueError('Asset-pinned task inventory changed')
    if hashlib.sha256((ap / 'task_binding_snapshot.json').read_bytes()).hexdigest() != SNAPSHOT_SHA256:
        raise ValueError('Frozen asset binding snapshot changed')
    for pin in pins:
        data = (p / pin['task_file']).read_bytes()
        if len(data) != pin['bytes'] or hashlib.sha256(data).hexdigest() != pin['sha256']:
            raise ValueError('Asset-pinned task file changed: ' + pin['task_file'])
    return True


def adapt_conformal(p):
    f = projection(p); validate_projection(f, p); return f
