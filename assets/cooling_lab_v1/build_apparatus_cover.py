"""Isolated film-supported ring candidate; no scene or execution acceptance.

The previous cover is retained as actual geometry before any integration.
Published dimensions are preserved. Membrane drape, support height and adhesive
are explicit hypotheses requiring later contact and membrane qualification.
"""
import json
from pathlib import Path
import numpy as np
import trimesh
import manifold3d
from geometry_tools import HERE, ROOT, sha, write_json
from build_apparatus_mounting import display
from build_stock_cutplan import load_parts
from build_cover_retention import apply_retention

PARTS = ['lift_plate', 'foam_1', 'foam_2', 'foam_mylar_1', 'foam_mylar_2',
         'emitter_copper', 'emitter_white_coating', 'PE_support', 'PE_support_mylar',
         'cover_lower', 'cover_upper', 'film_spacer', 'radiation_shield', 'aperture_plate']
PREFIX = 'COOLER_WHITE__'


def export(parts, path):
    scene = trimesh.Scene()
    for n, m in parts.items():
        scene.add_geometry(m, node_name=n, geom_name=n)
    path.write_bytes(scene.export(file_type='glb', include_normals=True))
    return dict(path=str(path.relative_to(ROOT)), sha256=sha(path), parts=len(parts))


def capture_legacy():
    record_path = HERE / 'cover_legacy_rejected.json'
    if record_path.exists():
        record = json.loads(record_path.read_text())
        assert sha(ROOT / record['geometry']['path']) == record['geometry']['sha256']
        return record
    source = 'assets/cooling_lab_v1/geometry/apparatus_cooler_white.glb'
    parts = load_parts(source)
    center = parts[PREFIX+'lift_plate'].bounds.mean(axis=0)
    center[2] = parts[PREFIX+'lift_plate'].bounds[1, 2]
    retained = {}
    for suffix in PARTS:
        m = parts[PREFIX+suffix].copy()
        m.apply_translation(-center)
        retained[suffix] = m
    gap = float(retained['radiation_shield'].bounds[0, 2])
    assert abs(gap-.0064) < 1e-7, 'Only the observed legacy failure may be captured'
    record = dict(schema_version=1,
        geometry=export(retained, HERE/'geometry'/'cover_legacy_rejected.glb'),
        historical_source_path=source, historical_source_sha256=sha(ROOT/source),
        historical_revision='3a91fa9115eaa59851478b503c01aa64c13e9776',
        normalization_translation_m=(-center).tolist(),
        observed_shield_platform_gap_m=gap,
        observations=['Unsupported shield above platform',
            'Ring bore exceeds PE outside diameter; no direct rigid bearing',
            'Films centered on nominal interfaces penetrate adjacent solids'],
        purpose='Retained actual earlier cover geometry; never updated to match a later candidate')
    write_json(record_path, record)
    return record


def membrane(thickness, inner_bottom, outer_top, transition, radius=.0635, sections=256):
    """Closed normal-offset membrane, smooth between two horizontal annuli."""
    r0, r1 = transition
    radii = np.r_[0., .038, .050, np.linspace(r0, r1, 33), radius]
    u = np.clip((radii-r0)/(r1-r0), 0, 1)
    h0, h1 = inner_bottom+thickness/2, outer_top-thickness/2
    mid = h0+(h1-h0)*(3*u*u-2*u*u*u)
    slope = (h1-h0)*6*u*(1-u)/(r1-r0)
    norm = np.sqrt(1+slope*slope)
    angles = np.arange(sections)*2*np.pi/sections
    vertices = []
    for sign in [-1, 1]:
        for r, z, derivative, length in zip(radii, mid, slope, norm):
            rr = r-sign*thickness*.5*derivative/length
            zz = z+sign*thickness*.5/length
            vertices.extend(np.c_[rr*np.cos(angles), rr*np.sin(angles), np.full(sections, zz)])
    faces = []
    layer = len(radii)*sections
    for side in range(2):
        offset = side*layer
        for row in range(len(radii)-1):
            for j in range(sections):
                a=offset+row*sections+j; b=offset+row*sections+(j+1)%sections
                faces.extend([[a,b,b+sections],[a,b+sections,a+sections]])
    edge=(len(radii)-1)*sections
    for j in range(sections):
        a=edge+j; b=edge+(j+1)%sections
        faces.extend([[a,a+layer,b+layer],[a,b+layer,b]])
    m=trimesh.Trimesh(vertices=vertices,faces=faces,process=True)
    m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices();m.fix_normals()
    assert m.is_watertight and m.is_winding_consistent and m.volume>0
    return m


