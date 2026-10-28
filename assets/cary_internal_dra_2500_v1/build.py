"""Original reconstruction of the legacy Cary internal DRA 2500."""
import bpy, math, json, hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
for n in ['geometry','evidence']:(HERE/n).mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
bpy.context.preferences.filepaths.save_version=0
root=bpy.data.objects.new('CARY_INTERNAL_DRA_2500_0010081100',None);scene.collection.objects.link(root)
parts=[];interfaces=[];font=bpy.data.fonts.load('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf');font.pack()
def mat(name,color,metal=0,rough=.45):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
CASE=mat('warm_instrument_white',(.72,.72,.67));BASE=mat('dark_gray_base',(.13,.17,.19));DARK=mat('dark_purge_bay',(.025,.035,.038));BLUE=mat('blue_panel_print',(.06,.19,.38));RED=mat('red_brand',(.65,.018,.018));STEEL=mat('brushed_steel',(.5,.54,.56),.85,.3);INK=mat('dark_legends',(.025,.03,.04));GREEN=mat('unpowered_status_lenses',(.08,.28,.18))
def finish(o,name,material,role):
 o.name=name;o.parent=root;o.data.materials.append(material);o['part_id']=name;o['role']=role
 o['geometry_basis']='Varian Internal DRA manual: source envelope and named interfaces; local dimensions inferred'
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
BLACK=mat('black_anodized_optics',(.035,.045,.053),.35,.38)
PTFE=mat('diffuse_white_PTFE',(.92,.925,.90),0,.9)
MIRROR=mat('optical_mirror',(.72,.78,.80),.98,.08)
W=.140;D=.340;H=.200;C=Vector((0,-.058,.084))
def subtract(o,c):
 m=o.modifiers.new('open_geometry','BOOLEAN');m.operation='DIFFERENCE';m.object=c;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True)
def bore(o,r,h,pos,axis='Z'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=r,depth=h,location=pos,rotation=(math.pi/2,0,0) if axis=='Y' else (0,math.pi/2,0) if axis=='X' else (0,0,0));subtract(o,bpy.context.object)
def shell(name,inner,outer,material):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=96,ring_count=64,radius=outer,location=C);o=finish(bpy.context.object,name,material,'sphere_shell')
 bpy.ops.mesh.primitive_uv_sphere_add(segments=96,ring_count=64,radius=inner,location=C);subtract(o,bpy.context.object);return o
def clip_half(o,front):
 # The cap owns the anterior spherical segment, without a duplicate shell.
 cut(o,(.20,.20,.20),(0,-.001 if front else -.201,.084))
def port_cuts(o):
 # Manual pp. 10-11: 16 mm %R, 19 x 17 mm %T, 11 x 13 mm reference.
 bore(o,.008,.040,(0,-.119,.084),'Y')
 cut(o,(.019,.030,.017),(0,-.002,.084))
 cut(o,(.030,.011,.013),(-.056,-.058,.084))
 bore(o,.0055,.040,(-.022,-.055,.137))
 # The manual specifies a 30 x 14 mm oval. A stadium profile is a selected
 # local reconstruction; overlapping circular/rectangular cutters avoid
 # the open boolean boundary produced by a scaled cylinder in Blender 2.82.
 cut(o,(.016,.014,.040),(.018,-.055,.137))
 for x in [.010,.026]:bore(o,.007,.040,(x,-.055,.137))
module=[];cap=[];reference=[];clamp=[];optics_cover=[]
box('module_base',(W,D,.006),(0,0,.009),BLACK,'base',.001)
for side in [-1,1]:
 box('rear_lockdown_foot_'+str(side),(.012,.018,.006),(side*.052,.145,.003),STEEL,'lockdown_foot',.0005)
cylinder('front_lockdown_pin',.003,.008,(0,-.150,.004),STEEL,'lockdown_pin')
case=box('sphere_housing',(.128,.132,.140),(0,-.045,.076),BLACK,'housing',.0015)
bore(case,.0615,.150,(0,-.045,.084),'Y')
cut(case,(.020,.011,.013),(-.061,-.058,.084))
box('detector_housing',(.128,.132,.054),(0,-.045,.173),BLACK,'detector_housing',.001)
# Housing seams, retained side screws and two cover screws are named parts.
for side in [-1,1]:
 for y in [-.096,.006]:
  for z in [.028,.128]:cylinder('sphere_case_screw_'+str(side)+'_'+str(y)+'_'+str(z),.0016,.001,(side*.0645,y,z),STEEL,'fastener','X')
