"""Original generic sucrose service scene. No source artwork, CAD or optical reconstruction.
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
MAIN=bpy.context.scene;MAIN.name='SUCROSE_AUTHORED_METRIC';sc=MAIN
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

# Exactly six main asset groups. Context geometry belongs to the standards bench.
root(PLAN['scene_assets'][0])
box('bench.base',(0,0,.065),(1.95,1.12,.11),'ivory',.02)
box('bench.inset',(0,0,.125),(1.88,1.045,.018),'steel',.012)
for x in [-.79,.79]:
 for y in [-.40,.40]:box('bench.foot',(x,y,.01),(.13,.13,.07),'black',.01)
label('bench.title','SUCROSE  /  ENCLOSED METROLOGY SERVICE',(0,-.564,.073),1.67,.052,.028)
text('bench.boundary','ORIGINAL GENERIC ASSETS   |   STATIC STUDY   |   NO DEVICE CONTROL',(-.72,-.569,.030),.017)
box('standards.platform',(-.61,.13,.158),(.62,.59,.045),'navy',.012)
# Authored balance and weighing dish; no measurement is emitted.
box('balance.body',(-.78,-.015,.20),(.24,.24,.07),'ivory',.01)
cyl('balance.pan',(-.78,-.005,.243),.075,.016,'steel')
label('balance.readout','TARE / DEMO',(-.78,-.139,.213),.21,.033,.012)
# Capped bottles are opaque proxy solids, no actual fluid simulation.
for i,(x,y) in enumerate([(-.67,.29),(-.52,.30)]):
 cyl(f'bottle.{i}.body',(x,y,.274),.045,.19,'cyan');cyl(f'bottle.{i}.cap',(x,y,.379),.040,.028,'navy')
 label(f'bottle.{i}.id',('STD' if i==0 else 'TEST')+' / 100 mL',(x,y-.045,.29),.092,.053,.009)
 cyl(f'bottle.{i}.coaster',(x,y,.18),.05,.01,'teal')
# Mixer puck without functional drive.
cyl('mixer.puck',(-.44,-.02,.194),.082,.038,'teal');cyl('mixer.top',(-.44,-.02,.219),.066,.012,'ivory')
# Distinct tube rack and nominal 1.5 mL proxy tubes.
box('tube.rack',(-.34,.22,.205),(.075,.31,.075),'ivory',.006)
for i in range(4):
 y=.11+i*.075;cyl(f'tube.{i}.body',(-.34,y,.269),.019,.096,'cyan');cyl(f'tube.{i}.cap',(-.34,y,.323),.022,.015,'teal')
# Filter is a sealed role proxy, dimensions not pore scale.
cyl('filter.proxy',(-.61,-.12,.218),.031,.032,'ivory');cyl('filter.in',(-.61,-.12,.246),.009,.022,'gold');cyl('filter.out',(-.61,-.12,.19),.009,.023,'gold')
label('standards.label','01 / STANDARDS',(-.60,-.172,.169),.52,.036,.016)
for a,p,t,meaning in [
('weigh_pan',(-.78,-.005,.253),'balance.pan','Authored dish center; not calibrated scale'),('mix_position',(-.44,-.02,.23),'mixer.top','Static mixer role'),('bottle_slot',(-.67,.29,.18),'bottle.0.coaster','Capped bottle nominal label'),('tube_rack',(-.34,.22,.33),'tube.rack','Receiving-tube identity role'),('filter_in',(-.61,-.12,.257),'filter.in','Logical filter entry'),('filter_out',(-.61,-.12,.178),'filter.out','Logical filter exit')]:anchor(a,p,t,meaning)

root(PLAN['scene_assets'][1])
box('reference.platform',(-.59,-.375,.16),(.66,.27,.05),'navy',.01)
box('reference.body',(-.72,-.36,.239),(.29,.20,.105),'ivory',.009)
cyl('reference.sample_recess',(-.80,-.34,.296),.035,.01,'black')
cyl('reference.sample_lip',(-.80,-.34,.296),.045,.005,'gold')
box('reference.display',(-.63,-.34,.296),(.10,.095,.009),'black',.003)
text('reference.display_label','REF ONLY',(-.673,-.369,.302),.011,'white',True)
box('reference.clean_tray',(-.41,-.365,.198),(.17,.16,.022),'teal',.007)
box('reference.inert_wipe',(-.41,-.365,.214),(.11,.10,.011),'ivory',.004)
label('reference.label','02 / REFERENCE',(-.59,-.513,.175),.57,.036,.016)
for a,p,t,meaning in [('sample_present',(-.80,-.34,.304),'reference.sample_recess','Reference sample presentation proxy'),('read_display',(-.63,-.34,.303),'reference.display','No numerical reading supplied'),('clean_tray',(-.41,-.365,.22),'reference.clean_tray','Inert cleaning-tray proxy')]:anchor(a,p,t,meaning)

root(PLAN['scene_assets'][2])
box('cartridge.platform',(.03,-.24,.16),(.47,.54,.045),'navy',.008)
box('cartridge.dock',(.03,-.22,.194),(.29,.245,.03),'steel',.006)
# Reuse exact mesh/topology/modifiers from the original AFM project. Only translated.
reuse=json.loads((OUT/'geometry/reused_carrier_components.json').read_text());origin=(.03,-.22,.224)
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
# Closed opaque chip shell; no source channel/plate geometry reconstructed.
box('cartridge.closed_shell',(.03,-.225,.253),(.097,.079,.028),'ivory',.004)
box('cartridge.bubble_window',(.03,-.236,.269),(.044,.020,.003),'cyan',.003)
text('cartridge.shell_label','CHIP',(.012,-.202,.269),.008,'navy',True)
for suffix,x in [('in',-.033),('out',.093)]:
 cyl('cartridge.port_'+suffix,(x,-.225,.251),.009,.034,'gold','X');cyl('cartridge.port_'+suffix+'_cap',(x+(-.015 if suffix=='in' else .015),-.225,.251),.010,.005,'black','X')
box('cartridge.inlet_clamp',(-.072,-.25,.247),(.023,.033,.036),'amber',.003)
label('cartridge.volume_label','22 uL CHAMBER / NOMINAL',(.03,-.405,.231),.40,.036,.013)
label('cartridge.label','03 / RETAINED CARTRIDGE',(.03,-.512,.17),.44,.036,.013)
# Syringe pump is an opaque locked enclosure only. No speed control, fluid or device code.
box('pump.closed_proxy',(.03,.12,.225),(.47,.20,.16),'ivory',.012)
box('pump.seal',(.03,.013,.238),(.34,.008,.06),'black',.003)
text('pump.hold_label','PUMP  /  BLOCKED',(-.112,.007,.235),.020,'amber')
text('pump.proxy_label','SEALED SYRINGE SERVICE',(-.12,.007,.215),.010,'white')
for x in [-.18,.24]:cyl('pump.seal_fastener',(x,.015,.23),.006,.012,'gold','Y',12)
for a,p,t,meaning in [('inlet_logical',(-.05,-.225,.251),'cartridge.port_in','Logical sealed inlet only'),('outlet_logical',(.111,-.225,.251),'cartridge.port_out','Logical sealed outlet only'),('inlet_clamp',(-.072,-.25,.267),'cartridge.inlet_clamp','Static closed isolation indicator'),('bubble_window',(.03,-.236,.272),'cartridge.bubble_window','Opaque placeholder; no bubble image or simulated flow'),('dock_anchor',(.03,-.22,.194),'cartridge.dock','Unqualified authored carrier datum'),('retained_mount',(.03,-.22,.224),'reuse.carrier.loaded.base','Reused original carrier; no validated retention')]:anchor(a,p,t,meaning)

root(PLAN['scene_assets'][3])
box('optics.footprint',(.60,.18,.167),(.64,.63,.055),'navy',.012)
box('optics.sealed_body',(.60,.18,.39),(.56,.53,.40),'ivory',.02)
box('optics.top_lid',(.60,.18,.602),(.54,.51,.022),'navy',.012)
for x in [.37,.83]:
 for y in [-.03,.39]:cyl('optics.seal_bolt',(x,y,.617),.006,.009,'steel',vertices=12)
box('optics.left_dock',(.298,.10,.32),(.045,.19,.085),'teal',.006)
box('optics.dock_seal',(.270,.10,.32),(.011,.14,.048),'black',.003)
box('optics.readout',(.60,-.09,.438),(.47,.009,.19),'black',.008)
text('optics.readout_title','ENCLOSED ACQUISITION',(.388,-.098,.497),.022,'white')
text('optics.readout_hold','NO LIVE DATA',(.39,-.098,.457),.034,'amber')
text('optics.readout_note','BEAM  /  SPECKLE  /  DARK',(.39,-.098,.42),.020,'cyan')
text('optics.temperature','TEMP : NOT CONNECTED',(.39,-.098,.381),.017,'white')
label('optics.label','04 / SEALED OPTICS',(.60,-.091,.286),.48,.054,.022)
text('optics.warning','NO OPEN BEAM  -  NO DEVICE I/O',(.392,-.097,.248),.014,'navy')
for a,p,t,meaning in [('sealed_dock',(.264,.10,.32),'optics.dock_seal','Closed service boundary; no beam path'),('status_display',(.60,-.10,.457),'optics.readout','Static not-connected status'),('temperature_display',(.60,-.10,.381),'optics.readout','No measured temperature'),('beam_channel',(.43,-.10,.42),'optics.readout','Beam-profile record role only'),('speckle_channel',(.60,-.10,.42),'optics.readout','Speckle record role only; no synthetic image'),('dark_channel',(.77,-.10,.42),'optics.readout','Dark-frame record role only')]:anchor(a,p,t,meaning)

root(PLAN['scene_assets'][4])
box('records.platform',(.60,-.38,.16),(.64,.27,.045),'navy',.009)
box('records.archive',(.80,-.36,.247),(.17,.19,.14),'ivory',.01)
label('records.archive_label','ARCHIVE',(.80,-.459,.263),.145,.045,.012)
for i,(name,title,col) in enumerate([('sample','SAMPLE','teal'),('reference','REF','gold'),('calibration','CAL','cyan'),('run','RUN','amber')]):
 x=.34+i*.108;box('records.'+name+'_card',(x,-.35,.23),(.092,.025,.15),col,.003)
 label('records.'+name+'_title',title,(x,-.366,.27),.083,.028,.010)
 text('records.'+name+'_id','ID / --',(x-.034,-.369,.229),.009,'navy')
 anchor(name+'_card',(x,-.37,.23),'records.'+name+'_card','Record identity proxy; never a source measurement')
anchor('archive_slot',(.8,-.36,.247),'records.archive','Explicit archive role; stored specimen not repeat count')
label('records.label','05 / CUSTODY + LINEAGE',(.6,-.513,.174),.58,.036,.016)

root(PLAN['scene_assets'][5])
box('holds.base',(-.03,.425,.16),(.47,.19,.043),'navy',.01)
for x in [-.20,.14]:box('holds.post',(x,.454,.287),(.023,.03,.235),'steel',.003)
box('holds.panel',(-.03,.427,.40),(.48,.035,.205),'navy',.009)
text('holds.title','06 / QUALIFICATION HOLDS',(-.244,.406,.467),.020,'white')
text('holds.flow','FLOW CONFLICT : 40x',(-.244,.406,.43),.024,'amber')
text('holds.default','DEFAULT : PUMP BLOCKED',(-.244,.406,.398),.017,'white')
for i,(name,title) in enumerate([('drift','DRIFT'),('bubble','BUBBLE'),('range','RANGE'),('qualification','QUAL')]):
 x=-.22+i*.108;cyl('holds.'+name+'_lamp',(x,.403,.354),.012,.006,'amber','Y')
 text('holds.'+name+'_label',title,(x-.025,.398,.324),.010,'white')
 anchor(name+'_hold',(x,.40,.354),'holds.'+name+'_lamp','Static hold class indicator, not service readback')
# plan calls final anchor qualification_hold (matches above)
anchor('flow_conflict',(-.03,.40,.43),'holds.panel','Forty-fold source discrepancy unresolved; no numeric pump setting')

CUR=None
floor=box('studio.floor',(0,0,-.065),(200,200,.07),'floor',0)
light('LIGHT.key',(-1.4,-1.3,2.6),420,2.0,(0,0,.3));light('LIGHT.fill',(2,-.5,1.8),260,1.8,(0,0,.3));light('LIGHT.rim',(0,1.7,2.4),480,1.8,(0,0,.3))
CAMS={'overview':camera('CAM.overview',(1.8,-2.8,2.0),(0,0,.29),2.46),'cartridge_service':camera('CAM.cartridge_service',(.80,-1.25,1.08),(.035,-.12,.28),1.13)}
MAIN.camera=CAMS['overview']
bpy.context.view_layer.update()
# Main scene contract records local-to-root transforms; all roots remain at identity.
assets=[]
for aid,r in ROOTS.items():
 parts=[]
 for o in r.children:
  if o.type in ['MESH','FONT']:
   parts.append({'part_id':o.name,'type':o.type,'dimensions_m':[round(float(v),10) for v in o.dimensions],'translation_m':list(o.location),'rotation_quaternion_xyzw':[o.rotation_euler.to_quaternion()[i] for i in [1,2,3,0]],'scale':list(o.scale),'geometry_basis':o.get('geometry_basis','original_authored'),'source_dimension_status':'authored_unqualified','source_asset_family':o.get('source_asset_family'),'source_part_id':o.get('source_part_id')})
 assets.append({'asset_id':aid,'instance_id':aid+'.01','role':r['role'],'source_evidence_ids':r['source_evidence_ids'].split(','),'operation_ids':r['operation_ids'].split(','),'display_scale':1,'coordinate_space':'MAIN_AUTHORED_METRIC','physical_qualified_transform':None,'parts':parts})
(OUT/'asset_inventory.json').write_text(json.dumps({'schema':'sucrose_original_scene.v1','units':'m','main_scene_group_count':6,'unique_asset_count':None,'counting_policy':'Do not infer unique designs from groups, mesh parts, repeated vials, labels or GLB exports. Reused AFM carrier/clamps receive zero new unique-asset credit.','reused_families':['afm.sample_carrier','afm.retention_clamps'],'assets':assets},indent=2))
(OUT/'affordances.json').write_text(json.dumps({'implementation':'metadata_only','qualified_robot_poses':False,'collision_meshes_supplied':False,'anchors':ANCHORS},indent=2))
(OUT/'materials/materials.json').write_text(json.dumps([{'id':m.name,'base_color':list(m.diffuse_color),'appearance_only':True,'measured_optical_properties':False} for m in M.values()],indent=2))
# Separate original information display. Equal-size cards deliberately do not encode volume.
DISPLAY=bpy.data.scenes.new('DISPLAY_ONLY_NOT_TO_SCALE');DISPLAY.world=MAIN.world.copy();sc=DISPLAY;bpy.context.window.scene=sc;setup(sc)
CUR=bpy.data.objects.new('DISPLAY.volume_lineage',None);sc.collection.objects.link(CUR);CUR['display_only']=True;CUR['physical_scale']=False;CUR['non_proportional_cards']=True;CUR['source_asset_reference']='A_CARTRIDGE_SERVICE'
box('display.base',(0,0,.04),(1.64,.71,.06),'ivory',.015)
text('display.title','THREE VOLUMES. THREE MEANINGS.',(-.72,-.272,.077),.035,'navy',True)
text('display.warning','DISPLAY ONLY / EQUAL CARDS ARE NOT VOLUME-SCALED',(-.70,-.333,.077),.017,'navy',True)
for i,(big,title,line2,col) in enumerate([('22 uL','CHAMBER','nominal capacity','teal'),('~300 pL','OPTICAL REGION','interrogated subset','cyan'),('UNKNOWN','HANDLING VOLUME','must be qualified','amber')]):
 x=-.51+i*.51;box('display.card.'+str(i),(x,.08,.25),(.47,.035,.30),'navy',.01)
 text('display.number.'+str(i),big,(x-.20,.059,.315),.052 if i<2 else .040,col)
 text('display.kind.'+str(i),title,(x-.20,.059,.241),.025,'white')
 text('display.note.'+str(i),line2,(x-.20,.059,.196),.021,'white')
text('display.facts','300 pL is not the entire sample. Neither reported volume defines transfer requirements.',(-.716,-.045,.111),.017,'navy')
CUR=None
box('display.studio.floor',(0,0,-.044),(200,200,.04),'floor',0)
light('DISPLAY.light',(-1,-1,2.5),350,2,(0,0,.2));light('DISPLAY.fill',(1.5,0,1.8),200,1.5,(0,0,.2))
DISPLAY.camera=camera('CAM.volume_lineage',(1.0,-2.5,1.65),(0,0,.18),1.90)
# Save native editable scenes before label mesh conversion.
bpy.context.window.scene=MAIN
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'geometry/sucrose_operations_lab.blend'))
# Native scene retains FONTs. Export snapshots convert only in this process.
for scene,path in [(MAIN,'sucrose_operations_lab.glb'),(DISPLAY,'sucrose_volume_lineage_display.glb')]:
 bpy.context.window.scene=scene
 for o in list(scene.objects):
  if o.type=='FONT':
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 bpy.ops.object.select_all(action='DESELECT')
 for o in scene.objects:
  if o.type in ['MESH','EMPTY'] and 'studio.floor' not in o.name:o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(OUT/'geometry'/path),export_format='GLB',use_selection=True,use_active_scene=True,export_apply=True,export_extras=True)
views=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['overview','cartridge_service','volume_lineage']
for view in views:
 scene=DISPLAY if view=='volume_lineage' else MAIN;bpy.context.window.scene=scene
 scene.camera=DISPLAY.camera if view=='volume_lineage' else CAMS[view]
 scene.render.filepath=str(OUT/'evidence'/f'{view}.png');bpy.ops.render.render(write_still=True)
print('SUCROSE_ASSET_BUILD_COMPLETE')