def review_wrap(radius, height, center):
    # Keep the nominal 12 micrometre film gauge. The 0.1 micrometre seam
    # separation is only an explicitly recorded numerical self-contact guard,
    # not a physical adhesive layer or a measured bending radius.
    gauge=.000012;lap=.003;separation=.0000001
    theta=np.r_[np.linspace(0,2*np.pi,1025),np.linspace(2*np.pi,2*np.pi+lap/radius,33)[1:]]
    guard=radius/np.cos(np.diff(theta).max()/2)-radius+2*float(np.spacing(np.float32(radius)))
    offset=(gauge+separation)*np.clip((theta-(2*np.pi-.001/radius))/(.001/radius),0,1)
    vertices=[];faces=[]
    for angle,step in zip(theta,offset):
        for r,z in [(radius+guard+step,-height/2),(radius+guard+step+gauge,-height/2),
                    (radius+guard+step+gauge,height/2),(radius+guard+step,height/2)]:
            vertices.append([r*np.cos(angle),r*np.sin(angle),z])
    for i in range(len(theta)-1):
        for j in range(4):
            a=4*i+j;b=4*i+(j+1)%4;c=b+4;d=a+4
            faces.extend([[a,b,c],[a,c,d]])
    faces.extend([[0,2,1],[0,3,2]]);a=4*(len(theta)-1)
    faces.extend([[a,a+1,a+2],[a,a+2,a+3]])
    m=trimesh.Trimesh(vertices=np.array(vertices)+center,faces=faces,process=False);m.fix_normals()
    assert m.is_watertight
    return m,dict(gauge_m=gauge,lap_m=lap,radial_faceting_guard_m=guard,seam_numerical_separation_m=separation)


def candidate(parts, ledger):
    # All coordinates are relative to the platform upper face. The input
    # dictionary is a separate snapshot; the current laboratory is untouched.
    result={n:m.copy() for n,m in parts.items()};changes=[]
    selection=ledger['selected_geometry_hypothesis'];facts=ledger['paper']['facts']
    h=selection['pe_support_height_mm']*.001
    ring_bottom=selection['ring_bottom_above_platform_mm']*.001
    ring_top=ring_bottom+facts['ring_thickness_mm']*.001
    t=facts['cover_layer_thickness_mm']*.001
    adhesive=ledger['adhesive_candidate']['nominal_adhesive_thickness_mm']*.001
    def put(name, m):
        m=display(m)
        if name in result:m.visual=parts[name].visual.copy()
        result[name]=m;changes.append(name)
    def annulus(inner,outer,height,bottom):
        m=trimesh.creation.annulus(inner,outer,height,sections=256)
        m.apply_translation([0,0,bottom+height/2]);return m
    # Source float32 transforms left nanometre-scale gaps/penetrations between
    # otherwise mating stack planes. Translate each unchanged mesh onto the
    # preceding real upper face; record every adjustment, without rescaling.
    stack_adjustments={};bottom=0.
    for name in ['foam_1','foam_2','emitter_copper']:
        m=result[name].copy();shift=bottom-float(m.bounds[0,2])
        assert abs(shift)<2e-8
        # apply_transform treats these tiny translations as identity; update
        # the vertices explicitly so the recorded correction actually occurs.
        m.vertices=m.vertices+np.array([0,0,shift]);stack_adjustments[name]=shift
        if name=='emitter_copper':
            m.merge_vertices(merge_norm=True,merge_tex=True,digits_vertex=8)
            m.fix_normals(multibody=True)
        put(name,m);bottom=float(m.bounds[1,2])
    put('PE_support',annulus(.038,.051,h,0))
    wraps={}
    for substrate,foil_name in [('PE_support','PE_support_mylar'),('foam_1','foam_mylar_1'),('foam_2','foam_mylar_2')]:
        under=result[substrate];center=under.bounds.mean(axis=0)
        radius=float(np.linalg.norm(under.vertices[:,:2]-center[:2],axis=1).max())
        foil,detail=review_wrap(radius,float(under.extents[2]),center)
        put(foil_name,foil);wraps[foil_name]=detail
    # The legacy coating has collapsed bevel triangles. Retain its explicitly
    # inferred 60 micrometre total gauge as a closed nominal disk, above copper.
    coating=trimesh.creation.cylinder(.025,.000060,sections=256)
    coating.apply_translation([0,0,result['emitter_copper'].bounds[1,2]+.000030])
    put('emitter_white_coating',coating)
    put('film_spacer',annulus(.0535,.0635,.0064,ring_bottom))
    for name, bottom in [('cover_lower_adhesive',ring_bottom-adhesive),('cover_upper_adhesive',ring_top)]:
        result[name]=display(annulus(.0535,.0635,adhesive,bottom),(.73,.70,.59,.9),0)
        changes.append(name)
    transition=np.array(selection['lower_membrane_transition_radius_mm'])*.001
    put('cover_lower',membrane(t,h,ring_bottom-adhesive,transition))
    upper=trimesh.creation.cylinder(.0635,t,sections=256)
    upper.apply_translation([0,0,ring_top+adhesive+t/2]);put('cover_upper',upper)
    put('radiation_shield',annulus(.070,.076,.057,0))
    put('aperture_plate',annulus(.025,.076,.001,.057))
    return result,dict(changed_parts=changes,foil_mesh_guards=wraps,stack_plane_export_adjustments_m=stack_adjustments,
        selected_lower_film_central_bottom_m=h,selected_upper_film_top_m=ring_top+adhesive+t,
        assembly_qualified=False,membrane_equilibrium_qualified=False,
        scope='Nominal static membrane-supported ring geometry only; adhesive compliance, tensions, edge bending and shield/aperture retention remain unresolved')


