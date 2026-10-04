"""Original generic actuator metrology scene. No source artwork, CAD or optical reconstruction.
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
MAIN=bpy.context.scene;MAIN.name='ACTUATOR_AUTHORED_METRIC';sc=MAIN
ROOTS={};CUR=None;ANCHORS=[]

def setup(scene):
 scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=False
 scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
 scene.render.image_settings.file_format='PNG';scene.world.color=(.15,.17,.20)
 scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-1.0
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

# Seven stable semantic groups. Scientific shape and performance are not reconstructed.
root(PLAN['scene_assets'][0])
box('bench.base',(0,0,.052),(1.28,.76,.09),'ivory',.016)
box('bench.top',(0,0,.107),(1.23,.72,.019),'steel',.006)
label('bench.title','ACTUATOR METROLOGY / STATIC ASSETS',(0,-.386,.06),1.17,.045,.023)
box('compute.body',(-.46,.19,.246),(.25,.16,.24),'navy',.012)
box('compute.screen',(-.46,.102,.268),(.213,.014,.164),'black',.002)
text('compute.title','RESEARCH ONLY',(-.551,.092,.317),.015)
text('compute.no_code','NO SOURCE CODE',(-.551,.092,.276),.012,'amber')
text('compute.no_result','NO OPTIMIZATION',(-.551,.092,.248),.012)
text('compute.state','NO RESULTS',(-.551,.092,.222),.012)
anchor('reference',(-.46,.09,.27),'compute.screen','Research metadata boundary; no copied algorithm or code')
root(PLAN['scene_assets'][1])
box('fabrication.closed_service',(.44,.20,.245),(.25,.22,.25),'ivory',.013)
box('fabrication.sealed_door',(.44,.084,.257),(.205,.014,.171),'navy',.004)
text('fabrication.title','FABRICATION',(.347,.073,.310),.015)
text('fabrication.closed','CLOSED SERVICE',(.347,.073,.272),.013,'amber')
text('fabrication.no_recipe','NO PRINT RECIPE',(.347,.073,.235),.012)
cyl('fabrication.seal',(.518,.070,.206),.012,.008,'gold','Y',12)
anchor('closed_handoff',(.44,.07,.25),'fabrication.sealed_door','No manufacturing geometry, recipe or device IO supplied')
root(PLAN['scene_assets'][2])
box('carrier.dock',(-.40,-.16,.136),(.285,.255,.041),'navy',.007)
reuse=json.loads((OUT/'geometry/reused_carrier_components.json').read_text());origin=(-.4,-.16,.168)
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
text('carrier.identity','A-001 / CARRIER EMPTY',(-.50,-.239,.180),.009,'white',True)
label('carrier.label','CUSTODY / NO FIT QUALIFICATION',(-.40,-.297,.142),.31,.034,.010)
anchor('carrier_datum',(-.4,-.16,.177),'reuse.carrier.loaded.base','Empty source-family carrier; native geometry retained; not a validated actuator fit')
anchor('grasp_left',(-.503,-.16,.177),'reuse.carrier.loaded.grasp_tab','Authored visual handling anchor, not robot qualified')
anchor('grasp_right',(-.297,-.16,.177),'reuse.carrier.loaded.grasp_tab.001','Authored visual handling anchor, not robot qualified')
# Native-size independent diamond lattice; one displayed specimen, not optimized.
# Beam mesh contains repeated rectangular prisms; no FEA connectivity, deformation or material model.
def beam_mesh(n,a,b,w,depth,m):
 a=Vector(a);b=Vector(b);v=b-a;side=Vector((v.z,0,-v.x)).normalized()*w/2;dep=Vector((0,depth/2,0));verts=[a-side-dep,a+side-dep,b+side-dep,b-side-dep,a-side+dep,a+side+dep,b+side+dep,b-side+dep]
 mesh=bpy.data.meshes.new(n);mesh.from_pydata(verts,[],[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]);mesh.update();o=bpy.data.objects.new(n,mesh);sc.collection.objects.link(o);return finish(o,n,m)
def lattice(prefix,origin,scale=1):
 pieces=[];x,y,z=origin
 for i in range(6):
  for j in range(4):
   cx=x+(-.035+i*.014)*scale;cz=z+(j*.014+.007)*scale;dx=.007*scale;dz=.007*scale
   pts=[(cx-dx,y,cz),(cx,y,cz+dz),(cx+dx,y,cz),(cx,y,cz-dz)]
   for k in range(4):pieces.append(beam_mesh(prefix+'.cell.%d.%d.%d'%(i,j,k),pts[k],pts[(k+1)%4],.0014*scale,.004*scale,'teal'))
 pieces.append(box(prefix+'.base',(x,y,z-.003*scale),(.088*scale,.004*scale,.006*scale),'teal',0))
 for o in pieces:o['representative_only']=True;o['optimized_design']=False;o['material_physics']=False;o['geometry_basis']='original_generic_diamond_lattice'
 return pieces
LATTICE=lattice('actuator_specimen_representative',(0,.015,.224))
anchor('specimen',(0,.015,.25),'actuator_specimen_representative.base','Authored generic diamond lattice; no source-geometry or response equivalence')
root(PLAN['scene_assets'][3])
box('metrology_base',(0,-.02,.143),(.29,.27,.052),'navy',.006)
box('fixture.backbone',(0,.076,.226),(.18,.023,.153),'steel',.003)
box('actuator_fixed_clamp',(0,.015,.216),(.098,.018,.019),'navy',.002)
for x in [-.038,.038]:cyl('fixture.clamp_screw',(x,.003,.214),.006,.007,'gold','Y',24)
box('input_displacement_stage',(.095,.011,.239),(.037,.040,.138),'steel',.003)
box('stage.rail',(.095,-.013,.247),(.012,.007,.100),'navy',.001)
box('stage.carriage',(.095,-.021,.275),(.035,.014,.025),'ivory',.002)
rod('stage.noncontact_link',(.083,-.021,.275),(.055,-.021,.275),.003,'steel')
box('actuator_moving_clamp',(.051,-.021,.275),(.012,.012,.012),'amber',.001)
text('stage.no_contact','GAP',(.046,-.030,.299),.007,'navy')
cyl('stage.handwheel',(.095,.011,.319),.021,.009,'navy')
cyl('stage.handwheel_hub',(.095,.011,.328),.009,.014,'gold')
label('fixture.label','SOURCE INPUT: 5 mm / STATIC REFERENCE',(0,-.163,.147),.37,.036,.0105)
# The two reference bars are exactly 5 mm apart. They do not show an applied displacement.
for i in [0,1]:box('reference_5mm.endpoint.'+str(i),(.133,-.04,.246+i*.005),(.012,.002,.0007),'amber',0)
rod('reference_5mm.length',(.133,-.04,.246),(.133,-.04,.251),.0006,'amber')
text('reference_5mm.label','5 mm',(.138,-.042,.247),.006,'navy')
for a,p,t,msg in [('dock',(0,.015,.207),'actuator_fixed_clamp','Authored fixture datum; no clearance qualification'),('fixed_base',(0,.003,.214),'actuator_fixed_clamp','Visual holder only; fixing requires qualified external evidence'),('input_stage',(.095,-.027,.275),'stage.carriage','Noncontact parked stage; no actuator input delivered'),('unloaded',(.051,-.03,.275),'actuator_moving_clamp','No force or unloading inference from parked appearance'),('source_5mm',(.133,-.04,.2485),'reference_5mm.length','Source 5 mm reference only; does not imply physically applied input')]:anchor(a,p,t,msg)
root(PLAN['scene_assets'][4])
box('camera_metrology',(.0,-.28,.222),(.073,.047,.048),'navy',.004)
cyl('camera.lens',(0,-.244,.222),.025,.026,'black','Y')
cyl('camera.opaque_lens_cap',(0,-.229,.222),.021,.006,'cyan','Y')
rod('camera.post',(0,-.28,.131),(0,-.28,.198),.009,'steel')
box('camera.foot',(0,-.28,.126),(.095,.074,.020),'ivory',.003)
text('camera.state','NO IMAGE',(-.029,-.306,.226),.007)
# Authored ruler shares specimen plane, with actual 1 mm tick spacing.
box('calibration_ruler',(-.065,.015,.253),(.020,.004,.074),'ivory',.001)
for i in range(61):
 z=.223+i*.001;box('ruler.tick.'+str(i),(-.068,.012,z),(.010 if i%10==0 else .006 if i%5==0 else .003,.0005,.00025),'navy',0)
for v in [0,20,40,60]:text('ruler.label.'+str(v),str(v),(-.061,.010,.222+v*.001),.0035,'navy')
text('ruler.unit','mm',(-.072,.010,.288),.004,'navy')
for n,x in [('input',.035),('output',-.035)]:
 cyl('target_marker_'+n,(x,.011,.280),.0032,.0015,'amber' if n=='input' else 'cyan','Y',24)
 for d in [-1,1]:box('marker.cross.'+n+'.'+str(d),(x,.010,.280),(.005 if d==1 else .0006,.0003,.0006 if d==1 else .005),'black',0)
for a,p,t,msg in [('camera',(0,-.228,.222),'camera.opaque_lens_cap','Generic camera shape; optical model and acquisition unavailable'),('calibration',(-.065,.01,.253),'calibration_ruler','Authored 60 mm reference, not calibrated hardware'),('input_target',(.035,.01,.280),'target_marker_input','Visual target designation only; not selected source node coordinates'),('output_target',(-.035,.01,.280),'target_marker_output','Visual target designation only; no output displacement')]:anchor(a,p,t,msg)
root(PLAN['scene_assets'][5])
box('records.console',(.43,-.15,.170),(.29,.22,.105),'navy',.010)
box('records.screen',(.43,-.265,.182),(.245,.008,.077),'black',.003)
text('records.title','BEFORE / AFTER / ID',(.323,-.271,.200),.012)
text('records.empty','NO ACQUISITION RECORD',(.323,-.271,.174),.010,'amber')
text('records.efficiency','EFFICIENCY: UNAVAILABLE',(.323,-.271,.154),.008)
anchor('record',(.43,-.27,.18),'records.screen','Metadata identity only; no scientific values or camera image emitted')
root(PLAN['scene_assets'][6])
box('hold.panel',(0,.22,.319),(.43,.021,.154),'navy',.008)
text('hold.title','DIRECTION: HOLD',(-.185,.205,.366),.025,'amber')
text('hold.conflict','FIG 2 / SUPP FIG 3 CONFLICT',(-.185,.205,.328),.014)
text('hold.no_default','NO AXIS MAP DEFAULT',(-.185,.205,.299),.017)
text('hold.static','STATIC ONLY / NO DEFORMATION',(-.185,.205,.269),.012)
anchor('direction_gate',(0,.20,.32),'hold.panel','Source direction discrepancy blocks all displacement mapping; acknowledgement does not resolve it')
# Canonical task anchors use group IDs independently of authored mesh IDs.
canonical = {
'A_COMPUTE_DESK': {'lattice_record':('compute.screen',(-.46,.09,.29)), 'run_record':('compute.screen',(-.46,.09,.26)), 'model_record':('compute.screen',(-.46,.09,.23))},
'A_FABRICATION_SERVICE': {'design_in':('fabrication.sealed_door',(.4,.07,.28)), 'job_status':('fabrication.sealed_door',(.44,.07,.25)), 'carrier_out':('fabrication.sealed_door',(.48,.07,.22))},
'A_SPECIMEN_CUSTODY': {'specimen_origin':('actuator_specimen_representative.base',(0,.015,.224)), 'carrier_slot':('reuse.carrier.loaded.base',(-.4,-.16,.177)), 'identity_card':('carrier.identity',(-.4,-.239,.18)), 'inspection_view':('actuator_specimen_representative.base',(0,-.01,.25))},
'A_DISPLACEMENT_FIXTURE': {'bottom_holder':('actuator_fixed_clamp',(0,.003,.214)), 'input_contact':('actuator_moving_clamp',(.051,-.03,.275)), 'input_origin':('stage.carriage',(.095,-.027,.275)), 'input_5mm_reference':('reference_5mm.length',(.133,-.04,.2485)), 'release_position':('actuator_moving_clamp',(.051,-.03,.275))},
'A_IMAGE_STATION': {'camera_view':('camera.opaque_lens_cap',(0,-.228,.222)), 'calibration_plane':('calibration_ruler',(-.065,.01,.253)), 'input_marker':('target_marker_input',(.035,.01,.28)), 'output_marker':('target_marker_output',(-.035,.01,.28)), 'base_marker':('calibration_ruler',(-.065,.01,.223))},
'A_RECORDS_CONSOLE': {'specimen_card':('records.screen',(.33,-.27,.18)), 'direction_card':('records.screen',(.38,-.27,.18)), 'calibration_card':('records.screen',(.43,-.27,.18)), 'run_card':('records.screen',(.48,-.27,.18)), 'archive_slot':('records.screen',(.53,-.27,.18))},
'A_HOLD_PANEL': {'direction_hold':('hold.panel',(-.15,.20,.32)), 'qualification_hold':('hold.panel',(-.075,.20,.32)), 'damage_hold':('hold.panel',(0,.20,.32)), 'image_hold':('hold.panel',(.075,.20,.32)), 'input_hold':('hold.panel',(.15,.20,.32))}}
for aid, entries in canonical.items():
 CUR=ROOTS[aid]
 for key,(target,point) in entries.items():anchor(key,point,target,'Canonical task visual-role anchor; authored and unqualified; no physical execution')
CUR=None
box('studio.floor',(0,0,-.02),(200,200,.02),'floor',0)
light('LIGHT.key',(-1.2,-1.4,2.3),320,1.7,(0,0,.22));light('LIGHT.fill',(1.6,-.3,1.5),150,1.5,(0,0,.22));light('LIGHT.rim',(-.3,1.5,2.2),350,1.6,(0,0,.22))
CAMS={'overview':camera('CAM.overview',(1.05,-1.9,1.20),(0,0,.22),1.63),'sample_handling':camera('CAM.sample_handling',(-.71,-.77,.81),(-.30,-.10,.21),.78),'measurement':camera('CAM.measurement',(.18,-.55,.355),(.02,.012,.252),.35)}
MAIN.camera=CAMS['overview'];bpy.context.view_layer.update()
assets=[]
for aid,r in ROOTS.items():
 parts=[]
 for o in r.children:
  if o.type in ['MESH','FONT']:
   q=o.rotation_euler.to_quaternion();parts.append({'part_id':o.name,'type':o.type,'dimensions_m':list(o.dimensions),'translation_m':list(o.location),'rotation_quaternion_xyzw':[q.x,q.y,q.z,q.w],'scale':list(o.scale),'geometry_basis':o.get('geometry_basis','original_authored'),'physical_geometry_validated':False,'source_part_id':o.get('source_part_id')})
 assets.append({'asset_id':aid,'instance_id':aid+'.01','role':r['role'],'operation_ids':r['operation_ids'].split(',') if r['operation_ids'] else [],'source_evidence_ids':r['source_evidence_ids'].split(',') if r['source_evidence_ids'] else [],'display_scale':1,'coordinate_space':'AUTHORED_METRIC','physical_qualified_transform':None,'parts':parts})
(OUT/'asset_inventory.json').write_text(json.dumps({'schema':'actuator_original_scene.v1','units':'m','main_scene_group_count':7,'unique_asset_count':None,'reused_mesh_count':15,'reused_new_unique_asset_credit':0,'assets':assets},indent=2)+'\n')
for a in ANCHORS:a.update({'allowed_tool':'metadata selector only','precondition':'identity bound and external qualification required','postcondition':'local metadata only','failure_stop':'unresolved direction, missing identity, stale evidence or absent adapter','collision_representation':'none','physical_execution':False})
(OUT/'affordances.json').write_text(json.dumps({'implementation':'metadata_only','qualified_robot_poses':False,'anchors':ANCHORS},indent=2)+'\n')
(OUT/'materials/materials.json').write_text(json.dumps([{'id':m.name,'base_color':list(m.diffuse_color),'appearance_only':True,'measured_material_properties':False} for m in M.values()],indent=2)+'\n')
# Separate 10x display copy of lattice. Native authored dimensions exist only in main scene.
DISPLAY=bpy.data.scenes.new('DISPLAY_ONLY_10X');DISPLAY.world=MAIN.world.copy();sc=DISPLAY;bpy.context.window.scene=sc;setup(sc)
CUR=bpy.data.objects.new('DISPLAY.representative_lattice',None);sc.collection.objects.link(CUR);CUR['display_only']=True;CUR['uniform_scale_factor']=10;CUR['native_scene']='ACTUATOR_AUTHORED_METRIC'
lattice('display.lattice',(0,.03,.16),10)
box('display.base',(0,.0,.064),(1.30,.40,.09),'ivory',.013)
label('display.title','GENERIC LATTICE / 10x DISPLAY',(0,-.208,.067),1.2,.048,.024)
for x,c,n in [(.35,'amber','INPUT'),(-.35,'cyan','OUTPUT')]:
 cyl('display.target.'+n,(x,.006,.72),.024,.011,c,'Y');text('display.target_label.'+n,n,(x-.065,-.01,.77),.021,'navy')
text('display.no_physics','ORIGINAL REPRESENTATIVE GEOMETRY',(-.52,-.08,.85),.028,'navy')
text('display.no_deformation','NO DEFORMATION / NO EFFICIENCY',(-.48,-.08,.12),.023,'navy')
for i in [0,1]:box('display.5mm.endpoint.'+str(i),(.51,.0,.37+i*.05),(.09,.004,.004),'amber',0)
rod('display.5mm.length',(.51,.0,.37),(.51,.0,.42),.003,'amber')
text('display.5mm.label','5 mm source',(.57,-.006,.40),.018,'navy');text('display.5mm.note','50 mm display',(.57,-.006,.37),.014,'navy')
CUR=None
box('display.studio.floor',(0,0,-.02),(200,200,.02),'floor',0)
light('DISPLAY.key',(-1,-1,2.2),300,1.8,(0,0,.4));light('DISPLAY.fill',(1,-.3,1.5),170,1.5,(0,0,.4))
DISPLAY.camera=camera('CAM.display',(1.3,-2.4,1.2),(.12,0,.43),1.7)
bpy.context.window.scene=MAIN;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'geometry/actuator_metrology_lab.blend'))
for scene,path in [(MAIN,'actuator_metrology_lab.glb'),(DISPLAY,'actuator_measurement_display.glb')]:
 bpy.context.window.scene=scene
 for o in list(scene.objects):
  if o.type=='FONT':
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 bpy.ops.object.select_all(action='DESELECT')
 for o in scene.objects:
  if o.type in ['MESH','EMPTY'] and 'studio.floor' not in o.name:o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(OUT/'geometry'/path),export_format='GLB',use_selection=True,use_active_scene=True,export_apply=True,export_extras=True)
views=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['overview','sample_handling','measurement']
receipt={'engine':'CYCLES','device':'CPU','blender_version':bpy.app.version_string,'samples':MAIN.cycles.samples,'resolution':[1600,1100],'views':[],'source_pixels_used':False}
for view in views:
 bpy.context.window.scene=MAIN;MAIN.camera=CAMS[view];MAIN.render.filepath=str(OUT/'evidence'/f'{view}.png');bpy.ops.render.render(write_still=True)
 p=OUT/'evidence'/f'{view}.png';receipt['views'].append({'id':view,'camera':MAIN.camera.name,'file':'evidence/'+p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'actual_render':True})
if views:(OUT/'review/render_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('ACTUATOR_ASSET_BUILD_COMPLETE')
