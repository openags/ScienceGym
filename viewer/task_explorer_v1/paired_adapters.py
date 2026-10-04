"""Lossless read-only views of one paper-level design and three bounded subsets.

Inventories and source lifecycle contracts never become executable browser physics.
"""
import copy
import hashlib
import json
from collections import Counter

PAIRED_COMMIT = 'f803612db28652d2e2dd574d8039c36b7136f399'
PACKAGES = {key: key + '_operations_v2' for key in ('laser_control', 'solar_water', 'sucrose_metrology', 'actuator_metrology')}
LABELS = {'laser_control': 'Modulation-free laser stabilization', 'solar_water': 'Clean-water solar metrology',
          'sucrose_metrology': 'Sucrose optical metrology', 'actuator_metrology': 'Actuator displacement metrology'}
COLORS = {'laser_control': '#c5a6ec', 'solar_water': '#e9c577', 'sucrose_metrology': '#87cbbd', 'actuator_metrology': '#a8c989'}
ALIASES = {'unknown_parameters.json': 'unknowns', 'evaluator_reference.json': 'acceptance', 'lineage_contract.json': 'lineage'}
SCOPE_LABELS = {'paper_level_design': 'PAPER-LEVEL DESIGN', 'bounded_subset': 'BOUNDED SUBSET'}
KINDS = {'design_only': 'DESIGN / NUMERICAL REFERENCE · NOT RUN', 'closed_service': 'CLOSED QUALIFIED SERVICE · NOT EXECUTED',
         'bounded_physical': 'BOUNDED PHYSICAL DESIGN · NOT EXECUTED', 'numerical': 'NUMERICAL REFERENCE · NOT RUN',
         'preparation': 'QUALIFIED PREPARATION SERVICE · NOT EXECUTED', 'failure_hold': 'DEFAULT / FAILURE HOLD · NO ACTIVATION',
         'session_teardown': 'SEPARATE SESSION TEARDOWN OBLIGATION', 'conditional_recovery': 'CONDITIONAL RECOVERY · NOT A NORMAL BRANCH'}
BOUNDARY = 'Read-only author/evaluator reference; no actor loader, task runner, solver, physical simulation, hardware activation or scientific reproduction. Membership is not chronology; exact source contracts remain authoritative.'
WARNINGS = {
 'laser_control': 'PAPER-LEVEL DESIGN accounted for; whole-paper execution remains false. Default QUALIFICATION_HOLD. Nine design-only and six closed-service scientific branches remain separate from the hold. Commands do not prove state. Three DFB identities, prepared-intake versus full-preparation lineage, reference chain, frozen control settings and in-loop versus independent heterodyne channels remain distinct. Source outcomes never become measured episode results. No laser, electrical or numerical execution.',
 'solar_water': 'BOUNDED NONBIOLOGICAL SUBSET; not a complete whole-paper design. Clean-water metrology only: all biological work remains excluded and no potability claim is supported. Prefabricated input never earns fabrication credit. Operation inventories do not replace the canonical lifecycle; coupon/water/setup/calibration lineage, independent safe-state evidence, unresolved qualification and source-conflict gates remain intact.',
 'sucrose_metrology': 'BOUNDED NONBIOLOGICAL SUBSET; not a complete whole-paper design. Default FLOW_HOLD preserves the unresolved 40x flow conflict; no pump setting is chosen or averaged. Three optical profiles and the 589.29 nm reference remain distinct. Cartridge retention, calibration revisions, session teardown, immutable sample/reference/frame lineage and excluded biological scope remain explicit. Main Figs 2-4 pixels and raw source data remain uninspected. No open-beam operation or numerical PCA execution.',
 'actuator_metrology': 'BOUNDED DISPLACEMENT-METROLOGY SUBSET; not a complete whole-paper design. Default DIRECTION_HOLD preserves unresolved specimen/node/world-frame direction qualification. Signed input/output projection never becomes absolute magnitude. Prepared intake earns no fabrication credit. Numerical design, qualified preparation and two physical-metrology designs remain distinct; FEM alternatives are not an AND gate. Sampled movies are not continuous or quantitative inspection. No mechanics solver or physical execution.'}
