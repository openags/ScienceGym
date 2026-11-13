"""Original A25/AC150 reconstruction from model-specific manufacturer evidence.

The source fixes the envelope and working opening. Small feature dimensions,
internal clearances and the unidentified historical controller are explicit
selections. The reservoir, handles, drain and controls are separate geometry.
"""
import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
for n in ['geometry','evidence']:(HERE/n).mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
bpy.context.preferences.filepaths.save_version=0
root=bpy.data.objects.new('THERMO_A25_SELECTED_AC150',None);scene.collection.objects.link(root);parts=[];interfaces=[]
font=bpy.data.fonts.load('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf');font.pack()
def material(name,color,metal=0,rough=.4):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;n=m.node_tree.nodes['Principled BSDF'];n.inputs['Base Color'].default_value=(*color,1);n.inputs['Metallic'].default_value=metal;n.inputs['Roughness'].default_value=rough;return m
WHITE=material('warm_gray_powdercoat',(.69,.72,.72),.15,.42);STEEL=material('brushed_stainless',(.52,.56,.57),.9,.31)
GRAY=material('moulded_gray',(.27,.32,.37),0,.43);DARK=material('dark_interior',(.015,.022,.026),0,.63)
BLUE=material('blue_panel_print',(.07,.24,.46),0,.50);PALE=material('light_blue_panel',(.25,.49,.68),0,.5)
RED=material('red_identity',(.67,.025,.025),0,.5);INK=material('dark_legends',(.02,.025,.027),0,.6)
LCD=material('unpowered_LCD',(.27,.39,.38),0,.28)
def finish(o,name,mat,role='housing'):
 o.name=name;o.parent=root;o.data.materials.append(mat);o['part_id']=name;o['role']=role;parts.append(o);return o
def box(name,size,pos,mat,role='housing',bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  mod=o.modifiers.new('edge_radius','BEVEL');mod.width=bevel;mod.segments=3;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 return finish(o,name,mat,role)
def cylinder(name,radius,depth,pos,mat,role='fastener',axis='Z',vertices=48):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=pos,rotation=(math.pi/2,0,0) if axis=='Y' else (0,math.pi/2,0) if axis=='X' else (0,0,0));return finish(bpy.context.object,name,mat,role)
def cut_box(o,size,pos):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos);c=bpy.context.object;c.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);mod=o.modifiers.new('opening','BOOLEAN');mod.operation='DIFFERENCE';mod.object=c;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(c,do_unlink=True)
def annulus(name,inner,outer,depth,pos,mat,role='port'):
 n=48;v=[(pos[0]+r*math.cos(i*2*math.pi/n),pos[1]+y,pos[2]+r*math.sin(i*2*math.pi/n)) for y,r in [(-depth/2,outer),(depth/2,outer),(-depth/2,inner),(depth/2,inner)] for i in range(n)];f=[]
 for i in range(n):
  j=(i+1)%n;f.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(v,[],f);mesh.update();o=bpy.data.objects.new(name,mesh);scene.collection.objects.link(o);return finish(o,name,mat,role)
def label(name,text,pos,size,mat=INK,rear=False):
 c=bpy.data.curves.new(name,'FONT');c.body=text;c.font=font;c.size=size;c.align_x='CENTER';c.align_y='CENTER';c.extrude=.000005;o=bpy.data.objects.new(name,c);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(math.pi/2,0,math.pi if rear else 0);return finish(o,name,mat,'identification_legend')
def screw(name,pos,axis='Z'):
 o=cylinder(name,.0026,.0013,pos,STEEL,axis=axis);return o
