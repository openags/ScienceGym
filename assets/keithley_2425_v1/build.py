"""Model-specific Keithley 2425 reconstruction from manufacturer documentation.

Blender 2.82+; dimensions in metres. Front-panel feature positions are traced
from Series user manual Figure 1-1 and scaled to the published rack envelope. They are
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
root=bpy.data.objects.new('KEITHLEY_2425',None);scene.collection.objects.link(root)
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


# Figure 1-1 front crop: x=309..1004, y=619..906. Source-specific
# 125 V terminal legends and 2425 identity follow the 2425 service manual.
def point(px,py,y=-.182):return ((px-309)/695*.213-.1065,y,.015+(906-py)/287*.089)
def rearpoint(px,py,y=.181):return (.1065-(px-287)/760*.213,y,.015+(563-py)/287*.089)
def rearlabel(name,text,px,py,size=.0025):
    o=label(name,text,rearpoint(px,py,.184),size);o.rotation_euler=(math.pi/2,0,math.pi);return o


BLUE=material('guard_sense_blue',(.025,.075,.34),0,.4)
IVORY=material('guard_white',(.78,.79,.73),0,.4)
box('key_panel',(.165,.003,.040),point(580,838,-.180),PANEL)
box('display_bezel',(.164,.004,.0445),point(580,701,-.1805),DARK,bevel=.001)
box('display_window',(.153,.001,.030),point(580,698,-.183),GLASS,'display')
label('brand','KEITHLEY',point(371,638,-.184),.004,WHITE)
label('model','2425 100 W SourceMeter',point(690,756,-.184),.0031,WHITE)
terminal=box('terminal_panel',(.045,.003,.084),point(923,764,-.1805),PANEL,bevel=.001)


def banana(name,px,py,color,back=False):
    coordinate=rearpoint if back else point;panel=rear_panel if back else terminal
    pos=coordinate(px,py,.178 if back else -.181)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.0042,depth=.025,location=pos,rotation=(math.pi/2,0,0));cutter=bpy.context.object
    bpy.context.view_layer.objects.active=panel;mod=panel.modifiers.new('bore_'+name,'BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
    annulus(name+'_insulator',.0022,.0065,.005,coordinate(px,py,.1825 if back else -.1825),color,'socket_insulator')
    annulus(name+'_contact',.002,.0022,.015,coordinate(px,py,.174 if back else -.174),METAL,'electrical_contact')
    interfaces.append(dict(id=name,kind='banana_socket',axis=[0,-1 if back else 1,0],entry_m=list(coordinate(px,py,.185 if back else -.185)),
        bore_radius_m=.002,insertion_depth_m=.012,dimensions_basis='Selected 4 mm interface; actual depth and tolerance unmeasured',
        layout_basis='Series user manual Figure 1-2' if back else 'Series user manual Figure 1-1 and 2425 service manual Figure 1-1'))


for name,x,y,color in [('sense_hi',892,682,RED),('sense_lo',892,748,BLACK),('force_hi',956,682,RED),('force_lo',956,748,BLACK)]:banana(name,x,y,color)
for text,x,y in [('4-WIRE',892,643),('SENSE',892,652),('INPUT/',956,643),('OUTPUT',956,652),('HI',924,663),('LO',924,773),('125V',866,711),('PEAK',866,720),('5V',925,711),('PEAK',925,720),('125V',981,711),('PEAK',981,720),('250V',981,777),('PEAK',981,786),('TERMINALS',958,832)]:label('legend_'+text+'_'+str(x),text,point(x,y,-.184),.0022)


def button(name,text,x,y,shape='round',radius=.0047,width=.011,height=.005,secondary=None):
    if shape=='round':cylinder('key_'+name,radius,.003,point(x,y,-.183),DARK,'push_button')
    else:box('key_'+name,(width,.003,height),point(x,y,-.183),PANEL,'push_button',min(.0018,height/2.2))
    label('text_'+name,text,point(x,y,-.185),.0026,WHITE if shape=='round' else INK)
    if secondary:label('secondary_'+name,secondary,point(x,y+23,-.183),.0018)
    interfaces.append(dict(id=name,kind='push_button',center_m=list(point(x,y,-.1845)),axis=[0,1,0],travel_m=.001,travel_basis='inferred'))


for name,text,x in [('MEAS_V','V',425),('MEAS_I','I',467),('MEAS_R','Ω',515),('FCTN','FCTN',558),('SOURCE_V','V',607),('SOURCE_I','I',648),('SOURCE_UP','+',699),('SOURCE_DOWN','-',739)]:button(name,text,x,801)
for group,x in [('MEAS',488),('SOURCE',667)]:label('group_'+group,group,point(x,778,-.183),.0022)
for y,labels in [(840,['LOCAL','REL','FILTER','LIMIT','TRIG','SWEEP','<','>']),(874,['DIGITS','SPEED','STORE','RECALL','CONFIG','MENU','EXIT','ENTER'])]:
    for x,text in zip([427,465,516,554,608,646,699,737],labels):button(text,text,x,y,'pill',width=.010,height=.0048)
for name,y,text in [('DISPLAY_EDIT',801,'EDIT'),('DISPLAY_TOGGLE',834,'TOGGLE'),('POWER',874,'POWER')]:
    cylinder('key_'+name,.0028,.003,point(370,y,-.183),PANEL,'push_button');label('text_'+name,text,point(341,y,-.183),.0019)
    interfaces.append(dict(id=name,kind='power_switch' if name=='POWER' else 'push_button',center_m=list(point(370,y,-.1845)),axis=[0,1,0],travel_m=.001,travel_basis='inferred'))
for name,text,y in [('RANGE_UP','+',798),('AUTO','AUTO',835),('RANGE_DOWN','-',874)]:button(name,text,810,y,'pill',width=.009,height=.0045)
box('output_button_recess',(.019,.002,.028),point(893,832,-.182),DARK,'panel')
cylinder('output_indicator',.0035,.001,point(893,817,-.1835),IVORY,'indicator')
button('OUTPUT','ON/OFF',893,854,'pill',width=.015,height=.008)
label('output_legend','OUTPUT',point(893,877,-.184),.0023)
button('TERMINALS','F/R',958,858,radius=.0043)
interfaces[-1]['kind']='latched_push_button'

# The rear drawing gives six sockets: four measurement terminals and two
# guards. Neither guard is silently repurposed as a FORCE/SENSE connection.
for name,x,y,color in [('rear_sense_hi',358,315,RED),('rear_sense_lo',358,388,BLACK),('rear_force_hi',430,315,RED),('rear_force_lo',430,388,BLACK),('guard',502,315,IVORY),('guard_sense',502,388,BLUE)]:banana(name,x,y,color,True)
for text,x,y in [('HI',394,291),('LO',394,420),('4-WIRE',357,429),('SENSE',357,438),('INPUT/',430,429),('OUTPUT',430,438),('V, Ω',554,306),('GUARD',554,317),('GUARD',557,387),('SENSE',557,399),('125V',326,349),('5V',394,349),('125V',469,349),('5V',533,349),('250V',490,433),('PEAK',490,442)]:rearlabel('rear_legend_'+text+'_'+str(x),text,x,y,.0022)
rearlabel('rear_brand','KEITHLEY',690,303,.0031)
rearlabel('rear_model','2425',735,322,.0025)
rearlabel('rear_line','100–240 VAC / 50–60 Hz',818,380,.0020)
rearlabel('rear_fuse','3.15 A / 250 V',818,360,.0020)
cylinder('chassis_ground_screw',.0022,.002,rearpoint(574,343,.181),METAL,'ground_terminal')
interfaces.append(dict(id='chassis_ground',kind='screw_terminal',entry_m=list(rearpoint(574,343,.183)),axis=[0,-1,0],contact_dimensions_qualified=False))


def connector(name,x,y,width,height,pins,male=False):
    center=Vector(rearpoint(x,y,.181));w=width/2;h=height/2;chamfer=.002
    for sign in [-1,1]:
        box(name+'_edge_'+str(sign),(width-(.003 if sign<0 else 0),.004,.001),center+Vector((0,0,sign*h)),METAL,'connector_shell')
        edge=box(name+'_side_'+str(sign),(.001,.004,height),center+Vector((sign*(w-chamfer/2),0,0)),METAL,'connector_shell');edge.rotation_euler.y=sign*math.atan2(chamfer,height)
        cylinder(name+'_jackscrew_'+str(sign),.0021,.003,center+Vector((sign*(w+.004),0,0)),METAL,'retainer')
    box(name+'_insert',(width-.003,.001,height-.002),center+Vector((0,-.001,0)),DARK,'connector_insert')
    for row,count in enumerate(pins):
        for i in range(count):cylinder(name+'_contact_'+str(row)+'_'+str(i),.0004,.0016 if male else .0004,center+Vector(((i-(count-1)/2)*.0022,0,(.5-row)*.0026)),METAL if male else BLACK,'electrical_contact')
    interfaces.append(dict(id=name,kind='connector',entry_m=list(center+Vector((0,.002,0))),axis=[0,-1,0],pin_rows=pins,layout_basis='Series user manual Figure 1-2',contact_dimensions_qualified=False))


connector('IEEE488',416,522,.032,.011,[12,12]);connector('RS232',602,523,.016,.007,[5,4]);connector('OUTPUT_ENABLE',972,518,.016,.007,[5,4],True)
for name,text,x,y in [('gpib','IEEE-488',416,471),('serial','RS-232',603,500),('output','OUTPUT ENABLE',972,490),('trigger','TRIGGER LINK',712,494)]:rearlabel('rear_'+name,text,x,y,.0022)
annulus('trigger_link_shell',.0042,.0052,.004,rearpoint(712,526,.181),METAL,'connector_shell')
cylinder('trigger_link_insert',.0042,.001,rearpoint(712,526,.1805),DARK,'connector_insert')
for i,(x,z) in enumerate([(-.0017,.002),(0,.002),(.0017,.002),(-.0024,0),(0,0),(.0024,0),(-.001,-.002),(.001,-.002)]):
    p=rearpoint(712,526,.1812);cylinder('trigger_link_socket_'+str(i),.00042,.0004,(p[0]+x,p[1],p[2]+z),BLACK,'electrical_contact')
interfaces.append(dict(id='trigger_link',kind='8_pin_mini_DIN',entry_m=list(rearpoint(712,526,.183)),axis=[0,-1,0],contact_dimensions_qualified=False))
box('mains_module',(.036,.004,.037),rearpoint(815,479,.181),DARK,'power_entry')
box('fuse_drawer',(.025,.002,.010),rearpoint(815,446,.184),CASE,'fuse_holder')
inlet=Vector(rearpoint(815,504,.183));box('IEC_recess',(.022,.002,.018),inlet,BLACK,'power_inlet')
for i,(x,z) in enumerate([(0,.005),(-.007,-.003),(.007,-.003)]):box('IEC_contact_'+str(i),(.0008,.002,.003),inlet+Vector((x,.001,z)),METAL,'electrical_contact',.0001)
interfaces.append(dict(id='mains_inlet',kind='IEC_inlet',entry_m=list(inlet),axis=[0,-1,0],contact_dimensions_qualified=False))
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
(HERE/'interfaces.json').write_text(json.dumps(dict(model='Keithley 2425',interfaces=interfaces,qualified_contact_tolerances=False),indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'geometry/keithley_2425.blend'))
for o in parts:
    if o.type in {'CURVE','FONT'}:
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
        bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
root.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(HERE/'geometry/keithley_2425.glb'),export_format='GLB',export_selected=True,export_apply=True,export_extras=True)
scene.render.filepath=str(HERE/'evidence/three_quarter.png');bpy.ops.render.render(write_still=True)
camera.location=(0,-.7,.0595);camera.data.ortho_scale=.26;camera.rotation_euler=(Vector((0,0,.0595))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_y=800;scene.render.filepath=str(HERE/'evidence/front.png');bpy.ops.render.render(write_still=True)
camera.location=(0,.7,.0595);camera.rotation_euler=(Vector((0,0,.0595))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(HERE/'evidence/rear.png');bpy.ops.render.render(write_still=True)
(HERE/'build_receipt.json').write_text(json.dumps(dict(builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    parts=len(parts),interfaces=len(interfaces),front_interfaces=sum(x['axis'][1]>0 for x in interfaces),
    rear_interfaces=sum(x['axis'][1]<0 for x in interfaces),blender=bpy.app.version_string,whole_equipment_qualified=False),indent=2)+'\n')
