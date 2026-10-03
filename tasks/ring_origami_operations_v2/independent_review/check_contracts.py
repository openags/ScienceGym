"""Finite independent contract checks; no robot, instrument or physics execution."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = {p.stem: json.loads(p.read_text()) for p in ROOT.glob('*.json')}
O = {x['id']: x for x in D['operations']['operations']}
B = {x['id']: x for x in D['branches']['branches']}
P = D['branches']['preparation_routes']
S = {x['id']: x for x in D['station_contracts']['stations']}
U = {x['id'] for x in D['unknown_parameters']['parameters']}
E = {x['id'] for x in D['provenance']['evidence']}
checks = []

def check(name, ok):
    checks.append({'check': name, 'passed': bool(ok)})

def oprefs(value, bindings=None):
    """Extract operation references from supported route container keys."""
    bindings = bindings or {}
    out = []
    if isinstance(value, str):
        if value in O or value.startswith('@'):
            out.append(bindings.get(value, value))
    elif isinstance(value, list):
        for v in value:
            out.extend(oprefs(v, bindings))
    elif isinstance(value, dict):
        for key in ['operation', 'steps', 'body', 'concurrent', 'postprocess']:
            if key in value:
                out.extend(oprefs(value[key], bindings))
    return out

def body(branch):
    return oprefs(B[branch]['test_body'], B[branch]['operation_bindings'])

def allrefs(value, key):
    out = []
    if isinstance(value, dict):
        for k, v in value.items():
            if k == key:
                out.extend(v)
            else:
                out.extend(allrefs(v, key))
    elif isinstance(value, list):
        for v in value:
            out.extend(allrefs(v, key))
    return out

check('Operation IDs are unique and declared count is accurate', len(O) == len(D['operations']['operations']) == D['operations']['count'])
check('Every operation station resolves', all(x['station_id'] in S for x in O.values()))
check('Every operation source and unknown reference resolves', all(set(x['source_evidence_ids']) <= E and set(x['unknown_input_ids']) <= U for x in O.values()))
fields = ['actor', 'objects', 'tool', 'interface', 'preconditions', 'action', 'completion_evidence', 'failure_and_recovery', 'ownership']
check('Physical operations have actor tool state interface evidence and failure fields', all(all(x.get(k) for k in fields) for x in O.values()))
check('Device processes have device ownership and are distinct from robot handling', all(x['actor'] == 'device' for x in O.values() if x['translation_kind'] == 'device_process') and all(O[i]['actor'] == 'robot' for i in ['PRINT_LOAD','PRINT_SET','PRINT_START','PRINT_RECEIVE','PLOTTER_LOAD','PLOTTER_START','PLOTTER_RECEIVE']))
check('All branch preparation routes resolve', all(x['preparation_route'] in P for x in B.values()))
check('All branch operation macros resolve', all(set(body(i) + x['assembly_operations'] + x['closure_operations']) <= O.keys() for i, x in B.items()))
check('All route operation references resolve', all(set(oprefs(x)) <= O.keys() for x in P.values()))
check('All branch source and required-input references resolve', all(set(x['source_evidence_ids']) <= E and set(x['required_input_ids']) <= U for x in B.values()))
check('Campaign covers all declared physical branches', set(D['branches']['campaign']['required_branch_ids']) == set(B))
check('Coverage references resolve and physical families are retained', all(set(x['task_branch_ids']) <= B.keys() and set(x['source_evidence_ids']) <= E for x in D['coverage_matrix']['rows']) and D['coverage_matrix']['all_physical_families_disposed'])
check('Thick and paper fabrication are separate routes', P['PREP_THICK'] != P['PREP_PAPER'] and 'PAPER_FOLD' in oprefs(P['PREP_PAPER']) and 'ELEMENT_CLOSE' in oprefs(P['PREP_THICK']))
check('Both fabrication routes retain actual print handling and output QC', all(set(['PRINT_LOAD','PRINT_SET','PRINT_START','PRINT_PROCESS','PRINT_RECEIVE','PART_QC']) <= set(oprefs(P[i])) for i in ['PREP_THICK','PREP_PAPER']))
check('Paper route includes actual plotter handling and folding', set(['PLOTTER_LOAD','PLOTTER_SET','PLOTTER_START','PLOTTER_PROCESS','PLOTTER_RECEIVE','PAPER_FOLD','PAPER_FRAME','PAPER_CONNECT']) <= set(oprefs(P['PREP_PAPER'])))
check('Crease coupon does not inherit completed-element assembly', 'PART_QC' in oprefs(P[B['CREASE_TENDENCY']['preparation_route']]) and 'ELEMENT_CLOSE' not in oprefs(P[B['CREASE_TENDENCY']['preparation_route']]))
check('Thick element assembly includes trimming sliding closure and frames', set(['HINGE_JOIN','CREASE_FASTEN','TRIM_SCREWS','FACET_III_JOIN','ELEMENT_CLOSE','FRAME_JOIN','ELEMENT_QC']) <= set(oprefs(P['PREP_THICK'])))
check('Unqualified resin treatment is not imposed on every material', 'TPU/accessory job does not inherit resin wash/cure' in json.dumps(P['PREP_THICK']))
check('Observation is a service without specimen transport', S['WS_OBSERVE']['physical_location'] is False and S['WS_OBSERVE']['specimen_movement'] == 'none')
check('Observed test specimen remains outside mobile transport', any('unloaded and untethered' in x for x in O['TRANSFER']['preconditions']))
mechanical = [i for i, x in B.items() if x['execution_mode'] == 'mechanical']
check('All mechanical branches configure arm acquire reset and unload', all(set(['CONFIG_TEST','ARM_TEST','TEST_PROCESS','SAFE_RESET','UNLOAD']) <= set(body(i)) for i in mechanical))
check('Mechanical acquisition precedes reset and unload', all(body(i).index('ARM_TEST') < body(i).index('TEST_PROCESS') < body(i).index('SAFE_RESET') < body(i).index('UNLOAD') for i in mechanical))
check('Quantitative thick branches reach measured-response analysis', all('ANALYZE_ELEMENT' in body(i) for i in mechanical))
check('Torsion analyses retain raw-image geometry and semi-experimental status', all(body(i).index('MANUAL_LOAD') < body(i).index('ANALYZE_IMAGE') < body(i).index('ANALYZE_TORQUE') for i in ['TRI_TORSION','QUAD_TORSION']) and 'semi_experimental' in json.dumps(O['ANALYZE_TORQUE']))
check('Torsion lineage requires measured element and geometry parents', len(D['lineage_contract']['semi_experimental_torque_required_parents']) >= 4 and any('measured element' in x for x in D['lineage_contract']['semi_experimental_torque_required_parents']))
angles = [22.5,45,67.5,90,112.5,135,157.5]
check('Both paper-array branches retain all seven source angle settings', all([x['angle_deg'] for x in B[i]['conditions']] == angles for i in ['ARRAY_COMPRESSION','ARRAY_TENSION']))
check('Array modes and classes remain separate', all(x['class'] == 'C_III' and x['load_mode'] == 'compression' for x in B['ARRAY_COMPRESSION']['conditions']) and all(x['class'] == 'C_I' and x['load_mode'] == 'tension' for x in B['ARRAY_TENSION']['conditions']))
check('Array analysis retains three widths and distinct baselines', len(D['lineage_contract']['array_ratio_required_parents']) >= 6 and 'mean' in O['ANALYZE_ARRAY']['action'] and 'zero axial strain' in O['ANALYZE_ARRAY']['action'])
check('Array observation remains concurrent with recorded displacement', all(any(isinstance(x,dict) and set(['TEST_PROCESS','MEASURE_WIDTH']) <= set(x.get('concurrent',[])) for x in B[i]['test_body']) for i in ['ARRAY_COMPRESSION','ARRAY_TENSION']))
check('Qualitative array transformation does not claim acquired force data', B['ARRAY_TRANSFORMATION']['execution_mode'] == 'qualitative' and 'ANALYZE_ARRAY' not in body('ARRAY_TRANSFORMATION') and 'unsupported mixed-array force' in B['ARRAY_TRANSFORMATION']['goal'])
check('Transformation preserves unloaded state and configuration evidence', all('unloaded' in json.dumps(O[i]['preconditions']).lower() or 'safe reset' in json.dumps(O[i]['preconditions']).lower() for i in ['GROUP_TRANSFORM','RING_RECONFIG','ARRAY_PIN','ARRAY_TRANSFORM']))
check('Source replica count is limited to element response', B['ELEMENT_RESPONSE']['source_repetition_count'] == 3 and all(x['source_repetition_count'] is None for i,x in B.items() if i != 'ELEMENT_RESPONSE'))
check('Source conflicts preserve loading direction angle notation and landmark issues', {'SC_DIRECTION_METHODS','SC_DIRECTION_CAPTIONS','SC_ANGLE_SET','SC_LANDMARK','SC_RATE_UNITS'} <= {x['id'] for x in D['source_conflicts']['conflicts']})
movies = D['source_access_audit']['movies']
check('Movie 9 remains unread and explicitly method-bearing', next(x for x in movies if x['number'] == 9)['status'] == 'unread' and next(x for x in movies if x['number'] == 9)['method_bearing'] is True)
check('Unread other movies do not claim verified non-method status', all(x.get('method_bearing') is not False for x in movies if x['number'] != 9))
check('Assembly motion retains unresolved choreography gate', 'U_MOVIES' in O['HINGE_JOIN']['unknown_input_ids'] and 'U_MOVIES' in O['CREASE_FASTEN']['unknown_input_ids'])
check('The episode gates every actually selected operation input', any('used by a selected operation' in x for x in D['episode_input_contract']['rules']))
check('Lineage preserves identity changes raw-derived types and failures', {'measured','image_derived','semi_experimental','analytical_model','source_reference','mock'} <= set(D['lineage_contract']['raw_derived_separation']) and any('Failures' in x for x in D['lineage_contract']['invariants']))
check('Actor projection excludes source outcomes and reference routes', 'source expected curves/outcomes' in D['agent_visible']['excluded'] and 'mandatory reference action sequence' in D['agent_visible']['excluded'])
check('Proposed robotics and logic remain nonmanual unmeasured applications', any(x['id'] == 'N_APPLICATIONS' and 'no fabricated measured hardware' in x['disposition'] for x in D['nonmanual_scope']['entries']))
check('No physical execution feasibility or runtime certification is claimed', all(D['RELEASE_BOUNDARY'][x] is False for x in ['physical_execution','feasibility_validated','source_complete','CAD_created','viewer_created','robot_runtime_implemented']))
check('Torsion has an explicit measured upstream dataset dependency', all('completed matched ELEMENT_RESPONSE attempt' in B[i]['upstream_measurement_dependency']['allowed_sources'] and 'partial' in B[i]['upstream_measurement_dependency']['missing_policy'] for i in ['TRI_TORSION','QUAD_TORSION']))
check('Every expanded condition requires physical state verification', all(x['condition_transition']['required_before_each_condition'] and x['condition_transition']['no_label_only_transition'] for x in B.values()))
check('Array angle changes have actual pin action and remount', all('ARRAY_PIN' in B[i]['condition_transition']['reuse_path']['operations'] and B[i]['condition_transition']['reuse_path']['remount'] for i in ['ARRAY_COMPRESSION','ARRAY_TENSION']))
check('Morphology changes have unloaded reconfiguration and support action', all(set(['RING_RECONFIG','RING_SUPPORT']) <= set(B[i]['condition_transition']['reuse_path']['operations']) and 'SAFE_RESET' in B[i]['condition_transition']['reuse_path']['precondition'] for i in ['MORPHOLOGY_I','MORPHOLOGY_II']))
controls = {x['id']: x for x in D['control_packages']['packages']}
check('Qualitative array control does not demand quantitative acquisition', 'ARRAY_TRANSFORMATION' not in controls['C_ARRAY']['applies_to'] and 'ARRAY_TRANSFORMATION' in controls['C_ARRAY_TRANSFORM']['applies_to'])
check('Assembly controls distinguish paper and sliding-facet objects', any(x['when'] == 'complete thick element' for x in controls['C_ASM']['conditional_checks']) and any(x['when'] == 'paper element/array' for x in controls['C_ASM']['conditional_checks']))
check('Reset and unload bind to the actual active specimen station', all('WS_TORSION' in O[i]['allowed_station_ids'] and 'do not move specimen' in O[i]['station_binding'] for i in ['SAFE_RESET','UNLOAD']))
check('Intrinsic crease classes cannot change through label-only ring reconfiguration', all('separately prepared matched specimen' in x['condition_transition']['class_change_policy'] and 'No implicit crease replacement' in x['condition_transition']['class_change_policy'] for x in B.values()))

result = {
    'scope': 'Independent finite static design-contract checks only; no physical, safety, feasibility, scientific, solver or runtime-loader validation.',
    'passed': sum(x['passed'] for x in checks), 'total': len(checks), 'checks': checks,
    'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.json') if p.name not in ['STATUS.json','VERIFICATION.json','EXPORT_ALLOWLIST.json']},
}
(ROOT / 'independent_review/contract_check_results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'passed':result['passed'],'total':result['total'],'failures':[x['check'] for x in checks if not x['passed']]},indent=2))
raise SystemExit(not all(x['passed'] for x in checks))