W=.273;D=.483;H=.749;RIM=.515;FRONT=-D/2
# The body is a hollow shell. Vent fields are open grids, not painted dots.
front=box('front_shell',(W-.014,.0018,.476),(0,FRONT+.0009,.253),WHITE,bevel=.001)
cut_box(front,(.142,.009,.225),(0,FRONT,.1535));cut_box(front,(.086,.012,.033),(0,FRONT,.355))
box('front_grille_dark_interior',(.142,.001,.225),(0,FRONT+.006,.1535),DARK,'vent_interior')
for i in range(18):box('front_grille_v_'+str(i),(.0017,.002,.225),(-.071+i*.142/17,FRONT,.1535),WHITE,'vent_grille')
for i in range(29):box('front_grille_h_'+str(i),(.142,.002,.0017),(0,FRONT,.041+i*.225/28),WHITE,'vent_grille')
for side in [-1,1]:
 panel=box('side_shell_'+str(side),(.0018,D-.026,.476),(side*(W/2-.0009),0,.253),WHITE,bevel=.001)
 cut_box(panel,(.010,.152,.178),(side*W/2,-.016,.165))
 box('side_vent_interior_'+str(side),(.001,.152,.178),(side*(W/2-.006),-.016,.165),DARK,'vent_interior')
 for i in range(16):box(f'side_{side}_grille_y_{i}',(.002,.002,.178),(side*(W/2-.001),-.092+i*.152/15,.165),WHITE,'vent_grille')
 for i in range(18):box(f'side_{side}_grille_z_{i}',(.002,.152,.002),(side*(W/2-.001),-.016,.076+i*.178/17),WHITE,'vent_grille')
 for y in [-.230,.230]:box(f'corner_rail_{side}_{y}',(.010,.014,.476),(side*(W/2-.005),y,.253),WHITE,bevel=.003)
 for y in [-.210,.210]:cylinder(f'foot_{side}_{y}',.011,.015,(side*.112,y,.0075),DARK,'support')
box('rear_shell',(W-.014,.0018,.476),(0,D/2-.0009,.253),WHITE,bevel=.001)
box('bottom_shell',(W-.012,D-.012,.002),(0,0,.016),STEEL)
# Folded rounded rim preserves an actual front working opening.
rim=box('reservoir_rim',(W,D,.027),(0,0,RIM-.0135),STEEL,bevel=.009)
cut_box(rim,(.173,.365,.05),(0,-.0215,RIM))
for x in [-.0875,.0875]:box('reservoir_wall_x_'+str(x),(.002,.365,.200),(x,-.0215,RIM-.100),STEEL,'reservoir_wall')
for y in [-.205,.162]:box('reservoir_wall_y_'+str(y),(.177,.002,.200),(0,y,RIM-.100),STEEL,'reservoir_wall')
box('reservoir_bottom',(.177,.369,.002),(0,-.0215,RIM-.201),STEEL,'reservoir_bottom')
# Controller bridge leaves exactly 173 x 184 mm working access in front.
box('controller_bridge',(.205,.207,.004),(0,.0835,RIM+.002),STEEL,'controller_bridge',.001)
for x in [-.094,.094]:
 for y in [-.008,.175]:screw('bridge_screw_'+str(x)+'_'+str(y),(x,y,RIM+.0047))
# Separate liftable lid and arched handle; no volume fills its grip opening.
lid=box('bath_lid',(.205,.190,.004),(0,-.115,RIM+.002),STEEL,'removable_lid',.0010)
cut_box(lid,(.201,.186,.006),(0,-.115,RIM))
v=[];faces=[];n=24
for y in [-.116,-.100]:
 for r in [.050,.058]:v.extend([(r*math.cos(i*math.pi/n),y,RIM+.004+r*.75*math.sin(i*math.pi/n)) for i in range(n+1)])
for i in range(n):
 j=i+1;a=n+1;faces.extend([(i,j,a+j,a+i),(2*a+i,3*a+i,3*a+j,2*a+j),(i,2*a+i,2*a+j,j),(a+i,a+j,3*a+j,3*a+i)])
