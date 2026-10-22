"""Original Cary 5000 instrument and legacy extended-compartment reconstruction."""
import bpy, bmesh, math, json, hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
for n in ['geometry','evidence']:(HERE/n).mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
bpy.context.preferences.filepaths.save_version=0
root=bpy.data.objects.new('CARY_5000_WITH_LEGACY_EXTENSION',None);scene.collection.objects.link(root)
parts=[];interfaces=[];font=bpy.data.fonts.load('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf');font.pack()
def mat(name,color,metal=0,rough=.45):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
CASE=mat('warm_instrument_white',(.72,.72,.67));BASE=mat('dark_gray_base',(.13,.17,.19));DARK=mat('dark_purge_bay',(.025,.035,.038));BLUE=mat('blue_panel_print',(.06,.19,.38));RED=mat('red_brand',(.65,.018,.018));STEEL=mat('brushed_steel',(.5,.54,.56),.85,.3);INK=mat('dark_legends',(.025,.03,.04));GREEN=mat('unpowered_status_lenses',(.08,.28,.18))
def finish(o,name,material,role):
 o.name=name;o.parent=root;o.data.materials.append(material);o['part_id']=name;o['role']=role
 o['geometry_basis']='Agilent Cary photographs and legacy extension manual; local dimensions inferred'
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
WHITE=mat('Cary_white_enclosure',(.78,.80,.81),0,.36)
BLACK=mat('Cary_graphite_sample_access',(.075,.085,.092),.15,.4)
W=1.020;D=.710;H=.380;CX=.185;FLOOR=.140
main=[];lid=[];front=[];extension_base=[];extension_cover=[]
box('instrument_plinth',(W,D,.030),(0,0,.015),BLACK,'support',.004)
box('lower_instrument_housing',(W,D,.100),(0,0,.080),WHITE,'housing',.006)
# The distinctive broad left white housing and narrower right section leave
# a real sample-access corridor. The local contour follows product photos.
yz=[(-.355,.130),(-.355,.280),(-.332,.319),(-.285,.359),(-.210,.380),(.325,.380),(.355,.350),(.355,.130)]
for name,lo,hi in [('left',-.510,CX-.099),('right',CX+.099,.510)]:profile(name+'_optics_housing',lo,hi,yz,WHITE,'housing',.005)
rear=box('rear_sample_housing',(.198,.205,.226),(CX,.2525,.243),WHITE,'housing',.001)
# The documented rearward sliding lid needs a physical receiving pocket.
# This local 1 mm clearance is an inferred mechanical reconstruction.
box('rear_lid_pocket_roof',(.198,.205,.013),(CX,.2525,.3695),WHITE,'housing',.001)
for side in [-1,1]:box('rear_lid_pocket_side_'+str(side),(.004,.120,.007),(CX+side*.097,.210,.3595),WHITE,'housing')
box('rear_lid_pocket_end',(.198,.085,.007),(CX,.3125,.3595),WHITE,'housing')
for x in [CX-.079,CX+.079]:box('sample_bay_side_'+str(x),(.004,.500,.212),(x,-.100,FLOOR+.106),BLACK,'sample_bay_wall',.0005)
box('removable_sample_floor',(.154,.500,.004),(CX,-.100,FLOOR-.002),BLACK,'sample_floor',.0005)
# Open beam windows are separated from internal optical context.
for x in [CX-.080,CX+.080]:
 wall=next(o for o in parts if o.name=='sample_bay_side_'+str(CX+(-.079 if x<CX else .079)))
 cut(wall,(.012,.028,.032),(x,-.075,.225));box('sample_beam_window_'+str(x),(.001,.025,.029),(x+(-.003 if x<CX else .003),-.075,.225),DARK,'optical_window')
# Floor retention: two rear feet receivers and the sliding front lock lever.
for x in [CX-.052,CX+.052]:
 box('lockdown_rear_ledge_'+str(x),(.017,.026,.008),(x,.105,FLOOR+.004),STEEL,'accessory_receiver',.0006)
