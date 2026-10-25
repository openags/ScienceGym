"""Account for physical identities and selected quantities before robot planning.

One campaign is the allocation unit. These are author/reviewer requirements,
not an actor plan, validated initial state, stock sufficiency or task execution.
Completed-state display meshes cannot supply the BUILD_PAIR initial inventory.
"""
import json
from pathlib import Path
from geometry_tools import HERE, ROOT, sha, write_json

TASK = ROOT / 'tasks/directional_cooling_operations_v3'

# Explicit component-to-instance associations. A model's presence says nothing
# about calibration, services, contacts or the complete resource group.
POOLS = {
    'smu': ('equipment:SMU', None, ['smu_white', 'smu_black']),
    'heater': ('equipment:HEATER', None, ['heater_white', 'heater']),
    'daq': ('equipment:DAQ', None, ['daq']),
    'bath': ('equipment:BATH', None, ['bath']),
    'dmm': ('equipment:DMM', None, ['dmm']),
    'reference_rtd': ('equipment:REF_RTD', None, ['rtd']),
    'probes': ('equipment:TC', 'identified K probes', ['tc_'+str(i).zfill(2) for i in range(1, 9)]),
    'ambient_rtd': ('equipment:AMB_RTD', 'ambient probe', ['ambient_rtd']),
    'uvvis': ('equipment:UVVIS', None, ['cary']),
    'dra': ('accessory:DRA_2500', None, ['dra']),
    'ftir': ('equipment:FTIR', None, ['nicolet']),
    'integratir': ('accessory:INTEGRATIR', None, ['pike']),
    'tracker': ('equipment:SOLAR_TRACKER', None, ['tracker']),
    'dni': ('equipment:DNI', None, ['eko_ms56']),
    'gti': ('equipment:GTI', None, ['eko_ms402']),
    'weather_logger': ('equipment:WEATHER', 'U30 logger', ['hobo_u30']),
}

ENV = dict(ambient_rtd=['ambient'], tracker=['solar_tracking'], dni=['direct_solar'],
           gti=['global_solar'], weather_logger=['weather_log'])
PAIRED = dict(ENV, daq=['temperature_log'], probes=['white_emitter', 'black_emitter'])
MAPPING = dict(ENV, daq=['temperature_log'],
              probes=['white_emitter']+['map_'+str(i) for i in range(1, 7)])
DEMANDS = {
    'BUILD_PAIR': {},
    'CALIBRATE': dict(daq=['calibration_log'], bath=['calibration_bath'],
                      dmm=['reference_readout'], reference_rtd=['reference'],
                      probes=['calibration_probe_'+str(i) for i in range(1, 9)]),
    'OPT_HEMISPHERICAL': dict(uvvis=['shortwave'], dra=['shortwave_accessory'],
                             ftir=['infrared'], integratir=['infrared_accessory']),
    'OPT_ANGULAR': dict(ftir=['infrared']),
    'ENVIRONMENT': ENV,
    'TRACKED_STAGNATION': PAIRED,
    'PID_POWER': dict(PAIRED, smu=['white_heater_source', 'black_heater_source'],
                     heater=['white_emitter', 'black_emitter']),
    'FIXED_LDPE': PAIRED,
    'MAP_CLEAR_DAY': MAPPING,
    'MAP_CLEAR_NIGHT': MAPPING,
    'MAP_HAZY_NOON': MAPPING,
}
APPARATUS = {
    'BUILD_PAIR': ['white', 'black'], 'TRACKED_STAGNATION': ['white', 'black'],
    'PID_POWER': ['white', 'black'], 'FIXED_LDPE': ['white', 'black'],
    'MAP_CLEAR_DAY': ['white'], 'MAP_CLEAR_NIGHT': ['white'], 'MAP_HAZY_NOON': ['white'],
}
DISPLAY_ONLY = {
    'cooler_white': ('completed_state_reference', '白色完成态，用于核对装配结果；不是已经备好的初始装置'),
    'cooler_black': ('completed_state_reference', '黑色完成态，用于核对装配结果；不是已经备好的初始装置'),
    'cooler_fixed': ('alternate_state_reference', '固定遮阳带构型的展示模板；不是第三台可用装置，也不能替代两套实际换装件'),
    'camera_head': ('alternate_hardware_reference', '备选 D455 外形参考；本次选定头部相机是 G1 原生 D435i'),
}