for x in [-.049,.049]:cylinder('detector_cover_screw_'+str(x),.002,.001,(x,-.04,.1995),STEEL)
# The front optical cap is independently removable and clocked S/D. Robust
# solid booleans run in prepare_sphere.py; Blender 2.82 left open boundaries
# around the intersecting curved wall and PMT port in the first candidate.
prepared=json.loads((HERE/'geometry/sphere_parts.json').read_text())
if prepared['generator_sha256']!=hashlib.sha256((HERE/'prepare_sphere.py').read_bytes()).hexdigest():raise ValueError('Regenerate sphere parts after changing the mesh generator')
for name,record in prepared['meshes'].items():
 m=bpy.data.meshes.new(name);m.from_pydata(record['vertices'],[],record['faces']);m.update();o=bpy.data.objects.new(name,m);scene.collection.objects.link(o);finish(o,name,PTFE if '_ptfe_' in name else BLACK,'sphere_shell')
 if name.endswith('_cap'):cap.append(o)
o=cylinder('sphere_cap_carrier',.058,.004,(0,-.120,.084),BLACK,'removable_cap','Y',n=96);bore(o,.008,.050,(0,-.120,.084),'Y');cap.append(o)
for i in range(48):
 a=2*math.pi*i/48;cap.append(cylinder('cap_grip_rib_'+str(i),.0007,.006,(.058*math.cos(a),-.119,.084+.058*math.sin(a)),BLACK,'cap_grip','Y',n=8))
for mark,z in [('S',.130),('D',.038)]:cap.append(label('cap_mark_'+mark,mark,(0,-.1222,z),.007,CASE))
cap.append(cylinder('cap_shipping_screw',.0025,.004,(.032,-.123,.047),STEEL,'shipping_fastener','Y',n=6))
# Reference beam attenuation clips on the left side remain exposed.
for y in [-.068,-.048]:box('attenuator_clip_'+str(y),(.001,.004,.022),(-.065,y,.084),STEEL,'attenuator_clip',.0002)
# Rear light cover is separate from the detector enclosure. The service
# cover does not receive routine-manipulation credit from this asset.
optics_cover.append(box('optics_cover_top',(.128,.140,.002),(0,.095,.151),BLACK,'optics_cover',.0004))
for x in [-.063,.063]:optics_cover.append(box('optics_cover_side_'+str(x),(.002,.140,.142),(x,.095,.079),BLACK,'optics_cover',.0004))
optics_cover.append(box('optics_cover_rear',(.124,.002,.142),(0,.164,.079),BLACK,'optics_cover',.0004))
for x in [-.040,.040]:
 cylinder('optics_cover_post_'+str(x),.003,.140,(x,.095,.078),STEEL,'optics_cover_mount')
 optics_cover.append(cylinder('optics_cover_screw_'+str(x),.0025,.001,(x,.095,.1525),STEEL))
# Photo-described top lift grip, with selected dimensions and clear opening.
for y in [.069,.121]:box('optics_handle_mount_'+str(y),(.010,.008,.014),(0,y,.159),BLACK,'handling_grip',.001)
box('optics_handle_bar',(.010,.060,.007),(0,.095,.1695),BLACK,'handling_grip',.0015)
# Mirrors/lens are visible when inspecting the separately removable cover.
for i,(x,y) in enumerate([(-.035,.110),(.025,.044)]):
 box('mirror_mount_'+str(i),(.032,.009,.049),(x,y,.055),BLACK,'optical_mount',.001)
 box('mirror_face_'+str(i),(.025,.001,.031),(x,y-.005,.058),MIRROR,'optical_surface',.0002)
 for dx in [-.018,.018]:cylinder('mirror_adjust_'+str(i)+'_'+str(dx),.002,.004,(x+dx,y-.003,.052),STEEL,'alignment_fastener','Y')
