"""Lossless whole-paper woven-material DESIGN inspector; no scientific execution."""
import hashlib
import json
from collections import Counter

from paired_adapters import clone, read, context_key, operation, contract

WOVEN_COMMIT = 'd62daed913e2ea04f0b7b0a0f20de9f6d42b7df6'
PACKAGES = {'woven': 'woven_material_operations_v2'}
KINDS = {'design_only': ('design_only', 'DESIGN REFERENCE · NOT RUN'),
         'closed_qualified_service': ('closed_service', 'CLOSED QUALIFIED SERVICE DESIGN · NOT EXECUTED'),
         'external_numerical_design': ('numerical', 'EXTERNAL NUMERICAL DESIGN · NO SOLVER RUN'),
         'conflict_hold': ('conflict_hold', 'SOURCE-CONFLICT HOLD · NOT RELEASED')}
BOUNDARY = ('Whole-paper DESIGN coverage only; not scientific reproduction or a runnable environment. '
            'Read-only author/evaluator reference; no actor projection, hardware control, scientific solver or execution. '
            'Source reverse-index memberships are unordered inventories, not chronology or performed operations. '
            'HOLD_* and QUARANTINE entries remain conditional recovery, never mandatory successful steps.')
WARNINGS = ('WHOLE-PAPER DESIGN, NOT REPRODUCTION. The 24 scientific design routes and 48 symbolic operations '
            'cover design scope whose source suite reports 96 synthetic contract configurations, with 11 static scene groups and 43 symbolic anchors; none is a physical trial, '
            'qualified device, source-exact CAD or scientific result. Default QUALIFICATION_HOLD is a separate inspection record, '
            'not a 25th scientific route. Eleven source conflicts and twelve required input gates remain unresolved or scope-controlled. '
            'Tetrakaidecahedron remains held without blocking unaffected topologies. Physical and numerical pattern maps, failure '
            'variables and geometry contexts cannot substitute for one another. Plasma/coating relative order requires an external '
            'order card; source partial order is preserved. Full fabrication versus independently prepared intake keep distinct lineage '
            'and preparation credit. Mount, calibration, control, sample and attempt revisions require independent current evidence; '
            'requests are never observations. BCC compression, BCC tension and octahedron compression cycles remain distinct. '
            'Signed closed-cycle loss differs from loading work and is not made positive with absolute value. Unknown isolation stays '
            'contained; damage is quarantined. All hazardous work stays inside closed externally qualified services, none implemented. '
            'Complete written main/SI design coverage does not mean videos were played or workbook values inspected. '
            'Only source agent_visible.json is actor context; this public inspector includes evaluator-only material and is not actor-safe.')


def view(identifier, detail, filename, pointer, kind, label, members):
    return {'id': identifier, 'label': label, 'route_kind': kind, 'metadata_only': not bool(members),
            'nodes': [{'type': 'obligations', 'label': 'Source operation inventory · no adjacency chronology',
                       'ordered': False, 'children': clone(members),
                       'meta': {'order': BOUNDARY,
                                'membership_source': 'Exact reverse index of operations.json /operations/*/branch_ids; source design_sequence remains distinct'
                                if filename == 'branches.json' else 'Authored navigation over source HOLD_QUALIFICATION; source lifecycle default retained'}},
                      contract('Exact source contract · unexpanded', detail, filename, pointer)],
            'basis': BOUNDARY, 'detail': clone(detail), 'source_file': filename, 'source_pointer': pointer,
            'navigation_basis': 'Authored inspection label; no additional experiment, service completion, specimen or scientific result'}


