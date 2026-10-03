"""Lossless assembly design projections. Read-only templates, never task execution."""
import copy
import hashlib
import json

ASSEMBLY_COMMIT = '41c4c52cfcf9d5b222404f2fd7ed9d6553f807cb'
PACKAGES = {key: key + '_operations_v2' for key in ('granular_assembly', 'beaded', 'thermal_jamming')}
LABELS = {'granular_assembly': 'Momentum-driven granular assembly', 'beaded': 'Beaded mechanical metamaterials',
          'thermal_jamming': 'Thermo-responsive particle jamming'}
COLORS = {'granular_assembly': '#d9b16d', 'beaded': '#79bfd1', 'thermal_jamming': '#dc8d83'}
ALIASES = {'unknown_parameters.json': 'unknowns', 'evaluator_reference.json': 'acceptance', 'lineage_contract.json': 'lineage'}
BOUNDARY = ('Author/evaluator design reference only; not an actor projection, task runner, solver, physical simulation or execution receipt. '
            'Missing inputs stay blocked. Preparation, device processes, measured data and numerical/reference scope remain distinct.')
KINDS = {'physical': 'PHYSICAL DESIGN', 'campaign': 'CAMPAIGN ACCOUNTING',
         'numerical': 'NUMERICAL / THEORY · NOT RUN', 'analysis': 'EXTERNAL ANALYSIS · NOT RUN',
         'reference': 'REFERENCE CONTEXT · NOT MEASURED', 'external': 'EXTERNAL INPUT / PREPARATION · NOT SUPPLIED',
         'device': 'DEVICE-OWNED SCOPE · NOT ROBOT LABOR'}
COMMON = {'title': 'label', 'stage': 'station', 'actions': 'robot_actions', 'objects': 'manipulated_objects_and_tools',
          'pre': 'preconditions', 'post': 'completion_state', 'acceptance': 'completion_evidence',
          'sources': 'source_refs', 'recovery': 'failure_handling', 'unknowns': 'required_unknowns'}
FIELDS = {'granular_assembly': {**COMMON, 'provenance': 'provenance'},
          'thermal_jamming': {**COMMON, 'provenance': 'provenance_class'},
          'beaded': {'title': 'title', 'stage': 'location_id', 'actions': 'actions', 'objects': 'manipulated_objects',
                     'pre': 'preconditions', 'post': 'postconditions', 'acceptance': 'success_evidence',
                     'sources': 'evidence_ids', 'recovery': 'recovery', 'unknowns': 'unknown_parameter_ids', 'provenance': 'provenance'}}
DEFAULTS = {'granular_assembly': 'QR_SHAKING', 'beaded': 'CHAIN_DILATION', 'thermal_jamming': 'CYCLE_PULL'}
NONMANUAL = {
    'granular_assembly': {'N_SPACE_SIM': 'numerical', 'N_PIXEL_CONTEXT': 'reference', 'N_ROT_ELLIPSE': 'numerical',
                         'N_PUF_COMPUTE': 'analysis', 'N_SURFACE_ENERGY': 'reference', 'N_HARDWARE': 'external'},
    'beaded': {'N_CAPSTAN': 'numerical', 'N_RING_MODEL': 'numerical', 'N_SHELL_PROJECTION': 'numerical',
               'N_DOME_DESIGN': 'external', 'N_OUTLOOK': 'reference', 'N_HISTORY': 'reference',
               'N_DEVICE': 'device', 'N_VIEWER': 'reference'}}


def read(p, filename): return json.loads((p / filename).read_text(encoding='utf-8'))
def context_key(filename): return ALIASES.get(filename, filename.removesuffix('.json'))
def ptr(text): return text.replace('~', '~0').replace('/', '~1')
def group(label, children=(), meta=None, kind='group', ordered=False):
    return {'type': kind, 'label': label, 'children': list(children), 'ordered': ordered,
            'meta': copy.deepcopy(meta or {}), **({'symbolic': True} if kind == 'loop' else {})}
def contract(label, value, kind='condition'):
    return group(label, meta={'source_contract': value}, kind=kind)
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


def route(record, pointer, kind, nodes, filename='branches.json', identifier=None, title=None):
    return {'id': identifier or record['id'], 'label': KINDS[kind] + ' · ' + (title or record.get('title', record.get('goal', record.get('scope', record.get('id', 'Source scope'))))),
            'route_kind': kind, 'metadata_only': not bool(op_ids(nodes)), 'nodes': nodes,
            'basis': BOUNDARY + ' Membership lists do not assert chronology. Source-declared typed sequence, choice, loop and dispatch scopes are displayed without selecting alternatives or instantiating counts.',
            'detail': copy.deepcopy(record), 'source_file': filename, 'source_pointer': pointer}