faces.extend([(0,a,3*a,2*a),(n,2*a+n,3*a+n,a+n)])
mesh=bpy.data.meshes.new('lid_handle');mesh.from_pydata(v,[],faces);mesh.update();o=bpy.data.objects.new('lid_handle',mesh);scene.collection.objects.link(o);finish(o,'lid_handle',GRAY,'lid_handle')
interfaces.append(dict(id='bath_lid_grip',kind='handle',center_m=[0,-.108,RIM+.0445],approach_axis=[0,0,-1],clearance_m=.033,basis='inferred from A25 photograph'))
# Front recessed carrying handle, drain fitting and restrained model badge.
box('front_handle_back',(.086,.002,.033),(0,FRONT+.016,.355),DARK,'handle_recess')
for x in [-.046,.046]:box('front_handle_side_'+str(x),(.006,.014,.039),(x,FRONT+.004,.355),GRAY,'carrying_handle',.001)
for z in [.3355,.3745]:box('front_handle_edge_'+str(z),(.098,.014,.006),(0,FRONT+.004,z),GRAY,'carrying_handle',.001)
annulus('drain_body',.004,.010,.025,(0,FRONT-.006,.302),STEEL,'drain')
annulus('drain_knurled_cap',.004,.014,.013,(0,FRONT-.0195,.302),GRAY,'drain_cap')
for i in range(16):
 a=i*2*math.pi/16;cylinder('drain_knurl_'+str(i),.0007,.009,(.0138*math.cos(a),FRONT-.0195,.302+.0138*math.sin(a)),GRAY,'drain_cap',axis='Y',vertices=12)
label('bath_brand','Thermo',( -.072,FRONT-.001,.452),.016,RED);label('bath_brand_sub','S C I E N T I F I C',(-.072,FRONT-.001,.439),.0039)
label('bath_model','ARCTIC A25',(.087,FRONT-.001,.329),.006)
box('bath_blue_stripe',(W-.023,.0003,.003),(0,FRONT-.001,.323),PALE,'identification_legend')
interfaces.append(dict(id='front_drain',kind='rotary_cap',center_m=[0,FRONT-.026,.302],axis=[0,1,0],source='manual filling/draining section',selected_bore_radius_m=.004,inferred_geometry=True))
# AC150 face dimensions and control layout follow printed manual page 4-1.
HEAD_Y=.085;HEAD_BOTTOM=.536
box('controller_pedestal',(.132,.147,.017),(0,HEAD_Y,.5275),GRAY,'controller_mount',.002)
head_case=box('controller_case',(.165,.199,H-HEAD_BOTTOM),(0,HEAD_Y,(H+HEAD_BOTTOM)/2),WHITE,'controller_housing',.008)
FACE=HEAD_Y-.0995-.0005
box('controller_face',(.148,.002,.193),(0,FACE,.642),WHITE,'control_panel',.005)
box('display_bezel',(.088,.001,.046),(0,FACE-.0015,.687),GRAY,'display_bezel',.001)
box('LCD',(.084,.0003,.042),(0,FACE-.0022,.687),LCD,'display')
label('head_brand','Thermo',(0,FACE-.002,.727),.009,RED);label('head_brand_sub','S C I E N T I F I C',(0,FACE-.002,.718),.0026)
# Source face drawing pixel map. All seven keys are separate physical parts.
PANEL_LEFT=624;PANEL_RIGHT=1045;PANEL_TOP=360;PANEL_BOTTOM=865
def face(px,py,y=FACE-.003):return [(px-PANEL_LEFT)/(PANEL_RIGHT-PANEL_LEFT)*.148-.074,y,.738-(py-PANEL_TOP)/(PANEL_BOTTOM-PANEL_TOP)*.193]
for name,glyph,px,py,r in [('up','▲',836,617,.0045),('down','▼',836,709,.0045),('left','◀',789,663,.0045),('right','▶',881,663,.0045),('enter','↵',835,663,.0075),('escape','esc',918,618,.0067),('standby','',990,703,.0058)]:
 pos=face(px,py);cylinder('key_'+name,r,.0010,pos,BLUE,'push_button',axis='Y')
 if glyph:label('key_legend_'+name,glyph,[pos[0],pos[1]-.0006,pos[2]],r*1.25,WHITE)
 else:
  curve=bpy.data.curves.new('power_symbol','CURVE');curve.dimensions='3D';curve.bevel_depth=.00035;curve.bevel_resolution=2;spline=curve.splines.new('POLY');spline.points.add(36)
  for i,point in enumerate(spline.points):
   a=math.pi/4+i*(1.5*math.pi)/36;point.co=(pos[0]+.0033*math.sin(a),pos[1]-.0006,pos[2]+.0033*math.cos(a),1)
  obj=bpy.data.objects.new('key_legend_standby_ring',curve);scene.collection.objects.link(obj);finish(obj,'key_legend_standby_ring',WHITE,'identification_legend')
  box('key_legend_standby_line',(.0007,.0004,.004),(pos[0],pos[1]-.0006,pos[2]+.002),WHITE,'identification_legend')
 interfaces.append(dict(id='AC150_'+name,kind='push_button',center_m=pos,axis=[0,1,0],selected_travel_m=.0006,layout_source='USER_MANUAL printed 4-1',dimensions_inferred=True))
