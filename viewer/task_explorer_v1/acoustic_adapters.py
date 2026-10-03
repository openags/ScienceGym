"""Explicit, lossless author/evaluator adapters for the three 2026 acoustic designs.

No loader, solver, schedule expansion, actor projection or execution is provided.
"""
import copy
import hashlib
import json

ACOUSTIC_COMMIT = '162905c0aeebd6da5eb9794df118458c24bb7d63'
PACKAGES = {'wavefront': 'acoustic_wavefront_operations_v2',
            'bianisotropic': 'bianisotropic_operations_v2',
            'edge': 'acoustic_edge_operations_v2'}
LABELS = {'wavefront': 'Acoustic wavefront modulation',
          'bianisotropic': 'Bianisotropic acoustic metasurfaces',
          'edge': 'Acoustic edge detection'}
COLORS = {'wavefront': '#86c5ef', 'bianisotropic': '#b69fe5', 'edge': '#e7b66c'}
ALIASES = {'unknown_parameters.json': 'unknowns', 'evaluator_reference.json': 'acceptance',
           'lineage_contract.json': 'lineage'}
FIELDS = {
    'wavefront': {'title': 'title', 'stage': 'location_id', 'actions': 'actions',
                 'objects': 'target_asset_roles', 'pre': 'preconditions', 'post': 'postconditions',
                 'sources': 'evidence_ids', 'acceptance': 'observable_completion',
                 'recovery': 'failure_handling', 'unknowns': 'unknown_parameter_ids'},
    'bianisotropic': {'title': 'title', 'stage': 'location_id', 'actions': 'actions',
                     'objects': 'objects', 'pre': 'preconditions', 'post': 'postconditions',
                     'sources': 'evidence_ids', 'acceptance': 'required_completion_evidence',
                     'recovery': 'recovery', 'unknowns': 'unknown_parameter_ids',
                     'loop': 'iteration', 'provenance': 'provenance'},
    'edge': {'title': 'title', 'stage': 'station_id', 'actions': 'actions',
             'objects': 'object_roles', 'pre': 'preconditions', 'post': 'postconditions',
             'sources': 'evidence_ids', 'acceptance': 'required_observations',
             'recovery': 'failure_handling', 'unknowns': 'unknown_parameter_ids',
             'provenance': 'provenance'},
}
ORDER = ('Source operation membership only; no chronological adjacency. Apply scoped '
         'dependencies, conditional gates and actual occurrence identities. Nothing here is executed.')

def read(p, name):
    return json.loads((p / name).read_text())

def context_key(name):
    return ALIASES.get(name, name.removesuffix('.json'))

def member_node(members, label='Operation membership · conditional applicability retained'):
    return {'type': 'obligations', 'label': label, 'ordered': False,
            'meta': {'order': ORDER}, 'children': list(members)}

def contract_node(label, contract, kind='condition'):
    return {'type': kind, 'label': label, 'meta': {'source_contract': copy.deepcopy(contract)},
            'children': [], 'ordered': False, **({'symbolic': True} if kind == 'loop' else {})}

def route(record, pointer, kind, nodes, filename='branches.json'):
    labels = {'physical': 'PHYSICAL DESIGN', 'numerical': 'NUMERICAL / THEORY · NOT RUN',
              'prerequisite': 'SHARED PREPARATION', 'campaign': 'CAMPAIGN ACCOUNTING'}
    return {'id': record['id'], 'label': labels[kind] + ' · ' + record.get('title', record['id']),
            'route_kind': kind, 'nodes': nodes,
            'basis': (ORDER + ' Numerical/theoretical records never count as physical measurements. '
                      'Source facts, task-authored interfaces and qualified episode inputs stay distinct.'),
            'detail': copy.deepcopy(record), 'source_file': filename, 'source_pointer': pointer}

def operation(key, original, index):
    fields = FIELDS[key]
    mapped = {'id': original['id'], **{target: copy.deepcopy(original[src]) for target, src in fields.items()},
              'source_file': 'operations.json', 'source_pointer': '/operations/' + str(index)}
    mapped.setdefault('loop', None)
    if key == 'wavefront':
        mapped['provenance'] = {'authorship': original['authorship']}
    used = set(fields.values()) | {'id'} | ({'authorship'} if key == 'wavefront' else set())
    mapped['detail'] = {k: copy.deepcopy(v) for k, v in original.items() if k not in used}
    return mapped

