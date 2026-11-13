"""Validate the low-mast asset context; retain finite failures explicitly."""
import itertools
import json
from pathlib import Path
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from shapely.geometry import MultiPoint,Polygon
from geometry_tools import HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap
from check_u30 import wire_clearance
from build_weather_station import pose
from weather_station_retention import slab_projection
from weather_station_routes import length


def build():
    r=json.loads((HERE/'weather_preparation_assets.json').read_text());station=json.loads((HERE/'weather_station_assets.json').read_text())
    stock=json.loads((HERE/'long_cable_tie_assets.json').read_text());checks=[]
    def check(name,passed,**details):checks.append(dict(name=name,passed=bool(passed),**details))
    for ref in r['source_artifacts']+stock['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    parts=load_parts(r['geometry']);original=load_parts(station['geometry']);physical={n:m for n,m in parts.items() if not n.endswith('_text')}
    check('unaccepted_partial_context',r['owner_acceptance'] is None and not any(r[k] for k in ['staged_in_lab','initial_stock_credit','installation_qualified','robot_use_qualified']))
    for n,m in physical.items():check('single_closed_solid_'+n,m.is_volume and len(m.split())==1)
    cache={};bad=[]
    for p in r['rigid_placements']:
        path=p['source_geometry']
        if path not in cache:cache[path]=load_parts(dict(path=path,sha256=sha(ROOT/path)))
        expected=cache[path][p['source_part']].copy();expected.apply_transform(p['source_to_preparation'])
        actual=parts[p['part']];distance=float(cKDTree(actual.vertices).query(expected.vertices)[0].max())
        if len(expected.faces)!=len(actual.faces) or distance>1e-6:bad.append(dict(part=p['part'],distance_m=distance))
    check('rigid_source_surfaces_preserved',not bad,failures=bad,count=len(r['rigid_placements']))
    represented={p['part'] for p in r['rigid_placements'] if p['part'] in original}
    dispositions={p['part'] for p in r['original_station_component_dispositions']}
    check('every_original_component_has_an_explicit_disposition',represented|dispositions==set(original),original_count=len(original),represented=len(represented),other_dispositions=len(dispositions))
    check('upright_upper_mast_rests_at_ground',abs(parts['support__upper_mast_with_dimple_and_crossarm_holes'].bounds[0,2])<1e-6 and np.allclose(np.asarray(r['upper_cluster_to_preparation'])[:3,2],[0,0,1]))
    allowed={frozenset(['rs3__rs3_tie_rod_'+side,'rs3__rs3_knurled_nut_'+side]) for side in ['left','right']}
    hits=[];retained_nominal=[];pairs=0
    for (n,m),(q,b) in itertools.combinations(physical.items(),2):
        pairs+=1;v=overlap(m,b)
        if frozenset([n,q]) in allowed:
            retained_nominal.append(dict(parts=[n,q],volume_mm3=v));continue
        if not np.isfinite(v) or abs(v)>.001:hits.append(dict(parts=[n,q],volume_mm3=v))
    check('complete_partial_context_has_no_new_material_intersections',not hits,pairs=pairs,intersections=hits,
        retained_source_thread_envelope_intersections=retained_nominal,
        scope='Two original RS3 rod/nut nominal-thread envelope overlaps remain explicit; no new overlap is excluded.')
    wires=[]
    for lead in r['routed_leads']:
        result=wire_clearance(lead);wires.append(dict(id=lead['id'],**result))
        check('free_lead_length_bend_and_separation_'+lead['id'],abs(result['length_m']-.5)<1e-8 and result['minimum_discrete_bend_radius_m']>.0045 and result['conservative_nonlocal_surface_gap_m']>0,**result)
        check('free_lead_endpoints_'+lead['id'],np.allclose(np.asarray(lead['points_m'])[[0,-1]],lead['endpoints_m'],atol=1e-10))
    for lead in station['routed_leads']:
        if lead['id'] not in ['temperature_sensor_lead','wind_sensor_lead']:continue
        path=trimesh.transform_points(lead['points_m'],r['upper_cluster_to_preparation'])
        check('complete_source_sensor_lead_'+lead['id'],abs(length(path)-lead['length_m'])<1e-8,length_m=length(path))
    tie_stock=next(iter(load_parts(stock['geometry']).values()))
    check('long_tie_source_envelope',np.allclose(tie_stock.extents,[.390,.0058,.0081],atol=1e-7),extents_m=tie_stock.extents.tolist())
    check('long_tie_real_feed_passage',not tie_stock.ray.intersects_any([[0,-.010,0]],[[0,1,0]])[0])
    check('long_tie_solid_head_sidewall',tie_stock.ray.intersects_any([[.003,-.010,0]],[[0,1,0]])[0])
    for t in r['temporary_ties']:
        matrix=np.asarray(t['plane_to_preparation']);p=np.vstack([slab_projection(parts[n],matrix) for n in t['enclosed_parts']]);c=t['containing_circle']
        maximum=float(np.linalg.norm(p-np.asarray(c['centre_plane_m']),axis=1).max())
        check('temporary_bundle_bound_'+t['id'],maximum<=c['radius_m']+1e-8 and 2*maximum<t['conservative_bundle_diameter_m'],diameter_m=2*maximum)
        # Close at the feed-head point before the full uncut tail. A tail must
        # not become an artificial edge of the claimed enclosure polygon.
        path=np.asarray(t['strap_centreline_plane_m']);head=np.asarray(t['head_origin_plane_m']);end=int(np.argmin(np.linalg.norm(path-head,axis=1)))
        check('temporary_strap_surrounds_actual_bundle_'+t['id'],Polygon(path[:end+1]).buffer(.0008).covers(MultiPoint(p).convex_hull))
        size=.300 if t['product'].endswith('111-01975') else .390;head_allowance=.0069 if size==.300 else .0071
        check('temporary_full_stock_retained_'+t['id'],not t['flush_cut'] and abs(t['retained_developed_length_m']-size)<1e-10 and t['cutoff_developed_length_m']==0 and t['protruding_uncut_tail_length_m']>.01 and abs(length(path)+head_allowance-size)<1e-9)
    brace=next(t for t in r['temporary_ties'] if t['id']=='temporary_brace')
    check('negative_short_tie_bundle_bound_rejected',brace['containing_circle']['diameter_m']>.080,actual_diameter_m=brace['containing_circle']['diameter_m'],prior_limit_m=.080)
    tray=parts['free_plug_tray__formed_tray'];floor=float(r['tray_origin_m'][2]+.0012)
    for plug in r['free_plugs']:
        body=parts[plug['id']+'_plug__modular_plug_body_and_latch'];bottom=body.vertices[np.abs(body.vertices[:,2]-body.bounds[0,2])<1e-7]
        starts=bottom+[0,0,.00005];directions=np.tile([0,0,-1],(len(starts),1))
        points,indices,_=tray.ray.intersects_location(starts,directions,multiple_hits=False)
        check('actual_tray_support_'+plug['id'],abs(body.bounds[0,2]-floor)<1e-7 and len(set(indices))==len(bottom) and np.allclose(points[:,2],floor,atol=1e-7),bottom_samples=len(bottom))
    # Preserve the first full-cluster lowering as a concrete failing example.
    bad=original['routed__temperature_sensor_lead'].copy();bad.apply_translation(-np.asarray(station['station_origin_world_m'])+[.150,.043,-1.050])
    collision=overlap(bad,parts['support__leg_3'])
    check('negative_unadjusted_low_cluster_hits_tripod_leg',collision>100,overlap_mm3=collision)
    regressions=json.loads((HERE/'weather_workspace_regressions.json').read_text());ref=regressions['robot_geometry']
    check('failed_pose_robot_geometry_pinned',sha(ROOT/ref['path'])==ref['sha256']);robot=trimesh.load(ROOT/ref['path'],force='scene')
    for witness in regressions['witnesses']:
        key=robot.graph[witness['robot_visual_part']][1];mesh=robot.geometry[key].copy();mesh.apply_transform(witness['visual_to_preparation'])
        if witness['obstacle_part']:
            collision=trimesh.collision.CollisionManager();collision.add_object('failed_hand',mesh)
            hit=collision.in_collision_single(parts[witness['obstacle_part']])
            check('negative_original_palm_allowance_'+witness['id'],hit,robot_part=witness['robot_visual_part'],obstacle_part=witness['obstacle_part'])
        else:check('negative_unraised_unused_hand_crosses_ground',mesh.bounds[0,2]<-.05,minimum_z_m=float(mesh.bounds[0,2]))
    refs=[Path(__file__),HERE/'weather_preparation_assets.json',HERE/'weather_station_assets.json',HERE/'long_cable_tie_assets.json',HERE/'weather_workspace_regressions.json',HERE/'check_weather_assets.py',HERE/'check_u30.py',HERE/'weather_station_retention.py']
    failed=[c['name'] for c in checks if not c['passed']]
    report=dict(schema_version=1,passed=not failed,checks=checks,failed=failed,cable_clearances=wires,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        scope='Static partial low-mast context with real complete sensor leads and ordinary uncut temporary ties. Not a complete inventory state, sequence, load qualification or single-robot joining result.',
        robot_use_qualified=False,installation_qualified=False,owner_acceptance=None)
    write_json(HERE/'weather_preparation_checks.json',report);print(json.dumps(dict(passed=not failed,checks=len(checks),parts=len(parts),failed=failed)))
    if failed:raise AssertionError('Failed low-mast checks: '+', '.join(failed))


if __name__=='__main__':build()