def base(p, key):
    raw = read(p, 'operations.json'); branches = read(p, 'branches.json'); prov = read(p, 'provenance.json')
    folder = f'https://github.com/openags/ScienceGym/blob/{ASSEMBLY_COMMIT}/tasks/{p.name}/'
    evidence = prov.get('evidence', prov.get('references'))
    if isinstance(evidence, list): evidence = {record['id']: record for record in evidence}
    field = 'branches' if key == 'beaded' else 'configurations'
    f = {'id': key, 'label': LABELS[key], 'title': prov.get('paper', {}).get('title', {'beaded': 'Beaded metamaterials', 'thermal_jamming': 'Thermo-responsive jamming by particle shape change'}.get(key, LABELS[key])),
         'doi': prov.get('doi', prov.get('paper', {}).get('doi')), 'color': COLORS[key],
         'source_commit': ASSEMBLY_COMMIT, 'source_folder': folder, 'status': BOUNDARY,
         'visibility': 'author_evaluator_reference_only', 'actor_projection_implemented': False,
         'operations': [operation(key, o, i) for i, o in enumerate(raw['operations'])],
         'routes': [], 'evidence': copy.deepcopy(evidence), 'dependencies': read(p, 'dependencies.json'),
         'context': {'operation_policy': {k: v for k, v in raw.items() if k != 'operations'},
                     'branch_policy': {k: v for k, v in branches.items() if k != field}},
         'source_files': {fn.relative_to(p).as_posix(): {'url': folder + fn.relative_to(p).as_posix(),
                          'sha256': hashlib.sha256(fn.read_bytes()).hexdigest()} for fn in sorted(p.rglob('*.json'))}}
    for name in f['source_files']:
        if name not in ('operations.json', 'branches.json', 'dependencies.json'):
            f['context'][context_key(name)] = read(p, name)
    return f, branches


def membership_routes(f, branches):
    """One membership view per configuration; source repetition remains metadata."""
    routes = []
    control_field = 'control_packages' if f['id'] == 'granular_assembly' else 'controls'
    controls = {c['id']: c for c in f['context']['control_packages'][control_field]}
    for i, record in enumerate(branches['configurations']):
        matches = [(j, d) for j, d in enumerate(f['dependencies']['routes']) if d['configuration_id'] == record['id']]
        if len(matches) != 1: raise ValueError('Configuration must have exactly one scoped dependency record')
        j, dependencies = matches[0]
        nodes = [group('Operation membership · not chronology', record['operation_ids'],
                       {'order': 'Only source-declared causal edges and gates constrain order. Display adjacency is not an edge.'}, 'obligations')]
        nodes.append(group('Configuration-specific causal edges, transfer obligations and exceptions',
                           meta={'source_file': 'dependencies.json', 'source_pointer': f'/routes/{j}', 'source_contract': dependencies}, kind='condition'))
        if 'repeat_scope' in dependencies:
            nodes.append(contract('Sample / condition / repeat / cycle allocation · counts remain unresolved', dependencies['repeat_scope'], 'loop'))
        for loop in dependencies.get('loop_contracts', []):
            nodes.append(contract('Unexpanded source loop · no default repetition count', loop, 'loop'))
        ids = record.get('control_package_ids', record.get('required_controls', []))
        r = route(record, f'/configurations/{i}', 'physical', nodes)
        r['controls'] = [copy.deepcopy(controls[identifier]) for identifier in ids]
        routes.append(r)
    return routes


def beaded_node(item, pointer):
    """Exact source grammar with mutually exclusive choice arms displayed separately.

    Recursive fields are represented by child nodes; all other source attributes
    are retained in metadata. The full original tree also remains in context.
    """
    typ = item['type']
    source = {'source_file': 'routes.json', 'source_pointer': pointer}
    if typ == 'operation':
        return {'type': 'op', 'id': item['operation_id'], 'meta': {**source, 'source_node': copy.deepcopy(item)}}
    child_fields = {'sequence': {'steps'}, 'loop': {'body'}, 'choice': {'alternatives'}, 'dispatch': set()}
    if typ not in child_fields: raise ValueError('Unknown beaded source node type: ' + typ)
    meta = {**source, 'source_attributes': {k: copy.deepcopy(v) for k, v in item.items() if k not in child_fields[typ]}}
    if typ == 'sequence':
        return group('Source-authored sequence · one template only',
                     [beaded_node(x, pointer + '/steps/' + str(i)) for i, x in enumerate(item['steps'])], meta, ordered=True)
    if typ == 'loop':
        return group(item['loop_id'] + ' · one unexpanded body template',
                     [beaded_node(item['body'], pointer + '/body')], meta, 'loop', True)
    if typ == 'choice':
        return group('Exclusive alternatives · ' + item['input'],
                     [group('Alternative: ' + key, [beaded_node(value, pointer + '/alternatives/' + ptr(key))],
                            {'selection': key, 'choice_input': item['input'], 'rule': 'Inspect all arms; execute only the selected qualified alternative'}, 'condition')
                      for key, value in item['alternatives'].items()], meta, 'condition')
    return group('Independent branch dispatch · no merged specimen history', meta=meta, kind='condition')


