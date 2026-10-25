"""Manufacturer-constrained ordinary tools and explicitly authored raw stock.

Meshes have real openings, separate service parts and SI dimensions. These are
review assets: they do not implement cutting, cable physics or device operation.
"""
import json
import math
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from scipy.optimize import brentq
from scipy.spatial import cKDTree
from PIL import Image,ImageDraw,ImageFont
from trimesh.visual.material import PBRMaterial
from geometry_tools import Geometry,HERE,ROOT,sha,write_json

STEEL=[180,190,199];DARK=[35,38,42];BLACK=[23,25,28]


def export_review(g,stem):
    # The authored byte palettes are sRGB. glTF baseColorFactor is linear;
    # writing bytes/255 directly washes black plastic into light grey. Texture
    # pixels remain sRGB and must not receive this factor conversion.
    def linear_materials(tree):
        for mat in tree.get('materials',[]):
            pbr=mat.get('pbrMetallicRoughness',{});rgba=pbr.get('baseColorFactor')
            if rgba is not None:
                pbr['baseColorFactor']=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgba[:3]]+[rgba[3]]
    for name,m in list(g.scene.geometry.items()):
        shaded=trimesh.graph.smooth_shade(m,angle=np.radians(35),facet_minarea=10)
        assert len(shaded.faces)==len(m.faces) and np.allclose(shaded.bounds,m.bounds,atol=1e-10)
        # submesh(..., append=True) used by smooth_shade drops the PBR visual.
        # Rebind the single part material and remap any texture UVs by unchanged
        # vertex positions; never let normal repair replace colors with defaults.
        uv=None
        if m.visual.uv is not None:
            distances,indices=cKDTree(m.vertices).query(shaded.vertices)
            assert np.max(distances)<1e-10
            uv=m.visual.uv[indices]
        shaded.visual=trimesh.visual.TextureVisuals(uv=uv,material=m.visual.material.copy())
        g.scene.geometry[name]=shaded
    path=HERE/'geometry'/(stem+'.glb')
    path.write_bytes(g.scene.export(file_type='glb',include_normals=True,tree_postprocessor=linear_materials))
    return dict(path=str(path.relative_to(ROOT)),sha256=sha(path),parts=len(g.parts),bounds_m=g.scene.bounds.tolist(),axes='+Z up; SI metres',part_records=g.parts,
        appearance='Authored sRGB palette converted to linear glTF factors. Sharp-edge normal splits preserve triangle positions; not measured reflectance.')


def cad_mesh(shape):
    assert shape.isValid()
    v,f=shape.tessellate(.03,.12)
    m=trimesh.Trimesh(vertices=np.array([[p.x,p.y,p.z] for p in v])*.001,faces=f)
    m.merge_vertices(digits_vertex=6);m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices()
    m.fix_normals();assert m.is_watertight
    return m


def solid(g,name,shape,color,metal=0,role='tool_part'):
    return g.add(name,cad_mesh(shape),color,metal=metal,role=role)


def top_label(g,name,text,width,height,center,background=(230,233,225),foreground=(28,32,36)):
    picture=Image.new('RGB',(1024,256),tuple(background));draw=ImageDraw.Draw(picture)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',90)
    draw.text((512,128),text,font=font,fill=foreground,anchor='mm')
    x,y,z=center;v=[[x-width/2,y-height/2,z],[x+width/2,y-height/2,z],[x+width/2,y+height/2,z],[x-width/2,y+height/2,z]]
    m=trimesh.Trimesh(vertices=v,faces=[[0,1,2],[0,2,3]],process=False)
    g.add(name,m,[255,255,255],role='original_identification_text')
    m.visual=trimesh.visual.TextureVisuals(uv=[[0,0],[1,0],[1,1],[0,1]],material=PBRMaterial(baseColorTexture=picture,roughnessFactor=.7))


