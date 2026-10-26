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
    'lab_jacks': ('equipment:COOLER', 'height-adjustable support', ['lab_jack_white', 'lab_jack_black']),
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
    'BUILD_PAIR': dict(lab_jacks=['white_height_adjuster','black_height_adjuster']),
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


def build_record(scene, readiness, quantity_policy=None):
    assets = {a['id']: a for a in scene['assets']}
    assert len(assets) == len(scene['assets']), 'duplicate scene asset identity'
    branches = {b['id']: b for b in readiness['branches']}
    assert set(branches) == set(DEMANDS), 'all branches require an explicit quantity review'
    items = {r['resource_id']: r for r in readiness['requirements']
             if r['disposition'] != 'historical_embodiment_reference'}
    policy = quantity_policy if quantity_policy is not None else json.loads((HERE/'component_quantity_policy.json').read_text())
    component_ids = {c['id']: c for r in items.values() for c in r['components']}
    kinds = {r['component_id']: r for r in policy['requirements']}
    selections = {r['component_id']: r for r in policy['selected_quantities']}
    nonstock = {r['component_id']: r for r in policy['non_stock_requirements']}
    assert len(kinds) == len(policy['requirements']) and set(kinds) == set(component_ids), 'every component needs exactly one quantity classification'
    assert len(selections) == len(policy['selected_quantities']) and set(selections) <= set(kinds), 'duplicate or unknown quantity selection'
    assert len(nonstock) == len(policy['non_stock_requirements']) and set(nonstock) <= set(kinds), 'duplicate or unknown non-stock requirement'
    assert not set(selections).intersection(nonstock), 'non-stock requirement cannot supply inventory'
    assert policy['owner_acceptance'] is None and not policy['qualified'], 'quantity policy cannot grant acceptance'
    for identity, row in kinds.items():
        assert row['label'] == component_ids[identity]['label'], 'quantity classification label drift'
        assert row['quantity_applicable'] == (identity not in nonstock), 'non-stock requirement must remain separately accounted'
    for identity, row in nonstock.items():
        assert row['kind'] in {'output_state','configuration_state','frame_requirement','acceptance_condition'}
        assert row['kind'] == kinds[identity]['kind'] and row['subjects'] and not row['complete']
    for identity, row in selections.items():
        assert row['label'] == component_ids[identity]['label'] and row['quantity'] > 0 and row['unit'] and row['basis']
        assert row['basis_type'] == 'demo_selection_not_paper_reported' and row['remaining_requirements']
    for source in policy['source_artifacts']:
        assert sha(ROOT/source['path']) == source['sha256'], 'stale quantity policy source'
    kinematics = json.loads((ROOT/'assets/unitree_g1_inspire_v1/kinematics.json').read_text())
    hand_parts = {}
    for side in ['left','right']:
        links = {side+'_base_link'}
        while True:
            children = {j['id'] for j in kinematics['joints'] if j['parent'] in links}
            if children <= links: break
            links |= children
        hand_parts[side] = {n for n,link in kinematics['part_links'].items() if link in links}
        selected = selections['robot:INSPIRE_FTP_'+side.upper()+':component_1']['members']
        assert len(selected)==1 and selected[0]['asset_id']=='g1' and set(selected[0]['parts'])==hand_parts[side], 'hand assignment differs from source kinematic subtree'
    body = selections['robot:G1_29DOF:component_1']['members']
    assert len(body)==1 and body[0]['asset_id']=='g1' and set(body[0]['parts'])==set(kinematics['part_links'])-hand_parts['left']-hand_parts['right'], 'body and hands must partition source visual parts'
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
    cutplan=json.loads((HERE/'stock_cutplan.json').read_text())
    tool_stock=json.loads((HERE/'fastener_tool_staging.json').read_text())
    explicit_quantities=cutplan['component_allocations']+[dict(resource_id=t['resource_id'],component_label=t['component_label'],selected_required_stock_units=t['selected_required_units']) for t in tool_stock['items']]
    stock_allocations={}
    for allocation in explicit_quantities:
        resource=items[allocation['resource_id']]
        component=next(c for c in resource['components'] if c['label']==allocation['component_label']) if allocation['component_label'] else resource['components'][0]
        if not allocation['component_label']:assert len(resource['components'])==1
        stock_allocations[component['id']]=allocation
    assert not set(selections).intersection(set(component_pool) | set(stock_allocations)), 'quantity policy duplicates existing allocation authority'
    for requirement in items.values():
        for component in requirement['components']:
            pool = component_pool.get(component['id'])
            staged = component.get('staged_candidates')
            selection = selections.get(component['id'])
            classification = kinds[component['id']]
            nonstock_requirement = nonstock.get(component['id'])
            if selection is not None and 'members' in selection:
                assert staged is None, 'explicit members cannot silently replace prior staged evidence'
                for member in selection['members']:
                    if member['asset_id'] in assets:
                        a = assets[member['asset_id']]
                        assert requirement['resource_id'] in a.get('resource_ids',[a['resource_id']]), 'explicit candidate has wrong resource type'
                staged = dict(unit=selection['unit'], quantity=len(selection['members']),
                    members=selection['members'], scope=selection['basis']) if selection['members'] else None
            if pool:
                evidence = dict(unit='instrument_or_probe', quantity=pool['staged_units'],
                                members=[dict(asset_id=m) for m in pool['staged_unit_ids']])
            elif staged:
                evidence = {k: staged[k] for k in ['unit', 'quantity', 'members', 'scope']}
                accounted=set()
                for member in staged['members']:
                    assert member['asset_id'] not in DISPLAY_ONLY, 'display reference cannot supply component stock'
                    assert len(member.get('parts',[])) == len(set(member.get('parts',[]))), 'duplicate named part within staged unit'
                    identifiers={(member['asset_id'],n) for n in member.get('parts',[])}
                    assert identifiers and not accounted.intersection(identifiers),'duplicate staged physical part'
                    accounted.update(identifiers)
                # Bind stock to the current placed instances and actual named
                # parts, even when a proposed inventory still lists a removed unit.
                present=lambda m:m['asset_id'] in assets and set(m.get('parts',[]))<=set(assets[m['asset_id']]['part_names'])
                evidence['missing_members']=[m for m in staged['members'] if not present(m)]
                evidence['members']=[m for m in staged['members'] if present(m)]
                evidence['quantity']=len(evidence['members'])
            else:
                evidence = None
            stock_quantity=stock_allocations.get(component['id'],{}).get('selected_required_stock_units')
            required=pool['selected_required_units'] if pool else selection['quantity'] if selection else stock_quantity
            unit=selection['unit'] if selection else evidence['unit'] if evidence else None
            if selection and evidence:
                assert selection['unit'] == evidence['unit'], 'required and staged quantity units differ'
            if nonstock_requirement:
                assert required is None and evidence is None, 'output, frame or acceptance evidence cannot become initial stock'
            basis=(selection['basis'] if selection else pool['quantity_basis'] if pool else
                   'Explicit stock-cut or fastener-tool allocation; not a completed-state inventory.' if stock_quantity is not None else
                   nonstock_requirement['basis'] if nonstock_requirement else 'Quantity, specification and candidate completeness remain to be allocated.')
            rows.append(dict(id=component['id'], resource_id=requirement['resource_id'], label=component['label'],
                required_quantity=required,
                required_unit=unit, quantity_basis=basis,
                requirement_kind=classification['kind'], stock_quantity_applicable=classification['quantity_applicable'],
                quantity_status='not_stock_quantity' if nonstock_requirement else 'selected_unaccepted' if required is not None else 'unallocated',
                staged_candidates=evidence,
                quantity_deficit=pool['quantity_deficit'] if pool else max(0,required-(evidence['quantity'] if evidence else 0)) if required is not None else None,
                state_or_acceptance_requirement=nonstock_requirement,
                remaining_requirements=selection['remaining_requirements'] if selection else [
                    'Required state or acceptance evidence remains incomplete; no additional stock is created.' if nonstock_requirement else
                    'Quantity/specification allocation and complete candidate configuration remain open.' if required is None else
                    'Quantity selection does not establish initial-state, compatibility or operation acceptance.'],
                branch_ids=[b['id'] for b in branch_rows if requirement['resource_id'] in b['required_resource_ids']],
                complete=False, qualification=False))
    uses = {}
    for row in rows:
        for member in (row['staged_candidates'] or {}).get('members', []):
            uses.setdefault(member['asset_id'], set()).add(row['id'])
    return dict(schema_version=2, status='asset_allocation_draft',
        scope='One complete campaign; quantities are independent of skill/branch/campaign validation repetitions',
        visibility='author_and_reviewer_only_not_actor_input',
        source_artifacts=[dict(path=str(p.relative_to(ROOT)), sha256=sha(p)) for p in
            [HERE/'scene.json', HERE/'readiness.json', HERE/'pilot_contract.json', TASK/'resources.json',
             TASK/'branches.json', TASK/'material_cards.json', HERE/'stock_cutplan.json',HERE/'fastener_tool_staging.json',HERE/'component_quantity_policy.json',Path(__file__)]],
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
        physical_instances=physical, pools=pools, stock_allocation={'path':'assets/cooling_lab_v1/stock_cutplan.json','sha256':sha(HERE/'stock_cutplan.json')},components=rows, branches=branch_rows,
        shared_asset_references=[dict(asset_id=identity,component_ids=sorted(ids),adds_stock=False)
                                 for identity,ids in sorted(uses.items()) if len(ids)>1],
        remaining=[
            dict(id='raw_stock', label='原料下料与制造条件', detail='两台装置的主要板材、管材、保温层、薄膜和框架已有逐件数量与下料范围；框架加工工具、孔与螺纹工艺、公差、存放约束及表面处理仍未补全。范围能放进原料不等于已加工。'),
            dict(id='fixed_pair', label='两套固定构型换装件', detail='已为两条遮阳带和四层 LDPE 预留原料，白色恢复另留两层 nano-PE；完整固定支架、换装连接和重复运行复位库存仍缺。'),
            dict(id='optical_specimens', label='光学试样与标准件', detail='至少需覆盖白／黑发射体、铝反射体、nano-PE 与 LDPE 五类材料；不同夹持口径是否可复用同一试片尚未证明，实际片数和尺寸未分配。'),
            dict(id='services', label='设备配套与连接', detail='记录器并不等于完整气象站；水刀、涂覆、湿区、光学安装、电源／数据和传感器线缆仍须逐项补全。'),
            dict(id='consumption', label='单次用量与重复运行复位', detail='薄膜、涂料、银浆、清洁材料、加工耗材及废物容量尚无完整用量预算；重试所需库存未计入。')],
        counts=dict(scene_instances=len(physical), reference_only_instances=sum(not p['initial_stock_credit'] for p in physical),
            component_requirements=len(rows), selected_quantity_components=sum(r['required_quantity'] is not None for r in rows),
            components_with_staged_bindings=sum(r['staged_candidates'] is not None for r in rows),
            quantified_pool_deficit=sum(p['quantity_deficit'] for p in pools),
            unallocated_component_quantities=sum(r['quantity_status']=='unallocated' for r in rows),
            non_stock_requirements=sum(r['quantity_status']=='not_stock_quantity' for r in rows),
            requirements_by_kind={kind:sum(r['requirement_kind']==kind for r in rows) for kind in sorted({r['requirement_kind'] for r in rows})},
            incomplete_component_requirements=sum(not r['complete'] for r in rows),
            qualified_branches=0, branches=len(branch_rows)))


def build():
    out = build_record(json.loads((HERE/'scene.json').read_text()), json.loads((HERE/'readiness.json').read_text()))
    write_json(HERE/'campaign_allocation.json', out)
    print(json.dumps(out['counts']))
    return out


if __name__ == '__main__':
    build()