def beaded_routes(f, branches):
    routes = []
    for i, record in enumerate(branches['branches']):
        matches = [(j, r) for j, r in enumerate(f['context']['routes']['routes']) if r['id'] == record['id']]
        if len(matches) != 1: raise ValueError('Beaded branch must resolve exactly one typed route')
        j, source = matches[0]
        kind = 'campaign' if source['tree']['type'] == 'dispatch' else 'physical'
        nodes = [beaded_node(source['tree'], f'/routes/{j}/tree')]
        if record.get('conditional_recovery_operation_ids'):
            nodes.append(group('Conditional recovery only · not a required normal step', record['conditional_recovery_operation_ids'],
                               {'source_file': 'branches.json', 'source_pointer': f'/branches/{i}/conditional_recovery_operation_ids'}, 'condition'))
        r = route(record, f'/branches/{i}', kind, nodes)
        r['controls'] = [copy.deepcopy(c) for c in f['context']['control_packages']['packages'] if record['id'] in c['branch_ids']]
        routes.append(r)
    return routes


def append_nonmanual(f):
    key = f['id']; scope = f['context']['nonmanual_scope']
    if key != 'thermal_jamming':
        for i, record in enumerate(scope['items']):
            kind = NONMANUAL[key][record['id']]
            f['routes'].append(route(record, f'/items/{i}', kind, [contract(KINDS[kind] + ' · source disposition', record)], 'nonmanual_scope.json'))
    else:
        # Source sections have no IDs. Navigation labels are explicitly authored
        # section identifiers, not extra source branches, operations or runs.
        for field, kind in [('computational_only', 'numerical'), ('device_owned', 'device'), ('reference_only', 'reference')]:
            record = {'source_section': copy.deepcopy(scope[field]),
                      'display_identifier_basis': 'Authored navigation ID for a source section without its own ID; not a new scientific branch'}
            f['routes'].append(route(record, '/' + field, kind, [contract(KINDS[kind] + ' · source section', scope[field])],
                                    'nonmanual_scope.json', identifier='SCOPE_' + field.upper(), title=field.replace('_', ' ')))


def summary(f):
    counts = {kind + '_records': sum(r['route_kind'] == kind for r in f['routes']) for kind in KINDS}
    counts['unresolved_input_groups'] = len(f['context']['unknowns']['unknown_parameters' if f['id'] == 'beaded' else 'unknowns'])
    control_field = {'granular_assembly': 'control_packages', 'beaded': 'packages', 'thermal_jamming': 'controls'}[f['id']]
    counts['control_records'] = len(f['context']['control_packages'][control_field])
    return {k: v for k, v in counts.items() if v}


def projection(p, key):
    f, branches = base(p, key)
    f['default_route'] = DEFAULTS[key]
    f['routes'] = beaded_routes(f, branches) if key == 'beaded' else membership_routes(f, branches)
    append_nonmanual(f); f['summary_counts'] = summary(f)
    return f


def validate_projection(f, p):
    if f != projection(p, f['id']): raise ValueError('Assembly projection changed, omitted or invented source data or view grammar')
    ids = {o['id'] for o in f['operations']}
    if len(ids) != len(f['operations']): raise ValueError('Duplicate operation ID')
    if len({r['id'] for r in f['routes']}) != len(f['routes']): raise ValueError('Duplicate route ID')
    for r in f['routes']:
        if not set(op_ids(r['nodes'])) <= ids: raise ValueError('Unknown operation reference')
        if r['source_file'] == 'nonmanual_scope.json' and op_ids(r['nodes']): raise ValueError('Nonmanual disposition gained physical operations')
    return True


def adapt(p, key):
    f = projection(p, key); validate_projection(f, p); return f

def adapt_granular_assembly(p): return adapt(p, 'granular_assembly')
def adapt_beaded(p): return adapt(p, 'beaded')
def adapt_thermal_jamming(p): return adapt(p, 'thermal_jamming')
