"""Static/kinematic PAIRED_TWO renders. No simulator, physics or robot controller.
G1 uses corrected original XML local transforms, never cached local matrices.
"""
import bpy, math, json, sys, os, xml.etree.ElementTree as ET, hashlib
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
from bpy_extras.object_utils import world_to_camera_view
def external_root(variable):
 value=os.environ.get(variable)
 if not value:
  raise SystemExit('Set '+variable+' to the existing external input directory. See EXTERNAL_INPUTS.md.')
 root=Path(value).expanduser().resolve()
 if not root.is_dir():
  raise SystemExit(variable+' must identify an existing directory. See EXTERNAL_INPUTS.md.')
 return root

OUT=Path(__file__).resolve().parents[1]
for directory in ['raw','frames','qa']:(OUT/directory).mkdir(parents=True,exist_ok=True)
SRC=external_root('THERMO_SCENE')
G1=external_root('G1_ASSETS')
manifest=json.loads((OUT/'frame_manifest.json').read_text());frames=manifest['frames']
layout={s['station_id']:s['center_xy_m'] for s in json.loads((SRC/'station_parts.json').read_text())['stations']}
ONLY=set(int(x) for x in sys.argv[sys.argv.index('--only')+1].split(',')) if '--only' in sys.argv else set()
bpy.ops.wm.open_mainfile(filepath=str(SRC/'assets/thermoelectric_lab_scene.blend'))
scene=bpy.context.scene
assert scene.rigidbody_world is None
original=list(bpy.data.objects)
BASE={o.name:o.matrix_world.copy() for o in original}
MATBASE={o.name:[m for m in o.data.materials] for o in original if o.type=='MESH'}
def mat(name,color,em=0,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.48;p.inputs['Metallic'].default_value=metal
 if em:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=em
 return m
orange=mat('VISUAL_active_target',(1,.22,.03),.3);cyan=mat('VISUAL_lineage_object',(.0,.65,.73),.1);dark=mat('G1_black',(.055,.07,.09),0,.25);silver=mat('G1_metal',(.66,.73,.77),0,.45);blue=mat('VISUAL_route',(.02,.45,.9),.25)

def empty(name):
 o=bpy.data.objects.new(name,None);scene.collection.objects.link(o);return o

def seg(name,p,q,r,ma):
 v=Vector(q)-Vector(p);bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=v.length,location=(Vector(p)+Vector(q))/2);o=bpy.context.object;o.name=name;o.rotation_euler=v.to_track_quat('Z','Y').to_euler();o.data.materials.append(ma);return o

def xmlmat(e):
 pos=Vector([float(v) for v in e.get('pos','0 0 0').split()]);q=Quaternion([float(v) for v in e.get('quat','1 0 0 0').split()]);return Matrix.Translation(pos)@q.to_matrix().to_4x4()
# Pure XML transforms and STL visuals. No MuJoCo model is loaded or stepped.
xml=ET.parse(G1/'g1_with_hands.xml').getroot(); meshes={}
for el in xml.find('asset').findall('mesh'):
 f=G1/'assets'/el.get('file'); key=el.get('name',f.stem)
 bpy.ops.wm.stl_import(filepath=str(f));o=bpy.context.object;meshes[key]=o.data;bpy.data.objects.remove(o,do_unlink=True)
robot=empty('G1_VISUAL_ROOT'); joints={}; links={};robot_meshes=[]
def import_body(el,parent):
 name=el.get('name');o=empty('G1_'+name);o.parent=parent;o.matrix_local=xmlmat(el);links[name]=o
 joint=el.find('joint')
 if joint is not None:
  joints[joint.get('name')]={'obj':o,'base':xmlmat(el),'axis':Vector([float(x) for x in joint.get('axis','0 0 1').split()]),'range':[float(x) for x in joint.get('range','-3.14 3.14').split()], 'q':0.}
 for g in el.findall('geom'):
  if g.get('class')!='visual' or not g.get('mesh'):continue
  ob=bpy.data.objects.new('G1_VISUAL_'+g.get('mesh'),meshes[g.get('mesh')]);scene.collection.objects.link(ob);ob.parent=o;ob.matrix_local=xmlmat(g);ob.data.materials.clear();ob.data.materials.append(dark if g.get('material')=='black' else silver);robot_meshes.append(ob)
 for child in el.findall('body'):import_body(child,o)
