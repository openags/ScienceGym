"""Lossless inspectors for reviewed lockable-origami and varactor task designs.

Source contracts, static assets and synthetic bookkeeping are never executions.
No paper, source geometry, live device command or scientific solver is added.
"""
import hashlib
import json
from collections import Counter
from paired_adapters import clone, read, context_key, operation, contract

PACKAGES = {key: key + '_operations_v2' for key in ('lockable_origami', 'varactor')}
SOURCE_COMMITS = {'lockable_origami': 'e1e4a74aae0126a2747961398bfd0a08623f76ee',
                  'varactor': '98d3bfe9adfb687a72002da314f2d597266a0d7f'}
LABELS = {'lockable_origami': 'Lockable flat-foldable origami',
          'varactor': 'Quantum paraelectric varactors'}
COLORS = {'lockable_origami': '#f0be79', 'varactor': '#a7c6ee'}
KINDS = {'design_only': ('design_only', 'DESIGN REFERENCE · NOT RUN'),
         'closed_service': ('closed_service', 'CLOSED QUALIFIED SERVICE DESIGN · NOT EXECUTED'),
         'external_model_metadata': ('numerical', 'EXTERNAL MODEL METADATA · NO SOLVER RUN'),
         'source_only_gated': ('source_hold', 'SOURCE-ONLY GATED DESIGN · NOT RELEASED'),
         'source_context_metadata': ('source_context', 'SOURCE CONTEXT METADATA · NOT EXECUTED')}
BOUNDARY = ('Whole-paper DESIGN coverage only; not scientific reproduction or a runnable environment. '
            'Read-only author/evaluator reference; no actor loader, hardware control, solver or physical simulation. '
            'Operation lists are unordered membership; exact dependencies, lifecycle and repeated occurrence contracts remain authoritative. '
            'Holds and quarantine remain conditional, never mandatory successful steps. Requests do not establish observations.')
WARNINGS = {
 'lockable_origami': ('Thirty scientific design routes, sixty symbolic operations and 143 finite synthetic bookkeeping fixtures remain distinct. '
    'The default qualification hold and three other global hold views are navigation records, not additional scientific routes. '
    'Full fabrication, prepared intake and cut-coupon preparation retain separate ancestry and credit. '
    'Machine/cross direction, regular/irregular mode, mode and configuration revisions, first peak versus densification maximum, '
    'engaged fit windows, signed open-path work and residual set (not closed-loop loss), virgin/cycled/damaged status and controls remain explicit. '
    'Three main-compression specimens, five per density scale and five finite-size specimens per geometry differ from ten N4/four N6 cycles; mixed-mode modulus/area denominators and crosshead/DIC gauge lengths remain distinct. Eleven source conflict/scope records and nine required-input gates are not resolved by this display. '
    'Twelve movies were sampled at six positions each, not continuously played; peer-review contents were not read. '
    'Static illustrative folds are not source-exact CAD, validated contact, grasps or mechanics.'),
 'varactor': ('Twenty-eight scientific design routes, eighty symbolic operations and 160 finite synthetic bookkeeping fixtures remain distinct. '
    'The separate default qualification hold is navigation, not a 29th scientific route. '
    'STO and KTO identities, fixed loads, SQD and DQD devices, JPA comparison settings and measured/modelled channels remain distinct. '
    'The same STO pair persists across SQD and DQD while circuit/calibration revisions change; the source 320 nH model and 0805CS-331 part code remain distinct; manufacturer nominal value is unverified, as are any substituted operational settings. Lattice and electron temperatures remain distinct. Prepared intake earns no fabrication credit; revision-bound calibration, sample/module/thermal/bias/control history, '
    'hysteresis and independent safe release cannot be replaced by acknowledgements or source outcomes. '
    'Twelve conflict/scope records and eighteen unknown-input groups remain explicit, including unavailable Section V and unresolved units/material descriptions. '
    'Main source access was full JATS, not a main PDF; the raw source archive and author code were not ingested. '
    'Cleanroom, chemical, growth, beam, bonding, cryogenic, magnetic, RF/DC and cleanup services are closed unimplemented external boundaries.')}


