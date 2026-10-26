"""Check cross-context identity, omitted stock and invalid substitutions."""
import copy
import json
from pathlib import Path
from build_laboratory_inventory import build_record
from geometry_tools import HERE, ROOT, sha, write_json


def inspect():
    names=['campaign_allocation','weather_scene_binding','weather_inventory_sources','mast_grease_assets','weather_preparation_assets','silicone_grease_assets','weather_cleanup_assets','weather_initial_stock_assets']
    inputs=[json.loads((HERE/(n+'.json')).read_text()) for n in names]
    allocation,binding,sources,grease,preparation,silicone_asset,cleanup,initial=inputs
    report=json.loads((HERE/'laboratory_inventory.json').read_text())
    checks=[]
    def check(name,passed):
        checks.append(dict(name=name,passed=bool(passed)))
        if not passed:raise AssertionError(name)
    check('report_matches_current_inputs',report==build_record(*inputs))
    refs={s['path']:s['sha256'] for r in [report,allocation,binding,grease,preparation,silicone_asset,cleanup] for s in r.get('source_artifacts',[])}
    for path,digest in refs.items():check('source_'+path,sha(ROOT/path)==digest)
    geometry={r['geometry']['path']:r['geometry']['sha256'] for e in report['identities'] for r in e['representations']}
    for path,digest in geometry.items():check('geometry_'+path,sha(ROOT/path)==digest)
    ids={e['id']:e for e in report['identities']}
    check('base_and_context_do_not_duplicate_logger_or_cart',
          len(ids)==81+37-2+2 and report['reused_identity_ids']==['hobo_u30','utility_cart'])
    for identity in ['hobo_u30','utility_cart']:
        check(identity+'_both_contexts_same_identity',
              {r['context'] for r in ids[identity]['representations']}==({'base_display','weather_installed_reference','weather_initial_stock_candidate'} if identity=='hobo_u30' else {'base_display','weather_installed_reference'}))
    check('removed_plugs_belong_to_same_logger',
          any(r.get('module')=='storage' and any(p.startswith('removed__') for p in r['parts']) for r in ids['hobo_u30']['representations']))
    ties=[e for e in ids.values() if e['id'].startswith('weather_tie_')]
    check('fourteen_ties_not_twenty_eight_pieces_of_stock',len(ties)==14 and all(e['context_quantity']==1 and
          {r['module'] for r in e['representations']}=={'station','storage','preparation','initial_stock'} for e in ties))
    check('two_sacrificial_ties_are_additional_stock',all(n in ids and ids[n]['context_quantity']==1 for n in
          ['weather_temporary_leg','weather_temporary_brace']))
    check('preparation_tray_is_same_identity',any(r['context']=='weather_partial_preparation' for r in ids['weather_removed_parts_tray']['representations']))
    check('staged_tool_locations_not_reported_as_absent',ids['weather_tape_measure_bt5m']['initial_state_status']=='context_candidate_placement_unqualified')
    check('unpacked_positions_keep_all_existing_identities',report['counts']['unpacked_weather_identity_candidates']==38 and report['counts']['identities_without_initial_placement']==0 and
          sum(e['initial_state_status']=='unpacked_candidate_placement_unqualified' for e in ids.values())==25)
    check('all_154_original_components_retained',len(report['components'])==154 and
          {r['id'] for r in report['components']}=={r['id'] for r in allocation['components']})
    check('reference_candidates_never_reduce_base_deficits',all(
          (new['required_quantity'],new['quantity_deficit'])==(old['required_quantity'],old['quantity_deficit'])
          for new,old in zip(report['components'],allocation['components'])))
    check('requirement_types_and_open_conditions_survive_inventory_merge',all(
          all(new[k]==old[k] for k in ['requirement_kind','stock_quantity_applicable','quantity_status','required_unit','quantity_basis','state_or_acceptance_requirement','remaining_requirements'])
          for new,old in zip(report['components'],allocation['components'])))
    needs={n['id']:n for n in report['installation_requirements']}
    silicone=needs['weather_need_silicone_grease']
    check('silicone_has_one_independent_tube',silicone['candidate_ids']==['weather_silicone_grease_93003'] and
          silicone['required_quantity']==1 and silicone['unit']=='container' and
          'weather_mast_grease_21030' in silicone['excluded_substitutions'])
    check('silicone_reservation_is_inferred_and_not_doubled_by_density_scenarios',
          silicone['material_reservation']['three_campaign_reservation_g']==9 and
          silicone['material_reservation']['nominal_remaining_after_reservation_g']==76 and
          not silicone['material_reservation']['dose_qualified'] and
          silicone['material_scope']['selected_containers']==1)
    check('silicone_channel_selection_excludes_silicone_door_gasket',
          silicone['material_scope']['selected_for_channel'] and
          silicone['material_scope']['excluded_destination_parts']==['u30__door_perimeter_gasket'] and
          not silicone['material_scope']['whole_assembly_compatibility_qualified'])
    check('single_mast_tube_has_single_85g_budget',needs['weather_need_mast_grease']['candidate_ids']==['weather_mast_grease_21030'] and
          needs['weather_need_mast_grease']['material_reservation']['three_campaign_reservation_g']==6)
    check('two_independent_applicators_and_one_pack_bound',
          needs['weather_need_mast_applicator']['candidate_ids']==['weather_mast_applicator'] and
          needs['weather_need_silicone_applicator']['candidate_ids']==['weather_silicone_applicator'] and
          needs['weather_need_wipes']['candidate_ids']==['weather_wipes_tx609'] and len(ids['weather_wipes_tx609']['contained_unit_ids'])==300)
    check('existing_waste_can_only_has_unqualified_planning_reservation',needs['weather_need_residue_collection']['candidate_ids']==['oily_waste_can'] and
          needs['weather_need_residue_collection']['required_quantity']==3 and needs['weather_need_residue_collection']['unit']=='L' and
          not needs['weather_need_residue_collection']['waste_reservation']['available_capacity_qualified'])
    check('packaging_cannot_disappear_or_be_mixed_into_grease_waste',not needs['weather_need_clean_packaging_collection']['candidate_ids'] and
          set(needs['weather_need_clean_packaging_collection']['retained_unit_ids'])=={'weather_wipes_tx609/inner_bag','weather_wipes_tx609/outer_bag'})
    check('facility_is_not_portable_stock',ids['weather_ground_design']['initial_state_status']=='facility_design_not_portable_stock')
    check('initial_inventory_stays_unqualified',not report['initial_inventory_complete'] and
          not any(e['initial_stock_credit'] or e['initial_state_qualified'] for e in ids.values()) and report['owner_acceptance'] is None)
    def rejected(name, mutate):
        altered=copy.deepcopy(inputs);mutate(altered)
        try:build_record(*altered)
        except (AssertionError,KeyError):check(name,True)
        else:check(name,False)
    rejected('negative_duplicate_context_identity',lambda x:x[1]['physical_entities'].append(copy.deepcopy(x[1]['physical_entities'][0])))
    def duplicate_part(x):
        x[1]['physical_entities'][1]['representations'].append(copy.deepcopy(x[1]['physical_entities'][0]['representations'][0]))
    rejected('negative_one_part_in_two_identities',duplicate_part)
    rejected('negative_lost_cutoff_cannot_disappear',lambda x:next(e for e in x[1]['physical_entities'] if e['id'].startswith('weather_tie_'))['representations'].pop())
    rejected('negative_reused_logger_cannot_be_new_stock',lambda x:next(e for e in x[1]['physical_entities'] if e['id']=='hobo_u30').update(existing_scene_identity=None))
    rejected('negative_installed_reference_stock_credit',lambda x:x[1]['physical_entities'][0].update(initial_stock_credit=True))
    rejected('negative_unselected_expander_packet_stock',lambda x:x[2]['stock_policy'].update(optional_expander_grease_stock_credit=1))
    rejected('negative_mast_grease_as_silicone',lambda x:x[2]['stock_policy'].update(mast_21030_satisfies_silicone_requirement=True))
    rejected('negative_multiple_tubes_from_inspection_states',lambda x:x[3]['material_allocation'].update(selected_containers=2))
    rejected('negative_temporary_tie_cannot_disappear',lambda x:x[4]['temporary_ties'].pop())
    rejected('negative_density_scenarios_cannot_double_silicone_stock',lambda x:x[5]['material_allocation'].update(selected_containers=2))
    rejected('negative_channel_silicone_cannot_lose_door_gasket_exclusion',lambda x:x[5]['material_allocation'].update(excluded_destination_parts=[]))
    rejected('negative_same_wipe_reserved_twice',lambda x:x[6]['wipe_pack']['application_budget']['allocations'][1]['unit_ids'].__setitem__(0,x[6]['wipe_pack']['application_budget']['allocations'][0]['unit_ids'][0]))
    rejected('negative_two_families_cannot_share_applicator_identity',lambda x:x[6]['applicators'][1].update(id=x[6]['applicators'][0]['id']))
    negative_count=sum(c['name'].startswith('negative_') for c in checks)
    result=dict(schema_version=1,passed=all(c['passed'] for c in checks),checks=checks,negative_cases=negative_count,
        scope='Canonical identity and requirement accounting; no initial-state, safety, material compatibility or robot qualification.',
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [Path(__file__),HERE/'laboratory_inventory.json']])
    write_json(HERE/'laboratory_inventory_checks.json',result)
    print(json.dumps(dict(passed=result['passed'],checks=len(checks),negative_cases=negative_count)))


if __name__=='__main__':inspect()
