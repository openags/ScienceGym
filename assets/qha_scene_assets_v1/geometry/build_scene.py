"""Original procedural illustration; disabled service interfaces, no scientific solver."""
import bpy, math, json, pathlib, time
from mathutils import Vector
P=pathlib.Path(__file__).resolve().parents[1]
C=json.loads((P/'shared_binding_contract.json').read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for d in bpy.data.materials: bpy.data.materials.remove(d)
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene['asset_package']='qha_scene_assets_v1';scene['physical_actuation_enabled']=False
scene['scientific_simulation_performed']=False;scene['geometry']='Original illustrative unqualified geometry'
scene['source_doi']='10.1038/s41467-022-34680-0'
M={}
def mat(n,c,metal=0,rough=.42):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough;M[n]=m;return m
for args in [('ink',(.023,.043,.061)),('floor',(.64,.70,.72)),('white',(.89,.94,.94)),('steel',(.32,.45,.49),.65),('dark',(.06,.13,.17)),('teal',(.015,.49,.51)),('cyan',(.10,.78,.79)),('amber',(.96,.46,.08)),('pale',(.69,.84,.84)),('gold',(.78,.52,.16),.55),('violet',(.39,.29,.61)),('red',(.64,.12,.17)),('chip',(.025,.07,.07),.4)]:mat(*args)
roots={}
for a in C['assets']:
 o=bpy.data.objects.new(a['asset_id'],None);scene.collection.objects.link(o);o['asset_id']=a['asset_id'];o['geometry_status']='original_illustrative_unqualified';o['physical_actuation_enabled']=False;o['routes']=','.join(a['route_ids']);roots[a['asset_id']]=o

def own(o,g):
 if g:o.parent=roots[g];o['asset_id']=g
 o['physical_actuation_enabled']=False;return o

def box(n,loc,dim,m='white',g=None,bev=.035):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(M[m])
 if bev:
  b=o.modifiers.new('soft edges','BEVEL');b.width=bev;b.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=b.name)
 own(o,g);return o

def cyl(n,loc,r,depth,m='steel',g=None,vertices=48):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc);o=bpy.context.object;o.name=n;o.data.materials.append(M[m]);own(o,g)
 for p in o.data.polygons:p.use_smooth=True
 return o

def line(n,a,b,r=.025,m='teal',g=None):
 a=Vector(a);b=Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,g,16);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def text(n,s,loc,size=.18,m='ink',g=None,flat=False,align='LEFT'):
 cu=bpy.data.curves.new(n,'FONT');cu.body=s;cu.size=size;cu.extrude=.0006;cu.resolution_u=2;cu.align_x=align
 o=bpy.data.objects.new(n,cu);scene.collection.objects.link(o);o.location=loc
 if not flat:o.rotation_euler=(math.pi/2,0,0)
 o.data.materials.append(M[m]);own(o,g);return o

def plaque(n,title,sub,loc,w,g,accent='teal'):
 x,y,z=loc;box(n+'_back',(x,y,z),(w,.065,.65),'dark',g)
 box(n+'_stripe',(x-w/2+.045,y-.041,z),(.055,.012,.52),accent,g,.003)
 text(n+'_title',title,(x-w/2+.13,y-.044,z+.09),.18,'white',g)
 text(n+'_sub',sub,(x-w/2+.13,y-.045,z-.15),.105,'cyan' if accent=='teal' else 'amber',g)

def bench(n,x,y,w=2.6,d=1.7,g=None):
 box(n+'_top',(x,y,.93),(w,d,.13),'white',g)
 for dx in [-w/2+.17,w/2-.17]:
  for dy in [-d/2+.17,d/2-.17]:box(n+'_leg',(x+dx,y+dy,.46),(.12,.12,.9),'steel',g,.015)
 box(n+'_shelf',(x,y,.3),(w-.2,d-.2,.08),'dark',g)

