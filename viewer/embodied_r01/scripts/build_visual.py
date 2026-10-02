"""Authored R01 visual storyboard. Blender CPU renders only: no dynamics, contacts or controller.
Reuses existing original lab meshes and BSD-3-Clause G1 visual geometry.
"""
import bpy, math, json, sys, os, struct, xml.etree.ElementTree as ET, hashlib
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(os.environ.get('SCIENCEGYM_RENDER_OUT', str(Path(__file__).resolve().parents[1])))
SRC=Path(os.environ['SCIENCEGYM_SCENE_ROOT'])
TASK=Path(os.environ.get('SCIENCEGYM_TASKS_ROOT', str(Path(__file__).resolve().parents[3] / 'tasks/chiral_operations_v2')))
G1=Path(os.environ['SCIENCEGYM_G1_ROOT'])
(OUT/'raw').mkdir(exist_ok=True,parents=True)
ONLY=set(int(x) for x in sys.argv[sys.argv.index('--only')+1].split(',')) if '--only' in sys.argv else set()
branch=json.loads((TASK/'branches.json').read_text())['branches'][0]
ops={o['id']:o for o in json.loads((TASK/'operations.json').read_text())['operations']}
layout={s['id']:s for s in json.loads((SRC/'inputs/scene_layout_authored_v2.json').read_text())['stations']}
bpy.ops.wm.open_mainfile(filepath=str(SRC/'assets/r01_complete_route_scene.blend'))
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
   goal=Vector(target)+robot.matrix_world.to_3x3()@Vector((0,sgn*.19,0))
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
 d=layout[st];a=math.radians(d['authored_front_yaw_deg']);return Vector((d['center_xy_m'][0]+p[0]*math.cos(a)-p[1]*math.sin(a),d['center_xy_m'][1]+p[0]*math.sin(a)+p[1]*math.cos(a),p[2]))

stock=items('WS_STOCK__rubber_stock_1_'); loaded=items('WS_RUBBER_PRINT__loaded_rubber_cassette');tray=items('WS_RUBBER_PRINT__build_tray'); cart=items('MOBILE_TRANSFER__');
halves=[items('WS_POST__half_unit_stage_'+str(i)+'_') for i in range(1,19)];halfcenters=[center(g) for g in halves];sample=items('WS_TEST__mounted_');sample_origin=Vector((10.15,2.35,1.015));samplecent=center(sample)
# Every downstream sample is hidden until its lineage reaches that operation.
permanent_hide=items('ROBOT_PLACEHOLDER__')+items('WS_ASSEMBLY__placed_half_')+items('WS_ASSEMBLY__loose_half_')+items('WS_RUBBER_PRINT__loaded_rubber_cassette')+items('WS_TEST__sidebox_')+items('WS_TEST__rotation_lock_')
for o in original:
 if o.name.startswith('ROOM__route_segment'):permanent_hide.append(o)
plates=items('WS_ASSEMBLY__bottom_plate_stage')+items('WS_ASSEMBLY__top_plate_stage')
active_objects=[]; annotations=[]
# One explicit authored route through known dock positions; display only, no obstacle checks.
route_stations=['WS_STOCK','WS_RUBBER_PRINT','WS_POST','WS_ASSEMBLY','WS_METROLOGY','WS_TEST','WS_STORAGE','WS_CLEAN']
route_pts=[(1.7,6.25,.03),(4.5,6.25,.03),(4.5,5.95,.03),(9,5.95,.03),(9,5.6,.03),(8.9,3.4,.03),(7.5,3.4,.03),(4.55,3.4,.03),(8.25,3.4,.03),(8.25,2.25,.03),(8.25,2.7,.03),(1.65,2.7,.03),(1.65,2.5,.03),(2.95,2.7,.03),(2.95,4.65,.03)]
for i,(a,b) in enumerate(zip(route_pts,route_pts[1:])):seg('VISUAL_route_'+str(i),a,b,.025,blue)
for i,st in enumerate(route_stations):
 p=layout[st]['dock_pose_xyz_m'];bpy.ops.mesh.primitive_torus_add(major_segments=32,minor_segments=6,location=(p[0],p[1],.04),major_radius=.27,minor_radius=.025);bpy.context.object.name='VISUAL_dock_'+st;bpy.context.object.data.materials.append(blue)

