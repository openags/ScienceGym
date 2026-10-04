"""Lossless, read-only projections of four published cross-disciplinary packages.

Authored navigation is not an executable plan. Full source records remain authoritative.
"""
import copy
import hashlib
import json
from collections import Counter

CROSSDISCIPLINARY_COMMIT = '990f98529182af0ddd03fba53587b0931630de96'
PACKAGES = {key: key + '_operations_v2' for key in ('atmospheric_optics', 'afm_metrology', 'martian_geophysics', 'transistor')}
LABELS = {'atmospheric_optics': 'Atmospheric wavefront sensing', 'afm_metrology': 'Parallel AFM bounded metrology',
          'martian_geophysics': 'Martian core-mantle geophysics', 'transistor': '3D metal-oxide transistor devices'}
COLORS = {'atmospheric_optics': '#9dbbee', 'afm_metrology': '#e1b985', 'martian_geophysics': '#e59678', 'transistor': '#a8c989'}
ALIASES = {'unknown_parameters.json': 'unknowns', 'evaluator_reference.json': 'acceptance', 'lineage_contract.json': 'lineage'}
BOUNDARY = ('Author/evaluator design reference only; not an actor projection, executable procedure, task runner, solver, physical simulation or execution receipt. '
            'Navigation and operation membership do not invent chronology, control settings, specimen counts or completed services.')
WARNINGS = {
 'atmospheric_optics': 'SOURCE-INCOMPLETE: source_complete_for_entire_paper=false; main figure pixels remain uninspected and the direct-byte identity hold remains active. Seven physical branches, thirteen observed-data/analysis branches and eight numerical branches remain distinct. '
   'Atmosphere is not a handled sample. Camera acquisition retains the mount lease: jobs and records move, not mounted hardware. '
   'TIS is computational, not physical piezo scanning. Frames, windows and inferred layers are not independent specimens. Source conflicts and qualified-card gates remain unresolved.',
 'afm_metrology': 'BOUNDED INERT IMAGING / METROLOGY ONLY; not full fabrication. The calibrated array or lever remains installed while targets or coupons are exchanged. '
   'Branch tails do not unmount the retained probe. Final session teardown invalidates calibration; calibration cannot be reused between episodes. '
   'Two incomplete fabrication preparation contracts remain separately gated. Prefabricated inputs never earn historical fabrication credit. Prospective extensions are not experiments.',
 'martian_geophysics': 'CLOSED QUALIFIED FACILITY SERVICES ONLY. Twenty-six physical, four measurement-analysis, seven numerical and one data-curation branch remain distinct. '
   'Powder and glass routes, run/cohort/region identities and destructive parent retirement remain separate. Source conflicts block physical binding. '
   'Calculated values and synthetic bookkeeping are not observations or independent physical replicates; no hazard commands or recipes are supplied.',
 'transistor': 'Operation lists are UNORDERED available inventories; repeated safe transitions and causal order belong to the lifecycle contract. '
   'Separate cohorts, destructive daughters, netlists, stack identities and persistent damage are never merged into one specimen history. '
   'Closed qualified services own fabrication, chemicals, thermal and electrical processes. Ten source conflicts remain gates. '
   'Independent safe-zero receipts, cooldown and elapsed-time obligations cannot be replaced by commands, source outcomes or synthetic fixture cases.'}
KINDS = {'physical': 'PHYSICAL DESIGN', 'analysis': 'OBSERVED-DATA / DERIVED ANALYSIS', 'numerical': 'NUMERICAL ONLY · NOT RUN',
         'data_curation': 'DATA CURATION · NOT ACQUISITION', 'bounded_fabrication': 'BOUNDED FABRICATION CONTRACT · INCOMPLETE',
         'session_teardown': 'SESSION TEARDOWN OBLIGATION', 'prospective': 'PROSPECTIVE ONLY · NOT AN EXPERIMENT',
         'reference': 'REFERENCE DEPENDENCY · NOT IMPLEMENTED', 'excluded': 'EXCLUDED SCOPE'}


def clone(value): return copy.deepcopy(value)
def read(p, name): return json.loads((p / name).read_text(encoding='utf-8'))
def context_key(name): return ALIASES.get(name, name.removesuffix('.json'))
def absence(field): return 'No ' + field + ' field supplied; inspect the exact source record and qualified branch contracts. No value is inferred.'
def first(record, names, missing=None):
    for name in names:
        if name in record: return clone(record[name])
    return missing

def as_list(value): return value if isinstance(value, list) else [value]

