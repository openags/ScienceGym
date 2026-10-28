"""Check initial stock identities, source surfaces, support and room clearance."""
import itertools
import json
from pathlib import Path
import numpy as np
import trimesh
from scipy.spatial import cKDTree, ConvexHull
from geometry_tools import HERE, ROOT, sha, write_json
from review_mesh_io import load_parts
from check_weather_assets import overlap


def broad(a, b):
    return bool(np.all(np.minimum(a[1],b[1])-np.maximum(a[0],b[0])>2e-7))


def build():
    record=json.loads((HERE/'weather_initial_stock_assets.json').read_text())
    scene=json.loads((HERE/'scene.json').read_text())
    binding=json.loads((HERE/'weather_scene_binding.json').read_text())
    parts=load_parts(record['geometry']); checks=[]
    def check(name, passed, **details):checks.append(dict(name=name,passed=bool(passed),**details))
    for ref in record['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    check('candidate_does_not_claim_acceptance',record['owner_acceptance'] is None and not any(record[k] for k in ['initial_inventory_complete','initial_stock_credit','robot_use_qualified']))
    expected={e['id'] for e in binding['physical_entities'] if e['id']!='weather_ground_design'}|{'weather_temporary_leg','weather_temporary_brace'}
    check('all_portable_weather_identities_once',set(record['physical_identity_ids'])==expected and len(record['physical_identity_ids'])==len(expected),count=len(expected))
    placements={p['part']:p for p in record['placements']}
    derived={p['part']:p for p in record['leads'] if p.get('authored_shape')}
    check('every_stock_mesh_has_a_single_owner',not set(placements)&set(derived) and set(placements)|set(derived)==set(parts)
          and len(placements)==len(record['placements']))
    cache={};errors=[]
    for name,p in placements.items():
        ref=p['source_geometry'];path=ref['path']
        if path not in cache:cache[path]=load_parts(ref)
        m=cache[path][p['source_part']].copy();m.apply_transform(p['source_to_world']);actual=parts[name]
        distance=float(cKDTree(actual.vertices).query(m.vertices)[0].max())
        matrix=np.asarray(p['source_to_world'])[:3,:3]
        if distance>2e-6 or len(actual.faces)!=len(m.faces) or not np.allclose(matrix.T@matrix,np.eye(3),atol=1e-10):errors.append(dict(part=name,distance_m=distance))
    check('all_source_surfaces_preserved_without_scaling',not errors,parts=len(placements),errors=errors)
    # Source counts are checked independently of the output owner list.
    source_expectations={'tripod_assets':62,'weather_anchoring_assets':49,'wind_sensor_assets':22,'wind_lead_assets':14,
        'wind_kit_assets':3,'u30_assets':143,'u30_ground_assets':7}
    for stem,count in source_expectations.items():
        ref=json.loads((HERE/(stem+'.json')).read_text())['geometry'];actual=[p['source_part'] for p in placements.values() if p['source_geometry']['path']==ref['path']]
        actual += [p['source_part'] for p in derived.values() if p['source_geometry']['path']==ref['path']]
        check('complete_original_parts_'+stem,len(actual)==count and set(actual)=={p['id'] for p in ref['part_records']},expected=count,actual=len(actual))
    ties=[g for g in record['groups'] if g['state_basis']=='full_uncut_unfastened_tie']
    check('fifteen_300mm_and_one_390mm_ties',len(ties)==16 and sum(g['identity']!='weather_temporary_brace' for g in ties)==15
        and all(abs(np.ptp(np.asarray(g['bounds_m']),axis=0).max()-(.390 if g['identity']=='weather_temporary_brace' else .300))<2e-6 for g in ties))
    for lead in record['leads']:
        length=float(np.linalg.norm(np.diff(lead['points_m'],axis=0),axis=1).sum())
        check('complete_uncut_length_'+lead['id'],not lead['cut'] and abs(length-lead['length_m'])<1e-7,length_m=length)
    surfaces={s['id']:s for s in record['support_surfaces']};support_results=[]
    for group in record['groups']:
        s=surfaces[group['support']];bounds=np.array([parts[n].bounds for n in group['parts']]);lo=bounds[:,0].min(0);hi=bounds[:,1].max(0)
        x0,y0,x1,y1=s['xy_bounds_m'];contained=lo[0]>=x0-2e-6 and lo[1]>=y0-2e-6 and hi[0]<=x1+2e-6 and hi[1]<=y1+2e-6
        on_plane=abs(lo[2]-s['top_m'])<2e-6
        support_results.append(dict(group=group['id'],support=s['id'],bounds_m=[lo.tolist(),hi.tolist()],inside=bool(contained),touches_plane=bool(on_plane)))
    check('every_rigid_group_on_existing_support',all(x['inside'] and x['touches_plane'] for x in support_results),groups=support_results)
    for name,lead in derived.items():
        s=surfaces[lead['support']];b=parts[name].bounds;x0,y0,x1,y1=s['xy_bounds_m']
        check('lead_inside_shelf_'+name,b[0,0]>=x0 and b[0,1]>=y0 and b[1,0]<=x1 and b[1,1]<=y1 and b[0,2]>=s['top_m']-2e-6,bounds_m=b.tolist(),settled_dynamics_qualified=False)
    # A rigid supplier assembly keeps its source contacts. The folded frame
    # has different transforms per link, so every newly affected pair is tested.
    hits=[];tested=0;inherited=[]
    for (a,ma),(b,mb) in itertools.combinations(parts.items(),2):
        if not broad(ma.bounds,mb.bounds):continue
        pa,pb=placements.get(a),placements.get(b)
        if pa and pb and pa['group']==pb['group'] and np.allclose(pa['source_to_world'],pb['source_to_world'],atol=1e-10):continue
        tested+=1
        if not ma.is_volume or not mb.is_volume:
            cm=trimesh.collision.CollisionManager();cm.add_object('a',ma)
            if cm.in_collision_single(mb):hits.append(dict(parts=[a,b],surface_intersection=True))
            continue
        v=overlap(ma,mb)
        if abs(v)<=.002:continue
        baseline=0.
        if pa and pb and pa['source_geometry']['path']==pb['source_geometry']['path'] and pa['group']==pb['group']:
            src=cache[pa['source_geometry']['path']];baseline=overlap(src[pa['source_part']],src[pb['source_part']])
        row=dict(parts=[a,b],volume_mm3=v,original_volume_mm3=baseline)
        if baseline>0 and abs(v-baseline)<.02:inherited.append(row)
        else:hits.append(row)
    check('stock_has_no_new_material_intersections',not hits,narrow_phase_pairs=tested,intersections=hits,inherited_contacts=inherited)
    # No existing obstacle is removed to make the packing fit. Only the same
    # logger's old display representation is replaced by its detailed model.
    occupied=[];stock_bounds=[m.bounds for m in parts.values()]
    for a in scene['assets']:
        if a['id'] in record['hide_base_identity_ids']:continue
        ab=np.asarray(a['normalized_bounds_m'])+a['position_m']
        if not any(broad(ab,b) for b in stock_bounds):continue
        for n,m in load_parts(dict(path=a['geometry'],sha256=a['geometry_sha256'])).items():
            m.apply_translation(a['position_m']);occupied.append((a['id']+'/'+n,m))
    for n,m in load_parts(scene['architecture']).items():
        if any(broad(m.bounds,b) for b in stock_bounds):occupied.append(('architecture/'+n,m))
    intersections=[];tested=0
    for name,m in parts.items():
        for other,b in occupied:
            if not broad(m.bounds,b.bounds):continue
            tested+=1
            if m.is_volume and b.is_volume:
                v=overlap(m,b)
                if abs(v)>.002:intersections.append(dict(part=name,other=other,volume_mm3=v))
            else:
                cm=trimesh.collision.CollisionManager();cm.add_object('a',m)
                if cm.in_collision_single(b):intersections.append(dict(part=name,other=other,surface_intersection=True))
    check('complete_existing_room_obstacles_preserved_and_clear',not intersections,narrow_phase_pairs=tested,intersections=intersections)
    check('folding_preserves_link_lengths_and_pivot_centres',all(abs(x['old_brace_length_m']-x['new_brace_length_m'])<1e-10 and x['outer_pivot_error_m']<1e-10 for x in record['folded_tripod']['linkage_constraints']))
    refs=[Path(__file__),HERE/'review_mesh_io.py',HERE/'check_weather_assets.py',HERE/'weather_initial_stock_assets.json',HERE/'scene.json',HERE/'weather_scene_binding.json']
    output=dict(schema_version=1,status='static_candidate_checks',passed=all(c['passed'] for c in checks),checks=checks,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        owner_acceptance=None,initial_state_qualified=False,robot_use_qualified=False,
        limitations=['Geometry and identity checks do not establish stable resting equilibrium, reachability, load rating, manipulation or complete initial inventory.'])
    write_json(HERE/'weather_initial_stock_checks.json',output)
    print(json.dumps(dict(passed=output['passed'],checks=len(checks),failed=[c['name'] for c in checks if not c['passed']]),ensure_ascii=False))


if __name__=='__main__':build()
