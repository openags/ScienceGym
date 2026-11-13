"""Check actual weather solids, cable lengths and a separate probe clearance.

No installation, electrical operation, thermal response or robot task is tested.
The reported cable separation is a conservative dense-centerline bound. It is
not a flexible-cable simulation or evidence of a gravity-settled rest shape.
"""
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import trimesh
from geometry_tools import HERE, ROOT, sha, write_json


def load_parts(ref):
    assert sha(ROOT/ref['path']) == ref['sha256'], ref['path']
    scene=trimesh.load(ROOT/ref['path'],force='scene');parts={}
    for name in scene.graph.nodes_geometry:
        matrix,key=scene.graph[name];mesh=scene.geometry[key].copy()
        mesh.apply_transform(matrix);mesh.merge_vertices(digits_vertex=8)
        mesh.fix_normals();parts[name]=mesh
    return parts


def overlap(a,b):
    if np.any(np.minimum(a.bounds[1],b.bounds[1])-np.maximum(a.bounds[0],b.bounds[0]) <= 1e-8):
        return 0.
    result=trimesh.boolean.intersection([a,b],engine='manifold')
    return float(result.volume*1e9) if len(result.faces) else 0.


def cable_clearance(lead):
    p=np.array(lead['points_m']);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    sample_arc=np.linspace(0,arc[-1],int(np.ceil(arc[-1]/.00025))+1)
    sampled=np.column_stack([np.interp(sample_arc,arc,p[:,i]) for i in range(3)])
    # Every location on each polyline segment lies within half a sample step
    # of some sample. Subtracting a full step bounds pairwise separation.
    step=float(np.max(np.diff(sample_arc)))
    pairs=cKDTree(sampled).query_pairs(.009,output_type='ndarray')
    pairs=pairs[np.abs(sample_arc[pairs[:,0]]-sample_arc[pairs[:,1]])>.010]
    minimum=float(np.min(np.linalg.norm(sampled[pairs[:,0]]-sampled[pairs[:,1]],axis=1)))
    return dict(actual_length_m=float(arc[-1]),sample_step_m=step,
        nonlocal_exclusion_arc_m=.010,minimum_sample_distance_m=minimum,
        conservative_nonlocal_surface_gap_m=minimum-step-2*lead['radius_m'])


def minimum_discrete_bend_radius(points):
    segments=np.diff(points,axis=0);lengths=np.linalg.norm(segments,axis=1)
    directions=segments/lengths[:,None]
    curvature=np.linalg.norm(np.diff(directions,axis=0),axis=1)/((lengths[:-1]+lengths[1:])/2)
    return float(1/np.max(curvature))


