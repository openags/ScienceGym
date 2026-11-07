"""Model-specific Keithley 2000 reconstruction from manufacturer documentation.

Blender 2.82+; dimensions in metres. Front-panel feature positions are traced
from manual Figure 2-1 and scaled to the published rack envelope. They are
image-derived estimates, not vendor CAD or measured port tolerances.
"""
import bpy
import math
import json
import hashlib
from pathlib import Path
from mathutils import Vector

HERE=Path(__file__).resolve().parent
for name in ['geometry','evidence']:(HERE/name).mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
bpy.context.preferences.filepaths.save_version=0
root=bpy.data.objects.new('KEITHLEY_2000',None);scene.collection.objects.link(root)
parts=[];interfaces=[]
font=bpy.data.fonts.load('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
font.pack()


def material(name,color,metal=0,rough=.4):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    bsdf=m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=(*color,1)
    bsdf.inputs['Metallic'].default_value=metal;bsdf.inputs['Roughness'].default_value=rough
    return m


CASE=material('warm_gray_powdercoat',(.49,.50,.47),.15,.53)
PANEL=material('front_panel',(.69,.70,.65),0,.46)
DARK=material('dark_polymer',(.022,.027,.025),0,.48)
BLACK=material('black_socket',(.009,.012,.011),0,.38)
RED=material('red_socket',(.52,.014,.009),0,.40)
METAL=material('nickel_contact',(.59,.61,.58),.92,.26)
GLASS=material('VFD_window',(.002,.004,.003),0,.23)
GLASS.node_tree.nodes.get('Principled BSDF').inputs['Specular'].default_value=.12
INK=material('panel_print',(.012,.016,.014),0,.72)
WHITE=material('key_print',(.81,.84,.80),0,.7)


def finish(o,name,mat,role='housing',bevel=0):
    o.name=name;o.parent=root;o.data.materials.append(mat)
    if bevel:
        o.data.use_auto_smooth=True
        m=o.modifiers.new('edge_radius','BEVEL');m.width=bevel;m.segments=3
        o.modifiers.new('normals','WEIGHTED_NORMAL')
    o['part_id']=name;o['role']=role
    parts.append(o);return o


def box(name,size,pos,mat,role='housing',bevel=.0006):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,mat,role,bevel)


def cylinder(name,radius,depth,pos,mat,role='fastener',axis='Y'):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=radius,depth=depth,location=pos)
    o=bpy.context.object
    o.rotation_euler=(math.pi/2,0,0) if axis=='Y' else (0,math.pi/2,0) if axis=='X' else (0,0,0)
    return finish(o,name,mat,role,.00015)


def annulus(name,inner,outer,depth,pos,mat,role):
    n=64;verts=[];faces=[]
    for y,r in [(-depth/2,outer),(depth/2,outer),(-depth/2,inner),(depth/2,inner)]:
        verts.extend([(pos[0]+r*math.cos(i*2*math.pi/n),pos[1]+y,pos[2]+r*math.sin(i*2*math.pi/n)) for i in range(n)])
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);scene.collection.objects.link(o)
    return finish(o,name,mat,role)


def label(name,text,pos,size,mat=INK):
    c=bpy.data.curves.new(name,'FONT');c.font=font;c.body=text;c.size=size;c.align_x='CENTER';c.align_y='CENTER'
    c.extrude=.000003;o=bpy.data.objects.new(name,c);scene.collection.objects.link(o)
    o.location=pos;o.rotation_euler=(math.pi/2,0,0)
    return finish(o,name,mat,'label')


def point(px,py,y=-.182):
    # Manual Figure 2-1 crop: rack front spans x=265..648,y=196..349.
    return ((px-265)/383*.213-.1065,y,.015+(349-py)/153*.089)


# Hollow sheet-metal shell; no solid volume seals the front socket bores.
box('top_shell',(.205,.345,.0015),(0,-.0015,.10325),CASE)
box('bottom_shell',(.205,.345,.0015),(0,-.0015,.01575),CASE)
for sign in [-1,1]:
    box('side_shell_'+str(sign),(.0015,.345,.086),(sign*.10175,-.0015,.0595),CASE)
    box('front_bumper_'+str(sign),(.008,.019,.089),(sign*.1025,-.1755,.0595),PANEL,bevel=.002)
    box('rear_bumper_'+str(sign),(.008,.012,.089),(sign*.1025,.179,.0595),PANEL,bevel=.002)
    for y in [-.126,.13]:box('foot_'+str(sign)+'_'+str(y),(.019,.032,.015),(sign*.085,y,.0075),DARK,role='support',bevel=.003)
    # Folded bench handle: outer width matches the 238 mm bench envelope.
    cylinder('handle_pivot_'+str(sign),.012,.012,(sign*.112, -.12,.05),DARK,'handle_pivot','X')
    arm=box('handle_arm_'+str(sign),(.010,.0652,.012),(sign*.114,-.1465,.031),DARK,'handle',.004)
    arm.rotation_euler.x=math.atan2(.038,.053)
