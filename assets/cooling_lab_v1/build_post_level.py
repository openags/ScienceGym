"""Source-based ordinary post level, with static uncalibrated vial states.

The closed acrylic, liquid and gas domains are appearance geometry. They do
not implement gravity-dependent menisci, optical calibration or an estimator.
"""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from build_supplies import solid,cad_mesh,export_review

ORANGE=[244,94,8];BLACK=[25,27,25]
VIALS=[('right',[.055,-.005,.114],[1,0,0],[-.0016,0,0]),
       ('left',[-.005,.055,.114],[0,1,0],[0,-.0016,0]),
       ('corner',[-.0035,-.0035,.065],[0,0,1],[0,0,.012])]


def cad_domain(shape):
    # Closed cavities have inward-facing boundaries. Per-component outward
    # normal repair would fill those voids; retain the oriented CAD boundary.
    assert shape.isValid()
    vertices,faces=shape.tessellate(.03,.12)
    mesh=trimesh.Trimesh(vertices=np.array([[p.x,p.y,p.z] for p in vertices])*.001,faces=faces)
    mesh.merge_vertices(digits_vertex=7)
    mesh.update_faces(mesh.nondegenerate_faces());mesh.remove_unreferenced_vertices()
    assert mesh.is_volume and abs(mesh.volume-shape.Volume()*1e-9)/(shape.Volume()*1e-9)<.004
    return mesh


def mirror_face(shape):
    return shape.rotate((0,0,0),(0,0,1),90).mirror('YZ')


def body():
    # Source silhouette; local waisting, ribs and seats are photo hypotheses.
    profile=[(0,0),(88.9,0),(88.9,42),(53,63),(53,83),(88.9,105),(88.9,139.7),(0,139.7)]
    face=cq.Workplane('XZ').polyline(profile).close().extrude(3).edges('|Y').fillet(1).val()
    for z in [3.5,136.2]:
        lip=cq.Workplane('XZ').center(44.45,z).slot2D(88.9,4).extrude(5).val()
        face=face.fuse(lip)
    boss=cq.Workplane('XZ').center(55,114).slot2D(48,20).extrude(10).edges().fillet(1).val()
    face=face.fuse(boss)
    result=face.fuse(mirror_face(face)).fuse(cq.Solid.makeBox(3,3,139.7,cq.Vector(-3,-3,0)))
    plane=cq.Plane(origin=(0,0,65),xDir=(1,-1,0),normal=(-1,-1,0))
    result=result.fuse(cq.Workplane(plane).slot2D(48,20,90).extrude(10).edges().fillet(1).val())
    # Actual axial seats and viewing windows; no opaque block over the vials.
    seat=cq.Solid.makeCylinder(4.95,34.2,cq.Vector(37.9,-5,114),cq.Vector(1,0,0))
    window=cq.Workplane('XZ').center(55,114).slot2D(29,10.3).extrude(13,both=True).val()
    for tool in [seat,window,mirror_face(seat),mirror_face(window)]:result=result.cut(tool)
    # A 5.1 mm corner seat avoids a nearly tangent sub-micrometre sliver at
    # the folded faces. This selected clearance is not an interference fit.
    result=result.cut(cq.Solid.makeCylinder(5.1,34.2,cq.Vector(-3.5,-3.5,47.9)))
    result=result.cut(cq.Workplane(plane).slot2D(29,10.3,90).extrude(15,both=True).val())
    result=result.cut(cq.Solid.makeCylinder(5.5,35,cq.Vector(8,8,123),cq.Vector(-1,-1,0)))
    # The source has a taller rectangular left anchor and a small right peg.
    post=cq.Solid.makeBox(6,8,14,cq.Vector(46,-10,63))
    result=result.fuse(mirror_face(post))
    peg=cq.Solid.makeCylinder(3,6,cq.Vector(-3,34,67),cq.Vector(-1,0,0))
    cap=cq.Solid.makeCylinder(4.5,2,cq.Vector(-9,34,67),cq.Vector(-1,0,0))
    return result.fuse(mirror_face(peg)).fuse(mirror_face(cap)).clean()