def base(p, key):
    raw = read(p, 'operations.json'); branches = read(p, 'branches.json'); prov = read(p, 'provenance.json')
    folder = f'https://github.com/openags/ScienceGym/blob/{ACOUSTIC_COMMIT}/tasks/{p.name}/'
    evidence = prov['evidence']
    if isinstance(evidence, list): evidence = {e['id']: e for e in evidence}
    evidence = copy.deepcopy(evidence)
    if key == 'edge':
        for entry in evidence.values(): entry['url'] = prov['source_ids'][entry['source_id']]
    f = {'id': key, 'label': LABELS[key], 'title': prov['title'], 'doi': prov['doi'], 'color': COLORS[key],
         'source_commit': ACOUSTIC_COMMIT, 'source_folder': folder,
         'status': 'Author/evaluator logical inspector; source-bounded design only; no actor projection, solver, simulator or robot execution',
         'visibility': 'author_evaluator_reference_only', 'actor_projection_implemented': False,
         'operations': [operation(key, op, i) for i, op in enumerate(raw['operations'])], 'routes': [],
         'evidence': evidence, 'dependencies': read(p, 'dependencies.json'),
         'context': {'operation_policy': {k: v for k, v in raw.items() if k != 'operations'},
                     'branch_policy': {k: v for k, v in branches.items() if k != 'branches'}},
         'source_files': {fn.relative_to(p).as_posix(): {'url': folder + fn.relative_to(p).as_posix(),
                          'sha256': hashlib.sha256(fn.read_bytes()).hexdigest()}
                          for fn in sorted(p.rglob('*.json'))}}
    for fn in sorted(p.rglob('*.json')):
        name = fn.relative_to(p).as_posix()
        if name not in ('operations.json', 'branches.json', 'dependencies.json'):
            f['context'][context_key(name)] = read(p, name)
    return f, branches

def adapt_wavefront(p):
    f, branches = base(p, 'wavefront'); f['default_route'] = 'NORMAL_INCIDENCE'
    for i, record in enumerate(branches['branches']):
        nodes = [member_node(record['operation_ids'])]
        # There is no explicit per-route loop binding in this schema. Keep all
        # seven global scopes as exact metadata, never guessed local bodies.
        nodes.append(contract_node('Global symbolic loop scopes · applicability is conditional',
                     {'loops': f['dependencies']['loops'],
                      'display_rule': 'Global contracts, not seven local repeats; apply only declared compatible operation/condition scopes'}, 'loop'))
        nodes.append(contract_node('Preparation handoff and episode-terminal policy',
                     {k: record[k] for k in ['required_branch_ids', 'preparation_policy', 'terminal_operation_ids',
                                            'terminal_policy', 'prepared_handoff']}))
        f['routes'].append(route(record, f'/branches/{i}', 'physical', nodes))
    for i, record in enumerate(f['context']['nonmanual_scope']['items']):
        if record['operation_ids']: raise ValueError('Wavefront numerical disposition must not contain physical operations')
        f['routes'].append(route(record, f'/items/{i}', 'numerical',
                          [contract_node('Numerical / theoretical disposition · no physical operation route', record)],
                          'nonmanual_scope.json'))
    f['summary_counts'] = {'physical_routes': len(branches['branches']),
                           'numerical_dispositions': len(f['context']['nonmanual_scope']['items']),
                           'symbolic_loops': len(f['dependencies']['loops']),
                           'input_gates': len(f['context']['unknowns']['unknowns'])}
    validate_projection(f, p)
    return f

def adapt_bianisotropic(p):
    f, branches = base(p, 'bianisotropic'); f['default_route'] = 'MEASURE_60'
    nonmanual = {job['branch_id']: job for job in f['context']['nonmanual_scope']['jobs']}
    for i, record in enumerate(branches['branches']):
        kind = 'numerical' if record['id'] in nonmanual else 'physical'
        nodes = [member_node(record['operation_ids'])]
        for loop in record.get('loops', []):
            nodes.append(contract_node(loop['id'] + ' · unexpanded source loop contract', loop, 'loop'))
        if kind == 'numerical': nodes.append(contract_node('Numerical / theoretical boundary · no physical specimens', nonmanual[record['id']]))
        f['routes'].append(route(record, f'/branches/{i}', kind, nodes))
    f['summary_counts'] = {'physical_routes': len(branches['branches']) - len(nonmanual),
                           'numerical_dispositions': len(nonmanual),
                           'branch_loop_contracts': sum(len(r.get('loops', [])) for r in branches['branches']),
                           'unknown_input_groups': len(f['context']['unknowns']['unknowns'])}
    validate_projection(f, p)
    return f

