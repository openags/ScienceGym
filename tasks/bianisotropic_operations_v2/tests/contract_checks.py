"""Static consistency checks, not authenticated hardware or acoustic validation.

Every record accepted here is still an untrusted input. Synthetic examples test
bookkeeping invariants only. No pressure field, optimizer or physical model runs.
"""
from __future__ import annotations
import json
import cmath
from datetime import datetime
import math
from pathlib import Path

CONDITION_KEYS = ('guide_revision', 'frame_id', 'source_calibration_id',
                  'microphone_id', 'daq_config_id', 'phase_reference_id',
                  'medium_card_id', 'frequency_hz', 'grid_id')

def need(condition, message):
    if not condition:
        raise ValueError(message)

def nonempty(value):
    return value is not None and value not in ('', [], {})

def strict_load(path):
    def pairs(items):
        result = {}
        for k, v in items:
            need(k not in result, 'duplicate JSON key')
            result[k] = v
        return result
    def reject(value):
        raise ValueError('nonfinite JSON: ' + value)
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs, parse_constant=reject)

def index(rows):
    need(isinstance(rows, list) and bool(rows), 'nonempty list required')
    result = {}
    for row in rows:
        need(isinstance(row, dict), 'record must be an object')
        key = row.get('id')
        need(isinstance(key, str) and bool(key) and key not in result, 'missing or duplicate ID')
        result[key] = row
    return result

def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)

def positive_integer(value):
    return type(value) is int and value > 0

def validate_dag(nodes, edges):
    nodes = set(nodes)
    adjacency = {n: set() for n in nodes}
    for before, after in edges:
        need(before in nodes and after in nodes, 'dangling dependency')
        adjacency[before].add(after)
    visiting, done = set(), set()
    def visit(n):
        need(n not in visiting, 'dependency cycle')
        if n in done:
            return
        visiting.add(n)
        for child in adjacency[n]:
            visit(child)
        visiting.remove(n)
        done.add(n)
    for n in nodes:
        visit(n)
    return True

def require_cards(required_ids, cards):
    for key in required_ids:
        card = cards.get(key)
        need(isinstance(card, dict), 'missing card: ' + key)
        need(nonempty(card.get('value')), 'empty card: ' + key)
        need(card.get('origin') in ('task_authored', 'qualified_episode_input'), 'unqualified origin')
        need(card.get('qualified') is True and nonempty(card.get('revision')) and nonempty(card.get('approver')), 'unqualified card')
    return True

def validate_schedule(points):
    by_id = index(points)
    poses = []
    for p in points:
        xy = p.get('xy')
        need(isinstance(xy, list) and len(xy) == 2 and all(finite_number(x) for x in xy), 'invalid point pose')
        poses.append(tuple(xy))
    need(len(poses) == len(set(poses)), 'duplicate point position')
    return by_id

def validate_panel(panel):
    need(panel.get('angle_deg') == 60, 'only 60-degree physical route is source-supported')
    need(positive_integer(panel.get('assembly_version')), 'invalid panel version')
    need(panel.get('inspection_version') == panel['assembly_version'], 'stale panel inspection')
    need(panel.get('orientation') == 'qualified_incident_face', 'wrong panel orientation')
    sections = panel.get('sections')
    by_id = index(sections)
    need(len(by_id) == 9, 'nine distinct physical period sections required')
    need({s.get('slot') for s in sections} == set(range(1, 10)), 'period slots incomplete')
    for section in sections:
        need(section.get('status') == 'accepted' and nonempty(section.get('build_id')), 'unqualified section')
        need(section.get('design_slots') == list(range(1, 12)), 'wrong local-cell order')
        need(section.get('location') == panel.get('id') and nonempty(panel.get('id')), 'custody mismatch')
    return True

def validate_build_release(receipt):
    for key in ('job_complete', 'thermal_safe', 'motion_stopped', 'guard_release'):
        need(receipt.get(key) is True, 'unsafe or incomplete build release: ' + key)
    need(nonempty(receipt.get('job_id')) and nonempty(receipt.get('geometry_revision')), 'unidentified build')
    return True