box('handle_crossbar',(.228,.012,.012),(0,-.173,.012),DARK,'handle',.004)
rear_panel=box('rear_panel',(.197,.002,.083),(0,.178,.0595),CASE)

# Front face has a separate terminal plate with real through-bores.
box('key_panel',(.166,.003,.0415),point(414,313.3,-.180),PANEL)
box('display_bezel',(.166,.004,.0465),point(414,236,-.1805),DARK,bevel=.001)
box('display_window',(.153,.001,.030),point(414,238,-.183),GLASS,'display')
label('brand','KEITHLEY',point(294,202,-.184),.004,WHITE)
label('model','2000 MULTIMETER',point(527,268,-.184),.0031,WHITE)
# The display is powered off. No fabricated measurement is printed on it.
terminal=box('terminal_panel',(.047,.003,.084),point(605.5,272,-.1805),PANEL,bevel=.001)
for name,px,py,color in [('sense_hi',587,227,RED),('sense_lo',587,262,BLACK),('input_hi',622,227,RED),('input_lo',622,262,BLACK),('amps',622,299,BLACK)]:
    pos=point(px,py,-.181)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.0042,depth=.025,location=pos,rotation=(math.pi/2,0,0))
    cutter=bpy.context.object;bpy.context.view_layer.objects.active=terminal
    mod=terminal.modifiers.new('bore_'+name,'BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
    annulus(name+'_insulator',.0022,.0065,.005,point(px,py,-.1825),color,'socket_insulator')
    annulus(name+'_contact',.002,.0022,.015,point(px,py,-.174),METAL,'electrical_contact')
    interfaces.append(dict(id=name,kind='banana_socket',axis=[0,1,0],entry_m=list(point(px,py,-.185)),bore_radius_m=.002,insertion_depth_m=.012,
                           dimensions_basis='selected 4 mm banana interface; depth and tolerance unmeasured',layout_basis='manufacturer manual Figure 2-1'))
for text,px,py in [('SENSE',587,203),('4 WIRE',587,210),('INPUT',622,207),('HI',637,227),('LO',637,262),('AMPS',622,320),('INPUTS',587,282),('FRONT/REAR',587,313)]:
    label('legend_'+text,text,point(px,py,-.184),.0026)
cylinder('input_selector',.0048,.005,point(587,299,-.1825),PANEL,'push_button')
interfaces.append(dict(id='input_selector',kind='latched_push_button',center_m=list(point(587,299,-.185)),axis=[0,1,0],travel_m=.002,travel_basis='inferred'))

functions=['DCV','ACV','DCI','ACI','Ω2','Ω4','FREQ','TEMP']
shifted=['MX+B','%','dBm','dB','CONT','DIODE','PERIOD','TCOUPL']
for i,(text,secondary) in enumerate(zip(functions,shifted)):
    px=325+i*25
    cylinder('key_'+text,.0052,.003,point(px,293,-.183),DARK,'push_button')
    label('text_'+text,text,point(px,293,-.185),.00265,WHITE)
    label('shift_'+text,secondary,point(px,281,-.183),.0020)
    interfaces.append(dict(id=text,kind='push_button',center_m=list(point(px,293,-.1845)),axis=[0,1,0],travel_m=.001,travel_basis='inferred'))
for row,(py,names) in enumerate([(314,['EX TRIG','TRIG','STORE','RECALL','FILTER','REL','<','>']),
                                (334,['OPEN','CLOSE','STEP','SCAN','DIGITS','RATE','EXIT','ENTER'])]):
    for i,text in enumerate(names):
        px=325+i*25
        box('key_'+text,(.012,.003,.0048),point(px,py,-.183),PANEL,'push_button',.002)
        label('text_'+text,text,point(px,py,-.185),.0023)
        interfaces.append(dict(id=text,kind='push_button',center_m=list(point(px,py,-.1845)),axis=[0,1,0],travel_m=.001,travel_basis='inferred'))
for text,px,py in [('SHIFT',294,293),('LOCAL',294,312),('POWER',294,335),('RANGE_UP',540,291),('AUTO',540,312),('RANGE_DOWN',540,334)]:
    cylinder('key_'+text,.0035 if px==294 else .0045,.003,point(px,py,-.183),DARK if text!='POWER' else PANEL,'push_button')
    if px==294:label('text_'+text,text,point(px-14,py,-.183),.0018)
    else:label('text_'+text,'AUTO' if text=='AUTO' else '+' if py==291 else '-',point(px,py,-.185),.0024,WHITE)
    interfaces.append(dict(id=text,kind='push_button',center_m=list(point(px,py,-.1845)),axis=[0,1,0],travel_m=.001,travel_basis='inferred'))

# Manufacturer Figure 2-2 supplies the distinct rear layout. Interface depths
# and retention geometry are reconstruction estimates, not metrology data.
def rearpoint(px,py,y=.181):
    return (.1065-(px-310)/520*.213,y,.015+(625-py)/211*.089)


def rearlabel(name,text,px,py,size=.0025):
    o=label(name,text,rearpoint(px,py,.184),size)
    o.rotation_euler=(math.pi/2,0,math.pi)
    return o


for name,px,py,color in [('rear_sense_hi',353,451,RED),('rear_sense_lo',353,502,BLACK),('rear_input_hi',402,451,RED),('rear_input_lo',402,502,BLACK)]:
    pos=rearpoint(px,py,.178)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.0042,depth=.025,location=pos,rotation=(math.pi/2,0,0))
    cutter=bpy.context.object;bpy.context.view_layer.objects.active=rear_panel
    mod=rear_panel.modifiers.new('bore_'+name,'BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
    annulus(name+'_insulator',.0022,.0065,.004,rearpoint(px,py,.181),color,'socket_insulator')
    annulus(name+'_contact',.002,.0022,.015,rearpoint(px,py,.171),METAL,'electrical_contact')
    interfaces.append(dict(id=name,kind='banana_socket',axis=[0,-1,0],entry_m=list(rearpoint(px,py,.183)),bore_radius_m=.002,insertion_depth_m=.012,layout_basis='manufacturer manual Figure 2-2',dimensions_basis='selected interface; depth and tolerance unmeasured'))
for text,px,py in [('SENSE',353,526),('4 WIRE',353,536),('INPUT',402,526),('HI',377,437),('LO',377,514),('TRIGGER',517,472),('LINK',517,482),('RS232',592,483),('IEEE-488',716,458)]:rearlabel('rear_'+text,text,px,py)
box('scanner_slot_cover',(.078,.002,.027),rearpoint(424,580,.18),CASE,'removable_panel')
for px in [335,516]:cylinder('scanner_screw_'+str(px),.0028,.0015,rearpoint(px,580,.1815),METAL)
annulus('trigger_link_shell',.0042,.0052,.004,rearpoint(517,500,.181),METAL,'connector_shell')
cylinder('trigger_link_insert',.0042,.001,rearpoint(517,500,.1805),DARK,'connector_insert')
interfaces.append(dict(id='trigger_link',kind='8_pin_mini_DIN',entry_m=list(rearpoint(517,500,.183)),axis=[0,-1,0],layout_basis='manufacturer manual Figure 2-2',contact_dimensions_qualified=False))
for i,(x,z) in enumerate([(-.0017,.002),(0,.002),(.0017,.002),(-.0024,0),(0,0),(.0024,0),(-.001,-.002),(.001,-.002)]):
    p=rearpoint(517,500,.1812);cylinder('trigger_link_socket_'+str(i),.00042,.0004,(p[0]+x,p[1],p[2]+z),BLACK,'electrical_contact')


def trapezoid_shell(name,px,py,width,height,pins):
    # Four metal strips and recessed insert form an open connector mouth.
    center=Vector(rearpoint(px,py,.181));w=width/2;h=height/2;chamfer=.0025
    for sign in [-1,1]:
        box(name+'_edge_'+str(sign),(width-(.004 if sign<0 else 0),.004,.001),center+Vector((0,0,sign*h)),METAL,'connector_shell')
        edge=box(name+'_side_'+str(sign),(.001,.004,height),center+Vector((sign*(w-chamfer/2),0,0)),METAL,'connector_shell')
        edge.rotation_euler.y=sign*math.atan2(chamfer,height)
        cylinder(name+'_jackscrew_'+str(sign),.0024,.003,center+Vector((sign*(w+.0045),0,0)),METAL,'retainer')
    box(name+'_insert',(width-.003,.001,height-.002),center+Vector((0,-.001,0)),DARK,'connector_insert')
    for row,count in enumerate(pins):
        for i in range(count):
            cylinder(name+'_socket_'+str(row)+'_'+str(i),.00045,.0004,center+Vector(((i-(count-1)/2)*.0022,0,(.5-row)*.0026)),BLACK,'electrical_contact')
    interfaces.append(dict(id=name,kind='connector',entry_m=list(center+Vector((0,.002,0))),axis=[0,-1,0],pin_rows=pins,layout_basis='manufacturer manual Figure 2-2',contact_dimensions_qualified=False))


trapezoid_shell('RS232',592,500,.016,.007,[5,4])
trapezoid_shell('IEEE488',716,495,.032,.011,[12,12])
box('mains_module',(.073,.004,.030),rearpoint(686,578,.181),DARK,'power_entry')
box('fuse_drawer',(.018,.002,.026),rearpoint(626,578,.184),CASE,'fuse_holder')
box('voltage_selector',(.022,.001,.024),rearpoint(687,578,.1835),DARK,'line_selector')
rearlabel('line_selector_text','LINE',687,579,.003)
inlet=Vector(rearpoint(750,578,.183))
box('IEC_recess',(.018,.002,.024),inlet,BLACK,'power_inlet')
for i,(x,z) in enumerate([(0,.007),(-.004,-.004),(.004,-.004)]):box('IEC_contact_'+str(i),(.002,.002,.0008),inlet+Vector((x,.001,z)),METAL,'electrical_contact',.0001)
interfaces.append(dict(id='mains_inlet',kind='IEC_inlet',entry_m=list(inlet),axis=[0,-1,0],layout_basis='manufacturer manual Figure 2-2',contact_dimensions_qualified=False))
for sign in [-1,1]:
    for z in [.025,.094]:cylinder('rear_screw_'+str(sign)+'_'+str(z),.0017,.001,(sign*.092,.18,z),METAL)

scene.render.engine='CYCLES';scene.cycles.samples=96;scene.cycles.use_denoising=True
scene.view_layers[0].cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.13,.16,.20,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
scene.view_settings.view_transform='Filmic';scene.view_settings.exposure=-2.2
for name,pos,power,size in [('key',(-.3,-.45,.5),85,.5),('fill',(.4,-.1,.25),45,.4),('rim',(0,.35,.5),95,.35)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.size=size
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=pos
    o.rotation_euler=(Vector((0,0,.05))-o.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('camera');camera=bpy.data.objects.new('camera',data);scene.collection.objects.link(camera);scene.camera=camera
camera.data.type='ORTHO';camera.data.ortho_scale=.54
camera.location=(.35,-.62,.32);camera.rotation_euler=(Vector((0,0,.05))-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update()
part_rows=[]
for o in parts:
    part_rows.append(dict(id=o.name,role=o['role'],location_m=list(o.location),dimensions_m=list(o.dimensions)))
(HERE/'parts.json').write_text(json.dumps(part_rows,indent=2)+'\n')
(HERE/'interfaces.json').write_text(json.dumps(dict(model='Keithley 2000',interfaces=interfaces,qualified_contact_tolerances=False),indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'geometry/keithley_2000.blend'))
for o in parts:
    if o.type in {'CURVE','FONT'}:
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
        bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
root.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(HERE/'geometry/keithley_2000.glb'),export_format='GLB',export_selected=True,export_apply=True,export_extras=True)
scene.render.filepath=str(HERE/'evidence/three_quarter.png');bpy.ops.render.render(write_still=True)
camera.location=(0,-.7,.0595);camera.data.ortho_scale=.26;camera.rotation_euler=(Vector((0,0,.0595))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_y=800;scene.render.filepath=str(HERE/'evidence/front.png');bpy.ops.render.render(write_still=True)
camera.location=(0,.7,.0595);camera.rotation_euler=(Vector((0,0,.0595))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(HERE/'evidence/rear.png');bpy.ops.render.render(write_still=True)
(HERE/'build_receipt.json').write_text(json.dumps(dict(builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    parts=len(parts),interfaces=len(interfaces),front_interfaces=sum(x['axis'][1]>0 for x in interfaces),
    rear_interfaces=sum(x['axis'][1]<0 for x in interfaces),blender=bpy.app.version_string,whole_equipment_qualified=False),indent=2)+'\n')