# Printed blue navigation surround, built as a shallow annulus behind keys.
p=face(835,663,FACE-.0012);annulus('navigation_surround',.0255,.027,.0002,p,PALE,'panel_print')
cut=face(693,780,FACE-.0028);cylinder('temperature_cutout',.007,.002,cut,RED,'rotary_cutout',axis='Y');label('cutout_arrow','→',[cut[0],cut[1]-.0011,cut[2]],.008)
interfaces.append(dict(id='high_temperature_cutout',kind='rotary_control',center_m=cut,axis=[0,1,0],inferred_geometry=True))
label('head_model','AC150',(.055,FACE-.002,.548),.0048);box('head_blue_stripe',(.148,.0003,.002),(0,FACE-.0015,.544),PALE,'panel_print')
# Recessed side cooling louvers, with separate slats and framed cavities.
for side in [-1,1]:
 cut_box(head_case,(.030,.117,.132),(side*.0825,HEAD_Y,.625))
 box('head_side_vent_'+str(side),(.001,.117,.132),(side*.068,HEAD_Y,.625),DARK,'vent_interior')
 for i in range(12):box(f'head_side_{side}_slat_{i}',(.002,.0035,.132),(side*.0815,HEAD_Y-.058+i*.116/11,.625),GRAY,'vent_grille',.001)
# Selected internal immersion envelope; no claim of exact impeller/heater CAD.
for x in [-.045,.045]:cylinder('immersion_guard_post_'+str(x),.003,.143,(x,HEAD_Y,.4485),STEEL,'immersion_clearance')
for z in [.384,.505]:box('immersion_guard_'+str(z),(.096,.120,.003),(0,HEAD_Y,z),STEEL,'immersion_clearance')
cylinder('pump_clearance',.025,.100,(.024,HEAD_Y,.443),STEEL,'immersion_clearance')
cylinder('sensor_stem',.003,.120,(-.026,HEAD_Y-.035,.437),STEEL,'immersion_clearance')
# AC150 rear: circulation, sensor, power. AC200-only USB/DB9 are omitted.
BACK=HEAD_Y+.1005
for name,x in [('outlet',-.034),('return',.034)]:
 annulus('circulation_'+name,.006,.008,.020,(x,BACK+.010,.550),STEEL,'circulation_port')
 cylinder('circulation_cap_'+name,.010,.003,(x,BACK+.0215,.550),STEEL,'removable_cap',axis='Y',vertices=6)
 interfaces.append(dict(id='circulation_'+name,kind='capped_circulation_port',center_m=[x,BACK+.023,.550],axis=[0,-1,0],outer_diameter_m=.016,source='USER_MANUAL printed 3-7',internal_bore_inferred=True))
