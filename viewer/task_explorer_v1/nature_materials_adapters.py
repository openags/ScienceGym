"""Lossless read-only Nature Materials package projections.

Navigation and display labels are authored; source procedures remain authoritative.
No actor loader, recipe instantiation, hazardous service execution or solver.
"""
import copy
import hashlib
import json

NATURE_MATERIALS_COMMIT = '9e490ae5d3380121df7be1c18d4de35aac8508c5'
PACKAGES = {key: key + '_operations_v2' for key in ('gear', 'hydrogel_optical')}
LABELS = {'gear': 'Programmable gear metamaterials', 'hydrogel_optical': 'Hydrogel optical metastructures'}
COLORS = {'gear': '#dda967', 'hydrogel_optical': '#79c9c0'}
ALIASES = {'unknown_parameters.json': 'unknowns', 'evaluator_reference.json': 'acceptance', 'lineage_contract.json': 'lineage'}
BOUNDARY = ('Author/evaluator design reference only; not an actor projection, executable procedure, task runner, solver, physical simulation or execution receipt. '
            'Authored navigation does not supply source chronology, specimen allocation, qualified inputs or completed services.')
WARNINGS = {
    'gear': 'Nineteen source specimen families remain distinct: micro Taiji build, compression and actuation are not one specimen; the macro video demonstrator is illustrative. '
            'Planetary CAD and micro geometry conflicts stay unresolved. Finite shear stiffness is not periodic-cell shear modulus; fit-window variation is not specimen SD. '
            'First-cycle exclusion, terminal impact allocation and enclosed service ownership remain explicit. Sampled movie frames are not full-motion review.',
    'hydrogel_optical': 'source_complete_for_entire_paper=false: all four Extended Data image sets remain uninspected; captions are not image inspection. '
                        'Power/data conflicts, paired-blank missingness and heated Fig. 6f single-constant semantics remain open. Video 9 is accelerated 20 times; sampled frames are not full playback. '
                        'Chemical, laser, UV and thermal operations remain CLOSED QUALIFIED SERVICES ONLY. A service command or expected optical result is never a safe-release receipt.'}
KINDS = {'physical': 'PHYSICAL DESIGN', 'preparation': 'SHARED PREPARATION RECIPE',
         'numerical': 'NUMERICAL MODEL · NOT RUN', 'analysis': 'DERIVED ANALYSIS · NOT RUN',
         'theory': 'THEORY REFERENCE · NOT VALIDATED', 'illustrative': 'ILLUSTRATIVE ONLY · NOT A PHYSICAL TRIAL',
         'compatibility': 'COMPATIBILITY STATEMENT · NOT AN EXPERIMENT'}
FIELDS = {
    'gear': {'stage': 'station_id', 'objects': 'objects', 'pre': 'preconditions', 'post': 'postconditions',
             'acceptance': 'completion_evidence', 'sources': 'source_evidence_ids', 'unknowns': 'unknown_input_ids', 'provenance': 'translation_kind'},
    'hydrogel_optical': {'title': 'title', 'stage': 'station_id', 'objects': 'objects', 'actions': 'robot_actions',
                        'pre': 'preconditions', 'post': 'postconditions', 'sources': 'source_evidence_ids',
                        'unknowns': 'unknown_parameter_ids', 'provenance': 'authored_translation'}}


def read(p, name): return json.loads((p / name).read_text(encoding='utf-8'))
def context_key(name): return ALIASES.get(name, name.removesuffix('.json'))
def clone(value): return copy.deepcopy(value)
def contract(label, value, filename, pointer):
    return {'type': 'condition', 'label': label, 'children': [], 'ordered': False,
            'meta': {'source_file': filename, 'source_pointer': pointer, 'source_contract': clone(value)}}
def op_ids(nodes):
    result = []
    for n in nodes:
        if isinstance(n, str): result.append(n)
        elif n['type'] == 'op': result.append(n['id'])
        else: result.extend(op_ids(n.get('children', [])))
    return result


def operation(key, original, index):
    mapped = {'id': original['id'], **{field: clone(original[source]) for field, source in FIELDS[key].items()},
              'source_file': 'operations.json', 'source_pointer': f'/operations/{index}', 'loop': None}
    # Singleton wrappers preserve original scalar action/recovery values; labels are explicitly authored.
    mapped['recovery'] = [original['failure_and_recovery' if key == 'gear' else 'failure_recovery']]
    removed = set(FIELDS[key].values()) | {'id', 'failure_and_recovery' if key == 'gear' else 'failure_recovery'}
    if key == 'gear':
        mapped.update(title=original['id'].replace('_', ' ').title(), actions=[original['action']],
                      display_title_basis='Authored navigation label from source operation ID; source supplies no title')
        removed.add('action')
    else:
        mapped['acceptance'] = ['No completion_evidence field supplied; required receipts and postconditions remain design obligations, not observed acceptance.']
        mapped['acceptance_display_basis'] = 'Authored absence notice; not a new source acceptance predicate'
    mapped['detail'] = {name: clone(value) for name, value in original.items() if name not in removed}
    return mapped