def view(identifier, detail, filename, pointer, kind, label, members, membership_source):
    return {'id': identifier, 'label': label, 'route_kind': kind, 'metadata_only': not bool(members),
            'nodes': [{'type': 'obligations', 'label': 'Exact source operation membership · conditional entries stay conditional',
                       'ordered': False, 'children': clone(members),
                       'meta': {'order': BOUNDARY, 'membership_source': membership_source}},
                      contract('Exact source contract · unexpanded', detail, filename, pointer)],
            'basis': BOUNDARY, 'detail': clone(detail), 'source_file': filename, 'source_pointer': pointer,
            'navigation_basis': 'Authored inspection label; no new experiment, service completion, specimen or result'}


def projection(p, key):
    docs = {n.relative_to(p).as_posix(): read(p, n.relative_to(p).as_posix()) for n in sorted(p.rglob('*.json'))}
    raw = docs['operations.json']['operations']; branches = docs['branches.json']['branches']; prov = docs['provenance.json']
    folder = '../../tasks/' + p.name + '/'
    operations = []
    for i, original in enumerate(raw):
        mapped = operation(original, i)
        # Keep failure disposition and recovery instructions separate and exact.
        mapped['recovery'] = {name: clone(original[name]) for name in ('failure', 'recovery') if name in original}
        mapped['display_action_ownership'] = 'Original authored symbolic task action; cited scientific evidence is separate. No live device command.'
        operations.append(mapped)
    f = {'id': key, 'label': LABELS[key], 'title': prov['title'], 'doi': prov['doi'], 'color': COLORS[key],
         'family_scope': 'paper_level_design', 'family_scope_label': 'WHOLE-PAPER DESIGN',
         'source_commit': SOURCE_COMMITS[key], 'source_folder': folder,
         'source_link_mode': 'repository_relative_frozen_local_snapshot',
         'source_publication': 'Local source commit and per-file hashes are recorded; remote publication is not asserted. Links resolve within the repository.',
         'status': BOUNDARY + ' ' + WARNINGS[key], 'source_warnings': WARNINGS[key],
         'visibility': 'author_evaluator_reference_only', 'actor_projection_implemented': False,
         'operations': operations, 'routes': [],
         'evidence': {e['id']: clone(e) for e in docs['evidence_map.json']['evidence']},
         'context': {context_key(name): clone(value) for name, value in docs.items()},
         'dependencies': {'rule': 'Exact source partial-order and receipt contracts below; no universal executable instance graph is inferred from membership.',
                          **{name: clone(docs[name + '.json']) for name in
                             ('dependencies', 'preparation_routes', 'lifecycle_contract', 'transport_routes')}},
         'source_files': {name: {'url': folder + name, 'repository_path': 'tasks/' + p.name + '/' + name,
                                'sha256': hashlib.sha256((p / name).read_bytes()).hexdigest()} for name in docs},
         'default_route': docs['episode_input_contract.json']['default'],
         'default_route_basis': 'Exact episode default, shown as separate authored navigation; it does not add a scientific branch or qualify a service.',
         'asset_links': [],
         'asset_boundary': 'Existing original editable static 3D assets and renders, linked within this repository. Scene groups, anchors, dimensions and grasp markers are unqualified authored interfaces; no source-exact CAD, contact/grasp validation, interactive physics or physical execution.'}
    for i, branch in enumerate(branches):
        kind, label = KINDS[branch['execution_class']]
        r = view(branch['id'], branch, 'branches.json', f'/branches/{i}', kind,
                 label + ' · ' + branch['id'].replace('_', ' ').title(), branch['operation_ids'],
                 'Exact branches.json operation_ids; design_sequence and route_operation_ids retain their separate meanings')
        r['nodes'].append(contract('Exact lifecycle closure · independent evidence remains required',
                                   docs['lifecycle_contract.json'], 'lifecycle_contract.json', ''))
        f['routes'].append(r)
    default = f['default_route']
    f['routes'].append(view(default, docs['episode_input_contract.json'], 'episode_input_contract.json', '',
                           'qualification_hold', 'DEFAULT QUALIFICATION HOLD · NO ACTIVATION', [default],
                           'Authored navigation over the exact episode default operation'))
    for oid in docs['operations.json'].get('global_conditional_operation_ids', []):
        if oid == default: continue
        i = next(i for i, o in enumerate(raw) if o['id'] == oid)
        f['routes'].append(view(oid, raw[i], 'operations.json', f'/operations/{i}',
                               'conditional_recovery', 'GLOBAL CONDITIONAL HOLD · ' + oid.replace('_', ' ').title(), [oid],
                               'Authored navigation over source global_conditional_operation_ids; not an additional scientific branch'))
    bindings = docs['asset_binding_plan.json']['scene_assets']
    f['summary_counts'] = dict(Counter(r['route_kind'] + '_records' for r in f['routes']))
    f['summary_counts'].update(source_branches=len(branches), source_json_documents=len(docs),
                              synthetic_configurations=docs['STATUS.json'].get('synthetic_configuration_count', docs['STATUS.json'].get('finite_synthetic_fixture_count')),
                              scene_groups=len(bindings), symbolic_anchors=sum(len(a['required_anchor_ids']) for a in bindings),
                              source_evidence_entries=len(f['evidence']), source_conflicts=len(docs['source_conflicts.json']['conflicts']),
                              unresolved_input_groups=len(docs['unknown_parameters.json']['gates' if key == 'lockable_origami' else 'unknowns']),
                              control_records=len(docs['control_packages.json']['packages' if key == 'lockable_origami' else 'controls']))
    asset = docs['asset_binding_plan.json']['asset_package']; ap = p.parent.parent / 'assets' / asset
    for name in ['README.md'] + [n.relative_to(ap).as_posix() for n in sorted((ap / 'evidence').glob('*.png'))]:
        if not (ap / name).is_file(): raise ValueError('Missing static asset ' + name)
        f['asset_links'].append({'label': 'Original editable static 3D asset guide' if name == 'README.md' else 'Static render: ' + name.split('/')[-1].removesuffix('.png').replace('_', ' '),
                                'path': 'assets/' + asset + '/' + name,
                                'url': '../../assets/' + asset + '/' + name,
                                'sha256': hashlib.sha256((ap / name).read_bytes()).hexdigest()})
    return f