TITLES=['Collect raw stock + empty tray','Load the material cassette','Insert build tray; start mock job','Release build; carry to handoff','Sort 18 released half-units','Locate the bottom plate','Place lower layer: 9 half-units','Place mirrored upper layer: 9 half-units','Join ring interfaces; seat top plate','Remove temporary locating tools','Record whole-specimen mass','Record external envelope','Carry specimen to tester','Open guard; clear loading volume','Seat specimen on lower platen','Preserve free internal rotation','Aim camera; capture initial shape','Close guard; arm task cycle 1','Load cycle 1; observe shape','Unload cycle 1','Record residual shape','Repeat load / unload on SAME object','Retrieve unloaded specimen','Archive R01 with two-cycle history','Return tools; dry-clean surfaces','Recover material; reset stations']
BEFORE=['Stock sealed; build tray empty','Stock at printer; chamber idle','Cassette seated; tray empty','Job-complete + safe-release events','Build tray at handoff','18 released halves; plates separate','Bottom plate and locators seated','9 lower half-units placed','18 half-units seated; top plate separate','Array joined; locating combs present','Assembled array; no cycle history','Whole mass fixture recorded','Envelope fixture recorded','Specimen staged outside tester','Guard open; platen retracted','Specimen seated; transport clips removed','Free internal-twist boundary','Initial image linked; robot withdrawn','Cycle 1 armed; guard closed','Cycle 1 terminal event','Cycle 1 unloaded; same object seated','Residual image recorded; cycle 1 complete','Cycle 2 complete; zero-load event','Specimen retrieved; history retained','Specimen archived','Tools returned; machine inactive']
AFTER=['Selected stock + empty tray at printer','Cassette inserted; feed cover closed','Mock job started; no finished sample yet','18-unit build travels to handoff','18 individual units sorted in R01 tray','Bottom plate on 3 x 3 locator','Lower layer complete: 9 / 18 units','Mirrored upper layer complete: 18 / 18','One assembled obj.R01.001','Combs removed; rings unbridged','Whole-mass mock field recorded','65 x 65 x 72 mm source envelope linked','Same specimen staged at tester','Loading area clear; no old boundary','Same specimen seated; gripper released','No lateral box or anti-rotation arm','Initial image fixture; same ID','Mock endpoint 0.25; cycle 1 armed','Authored compressed-shape illustration','Load/unload records for cycle 1','Residual state retained; no perfect-recovery claim','Separate cycle-2 records; same obj.R01.001','Tester empty; specimen in numbered carrier','R01 archived as used; 2 task cycles','Dry wipe + tooling returned','Leftover stock returned; safe idle + cart parked']
CARRIED=['stock.rubber.R01 + empty build tray','stock.rubber.R01','build_tray.R01','tray.R01.build + units01-18','unit.R01.018 to compartment','plate.R01.bottom','unit.R01.009','unit.R01.018','plate.R01.top','temporary locating comb','obj.R01.001','caliper (authored metrology)','tray.R01 + obj.R01.001','guard handle / empty hand','obj.R01.001 by bottom plate','removable transport support','camera mount','guard handle; hand withdrawn','none: robot outside hazard zone','none: robot outside hazard zone','none: camera observation','none: same specimen remains seated','tray.R01 + obj.R01.001','obj.R01.001 to archive slot','dry wipe / locating comb','leftover stock + empty tray']
frames=[]
for n,k in enumerate(branch['operation_sequence']):
 o=ops[k];st=o['location_id'];st=branch['location_binding'].get(st,st)
 frames.append({'id':k,'index':n+1,'title':TITLES[n],'image':f'frames/{n+1:02d}_{k}.jpg','action':' '.join(o['actions']),'station':st,'objects':CARRIED[n],'sample_state_before':BEFORE[n],'sample_state_after':AFTER[n],'evidence':{'operation_file':str(TASK/'operations.json'),'operation_id':k,'branch':'R01','source_refs':o.get('provenance',{})},'authored_notes':'Authored static visual demonstration; specimen/robot poses and apparatus are illustrative. No physical execution, contact, force, collision, or reachability validation.','physical_object_id':'obj.R01.001','source_unit_lineage':[f'unit.R01.{i:03d}' for i in range(1,19)],'robot':{'geometry':'Unitree G1 visual meshes, BSD-3-Clause','pose':'authored XML-transform posing, no controller'},'camera':None,'projected_annotations':[]})