def anchor(n,loc):
 a=n.split('.')[0];o=bpy.data.objects.new(n,None);scene.collection.objects.link(o);o.location=loc;o.empty_display_type='PLAIN_AXES';o.empty_display_size=.12;own(o,a);o['anchor_id']=n;o['mode']='evidence_only';o['qualified']=False
# Environment, deliberate grid / lab zoning
box('design_floor',(0,.1,-.13),(15.8,10.6,.25),'floor',bev=.12)
box('backdrop',(0,5.0,1.45),(15.8,.12,3.1),'pale',bev=.02)
text('title','GRAPHENE / QUANTUM HALL ARRAYS',(-7.1,4.91,2.55),.38,'ink')
text('subtitle','ORIGINAL SERVICE-BOUNDARY SCENE  /  DESIGN REVIEW ONLY',(-7.05,4.90,2.13),.17,'teal')
text('footer','ILLUSTRATIVE GEOMETRY  |  NO HARDWARE CONTROL  |  NO MEASURED TELEMETRY',(-7.05,-4.75,.015),.21,'ink',flat=True)
# AS01 protected intake carrier
bench('intake',-5.35,-.75,g='AS01')
box('AS01.intake_nest',(-5.35,-.75,1.05),(1.22,.94,.12),'dark','AS01')
for dx in [-.58,.58]:box('AS01.nest_guide',(-5.35+dx,-.75,1.18),(.07,1.0,.2),'teal','AS01',.01)
box('AS01.carrier_body',(-5.35,-.75,1.16),(.97,.72,.14),'steel','AS01')
box('AS01.sealed_lid',(-5.35,-.75,1.27),(.97,.72,.08),'white','AS01')
box('AS01.identity_plate',(-5.35,-.75,1.319),(.67,.35,.015),'teal','AS01',.002)
text('AS01.identity_text','CHIP 01 / SEALED',(-5.66,-.84,1.33),.073,'white','AS01',True)
for dx in [-.61,.61]:box('AS01.protected_handle',(-5.35+dx,-.75,1.16),(.2,.33,.11),'gold','AS01')
plaque('intake_label','01 / PROTECTED INTAKE','CARRIER ID + SUPPORT + CUSTODY',(-5.35,-1.65,1.05),2.75,'AS01')
# AS02 one physical 7 mm chip inside closed carrier, separate enlarged explanation
chip=box('AS02.physical_chip',(-5.35,-.75,1.218),(.007,.007,.0005),'chip','AS02',0);chip['physical_sample_id']='CHIP-01';chip['source_xy_m']='0.007,0.007';chip['thickness_is_illustrative']=True
bench('identity',-1.0,-.7,3.45,2.1,'AS02')
box('AS02.explanation_back',(-1.0,-.5,1.06),(2.9,1.9,.12),'dark','AS02')
text('AS02.explain_heading','ONE CHIP  /  7 x 7 mm SOURCE',(-2.35,.19,1.132),.16,'white','AS02',True)
text('AS02.explain_scale','ENLARGED LOGICAL MAP  /  NOT FABRICATION CAD',(-2.35,-.04,1.133),.095,'cyan','AS02',True)
for x,idx in [(-1.88,1),(-.91,2)]:
 box(f'AS02.array{idx}_tile',(x,-.63,1.16),(.83,.78,.07),'teal' if idx==1 else 'violet','AS02',.02)
 for i in range(4):
  for j in range(3):cyl(f'AS02.array{idx}_symbol_{i}_{j}',(x-.27+i*.18,-.80+j*.18,1.204),.048,.012,'gold','AS02',16)
 text(f'AS02.array{idx}_title',f'ARRAY {idx}',(x-.30,-1.14,1.134),.13,'white','AS02',True)
 text(f'AS02.array{idx}_count','118 PARALLEL',(x-.30,-1.34,1.134),.105,'cyan','AS02',True)