def base(p, key):
    raw = read(p, 'operations.json'); branches = read(p, 'branches.json'); prov = read(p, 'provenance.json')
    folder = f'https://github.com/openags/ScienceGym/blob/{NATURE_MATERIALS_COMMIT}/tasks/{p.name}/'
    evidence = prov['evidence']
    if isinstance(evidence, list): evidence = {record['id']: record for record in evidence}
    f = {'id': key, 'label': LABELS[key], 'title': prov['title'], 'doi': prov['doi'], 'color': COLORS[key],
         'source_commit': NATURE_MATERIALS_COMMIT, 'source_folder': folder, 'status': BOUNDARY + ' ' + WARNINGS[key],
         'visibility': 'author_evaluator_reference_only', 'actor_projection_implemented': False,
         'source_warnings': WARNINGS[key], 'operations': [operation(key, o, i) for i, o in enumerate(raw['operations'])],
         'routes': [], 'evidence': clone(evidence), 'dependencies': read(p, 'dependencies.json'),
         'context': {'operation_policy': {k: clone(v) for k, v in raw.items() if k != 'operations'},
                     'branch_policy': {k: clone(v) for k, v in branches.items() if k != 'branches'}},
         'source_files': {fn.relative_to(p).as_posix(): {'url': folder + fn.relative_to(p).as_posix(),
                          'sha256': hashlib.sha256(fn.read_bytes()).hexdigest()} for fn in sorted(p.rglob('*.json'))}}
    for name in f['source_files']:
        if name not in ('operations.json', 'branches.json', 'dependencies.json'):
            f['context'][context_key(name)] = read(p, name)
    return f, branches


def route(f, identifier, record, filename, pointer, kind, nodes, title=None, wrapper=None):
    return {'id': identifier, 'label': KINDS[kind] + ' · ' + (title or record.get('title', record.get('purpose', record.get('scope', identifier)))),
            'route_kind': kind, 'metadata_only': not bool(op_ids(nodes)), 'nodes': nodes,
            'basis': BOUNDARY + ' ' + WARNINGS[f['id']] + (' Gear recipes preserve source-declared authored valid order, not historical author chronology. '
                                'Preparation and each condition are separate templates; no repeat or full campaign is instantiated.' if f['id'] == 'gear' else
                                ' Hydrogel operation lists are unordered membership. Only source branch prerequisites and each service phase order constrain execution; no Cartesian crossing or cross-service chronology is inferred.'),
            'detail': {wrapper: clone(record)} if wrapper else clone(record),
            **({'detail_source_wrapper': wrapper} if wrapper else {}),
            'source_file': filename, 'source_pointer': pointer,
            'navigation_basis': 'Authored inspection view of the exact indicated source record; not an added scientific branch or execution'}


def recipe(entries, filename, pointer):
    return [{'type': 'op', 'id': entry['op_id'],
             'meta': {'source_file': filename, 'source_pointer': pointer + '/' + str(i), 'source_node': clone(entry)}}
            for i, entry in enumerate(entries)]


def project_gear(p):
    f, branches = base(p, 'gear'); f['default_route'] = 'TAIJI_PLUS'
    for i, record in enumerate(branches['branches']):
        pointer = f'/branches/{i}'
        # The source declares these recipes ordered. Metadata nodes are not procedural insertions.
        nodes = recipe(record['per_condition_operations'], 'branches.json', pointer + '/per_condition_operations')
        nodes.append(contract('Required preparation reference · separate once-per-object recipe',
                              record['preparation_route_id'], 'branches.json', pointer + '/preparation_route_id'))
        nodes.append(contract('Unexpanded allocation/condition/repeat obligations · no count defaults', record, 'branches.json', pointer))
        r = route(f, record['id'], record, 'branches.json', pointer, 'physical', nodes)
        r['controls'] = [clone(c) for c in f['context']['control_packages']['packages'] if record['id'] in c['required_branch_ids']]
        f['routes'].append(r)
    for identifier, entries in branches['preparation_routes'].items():
        pointer = '/preparation_routes/' + identifier
        f['routes'].append(route(f, identifier, entries, 'branches.json', pointer, 'preparation',
                                recipe(entries, 'branches.json', pointer), identifier, 'source_preparation_recipe'))
    for field, kind in [('numerical_branches', 'numerical'), ('analysis_branches', 'analysis'), ('illustrative_only', 'illustrative')]:
        for i, record in enumerate(f['context']['nonmanual_scope'][field]):
            pointer = f'/{field}/{i}'
            # Keep numerical and analysis templates visible without granting physical credit or an invented order.
            members = record.get('operation_ids', [record['operation_id']] if 'operation_id' in record else [])
            nodes = ([{'type': 'obligations', 'label': KINDS[kind] + ' · source template membership', 'ordered': False,
                       'children': clone(members), 'meta': {'order': 'Source membership only; no physical acquisition or inferred adjacency'}}] if members else [])
            nodes.append(contract(KINDS[kind] + ' · exact source disposition', record, 'nonmanual_scope.json', pointer))
            for j, dep in enumerate(f['dependencies']['analysis_dependencies']):
                if dep['id'] == record['id']: nodes.append(contract('Required measured/control parents · not supplied by this viewer', dep, 'dependencies.json', f'/analysis_dependencies/{j}'))
            f['routes'].append(route(f, record['id'], record, 'nonmanual_scope.json', pointer, kind, nodes))
    f['summary_counts'] = {'physical_branches': 18, 'preparation_recipes': 8, 'numerical_records': 7, 'analysis_records': 2,
                           'illustrative_records': 2, 'unresolved_input_groups': len(f['context']['unknowns']['parameters']),
                           'control_records': len(f['context']['control_packages']['packages']),
                           'specimen_family_definitions': len(f['context']['material_cards']['specimen_families'])}
    return f


