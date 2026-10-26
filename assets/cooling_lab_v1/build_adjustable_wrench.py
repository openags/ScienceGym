"""Original AC28VS candidate from manufacturer dimensions and photographs.

The slider, worm, axle and spring are inferred geometry. Static openings do
not constitute a qualified screw transmission, joint limit or tool action.
"""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from PIL import Image,ImageDraw,ImageFont,ImageOps
from trimesh.visual.material import PBRMaterial
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from build_supplies import cad_mesh,export_review
from build_weather_assets import cable_mesh

STEEL=[184,190,194];POLISHED=[197,202,205];ANGLE=15.;PITCH=3.2;REFERENCE_GAP=12.7;HANDLE_THICKNESS=9.5
WORM_U=15.8;WORM_Y0=-14.4;WORM_LENGTH=12.8;WORM_RADIUS=16.6624/2


def original_scales(g,frame):
    """Ordinary jaw graduations, independently typeset; no copied artwork."""
    records=[];u0,u1=.0004,.0066;y0,y1=-.026,.001
    width,height=512,2048
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',115)
    for name,side,step,count,labels in [
        ('metric_scale_text',1,.001,26,{0:'0',10:'10',20:'20'}),
        ('inch_scale_text',-1,.0254/16,17,{0:'0',4:'1/4',8:'1/2',12:'3/4',16:'1'})]:
        picture=Image.new('RGBA',(width,height),(0,0,0,0));draw=ImageDraw.Draw(picture)
        ticks=[]
        for i in range(count):
            y=-i*step;py=(y1-y)/(y1-y0)*(height-1)
            long=i in labels;draw.line((24,py,170 if long else 105,py),fill=(36,39,40,255),width=7)
            if long:draw.text((195,py),labels[i],font=font,fill=(36,39,40,255),anchor='lm')
            ticks.append(dict(opening_m=i*step,local_y_m=y,pixel_y=py,label=labels.get(i)))
        if side<0:picture=ImageOps.mirror(picture)
        z=side*.00381003
        vertices=[[u0,y0,z],[u1,y0,z],[u1,y1,z],[u0,y1,z]]
        faces=[[0,1,2],[0,2,3]] if side>0 else [[0,2,1],[0,3,2]]
        mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=False);mesh.apply_transform(frame)
        g.add(name,mesh,[255,255,255],role='original_ordinary_scale_artwork')
        mesh.visual=trimesh.visual.TextureVisuals(uv=[[0,0],[1,0],[1,1],[0,1]],
            material=PBRMaterial(baseColorTexture=picture,roughnessFactor=.65,metallicFactor=0,alphaMode='BLEND',doubleSided=False))
        records.append(dict(id=name,side=side,local_bounds_m=[[u0,y0,z],[u1,y1,z]],texture_size_px=[width,height],ticks=ticks,
            provenance='Original calibrated reference artwork. Manufacturer confirms SAE/metric scales; exact engraving layout is inferred.'))
    return records


def head_outline():
    p=cq.Workplane('XY').moveTo(-25.4,0).lineTo(-26.8,1.5)
    p=p.threePointArc((-21,15),(-8,20)).threePointArc((3,22),(13,17))
    for xy in [(29,7),(30,-12),(17,-25),(6,-30),(0,-27),(0,-6),(-2,-3),(-6,0)]:p=p.lineTo(*xy)
    return p.close().extrude(7.62).val().translate((0,0,-3.81))


def cylinder_y(radius,length,point):
    return cq.Solid.makeCylinder(radius,length,cq.Vector(*point),cq.Vector(0,1,0))


def rack_and_jaw():
    jaw=cq.Workplane('XY').moveTo(-25.4,0).lineTo(-25.4,-3.5)
    jaw=jaw.threePointArc((-15,-11),(-4,-10)).lineTo(0,-10).lineTo(0,-6.1).lineTo(-2,-3.2).lineTo(-6.2,0).close().extrude(7.62).val().translate((0,0,-3.81))
    neck=cq.Solid.makeBox(5.3,9.7,3.6,cq.Vector(0,-10,-1.8))
    rack=cylinder_y(3.4,32,(5.2,-10,0))
    # Original trapezoidal rack profile. The pitch and pressure angle are
    # unprovided local dimensions; checks must inspect actual exported fit.
    for k in range(-4,9):
        y=k*PITCH-.1
        cut=cq.Workplane('XY').polyline([(8.6,y-1.2),(7.1,y-.6),(7.1,y+.6),(8.6,y+1.2),(10,y+1.2),(10,y-1.2)]).close().extrude(10).val().translate((0,0,-5))
        rack=rack.cut(cut)
    return jaw.fuse(neck).fuse(rack)