post=cylinder('lockdown_front_post',.008,.010,(CX,-.280,FLOOR+.005),STEEL,'accessory_receiver');bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.0032,depth=.020,location=(CX,-.280,FLOOR+.005));c=bpy.context.object;m=post.modifiers.new('open_pin_receiver','BOOLEAN');m.operation='DIFFERENCE';m.object=c;bpy.context.view_layer.objects.active=post;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True)
box('lockdown_front_lever',(.060,.012,.006),(CX-.012,-.310,FLOOR+.012),BLACK,'lock_lever',.001)
# Main lid is a sliding top, not a hinge. A recessed pull is open geometry.
lid.append(box('sample_sliding_lid',(.188,.302,.005),(CX,-.190,.3595),BLACK,'sliding_lid',.001))
pull=box('sample_lid_pull',(.090,.047,.016),(CX,-.275,.370),BLACK,'lid_pull',.004);cut(pull,(.066,.024,.024),(CX,-.272,.376));lid.append(pull)
for x in [CX-.095,CX+.095]:box('sample_lid_track_'+str(x),(.004,.540,.006),(x,-.080,.353),BLACK,'slide_track',.0006)
# Standard front wall can be removed for the extended sample compartment.
front_yz=[(-.355,.035),(-.363,.070),(-.365,.210),(-.351,.315),(-.337,.354),(-.331,.354),(-.345,.313),(-.359,.210),(-.357,.070),(-.349,.035)]
front.append(profile('standard_front_panel',CX-.094,CX+.094,front_yz,BLACK,'removable_front_wall',.001))
for z in [.090,.225]:front.append(box('standard_front_seam_'+str(z),(.184,.001,.001),(CX,-.3655,z),DARK,'front_wall_detail'))
# Keyhole sockets used by the separately staged extension base.
for x in [CX-.055,CX+.055]:
 bracket=box('extension_keyhole_bracket_'+str(x),(.020,.003,.027),(x,-.354,.150),STEEL,'extension_mount',.0005)
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.0042,depth=.012,location=(x,-.354,.156),rotation=(math.pi/2,0,0));c=bpy.context.object;m=bracket.modifiers.new('open_keyhole_head','BOOLEAN');m.operation='DIFFERENCE';m.object=c;bpy.context.view_layer.objects.active=bracket;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True)
 cut(bracket,(.0045,.010,.012),(x,-.354,.147))
# Front source controls and identity follow the product photo proportions.
box('front_power_recess',(.064,.003,.033),(-.365,-.356,.069),BLACK,'control_recess',.003)
for i,x in enumerate([-.380,-.352]):
 box('power_key_'+str(i),(.018,.006,.022),(x,-.360,.069),BLACK,'power_control',.0015);label('power_symbol_'+str(i),['I','O'][i],(x,-.3635,.069),.010,CASE)
box('front_status_window',(.060,.0015,.026),(-.095,-.356,.065),WHITE,'status_window',.002)
label('model','Cary 5000',(-.343,-.356,.247),.015,BLUE);label('brand','Agilent Technologies',(-.343,-.356,.232),.007,INK)
for side in [-1,1]:
 for i in range(24):
  y=.025+i*.011;box('side_vent_'+str(side)+'_'+str(i),(.001,.004,.033),(side*.5105,y,.160),DARK,'recessed_vent')
for y in [.10,.19]:
 cylinder('rear_purge_barb_'+str(y),.004,.018,(-.30+y,.363,.105),STEEL,'purge_fitting','Y')
