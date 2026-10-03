"""Lossless, read-only projections for the final three published paper designs.

No episode instantiation, experimental execution, source acquisition or solver.
"""
import copy
import hashlib
import json

FINAL_MATERIALS_COMMIT = '26f402e4be797a91edce8253e4ed45bed6e01e7c'
PACKAGES = {key: key + '_operations_v2' for key in ('horn_acoustics', 'mechanical_logic', 'cold_shape')}
LABELS = {'horn_acoustics': 'Horn-like acoustic metamaterials',
          'mechanical_logic': 'Reprogrammable mechanical logic',
          'cold_shape': 'Cold-programmed shape morphing'}
COLORS = {'horn_acoustics': '#96c6a2', 'mechanical_logic': '#b4a1dc', 'cold_shape': '#73c6dc'}
ALIASES = {'unknown_parameters.json': 'unknowns', 'evaluator_reference.json': 'acceptance', 'lineage_contract.json': 'lineage'}
BOUNDARY = ('Author/evaluator design reference only; not an actor projection, task runner, solver, physical simulation or execution receipt. '
            'Missing inputs stay blocked. Physical acquisition, device-owned services, derived analysis and numerical reference scope remain distinct.')
WARNINGS = {
    'horn_acoustics': 'Horn physical prerequisites, both matched map conditions and physical/derived closure remain separate. '
                      '190 positions and ten technical readouts per position do not supply independent specimen replication. '
                      'No numerical branch earns physical campaign credit.',
    'mechanical_logic': 'ReMM source_complete is false. Main figure panels and actual movie contents remain uninspected. '
                        'Source inventory, truth-table cases and symbolic repeats do not supply an episode allocation. '
                        'Numerical gates, explanatory records and proposed extensions remain nonphysical.',
    'cold_shape': 'Chemical preparation, printing, thermal/mechanical actuation and liquid-metal filling remain closed, qualified services. '
                  'Eight actual movies and the source workbook remain uninspected. Ten and forty cycles are not independent specimen counts. '
                  'Derived parameter fits are not independent validation; no numerical result is a physical measurement.'}
KINDS = {'physical': 'PHYSICAL DESIGN', 'numerical': 'NUMERICAL / THEORY · NOT RUN',
         'analysis': 'DERIVED PARAMETER FIT · NOT RUN / NOT INDEPENDENT VALIDATION',
         'reference': 'EXPLANATORY REFERENCE · NOT PHYSICAL', 'proposal': 'FUTURE PROPOSAL · NOT IMPLEMENTED',
         'extension': 'SOURCE-DESCRIBED EXTENSION · NOT A PHYSICAL BRANCH'}
COMMON = {'title': 'title', 'actions': 'actions', 'pre': 'preconditions', 'post': 'postconditions',
          'acceptance': 'observable_completion', 'sources': 'evidence_ids', 'recovery': 'failure_handling',
          'unknowns': 'unknown_parameter_ids', 'provenance': 'authorship'}
FIELDS = {'horn_acoustics': {**COMMON, 'stage': 'station_id', 'objects': 'object_roles'},
          'mechanical_logic': {**COMMON, 'stage': 'location_id', 'objects': 'target_asset_roles'},
          'cold_shape': {**COMMON, 'actions': 'robot_actions', 'stage': 'station_id', 'objects': 'objects',
                         'sources': 'source_evidence_ids', 'recovery': 'failure_recovery', 'provenance': 'authored_translation'}}
DEFAULTS = {'horn_acoustics': 'B_WITH', 'mechanical_logic': 'NOR', 'cold_shape': 'MEMORY_COLD'}
LOGIC_KINDS = {'numerical_model': 'numerical', 'numerical_only': 'numerical', 'numerical_theoretical': 'numerical',
               'explanatory': 'reference', 'future_proposal': 'proposal', 'source_described_extension': 'extension'}


def read(p, name): return json.loads((p / name).read_text(encoding='utf-8'))
def context_key(name): return ALIASES.get(name, name.removesuffix('.json'))
def group(label, children=(), meta=None, kind='condition'):
    return {'type': kind, 'label': label, 'children': list(children), 'ordered': False,
            'meta': copy.deepcopy(meta or {}), **({'symbolic': True} if kind == 'loop' else {})}
def contract(label, value, filename, pointer, kind='condition'):
    return group(label, meta={'source_file': filename, 'source_pointer': pointer, 'source_contract': value}, kind=kind)
