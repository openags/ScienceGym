"""Original reconstruction of the legacy 2012 IntegratIR DLaTGS variant."""
import bpy, math, json, hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
for n in ['geometry','evidence']:(HERE/n).mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
bpy.context.preferences.filepaths.save_version=0
root=bpy.data.objects.new('PIKE_INTEGRATIR_DTGS_048_4000',None);scene.collection.objects.link(root)
parts=[];interfaces=[];font=bpy.data.fonts.load('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf');font.pack()
def mat(name,color,metal=0,rough=.45):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
CASE=mat('warm_instrument_white',(.72,.72,.67));BASE=mat('dark_gray_base',(.13,.17,.19));DARK=mat('dark_purge_bay',(.025,.035,.038));BLUE=mat('blue_panel_print',(.06,.19,.38));RED=mat('red_brand',(.65,.018,.018));STEEL=mat('brushed_steel',(.5,.54,.56),.85,.3);INK=mat('dark_legends',(.025,.03,.04));GREEN=mat('unpowered_status_lenses',(.08,.28,.18))
def finish(o,name,material,role):
 o.name=name;o.parent=root;o.data.materials.append(material);o['part_id']=name;o['role']=role
 o['geometry_basis']='PIKE 2012 manual figure 1; local dimensions inferred'
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
BLACK=mat('black_anodized_case',(.035,.044,.049),.3,.4)
TOPMETAL=mat('warm_metal_top_panels',(.48,.43,.34),.85,.32)
GOLD=mat('gold_coated_sphere',(.83,.55,.14),.88,.3)
WINDOW=mat('optional_ZnSe_window',(.55,.31,.07),0,.15)
WHITE=mat('white_selector_index',(.83,.84,.82))
W=.175;D=.195;HEIGHT=.165;SPHERE=(.040,-.010,.0619);PORT=(.040,-.010,.101)
module=[];reference=[];cap=[];plate=[]
def sphere(name,r,pos,material,role):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=96,ring_count=64,radius=r,location=pos);return finish(bpy.context.object,name,material,role)
def subtract(o,c):
 m=o.modifiers.new('open_geometry','BOOLEAN');m.operation='DIFFERENCE';m.object=c;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True)
def bore(o,r,depth,pos,axis='Z'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=r,depth=depth,location=pos,rotation=(math.pi/2,0,0) if axis=='Y' else (0,math.pi/2,0) if axis=='X' else (0,0,0));subtract(o,bpy.context.object)
box('module_base',(W,D,.006),(0,0,.003),BLACK,'base',.001)
box('front_lower_rail',(W,.004,.025),(0,-D/2+.002,.0185),BLACK,'housing',.0008)
for z in [.012,.019,.026]:box('front_rail_groove_'+str(z),(W-.003,.0006,.0008),(0,-D/2-.0002,z),DARK,'case_detail')
box('front_panel',(W,.003,.070),(0,-D/2+.0015,.066),BLACK,'housing',.0006)
box('rear_panel',(W,.003,.095),(0,D/2-.0015,.0535),BLACK,'housing',.0006)
box('left_panel',(.003,D-.006,.095),(-W/2+.0015,0,.0535),BLACK,'housing',.0006)
right=box('right_panel',(.003,D-.006,.095),(W/2-.0015,0,.0535),BLACK,'housing',.0006)
cut(right,(.010,.040,.064),(W/2,0,.065))
box('right_recess_gold_plate',(.001,.036,.058),(W/2-.008,0,.065),GOLD,'optical_recess')
cylinder('right_optical_window',.014,.001,(W/2-.007,0,.065),DARK,'optical_window','X')
left_top=box('top_left_panel',(.100,.195,.002),(-.0375,0,.101),TOPMETAL,'top_panel',.0004)
right_top=box('top_sample_panel',(.0745,.195,.002),(.05025,0,.101),TOPMETAL,'sample_support',.0004)
bore(right_top,.009,.015,PORT)
s=sphere('gold_sphere_shell',.0393,SPHERE,GOLD,'sphere_shell')
bpy.ops.mesh.primitive_uv_sphere_add(segments=96,ring_count=64,radius=.0381,location=SPHERE);subtract(s,bpy.context.object);bore(s,.009,.060,(SPHERE[0],SPHERE[1],.106))
# The black detector enclosure is the distinguishing legacy DTGS feature;
# it is not the liquid-nitrogen Dewar of later MCT product photographs.
box('detector_enclosure',(.090,.100,.063),(-.035,.0425,.1335),BLACK,'detector_housing',.005)
cylinder('detector_top_access_cap',.009,.002,(-.020,.017,.166),BLACK,'service_cap')
for i,y in enumerate([.016,.031]):cylinder('detector_top_fastener_'+str(i),.0035,.001,(-.067,y,.1655),BLACK)
# The photograph establishes a top detector connector. Its exact contact
# count and mating pinout are unresolved, so no false pin array is drawn.
box('detector_connector_flange',(.043,.012,.0015),(-.035,.077,.16575),STEEL,'connector_envelope',.001)
outer=[(-.017,.0045),(.017,.0045),(.0145,-.0045),(-.0145,-.0045)]
inner=[(-.0158,.0034),(.0158,.0034),(.0135,-.0034),(-.0135,-.0034)]
v=[(-.035+x,.077+y,z) for z in [.1665,.170] for poly in [outer,inner] for x,y in poly]
f=[]
for i in range(4):
 j=(i+1)%4;f.extend([(i,j,j+8,i+8),(i+4,i+12,j+12,j+4),(i+8,j+8,j+12,i+12),(i,i+4,j+4,j)])
