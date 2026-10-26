"""Check exported container topology, stock mass and cap inspection geometry."""
import itertools
import json
from pathlib import Path
import numpy as np
from shapely.geometry import MultiPoint, Point
import trimesh
from geometry_tools import HERE, ROOT, sha, write_json
from check_weather_assets import load_parts, overlap


def build():
    record=json.loads((HERE/'mast_grease_assets.json').read_text())
    source=json.loads((HERE/'mast_grease_sources.json').read_text());checks=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for ref in record['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    parts=load_parts(record['geometry']);solids={n:m for n,m in parts.items() if not n.endswith('_text')}
    check('exact_physical_groups',set(itertools.chain.from_iterable(record['groups'].values()))==set(parts) and len(parts)==5)
    for n,m in solids.items():check('connected_closed_'+n,m.is_volume and len(m.split())==1)
    for n,m in parts.items():
        row=next(r for r in record['geometry']['part_records'] if r['id']==n)
        check('exported_bounds_'+n,np.allclose(m.bounds,row['bounds_m'],atol=2e-8))
    scene=trimesh.util.concatenate(list(solids.values()))
    check('inferred_not_manufacturer_envelope',np.allclose(scene.extents,[.054,.032,.162],atol=3e-6,rtol=0)
        and not source['manufacturer_facts']['container_dimensions_published_in_inspected_primary_sources'],
        actual_m=scene.extents.tolist(),tessellation_tolerance_m=.000003)
    shell=solids['tube_shell_and_sealed_tail'];cap=solids['ribbed_hollow_cap'];stock=solids['nominal_85g_grease_stock']
    check('real_nozzle_bore_and_wall',not shell.contains([[0,0,.009],[.0078,0,.009]]).any() and shell.contains([[.0095,0,.009]])[0])
    check('real_tail_hanging_hole',not shell.ray.intersects_any([[0,-.01,.1574]],[[0,1,0]])[0]
        and shell.ray.intersects_any([[.02,-.01,.1574]],[[0,1,0]])[0])
    check('sealed_tail_above_cavity',shell.contains([[0,0,.152],[0,0,.154]]) .all())
    check('cap_is_hollow_with_closed_base',not cap.contains([[0,0,.010],[.011,0,.010]]).any()
        and cap.contains([[0,0,.001],[.014,0,.010]]).all())
    check('stock_mass_from_actual_exported_volume',abs(stock.volume*.89*1e6-85)<.1,
        actual_volume_ml=float(stock.volume*1e6),approximate_mass_g=float(stock.volume*.89*1e6),
        tolerance_g=.1,basis='Tessellation/nominal density consistency, not a filling tolerance or metrology result.')
    check('stock_fits_below_heat_seal',stock.bounds[1,2]<.150 and stock.bounds[0,2]>.007
        and record['inferred_cavity_volume_m3']>stock.volume)
    collisions=[]
    for (a,x),(b,y) in itertools.combinations(solids.items(),2):
        volume=overlap(x,y);collisions.append(dict(parts=[a,b],overlap_mm3=volume))
    check('distinct_material_volumes',all(abs(r['overlap_mm3'])<.01 for r in collisions),pairs=collisions)
    shifted=stock.copy();shifted.apply_translation([.003,0,0])
    check('negative_stock_through_wall_detected',overlap(shifted,shell)>1)
    opened={n:m.copy() for n,m in solids.items()}
    for n in record['groups']['cap']:opened[n].apply_translation(record['inspection']['cap_translation_m'])
    check('separated_cap_is_clear',all(abs(overlap(opened[n],opened[other]))<.01
        for n in record['groups']['cap'] for other in ['tube_shell_and_sealed_tail','nominal_85g_grease_stock']))
    check('separation_is_not_screw_motion','not an unscrewing path' in record['inspection']['scope'])
    # Upright capped stock rests on the actual cap base. Symmetric geometry
    # and broad density ranges are sufficient for this static support screen.
    contact=scene.vertices[scene.vertices[:,2]<1e-7];polygon=MultiPoint(contact[:,:2]).convex_hull
    density={'tube_shell_and_sealed_tail':1200.,'ribbed_hollow_cap':950.,
             'inferred_cap_sealing_annulus':1100.,'nominal_85g_grease_stock':890.}
    masses=np.array([m.volume*density[n] for n,m in solids.items()]);centres=np.array([m.center_mass for m in solids.values()])
    com=np.sum(masses[:,None]*centres,axis=0)/masses.sum();margin=polygon.boundary.distance(Point(com[:2]))
    check('actual_cap_base_support',abs(scene.bounds[0,2])<1e-7 and polygon.contains(Point(com[:2])) and margin>.010,
        inferred_com_m=com.tolist(),support_margin_m=margin,scope='Rigid static upright reference; no squeeze, fall or settling simulation.')
    check('negative_off_support_com_detected',not polygon.contains(Point([.1,0])))
    allocation=record['material_allocation']
    check('silicone_requirement_remains_separate',not source['manufacturer_facts']['contains_silicone']
        and not allocation['silicone_channel_requirement_satisfied'])
    budget=record['application_budget']
    check('consumption_marked_as_inventory_inference',allocation['per_application_mass_g']==2
        and allocation['mass_basis']=='inferred_planning_reservation' and not allocation['campaign_consumption_accepted'])
    check('application_and_campaign_material_balance',0<budget['nominal_retained_film_g']<2
        and abs(budget['nominal_retained_film_g']+budget['application_and_wipe_loss_allowance_g']-2)<1e-10
        and budget['three_campaign_reservation_g']==3*allocation['per_application_mass_g']
        and budget['three_campaign_reservation_g']+budget['nominal_remaining_after_reservation_g']==85)
    check('no_unearned_acceptance',record['owner_acceptance'] is None and not any(record[k] for k in
        ['staged_in_lab','initial_stock_credit','dispensing_qualified','sealing_qualified','compatibility_qualified','robot_use_qualified']))
    refs=[Path(__file__),HERE/'mast_grease_assets.json',HERE/'mast_grease_sources.json',HERE/'check_weather_assets.py']
    report=dict(schema_version=1,passed=True,checks=checks,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        resting_reference=dict(to_support_plane=np.eye(4).tolist(),support_margin_m=margin,
            estimated_total_mass_kg=float(masses.sum()),density_hypotheses_kg_m3=density),
        scope='Static container and nominal inventory only; no material flow, sealing, lubrication or robot operation.',
        robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'mast_grease_checks.json',report);print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':build()