box('AS02.hall_bar_symbol',(.04,-.61,1.18),(.16,.65,.07),'gold','AS02',.01)
for y in [-.80,-.42]:box('AS02.hall_bar_contact',(.04,y,1.184),(.48,.08,.07),'gold','AS02',.005)
text('AS02.hb_text','HB',(-.1,-1.11,1.134),.15,'white','AS02',True)
text('AS02.shared_identity','ONE PHYSICAL CHIP / SYMBOLS DO NOT COUNT ELEMENTS',(-2.77,.472,1.40),.091,'white','AS02')
plaque('map_label','02 / CHIP IDENTITY','CLOSED CARRIER ONLY / NO BARE-CHIP GRASP',(-1,-1.83,1.03),3.45,'AS02')
# AS03 upright topology board, original blocks no copied source diagram
box('AS03.topology_board',(-1.15,.56,2.02),(3.55,.11,1.45),'dark','AS03')
text('AS03.topology_title','TOPOLOGY / SOURCE CONTEXT',(-2.78,.491,2.59),.16,'white','AS03')
for x,n,m in [(-2.02,'A1','teal'),(-.31,'A2','violet')]:
 box('AS03.block_'+n,(x,.479,2.2),(1.30,.035,.38),m,'AS03')
 text('AS03.label_'+n,n+'  |  118 parallel',(x-.58,.452,2.16),.13,'white','AS03')
 text('AS03.resistance_'+n,'R_K/236 ~ 109 ohm',(x-.63,.472,1.87),.12,'cyan','AS03')
line('AS03.series_link',(-1.35,.453,2.2),(-.98,.453,2.2),.018,'gold','AS03')
text('AS03.whole_text','SERIES WHOLE  /  236 TOTAL  /  R_K/118 ~ 219 ohm',(-2.77,.473,1.58),.107,'white','AS03')
# AS04 completely closed preparation boundary
box('AS04.preparation_enclosure',(-5.6,2.8,1.20),(2.25,1.55,2.35),'white','AS04',.08)
box('AS04.closed_door',(-5.6,1.991,1.34),(1.94,.045,1.78),'dark','AS04')
box('AS04.receipt_slot',(-5.6,1.951,1.0),(1.25,.04,.26),'teal','AS04')
text('AS04.slot_text','RECEIPTS ONLY',(-6.10,1.921,.97),.125,'white','AS04')
plaque('preparation_label','03 / PREPARATION SERVICE','SEALED / QUALIFIED PROVIDER',(-5.6,1.93,2.20),2.4,'AS04',accent='amber')
text('AS04.no_recipe','NO PROCESS CONTROLS',(-6.39,1.92,.61),.126,'amber','AS04')
# AS05 closed cryostat with explicit closed nonoperating status and illustrative envelope
for x in [-3.12,.12]:box('AS05.zone_edge',(x,3.05,.016),(.06,3.18,.025),'amber','AS05',.005)
for y in [1.47,4.63]:box('AS05.zone_edge',(-1.5,y,.016),(3.3,.06,.025),'amber','AS05',.005)
for x in [-3.10,.10]:
 for y in [1.48,4.60]:
  cyl('AS05.zone_bollard',(x,y,.38),.065,.76,'amber','AS05',24)
  cyl('AS05.zone_bollard_cap',(x,y,.77),.085,.04,'dark','AS05',24)
