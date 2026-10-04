"""Original generic woven role scene, reconstructed from retained author commands.
No source art, CAD, source code, physics or device IO. Closed service roles only.
"""
import bpy, math, json, sys, hashlib, struct
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[1]
PLAN=json.loads((OUT/'task_binding_snapshot.json').read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.materials):bpy.data.materials.remove(d)
MAIN=bpy.context.scene;MAIN.name='WOVEN_AUTHORED_METRIC';sc=MAIN
ROOTS={};CUR=None;ANCHORS=[]
def setup(s):
 s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
 s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=64;s.cycles.use_denoising=False
 s.render.resolution_x=1600;s.render.resolution_y=1100;s.render.resolution_percentage=100
 s.render.image_settings.file_format='PNG';s.render.filepath='//renders/';s.render.use_stamp_filename=False;s.world.color=(.15,.17,.20)
 s.view_settings.view_transform='AgX';s.view_settings.exposure=-1.0
setup(sc)
def mat(n,c,metal=0,rough=.38):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 return m
M={'ivory':mat('Porcelain | appearance only',(.79,.86,.86),.1),'navy':mat('Deep petrol | appearance only',(.018,.062,.08),.55),'teal':mat('Teal | appearance only',(.025,.42,.43),.3),'amber':mat('Amber disabled | appearance only',(.95,.40,.06),.25),'steel':mat('Steel | appearance only',(.42,.54,.60),.7),'black':mat('Graphite | opaque',(.014,.025,.03),0,.5),'white':mat('White typography',(.94,.97,.95),0,.6),'cyan':mat('Blue closed service | opaque',(.23,.60,.71),.2),'floor':mat('Studio floor',(.73,.80,.83),0,.9),'gold':mat('Brass | appearance only',(.69,.42,.12),.7)}
def root(aid):
 global CUR
 a=next(a for a in PLAN['scene_assets'] if a['asset_id']==aid);o=bpy.data.objects.new(aid,None);sc.collection.objects.link(o);o.empty_display_size=.03
 for k,v in {'asset_id':aid,'asset_version':'1.0.0','role':a['role'],'authored_dimension_status':'unqualified_authored_metres','physical_execution':False,'device_io':False,'energy_enabled':False,'display_only':False,'operation_ids':','.join(a['bind_operation_ids'])}.items():o[k]=v
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
  b=o.modifiers.new('Authored edge radius','BEVEL');b.width=min(bevel,min(d)/3);b.segments=3;o.modifiers.new('Weighted visual normals','WEIGHTED_NORMAL')
 return o
def cyl(n,p,r,h,m='steel',axis='Z',vertices=32):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=h,location=p);o=bpy.context.object
 if axis=='Y':o.rotation_euler.x=math.pi/2
 if axis=='X':o.rotation_euler.y=math.pi/2
 finish(o,n,m)
 for f in o.data.polygons:f.use_smooth=True
 return o
def rod(n,a,b,r=.003,m='steel'):
 o=cyl(n,(Vector(a)+Vector(b))/2,r,(Vector(a)-Vector(b)).length,m);o.rotation_euler=(Vector(b)-Vector(a)).to_track_quat('Z','Y').to_euler();return o
def txt(n,s,p,size=.017,m='white',flat=False):
 c=bpy.data.curves.new(n,'FONT');c.body=s;c.size=size;c.extrude=.00008;c.space_character=1.05
 o=bpy.data.objects.new(n,c);sc.collection.objects.link(o);o.location=p
 if not flat:o.rotation_euler=(math.pi/2,0,0)
 return finish(o,n,m)
def label(n,s,p,w=.32,h=.046,size=.014,m='navy'):
 box(n+'.plate',p,(w,.005,h),m,.002);txt(n+'.text',s,(p[0]-w*.455,p[1]-.003,p[2]-.006),size)
