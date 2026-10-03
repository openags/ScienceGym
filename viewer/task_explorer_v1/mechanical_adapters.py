"""Lossless read-only mechanical design projections. Never instantiate or run tasks."""
import copy
import hashlib
import json

MECHANICAL_COMMIT = '43a185dacb02a979148bee93d5d9559e569086f3'
PACKAGES = {'origami_memory': 'origami_memory_operations_v2',
            'ring_origami': 'ring_origami_operations_v2',
            'mechanical_backprop': 'mechanical_backprop_operations_v2'}
LABELS = {'origami_memory': 'Origami mechanical memory', 'ring_origami': 'Reconfigurable ring origami',
          'mechanical_backprop': 'Mechanical backpropagation'}
COLORS = {'origami_memory': '#cc95c5', 'ring_origami': '#98c77b', 'mechanical_backprop': '#eba285'}
ALIASES = {'unknown_parameters.json': 'unknowns', 'evaluator_reference.json': 'acceptance',
           'lineage_contract.json': 'lineage'}
BOUNDARY = ('Author/evaluator design reference only; not an actor projection, task runner, '
            'solver, physical simulation or execution receipt. Missing inputs stay blocked. '
            'Numerical training is not physical self-updating hardware; derived torque is not direct torque measurement.')
KINDS = {'physical': 'PHYSICAL DESIGN', 'campaign': 'CAMPAIGN ACCOUNTING',
         'prerequisite': 'SHARED PREPARATION', 'numerical': 'NUMERICAL / THEORY · NOT RUN',
         'analysis': 'DERIVED ANALYSIS · NOT DIRECT MEASUREMENT', 'proposal': 'PROPOSAL / CONCEPT · NOT IMPLEMENTED'}
FIELDS = {
    'origami_memory': {'title': 'title', 'stage': 'location_id', 'actions': 'actions',
                      'objects': 'manipulated_objects_tools', 'pre': 'preconditions', 'post': 'completion_state',
                      'sources': 'evidence_ids', 'recovery': 'recoveries', 'unknowns': 'unknown_parameter_ids', 'provenance': 'provenance'},
    'ring_origami': {'stage': 'station_id', 'actions': 'action', 'objects': 'objects',
                    'pre': 'preconditions', 'acceptance': 'completion_evidence', 'sources': 'source_evidence_ids',
                    'recovery': 'failure_and_recovery', 'unknowns': 'unknown_input_ids'},
    'mechanical_backprop': {'title': 'title', 'stage': 'source_station', 'actions': 'actions',
                           'objects': 'manipulated_objects_tools', 'pre': 'preconditions', 'post': 'completion_state',
                           'sources': 'evidence_ids', 'recovery': 'recoveries', 'unknowns': 'unknown_parameter_ids', 'provenance': 'provenance'},
}

def read(p, name):
    return json.loads((p / name).read_text(encoding='utf-8'))

def context_key(name):
    return ALIASES.get(name, name.removesuffix('.json'))

def operation(key, original, index):
    fields = FIELDS[key]
    mapped = {'id': original['id'], **{k: copy.deepcopy(original[v]) for k, v in fields.items()},
              'source_file': 'operations.json', 'source_pointer': '/operations/' + str(index), 'loop': None}
    used = set(fields.values()) | {'id'}
    mapped['detail'] = {k: copy.deepcopy(v) for k, v in original.items() if k not in used}
    if key == 'ring_origami':
        mapped['actions'] = [copy.deepcopy(original['action'])]
        mapped['title'] = original['id'].replace('_', ' ').title()
        mapped['detail']['display_title_basis'] = 'Authored navigation label from operation ID; source supplies no title'
        mapped['provenance'] = {'translation_kind': original['translation_kind']}
        mapped['post'] = ['No postconditions or completion_state field supplied; completion evidence is separate']
    else:
        mapped['acceptance'] = ['No separate acceptance field supplied; inspect the source completion state and evaluator reference']
    return mapped

def group(label, children=(), meta=None, kind='group', ordered=False):
    return {'type': kind, 'label': label, 'children': list(children), 'ordered': ordered,
            'meta': copy.deepcopy(meta or {}), **({'symbolic': True} if kind == 'loop' else {})}

