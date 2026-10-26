"""Inspect actual exported tool geometry; no severing, forces or robot action."""
import itertools
import json
from pathlib import Path
import numpy as np
import trimesh
from shapely.geometry import MultiPoint,Point
from geometry_tools import HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap


def build():
    record=json.loads((HERE/'wire_rope_cutter_assets.json').read_text())
    sources=json.loads((HERE/'wire_rope_cutter_sources.json').read_text());checks=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for ref in record['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    models={state:load_parts(record[key]) for state,key in [('closed','geometry'),('opened','open_geometry')]}
    closed=models['closed'];opened=models['opened'];members=record['mechanical_groups']
    owner={n:group for group,names in members.items() for n in names}
    def pair_overlap(a,x,b,y,matrices):
        # Coincident steel/coating boundaries share one rigid lever. Evaluate
        # them in its source frame so float32 Boolean arithmetic does not turn
        # a common rotation into a spurious material overlap. Any relative
        # displacement is preserved; distinct levers remain in world space.
        if owner[a]==owner[b]:
            inverse=np.linalg.inv(matrices[a]);x=x.copy();y=y.copy()
            x.apply_transform(inverse);y.apply_transform(inverse)
        return overlap(x,y)
    names=[n for group in members.values() for n in group]
    check('each_part_belongs_to_one_mechanism_group',len(names)==len(set(names))==13 and set(names)==set(closed)==set(opened))
    for state,key in [('closed','geometry'),('opened','open_geometry')]:
        parts=models[state];bounds=np.stack([m.bounds for m in parts.values()]);actual=np.stack([bounds[:,0].min(0),bounds[:,1].max(0)])
        check(state+'_actual_envelope',np.allclose(actual,record[key]['bounds_m'],atol=1e-8),actual_m=actual.tolist())
        p_records={p['id']:p for p in record[key]['part_records']}
        for n,m in parts.items():
            check(state+'_closed_connected_'+n,m.is_volume and len(m.split())==1)
            check(state+'_actual_part_bounds_'+n,np.allclose(m.bounds,p_records[n]['bounds_m'],atol=1e-8))
        pairs=[dict(parts=[a,b],overlap_mm3=pair_overlap(a,x,b,y,record['inspection_states'][state])) for (a,x),(b,y) in itertools.combinations(parts.items(),2)]
        check(state+'_distinct_physical_volumes',all(np.isfinite(p['overlap_mm3']) and abs(p['overlap_mm3'])<.001 for p in pairs),pairs=pairs)
    ext=np.diff(np.array(record['geometry']['bounds_m']),axis=0)[0]
    check('catalogue_length_and_thickness',abs(ext[0]-.190)<.0001 and abs(ext[2]-.020)<1e-7,
        actual_m=ext.tolist(),length_tolerance_m=.0001,note='The photo-based circular tip is within 0.1 mm of the nominal overall length; it is not a measured manufacturing tolerance.')
    check('width_conflict_not_erased',sources['manufacturer_facts']['catalogue_envelope_jaw_state_specified'] is False
        and len(sources['source_differences'])>=2 and .044<ext[1]<.046,
        actual_closed_width_m=float(ext[1]),selected_photo_US_interpretation_m=.04445,
        unresolved_metric_catalogue_width_m=.060,note='Closed width is an inferred photo interpretation, not a measured manufacturer jaw-state dimension.')
    for n,m in closed.items():
        expected=m.copy();expected.apply_transform(np.array(record['inspection_states']['opened'][n]))
        check('rigid_state_'+n,np.array_equal(expected.faces,opened[n].faces) and np.allclose(expected.vertices,opened[n].vertices,atol=2e-8))
    # The pivot/retainer shafts and spring occupy actual bores/recesses. Solid
    # probe points just outside the holes reject a missing or enlarged body.
    jaw=closed['upper_polished_jaw']
    check('real_ground_bevel_and_finite_edge_land',jaw.contains([[.004,-.0006,.0001]])[0] and not jaw.contains([[.004,-.0006,.0035]])[0])
    check('pivot_real_bore_and_surrounding_steel',not jaw.contains([[.018,0,.003],[.02105,0,.003]]).any() and jaw.contains([[.02125,0,.003]])[0])
    check('internal_spring_recess_and_roof',not jaw.contains([[.022,0,.001]])[0] and jaw.contains([[.022,0,.002]])[0])
    check('retainer_real_bore',not jaw.contains([[.030,.010,.002]])[0] and jaw.contains([[.030,.012,.002]])[0])
    arm=closed['upper_forged_arm'];grip=closed['upper_plastic_grip']
    check('full_steel_core_inside_real_grip_cavity',arm.contains([[.100,.017,.002],[.100,.017,.008]]).all()
        and not grip.contains([[.100,.017,.002],[.100,.017,.008]]).any() and grip.contains([[.100,.017,.0093]])[0])
    shifted=opened['upper_plastic_grip'].copy();shifted.apply_translation([0,0,.00001])
    check('negative_relative_coating_shift_rejected_in_common_frame',pair_overlap('upper_plastic_grip',shifted,
        'upper_forged_arm',opened['upper_forged_arm'],record['inspection_states']['opened'])>.001)
    # Both crimp recesses open onto the inner arm edge in each shear plane.
    # Local radii are hypotheses, not wire/sleeve compatibility qualification.
    for x,r in [(.035,.0014),(.0405,.002)]:
        check('open_crimp_recess_'+str(x),not arm.contains([[x,.0001,.002],[x,r*.95,.002]]).any()
            and arm.contains([[x,r+.00015,.002]])[0])
    sample_rows=[]
    for angle in np.linspace(0,record['selected_half_opening_rad'],9):
        parts={n:m.copy() for n,m in closed.items()};matrices={n:np.eye(4) for n in parts}
        for group,sign in [('upper_lever',1),('lower_lever',-1)]:
            matrix=trimesh.transformations.rotation_matrix(sign*angle,[0,0,1],point=record['pivot_m'])
            for n in members[group]:parts[n].apply_transform(matrix);matrices[n]=matrix
        hits=[]
        for (a,x),(b,y) in itertools.combinations(parts.items(),2):
            v=pair_overlap(a,x,b,y,matrices)
            if not np.isfinite(v) or abs(v)>.001:hits.append(dict(parts=[a,b],overlap_mm3=v))
        sample_rows.append(dict(half_angle_rad=float(angle),intersections=hits))
    check('sampled_opening_has_no_solid_interpenetration',all(not r['intersections'] for r in sample_rows),samples=sample_rows,
        scope='Nine independent static samples only, not a continuous collision certificate or a dynamic trajectory.')
    def wire(radius):
        m=trimesh.creation.cylinder(radius=radius,height=.03,sections=96);m.apply_translation([.002,0,0]);return m
    nominal=wire(.0015);oversize=wire(.004)
    clear=[dict(part=n,overlap_mm3=overlap(nominal,m)) for n,m in opened.items()]
    check('selected_3mm_wire_can_enter_opened_mouth',all(np.isfinite(v['overlap_mm3']) and abs(v['overlap_mm3'])<.001 for v in clear),pairs=clear,
        selected_wire_axis_origin_m=[.002,0,0],scope='Geometric entry at this selected state; material, force and cutting mechanics remain unqualified.')
    check('negative_closed_mouth_rejects_uncut_wire',sum(overlap(nominal,m) for n,m in closed.items())>1)
    check('negative_oversized_wire_rejected',sum(overlap(oversize,m) for n,m in opened.items())>1)
    facts=sources['manufacturer_facts']['cutting_capacity_diameter_mm']
    check('distinct_catalogue_material_capacities',facts['wire_rope']==5 and facts['fine_stranded_copper']==6 and facts['piano_wire']==2.5,
        note='A 3 mm solid piano wire exceeds the quoted piano-wire row; do not use the wire-rope row for it.')
    # A complete tool needs actual support when staged on the worktop, rather
    # than translating its bounding box onto the table and leaving its centre
    # of mass outside the contact region. Density assumptions affect only this
    # static check; no inertial or material-parameter qualification is implied.
    volumes=np.array([m.volume for m in closed.values()]);centres=np.array([m.center_mass for m in closed.values()])
    plastic=np.array(['plastic_grip' in n for n in closed]);density=np.where(plastic,1400.,7850.)
    masses=volumes*density;com=(masses[:,None]*centres).sum(0)/masses.sum()
    check('mass_consistent_with_catalogue_under_explicit_density_hypotheses',abs(masses.sum()-.310)<.031,
        estimated_mass_kg=float(masses.sum()),catalogue_mass_kg=.310,inferred_density_kg_m3=dict(metal=7850,plastic=1400),
        tolerance_fraction=.1,note='A consistency constraint, not measured part densities, centre of mass or a certified digital twin.')
    whole=trimesh.util.concatenate(list(closed.values()));transforms,_=whole.compute_stable_poses(center_mass=com,n_samples=1,threshold=.001)
    # Stable-pose output has arbitrary yaw. Choose the face-up support normal
    # before removing yaw; comparing full rotations can prefer a side pose.
    rest=max(transforms,key=lambda t:t[2,2]).copy()
    rest=trimesh.transformations.rotation_matrix(-np.arctan2(rest[1,0],rest[0,0]),[0,0,1])@rest
    contacts=[];rest_parts={}
    for n,m in closed.items():
        placed=m.copy();placed.apply_transform(rest);rest_parts[n]=placed
        contact=placed.vertices[placed.vertices[:,2]<2e-7]
        contacts.extend(dict(part=n,point_m=p.tolist()) for p in contact)
    polygon=MultiPoint([c['point_m'][:2] for c in contacts]).convex_hull
    centres_to_check=[]
    for metal,polymer in itertools.product([7700.,8100.],[900.,1600.]):
        weights=volumes*np.where(plastic,polymer,metal);c=(weights[:,None]*centres).sum(0)/weights.sum()
        c=trimesh.transform_points([c],rest)[0];centres_to_check.append(dict(metal_density_kg_m3=metal,plastic_density_kg_m3=polymer,
            transformed_com_m=c.tolist(),inside_support=bool(polygon.contains(Point(c[:2]))),support_margin_m=float(polygon.boundary.distance(Point(c[:2])))))
    check('actual_resting_contacts_support_inferred_mass_range',polygon.area>1e-7 and all(c['inside_support'] and c['support_margin_m']>.001 for c in centres_to_check)
        and min(m.bounds[0,2] for m in rest_parts.values())>=-1e-7,contacts=contacts,centres=centres_to_check)
    check('negative_distant_load_centre_rejected',not polygon.contains(Point([.3,0])))
    resting=dict(to_support_plane=rest.tolist(),contacts=contacts,support_polygon_xy_m=list(map(list,polygon.exterior.coords)),
        density_hypotheses_kg_m3=dict(metal=7850,plastic=1400),estimated_mass_kg=float(masses.sum()),
        inferred_com_m=com.tolist(),catalogue_mass_kg=.310,range_checks=centres_to_check,
        scope='Rigid closed reference on a flat support only; no settling simulation, spring/retainer locking or grasp is validated.')
    check('no_unearned_qualification',not any(record[k] for k in ['staged_in_lab','initial_stock_credit','cutting_qualified','robot_use_qualified','owner_acceptance'])
        and not record['manufacturer_joint_range_known'])
    refs=[Path(__file__),HERE/'wire_rope_cutter_assets.json',HERE/'wire_rope_cutter_sources.json',HERE/'check_weather_assets.py']
    report=dict(schema_version=1,passed=True,checks=checks,resting_reference=resting,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        cutting_qualified=False,robot_use_qualified=False,owner_acceptance=None,
        limits=['Original geometry with source-constrained overall scale; local profiles, crimp dimensions, spring and joint construction are inferred.',
            'Rigid static inspection only. No spring ends/preload, retainer stop, blade contact, cutting force, deformation, fragments or robot grasp is qualified.',
            'No physical inventory, initial stock, installation or manipulation success is credited.'])
    write_json(HERE/'wire_rope_cutter_checks.json',report)
    print(json.dumps(dict(passed=True,checks=len(checks),parts=len(closed),static_samples=len(sample_rows))))


if __name__=='__main__':build()