def validate_scan(points, records, context):
    expected = validate_schedule(points)
    need(isinstance(records, list) and records, 'empty acquisition ledger')
    need(context.get('configuration_id') in ('blank_reflection','sample_reflection','sample_transmission'), 'unknown measurement configuration')
    need(context.get('calibration_valid') is True, 'invalid calibration')
    need(context.get('is_mock') is True, 'unit-test validator is not physical authentication')
    for key in CONDITION_KEYS:
        need(nonempty(context.get('condition', {}).get(key)), 'missing condition signature')
    need(nonempty(context.get('calibration_id')) and nonempty(context.get('run_id')), 'missing run identity')
    required_context = ['episode_id','branch_id','configuration_id','run_id','calibration_id','panel_id','assembly_version','install_epoch','frequency_hz','units']
    for key in ('episode_id','branch_id','units'):
        need(isinstance(context.get(key),str) and bool(context[key]), 'missing episode, branch or units')
    need(finite_number(context.get('frequency_hz')) and context['frequency_hz']>0 and context['frequency_hz']==context['condition']['frequency_hz'], 'invalid acquisition frequency')
    if context['configuration_id'] == 'blank_reflection':
        need(context.get('panel_id') == 'blank' and context.get('assembly_version') is None and context.get('install_epoch') is None, 'blank contains panel')
    else:
        need(context.get('panel_id') not in (None,'','blank') and positive_integer(context.get('assembly_version')) and positive_integer(context.get('install_epoch')), 'sample identity missing')
    ids, filled = set(), set()
    for record in records:
        required_raw_keys={'raw_id','episode_id','branch_id','run_id','configuration_id','panel_id','assembly_version','install_epoch','point_id','repeat_index','pose_receipt_id','frequency_hz','calibration_id','condition','timestamp','units','status','content_hash','is_mock'}
        need(required_raw_keys<=set(record), 'missing canonical raw-record fields')
        need(isinstance(record.get('timestamp'),str), 'timestamp must include timezone')
        try:
            stamp=datetime.fromisoformat(record['timestamp'].replace('Z','+00:00'))
        except (ValueError,TypeError):
            raise ValueError('invalid timestamp')
        need(stamp.tzinfo is not None, 'timestamp lacks timezone')
        raw_id = record.get('raw_id')
        need(isinstance(raw_id, str) and raw_id and raw_id not in ids, 'duplicate raw record ID')
        ids.add(raw_id)
        need(record.get('point_id') in expected, 'point outside schedule')
        need(all(record.get(k) == context.get(k) for k in required_context), 'mixed scan identity')
        need(record.get('condition') == context['condition'], 'mixed condition or stale calibration')
        need(record.get('is_mock') is True, 'unlabeled mock fixture')
        if context['configuration_id'] != 'blank_reflection':
            need(positive_integer(record.get('assembly_version')) and positive_integer(record.get('install_epoch')), 'record revision has wrong type')
        need(record.get('status') in ('valid','invalid'), 'unknown acquisition status')
        need(type(record.get('repeat_index')) is int and record['repeat_index'] in (1,2,3,4), 'invalid repeat index')
        need(nonempty(record.get('content_hash')), 'no raw artifact hash')
        if record['status'] == 'invalid':
            need(nonempty(record.get('invalid_reason')), 'failed attempts need reason')
            continue
        key = (record['point_id'],record['repeat_index'])
        need(key not in filled, 'duplicate valid point/repeat')
        filled.add(key)
        need(record.get('clipped') is False and record.get('settled') is True, 'invalid acquisition quality')
        need(record.get('pose_xy') == expected[record['point_id']]['xy'], 'wrong point pose')
        need(nonempty(record.get('pose_receipt_id')), 'no pose evidence')
        need(record.get('calibration_current') is True, 'calibration expired during acquisition')
    need(filled == {(point_id, r) for point_id in expected for r in range(1,5)}, 'incomplete scan')
    return True

