"""Original static scene. No physics, hardware, source CAD, or source software."""
import bpy, math, json, sys, hashlib, time
from mathutils import Vector
from pathlib import Path
P=Path(__file__).resolve().parents[1]
NORENDER='--no-render' in sys.argv
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene; sc.unit_settings.system='METRIC'; sc.unit_settings.scale_length=1
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=64
sc.cycles.use_denoising=False; sc.render.resolution_x=1600; sc.render.resolution_y=1000;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False
sc.world=bpy.data.worlds.new('Studio.World'); sc.world.use_nodes=True; sc.world.node_tree.nodes['Background'].inputs[0].default_value=(0.045,0.06,0.085,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.6
sc.view_settings.view_transform='AgX'
COL=bpy.data.collections.new('Original.Assets');sc.collection.children.link(COL)
STU=bpy.data.collections.new('Studio.NotExported');sc.collection.children.link(STU)
roots={};mats={}
req=json.load(open(P/'requirements_snapshot.json'))
for a in req['assets']:
 o=bpy.data.objects.new('ASSET.'+a['id'],None);COL.objects.link(o);o['asset_id']=a['id'];o['source_basis']=a['basis'];o['fidelity_boundary']=a['fidelity_boundary'];o['physical_execution_enabled']=False;roots[a['id']]=o

def mat(n,c,metal=0,rough=.45,alpha=1,trans=0):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,alpha);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,alpha);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;p.inputs['Alpha'].default_value=alpha;p.inputs['Transmission Weight'].default_value=trans;mats[n]=m;return m
mat('Ceramic.teal',(.018,.31,.32),.1);mat('Frame.navy',(.018,.038,.067),.65);mat('Steel.satin',(.4,.49,.56),.8);mat('Polymer.ivory',(.79,.81,.78));mat('Marker.graphite',(.015,.019,.025),.1);mat('Accent.amber',(1,.36,.05),.2);mat('Screen.blue',(.015,.25,.52),.3);mat('Status.green',(.04,.65,.36));mat('Fault.coral',(.8,.045,.025));mat('Panel.white',(.87,.9,.88));mat('Type.white',(.94,.97,1));mat('Type.navy',(.01,.023,.045));mat('Floor.slate',(.045,.07,.105),.2);mat('Glass.visual',(.45,.72,.78),0,.15,.12,.3);mat('Symbolic.violet',(.31,.10,.53),.3)

def own(o,n,a,ma):
 o.name=n
 for c in list(o.users_collection):c.objects.unlink(o)
 (COL if a else STU).objects.link(o)
 if a:o.parent=roots[a];o['asset_id']=a;o['geometry_class']='authored_display';o['physical_execution_enabled']=False
 if ma:o.data.materials.append(mats[ma])
 return o

def cube(n,loc,dims,a,ma='Frame.navy',bev=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=own(bpy.context.object,n,a,ma);o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bev:
  mo=o.modifiers.new('Original edge fillet','BEVEL');mo.width=bev;mo.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mo.name)
 return o

def cyl(n,loc,r,depth,a,ma='Steel.satin',rot=(0,0,0)):
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=depth,location=loc,rotation=rot);return own(bpy.context.object,n,a,ma)

def text(n,s,loc,size,a,ma='Type.white',rot=(math.pi/2,0,0),align='CENTER'):
 cu=bpy.data.curves.new(n,'FONT');cu.body=s;cu.size=size;cu.align_x=align;cu.align_y='CENTER';cu.extrude=size*.006
 o=bpy.data.objects.new(n,cu);COL.objects.link(o);o.location=loc;o.rotation_euler=rot;o.parent=roots[a] if a else None
 if a:o['asset_id']=a;o['geometry_class']='authored_label'
 o.data.materials.append(mats[ma]);bpy.context.view_layer.objects.active=o;o.select_set(True)
 bpy.ops.object.convert(target='MESH');o=bpy.context.object;o.select_set(False);return o

