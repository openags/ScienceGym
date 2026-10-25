"""Catalog-sized ordinary hex drivers and an open/box wrench for inspection."""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from trimesh.visual.material import PBRMaterial
from geometry_tools import Geometry, HERE, ROOT, sha, write_json
from build_apparatus_mounting import cad_mesh, display

STEEL=[190,198,207];DARK=[32,34,39];RED=[175,34,44]


def linear_color(srgb):
    # glTF factors are linear; passing display RGB integers directly makes a
    # black handle gray and a dark red cap pink after sRGB output conversion.
    value=np.asarray(srgb,dtype=float)/255
    return np.rint(np.where(value<=.04045,value/12.92,((value+.055)/1.055)**2.4)*255).astype(int).tolist()


def size_label(g,text,x0,x1,radius):
    """Original size text follows the round rear grip, without a maker logo."""
    picture=Image.new('RGBA',(768,160),(0,0,0,0));draw=ImageDraw.Draw(picture)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',100)
    draw.text((384,80),text,font=font,fill=(220,220,220,255),anchor='mm')
    angles=np.linspace(-.34,.34,17);vertices=[];uv=[]
    for x,u in [(x0,0),(x1,1)]:
        for i,a in enumerate(angles):vertices.append([x,-radius*np.cos(a),radius*np.sin(a)]);uv.append([u,i/16])
    faces=[]
    for i in range(16):faces.extend([[i,i+1,17+i],[i+1,18+i,17+i]])
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=False)
    g.add('size_label',mesh,[255,255,255],role='original_size_label')
    mesh.visual=trimesh.visual.TextureVisuals(uv=uv,material=PBRMaterial(baseColorTexture=picture,alphaMode='BLEND',roughnessFactor=.8,metallicFactor=0,doubleSided=True))


def loft_x(sections, sides=96):
    """Closed round/hex cross sections; dimensions in millimetres."""
    angles=np.arange(sides)*2*np.pi/sides;vertices=[]
    for x,radius,hex_weight in sections:
        local=(angles+np.pi/6)%(np.pi/3)-np.pi/6
        rr=radius*((1-hex_weight)+hex_weight*np.cos(np.pi/6)/np.cos(local))
        vertices.extend(np.column_stack([np.full(sides,x),rr*np.cos(angles),rr*np.sin(angles)]))
    faces=[]
    for k in range(len(sections)-1):
        for i in range(sides):
            j=(i+1)%sides;a=k*sides;b=(k+1)*sides
            faces.extend([[a+i,b+i,b+j],[a+i,b+j,a+j]])
    for i in range(1,sides-1):faces.extend([[0,i+1,i],[(len(sections)-1)*sides,(len(sections)-1)*sides+i,(len(sections)-1)*sides+i+1]])
    m=trimesh.Trimesh(vertices=vertices,faces=faces);m.fix_normals();m.apply_scale(.001)
    assert m.is_volume
    return m


def driver(identity,spec):
    g=Geometry();blade=spec['blade_mm'];end=spec['overall_mm'];radius=spec['inferred_grip_diameter_mm']/2;cap=spec['inferred_cap_length_mm'];handle=end-blade-cap
    # The actual photo has a narrower nose and broader rear. A six-sided
    # finger grip blends into the round rear section; it is not a reversed cone.
    handle_shape=loft_x([(blade,radius*.52,.75),(blade+1,radius*.60,1),
        (blade+handle*.35,radius*.66,1),(blade+handle*.60,radius*.94,.3),
        (end-cap-1,radius,0),(end-cap,radius*.98,0)])
    af=spec['drive_mm']-.02;circum=af/np.sqrt(3)
    shaft=loft_x([(0,circum*.86,1),(.2,circum,1),(blade+5,circum,1)],sides=96)
    # Hollow out the buried blade, keeping a separate closed steel shaft.
    handle_shape=trimesh.boolean.difference([handle_shape,shaft],engine='manifold')
    cap_shape=loft_x([(end-cap,radius*.98,0),(end-cap+.6,radius,0),
        (end-1.3,radius*.97,0),(end-.3,radius*.86,0),(end,radius*.72,0)])
    for name,m,color,metal in [('handle',handle_shape,DARK,0),('shaft',shaft,STEEL,.85),('rotating_cap',cap_shape,RED,0)]:
        g.add(name,display(m),linear_color(color),role='ordinary_tool_part',metal=metal)
    size_label(g,'HEX '+str(spec['drive_mm']), (end-cap-25)*.001,(end-cap-5)*.001,(radius+.035)*.001)
    out=g.export(identity)
    return dict(id=identity,identity=spec['identity'],geometry=out,
        interface=dict(kind='straight_hex',tip_origin_m=[0,0,0],handle_axis=[1,0,0],nominal_af_mm=spec['drive_mm'],selected_actual_af_mm=af,exposed_blade_mm=blade),
        source_mass_kg=spec['source_mass_lb']*.45359237,source_mass_is_geometry_validation=False)