def curved_tube(g,name,points,radius,color,metal=0):
    # One continuous mesh rather than hundreds of independent capped cylinders.
    p=np.array(points);t=np.gradient(p,axis=0);t/=np.linalg.norm(t,axis=1)[:,None]
    n=np.cross(t,[0,0,1]);bad=np.linalg.norm(n,axis=1)<1e-6;n[bad]=np.cross(t[bad],[0,1,0]);n/=np.linalg.norm(n,axis=1)[:,None]
    b=np.cross(t,n);a=np.linspace(0,2*np.pi,16,endpoint=False)
    v=(p[:,None,:]+radius*(np.cos(a)[None,:,None]*n[:,None,:]+np.sin(a)[None,:,None]*b[:,None,:])).reshape(-1,3)
    faces=[]
    for i in range(len(p)-1):
        for j in range(16):k=(j+1)%16;faces.extend([[i*16+j,i*16+k,(i+1)*16+k],[i*16+j,(i+1)*16+k,(i+1)*16+j]])
    for j in range(1,15):faces.extend([[0,j+1,j],[(len(p)-1)*16,(len(p)-1)*16+j,(len(p)-1)*16+j+1]])
    m=trimesh.Trimesh(vertices=v,faces=faces);m.fix_normals();assert m.is_watertight
    return g.add(name,m,color,role='cable_rest_shape',metal=metal)


def slotted_screw(g,name,position,radius=.0014):
    x,y,z=np.array(position)*1000;r=radius*1000
    head=cq.Solid.makeCylinder(r,.65,cq.Vector(x,y,z))
    slot=cq.Solid.makeBox(2*r+.2,.35,.4,cq.Vector(x-r-.1,y-.175,z+.3))
    solid(g,name,head.cut(slot),STEEL,.85)


def stripper():
    g=Geometry();yellow=[244,198,16]
    # Profile traced from the inspected manufacturer's ST-450 photograph.
    for sign in [-1,1]:
        outline=[(12,sign*12),(18,sign*19),(25,sign*18),(31,sign*19),(37,sign*21.95),(83,sign*16),(90,sign*13),(90,sign*10),(12,sign*10)]
        part=cq.Workplane('XY').polyline(outline).close().extrude(9).val().translate((0,0,1))
        solid(g,'yellow_spring_handle_'+str(sign),part,yellow)
        rail=cq.Workplane('XY').box(85,8.2,2.0).val().translate((49.3,sign*9.7,10))
        solid(g,'metal_rail_'+str(sign),rail,STEEL,.8)
    for name,outline in [('blade_end',[(0,-8),(6,-14),(10,-14),(10,14),(6,14),(0,8)]),('heel',[(88.6,-14),(92.6,-14),(98.6,-8),(98.6,8),(92.6,14),(88.6,14)])]:
        part=cq.Workplane('XY').polyline(outline).close().extrude(11).val()
        if name=='blade_end':part=part.cut(cq.Solid.makeBox(3,4,4,cq.Vector(4,-2,8)))
        solid(g,name,part,BLACK)
    # Open central channel, adjustable stop and visible blade throat.
    g.box('adjustable_strip_stop',[.014,.012,.010],[.067,0,.008],DARK)
    g.box('length_slide',[.021,.008,.003],[.081,0,.0045],DARK)
    g.box('steel_blade',[.002,.003,.0005],[.0055,0,.010],STEEL,metal=.85)
    top_label(g,'model_text','ST-450',.046,.005,[.039,-.0097,.0111])
    top_label(g,'range_text','26 - 36 AWG',.040,.005,[.053,.0097,.0111])
    for x in [.007,.091]:
        for y in [-.011,.011]:slotted_screw(g,'rail_screw_'+str(x)+'_'+str(y),[x,y,.0105],.0008)
    return g


def tweezers():
    g=Geometry()
    # Plate width and opening follow the catalogue envelope. Intermediate
    # spring curvature is authored; the rest model is not an elastic solver.
    for sign in [-1,1]:
        vertices=[]
        for x,halfwidth,center,thick in [(0,.00025,.003,.0004),(.016,.0015,.0045,.0007),(.060,.00575,.00575,.001),(.105,.0055,.0025,.001),(.130,.003,.0005,.001)]:
            for y,z in [(-thick/2,-halfwidth),(thick/2,-halfwidth),(thick/2,halfwidth),(-thick/2,halfwidth)]:vertices.append([x,sign*(center+y),z+.00575])
        faces=[[0,3,2],[0,2,1],[16,17,18],[16,18,19]]
        for i in range(4):
            for j in range(4):k=(j+1)%4;faces.extend([[4*i+j,4*i+k,4*(i+1)+k],[4*i+j,4*(i+1)+k,4*(i+1)+j]])
        m=trimesh.Trimesh(vertices=vertices,faces=faces);m.fix_normals();assert m.is_watertight
        g.add('ptfe_spring_arm_'+str(sign),m,[76,80,85],role='ordinary_tweezer_arm')
    g.box('joined_heel',[.003,.001,.006],[.1285,0,.00575],[76,80,85])
    return g


