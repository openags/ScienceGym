"""Bare Nicolet 6700: source envelope and open, separately covered sample bay.

Local shapes are original reconstructions. Installed Smart accessories visible
in the source photographs are deliberately separate from the instrument.
"""
import bpy, math, json, hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
for n in ['geometry','evidence']:(HERE/n).mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
bpy.context.preferences.filepaths.save_version=0
root=bpy.data.objects.new('THERMO_NICOLET_6700',None);scene.collection.objects.link(root)
parts=[];interfaces=[];font=bpy.data.fonts.load('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf');font.pack()
def mat(name,color,metal=0,rough=.45):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
CASE=mat('warm_instrument_white',(.72,.72,.67));BASE=mat('dark_gray_base',(.13,.17,.19));DARK=mat('dark_purge_bay',(.025,.035,.038));BLUE=mat('blue_panel_print',(.06,.19,.38));RED=mat('red_brand',(.65,.018,.018));STEEL=mat('brushed_steel',(.5,.54,.56),.85,.3);INK=mat('dark_legends',(.025,.03,.04));GREEN=mat('unpowered_status_lenses',(.08,.28,.18))
def finish(o,name,material,role):
 o.name=name;o.parent=root;o.data.materials.append(material);o['part_id']=name;o['role']=role
 o['geometry_basis']='selected unmeasured interface' if role in ['selected_access_cover','lid_handle','cover_hinge','service_port','accessory_socket'] else 'manufacturer-photo reconstruction; local dimensions inferred'
 parts.append(o);return o
def bevel(o,width):
 if width:
  m=o.modifiers.new('moulded_edges','BEVEL');m.width=width;m.segments=4;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name)
 return o
def box(name,size,pos,material=CASE,role='housing',radius=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);bevel(o,radius);return finish(o,name,material,role)
def cylinder(name,r,h,pos,material=STEEL,role='fastener',axis='Z',n=48):
 bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=h,location=pos,rotation=(math.pi/2,0,0) if axis=='Y' else (0,math.pi/2,0) if axis=='X' else (0,0,0));return finish(bpy.context.object,name,material,role)
def cut(o,size,pos):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos);c=bpy.context.object;c.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);m=o.modifiers.new('open_cavity','BOOLEAN');m.operation='DIFFERENCE';m.object=c;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True)
def profile(name,xlo,xhi,yz,material=CASE,role='housing',radius=.004):
 v=[(x,y,z) for x in [xlo,xhi] for y,z in yz];n=len(yz);f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)];m=bpy.data.meshes.new(name);m.from_pydata(v,[],f);m.update();o=bpy.data.objects.new(name,m);scene.collection.objects.link(o);bevel(o,radius);return finish(o,name,material,role)
def label(name,text,pos,size,material=INK,top=False):
 c=bpy.data.curves.new(name,'FONT');c.body=text;c.font=font;c.size=size;c.align_x='CENTER';c.align_y='CENTER';c.extrude=.000005;o=bpy.data.objects.new(name,c);scene.collection.objects.link(o);o.location=pos
 if not top:o.rotation_euler=(math.pi/2,0,0)
 return finish(o,name,material,'identification_legend')
W=.692;D=.655;H=.254;CX=-.011;BAY_FRONT=-.290;BAY_BACK=-.030;FLOOR=.050
chassis=box('base_chassis',(W,D,.040),(0,0,.030),BASE,radius=.008)
cut(chassis,(.210,.260,.010),(CX,-.160,.051))
for x in [-.295,.295]:
 for y in [-.280,.270]:cylinder('foot_'+str(x)+'_'+str(y),.019,.010,(x,y,.005),DARK,'support')
# Sculpted side wings and ribbed rear enclosure leave the real bay open.
yz=[(-D/2,.050),(-D/2,.160),(-.302,.184),(-.255,.205),(-.060,.215),(.020,.252),(D/2,.252),(D/2,.050)]
left=profile('left_detector_housing',-W/2,CX-.119,yz)
right=profile('right_source_housing',CX+.119,W/2,yz)
rear=profile('rear_optics_housing',CX-.119,CX+.119,[(-.026,.050),(-.026,.248),(.020,.252),(D/2,.252),(D/2,.050)])
for i in range(28):
 x=-.328+i*.656/27
 box('rear_cover_rib_'+str(i),(.0035,.276,.002),(x,.176,.253),CASE,'cover_rib',.0008)
for x in [-.322,.322]:
 for y in [-.278,.278]:cylinder('case_fastener_'+str(x)+'_'+str(y),.0032,.001,(x,y,.051),STEEL)
