"""Independent exported-mesh checks for the isolated cover candidate."""
import itertools
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE, ROOT, sha, write_json
from build_stock_cutplan import load_parts
from check_apparatus_frame import solid, intersection_mm3


def contacts(parts, tolerance=2e-7):
    edges=[]
    for a,b in itertools.combinations(parts,2):
        aa,bb=parts[a].bounds,parts[b].bounds
        if np.any(np.maximum(aa[0],bb[0])-np.minimum(aa[1],bb[1])>tolerance):continue
        manager=trimesh.collision.CollisionManager();manager.add_object(a,parts[a])
        if manager.min_distance_single(parts[b])<=tolerance:edges.append([a,b])
    return edges


def connected(edges, start, end, absent=()):
    visited={start};pending=[start]
    while pending:
        n=pending.pop()
        for a,b in edges:
            if a in absent or b in absent:continue
            other=b if n==a else a if n==b else None
            if other is not None and other not in visited:visited.add(other);pending.append(other)
    return end in visited


def build():
    record=json.loads((HERE/'apparatus_cover_candidate.json').read_text())
    rejected=json.loads((HERE/'cover_legacy_rejected.json').read_text())
    p=load_parts(record['geometry']['path']);old=load_parts(rejected['geometry']['path']);checks=[]
    def check(name,value,**details):
        checks.append(dict(name=name,passed=bool(value),**details))
        if not value:raise AssertionError(name+' '+str(details))
    for ref in record['source_artifacts']+[record['geometry'],record['sections'],rejected['geometry']]:
        check('pinned_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    for name,m in p.items():
        s=solid(m)
        check('positive_closed_consistent_'+name,s.is_volume and np.isfinite(s.vertices).all())
    caps=load_parts(record['sections']['path'])
    check('section_matches_intersected_parts',set(caps)=={n for n,m in p.items() if m.bounds[0,1]<.0005<m.bounds[1,1]} and set(record['sections']['uncut_parts'])==set(p)-set(caps))
    for name,m in caps.items():
        check('actual_planar_section_'+name,np.max(abs(m.vertices[:,1]-.0005))<1e-8 and m.area>0)
    for name,x,z,expected in [('PE_support',0,.025,False),('PE_support',.045,.025,True),('film_spacer',.052,.054,False),('film_spacer',.060,.054,True)]:
        check('section_preserves_hole_'+name+'_'+str(x),bool(caps[name].ray.intersects_any([[x,-.1,z]],[[0,1,0]])[0])==expected)
    check('section_area_PE_wall',abs(caps['PE_support'].area*1e6-1326)<.01)
    check('section_area_shield_wall',abs(caps['radiation_shield'].area*1e6-684)<.01)
    check('thin_film_section_not_filled_envelope',2< caps['cover_lower'].area*1e6 <2.1)
    check('legacy_coating_is_invalid',not solid(old['emitter_white_coating']).is_volume)
    check('legacy_copper_has_inconsistent_faces',not solid(old['emitter_copper']).is_winding_consistent)
    check('legacy_shield_gap_retained',abs(old['radiation_shield'].bounds[0,2]-.0064)<1e-7)
    check('legacy_lower_film_straddles_tube_plane',old['cover_lower'].bounds[0,2]<old['PE_support'].bounds[1,2]<old['cover_lower'].bounds[1,2])
    for name,inner,outer,height in [('PE_support',.076,.102,.051),('film_spacer',.107,.127,.0064),('radiation_shield',.140,.152,.057),('aperture_plate',.050,.152,.001)]:
        m=p[name];r=np.linalg.norm(m.vertices[:,:2],axis=1)
        check('real_annular_dimensions_'+name,abs(2*r.min()-inner)<2e-7 and abs(2*r.max()-outer)<2e-7 and abs(m.extents[2]-height)<2e-7 and not m.contains([m.bounds.mean(axis=0)]).any())
    for name in ['cover_lower_adhesive','cover_upper_adhesive']:
        check('selected_58_micrometre_adhesive_'+name,abs(p[name].extents[2]-.000058)<1e-8)
    for a,b in [('lift_plate','foam_1'),('foam_1','foam_2'),('foam_2','emitter_copper'),('emitter_copper','emitter_white_coating'),('lift_plate','radiation_shield'),('radiation_shield','aperture_bond'),('aperture_bond','aperture_plate')]:
        check('actual_bearing_planes_'+a+'_'+b,abs(p[a].bounds[1,2]-p[b].bounds[0,2])<1e-8)
    check('central_film_emitter_gap',p['cover_lower'].bounds[1,2]-.000016-p['emitter_white_coating'].bounds[1,2]>.00043)
    check('upper_film_aperture_gap',p['aperture_plate'].bounds[0,2]-p['cover_upper'].bounds[1,2]>.00042)
    check('enlarged_platform_has_selected_size',np.allclose(p['lift_plate'].extents,[.180,.180,.005],atol=2e-7))
    check('aperture_bond_has_actual_gauge',abs(p['aperture_bond'].extents[2]-.000058)<1e-8)
    for x in [-.0374904,.0374904]:
        for y in [-.0124968,.0124968]:
            check('retained_source_jack_hole_'+str((x,y)),not p['lift_plate'].ray.intersects_any([[x,y,.01]],[[0,0,-1]])[0])
    unsupported_old=[]
    for joint in record['details']['retention']['connections']:
        i=joint['index'];angle=p['shield_angle_'+str(i)];base=p['shield_base_screw_'+str(i)];side=p['shield_side_screw_'+str(i)];ring=p['shield_base_washer_'+str(i)]
        foot=angle.vertices[angle.vertices[:,2]<.0015875+1e-8]
        check('angle_foot_inside_platform_'+str(i),np.all(foot[:,:2]>=p['lift_plate'].bounds[0,:2]-1e-8) and np.all(foot[:,:2]<=p['lift_plate'].bounds[1,:2]+1e-8))
        unsupported_old.append(bool(np.any(foot[:,:2]<old['lift_plate'].bounds[0,:2]) or np.any(foot[:,:2]>old['lift_plate'].bounds[1,:2])))
        check('washer_rests_on_angle_'+str(i),abs(ring.bounds[0,2]-.0015875)<1e-8)
        check('base_screw_stays_inside_plate_'+str(i),abs(base.bounds[0,2]+.0036125)<1e-8 and base.bounds[0,2]>p['lift_plate'].bounds[0,2]+.001)
        outward=-np.array(joint['side_screw_axis']);projected=side.vertices@outward
        check('side_screw_stays_inside_wall_'+str(i),abs(projected.min()-.0715875)<2e-7 and projected.min()>.071)
        x,y=joint['base_center_xy_m']
        check('base_thread_envelope_open_'+str(i),not p['lift_plate'].ray.intersects_any([[x,y,.01]],[[0,0,-1]])[0])
    check('negative_previous_platform_does_not_support_all_angles',any(unsupported_old))
    # Measure the actual two intersections along an exported lower-face normal,
    # including the sloped transition. Do not infer gauge from a Z envelope.
    m=p['cover_lower'];gauges=[]
    for radius in [.015,.045,.0511,.0515,.052,.0525,.053,.05335,.060]:
        theta=np.pi/256;origin=[radius*np.cos(theta),radius*np.sin(theta),.045]
        hits,_,faces=m.ray.intersects_location([origin],[[0,0,1]],multiple_hits=True)
        order=np.argsort(hits[:,2]);check('two_vertical_film_surfaces_'+str(radius),len(hits)==2)
        hit=hits[order[0]];direction=-m.face_normals[faces[order[0]]]
        across,_,_=m.ray.intersects_location([hit-direction*.000010],[direction],multiple_hits=True)
        distance=np.sort((across-hit)@direction)
        gauge=float(distance[1]-distance[0]) if len(distance)==2 else float('nan')
        check('normal_film_gauge_'+str(radius),len(distance)==2 and abs(gauge-.000016)<2e-7,measured_m=gauge)
        gauges.append(gauge)
    intersections=[]
    for a,b in itertools.combinations(p,2):
        overlap=np.minimum(p[a].bounds[1],p[b].bounds[1])-np.maximum(p[a].bounds[0],p[b].bounds[0])
        if np.any(overlap<=0):continue
        declared_thread=any((n.startswith('shield_base_screw_') and other=='lift_plate') or (n.startswith('shield_side_screw_') and other=='radiation_shield') for n,other in [(a,b),(b,a)])
        v=intersection_mm3(p[a],p[b]);check('no_solid_overlap_'+a+'_'+b,v<(.05 if declared_thread else .001),volume_mm3=v,nominal_thread_envelope=declared_thread)
        intersections.append(dict(parts=[a,b],volume_mm3=v,nominal_thread_envelope=declared_thread,physical_mating_qualified=False))
    edges=contacts(p)
    check('ring_has_geometric_path_to_platform',connected(edges,'film_spacer','lift_plate'))
    check('negative_no_invisible_support_without_lower_membrane',not connected(edges,'film_spacer','lift_plate',['cover_lower']))
    check('negative_no_hidden_ring_bond_without_lower_adhesive',not connected(edges,'film_spacer','lift_plate',['cover_lower_adhesive']))
    check('standalone_inspection_not_physical_qualification',record['standalone_inspection_artifact'] and record['owner_acceptance'] is None and not record['details']['assembly_qualified'] and not record['details']['membrane_equilibrium_qualified'])
    report=dict(passed=True,checks=checks,geometric_contacts=edges,solid_intersections=intersections,
        measured_lower_membrane_normal_gauge_m=gauges,physical_load_path_qualified=False,
        scope='Isolated nominal geometry, contact connectivity and retained failures only. No membrane equilibrium, adhesion, retention, dynamics or robot operation is established.',
        source_artifacts=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in [Path(__file__),HERE/'apparatus_cover_candidate.json',HERE/'cover_legacy_rejected.json',HERE/'check_apparatus_frame.py']],
        owner_acceptance=None)
    write_json(HERE/'apparatus_cover_checks.json',report)
    print(json.dumps(dict(passed=True,checks=len(checks),contact_edges=len(edges),physical_load_path_qualified=False)))


if __name__=='__main__':build()
