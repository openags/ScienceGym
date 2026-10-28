"""Physical storage, source preservation and full-station static clearance."""
import itertools
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from geometry_tools import HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap


def build():
    r=json.loads((HERE/'weather_storage_assets.json').read_text())
    station=json.loads((HERE/'weather_station_assets.json').read_text());checks=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for ref in r['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    check('scope_remains_unaccepted',r['owner_acceptance'] is None and not r['staged_in_lab'] and not r['initial_stock_credit'] and not r['robot_use_qualified'])
    check('reuses_existing_cart_without_reassigning_lab_trays',r['inventory_intent']['reuse_existing_cart_instance']=='utility_cart' and not r['inventory_intent']['existing_lab_trays_reassigned'] and len(r['inventory_intent']['additional_tray_candidates'])==2)
    parts=load_parts(r['geometry']);physical={n:m for n,m in parts.items() if not n.endswith('_text')}
    sources={};errors=[]
    for p in r['rigid_placements']:
        path=p['source_geometry']
        if path not in sources:sources[path]=load_parts(dict(path=path,sha256=sha(ROOT/path)))
        m=sources[path][p['source_part']].copy();m.apply_transform(p['source_to_storage']);actual=parts[p['part']]
        delta=float(cKDTree(actual.vertices).query(m.vertices)[0].max())
        if len(actual.faces)!=len(m.faces) or delta>2e-7:errors.append(dict(part=p['part'],surface_error_m=delta))
    check('cart_trays_and_plugs_preserve_original_surfaces',not errors,failures=errors)
    for n,m in physical.items():
        # The source cart contains documented overlapping ribs/legs; its
        # existing mechanical reconstruction is reused, not requalified.
        if not n.startswith('cart__'):check('connected_solid_'+n,m.is_volume and len(m.split())==1)
    pairs=0;hits=[]
    for (n,m),(q,b) in itertools.combinations(physical.items(),2):
        if n.startswith('cart__') and q.startswith('cart__'):continue
        pairs+=1;v=overlap(m,b)
        if not np.isfinite(v) or abs(v)>.001:hits.append(dict(parts=[n,q],volume_mm3=v))
    check('storage_contents_trays_and_cart_clear',not hits,pairs=pairs,intersections=hits)
    installed=load_parts(station['geometry']);origin=np.asarray(station['station_origin_world_m'])
    for m in installed.values():m.apply_translation(-origin)
    hits=[];pairs=0
    for n,m in physical.items():
        for q,b in installed.items():
            if q.endswith('_text'):continue
            pairs+=1;v=overlap(m,b)
            if not np.isfinite(v) or abs(v)>.001:hits.append(dict(parts=[n,q],volume_mm3=v))
    check('complete_station_and_cart_clear',not hits,pairs=pairs,intersections=hits)
    def supported(mesh,support):
        bottom=float(mesh.bounds[0,2]);points=mesh.vertices[np.abs(mesh.vertices[:,2]-bottom)<2e-7]
        # Actual contact vertices, ray-cast through the real supporting mesh.
        points=points[np.linspace(0,len(points)-1,min(9,len(points)),dtype=int)].copy();points[:,2]+=1e-4
        locations,rays,_=support.ray.intersects_location(points,np.tile([0,0,-1],(len(points),1)),multiple_hits=True)
        for i in range(len(points)):
            z=locations[rays==i,2]
            if len(z)==0 or abs(float(z.max())-bottom)>3e-7:return False
        return True
    for item in r['cutoffs']+r['removed_plugs']:
        check('actual_floor_support_'+item['part'],supported(parts[item['part']],parts[item['storage_container']]))
    for kind in ['cutoffs','plugs']:
        check('tray_supported_on_cart_'+kind,supported(parts[kind+'_tray__formed_tray'],parts['cart__upper_shelf']))
    displaced=parts[r['cutoffs'][0]['part']].copy();displaced.apply_translation([0,0,.01])
    check('negative_floating_cutoff_rejected',not supported(displaced,parts['cutoffs_tray__formed_tray']))
    check('all_removed_plugs_retained_once',sorted(x['source_part'] for x in r['removed_plugs'])==sorted(x['source_part'] for x in station['detached_channel_plugs']) and len(set(x['part'] for x in r['removed_plugs']))==3)
    check('all_cutoffs_retained_once',sorted(x['source_tie'] for x in r['cutoffs'])==sorted(x['id'] for x in station['retention_ties']) and len(set(x['part'] for x in r['cutoffs']))==14)
    for item in r['cutoffs']:
        mesh=parts[item['part']];p=np.c_[mesh.vertices,np.ones(len(mesh.vertices))]@np.linalg.inv(item['source_to_storage']).T
        check('original_stock_cut_plane_'+item['source_tie'],abs(p[:,0].min()-item['source_cut_plane_x_m'])<2e-7 and abs(p[:,0].max()-.2965)<2e-7)
        check('actual_cutoff_and_retained_length_balance_'+item['source_tie'],abs(np.ptp(p[:,0])-item['developed_length_m'])<2e-7 and abs(item['developed_length_m']+item['retained_developed_length_m']-.300)<1e-9)
    world_bounds=np.array([np.min([m.bounds[0] for m in physical.values()],axis=0),np.max([m.bounds[1] for m in physical.values()],axis=0)])+origin
    check('cart_inside_existing_outdoor_area',world_bounds[0,0]>0 and world_bounds[1,0]<12 and world_bounds[0,1]>12 and world_bounds[1,1]<20 and abs(world_bounds[0,2])<2e-7,world_bounds_m=world_bounds.tolist())
    refs=[Path(__file__),HERE/'weather_storage_assets.json',HERE/'weather_station_assets.json',HERE/'check_weather_assets.py']
    result=dict(schema_version=1,passed=True,checks=checks,source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        scope='Static final storage candidate: source-preserving cart, two catalog trays, fourteen original stock cut tails and three original plugs; actual floor support and whole-station clearance. No settling, gravity/rolling stability, pushing, hand access or cleanup execution.',
        robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'weather_storage_checks.json',result);print(json.dumps(dict(passed=True,checks=len(checks),parts=len(parts))))


if __name__=='__main__':build()