def contract(label, value, kind='condition'):
    return group(label, meta={'source_contract': value}, kind=kind)

def membership(ids):
    return group('Capability membership · not chronology or completed work', ids,
                 {'order': 'Source operation membership only. Apply scoped dependencies and conditional gates; no list adjacency is a causal edge.'}, 'obligations')

def route(record, pointer, kind, nodes, filename='branches.json', route_id=None, title=None):
    return {'id': route_id or record['id'], 'label': KINDS[kind] + ' · ' + (title or record.get('title', record.get('id', 'Source contract'))),
            'route_kind': kind, 'metadata_only': not bool(op_ids(nodes)), 'nodes': nodes,
            'basis': BOUNDARY + ' Typed bodies are unexpanded templates, with source-declared nesting, bindings and concurrency retained. Campaigns preserve independent branch identities.',
            'detail': copy.deepcopy(record), 'source_file': filename, 'source_pointer': pointer}

def op_ids(nodes):
    result = []
    for node in nodes:
        if isinstance(node, str): result.append(node)
        elif node['type'] == 'op': result.append(node['id'])
        else: result.extend(op_ids(node.get('children', [])))
    return result

def base(p, key):
    raw = read(p, 'operations.json'); branches = read(p, 'branches.json'); prov = read(p, 'provenance.json')
    folder = f'https://github.com/openags/ScienceGym/blob/{MECHANICAL_COMMIT}/tasks/{p.name}/'
    evidence = prov['evidence']
    if isinstance(evidence, list): evidence = {entry['id']: entry for entry in evidence}
    f = {'id': key, 'label': LABELS[key], 'title': prov.get('title', prov.get('paper', {}).get('title')),
         'doi': prov['doi'], 'color': COLORS[key], 'source_commit': MECHANICAL_COMMIT, 'source_folder': folder,
         'status': BOUNDARY, 'visibility': 'author_evaluator_reference_only', 'actor_projection_implemented': False,
         'operations': [operation(key, op, i) for i, op in enumerate(raw['operations'])],
         'routes': [], 'evidence': copy.deepcopy(evidence), 'dependencies': read(p, 'dependencies.json'),
         'context': {'operation_policy': {k: v for k, v in raw.items() if k != 'operations'},
                     'branch_policy': {k: v for k, v in branches.items() if k != 'branches'}},
         'source_files': {fn.relative_to(p).as_posix(): {'url': folder + fn.relative_to(p).as_posix(),
                          'sha256': hashlib.sha256(fn.read_bytes()).hexdigest()}
                          for fn in sorted(p.rglob('*.json'))}}
    for name in f['source_files']:
        if name not in ('operations.json', 'branches.json', 'dependencies.json'):
            f['context'][context_key(name)] = read(p, name)
    return f, branches

def nonmanual_kind(key, record):
    if key == 'ring_origami':
        return {'N_MODEL': 'numerical', 'N_APPLICATIONS': 'proposal', 'N_TORQUE_DERIVATION': 'analysis'}[record['id']]
    classification = record['classification']
    return 'proposal' if classification in ('proposed_not_performed', 'conceptual_extension', 'proposed_not_implemented', 'numerical_readout_proposal') else 'numerical'

def append_nonmanual(f, key):
    field = 'entries' if key == 'ring_origami' else 'items'
    for i, record in enumerate(f['context']['nonmanual_scope'][field]):
        kind = nonmanual_kind(key, record)
        f['routes'].append(route(record, f'/{field}/{i}', kind,
                          [contract(KINDS[kind] + ' · source disposition', record)], 'nonmanual_scope.json'))

def origami_routes(f, branches):
    routes = []
    for i, record in enumerate(branches['branches']):
        kind = 'campaign' if 'subbranch_ids' in record else 'physical'
        nodes = [membership(record['operation_ids'])]
        nodes.extend(contract(loop['loop_id'] + ' · unexpanded source contract', loop, 'loop') for loop in record['loops'])
        nodes.append(contract('Shared preparation loops · actual parts, joints and cell slots retain identities', branches['shared_preparation_loops'], 'loop'))
        if kind == 'campaign': nodes.append(contract('Independent branch accounting · no merged specimen history', record['subbranch_ids']))
        routes.append(route(record, f'/branches/{i}', kind, nodes))
    return routes

