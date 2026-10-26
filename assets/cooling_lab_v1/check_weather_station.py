"""Verify the static integrated weather candidate, without crediting assembly."""
import itertools
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import MultiPoint,Polygon
import trimesh
from geometry_tools import HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap
from check_u30 import wire_clearance
from weather_station_retention import slab_projection
from weather_station_routes import network_routes,length
from build_weather_assets import cable_mesh


def build():
    r=json.loads((HERE/'weather_station_assets.json').read_text());tie=json.loads((HERE/'cable_tie_assets.json').read_text());checks=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for ref in r['source_artifacts']+tie['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    check('unaccepted_static_scope',r['owner_acceptance'] is None and not any(r[k] for k in ['staged_in_lab','initial_stock_credit','installation_qualified','electrical_qualified','structural_load_qualified','robot_use_qualified']))
    parts=load_parts(r['geometry']);origin=np.asarray(r['station_origin_world_m'])
    for m in parts.values():m.apply_translation(-origin)
    physical={n:m for n,m in parts.items() if not n.endswith('_text')}
    for n,m in physical.items():check('closed_connected_'+n,m.is_volume and len(m.split())==1)
    # Preserve the real source surfaces, not only their bounding boxes.
    sources={};preserved=[]
    for placement in r['rigid_placements']:
        path=placement['source_geometry']
        if path not in sources:sources[path]=load_parts(dict(path=path,sha256=sha(ROOT/path)))
        expected=sources[path][placement['source_part']].copy();expected.apply_transform(placement['source_to_station'])
        actual=parts[placement['part']];distance=cKDTree(actual.vertices).query(expected.vertices)[0].max()
        if not(len(actual.faces)==len(expected.faces) and distance<1e-6):preserved.append(dict(part=placement['part'],distance_m=float(distance)))
    check('source_surfaces_preserved_by_recorded_rigid_poses',not preserved,failures=preserved,count=len(r['rigid_placements']))
    hits=[];pairs=0
    for (n,m),(q,b) in itertools.combinations(physical.items(),2):
        group=n.split('__')[0]
        if group==q.split('__')[0] and group not in ['routed','retention']:continue
        pairs+=1;v=overlap(m,b)
        if not np.isfinite(v) or abs(v)>.001:hits.append(dict(parts=[n,q],volume_mm3=v))
    check('cross_component_cable_and_tie_domains_do_not_intersect',not hits,pairs=pairs,intersections=hits,
        scope='Intragroup source components retain their existing checks and declared nominal thread overlaps; all distinct routed leads and ties are checked here.')
    wires=[]
    for lead in r['routed_leads']:
        result=wire_clearance(lead);wires.append(dict(id=lead['id'],**result))
        check('source_length_'+lead['id'],abs(result['length_m']-lead['length_m'])<1e-8,actual_m=result['length_m'])
        check('continuous_bend_and_nonlocal_gap_'+lead['id'],result['minimum_discrete_bend_radius_m']>3*lead['radius_m'] and result['conservative_nonlocal_surface_gap_m']>0,**result)
        check('endpoints_'+lead['id'],np.allclose(np.asarray(lead['points_m'])[[0,-1]],lead['endpoints_m'],atol=1e-10))
        if 'coil' in lead:
            gap=float(np.min(np.asarray(lead['coil']['points_m'])[:,2])-lead['radius_m']-physical['u30__outer_case'].bounds[1,2])
            check('excess_coil_outside_one_foot_case_exclusion_'+lead['id'],gap>.3048,vertical_lower_bound_m=gap)
        else:check('drip_below_case_entry_'+lead['id'],lead['drip_lowest_z_m']<r['selected_layout']['logger_origin_m'][2])
    stock=next(iter(load_parts(tie['geometry']).values()))
    check('stock_tie_envelope',np.allclose(stock.extents,[.300,.0058,.0078],atol=1e-7),actual_m=stock.extents.tolist())
    check('stock_head_has_open_feed_passage',not stock.ray.intersects_any([[0,-.010,0]],[[0,1,0]])[0])
    check('stock_head_has_solid_sidewall',stock.ray.intersects_any([[.003,-.010,0]],[[0,1,0]])[0])
    check('negative_filled_feed_passage_rejected',trimesh.creation.box([.007,.0058,.0078]).ray.intersects_any([[0,-.010,0]],[[0,1,0]])[0])
    check('fourteen_ordinary_ties',len(r['retention_ties'])==14)
    for t in r['retention_ties']:
        matrix=np.asarray(t['plane_to_station']);p=np.vstack([slab_projection(parts[n],matrix) for n in t['enclosed_parts']])
        c=t['containing_circle'];actual=float(np.linalg.norm(p-np.asarray(c['centre_plane_m']),axis=1).max())
        check('conservative_bundle_bound_'+t['id'],actual<=c['radius_m']+1e-10 and 2*actual<=.080,diameter_m=2*actual)
        contour=Polygon(t['strap_centreline_plane_m']).buffer(.0007);support=MultiPoint(p).convex_hull
        check('strap_surrounds_actual_support_'+t['id'],contour.covers(support))
        check('source_stock_balance_'+t['id'],abs(length(t['strap_centreline_plane_m'])+.0069-t['retained_developed_length_m'])<1e-9 and abs(t['retained_developed_length_m']+t['cutoff_developed_length_m']-.300)<1e-9 and t['cutoff_developed_length_m']>0)
        check('negative_displaced_strap_cannot_retain_'+t['id'],not Polygon(np.asarray(t['strap_centreline_plane_m'])+[1,0]).buffer(.0007).covers(support))
    check('removed_plugs_are_tracked',sorted(x['source_part'] for x in r['detached_channel_plugs'])==['unused_channel_plug_2','unused_channel_plug_6'] and all('u30__'+x['source_part'] not in parts for x in r['detached_channel_plugs']))
    weather=json.loads((HERE/'weather_assets.json').read_text());probe=next(x for x in weather['items'] if x['id']=='onset_sthb_m002')
    wind=json.loads((HERE/'wind_lead_assets.json').read_text());bad=network_routes(r,probe,wind,clear_splice=False)[0]
    m=cable_mesh(bad['points_m'],bad['radius_m']);volume=sum(overlap(m,b) for n,b in physical.items() if 'mast_splice' in n)
    check('negative_unrouted_network_lead_hits_splice_hardware',volume>10,overlap_mm3=volume)
    refs=[Path(__file__),HERE/'weather_station_assets.json',HERE/'cable_tie_assets.json',HERE/'check_u30.py']
    report=dict(schema_version=1,passed=True,checks=checks,cable_clearances=wires,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        scope='Static source-preserving integration and ordinary retention geometry only. No gravity-settled cables, strain, ratchet, friction, preload, grounding, weatherproofing, whole-body access or robot operation is qualified.',
        missing=r['missing'],installation_qualified=False,electrical_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'weather_station_checks.json',report);print(json.dumps(dict(passed=True,checks=len(checks),parts=len(parts),cross_pairs=pairs)))


if __name__=='__main__':build()