def plate(n,s,loc,width,height,a,ma='Frame.navy',font=.035):
 cube(n+'.back',loc,(width,.035,height),a,ma,.01);return text(n+'.label',s,(loc[0],loc[1]-.020,loc[2]),font,a)

def empty(n,loc,a,typ='semantic_anchor',target=None):
 o=bpy.data.objects.new(n,None);COL.objects.link(o);o.parent=roots[a];o.location=loc;o.empty_display_size=.02;o.empty_display_type='PLAIN_AXES';o['asset_id']=a;o['kind']=typ;o['qualified_pose']=False;o['physical_execution_enabled']=False
 if target:o['target_mesh']=target
 return o

def table(n,x,y,a,w=.85,d=.65,h=.73):
 cube(n+'.top',(x,y,h),(w,d,.05),a,'Panel.white',.025)
 for dx in [-w*.4,w*.4]:
  for dy in [-d*.36,d*.36]:cube(n+'.leg'+str(dx)+str(dy),(x+dx,y+dy,h/2),(.035,.035,h),a,'Steel.satin')

# A01/A02: source scalar envelope and counts, original disconnected presentation lattice.
L,W,H=.306,.064,.04;side=.0048;ang=math.radians(20);extent=side*(math.cos(ang)+math.sin(ang));px=(L-extent)/47;pz=(W-extent)/9
for i in range(48):
 for j in range(10):
  x=-L/2+extent/2+i*px;z=1.10-W/2+extent/2+j*pz
  o=cube(f'beam.square.{i:02}.{j:02}',(x,0,z),(side,H,side),'A01','Ceramic.teal');o.rotation_euler.y=ang*((-1)**(i+j));o['geometry_class']='source_scalar_authored_placement';o['square_side_mm']=4.8;o['topology_validated']=False
  pad=cube(f'pad.{i:02}.{j:02}',(x,-.02035,z),(.0036,.0005,.0036),'A02','Marker.graphite');pad.rotation_euler.y=o.rotation_euler.y;pad['geometry_class']='source_scalar_authored_placement';pad['pad_side_mm']=3.6;pad['tracking_id']=f'display_{i:02}_{j:02}'
# Dimension lines surround, rather than distort, the specimen.
for z in [1.053]:
 cube('beam.length_reference',(0,-.028,z),(.306,.0006,.0006),'A01','Accent.amber')
 for x in [-.153,.153]:cube('beam.dimension_tick'+str(x),(x,-.028,z),(.0006,.0006,.005),'A01','Accent.amber')
text('beam.scalar_label','306 mm',(0,-.03,1.043),.009,'A01','Accent.amber')
text('beam.topology_label','48 x 10  |  layout illustrative',(0,-.03,1.157),.008,'A01','Type.navy')
text('beam.detail_label','4.8 mm squares / 3.6 mm pads',(0,-.03,1.147),.006,'A01','Type.navy')
cube('beam.build_receipt',(-.23,-.22,.86),(.055,.032,.008),'A01','Status.green',.002)
# Separate dimensional hinge gauge is a reference, not a fabricated connector.
cube('beam.hinge_gauge',(0.166,-.015,1.11),(.0002,.008,.016),'A01','Accent.amber')
text('beam.hinge_label','0.2 mm\nhinge datum\nnot connected',(.171,-.03,1.10),.0045,'A01','Type.navy',align='LEFT')

# A05 guarded tester. Static visual guard, not a safety-qualified machine.
cube('tester.base',(0,0,.82),(.78,.64,.10),'A05','Frame.navy',.035)
for x in [-.36,.36]:
 for y in [-.28,.28]:cube('tester.post'+str(x)+str(y),(x,y,1.33),(.028,.028,1),'A05','Steel.satin',.004)