annulus('remote_sensor_socket',.003,.005,.003,(-.018,BACK+.0015,.718),STEEL,'sensor_socket')
box('controller_rear_rocker',(.018,.004,.027),(.052,BACK+.002,.645),DARK,'rocker_switch',.001);label('rear_rocker_text','I\nO',(.052,BACK+.0042,.645),.006,WHITE,rear=True)
box('controller_power_inlet',(.022,.004,.028),(.052,BACK+.002,.588),DARK,'power_inlet',.001)
for x,z in [(.046,.586),(.058,.586),(.052,.597)]:box('power_contact_'+str(x),(.002,.004,.004),(x,BACK+.005,z),STEEL,'electrical_contact')
for i in range(16):box('rear_vent_'+str(i),(.002,.0005,.014),(-.055+i*.006,BACK+.0005,.672),DARK,'vent_interior')
for z in [.625,.730]:screw('rear_fastener_'+str(z),(0,BACK+.001,z),axis='Y')
box('bath_rear_rocker',(.018,.004,.026),(.084,D/2+.002,.421),DARK,'rocker_switch',.001)
for name,center in [('controller_power',[.052,BACK+.004,.645]),('bath_power',[.084,D/2+.004,.421])]:interfaces.append(dict(id=name,kind='rocker_switch',center_m=center,axis=[0,-1,0],layout_inferred=True))
bpy.context.view_layer.update()
contract=dict(model='Thermo Scientific A25 with selected AC150',units='m',axes='+Z up, -Y bath front',
 historical_controller_known=False,source_envelope_m=[W,D,H],selected_bath_rim_height_m=RIM,
 work_area=dict(center_xy_m=[0,-.112],width_m=.173,length_m=.184,depth_m=.200,rim_height_m=RIM,source='USER_MANUAL printed 2-2'),
 reservoir=dict(inner_x_m=[-.0865,.0865],inner_y_m=[-.204,.161],floor_z_m=RIM-.200,hidden_extension_inferred=True),
 fill_below_rim_m=[.022,.057],source_capacity_L=[7,12],interfaces=interfaces,
 lid_parts=['bath_lid','lid_handle'],selected_lid_sheet_m=.001,contact_qualified=False,
 selected_geometry_notes=['All local contact dimensions require qualification; no manufacturer CAD was available.','AC150 is a selected compatible controller, not identified as the paper historical unit.','Liquid, thermal control and electrical response are outside the static mesh.'])
(HERE/'interfaces.json').write_text(json.dumps(contract,indent=2)+'\n')
(HERE/'parts.json').write_text(json.dumps([dict(id=o.name,role=o['role'],dimensions_m=list(o.dimensions)) for o in parts],indent=2)+'\n')
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.view_layers[0].cycles.use_denoising=True
scene.render.resolution_x=1400;scene.render.resolution_y=1600;scene.render.resolution_percentage=100
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.18,.23,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
scene.view_settings.view_transform='Filmic';scene.view_settings.exposure=-2.0
for n,pos,power,size in [('key',(.7,-.8,1.5),170,1.0),('fill',(-.8,-.3,.9),110,.8),('rim',(.6,.7,1.2),100,.6)]:
 data=bpy.data.lights.new(n,'AREA');data.energy=power;data.size=size;o=bpy.data.objects.new(n,data);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.4))-o.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('camera');camera=bpy.data.objects.new('camera',data);scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=.95
camera.location=(.85,-1.2,1.1);camera.rotation_euler=(Vector((0,0,.38))-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'geometry/thermo_a25_ac150.blend'))
for o in parts:
 if o.type in ['FONT','CURVE']:
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
root.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(HERE/'geometry/thermo_a25_ac150.glb'),export_format='GLB',export_selected=True,export_apply=True,export_extras=True)
for view,pos,target,scale in [('front',(.85,-1.2,1.1),(0,0,.38),.95),('rear',(-.85,1.2,1.0),(0,0,.38),.95),('controls',(.22,-.5,.83),(0,.03,.643),.32),('reservoir',(.45,-.75,1.2),(0,-.02,.50),.63)]:
 for n in ['bath_lid','lid_handle']:bpy.data.objects[n].hide_render=view=='reservoir'
 camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
 scene.render.filepath=str(HERE/'evidence'/f'{view}.png');bpy.ops.render.render(write_still=True)
receipt=dict(builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),sources_sha256=hashlib.sha256((HERE/'sources.json').read_bytes()).hexdigest(),parts=len(parts),blender_version=bpy.app.version_string,manufacturer_CAD=False,
 artifacts_sha256={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE/'geometry').glob('*'))})
(HERE/'build_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('A25 ASSET',len(parts),'parts',flush=True)