def projection(p):
    docs = {path.relative_to(p).as_posix(): read(p, path.relative_to(p).as_posix()) for path in sorted(p.rglob('*.json'))}
    raw = docs['operations.json']['operations']; branches = docs['branches.json']['branches']; prov = docs['provenance.json']
    folder = f'https://github.com/openags/ScienceGym/blob/{WOVEN_COMMIT}/tasks/{p.name}/'
    f = {'id': 'woven', 'label': 'Woven metamaterials', 'title': prov['title'], 'doi': prov['doi'], 'color': '#daae85',
         'family_scope': 'paper_level_design', 'family_scope_label': 'WHOLE-PAPER DESIGN',
         'source_commit': WOVEN_COMMIT, 'source_folder': folder, 'status': BOUNDARY + ' ' + WARNINGS,
         'source_warnings': WARNINGS, 'visibility': 'author_evaluator_reference_only', 'actor_projection_implemented': False,
         'operations': [operation(o, i) for i, o in enumerate(raw)], 'routes': [],
         'evidence': {e['id']: clone(e) for e in docs['evidence_map.json']['entries']},
         'context': {context_key(name): clone(value) for name, value in docs.items()},
         'dependencies': {'rule': 'No universal operation DAG supplied. Exact source preparation and lifecycle contracts remain authoritative; receipt-stage names are not operation IDs.',
                          'preparation_routes': clone(docs['preparation_routes.json']),
                          'lifecycle_contract': clone(docs['lifecycle_contract.json']),
                          'transport_routes': clone(docs['transport_routes.json'])},
         'source_files': {name: {'url': folder + name, 'sha256': hashlib.sha256((p / name).read_bytes()).hexdigest()} for name in docs},
         'default_route': 'QUALIFICATION_HOLD',
         'default_route_basis': 'Exact lifecycle/episode default; authored navigation record does not add a scientific branch or qualify a service.',
         'asset_links': [],
         'asset_boundary': 'Existing original editable static 3D assets and renders only. The 11 groups and 43 symbolic anchors are unqualified authored placeholders; no source-exact geometry, mechanics, collision/grasp validation or interactive browser physics.'}
    for i, branch in enumerate(branches):
        kind, label = KINDS[branch['execution_class']]
        members = [o['id'] for o in raw if branch['id'] in o['branch_ids']]
        route = view(branch['id'], branch, 'branches.json', f'/branches/{i}', kind,
                     label + ' · ' + branch['id'].replace('_', ' ').title(), members)
        route['nodes'].append(contract('Exact lifecycle principles · qualification and safe release remain required', docs['lifecycle_contract.json'], 'lifecycle_contract.json', ''))
        f['routes'].append(route)
    f['routes'].append(view('QUALIFICATION_HOLD', docs['lifecycle_contract.json'], 'lifecycle_contract.json', '',
                            'qualification_hold', 'DEFAULT QUALIFICATION HOLD · NO ACTIVATION', ['HOLD_QUALIFICATION']))
    services = docs['station_contracts.json']['services']
    f['summary_counts'] = dict(Counter(r['route_kind'] + '_records' for r in f['routes']))
    f['summary_counts'].update(source_branches=len(branches), source_json_documents=len(docs),
                              synthetic_configurations=docs['STATUS.json']['synthetic_configuration_count'],
                              scene_groups=len(services), symbolic_anchors=sum(len(s['anchors']) for s in services),
                              source_evidence_entries=len(f['evidence']), source_conflicts=len(docs['source_conflicts.json']['items']),
                              unresolved_input_groups=len(docs['unknown_parameters.json']['required_input_gates']),
                              control_records=len(docs['control_packages.json']['cards']))
    asset = 'woven_scene_assets_v1'; ap = p.parent.parent / 'assets' / asset
    for name in ['README.md'] + [n.relative_to(ap).as_posix() for n in sorted((ap / 'evidence').glob('*.png'))]:
        if not (ap / name).is_file(): raise ValueError('Missing original woven asset ' + name)
        f['asset_links'].append({'label': 'Original editable static 3D asset guide' if name == 'README.md' else 'Static render: ' + name.split('/')[-1].removesuffix('.png').replace('_', ' '),
                                'path': 'assets/' + asset + '/' + name,
                                'url': f'https://github.com/openags/ScienceGym/blob/{WOVEN_COMMIT}/assets/{asset}/{name}',
                                'sha256': hashlib.sha256((ap / name).read_bytes()).hexdigest()})
    return f


def validate_projection(f, p):
    if json.dumps(f, sort_keys=True, allow_nan=False) != json.dumps(projection(p), sort_keys=True, allow_nan=False):
        raise ValueError('Woven projection changed, omitted or invented source data or conservative display grammar')
    ids = [o['id'] for o in f['operations']]
    if len(ids) != len(set(ids)): raise ValueError('Duplicate operation ID')
    routes = [r['id'] for r in f['routes']]
    if len(routes) != len(set(routes)): raise ValueError('Duplicate route ID')
    used = {oid for r in f['routes'] for n in r['nodes'] if n['type'] == 'obligations' for oid in n['children']}
    if used != set(ids): raise ValueError('Unresolved or inaccessible operation')
    branch_ids = {r['id'] for r in f['routes'] if r['source_file'] == 'branches.json'}
    for op in f['operations']:
        if not set(op['detail']['branch_ids']) <= branch_ids: raise ValueError('Unresolved source branch')
        if not set(op['sources']) <= set(f['evidence']): raise ValueError('Unresolved source evidence')
    return True


def adapt_woven(p):
    f = projection(p); validate_projection(f, p); return f
