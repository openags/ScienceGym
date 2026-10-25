"""Inspect actual U30 solids and static interfaces, without task execution."""
import itertools
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import trimesh
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap,minimum_discrete_bend_radius


def rotated(mesh,point,degrees):
    m=mesh.copy();m.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(degrees),[0,0,1],point));return m


def cylinder(radius,height,start,axis=(0,0,1)):
    m=trimesh.creation.cylinder(radius,height,sections=192)
    m.apply_transform(trimesh.geometry.align_vectors([0,0,1],axis))
    m.apply_translation(np.asarray(start)+np.asarray(axis)*height/2);return m


def wire_clearance(lead):
    p=np.asarray(lead['points_m']);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    s=np.linspace(0,arc[-1],int(np.ceil(arc[-1]/.00025))+1)
    q=np.column_stack([np.interp(s,arc,p[:,i]) for i in range(3)])
    pairs=cKDTree(q).query_pairs(.015,output_type='ndarray')
    pairs=pairs[np.abs(s[pairs[:,0]]-s[pairs[:,1]])>.010]
    nearest=float(np.linalg.norm(q[pairs[:,0]]-q[pairs[:,1]],axis=1).min())
    return dict(length_m=float(arc[-1]),nonlocal_exclusion_arc_m=.010,
        conservative_nonlocal_surface_gap_m=nearest-float(np.max(np.diff(s)))-2*lead['radius_m'],
        minimum_discrete_bend_radius_m=minimum_discrete_bend_radius(p))


