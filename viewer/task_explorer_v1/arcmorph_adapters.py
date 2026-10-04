"""Lossless static Arc-Morph design inspector; no physical or numerical execution."""
import hashlib
import json
from collections import Counter
from paired_adapters import clone, read, context_key, contract

PACKAGES = {'arcmorph': 'arcmorph_operations_v2'}
SOURCE_COMMIT = '4152571bcd56cf10387ba36df913b790873c018d'
ASSET_PACKAGE = 'arcmorph_scene_assets_v1'
BOUNDARY = ('Whole-paper DESIGN only; zero validated runnable whole-paper tasks. '
    'Read-only author/evaluator inspection, not an actor context, controller, physical simulation or scientific reproduction. '
    'Source facts and independently authored robot contracts remain separate. Source-listed occurrences and phase bodies are retained, '
    'but cross-phase display order is not a historical chronology or an executable global sequence. '
    'Eight configuration slots remain one unexpanded same-specimen template; no repeats, allocations or successful outcomes are instantiated. '
    'Qualification holds remain active and required post-states are design obligations, never observations.')
WARNINGS = ('Seven physical route families and thirty-one operation templates are one paper-level design, not thirty-one papers. '
    'Four cardstock families retain separate ground, rigid and sheared evidence slots; those twelve slots do not supply specimen counts. '
    'The polymer quantitative series reports one specimen, one set and eight configurations, not eight independent samples or repeated cycles. '
    'Ten source conflicts and fourteen unresolved-input cards remain open and claim-local. C01 keeps the physical geometry unresolved; '
    'theoretical dimensions cannot become fabrication defaults. Qualitative shear is not a measured stiffness or force law. '
    'Paired cameras, independent length references, locked capture state, mount leases, fixture-specific release and specimen/rest history remain distinct. '
    'Machining, powered loading and all physical services stay closed, qualified and unimplemented; nominal anchors are not motion permission. '
    'Upstream source review covered twelve main pages, twenty-two written SI pages and main/SI figures. The raw-image/code archive was not acquired or read; '
    'notebooks were not run and source mathematics was not independently proved. '
    'Original scene geometry, dimensions, grasps and interfaces are illustrative and unqualified; no source-exact CAD, real physics or safe motion is established.')


def occurrence(identifier, filename, pointer):
    return {'type': 'op', 'id': identifier,
            'meta': {'source_file': filename, 'source_pointer': pointer, 'source_node': identifier,
                     'meaning': 'Exact source-listed template occurrence; not execution or an independent specimen'}}


def sequence(label, values, pointer, ordered=True):
    return {'type': 'sequence' if ordered else 'obligations', 'label': label,
            'ordered': ordered, 'children': [occurrence(v, 'branches.json', pointer + '/' + str(i)) for i, v in enumerate(values)],
            'meta': {'source_file': 'branches.json', 'source_pointer': pointer, 'source_node': clone(values),
                     'order': 'Source-declared authored list order only; not historical chronology' if ordered else BOUNDARY}}


def record(detail, pointer, kind, label, nodes):
    return {'id': detail['id'], 'label': label, 'route_kind': kind, 'metadata_only': not bool(nodes),
            'nodes': nodes + [contract('Exact source branch/disposition contract', detail, 'branches.json', pointer)],
            'basis': BOUNDARY, 'detail': clone(detail), 'source_file': 'branches.json', 'source_pointer': pointer,
            'navigation_basis': 'Authored inspection label; separate scopes do not create new papers, experiments or observations'}