def jug():
    g=Geometry();n=128;a=np.linspace(0,2*np.pi,n,endpoint=False);loops=[]
    # Watertight wall and bottom with an OPEN mouth. Spout/handle shape is
    # inferred from the catalogue photo; catalogue body diameters are retained.
    for radius,z in [(.0625,0),(.0625,.003),(.0737,.190),(.075,.213),(.0728,.213),(.0603,.003)]:
        spout=.014*np.exp(-((np.angle(np.exp(1j*(a-np.pi))))/.24)**2)*max(0,(z-.170)/.043)
        loops.append(np.column_stack([(radius+spout)*np.cos(a),(radius+spout)*np.sin(a),np.full(n,z)]))
    v=np.concatenate(loops);f=[]
    for i in range(len(loops)-1):
        for j in range(n):k=(j+1)%n;f.extend([[i*n+j,i*n+k,(i+1)*n+k],[i*n+j,(i+1)*n+k,(i+1)*n+j]])
    for j in range(1,n-1):f.extend([[0,j+1,j],[5*n,5*n+j,5*n+j+1]])
    m=trimesh.Trimesh(vertices=v,faces=f);m.fix_normals();assert m.is_watertight
    g.add('open_pp_vessel',m,[220,229,228],role='ordinary_fill_vessel',alpha=210)
    # Rectangular closed handle with a curved outside and an actual grip hole.
    outer=cq.Workplane('XZ').moveTo(67,114).lineTo(84,114).threePointArc((96,119),(101,131)).lineTo(121,186).threePointArc((118,204),(100,208)).lineTo(74,208).close().extrude(5,both=True).val()
    inner=cq.Workplane('XZ').moveTo(74,125).lineTo(82,125).threePointArc((88,128),(91,137)).lineTo(110,188).threePointArc((108,195),(98,197)).lineTo(75,197).close().extrude(8,both=True).val()
    solid(g,'closed_handle',outer.cut(inner),[220,229,228])
    # Embossed graduation position is a volume calculation, not equally spaced
    # ticks. Inner body is a truncated cone above the 3 mm bottom.
    r0=.0603;slope=(.0728-r0)/.210
    for ml in range(100,2001,100):
        h=brentq(lambda h:np.pi*(r0*r0*h+r0*slope*h*h+slope*slope*h**3/3)-ml*1e-6,0,.210)
        rad=.0625+(h/.210)*.0125
        g.box('embossed_'+str(ml),[.012 if ml%500==0 else .007,.0006,.0005],[0,-rad-.00015,.003+h],[205,216,214],role='nominal_volume_graduation')
    return g


def driver():
    g=Geometry()
    g.profile('handle',[(0,0),(.0057,0),(.00635,.004),(.0058,.010),(.0042,.020),(.004,.060),(.003,.078),(0,.078)],DARK,axis=(1,0,0),position=(.040,0,.00635))
    g.cylinder('round_shaft',.001,.034,[.023,0,.00635],STEEL,axis=(1,0,0),metal=.85)
    tip=trimesh.convex.convex_hull(np.array([[x,y,z] for x,w,h in [(0,.0015,.00025),(.006,.002,.002)] for y in [-w/2,w/2] for z in [.00635-h/2,.00635+h/2]]))
    g.add('slotted_blade_1_5x0_25',tip,STEEL,metal=.85)
    g.cylinder('rotating_cap',.00635,.002,[.119,0,.00635],[171,35,40],axis=(1,0,0))
    return g