def op_ids(nodes):
    result = []
    for node in nodes:
        if isinstance(node, str): result.append(node)
        elif node['type'] == 'op': result.append(node['id'])
        else: result.extend(op_ids(node.get('children', [])))
    return result


def operation(key, original, index):
    fields = FIELDS[key]
    return {'id': original['id'], **{k: copy.deepcopy(original[v]) for k, v in fields.items()},
            'detail': {k: copy.deepcopy(v) for k, v in original.items() if k not in set(fields.values()) | {'id'}},
            'source_file': 'operations.json', 'source_pointer': '/operations/' + str(index), 'loop': None}


def base(p, key):
    raw = read(p, 'operations.json'); branches = read(p, 'branches.json'); prov = read(p, 'provenance.json')
    folder = f'https://github.com/openags/ScienceGym/blob/{FINAL_MATERIALS_COMMIT}/tasks/{p.name}/'
    evidence = prov['evidence']
    if isinstance(evidence, list): evidence = {record['id']: record for record in evidence}
    f = {'id': key, 'label': LABELS[key], 'title': prov.get('title', prov.get('identity', {}).get('title')),
         'doi': prov['doi'], 'color': COLORS[key], 'source_commit': FINAL_MATERIALS_COMMIT, 'source_folder': folder,
         'status': BOUNDARY + ' ' + WARNINGS[key], 'visibility': 'author_evaluator_reference_only',
         'actor_projection_implemented': False, 'source_warnings': WARNINGS[key],
         'operations': [operation(key, o, i) for i, o in enumerate(raw['operations'])], 'routes': [],
         'evidence': copy.deepcopy(evidence), 'dependencies': read(p, 'dependencies.json'),
         'context': {'operation_policy': {k: v for k, v in raw.items() if k != 'operations'},
                     'branch_policy': {k: v for k, v in branches.items() if k != 'branches'}},
         'source_files': {fn.relative_to(p).as_posix(): {'url': folder + fn.relative_to(p).as_posix(),
                          'sha256': hashlib.sha256(fn.read_bytes()).hexdigest()} for fn in sorted(p.rglob('*.json'))}}
    for name in f['source_files']:
        if name not in ('operations.json', 'branches.json', 'dependencies.json'):
            f['context'][context_key(name)] = read(p, name)
    return f, branches


def route(f, record, pointer, kind, nodes, filename='branches.json'):
    title = record.get('title', record['id'])
    label = KINDS[kind]
    if f['id'] == 'horn_acoustics' and record['id'] == 'B_COMPARE_CLOSE':
        label = 'PHYSICAL / DERIVED ANALYSIS CLOSURE · NOT EXECUTED'
    return {'id': record['id'], 'label': label + ' · ' + title, 'route_kind': kind,
            'metadata_only': not bool(op_ids(nodes)), 'nodes': nodes,
            'basis': f['status'] + ' Operation lists are unordered membership. Only declared causal, condition and phase constraints impose order. '
                     'Symbolic loops preserve their exact scope without expanding counts or inventing specimen, transfer or execution instances.',
            'detail': copy.deepcopy(record), 'source_file': filename, 'source_pointer': pointer}


def controls(f, identifier):
    key = f['id']; field = 'controls' if key == 'cold_shape' else 'packages'
    scope = {'horn_acoustics': 'required_branches', 'mechanical_logic': 'branches', 'cold_shape': 'scope'}[key]
    # Preserve the original scope, including non-list descriptive scopes, in context.
    return [copy.deepcopy(c) for c in f['context']['control_packages'][field]
            if isinstance(c[scope], list) and identifier in c[scope]]