def validate_reflection_pair(blank, sample, analysis):
    need(blank.get('configuration_id') == 'blank_reflection' and sample.get('configuration_id') == 'sample_reflection', 'wrong region/configuration pair')
    for field in (blank, sample):
        need(field.get('complete') is True and field.get('representation') == 'complex_pressure', 'complex complete field required')
        need(nonempty(field.get('raw_parent_ids')) and field.get('is_mock') is True, 'missing parents or mock label')
        need(field.get('post_drift_valid') is True, 'failed closing drift')
    for key in CONDITION_KEYS:
        need(nonempty(blank.get('condition', {}).get(key)), 'missing reference signature')
    need(blank['condition'] == sample.get('condition'), 'incompatible blank/reference signatures')
    need(blank.get('point_ids') and blank['point_ids'] == sample.get('point_ids'), 'reflection grid mismatch')
    need(blank.get('panel_id') == 'blank' and sample.get('panel_id') not in (None,'','blank'), 'panel identity mismatch')
    need(analysis.get('mode') == 'complex_sample_minus_blank', 'magnitude subtraction forbidden')
    need(analysis.get('blank_id') == blank.get('id') and analysis.get('sample_id') == sample.get('id'), 'wrong raw parent pair')
    need(analysis.get('pair_validity_current') is True, 'pair expired or frame moved')
    sample_keys=('episode_id','branch_id','run_id','panel_id','assembly_version','install_epoch')
    expected=analysis.get('expected_sample_context')
    need(isinstance(expected,dict) and set(expected)==set(sample_keys), 'missing expected sample context')
    for key in sample_keys:
        need(nonempty(expected.get(key)) and sample.get(key)==expected[key], 'stale or substituted sample context: '+key)
    need(positive_integer(sample.get('assembly_version')) and positive_integer(sample.get('install_epoch')), 'sample version/epoch missing')
    need(blank.get('assembly_version') is None and blank.get('install_epoch') is None, 'blank carries sample revision')
    for key in ('episode_id','branch_id'):
        need(blank.get(key)==sample.get(key), 'cross-campaign blank substitution')
    need(nonempty(analysis.get('expected_blank_run_id')) and blank.get('run_id')==analysis['expected_blank_run_id'], 'wrong blank run')
    need(set(analysis.get('raw_parent_ids', [])) == set(blank['raw_parent_ids'] + sample['raw_parent_ids']), 'parent loss or substitution')
    return True

def validate_metric(metric):
    types = {
      'incident_to_target_efficiency': ('incident_normal_flux','propagating_normal_flux'),
      'transmitted_direction_share': ('total_transmitted_normal_flux','propagating_normal_flux'),
      'reflected_energy_fraction': ('declared_reference_normal_flux','propagating_normal_flux'),
      'near_field_order_amplitude': ('declared_amplitude_normalization','complex_amplitude'),
      'theoretical_GSL_bound': ('incident_normal_flux','theory')}
    name = metric.get('name')
    need(name in types, 'unknown metric')
    denominator, quantity = types[name]
    need(metric.get('denominator') == denominator and metric.get('quantity') == quantity, 'metric denominator or quantity confusion')
    need(finite_number(metric.get('value')), 'invalid metric value')
    need(nonempty(metric.get('source_record_id')), 'no result evidence')
    if quantity == 'propagating_normal_flux':
        need(metric.get('includes_evanescent_as_power') is False, 'evanescent amplitude is not normal energy flux')
        need(0 <= metric['value'] <= 1, 'fraction outside range')
    return True

def validate_numerical_pair(a, b):
    need(a.get('id') != b.get('id'), 'same job reused as control')
    need(a.get('kind') == 'bianisotropic' and b.get('kind') == 'ideal_GSL', 'missing GSL comparator')
    for job in (a,b):
        need(job.get('evidence_type') == 'synthetic_numerical_job_fixture', 'fixture evidence type confusion')
        need(job.get('converged') is True and nonempty(job.get('field_artifact')) and nonempty(job.get('mesh_study_id')), 'unconverged or absent numerical evidence')
    keys=('angle_deg','cells_per_period','frequency_hz','source_signature','medium_card','domain_card','PML_card','flux_definition')
    for key in keys:
        need(nonempty(a.get(key)) and a.get(key) == b.get(key), 'unmatched numerical control: '+key)
    need(a['angle_deg'] in (60,70,80), 'angle outside source design scope')
    need(a['cells_per_period'] == (11 if a['angle_deg']==60 else 4), 'wrong spatial discretization')
    return True

