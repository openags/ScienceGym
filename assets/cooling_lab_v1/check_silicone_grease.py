"""Verify actual exported capacity, alternate fills, support and use boundaries."""
import itertools
import json
from pathlib import Path
import numpy as np
from shapely.geometry import MultiPoint, Point
import trimesh
from geometry_tools import HERE, ROOT, sha, write_json
from check_weather_assets import load_parts, overlap


def build():
    record=json.loads((HERE/'silicone_grease_assets.json').read_text())
    source=json.loads((HERE/'silicone_grease_sources.json').read_text());checks=[];all_parts={};supports=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for ref in record['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    check('both_conflicting_source_densities_preserved',{i['approximate_density_g_ml'] for i in record['items']}=={.96,1.11}
          and 'not a measured temperature law' in source['reconstruction']['density_status'])
    for item in record['items']:
        key=item['id'];parts=load_parts(item['geometry']);all_parts[key]=parts
        solids={n:m for n,m in parts.items() if not n.endswith('_text')}
        check(key+'_physical_groups',set(itertools.chain.from_iterable(record['groups'].values()))==set(parts) and len(parts)==5)
        for n,m in solids.items():check(key+'_connected_closed_'+n,m.is_volume and len(m.split())==1)
        scene=trimesh.util.concatenate(list(solids.values()))
        check(key+'_source_proportioned_inferred_envelope',np.allclose(scene.extents,[.054,.032,.152],atol=3e-6,rtol=0)
            and not source['manufacturer_facts']['container_dimensions_published_in_inspected_primary_sources'],actual_m=scene.extents.tolist())
        shell=solids['tube_shell_and_sealed_tail'];cap=solids['ribbed_hollow_cap'];stock=solids['nominal_85g_silicone_stock']
        check(key+'_real_nozzle_bore_and_wall',not shell.contains([[0,0,.009],[.0078,0,.009]]).any() and shell.contains([[.0095,0,.009]])[0])
        check(key+'_actual_euro_hanging_slot',not shell.ray.intersects_any([[0,-.01,.148],[.010,-.01,.1435]],[[0,1,0],[0,1,0]]).any()
              and shell.ray.intersects_any([[.020,-.01,.145]],[[0,1,0]])[0])
        check(key+'_sealed_tail',shell.contains([[0,0,.137],[0,0,.139]]).all())
        check(key+'_hollow_cap_closed_base',not cap.contains([[0,0,.010],[.011,0,.010]]).any()
              and cap.contains([[0,0,.001],[.014,0,.010]]).all())
        measured_mass=stock.volume*item['approximate_density_g_ml']*1e6
        check(key+'_85g_from_exported_volume',abs(measured_mass-85)<.1,
              actual_volume_ml=float(stock.volume*1e6),approximate_mass_g=measured_mass,
              scope='Nominal density and tessellated volume consistency; no metrology or filling tolerance.')
        check(key+'_stock_inside_tube',stock.bounds[1,2]<.1358 and stock.bounds[0,2]>.007
              and record['inferred_cavity_volume_m3']>stock.volume)
        intersections=[dict(parts=[a,b],volume_mm3=overlap(x,y)) for (a,x),(b,y) in itertools.combinations(solids.items(),2)]
        check(key+'_distinct_material_volumes',all(abs(r['volume_mm3'])<.01 for r in intersections),pairs=intersections)
        shifted=stock.copy();shifted.apply_translation([.003,0,0])
        check(key+'_negative_stock_through_wall',overlap(shifted,shell)>1)
        opened={n:m.copy() for n,m in solids.items()}
        for n in record['groups']['cap']:opened[n].apply_translation(record['inspection']['cap_translation_m'])
        check(key+'_separated_cap_clear',all(abs(overlap(opened[n],opened[other]))<.01
              for n in record['groups']['cap'] for other in ['tube_shell_and_sealed_tail','nominal_85g_silicone_stock']))
        contact=scene.vertices[scene.vertices[:,2]<1e-7];polygon=MultiPoint(contact[:,:2]).convex_hull
        density={'tube_shell_and_sealed_tail':1200.,'ribbed_hollow_cap':950.,
                 'inferred_cap_sealing_annulus':1100.,'nominal_85g_silicone_stock':item['approximate_density_g_ml']*1000}
        masses=np.array([m.volume*density[n] for n,m in solids.items()]);centres=np.array([m.center_mass for m in solids.values()])
        com=np.sum(masses[:,None]*centres,axis=0)/masses.sum();margin=polygon.boundary.distance(Point(com[:2]))
        check(key+'_actual_cap_base_support',abs(scene.bounds[0,2])<1e-7 and polygon.contains(Point(com[:2])) and margin>.010,
              inferred_com_m=com.tolist(),support_margin_m=margin)
        supports.append(dict(scenario=key,to_support_plane=np.eye(4).tolist(),support_margin_m=margin,
                             estimated_total_mass_kg=float(masses.sum()),density_hypotheses_kg_m3=density))
    first,second=(all_parts[i['id']] for i in record['items'])
    check('same_external_container_in_both_scenarios',all(np.array_equal(first[n].vertices,second[n].vertices)
          and np.array_equal(first[n].faces,second[n].faces) for n in record['groups']['container']+record['groups']['cap']))
    check('lower_density_requires_larger_fill',second['nominal_85g_silicone_stock'].volume>first['nominal_85g_silicone_stock'].volume)
    check('negative_reusing_one_fill_for_both_densities',abs(first['nominal_85g_silicone_stock'].volume*.96*1e6-85)>5)
    allocation=record['material_allocation'];budget=record['application_budget']
    check('one_tube_across_all_views',allocation['selected_containers']==1 and
          {i['physical_identity'] for i in record['items']}=={allocation['physical_identity']})
    check('epdm_and_silicone_gasket_are_different_destinations',source['manufacturer_facts']['contains_silicone'] and
          allocation['manufacturer_epdm_compatibility_rating']=='E' and allocation['manufacturer_silicone_rubber_compatibility_rating']=='NC' and
          'u30__door_perimeter_gasket' in allocation['excluded_destination_parts'] and
          not allocation['actual_cable_jacket_compatibility_qualified'] and not allocation['whole_assembly_compatibility_qualified'])
    check('no_mixing_with_mast_grease','mixing_with_mast_grease' in allocation['additional_exclusions'])
    check('future_power_path_included_in_selected_budget','future_external_power' in budget['reserved_cable_paths'] and len(budget['reserved_cable_paths'])==4)
    check('fresh_assembly_and_three_campaign_mass_balance',budget['per_channel_g']+4*budget['per_cable_path_g']+budget['application_and_wipe_loss_g']==budget['per_fresh_assembly_g']
          and 3*budget['per_fresh_assembly_g']==budget['three_campaign_reservation_g']
          and budget['three_campaign_reservation_g']+budget['nominal_remaining_after_reservation_g']==85
          and not budget['dose_qualified'] and not budget['validation_trial_and_reset_budget_complete'])
    check('no_unearned_acceptance',record['owner_acceptance'] is None and not any(record[k] for k in
          ['staged_in_lab','initial_stock_credit','dispensing_qualified','sealing_qualified','compatibility_qualified','robot_use_qualified'])
          and not allocation['silicone_channel_requirement_satisfied'])
    paths=[Path(__file__),HERE/'silicone_grease_assets.json',HERE/'silicone_grease_sources.json',HERE/'check_weather_assets.py']
    result=dict(schema_version=1,passed=True,checks=checks,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in paths],
        resting_reference=supports[0],density_scenario_support=supports,
        scope='Static inferred package and nominal stock; no material flow, seal performance, lubrication or robot operation.',
        robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'silicone_grease_checks.json',result)
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':build()
