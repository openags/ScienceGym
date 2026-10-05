"""Independent adversarial probes for a static, non-actuating scene adapter.
Run with Python from this directory; writes independent_guard_probe_results.json.
No device, network, controller, solver, or source-artifact access occurs.
"""
import copy
import hashlib
import json
from pathlib import Path
from scene_guards import evaluate

ROOT = Path(__file__).resolve().parent
BASE = {
    'physical_execution_enabled': False,
    'operation_id': 'R03',
    'anchor_id': 'AS02.M1.carrier_acceptance',
    'action': 'set_synthetic_visual_state',
    'evidence_kind': 'synthetic_fixture',
    'claims_real_observation': False,
    'branch_id': 'B01',
    'science_type': 'experimental_source_review',
    'coordinate_mapping_status': 'explicit_synthetic_test_mapping',
    'family_id': 'GROOVE_M1',
    'supported': True,
    'custody_holder': 'SYNTHETIC_HOLDER',
    'occupancy': 'known_synthetic',
    'retained_lease': 'SYNTHETIC_LEASE',
    'configuration_epoch': 'SYNTHETIC_E1',
    'calibration_configuration_epoch': 'SYNTHETIC_E1',
    'observed_safe_fixture': {
        'acoustic_off': True, 'beam_safe': True,
        'motion_safe': True, 'support_safe': True,
    },
}
HOLD = 'HOLD_QUALIFICATION'
SYNTHETIC = 'SYNTHETIC_VISUAL_STATE_ONLY'
STATIC = 'STATIC_REVIEW_ONLY'
results = []

def check(name, request, expected):
    try:
        output = evaluate(request)
        invariants = (output.get('physical_execution_enabled') is False
                      and output.get('hardware_commands') == []
                      and output.get('scientific_physics_implemented') is False)
        passed = output.get('status') == expected and invariants
        results.append({'test': name, 'expected_status': expected,
                        'actual_status': output.get('status'),
                        'reason': output.get('reason'), 'passed': passed,
                        'nonexecution_invariants': invariants})
    except Exception as exc:
        results.append({'test': name, 'passed': False,
                        'exception_type': type(exc).__name__})

def mutate(name, changes=None, remove=(), expected=HOLD):
    request = copy.deepcopy(BASE)
    request.update(changes or {})
    for key in remove:
        request.pop(key, None)
    check(name, request, expected)

mutate('missing_branch', remove=['branch_id'])
mutate('missing_science_type', remove=['science_type'])
for value, name in [('Z99', 'unknown_branch'), ('B99', 'unknown_B_branch'),
                    ('', 'empty_branch'), (None, 'null_branch'),
                    ([], 'list_branch')]:
    mutate(name, {'branch_id': value})
mutate('unknown_A_branch', {'branch_id': 'A99', 'science_type': 'numerical_source_review'})
for name, changes in [
    ('list_operation', {'operation_id': []}),
    ('dict_anchor', {'anchor_id': {}}),
    ('numeric_custody_holder', {'custody_holder': 0}),
    ('empty_custody_holder', {'custody_holder': ''}),
    ('numeric_retained_lease', {'retained_lease': 1}),
    ('boolean_configuration_epoch', {'configuration_epoch': True, 'calibration_configuration_epoch': True}),
    ('list_configuration_epoch', {'configuration_epoch': ['E1'], 'calibration_configuration_epoch': ['E1']}),
    ('branch_family_mismatch_B04_M1', {'branch_id': 'B04', 'family_id': 'GROOVE_M1'}),
    ('numerical_branch_specimen_acceptance', {'branch_id': 'A01', 'science_type': 'numerical_source_review'}),
    ('numerical_R14_return_target', {'operation_id': 'R14', 'anchor_id': 'AS10.return_acceptance', 'branch_id': 'A01', 'science_type': 'numerical_source_review'}),
    ('preparation_branch_numerical_R11', {'operation_id': 'R11', 'anchor_id': 'AS11.analysis_record', 'branch_id': 'P01', 'science_type': 'preparation_source_review'}),
    ('experimental_branch_numerical_R11', {'operation_id': 'R11', 'anchor_id': 'AS11.analysis_record'}),
    ('contradictory_force_output_alias', {'scientific_physics_implemented': True, 'force_N': 1.0}),
    ('contradictory_hardware_commands', {'hardware_commands': ['move_robot']}),
    ('extra_real_evidence_claim', {'real_observation': True}),
]:
    mutate(name, changes)
mutate('valid_A01_numerical_R11', {'operation_id': 'R11', 'anchor_id': 'AS11.analysis_record', 'branch_id': 'A01', 'science_type': 'numerical_source_review'}, expected=SYNTHETIC)
for value, name in [(None, 'null'), (False, 'false'), (0, 'zero'), (1, 'one'),
                    ('request', 'string'), ([], 'list'), ({}, 'empty_dict')]:
    check('malformed_top_level_' + name, value, HOLD)
adversarial_results = list(results)
contract = json.loads((ROOT / 'asset_binding_contract.json').read_text())
bindings = {x['operation_id']: set(x['anchor_ids']) for x in contract['operation_bindings']}
anchors = {a for group in contract['asset_groups'] for a in group['anchor_ids']}
for operation, permitted in bindings.items():
    for anchor in sorted(anchors):
        check('binding_' + operation + '_' + anchor,
              {'physical_execution_enabled': False, 'operation_id': operation,
               'anchor_id': anchor, 'action': 'inspect_anchor'},
              STATIC if anchor in permitted else HOLD)
fuzz = []
for key in BASE:
    for value in [None, True, False, 0, 1, '', [], {}, [1], {'x': 1}]:
        request = copy.deepcopy(BASE)
        request[key] = value
        try:
            output = evaluate(request)
            passed = (output.get('physical_execution_enabled') is False
                      and output.get('hardware_commands') == []
                      and output.get('scientific_physics_implemented') is False)
            fuzz.append({'field': key, 'input_type': type(value).__name__, 'passed': passed})
        except Exception as exc:
            fuzz.append({'field': key, 'input_type': type(value).__name__,
                         'passed': False, 'exception_type': type(exc).__name__})
summary = {
    'status': 'PASS' if all(x['passed'] for x in results + fuzz) else 'FAIL',
    'guard_sha256': hashlib.sha256((ROOT / 'scene_guards.py').read_bytes()).hexdigest(),
    'independent_assertions': len(results),
    'independent_assertions_passed': sum(x['passed'] for x in results),
    'adversarial_cases': adversarial_results,
    'binding_matrix': {'operations': len(bindings), 'anchors': len(anchors),
                       'cases': len(bindings) * len(anchors),
                       'failed': [x for x in results[len(adversarial_results):] if not x['passed']]},
    'field_type_fuzz': {'cases': len(fuzz), 'passed': sum(x['passed'] for x in fuzz),
                        'failed': [x for x in fuzz if not x['passed']]},
    'hardware_commands_emitted': 0,
    'physical_execution_enabled': False,
    'scientific_physics_implemented': False,
}
(ROOT / 'independent_guard_probe_results.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({k: summary[k] for k in ['status', 'independent_assertions', 'independent_assertions_passed', 'binding_matrix', 'field_type_fuzz']}))
assert summary['status'] == 'PASS'