def validate_projection(f, p):
    if json.dumps(f, sort_keys=True, allow_nan=False) != json.dumps(projection(p, f['id']), sort_keys=True, allow_nan=False):
        raise ValueError('Recent-paper projection changed, omitted or invented source data or conservative display grammar')
    ids = [o['id'] for o in f['operations']]; branches = f['context']['branches']['branches']
    if len(ids) != len(set(ids)): raise ValueError('Duplicate operation ID')
    routes = [r['id'] for r in f['routes']]
    if len(routes) != len(set(routes)): raise ValueError('Duplicate route ID')
    used = {oid for r in f['routes'] for n in r['nodes'] if n['type'] == 'obligations' for oid in n['children']}
    if used != set(ids): raise ValueError('Unresolved or inaccessible operation')
    for branch in branches:
        expected = {o['id'] for o in f['operations'] if branch['id'] in o['detail']['branch_ids']}
        if set(branch['operation_ids']) != expected: raise ValueError('Source branch/operation reverse-index mismatch')
    for op in f['operations']:
        if not set(op['detail']['branch_ids']) <= {b['id'] for b in branches}: raise ValueError('Unresolved source branch')
        if not set(op['sources']) <= set(f['evidence']): raise ValueError('Unresolved source evidence')
    bound = {a['asset_id']: a for a in f['context']['asset_binding_plan']['scene_assets']}
    for op in f['operations']:
        for aid in op['objects']:
            if aid not in bound or op['id'] not in bound[aid]['bind_operation_ids']:
                raise ValueError('Unresolved task-to-asset operation binding')
    return True


def adapt_lockable_origami(p):
    f = projection(p, 'lockable_origami'); validate_projection(f, p); return f


def adapt_varactor(p):
    f = projection(p, 'varactor'); validate_projection(f, p); return f