ASSET_KEYS = {'laser_control': 'laser', 'sucrose_metrology': 'sucrose', 'actuator_metrology': 'actuator'}

def clone(v): return copy.deepcopy(v)
def read(p, n): return json.loads((p / n).read_text(encoding='utf-8'))
def context_key(n): return ALIASES.get(n, n.removesuffix('.json'))
def absent(n): return 'No ' + n + ' field supplied; inspect the exact source contract. No value or command is inferred.'
def first(d, names, fallback):
    return clone(next((d[n] for n in names if n in d), fallback))

def operation(o, i):
    actions = first(o, ('robot_actions', 'actions', 'action'), absent('actions'))
    return {'id': o['id'], 'title': o.get('title', o['id'].replace('_', ' ').title()),
            'stage': o.get('station_id', absent('per-operation station')),
            'actions': actions if isinstance(actions, list) else [actions],
            'objects': first(o, ('asset_ids', 'sample_or_payload', 'input_kind'), absent('per-operation objects')),
            'pre': first(o, ('preconditions', 'pre_state', 'precondition'), absent('pre-state')),
            'post': first(o, ('postconditions', 'post_state'), absent('post-state')),
            'acceptance': first(o, ('completion_evidence', 'required_receipts', 'required_receipt_fields', 'required_output'), absent('completion evidence')),
            'recovery': first(o, ('failure_recovery', 'failure_action', 'failure'), absent('recovery')),
            'sources': clone(o.get('source_evidence_ids', [])), 'unknowns': first(o, ('unknown_parameter_ids', 'required_card_ids'), []),
            'provenance': first(o, ('source_vs_authored', 'authored_translation', 'origin'), absent('source/authored provenance')),
            'loop': None, 'detail': clone(o), 'source_file': 'operations.json', 'source_pointer': f'/operations/{i}',
            'display_mapping_basis': 'Authored display mapping; detail retains the complete source record. Required output is acceptance evidence, never a proven post-state. Absent action fields do not authorize commands.',
            'display_title_basis': 'Exact source title' if 'title' in o else 'Authored navigation title from source operation ID; no source title supplied'}

def contract(label, value, filename, pointer):
    return {'type': 'condition', 'label': label, 'ordered': False, 'children': [],
            'meta': {'source_file': filename, 'source_pointer': pointer, 'source_contract': clone(value)}}

def route(identifier, record, filename, pointer, kind, members=(), membership_source=None):
    title = record.get('title', record.get('purpose', identifier.replace('_', ' ').title())) if isinstance(record, dict) else identifier.replace('_', ' ').title()
    nodes = []
    if members:
        nodes.append({'type': 'obligations', 'label': 'Source operation inventory · no adjacency chronology', 'ordered': False,
                      'children': clone(list(members)), 'meta': {'order': 'Inspection membership only. Conditional recovery remains conditional; exact lifecycle and source causal constraints remain authoritative.', 'membership_source': membership_source or 'Exact source operation_ids'}})
    nodes.append(contract('Exact source scope and obligations · unexpanded', record, filename, pointer))
    return {'id': identifier, 'label': KINDS[kind] + ' · ' + title, 'route_kind': kind, 'metadata_only': not bool(members),
            'nodes': nodes, 'basis': BOUNDARY, 'detail': clone(record) if isinstance(record, dict) else {'source_record': clone(record)},
            **({'detail_source_wrapper': 'source_record'} if not isinstance(record, dict) else {}),
            'source_file': filename, 'source_pointer': pointer,
            'navigation_basis': 'Authored view label for the exact source record; not a new experiment, successful service or execution'}