manifest={'title':'Chiral R01 | An embodied whole-route task','status':'Authored visual task demonstration; static / kinematic storyboard','coverage':{'reference_operations':26,'frames_planned':26,'frames_rendered':0,'operation_iterations':'9 lower + 9 upper placements summarized in layer-completion keyframes; no per-pick execution claim'},'limitations':['Physical simulation paused; no robot execution or contact validation','Generic laboratory apparatus proxies; source apparatus make/model unknown','Only R01 rubber route; not whole-paper branch coverage','Fabrication completion is a mock event; process/recipe unknown','Two task cycles are authored; not the paper total cycle count','Compression geometry is an authored illustration, not mechanics or measured recovery','Single lineage: downstream state geometry hidden until corresponding step'], 'overview':'overview.jpg','frames':frames,'source_scene':str(SRC),'source_tasks':str(TASK),'attribution':'Unitree G1 visual geometry: Copyright 2016-2023 HangZhou YuShu TECHNOLOGY CO.,LTD. BSD-3-Clause. See licenses/Unitree_G1_BSD3.txt. Lab/equipment/sample geometry: existing first-party authored proxies.'}
if ONLY and (OUT/'frame_manifest.json').exists():
 manifest=json.loads((OUT/'frame_manifest.json').read_text());frames=manifest['frames']
else:(OUT/'frame_manifest.json').write_text(json.dumps(manifest,indent=2))
# General CPU render configuration.
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=8;scene.render.resolution_x=1240;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-1.25;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='EMBODIED_VISUAL_CAMERA';cam.data.type='ORTHO';cam.data.clip_start=.005;scene.camera=cam

def setcam(loc,target,scale):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;bpy.context.view_layer.update()
def pixel(p):
 v=world_to_camera_view(scene,cam,Vector(p));return [round(v.x*scene.render.resolution_x,1),round((1-v.y)*scene.render.resolution_y,1)]
def highlight(group):
 for o in group:
  if o.type=='MESH':o.data.materials.clear();o.data.materials.append(orange)
def reset_state():
 for o in original:
  o.matrix_world=BASE[o.name].copy();o.hide_render=False;o.hide_viewport=False
  if o.name in MATBASE:o.data.materials.clear();[o.data.materials.append(m) for m in MATBASE[o.name]]
 show(permanent_hide,False);show(sample,False)
 for g in halves:show(g,False)
 show(plates,False)
 # The other stock cassettes remain legitimate unused raw inventory.
 show(stock,True);show(cart,True)

def set_sample(dest,compressed=False):
 show(sample,True);T=Matrix.Translation(Vector(dest)-sample_origin)
 if compressed:
  T=Matrix.Translation(Vector(dest))@Matrix.Diagonal((1,1,.75,1))@Matrix.Translation(-sample_origin)
 for o in sample:o.matrix_world=T@BASE[o.name]
 return Vector(dest)+Vector((0,0,.036 if not compressed else .027))
