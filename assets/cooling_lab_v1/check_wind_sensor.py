"""Inspect rigid wind-sensor parts and conservative full-turn occupancy.

This does not test bearings, clamping force, wind response, cables, robot access
or a mounted weather station. Full-turn envelopes are separate review geometry.
"""
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import trimesh
from geometry_tools import HERE, ROOT, sha, write_json
from check_weather_assets import load_parts, overlap


def cylinder(radius,low,high,inner=0):
    mesh=(trimesh.creation.annulus(inner,radius,high-low,sections=128) if inner else
        trimesh.creation.cylinder(radius,high-low,sections=128))
    mesh.apply_translation([.3,0,(low+high)/2]);return mesh


def cup_sweep(check,orbit_radius):
    # A torus bounds the complete orbit of a 38.1 mm cup sphere. A coarse
    # rectangular annulus incorrectly occupied empty space beside the arm.
    angle=np.linspace(0,2*np.pi,65)
    profile=np.column_stack([orbit_radius+.01925*np.cos(angle),.333+.01925*np.sin(angle)])
    mesh=trimesh.creation.revolve(profile,sections=128);mesh.apply_translation([.3,0,0])
    # Verify the generated polyhedron's exact sector symmetry, then inspect
    # one complete sector. This is equivalent to 4096 full-circle samples.
    turn=trimesh.transformations.rotation_matrix(2*np.pi/128,[0,0,1],[.3,0,0])
    rotated=trimesh.transform_points(mesh.vertices,turn)
    distances,mapping=cKDTree(mesh.vertices).query(rotated)
    faces={tuple(f) for f in np.sort(mesh.faces,axis=1)}
    mapped_faces={tuple(f) for f in np.sort(mapping[mesh.faces],axis=1)}
    check('cup_sweep_polyhedron_sector_symmetry',distances.max()<1e-11 and faces==mapped_faces)
    theta=np.linspace(0,2*np.pi/128,33)
    centers=np.column_stack([.3+orbit_radius*np.cos(theta),orbit_radius*np.sin(theta),np.full(len(theta),.333)])
    _,distance,_=trimesh.proximity.closest_point(mesh,centers)
    arc_error=2*orbit_radius*np.sin(np.pi/(128*32*2))
    certified_radius=float(distance.min()-arc_error)
    certificate=dict(sectors=128,samples_in_one_sector=33,
        minimum_sample_boundary_distance_m=float(distance.min()),
        unsampled_centerline_displacement_bound_m=float(arc_error),
        certified_contained_ball_radius_m=certified_radius,nominal_cup_radius_m=.01905,
        export_radial_guard_m=1e-7,physical_cup_ball_radius_m=.0190501)
    check('entire_cup_orbit_contained_by_sweep_polyhedron',mesh.contains(centers).all() and certified_radius>.0190501,**certificate)
    return mesh,certificate


def faces_in_rotational_primitives(mesh,cylinders,balls=()):
    """Every triangle must fit in one convex rotation-invariant primitive.

    A cylinder uses the polygon's inscribed radius; a cup triangle fits within
    one sphere whose complete orbit is certified separately by cup_sweep.
    """
    triangles=mesh.triangles;covered=np.zeros(len(triangles),dtype=bool)
    radii=np.linalg.norm(triangles[:,:,:2]-[.3,0],axis=2)
    for radius,low,high in cylinders:
        covered|=(radii.max(axis=1)<=radius*np.cos(np.pi/128)) & (triangles[:,:,2].min(axis=1)>=low) & (triangles[:,:,2].max(axis=1)<=high)
    for center,radius in balls:
        covered|=np.linalg.norm(triangles-np.array(center),axis=2).max(axis=1)<=radius
    return int(np.count_nonzero(~covered))