import_body(xml.find('worldbody/body'),robot)

def qset(name,q):
 j=joints[name];lo,hi=j['range'];q=min(hi,max(lo,q));j['q']=q;j['obj'].matrix_local=j['base']@Quaternion(j['axis'],q).to_matrix().to_4x4()
def pose(target=None):
 for name,j in joints.items():qset(name,0)
 for side in ['left','right']:
  qset(side+'_shoulder_pitch_joint',-.45);qset(side+'_elbow_joint',1.2)
 bpy.context.view_layer.update()
 # Static numerical posing, not a controller or reachability certification.
 if target is not None:
  for side,sgn in [('left',1),('right',-1)]:
   goal=Vector(target)+robot.matrix_world.to_3x3()@Vector((0,sgn*.095,0))
   eff=links[side+'_wrist_yaw_link']; chain=[side+'_'+s+'_joint' for s in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow','wrist_roll']]
   for _ in range(10):
    for jn in chain[::-1]:
     j=joints[jn];bpy.context.view_layer.update();pivot=j['obj'].matrix_world.translation;ax=(j['obj'].parent.matrix_world@j['base']).to_3x3()@j['axis'];a=eff.matrix_world.translation-pivot;b=goal-pivot;a-=ax*a.dot(ax);b-=ax*b.dot(ax)
     if a.length<1e-6 or b.length<1e-6:continue
     a.normalize();b.normalize();delta=math.atan2(ax.dot(a.cross(b)),a.dot(b));qset(jn,j['q']+delta*.7)
   bpy.context.view_layer.update()

def items(prefix):return [o for o in original if o.name.startswith(prefix)]
def show(group,v=True):
 for o in group:o.hide_render=not v;o.hide_viewport=not v

def move(group,oldcenter,newcenter,yaw=0):
 T=Matrix.Translation(Vector(newcenter))@Matrix.Rotation(yaw,4,'Z')@Matrix.Translation(-Vector(oldcenter))
 for o in group:o.matrix_world=T@BASE[o.name]

def center(group):
 vv=[o.matrix_world@Vector(v) for o in group for v in o.bound_box];return sum(vv,Vector())/len(vv)

def local(st,p):
 d=layout[st];return Vector((d[0]+p[0],d[1]+p[1],p[2]))
instances=json.loads((SRC/'sample_instances.json').read_text())['instances']
instance_groups={s['id']:[bpy.data.objects[k] for k in s['part_ids']] for s in instances}
all_sample_objects=[o for g in instance_groups.values() for o in g]
centers={k:center(g) for k,g in instance_groups.items()}
cart=items('WS_TRANSPORT__'); cart_origin=(10.4,2.,0)
module=instance_groups['T06_MODULE_ASSEMBLY'];module_origin=Vector((4.08,6.2,.957))
vials={c:instance_groups['T01_'+c+'_VIAL'] for c in ['P','N']}
powders={c:instance_groups['T03_'+c+'_POWDER'] for c in ['P','N']}
blanks={c:instance_groups['T04_'+c+'_BLANK'] for c in ['P','N']}
legs={c:instance_groups['T05_'+c+'_LEG'] for c in ['P1','N1','P2','N2']}
legcent={c:center(g) for c,g in legs.items()}
die=items('WS_DIE__die_transfer')+items('WS_DIE__die_sleeve')+items('WS_DIE__lower_punch')+items('WS_DIE__upper_punch')
die_origin=Vector((12.1,6.2,.938))
permanent_hide=items('ROOM__state_warning')+items('WS_DIE__P_powder')+items('WS_MELT__B_empty_vial')+items('WS_PREP__returned_stock')
# Scene labels referring to simultaneous temporal display are replaced by truthful episode labels.
for o in original:
 if o.type=='FONT':
  if o.name=='ROOM__state_warning':o.data.body='ONE PAIRED_TWO STORYBOARD  |  STATIC KEYFRAMES  |  NO PHYSICS'
  if o.name=='ROOM__title':o.data.body='THERMOELECTRIC / EMBODIED TASK VISUALIZATION'
  if o.name.endswith('__header_static'):o.data.body='AUTHORED TASK PROXY / NO PROCESS BACKEND'
  if o.name=='ROOM__optional_legend':o.data.body='OTHER BRANCHES / INACTIVE IN THIS ROUTE'
# Equipment covers below are explicitly authored closed-state markers, not vendor mechanisms.
closed_mat=mat('VISUAL_closed_state_panel',(.035,.14,.20),.0,.1)
closed_markers={}
for st in ['WS_ATMOSPHERE','WS_MILL','WS_SPS','WS_CUT','WS_PEM']:
 bpy.ops.mesh.primitive_cube_add(size=1,location=local(st,(-.2,-.4,1.24)));o=bpy.context.object;o.name='VISUAL_AUTHORED_CLOSED_STATE_'+st;o.dimensions=(1.18,.018,.50);o.data.materials.append(closed_mat);closed_markers[st]=o
# Bright table-edge target cue: explanatory geometry only, no contact constraint.
hand_guides=[]
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=8
scene.render.resolution_x=1240;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-1.10;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
for vl in scene.view_layers:
 if hasattr(vl,'cycles') and hasattr(vl.cycles,'use_denoising'):vl.cycles.use_denoising=False
bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='PAIRED_TWO_CAMERA';cam.data.type='ORTHO';cam.data.clip_start=.002;scene.camera=cam

def setcam(loc,target,scale):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;bpy.context.view_layer.update()
def pixel(p):
 v=world_to_camera_view(scene,cam,Vector(p));return [round(v.x*scene.render.resolution_x,1),round((1-v.y)*scene.render.resolution_y,1)]
def highlight(group):
 for o in group:
  if o.type=='MESH':o.data.materials.clear();o.data.materials.append(orange)
def place_group(group,dest,source=None):
 show(group,True);move(group,source or center(group),dest)
def place_instance(k,dest):
 show(instance_groups[k],True);move(instance_groups[k],centers[k],dest)
def putleg(c,dest):
 show(legs[c],True);move(legs[c],legcent[c],dest)
def putmodule(dest,placed=4,bridges=True):
 show(module,False)
 for o in module:
  n=o.name.replace('WS_MODULE__T06_MODULE_','')
  leg=next((c for c in ['p1','n1','p2','n2'] if n.startswith(c+'_')),None)
  visible=leg is None or ['p1','n1','p2','n2'].index(leg)<placed
  if n.startswith('hot_copper_bridge') and not bridges:visible=False
  o.hide_render=not visible;o.hide_viewport=not visible;o.matrix_world=Matrix.Translation(Vector(dest)-module_origin)@BASE[o.name]
 return Vector(dest)+Vector((0,0,.075))
def reset():
 for o in original:
  o.matrix_world=BASE[o.name].copy();o.hide_render=False;o.hide_viewport=False
  if o.name in MATBASE:o.data.materials.clear();[o.data.materials.append(m) for m in MATBASE[o.name]]
 show(all_sample_objects,False);show(permanent_hide,False)
 for k,g in instance_groups.items():
  if k.startswith('T00_RAW'):show(g,True)
 # Empty P/N vessels are legitimate initial inventory, not processed material.
 # Initial frame conservatively omits downstream jar stage copies as well.
 for o in closed_markers.values():o.hide_render=True;o.hide_viewport=True
 for o in hand_guides:bpy.data.objects.remove(o,do_unlink=True)
 hand_guides.clear()
 # Unrelated routes remain apparatus-only, with no B/segmented/contact samples.
 show(items('WS_PEM__lead_'),False)

def state(f,overview=False):
 reset();st=f['station'];kind=f['visual_kind'];c=f['phase'];n=f['index'];
 if not overview and kind!='reset':
  # Camera cutaway only: omit unrelated foreground stations that block robot feet/hands.
  for sid,xy in layout.items():
   if sid!=st and xy[1]<layout[st][1]-1.6:show(items(sid+'__'),False)
 f['camera_cutaway']='Unrelated foreground-row equipment hidden for interaction readability; complete lab preserved in overview.' if not overview and kind!='reset' else None
 dock=local(st,(0,-1.04,.035));robot.location=dock;robot.rotation_euler.z=math.pi/2;pose()
 cartdest=dock+Vector((1.02,-.20,-.035));move(cart,cart_origin,cartdest)
 target=local(st,(0,-.30,1.04));objpoint=None;targetgroup=[];detail_scale=.7
 traypos=cartdest+Vector((0,0,.78));moddest=local('WS_MODULE',(-.12,-.03,.957));pemdest=local('WS_PEM',(-.25,.015,1.052))
 # During N processing the completed P legs remain two live compartmented items on the cart.
 if c=='N':
  for i,k in enumerate(['P1','P2']):putleg(k,traypos+Vector((-.24+i*.21,-.05,0)))
 if kind=='initial':
  targetgroup=items('WS_STOCK__stock_');target=local(st,(-.33,-.2,1.03));objpoint=target
 elif c in ['P','N']:
  vid='T01_'+c+'_VIAL';pid='T03_'+c+'_POWDER';bid='T04_'+c+'_BLANK';x=-.74 if c=='P' else -.01
  if kind in ['portion','cap']:
   dest=local(st,(x,-.21,1.055));place_instance(vid,dest);targetgroup=vials[c];target=dest;objpoint=dest
   if kind=='portion':
    for o in vials[c]:
     if o.name.endswith('_cap'):o.location+=Vector((.20,0,-.10))
    targetgroup+=items('WS_PREP__scoop_')
  elif kind=='ar':
   dest=local(st,(-.1,-.26,1.13));place_instance(vid,dest);targetgroup=vials[c];target=dest;objpoint=dest
  elif kind in ['mill_seat','mill_run','mill_unload']:
   dest=local(st,(.66,-.03,1.075)) if kind!='mill_unload' else traypos+Vector((.2,0,.08));place_instance(vid,dest);targetgroup=vials[c];target=dest;objpoint=dest
   if kind=='mill_run':
    closed_markers[st].hide_render=False;targetgroup=items('WS_MILL__REUSE_');target=local(st,(.1,-.50,1.1));robot.location+=Vector((0,-.4,0));pose()
  elif kind=='stack':
   dest=local(st,(.58,-.25,1.06));place_instance(pid,dest);targetgroup=die;target=local(st,(-.2,-.12,1.06));objpoint=dest
  elif kind in ['sps_load','sps_release']:
   x=-.56 if c=='P' else .56;target=local(st,(x,-.18,1.04));move(die,die_origin,target-Vector((0,0,.08)));targetgroup=die;objpoint=target
   if kind=='sps_release':
    target=traypos+Vector((0,0,.01));move(die,die_origin,target);objpoint=target
  elif kind=='demold':
   target=local(st,(.53,-.21,1.012));place_instance(bid,target);targetgroup=blanks[c];objpoint=target;detail_scale=.35
  elif kind=='cut':
   target=local(st,(-.23,-.12,1.064));place_instance(bid,target);targetgroup=items('WS_CUT__dimension_card')+items('WS_CUT__dimension_text');objpoint=target;detail_scale=.4
  elif kind=='legs':
   for i,k in enumerate([c+'1',c+'2']):putleg(k,local(st,(.62 if c=='P' else .83,-.15+i*.26,1.025)))
   targetgroup=legs[c+'2'];target=center(targetgroup);objpoint=local(st,(.62 if c=='P' else .83,-.02,1.025));detail_scale=.55
 else:
  if kind in ['module_base','module_leg','module_bridge','module_release']:
   placed=0 if kind=='module_base' else f['leg_index']+1 if kind=='module_leg' else 4
   objpoint=putmodule(moddest,placed,kind in ['module_bridge','module_release']);target=objpoint
   for i,k in enumerate(['P1','N1','P2','N2']):
    if i>=placed:putleg(k,local(st,(.45+(i%2)*.20,-.14+(i//2)*.23,1.025)))
   targetgroup=[o for o in module if not o.hide_render]
   if kind=='module_leg':targetgroup=[o for o in module if '_'+['p1','n1','p2','n2'][f['leg_index']]+'_' in o.name]
   if kind=='module_release':
    objpoint=putmodule(traypos-Vector((0,0,.075)));target=objpoint;targetgroup=module
   detail_scale=.45 if kind=='module_base' else .30
  elif kind in ['pem_mount','pem_wire','pem_seal','boundary','powerdown','pem_unload']:
   objpoint=putmodule(pemdest);target=objpoint;targetgroup=module;detail_scale=.36
   if kind in ['pem_wire','pem_seal','boundary','powerdown']:show(items('WS_PEM__lead_'),True)
   if kind=='pem_wire':targetgroup=items('WS_PEM__task_port_');target=local(st,(.7,-.28,1.12))
   if kind in ['pem_seal','boundary','powerdown']:
    closed_markers[st].hide_render=False;target=local(st,(.7,-.20,1.45));targetgroup=items('WS_PEM__measurement_ui_button_');robot.location=local(st,(.30,-1.43,.035));pose()
   if kind=='pem_unload':
    objpoint=putmodule(traypos-Vector((0,0,.075)));target=objpoint;targetgroup=module;show(items('WS_PEM__lead_'),False)
  elif kind=='data':
   objpoint=putmodule(traypos-Vector((0,0,.075)));targetgroup=items('WS_DATA__keyboard');target=local(st,(0,-.29,.96));detail_scale=.36
  elif kind in ['archive','clean','reset']:
   objpoint=putmodule(local('WS_STORAGE',(-.43,-.06,.965)));target=objpoint;targetgroup=module;detail_scale=.36
   if kind=='clean':targetgroup=items('WS_CLEAN__wipe_proxy');target=center(targetgroup)
 # Hand and target relation is an authored pose with a visible explanation cue.
 if kind not in ['initial','mill_run','pem_seal','boundary','powerdown','reset']:
  robot.location=Vector((target.x,target.y-.58,.035));robot.rotation_euler.z=math.pi/2;bpy.context.view_layer.update();pose(target)
  for side in ['left','right']:
   palm=links[side+'_wrist_yaw_link'].matrix_world.translation
   if (palm-target).length>.12:
    # Short dashed guide, not a tool/constraint/certified contact.
    delta=target-palm
    for i in range(4):hand_guides.append(seg('VISUAL_hand_target_guide',palm+delta*(i/4),palm+delta*(i/4+.10),.0025,cyan))
 highlight(targetgroup)
 # Keep module material colors (P coral, N blue) rather than orange recoloring.
 if c=='PAIR':
  for o in module:
   if o.name in MATBASE:o.data.materials.clear();[o.data.materials.append(m) for m in MATBASE[o.name]]
 bpy.context.view_layer.update()
 if overview or kind=='reset':setcam((23,-18,22),(7.6,5.8,.4),20.6)
 else:
  focus=local(st,(0,-.27,.96))
  if kind in ['mill_unload','sps_release','module_release','pem_unload','mill_run','pem_seal','boundary','powerdown','pem_wire']:
   focus=(focus+Vector((robot.location.x,robot.location.y,.88)))/2
  setcam(focus+Vector((3.25,-4.1,2.65)),focus,4.05 if kind in ['mill_unload','sps_release','module_release','pem_unload','mill_run','pem_seal','boundary','powerdown','pem_wire'] else 3.85)
 f['camera']={'location':list(cam.location),'ortho_scale':cam.data.ortho_scale,'target_station':st}
 robot_vertices=[o.matrix_world@Vector(v) for o in robot_meshes for v in o.bound_box]
 f['robot_bounds_world_m']={axis:[min(v[i] for v in robot_vertices),max(v[i] for v in robot_vertices)] for i,axis in enumerate(['x','y','z'])}
 robot_pixels=[pixel(v) for v in robot_vertices]
 f['robot_projected_bounds_px']={'x':[min(v[0] for v in robot_pixels),max(v[0] for v in robot_pixels)],'y':[min(v[1] for v in robot_pixels),max(v[1] for v in robot_pixels)]}
 f['robot_pose']={'position_m':list(robot.location),'yaw_rad':robot.rotation_euler.z,'joint_angles_rad':{k:v['q'] for k,v in joints.items()},'authored':True,'source_transforms':'original XML pos/quat plus explicit joint rotations; no cached local matrices'}
 f['object_focus_world_m']=list(objpoint or target)
 f['projected_annotations']=[{'label':'G1 / authored pose','xy':pixel(robot.location+Vector((0,0,1.03))),'kind':'robot'},{'label':'Active hand / object target','xy':pixel(target),'kind':'target'}]
 if objpoint:f['projected_annotations'].append({'label':'Current lineage state','xy':pixel(objpoint),'kind':'object'})
 f['sample_representation']={'visible_instance_ids':[k for k,g in instance_groups.items() if any(not o.hide_render for o in g)],'old_PEM_module_duplicate_visible':any(not o.hide_render for o in instance_groups['T07_MODULE_PEM']),'active_module_visual_parts':sum(not o.hide_render for o in module),'finished_module_exists':c=='PAIR' and kind not in ['module_base','module_leg'],'leg_lineage':['leg.P1','leg.N1','leg.P2','leg.N2'] if c=='PAIR' else [c+'.parent'],'other_branch_samples_visible':False}
 f['transport']={'carrier':'WS_TRANSPORT numbered cart','keyframe_position_m':list(cartdest),'previous_station':frames[n-2]['station'] if n>1 else None,'changed_station':n>1 and frames[n-2]['station']!=st,'scope':'Supported-carrier station keyframes; intervening path and handoff microsteps aggregated, not collision-checked or executed'}
 f['inspection_scale']=detail_scale
 return objpoint,detail_scale

def render(p):scene.render.filepath=str(p);bpy.ops.render.render(write_still=True)
if '--audit-only' in sys.argv:
 for f in frames:state(f)
 vv=[o.matrix_world@Vector(v) for o in robot_meshes for v in o.bound_box]
 print('G1_HEIGHT',max(v.z for v in vv)-min(v.z for v in vv))
 (OUT/'qa/state_audit.json').write_text(json.dumps({'physics_executed':False,'rigidbody_world':scene.rigidbody_world is not None,'robot_visual_meshes':len(robot_meshes),'frames':[{'id':f['id'],**f['sample_representation']} for f in frames]},indent=2))
 (OUT/'frame_manifest.json').write_text(json.dumps(manifest,indent=2));sys.exit(0)
if '--overview' in sys.argv:
 state(frames[0],True);render(OUT/'raw/overview.png');manifest['overview_annotations']=frames[0]['projected_annotations'];(OUT/'frame_manifest.json').write_text(json.dumps(manifest,indent=2))
for f in frames:
 if ONLY and f['index'] not in ONLY:continue
 if '--skip-rendered' in sys.argv and f.get('rendered') and (OUT/'raw'/f"{f['index']:02d}_{f['id']}.png").exists():continue
 point,sc=state(f);render(OUT/'raw'/f"{f['index']:02d}_{f['id']}.png")
 if point is not None and f['visual_kind'] not in ['initial','reset','clean','boundary','pem_seal','powerdown','mill_run']:
  # Re-render the same active object with unrelated occluders removed only for inspection.
  hidden=[]
  for o in robot_meshes+hand_guides+(items('WS_PEM__hot_upper_contact')+items('WS_PEM__upper_contact_screw') if f['station']=='WS_PEM' else []):
   if not o.hide_render:o.hide_render=True;hidden.append(o)
  for o in closed_markers.values():
   if not o.hide_render:o.hide_render=True;hidden.append(o)
  setcam(point+Vector((.45,-.58,.37)),point,sc);scene.render.resolution_x=480;scene.render.resolution_y=360;scene.cycles.samples=24
  f['detail_labels']=[]
  if f['phase']=='PAIR' and f['visual_kind'] not in ['module_base']:
   for code in ['p1','n1','p2','n2']:
    gg=[o for o in module if ('_'+code+'_core') in o.name and not o.hide_render]
    if gg:f['detail_labels'].append({'label':code.upper(),'xy':pixel(center(gg)),'material':code[0].upper()})
  elif f['visual_kind']=='legs':
   for code in [f['phase']+'1',f['phase']+'2']:f['detail_labels'].append({'label':code,'xy':pixel(center(legs[code])),'material':code[0]})
  render(OUT/'raw'/f"{f['index']:02d}_{f['id']}_detail.png")
  for o in hidden:o.hide_render=False
  scene.render.resolution_x=1240;scene.render.resolution_y=800;scene.cycles.samples=32
  f['detail_image']=f"raw/{f['index']:02d}_{f['id']}_detail.png";f['detail_note']='Same active scene object; robot/guide/cover/contact occluders removed only in inspection camera.'
 f['rendered']=True;manifest['coverage']['frames_rendered']=sum(x.get('rendered',False) for x in frames);(OUT/'frame_manifest.json').write_text(json.dumps(manifest,indent=2));print('FRAME_RENDERED',f['index'],f['id'],flush=True)
print('SELECTED_RENDERS_DONE',flush=True)