cube('tester.roof',(0,0,1.84),(.80,.67,.065),'A05','Frame.navy',.02)
for x in [-.355,.355]:cube('tester.side_guard'+str(x),(x,0,1.30),(.006,.52,.88),'A05','Glass.visual')
cube('tester.front_guard',(0,-.276,1.30),(.68,.003,.88),'A05','Glass.visual')
cube('tester.rear_guard',(0,.276,1.30),(.68,.003,.88),'A05','Glass.visual')
cyl('tester.load_axis',(0,0,1.58),.018,.38,'A05');cyl('tester.loadcell',(0,0,1.365),.05,.055,'A05','Ceramic.teal')
cube('tester.fixture_dock',(0,0,.965),(.40,.22,.05),'A05','Steel.satin',.009)
cube('tester.fixture_latch',(.28,-.29,1.12),(.05,.028,.10),'A05','Accent.amber',.007)
cube('tester.interlock',(.31,-.299,1.37),(.045,.02,.065),'A05','Status.green',.005)
cyl('tester.emergency_stop',(.30,-.33,.875),.029,.025,'A05','Fault.coral',(math.pi/2,0,0))
for nm,x,ma in [('test_trigger',-.26,'Screen.blue'),('mechanics_receipt',-.15,'Status.green'),('isolation_port',-.04,'Accent.amber')]:cube('tester.'+nm,(x,-.329,.86),(.07,.018,.034),'A05',ma,.004)
plate('tester.title','STATIC MECHANICS',(0,-.36,1.85),.72,.12,'A05',font=.057)
text('tester.status','DISARMED / UNLOADED',(0,-.34,.805),.038,'A05','Accent.amber')

# A04: original three-point fixture proxy, exact span and contacts not claimed.
for x,n in [(-.12,'left'),(.12,'right')]:
 cyl('bridge.'+n+'_support',(x,0,1.05),.011,.10,'A04','Ceramic.teal',(math.pi/2,0,0))
 cube('bridge.'+n+'_stand',(x,0,1.01),(.04,.10,.07),'A04','Steel.satin',.006)
cyl('bridge.center_pusher',(0,0,1.235),.012,.09,'A04','Accent.amber',(math.pi/2,0,0))
cube('bridge.mount',(0,0,1.28),(.07,.07,.07),'A04','Steel.satin',.008)
plate('bridge.caption','BRIDGE: DISPLAY ONLY',(0,.22,.94),.42,.06,'A04',font=.021)

# A03: foot-like outline is independently designed and parked beside the machine.
table('foot.parking',-.62,-.06,'A03',.35,.42,.75)
outline=[(-.11,-.024),(-.09,-.046),(-.045,-.045),(0,-.027),(.055,-.038),(.105,-.030),(.12,-.012),(.117,.035),(.082,.047),(.018,.028),(-.03,.018),(-.085,.034),(-.111,.015)]
verts=[(x-.62,y,z) for y in [-.11,.01] for x,z in outline];n=len(outline);faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
me=bpy.data.meshes.new('foot.original_outline');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('foot.original_proxy',me);COL.objects.link(o);o.parent=roots['A03'];o.location.z=.87;o['asset_id']='A03';o['geometry_class']='authored_placeholder';me.materials.append(mats['Accent.amber'])
cube('foot.mount',(-.62,-.05,.97),(.07,.09,.08),'A03','Steel.satin',.009)
cube('foot.inspection_tag',(-.63,-.23,.78),(.12,.022,.03),'A03','Status.green',.004)
plate('foot.label','FOOT / PARKED',(-.62,-.265,.705),.40,.095,'A03',font=.029)

# A06: source 4 m camera-target separation; product shell is original.
C=(0,-4,1.10)
cube('camera.body',(0,-4.16,1.1),(.25,.13,.17),'A06','Frame.navy',.03)
cyl('camera.lens',(0,-4.055,1.1),.054,.17,'A06','Marker.graphite',(math.pi/2,0,0));cyl('camera.front_element',C,.047,.009,'A06','Screen.blue',(math.pi/2,0,0))
cyl('camera.tripod_column',(0,-4.15,.65),.018,.72,'A06')
for x,y in [(-.30,-4.32),(.30,-4.32),(0,-3.92)]:
 v=Vector((x,y,.04))-Vector((0,-4.15,.68));o=cyl('camera.tripod_leg'+str(x)+str(y),(Vector((x,y,.04))+Vector((0,-4.15,.68)))/2,.014,v.length,'A06');o.rotation_euler=v.to_track_quat('Z','Y').to_euler()
