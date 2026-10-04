"""Original static laboratory roles and source-dimensional varactor references.
All services are disabled metadata proxies. No source/vendor CAD or source pixels.
Rebuild with Blender 4.3 CPU from this directory's parent package.
"""
import bpy, math, json, sys, hashlib, struct
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[1]
PLAN=json.loads((OUT/'task_binding_snapshot.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
MAIN=bpy.context.scene;MAIN.name='VARACTOR_ORIGINAL_LAB_METRIC';sc=MAIN;CUR=None;ROOTS={};ANCHORS=[];TARGETS={}
def setup(s):
 s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
 s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=128;s.cycles.use_denoising=False;s.cycles.seed=17
 s.render.resolution_x=1800;s.render.resolution_y=1200;s.render.resolution_percentage=100
 s.render.image_settings.file_format='PNG';s.render.filepath='//evidence/';s.render.use_stamp=False;s.render.use_stamp_filename=False
 s.world=bpy.data.worlds.new(s.name+'.world');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.38,.45,.50,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.35
 s.view_settings.view_transform='AgX';s.view_settings.exposure=-2.0
setup(sc)
def material(n,c,metal=0,rough=.4):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
M={'navy':material('Petrol / authored apparatus',(.015,.052,.071),.3),'teal':material('Teal / metadata selector',(.024,.37,.35),.25),'crystal':material('STO appearance / no dielectric model',(.55,.69,.72),.05,.3),'kto':material('KTO appearance / no dielectric model',(.44,.55,.69),.05,.3),'cream':material('Ivory / authored case',(.78,.85,.84),.1),'steel':material('Aluminum appearance',(.43,.53,.60),.7),'gold':material('Au appearance only',(.77,.50,.13),.7),'titanium':material('Ti appearance only',(.24,.27,.30),.6),'amber':material('Amber / permanent execution hold',(.97,.43,.035),.1),'black':material('Graphite / disabled screen',(.010,.019,.025),.15),'white':material('White type',(.95,.98,.96)),'cyan':material('Cyan / record role',(.27,.76,.82),.15),'floor':material('Studio neutral',(.60,.67,.72),0,.9),'pcb':material('Generic PCB appearance',(.021,.13,.12),.2)}
def root(aid):
 global CUR
 spec=next(x for x in PLAN['scene_assets'] if x['asset_id']==aid);o=bpy.data.objects.new(aid,None);sc.collection.objects.link(o);o.empty_display_size=.01
 for k,v in {'asset_id':aid,'role':spec['role'],'physical_execution':False,'device_io':False,'energy_enabled':False,'physical_geometry_validated':False,'authored_geometry':True,'display_scale':1,'operation_ids':','.join(spec['bind_operation_ids'])}.items():o[k]=v
 ROOTS[aid]=o;CUR=o;return o
def finish(o,n,m=None):
 o.name=n
 if m:o.data.materials.append(M[m])
 if CUR:o.parent=CUR
 o['geometry_basis']='original_authored';o['physical_geometry_validated']=False;o['device_io']=False;o['energy_enabled']=False
 return o
def box(n,p,d,m='navy',bevel=.003):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.dimensions=d;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(o,n,m)
 if bevel:
  b=o.modifiers.new('Original edge radius','BEVEL');b.width=min(bevel,min(d)/3);b.segments=3;o.modifiers.new('Visual normals','WEIGHTED_NORMAL')
 return o
def cyl(n,p,r,h,m='steel',axis='Z'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=r,depth=h,location=p);o=bpy.context.object
 if axis=='Y':o.rotation_euler.x=math.pi/2
 if axis=='X':o.rotation_euler.y=math.pi/2
 finish(o,n,m)
 for f in o.data.polygons:f.use_smooth=True
 return o
def rod(n,a,b,r=.003,m='steel'):
 o=cyl(n,(Vector(a)+Vector(b))/2,r,(Vector(b)-Vector(a)).length,m);o.rotation_euler=(Vector(b)-Vector(a)).to_track_quat('Z','Y').to_euler();return o
def txt(n,s,p,size=.013,m='white',flat=False):
 c=bpy.data.curves.new(n,'FONT');c.body=s;c.size=size;c.extrude=.000015;c.space_character=1.01;o=bpy.data.objects.new(n,c);sc.collection.objects.link(o);o.location=p
 if not flat:o.rotation_euler=(math.pi/2,0,0)
 return finish(o,n,m)
def label(n,s,p,w=.30,h=.035,size=.011,m='navy'):
 box(n+'.plate',p,(w,.005,h),m,.0015);return txt(n+'.text',s,(p[0]-w*.46,p[1]-.0035,p[2]-.003),size)
def screen(prefix,p,w,h,title,lines):
 x,y,z=p;box(prefix+'.body',(x,y,z),(w,.06,h),'navy',.008);face=box(prefix+'.face',(x,y-.035,z),(w-.019,.009,h-.019),'black',.002)
 txt(prefix+'.title',title,(x-w*.44,y-.041,z+h*.31),w*.041,'cyan')
 for i,(s,col) in enumerate(lines):txt(prefix+'.line.'+str(i),s,(x-w*.44,y-.041,z+h*.08-i*h*.19),w*.032,col)
 return face
# Target objects are real static geometry; anchors will be matched to canonical task IDs.
def targets(default,**named):TARGETS[CUR.name]={'default':default,**named}
def camera(n,p,target,scale):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);sc.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=scale;d.clip_start=.0000001;d.clip_end=100;return o
def light(n,p,energy,size,target):
 d=bpy.data.lights.new(n,'AREA');d.energy=energy;d.shape='DISK';d.size=size;o=bpy.data.objects.new(n,d);sc.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def proxy(prefix,p,d,title,subtitle):
 x,y,z=p;w,dep,h=d;body=box(prefix+'.enclosure',p,d,'cream',.008);door=box(prefix+'.closed_door',(x,y-dep/2-.005,z),(w-.028,.012,h-.034),'navy',.003);door['closed']=True;door['service_qualified']=False
 txt(prefix+'.title',title,(x-w*.43,y-dep/2-.013,z+h*.27),w*.046)
 txt(prefix+'.status','CLOSED / DISABLED',(x-w*.43,y-dep/2-.013,z+h*.03),w*.041,'amber')
 txt(prefix+'.subtitle',subtitle,(x-w*.43,y-dep/2-.013,z-h*.22),w*.030,'cyan')
 for dx in [-w*.38,w*.38]:cyl(prefix+'.fastener',(x+dx,y-dep/2-.015,z-h*.36),.005,.006,'steel','Y')
 return door
# The workbench and every equipment housing are authored at room scale.
root('A_DESIGN_CONSOLE')
box('bench.base',(0,0,.075),(2.56,1.40,.12),'cream',.022);box('bench.top',(0,0,.146),(2.54,1.38,.022),'steel',.005)
for x in [-1.13,1.13]:
 for y in [-.55,.55]:cyl('bench.foot',(x,y,.023),.045,.045,'black')
label('bench.title','QUANTUM PARAELECTRIC VARACTORS / ORIGINAL STATIC LAB ROLES',(0,-.714,.076),2.46,.055,.025)
face=screen('design',(-1.005,.47,.382),.385,.385,'DESIGN / SOURCE',[('DOI 10.1038 / 01214-z','white'),('GEOMETRY: REFERENCE','white'),('SOURCE CONFLICTS: HOLD','amber')]);targets(face,design=face,source=face,geometry=face)
root('A_CRYSTAL_CARRIER')
base=box('carrier.base',(-.90,-.345,.197),(.63,.49,.08),'navy',.009);tray=box('carrier.recess',(-.90,-.345,.243),(.535,.38,.025),'black',.004)
for x in [-1.223,-.577]:box('carrier.grasp_tab',(x,-.345,.245),(.057,.12,.032),'steel',.003)
# Reference holders are original, not source sample-holder CAD.
for prefix,x,m in [('sto',-1.045,'crystal'),('kto',-.76,'kto')]:
 box('holder.'+prefix+'.base',(x,-.345,.269),(.236,.28,.026),'teal',.004)
 box('holder.'+prefix+'.well',(x,-.32,.286),(.185,.20,.010),'cream',.002)
 box('holder.'+prefix+'.datum',(x,-.32,.294),(.06,.06,.006),'navy',.001)
 txt('holder.'+prefix+'.identity',prefix.upper()+' / ID HOLD',(x-.103,-.446,.287),.018,'white',True)
# Exact micrometre/nanometre reference solids. Layer planar shape and locations original.
def device(prefix,center,S=1,material_key='crystal',pads=True):
 x,y,z=center
 s=box(prefix+'.substrate',(x,y,z+.00025*S),(.003*S,.003*S,.0005*S),material_key,0);s['source_dimensions_m']=[.003,.003,.0005];s['display_scale']=S;s['source_anchor']='Methods, varactor fabrication';s['full_device_reconstruction']=False
 box(prefix+'.back_ti',(x,y,z-.0000000025*S),(.003*S,.003*S,.000000005*S),'titanium',0)
 box(prefix+'.back_au',(x,y,z-.000000035*S),(.003*S,.003*S,.000000060*S),'gold',0)
 if pads:
  for i,dx in enumerate([-.001,.001]):
   for key,t,zoff,mat in [('ti',5e-9,2.5e-9,'titanium'),('au',60e-9,35e-9,'gold')]:
    o=box(prefix+'.pad'+str(i)+'.'+key,(x+dx*S,y,z+(.0005+zoff)*S),(.00012*S,.00012*S,t*S),mat,0);o['display_scale']=S;o['source_dimensions_m']=[.00012,.00012,t];o['pair_spacing_m']=.002;o['spacing_status']='about 2 mm in source; model uses 2 mm reference';o['source_anchor']='Methods, varactor fabrication'
 return s
sto=device('native.sto',(-1.045,-.32,.2971));kto=device('native.kto',(-.76,-.32,.2971),material_key='kto',pads=False)
label('carrier.label','NATIVE 3 mm CRYSTALS / ID + FIT UNQUALIFIED',(-.90,-.598,.200),.63,.037,.014)
targets(tray,sto=sto,kto=kto,sample=sto,identity=bpy.data.objects['holder.sto.identity'],ancestry=bpy.data.objects['holder.sto.identity'],grasp_left=bpy.data.objects['carrier.grasp_tab'],grasp_right=bpy.data.objects['carrier.grasp_tab.001'],carrier=tray)
root('A_CLEANROOM_SERVICE')
f=proxy('cleanroom',(-.57,.46,.305),(.38,.31,.29),'LITHOGRAPHY SERVICE','EXTERNAL QUALIFIED RECEIPT');targets(f)
root('A_NANOTUBE_SERVICE')
f=proxy('nanotube',(-.13,.46,.305),(.38,.31,.29),'CNT / AFM SERVICE','GROWTH + CONTACTS ON HOLD');targets(f)
root('A_ASSEMBLY_SERVICE')
f=proxy('assembly',(-.20,-.345,.286),(.61,.48,.24),'ASSEMBLY / SAMPLE EXCHANGE','BONDING + ANNEALING DISABLED')
box('assembly.receipt_slot',(-.20,-.593,.226),(.25,.008,.016),'black',.001)
box('assembly.closed_lid',(-.20,-.345,.414),(.59,.46,.02),'navy',.004)
for x in [-.444,.044]:cyl('assembly.latch',(x,-.345,.430),.013,.012,'amber')
txt('assembly.access_label','CLOSED ACCESS / NO SAMPLE TRANSFER',(-.469,-.367,.428),.015,'white',True)
targets(f,board_reference=bpy.data.objects['assembly.closed_lid'],bond_record=bpy.data.objects['assembly.receipt_slot'],sample_in=f,sample_out=f,access=bpy.data.objects['assembly.closed_lid'],receipt=bpy.data.objects['assembly.receipt_slot'])
root('A_CIRCUIT_MODULE')
case=box('circuit.case',(.48,-.345,.215),(.62,.49,.11),'navy',.01)
box('circuit.closed_cover',(.48,-.345,.280),(.60,.47,.02),'cream',.004)
# Authored functional modules are isolated reference blocks, not a wiring diagram.
mods={}
for title,x,y,col in [('Cm',.28,-.22,'gold'),('Cf',.48,-.22,'gold'),('L',.68,-.22,'steel'),('SOURCE',.31,-.43,'teal'),('DRAIN',.65,-.43,'teal')]:
 n='circuit.module.'+title;mods[title]=box(n,(x,y,.316),(.142,.125,.048),col,.003);txt(n+'.label',title,(x-.061,y-.017,.342),.018,'navy' if col!='teal' else 'white',True)
for x in [.23,.73]:
 cyl('circuit.capped_port',(x,-.596,.226),.021,.025,'steel','Y');cyl('circuit.cap',(x,-.614,.226),.017,.012,'black','Y')
mods['DRAIN']['branch_scope']='SQD only; DQD has a single source electrode';mods['SOURCE']['branch_scope']='device reference role, separate SQD/DQD lineages'
label('circuit.branch_card','FIXED LOAD | SQD | DQD: 20 pF + JPA',(.48,-.114,.374),.60,.046,.018)
label('circuit.label','RF MODULE ROLES / PORTS CAPPED / NO NETLIST',(.48,-.599,.186),.62,.032,.0125)
targets(case,rf_port=bpy.data.objects['circuit.cap'],dc_port_map=bpy.data.objects['circuit.cap.001'],circuit_card=bpy.data.objects['circuit.branch_card.plate'],mount_record=bpy.data.objects['circuit.closed_cover'],source=mods['SOURCE'],drain=mods['DRAIN'],matching=mods['Cm'],frequency=mods['Cf'],inductor=mods['L'],circuit=case)
root('A_CRYOSTAT_SERVICE')
x,y=.50,.37
cyl('cryo.base',(x,y,.190),.224,.065,'navy');body=cyl('cryo.closed_vessel',(x,y,.490),.202,.55,'steel');body['closed']=True
for z in [.247,.695]:cyl('cryo.band',(x,y,z),.207,.033,'navy')
cyl('cryo.closed_top',(x,y,.785),.217,.04,'cream')
for a in range(0,360,45):
 rad=math.radians(a);cyl('cryo.bolt',(x+.18*math.cos(rad),y+.18*math.sin(rad),.814),.009,.019,'steel')
for dx in [-.08,.08]:
 cyl('cryo.top_capped_port',(x+dx,y,.84),.018,.05,'steel');cyl('cryo.top_cap',(x+dx,y,.868),.022,.016,'black')
label('cryo.label','CRYOSTAT / CLOSED',(x,y-.212,.525),.335,.07,.022)
label('cryo.state','NO COOLING / NO VACUUM',(x,y-.212,.434),.335,.043,.016,'amber')
dock=box('cryo.exchange_dock',(x,y-.25,.269),(.26,.12,.065),'navy',.005);box('cryo.exchange_cap',(x,y-.318,.27),(.20,.014,.043),'cream',.003)
label('cryo.dock_label','SEALED EXCHANGE',(x,y-.328,.27),.22,.032,.011)
targets(body,module_in=dock,module_out=dock,sample=dock,dock=dock,exchange=dock,closed=body,thermal=body,vacuum=body)
root('A_RF_CALIBRATION')
face=screen('rf',(.998,.425,.466),.39,.28,'RF / NETWORK READOUT',[('RF + DC OUTPUTS OFF','amber'),('CALIBRATION: UNVERIFIED','white'),('NO ACQUIRED TRACE','white')]);box('rf.base',(.998,.43,.230),(.415,.33,.14),'cream',.008)
for x in [.86,1.01,1.15]:
 cyl('rf.capped_connector',(x,.255,.24),.019,.022,'steel','Y');cyl('rf.cap',(x,.240,.24),.014,.014,'black','Y')
cal=box('calibration.reference_case',(1.03,-.34,.238),(.31,.47,.16),'cream',.007)
for i,title in enumerate(['OPEN','SHORT','LOAD']):
 cyl('calibration.capped_reference.'+title,(1.03,-.19-i*.12,.34),.035,.028,'steel');txt('calibration.label.'+title,title,(.95,-.202-i*.12,.356),.016,'navy',True)
label('calibration.front','CAL / ID HOLD',(1.03,-.585,.22),.30,.038,.016)
targets(face,calibration=cal,reference=cal,rf=face,readout=face)
root('A_FIELD_SERVICE')
f=proxy('field',(-.58,.038,.283),(.30,.19,.23),'FIELD SERVICE','NO MAGNET / NO RAMP');targets(f)
root('A_ACQUISITION_RECORDS')
record=box('records.archive',(-1.028,.050,.240),(.33,.18,.15),'teal',.006)
for i in range(3):box('records.blank_card',(-1.025,.046,.324+i*.006),(.28,.14,.003),'cream',.0008)
txt('records.card_label','RUN / LINEAGE / RAW FILES',(-1.15,.00,.341),.012,'navy',True)
label('records.label','RECEIPTS ONLY',(-1.028,-.046,.24),.31,.038,.016)
targets(record)
root('A_ANALYSIS_CONSOLE')
face=screen('analysis',(-.08,.62,.710),.48,.23,'ANALYSIS / EXTERNAL RECORDS',[('NO FIT OR SOLVER','amber'),('NO SENSITIVITY CLAIM','white'),('MODEL / DATA: HOLD','white')]);box('analysis.stand',(-.08,.66,.424),(.07,.06,.53),'steel',.003);targets(face)
root('A_HOLD_STORAGE')
box('hold.sign',(0,.732,.936),(2.28,.025,.135),'navy',.008)
txt('hold.title','METADATA ONLY / PERMANENT EXECUTION HOLD',(-1.055,.715,.962),.042,'amber')
txt('hold.detail','ORIGINAL LAB HOUSINGS  |  NO LIVE RF, DC, FIELD, CRYOGENICS OR FABRICATION',(-1.055,.715,.914),.020)
for x in [-1.08,1.08]:rod('hold.sign_support',(x,.735,.16),(x,.735,.867),.010,'steel')
box('hold.storage_case',(.99,.04,.260),(.38,.19,.15),'amber',.006);lid=box('hold.storage_lid',(.99,.04,.345),(.39,.20,.018),'navy',.003)
label('hold.storage_label','SEALED / QUARANTINE',(.99,-.060,.263),.375,.04,.015)
targets(lid,qualification=bpy.data.objects['hold.sign'],source=bpy.data.objects['hold.sign'],calibration=bpy.data.objects['hold.sign'],lineage=bpy.data.objects['hold.sign'])
# Canonical anchors are symbolic selectors on original geometry, never tool poses.
for spec in PLAN['scene_assets']:
 aid=spec['asset_id'];CUR=ROOTS[aid];d=TARGETS[aid]
 for index,a in enumerate(spec['required_anchor_ids']):
  target=d.get(a)
  if target is None:
   key=next((k for k in d if k!='default' and k in a),None);target=d[key] if key else d['default']
  p=target.location.copy();n=aid+'.'+a;o=bpy.data.objects.new(n,None);sc.collection.objects.link(o);o.parent=CUR;o.location=p;o.empty_display_type='ARROWS';o.empty_display_size=.008;o['anchor_id']=a;o['target_object']=target.name;o['coordinate_status']='authored_unqualified';o['physical_execution']=False
  ANCHORS.append({'asset_id':aid,'anchor_id':a,'scene_object':n,'target_object':target.name,'translation_m':list(p),'rotation_quaternion_xyzw':[0,0,0,1],'coordinate_status':'authored_unqualified','physical_qualified_transform':None,'meaning':'Original static metadata target; not calibrated robot pose or physical connection','allowed_tool':'metadata selector only','precondition':'external identity, fit, service and source records independently qualified','postcondition':'local metadata selection only','failure_stop':'missing, stale or conflicting evidence','collision_representation':'none','physical_execution':False})
CUR=None;box('studio.floor',(0,0,-.021),(200,200,.02),'floor',0)
light('LIGHT.key',(-2,-2.4,3.8),1250,2.5,(0,0,.4));light('LIGHT.fill',(2.6,-.8,2.8),850,2.5,(0,0,.4));light('LIGHT.rim',(0,3,3.5),1400,2.0,(0,0,.4))
CAMS={'overview':camera('CAM.overview',(1.9,-4.8,3.40),(0,.06,.48),3.47),'handling':camera('CAM.handling',(-1.2,-3.4,2.8),(-.44,-.35,.27),2.20)}
MAIN.camera=CAMS['overview'];bpy.context.view_layer.update()
assets=[]
for aid,r in ROOTS.items():
 parts=[]
 for o in r.children:
  if o.type in ['MESH','FONT','CURVE']:
   q=o.rotation_euler.to_quaternion();parts.append({'part_id':o.name,'type':o.type,'dimensions_m':list(o.dimensions),'translation_m':list(o.location),'rotation_quaternion_xyzw':[q.x,q.y,q.z,q.w],'scale':list(o.scale),'geometry_basis':'original_authored','physical_geometry_validated':False})
 assets.append({'asset_id':aid,'instance_id':aid+'.01','role':r['role'],'operation_ids':r['operation_ids'].split(','),'display_scale':1,'coordinate_space':'AUTHORED_METRIC','physical_qualified_transform':None,'parts':parts})
(OUT/'asset_inventory.json').write_text(json.dumps({'schema':'varactor_original_scene.v1','units':'m','main_scene_group_count':len(assets),'original_asset_group_count':12,'imported_mesh_count':0,'reused_asset_credit':0,'assets':assets},indent=2)+'\n')
(OUT/'affordances.json').write_text(json.dumps({'implementation':'metadata_only','qualified_robot_poses':False,'anchors':ANCHORS},indent=2)+'\n')
(OUT/'materials/materials.json').write_text(json.dumps([{'id':m.name,'base_color':list(m.diffuse_color),'appearance_only':True,'measured_material_properties':False} for m in M.values()],indent=2)+'\n')
# Independent display: uniform 100x metric reference geometry. No thickness exaggeration.
DISPLAY=bpy.data.scenes.new('VARACTOR_REFERENCE_DISPLAY_100X');sc=DISPLAY;bpy.context.window.scene=sc;setup(sc)
CUR=bpy.data.objects.new('DISPLAY.varactor_reference',None);sc.collection.objects.link(CUR);CUR['display_only']=True;CUR['reference_scale_factor']=100;CUR['paper_exact_geometry']=False;CUR['physical_execution']=False;CUR['energy_enabled']=False;CUR['device_io']=False
box('display.plinth',(0,0,.014),(1.24,.57,.028),'cream',.006)
for x in [-.29,.29]:box('display.support',(x,0,.037),(.34,.34,.018),'navy',.003)
device('display.sto',(-.29,0,.047),100);device('display.kto',(.29,0,.047),100,'kto',False)
# Visual leaders are outside the reference solids and explicitly marked as authored guides.
for x in [-.39,-.19]:
 o=rod('display.pad_guide',(x,.017,.102),(x,.17,.19),.0012,'amber');o['source_geometry']=False;o['role']='authored visual leader'
txt('display.pad_note','120 x 120 um PADS',(-.465,.179,.206),.022,'navy')
# A true metric wire-diameter reference, not source bonding topology.
wire=rod('display.wire_diameter_reference',(.49,-.12,.095),(.49,.10,.095),.00125,'gold');wire['native_diameter_m']=.000025;wire['display_scale']=100;wire['length_authored']=True
label('display.sto_label','STO / 3 x 3 x 0.5 mm',(-.29,-.291,.036),.56,.044,.023)
label('display.kto_label','KTO / PAD TOPOLOGY HELD',(.29,-.291,.036),.56,.044,.021)
box('display.title.plate',(0,.31,.292),(1.24,.012,.20),'navy',.004)
txt('display.title','DEVICE REFERENCES / UNIFORM 100x',(-.564,.301,.353),.038)
txt('display.note1','NOMINAL: 3 x 3 x 0.5 mm SUBSTRATES / Ti-Au 5/60 nm',(-.564,.301,.302),.023,'cyan')
txt('display.note2','STO PAD SPACING: ABOUT 2 mm / POSITIONS AUTHORED',(-.564,.301,.262),.0215)
txt('display.note3','NOMINAL LAYERS / NOT RESOLVED METROLOGY / NO ELECTRICAL MODEL',(-.564,.301,.222),.018,'amber')
# Horizontal length reference, separated from specimen geometry.
rod('display.scale.line',(-.44,-.222,.065),(-.14,-.222,.065),.001,'navy')
for x in [-.44,-.14]:rod('display.scale.tick',(x,-.23,.065),(x,-.213,.065),.001,'navy')
txt('display.scale.text','3 mm NATIVE',(-.385,-.267,.060),.018,'navy',True)
txt('display.wire.text','25 um WIRE DIA.',(.12,-.267,.060),.018,'navy',True)
CUR=None;box('display.studio.floor',(0,0,-.018),(200,200,.02),'floor',0)
light('DISPLAY.key',(-1.2,-1.7,2),400,1.5,(0,0,.12));light('DISPLAY.fill',(1.8,-.4,1.5),250,1.5,(0,0,.12));light('DISPLAY.rim',(0,1.5,1.8),450,1.5,(0,0,.12))
DISPLAY.camera=camera('CAM.dimensions',(.46,-1.95,1.5),(0,.04,.17),1.65)
# Preserve editable text in native Blender; GLB uses converted mesh copies afterward.
for scr in bpy.data.screens:
 for area in scr.areas:
  for sp in area.spaces:
   if sp.type=='FILE_BROWSER' and sp.params:sp.params.directory=b'//'
bpy.context.window.scene=MAIN;bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'geometry/varactor_lab.blend'))
for scene,filename in [(MAIN,'varactor_lab.glb'),(DISPLAY,'varactor_reference_display.glb')]:
 bpy.context.window.scene=scene
 for o in list(scene.objects):
  if o.type in ['FONT','CURVE']:
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 bpy.ops.object.select_all(action='DESELECT')
 for o in scene.objects:
  if o.type in ['MESH','EMPTY'] and 'studio.floor' not in o.name:o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(OUT/'geometry'/filename),export_format='GLB',use_selection=True,use_active_scene=True,export_apply=True,export_extras=True)
views=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['overview','handling','dimensions']
receipt={'engine':'CYCLES','device':'CPU','blender_version':bpy.app.version_string,'samples':128,'denoising':False,'resolution':[1800,1200],'views':[],'source_pixels_used':False}
for view in views:
 scene=DISPLAY if view=='dimensions' else MAIN;bpy.context.window.scene=scene
 if view!='dimensions':scene.camera=CAMS[view]
 scene.render.filepath=str(OUT/'evidence'/f'{view}.png');bpy.ops.render.render(write_still=True)
 p=OUT/'evidence'/f'{view}.png';raw=p.read_bytes();clean=raw[:8];offset=8
 while offset<len(raw):
  length=struct.unpack('>I',raw[offset:offset+4])[0];kind=raw[offset+4:offset+8]
  if kind not in [b'tEXt',b'zTXt',b'iTXt']:clean+=raw[offset:offset+length+12]
  offset+=length+12
 p.write_bytes(clean);receipt['views'].append({'id':view,'scene':scene.name,'camera':scene.camera.name,'file':'evidence/'+p.name,'sha256':hashlib.sha256(clean).hexdigest(),'actual_render':True,'text_metadata_removed':True})
if views:(OUT/'review/render_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('VARACTOR_BUILD_COMPLETE')