def build_record(scene, readiness):
    assets = {a['id']: a for a in scene['assets']}
    assert len(assets) == len(scene['assets']), 'duplicate scene asset identity'
    branches = {b['id']: b for b in readiness['branches']}
    assert set(branches) == set(DEMANDS), 'all branches require an explicit quantity review'
    items = {r['resource_id']: r for r in readiness['requirements']
             if r['disposition'] != 'historical_embodiment_reference'}
    physical = []
    for a in scene['assets']:
        role, note = DISPLAY_ONLY.get(a['id'], ('staged_candidate', '已放置的候选实例；未验收配置、连接或物理行为'))
        physical.append(dict(id=a['id'], role=role, label=a['label'], note=note,
            initial_stock_credit=role == 'staged_candidate', initial_state_qualified=False,
            geometry=dict(path=a['geometry'], sha256=a['geometry_sha256']),
            station=a['station'], position_m=a['position_m']))
    pools = []
    component_pool = {}
    used_assets = set()
    for identity, (resource, label, members) in POOLS.items():
        assert len(members) == len(set(members)), 'duplicate unit in '+identity
        assert not used_assets.intersection(members), 'same unit double-counted in independent pools'
        used_assets.update(members)
        assert not set(members).intersection(DISPLAY_ONLY), 'display reference cannot supply initial stock'
        requirement = items[resource]
        component = next(c for c in requirement['components'] if c['label'] == label) if label else requirement['components'][0]
        if label is None: assert len(requirement['components']) == 1
        present = [m for m in members if m in assets]
        for member in present:
            a = assets[member]
            assert resource in a.get('resource_ids', [a['resource_id']]), 'wrong resource type for '+member
        peak = max(len(d.get(identity, [])) for d in DEMANDS.values())
        assert len(members) >= peak, 'insufficient proposed identities in '+identity
        record = dict(id=identity, resource_id=resource, component_id=component['id'],
                      selected_required_units=peak, proposed_unit_ids=members,
                      staged_unit_ids=present, staged_units=len(present),
                      missing_unit_ids=[m for m in members if m not in assets],
                      quantity_deficit=max(0, peak-len(present)),
                      quantity_basis='Selected shared inventory for one campaign; not the historical instrument count',
                      quantity_accepted=False, resource_complete=False)
        pools.append(record); component_pool[component['id']] = record
    by_pool = {p['id']: p for p in pools}
    branch_rows = []
    for identity, demands in DEMANDS.items():
        allocations = []
        for pool_id, roles in demands.items():
            p = by_pool[pool_id]
            assert len(roles) == len(set(roles)), 'duplicate simultaneous role'
            proposed = p['proposed_unit_ids'][:len(roles)]
            assigned = [unit if unit in assets else None for unit in proposed]
            allocations.append(dict(pool_id=pool_id, simultaneous_units=len(roles),
                roles=[dict(role=role, physical_id=assigned[i], proposed_physical_id=proposed[i])
                       for i, role in enumerate(roles)], missing_units=assigned.count(None)))
        related = [s for s in readiness['manual_step_requirements'] if s['step_id'] in branches[identity]['manual_step_ids']]
        resources = sorted({r for s in related for r in s['resource_requirements']+s['embodiment_requirements']})
        branch_rows.append(dict(id=identity, title=branches[identity]['title'],
            apparatus_ids=['apparatus_'+c for c in APPARATUS.get(identity, [])],
            allocations=allocations, required_resource_ids=resources,
            allocation_complete=False, qualified=False))
    rows = []
    for requirement in items.values():
        for component in requirement['components']:
            pool = component_pool.get(component['id'])
            staged = component.get('staged_candidates')
            if pool:
                evidence = dict(unit='instrument_or_probe', quantity=pool['staged_units'],
                                members=[dict(asset_id=m) for m in pool['staged_unit_ids']])
            elif staged:
                evidence = {k: staged[k] for k in ['unit', 'quantity', 'members', 'scope']}
            else:
                evidence = None
            rows.append(dict(id=component['id'], resource_id=requirement['resource_id'], label=component['label'],
                required_quantity=pool['selected_required_units'] if pool else None,
                quantity_status='selected_unaccepted' if pool else 'unallocated',
                staged_candidates=evidence,
                quantity_deficit=pool['quantity_deficit'] if pool else None,
                branch_ids=[b['id'] for b in branch_rows if requirement['resource_id'] in b['required_resource_ids']],
                complete=False, qualification=False))
    return dict(schema_version=1, status='asset_allocation_draft',
        scope='One complete campaign; quantities are independent of skill/branch/campaign validation repetitions',
        visibility='author_and_reviewer_only_not_actor_input',
        source_artifacts=[dict(path=str(p.relative_to(ROOT)), sha256=sha(p)) for p in
            [HERE/'scene.json', HERE/'readiness.json', HERE/'pilot_contract.json', TASK/'resources.json',
             TASK/'branches.json', TASK/'material_cards.json', Path(__file__)]],
        selected_policy=dict(apparatus_count=2, initial_completed_apparatus_count=0,
            configuration_reuse='Reuse the identified white/black pair for tracked and fixed branches; restore the same white apparatus before tracked mapping',
            historical_reuse_known=False, inferred_quantity_selection=True,
            environmental_resources='ENVIRONMENT is shared with outdoor sessions, not an extra simultaneous sensor set',
            probe_assignment='tc_01 white emitter; tc_02 black emitter in paired runs. In maps tc_01 stays white and tc_02..tc_07 are the six map probes; tc_08 is unassigned. Repositioning and recalibration requirements are not qualified',
            validation_repeats='A fresh reset/stock budget for repeated trials is still required; multiplying inventory by 20/10/3 is not justified',
            allocation_complete=False, owner_acceptance=None, new_manipulation_development_allowed=False),
        apparatus=[dict(id='apparatus_'+c, condition=c, output_review_asset='cooler_'+c,
                       initial_state='unbuilt_from_identified_raw_stock', required_output_quantity=1,
                       raw_stock_allocation_complete=False,
                       configurations=['tracked_nano_PE', 'fixed_LDPE'], configuration_geometry_complete=False)
                   for c in ['white', 'black']],
        physical_instances=physical, pools=pools, components=rows, branches=branch_rows,
        remaining=[
            dict(id='raw_stock', label='两台装置的原料切割分配', detail='铜、铝板／管、PE 支撑、泡沫、亚克力、紧固件与余料尚未逐件分配；完成态模型不能替代它们。'),
            dict(id='fixed_pair', label='两套固定遮阳带与换装薄膜', detail='仅有一个白色固定构型展示模板；两台装置所需的独立换装件和返修／恢复库存未落实。'),
            dict(id='optical_specimens', label='光学试样与标准件', detail='至少需覆盖白／黑发射体、铝反射体、nano-PE 与 LDPE 五类材料；不同夹持口径是否可复用同一试片尚未证明，实际片数和尺寸未分配。'),
            dict(id='services', label='设备配套与连接', detail='记录器并不等于完整气象站；水刀、涂覆、湿区、光学安装、电源／数据和传感器线缆仍须逐项补全。'),
            dict(id='consumption', label='单次用量与重复运行复位', detail='薄膜、涂料、银浆、清洁材料、加工耗材及废物容量尚无完整用量预算；重试所需库存未计入。')],
        counts=dict(scene_instances=len(physical), reference_only_instances=sum(not p['initial_stock_credit'] for p in physical),
            component_requirements=len(rows), selected_quantity_components=len(component_pool),
            components_with_staged_bindings=sum(r['staged_candidates'] is not None for r in rows),
            quantified_pool_deficit=sum(p['quantity_deficit'] for p in pools),
            unallocated_component_quantities=sum(r['required_quantity'] is None for r in rows),
            qualified_branches=0, branches=len(branch_rows)))


def build():
    out = build_record(json.loads((HERE/'scene.json').read_text()), json.loads((HERE/'readiness.json').read_text()))
    write_json(HERE/'campaign_allocation.json', out)
    print(json.dumps(out['counts']))
    return out


if __name__ == '__main__':
    build()
