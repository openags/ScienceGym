"""Manufacturer-informed USB-TC with individually accessible terminals.

Metres, +Z up, USB face +X. The source envelope and pin map are exact inputs;
housing profile, pitch and terminal internals are declared reconstruction choices.
Run in Blender 2.82+. No manufacturer CAD or photograph is embedded.
"""
import bpy
import math
import sys
import json
import hashlib
from pathlib import Path
from mathutils import Vector

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'cooling_scene_assets_v2'))
from interaction_geometry import PIN_SIGNALS,TC_CHANNEL_PINS
for n in ['geometry','evidence']:(HERE/n).mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
bpy.context.preferences.filepaths.save_version=0
root=bpy.data.objects.new('MCC_USB_TC',None);scene.collection.objects.link(root)
parts=[]


def material(name,color,metal=0,rough=.4):
    mat=bpy.data.materials.new(name);mat.diffuse_color=(*color,1);mat.use_nodes=True
    node=mat.node_tree.nodes['Principled BSDF'];node.inputs['Base Color'].default_value=(*color,1)
    node.inputs['Metallic'].default_value=metal;node.inputs['Roughness'].default_value=rough
    return mat


BLUE=material('blue_moulded_enclosure',(.19,.27,.47),0,.47)
PALE=material('pale_terminal_insulator',(.78,.77,.57),0,.43)
METAL=material('terminal_screw_steel',(.51,.53,.55),.85,.27)
BRASS=material('terminal_contact_metal',(.42,.33,.12),.75,.34)
BLACK=material('port_and_legend_black',(.009,.012,.016),0,.38)
WHITE=material('legend_white',(.86,.87,.84),0,.45)
GREEN=material('status_lens',(.10,.36,.025),.05,.24)
font=bpy.data.fonts.load('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')


def finish(obj,name,mat,role):
    obj.name=name;obj.parent=root;obj.data.materials.append(mat)
    obj['part_id']=name;obj['role']=role;parts.append(obj);return obj


def box(name,size,pos,mat,role,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos);obj=bpy.context.object;obj.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=obj.modifiers.new('moulded_edges','BEVEL');mod.width=bevel;mod.segments=3
        bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_apply(modifier=mod.name)
    return finish(obj,name,mat,role)


def cylinder(name,radius,depth,pos,mat,role,rotation=(0,0,0),vertices=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=pos,rotation=rotation)
    return finish(bpy.context.object,name,mat,role)


def shell_profile(name,sections,bevel):
    vertices=[]
    for z,x0,x1,half_y in sections:
        vertices.extend([(x0,-half_y,z),(x1,-half_y,z),(x1,half_y,z),(x0,half_y,z)])
    faces=[(3,2,1,0),tuple(range(len(vertices)-4,len(vertices)))]
    for layer in range(len(sections)-1):
        for i in range(4):
            j=(i+1)%4;a=4*layer
            faces.append((a+i,a+j,a+4+j,a+4+i))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj)
    mod=obj.modifiers.new('moulded_corner_radius','BEVEL');mod.width=bevel;mod.segments=3
    bpy.context.view_layer.objects.active=obj;obj.select_set(True);bpy.ops.object.modifier_apply(modifier=mod.name)
    return finish(obj,name,BLUE,'housing')


def cut_box(obj,size,pos):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos);cutter=bpy.context.object;cutter.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    mod=obj.modifiers.new('physical_opening','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
    bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter,do_unlink=True)


def cut_cylinder(obj,radius,depth,pos):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=radius,depth=depth,location=pos)
    cutter=bpy.context.object;mod=obj.modifiers.new('shaft_clearance','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
    bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter,do_unlink=True)


def label(name,text,pos,size,mat=BLACK,rotation=(0,0,0)):
    curve=bpy.data.curves.new(name,'FONT');curve.body=text;curve.font=font;curve.size=size
    curve.align_x='CENTER';curve.align_y='CENTER';curve.extrude=0
    obj=bpy.data.objects.new(name,curve);scene.collection.objects.link(obj);obj.location=pos;obj.rotation_euler=rotation
    return finish(obj,name,mat,'identification_legend')


L=.12852;W=.08839;H=.03556
base=shell_profile('lower_enclosure',[(0,-.0615,.0615,.0414),(.0035,-.0632,.0632,.0433),
    (.0115,-L/2,L/2,W/2),(.013,-L/2,L/2,W/2)],.0004)