def matrix_condition_1(matrix):
    """Exact 2x2 one-norm conditioning of synthetic supplied numbers only."""
    a,b=matrix[0]; cc,d=matrix[1]
    determinant=a*d-b*cc
    need(abs(determinant)>0, 'linearly dependent retrieval states')
    norm=max(abs(a)+abs(cc),abs(b)+abs(d))
    inverse_norm=max(abs(d)+abs(cc),abs(b)+abs(a))/abs(determinant)
    result=norm*inverse_norm
    need(math.isfinite(result), 'nonfinite conditioning')
    return result

def matrix_multiply_2(a, b):
    return [[sum(a[i][n]*b[n][j] for n in range(2)) for j in range(2)] for i in range(2)]

def matrix_inverse_2(m):
    a,b=m[0];cc,d=m[1]
    determinant=a*d-b*cc
    need(abs(determinant)>0, 'singular matrix')
    return [[d/determinant,-b/determinant],[-cc/determinant,a/determinant]]

def validate_retrieval(records, conditioning_limit):
    need(finite_number(conditioning_limit) and conditioning_limit > 1, 'missing conditioning bound')
    need(len(records)==2 and {r.get('termination') for r in records}=={'plane_wave_radiation','hard_wall'}, 'two independent terminations required')
    need(len({r.get('job_id') for r in records})==2, 'duplicated termination job')
    first=records[0]
    matching=('geometry_revision','frequency_hz','medium_card_id','source_signature','port_convention','wavenumber_rad_m','cell_datum_m','probe_positions_m')
    for r in records:
        need(r.get('converged') is True and r.get('is_mock') is True, 'unconverged or unlabeled retrieval fixture')
        for key in matching:
            need(nonempty(r.get(key)) and r.get(key)==first.get(key), 'retrieval signature mismatch: '+key)
        need(finite_number(r.get('frequency_hz')) and r['frequency_hz']>0, 'invalid retrieval frequency')
        need(finite_number(r.get('wavenumber_rad_m')) and r['wavenumber_rad_m']>0, 'invalid retrieval wavenumber')
        need(r.get('probe_ids') == ['p1','p2','p3','p4'], 'four ordered probes required')
        p=r.get('pressures')
        need(isinstance(p,list) and len(p)==4 and all(isinstance(z,list) and len(z)==2 and all(finite_number(x) for x in z) for z in p), 'four finite complex pressures required')
        positions=r.get('probe_positions_m')
        need(isinstance(positions,list) and len(positions)==4 and all(finite_number(x) for x in positions) and positions==sorted(set(positions)), 'four distinct ordered probe positions required')
        need(finite_number(r.get('cell_datum_m')) and positions[1] < r['cell_datum_m'] < positions[2], 'cell datum must separate the probe pairs')
        k=r['wavenumber_rad_m']
        for pair in (positions[:2],positions[2:]):
            matrix=[[cmath.exp(-1j*k*x),cmath.exp(1j*k*x)] for x in pair]
            need(matrix_condition_1(matrix)<=conditioning_limit, 'ill-conditioned probe spacing')
    upstream=[[complex(*r['pressures'][i]) for r in records] for i in range(2)]
    need(matrix_condition_1(upstream)<=conditioning_limit, 'ill-conditioned independent termination pressures')
    # SI Note3-style interface inversion, with velocity multiplied by Z0 so
    # both rows have pressure units. This tests supplied synthetic algebra only.
    k=first['wavenumber_rad_m'];x0=first['cell_datum_m']
    probe_matrix=[[cmath.exp(-1j*k*x),cmath.exp(1j*k*x)] for x in first['probe_positions_m'][:2]]
    wave_amplitudes=matrix_multiply_2(matrix_inverse_2(probe_matrix),upstream)
    forward,backward=cmath.exp(-1j*k*x0),cmath.exp(1j*k*x0)
    normalized_interface=matrix_multiply_2([[forward,backward],[forward,-backward]],wave_amplitudes)
    need(matrix_condition_1(normalized_interface)<=conditioning_limit, 'ill-conditioned interface pressure/normalized-velocity inversion')
    return True