plate('camera.label','CAMERA  /  4 m',(0,-4.38,.33),.85,.13,'A06',font=.057)
# Floor witness line denotes distance metadata only, not a real ray or optical simulation.
for i in range(17):cube('camera.distance_mark'+str(i),(.10,-3.8+i*.21,.017),(.014,.085,.006),'A06','Screen.blue')
text('camera.distance_caption','4 m SOURCE DISTANCE  /  OPTICS UNCALIBRATED',(.35,-2.15,.035),.074,'A06','Type.white',rot=(0,0,math.pi/2))

# A07: two source-role LED panels and a white backing sheet proxy.
for x,name in [(-.84,'left'),(.84,'right')]:
 cyl('lighting.'+name+'_stand',(x,-.28,.85),.012,1.5,'A07');cube('lighting.'+name+'_panel',(x,-.28,1.65),(.35,.04,.25),'A07','Panel.white',.015)
 cube('lighting.'+name+'_foot',(x,-.28,.035),(.27,.28,.04),'A07','Frame.navy',.015)
cube('lighting.background',(0,.24,1.12),(.48,.004,.21),'A07','Panel.white')

# A08: supported carrier, storage, recovery and quarantine. Handles avoid fragile squares.
table('storage.table',-1.43,-1.1,'A08',1.12,.76,.73)
cube('carrier.base',(-1.45,-1.16,.805),(.48,.25,.045),'A08','Ceramic.teal',.014)
for x in [-1.64,-1.26]:cube('carrier.support'+str(x),(x,-1.16,.837),(.045,.18,.02),'A08','Polymer.ivory',.004)
for x,n in [(-1.72,'left'),(-1.18,'right')]:cube('carrier.handle_'+n,(x,-1.16,.823),(.09,.13,.035),'A08','Steel.satin',.012)
cube('carrier.dock_key',(-1.45,-1.28,.85),(.045,.025,.025),'A08','Accent.amber',.003)
for nm,x,ma in [('storage_slot',-1.76,'Screen.blue'),('recovery_slot',-1.43,'Status.green'),('quarantine_slot',-1.10,'Fault.coral')]:
 cube('storage.'+nm,(x,-.83,.81),(.27,.16,.04),'A08',ma,.01)
 text('storage.'+nm+'.label',nm.split('_')[0].upper(),(x,-.925,.875),.021,'A08')
cube('storage.archive_port',(-1.45,-1.485,.72),(.23,.025,.08),'A08','Screen.blue',.008)
plate('storage.label','SUPPORTED TRANSFER',(-1.43,-1.505,.62),1.04,.13,'A08',font=.056)
# Stationary end-effector visual grasping empty carrier handles, not specimen.
cube('carrier.gripper_body',(-1.95,-1.16,1.03),(.13,.19,.09),'A08','Frame.navy',.012)
for y in [-1.235,-1.085]:cube('carrier.gripper_finger'+str(y),(-1.84,y,.935),(.035,.025,.15),'A08','Steel.satin',.003)

# A09: only closed fabrication/contact qualified-service shells and receipt ports.
table('service.table',-1.49,.36,'A09',1.06,.76,.73)
for x,n,ma in [(-1.76,'fabrication','Ceramic.teal'),(-1.24,'contact','Frame.navy')]:
 cube('service.'+n+'_shell',(x,.36,1.005),(.45,.58,.48),'A09',ma,.035)
 cube('service.'+n+'_door',(x,.063,1.02),(.34,.018,.33),'A09','Steel.satin',.015)
 cube('service.'+n+'_in',(x,-.002,.87),(.22,.12,.045),'A09','Accent.amber',.009)
 cube('service.'+n+'_receipt',(x,.045,1.12),(.16,.018,.06),'A09','Status.green',.005)
 text('service.'+n+'_title',n.upper(),(x,.035,1.215),.035,'A09')
 text('service.'+n+'_closed','CLOSED SERVICE',(x,.035,1.02),.024,'A09')
