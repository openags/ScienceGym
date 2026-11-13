"""Static AC28VS candidate geometry and a detached fastener gauge only."""
import itertools
import json
from pathlib import Path
import numpy as np
import trimesh
from shapely.geometry import MultiPoint,Point
from geometry_tools import HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap


def build():
    record=json.loads((HERE/'adjustable_wrench_assets.json').read_text());checks=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for ref in record['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    frame=np.asarray(record['local_jaw_frame_to_tool']);inverse=np.linalg.inv(frame)
    all_models={i['id']:load_parts(i['geometry']) for i in record['items']}
    models={key:{n:m for n,m in parts.items() if not n.endswith('_text')} for key,parts in all_models.items()};reference=models['half_inch_reference']
    for item in record['items']:
        parts=models[item['id']];check('five_named_solids_'+item['id'],len(parts)==5)
        check('two_original_scale_faces_'+item['id'],set(all_models[item['id']])-set(parts)=={'metric_scale_text','inch_scale_text'})
        bounds=np.array([p.bounds for p in parts.values()]);actual=np.array([bounds[:,0].min(0),bounds[:,1].max(0)])
        check('actual_bounds_'+item['id'],np.allclose(actual,item['geometry']['bounds_m'],atol=1e-8),actual_m=actual.tolist())
        check('source_length_'+item['id'],abs(actual[1,0]-actual[0,0]-.2032)<.0001)
        for n,m in parts.items():
            check('connected_volume_'+item['id']+'/'+n,m.is_volume and len(m.split())==1)
            expected=reference[n].copy();expected.apply_transform(item['part_transforms'][n])
            check('declared_rigid_state_'+item['id']+'/'+n,np.array_equal(m.faces,expected.faces) and np.allclose(m.vertices,expected.vertices,atol=2e-8))
        hits=[]
        for (a,x),(b,y) in itertools.combinations(parts.items(),2):
            volume=overlap(x,y)
            if not np.isfinite(volume) or abs(volume)>.001:hits.append(dict(parts=[a,b],intersection_mm3=volume))
        check('no_interpenetration_'+item['id'],not hits,examined_pairs=10,intersections=hits)
        local={n:m.copy() for n,m in parts.items()}
        for m in local.values():m.apply_transform(inverse)
        body=local['forged_body_and_fixed_jaw'];jaw=local['sliding_jaw_and_rack'];gap=item['selected_gap_m']
        upper=body.ray.intersects_location([[-.015,-.005,0]],[[0,1,0]])[0]
        lower=jaw.ray.intersects_location([[-.015,.005-gap,0]],[[0,-1,0]])[0]
        upper_y=upper[:,1].min();lower_y=lower[:,1].max()
        check('actual_parallel_jaw_opening_'+item['id'],abs(upper_y)<1e-7 and abs(lower_y+gap)<1e-7,
            measured_opening_m=float(upper_y-lower_y),selected_m=gap)
        for label,m,y in [('fixed',body,.001),('sliding',jaw,-gap-.002)]:
            points=m.ray.intersects_location([[-.015,y,-.02]],[[0,0,1]])[0]
            thickness=points[:,2].max()-points[:,2].min()
            check('source_jaw_thickness_'+item['id']+'/'+label,abs(thickness-.00762)<1e-7,actual_m=float(thickness))
    local={n:m.copy() for n,m in reference.items()}
    for m in local.values():m.apply_transform(inverse)
    body=local['forged_body_and_fixed_jaw'];jaw=local['sliding_jaw_and_rack'];worm=local['helical_adjustment_worm']
    for scale in record['ordinary_scale_artwork']:
        mesh=all_models['half_inch_reference'][scale['id']].copy();mesh.apply_transform(inverse)
        check('scale_face_'+scale['id'],np.allclose(mesh.bounds,scale['local_bounds_m'],atol=1e-8) and np.all(mesh.face_normals[:,2]*scale['side']>.999))
        points=np.array([[u,y,scale['side']*.0037] for u in np.linspace(.0005,.0065,7) for y in np.linspace(-.0259,.0009,28)])
        check('scale_supported_by_real_head_face_'+scale['id'],body.contains(points).all(),sample_count=len(points))
        ys=np.array([t['local_y_m'] for t in scale['ticks']]);pixel_y=np.array([t['pixel_y'] for t in scale['ticks']]);openings=np.array([t['opening_m'] for t in scale['ticks']])
        decoded=.001-pixel_y/(scale['texture_size_px'][1]-1)*.027
        check('scale_graduations_match_jaw_datum_'+scale['id'],np.allclose(decoded,ys,atol=1e-12) and np.allclose(ys,-openings,atol=1e-12))
    check('real_rack_guide_and_steel_roof',not body.contains([[.0052,-.005,0]])[0] and body.contains([[.0052,-.005,.0037]])[0] and jaw.contains([[.0052,-.005,0]])[0])
    check('real_worm_axle_bore_and_core',not worm.contains([[.0158,-.008,0]])[0] and worm.contains([[.0178,-.008,0]])[0])
    fixed=reference['forged_body_and_fixed_jaw']
    check('real_hanging_hole_and_surrounding_steel',not fixed.contains([[.193,0,0]])[0] and fixed.contains([[.193,.008,0]])[0])
    rows=[]
    for gap in np.linspace(0,.028575,17):
        parts={n:m.copy() for n,m in reference.items()};delta=np.eye(4);delta[1,3]=-(gap-record['reference_gap_m'])
        parts['sliding_jaw_and_rack'].apply_transform(frame@delta@inverse)
        roll=trimesh.transformations.rotation_matrix(-2*np.pi*(gap-record['reference_gap_m'])/record['inferred_thread_pitch_m'],[0,1,0],point=[.0158,0,0])
        parts['helical_adjustment_worm'].apply_transform(frame@roll@inverse);hits=[]
        for (a,x),(b,y) in itertools.combinations(parts.items(),2):
            volume=overlap(x,y)
            if not np.isfinite(volume) or abs(volume)>.001:hits.append(dict(parts=[a,b],intersection_mm3=volume))
        rows.append(dict(gap_m=float(gap),intersections=hits))
    check('sampled_nominal_adjustments_clear',all(not r['intersections'] for r in rows),samples=rows,
        scope='Seventeen independent rigid states with an inferred pitch relation. No continuous clearance, backlash, spring or torque qualification.')
    def gauge(af):
        m=trimesh.creation.cylinder(radius=af/np.sqrt(3),height=.0068,sections=6)
        m.apply_translation([-.015,-record['reference_gap_m']/2,0]);return m
    nominal=gauge(.0127);wide=gauge(.013)
    check('detached_half_inch_hex_fits_parallel_faces',all(abs(overlap(nominal,m))<.001 for m in local.values()))
    check('negative_oversize_hex_rejected',sum(overlap(wide,m) for m in local.values())>1)
    mass=sum(m.volume for m in reference.values())*7850
    target=.62*.45359237
    check('catalogue_mass_consistency_under_density_hypothesis',abs(mass-target)<target*.1,
        estimated_mass_kg=mass,catalogue_mass_kg=target,inferred_density_kg_m3=7850,tolerance_fraction=.1,
        note='Consistency only; handle section, density, centre of mass and inertia are not measured.')
    volumes=np.array([m.volume for m in reference.values()]);centres=np.array([m.center_mass for m in reference.values()])
    com=(volumes[:,None]*centres).sum(0)/volumes.sum()
    whole=trimesh.util.concatenate(list(reference.values()));transforms=[]
    # Enumerate actual convex support planes. Probability-based stable-pose
    # integration can discard these nearly coplanar shallow hull facets.
    for normal in np.unique(whole.convex_hull.face_normals.round(7),axis=0):
        if normal[2]>-.9:continue
        candidate=trimesh.geometry.align_vectors(normal,[0,0,-1])
        vertices=trimesh.transform_points(whole.vertices,candidate);candidate[2,3]=-vertices[:,2].min();vertices[:,2]+=candidate[2,3]
        polygon=MultiPoint(vertices[vertices[:,2]<2e-7,:2]).convex_hull;c=trimesh.transform_points([com],candidate)[0]
        if polygon.area>1e-7 and polygon.contains(Point(c[:2])):transforms.append(candidate)
    check('face_up_rigid_support_plane_exists',bool(transforms))
    rest=max(transforms,key=lambda t:t[2,2]).copy()
    rest=trimesh.transformations.rotation_matrix(-np.arctan2(rest[1,0],rest[0,0]),[0,0,1])@rest
    contacts=[];placed=[]
    for n,m in reference.items():
        mesh=m.copy();mesh.apply_transform(rest);placed.append(mesh)
        contacts.extend(dict(part=n,point_m=p.tolist()) for p in mesh.vertices[mesh.vertices[:,2]<2e-7])
    polygon=MultiPoint([c['point_m'][:2] for c in contacts]).convex_hull
    ranges=[]
    for density in itertools.product([7700.,8100.],repeat=len(reference)):
        weights=volumes*density;c=(weights[:,None]*centres).sum(0)/weights.sum();c=trimesh.transform_points([c],rest)[0]
        ranges.append(dict(densities_kg_m3=list(density),com_m=c.tolist(),inside_support=bool(polygon.contains(Point(c[:2]))),support_margin_m=float(polygon.boundary.distance(Point(c[:2])))))
    check('actual_resting_contacts_support_inferred_mass_range',polygon.area>1e-7 and all(c['inside_support'] and c['support_margin_m']>.001 for c in ranges) and min(m.bounds[0,2] for m in placed)>=-1e-7,contacts=contacts)
    check('negative_distant_com_rejected',not polygon.contains(Point([.3,0])))
    resting=dict(to_support_plane=rest.tolist(),contacts=contacts,support_polygon_xy_m=list(map(list,polygon.exterior.coords)),
        part_order=list(reference),range_checks=ranges,estimated_mass_kg=mass,inferred_com_m=com.tolist(),
        scope='Rigid half-inch reference; independent 7700–8100 kg/m3 steel density hypotheses. No settling or worm/rack locking simulation.')
    check('no_unearned_qualification',record['owner_acceptance'] is None and not any(record[k] for k in ['staged_in_lab','initial_stock_credit','torque_qualified','robot_use_qualified']))
    refs=[Path(__file__),HERE/'adjustable_wrench_assets.json',HERE/'check_weather_assets.py']
    result=dict(schema_version=1,passed=True,checks=checks,resting_reference=resting,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        limits=['Original static candidate only; actual tripod/fastener access and final visual review remain pending.',
            'The source tension spring is represented by an inferred axial coil; factory spring layout, retention, preload and drive contacts are not established.',
            'A detached hex gauge is not a complete service interface, counter-holding action, hand grasp or torque test.'],
        torque_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'adjustable_wrench_checks.json',result);print(json.dumps(dict(passed=True,checks=len(checks),states=len(models),samples=len(rows))))


if __name__=='__main__':build()