def anchor(a,p,t,meaning='Canonical visual-role anchor; unqualified authored pose; metadata only'):
 n=CUR.name+'.'+a;o=bpy.data.objects.new(n,None);sc.collection.objects.link(o);o.parent=CUR;o.location=p;o.empty_display_type='ARROWS';o.empty_display_size=.018
 o['anchor_id']=a;o['coordinate_status']='authored_unqualified';o['interaction']='metadata_only';o['target_object']=t
 ANCHORS.append({'asset_id':CUR.name,'anchor_id':a,'scene_object':n,'target_object':t,'translation_m':list(p),'rotation_quaternion_xyzw':[0,0,0,1],'coordinate_status':'authored_unqualified','physical_qualified_transform':None,'meaning':meaning,'allowed_tool':'metadata selector only','precondition':'identity bound and independent external qualification required','postcondition':'local metadata only','failure_stop':'missing, mismatched or stale qualification/evidence; energy request refused','collision_representation':'none','physical_execution':False})
def camera(n,p,target,scale):
 c=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,c);sc.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();c.type='ORTHO';c.ortho_scale=scale;c.clip_start=.000001;c.clip_end=100;return o
def light(n,p,power,size,target):
 d=bpy.data.lights.new(n,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(n,d);sc.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
root('A_DESIGN_CONSOLE')
box('bench.base',(0,.02,.052),(1.94,1.13,.09),'ivory',.018)
box('bench.top',(0,.02,.108),(1.9,1.09,.022),'steel',.006)
label('bench.title','WOVEN MICROSTRUCTURES / ORIGINAL STATIC RESEARCH SCENE',(0,-.554,.05),1.82,.05,.023)
box('design.body',(-.68,.39,.282),(.40,.20,.325),'navy',.013)
box('design.face',(-.68,.283,.292),(.355,.014,.256),'black',.004)
txt('design.title','DESIGN / TOPOLOGY',(-.838,.272,.39),.020)
txt('design.roles','BCC + CUBIC ROLES',(-.838,.272,.349),.017,'cyan')
txt('design.no_cad','NO PAPER-EXACT CAD',(-.838,.272,.307),.014)
txt('design.conflict','TETRAKAIDECAHEDRON: HOLD',(-.838,.272,.263),.011,'amber')
txt('design.no_nodes','NO SOURCE NODE GEOMETRY',(-.838,.272,.220),.011)
for key,z in [('design_record',.39),('topology_card',.349),('conflict_hold',.263)]:anchor(key,(-.68,.268,z),'design.face')
def service(aid,p,prefix,title,sub,receipt_keys):
 root(aid);x,y=p
 box(prefix+'.body',(x,y,.244),(.31,.23,.25),'ivory',.010)
 box(prefix+'.sealed_door',(x,y-.123,.254),(.274,.012,.185),'navy',.003)
 txt(prefix+'.title',title,(x-.124,y-.132,.315),.016)
 txt(prefix+'.closed','CLOSED SERVICE',(x-.124,y-.132,.28),.013,'amber')
 txt(prefix+'.detail',sub,(x-.124,y-.132,.243),.0105)
 txt(prefix+'.disabled','NO ACTUATION',(x-.124,y-.132,.207),.011)
 for i,key in enumerate(receipt_keys):anchor(key,(x-.105+i*.21/max(1,len(receipt_keys)-1),y-.135,.25),prefix+'.sealed_door')
service('A_FABRICATION_SERVICE',(-.24,.41),'fab','FAB / DEVELOPMENT','EXTERNAL RECEIPTS ONLY',['design_in','fabrication_receipt','development_receipt','sample_out'])
service('A_CPD_SERVICE',(.11,.41),'cpd','CRITICAL-POINT DRY','SEALED RECEIPT DOCK',['sample_in','cpd_receipt','sample_out'])
service('A_COATING_SERVICE',(.46,.41),'coat','GOLD COATING','10 nm SOURCE FACT ONLY',['sample_in','coating_receipt','sample_out'])
service('A_PLASMA_SERVICE',(-.69,.06),'plasma','SUPPORT REMOVAL','PLASMA / CLOSED SERVICE',['sample_in','closed_chamber','removal_receipt','sample_out'])
root('A_MICROCARRIER')
box('carrier.dock',(-.67,-.28,.141),(.40,.35,.05),'navy',.008)
box('carrier.base',(-.67,-.28,.185),(.29,.21,.035),'teal',.006)
box('carrier.recess',(-.67,-.28,.206),(.23,.145,.009),'black',.003)
for x in [-.829,-.511]:box('carrier.grasp_tab',(x,-.28,.194),(.04,.075,.027),'steel',.004)
for x in [-.77,-.57]:
 for y in [-.33,-.23]:cyl('carrier.registration_pin',(x,y,.22),.006,.022,'gold',vertices=16)
box('carrier.closed_case',(-.67,-.28,.243),(.17,.10,.065),'ivory',.005)
box('carrier.opaque_lid',(-.67,-.28,.28),(.18,.11,.01),'navy',.002)
txt('carrier.identity','WVN-001',(-.728,-.297,.286),.015,'white',True)
txt('carrier.sealed','SEALED',(-.718,-.265,.286),.012,'amber',True)
label('carrier.label','GENERIC CARRIER / FIT UNQUALIFIED',(-.67,-.461,.16),.40,.036,.0104)
box('native.cell_reference',(-.67,-.28,.288),(60e-6,60e-6,60e-6),'cyan',0)['reference_only']=True
cyl('native.fiber_radius_reference',(-.67+80e-6,-.28,.288),1e-6,60e-6,'gold',vertices=32)['reference_only']=True
for key,p,t in [('sample_origin',(-.67,-.28,.243),'carrier.closed_case'),('carrier_slot',(-.67,-.28,.206),'carrier.recess'),('identity_card',(-.67,-.28,.286),'carrier.identity'),('grasp_left',(-.829,-.28,.194),'carrier.grasp_tab'),('grasp_right',(-.511,-.28,.194),'carrier.grasp_tab.001'),('native_cell_reference',(-.67,-.28,.288),'native.cell_reference')]:anchor(key,p,t)
root('A_TENSION_FIXTURE')
box('tension.base',(-.15,-.25,.147),(.43,.37,.058),'navy',.007)
for x in [-.31,.01]:cyl('tension.static_post',(x,-.16,.315),.014,.28,'steel');cyl('tension.post_cap',(x,-.16,.461),.019,.012,'gold')
box('tension.bridge',(-.15,-.16,.44),(.37,.063,.035),'ivory',.005)
box('tension.lower_grip',(-.15,-.26,.214),(.095,.08,.055),'teal',.003)
box('tension.upper_grip',(-.15,-.26,.365),(.095,.08,.055),'teal',.003)
box('tension.empty_gap',(-.15,-.185,.29),(.10,.006,.012),'black',.001)['specimen_present']=False
box('tension.silicon_support_role',(-.15,-.26,.245),(.13,.105,.008),'black',.001)
txt('tension.substrate_label','SILICON BASE ROLE',(-.325,-.388,.182),.010,'white',True)
txt('tension.grip_label','TOP FIXTURE GRIP / AUTHORED',(-.325,-.357,.182),.0085,'white',True)
rod('tension.inactive_spindle',(-.15,-.16,.44),(-.15,-.16,.50),.009,'steel')
label('tension.label','TENSION FIXTURE / DISABLED',(-.15,-.444,.17),.43,.035,.012)
txt('tension.no_motion','EMPTY / NO FIBER CONTACT',(-.326,-.411,.192),.011,'amber',True)
for key,p,t in [('fixture_origin',(-.15,-.25,.147),'tension.base'),('lower_grip',(-.15,-.26,.241),'tension.lower_grip'),('upper_grip',(-.15,-.26,.338),'tension.upper_grip'),('alignment_record',(-.15,-.26,.291),'tension.empty_gap'),('disabled_state',(-.15,-.448,.17),'tension.label.plate')]:anchor(key,p,t)
root('A_SEM_HOLDER')
box('sem.dock',(.37,-.28,.147),(.43,.35,.058),'navy',.007)
cyl('sem.holder_body',(.37,-.26,.211),.124,.065,'steel',vertices=48)
cyl('sem.opaque_cover',(.37,-.26,.256),.127,.025,'ivory',vertices=48)
for ang in [0,math.pi/2,math.pi,3*math.pi/2]:cyl('sem.lid_fastener',(.37+.108*math.cos(ang),-.26+.108*math.sin(ang),.271),.005,.008,'gold',vertices=12)
txt('sem.identity','WVN-001',(.315,-.293,.273),.015,'navy',True)
txt('sem.closed','SEALED',(.326,-.259,.273),.012,'navy',True)
label('sem.label','SEM HOLDER / CLOSED SERVICE',(.37,-.461,.164),.43,.036,.011)
for key,p,t in [('holder_slot',(.37,-.26,.18),'sem.holder_body'),('closed_cover',(.37,-.26,.269),'sem.opaque_cover'),('identity_card',(.37,-.26,.273),'sem.identity'),('acquisition_record',(.37,-.464,.164),'sem.label.plate')]:anchor(key,p,t)
root('A_ACQUISITION_RECORDS')
box('records.body',(.78,.05,.29),(.25,.30,.33),'navy',.012)
box('records.face',(.78,-.107,.302),(.22,.014,.25),'black',.003)
txt('records.title','EXTERNAL RECORDS',(.681,-.117,.393),.013)
for key,z,caption in [('mechanical_record',.351,'LOAD / DISPLACEMENT'),('sem_record',.306,'SEM IMAGE ID'),('timebase_record',.261,'SYNC / LINEAGE ID'),('calibration_record',.216,'CALIBRATION ID')]:txt('records.'+key,caption,(.681,-.117,z),.0105,'cyan');anchor(key,(.78,-.119,z),'records.face')
root('A_ANALYSIS_CONSOLE')
box('analysis.body',(.72,.41,.26),(.19,.20,.28),'teal',.009)
box('analysis.face',(.72,.303,.272),(.166,.014,.211),'black',.003)
txt('analysis.title','ANALYSIS',(.646,.292,.352),.014)
txt('analysis.no_data','NO DATA',(.646,.292,.307),.014,'amber')
txt('analysis.no_model','NO SOLVER',(.646,.292,.26),.011)
txt('analysis.empty','EMPTY',(.646,.292,.215),.014)
for key,z in [('analysis_record',.307),('numerical_record',.26),('archive_slot',.215)]:anchor(key,(.72,.289,z),'analysis.face')
root('A_HOLD_PANEL')
box('hold.panel',(.06,.155,.61),(.71,.02,.155),'navy',.007)
txt('hold.title','PERMANENT EXECUTION HOLD',(-.27,.141,.654),.025,'amber')
txt('hold.detail','NO CHEMISTRY / PLASMA / CPD / SEM / LOADING',(-.27,.141,.616),.013)
txt('hold.records','RECORD LABELS NEVER ENABLE HARDWARE',(-.27,.141,.578),.014)
for key,x in [('qualification_hold',-.22),('topology_hold',-.04),('calibration_hold',.14),('lineage_hold',.30)]:anchor(key,(x,.14,.60),'hold.panel')
for x in [-.25,.37]:rod('hold.support',(x,.171,.12),(x,.171,.535),.008,'steel')
label('lineage.note','WVN-001 / CUSTODY LINEAGE ONLY',(.1,.03,.136),.70,.027,.012)
CUR=None
box('studio.floor',(0,0,-.02),(200,200,.02),'floor',0)
light('LIGHT.key',(-1.2,-1.5,2.7),490,1.8,(0,0,.23));light('LIGHT.fill',(2,-.3,1.9),270,1.9,(0,0,.25));light('LIGHT.rim',(-.2,1.8,2.4),500,1.7,(0,0,.25))
CAMS={'overview':camera('CAM.overview',(1.2,-2.9,2.0),(0,.02,.31),2.50),'package_handling':camera('CAM.package_handling',(-.85,-1.50,1.28),(-.25,-.24,.27),1.58)}
MAIN.camera=CAMS['overview'];bpy.context.view_layer.update()
assets=[]
for aid,r in ROOTS.items():
 parts=[]
 for o in r.children:
  if o.type in ['MESH','FONT','CURVE']:
   q=o.rotation_euler.to_quaternion();parts.append({'part_id':o.name,'type':o.type,'dimensions_m':list(o.dimensions),'translation_m':list(o.location),'rotation_quaternion_xyzw':[q.x,q.y,q.z,q.w],'scale':list(o.scale),'geometry_basis':o.get('geometry_basis','original_authored'),'physical_geometry_validated':False})
 assets.append({'asset_id':aid,'instance_id':aid+'.01','role':r['role'],'operation_ids':[x for x in r['operation_ids'].split(',') if x],'display_scale':1,'coordinate_space':'AUTHORED_METRIC','physical_qualified_transform':None,'parts':parts})
(OUT/'asset_inventory.json').write_text(json.dumps({'schema':'woven_original_scene.v1','units':'m','main_scene_group_count':len(assets),'unique_asset_count':None,'reused_mesh_count':0,'reused_new_unique_asset_credit':0,'assets':assets},indent=2)+'\n')
(OUT/'affordances.json').write_text(json.dumps({'implementation':'metadata_only','qualified_robot_poses':False,'anchors':ANCHORS},indent=2)+'\n')
(OUT/'materials/materials.json').write_text(json.dumps([{'id':m.name,'base_color':list(m.diffuse_color),'appearance_only':True,'measured_material_properties':False,'emission':False} for m in M.values()],indent=2)+'\n')
DISPLAY=bpy.data.scenes.new('DISPLAY_ONLY_1000X');DISPLAY.world=MAIN.world.copy();sc=DISPLAY;bpy.context.window.scene=sc;setup(sc)
CUR=bpy.data.objects.new('DISPLAY.woven_reference',None);sc.collection.objects.link(CUR);CUR['display_only']=True;CUR['reference_scale_factor']=1000;CUR['scale_applies_to']='cell and fiber reference dimensions only';CUR['paper_exact_geometry']=False
box('display.plinth',(0,0,.012),(.285,.155,.02),'ivory',.005)
def polycurve(name,points,r,material):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=2;s=c.splines.new('POLY');s.points.add(len(points)-1)
 for p,v in zip(s.points,points):p.co=(*v,1)
 o=bpy.data.objects.new(name,c);sc.collection.objects.link(o);finish(o,name,material);o['paper_exact_geometry']=False;o['connectivity_qualified']=False;o['display_only']=True;return o
def beamrole(prefix,a,b,strands):
 a,b=Vector(a),Vector(b);axis=(b-a).normalized();u=axis.cross(Vector((0,0,1)))
 if u.length<.01:u=axis.cross(Vector((0,1,0)))
 u.normalize();v=axis.cross(u).normalized()
 for j in range(strands):
  points=[]
  for k in range(49):
   t=.10+.80*k/48;theta=2*math.pi*(1.0*t+j/strands)
   p=a+(b-a)*t+.003*(math.cos(theta)*u+math.sin(theta)*v);points.append(tuple(p))
  polycurve(prefix+'.strand.'+str(j),points,.001,['teal','gold','cyan','navy'][j])
for kind,cx,strands in [('BCC',-.072,3),('CUBIC',.072,4)]:
 z=.054;corners=[Vector((cx+x*.03,y*.03,z+k*.03)) for x in [-1,1] for y in [-1,1] for k in [-1,1]]
 if kind=='BCC':edges=[(p,Vector((cx,0,z))) for p in corners]
 else:edges=[(a,b) for i,a in enumerate(corners) for b in corners[i+1:] if sum(abs(a[k]-b[k])>.0001 for k in range(3))==1]
 for i,(a,b) in enumerate(edges):beamrole('display.'+kind+'.beam.'+str(i),a,b,strands)
 mesh=bpy.data.meshes.new('display.'+kind+'.reference_mesh');mesh.from_pydata([tuple(p) for p in corners],[(i,j) for i,a in enumerate(corners) for j,b in enumerate(corners) if i<j and sum(abs(a[k]-b[k])>.0001 for k in range(3))==1],[]);mesh.update()
 o=bpy.data.objects.new('display.'+kind+'.cell_reference',mesh);sc.collection.objects.link(o);finish(o,o.name);o['native_cell_m']=60e-6;o['scale_factor']=1000;o['reference_only']=True
 label('display.'+kind+'.label',kind+'-LIKE / OPEN NODES',(cx,-.082,.016),.133,.017,.0063)
 rod('display.'+kind+'.width',(cx-.03,-.042,.025),(cx+.03,-.042,.025),.0006,'steel')
 txt('display.'+kind+'.size','60 um native / 60 mm display',(cx-.049,-.058,.026),.0047,'navy',True)
 txt('display.'+kind+'.count',str(strands)+' STRAND BEAM ROLE',(cx-.046,.050,.026),.005,'navy',True)
cyl('display.fiber_radius_reference',(0,-.047,.027),.001,.02,'gold',vertices=32)['native_radius_m']=1e-6
box('display.info_panel',(0,.091,.121),(.292,.005,.091),'navy',.003)
txt('display.info_title','1000x DIMENSIONAL REFERENCES',(-.132,.087,.148),.009,'white')
txt('display.original','ORIGINAL GENERIC ILLUSTRATIONS',(-.132,.087,.132),.007,'cyan')
txt('display.not_exact','NOT PAPER-EXACT / NOT CONNECTIVITY QUALIFIED',(-.132,.087,.115),.0058)
txt('display.no_physics','NO SIMULATED STRESS / STRAIN / CONTACT',(-.132,.087,.099),.006,'amber')
txt('display.hold','TETRAKAIDECAHEDRON: CONFLICT HOLD',(-.132,.087,.083),.006,'amber')
CUR=None
box('display.studio.floor',(0,0,-.02),(200,200,.02),'floor',0)
light('DISPLAY.key',(-.3,-.4,.7),45,.7,(0,0,.06));light('DISPLAY.fill',(.5,-.1,.4),20,.5,(0,0,.06));light('DISPLAY.rim',(0,.4,.5),30,.5,(0,0,.1))
DISPLAY.camera=camera('CAM.measurement',(.18,-.48,.35),(0,.016,.079),.405)
for screen in bpy.data.screens:
 for area in screen.areas:
  for space in area.spaces:
   if space.type=='FILE_BROWSER' and space.params:space.params.directory=b'//'
bpy.context.window.scene=MAIN;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'geometry/woven_material_lab.blend'))
for scene,path in [(MAIN,'woven_material_lab.glb'),(DISPLAY,'woven_reference_display.glb')]:
 bpy.context.window.scene=scene
 for o in list(scene.objects):
  if o.type in ['FONT','CURVE']:
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 bpy.ops.object.select_all(action='DESELECT')
 for o in scene.objects:
  if o.type in ['MESH','EMPTY'] and 'studio.floor' not in o.name:o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(OUT/'geometry'/path),export_format='GLB',use_selection=True,use_active_scene=True,export_apply=True,export_extras=True,use_mesh_edges=True)