roof=box('upper_central_shell',(.113,.0618,.02256),(0,0,.02428),BLUE,'housing',.0012)
endcaps=[]
for side in [-1,1]:
    sections=[]
    for z,outer,half_y in [(.013,L/2,W/2),(.026,L/2,W/2),(H,.0616,.0418)]:
        sections.append((z,.056 if side>0 else -outer,outer if side>0 else -.056,half_y))
    endcaps.append(shell_profile('endcap_'+('usb' if side>0 else 'rear'),sections,.0005))
# The endcap keeps the full documented width, while the terminal channels
# remain open from the sides. Tiny mould seam and relief dimensions are inferred.
for side in [-1,1]:
    box('terminal_channel_floor_'+str(side),(.112,.012,.002),(0,side*.0368,.014),BLUE,'housing',.0005)

pitch=.00381;start=-.0535;gap=.006
terminals=[]
for bank,side in enumerate([-1,1]):
    y=side*.0357
    for block,indexes in enumerate([range(10),range(10,26)]):
        xs=[start+i*pitch+(gap if i>=10 else 0) for i in indexes]
        lo,hi=min(xs)-pitch/2,max(xs)+pitch/2
        box(f'legend_backing_{bank}_{block}',(hi-lo,.00025,.0068),((hi+lo)/2,side*.03105,.0315),WHITE,'terminal_legend_strip')
    for i in range(26):
        pin=bank*26+i+1;x=start+i*pitch+(gap if i>=10 else 0)
        name=f'pin_{pin:02d}';entry=[x,side*.0401,.0221];screw=[x,y,.0274]
        housing=box(name+'_insulator',(.00355,.0082,.009),(x,y,.0223),PALE,'terminal_insulator',.00018)
        # A real rectangular wire-entry passage, with a backstop at 6 mm.
        cut_box(housing,(.0021,.0068,.0024),(x,side*.037,.0221))
        # The open plate needs an internal seat above the wire-entry ceiling;
        # its screw passes through a separate shaft bore in the upper wall.
        cut_box(housing,(.0022,.0032,.0007),(x,side*.0365,.0236))
        cut_cylinder(housing,.00070,.0036,(x,y,.0255))
        cut_cylinder(housing,.00140,.0025,(x,y,.02595))
        jaw=box(name+'_clamp',(.0020,.0030,.0006),(x,side*.0365,.0236),BRASS,'terminal_clamp',.00006)
        head=cylinder(name+'_screw',.00128,.0008,screw,METAL,'terminal_screw')
        cut_box(head,(.0028,.00045,.0005),(x,y,.02785))
        cylinder(name+'_shank',.00062,.0031,(x,y,.02545),METAL,'screw_shank',vertices=24)
        # Legends face outward on the raised wall behind each terminal bank.
        rotation=(math.pi/2 if side<0 else -math.pi/2,0,0 if side<0 else math.pi)
        label(name+'_legend',str(pin)+'\n'+PIN_SIGNALS[pin],(x,side*.03125,.0315),.00115,rotation=rotation)
        terminals.append(dict(pin=pin,signal=PIN_SIGNALS[pin],wire_entry_m=entry,
            insertion_axis=[0,-side,0],entry_width_m=.0021,entry_height_m=.0024,
            insertion_depth_m=.0055,screw_center_m=screw,screw_axis=[0,0,-1],
            selected_driver_slot_m=[.0026,.00045],selected_screw_pitch_m=.0005,
            parts=dict(housing=name+'_insulator',screw=name+'_screw',shank=name+'_shank',clamp=name+'_clamp'),
            inferred_contact_geometry=True))
    cjc_x=start+9*pitch+pitch/2+gap/2
    box('CJC_'+str(bank),(.0032,.0034,.0025),(cjc_x,y,.0205),BLACK,'cold_junction_sensor',.0003)

# USB-B shell: four-sided lower rectangle and two chamfered top corners.
usb_y=-.005;usb_z=.022;outer=[(-.0053,-.0055),(.0053,-.0055),(.0053,.0026),(.0028,.0055),(-.0028,.0055),(-.0053,.0026)]
inner=[(-.0042,-.0045),(.0042,-.0045),(.0042,.0022),(.0023,.0045),(-.0023,.0045),(-.0042,.0022)]
cut_box(endcaps[1],(.012,.0108,.0112),(.061,usb_y,usb_z))
cut_box(roof,(.009,.0108,.0112),(.057,usb_y,usb_z))
vertices=[(x,usb_y+y,usb_z+z) for x in [.057,.06426] for profile in [outer,inner] for y,z in profile]
faces=[]
for i in range(6):
    j=(i+1)%6
    faces.extend([(i,j,12+j,12+i),(6+i,18+i,18+j,6+j),(12+i,12+j,18+j,18+i),(i,6+i,6+j,j)])