bay=box('sample_compartment_floor',(.210,.260,.004),(CX,(BAY_FRONT+BAY_BACK)/2,FLOOR-.002),DARK,'accessory_mount')
for x in [CX-.107,CX+.107]:
 wall=box('sample_compartment_wall_'+str(x),(.004,.260,.200),(x,-.160,.150),DARK,'sample_bay_wall')
 # Optical windows are recessed holes through the bay liner, distinct from
 # any accessory's sample port; optical response is not simulated here.
 cut(wall,(.010,.036,.036),(x,-.150,.150))
 box('beam_window_'+str(x),(.0008,.034,.034),(x+(-.003 if x<CX else .003),-.150,.150),BASE,'optical_window')
box('sample_bay_rear_wall',(.210,.004,.200),(CX,BAY_BACK+.002,.150),DARK,'sample_bay_wall')
# Small mounting interfaces have explicit sockets, not painted cylinders.
for x in [CX-.075,CX+.075]:
 for y in [-.250,-.070]:
  socket=cylinder('mount_socket_'+str(x)+'_'+str(y),.006,.004,(x,y,.052),STEEL,'accessory_socket')
  bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.0025,depth=.010,location=(x,y,.052));c=bpy.context.object;m=socket.modifiers.new('socket_bore','BOOLEAN');m.operation='DIFFERENCE';m.object=c;bpy.context.view_layer.objects.active=socket;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True)
# Source photographs show detector/service caps and four scan controls.
for i,y in enumerate([-.215,-.100]):
 cylinder('detector_cap_recess_'+str(i),.032,.002,(-.250,y,.216),DARK,'service_recess')
 cylinder('detector_cap_'+str(i),.028,.007,(-.250,y,.2195),BASE,'service_cap')
 box('detector_cap_grip_'+str(i),(.037,.008,.006),(-.250,y,.226),BASE,'service_cap',.002)
cylinder('detector_selector',.009,.012,(-.250,-.1575,.221),BASE,'service_control')
box('status_panel',(.145,.064,.001),(-.250,.018,.251),CASE,'control_panel',.003)
for i,text in enumerate(['POWER','SCAN','LASER']):
 x=-.294+i*.043;cylinder('status_lens_'+str(i),.004,.001,(x,.032,.252),GREEN,'status_lens');label('status_text_'+str(i),text,(x,.013,.252),.004,top=True)
label('model','Nicolet 6700 FT-IR',(-.250,-.002,.252),.007,BLUE,top=True)
panel_angle=math.atan(.037/.080);panel_z=.215+.035*.037/.080+.0015
panel=box('scan_panel',(.198,.060,.002),(.231,-.025,panel_z),CASE,'control_panel',.001);panel.rotation_euler.x=panel_angle
def on_panel(x,y,height=0):return (x,-.025+y*math.cos(panel_angle)-height*math.sin(panel_angle),panel_z+y*math.sin(panel_angle)+height*math.cos(panel_angle))
for i,name in enumerate(['SAMPLE','BACKGROUND','OK / ENTER','STOP']):
 x=.157+i*.049;position=on_panel(x,.011,.00175);key=cylinder('scan_key_'+str(i),.006,.0015,position,BLUE,'push_button');key.rotation_euler.x=panel_angle
 text=label('scan_key_text_'+str(i),name,on_panel(x,-.014,.0011),.0035,BLUE,top=True);text.rotation_euler.x=panel_angle
 interfaces.append(dict(id='scan_'+str(i),kind='push_button',label=name,center_m=list(position),axis=[0,math.sin(panel_angle),-math.cos(panel_angle)],dimensions_inferred=True))
