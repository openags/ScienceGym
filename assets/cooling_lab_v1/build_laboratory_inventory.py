"""Join base allocation and installed-reference identities without stock credit.

This is downstream of both records, avoiding a circular build dependency.
Supplementary installation needs refine existing requirements; they do not
replace the 154 paper-derived components or turn reference poses into stock.
"""
import copy
import json
from collections import Counter
from pathlib import Path
from geometry_tools import HERE, ROOT, sha, write_json


COMPONENT_REFERENCES = {
    'equipment:WEATHER:component_1': ['hobo_u30'],
    'equipment:WEATHER:component_2': ['weather_temperature_humidity'],
    'equipment:WEATHER:component_3': ['weather_wind'],
    'equipment:WEATHER:component_4': ['weather_mast_anchoring_set', 'weather_radiation_shield'],
    'equipment:WEATHER:component_5': ['weather_logger_ground_lead'],
    'tools:fastener_driver:component_1': ['weather_nut_driver_sw7', 'weather_nut_driver_half',
                                        'weather_nut_driver_7_16', 'weather_adjustable_wrench'],
    'tools:wire_stripper_and_driver:component_3': ['weather_wire_rope_cutter'],
    'tools:supported_carrier:component_1': ['utility_cart', 'weather_cutoff_tray',
                                         'weather_removed_parts_tray', 'weather_unused_kit_tray'],
}