def wrench(spec):
    # Millimetres, shaft along X. Real open jaw and bihex cutouts, recessed
    # faces and an inclined ring are solid geometry rather than dark decals.
    jaw=cq.Solid.makeCylinder(9,4.2,cq.Vector(9,0,0))
    neck=cq.Workplane('XY').polyline([(10,-7),(22,-3.6),(99,-3.6),(106,-5.5),(106,5.5),(99,3.6),(22,3.6),(10,7)]).close().extrude(3.0).val().translate((0,0,.6))
    ring=cq.Solid.makeCylinder(6.2,7,cq.Vector(0,0,-3.5))
    hole=cq.Workplane('XY').polygon(6,8.1/np.cos(np.pi/6)).extrude(10).val().translate((0,0,-5))
    hole=hole.fuse(hole.rotate((0,0,0),(0,0,1),30))
    ring=ring.cut(hole).rotate((0,0,0),(0,1,0),-15)
    # The drawing measures L along X, including the tilted ring's thickness.
    # A rounded-back slot, open toward -X; 15-degree jaw inclination in plan.
    slot=cq.Solid.makeBox(32,8.1,8,cq.Vector(-30,-4.05,-2)).fuse(cq.Solid.makeCylinder(4.05,8,cq.Vector(2,0,-2)))
    slot=slot.rotate((0,0,0),(0,0,1),15).translate((7,0,0))
    jaw=jaw.cut(slot);left=jaw.BoundingBox().xmin
    ring_x=115+left-ring.BoundingBox().xmax;ring_z=3.2
    ring=ring.translate((ring_x,0,ring_z))
    body=jaw.fuse(neck).fuse(ring).cut(slot)
    # Forged recessed faces leave load-bearing raised borders.
    for z in [0,3.1]:
        pocket=cq.Workplane('XY').center(60,0).slot2D(72,3.6).extrude(1.1).val().translate((0,0,z))
        body=body.cut(pocket)
    # Small edge rounds on the long shaft/pocket edges catch light like the
    # forged reference while preserving the published head and ring envelopes.
    edges=[e for e in body.Edges() if e.geomType()=='LINE' and e.Length()>30]
    body=body.fillet(.15,edges)
    body=body.translate((-left,0,0))
    mesh=cad_mesh(body);g=Geometry();g.add('forged_wrench',display(mesh),linear_color(STEEL),role='ordinary_tool_part',metal=.9)
    out=g.export('stahlwille_40080808')
    return dict(id='stahlwille_40080808',identity=spec['identity'],geometry=out,
        interface=dict(kind='open_and_bihex',nominal_af_mm=8,selected_opening_af_mm=8.1,
            open_jaw_center_m=[(7-left)*.001,0,.0021],open_jaw_angle_degrees=15,
            ring_center_m=[(ring_x-left)*.001,0,ring_z*.001],ring_axis=[-np.sin(np.pi/12),0,np.cos(np.pi/12)],
            exact_as_drive_profile=False),source_mass_kg=.021,source_mass_is_geometry_validation=False)


def build():
    ledger=json.loads((HERE/'fastener_tools_sources.json').read_text());items=[]
    for identity,spec in ledger['items'].items():
        item=wrench(spec) if identity.startswith('stahlwille') else driver(identity,spec)
        item.update(appearance_accepted=False,interaction_qualified=False,owner_acceptance=None)
        items.append(item)
    write_json(HERE/'fastener_tools.json',dict(schema_version=1,status='isolated_catalog_candidates',
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [Path(__file__),HERE/'fastener_tools_sources.json',HERE/'geometry_tools.py',HERE/'build_apparatus_mounting.py']],
        items=items,integrated_in_lab=False,owner_acceptance=None,
        limits=['Nominal ordinary tools for asset inspection; no fastener torque, assembled access, hand grasp or robot operation qualification']))
    print(json.dumps(dict(tool_types=len(items),integrated_in_lab=False)))


if __name__=='__main__':build()
