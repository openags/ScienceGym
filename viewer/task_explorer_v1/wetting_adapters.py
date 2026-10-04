"""Lossless wetting-task inspector. Static authored design, never execution."""
import hashlib
import json
from collections import Counter
from paired_adapters import clone, read, context_key, contract, absent
from recent_paper_adapters import view

PACKAGES = {'wetting': 'wetting_operations_v2'}
SOURCE_COMMIT = '23799405e6a68909a769c98285de5f22231965bc'
ASSET_PACKAGE = 'wetting_scene_assets_v1'
KINDS = {
    'authored_design': ('design_only', 'AUTHORED DESIGN'),
    'physical_service_and_manipulation_design': ('closed_service', 'CLOSED SERVICE / MANIPULATION DESIGN'),
    'external_service_only': ('external_service', 'EXTERNAL SEALED-RECEIPT BOUNDARY'),
    'physical_measurement_and_analysis_design': ('measurement_analysis', 'MEASUREMENT / ANALYSIS DESIGN'),
    'authored_analysis_service_design': ('numerical', 'EXTERNAL ANALYSIS DESIGN'),
    'analysis_design': ('analysis', 'AUTHORED ANALYSIS DESIGN'),
    'authored_safe_closeout': ('closeout', 'AUTHORED SAFE-CLOSEOUT DESIGN'),
}
BOUNDARY = ('Whole-paper DESIGN only; zero validated runnable whole-paper tasks. '
    'Read-only author/evaluator inspection, not an actor context, physical simulation, hardware control or scientific reproduction. '
    'Source facts and independently authored robot contracts remain separate. Display membership is not chronology: '
    'exact predecessor, material-ancestry, lifecycle and route-output contracts govern scope; no universal all-material AND gate is inferred. '
    'Requests do not establish measurements, qualification, safe release or completed external services.')
WARNINGS = ('Sixteen source design routes and seventy-four authored operation contracts remain distinct from the separate metadata-only default qualification-hold view. '
    'Ten source conflicts and twenty-five unresolved input groups remain open and claim-local. '
    'Cadmium-containing quantum-dot synthesis, ink handling and high-voltage deposition remain unmodeled closed external preparation; only a sealed specimen and independent receipt boundary is shown. '
    'Commercial silicone preparation and all hardware/analysis services remain unimplemented. '
    'Independent macro measurements, film specimens, image timepoints, fiducial sites, reference configurations and inverse-model results are not interchangeable replicates. '
    'No inferred 44-condition phase matrix, resolved thickness/modulus conflict, guessed missing SI Fig. 9 workbook, trusted source outcome or cTFM solver is supplied. '
    'Main text and all fifteen written SI pages were read upstream; main/SI figures were inspected. The movie was sampled at six times only, never continuously reviewed; workbook numerical cells remain unread. '
    'Original scene dimensions and anchors are illustrative, unqualified interfaces; no real physics, safe grasp or robot motion is established.')


