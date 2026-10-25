"""Reject shared-unit double counts and completed-display stock substitutions."""
import copy
import json
from build_campaign_allocation import build_record, POOLS
from geometry_tools import HERE, ROOT, sha, write_json


def inspect():
    scene = json.loads((HERE/'scene.json').read_text())
    readiness = json.loads((HERE/'readiness.json').read_text())
    report = json.loads((HERE/'campaign_allocation.json').read_text())
    checks = []
    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))
        if not passed: raise AssertionError(name)
    check('report_matches_current_inputs', report == build_record(scene, readiness))
    for s in report['source_artifacts']:
        check('current_source_'+s['path'], sha(ROOT/s['path']) == s['sha256'])
    for p in report['physical_instances']:
        check('physical_geometry_'+p['id'], sha(ROOT/p['geometry']['path']) == p['geometry']['sha256'])
    check('all_active_components_accounted', report['counts']['component_requirements'] == readiness['counts']['active_component_requirements'])
    check('all_branches_accounted', {b['id'] for b in report['branches']} == {b['id'] for b in readiness['branches']})
    check('completed_meshes_not_initial_stock', all(not p['initial_stock_credit'] for p in report['physical_instances'] if p['id'].startswith('cooler_')))
    check('pair_not_three_independent_apparatus', len(report['apparatus']) == 2 and report['selected_policy']['initial_completed_apparatus_count'] == 0)
    check('unallocated_quantities_remain_unknown', all(c['required_quantity'] is None for c in report['components'] if c['quantity_status'] == 'unallocated'))
    check('no_qualification_from_inventory', all(not b['qualified'] and not b['allocation_complete'] for b in report['branches']))
    branches = {b['id']: b for b in report['branches']}
    jacks=next(a for a in branches['BUILD_PAIR']['allocations'] if a['pool_id']=='lab_jacks')['roles']
    check('pair_uses_two_distinct_initial_jacks',{r['physical_id'] for r in jacks}=={'lab_jack_white','lab_jack_black'})
    fasteners=next(c for c in report['components'] if c['label']=='height-adjuster mount fasteners')
    check('twenty_four_mount_fasteners_allocated',fasteners['required_quantity']==24 and fasteners['staged_candidates']['quantity']==24 and fasteners['quantity_deficit']==0)
    for label in ['2 mm straight hex driver','2.5 mm straight hex driver','3 mm straight hex driver','8 mm open and box wrench']:
        row=next(c for c in report['components'] if c['label']==label)
        check('one_reusable_tool_'+label,row['required_quantity']==row['staged_candidates']['quantity']==1 and row['quantity_deficit']==0)
    missing_tool=copy.deepcopy(scene);missing_tool['assets']=[a for a in missing_tool['assets'] if a['id']!='hex_driver_2_5']
    row=next(c for c in build_record(missing_tool,readiness)['components'] if c['label']=='2.5 mm straight hex driver')
    check('negative_missing_driver_not_replaced_by_another_size',row['quantity_deficit']==1 and row['staged_candidates']['quantity']==0)
    for label,quantity in [('frame extrusion stock',4),('upright tube stock',4),('frame fasteners',84),('aluminum sheet stock',7),('aluminum angle stock',1),('shield attachment hardware',18),('film attachment adhesive stock',12)]:
        row=next(c for c in report['components'] if c['label']==label)
        check('actual_frame_stock_quantity_'+label,row['required_quantity']==quantity and row['staged_candidates']['quantity']==quantity and row['quantity_deficit']==0)
    missing=copy.deepcopy(scene);asset=next(a for a in missing['assets'] if a['id']=='cover_adhesive_stock')
    asset['part_names'].remove('raw_liner_12')
    row=next(c for c in build_record(missing,readiness)['components'] if c['label']=='film attachment adhesive stock')
    check('negative_missing_liner_invalidates_stock_unit',row['quantity_deficit']==1 and row['staged_candidates']['quantity']==11)
    missing=copy.deepcopy(scene);asset=next(a for a in missing['assets'] if a['id']=='frame_mount_hardware')
    asset['part_names'].remove('white_frame_bridge_left_1_tnut')
    row=next(c for c in build_record(missing,readiness)['components'] if c['label']=='frame fasteners')
    check('negative_one_missing_frame_nut_exposes_one_unit_deficit',row['quantity_deficit']==1 and row['staged_candidates']['quantity']==83)
    duplicate=copy.deepcopy(readiness)
    c=next(c for r in duplicate['requirements'] for c in r['components'] if c['label']=='frame fasteners')
    c['staged_candidates']['members'].append(copy.deepcopy(c['staged_candidates']['members'][0]))
    try:build_record(scene,duplicate)
    except AssertionError as e:check('negative_duplicate_frame_part_rejected','duplicate staged physical part' in str(e))
    else:check('negative_duplicate_frame_part_rejected',False)
    pid = {p['pool_id']: p for p in branches['PID_POWER']['allocations']}
    check('simultaneous_heaters_have_distinct_physical_instances', {r['physical_id'] for r in pid['heater']['roles']} == {'heater', 'heater_white'})
    check('simultaneous_sources_have_distinct_physical_instances', {r['physical_id'] for r in pid['smu']['roles']} == {'smu_white', 'smu_black'})
    check('fixed_pair_reuses_identified_outputs', branches['FIXED_LDPE']['apparatus_ids'] == branches['BUILD_PAIR']['apparatus_ids'])
    for b in ['MAP_CLEAR_DAY', 'MAP_CLEAR_NIGHT', 'MAP_HAZY_NOON']:
        probes = next(a for a in branches[b]['allocations'] if a['pool_id'] == 'probes')['roles']
        check('seven_unique_map_probes_'+b, len({p['physical_id'] for p in probes}) == 7 and probes[0]['physical_id'] == 'tc_01')
    # Recreate the real previous one-heater shortage: the report must expose it,
    # never create a second copy by assigning the same mesh instance twice.
    missing = copy.deepcopy(scene)
    missing['assets'] = [a for a in missing['assets'] if a['id'] != 'heater_white']
    deficit = build_record(missing, readiness)
    pool = next(p for p in deficit['pools'] if p['id'] == 'heater')
    check('negative_missing_second_heater_exposes_deficit', pool['quantity_deficit'] == 1 and pool['missing_unit_ids'] == ['heater_white'])
    failed_pid = next(b for b in deficit['branches'] if b['id'] == 'PID_POWER')
    roles = next(a for a in failed_pid['allocations'] if a['pool_id'] == 'heater')['roles']
    check('negative_missing_white_does_not_reassign_black', roles[0]['physical_id'] is None and roles[1]['physical_id'] == 'heater')
    missing_stock=copy.deepcopy(scene)
    missing_stock['assets']=[a for a in missing_stock['assets'] if a['id']!='acrylic_stock']
    absent=next(c for c in build_record(missing_stock,readiness)['components'] if c['resource_id']=='consumables:consumable_10')
    check('negative_removed_acrylic_exposes_two_plate_deficit',absent['quantity_deficit']==2 and absent['staged_candidates']['quantity']==0)
    missing_sheet=copy.deepcopy(scene)
    next(a for a in missing_sheet['assets'] if a['id']=='ldpe_stock')['part_names'].remove('raw_film_6')
    absent=next(c for c in build_record(missing_sheet,readiness)['components'] if c['resource_id']=='consumables:consumable_06')
    check('negative_removed_ldpe_sheet_exposes_deficit',absent['quantity_deficit']==1 and absent['staged_candidates']['quantity']==5)
    missing_jack=copy.deepcopy(scene);missing_jack['assets']=[a for a in missing_jack['assets'] if a['id']!='lab_jack_black']
    absent=next(p for p in build_record(missing_jack,readiness)['pools'] if p['id']=='lab_jacks')
    check('negative_missing_black_jack_exposes_deficit',absent['quantity_deficit']==1 and absent['missing_unit_ids']==['lab_jack_black'])
    missing_fastener=copy.deepcopy(scene);a=next(a for a in missing_fastener['assets'] if a['id']=='lift_mount_hardware');a['part_names'].pop()
    absent=next(c for c in build_record(missing_fastener,readiness)['components'] if c['label']=='height-adjuster mount fasteners')
    check('negative_missing_mount_fastener_exposes_deficit',absent['quantity_deficit']==1 and absent['staged_candidates']['quantity']==23)
    original = POOLS['heater']
    for name, units in [('duplicate_unit', ['heater', 'heater']), ('completed_stock', ['cooler_white', 'heater']), ('cross_pool_reuse', ['smu_white', 'heater']), ('wrong_resource_type', ['caliper', 'heater'])]:
        rejected = False
        try:
            POOLS['heater'] = (original[0], original[1], units)
            build_record(scene, readiness)
        except AssertionError:
            rejected = True
        finally:
            POOLS['heater'] = original
        check('negative_'+name+'_rejected', rejected)
    result = dict(schema_version=1, passed=all(c['passed'] for c in checks), checks=checks,
                  negative_cases=13, scope='Inventory identities and selected quantities only; no task or stock sufficiency acceptance',
                  source_artifacts=[dict(path=str(p.relative_to(ROOT)), sha256=sha(p)) for p in
                      [HERE/'campaign_allocation.json', HERE/'check_allocation.py']])
    write_json(HERE/'allocation_checks.json', result)
    print(json.dumps(dict(passed=result['passed'], checks=len(checks), negative_cases=result['negative_cases'])))
    return result


if __name__ == '__main__': inspect()