def build():
    r=json.loads((HERE/'u30_assets.json').read_text());checks=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for ref in r['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    parts=load_parts(r['geometry']);p={n:m for n,m in parts.items() if not n.endswith('_text')}
    check('parts_and_text_count',len(parts)==143 and len(p)==138)
    for n,m in p.items():check('closed_connected_'+n,m.is_volume and len(m.split())==1)
    hits=[]
    for (n,m),(q,b) in itertools.combinations(p.items(),2):
        v=overlap(m,b)
        if not np.isfinite(v) or abs(v)>.001:hits.append(dict(parts=[n,q],overlap_mm3=v))
    check('distinct_material_domains',not hits,intersections=hits)
    enclosure=trimesh.util.concatenate([m for n,m in p.items() if not n.startswith('mount_')])
    check('manufacturer_enclosure_envelope_without_mount_kit',np.allclose(enclosure.extents,[.1806,.1181,.1887],atol=3e-7),actual_m=enclosure.extents.tolist())
    body=p['outer_case']
    check('primary_slot_open_and_optional_knockout_retained',not body.contains([[-.003,.029,.011]])[0] and body.contains([[-.003,.047,.0109]])[0])
    check('vent_is_a_real_body_opening',not body.contains([[.065,.038,.012]])[0])
    check('rear_mount_holes_remain_blind',not body.contains([[.059,.115,.174]])[0] and body.contains([[.059,.1117,.174]])[0])
    check('source_five_sockets_without_expander',len([n for n in p if n.startswith('sensor_jack_') and '_contact_' not in n])==5)
    usb=p['usb_mini_b_shell']
    check('mini_b_reference_tab_width_height_and_length',np.allclose(usb.extents,[.0099,.0093,.004],atol=4e-5),actual_m=usb.extents.tolist(),length_note='9.2 mm shell with 0.1 mm rear tab overhang; five contact tails reach source 9.4 mm overall.')
    contacts=[p['usb_contact_'+str(i)] for i in range(1,6)]
    check('five_usb_contacts_at_source_pitch',np.allclose(np.diff([m.bounds.mean(axis=0)[0] for m in contacts]),.0008,atol=1e-7))
    check('mini_b_actual_open_mouth',not usb.contains([[.055,.0202,.0745]])[0] and usb.contains([[.055,.0202,.0758]])[0])
    wire_results=[]
    for lead in r['battery_leads']:
        result=wire_clearance(lead);wire_results.append(dict(id=lead['id'],**result))
        check('continuous_wire_'+lead['id'],abs(result['length_m']-lead['measured_length_m'])<1e-10 and result['conservative_nonlocal_surface_gap_m']>0,
            **result,source_length_known=lead['source_length_known'])
        check('selected_bend_bound_'+lead['id'],result['minimum_discrete_bend_radius_m']>3*lead['radius_m'],
            scope='Three radii is a selected geometry screen; no cable manufacturer bend-radius or fatigue qualification is asserted.')
    t=np.linspace(0,np.pi,41);tight=np.column_stack([.0007*np.cos(t),.0007*np.sin(t),np.zeros(len(t))])
    check('negative_tight_wire_turn_rejected',minimum_discrete_bend_radius(tight)<.0036)
    # Articulation is an inspection of sampled rigid poses, not a controller,
    # actuator, contact simulation or proof of continuous collision freedom.
    open_parts={n:m.copy() for n,m in parts.items()};latch_angles=[0,.1,.2,.5,1,2,3,4,5,10,20,30,45,60,75,90]
    for i,axis in enumerate(r['latch_axes_m'],1):
        name='latch_clasp_'+str(i);fail=[]
        for angle in latch_angles:
            m=rotated(p[name],axis,angle)
            for n,b in p.items():
                if n==name:continue
                v=overlap(m,b)
                if not np.isfinite(v) or abs(v)>.001:fail.append(dict(angle_deg=angle,part=n,overlap_mm3=v))
        check('sampled_latch_release_'+str(i),not fail,intersections=fail,angles_deg=latch_angles)
        open_parts[name]=rotated(p[name],axis,90)
    door_angles=[0,.1,.2,.5,1,2,3,4]+list(range(5,111,5));fail=[]
    for angle in door_angles:
        door=rotated(p['hinged_door'],r['hinge_axis_m'],-angle)
        for n,b in open_parts.items():
            if n in r['door_parts'] or n.endswith('_text'):continue
            v=overlap(door,b)
            if not np.isfinite(v) or abs(v)>.001:fail.append(dict(angle_deg=angle,part=n,overlap_mm3=v))
    check('sampled_door_opening_after_release',not fail,intersections=fail,angles_deg=door_angles)
    closed_obstruction=sum(overlap(rotated(p['hinged_door'],r['hinge_axis_m'],-.2),p['latch_clasp_'+str(i)]) for i in [1,2])
    check('negative_door_against_closed_clasps',closed_obstruction>.01,overlap_mm3=closed_obstruction)
    for n in r['door_parts']:open_parts[n]=rotated(parts[n],r['hinge_axis_m'],-110)
    weather=json.loads((HERE/'weather_assets.json').read_text());sensor=next(i for i in weather['items'] if i['id']=='onset_sthb_m002')
    plug={n:m for n,m in load_parts(sensor['geometry']).items() if n.startswith('plug_contact_') or n=='modular_plug_body_and_latch'}
    check('real_seven_part_modular_plug_used',len(plug)==7)
    R=np.array([[0,1,0],[0,0,1],[1,0,0]]);fit_plug={};transforms=[]
    for i,centre in enumerate(r['sensor_jack_centres_m'],1):
        matrix=np.eye(4);matrix[:3,:3]=R;matrix[:3,3]=np.asarray(centre)-[0,0,.001]-R@np.asarray(sensor['modular_plug']['cable_entry_m']);transforms.append(matrix.tolist())
        placed={n:m.copy() for n,m in plug.items()}
        for m in placed.values():m.apply_transform(matrix)
        fail=[]
        for withdrawal in np.linspace(0,.020,11):
            for n,m in placed.items():
                moved=m.copy();moved.apply_translation([0,0,-withdrawal])
                for q,b in p.items():
                    if q=='hinged_door':continue
                    v=overlap(moved,b)
                    if not np.isfinite(v) or abs(v)>.001:fail.append(dict(withdrawal_m=float(withdrawal),parts=[n,q],overlap_mm3=v))
        check('selected_RJ12_static_fit_and_sampled_20mm_withdrawal_'+str(i),not fail,intersections=fail,
            scope='Rigid selected plug only; no cable, latch deflection, electrical contact, insertion force or hand clearance qualification.')
        filled=trimesh.creation.box([.0101,.009,.016]);filled.apply_translation([centre[0],.030,.075])
        check('negative_filled_jack_'+str(i),overlap(placed['modular_plug_body_and_latch'],filled)>1)
        if i==3:fit_plug={'selected_plug_'+n:m for n,m in placed.items()}
    mast=cylinder(.0205,.300,[0,.147,-.050]);mast=trimesh.boolean.difference([mast,cylinder(.0185,.302,[0,.147,-.051])],engine='manifold')
    fail=[]
    for n,m in p.items():
        v=overlap(m,mast)
        if not np.isfinite(v) or abs(v)>.001:fail.append(dict(part=n,overlap_mm3=v))
    check('mount_kit_and_case_clear_selected_41mm_mast',not fail,intersections=fail)
    shifted=mast.copy();shifted.apply_translation([.006,0,0])
    check('negative_lateral_mast_misalignment',sum(overlap(shifted,p['mount_'+str(i)+'_u_bolt']) for i in [1,2])>1)
    check('no_unearned_qualification',not any(r[k] for k in ['staged_in_lab','initial_stock_credit','weatherproof_qualified','robot_use_qualified','owner_acceptance']) and not r['mounting']['load_qualified'])
    g=Geometry()
    for n,m in {**open_parts,**fit_plug,'selected_mast_fixture':mast}.items():
        g.scene.add_geometry(m,node_name=n,geom_name=n);g.parts.append(dict(id=n,role='static_interface_inspection',bounds_m=m.bounds.tolist()))
    fit=g.export('onset_u30_nrc_static_interface_fit')
    refs=[Path(__file__),HERE/'u30_assets.json',HERE/'weather_assets.json',HERE/'check_weather_assets.py']
    report=dict(schema_version=1,passed=True,checks=checks,fit_geometry=fit,plug_transforms=transforms,battery_wire_checks=wire_results,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        robot_use_qualified=False,weatherproof_qualified=False,owner_acceptance=None,
        limits=['Static candidate with explicit local inferences, not exact Onset CAD or identified paper SKU.',
            'Sampled articulation and plug withdrawal do not establish continuous contact-based manipulation.',
            'No sensor cable installation, mounting tool access, grounding, battery/USB electrical performance, seal compression or load qualification.',
            'Standalone inspection fixture does not add inventory or stage a weather station in the main laboratory.'])
    write_json(HERE/'u30_checks.json',report);print(json.dumps(dict(passed=True,checks=len(checks),fit_parts=fit['parts'])))


if __name__=='__main__':build()