cyl('AS05.closed_cryostat',(-1.5,3.05,1.20),.87,2.22,'steel','AS05')
cyl('AS05.bottom_ring',(-1.5,3.05,.22),.94,.18,'dark','AS05')
cyl('AS05.top_cap',(-1.5,3.05,2.33),.98,.13,'white','AS05')
cyl('AS05.top_lock',(-1.5,3.05,2.51),.37,.23,'dark','AS05')
box('AS05.service_face',(-1.5,2.175,1.65),(1.23,.08,.67),'dark','AS05')
text('AS05.lock_label','LOCKED',(-1.93,2.128,1.71),.20,'amber','AS05')
text('AS05.lock_sub','NO ACTUATION',(-1.95,2.123,1.47),.12,'white','AS05')
box('AS05.room_temperature_handoff',(-3.63,1.16,.92),(.7,.66,.1),'white','AS05')
box('AS05.handoff_support',(-3.63,1.16,.44),(.14,.14,.88),'steel','AS05')
plaque('cryostat_label','04 / CRYO + FIELD SERVICE','ZONE ILLUSTRATIVE / ACCESS UNQUALIFIED',(-1.5,1.39,.67),3.20,'AS05',accent='amber')
# AS06 closed logical instrument front panels, evidence slots only
bench('precision',2.05,3.1,2.8,1.85,'AS06')
for z,lab,n in [(1.26,'CHARACTERIZATION','char'),(1.86,'PRECISION CCC','ccc')]:
 box('AS06.'+n+'_cabinet',(2.05,3.1,z),(2.30,1.15,.52),'white','AS06')
 box('AS06.'+n+'_face',(2.05,2.502,z),(2.09,.035,.36),'dark','AS06')
 text('AS06.'+n+'_label',lab,(1.10,2.477,z+.025),.14,'white','AS06')
 text('AS06.'+n+'_state','RECEIPT MISSING / HOLD',(1.10,2.473,z-.125),.092,'amber','AS06')
plaque('precision_label','05 / ELECTRICAL SERVICES','NO LIVE VALUES / SHARED LEASE', (2.05,2.11,.83),2.8,'AS06')
# AS07 & AS08 separate baths
for aid,x,ref,title,bath,col in [('AS07',2.6,'100 ohm','OIL REFERENCE','OIL BATH','teal'),('AS08',5.3,'12.9 kohm','AIR REFERENCE','AIR BATH','violet')]:
 bench(aid+'_bench',x,-.55,2.20,1.65,aid)
 box(aid+'.closed_reference_enclosure',(x,-.45,1.43),(1.75,1.17,.84),'white',aid,.065)
 box(aid+'.sealed_lid',(x,-.45,1.885),(1.83,1.25,.10),col,aid)
 box(aid+'.reference_plate',(x,-1.055,1.46),(1.57,.035,.53),'dark',aid)
 text(aid+'.resistor_value',ref,(x-.66,-1.081,1.53),.23,'white',aid)
 text(aid+'.bath_label',bath+' / CLOSED',(x-.67,-1.08,1.29),.108,'cyan' if aid=='AS07' else 'white',aid)
 plaque(aid+'_station',('06' if aid=='AS07' else '07')+' / '+title,'ID + CALIBRATION + LOAD EVIDENCE',(x,-1.45,.91),2.28,aid)
# AS09 evidence board, blank measured fields and explicit unresolved equations
box('AS09.review_panel',(5.43,3.45,1.75),(2.92,.17,2.90),'dark','AS09')
text('AS09.heading','08 / EVIDENCE REVIEW',(4.12,3.351,3.00),.195,'white','AS09')
for i,(label,color) in enumerate([('RAW DATA: NOT ACQUIRED','amber'),('MEASURED VALUES: NONE','white'),('Eq 3 / Eq 4: QUALIFICATION HOLD','amber'),('SI LOOP EXPANSION: HOLD','amber'),('SOURCE != NEW OBSERVATION','cyan'),('NO PAPER-MATCH REWARD','white')]):text('AS09.line'+str(i),label,(4.13,3.345,2.66-i*.24),.113,color,'AS09')
text('AS09.net_heading','CONNECTIVITY / SIGN MAPPING HELD',(4.13,3.345,1.16),.105,'white','AS09')
net={'A1':(4.63,3.323,.95),'A2':(6.05,3.323,.95),'HB':(4.63,3.323,.53),'100':(6.05,3.323,.53)}
for k,(x,y,z) in net.items():
 box('AS09.network_node_'+k,(x,y-.025,z),(.51,.026,.21),'teal' if k!='100' else 'violet','AS09',.012)
 text('AS09.network_label_'+k,k,(x-.17,y-.046,z-.045),.11,'white','AS09')