def build():
    record=json.loads((HERE/'wind_sensor_assets.json').read_text());parts=load_parts(record['geometry'])
    checks=[];poses=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for ref in record['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    for name,mesh in parts.items():check('single_closed_volume_'+name,mesh.is_volume and len(mesh.split())==1)
    intersections=[]
    for i,(name,a) in enumerate(parts.items()):
        for other,b in list(parts.items())[i+1:]:
            volume=overlap(a,b)
            if volume>.001:intersections.append(dict(parts=[name,other],volume_mm3=volume))
    check('no_unexplained_static_overlap',not intersections,intersections=intersections)
    cup_radius=record['selected_dimensions']['cup_turning_radius_m'];orbit_radius=cup_radius-.01905
    for name,radius in [('three_cup_rotor',cup_radius),('vane_with_d_bore',.135)]:
        actual=np.linalg.norm(parts[name].vertices[:,:2]-[.3,0],axis=1).max()
        check('selected_turning_radius_'+name,abs(actual-radius)<2e-7,actual_radius_m=float(actual),
            dimension_status='photo-constrained inference; source conflict open' if name=='three_cup_rotor' else 'approximate published value')
    literal=load_parts(record['unresolved_cup_radius']['literal_interpretation_geometry'])['literal_108mm_cup_rotor']
    literal_radius=float(np.linalg.norm(literal.vertices[:,:2]-[.3,0],axis=1).max())
    check('conflicting_literal_radius_retained_separately',abs(literal_radius-.108)<2e-7 and cup_radius!=.108,actual_literal_radius_m=literal_radius)
    for index,angle in enumerate(np.arange(3)*2*np.pi/3):
        radial=np.array([np.cos(angle),np.sin(angle),0.]);direction=np.array([-np.sin(angle),np.cos(angle),0.])
        origin=np.array([.3,0,.333])+orbit_radius*radial
        hits=parts['three_cup_rotor'].ray.intersects_location([origin],[direction])[0]
        depth=float(np.min((hits-origin)@direction))
        check('cup_'+str(index+1)+'_is_open_and_hollow',.0177<depth<.018,first_inner_wall_m=depth)
    mast=trimesh.creation.cylinder(.0205,.15,sections=128);mast.apply_translation([-.0255,0,.05])
    hits=[dict(part=n,volume_mm3=overlap(m,mast)) for n,m in parts.items() if overlap(m,mast)>.001]
    check('selected_41mm_mast_has_no_solid_interference',not hits,intersections=hits)
    for group,axis in record['rotor_axes'].items():
        fixed={n:m for n,m in parts.items() if n not in axis['parts']}
        for degrees in range(0,360,30):
            rotation=trimesh.transformations.rotation_matrix(np.radians(degrees),axis['axis'],axis['origin_m'])
            maximum=0.
            for name in axis['parts']:
                mesh=parts[name].copy();mesh.apply_transform(rotation)
                maximum=max(maximum,max(overlap(mesh,b) for b in fixed.values()))
            check(group+'_pose_'+str(degrees),maximum<.001,maximum_overlap_mm3=maximum)
            poses.append(dict(group=group,degrees=degrees,maximum_overlap_mm3=maximum))
    # Treating the keyed direction shaft as fixed produces a false collision.
    # Keep a regression case for that incorrect mechanical grouping.
    wrong=parts['vane_with_d_bore'].copy();wrong.apply_transform(trimesh.transformations.rotation_matrix(np.pi/6,[0,0,1],[.3,0,.410]))
    check('negative_fixed_d_shaft_rejected',overlap(wrong,parts['upper_direction_d_shaft'])>1)
    torus,cup_certificate=cup_sweep(check,orbit_radius)
    specs={'cups':[(orbit_radius-.01905+.0017,.33095,.33505),(.00905,.32695,.34105),(.00301,.32699,.35201)],
        'vane':[(.1351,.40695,.47005),(.01805,.39795,.41405),(.00301,.38799,.41101)]}
    balls=[([.3+orbit_radius*np.cos(a),orbit_radius*np.sin(a),.333],.0190501) for a in np.arange(3)*2*np.pi/3]
    envelope_parts={group:[cylinder(*s) for s in cylinders] for group,cylinders in specs.items()}
    envelope_parts['cups'].insert(0,torus)
    envelopes={};full_turn=[];scene=trimesh.Scene()
    for group,elements in envelope_parts.items():
        envelope=trimesh.boolean.union(elements,engine='manifold');envelopes[group]=envelope
        axis=record['rotor_axes'][group]
        outside=[]
        for name in axis['parts']:
            uncovered=faces_in_rotational_primitives(parts[name],specs[group],balls if group=='cups' else [])
            check('continuous_rotation_surface_bound_'+name,uncovered==0,uncovered_triangles=uncovered)
            difference=trimesh.boolean.difference([parts[name],envelope],engine='manifold')
            volume=float(difference.volume*1e9) if len(difference.faces) else 0.
            if volume>.001:outside.append(dict(part=name,volume_mm3=volume))
        check('full_turn_envelope_contains_actual_'+group,not outside,outside=outside)
        # Other moving groups are checked against their complete envelopes
        # below; compare only the truly stationary assembly here.
        moving={n for a in record['rotor_axes'].values() for n in a['parts']}
        hits=[dict(part=n,volume_mm3=overlap(envelope,m)) for n,m in parts.items() if n not in moving and overlap(envelope,m)>.001]
        clear=not hits
        full_turn.append(dict(group=group,conservative_envelope_clear=clear,stationary_intersections=hits))
        check('conservative_full_turn_clear_'+group,clear,intersections=hits)
        scene.add_geometry(envelope,node_name=group,geom_name=group)
    check('independent_rotors_have_disjoint_sweep_envelopes',overlap(envelopes['cups'],envelopes['vane'])<.001)
    path=HERE/'geometry/weather_wind_sweep_envelopes.glb';path.write_bytes(scene.export(file_type='glb'))
    refs=[Path(__file__),HERE/'check_weather_assets.py',HERE/'wind_sensor_assets.json',HERE/'wind_sensor_sources.json']
    report=dict(passed=True,checks=checks,static_rotor_poses=poses,full_turn_geometry=full_turn,cup_orbit_certificate=cup_certificate,
        sweep_geometry=dict(path=str(path.relative_to(ROOT)),sha256=sha(path),parts=len(scene.geometry)),
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        installation_qualified=False,robot_use_qualified=False,owner_acceptance=None,
        limits=['Full-turn occupancy contains every moving triangle in a rotation-invariant cylinder or a certified cup-sphere orbit; actual zero-pose volumes are also checked.',
            'Nominal thread/shaft clearances do not test force, friction, retention, structural load or manufacturer tolerances.',
            'Cable, tripod, robot and complete weather-station interference are excluded. Source dimensional conflicts remain open.'])
    write_json(HERE/'wind_sensor_checks.json',report)
    print(json.dumps(dict(passed=True,checks=len(checks),parts=len(parts),full_turn_geometry=full_turn)))


if __name__=='__main__':build()