def kind(key, b):
    if b['id'].endswith('HOLD'): return 'failure_hold'
    if key == 'laser_control': return 'design_only' if b['execution_class'] == 'design_only' else 'closed_service'
    if key == 'solar_water': return 'closed_service' if b['type'] == 'closed_service_interface' else 'bounded_physical'
    if key == 'actuator_metrology':
        return 'numerical' if b['phase_class'].startswith('numerical_') else 'preparation' if b['phase_class'] == 'physical_preparation' else 'bounded_physical'
    return 'bounded_physical'

def projection(p, key):
    raw = read(p, 'operations.json'); branches = read(p, 'branches.json'); prov = read(p, 'provenance.json')
    docs = {n.relative_to(p).as_posix(): read(p, n.relative_to(p).as_posix()) for n in sorted(p.rglob('*.json'))}
    folder = f'https://github.com/openags/ScienceGym/blob/{PAIRED_COMMIT}/tasks/{p.name}/'
    ident = prov.get('identity', prov.get('article', prov))
    em = docs.get('evidence_map.json', prov.get('evidence', []))
    ev = em.get('evidence', []) if isinstance(em, dict) else em
    evidence = {x['id']: clone(x) for x in ev}
    if key == 'laser_control':
        for ref in em['source_reference_ids']:
            evidence[ref] = {'id': ref, 'namespace': 'source_reference_ids', 'locator': em['source_locator'],
                             'related_evidence_ids': [e['id'] for e in ev if ref in e['sources']]}
    scope = 'paper_level_design' if key == 'laser_control' else 'bounded_subset'
    f = {'id': key, 'label': LABELS[key], 'title': ident.get('title', prov.get('article_title', LABELS[key])),
         'doi': ident.get('doi', prov.get('doi', prov.get('source_doi'))), 'color': COLORS[key],
         'family_scope': scope, 'family_scope_label': SCOPE_LABELS[scope], 'source_commit': PAIRED_COMMIT, 'source_folder': folder,
         'status': SCOPE_LABELS[scope] + ' · ' + BOUNDARY + ' ' + WARNINGS[key], 'source_warnings': WARNINGS[key],
         'visibility': 'author_evaluator_reference_only', 'actor_projection_implemented': False,
         'operations': [operation(o, i) for i, o in enumerate(raw['operations'])], 'routes': [], 'evidence': evidence,
         'dependencies': clone(docs.get('dependencies.json', {})),
         'context': {context_key(name): clone(value) for name, value in docs.items()},
         'source_files': {name: {'url': folder + name, 'sha256': hashlib.sha256((p / name).read_bytes()).hexdigest()} for name in docs},
         'asset_links': [], 'asset_boundary': 'Existing original authored 3D assets and static renders only. These links do not implement interactive browser physics or physical execution.'}
    for i, b in enumerate(branches['branches']):
        members = [o['id'] for o in raw['operations'] if b['id'] in o['branch_ids']] if key == 'laser_control' else b['operation_ids']
        r = route(b['id'], b, 'branches.json', f'/branches/{i}', kind(key, b), members,
                  'Exact reverse index of operations.json /operations/*/branch_ids; source design_sequence remains distinct' if key == 'laser_control' else None)
        for name in ['lifecycle_contract.json', 'episode_input_contract.json']:
            if name in docs: r['nodes'].append(contract('Exact scoped ' + name + ' · not expanded', docs[name], name, ''))
        f['routes'].append(r)
    if key == 'laser_control':
        r = route('QUALIFICATION_HOLD', branches['hold_branch'], 'branches.json', '/hold_branch', 'failure_hold', docs['lifecycle_contract.json']['hold_phases'], 'lifecycle_contract.json /hold_phases; independent of scientific branch membership')
        r['nodes'].append(contract('Exact qualification-hold phase contract', docs['lifecycle_contract.json']['hold_phases'], 'lifecycle_contract.json', '/hold_phases'))
        f['routes'].append(r)
    if key == 'sucrose_metrology':
        i = next(i for i, b in enumerate(branches['branches']) if 'session_teardown_operation_ids' in b)
        members = branches['branches'][i]['session_teardown_operation_ids']
        f['routes'].append(route('SESSION_TEARDOWN', members, 'branches.json', f'/branches/{i}/session_teardown_operation_ids', 'session_teardown', members,
                                 'Separate source session teardown; never appended to each measurement branch'))
    used = {o for r in f['routes'] for n in r['nodes'] if n['type'] == 'obligations' for o in n['children']}
    for i, o in enumerate(raw['operations']):
        if o['id'] not in used:
            if o['id'] not in ('HOLD_BUBBLE', 'HOLD_RANGE', 'HOLD_DRIFT', 'QUARANTINE', 'HOLD_QUALIFICATION'): raise ValueError('Unmapped operation ' + o['id'])
            f['routes'].append(route('RECOVERY_' + o['id'], o, 'operations.json', f'/operations/{i}', 'conditional_recovery', [o['id']], 'Operation-level conditional recovery contract; no mandatory branch placement inferred'))
    f['default_route'] = {'laser_control': 'QUALIFICATION_HOLD', 'solar_water': 'RECEIPT', 'sucrose_metrology': 'FLOW_HOLD', 'actuator_metrology': 'DIRECTION_HOLD'}[key]
    f['default_route_basis'] = 'Source hold default retained; solar receipt is authored navigation only, not execution qualification.'
    f['summary_counts'] = dict(Counter(r['route_kind'] + '_records' for r in f['routes']))
    unknowns = docs['unknown_parameters.json']
    f['summary_counts'].update(source_branches=len(branches['branches']), source_json_documents=len(docs),
                              unresolved_input_groups=len(first(unknowns, ('parameters', 'unknown_parameters', 'unknowns'), [])),
                              control_records=len(docs['control_packages.json']['controls']))
    if key == 'laser_control':
        f['summary_counts']['unresolved_input_groups'] = len(unknowns['required_before_physical_execution']) + len(unknowns['required_before_numerical_reproduction'])
        f['summary_counts']['physical_input_groups'] = len(unknowns['required_before_physical_execution'])
        f['summary_counts']['numerical_input_groups'] = len(unknowns['required_before_numerical_reproduction'])
    if key in ASSET_KEYS:
        asset = ASSET_KEYS[key] + '_scene_assets_v1'; ap = p.parent.parent / 'assets' / asset
        names = ['README.md'] + [n.relative_to(ap).as_posix() for n in sorted((ap / 'evidence').glob('*.png'))]
        for name in names:
            if not (ap / name).is_file(): raise ValueError('Missing paired asset ' + name)
            f['asset_links'].append({'label': 'Original 3D asset guide' if name == 'README.md' else 'Static render: ' + name.split('/')[-1].removesuffix('.png').replace('_', ' '),
                                    'path': 'assets/' + asset + '/' + name, 'url': f'https://github.com/openags/ScienceGym/blob/{PAIRED_COMMIT}/assets/{asset}/{name}',
                                    'sha256': hashlib.sha256((ap / name).read_bytes()).hexdigest()})
    return f

def validate_projection(f, p):
    if json.dumps(f, sort_keys=True, allow_nan=False) != json.dumps(projection(p, f['id']), sort_keys=True, allow_nan=False): raise ValueError('Paired projection changed, omitted or invented source data or conservative display grammar')
    ids = [o['id'] for o in f['operations']]
    if len(ids) != len(set(ids)): raise ValueError('Duplicate operation ID')
    if len(f['routes']) != len({r['id'] for r in f['routes']}): raise ValueError('Duplicate route ID')
    used = {o for r in f['routes'] for n in r['nodes'] if n['type'] == 'obligations' for o in n['children']}
    if used != set(ids): raise ValueError('Unresolved or inaccessible operation')
    return True

def adapt(p, key):
    f = projection(p, key); validate_projection(f, p); return f

def adapt_laser_control(p): return adapt(p, 'laser_control')
def adapt_solar_water(p): return adapt(p, 'solar_water')
def adapt_sucrose_metrology(p): return adapt(p, 'sucrose_metrology')
def adapt_actuator_metrology(p): return adapt(p, 'actuator_metrology')