def validate_ga(config, cell_ids, runs):
    expected={'population':10,'mutation_rate':0.2,'retention_fraction':0.5,'elite_mutates':False,'crossover':False,'generation_limit':1500,'restarts_per_cell':50}
    for key,value in expected.items():
        need(type(config.get(key)) is type(value) and config.get(key)==value, 'baseline GA changed: '+key)
    need(nonempty(config.get('objective_revision')) and nonempty(config.get('bounds_revision')), 'missing objective or bounds')
    need(cell_ids and len(set(cell_ids))==len(cell_ids), 'nonempty distinct cell IDs required')
    seen=set()
    for run in runs:
        key=(run.get('cell_id'),run.get('restart'))
        need(key not in seen and key[0] in cell_ids and type(key[1]) is int and 1<=key[1]<=50, 'invalid or duplicated restart')
        seen.add(key)
        need(run.get('status') in ('completed','failed'), 'unfinished restart')
        need(nonempty(run.get('history_id')) and type(run.get('seed')) is int, 'missing optimization lineage')
        if run['status']=='completed':
            need(run.get('generation_count')==1500, 'undeclared early stopping')
        else:
            need(nonempty(run.get('failure_reason')), 'missing failed-search evidence')
    need(seen == {(cell,r) for cell in cell_ids for r in range(1,51)}, 'missing restarts')
    return True

def validate_archive(manifest):
    required=('raw_immutable','all_attempts_retained','lineage_complete','report_scoped')
    for key in required:
        need(manifest.get(key) is True, 'archive missing '+key)
    need(type(manifest.get('physical_campaign')) is bool, 'physical scope required')
    need(type(manifest.get('measurement_selected')) is bool, 'measurement scope required')
    if manifest['physical_campaign']:
        stations=manifest.get('used_stations')
        need(isinstance(stations,list) and stations and all(isinstance(x,str) and x for x in stations) and len(stations)==len(set(stations)), 'used station scope required')
        for key in ('custody_complete','cleanup_complete'):
            need(manifest.get(key) is True,'physical closure missing '+key)
        if 'WS_PRINT' in stations:
            for key in ('print_job_terminal','print_thermal_safe','print_motion_stopped','print_guard_release'):
                need(manifest.get(key) is True,'fabrication closure missing '+key)
        if 'WS_GUIDE' in stations:
            for key in ('source_off','motion_stopped'):
                need(manifest.get(key) is True,'guide closure missing '+key)
        if manifest['measurement_selected']:
            need('WS_GUIDE' in stations, 'measurement needs guide station')
            need(manifest.get('post_drift_valid') is True, 'measurement closing drift required')
    else:
        need(manifest['measurement_selected'] is False, 'physical measurement mislabeled as computational')
    need(manifest.get('evidence_claim') == 'synthetic_bookkeeping_only', 'cannot claim physical execution from a static fixture')
    return True

def actor_projection(payload):
    """Testable minimal projection policy, not a production actor-loader.

    Exact finite schema rejects opaque nested card bodies. Full qualified cards
    need a separately reviewed typed loader before any runtime use.
    """
    allowed={'goal_id','inventory','observations','qualified_card_ids'}
    need(isinstance(payload,dict) and set(payload)<=allowed, 'unexpected actor input key')
    need(isinstance(payload.get('goal_id'),str) and payload['goal_id'], 'missing actor goal')
    result={'goal_id':payload['goal_id']}
    for category,fields in [('inventory',{'id','location','status'}),('observations',{'id','observable','value','acquired'})]:
        records=payload.get(category,[])
        need(isinstance(records,list), 'actor records must be lists')
        for r in records:
            need(isinstance(r,dict) and set(r)==fields, 'nested evaluator leakage')
            need(all(type(v) in (str,int,float,bool) or v is None for v in r.values()), 'opaque nested actor value')
            if category=='observations':
                need(r['acquired'] is True, 'future observation leak')
                need(r['observable'] in {'part_inspection_status','source_off','stage_pose','calibration_valid','acquisition_status'}, 'unapproved observable')
        result[category]=records
    ids=payload.get('qualified_card_ids',[])
    need(isinstance(ids,list) and all(isinstance(i,str) and i for i in ids), 'opaque card leak')
    result['qualified_card_ids']=ids
    return result