def ambient_rtd():
    g=Geometry();length=.1524
    sheath=cq.Solid.makeCylinder(3.175,152.4,cq.Vector(0,0,0),cq.Vector(1,0,0)).cut(cq.Solid.makeCylinder(2.675,151.9,cq.Vector(.5,0,0),cq.Vector(1,0,0)))
    for x in [4,9,14]:
        for axis in [(0,1,0),(0,0,1)]:sheath=sheath.cut(cq.Solid.makeCylinder(1.1,10,cq.Vector(x,-5*axis[1],-5*axis[2]),cq.Vector(*axis)))
    solid(g,'vented_air_sheath',sheath,STEEL,.9)
    g.cylinder('ceramic_sensor_core',.0008,.014,[.008,0,0],[221,218,202],axis=(1,0,0))
    # NPT thread identification is sourced. The fitting envelope/crest is
    # inferred and is not used to claim threaded insertion.
    g.cylinder('npt_core',.0062,.010,[length+.005,0,0],STEEL,axis=(1,0,0),metal=.9)
    p=[]
    for x in np.linspace(length+.0003,length+.0097,360):
        theta=(x-length)*2*np.pi/(.0254/18);r=.0064+(x-length)/32;p.append([x,r*np.cos(theta),r*np.sin(theta)])
    curved_tube(g,'npt_visual_crest',p,.00028,STEEL,.9)
    hexagon=trimesh.creation.cylinder(.009525/np.cos(np.pi/6),.005,sections=6);hexagon.apply_transform(trimesh.geometry.align_vectors([0,0,1],[1,0,0]));hexagon.apply_translation([length+.0125,0,0]);g.add('inferred_hex',hexagon,STEEL,metal=.9)
    g.cylinder('cable_transition',.004,.015,[length+.0225,0,0],STEEL,axis=(1,0,0),metal=.85)
    start=np.array([length+.030,0,0]);coilstart=.24;radius=.06;rise=.0035;breakout=.06;target=1.8288-breakout
    def points(turns):
        u=np.linspace(0,turns,801);theta=-np.pi/2+2*np.pi*u
        return np.vstack([start,np.column_stack([coilstart+radius*np.cos(theta),radius+radius*np.sin(theta),rise*u])])
    def total(p):return np.linalg.norm(np.diff(p,axis=0),axis=1).sum()
    turns=brentq(lambda t:total(points(t))-target,3,6);p=points(turns);curved_tube(g,'pfa_cable_nominal_6ft',p,.0015,[65,69,71])
    tangent=p[-1]-p[-2];tangent/=np.linalg.norm(tangent);normal=np.cross(tangent,[0,0,1]);normal/=np.linalg.norm(normal)
    terminals=[]
    for i in range(4):
        direction=tangent+normal*(i-1.5)*.11;direction/=np.linalg.norm(direction)
        q=np.array([p[-1],p[-1]+direction*.053,p[-1]+direction*.060]);curved_tube(g,'lead_'+str(i),q[:2],.00045,[177,33,39] if i<2 else [230,228,218]);curved_tube(g,'stripped_'+str(i),q[1:],.00020,STEEL,.8);terminals.append(q[-1].tolist())
    return g,dict(nominal_cable_length_m=1.8288,modeled_jacket_length_m=float(total(p)),breakout_length_m=breakout,rest_points_m=p.tolist(),terminals_m=terminals,wire_colours_inferred=True)


def connector(male=True):
    g=Geometry();length=.02957 if male else .03411;bodyend=.0206 if male else .0254;yellow=[233,198,57]
    # Drawing page 2: 17 mm width, 8 mm total nominal body height, 8 mm pin
    # pitch, unequal 2.4 / 3.17 mm wide x .8 mm flat pins, 12.7 mm projection.
    body=cq.Solid.makeBox(bodyend*1000,17,4.8,cq.Vector(0,-8.5,0))
    body=body.cut(cq.Solid.makeCylinder(1.25,10,cq.Vector(4.8 if male else 7.1,0,-1)))
    body=body.cut(cq.Solid.makeCylinder(2.45,12,cq.Vector(bodyend*1000-5,0,4),cq.Vector(1,0,0)))
    if not male:
        for y,w in [(-4,2.4),(4,3.17)]:body=body.cut(cq.Solid.makeBox(13,w+.15,1,cq.Vector(-1,y-w/2-.075,3.5)))
    solid(g,'connector_body',body,yellow)
    for y in [-.0065,.0065]:
        g.box('clamp_bridge_'+str(y),[length-bodyend,.004,.003],[bodyend+(length-bodyend)/2,y,.0015],yellow)
        g.box('cap_bridge_'+str(y),[.005,.004,.003],[bodyend-.003,y,.0065],yellow)
    g.box('cable_clamp_end',[.004,.017,.003],[length-.002,0,.0015],yellow)
    g.box('top_wire_clamp',[.004,.017,.003],[length-.002,0,.0065],yellow)
    for x in [bodyend-.003,length-.002]:
        for y in [-.0065,.0065]:slotted_screw(g,'captive_screw_'+str(x)+'_'+str(y),[x,y,.00735])
    if male:
        for y,w in [(-.004,.0024),(.004,.00317)]:g.box('flat_pin_'+str(y),[.0127,w,.0008],[-.00635,y,.004],STEEL,metal=.85)
    top_label(g,'type_K_text','K',.006,.003,[.012,0,.00485],tuple(yellow))
    return g