def worm_mesh():
    # Continuous helical ridge, with real radial/axial section rather than
    # independent decorative rings. The axis is local +Y.
    theta=np.linspace(0,2*np.pi*4,961);profile=[(4.9,-.9),(WORM_RADIUS,-.35),(WORM_RADIUS,.35),(4.9,.9)]
    vertices=[]
    for a in theta:
        for radius,dy in profile:vertices.append([WORM_U+radius*np.cos(a),WORM_Y0+PITCH*a/(2*np.pi)+dy,radius*np.sin(a)])
    faces=[];count=len(profile)
    for i in range(len(theta)-1):
        for j in range(count):
            a=i*count+j;b=i*count+(j+1)%count;c=b+count;d=a+count
            faces.extend([[a,b,c],[a,c,d]])
    faces.extend([[0,2,1],[0,3,2]])
    q=(len(theta)-1)*count;faces.extend([[q,q+1,q+2],[q,q+2,q+3]])
    ridge=trimesh.Trimesh(vertices=np.array(vertices)*.001,faces=faces,process=True);ridge.fix_normals()
    core=cad_mesh(cylinder_y(5.1,WORM_LENGTH,(WORM_U,WORM_Y0,0)))
    result=trimesh.boolean.union([core,ridge],engine='manifold')
    bounds=cad_mesh(cq.Solid.makeBox(40,WORM_LENGTH,30,cq.Vector(-5,WORM_Y0,-15)))
    result=trimesh.boolean.intersection([result,bounds],engine='manifold')
    bore=cad_mesh(cylinder_y(1.65,16,(WORM_U,-16,0)))
    result=trimesh.boolean.difference([result,bore],engine='manifold')
    # Remove sub-micrometre CSG slivers before glTF float32 export. Otherwise
    # coincident ridge/core intersections can collapse into detached faces.
    result.merge_vertices(digits_vertex=6);result.update_faces(result.nondegenerate_faces())
    result.remove_unreferenced_vertices();result.fix_normals();assert result.is_volume
    return result


