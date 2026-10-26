"""Check identity conservation and actual placement in the complete base lab."""
import copy
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE, ROOT, sha, write_json
from check_weather_assets import load_parts, overlap


def membership_valid(record):
    expected={(m['id'],p['id']) for m in record['modules'] for p in m['geometry']['part_records']}
    actual=[(p['module'],p['part']) for e in record['physical_entities'] for p in e['representations']]
    return set(actual)==expected and len(actual)==len(expected)


def build():
    r=json.loads((HERE/'weather_scene_binding.json').read_text());checks=[]
    def check(name,passed,**details):checks.append(dict(name=name,passed=bool(passed),**details))
    for ref in r['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    scene=json.loads((ROOT/r['base_scene']['path']).read_text())
    assets={a['id']:a for a in scene['assets']};modules={m['id']:m for m in r['modules']}
    check('every_rendered_part_has_exactly_one_inventory_owner',membership_valid(r))
    duplicate=copy.deepcopy(r);duplicate['physical_entities'][1]['representations'].append(duplicate['physical_entities'][0]['representations'][0])
    check('negative_duplicate_part_ownership_rejected',not membership_valid(duplicate))
    omitted=copy.deepcopy(r);omitted['physical_entities'][0]['representations'].pop()
    check('negative_omitted_part_ownership_rejected',not membership_valid(omitted))
    identities=[e['id'] for e in r['physical_entities']]
    check('no_duplicate_physical_identities',len(identities)==len(set(identities)))
    check('only_two_existing_assets_represented_elsewhere',set(identities)&set(assets)==set(r['hide_scene_asset_ids'])=={'hobo_u30','utility_cart'})
    check('all_independent_environment_instruments_retained',set(r['preserved_independent_scene_asset_ids'])<=set(assets)-set(r['hide_scene_asset_ids']))
    check('one_ground_layer_replaces_one_existing_floor',r['hide_architecture_parts']==['outdoor_floor'] and any(p['id']=='outdoor_floor' for p in scene['architecture']['part_records']))
    entities={e['id']:e for e in r['physical_entities']}
    check('same_logger_keeps_three_removed_plugs',sum(p['module']=='storage' for p in entities['hobo_u30']['representations'])==3)
    ties=[e for e in r['physical_entities'] if e['id'].startswith('weather_tie_')]
    check('fourteen_ties_each_have_strap_and_cutoff',len(ties)==14 and all(len(e['representations'])==2 and {p['module'] for p in e['representations']}=={'station','storage'} for e in ties))
    check('seven_shared_weather_tools',set(t['id'] for t in r['staged_tool_candidates'])=={'weather_nut_driver_sw7','weather_nut_driver_half','weather_nut_driver_7_16','weather_wire_rope_cutter','weather_adjustable_wrench','weather_tape_measure_bt5m','weather_engineer_hammer_56_204'} and all(t['selected_required_units']==1 and t['shared_across_all_service_poses'] for t in r['staged_tool_candidates']))
    check('partial_context_does_not_duplicate_tray_or_claim_initial_state',r['alternative_context']['reused_tray_identity']=='weather_removed_parts_tray' and not r['alternative_context']['simultaneously_visible'] and not r['initial_state_qualified'])
    check('no_acceptance_or_execution_credit',r['owner_acceptance'] is None and not any(r[k] for k in ['robot_use_qualified','installation_qualified','new_manipulation_development_allowed']) and all(not e['initial_stock_credit'] and not e['quantity_accepted'] for e in entities.values()))
    for ref in r['source_artifacts']:
        if ref['path'].endswith('_checks.json'):
            q=json.loads((ROOT/ref['path']).read_text());check('upstream_'+Path(ref['path']).stem,q['passed'])
    new={};bounds={}
    for m in r['modules']:
        parts=load_parts(m['geometry'])
        check('actual_part_names_'+m['id'],set(parts)=={p['id'] for p in m['geometry']['part_records']})
        for n,mesh in parts.items():
            mesh.apply_transform(m['to_world']);new[(m['id'],n)]=mesh
        array=np.array([p.bounds for p in parts.values()]);bounds[m['id']]=[array[:,0].min(axis=0).tolist(),array[:,1].max(axis=0).tolist()]
    bench=next(s for s in scene['support_surfaces'] if s['id']=='weather_service')
    for t in r['staged_tool_candidates']+r['staged_consumable_candidates']:
        lo,hi=np.array(bounds[t['id']]);x0,y0,x1,y1=bench['xy_bounds_m']
        check('complete_tool_on_actual_service_worktop_'+t['id'],abs(lo[2]-bench['top_m'])<1e-7 and lo[0]>=x0 and hi[0]<=x1 and lo[1]>=y0 and hi[1]<=y1,bounds_m=[lo.tolist(),hi.tolist()])
        if t['id']=='weather_wire_rope_cutter':
            reference=json.loads((HERE/'wire_rope_cutter_checks.json').read_text())['resting_reference']
            expected=np.eye(4);expected[:3,3]=[8.93,18.595,bench['top_m']]
            expected=expected@np.array(reference['to_support_plane'])
            check('cutter_preserves_verified_resting_contacts',np.allclose(modules[t['id']]['to_world'],expected,atol=1e-10)
                and all(c['inside_support'] for c in reference['range_checks']))
        if t['id']=='weather_adjustable_wrench':
            reference=json.loads((HERE/'adjustable_wrench_checks.json').read_text())['resting_reference']
            expected=np.eye(4);expected[:3,3]=[8.93,18.7,bench['top_m']]
            expected=expected@np.array(reference['to_support_plane'])
            check('wrench_preserves_verified_resting_contacts',np.allclose(modules[t['id']]['to_world'],expected,atol=1e-10)
                and all(c['inside_support'] for c in reference['range_checks']))
        if t['id']=='weather_mast_grease_21030':
            reference=json.loads((HERE/'mast_grease_checks.json').read_text())['resting_reference']
            expected=np.eye(4);expected[:3,3]=[9.05,18.8,bench['top_m']]
            check('grease_keeps_cap_base_support_and_separate_silicone_requirement',np.allclose(modules[t['id']]['to_world'],expected,atol=1e-10)
                and reference['support_margin_m']>.010 and not t['silicone_channel_requirement_satisfied'] and t['net_mass_g']==85)
        if t['id']=='weather_tape_measure_bt5m':
            reference=json.loads((HERE/'tape_measure_checks.json').read_text())['resting_reference']
            expected=np.eye(4);expected[:3,3]=[9.25,18.8,bench['top_m']]
            expected=expected@np.array(reference['to_support_plane'])
            check('tape_preserves_actual_base_support',np.allclose(modules[t['id']]['to_world'],expected,atol=1e-10)
                and reference['support_margin_m']>.001)
        if t['id']=='weather_engineer_hammer_56_204':
            reference=json.loads((HERE/'engineer_hammer_checks.json').read_text())['resting_reference']
            expected=np.eye(4);expected[:3,3]=[9.55,18.35,bench['top_m']]
            expected=expected@np.array(reference['to_support_plane'])
            check('hammer_keeps_actual_head_and_handle_support',np.allclose(modules[t['id']]['to_world'],expected,atol=1e-10)
                and reference['support_margin_m']>.001 and all(c['inside_support'] for c in reference['range_checks']))
    def broad(a,b):return bool(np.all(np.minimum(a[1],b[1])-np.maximum(a[0],b[0])>1e-7))
    occupied=[];collisions=[];tested=0;nonvolume=[]
    # Read only possible neighbours, but use their complete actual meshes.
    for a in scene['assets']:
        if a['id'] in r['hide_scene_asset_ids']:continue
        ab=np.asarray(a['normalized_bounds_m'])+a['position_m']
        if not any(broad(ab,b) for k,b in bounds.items() if k!='ground'):continue
        for n,m in load_parts(dict(path=a['geometry'],sha256=a['geometry_sha256'])).items():
            m.apply_translation(a['position_m']);occupied.append((a['id']+'/'+n,m))
    architecture=load_parts(scene['architecture'])
    for n,m in architecture.items():
        if n not in r['hide_architecture_parts'] and any(broad(m.bounds,b) for k,b in bounds.items() if k!='ground'):
            occupied.append(('architecture/'+n,m))
    for (module,n),a in new.items():
        if module=='ground' or n.endswith('_text'):continue
        for other,b in occupied:
            if not broad(a.bounds,b.bounds):continue
            tested+=1
            if a.is_volume and b.is_volume:
                v=overlap(a,b)
                if not np.isfinite(v) or abs(v)>.001:collisions.append(dict(module=module,part=n,other=other,intersection_mm3=v))
            else:
                manager=trimesh.collision.CollisionManager();manager.add_object('candidate',a)
                hit=manager.in_collision_single(b);nonvolume.append(dict(module=module,part=n,other=other,surface_intersection=bool(hit)))
                if hit:collisions.append(dict(module=module,part=n,other=other,surface_intersection=True))
    check('new_modules_clear_complete_remaining_lab_geometry',not collisions,narrow_phase_pairs=tested,intersections=collisions,nonvolume_surface_checks=nonvolume)
    tool_ids={t['id'] for t in r['staged_tool_candidates']+r['staged_consumable_candidates']};tool_hits=[];tool_pairs=0
    for (mid,n),a in new.items():
        if mid not in tool_ids or n.endswith('_text'):continue
        for (other,q),b in new.items():
            if other in ['ground',mid] or q.endswith('_text') or not broad(a.bounds,b.bounds):continue
            tool_pairs+=1;v=overlap(a,b)
            if not np.isfinite(v) or abs(v)>.001:tool_hits.append(dict(tool=mid,part=n,other=other+'/'+q,intersection_mm3=v))
    check('staged_tools_clear_station_cart_and_each_other',not tool_hits,narrow_phase_pairs=tool_pairs,intersections=tool_hits)
    # Retain the actual failed first placement over the ambient RTD lead.
    # The cable stays in the scene; moving the tool, not hiding the obstacle,
    # resolves this regression.
    hammer='weather_engineer_hammer_56_204'
    hammer_rest=json.loads((HERE/'engineer_hammer_checks.json').read_text())['resting_reference']['to_support_plane']
    rejected=np.eye(4);rejected[:3,3]=[9.75,18.8,bench['top_m']];rejected=rejected@np.array(hammer_rest)
    delta=rejected@np.linalg.inv(np.array(modules[hammer]['to_world']))
    rtd=assets['ambient_rtd'];lead=load_parts(dict(path=rtd['geometry'],sha256=rtd['geometry_sha256']))['pfa_cable_nominal_6ft']
    lead.apply_translation(rtd['position_m']);rejected_hits=[]
    for (mid,n),m in new.items():
        if mid!=hammer or n.endswith('_text'):continue
        candidate=m.copy();candidate.apply_transform(delta);v=overlap(candidate,lead)
        if v>.001:rejected_hits.append(dict(part=n,other='ambient_rtd/pfa_cable_nominal_6ft',intersection_mm3=v))
    check('negative_hammer_placement_over_rtd_lead_rejected',bool(rejected_hits),rejected_to_world=rejected.tolist(),intersections=rejected_hits)
    failed=[c['name'] for c in checks if not c['passed']]
    paths=[Path(__file__),HERE/'weather_scene_binding.json',HERE/'check_weather_assets.py']
    result=dict(schema_version=1,passed=not failed,failed=failed,checks=checks,module_world_bounds_m=bounds,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in paths],
        counts=dict(modules=len(modules),physical_entities=len(entities),existing_reused=2,rendered_parts=len(new),
            base_scene_assets=len(assets),hidden_base_assets=2,visible_base_assets=len(assets)-2),
        scope='Complete laboratory composition, exact part ownership and static placement. Terrain penetration is intentional design context and is excluded from solid overlap; existing station/storage internal checks remain upstream. No collision-free path, load, initial-state completeness or operation qualification.',
        owner_acceptance=None,robot_use_qualified=False)
    write_json(HERE/'weather_scene_binding_checks.json',result)
    print(json.dumps(dict(passed=not failed,checks=len(checks),failed=failed,counts=result['counts'])))
    if failed:raise AssertionError(failed)


if __name__=='__main__':build()