def ring_nodes(items, bindings=None, pointer=''):
    """Project the explicit source grammar; loops/conditionals are never expanded."""
    bindings = bindings or {}; nodes = []
    for i, item in enumerate(items):
        source = {'source_file': 'branches.json', 'source_pointer': pointer + '/' + str(i), 'source_node': copy.deepcopy(item)}
        if isinstance(item, str):
            oid = bindings[item] if item.startswith('@') else item
            nodes.append({'type': 'op', 'id': oid, 'meta': {**source, **({'macro_binding': {item: oid}} if item.startswith('@') else {})}})
        elif 'operation' in item:
            nodes.append({'type': 'op', 'id': item['operation'], 'meta': source})
        elif 'concurrent' in item:
            nodes.append(group('Concurrent source obligations · safe remote observation', ring_nodes(item['concurrent'], bindings, pointer + f'/{i}/concurrent'), source, 'obligations'))
        elif 'loop' in item:
            children = ring_nodes(item['body'], bindings, pointer + f'/{i}/body')
            if isinstance(item.get('postprocess'), dict):
                post = item['postprocess']
                children.append(group('Conditional postprocessing only · no inherited resin default',
                                      ring_nodes(post['body'], bindings, pointer + f'/{i}/postprocess/body'),
                                      {'source_contract': post}, 'condition', True))
            nodes.append(group(item['loop'] + ' · one unexpanded body template', children, source, 'loop', True))
        else: raise ValueError('Unrecognized ring source node: ' + repr(item))
    return nodes

def ring_routes(f, branches):
    routes = []
    for i, record in enumerate(branches['branches']):
        pointer = f'/branches/{i}'
        trial = group('For each attempt · no specimen count inferred',
                      ring_nodes(record['test_body'], record['operation_bindings'], pointer + '/test_body'),
                      {'source_contract': record['trial_loop']}, 'loop', True)
        condition = group('For each finite condition · no historical cross-product inferred',
                          [contract('Required configuration transition · new specimen or verified reuse', record['condition_transition']), trial],
                          {'conditions': record['conditions'], 'condition_count_policy': record['condition_count_policy'],
                           'condition_expansion_contract': branches['condition_expansion_contract']}, 'loop', True)
        nodes = [contract('Required preparation · open the separate preparation view',
                          {'preparation_route': record['preparation_route'], 'preparation_product_requirement': record['preparation_product_requirement']}),
                 group('Source-listed assembly operations', ring_nodes(record['assembly_operations'], pointer=pointer + '/assembly_operations'), ordered=True), condition,
                 group('Source closure obligations', ring_nodes(record['closure_operations'], pointer=pointer + '/closure_operations'), ordered=True),
                 contract('Actual station changes require qualified physical TRANSFER instances', record['transport_rule'])]
        if 'upstream_measurement_dependency' in record:
            nodes.append(contract('Semi-experimental torque · matched measured parents, not direct torque measurement', record['upstream_measurement_dependency']))
        routes.append(route(record, pointer, 'physical', nodes))
    for name, record in branches['preparation_routes'].items():
        pointer = '/preparation_routes/' + name
        routes.append(route(record, pointer, 'prerequisite',
                      [group('Source preparation tree · unexpanded loops and conditional processing',
                             ring_nodes(record['steps'], pointer=pointer + '/steps'), ordered=True)],
                      route_id=name, title=record['goal']))
    record = branches['campaign']
    routes.append(route(record, '/campaign', 'campaign', [contract('Fourteen independent physical branch obligations', record)]))
    return routes