cylinder('front_source_access_ring',.027,.004,(.145,-D/2-.001,.120),STEEL,'service_ring','Y')
cylinder('front_source_access_cap',.023,.005,(.145,-D/2-.003,.120),BASE,'service_cap','Y')
box('front_brand_plate',(.093,.001,.034),(.277,-D/2-.001,.122),CASE,'identification_legend',.001)
label('brand','Thermo',(.277,-D/2-.002,.129),.014,RED);label('brand_sub','S C I E N T I F I C',(.277,-D/2-.002,.113),.0037)
# The selected removable hinged cover is explicitly inferred; no accessory
# body is used to fill the bay. Its motion remains unqualified at this stage.
cover=[]
cover.append(box('sample_bay_lid',(.238,.268,.004),(CX,-.160,.252),BASE,'selected_access_cover',.001))
cover.append(box('sample_bay_front',(.238,.004,.194),(CX,-.292,.151),BASE,'selected_access_cover',.001))
for x in [CX-.117,CX+.117]:cover.append(box('sample_bay_lid_skirt_'+str(x),(.004,.264,.012),(x,-.160,.244),BASE,'selected_access_cover',.001))
for x in [CX-.038,CX+.038]:cover.append(box('lid_handle_post_'+str(x),(.008,.018,.008),(x,-.296,.215),BASE,'lid_handle',.002))
cover.append(cylinder('lid_handle_bar',.004,.076,(CX,-.306,.215),BASE,'lid_handle','X'))
for x in [CX-.084,CX+.084]:cover.append(cylinder('lid_hinge_'+str(x),.004,.025,(x,BAY_BACK,.250),STEEL,'cover_hinge','X'))
interfaces.append(dict(id='sample_cover',kind='selected_hinge',axis=[1,0,0],pivot_m=[CX,BAY_BACK,.250],selected_open_angle_rad=-math.pi/2,parts=[o.name for o in cover],grasp_center_m=[CX,-.306,.215],inferred=True,qualified=False))
# Rear connections are approximate service envelopes; they do not qualify a
# model-specific electrical insertion interface.
for name,x,w,h,z in [('power',.255,.027,.022,.095),('usb',.193,.012,.012,.095),('external_detector',-.230,.031,.016,.110)]:
 box('rear_'+name+'_recess',(w+.006,.002,h+.006),(x,D/2+.001,z),DARK,'service_port');box('rear_'+name+'_socket',(w,.003,h),(x,D/2+.0015,z),BASE,'service_port')
for side in [-1,1]:
 shell=left if side<0 else right
 for i in range(20):
  y=.035+i*.012;cut(shell,(.012,.004,.028),(side*(W/2-.003),y,.095));box('side_vent_back_'+str(side)+'_'+str(i),(.0005,.004,.028),(side*(W/2-.009),y,.095),DARK,'vent_interior')
cfg=dict(model='Thermo Scientific Nicolet 6700',units='m',axes='+Z up; -Y instrument front',source_envelope_m=[W,D,H],source_mass_kg=69.,
 sample_bay=dict(center_xy_m=[CX,-.160],width_m=.210,depth_m=.260,height_m=.200,floor_z_m=FLOOR,datum_inferred=True),
 interfaces=interfaces,cover_parts=[o.name for o in cover],contact_qualified=False,manufacturer_CAD=False,
 exclusions=['Installed Smart accessories','IntegratIR sphere and its own reference/sample ports','Internal optical/electronic function'],
 reconstruction_notes=['Source envelope and clear sample-bay dimensions; local housing, ports and cover details are selected inferences.','Source photos contain different Smart accessories. Their exterior is not used as the bare spectrometer bay.'])
bpy.context.view_layer.update();(HERE/'interfaces.json').write_text(json.dumps(cfg,indent=2)+'\n');(HERE/'parts.json').write_text(json.dumps([dict(id=o.name,role=o['role'],dimensions_m=list(o.dimensions),geometry_basis=o['geometry_basis']) for o in parts],indent=2)+'\n')
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.view_layers[0].cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.18,.23,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5;scene.view_settings.view_transform='Filmic';scene.view_settings.exposure=-2
for n,pos,power,size in [('key',(.6,-1.0,1.4),220,1.2),('fill',(-.8,-.3,1),140,1),('rim',(.6,.8,1),130,.8)]:
 d=bpy.data.lights.new(n,'AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(n,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.15))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('camera');camera=bpy.data.objects.new('camera',d);scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=.95;camera.location=(.8,-1.2,.8);camera.rotation_euler=(Vector((0,0,.12))-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'geometry/nicolet_6700.blend'))
for o in parts:
 if o.type=='FONT':
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
root.select_set(True);bpy.ops.export_scene.gltf(filepath=str(HERE/'geometry/nicolet_6700.glb'),export_format='GLB',export_selected=True,export_apply=True,export_extras=True)
for view,pos,target,scale in [('front',(.8,-1.2,.8),(0,0,.12),.95),('rear',(-.8,1.2,.8),(0,0,.12),.95),('sample_bay',(.38,-.7,.68),(CX,-.16,.12),.50),('controls',(.45,-.55,.70),(.18,-.03,.21),.48)]:
 for o in cover:o.hide_render=view=='sample_bay'
 camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale;scene.render.filepath=str(HERE/'evidence'/f'{view}.png');bpy.ops.render.render(write_still=True)
receipt=dict(builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),sources_sha256=hashlib.sha256((HERE/'sources.json').read_bytes()).hexdigest(),parts=len(parts),blender_version=bpy.app.version_string,manufacturer_CAD=False,artifacts_sha256={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE/'geometry').glob('*'))})
(HERE/'build_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('NICOLET ASSET',len(parts),'parts',flush=True)
