"""Original generic transistor service scene. No source artwork, CAD or optical reconstruction.
All main-scene coordinates are authored metres, not qualified physical coordinates.
Separate display scene is a non-proportional information diagram. Blender 4.3+ / CPU.
"""
import bpy, math, json, sys, hashlib
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[1]
PLAN=json.loads((OUT/'task_binding_snapshot.json').read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.materials):bpy.data.materials.remove(d)
MAIN=bpy.context.scene;MAIN.name='TRANSISTOR_AUTHORED_METRIC';sc=MAIN
ROOTS={};CUR=None;ANCHORS=[]

def setup(scene):
 scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=96;scene.cycles.use_denoising=False
 scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
 scene.render.image_settings.file_format='PNG';scene.world.color=(.15,.17,.20)
 scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-1.25
setup(sc)

def mat(n,c,metal=0,rough=.38):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 return m
M={'ivory':mat('Ceramic ivory | appearance only',(.78,.84,.83),.1), 'navy':mat('Petrol anodized | appearance only',(.022,.07,.09),.55), 'teal':mat('Teal datum | appearance only',(.022,.48,.45),.3), 'amber':mat('Amber hold | appearance only',(.97,.40,.07),.25), 'steel':mat('Steel grey | appearance only',(.44,.54,.59),.75), 'black':mat('Graphite | appearance only',(.012,.024,.027),0,.5),'white':mat('Ivory typography',(.91,.97,.96),0,.6),'cyan':mat('Placeholder window | opaque',(.23,.63,.73),.35),'floor':mat('Studio background',(.72,.80,.84),0,.9),'gold':mat('Brass datum | appearance only',(.68,.39,.10),.7)}

def root(asset):
 global CUR
 aid=asset['asset_id'];o=bpy.data.objects.new(aid,None);sc.collection.objects.link(o);o.empty_display_size=.03
 for k,v in {'asset_id':aid,'asset_version':'1.0.0','role':asset['role'],'authored_dimension_status':'unqualified_authored_metres','physical_execution':False,'display_only':False,'operation_ids':','.join(asset['bind_operation_ids']),'source_evidence_ids':','.join(asset['source_evidence_ids'])}.items():o[k]=v
 ROOTS[aid]=o;CUR=o;return o

def finish(o,n,m=None):
 o.name=n
 if m:o.data.materials.append(M[m])
 if CUR:o.parent=CUR
 o['geometry_basis']='original_authored';o['physical_geometry_validated']=False;o['device_io']=False
 return o

def box(n,p,d,m='navy',bevel=.003):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.dimensions=d;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(o,n,m)
 if bevel:
  b=o.modifiers.new('Authored edge radius','BEVEL');b.width=min(bevel,min(d)/3);b.segments=3;o.modifiers.new('Weighted visual normals','WEIGHTED_NORMAL')
 return o

def cyl(n,p,r,h,m='steel',axis='Z',vertices=48):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=h,location=p);o=bpy.context.object
 if axis=='Y':o.rotation_euler.x=math.pi/2
 if axis=='X':o.rotation_euler.y=math.pi/2
 finish(o,n,m)
 for f in o.data.polygons:f.use_smooth=True
 return o

def rod(n,a,b,r=.003,m='steel'):
 o=cyl(n,(Vector(a)+Vector(b))/2,r,(Vector(a)-Vector(b)).length,m);o.rotation_euler=(Vector(b)-Vector(a)).to_track_quat('Z','Y').to_euler();return o

def text(n,s,p,size=.017,m='white',flat=False):
 c=bpy.data.curves.new(n,'FONT');c.body=s;c.size=size;c.extrude=.00008;c.space_character=1.05
 o=bpy.data.objects.new(n,c);sc.collection.objects.link(o);o.location=p
 if not flat:o.rotation_euler=(math.pi/2,0,0)
 return finish(o,n,m)

def label(n,s,p,w=.32,h=.046,size=.014,m='navy'):
 box(n+'.plate',p,(w,.005,h),m,.002);text(n+'.text',s,(p[0]-w*.455,p[1]-.003,p[2]-.006),size)

