"""Inspect exported tool solids and fit them to existing fastener geometry.

These are isolated dimensional/mating checks. They do not simulate torque or
approve hand access, fastening order, wrench swing or robot manipulation.
"""
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE, ROOT, sha, write_json
from build_stock_cutplan import load_parts
from build_apparatus_mounting import cap_screw, countersunk_screw, display
from build_apparatus_frame import screw, csk_m3x10, nut
from check_apparatus_frame import solid, intersection_mm3


def build():
    record=json.loads((HERE/'fastener_tools.json').read_text());ledger=json.loads((HERE/'fastener_tools_sources.json').read_text())
    checks=[];fits=[];samples=trimesh.Scene();items={r['id']:r for r in record['items']};meshes={k:load_parts(i['geometry']['path']) for k,i in items.items()}
    def check(name,passed,**data):
        checks.append(dict(name=name,passed=bool(passed),**data))
        if not passed:raise AssertionError(name+' '+str(data))
    for ref in record['source_artifacts']:
        check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    for identity,item in items.items():
        parts=meshes[identity];spec=ledger['items'][identity]
        check('export_'+identity,sha(ROOT/item['geometry']['path'])==item['geometry']['sha256'])
        for n,m in parts.items():
            if n=='size_label':continue
            s=solid(m);check('closed_single_solid_'+identity+'/'+n,s.is_volume and len(s.split())==1)
        bounds=np.array([m.bounds for m in parts.values()]);length=bounds[:,1,0].max()-bounds[:,0,0].min()
        check('catalog_overall_length_'+identity,abs(length-spec['overall_mm']*.001)<2e-6,actual_mm=length*1000)
        if identity.startswith('wiha'):
            handle=parts['handle'];shaft=parts['shaft'];cap=parts['rotating_cap']
            check('published_blade_length_'+identity,abs(handle.bounds[0,0]-shaft.bounds[0,0]-spec['blade_mm']*.001)<1e-7)
            section=shaft.section(plane_origin=[.010,0,0],plane_normal=[1,0,0]);points=section.vertices[:,1:]
            widths=[np.ptp(points@np.array([np.cos(a),np.sin(a)])) for a in np.arange(6)*np.pi/3]
            check('selected_hex_clearance_'+identity,np.max(abs(np.array(widths)*1000-(spec['drive_mm']-.02)))<1e-5,af_mm=(np.array(widths)*1000).tolist())
            check('buried_shaft_does_not_overlap_plastic_'+identity,intersection_mm3(handle,shaft)<.001)
            check('cap_separate_at_rear_'+identity,abs(handle.bounds[1,0]-cap.bounds[0,0])<1e-7 and intersection_mm3(handle,cap)<.001)
            front=handle.section(plane_origin=[handle.bounds[0,0]+.002,0,0],plane_normal=[1,0,0])
            rear=handle.section(plane_origin=[handle.bounds[1,0]-.002,0,0],plane_normal=[1,0,0])
            check('photo_grip_widens_toward_cap_'+identity,np.ptp(rear.vertices[:,1])>np.ptp(front.vertices[:,1])*1.3)
    cases=[('jack_M3_cap',cap_screw(),0,1.3,'wiha_26325'),
           ('platform_M3_countersunk',countersunk_screw(),0,1.1,'wiha_26320'),
           ('frame_M3_cap',screw(3,6),-3,1.3,'wiha_26325'),
           ('frame_M4_cap',screw(4,40),-4,2,'wiha_26330'),
           ('frame_M5_button',screw(5,16,'button'),-2.63,1.3,'wiha_26330'),
           ('carriage_M3_countersunk',csk_m3x10(),0,1.1,'wiha_26320')]
    align=trimesh.geometry.align_vectors([1,0,0],[0,0,-1])
    for name,fastener,opening,depth,identity in cases:
        matrix=align.copy();matrix[:3,3]=[0,0,(opening+depth-.15)*.001]
        # Evaluate all physical tool parts, including the handle; the matching
        # socket must remain a real void in the independent fastener solid.
        maximum=0
        for part,m in meshes[identity].items():
            posed=m.copy();posed.apply_transform(matrix)
            if part!='size_label':
                v=intersection_mm3(posed,fastener);maximum=max(maximum,v)
            samples.add_geometry(posed,node_name=name+'__'+part,geom_name=name+'__'+part)
        samples.add_geometry(display(fastener),node_name=name+'__fastener',geom_name=name+'__fastener')
        check('nominal_isolated_socket_fit_'+name,maximum<.001,intersection_mm3=maximum)
        rotated=meshes[identity]['shaft'].copy();turn=trimesh.transformations.rotation_matrix(np.radians(2),[1,0,0]);rotated.apply_transform(matrix@turn)
        interference=intersection_mm3(rotated,fastener)
        check('socket_has_driving_faces_'+name,interference>.001,rotated_intersection_mm3=interference)
        fits.append(dict(id=name,tool=identity,tool_from_local=matrix.tolist(),maximum_intersection_mm3=maximum,
            two_degree_rotation_interference_mm3=interference,scope='isolated geometric fit, not an applied torque or assembled access test'))
    wrong=meshes['wiha_26330']['shaft'].copy();m=align.copy();m[:3,3]=[0,0,.00095];wrong.apply_transform(m)
    check('negative_3mm_driver_cannot_enter_2mm_socket',intersection_mm3(wrong,countersunk_screw())>.1)
    wrench=meshes['stahlwille_40080808']['forged_wrench'];interface=items['stahlwille_40080808']['interface']
    # Compare a separate catalog mass to geometric volume under a declared
    # assumed steel density; do not force mass agreement by scaling the tool.
    geometric_mass=float(solid(wrench).volume*7850)
    mass_comparison=dict(assumed_steel_density_kg_m3=7850,geometric_mass_kg=geometric_mass,catalog_mass_kg=.021,
        relative_difference=(geometric_mass-.021)/.021,mass_distribution_qualified=False)
    # The open end is usable without requiring a full pass over a threaded rod.
    n=nut();jaw=np.asarray(interface['open_jaw_center_m']);angle=np.radians(interface['open_jaw_angle_degrees'])
    matrix=trimesh.transformations.rotation_matrix(angle,[0,0,1]);matrix[:3,3]=jaw-[0,0,.00235]
    n.apply_transform(matrix);overlap=intersection_mm3(n,wrench)
    check('nominal_8mm_open_jaw_fit',overlap<.001,intersection_mm3=overlap)
    for name,m in [('wrench',wrench),('nut',display(n))]:samples.add_geometry(m.copy(),node_name='open_jaw__'+name,geom_name='open_jaw__'+name)
    big=nut();big.vertices[:,:2]*=9/8;big.apply_transform(matrix)
    check('negative_9mm_nut_cannot_enter_8mm_jaw',intersection_mm3(big,wrench)>.05)
    n=nut();matrix=trimesh.geometry.align_vectors([0,0,1],interface['ring_axis']);matrix[:3,3]=np.array(interface['ring_center_m'])-np.array(interface['ring_axis'])*.00235;n.apply_transform(matrix)
    overlap=intersection_mm3(n,wrench)
    check('nominal_8mm_bihex_ring_fit',overlap<.001,intersection_mm3=overlap)
    for name,m in [('wrench',wrench),('nut',display(n))]:samples.add_geometry(m.copy(),node_name='bihex_ring__'+name,geom_name='bihex_ring__'+name)
    check('ring_profile_limit_not_hidden',not interface['exact_as_drive_profile'])
    # Real open passage through the ring, not a black painted disk.
    origin=np.array(interface['ring_center_m'])-np.array(interface['ring_axis'])*.015
    check('ring_has_open_through_bore',not wrench.ray.intersects_any([origin],[interface['ring_axis']])[0])
    files=[Path(__file__),HERE/'fastener_tools.json',HERE/'fastener_tools_sources.json',HERE/'build_apparatus_frame.py',HERE/'build_apparatus_mounting.py',HERE/'check_apparatus_frame.py']
    sample_path=HERE/'geometry/fastener_tool_fit_samples.glb';sample_path.write_bytes(samples.export(file_type='glb',include_normals=True))
    write_json(HERE/'fastener_tool_checks.json',dict(passed=True,checks=checks,isolated_socket_fits=fits,
        inspection_samples=dict(path=str(sample_path.relative_to(ROOT)),sha256=sha(sample_path),parts=len(samples.geometry),groups=[r['id'] for r in fits]+['open_jaw','bihex_ring']),
        wrench_mass_comparison=mass_comparison,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in files],
        appearance_accepted=False,assembled_access_qualified=False,torque_qualified=False,robot_use_qualified=False,owner_acceptance=None,
        limits=['All mating cases are isolated tool/fastener checks; no whole-apparatus swing, insertion path, tolerances, strength, hand grasp or torque has been accepted']))
    print(json.dumps(dict(passed=True,checks=len(checks),isolated_socket_fits=len(fits),assembled_access_qualified=False)))


if __name__=='__main__':build()