m=bpy.data.meshes.new('detector_connector_shell');m.from_pydata(v,[],f);m.update();m.flip_normals();o=bpy.data.objects.new('detector_connector_shell',m);scene.collection.objects.link(o);finish(o,o.name,STEEL,'connector_envelope')
box('detector_connector_recess',(.031,.006,.0005),(-.035,.077,.1668),DARK,'unresolved_connector_interior',.0005)
for x in [-.054,-.016]:
 o=cylinder('detector_connector_jack_'+str(x),.003,.004,(x,.077,.1675),STEEL,'connector_jack',n=6);bore(o,.0012,.008,(x,.077,.1675))
# Rotary selector and front push-in purge connector are independently named.
cylinder('selector_axis',.004,.008,(.032,-.101,.061),STEEL,'selector_axis','Y')
cylinder('sample_reference_knob',.011,.013,(.032,-.109,.061),BLACK,'rotary_selector','Y',n=96)
cylinder('selector_face',.009,.0008,(.032,-.116,.061),STEEL,'selector_face','Y')
box('selector_pointer',(.0008,.0003,.009),(.032,-.1165,.0655),WHITE,'selector_index')
for i in range(40):
 a=i*2*math.pi/40;cylinder('selector_knurl_'+str(i),.00035,.010,(.032+.011*math.cos(a),-.109,.061+.011*math.sin(a)),BLACK,'selector_knurl','Y',n=8)
label('sample_mark','SAMPLE',(.032,-.0992,.080),.0035,WHITE)
label('reference_mark','REFERENCE',(.064,-.0992,.061),.0028,WHITE)
cylinder('purge_hex',.006,.004,(.030,-.100,.018),STEEL,'purge_connector','Y',n=6)
o=cylinder('purge_collet',.004,.008,(.030,-.105,.018),STEEL,'purge_connector','Y');bore(o,.002,.018,(.030,-.105,.018),'Y')
box('brand_plate',(.063,.0008,.017),(-.042,-.099,.018),WHITE,'identification_legend',.0005)
label('brand','PIKE',(-.050,-.0995,.021),.009,BLACK);label('model','IntegratIR',(-.029,-.0995,.012),.0037,BLUE)
for x in [-.083,.083]:
 for z in [.008,.036,.093]:cylinder('front_screw_'+str(x)+'_'+str(z),.0018,.001,(x,-.099,z),STEEL,'fastener','Y')
for y in [-.087,.087]:
 for x in [-.083,.083]:cylinder('top_screw_'+str(x)+'_'+str(y),.0018,.0007,(x,y,.1025),STEEL)