def adapt_edge(p):
    f, branches = base(p, 'edge'); f['default_route'] = 'SINGLE_EDGE_1D'
    loops = {item['id']: item for item in branches['loops']}
    for i, record in enumerate(branches['branches']):
        nodes = [member_node(record['operation_ids'])]
        nodes.append(contract_node('Required shared preparation · separate identity-scoped receipts',
                                   {'prerequisite_family_ids': record['prerequisite_family_ids']}))
        nodes.extend(contract_node(lid + ' · branch-applicable symbolic contract', loops[lid], 'loop') for lid in record['loop_ids'])
        f['routes'].append(route(record, f'/branches/{i}', 'physical', nodes))
    for i, record in enumerate(branches['families']):
        if 'route_variants' in record:
            nodes = [{'type': 'choice', 'label': 'Exclusive alternatives · choose exactly one per target',
                      'ordered': False, 'meta': {'selection_rule': record['selection_rule']},
                      'children': [member_node(ids, name + ' · alternative membership only')
                                   for name, ids in record['route_variants'].items()]}]
        else: nodes = [member_node(record['operation_ids'])]
        if record['id'] == 'F_RIG': nodes.append(contract_node('L_MIC · four sensor slots, not four specimens', loops['L_MIC'], 'loop'))
        f['routes'].append(route(record, f'/families/{i}', 'prerequisite', nodes))
    for i, record in enumerate(f['context']['nonmanual_scope']['numerical_branches']):
        f['routes'].append(route(record, f'/numerical_branches/{i}', 'numerical',
                          [contract_node('Numerical prediction obligations · no operation IDs or solver supplied', record)],
                          'nonmanual_scope.json'))
    campaign = branches['campaign']
    nodes = [contract_node('Required independent branch dispositions · never one merged sample history',
                           {k: campaign[k] for k in ['required_branch_ids', 'required_control_package_ids', 'completion']}),
             {'type': 'choice', 'label': 'Conditional campaign closure · complete versus abort', 'ordered': False,
              'meta': {'scope': 'Closure contracts are conditional alternatives, not mandatory serial operation lists'},
              'children': [member_node(campaign['required_closure_operation_ids'], 'Required completion closure membership'),
                           member_node(campaign['abort_closure_operation_ids'], 'Abort-only closure membership')]}]
    f['routes'].append(route(campaign, '/campaign', 'campaign', nodes))
    f['summary_counts'] = {'physical_routes': len(branches['branches']),
                           'shared_preparation_records': len(branches['families']),
                           'numerical_dispositions': len(f['context']['nonmanual_scope']['numerical_branches']),
                           'campaign_accounting_records': 1, 'symbolic_loops': len(branches['loops']),
                           'input_gates': len(f['context']['unknowns']['unknowns'])}
    validate_projection(f, p)
    return f

def op_ids(nodes):
    result = []
    for node in nodes:
        if isinstance(node, str): result.append(node)
        elif node.get('type') == 'op': result.append(node['id'])
        else: result.extend(op_ids(node.get('children', [])))
    return result

def pointer(document, path):
    for item in path.strip('/').split('/'):
        document = document[int(item)] if isinstance(document, list) else document[item]
    return document