def project_hydrogel_optical(p):
    f, branches = base(p, 'hydrogel_optical'); f['default_route'] = 'BEAM_POWER'
    for i, record in enumerate(branches['branches']):
        pointer = f'/branches/{i}'
        nodes = [{'type': 'obligations', 'label': 'Required operation membership · no chronological adjacency',
                  'ordered': False, 'children': clone(record['operation_ids']),
                  'meta': {'order': record['operation_list_semantics']}}]
        for field in ('condition_axes', 'source_cycles', 'source_independent_specimens'):
            nodes.append(contract('Exact source ' + field.replace('_', ' ') + ' · not allocated instances', record[field], 'branches.json', pointer + '/' + field))
        nodes.append(contract('Per-service phase order only · no cross-service order inferred', f['dependencies']['service_phase_order'], 'dependencies.json', '/service_phase_order'))
        nodes.append(contract('Closed qualified service boundaries · no hazardous robot procedure', f['context']['station_contracts'], 'station_contracts.json', ''))
        r = route(f, record['id'], record, 'branches.json', pointer, 'physical', nodes)
        r['controls'] = [clone(c) for c in f['context']['control_packages']['controls'] if c['scope'] in ('all', record['id'])]
        f['routes'].append(r)
    kinds = {'analysis_only_gated': 'numerical', 'theory_reference_only': 'theory', 'derived_fit_reference': 'analysis',
             'compatibility_statement_not_experiment': 'compatibility'}
    for i, record in enumerate(f['context']['nonmanual_scope']['items']):
        kind = kinds[record['disposition']]; pointer = f'/items/{i}'
        f['routes'].append(route(f, record['id'], record, 'nonmanual_scope.json', pointer, kind,
                                [contract(KINDS[kind] + ' · exact source disposition', record, 'nonmanual_scope.json', pointer)]))
    f['summary_counts'] = {'physical_branches': len(branches['branches']), 'numerical_records': 1, 'theory_records': 1,
                           'analysis_records': 1, 'compatibility_records': 1, 'unresolved_input_groups': len(f['context']['unknowns']['unknowns']),
                           'control_records': len(f['context']['control_packages']['controls']),
                           'lineage_dependency_edges': len(f['dependencies']['branch_edges'])}
    return f


def validate_projection(f, p):
    """Reject invalid references and namespace promotions; source equality is independently tested."""
    if f != projection(p, f['id']): raise ValueError('Nature-materials projection changed, omitted or invented source data or display grammar')
    ids = [o['id'] for o in f['operations']]
    if len(ids) != len(set(ids)): raise ValueError('Duplicate operation ID')
    if len(f['routes']) != len({r['id'] for r in f['routes']}): raise ValueError('Duplicate route ID')
    for r in f['routes']:
        members = op_ids(r['nodes'])
        if not set(members) <= set(ids): raise ValueError('Unknown operation reference')
        if r['route_kind'] in ('illustrative', 'theory', 'compatibility') and members: raise ValueError('Reference scope gained execution operations')
        if f['id'] == 'gear' and r['route_kind'] == 'numerical' and members != ['NUMERICAL_CONFIG', 'NUMERICAL_RUN', 'NUMERICAL_REPORT']:
            raise ValueError('Numerical namespace changed or gained physical operations')
    return True


def projection(p, key):
    return {'gear': project_gear, 'hydrogel_optical': project_hydrogel_optical}[key](p)

def adapt(p, key):
    f = projection(p, key); validate_projection(f, p); return f

def adapt_gear(p): return adapt(p, 'gear')
def adapt_hydrogel_optical(p): return adapt(p, 'hydrogel_optical')