def connector_kit():
    g=Geometry();records=[]
    for i in range(8):
        for male,y in [(True,.018),(False,-.018)]:
            item=connector(male);t=np.eye(4);t[:3,3]=[-.112+(i%4)*.07,y-.043+(i//4)*.086,.0012]
            for node in item.scene.graph.nodes_geometry:
                local,key=item.scene.graph[node];m=item.scene.geometry[key].copy();m.apply_transform(t@local);visual=m.visual.copy();g.add('channel_'+str(i+1)+'_'+('M_' if male else 'F_')+node,m,[233,198,57],role='ordinary_thermocouple_connector');m.visual=visual
            records.append(dict(id='TC'+str(i+1)+('_M' if male else '_F'),model='SMPW-CC-K-'+('M' if male else 'F'),position_m=t[:3,3].tolist(),connected=False))
    # Ordinary Buerkle tray is a catalog product, not a robot-only carrier.
    tray=trimesh.load(HERE/'geometry/buerkle_4208_0022.glb',force='scene')
    for node in tray.graph.nodes_geometry:
        t,k=tray.graph[node];m=tray.geometry[k].copy();m.apply_transform(t);g.add('ordinary_tray_'+node,m,STEEL,role='ordinary_catalog_tray',metal=.9)
    return g,records


def film_stack(kind,thickness,count,size=(.16,.16)):
    g=Geometry()
    # Archival interleaves and an ordinary backing sheet protect the as-received
    # stock. No support fixture or completed scientific sample is substituted.
    w,h=size
    g.box('paper_backing',[w+.02,h+.02,.0003],[0,0,.00015],[212,207,185],role='ordinary_stock_interleaf')
    for i in range(count):
        z=.0003+i*(thickness+.0001)
        g.box('raw_film_'+str(i+1),[w,h,thickness],[0,0,z+thickness/2],[205,207,198] if kind!='mylar' else [179,185,191],role='raw_material',metal=.92 if kind=='mylar' else 0)
        if i<count-1:g.box('paper_interleaf_'+str(i+1),[w+.01,h+.01,.0001],[0,0,z+thickness+.00005],[236,230,211],role='ordinary_stock_interleaf')
    top_label(g,'lot_card',kind.upper()+' STOCK',.14,.012,[0,-h/2-.003,.00031],[212,207,185])
    return g


def tape():
    g=Geometry();length=55.;thickness=.00014;core_inner=.0381;core_outer=.0401;outer=np.sqrt(core_outer**2+length*thickness/np.pi)
    g.ring('paper_core',core_inner,core_outer,.024,[0,0,.012],[174,150,111],role='ordinary_consumable')
    g.ring('wound_blue_tape',core_outer,outer,.024,[0,0,.012],[42,94,174],role='ordinary_consumable')
    for i in range(1,11):g.ring('winding_edge_'+str(i),outer-i*.00014-.00002,outer-i*.00014,.00005,[0,0,.02403],[36,79,149])
    return g


def copper_block():
    g=Geometry();shape=cq.Workplane('XY').box(60,50,30).edges().chamfer(.15).val().translate((0,0,15))
    solid(g,'unmachined_copper_block',shape,[183,113,73],.85,role='raw_material')
    return g


def utility_cart():
    g=Geometry();polymer=[45,48,51];red=[166,33,41];width=.45085
    # Source overall dimensions constrain the envelope. Local moulding,
    # heights, brackets and folded work-surface state are photo reconstructions.
    for name,z,height in [('lower_shelf',.170,.080),('upper_shelf',.760,.080)]:
        outer=cq.Workplane('XY').box(964,width*1000,height*1000,centered=(True,True,False)).edges('|Z').fillet(8).val().translate((0,0,z*1000))
        inner=cq.Workplane('XY').box(944,(width-.020)*1000,height*1000,centered=(True,True,False)).edges('|Z').fillet(5).val().translate((0,0,(z+.012)*1000))
        solid(g,name,outer.cut(inner),polymer,role='ordinary_catalog_cart')
    for x in [-.43,.43]:
        for y in [-.195,.195]:
            post=cq.Solid.makeBox(70,48,526,cq.Vector((x-.035)*1000,(y-.024)*1000,245))
            # L-shaped moulded legs retain real holes and internal ribs.
            post=post.cut(cq.Solid.makeBox(59,37,528,cq.Vector((x-.0295)*1000,(y-.0185)*1000,244)))
            for z in [330,440,550,660]:post=post.cut(cq.Solid.makeCylinder(7,60,cq.Vector(x*1000,y*1000-30,z),cq.Vector(0,1,0)))
            solid(g,'perforated_leg_'+str(x)+'_'+str(y),post,polymer)
            for z in [.29,.40,.51,.62,.73]:g.box('leg_rib_'+str(x)+'_'+str(y)+'_'+str(z),[.059,.037,.004],[x,y,z],polymer)
    for x in [-.40,.40]:
        for y in [-.17,.17]:
            suffix=str(x)+'_'+str(y)
            g.cylinder('rubber_wheel_'+suffix,.0635,.038,[x,y,.0635],[34,37,41],axis=(0,1,0))
            for side in [-1,1]:
                g.cylinder('wheel_hub_'+suffix+'_'+str(side),.027,.002,[x,y+side*.020,.0635],[107,117,121],axis=(0,1,0),metal=.8)
                g.box('caster_fork_'+suffix+'_'+str(side),[.042,.004,.09],[x-.010,y+side*.025,.0995],STEEL,metal=.85)
            g.cylinder('wheel_axle_'+suffix,.007,.057,[x,y,.0635],STEEL,axis=(0,1,0),metal=.9)
            g.box('caster_plate_'+suffix,[.070,.065,.006],[x,y,.150],STEEL,metal=.85)
            g.cylinder('caster_swivel_'+suffix,.024,.014,[x,y,.162],STEEL,metal=.85)
            g.box('caster_mount_'+suffix,[.070,.065,.008],[x,y,.174],polymer)
            if x>.0:
                pedal=cq.Workplane('XY').box(42,22,3).val().rotate((0,0,0),(0,1,0),-18).translate((x*1000+40,y*1000,87))
                solid(g,'caster_brake_'+suffix,pedal,STEEL,.8)
    # Source handle is pivoted and has a red crossbar, rather than a generic
    # stainless trolley handle. Only one selected angle is built here.
    for y in [-.204,.204]:
        g.cylinder('handle_pivot_'+str(y),.043,.026,[.465,y,.805],polymer,axis=(0,1,0))
        g.cylinder('handle_pivot_button_'+str(y),.021,.003,[.465,y+np.sign(y)*.014,.805],red,axis=(0,1,0))
        p=np.array([[.465,y,.805],[.67348,y,.8964]]);vector=p[1]-p[0]
        g.cylinder('handle_arm_'+str(y),.018,np.linalg.norm(vector),p.mean(axis=0),polymer,axis=vector/np.linalg.norm(vector))
    g.cylinder('handle_crossbar',.018,.405,[.67348,0,.8964],red,axis=(0,1,0))
    # Folded front work surface and hinge; no added robot-specific workholding.
    g.box('folding_work_surface',[.300,width-.020,.007],[-.325,0,.8435],polymer)
    g.cylinder('work_surface_hinge',.006,width-.035,[-.175,0,.840],red,axis=(0,1,0))
    # Built-in storage wells near the handle, open at the top.
    for y in [-.145,0,.145]:
        outer=cq.Solid.makeBox(115,125,60,cq.Vector(355,y*1000-62.5,775))
        inner=cq.Solid.makeBox(105,115,60,cq.Vector(360,y*1000-57.5,780))
        solid(g,'handle_storage_well_'+str(y),outer.cut(inner),polymer)
    top_label(g,'cart_model_text','1997206',.14,.027,[-.325,0,.8471],tuple(polymer),(207,211,214))
    return g


def oily_waste_can():
    g=Geometry();red=[168,40,39]
    # Empty vessel with elevated base, pedal, linkage and separate lid. Source
    # approvals are not transferred to this reconstruction or to a waste stream.
    g.profile('ventilated_base',[(.141,0),(.149,0),(.149,.035),(.146,.040),(.141,.040),(.141,0)],red)
    g.profile('steel_body',[(0,.032),(.146,.032),(.146,.382),(.145,.387),(.144,.387),(.144,.034),(0,.034),(0,.032)],red,metal=.15)
    g.ring('rolled_bottom_seam',.145,.148,.005,[0,0,.045],red)
    g.profile('lid',[(0,.401),(.09,.399),(.142,.390),(.151,.387),(.151,.393),(.144,.397),(.09,.402),(0,.403),(0,.401)],red,metal=.15)
    g.cylinder('rear_hinge',.006,.055,[0,.145,.388],STEEL,axis=(1,0,0),metal=.85)
    g.box('hinge_mount',[.055,.005,.025],[0,.145,.376],STEEL,metal=.85)
    g.box('foot_pedal',[.095,.045,.007],[0,-.174,.016],STEEL,metal=.8)
    for x in np.linspace(-.040,.040,9):g.box('pedal_grip_'+str(x),[.002,.036,.001],[x,-.174,.020],DARK)
    g.cylinder('pedal_pivot',.006,.12,[0,-.130,.021],STEEL,axis=(1,0,0),metal=.8)
    g.tube('rear_linkage',[[0,-.130,.021],[0,.150,.027],[0,.154,.355],[0,.145,.388]],.003,STEEL)
    # Original role text only: no reproduced manufacturer certification marks.
    g.label('waste_role','OILY WIPES',.115,.040,[0,-.1461,.245],[236,221,158],[45,37,26])
    return g


def build():
    from build_preparation_supplies import models as preparation_models
    from build_robot_service import models as service_models
    from build_coating_supplies import models as coating_models
    from build_raw_stock import models as raw_models
    source=json.loads((HERE/'supply_sources.json').read_text());items=[]
    models=[('jonard_st450',stripper,{}),('idealtek_aa_sa_t6',tweezers,{}),('buerkle_7102_2000',jug,{}),('wiha_26015',driver,{}),
        ('omega_ambient_rtd',ambient_rtd,{}),('omega_smpw_cc_kit',connector_kit,{}),
        ('nano_pe_stock',lambda:film_stack('nano PE',.000016,8),{}),('ldpe_stock',lambda:film_stack('LDPE',.00005,6),{}),
        ('mylar_stock',lambda:film_stack('mylar',.000012,3,(.500,.300)),{}),('masking_tape',tape,{}),('calibration_copper_stock',copper_block,{}),
        ('rubbermaid_1997206',utility_cart,{}),('justrite_09100',oily_waste_can,{})]
    models.extend(preparation_models())
    models.extend(service_models())
    models.extend(coating_models())
    models.extend(raw_models())
    for key,fn,extra in models:
        result=fn();g=result[0] if isinstance(result,tuple) else result
        if isinstance(result,tuple):extra['cable' if key=='omega_ambient_rtd' else 'contents' if key=='omega_smpw_cc_kit' else 'details']=result[1]
        geometry=export_review(g,'supply_'+key);record=next(v for v in source['items'] if v['id']==key)
        items.append(dict(id=key,label=record['label'],resources=record['resources'],geometry=geometry,source_record=key,
            status='geometry_for_review_not_manipulation_qualified',**extra))
    write_json(HERE/'supplies.json',dict(schema_version=1,source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [Path(__file__),HERE/'build_preparation_supplies.py',HERE/'build_robot_service.py',HERE/'build_coating_supplies.py',HERE/'build_raw_stock.py',HERE/'supply_sources.json',HERE/'stock_sources.json',HERE/'geometry_tools.py',HERE/'ordinary_tools.json']],items=items,
        quantity_allocation='Selected staged stock and 8 separate thermocouple connector pairs. Campaign/recovery consumption is not yet accepted.',
        asset_acceptance=False,manipulation_qualified=False))
    print(json.dumps(dict(supply_types=len(items),component_meshes=sum(i['geometry']['parts'] for i in items))))


if __name__=='__main__':build()