def build():
    legacy=capture_legacy();ledger=json.loads((HERE/'apparatus_cover_sources.json').read_text())
    parts=load_parts(legacy['geometry']['path']);result,details=candidate(parts,ledger)
    result,retention=apply_retention(result);details['retention']=retention
    geometry=export(result,HERE/'geometry'/'apparatus_cover_candidate.glb')
    # Real planar section faces of the exported solids. Open clipping exposes
    # nearly coincident back surfaces of foil/substrate and misrepresents a
    # solid cross-section. These caps are display geometry only.
    caps={};cap_details=[];uncut=[];offset=.0005
    for name,m in load_parts(geometry['path']).items():
        if not m.bounds[0,1]<offset<m.bounds[1,1]:
            uncut.append(name);continue
        s=m.copy();s.merge_vertices(merge_norm=True,merge_tex=True,digits_vertex=8)
        cut=manifold3d.Manifold(manifold3d.Mesh(np.array(s.vertices,dtype=np.float32),np.array(s.faces,dtype=np.uint32))).trim_by_plane([0,1,0],offset).to_mesh()
        vertices=cut.vert_properties[:,:3];faces=cut.tri_verts
        selected=np.max(abs(vertices[faces,1]-offset),axis=1)<1e-8
        cap=trimesh.Trimesh(vertices,faces[selected],process=False);cap.remove_unreferenced_vertices()
        assert len(cap.faces)>0
        cap.visual=m.visual.copy();caps[name]=cap
        cap_details.append(dict(part=name,area_m2=float(cap.area)))
    sections=export(caps,HERE/'geometry'/'apparatus_cover_sections.glb')
    sections.update(plane_normal=[0,1,0],plane_offset_m=offset,source_geometry=geometry,items=cap_details,uncut_parts=uncut,
                    scope='Exact planar display sections of exported positive solids; not added physical parts')
    record=dict(schema_version=1,id='cover_candidate',geometry=geometry,sections=sections,
        details=details,integrated_in_lab=False,owner_acceptance=None,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in
            [Path(__file__),HERE/'apparatus_cover_sources.json',HERE/'cover_legacy_rejected.json',HERE/'build_apparatus_mounting.py',HERE/'build_stock_cutplan.py',HERE/'requirements.txt',
             HERE/'build_cover_retention.py',HERE/'build_apparatus_frame.py',HERE/'apparatus_frame_sources.json',HERE/'apparatus_mount_sources.json']],
        limits=ledger['remaining'])
    write_json(HERE/'apparatus_cover_candidate.json',record)
    print(json.dumps(dict(parts=len(result),integrated_in_lab=False,assembly_qualified=False)))


if __name__=='__main__':build()