mesh=bpy.data.meshes.new('usb_B_shell');mesh.from_pydata(vertices,[],faces);mesh.update()
obj=bpy.data.objects.new('usb_B_shell',mesh);scene.collection.objects.link(obj);finish(obj,'usb_B_shell',METAL,'usb_shell')
box('usb_B_contact_tongue',(.004,.0055,.0032),(.0587,usb_y,.0205),BLACK,'usb_tongue',.0002)
for i in range(4):box('usb_B_contact_'+str(i),(.003,.0005,.0002),(.060,usb_y+(i-1.5)*.0012,.02215),BRASS,'usb_contact')
for name,z in [('power',.019),('activity',.025)]:
    cylinder('LED_'+name,.0011,.00025,(.06424,.009,z),GREEN,'status_lens',(0,math.pi/2,0),32)

oval=cylinder('identity_oval',.016,.00012,(0,0,H+.00006),BLACK,'identity_badge',vertices=96)
oval.scale.y=.38
label('brand','MEASUREMENT COMPUTING',(0,.0018,H+.00014),.0016,WHITE)
label('model','USB-TC',(0,-.0015,H+.00014),.0021,WHITE)
bpy.context.view_layer.update()
interfaces=dict(model='Measurement Computing USB-TC',units='m',axes='+X USB face, +Z up',
    source_enclosure_m=[L,W,H],terminals=terminals,
    thermocouple_channels=[dict(channel=i,positive_pin=p,negative_pin=n) for i,(p,n) in enumerate(TC_CHANNEL_PINS)],
    usb=dict(type='USB Type-B',entry_m=[.06426,usb_y,usb_z],insertion_axis=[-1,0,0],geometry_inferred=True),
    cjc_locations_m=[[start+9*pitch+pitch/2+gap/2,s*.0357,.0205] for s in [-1,1]],
    inferred_terminal_pitch_m=pitch,declared_wire_gauge_range_AWG=[16,30],
    clamp_state='Selected open wire entries; a static reconstruction, not a threaded contact simulation',
    contact_qualified=False)
(HERE/'interfaces.json').write_text(json.dumps(interfaces,indent=2)+'\n')
(HERE/'parts.json').write_text(json.dumps([dict(id=o.name,role=o['role'],dimensions_m=list(o.dimensions)) for o in parts],indent=2)+'\n')

scene.render.engine='CYCLES';scene.cycles.samples=72;scene.cycles.use_denoising=True
scene.view_layers[0].cycles.use_denoising=True;scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.13,.16,.22,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.6
scene.view_settings.view_transform='Filmic';scene.view_settings.exposure=-1.0
for name,pos,power,size in [('key',(.10,-.10,.22),1.2,.18),('fill',(-.12,.09,.15),.8,.18),('rim',(.12,.12,.15),.5,.12)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=pos
    obj.rotation_euler=(Vector((0,0,.018))-obj.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('camera');camera=bpy.data.objects.new('camera',data);scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO'
camera.location=(.20,-.25,.21);camera.data.ortho_scale=.185
camera.rotation_euler=(Vector((0,0,.018))-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'geometry/mcc_usb_tc.blend'))
for obj in parts:
    if obj.type=='FONT':
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='DESELECT')
for obj in parts:obj.select_set(True)
root.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(HERE/'geometry/mcc_usb_tc.glb'),export_format='GLB',export_selected=True,export_apply=True,export_extras=True)
for name,pos,target,scale in [('three_quarter',(.20,-.25,.21),(0,0,.018),.185),('terminals',(.01,-.20,.11),(-.012,-.033,.025),.13),('usb',(.24,-.01,.09),(.058,0,.022),.115),('top',(0,0,.3),(0,0,.018),.155)]:
    camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
    scene.render.filepath=str(HERE/'evidence'/f'{name}.png');bpy.ops.render.render(write_still=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(HERE/'build_receipt.json').write_text(json.dumps(dict(builder_sha256=sha(Path(__file__)),source_sha256=sha(HERE/'sources.json'),
    shared_pinmap_sha256=sha(HERE.parent/'cooling_scene_assets_v2/interaction_geometry.py'),blender=bpy.app.version_string,parts=len(parts),
    artifacts_sha256={str(p.relative_to(HERE)):sha(p) for p in sorted((HERE/'geometry').glob('*'))},vendor_cad=False,contact_qualified=False),indent=2)+'\n')