# A source-described alignment pin, with selected size and position.
cylinder('bottom_alignment_pin',.0025,.005,(0,.020,-.0025),STEEL,'alignment_pin')
module=list(parts)
# Independently handled reference, cap and optional sealed window plate.
reference_origin=(.145,-.060,.004)
reference.append(cylinder('gold_reference_holder',.026,.027,(.145,-.060,.0175),BLACK,'reference_holder'))
reference.append(cylinder('gold_reference_shoulder',.023,.006,(.145,-.060,.034),BLACK,'reference_holder'))
reference.append(cylinder('diffuse_gold_reference_face',.009,.0005,(.145,-.060,.03725),GOLD,'reference_surface',n=96))
cap_origin=(.210,-.060,.004)
o=cylinder('reference_protective_cap',.028,.024,(.210,-.060,.016),BLACK,'reference_cap',n=96);bore(o,.0263,.026,(.210,-.060,.020));cap.append(o)
o=box('optional_sample_plate',(.052,.052,.002),(.150,.050,.006),GOLD,'optional_sample_plate',.0005);bore(o,.009,.010,(.150,.050,.006));plate.append(o)
plate.append(cylinder('optional_ZnSe_window',.009,.002,(.150,.050,.006),WINDOW,'optional_optical_window',n=96))
cfg=dict(model='PIKE IntegratIR legacy DLaTGS 048-4000',units='m',axes='+Z up; -Y selector/purge front',manufacturer_CAD=False,contact_qualified=False,
 source_sphere_diameter_m=.0762,source_sample_port_diameter_m=.018,selected_main_envelope_m=[W,D,HEIGHT],envelope_is_inferred=True,
 module_parts=[o.name for o in module],reference_parts=[o.name for o in reference],cap_parts=[o.name for o in cap],optional_plate_parts=[o.name for o in plate],
 interfaces=[dict(id='sample_port',kind='sample_support',center_m=list(PORT),normal=[0,0,1],diameter_m=.018,source='DTGS_MANUAL_2012 p. 1',qualified=False),
 dict(id='selector',kind='rotary_selector',center_m=[.032,-.109,.061],axis=[0,-1,0],states=['SAMPLE','REFERENCE'],selected_angles_rad=[0,math.pi/2],dimensions_inferred=True,qualified=False),
 dict(id='purge',kind='purge_connector',center_m=[.030,-.109,.018],axis=[0,-1,0],selected_bore_diameter_m=.004,dimensions_inferred=True,qualified=False),
 dict(id='detector',kind='unresolved_detector_connector',center_m=[-.035,.077,.170],normal=[0,0,1],contact_count=None,pinout=None,mating_qualified=False),
 dict(id='alignment_pin',kind='alignment_pin',center_m=[0,.020,-.0025],axis=[0,0,-1],selected_diameter_m=.005,dimensions_inferred=True,qualified=False),
 dict(id='gold_reference',kind='reference_standard',origin_m=list(reference_origin),surface_center_m=[.145,-.060,.0375],part_number='048-3000',dimensions_inferred=True,qualified=False),
 dict(id='protective_cap',kind='removable_cap',origin_m=list(cap_origin),selected_inside_diameter_m=.0526,dimensions_inferred=True,qualified=False)],
 exclusions=['Later gold-front 12-degree/MCT housing and liquid-nitrogen Dewar','Optical response and electronic function','Detector connector pinout and verified cable compatibility'])
bpy.context.view_layer.update();(HERE/'interfaces.json').write_text(json.dumps(cfg,indent=2)+'\n');(HERE/'parts.json').write_text(json.dumps([dict(id=o.name,role=o['role'],dimensions_m=list(o.dimensions),geometry_basis=o['geometry_basis']) for o in parts],indent=2)+'\n')
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.view_layers[0].cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.18,.23,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5;scene.view_settings.view_transform='Filmic';scene.view_settings.exposure=-2
for n,pos,power,size in [('key',(.4,-.6,.8),100,.7),('fill',(-.5,-.1,.5),60,.5),('rim',(.4,.5,.6),60,.5)]:
 d=bpy.data.lights.new(n,'AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(n,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.07))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('camera');camera=bpy.data.objects.new('camera',d);scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=.42;camera.location=(.4,-.6,.45);camera.rotation_euler=(Vector((.04,0,.06))-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'geometry/pike_integratir_dtgs.blend'))
for o in parts:
 if o.type=='FONT':
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
root.select_set(True);bpy.ops.export_scene.gltf(filepath=str(HERE/'geometry/pike_integratir_dtgs.glb'),export_format='GLB',export_selected=True,export_apply=True,export_extras=True)
for view,pos,target,scale in [('front',(.4,-.6,.45),(.05,0,.06),.43),('rear',(-.4,.6,.45),(.03,0,.07),.40),('sample_port',(.20,-.30,.50),(.035,-.01,.095),.19),('reference',(.40,-.4,.35),(.170,-.03,.025),.22)]:
 camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale;scene.render.filepath=str(HERE/'evidence'/f'{view}.png');bpy.ops.render.render(write_still=True)
receipt=dict(builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),sources_sha256=hashlib.sha256((HERE/'sources.json').read_bytes()).hexdigest(),parts=len(parts),blender_version=bpy.app.version_string,manufacturer_CAD=False,artifacts_sha256={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE/'geometry').glob('*'))})
(HERE/'build_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('PIKE DTGS ASSET',len(parts),'parts',flush=True)