plate('service.label','QUALIFIED SERVICES',(-1.5,-.045,.665),1.04,.13,'A09',font=.056)
text('service.warning','NO POWDER / NO MACHINE RECIPE',(-1.5,-.04,.795),.027,'A09','Accent.amber')

# A10: calibration target and distinct inspection/receipt ports, no certificate.
table('calibration.table',1.32,-1.25,'A10',.88,.72,.73)
cube('calibration.target',(1.31,-1.12,.97),(.34,.022,.30),'A10','Panel.white',.003)
for i in range(6):
 for j in range(4):
  if (i+j)%2==0:cube(f'calibration.checker.{i}.{j}',(1.31+(i-2.5)*.045,-1.137,.97+(j-1.5)*.055),(.045,.002,.055),'A10','Marker.graphite')
cube('calibration.mount',(1.31,-1.12,.83),(.045,.07,.18),'A10','Steel.satin',.007)
cube('calibration.camera_receipt',(1.60,-1.32,.79),(.16,.14,.025),'A10','Screen.blue',.008)
plate('calibration.label','REFERENCE / QC',(1.32,-1.635,.64),.87,.13,'A10',font=.052)

# A11: separate fit, inference, tracking and evaluator policy paths.
table('analysis.table',1.48,.25,'A11',1.10,.75,.73)
cube('analysis.console_body',(1.48,.30,1.105),(1.05,.11,.62),'A11','Frame.navy',.035)
text('analysis.title','RECEIPTS & ANALYSIS',(1.48,.237,1.355),.057,'A11')
ports=[('campaign_port','PLAN','Screen.blue'),('freeze_policy','FREEZE','Accent.amber'),('sync_port','SYNC','Screen.blue'),('capture_gate','CAPTURE','Status.green'),('tracking_port','TRACK','Screen.blue'),('quality_mask','MASK','Accent.amber'),('fit_port','FIT','Ceramic.teal'),('inference_port','BOUNDARY','Symbolic.violet'),('evaluation_port','COMPARE','Screen.blue'),('policy_port','POLICY','Accent.amber')]
for i,(nm,label,ma) in enumerate(ports):
 x=1.48+(i%2-.5)*.47;z=1.245-(i//2)*.10
 cube('analysis.'+nm,(x,.231,z),(.41,.03,.079),'A11',ma,.008);text('analysis.'+nm+'.label',label,(x,.211,z),.036,'A11')
plate('analysis.label','DATA REMAINS IMMUTABLE',(1.48,-.15,.655),1.11,.13,'A11',font=.052)

# A12: explicitly symbolic board, never invented physical simulation hardware.
cube('symbolic.board',(-.3,1.03,1.18),(2.03,.10,.80),'A12','Symbolic.violet',.035)
text('symbolic.title','NUMERICAL / THEORY SCOPE',(-.3,.971,1.49),.078,'A12')
for i,(nm,title,sub) in enumerate([('unit_cell_card','B04 / UNIT CELL','FEM: unexecuted'),('fem_card','B05 / STRUCTURE','FEM: unexecuted'),('theory_card','B07 / THEORY','Conflicts retained'),('spring_card','B08 / SPRINGS','Numerical only')]):
 x=-1.05+i*.5;cube('symbolic.'+nm,(x,.965,1.15),(.45,.024,.39),'A12','Frame.navy',.018)
 text('symbolic.'+nm+'.title',title,(x,.947,1.275),.031,'A12');text('symbolic.'+nm+'.sub',sub,(x,.947,1.038),.028,'A12','Accent.amber')
 # Original symbolic ring, not a scientific model.
 for k in range(4):
  ob=cube('symbolic.icon'+str(i)+str(k),(x+(k%2-.5)*.11,.942,1.16+(k//2-.5)*.11),(.07,.016,.07),'A12','Ceramic.teal');ob.rotation_euler.y=math.radians(20*(-1)**k)
cube('symbolic.scope_guard',(-.3,.945,.846),(1.87,.03,.095),'A12','Accent.amber',.014)
text('symbolic.scope_guard.label','NO PHYSICAL BOUNDARY ACTUATOR',(-.3,.925,.846),.058,'A12','Type.navy')

# Required semantic anchors are explicit labeled selectors, not qualified coordinates.
positions={
'A01':[(0,0,1.1),(-.12,0,1.05),(.12,0,1.05),(0,-.0205,1.1),(-1.72,-1.16,.823)],
'A02':[(0,-.0205,1.1),(-.15,-.0205,1.07)],
'A03':[(-.62,-.05,.97),(-.62,-.05,.82),(-.62,-.05,1.05)],
'A04':[(-.12,0,1.05),(.12,0,1.05),(0,0,1.235),(0,0,1.3)],
'A05':[(0,0,.965),(0,0,1.58),(.36,0,1.3),(.31,-.299,1.37),(.3,-.33,.875)],
'A06':[C,(0,-3.9,1.1),(0,0,1.1)],
'A07':[(-.84,-.28,1.65),(.84,-.28,1.65),(0,.24,1.12)],
'A08':[(-1.45,-1.16,.805),(-1.72,-1.16,.823),(-1.76,-.83,.81),(-1.1,-.83,.81)],
'A09':[(-1.24,-.002,.87),(-1.24,.5,.87),(-1.24,.045,1.12)],
'A10':[(1.31,-1.137,.97),(1.31,-1.137,.97),(0,0,1.1)],
'A11':[(1.48,.23,1.10),(1.245,.231,1.045),(1.245,.231,.945),(1.715,.231,.945)],
'A12':[(-1.05,.965,1.15),(-.55,.965,1.15),(.45,.965,1.15)]}
for a in req['assets']:
 for n,loc in zip(a['required_semantic_anchors'],positions[a['id']]):empty('ANCHOR.'+a['id']+'.'+n,loc,a['id'])
contract=json.load(open(P/'operation_binding_contract.json'))
for r in contract['operations']:
 for role in ['primary','control']:
  target=bpy.data.objects[r[role+'_target']];empty(r[role+'_anchor'],target.matrix_world.translation,r['primary_asset_id'],'operation_'+role,target.name)

roots['A12'].location.z=.7

# Render studio and original dimension-agnostic floor.
cube('Studio.floor',(0,-1.65,-.045),(5.15,6.5,.09),None,'Floor.slate',.10)
for x in [-2.1,2.1]:cube('Studio.border'+str(x),(x,-1.6,.006),(.018,5.7,.005),None,'Ceramic.teal')
text('floor.title','CONFORMAL ELASTICITY',(0,-3.04,.01),.22,'A06','Type.white',rot=(0,0,0))
text('floor.subtitle','ORIGINAL STATIC ASSETS  /  NO EXPERIMENT EXECUTED',(0,-3.27,.012),.069,'A06','Accent.amber',rot=(0,0,0))

def area(n,loc,power,size,color):
 da=bpy.data.lights.new(n,'AREA');da.energy=power;da.shape='DISK';da.size=size;da.color=color;o=bpy.data.objects.new(n,da);STU.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,-.8,1))-o.location).to_track_quat('-Z','Y').to_euler()
area('Studio.key',(1,-4,7),1700,5,(.84,.93,1));area('Studio.fill',(-4,-1,4),1100,4,(.76,1,.95));area('Studio.rim',(1,4,5),1500,3,(1,.68,.38))
cameras={}
for nm,pos,target,scale in [('overview',(5,-7.5,6.3),(0,-1.4,1.05),7.9),('specimen',(0,-.22,1.101),(0,0,1.101),.45),('stations',(4,-5,4.1),(-.1,.03,1.35),4.6)]:
 da=bpy.data.cameras.new('Render.'+nm);da.type='ORTHO';da.ortho_scale=scale;da.lens=50;o=bpy.data.objects.new('Render.'+nm,da);STU.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();cameras[nm]=o
# Frame every asset with a pixel margin; exclude the distant camera role in station detail.
bpy.context.view_layer.update()
for nm in ['overview','stations']:
 cam=cameras[nm];inv=cam.matrix_world.inverted();pts=[]
 for ob in COL.objects:
  if ob.type=='MESH' and (nm=='overview' or ob.get('asset_id')!='A06'):
   pts.extend(inv@(ob.matrix_world@Vector(c)) for c in ob.bound_box)
 minx,maxx=min(p.x for p in pts),max(p.x for p in pts);miny,maxy=min(p.y for p in pts),max(p.y for p in pts)
 cam.location+=cam.rotation_euler.to_quaternion()@Vector(((minx+maxx)/2,(miny+maxy)/2,0));cam.data.ortho_scale=max(maxx-minx,(maxy-miny)*1.6)*1.08
sc.camera=cameras['overview'];sc['scientific_simulation']=False;sc['physical_execution_enabled']=False;sc['render_kind']='original static Cycles CPU';sc.render.filepath='//evidence/overview.png'
bpy.context.view_layer.update()
# Record static object bounds after evaluated transforms.
assets=[]
for a in req['assets']:
 obs=[o for o in COL.objects if o.get('asset_id')==a['id']];meshes=[o for o in obs if o.type=='MESH']
 assets.append({**a,'root':'ASSET.'+a['id'],'mesh_count':len(meshes),'object_count':len(obs),'objects':[{'name':o.name,'type':o.type,'position_m':list(o.matrix_world.translation),'dimensions_m':list(o.dimensions),'geometry_class':o.get('geometry_class','authored_display')} for o in obs]})
(P/'asset_inventory.json').write_text(json.dumps({'units':'m','assets':assets},indent=2)+'\n')
anchors=[{'name':o.name,'owner':o.get('asset_id'),'position_m':list(o.matrix_world.translation),'target_mesh':o.get('target_mesh'),'qualified_pose':False,'physical_execution_enabled':False} for o in COL.objects if o.type=='EMPTY' and o.name.startswith('ANCHOR.')]
(P/'affordances.json').write_text(json.dumps({'semantic_only':True,'anchors':anchors},indent=2)+'\n')
(P/'materials'/'materials.json').write_text(json.dumps({'scope':'Illustrative PBR colors only; no measured elastic or optical parameters','materials':[{'name':m.name,'rgba':list(m.diffuse_color)} for m in mats.values()]},indent=2)+'\n')
# Only original asset collection exported. Studio is omitted from portable scene.
bpy.ops.object.select_all(action='DESELECT')
for o in COL.objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(P/'geometry'/'conformal_lab.glb'),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_animations=False,export_cameras=False,export_lights=False)
for scr in bpy.data.screens:
 for ar in scr.areas:
  for sp in ar.spaces:
   if sp.type=='FILE_BROWSER' and sp.params:
    sp.params.directory=b' '*1000;sp.params.directory=b'//'
    sp.params.filename=' '*200;sp.params.filename=''
bpy.ops.wm.save_as_mainfile(filepath=str(P/'geometry'/'conformal_lab.blend'),compress=True)
if not NORENDER:
 out=[]
 for nm,cam in cameras.items():
  sc.camera=cam;sc.render.filepath=str(P/'evidence'/(nm+'.png'));start=time.time();bpy.ops.render.render(write_still=True);out.append({'file':'evidence/'+nm+'.png','camera':cam.name,'engine':'CYCLES','device':'CPU','samples':sc.cycles.samples,'resolution':[1600,1000],'seconds':round(time.time()-start,3),'sha256':hashlib.sha256((P/'evidence'/(nm+'.png')).read_bytes()).hexdigest()})
 (P/'review'/'render_receipt.json').write_text(json.dumps({'status':'rendered','source':'original_blender_geometry','renders':out,'no_image_generation_or_source_images':True},indent=2)+'\n')
 sc.camera=cameras['overview'];sc.render.filepath='//evidence/overview.png';bpy.ops.wm.save_as_mainfile(filepath=str(P/'geometry'/'conformal_lab.blend'),compress=True)
print('ORIGINAL_SCENE_COMPLETE',len(COL.objects),'objects')