for a,b in [('A1','A2'),('A1','HB'),('A1','100'),('A2','100'),('HB','100')]:line('AS09.network_edge_'+a+'_'+b,net[a],net[b],.012,'gold','AS09')
# AS10 quarantine support designed to remain amber until evidence
box('AS10.return_platform',(-5.30,-3.50,.45),(2.85,1.4,.84),'white','AS10')
box('AS10.supported_quarantine_nest',(-5.3,-3.5,.94),(1.43,.91,.12),'dark','AS10')
for x in [-5.95,-4.65]:box('AS10.nest_rail',(x,-3.5,1.05),(.075,.9,.18),'amber','AS10')
plaque('return_label','09 / RETURN + QUARANTINE','SAFE RECEIPT + RECEIVER ACCEPTANCE',(-5.3,-4.24,.65),2.93,'AS10',accent='amber')
# AS11 passive mobile robot + protected handling datum and transport envelope
for a,b in [((-.2,-3.45,.03),(-2.8,-3.45,.03)),((-2.8,-3.45,.03),(-2.8,.84,.03)),((-2.8,.84,.03),(-3.65,.84,.03))]:line('AS11.illustrative_route',a,b,.033,'teal','AS11')
text('AS11.route_warning','UNQUALIFIED PATH',(-2.56,-2.44,.035),.15,'teal','AS11',True)
box('AS11.robot_base',(.10,-3.4,.27),(1.55,1.15,.40),'dark','AS11',.14)
box('AS11.robot_shell',(.10,-3.4,.5),(1.35,1.0,.18),'white','AS11',.10)
for x in [-.63,.83]:
 for y in [-3.77,-3.03]:
  o=cyl('AS11.robot_wheel',(x,y,.21),.21,.12,'ink','AS11',32);o.rotation_euler[1]=math.pi/2
cyl('AS11.robot_pedestal',(.10,-3.4,.82),.19,.57,'steel','AS11')
line('AS11.robot_upperarm',(.10,-3.4,1.11),(.35,-3.3,1.72),.105,'white','AS11')
line('AS11.robot_forearm',(.35,-3.3,1.72),(-.35,-3.08,1.75),.085,'white','AS11')
for v in [(.10,-3.4,1.11),(.35,-3.3,1.72),(-.35,-3.08,1.75)]:cyl('AS11.passive_joint',v,.13,.17,'teal','AS11',24)
for dx in [-.10,.10]:box('AS11.carrier_gripper_finger',(-.47+dx,-3.08,1.59),(.05,.22,.22),'gold','AS11',.009)
text('AS11.robot_label','PASSIVE ROBOT / NO CONTROL',(-.64,-4.04,.66),.12,'white','AS11')
# Evidence anchors: all exact contract names exported as empties
locs={
'AS01':[(-5.35,-.75,1.32),(-5.35,-.75,1.05),(-5.35,-1.65,1.05)],
'AS02':[(-5.35,-.75,1.218),(-1.88,-.63,1.20),(-.91,-.63,1.20),(.04,-.61,1.20)],
'AS03':[(-2.02,.45,2.20),(-1.15,.45,1.58),(-2.35,.19,1.13)],
'AS04':[(-5.6,1.92,1.0),(-5.6,1.92,.70)],
'AS05':[(-1.5,1.47,.05),(-3.63,1.16,.97),(-1.5,2.12,1.48)],
'AS06':[(2.05,2.47,1.26),(2.05,2.47,1.86),(2.05,2.11,.83)],
'AS07':[(2.6,-1.08,1.53),(2.6,-1.08,1.29)],
'AS08':[(5.3,-1.08,1.53),(5.3,-1.08,1.29)],
'AS09':[(4.24,3.34,2.76),(4.24,3.34,2.36),(4.24,3.34,1.82),(4.24,3.34,.63)],
'AS10':[(-5.3,-3.5,1.0),(-5.3,-4.24,.65),(-5.3,-4.24,.45)],
'AS11':[(-.47,-3.08,1.59),(-2.8,-1.3,.04),(.1,-3.4,.27)]}
for a in C['assets']:
 for k,xyz in zip(a['anchors'],locs[a['asset_id']]):anchor(k['anchor_id'],xyz)
