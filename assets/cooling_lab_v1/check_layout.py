"""Independent conservative layout checks. No dynamic safety or task credit.

Tests planar corridors against occupied furniture/wall volumes, exact imported
mesh bounds against supporting surfaces, and device opening sweeps against
external obstacles. Intended assembly contacts inside each device are outside
this checker. All simplifications are retained in the report.
"""
import json
import numpy as np
import trimesh
from shapely.geometry import LineString, Point, box
from geometry_tools import HERE, ROOT, sha, write_json


def bounds_overlap(a,b,tolerance=1e-5):
    return bool(np.all(np.minimum(a[1],b[1])-np.maximum(a[0],b[0])>tolerance))


def inspect(scene_path=None,output_path=None,quiet=False):
    p=scene_path or HERE/'scene.json';scene=json.loads(p.read_text());checks=[]
    def check(name,passed,**data):checks.append(dict(name=name,passed=bool(passed),**data))
    obstacles=scene['obstacles'];transit_height=scene['envelope']['transit_height_m']
    hand=json.loads((ROOT/scene['envelope']['hand_evidence']['path']).read_text())
    check('selected_hand_radius',scene['envelope']['transit_radius_m']>=hand['selected_body_hand_radius_m'])
    check('hand_envelope_identity',sha(ROOT/scene['envelope']['hand_evidence']['path'])==scene['envelope']['hand_evidence']['sha256'])
    # Only solids intersecting the declared standing-height volume obstruct
    # the planar sweep. All overhead solids remain in 3D opening checks.
    floor_obstacles=[o for o in obstacles if o['bounds_m'][0][2] < transit_height and o['bounds_m'][1][2] > 0]
    footprints=[(o,box(o['bounds_m'][0][0],o['bounds_m'][0][1],o['bounds_m'][1][0],o['bounds_m'][1][1])) for o in floor_obstacles]
    routes=[]
    for c in scene['corridors']:
        line=LineString(c['points_m']); corridor=line.buffer(c['width_m']/2,cap_style='flat',join_style='mitre')
        nearest=min([(line.distance(poly),o['id']) for o,poly in footprints])
        hits=[o['id'] for o,poly in footprints if corridor.intersection(poly).area>1e-6]
        sufficient=nearest[0]+1e-6>=scene['envelope']['transit_radius_m']+scene['envelope']['margin_m']
        row=dict(id=c['id'],label=c['label'],declared_width_m=c['width_m'],minimum_centerline_distance_m=nearest[0],nearest_obstacle=nearest[1],
                 corridor_obstructions=hits,provisional_transit_clear=sufficient,declared_corridor_clear=not hits)
        overhead=[o for o in obstacles if o['bounds_m'][0][2] > 0 and corridor.intersection(box(o['bounds_m'][0][0],o['bounds_m'][0][1],o['bounds_m'][1][0],o['bounds_m'][1][1])).area>1e-6]
        height=min((o['bounds_m'][0][2] for o in overhead),default=None)
        check('headroom_'+c['id'],height is None or height>=transit_height,minimum_overhead_m=height,required_height_m=transit_height,scope='Static authored envelope only')
        routes.append(row);check('corridor_'+c['id'],sufficient and not hits,**row)
    for space in scene['spaces']:
        x,y=space['center_m']
        area=Point(x,y).buffer(space['radius_m'],quad_segs=96) if space['kind']=='turn' else box(x-space['size_m'][0]/2,y-space['size_m'][1]/2,x+space['size_m'][0]/2,y+space['size_m'][1]/2)
        hits=[o['id'] for o,poly in footprints if area.intersection(poly).area>1e-6]
        check('space_'+space['id'],not hits,obstructions=hits)
    surface_map={s['id']:s for s in scene['support_surfaces']};asset_bounds={};loaded={}
    for a in scene['assets']:
        s=trimesh.load(ROOT/a['geometry'],force='scene');loaded[a['id']]=s
        check('identity_'+a['id'],sha(ROOT/a['geometry'])==a['geometry_sha256'] and sha(ROOT/a['source_artifact']['path'])==a['source_artifact']['sha256'] and a['scale']==[1,1,1])
        bounds=s.bounds+np.array(a['position_m']);asset_bounds[a['id']]=bounds
        if a['station'] in surface_map:
            surface=surface_map[a['station']];xy=surface['xy_bounds_m']
            check('support_'+a['id'],bounds[0,0]>=xy[0]-.001 and bounds[0,1]>=xy[1]-.001 and bounds[1,0]<=xy[2]+.001 and bounds[1,1]<=xy[3]+.001 and abs(bounds[0,2]-surface['top_m'])<.001,
                  geometry_bounds_m=bounds.tolist(),surface=surface['id'],capacity_validated=False)
    structure=trimesh.load(ROOT/scene['architecture']['path'],force='scene')
    check('architecture_identity',sha(ROOT/scene['architecture']['path'])==scene['architecture']['sha256'])
    for component in scene.get('authored_components',[]):
        if not component['check_separation']:continue
        vertices=[]
        for node in component['parts']:
            matrix,mesh=structure.graph[node];vertices.append(trimesh.transform_points(structure.geometry[mesh].vertices,matrix))
        vertices=np.concatenate(vertices);bounds=np.array([vertices.min(axis=0),vertices.max(axis=0)])
        check('component_bounds_'+component['id'],np.allclose(bounds,component['bounds_m'],atol=1e-6))
        asset_bounds['authored:'+component['id']]=bounds
        surface=surface_map[component['support']];xy=surface['xy_bounds_m']
        check('support_authored_'+component['id'],bounds[0,0]>=xy[0]-.001 and bounds[0,1]>=xy[1]-.001 and bounds[1,0]<=xy[2]+.001 and bounds[1,1]<=xy[3]+.001 and abs(bounds[0,2]-surface['top_m'])<.001,
              surface=surface['id'],geometry_bounds_m=bounds.tolist(),capacity_validated=False)
    ids=list(asset_bounds);overlaps=[]
    for i,key in enumerate(ids):
        for other in ids[i+1:]:
            if bounds_overlap(asset_bounds[key],asset_bounds[other]):overlaps.append([key,other])
    check('assets_and_authored_fixtures_separated',not overlaps,pairs_checked=len(ids)*(len(ids)-1)//2,overlaps=overlaps,method='Conservative axis-aligned boxes; intended internal assembly contacts excluded')
    state_reports=[]
    for state in scene['inspection_states']:
        a=next(a for a in scene['assets'] if a['id']==state['asset']);s=loaded[a['id']]
        vertices=[];part_vertices={}
        for node in s.graph.nodes_geometry:
            if node in state['parts']:
                matrix,mesh=s.graph[node];v=trimesh.transform_points(s.geometry[mesh].vertices,matrix);vertices.append(v);part_vertices[node]=v
        check('state_parts_'+state['id'],len(vertices)==len(state['parts']),matched=len(vertices),required=len(state['parts']))
        if not vertices:continue
        vertices=np.concatenate(vertices);offset=np.array(a['position_m']);norm=np.array(a['normalization_matrix'])
        pivot=np.array(state.get('pivot_m',[0,0,0]))+norm[:3,3]
        sweep_bounds=[];hits=set()
        for fraction in np.linspace(0,1,101):
            if state['kind']=='joint_tree':
                k=state['kinematics'];world={k.get('root_link','palm'):np.asarray(k.get('root_matrix',np.eye(4)))}
                for j in k['joints']:
                    t=np.asarray(j['origin_matrix']) if 'origin_matrix' in j else np.eye(4)
                    if 'origin_matrix' not in j:t[:3,3]=j['origin_m']
                    world[j['id']]=world[j['parent']]@t
                    if fraction*j['inspection_angle_rad']:world[j['id']]=world[j['id']]@trimesh.transformations.rotation_matrix(fraction*j['inspection_angle_rad'],j['axis'])
                parts=[]
                for name,pv in part_vertices.items():
                    link=k['part_links'][name];delta=norm@world[link]@np.linalg.inv(k['bind_world'][link])@np.linalg.inv(norm)
                    parts.append(trimesh.transform_points(pv,delta))
                v=np.concatenate(parts)
            elif state['kind']=='slide':v=vertices+fraction*state['maximum']*np.array(state['axis'])
            else:v=trimesh.transform_points(vertices,trimesh.transformations.rotation_matrix(fraction*state['maximum'],state['axis'],point=pivot))
            if not np.isfinite(v).all():raise ValueError('Nonfinite inspection geometry: '+state['id'])
            bounds=np.array([v.min(axis=0),v.max(axis=0)])+offset;sweep_bounds.append(bounds)
            for obstacle in obstacles:
                if obstacle['id']==a['station']:continue
                if bounds_overlap(bounds,np.array(obstacle['bounds_m'])):hits.add(obstacle['id'])
            for key,other in asset_bounds.items():
                if key!=a['id'] and bounds_overlap(bounds,other):hits.add(key)
        merged=np.array([np.min(sweep_bounds,axis=(0,1)),np.max(sweep_bounds,axis=(0,1))])
        row=dict(id=state['id'],sample_count=101,external_obstructions=sorted(hits),sweep_bounds_m=merged.tolist(),
                 own_device_internal_collisions_checked=False,continuous_collision_proof=False)
        state_reports.append(row);check('external_opening_'+state['id'],not hits,**row)
    # Geometry-only probes must stay explicitly unqualified for full acceptance.
    check('acceptance_not_inferred',scene['owner_acceptance'] is None and scene['manipulation_development_allowed'] is False and scene['envelope']['exact_hand_qualified'] is False)
    report=dict(passed=all(c['passed'] for c in checks),scope='Conservative static layout and sampled external opening checks only',
      scene_sha256=sha(p),checker_sha256=sha(__file__),checks=checks,routes=routes,opening_states=state_reports,
      full_humanoid_clearance_accepted=False,asset_fidelity_accepted=False,safe_use_certified=False,owner_acceptance=None,
      limitations=['Planar occupied boxes are conservative; opening sweeps sample 101 states and omit internal device contacts',
                  'Hand bound uses the official G1/FTP chain at restricted static transit poses; cameras, loads and dynamic motion are excluded',
                  'No dynamic walking, stopping, falling, balance, structural, ventilation or regulatory validation'])
    write_json(output_path or HERE/'layout_checks.json',report)
    if not quiet:print(json.dumps(dict(passed=report['passed'],checks=len(checks),failed=[c for c in checks if not c['passed']]),ensure_ascii=False,indent=2))
    return report


if __name__=='__main__':raise SystemExit(0 if inspect()['passed'] else 1)
