"""Independent finite design checks, not a robot executor or scientific validator."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = {p.stem: json.loads(p.read_text()) for p in ROOT.glob('*.json')}
O = {x['id']: x for x in D['operations']['operations']}
B = {x['id']: x for x in D['branches']['configurations']}
R = {x['configuration_id']: x for x in D['dependencies']['routes']}
S = {x['id'] for x in D['station_contracts']['stations']}
U = {x['id'] for x in D['unknown_parameters']['unknowns']}
P = {x['id'] for x in D['provenance']['references']}
K = {x['id']: x for x in D['control_packages']['controls']}
V = {x['id']: x for x in D['source_parameters']['parameters']}
checks = []

def check(name, result):
    checks.append({'check': name, 'passed': bool(result)})

def reach(edges, start, end):
    seen = {start}
    todo = [start]
    while todo:
        x = todo.pop()
        for a, b in edges:
            if a == x and b not in seen:
                seen.add(b)
                todo.append(b)
    return end in seen

def dag(nodes, edges):
    incoming = {n: 0 for n in nodes}
    adjacent = {n: [] for n in nodes}
    for a, b in edges:
        if a not in incoming or b not in incoming:
            return False
        incoming[b] += 1
        adjacent[a].append(b)
    todo = [n for n, count in incoming.items() if count == 0]
    visited = 0
    while todo:
        n = todo.pop()
        visited += 1
        for nxt in adjacent[n]:
            incoming[nxt] -= 1
            if incoming[nxt] == 0:
                todo.append(nxt)
    return visited == len(nodes)

check('Every operation resolves a station', all(x['station'] in S for x in O.values()))
check('Every operation resolves source references', all(set(x['source_refs']) <= P for x in O.values()))
check('Every operation resolves input gates', all(set(x['required_unknowns']) <= U for x in O.values()))
check('Every branch resolves operations controls sources and gates', all(set(x['operation_ids']) <= O.keys() and set(x['required_controls']) <= K.keys() and set(x['source_refs']) <= P and set(x['required_unknowns']) <= U for x in B.values()))
check('Branch gates include all selected operation gates', all(set().union(*(set(O[i]['required_unknowns']) for i in x['operation_ids'])) <= set(x['required_unknowns']) for x in B.values()))
check('Each branch has exactly one matching route', set(B) == set(R) and len(D['dependencies']['routes']) == len(B))
check('All one-pass route graphs are acyclic with local references', all(dag(x['suggested_operation_ids'], x['causal_edges']) for x in R.values()))
check('Finite loop references are local operations', all(set(y['repeat_operation_ids']) <= set(x['suggested_operation_ids']) for x in R.values() for y in x['loop_contracts']))
fields = ['actor', 'source_station', 'target_station', 'manipulated_objects_and_tools', 'robot_actions', 'preconditions', 'completion_state', 'completion_evidence', 'failure_handling']
check('Operations expose actor manipulation state custody and evidence', all(all(x.get(k) for k in fields) for x in O.values()))
check('Robot translations and device actions are distinguished', all(x['provenance_class'] == 'authored_robot_translation' and isinstance(x['device_actions'], list) for x in O.values()))
check('Part manufacture contains actual load recover finish inspect actions', all(len(O[i]['robot_actions']) >= 4 for i in ['CUT_RODS', 'PMMA_FAB', 'NYLON_FAB']))
check('Packing proceeds from qualified shape and fabricated inspected parts', all(reach(R['TEMP_PHI']['causal_edges'], a, 'PACK_CLOSE') for a in ['SHAPE_VERIFY', 'PMMA_FAB', 'NYLON_FAB', 'ALLOCATE_CHARGE']))
check('Stick insertion precedes thermal actuation', reach(R['TEMP_PHI']['causal_edges'], 'INSERT_STICK', 'HEAT_LOAD'))
check('Thermal qualification precedes mechanical acquisition', reach(R['TEMP_PHI']['causal_edges'], 'HEAT_WAIT', 'PULL_RUN'))
check('Mechanical cycle recovers cools then reinserts before next pass', all(reach(R['CYCLE_PULL']['causal_edges'], a, b) for a, b in [('PULL_RUN','PULL_UNLOAD'),('PULL_UNLOAD','COOL_RESET'),('COOL_RESET','REINSERT')]) and bool(R['CYCLE_PULL']['loop_contracts']))
check('XCT does not silently inherit unconditional mechanical reinsertion control', 'C_CYCLE' not in B['XCT_CYCLES']['required_controls'] or 'if' in K['C_CYCLE']['requirement'].lower() or 'conditional' in K['C_CYCLE']['requirement'].lower())
check('XCT raw acquisition precedes geometry derivation', reach(R['XCT_STATES']['causal_edges'], 'XCT_ACQUIRE', 'XCT_ANALYZE'))
check('XCT scan versus pull sequence ambiguity remains explicit', 'unresolved' in json.dumps(D['source_conflicts']).lower() or 'not specified' in json.dumps(D['source_conflicts']).lower())
check('Hold preparation observation and contained release remain ordered', all(reach(R['EXTENDED_HOLD']['causal_edges'], a, b) for a, b in [('HOLD_PREP','HOLD_OBSERVE'),('HOLD_OBSERVE','HOLD_RELEASE')]))
check('Continuous extended hold is distinct from repeated pull cycles', 'PULL_RUN' not in B['EXTENDED_HOLD']['operation_ids'] and '15' in B['EXTENDED_HOLD']['condition_contract']['duration_rule'])
check('DSC and friction preparation precede actual acquisition', reach(R['MATERIAL_DSC']['causal_edges'],'DSC_PREP','DSC_RUN') and reach(R['FRICTION_PAIRS']['causal_edges'],'FRICTION_PREP','FRICTION_RUN'))
check('Single-rod load and unload history precedes thermal recovery', reach(R['SINGLE_ROD_BEND']['causal_edges'],'BEND_PREP','BEND_RECOVER'))
check('Aspect ratio and baseline fixture dimensions are distinct', V['P_BASE_INNER']['value'] == 32 and V['P_BASE_STICK']['value'] == 14 and V['P_AR_FIXTURE']['value'] == [42,32])
check('All reported container sizes retained including unresolved largest', V['P_SIZE_DINS']['value'] == [42,46,50,55,59,67,76,84])
check('Outside versus inside conflict remains explicit and gated', any(x['id'] == 'CONTAINER_OUTER' and x['gate'] == 'U_GEOMETRY' for x in D['source_conflicts']['conflicts']))
check('XCT designation is not emitted as a qualified scan recipe', 'Not evidence of actual scan voltage' in V['P_XCT_RATING']['qualification_note'] and 'U_XCT' in O['XCT_ACQUIRE']['required_unknowns'])
check('Unspecified rod reference programming remains an input gate', 'U_PROGRAM' in O['SHAPE_VERIFY']['required_unknowns'])
check('DEM packing count is not an experimental replicate claim', V['P_DEM_REPEATS']['value'] == 5 and 'Not a count of physical' in V['P_DEM_REPEATS']['qualification_note'])
check('Temperature tolerance is strict and acquisition-linked', V['P_TEMP_LIMIT']['value'] == 2 and 'strictly less than 2' in V['P_TEMP_LIMIT']['qualification_note'] and 'throughout' in ' '.join(O['PULL_RUN']['robot_actions']))
check('Distinct fixed-rod and fixed-total composition comparisons preserved', V['P_BALL_FIXED_ROD']['value'] == 0.18 and V['P_BALL_FIXED_TOTAL']['value'] == 0.28 and B['BALL_FIXED_RODS']['required_controls'] != B['BALL_FIXED_TOTAL']['required_controls'])
check('Lineage distinguishes repacking and protects source-independent raw data', 'new packing_id' in json.dumps(D['lineage_contract']) and 'source outcome files cannot be raw parents' in json.dumps(D['lineage_contract']))
check('Actor excludes source outcomes and hidden reference route', 'source_outcomes.json' in D['agent_visible']['exclude'] and 'full reference route and answer' in D['agent_visible']['exclude'])
check('Source access incompleteness remains visible', D['source_access_audit']['source_completeness_claim'] is False and len(D['source_access_audit']['not_inspected']) >= 4)
check('Design review does not certify physical device or CAD execution', not D['RELEASE_BOUNDARY']['physical_execution'] and not D['RELEASE_BOUNDARY']['device_execution'] and not D['RELEASE_BOUNDARY']['cad_or_viewer_work'])

result = {
    'scope': 'Independent finite static design checks only; no physical execution, feasibility, safety qualification, source-result replication, solver or runtime-loader validation.',
    'passed': sum(x['passed'] for x in checks), 'total': len(checks), 'checks': checks,
    'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.json') if p.name not in ['STATUS.json', 'VERIFICATION.json', 'EXPORT_ALLOWLIST.json']},
}
(ROOT / 'independent_review/contract_check_results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'passed': result['passed'], 'total': result['total'], 'failures': [x['check'] for x in checks if not x['passed']]}, indent=2))
raise SystemExit(not all(x['passed'] for x in checks))