def vial(g,name,centre,axis,bubble_offset):
    transform=trimesh.geometry.align_vectors([0,0,1],axis);transform[:3,3]=centre
    outside=cq.Solid.makeCylinder(4.8,34,cq.Vector(0,0,-17))
    chamber=cq.Solid.makeCylinder(4.1,31.5,cq.Vector(0,0,-15.75))
    shell=cad_domain(outside.cut(chamber));liquid=cad_domain(chamber)
    gas=trimesh.creation.icosphere(subdivisions=3,radius=1)
    gas.apply_scale([.0022,.0022,.0032]);gas.apply_translation(bubble_offset)
    # The bubble is a real subtracted chamber, not an overlapping white sphere.
    fluid=trimesh.boolean.difference([liquid,gas],engine='manifold',check_volume=True)
    records=[]
    for label,mesh,color,alpha in [('acrylic',shell,[224,239,225],65),('liquid',fluid,[203,218,48],155),('air',gas,[235,244,232],40)]:
        mesh.apply_transform(transform);identity=name+'_'+label
        g.add(identity,mesh,color,alpha=alpha,role='static_uncalibrated_vial_'+label);records.append(identity)
    for i,z in enumerate([-.008,-.006,.006,.008],1):
        ring=trimesh.creation.annulus(.00481,.00494,.00045,sections=64);ring.apply_translation([0,0,z]);ring.apply_transform(transform)
        g.add(name+'_mark_'+str(i),ring,BLACK,role='inferred_vial_marking');records.append(name+'_mark_'+str(i))
    # Reflector behind the glass, separated from acrylic and molded frame.
    if name=='right':
        reflector=cq.Workplane('XZ').center(55,114).slot2D(27,8).extrude(.1).val().translate((0,.2,0))
    elif name=='left':
        reflector=mirror_face(cq.Workplane('XZ').center(55,114).slot2D(27,8).extrude(.1).val().translate((0,.2,0)))
    else:
        p=cq.Plane(origin=(.15,.15,65),xDir=(1,-1,0),normal=(-1,-1,0))
        reflector=cq.Workplane(p).slot2D(27,8,90).extrude(.1).val()
    solid(g,name+'_reflector',reflector,[210,216,208],metal=.8,role='inferred_reflective_backing');records.append(name+'_reflector')
    return dict(id=name,centre_m=centre,axis=axis,outer_radius_m=.0048,length_m=.034,chamber_radius_m=.0041,chamber_length_m=.0315,
        local_bubble_centre_m=bubble_offset,parts=records,state='Static illustration; no gravity, calibration or sensor evidence')


def build():
    g=Geometry();solid(g,'orange_molded_body',body(),ORANGE,role='source_photo_molded_body')
    vials=[vial(g,*row) for row in VIALS]
    # Detached flat ring strap is an explicit rest-shape hypothesis. A pose is
    # not a material model or a verified installed/taut strap around a mast.
    strap=cq.Workplane('XY').slot2D(220,18).extrude(2).val()
    hole=cq.Workplane('XY').slot2D(210,8).extrude(4).val().translate((0,0,-1))
    solid(g,'detached_rubber_strap',strap.cut(hole).translate((-.025,-55,0)),BLACK,role='inferred_detached_rubber_strap')
    g.label('right_identification','175-O',.045,.012,[.047,-.00305,.026],ORANGE,[30,30,26])
    b=g.label('left_identification','POST LEVEL',.052,.012,[-.047,-.00305,.026],ORANGE,[30,30,26])
    b.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2,[0,0,1]))
    # A rotation keeps the original text readable on the second face.
    g.parts[-1]['bounds_m']=b.bounds.tolist()
    geometry=export_review(g,'johnson_175o_post_level')
    refs=[Path(__file__),HERE/'post_level_sources.json',HERE/'build_supplies.py',HERE/'geometry_tools.py']
    record=dict(schema_version=1,status='unaccepted_source_based_post_level_candidate',geometry=geometry,vials=vials,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        physical_part_count=26,visual_label_count=2,body_envelope_m=dict(height=.1397,face_width=.0889,inside_angle_degrees=90),
        candidate_mast_radius_m=.0205,candidate_mast_axis_xy_m=[.0205,.0205],
        detached_strap=dict(length_m=.220,width_m=.018,thickness_m=.002,opening_length_m=.210,opening_width_m=.008,
            basis='Selected flattened continuous loop from photo topology; dimensions, natural length and elasticity unknown'),
        scope='Ordinary tool appearance and isolated static mast-seat geometry; not staged inventory or a completed level measurement',
        inference_limits=['General manufacturer educational dimensions are adopted; no dimensioned 175-O drawing was found.',
            'The vial chamber is straight; actual barrel curvature, meniscus, refractive indices and gravity response remain unmodeled.',
            'Gas cavities illustrate source-photo states. The vertical vial gas is near its upper end, not falsely centered.',
            'Local body, pins, backing, ring markings and detached strap are selected geometry, not manufacturer CAD.',
            'No calibrated reading, level adjustment, strap retention, robot grasp, optical estimator or tool staging is qualified.'],
        staged_in_lab=False,initial_stock_credit=False,measurement_qualified=False,strap_retention_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'post_level_assets.json',record);print(json.dumps(dict(parts=geometry['parts'],geometry=geometry['path'])))


if __name__=='__main__':build()