def build():
    record=json.loads((HERE/'weather_assets.json').read_text())
    ledger=json.loads((HERE/'weather_sources.json').read_text())
    checks=[];intersections=[];clearances=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for ref in record['source_artifacts']:
        check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    check('scope_does_not_credit_installation',not record['staged_in_lab'] and not record['weather_station_complete'] and record['owner_acceptance'] is None)
    sources={s['id']:s for s in ledger['sources']};models={}
    for item in record['items']:
        identity=item['id'];parts=load_parts(item['geometry']);models[identity]=parts
        check('parts_'+identity,len(parts)==item['geometry']['parts'])
        check('sources_'+identity,all(s in sources for s in item['source_ids']))
        for name,m in parts.items():
            check('single_volume_'+identity+'/'+name,m.is_volume and len(m.split())==1)
        for i,(name,a) in enumerate(parts.items()):
            for other,b in list(parts.items())[i+1:]:
                volume=overlap(a,b)
                if volume>.001:
                    allowed=identity=='onset_rs3' and {name,other} in [
                        {'tie_rod_left','knurled_nut_left'}, {'tie_rod_right','knurled_nut_right'}]
                    intersections.append(dict(model=identity,parts=[name,other],volume_mm3=volume,
                        interpretation='Nominal internal/external thread envelopes; flank contact is not modeled' if allowed else 'Unexplained overlap'))
                    check('declared_overlap_'+identity+'/'+name+'/'+other,allowed)
        for lead in item.get('stored_leads',[]):
            result=cable_clearance(lead)
            result['minimum_discrete_bend_radius_m']=minimum_discrete_bend_radius(lead['points_m'])
            clearances.append(dict(id=lead['id'],**result))
            check('measured_length_'+lead['id'],abs(result['actual_length_m']-lead['length_m'])<1e-8,**result)
            check('nonlocal_cable_clearance_'+lead['id'],result['conservative_nonlocal_surface_gap_m']>0)
            check('local_bend_exceeds_three_wire_radii_'+lead['id'],result['minimum_discrete_bend_radius_m']>3*lead['radius_m'])
            check('lead_endpoints_'+lead['id'],np.allclose(np.array(lead['points_m'])[[0,-1]],lead['endpoints_m'],atol=1e-10))
    check('only_declared_thread_intersections',len(intersections)==2,intersections=intersections)
    theta=np.linspace(0,np.pi,41)
    tight_turn=np.column_stack([.0007*np.cos(theta),.0007*np.sin(theta),np.zeros(len(theta))])
    check('negative_submillimetre_turn_rejected',minimum_discrete_bend_radius(tight_turn)<3*.0015)
    shield=models['onset_rs3'];probe=models['onset_sthb_m002']
    lamella=trimesh.util.concatenate([m for n,m in shield.items() if n.startswith('shield_lamella_')])
    check('source_shield_envelope',np.allclose(lamella.extents,[.102,.102,.089],atol=2e-7),actual_m=lamella.extents.tolist())
    ceiling=lamella.ray.intersects_location([[0,0,0]],[[0,0,1]])[0][:,2].min()
    check('source_closed_ceiling',abs(ceiling-.065)<2e-7,actual_m=float(ceiling))
    bracket=shield['inclined_mounting_bracket']
    check('source_bracket_total_height',abs(lamella.bounds[1,2]-bracket.bounds[0,2]-.159)<2e-7)
    check('source_bracket_rear_projection',abs(-bracket.bounds[0,1]-.051-.102)<2e-7)
    check('bracket_cable_hole_open',not bracket.ray.intersects_any([[0,0,-.02]],[[0,0,1]])[0])
    head=trimesh.util.concatenate([probe[n] for n in ['probe_receptacle','rh_membrane_cap']])
    check('source_probe_envelope',np.allclose(head.extents,[.035,.010,.010],atol=2e-7),actual_m=head.extents.tolist())
    contacts=[probe['plug_contact_'+str(i)] for i in range(1,7)]
    check('six_contacts_at_catalog_pitch',np.allclose(np.diff([m.bounds.mean(axis=0)[1] for m in contacts]),.00102,atol=2e-7))
    check('plug_catalog_width',abs(probe['modular_plug_body_and_latch'].extents[1]-.00965)<2e-7)
    plug_hits=probe['modular_plug_body_and_latch'].ray.intersects_location([[-.101,.28,.0078]],[[1,0,0]])[0]
    first_surface=float(plug_hits[:,0].min())
    check('plug_cable_opening',first_surface>-.092,first_internal_surface_x_m=first_surface)
    # Inspect a physically separate head inside the shield. The cable, ties
    # and full adapter are deliberately absent from this clearance-only case.
    scene=trimesh.Scene();head_pose=trimesh.transformations.rotation_matrix(-np.pi/2,[0,1,0]);head_pose[:3,3]=[.015,0,.005]
    core={n:m for n,m in shield.items() if not n.startswith(('loose_','optional_','band_','mast_'))}
    for name,m in core.items():scene.add_geometry(m.copy(),node_name='shield__'+name,geom_name='shield__'+name)
    installed=[]
    for name in ['probe_receptacle','rh_membrane_cap','sensor_board_envelope','probe_strain_relief_candidate']:
        m=probe[name].copy();m.apply_transform(np.linalg.inv(head_pose));installed.append(m)
        scene.add_geometry(m,node_name='probe__'+name,geom_name='probe__'+name)
    maximum=max(overlap(a,b) for a in installed for b in core.values())
    check('isolated_probe_head_fits_nominal_shield',maximum<.001,maximum_overlap_mm3=maximum)
    upper=max(m.bounds[1,2] for m in installed)
    check('positive_head_ceiling_gap',ceiling-upper>.0149,actual_gap_m=float(ceiling-upper))
    oversize=head.copy();oversize.apply_transform(np.linalg.inv(head_pose));oversize.apply_translation([0,0,.03])
    check('negative_overheight_probe_hits_closed_lid',sum(overlap(oversize,b) for b in core.values())>1)
    path=HERE/'geometry/weather_probe_clearance.glb';path.write_bytes(scene.export(file_type='glb',include_normals=True))
    refs=[Path(__file__),HERE/'weather_assets.json',HERE/'weather_sources.json']
    report=dict(passed=True,checks=checks,declared_intersections=intersections,cable_clearances=clearances,
        inspection_sample=dict(path=str(path.relative_to(ROOT)),sha256=sha(path),parts=len(scene.geometry)),
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        assembly_qualified=False,electrical_qualified=False,robot_use_qualified=False,owner_acceptance=None,
        limits=['Probe sample checks only head/rigid-shield clearance; it does not include installed cable routing or retention.',
            'Dense centerline clearance excludes local neighbors within 10 mm of arc length; no bending stiffness or gravity settling.',
            'Discrete local bend radius exceeds three selected wire radii; this is a geometric fold screen, not a manufacturer cable bend rating.',
            'Clamp worm teeth, screw threads, membrane transport and weather response are not modeled.'])
    write_json(HERE/'weather_asset_checks.json',report)
    print(json.dumps(dict(passed=True,checks=len(checks),component_models=len(models),cable_clearances=clearances)))


if __name__=='__main__':build()