def branch_nodes(f, record, i):
    key = f['id']; pointer = f'/branches/{i}'
    nodes = [group('Operation membership · no chronological adjacency', record['operation_ids'],
                   {'order': 'Only declared prerequisites and qualified occurrence scopes constrain order; display adjacency is not an edge.'}, 'obligations')]
    if key == 'horn_acoustics':
        for j, text in enumerate(record.get('loops', [])):
            nodes.append(contract('Unexpanded source repeat · not independent replication', text, 'branches.json', pointer + f'/loops/{j}', 'loop'))
        for j, scoped in enumerate(f['dependencies']['condition_scoped_edges']):
            # Scope is preserved as source metadata; the branch list never implies both panel states.
            nodes.append(contract('Condition-scoped dependency · applies only to the named condition', scoped, 'dependencies.json', f'/condition_scoped_edges/{j}'))
    elif key == 'mechanical_logic':
        for j, loop in enumerate(f['dependencies']['loops']):
            if record['id'] in loop['branch_ids']:
                nodes.append(contract('Unexpanded scoped loop · ' + loop['id'], loop, 'dependencies.json', f'/loops/{j}', 'loop'))
    else:
        matches = [(j, c) for j, c in enumerate(f['context']['condition_requirements']['branches']) if c['branch_id'] == record['id']]
        if len(matches) != 1: raise ValueError('Cold-shape branch must have exactly one condition requirement record')
        j, requirements = matches[0]
        nodes.append(contract('Exact condition dimensions and required phase order · no invented operation schedule', requirements,
                              'condition_requirements.json', f'/branches/{j}'))
        nodes.append(group('Global loop catalog · apply only the stated source scope, never all loops to every branch',
                           [contract('Unexpanded source scope · ' + loop['id'], loop, 'dependencies.json', f'/loops/{j}', 'loop')
                            for j, loop in enumerate(f['dependencies']['loops'])]))
        nodes.append(contract('Closed qualified station/service boundaries · no hazardous robot process recipe',
                              f['context']['station_contracts'], 'station_contracts.json', ''))
    return nodes


def projection(p, key):
    f, branches = base(p, key); f['default_route'] = DEFAULTS[key]
    for i, record in enumerate(branches['branches']):
        kind = 'numerical' if record.get('kind') == 'theory_or_numerical_only' else 'physical'
        nodes = (branch_nodes(f, record, i) if kind == 'physical' else
                 [contract('Source numerical disposition · no physical operations or measurements', record, 'branches.json', f'/branches/{i}')])
        r = route(f, record, f'/branches/{i}', kind, nodes)
        if kind == 'physical': r['controls'] = controls(f, record['id'])
        f['routes'].append(r)
    if key != 'horn_acoustics':
        field = 'dispositions' if key == 'mechanical_logic' else 'items'
        for i, record in enumerate(f['context']['nonmanual_scope'][field]):
            if key == 'mechanical_logic': kind = LOGIC_KINDS[record['disposition']]
            else: kind = 'analysis' if record['id'] in ('N_DMA_FIT', 'N_RATE_FIT') else 'numerical'
            r = route(f, record, f'/{field}/{i}', kind,
                      [contract(KINDS[kind] + ' · exact source disposition', record, 'nonmanual_scope.json', f'/{field}/{i}')],
                      'nonmanual_scope.json')
            if kind == 'analysis':
                r['display_classification_basis'] = ('Authored navigation subtype for source-described parameter identification. '
                                                     'The original numerical_or_analytical_only classification is unchanged in detail; this is not an additional source branch.')
            f['routes'].append(r)
    counts = {kind + '_records': sum(r['route_kind'] == kind for r in f['routes']) for kind in KINDS}
    counts['unresolved_input_groups'] = len(f['context']['unknowns']['unknowns'])
    counts['control_records'] = len(f['context']['control_packages']['controls' if key == 'cold_shape' else 'packages'])
    counts['symbolic_loop_contracts'] = (sum(len(r.get('loops', [])) for r in branches['branches']) if key == 'horn_acoustics'
                                       else len(f['dependencies']['loops']))
    f['summary_counts'] = {k: v for k, v in counts.items() if v}
    return f


def validate_projection(f, p):
    if f != projection(p, f['id']): raise ValueError('Final-materials projection changed, omitted or invented source data or display grammar')
    ids = {o['id'] for o in f['operations']}
    if len(ids) != len(f['operations']): raise ValueError('Duplicate operation ID')
    if len({r['id'] for r in f['routes']}) != len(f['routes']): raise ValueError('Duplicate route ID')
    for r in f['routes']:
        if not set(op_ids(r['nodes'])) <= ids: raise ValueError('Unknown operation reference')
        if r['route_kind'] != 'physical' and op_ids(r['nodes']): raise ValueError('Nonphysical disposition gained physical operations')
    return True


def adapt(p, key):
    f = projection(p, key); validate_projection(f, p); return f

def adapt_horn_acoustics(p): return adapt(p, 'horn_acoustics')
def adapt_mechanical_logic(p): return adapt(p, 'mechanical_logic')
def adapt_cold_shape(p): return adapt(p, 'cold_shape')
