"""Bind alternative weather representations to one laboratory inventory.

This downstream composition leaves source geometry and the base scene intact.
An installed reference cannot create initial stock or validate an assembly step.
"""
import json
from pathlib import Path
import numpy as np
from geometry_tools import HERE, ROOT, sha, write_json


def build():
    # Bind geometry and physical identities. Readiness and campaign quantities
    # are downstream review concerns, not inputs to this composition.
    names=['scene','weather_station_assets',
        'weather_storage_assets','weather_preparation_assets','outdoor_ground_assets',
        'weather_station_checks','weather_storage_checks','weather_preparation_checks',
        'outdoor_ground_checks','weather_service_checks','weather_wind_service_checks',
        'weather_remainders_assets','weather_remainders_checks',
        'nut_driver_assets','mast_driver_assets','wind_driver_assets',
        'nut_driver_checks','mast_driver_checks','wind_driver_checks',
        'wire_rope_cutter_assets','wire_rope_cutter_checks','adjustable_wrench_assets','adjustable_wrench_checks',
        'mast_grease_assets','mast_grease_checks','tape_measure_assets','tape_measure_checks',
        'engineer_hammer_assets','engineer_hammer_checks','silicone_grease_assets','silicone_grease_checks',
        'weather_cleanup_assets','weather_cleanup_checks']
    r={n:json.loads((HERE/(n+'.json')).read_text()) for n in names}
    station=r['weather_station_assets'];storage=r['weather_storage_assets']
    site=station['station_origin_world_m'];modules=[];entities={}
    def module(identity,label,geometry,translation):
        matrix=np.eye(4);matrix[:3,3]=translation
        row=dict(id=identity,label=label,geometry=geometry,to_world=matrix.tolist())
        modules.append(row);return row
    module('station','天气站安装参考',station['geometry'],[0,0,0])
    module('storage','同一辆小车与拆下零件',storage['geometry'],site)
    module('ground','室外地面与锚固埋深参考',r['outdoor_ground_assets']['geometry'],[0,0,0])
    def member(identity,label,resource,mod,part,*,existing=False,basis='selected_additional_candidate'):
        row=entities.setdefault(identity,dict(id=identity,label=label,resource_id=resource,
            existing_scene_identity=identity if existing else None,quantity=1,
            allocation_basis=basis,representations=[],initial_stock_credit=False,
            quantity_accepted=False,robot_use_qualified=False))
        row['representations'].append(dict(module=mod,part=part))
    for p in station['geometry']['part_records']:
        n=p['id'];prefix=n.split('__')[0]
        if prefix=='u30':
            member('hobo_u30','同一台 U30：详细外壳、内部和安装件参考','equipment:WEATHER','station',n,existing=True,basis='replacement_detail_for_existing_logger_identity')
        elif prefix in ['temperature_head','temperature_adapter','temperature_plug'] or n in ['routed__temperature_sensor_lead','routed__temperature_network_lead']:
            member('weather_temperature_humidity','Onset S-THB-M002 探头、适配器和完整引线','equipment:WEATHER','station',n)
        elif prefix in ['wind','wind_adapter','wind_plug'] or n in ['routed__wind_sensor_lead','routed__wind_network_lead']:
            member('weather_wind','Onset S-WCF 传感器、适配器和完整引线','equipment:WEATHER','station',n)
        elif prefix=='rs3':
            member('weather_radiation_shield','RS3 防辐射罩和普通抱箍安装件','equipment:WEATHER','station',n)
        elif prefix=='support':
            member('weather_mast_anchoring_set','三脚架、桅杆、拉线与接地组件套件','equipment:WEATHER','station',n,basis='one_selected_kit_set_not_one_rigid_manufactured_object')
        elif prefix=='logger_ground':
            member('weather_logger_ground_lead','U30 接地引线与端子假设','equipment:WEATHER','station',n)
        elif prefix=='retention':
            member('weather_tie_'+n.split('__',1)[1],'T50I 300 mm 扎带及其原始截尾','equipment:WEATHER','station',n,basis='one_source_tie_split_into_retained_strap_and_cutoff')
        else:raise ValueError('Unassigned station part '+n)
    for p in storage['geometry']['part_records']:
        n=p['id'];prefix=n.split('__')[0]
        if prefix=='cart':member('utility_cart','同一辆 Rubbermaid 1997206 小车','tools:supported_carrier','storage',n,existing=True,basis='same_source_cart_rigidly_relocated')
        elif prefix=='removed':member('hobo_u30',entities['hobo_u30']['label'],'equipment:WEATHER','storage',n,existing=True)
        elif prefix=='cutoff':member('weather_tie_'+n.split('__',1)[1],'T50I 300 mm 扎带及其原始截尾','equipment:WEATHER','storage',n)
        elif prefix in ['cutoffs_tray','plugs_tray']:
            identity='weather_cutoff_tray' if prefix=='cutoffs_tray' else 'weather_removed_parts_tray'
            member(identity,'新增 Bürkle 300 × 200 × 50 mm 普通托盘','tools:supported_carrier','storage',n)
        else:raise ValueError('Unassigned storage part '+n)
    for p in r['outdoor_ground_assets']['geometry']['part_records']:
        member('weather_ground_design','替代原室外平板的地面设计','facility:OUTDOOR','ground',p['id'],basis='replacement_site_geometry_not_portable_stock')
    remainder=r['weather_remainders_assets']
    module('remainders','小车下层：剩余线材与未用套件',remainder['geometry'],site)
    for p in remainder['geometry']['part_records']:
        n=p['id']
        if n in ['guy_wire_remainder','ground_wire_remainder']:identity='weather_mast_anchoring_set'
        elif n.startswith('wind_kit__'):identity='weather_wind'
        elif n.startswith('rs3_kit__'):identity='weather_radiation_shield'
        elif n.startswith('kit_tray__'):identity='weather_unused_kit_tray'
        else:raise ValueError('Unassigned remaining-stock part '+n)
        e=entities.get(identity)
        member(identity,e['label'] if e else '新增 Bürkle 普通托盘：未用套件',e['resource_id'] if e else 'tools:supported_carrier','remainders',n)
    tools=[]
    for i,(name,identity,label) in enumerate([
        ('nut_driver_assets','weather_nut_driver_sw7','Wiha 34123 · SW7'),
        ('mast_driver_assets','weather_nut_driver_half','Wiha 34143 · 1/2 inch'),
        ('wind_driver_assets','weather_nut_driver_7_16','Wiha 34142 · 7/16 inch')]):
        geometry=r[name]['geometry'];position=[8.93,18.34+.085*i,.9-geometry['bounds_m'][0][2]]
        mod=module(identity,label,geometry,position)
        tools.append(dict(id=identity,station='weather_service',support_top_m=.9,
            selected_required_units=1,shared_across_all_service_poses=True))
        for p in geometry['part_records']:
            member(identity,label,'tools:fastener_driver',identity,p['id'])
    identity='weather_wire_rope_cutter';label='KNIPEX 95 61 190 · 钢丝绳剪'
    geometry=r['wire_rope_cutter_assets']['geometry']
    rest=r['wire_rope_cutter_checks']['resting_reference']
    mod=module(identity,label,geometry,[8.93,18.595,.9])
    mod['to_world']=(np.array(mod['to_world'])@np.array(rest['to_support_plane'])).tolist()
    tools.append(dict(id=identity,station='weather_service',support_top_m=.9,
        selected_required_units=1,shared_across_all_service_poses=True,
        resting_reference_source='assets/cooling_lab_v1/wire_rope_cutter_checks.json'))
    for p in geometry['part_records']:
        member(identity,label,'tools:wire_stripper_and_driver',identity,p['id'])
    identity='weather_adjustable_wrench';label='Crescent AC28VS · 活动扳手'
    geometry=next(i['geometry'] for i in r['adjustable_wrench_assets']['items'] if i['id']=='half_inch_reference')
    rest=r['adjustable_wrench_checks']['resting_reference']
    mod=module(identity,label,geometry,[8.93,18.7,.9])
    mod['to_world']=(np.array(mod['to_world'])@np.array(rest['to_support_plane'])).tolist()
    tools.append(dict(id=identity,station='weather_service',support_top_m=.9,
        selected_required_units=1,shared_across_all_service_poses=True,
        resting_reference_source='assets/cooling_lab_v1/adjustable_wrench_checks.json'))
    for p in geometry['part_records']:
        member(identity,label,'tools:fastener_driver',identity,p['id'])
    identity='weather_tape_measure_bt5m';label='Hultafors BT5M · 5 m 钢卷尺'
    geometry=next(i['geometry'] for i in r['tape_measure_assets']['items'] if i['id']=='retracted')
    rest=r['tape_measure_checks']['resting_reference']
    mod=module(identity,label,geometry,[9.25,18.8,.9])
    mod['to_world']=(np.array(mod['to_world'])@np.array(rest['to_support_plane'])).tolist()
    tools.append(dict(id=identity,station='weather_service',support_top_m=.9,
        selected_required_units=1,shared_across_all_service_poses=True,
        resting_reference_source='assets/cooling_lab_v1/tape_measure_checks.json'))
    for p in geometry['part_records']:
        member(identity,label,'tools:tape_measure',identity,p['id'],basis='one_case_blade_and_clip_identity_shared_across_all_inspection_shapes')
    identity='weather_engineer_hammer_56_204';label='Stanley 56-204 · 玻纤柄工程锤'
    geometry=r['engineer_hammer_assets']['geometry'];rest=r['engineer_hammer_checks']['resting_reference']
    mod=module(identity,label,geometry,[9.55,18.35,.9])
    mod['to_world']=(np.array(mod['to_world'])@np.array(rest['to_support_plane'])).tolist()
    tools.append(dict(id=identity,station='weather_service',support_top_m=.9,
        selected_required_units=1,shared_across_all_service_poses=True,
        resting_reference_source='assets/cooling_lab_v1/engineer_hammer_checks.json'))
    for p in geometry['part_records']:
        member(identity,label,'tools:engineer_hammer',identity,p['id'],basis='one_forged_head_and_attached_handle_not_separate_striking_caps')
    identity='weather_mast_grease_21030';label='Super Lube 21030 · 桅杆通用润滑脂 · 85 g'
    geometry=r['mast_grease_assets']['geometry']
    module(identity,label,geometry,[9.05,18.8,.9])
    for p in geometry['part_records']:
        member(identity,label,'consumables:mast_all_purpose_grease',identity,p['id'],basis='one_container_and_85g_nominal_contents_not_extra_stock_per_inspection')
    consumables=[dict(id=identity,station='weather_service',support_top_m=.9,selected_required_units=1,
        net_mass_g=85,resting_reference_source='assets/cooling_lab_v1/mast_grease_checks.json',
        application_budget_source='assets/cooling_lab_v1/mast_grease_assets.json',
        silicone_channel_requirement_satisfied=False)]
    identity='weather_silicone_grease_93003';label='Super Lube 93003 · U30 线槽硅脂 · 85 g'
    geometry=r['silicone_grease_assets']['geometry']
    module(identity,label,geometry,[9.68,18.58,.9])
    for p in geometry['part_records']:
        member(identity,label,'consumables:u30_silicone_grease',identity,p['id'],basis='one_85g_tube_shared_across_both_source_density_scenarios')
    consumables.append(dict(id=identity,station='weather_service',support_top_m=.9,selected_required_units=1,
        net_mass_g=85,resting_reference_source='assets/cooling_lab_v1/silicone_grease_checks.json',
        application_budget_source='assets/cooling_lab_v1/silicone_grease_assets.json',
        selected_for_channel=True,silicone_channel_requirement_satisfied=False))
    cleanup=r['weather_cleanup_assets']
    for item,y in zip(cleanup['applicators'],[18.50,18.60]):
        identity=item['id'];geometry=item['geometry'];module(identity,item['label'],geometry,[9.35,y,.9])
        for p in geometry['part_records']:
            member(identity,item['label'],'tools:grease_applicator',identity,p['id'],basis='one_separate_ordinary_spatula_per_grease_family')
        tools.append(dict(id=identity,station='weather_service',support_top_m=.9,selected_required_units=1,
            shared_across_all_service_poses=True,shared_between_grease_families=False,
            assigned_grease_identity=item['assigned_grease_identity'],
            resting_reference_source='assets/cooling_lab_v1/weather_cleanup_assets.json',
            dynamic_stability_qualified=False))
    item=cleanup['wipe_pack'];identity=item['id'];geometry=item['geometry']
    module(identity,item['label'],geometry,[9.96,18.36,.9])
    for p in geometry['part_records']:
        member(identity,item['label'],'consumables:cleaning_wipes',identity,p['id'],basis='one_pack_with_300_individual_wipes_and_two_packaging_films')
    entities[identity]['contained_unit_ids']=item['unit_ids']
    entities[identity]['packaging_parts']=item['packaging_parts']
    consumables.append(dict(id=identity,station='weather_service',support_top_m=.9,selected_required_units=1,
        selected_packs=1,contained_wipes=300,application_budget_source='assets/cooling_lab_v1/weather_cleanup_assets.json'))
    old={a['id']:a for a in r['scene']['assets']}
    refs=[Path(__file__)]+[HERE/(n+'.json') for n in names]
    record=dict(schema_version=1,status='laboratory_composition_candidate_not_initial_state',
        visibility='author_and_reviewer_only_not_actor_input',
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        base_scene=dict(path='assets/cooling_lab_v1/scene.json',sha256=sha(HERE/'scene.json')),
        state_id='weather_installed_reference',modules=modules,physical_entities=list(entities.values()),
        hide_scene_asset_ids=['hobo_u30','utility_cart'],hide_architecture_parts=['outdoor_floor'],
        preserved_independent_scene_asset_ids=['ambient_rtd','eko_ms402','eko_ms56','tracker'],
        identity_replacements=[dict(id=n,base_geometry=dict(path=old[n]['geometry'],sha256=old[n]['geometry_sha256']),
            basis='Earlier low-detail logger representation is replaced, not surface-equivalent' if n=='hobo_u30' else 'Original cart source geometry and unit identity are reused') for n in ['hobo_u30','utility_cart']],
        staged_tool_candidates=tools,staged_consumable_candidates=consumables,
        alternative_context=dict(path='assets/cooling_lab_v1/weather_preparation_assets.json',sha256=sha(HERE/'weather_preparation_assets.json'),
            reused_tray_identity='weather_removed_parts_tray',simultaneously_visible=False,
            temporary_additional_stock=[dict(product='HellermannTyton 111-01975',units=1),dict(product='HellermannTyton 111-05440',units=1)],
            scope='Partial inspection only; omitted original components remain explicitly outside context. It is not a complete initial state or a transition.'),
        resource_bindings=[dict(resource_id='equipment:WEATHER',physical_entity_ids=[n for n,e in entities.items() if e['resource_id']=='equipment:WEATHER'],
            completeness_accepted=False),dict(resource_id='tools:fastener_driver',physical_entity_ids=[n for n,e in entities.items() if e['resource_id']=='tools:fastener_driver'],completeness_accepted=False),
            dict(resource_id='tools:wire_stripper_and_driver',physical_entity_ids=['weather_wire_rope_cutter'],completeness_accepted=False,
                scope='Separate cable cutter candidate for guy/ground wire; does not replace the existing electronic cutter or establish complete wire-tool stock.'),
            dict(resource_id='tools:tape_measure',physical_entity_ids=['weather_tape_measure_bt5m'],completeness_accepted=False,
                scope='Additional requirement from the tripod manufacturer tool list for external wire-length measurement; does not replace the existing caliper. Calibration and complete initial-state reconciliation remain open.'),
            dict(resource_id='tools:engineer_hammer',physical_entity_ids=['weather_engineer_hammer_56_204'],completeness_accepted=False,
                scope='Ordinary driving-tool candidate for the tripod manual stake/ground-rod requirement. Head-only catalogue mass and inferred whole-tool mass remain distinct; strike, target compatibility and robot use are unqualified.'),
            dict(resource_id='consumables:mast_all_purpose_grease',physical_entity_ids=['weather_mast_grease_21030'],completeness_accepted=False,
                scope='Metal mast only; independent from the selected U30 silicone grease. Application/cleanup behavior and complete trial/reset budgets remain open.'),
            dict(resource_id='consumables:u30_silicone_grease',physical_entity_ids=['weather_silicone_grease_93003'],completeness_accepted=False,
                scope='One selected 85 g tube for the EPDM channel; two source-density scenarios are the same stock. Silicone-rubber door gasket excluded; cable compatibility and actual application remain open.'),
            dict(resource_id='tools:grease_applicator',physical_entity_ids=[i['id'] for i in cleanup['applicators']],completeness_accepted=False,
                scope='Two separate ordinary spatulas; same model, different stock identities and lubricant assignments. Contact and roll stability unqualified.'),
            dict(resource_id='consumables:cleaning_wipes',physical_entity_ids=['weather_wipes_tx609'],completeness_accepted=False,
                scope='One 300-wipe pack with individually named sheets and two packaging films; trial/reset and packaging collection remain open.')],
        limits=['Installed/reference, base-staging and partial preparation views are mutually exclusive representations, not extra inventory.',
            'Kit groups retain individually named parts; a group is not a welded or rigid simulation body.',
            'Permanent ties retain their original cutoff identity; removed U30 plugs remain part of that same logger.',
            'All initial poses, consumed stock budgets, complete assembly states and main-scene dynamic movement remain unqualified.',
            'The weather temperature/humidity probe does not replace the independently required ambient Omega probe.',
            'Ground contact and terrain penetration are design geometry; anchoring force and soil properties remain unqualified.'],
        new_manipulation_development_allowed=False,owner_acceptance=None,
        initial_state_qualified=False,installation_qualified=False,robot_use_qualified=False)
    write_json(HERE/'weather_scene_binding.json',record)
    print(json.dumps(dict(modules=len(modules),entities=len(entities),parts=sum(m['geometry']['parts'] for m in modules))))


if __name__=='__main__':build()