def validate_projection(f, p):
    """Fail closed on branch mixing, contract leakage/relabeling or invented defaults.

    This validates the unpooled projection against local source contracts. It is
    not a runtime actor-redaction implementation or scientific evaluator.
    """
    key = f['id']; raw = read(p, 'operations.json'); b = read(p, 'branches.json')
    if f['visibility'] != 'author_evaluator_reference_only' or f['actor_projection_implemented'] is not False:
        raise ValueError('Public inspector must never be labeled an actor projection')
    if any(k in f for k in ('actor_prompt', 'actor_payload', 'actor_export', 'execution_receipt')):
        raise ValueError('Actor exports and execution receipts are not inspector outputs')
    if f['operations'] != [operation(key, op, i) for i, op in enumerate(raw['operations'])]:
        raise ValueError('Operation contract changed or fields leaked across schemas')
    if f['dependencies'] != read(p, 'dependencies.json'): raise ValueError('Dependency contract changed')
    source_names = {fn.relative_to(p).as_posix() for fn in p.rglob('*.json')}
    if set(f['source_files']) != source_names: raise ValueError('Source inventory loss or leakage')
    expected_context = {'operation_policy', 'branch_policy'} | {context_key(n) for n in source_names if n not in ('operations.json', 'branches.json', 'dependencies.json')}
    if set(f['context']) != expected_context: raise ValueError('Context inventory loss or leakage')
    for name in f['source_files']:
        if f['source_files'][name]['sha256'] != hashlib.sha256((p / name).read_bytes()).hexdigest(): raise ValueError('Incorrect source hash')
        expected_url = f'https://github.com/openags/ScienceGym/blob/{ACOUSTIC_COMMIT}/tasks/{p.name}/{name}'
        if f['source_files'][name]['url'] != expected_url: raise ValueError('Source URL must use the acoustic release pin')
        if name not in ('operations.json', 'branches.json', 'dependencies.json'):
            if f['context'].get(context_key(name)) != read(p, name):
                raise ValueError('Source contract changed, omitted or assigned an invented default: ' + name)
    if f['context']['operation_policy'] != {k: v for k, v in raw.items() if k != 'operations'}:
        raise ValueError('Operation policy changed')
    if f['context']['branch_policy'] != {k: v for k, v in b.items() if k != 'branches'}:
        raise ValueError('Branch policy changed')
    operation_map = {op['id']: op for op in raw['operations']}
    if len(operation_map) != len(raw['operations']): raise ValueError('Duplicate operation ID')
    if len({r['id'] for r in f['routes']}) != len(f['routes']): raise ValueError('Duplicate route ID')
    for r in f['routes']:
        original = pointer(read(p, r['source_file']), r['source_pointer'])
        if r['detail'] != original or r['id'] != original['id']: raise ValueError('Route source contract changed')
        members = op_ids(r['nodes'])
        if not set(members) <= set(operation_map): raise ValueError('Unknown operation ID')
        if r['source_file'] == 'nonmanual_scope.json':
            expected = []; kind = 'numerical'
        elif r['source_pointer'] == '/campaign':
            expected = original['required_closure_operation_ids'] + original['abort_closure_operation_ids']; kind = 'campaign'
        elif r['source_pointer'].startswith('/families/'):
            expected = ([oid for ids in original['route_variants'].values() for oid in ids]
                        if 'route_variants' in original else original['operation_ids']); kind = 'prerequisite'
        else:
            expected = original['operation_ids']; kind = ('numerical' if key == 'bianisotropic' and
                        original['id'] in {j['branch_id'] for j in f['context']['nonmanual_scope']['jobs']} else 'physical')
        if members != expected or r['route_kind'] != kind: raise ValueError('Branch mixing or membership loss')
        if kind == 'numerical' and 'NUMERICAL / THEORY · NOT RUN' not in r['label']: raise ValueError('Numerical status label lost')
        if kind == 'numerical' and any(operation_map[oid]['kind'] != 'digital_job' for oid in members):
            raise ValueError('Physical operation leaked into numerical branch')
        def check_unordered(nodes):
            for node in nodes:
                if isinstance(node, dict) and 'children' in node:
                    if node.get('ordered') is not False: raise ValueError('Invented chronological adjacency')
                    check_unordered(node['children'])
        check_unordered(r['nodes'])
        symbolic = [node['meta']['source_contract'] for node in r['nodes'] if isinstance(node, dict) and node.get('type') == 'loop']
        if key == 'wavefront' and kind == 'physical':
            if len(symbolic) != 1 or symbolic[0]['loops'] != f['dependencies']['loops']: raise ValueError('Wavefront global loop contract changed')
            expected_handoff = {k: original[k] for k in ['required_branch_ids', 'preparation_policy', 'terminal_operation_ids', 'terminal_policy', 'prepared_handoff']}
            if len(r['nodes']) != 3 or r['nodes'][2]['meta'].get('source_contract') != expected_handoff: raise ValueError('Wavefront handoff or terminal scope changed')
        elif key == 'bianisotropic':
            if symbolic != original.get('loops', []): raise ValueError('Branch-local loop changed or flattened')
        elif key == 'edge':
            loop_map = {loop['id']: loop for loop in b['loops']}
            expected_loops = ([loop_map[lid] for lid in original['loop_ids']] if kind == 'physical' else [loop_map['L_MIC']] if r['id'] == 'F_RIG' else [])
            if symbolic != expected_loops: raise ValueError('Edge loop scope or default changed')
        if key == 'edge' and r['id'] == 'F_TARGET':
            if len(r['nodes']) != 1 or r['nodes'][0]['type'] != 'choice': raise ValueError('Target alternatives were merged')
            if r['nodes'][0]['meta'].get('selection_rule') != original['selection_rule']: raise ValueError('Target selection rule lost')
            alternatives = r['nodes'][0]['children']
            if [op_ids([node]) for node in alternatives] != list(original['route_variants'].values()): raise ValueError('Target route variants mixed')
        if key == 'edge' and kind == 'campaign':
            expected_scope = {k: original[k] for k in ['required_branch_ids', 'required_control_package_ids', 'completion']}
            if len(r['nodes']) != 2 or r['nodes'][0]['meta'].get('source_contract') != expected_scope: raise ValueError('Campaign requirements lost')
            if r['nodes'][1]['type'] != 'choice': raise ValueError('Campaign closure alternatives merged')
            if [op_ids([node]) for node in r['nodes'][1]['children']] != [original['required_closure_operation_ids'], original['abort_closure_operation_ids']]: raise ValueError('Campaign closure roles mixed')
    expected_routes = len(b['branches'])
    if key == 'wavefront': expected_routes += len(read(p, 'nonmanual_scope.json')['items'])
    if key == 'edge': expected_routes += len(b['families']) + len(read(p, 'nonmanual_scope.json')['numerical_branches']) + 1
    if len(f['routes']) != expected_routes: raise ValueError('Omitted or invented branch record')