def build_record(allocation, binding, sources, grease, preparation, silicone):
    base = {p['id']: p for p in allocation['physical_instances']}
    assert len(base) == len(allocation['physical_instances']), 'duplicate base identity'
    weather = {p['id']: p for p in binding['physical_entities']}
    assert len(weather) == len(binding['physical_entities']), 'duplicate weather identity'
    modules = {m['id']: m for m in binding['modules']}
    assert len(modules) == len(binding['modules']), 'duplicate context module'
    staged_ids={p['id'] for p in binding['staged_tool_candidates']+binding['staged_consumable_candidates']}
    identities = {}
    for p in base.values():
        identities[p['id']] = dict(id=p['id'], label=p['label'],
            kind='reference_asset' if not p['initial_stock_credit'] else 'base_candidate',
            base_candidate_placement=True, installed_reference_present=False,
            representations=[dict(context='base_display', geometry=p['geometry'],
                station=p['station'], position_m=p['position_m'])],
            initial_stock_credit=False, initial_state_qualified=False,
            initial_state_status='base_candidate_placement_unqualified')
    occupied = set()
    reused = []
    for e in weather.values():
        existing = e['existing_scene_identity']
        if existing:
            assert existing == e['id'] and existing in base, 'unresolved reused scene identity'
            reused.append(existing)
        else:
            assert e['id'] not in base, 'undeclared duplicate identity across contexts'
        assert not e['initial_stock_credit'], 'installed reference cannot grant initial stock'
        row = identities.setdefault(e['id'], dict(id=e['id'], label=e['label'],
            kind='facility_design' if e['resource_id'].startswith('facility:') else 'context_candidate',
            base_candidate_placement=False, installed_reference_present=False, representations=[],
            initial_stock_credit=False, initial_state_qualified=False,
            initial_state_status='facility_design_not_portable_stock' if e['resource_id'].startswith('facility:') else
                'context_candidate_placement_unqualified' if e['id'] in staged_ids else 'initial_placement_missing'))
        row['installed_reference_present'] = True
        row['context_quantity'] = e['quantity']
        row['allocation_basis'] = e['allocation_basis']
        grouped = {}
        for ref in e['representations']:
            key = (ref['module'], ref['part'])
            assert key not in occupied, 'context part assigned to two physical identities'
            occupied.add(key)
            module = modules[ref['module']]
            assert ref['part'] in {p['id'] for p in module['geometry']['part_records']}, 'unknown context part'
            grouped.setdefault(ref['module'], []).append(ref['part'])
        for module_id, parts in grouped.items():
            m = modules[module_id]
            row['representations'].append(dict(context=binding['state_id'], module=module_id,
                geometry=dict(path=m['geometry']['path'], sha256=m['geometry']['sha256']),
                parts=parts, to_world=m['to_world']))
    expected = {(m['id'], p['id']) for m in modules.values() for p in m['geometry']['part_records']}
    assert occupied == expected, 'context parts absent from inventory'
    assert set(reused) == set(binding['hide_scene_asset_ids']), 'replacement identities disagree with hidden base assets'
    # The partial low-mast view reuses installed parts and one tray, but has
    # two additional sacrificial ties. Account for these without inventing a
    # second sensor, mast or tray, or assuming a disposal state after cutting.
    station_owner={r['part']:e['id'] for e in weather.values() for r in e['representations'] if r['module']=='station'}
    temporary={t['part']:t for t in preparation['temporary_ties']}
    assert len(temporary)==len(preparation['temporary_ties']), 'duplicate temporary tie part'
    planned=Counter({r['product']:r['units'] for r in binding['alternative_context']['temporary_additional_stock']})
    assert Counter(t['product'] for t in temporary.values())==planned, 'temporary stock omitted or duplicated'
    prep_groups={}
    for p in preparation['geometry']['part_records']:
        name=p['id']
        if name in temporary:
            tie=temporary[name];identity='weather_'+tie['id']
            assert identity not in identities, 'temporary tie identity reused'
            identities[identity]=dict(id=identity,label='临时固定扎带 · '+tie['product'],kind='context_candidate',
                base_candidate_placement=False,installed_reference_present=False,representations=[],
                initial_stock_credit=False,initial_state_qualified=False,initial_state_status='initial_placement_missing',
                context_quantity=1,allocation_basis='additional_sacrificial_tie_not_one_of_fourteen_retained_ties',
                disposition='Removal and post-cut stock/waste geometry remain unspecified.')
        elif name=='free_plug_tray__formed_tray':identity=preparation['reuse_candidate_tray_identity']
        else:identity=station_owner[name]
        assert identity in identities, 'unknown preparation identity'
        prep_groups.setdefault(identity,[]).append(name)
    assert set(temporary)<=set(p['id'] for p in preparation['geometry']['part_records']), 'temporary tie lacks geometry'
    origin=preparation['station_origin_world_m']
    for identity,parts in prep_groups.items():
        identities[identity]['preparation_reference_present']=True
        identities[identity]['representations'].append(dict(context='weather_partial_preparation',module='preparation',
            geometry={k:preparation['geometry'][k] for k in ['path','sha256']},parts=parts,
            to_world=[[1,0,0,origin[0]],[0,1,0,origin[1]],[0,0,1,origin[2]],[0,0,0,1]]))
    assert not sources['stock_policy']['optional_expander_selected'], 'selected configuration changed; review kit stock'
    assert not sources['stock_policy']['mast_21030_satisfies_silicone_requirement'], 'silicone-free grease misallocated'
    assert sources['stock_policy']['optional_expander_grease_stock_credit'] == 0, 'unselected kit credited as stock'
    components = copy.deepcopy(allocation['components'])
    by_component = {c['id']: c for c in components}
    for identity, candidates in COMPONENT_REFERENCES.items():
        assert identity in by_component, 'unknown parent component'
        assert set(candidates) <= set(weather), 'missing component reference identity'
        by_component[identity]['context_reference_ids'] = candidates
        by_component[identity]['context_reference_scope'] = 'Partial installed/reference candidate only; does not change initial quantity or completeness.'
    environment_branches = by_component['equipment:WEATHER:component_1']['branch_ids']
    needs = []
    def need(identity, label, resource, candidates, quantity, unit, basis, parent=None,
             source_ids=None, exclusion=None):
        assert len(candidates) == len(set(candidates)), 'duplicate candidate in installation need'
        assert set(candidates) <= set(identities), 'unknown candidate in installation need'
        if parent: assert parent in by_component, 'unknown installation parent component'
        needs.append(dict(id=identity, label=label, resource_id=resource,
            parent_resource_id='equipment:WEATHER', parent_component_id=parent,
            branch_ids=environment_branches, required_quantity=quantity, unit=unit,
            quantity_basis=basis, candidate_ids=candidates, candidate_identity_count=len(candidates),
            initial_stock_credit=0, initial_state_qualified=False, complete=False,
            source_ids=source_ids or [], excluded_substitutions=exclusion or [],
            status='candidate_initial_state_unqualified' if candidates else 'missing_candidate'))
    for suffix, label in [('sw7','SW7 套筒工具'), ('half','1/2 inch 套筒工具'), ('7_16','7/16 inch 套筒工具')]:
        need('weather_need_nut_driver_'+suffix, label, 'tools:fastener_driver',
             ['weather_nut_driver_'+suffix], 1, 'tool', 'One shared tool across matching fasteners; selected installation inventory.',
             'tools:fastener_driver:component_1', [] if suffix=='sw7' else ['ONSET_TRIPOD'])
        if suffix=='sw7':
            needs[-1]['quantity_basis']='Selected SW7 driver for the NORMA clamp candidate; size comes from the clamp/driver records, not the tripod tool list.'
        name={'sw7':'nut_driver','half':'mast_driver','7_16':'wind_driver'}[suffix]
        needs[-1]['source_artifacts']=[dict(path='assets/cooling_lab_v1/'+name+'_assets.json',sha256=sha(HERE/(name+'_assets.json')))]
    for suffix, label, resource, parent in [
        ('adjustable_wrench','活动扳手','tools:fastener_driver','tools:fastener_driver:component_1'),
        ('wire_rope_cutter','拉线／接地线剪切工具','tools:wire_stripper_and_driver','tools:wire_stripper_and_driver:component_3'),
        ('tape_measure_bt5m','外部线材测长工具','tools:tape_measure',None),
        ('engineer_hammer_56_204','桩／接地棒敲击工具候选','tools:engineer_hammer',None)]:
        need('weather_need_'+suffix, label, resource, ['weather_'+suffix], 1, 'tool',
             'One reusable installation candidate. Target suitability and robot operation are unqualified.', parent, ['ONSET_TRIPOD'])
    need('weather_need_mast_grease','桅杆通用润滑脂','consumables:mast_all_purpose_grease',
         ['weather_mast_grease_21030'], 1, 'container', 'One selected 85 g tube; per-application mass is an inference.', source_ids=['ONSET_TRIPOD'])
    needs[-1]['material_reservation'] = copy.deepcopy(grease['application_budget'])
    need('weather_need_silicone_grease','U30 线槽硅脂','consumables:u30_silicone_grease',
         ['weather_silicone_grease_93003'], 1, 'container',
         'One selected 85 g tube, shared across two conflicting source-density scenarios. Application mass is an inference, not a qualified dose.',
         'equipment:WEATHER:component_5', ['ONSET_U30_NRC','ONSET_EXPANDER'],
         ['weather_mast_grease_21030', 'unselected_S-ADAPT-X5-10_grease', 'RX3004_5g_packet_assumption'])
    needs[-1]['material_reservation'] = copy.deepcopy(silicone['application_budget'])
    needs[-1]['material_scope'] = copy.deepcopy(silicone['material_allocation'])
    needs[-1]['source_artifacts'] = [dict(path='assets/cooling_lab_v1/silicone_grease_assets.json',
                                        sha256=sha(HERE/'silicone_grease_assets.json'))]
    for family, label in [('mast','桅杆润滑脂普通涂抹工具'), ('silicone','硅脂普通涂抹工具')]:
        need('weather_need_'+family+'_applicator', label, 'tools:grease_applicator', [], 1, 'tool',
             'Engineering inference: a separate ordinary applicator for each grease family; tool selection and material compatibility remain open.')
    need('weather_need_wipes','涂抹前后擦拭材料','consumables:cleaning_wipes',[],None,'wipe',
         'Count and compatible material remain unallocated; one waste container is not wipe stock.', source_ids=['ONSET_U30_NRC'])
    need('weather_need_residue_collection','残脂／擦拭物收集容量','facility:WASTE',['oily_waste_can'],None,'g',
         'Existing can is only a service candidate; liner, material compatibility and free capacity are not allocated.')
    for tie in temporary.values():
        need('weather_need_'+tie['id'],'临时固定扎带 · '+tie['product'],'consumables:temporary_tie',
             ['weather_'+tie['id']],1,'tie','One additional sacrificial tie in the low-mast reference; reset stock and post-cut disposition remain open.')
    # A returned list of alternate meshes must never increase nominal grease.
    assert grease['net_mass_g'] == 85 and grease['material_allocation']['selected_containers'] == 1
    assert silicone['net_mass_g'] == 85 and silicone['material_allocation']['selected_containers'] == 1
    assert silicone['material_allocation']['physical_identity'] == 'weather_silicone_grease_93003'
    assert silicone['material_allocation']['selected_for_channel']
    assert 'u30__door_perimeter_gasket' in silicone['material_allocation']['excluded_destination_parts']
    paths = [Path(__file__), HERE/'campaign_allocation.json', HERE/'weather_scene_binding.json',
             HERE/'weather_inventory_sources.json', HERE/'mast_grease_assets.json',HERE/'weather_preparation_assets.json',
             HERE/'silicone_grease_assets.json']
    return dict(schema_version=1, status='laboratory_inventory_incomplete',
        scope='One canonical identity registry across base, installed-weather and partial-preparation displays, base component requirements, and supplementary installation needs. Not an initial simulation state or controller input.',
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in paths],
        identities=list(identities.values()), components=components, installation_requirements=needs,
        sources=sources, reused_identity_ids=sorted(reused),
        counts=dict(base_identities=len(base), context_identities=len(weather), reused_identities=len(reused),
            preparation_only_identities=len(temporary),
            unique_review_identities=len(identities), facility_designs=sum(r['kind']=='facility_design' for r in identities.values()),
            context_only_identities=sum(not r['base_candidate_placement'] for r in identities.values()),
            base_component_requirements=len(components), installation_requirements=len(needs),
            installation_needs_without_candidate=sum(not n['candidate_ids'] for n in needs),
            installation_quantities_unallocated=sum(n['required_quantity'] is None for n in needs),
            qualified_initial_identities=0, qualified_branches=0),
        quantity_accepted=False, initial_inventory_complete=False, owner_acceptance=None,
        new_manipulation_development_allowed=False)


def build():
    inputs=[json.loads((HERE/(n+'.json')).read_text()) for n in
            ['campaign_allocation','weather_scene_binding','weather_inventory_sources','mast_grease_assets','weather_preparation_assets','silicone_grease_assets']]
    result=build_record(*inputs)
    write_json(HERE/'laboratory_inventory.json',result)
    print(json.dumps(result['counts']))
    return result


if __name__=='__main__': build()