def anchor(a,p,target,meaning):
 n=CUR.name+'.'+a;o=bpy.data.objects.new(n,None);sc.collection.objects.link(o);o.parent=CUR;o.location=p;o.empty_display_type='ARROWS';o.empty_display_size=.019
 o['anchor_id']=a;o['coordinate_status']='authored_unqualified';o['interaction']='metadata_only';o['target_object']=target
 ANCHORS.append({'asset_id':CUR.name,'anchor_id':a,'scene_object':n,'target_object':target,'translation_m':list(p),'rotation_quaternion_xyzw':[0,0,0,1],'coordinate_status':'authored_unqualified','physical_qualified_transform':None,'meaning':meaning})
 return o

def camera(n,p,target,scale):
 c=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,c);sc.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();c.type='ORTHO';c.ortho_scale=scale;c.clip_start=.0001;c.clip_end=100;return o

def light(n,p,power,size,target):
 d=bpy.data.lights.new(n,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(n,d);sc.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()

# Six semantic groups, with source-known chip-envelope facts and authored apparatus.
root(PLAN['scene_assets'][0])
box('bench.base',(0,0,.063),(2.05,1.12,.11),'ivory',.018)
box('bench.top',(0,0,.127),(1.98,1.045,.02),'steel',.009)
for x in [-.86,.86]:
 for y in [-.4,.4]:box('bench.foot',(x,y,.009),(.12,.12,.07),'black',.008)
label('bench.title','TRANSISTORS  /  CUSTODY + CLOSED SERVICES',(0,-.567,.08),1.80,.052,.029)
text('bench.boundary','STATIC ASSETS  |  NO LIVE BIAS  |  QUALIFICATION REQUIRED',(-.76,-.572,.035),.018)
box('carrier.platform',(-.63,-.20,.17),(.62,.60,.057),'navy',.009)
box('carrier.dock',(-.64,-.23,.216),(.31,.25,.034),'steel',.005)
reuse=json.loads((OUT/'geometry/reused_carrier_components.json').read_text());origin=(-.64,-.23,.246)
for p in reuse['parts']:
 mesh=bpy.data.meshes.new('reuse.'+p['source_part_id']);mesh.from_pydata(p['vertices'],[],p['faces']);mesh.update()
 o=bpy.data.objects.new('reuse.'+p['source_part_id'],mesh);sc.collection.objects.link(o);o.parent=CUR
 o.location=tuple(origin[i]+p['translation_m'][i] for i in range(3));o.rotation_euler=p['rotation_euler_rad'];o.scale=p['scale']
 for q,smooth in zip(mesh.polygons,p['smooth_faces']):q.use_smooth=smooth
 material=p['source_material'].lower();key='teal' if 'teal' in material else 'steel' if 'metal' in material else 'gold' if 'brass' in material else 'black' if 'graphite' in material else 'navy';mesh.materials.append(M[key])
 for mod in p['modifiers']:
  m=o.modifiers.new('Preserved original '+mod['type'],mod['type'])
  if m.type=='BEVEL':m.width=mod['width'];m.segments=mod['segments']
 o['geometry_basis']='reused_original_afm_mesh';o['source_asset_family']=p['source_asset_family'];o['source_part_id']=p['source_part_id'];o['new_unique_asset_credit']=0;o['physical_geometry_validated']=False
# Native-size outer substrate example. No circuit pattern, bond pad or functional layer mesh.
box('chip.support',(-.64,-.23,.263),(.065,.060,.005),'ivory',.001)
chip=box('chip.source_envelope',(-.64,-.23,.26576435),(.020,.020,.0005287),'black',0)
chip['geometry_basis']='source_reported_substrate_context_plus_table_thickness';chip['source_locator']='Main p769; SI TableS1';chip['unpatterned']=True;chip['electrical_connectivity']=False
text('carrier.sample_id','SPECIMEN T-001 / v1',(-.76,-.33,.239),.014,'navy',True)
# Authored ruler with real metric spacing.
box('carrier.ruler',(-.620,-.390,.214),(.212,.022,.005),'ivory',.001)
for i in range(21):
 x=-.72+i*.01;box('ruler.tick.'+str(i),(x,-.389,.217),(.0007,.014 if i%5==0 else .007,.0005),'navy',0)
for value in [0,50,100,150,200]:text('ruler.label.'+str(value),str(value),(-.727+value*.001,-.418,.218),.008,'white',True)
text('ruler.unit','mm',(-.486,-.418,.218),.008,'white',True)
label('carrier.label','01 / RETAINED SAMPLE',(-.63,-.509,.169),.55,.04,.018)
label('carrier.scale_note','CHIP 20 mm / UNPATTERNED',(-.63,.050,.211),.55,.038,.017)
for a,p,t,meaning in [('dock',(-.64,-.23,.233),'carrier.dock','Authored support datum, not fit-qualified'),('grasp_left',(-.743,-.23,.255),'reuse.carrier.loaded.grasp_tab','Original AFM carrier grasp family reused, no robot validation'),('grasp_right',(-.537,-.23,.255),'reuse.carrier.loaded.grasp_tab.001','No source trajectory or force limit'),('retention',(-.64,-.203,.276),'reuse.clamp.loaded.arm','Static retained pose, not observed mechanical safety'),('specimen',(-.64,-.23,.266),'chip.source_envelope','Unpatterned 20 mm source-context envelope'),('ruler',(-.625,-.39,.217),'carrier.ruler','Authored metric reference')]:anchor(a,p,t,meaning)

root(PLAN['scene_assets'][1])
box('packaging.platform',(-.035,-.275,.17),(.49,.46,.057),'navy',.008)
box('packaging.handoff_fixture',(-.035,-.28,.221),(.31,.27,.04),'steel',.006)
# Generic PCB slab and blank connector housing: all dimensions authored, no pad-map claim.
box('pcb.blank_board',(-.035,-.28,.246),(.11,.090,.006),'teal',.001)
box('pcb.blank_chip_envelope',(-.035,-.28,.2493),(.020,.020,.0005287),'black',0)
for i,x in enumerate([-.095,.025]):box('pcb.edge_retainer.'+str(i),(x,-.28,.252),(.01,.08,.016),'gold',.002)
box('pcb.capped_connector',(-.035,-.224,.258),(.087,.016,.018),'black',.002)
text('pcb.id','PCB-P001',(-.08,-.36,.248),.012,'navy',True)
box('packaging.sealed_service',(-.035,.074,.298),(.47,.22,.27),'ivory',.012)
box('packaging.front_seal',(-.035,-.042,.323),(.37,.012,.135),'black',.006)
text('packaging.title','PACKAGING',(-.20,-.050,.358),.024,'white')
text('packaging.status','CLOSED SERVICE',(-.20,-.050,.317),.020,'amber')
text('packaging.note','NO BOND SETTINGS',(-.20,-.050,.282),.014,'white')
label('packaging.label','02 / PCB HANDOFF',(-.035,-.509,.169),.43,.04,.017)
for a,p,t,meaning in [('pcb_datum',(-.035,-.28,.243),'packaging.handoff_fixture','Unqualified authored PCB support'),('pcb_grasp',(-.095,-.28,.262),'pcb.edge_retainer.0','Edge handling role, no verified grasp'),('closed_service',(-.035,-.05,.32),'packaging.front_seal','Chip attach and bond services remain closed'),('inspection',(-.035,-.28,.250),'pcb.blank_board','No bond-wire geometry or inspection outcome supplied')]:anchor(a,p,t,meaning)

root(PLAN['scene_assets'][2])
box('probe.platform',(.59,.15,.169),(.72,.63,.057),'navy',.011)
box('probe.closed_chamber',(.73,.25,.361),(.36,.42,.33),'ivory',.015)
box('probe.lid',(.73,.25,.537),(.35,.41,.019),'navy',.009)
box('probe.closed_window',(.73,.032,.370),(.28,.012,.14),'black',.006)
text('probe.chamber_label','SEALED PROBE',(.606,.023,.398),.019,'white')
text('probe.chamber_status','NO CONTACT',(.61,.023,.355),.023,'amber')
# Closed logical ports, no electrical cables or inferred connections.
for i,n in enumerate(['BG','TG','D','S']):
 x=.62+i*.073;cyl('probe.capped_port.'+n,(x,.025,.274),.014,.017,'steel','Y');cyl('probe.port_cap.'+n,(x,.013,.274),.010,.005,'black','Y');text('probe.port_text.'+n,n,(x-.011,.003,.236),.014,'navy')
box('readout.body',(.34,.265,.36),(.22,.36,.33),'navy',.014)
box('readout.screen',(.34,.078,.405),(.19,.012,.176),'black',.004)
text('readout.title','READOUT',(.26,.069,.463),.020,'white')
text('readout.value','NO DATA',(.26,.069,.418),.024,'amber')
text('readout.boundary','STATIC ONLY',(.26,.069,.38),.014,'white')
text('readout.safe','SAFE STATE:',(.26,.069,.330),.014,'white')
text('readout.unknown','UNKNOWN',(.26,.069,.300),.020,'amber')
label('probe.label','03 / PROBE + RECORDS',(.59,-.178,.171),.64,.042,.018)
for a,p,t,meaning in [('record_display',(.34,.067,.415),'readout.screen','No measurement emitted'),('safe_state',(.34,.067,.30),'readout.body','Independent receipt required, never inferred from off command'),('sealed_probe',(.73,.020,.370),'probe.closed_window','No live electrode access'),('capped_BG',(.62,.008,.274),'probe.port_cap.BG','Logical terminal identity only'),('capped_TG',(.693,.008,.274),'probe.port_cap.TG','Logical terminal identity only'),('capped_D',(.766,.008,.274),'probe.port_cap.D','Logical terminal identity only'),('capped_S',(.839,.008,.274),'probe.port_cap.S','Logical terminal identity only')]:anchor(a,p,t,meaning)

root(PLAN['scene_assets'][3])
box('bias.platform',(.59,-.367,.168),(.72,.285,.056),'navy',.01)
box('bias.closed_console',(.59,-.351,.257),(.65,.22,.12),'ivory',.008)
box('bias.control_bar',(.59,-.466,.275),(.59,.010,.068),'black',.004)
for i,(name,col) in enumerate([('VBG','teal'),('VTG1','gold'),('VTG2','cyan')]):
 x=.37+i*.205;cyl('bias.locked_control.'+name,(x,-.479,.279),.019,.013,col,'Y');text('bias.label.'+name,name,(x-.033,-.490,.235),.013,'navy')
text('bias.no_output','LOCKED  /  NO VOLTAGE OUTPUT',(.31,-.466,.331),.016,'navy')
label('bias.label','04 / LOGICAL BIAS CONTROL',(.59,-.512,.168),.64,.040,.017)
for n,x in [('VBG',.37),('VTG1',.575),('VTG2',.78)]:anchor(n,(x,-.490,.279),'bias.locked_control.'+n,'Decorative locked channel; no numeric control or electrical physics')
anchor('netlist_select',(.59,-.466,.33),'bias.closed_console','Ordinary and independent maps are separate named static contracts')

root(PLAN['scene_assets'][4])
box('service.platform',(-.63,.30,.17),(.62,.40,.057),'navy',.009)
for i,(name,title) in enumerate([('fab','FAB'),('metrology','METROLOGY'),('thermal','THERMAL')]):
 x=-.825+i*.194;box('service.'+name,(x,.30,.32),(.174,.31,.245),'ivory',.009)
 box('service.'+name+'_sealed_door',(x,.139,.329),(.142,.011,.143),'navy',.004)
 text('service.'+name+'_title',title,(x-.060,.131,.36),.016 if i!=1 else .011,'white')
 text('service.'+name+'_hold','CLOSED',(x-.050,.131,.317),.013,'amber')
 cyl('service.'+name+'_seal',(x,.125,.27),.012,.005,'gold','Y',12)
 anchor(name+'_handoff',(x,.127,.32),'service.'+name+'_sealed_door','Closed qualified service boundary; no recipe, internal equipment or device adapter')
label('service.label','05 / QUALIFIED SERVICES',(-.63,.514,.196),.59,.048,.018)
anchor('cooldown_ledger',(-.436,.127,.329),'service.thermal_sealed_door','Off-hotplate time/custody requires external evidence; no temperature or elapsed-time simulation')

root(PLAN['scene_assets'][5])
box('storage.platform',(-.035,.375,.169),(.47,.275,.056),'navy',.008)
for i,(name,title,col) in enumerate([('input','T-001','teal'),('daughter','D-001','cyan'),('hold','HOLD','amber')]):
 x=-.19+i*.154;box('storage.bin.'+name,(x,.372,.258),(.14,.20,.14),'ivory',.006)
 box('storage.lid.'+name,(x,.372,.337),(.145,.205,.018),col,.005)
 label('storage.id.'+name,title,(x,.265,.283),.125,.047,.016)
 text('storage.version.'+name,'ID / v1',(x-.046,.262,.235),.010,'navy')
 anchor(name+'_slot',(x,.372,.34),'storage.lid.'+name,'Authored custody placeholder; no extra scientific specimen-count credit')
label('storage.label','06 / CUSTODY + HOLD',(-.035,.514,.196),.46,.048,.017)
anchor('archive',(-.035,.25,.28),'storage.bin.daughter','Record metadata role; source populations remain separate')
# Upright boundary marker records all unresolved source conflicts compactly.
box('storage.conflict_panel',(-.02,.491,.44),(.46,.021,.16),'navy',.007)
text('storage.conflict_title','10 SOURCE HOLDS',(-.22,.477,.480),.025,'amber')
text('storage.conflict_ids','C01 C02 C03 C04 C05',(-.219,.477,.440),.017,'white')
text('storage.conflict_ids2','C06 C07 C08 C09 C10',(-.219,.477,.410),.017,'white')
text('storage.conflict_note','NONE RESOLVED BY THIS SCENE',(-.219,.477,.379),.011,'white')
anchor('conflict_gate',(-.02,.475,.44),'storage.conflict_panel','All ten unresolved conflicts are blocking qualifications')
CUR=None
box('studio.floor',(0,0,-.065),(200,200,.07),'floor',0)
light('LIGHT.key',(-1.8,-1.5,2.7),450,2,(0,0,.25));light('LIGHT.fill',(2,-.3,2.0),260,1.8,(0,0,.25));light('LIGHT.rim',(-.1,1.8,2.7),450,1.9,(0,0,.25))
CAMS={'overview':camera('CAM.overview',(1.6,-2.9,2.25),(0,0,.29),2.55),'sample_handling':camera('CAM.sample_handling',(-1.05,-1.25,1.10),(-.41,-.22,.29),1.14),'equipment_closeup':camera('CAM.equipment_closeup',(1.25,-1.45,1.03),(.60,.04,.33),1.17)}
MAIN.camera=CAMS['overview'];bpy.context.view_layer.update()
assets=[]
for aid,r in ROOTS.items():
 parts=[]
 for o in r.children:
  if o.type in ['MESH','FONT']:
   parts.append({'part_id':o.name,'type':o.type,'dimensions_m':[float(v) for v in o.dimensions],'translation_m':list(o.location),'rotation_quaternion_xyzw':[o.rotation_euler.to_quaternion()[i] for i in [1,2,3,0]],'scale':list(o.scale),'geometry_basis':o.get('geometry_basis','original_authored'),'physical_geometry_validated':False,'source_asset_family':o.get('source_asset_family'),'source_part_id':o.get('source_part_id')})
 assets.append({'asset_id':aid,'instance_id':aid+'.01','role':r['role'],'operation_ids':r['operation_ids'].split(','),'source_evidence_ids':r['source_evidence_ids'].split(','),'display_scale':1,'coordinate_space':'MAIN_AUTHORED_METRIC','physical_qualified_transform':None,'parts':parts})
(OUT/'asset_inventory.json').write_text(json.dumps({'schema':'transistor_original_scene.v1','units':'m','main_scene_group_count':6,'unique_asset_count':None,'reused_mesh_count':15,'reused_new_unique_asset_credit':0,'counting_policy':'Layers, repeated parts, labels, exports and scene groups are not independently new assets.','assets':assets},indent=2)+'\n')
for a in ANCHORS:
 a.update({'allowed_tool':'metadata selector only; no qualified physical tool','precondition':'identity bound and appropriate static guard satisfied; real use requires external qualification','postcondition':'local metadata transition only','failure_stop':'missing identity, stale receipt, unresolved qualification or absent adapter','collision_representation':'none','physical_execution':False})
(OUT/'affordances.json').write_text(json.dumps({'implementation':'metadata_only','qualified_robot_poses':False,'collision_meshes_supplied':False,'anchors':ANCHORS},indent=2)+'\n')
(OUT/'materials/materials.json').write_text(json.dumps([{'id':m.name,'base_color':list(m.diffuse_color),'appearance_only':True,'measured_material_properties':False} for m in M.values()],indent=2)+'\n')
# Separate native reference. Positions and thicknesses are local near origin to retain
# nanometre precision; full square laminae do NOT represent patterned circuit connectivity.
NATIVE=bpy.data.scenes.new('NATIVE_LAYER_REFERENCE_METRES');NATIVE.world=MAIN.world.copy();sc=NATIVE;bpy.context.window.scene=sc;setup(sc)
CUR=bpy.data.objects.new('NATIVE.unpatterned_layer_reference',None);sc.collection.objects.link(CUR)
CUR['reference_only']=True;CUR['lateral_geometry']='unpatterned authored 20mm visualization envelope';CUR['electrical_connectivity']=False;CUR['source_variant']='SI_TableS1';CUR['execution_thickness_default']='NULL_UNRESOLVED_C01'
z=0
for layer in PLAN['layer_contract']['layers']:
 h=layer['source_thickness']*(1e-6 if layer['unit']=='um' else 1e-9)
 color='black' if layer['index']==1 else 'cyan' if layer['material']=='SiO2' else 'gold' if layer['material']=='Al' else 'teal' if layer['material']=='In2O3' else 'ivory'
 o=box('native.layer.%02d.%s'%(layer['index'],layer['role']),(0,0,z+h/2),(.02,.02,h),color,0)
 o['layer_index']=layer['index'];o['source_thickness_m']=h;o['source_role']=layer['role'];o['source_material']=layer['material'];o['stack_id']=layer['stack'] or 0;o['source_variant']='SI_TableS1';o['unpatterned_visualization_envelope']=True;o['electrical_connectivity']=False;o['fabrication_executable']=False
 if layer['role'] in ['interstack_buffer','final_cap']:o['execution_thickness_default']='NULL';o['conflict_id']='C01'
 z+=h
CUR['total_table_reference_thickness_m']=z;CUR=None
NATIVE.camera=camera('CAM.native_reference',(.04,-.04,.024),(0,0,.00026),.04)
# Separate display. Equal height bars encode order, never relative layer thickness.
DISPLAY=bpy.data.scenes.new('DISPLAY_ONLY_NOT_TO_SCALE');DISPLAY.world=MAIN.world.copy();sc=DISPLAY;bpy.context.window.scene=sc;setup(sc)
CUR=bpy.data.objects.new('DISPLAY.layer_ledger',None);sc.collection.objects.link(CUR);CUR['display_only']=True;CUR['uniform_scale_factor']='NONE';CUR['source_layer_count']=72
box('display.base',(0,0,.035),(1.86,.65,.05),'ivory',.013)
text('display.title','72 LAYERS / ORDER ONLY',(-.85,-.267,.066),.032,'navy',True)
text('display.boundary','EQUAL DISPLAY THICKNESS  |  NOT A MASK, CROSS-SECTION OR FABRICATION RECIPE',(-.85,-.313,.066),.013,'navy',True)
for layer in PLAN['layer_contract']['layers']:
 i=layer['index'];color='black' if i==1 else 'cyan' if i==2 else 'gold' if layer['material']=='Al' else 'teal' if layer['material']=='In2O3' else 'ivory'
 o=box('display.layer.%02d.%s'%(i,layer['role']),(-.70,.10,.085+(i-1)*.0045),(.26,.25,.003),color,0)
 o['layer_index']=i;o['display_only']=True;o['source_thickness_m']=layer['source_thickness']*(1e-6 if layer['unit']=='um' else 1e-9);o['display_thickness_m']=.003;o['display_gap_m']=.0015;o['uniform_scale_factor']='NONE'
text('display.layer_count','60 ACTIVE + 9 BUFFERS + 1 CAP',(-.848,-.036,.445),.015,'navy')
text('display.substrate_count','+ Si SUBSTRATE + SiO2 = 72',(-.848,-.036,.423),.015,'navy')
text('display.conflict','C01: 25 / 50 nm UNRESOLVED',(-.848,-.036,.478),.017,'navy')
text('display.native_note','NATIVE THICKNESSES: SEPARATE BLEND SCENE',(-.85,-.075,.077),.011,'navy',True)
# The maps are factual logical labels only. No drawn trace is claimed as PCB wiring.
for j,(title,rows) in enumerate([('ORDINARY / FIG4',[('DR BG/TG','VIN / VIN'),('DR S/D','GND / VOUT'),('LD BG/TG','VDD / VOUT'),('LD S/D','VOUT / VDD')]),('INDEPENDENT / S31',[('DR BG/TG','VBG / VTG1'),('DR S/D','GND / VOUT'),('LD BG/TG','VOUT / VTG2'),('LD S/D','VOUT / VDD')])]):
 x=-.18+j*.55;box('display.netlist_card.'+str(j),(x,.12,.30),(.51,.027,.42),'navy',.007)
 text('display.netlist_title.'+str(j),title,(x-.23,.103,.473),.019,'white')
 for k,(term,node) in enumerate(rows):
  text('display.netlist_term.%s.%s'%(j,k),term,(x-.23,.103,.418-k*.066),.019,'cyan')
  text('display.netlist_node.%s.%s'%(j,k),node,(x-.23,.103,.391-k*.066),.018,'white')
 text('display.netlist_gate.'+str(j),'PAD MAP / REVIEW REQUIRED',(x-.23,.103,.112),.013,'amber')
text('display.no_wiring','LOGICAL TOPOLOGY ONLY / NO PHYSICAL PAD MAP',(-.42,-.12,.075),.016,'navy',True)
CUR=None
box('display.studio.floor',(0,0,-.022),(200,200,.02),'floor',0)
light('DISPLAY.key',(-1,-1,2.5),350,2,(0,0,.2));light('DISPLAY.fill',(1.5,-.4,1.6),250,1.5,(0,0,.2))
DISPLAY.camera=camera('CAM.layer_ledger',(1.1,-2.6,1.4),(0,0,.24),2.10)
bpy.context.window.scene=MAIN
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'geometry/transistor_operations_lab.blend'))
for scene,path in [(MAIN,'transistor_operations_lab.glb'),(DISPLAY,'transistor_layer_ledger_display.glb')]:
 bpy.context.window.scene=scene
 for o in list(scene.objects):
  if o.type=='FONT':
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 bpy.ops.object.select_all(action='DESELECT')
 for o in scene.objects:
  if o.type in ['MESH','EMPTY'] and 'studio.floor' not in o.name:o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(OUT/'geometry'/path),export_format='GLB',use_selection=True,use_active_scene=True,export_apply=True,export_extras=True)
views=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['overview','sample_handling','equipment_closeup']
receipt={'engine':'CYCLES','device':'CPU','blender_version':bpy.app.version_string,'samples':MAIN.cycles.samples,'resolution':[1600,1100],'views':[],'source_pixels_used':False}
for view in views:
 scene=DISPLAY if view=='layer_ledger' else MAIN;bpy.context.window.scene=scene;scene.camera=DISPLAY.camera if view=='layer_ledger' else CAMS[view]
 scene.render.filepath=str(OUT/'evidence'/f'{view}.png');bpy.ops.render.render(write_still=True)
 p=OUT/'evidence'/f'{view}.png';receipt['views'].append({'id':view,'camera':scene.camera.name,'file':'evidence/'+p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'actual_render':True})
if views:(OUT/'review/render_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('TRANSISTOR_ASSET_BUILD_COMPLETE')