def set_halves(where,count=18,assembled=0):
 for i,g in enumerate(halves):
  show(g,i<count)
  if i>=count:continue
  if i<assembled:
   j=i%9;dest=local('WS_ASSEMBLY',(-.22+(j%3-1)*.021,(j//3-1)*.021,.943+(i//9)*.033))
  else:
   dest=Vector(where)+Vector(((i%3-1)*.05,(i//3-2.5)*.061,.017))
  move(g,halfcenters[i],dest)

def state(n,overview=False):
 reset_state();f=frames[n];st='WS_STOCK' if n==25 else f['station'];dock=Vector(layout[st]['dock_pose_xyz_m']);face=Vector((*layout[st]['center_xy_m'],0))-dock;face.normalize();right=Vector((face.y,-face.x,0));pos=dock+face*.35+right*.18+Vector((0,0,.035))
 robot.location=pos;robot.rotation_euler=(0,0,math.atan2(face.y,face.x));bpy.context.view_layer.update()
 traygoal=pos+face*.35+Vector((0,0,.94));pose(traygoal)
 # Move cart with the active station, at its side, away from work volume.
 cartdest=pos+right*.75+face*.05;move(cart,(3.10,2.80,0),cartdest,math.atan2(face.y,face.x)-math.pi/2)
 target=local(st,(0,-.15,1.0));objpoint=None;targetgroup=[]
 if 4<=n<25:move(tray,(4.27,6.86,1.015),local('WS_POST',(0,-.11,.932)))
 if n>=10:
  tools=items('WS_ASSEMBLY__alignment_comb')+items('WS_ASSEMBLY__comb_tooth');move(tools,(7.28,4.63,.95),local('WS_CLEAN',(.45,-.02,.97)))
 # Stock remains seated in printer after insertion, until recovered at final step.
 if n not in [1,3]:
  for o in items('WS_RUBBER_PRINT__door_open')+items('WS_RUBBER_PRINT__door_handle'):o.location.x+=1.43
 if n>=1:move(stock,(1.16,7.22,1.03),local('WS_RUBBER_PRINT',(.59,-.53,1.08)))
 if n==0:
  move(stock,(1.16,7.22,1.03),traygoal+Vector((0,0,.15)));move(tray,(4.27,6.86,1.015),traygoal-Vector((0,0,.03)));targetgroup=stock;target=traygoal;objpoint=traygoal+Vector((0,0,.14))
 elif n==1:targetgroup=stock;target=local(st,(.59,-.53,1.08));objpoint=target
 elif n==2:
  targetgroup=items('WS_RUBBER_PRINT__key_START');target=local(st,(.63,-.819,1.60))
 elif n==3:
  move(tray,(4.27,6.86,1.015),traygoal-Vector((0,0,.02)));set_halves(traygoal,count=18);targetgroup=tray;target=traygoal;objpoint=traygoal
 elif n==4:
  set_halves(local(st,(0,-.11,.949)));targetgroup=halves[-1];target=center(halves[-1]);objpoint=target
 elif 5<=n<=8:
  show(plates,True);set_halves(local(st,(.38,.01,.949)),18,0 if n==5 else 9 if n==6 else 18)
  bottom=items('WS_ASSEMBLY__bottom_plate_stage');move(bottom,(7.0,4.53,.923),local(st,(-.22,0,.937)))
  if n==8:
   for g in halves:show(g,False)
   show(plates,False);objpoint=set_sample(local(st,(-.22,0,.943)));targetgroup=items('WS_TEST__mounted_sample_top_plate');target=objpoint
  else:targetgroup=bottom if n==5 else halves[8 if n==6 else 17];target=center(targetgroup);objpoint=target
 elif n==9:
  objpoint=set_sample(local(st,(-.22,0,.943)));targetgroup=items('WS_ASSEMBLY__alignment_comb')+items('WS_ASSEMBLY__comb_tooth');move(targetgroup,(7.28,4.63,.95),traygoal);target=traygoal
 elif n in [10,11]:
  dest=local(st,(-.43,.08,1.002)) if n==10 else local(st,(.27,-.02,.935));objpoint=set_sample(dest);targetgroup=items('WS_METROLOGY__balance_pan') if n==10 else items('WS_METROLOGY__caliper_');target=objpoint
 elif n in [12,13]:
  objpoint=set_sample(local(st,(-.45,-.02,.863)));targetgroup=items('WS_TEST__carrier_') if n==12 else items('WS_TEST__guard_handle');target=center(targetgroup)
 elif 14<=n<=21:
  objpoint=set_sample(sample_origin,compressed=n in [18,21]);targetgroup=sample if n in [14,15,18,20,21] else items('WS_TEST__camera_') if n==16 else items('WS_TEST__guard_handle') if n==17 else items('WS_TEST__upper_platen');target=center(targetgroup)
  if n>=17:
   # Slide the original open guard into its closed display pose.
   for o in items('WS_TEST__guard_front_panel')+items('WS_TEST__guard_handle'):o.location.y-=.72
   robot.location=dock-face*.22+right*.52;bpy.context.view_layer.update();pose(None)
  if n in [18,21]:
   # Illustrative axial displacement only; no physical response or predicted twist.
   for o in items('WS_TEST__upper_platen'):o.location.z-=.176
 elif n==22:
  objpoint=set_sample(traygoal);targetgroup=sample;target=traygoal
 elif n>=23:
  objpoint=set_sample(local('WS_STORAGE',(0,-.04,.67)));targetgroup=sample if n==23 else items('WS_CLEAN__dry_wipe') if n==24 else stock;target=center(targetgroup)
  if n==25:
   move(stock,(1.16,7.22,1.03),(1.16,7.22,1.03));target=Vector((1.16,7.22,1.03));move(cart,(3.10,2.80,0),(3.1,2.8,0));
 # Authored interaction pose. Navigation poses and arm poses are not execution evidence.
 if n not in [0,3,17,18,19,20,21,22,25]:
  approach=Vector((target.x,target.y,.035))-face*.52
  robot.location=approach;bpy.context.view_layer.update();pose(target)
  # Keep a visible cart parked beside the active robot, not between hand and target.
  cartdest=approach+right*.83-face*.22;move(cart,(3.10,2.80,0),cartdest,math.atan2(face.y,face.x)-math.pi/2)
 highlight(targetgroup)
 # Remove all inactive duplicate assembly half-cell stage props at every time.
 bpy.context.view_layer.update()
 if overview or n==25:setcam((18,-15,20),(5.8,4.6,.0),16.8)
 else:
  c=Vector((*layout[st]['center_xy_m'],.85));view=c-face*4.2+right*3.8+Vector((0,0,2.15));setcam(view,c-face*.3,3.8 if st!='WS_RUBBER_PRINT' else 4.25)
 f['camera']={'location':list(cam.location),'target_station':st,'ortho_scale':cam.data.ortho_scale}
 f['robot_pose']={'position_m':list(robot.location),'yaw_rad':robot.rotation_euler.z,'authored':True,'joint_angles_rad':{k:j['q'] for k,j in joints.items()}}
 f['object_focus_world_m']=list(objpoint or target)
 f['projected_annotations']=[{'label':'G1 visual model / authored pose','xy':pixel(robot.location+Vector((0,0,1.15))),'kind':'robot'},{'label':'ACTIVE: '+CARRIED[n],'xy':pixel(target),'kind':'target'}]
 if objpoint:f['projected_annotations'].append({'label':'R01 lineage / current state','xy':pixel(objpoint),'kind':'object'})
 f['sample_representation']={'assembled_visible':sum(not o.hide_render for o in sample)>0,'half_units_visible':sum(not g[0].hide_render for g in halves),'assembly_stage_copies_visible':False,'mounted_identity':'obj.R01.001' if n>=8 else None}
 return target,objpoint

def render(path):
 scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)

# Audit authored pose hierarchy without rendering.
if '--audit-only' in sys.argv:
 state(8);bpy.context.view_layer.update();vv=[o.matrix_world@Vector(v) for o in robot_meshes for v in o.bound_box]
 print('G1_BOUNDS',[(min(v[a] for v in vv),max(v[a] for v in vv)) for a in range(3)],flush=True)
 for key in ['pelvis','torso_link','left_shoulder_pitch_link','left_elbow_link','left_wrist_yaw_link','left_ankle_roll_link']:
  if key in links:print('LINK',key,tuple(links[key].matrix_world.translation),'LOCAL',tuple(links[key].matrix_local.translation),flush=True)
 print('POSE',frames[8]['robot_pose'],flush=True);sys.exit(0)
if not ONLY:
 # Publish one annotated initial state overview first.
 state(0,True);render(OUT/'raw/overview.png');manifest['overview_annotations']=[{'label':'Mobile G1 visual robot','xy':pixel(robot.location+Vector((0,0,.9))),'kind':'robot'},{'label':'Raw R01 stock + empty tray','xy':pixel(Vector(frames[0]['object_focus_world_m'])),'kind':'object'}]
 for i,st in enumerate(route_stations):manifest['overview_annotations'].append({'label':f'{i+1}. '+{'WS_STOCK':'RAW STOCK','WS_RUBBER_PRINT':'FABRICATION','WS_POST':'RELEASE / SORT','WS_ASSEMBLY':'ASSEMBLY','WS_METROLOGY':'METROLOGY','WS_TEST':'LOAD / OBSERVE / REPEAT','WS_STORAGE':'ARCHIVE','WS_CLEAN':'CLEANUP'}[st],'xy':pixel(local(st,(0,0,.9))),'kind':'station'})
 (OUT/'frame_manifest.json').write_text(json.dumps(manifest,indent=2));print('OVERVIEW_RENDERED',flush=True)
 if '--overview-only' in sys.argv:sys.exit(0)
for n,f in enumerate(frames):
 if ONLY and n+1 not in ONLY:continue
 target,objpoint=state(n)
 if '--details-only' not in sys.argv:render(OUT/'raw'/f"{n+1:02d}_{f['id']}.png")
 # A screen-space inspection view of the SAME scene object, not an extra sample in world.
 if objpoint is not None and n>=3:
  focus=Vector(objpoint);scale=.32 if n in [3,4,5,6,7] else .19
  setcam(focus+Vector((.20,-.28,.025) if 14<=n<=21 else (.18,.24,.10) if n>=23 else (.18,-.24,.16)),focus,scale);scene.render.resolution_x=480;scene.render.resolution_y=360;scene.cycles.samples=12;render(OUT/'raw'/f"{n+1:02d}_{f['id']}_detail.png");scene.render.resolution_x=1240;scene.render.resolution_y=800;scene.cycles.samples=24
  f['detail_image']=f"raw/{n+1:02d}_{f['id']}_detail.png"
 f['rendered']=True;manifest['coverage']['frames_rendered']=n+1;(OUT/'frame_manifest.json').write_text(json.dumps(manifest,indent=2));print('FRAME_RENDERED',n+1,f['id'],flush=True)
receipt={'status':'final_corrected_G1_hierarchy','obsolete_pass':'Pass 1 joint offsets collapsed because cached local transforms were read too early. All pass-1 images superseded. Final uses XML source transforms directly.','robot_hierarchy_validation':'pelvis root and native body offsets retained; full G1 visual height approximately 1.323 m; ground offset 0.035 m','renderer':'Blender 4.3.2 Cycles CPU','samples':24,'detail_samples':12,'source_scene_sha256':hashlib.sha256((SRC/'assets/r01_complete_route_scene.blend').read_bytes()).hexdigest(),'robot_source':str(G1),'robot_license':'BSD-3-Clause','robot_visual_meshes':len(robot_meshes),'physics_executed':False,'rigidbody_world':False,'robot_execution':False,'contact_validation':False,'policy_controller':False,'state_steps':26,'rendered_reference_operations':[f['id'] for f in frames], 'deformation':'Authored axial visual scaling, no mechanics or predicted recovery','source_assets_duplicated':False,'sample_visibility_audit':[{'id':f['id'],**f['sample_representation']} for f in frames]}
(OUT/'render_receipt.json').write_text(json.dumps(receipt,indent=2));print('ALL_RENDERED',flush=True)