def projection(p):
    docs = {n.relative_to(p).as_posix(): read(p, n.relative_to(p).as_posix()) for n in sorted(p.rglob('*.json'))}
    paper = docs['provenance.json']['paper']; raw = docs['operations.json']['operations']
    branches = docs['branches.json']['branches']; folder = '../../tasks/' + p.name + '/'
    operations = []
    for i, original in enumerate(raw):
        operations.append({'id': original['id'], 'title': original['description'],
            'stage': original['route_id'], 'actions': [original['description']],
            'objects': clone(original['asset_ids']),
            'pre': {'predecessor_operation_ids': clone(original['predecessor_operation_ids']),
                    'requires_route_outputs_from': clone(original['requires_route_outputs_from']),
                    'required_context': original['required_context']},
            'post': absent('post-state'),
            'acceptance': {'required_record_type': original['required_record_type'], 'evidence_role': original['evidence_role'],
                           'required_context': original['required_context']},
            'recovery': original['failure_transition'], 'sources': clone(original['source_evidence_ids']),
            'unknowns': clone(original['unknown_ids']), 'provenance': {'step_origin': original['step_origin'],
                'source_is_robot_protocol': original['source_is_robot_protocol']},
            'loop': None, 'detail': clone(original), 'source_file': 'operations.json', 'source_pointer': f'/operations/{i}',
            'display_mapping_basis': 'Exact authored description and record requirements; required evidence is not an observed post-state or source-reported robot protocol.',
            'display_title_basis': 'Exact source-package authored description; not a paper quotation',
            'display_action_ownership': 'Independently authored symbolic task design, not a source human trajectory or live device command.'})
    f = {'id': 'wetting', 'label': 'Wetting transitions on soft materials', 'title': paper['title'], 'doi': paper['doi'], 'color': '#82d0ce',
         'family_scope': 'paper_level_design', 'family_scope_label': 'WHOLE-PAPER DESIGN',
         'source_commit': SOURCE_COMMIT, 'source_folder': folder,
         'source_link_mode': 'repository_relative_frozen_local_snapshot',
         'source_publication': 'Local source commit and per-file hashes are recorded; remote publication is not asserted. Links resolve within the repository.',
         'status': BOUNDARY + ' ' + WARNINGS, 'source_warnings': WARNINGS,
         'visibility': 'author_evaluator_reference_only', 'actor_projection_implemented': False,
         'operations': operations, 'routes': [], 'evidence': {e['id']: clone(e) for e in docs['evidence_map.json']['records']},
         'context': {context_key(name): clone(value) for name, value in docs.items()},
         'dependencies': {'display_rule': 'Exact dependency records, without invented chronology or all-material preparation requirements.',
                          **{name: clone(docs[name + '.json']) for name in ('dependencies', 'preparation_routes', 'lifecycle_contract', 'lineage_contract', 'transport_routes', 'recovery_boundaries')}},
         'source_files': {name: {'url': folder + name, 'repository_path': 'tasks/' + p.name + '/' + name,
                                'sha256': hashlib.sha256((p / name).read_bytes()).hexdigest()} for name in docs},
         'default_route': docs['episode_input_contract.json']['default'],
         'default_route_basis': 'Exact episode default shown as metadata-only authored navigation; no invented hold operation or additional scientific branch.',
         'asset_links': [],
         'asset_boundary': 'Original editable static 3D assets and renders only. The task asset_pack_id is a logical identifier; the repository folder is wetting_scene_assets_v1. Anchors, scales and handling interfaces remain unqualified, with no source-exact CAD, contact model, validated grasp, real physics or physical execution.'}
    for i, branch in enumerate(branches):
        kind, label = KINDS[branch['kind']]
        r = view(branch['id'], branch, 'branches.json', f'/branches/{i}', kind,
                 label + ' · ' + branch['title'], branch['route_operation_ids'],
                 'Exact branches.json route_operation_ids; predecessor_operation_ids and required route outputs remain separately authoritative')
        r['basis'] = BOUNDARY
        r['nodes'][0]['meta']['order'] = BOUNDARY
        r['nodes'].append(contract('Exact lifecycle and safe closeout · independent records required', docs['lifecycle_contract.json'], 'lifecycle_contract.json', ''))
        f['routes'].append(r)
    hold = view(f['default_route'], docs['episode_input_contract.json'], 'episode_input_contract.json', '',
                'qualification_hold', 'DEFAULT QUALIFICATION HOLD · NO ACTIVATION', [],
                'Metadata-only episode default; no corresponding source operation is invented')
    hold['basis'] = BOUNDARY
    hold['nodes'] = [contract('Exact qualification-hold input contract · no activation', docs['episode_input_contract.json'], 'episode_input_contract.json', '')]
    f['routes'].append(hold)
    assets = docs['asset_binding_plan.json']['assets']
    f['summary_counts'] = dict(Counter(r['route_kind'] + '_records' for r in f['routes']))
    f['summary_counts'].update(source_branches=len(branches), source_json_documents=len(docs),
        scene_groups=len(assets), symbolic_anchors=sum(len(a['required_anchor_ids']) for a in assets),
        source_evidence_entries=len(f['evidence']), source_conflicts=len(docs['source_conflicts.json']['conflicts']),
        unresolved_input_groups=len(docs['unknown_parameters.json']['unknowns']),
        source_reported_control_records=len(docs['controls_and_repeats.json']['source_reported']))
    ap = p.parent.parent / 'assets' / ASSET_PACKAGE
    for name in ['README.md'] + [n.relative_to(ap).as_posix() for n in sorted((ap / 'evidence').glob('*.png'))]:
        if not (ap / name).is_file(): raise ValueError('Missing original static asset: ' + name)
        f['asset_links'].append({'label': 'Original static 3D asset guide' if name == 'README.md' else 'Static render: ' + name.split('/')[-1].removesuffix('.png'),
            'path': 'assets/' + ASSET_PACKAGE + '/' + name, 'url': '../../assets/' + ASSET_PACKAGE + '/' + name,
            'sha256': hashlib.sha256((ap / name).read_bytes()).hexdigest()})
    return f


def validate_projection(f, p):
    if json.dumps(f, sort_keys=True, allow_nan=False) != json.dumps(projection(p), sort_keys=True, allow_nan=False):
        raise ValueError('Wetting projection omitted, changed or invented a source contract or display boundary')
    ids = [o['id'] for o in f['operations']]; branches = f['context']['branches']['branches']
    if len(ids) != len(set(ids)): raise ValueError('Duplicate operation')
    if len({r['id'] for r in f['routes']}) != len(f['routes']): raise ValueError('Duplicate inspection route')
    if f['default_route'] in ids: raise ValueError('Qualification hold must not invent an operation')
    if {oid for b in branches for oid in b['route_operation_ids']} != set(ids): raise ValueError('Unresolved operation inventory')
    bound = {a['asset_id']: a for a in f['context']['asset_binding_plan']['assets']}
    for branch in branches:
        if branch['route_operation_ids'] != [o['id'] for o in f['operations'] if o['detail']['route_id'] == branch['id']]:
            raise ValueError('Branch/operation mismatch')
    for operation in f['operations']:
        o = operation['detail']
        if not set(o['predecessor_operation_ids']) <= set(ids): raise ValueError('Unresolved predecessor')
        if not set(o['source_evidence_ids']) <= set(f['evidence']): raise ValueError('Unresolved evidence')
        for aid in o['asset_ids']:
            if aid not in bound or o['id'] not in bound[aid]['bind_operation_ids']: raise ValueError('Unresolved asset binding')
        for anchor in o['anchor_ids']:
            aid, name = anchor.split('.', 1)
            if aid not in bound or name not in bound[aid]['required_anchor_ids']: raise ValueError('Unresolved symbolic anchor')
    return True


def adapt_wetting(p):
    f = projection(p); validate_projection(f, p); return f
