"""Check actual leftover stock length, original kit parts and supported storage."""
import itertools
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import trimesh
from geometry_tools import HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap,cable_clearance,minimum_discrete_bend_radius


def build():
    r=json.loads((HERE/'weather_remainders_assets.json').read_text());checks=[]
    def check(name,passed,**details):checks.append(dict(name=name,passed=bool(passed),**details))
    for ref in r['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    check('unqualified_scope',r['owner_acceptance'] is None and not r['initial_stock_credit'] and not r['robot_use_qualified'])
    parts=load_parts(r['geometry']);stored=json.loads((HERE/'weather_storage_assets.json').read_text());cart=load_parts(stored['geometry'])
    station=json.loads((HERE/'weather_station_assets.json').read_text());installed=load_parts(station['geometry'])
    for m in installed.values():m.apply_translation(-np.array(station['station_origin_world_m']))
    check('uses_same_cart_identity_and_pose',r['cart_identity']==stored['inventory_intent']['reuse_existing_cart_instance'] and r['cart_origin_m']==stored['cart_origin_m'])
    for n,m in parts.items():check('closed_connected_'+n,m.is_volume and len(m.split())==1)
    sources={};failures=[]
    for p in r['rigid_placements']:
        path=p['source_geometry']
        if path not in sources:sources[path]=load_parts(dict(path=path,sha256=sha(ROOT/path)))
        expected=sources[path][p['source_part']].copy();expected.apply_transform(p['source_to_storage']);actual=parts[p['part']]
        error=float(cKDTree(actual.vertices).query(expected.vertices)[0].max())
        if len(actual.faces)!=len(expected.faces) or error>2e-7:failures.append(dict(part=p['part'],surface_error_m=error))
    check('original_unused_kit_and_tray_surfaces_preserved',not failures,failures=failures)
    check('wind_two_unused_screws_and_supplied_key_retained_once',sorted(x['source_part'] for x in r['unused_kit_contents'] if x['kit']=='weather_wind')==['optional_wood_lag_1','optional_wood_lag_2','supplied_0050_hex_key_candidate'])
    shield=[x for x in r['unused_kit_contents'] if x['kit']=='weather_radiation_shield']
    check('shield_six_complete_ties_and_two_wall_screws_retained_once',len(shield)==14 and len({x['part'] for x in shield})==14 and all(sum(x.get('selected_tie')==i for x in shield)==2 for i in range(1,7)))
    for w in r['wires']:
        measured=float(np.linalg.norm(np.diff(w['points_m'],axis=0),axis=1).sum());total=sum(w['installed_cut_lengths_m'])+w['remaining_length_m']+w['material_loss_m']
        check('original_stock_length_conserved_'+w['id'],abs(measured-w['remaining_length_m'])<1e-9 and abs(total-w['source_total_length_m'])<1e-9,measured_remainder_m=measured,accounted_total_m=total)
        check('negative_extra_wire_rejected_'+w['id'],abs(total+.01-w['source_total_length_m'])>1e-9)
        clear=cable_clearance(w);check('nonlocal_wire_surface_separation_'+w['id'],clear['conservative_nonlocal_surface_gap_m']>0,**clear,selected_minimum_bend_radius_m=minimum_discrete_bend_radius(w['points_m']))
    def supported(mesh,support):
        bottom=float(mesh.bounds[0,2]);p=mesh.vertices[np.abs(mesh.vertices[:,2]-bottom)<2e-7]
        p=p[np.linspace(0,len(p)-1,min(25,len(p)),dtype=int)].copy();p[:,2]+=1e-4
        locations,rays,_=support.ray.intersects_location(p,np.tile([0,0,-1],(len(p),1)),multiple_hits=True)
        return all(len(locations[rays==i]) and abs(float(locations[rays==i,2].max())-bottom)<3e-7 for i in range(len(p)))
    check('ordinary_tray_supported_by_actual_lower_shelf',supported(parts['kit_tray__formed_tray'],cart['cart__lower_shelf']))
    for w in r['wires']:check('remaining_wire_supported_by_actual_lower_shelf_'+w['id'],supported(parts[w['part']],cart[w['storage_container']]))
    for item in r['unused_kit_contents']:check('unused_part_supported_by_actual_tray_floor_'+item['part'],supported(parts[item['part']],parts[item['storage_container']]))
    lifted=parts[r['wires'][0]['part']].copy();lifted.apply_translation([0,0,.01]);check('negative_floating_wire_rejected',not supported(lifted,cart['cart__lower_shelf']))
    pairs=0;hits=[]
    for (n,a),(q,b) in itertools.combinations(parts.items(),2):
        pairs+=1;v=overlap(a,b)
        if not np.isfinite(v) or abs(v)>.001:hits.append(dict(parts=[n,q],volume_mm3=v))
    check('all_new_contents_clear_each_other',not hits,pairs=pairs,intersections=hits)
    for context,others in [('existing_cart_and_contents',cart),('complete_station',installed)]:
        pairs=0;hits=[]
        for n,a in parts.items():
            for q,b in others.items():
                if q.endswith('_text'):continue
                pairs+=1;v=overlap(a,b)
                if not np.isfinite(v) or abs(v)>.001:hits.append(dict(parts=[n,q],volume_mm3=v))
        check('new_remainders_clear_'+context,not hits,pairs=pairs,intersections=hits)
    workspace=json.loads((HERE/'weather_workspace_checks.json').read_text())
    preview=trimesh.load(ROOT/workspace['robot_geometry']['path'],force='scene')
    check('source_robot_for_existing_pose_witnesses',sha(ROOT/workspace['robot_geometry']['path'])==workspace['robot_geometry']['sha256'])
    rig_path=ROOT/'assets/g1_sensor_rig_v1/rig.json';rig=json.loads(rig_path.read_text());rig_meshes={}
    for a in rig['attachments']:
        check('source_rig_'+a['id'],sha(ROOT/a['geometry_path'])==a['geometry_sha256'])
        rig_meshes[a['id']]=trimesh.load(ROOT/a['geometry_path'],force='scene').to_geometry()
    environment=trimesh.collision.CollisionManager()
    for n,m in parts.items():environment.add_object(n,m)
    pose_witnesses=[]
    for target in workspace['targets']:
        result=target['result']
        if not result['position_candidate']:continue
        robot=trimesh.collision.CollisionManager()
        for n,matrix in result['visual_transforms'].items():
            _,key=preview.graph[n];robot.add_object(n,preview.geometry[key],np.asarray(matrix))
        for n,matrix in result['rig_transforms'].items():robot.add_object('rig__'+n,rig_meshes[n],np.asarray(matrix))
        hit,names=robot.in_collision_other(environment,return_names=True)
        witness=dict(target=target['id'],visual_parts=len(result['visual_transforms']),rig_groups=len(result['rig_transforms']),intersections=[list(p) for p in sorted(names)])
        check('existing_complete_humanoid_pose_clear_of_remainders_'+target['id'],not hit,**witness);pose_witnesses.append(witness)
    failed=[c['name'] for c in checks if not c['passed']]
    refs=[Path(__file__),HERE/'weather_remainders_assets.json',HERE/'weather_storage_assets.json',HERE/'weather_station_assets.json',HERE/'weather_workspace_checks.json',rig_path,HERE/'check_weather_assets.py']
    result=dict(schema_version=1,passed=not failed,failed=failed,checks=checks,existing_static_pose_witnesses=pose_witnesses,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        scope='Actual lower-shelf/tray support, original kit surfaces, source wire length and cross-component clearance. No cutting process, holding force, gravity settling, cart motion or robot execution.',owner_acceptance=None,robot_use_qualified=False)
    write_json(HERE/'weather_remainders_checks.json',result);print(json.dumps(dict(passed=not failed,checks=len(checks),parts=len(parts),failed=failed)))
    if failed:raise AssertionError(failed)


if __name__=='__main__':build()