lens=box('transmission_lens_frame',(.030,.003,.032),(0,.009,.084),BLACK,'transmission_interface',.0005);cut(lens,(.019,.010,.017),(0,.009,.084))
# Special D-range connector: source identity only, no fabricated pin map.
box('detector_cable_exit',(.013,.009,.012),(.042,.023,.060),BLACK,'cable_exit',.002)
# A short retained visual cable segment identifies the exit, not a complete cable task.
curve=bpy.data.curves.new('retained_detector_cable','CURVE');curve.dimensions='3D';curve.bevel_depth=.0025;curve.bevel_resolution=4
sp=curve.splines.new('BEZIER');sp.bezier_points.add(3)
for p,xyz in zip(sp.bezier_points,[(.042,.023,.060),(.050,.060,.027),(.045,.120,.018),(.038,.145,.026)]):p.co=xyz;p.handle_left_type=p.handle_right_type='AUTO'
o=bpy.data.objects.new('retained_detector_cable',curve);scene.collection.objects.link(o);finish(o,o.name,BLACK,'retained_cable_context')
box('special_detector_plug_envelope',(.040,.018,.014),(.030,.144,.029),BLACK,'unresolved_connector',.002)
# Physical sample-clamp elements are separate from the removable optical cap.
clamp.append(cylinder('sample_clamp_post',.003,.040,(.039,-.140,.084),STEEL,'sample_clamp_post','Y'))
clamp.append(box('sample_clamp_slider',(.011,.010,.013),(.039,-.154,.084),STEEL,'sample_clamp_slider',.001))
clamp.append(box('sample_clamp_arm',(.039,.002,.007),(.0205,-.159,.084),STEEL,'sample_clamp_arm',.0005))
clamp.append(cylinder('sample_clamp_contact',.004,.004,(.001,-.157,.084),DARK,'sample_clamp_pad','Y'))
# Compression spring around the carrier post, explicitly inferred geometry.
verts=[];faces=[]
for i in range(193):
 a=i*2*math.pi*8/192
 for j in range(8):
  b=j*2*math.pi/8;r=.004+.00045*math.cos(b);verts.append((.039+r*math.cos(a),-.130-i*.020/192+.00045*math.sin(b),.084+r*math.sin(a)))
for i in range(192):
 for j in range(8):k=i*8+j;l=i*8+(j+1)%8;faces.append((k,l,l+8,k+8))