box('rear_power_envelope',(.040,.005,.027),(.34,.357,.065),BLACK,'unqualified_service_port',.002)
main=list(parts)
# Legacy extension is displayed separately, ready for installation. Its
# exact source internal dimensions are preserved; local mount sizes inferred.
EX=-.670;EY=-.030;EZ=.010;ex_origin=Vector((EX,EY,EZ))
def exbox(name,size,p,material=BLACK,role='extension_base',radius=0):return box(name,size,ex_origin+Vector(p),material,role,radius)
base=exbox('extension_base_plate',(.170,.180,.006),(0,0,.003),BLACK,'extension_base',.001);extension_base.append(base)
# Its source 170 mm internal depth lies between the front inner face and the
# instrument mating plane. Base and cover are independently removable.
for x in [-.083,.083]:extension_base.append(exbox('extension_base_rail_'+str(x),(.004,.180,.012),(x,0,.012),BLACK,'extension_base',.0005))
for x in [-.055,.055]:
 extension_base.append(cylinder('extension_mount_shank_'+str(x),.002,.009,ex_origin+Vector((x,.091,.014)),STEEL,'keyhole_pin','Y'))
 extension_base.append(cylinder('extension_mount_head_'+str(x),.004,.002,ex_origin+Vector((x,.096,.014)),STEEL,'keyhole_pin','Y'))
extension_base.append(cylinder('extension_hinge_bar',.003,.154,ex_origin+Vector((0,-.080,.011)),STEEL,'hinge_bar','X'))
for x in [-.050,.050]:
 o=cylinder('extension_hose_barb_'+str(x),.004,.014,ex_origin+Vector((x,-.095,.015)),STEEL,'hose_barb','Y');bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.0025,depth=.025,location=ex_origin+Vector((x,-.095,.015)),rotation=(math.pi/2,0,0));c=bpy.context.object;m=o.modifiers.new('open_hose_passage','BOOLEAN');m.operation='DIFFERENCE';m.object=c;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True);extension_base.append(o)
# Source internal 154 mm width, 212 mm height; 170 mm depth to mating plane.
for x in [-.079,.079]:extension_cover.append(exbox('extension_cover_side_'+str(x),(.004,.174,.212),(x,-.003,.112),BLACK,'extension_cover',.0005))
extension_cover.append(exbox('extension_cover_front',(.158,.004,.212),(0,-.088,.112),BLACK,'extension_cover',.0005))
extension_cover.append(exbox('extension_cover_roof',(.162,.174,.004),(0,-.003,.220),BLACK,'extension_cover',.001))
for x in [-.037,.037]:extension_cover.append(exbox('extension_pull_post_'+str(x),(.008,.008,.008),(x,-.008,.226),BLACK,'extension_handle',.001))
extension_cover.append(cylinder('extension_pull_bar',.004,.074,ex_origin+Vector((0,-.008,.230)),BLACK,'extension_handle','X'))
for x in [-.063,.063]:
 extension_cover.append(exbox('extension_front_hook_'+str(x),(.007,.009,.004),(x,.088,.198),STEEL,'extension_hook',.0004))
 extension_cover.append(exbox('extension_hinge_hook_'+str(x),(.006,.011,.004),(x,-.082,.017),STEEL,'extension_hook',.0003))
