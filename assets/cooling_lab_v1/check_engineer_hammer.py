"""Check actual hammer domains, head-only mass and ordinary resting support."""
import itertools
import json
from pathlib import Path
import numpy as np
import trimesh
from scipy.optimize import brentq
from shapely.geometry import MultiPoint,Point
from geometry_tools import HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap


def build():
    r=json.loads((HERE/'engineer_hammer_assets.json').read_text());parts=load_parts(r['geometry']);checks=[]
    def check(name,passed,**detail):checks.append(dict(name=name,passed=bool(passed),**detail))
    for ref in r['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    check('part_manifest',set(parts)=={p['id'] for p in r['geometry']['part_records']})
    solids={n:m for n,m in parts.items() if not n.endswith('_text')}
    for n,m in solids.items():check('connected_solid_'+n,m.is_volume and len(m.split())==1)
    intersections=[]
    for (a,x),(b,y) in itertools.combinations(solids.items(),2):
        if not x.is_volume or not y.is_volume:intersections.append(dict(parts=[a,b],reason='nonvolume'));continue
        value=overlap(x,y)
        if not np.isfinite(value) or abs(value)>.01:intersections.append(dict(parts=[a,b],mm3=value))
    check('no_unexplained_material_overlap',not intersections,intersections=intersections)
    whole=trimesh.util.concatenate(list(solids.values()))
    head_names=['forged_steel_head','machined_striking_face_left','machined_striking_face_right']
    head=trimesh.util.concatenate([solids[n] for n in head_names]);head_mass=sum(solids[n].volume for n in head_names)*7850
    check('selected_cross_edition_dimensions',np.allclose(whole.extents[:2],[.356,.135],atol=.0001,rtol=0),actual_m=whole.extents.tolist())
    check('catalogue_head_mass_excludes_handle',abs(head_mass/1.8-1)<.002,represented_head_mass_kg=float(head_mass),tolerance_fraction=.002)
    z=r['inferred_geometry']['head_section_across_flats_m']/2
    check('real_head_eye_with_separate_core',not head.contains([[0,0,z]])[0] and solids['fiberglass_core'].contains([[0,0,z]])[0] and head.contains([[0,0,z+.012]])[0])
    jacket=solids['yellow_handle_jacket'];x0,x1=jacket.bounds[:,0]
    origins=np.column_stack([np.linspace(x0+.002,x1-.002,151),np.full(151,-.040),np.full(151,z)])
    hits,rays,_=jacket.ray.intersects_location(origins,np.tile([0,1,0],(len(origins),1)))
    front=np.full(len(origins),np.inf);np.minimum.at(front,rays,hits[:,1]);wall=-front-.011
    check('continuous_jacket_surrounds_core_between_profile_sections',np.isfinite(front).all() and np.min(wall)>.0003,minimum_radial_wall_at_midplane_m=float(np.min(wall)))
    label=parts['original_handle_identification_text'];centres=label.triangles_center
    hits,rays,_=jacket.ray.intersects_location(centres+[0,-.003,0],np.tile([0,1,0],(len(centres),1)))
    surface=np.full(len(centres),np.inf);np.minimum.at(surface,rays,hits[:,1]);gap=surface-centres[:,1]
    check('label_above_actual_handle_facets',np.isfinite(gap).all() and np.all((gap>.00001)&(gap<.00008)),minimum_gap_m=float(np.min(gap)),maximum_gap_m=float(np.max(gap)))
    check('negative_buried_label_rejected',np.any(gap-.00008<0))
    def matrix(angle):return trimesh.transformations.rotation_matrix(angle,[0,1,0])
    def lowest(mesh,angle):return np.min(mesh.vertices@matrix(angle)[:3,:3].T,axis=0)[2]
    angle=brentq(lambda a:lowest(head,a)-lowest(jacket,a),-.15,0,xtol=1e-13)
    rest=matrix(angle);rest[2,3]=-np.min(whole.vertices@rest[:3,:3].T,axis=0)[2]
    placed=whole.copy();placed.apply_transform(rest);contact=placed.vertices[placed.vertices[:,2]<2e-7]
    polygon=MultiPoint(contact[:,:2]).convex_hull
    check('head_and_handle_both_reach_support',abs(lowest(head,angle)+rest[2,3])<1e-7 and abs(lowest(jacket,angle)+rest[2,3])<1e-7 and np.min(placed.vertices[:,2])>=-1e-8,
        tilt_degrees=float(np.degrees(angle)),contact_points=len(contact))
    def mass_com(densities):
        masses=np.array([m.volume*(densities[0] if n in head_names else densities[1] if n=='fiberglass_core' else densities[2] if n=='yellow_handle_jacket' else densities[3]) for n,m in solids.items()])
        com=np.sum(masses[:,None]*np.array([m.center_mass for m in solids.values()]),axis=0)/masses.sum()
        return masses.sum(),com
    variants=[]
    for densities in itertools.product([7700,8000],[1850,2050],[950,1250],[1100,1300]):
        mass,com=mass_com(densities);position=trimesh.transform_points([com],rest)[0]
        variants.append(dict(densities_kg_m3=densities,mass_kg=float(mass),inside_support=polygon.contains(Point(position[:2])),support_margin_m=float(polygon.boundary.distance(Point(position[:2])))))
    mass,com=mass_com([7850,1950,1100,1200]);support_margin=min(c['support_margin_m'] for c in variants)
    check('support_contains_inferred_mass_range',all(c['inside_support'] for c in variants) and support_margin>.001,minimum_margin_m=support_margin,range_checks=variants)
    check('head_mass_is_not_whole_tool_mass',mass>head_mass,estimated_total_mass_kg=float(mass),head_mass_kg=float(head_mass),non_head_mass_kg=float(mass-head_mass))
    check('negative_displaced_com_rejected',not polygon.contains(Point([1,1])))
    check('no_unearned_qualification',r['owner_acceptance'] is None and not any(r[k] for k in ['impact_qualified','robot_use_qualified','initial_stock_credit']))
    failed=[c['name'] for c in checks if not c['passed']]
    refs=[Path(__file__),HERE/'engineer_hammer_assets.json',HERE/'check_weather_assets.py']
    report=dict(schema_version=1,passed=not failed,failed=failed,checks=checks,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        resting_reference=dict(to_support_plane=rest.tolist(),inferred_mass_kg=float(mass),inferred_com_m=com.tolist(),
            support_margin_m=support_margin,range_checks=variants,placed_bounds_m=placed.bounds.tolist(),
            scope='Rigid support under explicit inferred densities. No dynamic settling, factory inertia or impact qualification.'),
        scope='Original steel/core/jacket domains, nominal head-only mass, real eye and static support. No force, retention, soil driving or humanoid action.',
        owner_acceptance=None,robot_use_qualified=False)
    write_json(HERE/'engineer_hammer_checks.json',report)
    print(json.dumps(dict(passed=not failed,checks=len(checks),failed=failed,intersections=intersections,estimated_mass_kg=float(mass),support_margin_m=support_margin)))
    if failed:raise AssertionError(failed)


if __name__=='__main__':build()