# Add descriptive metadata to every mesh; remove unused data before export.
for o in bpy.data.objects:
 if o.type=='MESH':o['geometry_basis']='original_illustrative' if o.name!='AS02.physical_chip' else 'source_xy_illustrative_thickness'
# Soft studio illumination, CPU Cycles only.
scene.world.color=(.3,.3,.3);scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.64,.68,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.6
for n,loc,power,size in [('key',(1,-5,11),2300,8),('fill',(-8,-1,7),1600,7),('rim',(4,6,8),1800,6)]:
 data=bpy.data.lights.new(n,'AREA');data.energy=power;data.shape='DISK';data.size=size;o=bpy.data.objects.new(n,data);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=64;scene.cycles.use_denoising=False
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.render.film_transparent=False
cams={
'overview':((14,-20,18),(-.1,.2,1.0),20.2,(1800,1200)),
'specimen':((-.9,-7.4,6.2),(-1.2,-.40,1.35),5.2,(1600,1200)),
'services':((9,-11,9),(1.0,2.2,1.15),11.6,(1800,1200))}
for n,(pos,target,scale,res) in cams.items():
 d=bpy.data.cameras.new(n);d.type='ORTHO';d.ortho_scale=scale;o=bpy.data.objects.new('Camera_'+n,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
scene.camera=bpy.data.objects['Camera_overview'];scene.render.resolution_x=1800;scene.render.resolution_y=1200
scene.render.filepath='//../previews/preview_01_overview.png'
for screen in bpy.data.screens:
 for area in screen.areas:
  for space in area.spaces:
   if space.type=='FILE_BROWSER' and space.params:space.params.directory=b'//'
# Native remains editable text; GLB exports converted evaluated text meshes.
bpy.ops.wm.save_as_mainfile(filepath=str(P/'geometry/qha_lab.blend'),compress=True)
# Duplicate text conversion in-memory after native save.
for o in list(bpy.data.objects):
 if o.type=='FONT':bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
bpy.ops.export_scene.gltf(filepath=str(P/'geometry/qha_lab.glb'),export_format='GLB',export_extras=True,export_cameras=True,export_lights=False,export_yup=True)
manifest={'schema':'sciencegym3d.scene.v1','source_doi':C['source_doi'],'asset_package':C['asset_package'],'physical_actuation_enabled':False,'objects':[{'name':o.name,'type':o.type,'asset_id':o.get('asset_id'),'anchor_id':o.get('anchor_id'),'location_m':list(o.location),'dimensions_m':list(o.dimensions),'parent':o.parent.name if o.parent else None} for o in bpy.data.objects], 'render_device':'CPU','render_engine':'CYCLES'}
(P/'scene_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
receipts=[]
for i,(n,(_,_,_,res)) in enumerate(cams.items(),1):
 scene.camera=bpy.data.objects['Camera_'+n];scene.render.resolution_x=res[0];scene.render.resolution_y=res[1];out=P/'previews'/f'preview_{i:02d}_{n}.png';scene.render.filepath=str(out);t=time.time();bpy.ops.render.render(write_still=True);receipts.append({'file':out.relative_to(P).as_posix(),'camera':scene.camera.name,'resolution':list(res),'engine':'CYCLES','device':'CPU','samples':64,'render_seconds':round(time.time()-t,3),'actual_render':True,'scientific_simulation':False})
(P/'review/render_receipt.json').write_text(json.dumps({'renders':receipts,'no_generated_image_substitution':True},indent=2)+'\n')

exec((P/'sanitize_previews.py').read_text(),{'__file__':str(P/'sanitize_previews.py')})

# This is the last native-file mutation: scrub complete SDNA buffers after saving.
import subprocess,shutil
subprocess.run([shutil.which('python3'),str(P/'geometry/finalize_native_buffers.py')],check=True)