cfg=dict(model='Agilent Cary 5000 with legacy 0010079800 extension',units='m',axes='+Z up; -Y instrument front',manufacturer_CAD=False,contact_qualified=False,source_envelope_m=[W,D,H],source_envelope_reference='Main housing envelope; small source-photo control, fitting and front-panel projections are separately inferred.',source_instrument_mass_kg=91.,
 main_parts=[o.name for o in main],sliding_lid_parts=[o.name for o in lid],front_panel_parts=[o.name for o in front],extension_base_parts=[o.name for o in extension_base],extension_cover_parts=[o.name for o in extension_cover],cover_parts=[o.name for o in lid+front+extension_cover],
 selected_bare_bay=dict(center_xy_m=[CX,-.100],floor_z_m=FLOOR,dimensions_m=[.154,.500,.212],dimensions_are_inferred=True),
 extension=dict(part_number='0010079800',presentation_origin_m=list(ex_origin),source_internal_dimensions_m=[.154,.170,.212],source_added_depth_m=.180,selected_installed_origin_m=[CX,-.440,FLOOR-.006]),
 interfaces=[dict(id='sample_lid',kind='slide',axis=[0,1,0],center_m=[CX,-.275,.370],selected_travel_m=.305,dimensions_inferred=True,qualified=False),
 dict(id='front_panel',kind='removable_wall',center_m=[CX,-.360,.195],selected_removal_axis=[0,-1,0],dimensions_inferred=True,qualified=False),
 dict(id='extension_base',kind='keyhole_mount',center_m=list(ex_origin),source='LEGACY_EXTENSION pp.3-4',dimensions_inferred=True,qualified=False),
 dict(id='extension_cover',kind='lift_slide_detachable_hinge',center_m=list(ex_origin+Vector((0,-.008,.230))),selected_hinge_origin_m=list(ex_origin+Vector((0,-.080,.011))),selected_hook_lift_m=.006,source='LEGACY_EXTENSION p.5',dimensions_inferred=True,qualified=False),
 dict(id='lockdown',kind='slide_lock',center_m=[CX-.012,-.310,FLOOR+.012],axis=[-1,0,0],selected_travel_m=.024,dimensions_inferred=True,qualified=False),
 dict(id='power',kind='push_control',center_m=[-.380,-.363,.069],axis=[0,1,0],dimensions_inferred=True,qualified=False)],
 exclusions=['Internal and external DRA modules are separate assets','Optical and electrical response','Measured hook/lock geometry and physical mounting qualification','Whole 91 kg instrument transport'])
for o in parts:
 if o.type=='MESH':
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
  bm.to_mesh(o.data);bm.free();o.data.update()
bpy.context.view_layer.update();(HERE/'interfaces.json').write_text(json.dumps(cfg,indent=2)+'\n');(HERE/'parts.json').write_text(json.dumps([dict(id=o.name,role=o['role'],dimensions_m=list(o.dimensions),geometry_basis=o['geometry_basis']) for o in parts],indent=2)+'\n')
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.view_layers[0].cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.18,.23,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5;scene.view_settings.view_transform='Filmic';scene.view_settings.exposure=-.6
for n,pos,power,size in [('key',(1,-2,3),500,2),('fill',(-2,-1,1.8),300,1.6),('rim',(1,2,2),300,1.6)]:
 d=bpy.data.lights.new(n,'AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(n,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.2))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('camera');camera=bpy.data.objects.new('camera',d);scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=1.6;camera.location=(1.3,-2,.95);camera.rotation_euler=(Vector((-.1,0,.15))-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'geometry/cary_5000.blend'))
for o in parts:
 if o.type=='FONT':
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
root.select_set(True);bpy.ops.export_scene.gltf(filepath=str(HERE/'geometry/cary_5000.glb'),export_format='GLB',export_selected=True,export_apply=True,export_extras=True)
for view,pos,target,scale in [('front',(1.3,-2,.95),(-.10,0,.15),1.55),('rear',(-1.3,2,1.1),(-.10,0,.15),1.55),('sample_bay',(.9,-1.2,1.3),(CX,-.11,.23),.65),('extension',(-1.15,-.8,.65),(EX,EY,.115),.43)]:
 for o in lid+front:o.hide_render=view=='sample_bay'
 for o in extension_cover:o.hide_render=view=='sample_bay'
 for o in main:
  if view=='extension':o.hide_render=True
 camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale;scene.render.filepath=str(HERE/'evidence'/f'{view}.png');bpy.ops.render.render(write_still=True)
receipt=dict(builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),sources_sha256=hashlib.sha256((HERE/'sources.json').read_bytes()).hexdigest(),parts=len(parts),blender_version=bpy.app.version_string,manufacturer_CAD=False,artifacts_sha256={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE/'geometry').glob('*'))})
(HERE/'build_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('CARY 5000 ASSET',len(parts),'parts',flush=True)