faces.extend([tuple(range(7,-1,-1)),tuple(range(192*8,193*8))]);m=bpy.data.meshes.new('sample_clamp_spring');m.from_pydata(verts,[],faces);m.update();o=bpy.data.objects.new('sample_clamp_spring',m);scene.collection.objects.link(o);clamp.append(finish(o,o.name,STEEL,'sample_clamp_spring'))
module=[o for o in parts if o not in cap and o not in clamp]
# Source 1 3/4 inch PTFE plate, presented separately for handling inspection.
reference.append(cylinder('large_reference_holder',.025,.008,(.125,-.075,.034),BLACK,'reference_holder','Y'))
reference.append(cylinder('large_PTFE_reference',.022225,.006,(.125,-.082,.034),PTFE,'reference_surface','Y',n=96))
label('reference_identification','PTFE',(.125,-.086,.010),.0035,CASE)
# Discrete legend on the service cover, not a fabricated vendor product label.
label('asset_identity','INTERNAL DRA 2500',(0,.075,.1521),.005,CASE,top=True)
cfg=dict(model='Cary internal DRA 2500 (legacy 0010081100)',units='m',axes='+Z up; -Y reflectance cap',manufacturer_CAD=False,contact_qualified=False,
 source_envelope_m=[W,D,H],source_mass_kg=5.,source_sphere_diameter_m=.110,source_PTFE_thickness_m=.004,source_reflectance_port_diameter_m=.016,
 module_parts=[o.name for o in module],cap_parts=[o.name for o in cap],clamp_parts=[o.name for o in clamp],reference_parts=[o.name for o in reference],cover_parts=[o.name for o in optics_cover],
 interfaces=[dict(id='reflectance',kind='sample_port',center_m=[0,-.122,.084],normal=[0,-1,0],diameter_m=.016,source='INTERNAL_DRA_MANUAL pp.10-11',qualified=False),
 dict(id='transmission',kind='sample_port',center_m=[0,.009,.084],normal=[0,1,0],aperture_m=[.019,.017],source='INTERNAL_DRA_MANUAL p.10',qualified=False),
 dict(id='reference_beam',kind='attenuator_port',center_m=[-.064,-.058,.084],normal=[-1,0,0],aperture_m=[.011,.013],qualified=False),
 dict(id='cap',kind='removable_clocked_cap',center_m=[0,-.120,.084],axis=[0,-1,0],states=['S','D'],selected_clock_angles_rad=[0,math.pi],source_sample_plane_angles_deg=[10/3,0],dimensions_inferred=True,qualified=False),
 dict(id='sample_clamp',kind='spring_clamp',center_m=[.039,-.154,.084],axis=[0,-1,0],selected_travel_m=.020,dimensions_inferred=True,qualified=False),
 dict(id='reference',kind='reference_standard',center_m=[.125,-.085,.034],diameter_m=.04445,PTFE_depth_m=.006,qualified=False),
 dict(id='lockdown',kind='base_mount',center_m=[0,-.150,.004],rear_feet_m=[[-.052,.145,.003],[.052,.145,.003]],dimensions_inferred=True,qualified=False),
 dict(id='detector_connector',kind='unresolved_special_D_range',center_m=[.030,.144,.029],source_description='15-pin D-range with two high-voltage pins',contact_layout=None,pinout=None,mating_qualified=False)],
 handling_requirements=dict(source_payload_kg=5.,current_Panda_payload_kg=3.,direct_Panda_lift_allowed=False,required='Adequately rated handler or physically modeled support assistance'),
 exclusions=['Electrical and optical behavior','Service alignment and electronics access qualification','Detector connector pin map and cable mating','Complete lead dynamics','Unassisted 3 kg Panda installation of the 5 kg module'])
bpy.context.view_layer.update();(HERE/'interfaces.json').write_text(json.dumps(cfg,indent=2)+'\n');(HERE/'parts.json').write_text(json.dumps([dict(id=o.name,role=o['role'],dimensions_m=list(o.dimensions),geometry_basis=o['geometry_basis']) for o in parts],indent=2)+'\n')
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.view_layers[0].cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.18,.23,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5;scene.view_settings.view_transform='Filmic';scene.view_settings.exposure=-2
for n,pos,power,size in [('key',(.4,-.6,.8),100,.7),('fill',(-.5,-.1,.5),60,.5),('rim',(.4,.5,.6),60,.5)]:
 d=bpy.data.lights.new(n,'AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(n,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.07))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('camera');camera=bpy.data.objects.new('camera',d);scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=.49;camera.location=(.4,-.6,.45);camera.rotation_euler=(Vector((0,0,.08))-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'geometry/cary_internal_dra_2500.blend'))
for o in parts:
 if o.type in {'FONT','CURVE'}:
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
root.select_set(True);bpy.ops.export_scene.gltf(filepath=str(HERE/'geometry/cary_internal_dra_2500.glb'),export_format='GLB',export_selected=True,export_apply=True,export_extras=True)
for view,pos,target,scale in [('front',(.4,-.6,.45),(.02,0,.08),.46),('rear',(-.4,.6,.45),(0,.03,.08),.45),('cap',(.18,-.55,.25),(.01,-.10,.08),.22),('interior',(.4,-.3,.6),(0,0,.07),.46)]:
 for o in optics_cover:o.hide_render=view=='interior'
 camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale;scene.render.filepath=str(HERE/'evidence'/f'{view}.png');bpy.ops.render.render(write_still=True)
receipt=dict(builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),sources_sha256=hashlib.sha256((HERE/'sources.json').read_bytes()).hexdigest(),parts=len(parts),blender_version=bpy.app.version_string,manufacturer_CAD=False,artifacts_sha256={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE/'geometry').glob('*'))})
(HERE/'build_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('CARY INTERNAL DRA ASSET',len(parts),'parts',flush=True)