def operation(original, index):
    """Normalize for display while retaining the ENTIRE source record in detail."""
    return {'id': original['id'], 'title': original.get('title', original['id'].replace('_', ' ').title()),
            'stage': original.get('station_id', 'Station is route-bound; inspect branch and station contracts'),
            'actions': as_list(first(original, ('robot_actions', 'actions', 'action'), absence('actions'))),
            'objects': first(original, ('sample_or_payload', 'input_kind'), absence('per-operation objects')),
            'pre': first(original, ('preconditions', 'pre_state'), absence('pre-state')),
            'post': first(original, ('postconditions', 'post_state'), absence('post-state')),
            'acceptance': first(original, ('completion_evidence', 'required_receipts', 'required_receipt_fields'), absence('completion evidence')),
            'recovery': first(original, ('failure_recovery', 'failure_action'), absence('recovery')),
            'sources': original.get('source_evidence_ids', []),
            'unknowns': first(original, ('unknown_parameter_ids', 'required_card_ids'), []),
            'provenance': first(original, ('source_vs_authored', 'authored_translation'),
                               'Authored display mapping only; scientific evidence and facility ownership remain in the full source contract'),
            'loop': None, 'detail': clone(original), 'source_file': 'operations.json', 'source_pointer': f'/operations/{index}',
            'display_mapping_basis': 'Authored display fields; detail is the exact complete source operation. Missing fields are explicit absence notices, not new predicates.',
            'display_title_basis': 'Exact source title' if 'title' in original else 'Authored navigation label from source operation ID; source supplies no title'}


def contract(label, record, filename, pointer):
    return {'type': 'condition', 'label': label, 'children': [], 'ordered': False,
            'meta': {'source_file': filename, 'source_pointer': pointer, 'source_contract': clone(record)}}


def base(p, key):
    raw = read(p, 'operations.json'); branches = read(p, 'branches.json'); prov = read(p, 'provenance.json')
    folder = f'https://github.com/openags/ScienceGym/blob/{CROSSDISCIPLINARY_COMMIT}/tasks/{p.name}/'
    evidence = prov['evidence']
    if isinstance(evidence, list): evidence = {r['id']: r for r in evidence}
    title = prov.get('title', prov.get('paper_title', prov.get('paper', {}).get('title', LABELS[key])))
    f = {'id': key, 'label': LABELS[key], 'title': title, 'doi': prov['doi'], 'color': COLORS[key],
         'source_commit': CROSSDISCIPLINARY_COMMIT, 'source_folder': folder,
         'status': BOUNDARY + ' ' + WARNINGS[key], 'source_warnings': WARNINGS[key],
         'visibility': 'author_evaluator_reference_only', 'actor_projection_implemented': False,
         'operations': [operation(o, i) for i, o in enumerate(raw['operations'])], 'routes': [], 'evidence': clone(evidence),
         'dependencies': read(p, 'dependencies.json') if (p / 'dependencies.json').exists() else {},
         'context': {'operation_policy': {k: clone(v) for k, v in raw.items() if k != 'operations'},
                     'branch_policy': {k: clone(v) for k, v in branches.items() if k != 'branches'}},
         'source_files': {fn.relative_to(p).as_posix(): {'url': folder + fn.relative_to(p).as_posix(),
                          'sha256': hashlib.sha256(fn.read_bytes()).hexdigest()} for fn in sorted(p.rglob('*.json'))}}
    for name in f['source_files']:
        if name not in ('operations.json', 'branches.json', 'dependencies.json'):
            f['context'][context_key(name)] = read(p, name)
    return f, branches


def route(f, identifier, record, filename, pointer, kind, members=(), title=None):
    if title is None: title = record.get('title', identifier) if isinstance(record, dict) else str(record)
    nodes = []
    if members:
        nodes.append({'type': 'obligations', 'label': 'Source operation inventory · no adjacency chronology',
                      'ordered': False, 'children': clone(list(members)),
                      'meta': {'order': 'Unordered inspection membership. Apply exact source phase, lifecycle and dependency contracts; no counts or schedule are instantiated.'}})
    nodes.append(contract('Exact source scope and typed obligations · unexpanded', record, filename, pointer))
    return {'id': identifier, 'label': KINDS[kind] + ' · ' + title, 'route_kind': kind, 'metadata_only': not bool(members),
            'nodes': nodes, 'basis': BOUNDARY + ' ' + WARNINGS[f['id']],
            'detail': clone(record) if isinstance(record, dict) else {'source_record': clone(record)},
            **({'detail_source_wrapper': 'source_record'} if not isinstance(record, dict) else {}),
            'source_file': filename, 'source_pointer': pointer,
            'navigation_basis': 'Authored inspection ID and label for the exact indicated source record; not an additional experiment or execution'}


