#!/usr/bin/env python3
"""Independent, read-only source/recipe checks. No physical execution or simulation."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name):
    return json.loads((ROOT / name).read_text())


def run_checks():
    results = []
    def check(name, predicate, detail=''):
        try:
            result = bool(predicate())
        except Exception as exc:
            result = False
            detail = f'{type(exc).__name__}: {exc}'
        results.append({'name': name, 'passed': result, 'detail': detail})
    branches = load('branches.json')
    b = {x['id']: x for x in branches['branches']}
    materials = load('material_cards.json')
    families = {x['id']: x for x in materials['specimen_families']}
    m = {x['id']: x for x in materials['cards']}
    operations = load('operations.json')
    o = {x['id']: x for x in operations['operations']}
    stations = {x['id']: x for x in load('station_contracts.json')['stations']}
    unknowns = {x['id']: x for x in load('unknown_parameters.json')['parameters']}
    conflicts = {x['id']: x for x in load('source_conflicts.json')['conflicts']}
    evidence = {x['id'] for x in load('provenance.json')['evidence']}
    required_branches = {'TAIJI_PLUS','TAIJI_MINUS','STEEL_FRAME_CONTROL','MICRO_TAIJI_BUILD','MICRO_TAIJI_COMP','MICRO_TAIJI_ACT','STEEL_PLANET_COMP','STEEL_PLANET_TENSION','MACRO_PLANET_COMP','MACRO_PLANET_TENSION','MACRO_PLANET_ACT','MICRO_PLANET_COMP','MICRO_PLANET_TENSION','MICRO_PLANET_ACT','FINITE_SHEAR','SOFT_SHEAR','RUBBER_FRAME_CONTROL','IMPACT'}
    check('exact physical branch coverage', lambda: set(b) == required_branches)
    check('18 distinct physical branch identifiers', lambda: len(b) == len(branches['branches']) == 18)
    check('unique operation and station identifiers', lambda: len(o) == len(operations['operations']) and len(stations) == len(load('station_contracts.json')['stations']))
    check('whole-paper coverage agrees across declarations', lambda: set(branches['whole_paper_physical_branch_ids']) == required_branches == set(load('evaluator_reference.json')['whole_paper_requires']['physical_branch_ids']))
    expected_shapes = {
        'F_TAIJI_PLUS':[5,5], 'F_TAIJI_MINUS':[5,5], 'F_TAIJI_VIDEO1':[4,4],
        'F_MICRO_TAIJI_BUILD':[5,6], 'F_MICRO_TAIJI_COMP':[4,4], 'F_MICRO_TAIJI_ACT':[5,5],
        'F_STEEL_PLANET_COMP':[3,3], 'F_STEEL_PLANET_TENSION':[2,2],
        'F_MACRO_PLANET_COMP':[6,6], 'F_MACRO_PLANET_TENSION':[2,6], 'F_MACRO_PLANET_ACT':[6,6],
        'F_MICRO_PLANET_COMP':[3,4], 'F_MICRO_PLANET_TENSION':[2,3], 'F_MICRO_PLANET_ACT':[3,4],
        'F_FINITE_SHEAR':[3,3], 'F_SOFT_SHEAR':[4,4], 'F_IMPACT':[3,3]}
    for family, shape in expected_shapes.items():
        check('source specimen shape ' + family, lambda family=family,shape=shape: families[family]['array_shape'] == shape)
    check('illustrative macro family has no physical recipe', lambda: families['F_TAIJI_VIDEO1']['preparation_route_id'] is None and 'F_TAIJI_VIDEO1' not in {x['specimen_family_id'] for x in b.values()})
    check('distinct micro Taiji family IDs', lambda: len({b[x]['specimen_family_id'] for x in ['MICRO_TAIJI_BUILD','MICRO_TAIJI_COMP','MICRO_TAIJI_ACT']}) == 3)
    check('metal Taiji frames have explicit component-material lineage', lambda: all(families[x]['component_material_bindings'].get('front_and_back_frames') == 'M_STEEL_FRAME' for x in ['F_TAIJI_PLUS','F_TAIJI_MINUS','F_FINITE_SHEAR']))
    check('micro Taiji test and actuation capture shafts explicitly', lambda: all('MICRO_SHAFT_CAPTURE' in [step['op_id'] for step in branches['preparation_routes'][b[x]['preparation_route_id']]] for x in ['MICRO_TAIJI_COMP','MICRO_TAIJI_ACT']))
    check('5x6 micro Taiji build keeps separate preparation route', lambda: b['MICRO_TAIJI_BUILD']['preparation_route_id'] != b['MICRO_TAIJI_COMP']['preparation_route_id'])
    check('no invented physical specimen instances', lambda: all(x['actual_specimen_ids'] == [] and x['historical_identity_inferred'] is False for x in families.values()))
    check('no source-imputed repeats', lambda: all(x['repeat_count'] is None and x['independent_specimen_count'] is None for x in b.values()))
    check('impact and general macro material IDs differ', lambda: families['F_IMPACT']['material_card_id'] != families['F_MACRO_PLANET_COMP']['material_card_id'])
    check('source polymer moduli preserved', lambda: m['M_IMPACT_RESIN']['source_facts']['modulus_GPa_approx'] == 2.0 and m['M_MACRO_RESIN']['source_facts']['model_modulus_GPa'] == 2.5 and m['M_MICRO_RESIN']['source_facts']['modulus_GPa'] == 3.5)
    check('micro planetary contradictory radii preserved', lambda: m['M_MICRO_RESIN']['source_facts']['planetary']['sun_radius_mm_by_source'] == {'main':0.6,'si_table_1':1.2} and m['M_MICRO_RESIN']['source_facts']['planetary']['planet_radius_mm_si_table_1_unresolved'] == 0.06)
    check('all planetary branches retain module gate', lambda: all('U_PLANET_CAD' in b[x]['required_input_ids'] for x in required_branches if 'PLANET' in x or x == 'IMPACT'))
    check('micro planetary branches retain radius gate', lambda: all('U_MICRO_GEOM' in b[x]['required_input_ids'] for x in ['MICRO_PLANET_COMP','MICRO_PLANET_TENSION','MICRO_PLANET_ACT']))
    check('dimension conflicts remain unresolved', lambda: all(conflicts[x]['status'] == 'preserved_unresolved' for x in ['C_SUN','C_PLANET','C_MODULE']))
    check('no unknown input has an execution default', lambda: all(x['defaults'] is None and x['state'] == 'execution_gate_open' for x in unknowns.values()))
    check('family and material references resolve', lambda: all(x['specimen_family_id'] in families for x in b.values()) and all(x['material_card_id'] in m for x in families.values()))
    all_json = {p.name:json.loads(p.read_text()) for p in ROOT.glob('*.json')}
    def references_valid():
        bad = []
        def walk(value, trail):
            if isinstance(value, dict):
                for k,v in value.items():
                    pool = evidence if k == 'source_evidence_ids' else set(unknowns) if k in {'unknown_input_ids','required_input_ids','gate_ids'} else None
                    if pool is not None and isinstance(v,list):
                        bad.extend((trail+'.'+k,x) for x in v if x not in pool)
                    walk(v,trail+'.'+k)
            elif isinstance(value,list):
                for i,v in enumerate(value): walk(v,f'{trail}[{i}]')
        for k,v in all_json.items(): walk(v,k)
        if bad: raise AssertionError(bad)
        return True
    check('source and unknown-gate references resolve recursively', references_valid)
    check('operation station references resolve', lambda: all(x['station_id'] in stations for x in o.values()))
    routes = branches['preparation_routes']
    check('branch preparation references resolve', lambda: all(x['preparation_route_id'] in routes for x in b.values()))
    check('recipe operation references resolve', lambda: all(x['op_id'] in o for route in list(routes.values())+[x['per_condition_operations'] for x in b.values()] for x in route))
    check('every physical branch has preparation and terminal cleanup', lambda: all(routes[x['preparation_route_id']] and {'CLEAN','STORE'} <= {v['op_id'] for v in x['per_condition_operations']} for x in b.values()))
    common_mechanical = ['FIXTURE_SELECT','CALIBRATE','MOUNT_QC','ZERO','ACQ_ARM','LOAD_CYCLE','IMAGE','ACQ_CLOSE','UNLOAD','RELEASE_FIXTURE','POST_INSPECT','CLEAN','STORE']
    for name, branch in b.items():
        seq = [x['op_id'] for x in branch['per_condition_operations']]
        if branch['mode'] in {'compression','tension','finite_shear','diagonal_shear'}:
            check('ordered test lifecycle '+name, lambda seq=seq: all(x in seq for x in common_mechanical) and [seq.index(x) for x in common_mechanical] == sorted(seq.index(x) for x in common_mechanical))
            fixture_op = {'compression':'COMP_SEAT','tension':'TENSION_CLAMP','finite_shear':'SHEAR_PIN','diagonal_shear':'SOFT_GROOVE'}[branch['mode']]
            check('correct fixture '+name, lambda seq=seq,fixture_op=fixture_op: fixture_op in seq and seq.index(fixture_op) < seq.index('MOUNT_QC'))
        if branch['mode'] == 'actuation':
            required = ['MOTOR_MOUNT','MOTOR_CONNECT','MOTOR_HOME','ACT_ACQ_ARM','MOTOR_RUN','MOTOR_STOP','ACT_ACQ_CLOSE','ACT_RELEASE','POST_INSPECT','ANALYZE_ACT','CLEAN','STORE']
            check('ordered motor lifecycle '+name, lambda seq=seq,required=required: all(x in seq for x in required) and [seq.index(x) for x in required] == sorted(seq.index(x) for x in required))
    check('micro Taiji box precedes baseplate release', lambda: [x['op_id'] for x in routes['PREP_MICRO_TAIJI']].index('MICRO_BOX') < [x['op_id'] for x in routes['PREP_MICRO_TAIJI']].index('BASEPLATE_RELEASE'))
    check('macro planetary support removal explicit', lambda: 'SUPPORT_CLEAR' in [x['op_id'] for x in routes['PREP_MACRO_PLANET']])
    impact_seq = [x['op_id'] for x in b['IMPACT']['per_condition_operations']]
    check('ordered guarded impact lifecycle', lambda: [impact_seq.index(x) for x in ['IMPACT_LOAD','IMPACT_GUARD','IMPACT_RUN','IMPACT_SAFE','IMPACT_UNLOAD']] == sorted(impact_seq.index(x) for x in ['IMPACT_LOAD','IMPACT_GUARD','IMPACT_RUN','IMPACT_SAFE','IMPACT_UNLOAD']))
    check('impact guard/run/safe/unload belong to qualified service', lambda: all(o[x]['actor'] == 'qualified_service' for x in ['IMPACT_GUARD','IMPACT_RUN','IMPACT_SAFE','IMPACT_UNLOAD']))
    def location_routes_valid():
        failures = []
        for bid, branch in b.items():
            location = 'WS_STOCK'
            for step in routes[branch['preparation_route_id']] + branch['per_condition_operations']:
                op = o[step['op_id']]
                if op['id'] == 'TRANSFER':
                    destination = step.get('destination_station')
                    if destination not in stations or not stations[destination]['physical_location']:
                        failures.append((bid,'invalid destination',destination))
                    location = destination
                elif stations[op['station_id']]['physical_location'] and op['station_id'] != location:
                    failures.append((bid,op['id'],location,op['station_id']))
        if failures: raise AssertionError(failures)
        return True
    check('all physical recipe transitions explicit; logical observation does not teleport', location_routes_valid)
    ev = load('evaluator_reference.json')
    check('fit-window error bars not specimen SD', lambda: 'variation across fitted strain intervals' in ev['error_bar_semantics'] and ev['first_cycle_in_modulus_fit'] is False)
    check('literature outcomes excluded from score gates', lambda: ev['reference_outcomes_are_scoring_gates'] is False)
    check('finite shear quantity distinctly labeled', lambda: ev['finite_shear_quantity'] == 'generalized_finite_shear_stiffness_G_prime')
    check('measured damping mandatory whole-paper analysis', lambda: 'DAMPING_ANALYSIS' in ev['whole_paper_requires']['analysis_ids'] and any(x['id']=='DAMPING_ANALYSIS' and x['mandatory_for_whole_paper'] is True for x in load('dependencies.json')['analysis_dependencies']))
    access = load('source_access_audit.json')
    check('full-motion review not claimed', lambda: access['full_motion_videos_inspected'] is False)
    check('actor projection not claimed implemented', lambda: load('agent_visible.json')['loader_implemented'] is False)
    check('answer and evaluator files excluded from actor', lambda: {'source_outcomes.json','evaluator_reference.json','tests/','independent_review/'} <= set(load('agent_visible.json')['not_loaded_into_actor']))
    check('actor allow and deny fields do not conflict', lambda: not (set(load('agent_visible.json')['allowed_fields']) & set(load('agent_visible.json')['forbidden_fields'])))
    boundary = load('RELEASE_BOUNDARY.json')
    check('no execution, replication, runtime or publication claims', lambda: all(boundary[x] is False for x in ['physical_execution','feasibility_validated','scientific_replication','physics_simulation','numerical_reproduction','robot_runtime','publication_performed','source_bytes_exported']))
    check('no raw source binaries in authored package', lambda: not any(p.suffix.lower() in {'.pdf','.mp4','.png','.jpg','.jpeg','.xml'} for p in ROOT.rglob('*') if p.is_file()))
    return {'checker':'independent_review/check_static.py','scope':'Independent read-only source/recipe assertions; not a runtime or physics test','checks':results,'passed':sum(x['passed'] for x in results),'failed':sum(not x['passed'] for x in results),'total':len(results)}

if __name__ == '__main__':
    result=run_checks()
    print(json.dumps(result,indent=2))
    raise SystemExit(bool(result['failed']))
