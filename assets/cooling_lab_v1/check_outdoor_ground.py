"""Check actual earth/pad solids against station and current laboratory layout."""
import itertools
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Point,LineString,box
import trimesh
from geometry_tools import HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap


def ground_parts(ref):
    parts=load_parts(ref)
    # Per-face UV seams are rendering vertices, not cracks in the soil.
    # Weld the geometry-only inspection copies across texture/normal seams.
    for m in parts.values():
        m.merge_vertices(merge_tex=True,merge_norm=True,digits_vertex=8);m.fix_normals()
    return parts


def build():
    record=json.loads((HERE/'outdoor_ground_assets.json').read_text());parts=ground_parts(record['geometry'])
    site=json.loads((HERE/'weather_site_review.json').read_text());scene=json.loads((HERE/'scene.json').read_text());checks=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for ref in record['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    for name,m in parts.items():check('single_closed_volume_'+name,m.is_volume and len(m.split())==1)
    sections=ground_parts(record['section_geometry'])
    for name,m in sections.items():check('section_is_actual_closed_volume_'+name,m.is_volume and len(m.split())==1 and m.bounds[0,0]>=6.-1e-6)
    check('capped_section_has_half_ground_volume',abs(sum(m.volume for m in sections.values())-72.)<1e-5)
    check('same_outdoor_area_as_current_scene',record['design']['area_bounds_m']==next(z for z in scene['zones'] if z['id']=='outdoor')['bounds_m'])
    expected_volume=12*8*1.5;volume=sum(m.volume for m in parts.values());check('complete_ground_volume_no_missing_layers',abs(volume-expected_volume)<1e-5,actual_volume_m3=float(volume))
    hits=[]
    for (a,ma),(b,mb) in itertools.combinations(parts.items(),2):
        v=overlap(ma,mb)
        if v>.1:hits.append(dict(parts=[a,b],volume_mm3=v))
    check('ground_layers_and_pads_do_not_overlap',not hits,intersections=hits)
    surface=[(n,m) for n,m in parts.items() if n!='outdoor_floor_soil_substrate']
    for n,m in surface:check('flush_surface_'+n,abs(m.bounds[1,2])<2e-7)
    def first_material(x,y):
        rows=[]
        for n,m in parts.items():
            points=m.ray.intersects_location([[x,y,.02]],[[0,0,-1]])[0]
            if len(points):rows.append((float(points[:,2].max()),n))
        return max(rows)[1]
    for i,xy in enumerate(site['guy_anchors_xy_m'],1):check('guy_anchor_in_earth_'+str(i),'level_earth_' in first_material(*xy))
    for i,xy in enumerate(site['tripod_feet_xy_m'],1):check('tripod_foot_in_earth_'+str(i),'level_earth_' in first_material(*xy))
    centre=np.array(site['mast_center_xy_m']);rod_xy=centre+[.12,0]
    check('provisional_ground_rod_in_earth','level_earth_' in first_material(*rod_xy))
    rod=trimesh.creation.cylinder(.00635,1.2192,sections=64);rod.apply_translation([*rod_xy,-.6096])
    hard=[m for n,m in parts.items() if 'walkway' in n or 'bench_pad_' in n]
    check('provisional_ground_rod_clear_of_hard_surfaces',all(overlap(rod,m)<.001 for m in hard))
    check('provisional_ground_rod_within_authored_soil_depth',rod.bounds[0,2]>record['design']['soil_bottom_m'])
    for n in ['white_bench','black_bench','weather_service','tracker_support']:
        oid={'white_bench':'outdoor_white','black_bench':'outdoor_black'}.get(n,n)
        obstacle=next(o for o in scene['obstacles'] if o['id']==oid)
        bounds=obstacle['bounds_m'];xy=(np.array(bounds[0][:2])+bounds[1][:2])/2
        check('bench_supported_by_pad_'+n,first_material(*xy)=='outdoor_floor_bench_pad_'+n)
    # Compare the actual exported walkway's top footprint, rather than just
    # checking a drawing of a centreline. Keep both existing corridor and
    # selected new approach buffers covered by the concrete surface.
    walkway=parts['outdoor_floor_flush_walkway'];top_faces=walkway.faces[np.all(abs(walkway.vertices[walkway.faces,2])<2e-7,axis=1)]
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    plan=unary_union([Polygon(walkway.vertices[f,:2]) for f in top_faces])
    corridor=site['existing_front_corridor'];required=LineString(corridor['points_m']).buffer(corridor['width_m']/2,cap_style='flat')
    approach=LineString(site['provisional_front_approach_xy_m']).buffer(site['provisional_approach_half_width_m'])
    check('existing_corridor_on_walkway',required.difference(plan.buffer(2e-6)).area<1e-8)
    check('provisional_approach_on_walkway',approach.difference(plan.buffer(2e-6)).area<1e-8)
    old_slab=trimesh.creation.box([12,8,.12]);old_slab.apply_translation([6,16,-.06])
    check('negative_old_hard_slab_blocks_ground_rod',overlap(rod,old_slab)>1.)
    check('no_unevaluated_strength_or_robot_credit',not any([record['staged_in_lab'],record['installation_qualified'],record['robot_use_qualified'],record['owner_acceptance'],record['design']['ground_strength_qualified'],record['design']['stake_retention_qualified']]))
    refs=[Path(__file__),HERE/'outdoor_ground_assets.json',HERE/'check_weather_assets.py',HERE/'weather_site_review.json',HERE/'scene.json']
    report=dict(passed=True,checks=checks,source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],staged_in_lab=False,ground_strength_qualified=False,stake_retention_qualified=False,robot_use_qualified=False,owner_acceptance=None,
        limits=['Selected earthen site and flush hard surfaces are static authored geometry; no measured soil parameters, compression, driving or pulling forces are represented.',
            'Provisional rod/anchor locations do not constitute installed hardware or completed cable routing.',
            'Current main-scene slab is unchanged until this candidate is explicitly integrated and downstream checks rerun.'])
    write_json(HERE/'outdoor_ground_checks.json',report);print(json.dumps(dict(passed=True,checks=len(checks),parts=len(parts))))


if __name__=='__main__':build()