def projection(p):
    docs = {n.relative_to(p).as_posix(): read(p, n.relative_to(p).as_posix()) for n in sorted(p.rglob('*.json'))}
    branches = docs['branches.json']; raw = docs['operations.json']['operations']; ids = {o['id'] for o in raw}
    folder = '../../tasks/' + p.name + '/'; paper = docs['provenance.json']['paper']
    operations = []
    for i, o in enumerate(raw):
        operations.append({'id': o['id'], 'title': o['interaction'], 'stage': o['station'],
            'actions': [o['interaction']], 'objects': {'object': o['object'], 'asset_ids': clone(o['asset_ids'])},
            'pre': clone(o['preconditions']), 'post': clone(o['postconditions']),
            'acceptance': {k: clone(o[k]) for k in ('completion_evidence', 'required_record_type', 'evidence_role')},
            'recovery': {k: o[k] for k in ('failure_response', 'failure_transition')},
            'sources': clone(o['source_fact_ids']), 'unknowns': clone(o['unknown_ids']),
            'provenance': {k: clone(o[k]) for k in ('provenance_class', 'actor', 'source_is_robot_protocol', 'physical_implemented')},
            'loop': None, 'detail': clone(o), 'source_file': 'operations.json', 'source_pointer': '/operations/' + str(i),
            'display_title_basis': 'Exact task-package authored interaction; not a paper quotation',
            'display_mapping_basis': 'Exact pre/postconditions and record requirements are authored obligations, not observed states or completion receipts.',
            'display_action_ownership': 'Independently authored symbolic robot translation; no live device control.'})
    f = {'id': 'arcmorph', 'label': 'Arc-Morph origami metrology', 'title': paper['title'], 'doi': paper['doi'], 'color': '#dfb17d',
         'family_scope': 'paper_level_design', 'family_scope_label': 'WHOLE-PAPER DESIGN',
         'source_commit': SOURCE_COMMIT, 'source_folder': folder,
         'source_link_mode': 'repository_relative_frozen_local_snapshot',
         'source_publication': 'Local source commit and per-file hashes are recorded; remote publication is not asserted. Links resolve within the repository.',
         'status': BOUNDARY + ' ' + WARNINGS, 'source_warnings': WARNINGS,
         'visibility': 'author_evaluator_reference_only', 'actor_projection_implemented': False,
         'operations': operations, 'routes': [], 'evidence': {e['id']: clone(e) for e in docs['evidence_map.json']['facts']},
         'context': {context_key(name): clone(value) for name, value in docs.items()},
         'dependencies': {'display_rule': BOUNDARY, **{name: clone(docs[name + '.json']) for name in
                          ('dependencies', 'preparation_routes', 'lifecycle_contract', 'lineage_contract', 'transport_routes', 'recovery_boundaries')}},
         'source_files': {name: {'url': folder + name, 'repository_path': 'tasks/' + p.name + '/' + name,
                                'sha256': hashlib.sha256((p / name).read_bytes()).hexdigest()} for name in docs},
         'default_route': docs['episode_input_contract.json']['default'],
         'default_route_basis': 'Exact metadata-only episode default; no new operation, scientific branch or qualification is invented.',
         'asset_links': [],
         'asset_boundary': 'Original editable static 3D scene and three renders only. All geometry, nominal dimensions, anchors, poses, grasps and handling interfaces remain illustrative and unqualified. No source-exact CAD, contact model, validated motion, real physics or scientific measurement is supplied.'}
    for i, b in enumerate(branches['physical_routes']):
        pointer = '/physical_routes/' + str(i); nodes = []
        prerequisite_nodes = [occurrence(v, 'branches.json', pointer + '/dependencies/' + str(j))
                              for j, v in enumerate(b['dependencies']) if v in ids]
        if prerequisite_nodes:
            nodes.append({'type': 'obligations', 'label': 'Declared operation prerequisites; route dependencies stay in the exact contract',
                          'ordered': False, 'children': prerequisite_nodes,
                          'meta': {'source_file': 'branches.json', 'source_pointer': pointer + '/dependencies',
                                   'source_node': clone(b['dependencies']), 'order': 'Prerequisites only; no global sequence is inferred'}})
        if 'operation_groups' in b:
            nodes.append({'type': 'obligations', 'label': 'Separate phase bodies; mode order and specimen reuse remain qualified choices',
                          'ordered': False,
                          'children': [sequence(name.replace('_', ' ') + ' · exact authored body', values,
                                                pointer + '/operation_groups/' + name) for name, values in b['operation_groups'].items()],
                          'meta': {'source_file': 'branches.json', 'source_pointer': pointer + '/operation_groups',
                                   'source_node': clone(b['operation_groups']), 'order': b['order_policy'],
                                   'state_slots': clone(b['state_slots'])}})
        elif 'operation_sequence' in b:
            nodes.append(sequence('Exact authored operation sequence', b['operation_sequence'], pointer + '/operation_sequence'))
        else:
            nodes.append(sequence('Exact setup body', b['setup'], pointer + '/setup'))
            loop = b['state_loop']
            nodes.append({'type': 'loop', 'label': 'Same specimen · eight configuration slots · body shown once',
                          'symbolic': True, 'ordered': True,
                          'children': [occurrence(v, 'branches.json', pointer + '/state_loop/per_instance/' + str(j))
                                       for j, v in enumerate(loop['per_instance'])],
                          'meta': {'source_file': 'branches.json', 'source_pointer': pointer + '/state_loop',
                                   'source_node': clone(loop), 'order': loop['state_order'],
                                   'count_boundary': 'Eight configurations on one source specimen; not eight samples or technical repeats'}})
            nodes.append(sequence('Exact closeout body', b['closeout'], pointer + '/closeout'))
        f['routes'].append(record(b, pointer, 'physical_design', 'PHYSICAL ROUTE DESIGN · ' + b['name'], nodes))
    for i, b in enumerate(branches['auxiliary_routes']):
        pointer = '/auxiliary_routes/' + str(i)
        if b['id'] == 'CLOSEOUT':
            choices = {'type': 'choice', 'label': 'Fixture-specific unmount alternatives · never both on one mount', 'ordered': False,
                       'children': [occurrence(v, 'branches.json', pointer + '/operations/' + str(j))
                                    for j, v in enumerate(b['operations']) if v in ('R22', 'R30')],
                       'meta': {'source_file': 'branches.json', 'source_pointer': pointer,
                                'source_node': clone(b), 'selection_rule': b['selection_rule']}}
            nodes = [{'type': 'obligations', 'label': 'Conditional safe-closeout obligations', 'ordered': False,
                      'children': [occurrence('R19', 'branches.json', pointer + '/operations/0'), choices,
                                   occurrence('R23', 'branches.json', pointer + '/operations/3'),
                                   occurrence('R24', 'branches.json', pointer + '/operations/4')],
                      'meta': {'source_file': 'branches.json', 'source_pointer': pointer,
                               'source_node': clone(b), 'order': b['selection_rule']}}]
            kind, label = 'conditional_closeout', 'CONDITIONAL CLOSEOUT · actual fixture governs release'
        else:
            nodes = [sequence('Exact nonmanual analysis obligation', b['operations'], pointer + '/operations', False)]
            kind, label = 'analysis', 'NONMANUAL IMAGE ANALYSIS · no solver or source-data run'
        f['routes'].append(record(b, pointer, kind, label, nodes))
    for i, b in enumerate(branches['nonmanual_dispositions']):
        f['routes'].append(record(b, '/nonmanual_dispositions/' + str(i), 'nonmanual_reference',
                                 'NONMANUAL REFERENCE · ' + b['subject'], []))
    hold = docs['episode_input_contract.json']
    f['routes'].append({'id': f['default_route'], 'label': 'DEFAULT QUALIFICATION HOLD · NO ACTIVATION',
        'route_kind': 'qualification_hold', 'metadata_only': True,
        'nodes': [contract('Exact qualification-hold input contract', hold, 'episode_input_contract.json', '')],
        'basis': BOUNDARY, 'detail': clone(hold), 'source_file': 'episode_input_contract.json', 'source_pointer': '',
        'navigation_basis': 'Metadata-only default, not a scientific route or invented operation'})
    assets = docs['asset_binding_plan.json']['assets']
    f['summary_counts'] = dict(Counter(r['route_kind'] + '_records' for r in f['routes']))
    f['summary_counts'].update(physical_route_families=len(branches['physical_routes']), source_json_documents=len(docs),
        scene_groups=len(assets), symbolic_anchors=len({anchor for binding in docs['asset_binding_plan.json']['operation_bindings'] for anchor in binding['anchor_ids']} | {binding['anchor_id'] for binding in docs['asset_binding_plan.json']['contextual_anchor_bindings']}),
        source_evidence_entries=len(f['evidence']), source_conflicts=len(docs['source_conflicts.json']['conflicts']),
        unresolved_input_groups=len(docs['unknown_parameters.json']['unknowns']),
        source_quantitative_specimens=docs['controls_and_repeats.json']['source_quantitative_specimens'],
        source_configurations=docs['controls_and_repeats.json']['source_configurations'])
    ap = p.parent.parent / 'assets' / ASSET_PACKAGE
    for name in ['README.md'] + [n.relative_to(ap).as_posix() for n in sorted((ap / 'evidence').glob('*.png'))]:
        if not (ap / name).is_file(): raise ValueError('Missing original static asset: ' + name)
        f['asset_links'].append({'label': 'Original editable static 3D guide' if name == 'README.md' else 'Static render: ' + name.split('/')[-1].removesuffix('.png'),
            'path': 'assets/' + ASSET_PACKAGE + '/' + name, 'url': '../../assets/' + ASSET_PACKAGE + '/' + name,
            'sha256': hashlib.sha256((ap / name).read_bytes()).hexdigest()})
    return f


def validate_projection(f, p):
    if json.dumps(f, sort_keys=True, ensure_ascii=False, allow_nan=False) != json.dumps(projection(p), sort_keys=True, ensure_ascii=False, allow_nan=False):
        raise ValueError('Arc-Morph projection omitted, changed or invented a source contract or display boundary')
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
    pins = f['context']['review/INDEPENDENT_REVIEW']['observed_sibling_contract_hashes']
    for name, digest in pins.items():
        if hashlib.sha256((ap / name).read_bytes()).hexdigest() != digest: raise ValueError('Task-pinned scene file changed: ' + name)
    if (ap / 'task_binding_snapshot.json').read_bytes() != (p / 'asset_binding_plan.json').read_bytes():
        raise ValueError('Task/asset snapshot mismatch')
    return True


def adapt_arcmorph(p):
    f = projection(p); validate_projection(f, p); return f