def build():
    source=json.loads((HERE/'adjustable_wrench_sources.json').read_text())
    head=head_outline();rotated=head.rotate((0,0,0),(0,0,1),ANGLE)
    offset=np.array([-rotated.BoundingBox().xmin,10.,0.])
    local=trimesh.transformations.rotation_matrix(np.radians(ANGLE),[0,0,1]);local[:3,3]=offset*.001
    def place(shape):return shape.rotate((0,0,0),(0,0,1),ANGLE).translate(tuple(offset))
    def xy(u,v):return tuple((local[:2,:2]@np.array([u,v])+offset[:2]).tolist())
    # One continuous forged silhouette. Joining independently extruded head
    # and handle outlines leaves an artificial shoulder absent from the photos.
    outline=cq.Workplane('XY').moveTo(*xy(-25.4,0)).lineTo(*xy(-26.8,1.5))
    outline=outline.threePointArc(xy(-21,15),xy(-8,20)).threePointArc(xy(3,22),xy(13,17))
    outline=outline.spline([xy(22,10),(72,11),(95,8.7),(189,9.4)],includeCurrent=True)
    outline=outline.threePointArc((203.2,0),(189,-9.4)).spline([(95,-8.7),(72,-11),xy(17,-25)],includeCurrent=True)
    for point in [(6,-30),(0,-27),(0,-6),(-2,-3),(-6,0)]:outline=outline.lineTo(*xy(*point))
    fixed=outline.close().extrude(HANDLE_THICKNESS).edges('|Z').fillet(.35).edges('#Z').chamfer(.25).val().translate((0,0,-HANDLE_THICKNESS/2))
    # Source jaw thickness is 7.62 mm; blend the machined head faces into the
    # inferred thicker forged handle rather than scaling the whole tool.
    face_cut=cq.Workplane('XZ').polyline([(-5,3.81),(57,3.81),(60,HANDLE_THICKNESS/2),(60,10),(-5,10)]).close().extrude(120).val().translate((0,60,0))
    fixed=fixed.cut(face_cut).cut(face_cut.rotate((0,0,0),(1,0,0),180))
    # Two shallow forged-web recesses and a genuine tail hanging hole.
    recess=cq.Workplane('XY').moveTo(64,7.2).spline([(88,5.5),(182,6.3)],includeCurrent=True).lineTo(183,-6.3).spline([(88,-5.5),(64,-7.2)],includeCurrent=True).close().extrude(1.2).val()
    fixed=fixed.cut(recess.translate((0,0,HANDLE_THICKNESS/2-.9))).cut(recess.translate((0,0,-HANDLE_THICKNESS/2-.3)))
    fixed=fixed.cut(cq.Solid.makeCylinder(6,12,cq.Vector(193,0,-6)))
    # The rack slides in a real cylindrical keyway with a narrow open tongue
    # slot. The exposed adjustment window and axle bore remain separate voids.
    guide=cylinder_y(3.55,70,(5.2,-40,0)).fuse(cq.Solid.makeBox(5.4,70,4,cq.Vector(-.1,-40,-2)))
    window=cq.Solid.makeBox(17.3,14.4,24,cq.Vector(7.2,-15.2,-12))
    fixed=fixed.cut(place(guide)).cut(place(window))
    fixed=fixed.cut(place(cylinder_y(1.6,40,(WORM_U,-24,0))))
    fixed=fixed.cut(place(cylinder_y(2.25,2.5,(WORM_U,-17.2,0))))
    g=Geometry();g.add('forged_body_and_fixed_jaw',cad_mesh(fixed),STEEL,metal=.8,role='source_constrained_fixed_body')
    jaw=cad_mesh(rack_and_jaw());jaw.apply_translation([0,-REFERENCE_GAP*.001,0]);jaw.apply_transform(local)
    g.add('sliding_jaw_and_rack',jaw,POLISHED,metal=.85,role='inferred_one_piece_slider_and_rack')
    worm=worm_mesh();worm.apply_transform(local);g.add('helical_adjustment_worm',worm,STEEL,metal=.85,role='inferred_continuous_worm')
    pin=cad_mesh(cylinder_y(1.5,21,(WORM_U,-19,0)));pin.apply_transform(local);g.add('worm_axle',pin,STEEL,metal=.85,role='inferred_factory_axle')
    theta=np.linspace(0,4*np.pi,401);points=np.column_stack([WORM_U+1.9*np.cos(theta),np.linspace(-16,-14.8,len(theta)),1.9*np.sin(theta)])*.001
    spring=cable_mesh(points,.00015);spring.apply_transform(local);g.add('axial_spring_reference',spring,STEEL,metal=.75,role='unresolved_source_tension_spring_reference')
    scales=original_scales(g,local)
    # The isolated nominal openings are inspection alternatives only.
    items=[];inverse=np.linalg.inv(local)
    for identity,gap in [('half_inch_reference',REFERENCE_GAP),('nominal_closed',0.),('catalogue_capacity',28.575)]:
        copy=Geometry();copy.scene=g.scene.copy();copy.parts=[];transforms={n:np.eye(4) for n in copy.scene.graph.nodes_geometry}
        delta=np.eye(4);delta[1,3]=-(gap-REFERENCE_GAP)*.001
        transforms['sliding_jaw_and_rack']=local@delta@inverse
        roll=trimesh.transformations.rotation_matrix(-2*np.pi*(gap-REFERENCE_GAP)/PITCH,[0,1,0],point=[WORM_U*.001,0,0])
        transforms['helical_adjustment_worm']=local@roll@inverse
        for p in g.parts:
            n=p['id'];matrix,key=copy.scene.graph[n];matrix=transforms[n]@matrix
            copy.scene.graph.update(frame_to=n,matrix=matrix,geometry=key)
            mesh=copy.scene.geometry[key].copy();mesh.apply_transform(matrix)
            copy.parts.append(dict(p,bounds_m=mesh.bounds.tolist()))
        geometry=export_review(copy,'crescent_ac28vs_'+identity)
        items.append(dict(id=identity,selected_gap_m=gap*.001,geometry=geometry,part_transforms={n:m.tolist() for n,m in transforms.items()}))
    refs=[Path(__file__),HERE/'adjustable_wrench_sources.json',HERE/'build_supplies.py',HERE/'build_weather_assets.py',HERE/'geometry_tools.py']
    record=dict(schema_version=1,status='source_constrained_candidate_pending_geometry_checks',items=items,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        manufacturer_facts=source['manufacturer_facts'],source_differences=source['source_differences'],
        local_jaw_frame_to_tool=local.tolist(),reference_gap_m=REFERENCE_GAP*.001,
        inferred_thread_pitch_m=PITCH*.001,inferred_jaw_angle_deg=ANGLE,
        inferred_handle_thickness_m=HANDLE_THICKNESS*.001,
        ordinary_scale_artwork=scales,
        limitations=['Worm/rack profiles, clearances, axle and spring construction are original hypotheses and have not passed geometric fit checks.',
            'The quoted capacity is not a validated joint limit. Static alternatives do not establish force transmission, retention or adjustment.',
            'Manufacturer dimension axes and jaw state are not fully specified. Actual exported envelopes must be checked and differences retained.',
            'Scale artwork is independently typeset from the selected opening datum; exact manufacturer engraving layout is inferred. Final source-to-model visual review remains pending.'],
        staged_in_lab=False,initial_stock_credit=False,torque_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'adjustable_wrench_assets.json',record)
    print(json.dumps(dict(parts=len(g.parts),states=[dict(id=i['id'],bounds_m=i['geometry']['bounds_m']) for i in items])))


if __name__=='__main__':build()