views=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['overview','package_handling','measurement']
receipt={'engine':'CYCLES','device':'CPU','blender_version':bpy.app.version_string,'samples':MAIN.cycles.samples,'resolution':[1600,1100],'views':[],'source_pixels_used':False}
for view in views:
 scene=DISPLAY if view=='measurement' else MAIN;bpy.context.window.scene=scene
 if view!='measurement':scene.camera=CAMS[view]
 scene.render.filepath=str(OUT/'evidence'/f'{view}.png');bpy.ops.render.render(write_still=True)
 p=OUT/'evidence'/f'{view}.png'
 # Remove PNG text metadata only; retain all image data chunks byte-for-byte.
 raw=p.read_bytes();clean=raw[:8];offset=8
 while offset<len(raw):
  length=struct.unpack('>I',raw[offset:offset+4])[0];kind=raw[offset+4:offset+8];chunk=raw[offset:offset+length+12]
  if kind not in [b'tEXt',b'zTXt',b'iTXt']:clean+=chunk
  offset+=length+12
 p.write_bytes(clean);receipt['nonpixel_metadata_sanitized']=True
 receipt['views'].append({'id':view,'scene':scene.name,'camera':scene.camera.name,'file':'evidence/'+p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'actual_render':True})
if views:(OUT/'review/render_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('WOVEN_ASSET_BUILD_COMPLETE')
