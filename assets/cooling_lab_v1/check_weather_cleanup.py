"""Actual geometry, material separation and cleanup stock conservation."""
import copy
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE, ROOT, sha, write_json
from check_weather_assets import overlap
from review_mesh_io import load_parts


def stock_valid(r):
    p=r['wipe_pack'];budget=p['application_budget'];ids=p['unit_ids']
    used=[n for row in budget['allocations'] for n in row['unit_ids']]
    apps=r['applicators']
    return (len(ids)==len(set(ids))==p['selected_packs']*p['wipes_per_pack']==300
        and len(used)==len(set(used))==budget['reserved_wipes'] and set(used)<=set(ids)
        and budget['reserved_wipes']+budget['remaining_wipes']==len(ids)
        and all(row['quantity']==len(row['unit_ids']) for row in budget['allocations'])
        and len(apps)==len({a['id'] for a in apps})==2
        and {a['assigned_grease_identity'] for a in apps}=={'weather_mast_grease_21030','weather_silicone_grease_93003'}
        and not any(a['shared_between_grease_families'] for a in apps)
        and p['isolated_reference']['physical_identity'] in ids and not p['isolated_reference']['adds_stock'])


def build():
    r=json.loads((HERE/'weather_cleanup_assets.json').read_text());checks=[]
    def check(name,passed,**extra):
        checks.append(dict(name=name,passed=bool(passed),**extra))
        if not passed:raise AssertionError(name+' '+str(extra))
    for ref in r['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    source=json.loads((HERE/'weather_cleanup_sources.json').read_text())
    check('two_tools_share_geometry_but_not_identity',r['applicators'][0]['geometry']==r['applicators'][1]['geometry'] and
          r['applicators'][0]['id']!=r['applicators'][1]['id'])
    tool=load_parts(r['applicators'][0]['geometry'])['continuous_stainless_spatula']
    check('spatula_is_one_connected_closed_solid',tool.is_volume and len(tool.split())==1)
    check('spatula_matches_published_envelope',np.allclose(tool.extents,[.150,.009,.0035],atol=2e-7,rtol=0),actual_m=tool.extents.tolist())
    shaft=tool.vertices[np.abs(tool.vertices[:,0])<=.03000001]
    check('round_handle_keeps_source_diameter',np.allclose(np.linalg.norm(shaft[:,1:]-[0,.00175],axis=1),.00175,atol=1e-8,rtol=0))
    check('two_blade_ends_differ',tool.contains([[-.074,.004,.00175]])[0] and not tool.contains([[.074,.004,.00175]])[0])
    check('flat_ends_keep_inferred_thickness',np.allclose(np.ptp(tool.vertices[np.abs(tool.vertices[:,0]-.060)<1e-6,2]),.0007,atol=1e-8))
    check('round_handle_contact_does_not_grant_stability',abs(tool.bounds[0,2])<1e-9 and
          all(a['rest']['contact_basis']=='round_handle_tangent_line' and not a['rest']['dynamic_stability_qualified'] and not a['rest']['anti_roll_feature'] for a in r['applicators']))
    p=r['wipe_pack'];parts=load_parts(p['geometry']);wipes={n:m for n,m in parts.items() if n.startswith('wipe_')}
    check('all_300_wipes_are_individually_represented',set(wipes)=={'wipe_'+str(i).zfill(3) for i in range(1,301)} and len(parts)==303)
    actual_mass=0;positions=[]
    for name,m in wipes.items():
        check('sheet_geometry_'+name,m.is_volume and np.allclose(m.extents,[.2286,.2286,.00035],atol=2e-8,rtol=0))
        actual_mass+=m.volume/.00035*69;positions.append(m.bounds)
    positions=np.array(positions);z=sorted((b[0,2],b[1,2]) for b in positions)
    check('ordered_stack_has_no_duplicated_volume',all(a[1]<=b[0]+1e-8 for a,b in zip(z,z[1:])))
    check('typical_basis_weight_mass_preserved',abs(actual_mass-p['expected_total_dry_wipe_mass_g'])<.001,actual_dry_mass_g=actual_mass)
    lo=positions[:,0].min(axis=0);hi=positions[:,1].max(axis=0)
    stack=trimesh.creation.box(hi-lo);stack.apply_translation((lo+hi)/2)
    for name in ['inner_bag','outer_bag']:
        bag=parts[name]
        check('hollow_closed_packaging_'+name,bag.is_volume and not bag.contains([stack.centroid])[0])
        v=overlap(stack,bag)
        check('all_actual_sheets_clear_'+name,abs(v)<.01,intersection_mm3=v)
    v=overlap(parts['inner_bag'],parts['outer_bag'])
    check('separate_packaging_films_do_not_intersect',abs(v)<.01,intersection_mm3=v)
    damaged=parts['inner_bag'].copy();damaged.fix_normals(multibody=True)
    check('negative_per_component_normal_repair_fills_cavity',overlap(stack,damaged)>1e6 and damaged.volume>100*parts['inner_bag'].volume,
          actual_hollow_volume_m3=float(parts['inner_bag'].volume),incorrect_repaired_volume_m3=float(damaged.volume))
    from build_weather_cleanup import pouch
    check('negative_inner_bag_extending_into_outer_seal_rejected',overlap(pouch(.244,.146,.056,.00008),parts['outer_bag'])>1000)
    shifted=parts['inner_bag'].copy();shifted.apply_translation([.010,0,0])
    check('negative_displaced_packaging_through_wipes_rejected',overlap(stack,shifted)>1)
    one=load_parts(p['isolated_reference']['geometry'])['wipe_001']
    check('isolated_sheet_preserves_same_dimensions_and_volume',np.allclose(one.extents,wipes['wipe_001'].extents,atol=1e-8) and abs(one.volume-wipes['wipe_001'].volume)<1e-10)
    check('one_pack_and_36_distinct_reserved_sheets',stock_valid(r) and p['application_budget']['reserved_wipes']==36)
    for name,mutation in [
        ('duplicate_reserved_sheet',lambda x:x['wipe_pack']['application_budget']['allocations'][1]['unit_ids'].__setitem__(0,x['wipe_pack']['application_budget']['allocations'][0]['unit_ids'][0])),
        ('shipping_case_as_selected_stock',lambda x:x['wipe_pack'].update(selected_packs=10)),
        ('isolated_view_adds_stock',lambda x:x['wipe_pack']['isolated_reference'].update(adds_stock=True)),
        ('one_tool_shared_between_greases',lambda x:x['applicators'][1].update(id=x['applicators'][0]['id']))]:
        bad=copy.deepcopy(r);mutation(bad);check('negative_'+name,not stock_valid(bad))
    waste=r['waste_reservation'];estimated=waste['estimated_loose_wipe_volume_l']+waste['upper_bound_grease_mass_g']/.89/1000
    check('explicit_waste_planning_envelope',estimated<waste['reserved_volume_l']<waste['nominal_catalogue_capacity_l'],
          conservative_planning_volume_l=estimated,scope='Fourfold dry-sheet volume plus all 15 g reserved grease at the lower nominal density; not measured waste capacity.')
    check('source_sorption_not_used_as_grease_absorption_limit','sorption' not in waste and not waste['available_capacity_qualified'])
    check('no_execution_or_acceptance_credit',r['owner_acceptance'] is None and not r['initial_stock_credit'] and not r['robot_use_qualified'] and not waste['actual_transfer_complete'])
    result=dict(schema_version=1,passed=True,checks=checks,
        source_artifacts=[dict(path=str(q.relative_to(ROOT)),sha256=sha(q)) for q in [Path(__file__),HERE/'weather_cleanup_assets.json',HERE/'check_weather_assets.py',HERE/'review_mesh_io.py']],
        estimated_spatula_mass_g=tool.volume*source['reconstruction']['spatula_steel_density_kg_m3']*1000,
        scope='Geometry, stock reservation and separate candidate material volumes. No grip, wiping, dose, contamination removal, roll stability or waste-handling qualification.',
        owner_acceptance=None,robot_use_qualified=False)
    write_json(HERE/'weather_cleanup_checks.json',result)
    print(json.dumps(dict(passed=True,checks=len(checks),spatula_mass_g=result['estimated_spatula_mass_g'])))


if __name__=='__main__':build()