def backprop_nodes(items, transfers, pointer):
    nodes = []
    for i, item in enumerate(items):
        source = {'source_file': 'reference_routes.json', 'source_pointer': pointer + '/' + str(i), 'source_node': copy.deepcopy(item)}
        if item['kind'] == 'operation': nodes.append({'type': 'op', 'id': item['operation_id'], 'meta': source})
        elif item['kind'] == 'transfer':
            t = transfers[item['transfer_id']]
            nodes.append({'type': 'op', 'id': t['operation_id'], 'meta': {**source, 'transfer_contract': copy.deepcopy(t)}})
        elif item['kind'] in ('repeat', 'for_each'):
            nodes.append(group(item['variable'] + ' · one unexpanded source body',
                               backprop_nodes(item['body'], transfers, pointer + f'/{i}/body'), source, 'loop', True))
        else: raise ValueError('Unrecognized backprop source node: ' + repr(item))
    return nodes

def backprop_routes(f, branches):
    references = f['context']['reference_routes']; transfers = {t['id']: t for t in references['transfers']}
    routes = []
    for i, record in enumerate(branches['branches']):
        if record['role'] == 'campaign':
            nodes = [contract('Independent source-matched campaign obligations', references['campaign']), membership(record['operation_ids'])]
            kind = 'campaign'
        else:
            matches = [(j, r) for j, r in enumerate(references['routes']) if r['id'] == record['reference_route_id'] and r['branch_id'] == record['id']]
            if len(matches) != 1: raise ValueError('Backprop branch must resolve exactly one typed source tree')
            j, reference = matches[0]
            nodes = [group('Source-authored typed reference tree · not robot execution or physical self-updating',
                           backprop_nodes(reference['body'], transfers, f'/routes/{j}/body'),
                           {'source_file': 'reference_routes.json', 'source_pointer': f'/routes/{j}',
                            'source_contract': reference, 'semantics': references['semantics']}, ordered=True)]
            kind = 'physical'
        routes.append(route(record, f'/branches/{i}', kind, nodes))
    return routes

ROUTE_BUILDERS = {'origami_memory': origami_routes, 'ring_origami': ring_routes, 'mechanical_backprop': backprop_routes}
DEFAULTS = {'origami_memory': 'ONE_BIT_TORQUE', 'ring_origami': 'TRI_TORSION', 'mechanical_backprop': 'GRADIENT_SEPARATE'}

def summary(f):
    counts = {kind + '_records': sum(r['route_kind'] == kind for r in f['routes']) for kind in KINDS}
    counts['unresolved_input_groups'] = len(f['context']['unknowns']['parameters' if f['id'] == 'ring_origami' else 'unknowns'])
    counts['dependency_' + ('rules' if f['id'] == 'ring_origami' else 'edges')] = len(f['dependencies'].get('rules', f['dependencies'].get('edges', [])))
    return {k: v for k, v in counts.items() if v}

def adapt(p, key):
    f, branches = base(p, key)
    f['default_route'] = DEFAULTS[key]
    f['routes'] = ROUTE_BUILDERS[key](f, branches)
    append_nonmanual(f, key)
    f['summary_counts'] = summary(f)
    validate_projection(f, p)
    return f

def validate_projection(f, p):
    """Exact unpooled projection equality; rejects altered source facts and view grammar."""
    key = f['id']; expected, branches = base(p, key)
    expected['default_route'] = DEFAULTS[key]
    expected['routes'] = ROUTE_BUILDERS[key](expected, branches)
    append_nonmanual(expected, key)
    expected['summary_counts'] = summary(expected)
    if f != expected: raise ValueError('Mechanical projection changed, omitted or invented source data, metadata, route binding or boundary')
    ids = {o['id'] for o in f['operations']}
    if len(ids) != len(f['operations']): raise ValueError('Duplicate operation ID')
    if len({r['id'] for r in f['routes']}) != len(f['routes']): raise ValueError('Duplicate route ID')
    for r in f['routes']:
        if not set(op_ids(r['nodes'])) <= ids: raise ValueError('Unknown operation reference')
        if r['source_file'] == 'nonmanual_scope.json' and op_ids(r['nodes']): raise ValueError('Nonmanual disposition gained physical steps')
    return True

def adapt_origami_memory(p): return adapt(p, 'origami_memory')
def adapt_ring_origami(p): return adapt(p, 'ring_origami')
def adapt_mechanical_backprop(p): return adapt(p, 'mechanical_backprop')