def branch_kind(key, record):
    classification = record.get('classification', record.get('type'))
    if key == 'atmospheric_optics':
        if classification.startswith('physical_'): return 'physical'
        return 'numerical' if classification == 'numerical_simulation' else 'analysis'
    if key == 'martian_geophysics':
        return {'measurement_analysis': 'analysis', 'numerical_analysis': 'numerical', 'data_curation': 'data_curation'}.get(classification, 'physical')
    return 'physical'


def projection(p, key):
    f, branches = base(p, key)
    for i, record in enumerate(branches['branches']):
        r = route(f, record['id'], record, 'branches.json', f'/branches/{i}', branch_kind(key, record), record['operation_ids'])
        controls = f['context']['control_packages']['controls']
        if key in ('atmospheric_optics', 'martian_geophysics'):
            r['controls'] = [clone(c) for c in controls if c['id'] in record['control_ids']]
        elif key == 'transistor': r['controls'] = [clone(c) for c in controls if c['id'] == record['id']]
        else: r['controls'] = clone(controls)  # AFM has global scoped rules, not branch ID bindings.
        if key == 'transistor':
            r['nodes'].append(contract('Canonical lifecycle catalog · apply only each named route scope', f['context']['lifecycle_contract'], 'lifecycle_contract.json', ''))
        if key == 'afm_metrology':
            r['nodes'].append(contract('Episode custody, retained probe and calibration boundaries', f['context']['episode_input_contract'], 'episode_input_contract.json', ''))
        f['routes'].append(r)
    if key == 'afm_metrology':
        for i, record in enumerate(f['context']['preparation_routes']['routes']):
            f['routes'].append(route(f, record['id'], record, 'preparation_routes.json', f'/routes/{i}', 'bounded_fabrication', record['operation_ids'], record['paper_role']))
        i, op = next((i, o) for i, o in enumerate(f['operations']) if o['id'] == 'FINAL_SESSION_TEARDOWN')
        f['routes'].append(route(f, 'SESSION_TEARDOWN', op['detail'], 'operations.json', f'/operations/{i}', 'session_teardown', [op['id']], op['title']))
    scope = f['context']['nonmanual_scope']
    categories = {'atmospheric_optics': [('conceptual_only', 'prospective'), ('comparison_dependencies', 'reference')],
                  'afm_metrology': [('numerical_only', 'numerical'), ('prospective_not_experiments', 'prospective')],
                  'martian_geophysics': [],
                  'transistor': [('numerical_only', 'numerical'), ('prospective_not_demonstrated', 'prospective'), ('excluded', 'excluded')]}
    for field, kind in categories[key]:
        for i, record in enumerate(scope[field]):
            title = record.get('source_evidence_id', field) if isinstance(record, dict) else record
            f['routes'].append(route(f, 'SCOPE_' + field.upper() + '_' + str(i + 1), record, 'nonmanual_scope.json', f'/{field}/{i}', kind, title=title))
    f['default_route'] = branches['branches'][0]['id']
    f['summary_counts'] = dict(Counter(r['route_kind'] + '_records' for r in f['routes']))
    unknowns = f['context']['unknowns']
    f['summary_counts'].update(source_branches=len(branches['branches']), source_json_documents=len(f['source_files']),
                              unresolved_input_groups=len(first(unknowns, ('parameters', 'unknowns', 'unknown_parameters'), [])),
                              control_records=len(f['context']['control_packages']['controls']))
    return f


def operation_ids(nodes):
    result = []
    for n in nodes:
        if isinstance(n, str): result.append(n)
        elif n['type'] == 'op': result.append(n['id'])
        else: result.extend(operation_ids(n.get('children', [])))
    return result


def validate_projection(f, p):
    """Reject any mutation to source preservation or authored conservative display grammar."""
    if f != projection(p, f['id']): raise ValueError('Cross-disciplinary projection changed, omitted or invented source data or display grammar')
    ids = [o['id'] for o in f['operations']]
    if len(ids) != len(set(ids)): raise ValueError('Duplicate operation ID')
    if len(f['routes']) != len({r['id'] for r in f['routes']}): raise ValueError('Duplicate route ID')
    used = set()
    for r in f['routes']:
        members = operation_ids(r['nodes']); used.update(members)
        if not set(members) <= set(ids): raise ValueError('Unknown operation reference')
        if r['route_kind'] in ('prospective', 'reference', 'excluded') and members: raise ValueError('Reference scope gained operations')
    if used != set(ids): raise ValueError('Operation definitions missing from navigation')
    return True


def adapt(p, key):
    f = projection(p, key); validate_projection(f, p); return f

def adapt_atmospheric_optics(p): return adapt(p, 'atmospheric_optics')
def adapt_afm_metrology(p): return adapt(p, 'afm_metrology')
def adapt_martian_geophysics(p): return adapt(p, 'martian_geophysics')
def adapt_transistor(p): return adapt(p, 'transistor')
