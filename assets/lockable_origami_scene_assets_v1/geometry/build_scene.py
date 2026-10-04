"""Original metric laboratory roles and source-dimension reference display.
No source CAD, figures, data, contact physics, or device I/O. Blender4.3 CPU.
"""
import bpy, math, json, sys, hashlib, struct
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[1]
PLAN=json.loads((OUT/'task_binding_snapshot.json').read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for s in list(bpy.data.scenes):
 if s!=bpy.context.scene: bpy.data.scenes.remove(s)
for m in list(bpy.data.materials):bpy.data.materials.remove(m)
MAIN=bpy.context.scene;MAIN.name='LOCKABLE_ORIGAMI_AUTHORED_METRIC';sc=MAIN;CUR=None;ROOTS={};ANCHORS=[];KIN=[]
def setup(s):
 s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
 s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=96;s.cycles.use_denoising=False
 s.render.resolution_x=1800;s.render.resolution_y=1200;s.render.resolution_percentage=100
 s.render.image_settings.file_format='PNG';s.render.filepath='//evidence/';s.render.use_stamp=False;s.render.use_stamp_filename=False
 s.world.color=(.22,.24,.26);s.view_settings.view_transform='AgX';s.view_settings.exposure=-1.3
setup(sc)
def material(n,c,metal=0,rough=.45):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
M={'navy':material('Petrol / authored apparatus',(.018,.059,.073),.25),'teal':material('Teal / generic role',(.022,.38,.34),.15),'paper':material('Warm paper / appearance only',(.77,.55,.31),0,.8),'cream':material('Ivory / authored apparatus',(.77,.84,.83),.1),'steel':material('Aluminum look / appearance only',(.47,.57,.62),.75),'amber':material('Amber / execution hold',(.95,.43,.05),.1),'black':material('Graphite',(.01,.019,.024),.1),'white':material('White type',(.94,.97,.93)),'cyan':material('Cyan / metadata role',(.28,.70,.79),.1),'floor':material('Light gray ground',(.60,.68,.73),0,.9),'band':material('Restraining band / role only',(.46,.18,.12),0,.8)}
def root(aid):
 global CUR
 spec=next(x for x in PLAN['scene_assets'] if x['asset_id']==aid);o=bpy.data.objects.new(aid,None);sc.collection.objects.link(o);o.empty_display_size=.02
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
  b=o.modifiers.new('Visual edge radius','BEVEL');b.width=min(bevel,min(d)/3);b.segments=3;o.modifiers.new('Visual weighted normals','WEIGHTED_NORMAL')
 return o
def cyl(n,p,r,h,m='steel',axis='Z'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r,depth=h,location=p);o=bpy.context.object
 if axis=='Y':o.rotation_euler.x=math.pi/2
 if axis=='X':o.rotation_euler.y=math.pi/2
 finish(o,n,m)
 for f in o.data.polygons:f.use_smooth=True
 return o
def rod(n,a,b,r=.003,m='steel'):
 o=cyl(n,(Vector(a)+Vector(b))/2,r,(Vector(b)-Vector(a)).length,m);o.rotation_euler=(Vector(b)-Vector(a)).to_track_quat('Z','Y').to_euler();return o
def txt(n,s,p,size=.013,m='white',flat=False):
 c=bpy.data.curves.new(n,'FONT');c.body=s;c.size=size;c.extrude=.00003;c.space_character=1.03;o=bpy.data.objects.new(n,c);sc.collection.objects.link(o);o.location=p
 if not flat:o.rotation_euler=(math.pi/2,0,0)
 return finish(o,n,m)
def label(n,s,p,w=.30,h=.035,size=.011,m='navy'):
 box(n+'.plate',p,(w,.006,h),m,.002);txt(n+'.text',s,(p[0]-w*.46,p[1]-.004,p[2]-.004),size)
def anchor(a,p,t,meaning='Original unqualified visual anchor; not robot pose, calibration or evidence'):
 n=CUR.name+'.'+a;o=bpy.data.objects.new(n,None);sc.collection.objects.link(o);o.parent=CUR;o.location=p;o.empty_display_type='ARROWS';o.empty_display_size=.01
 o['anchor_id']=a;o['target_object']=t;o['coordinate_status']='authored_unqualified';o['physical_execution']=False
 ANCHORS.append({'asset_id':CUR.name,'anchor_id':a,'scene_object':n,'target_object':t,'translation_m':list(p),'rotation_quaternion_xyzw':[0,0,0,1],'coordinate_status':'authored_unqualified','physical_qualified_transform':None,'meaning':meaning,'allowed_tool':'metadata selector only','precondition':'externally qualified identity, fit and role record','postcondition':'local metadata selection only','failure_stop':'missing or stale qualification, lineage or source evidence','collision_representation':'none','physical_execution':False})
def camera(n,p,target,scale):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);sc.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=scale;d.clip_start=.000001;d.clip_end=100;return o
def light(n,p,energy,size,target):
 d=bpy.data.lights.new(n,'AREA');d.energy=energy;d.shape='DISK';d.size=size;o=bpy.data.objects.new(n,d);sc.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def screen(prefix,p,w,h,title,lines):
 x,y,z=p;box(prefix+'.body',(x,y,z),(w,.08,h),'navy',.008);box(prefix+'.face',(x,y-.047,z),(w-.025,.012,h-.025),'black',.002)
 txt(prefix+'.title',title,(x-w*.43,y-.055,z+h*.33),w*.052,'cyan')
 for i,(s,col) in enumerate(lines):txt(prefix+'.line.'+str(i),s,(x-w*.43,y-.055,z+h*.12-i*h*.19),w*.043,col)
 return prefix+'.face'
def accordion(prefix,origin,angle,scale=1):
 # Original open chain: exact centerline link length, alternating rotations;
 # finite panels shortened at both ends, no calibrated physical hinge.
 L=.03*scale;W=.03*scale;t=.00021*scale;trim=.0005*scale;a=math.radians(angle);p=Vector(origin);verts=[list(p)];parts=[]
 for i in range(4):
  sign=1 if i%2==0 else -1;v=Vector((L*math.cos(a),0,sign*L*math.sin(a)));q=p+v
  o=box(prefix+'.panel.'+str(i),(p+q)/2,(L-2*trim,W,t),'paper',0);o.rotation_euler.y=-sign*a;o['proxy_snapshot_degrees']=angle;o['source_mode']=False
  if i<3:rod(prefix+'.virtual_hinge.'+str(i),q+Vector((0,-W*.52,0)),q+Vector((0,W*.52,0)),.00035*scale,'teal')
  parts.append(o.name);p=q;verts.append(list(p))
 KIN.append({'id':prefix,'angle_degrees':angle,'is_source_theta':False,'centerline_vertices_m':verts,'centerline_link_length_m':L,'visible_panel_length_m':L-2*trim,'panel_width_m':W,'panel_thickness_m':t,'panel_objects':parts,'source_mode':None,'locking_or_contact':False})
 return parts[0]
root('A_DESIGN_CONSOLE')
box('bench.base',(0,0,.06),(2.08,1.18,.10),'cream',.016);box('bench.top',(0,0,.12),(2.06,1.16,.025),'steel',.005)
label('bench.title','LOCKABLE ORIGAMI / ORIGINAL STATIC RESEARCH ROLES',(0,-.60,.065),1.98,.048,.023)
screen('design',(-.84,.44,.31),.33,.33,'DESIGN / SOURCE',[('NO SOURCE CAD','amber'),('TOPOLOGY: HOLD','white'),('A/O MODES NOT DRAWN','white')])
for key,z in [('design_record',.37),('mode_map',.30),('geometry_hold',.23)]:anchor(key,(-.84,.385,z),'design.face')
root('A_PAPERBOARD_CARRIER')
box('carrier.base',(-.78,-.31,.163),(.47,.42,.06),'navy',.009);box('carrier.tray',(-.78,-.31,.204),(.39,.31,.023),'teal',.005);box('carrier.recess',(-.78,-.31,.22),(.33,.245,.009),'black',.002)
for x in [-1.006,-.554]:box('carrier.grasp_tab',(x,-.30,.219),(.047,.08,.023),'steel',.004)
box('carrier.opaque_case',(-.78,-.33,.249),(.28,.17,.05),'cream',.004)
label('carrier.label','PAPERBOARD / FIT UNQUALIFIED',(-.78,-.531,.173),.47,.032,.012)
txt('carrier.identity','ORI-001 / LOT / MD-CD',(-.906,-.391,.277),.014,'navy',True)
# Genuine metric dimensional references; positions and rectangular topology authored.
NATIVE=box('native.paperboard_coupon',(-.87,-.28,.279),(.015,.015,.00021),'paper',0);NATIVE['source_thickness_m']=.00021;NATIVE['span_status']='authored 15 mm reference, not source panel topology'
STRIP=box('native.tensile_strip',(-.77,-.323,.279),(.24,.005,.00021),'paper',0);STRIP['source_dimensions_m']=[.24,.005,.00021];STRIP['not_gripped']=True
for key,p,t in [('sample_origin',(-.78,-.33,.25),'carrier.opaque_case'),('carrier_slot',(-.78,-.31,.22),'carrier.recess'),('identity_card',(-.78,-.391,.277),'carrier.identity'),('grasp_left',(-1.006,-.3,.219),'carrier.grasp_tab'),('grasp_right',(-.554,-.3,.219),'carrier.grasp_tab.001'),('sheet_reference',(-.87,-.28,.279),'native.paperboard_coupon')]:anchor(key,p,t)
root('A_CUT_SERVICE')
box('cut.enclosure',(-.44,.40,.275),(.36,.26,.285),'cream',.01);box('cut.closed_door',(-.44,.264,.281),(.31,.014,.21),'navy',.004)
txt('cut.title','LASER CUT SERVICE',(-.58,.252,.35),.016);txt('cut.closed','CLOSED / NO LASER',(-.58,.252,.303),.014,'amber');txt('cut.receipt','EXTERNAL RECEIPT',(-.58,.252,.257),.013);txt('cut.settings','NO TOOLPATH',(-.58,.252,.214),.013)
for key,x in [('design_in',-.56),('closed_enclosure',-.48),('cut_receipt',-.40),('sample_out',-.32)]:anchor(key,(x,.25,.29),'cut.closed_door')
root('A_FOLD_BOND_STATION')
box('fold.base',(-.22,-.30,.162),(.57,.42,.059),'navy',.008);box('fold.plate',(-.22,-.30,.203),(.53,.36,.023),'cream',.005)
for x in [-.46,.02]:
 for y in [-.43,-.16]:cyl('fold.registration_pin',(x,y,.239),.005,.05,'steel')
# Three side-by-side static visualization snapshots, no source closed cell or lock.
for i,(a,y) in enumerate([(0,-.18),(35,-.29),(65,-.40)]):
 span=4*.03*math.cos(math.radians(a));accordion('proxy.'+str(a),(-.22-span/2,y,.221),a)
 txt('proxy.label.'+str(a),str(a)+' DEG PROXY',(-.43,y-.021,.224),.011,'navy',True)
label('fold.label','ORIGINAL OPEN CHAIN / NO LOCK MODEL',(-.22,-.521,.175),.57,.032,.0118)
for key,p,t in [('sheet_in',(-.43,-.18,.23),'fold.plate'),('fold_support',(-.22,-.30,.216),'fold.plate'),('stack_alignment',(.02,-.16,.26),'fold.registration_pin.003'),('bond_record',(-.36,-.522,.176),'fold.label.plate'),('cure_record',(-.17,-.522,.176),'fold.label.plate'),('sample_out',(-.05,-.18,.23),'fold.plate')]:anchor(key,p,t)
root('A_RECONFIGURATION_FIXTURE')
box('reconfig.base',(.10,.39,.159),(.62,.32,.055),'teal',.006);box('reconfig.closed_cover',(.10,.39,.21),(.53,.25,.04),'cream',.006)
# Opaque chamber and separate band reference; no loaded specimen or self-support claim.
for x in [-.115,.315]:box('reconfig.static_stop',(x,.39,.246),(.035,.18,.035),'navy',.002)
bpy.ops.mesh.primitive_torus_add(major_radius=.055,minor_radius=.0025,major_segments=64,minor_segments=10,location=(.10,.39,.237));finish(bpy.context.object,'reconfig.band_reference','band')
txt('reconfig.top','MANUAL MODE / RETENTION RECORD',(-.128,.338,.238),.012,'navy',True)
label('reconfig.label','CONFINEMENT / CLOSED SERVICE',(.10,.215,.169),.62,.034,.013)
for key,p,t in [('fixture_origin',(.10,.39,.159),'reconfig.base'),('axis_x',(.315,.39,.25),'reconfig.static_stop.001'),('axis_y',(.1,.49,.23),'reconfig.closed_cover'),('mode_record',(-.08,.211,.17),'reconfig.label.plate'),('confinement_record',(.20,.211,.17),'reconfig.label.plate')]:anchor(key,p,t)
root('A_TENSILE_FIXTURE')
box('tension.base',(.34,-.31,.162),(.43,.42,.059),'navy',.006)
for x in [.19,.49]:cyl('tension.post',(x,-.28,.372),.011,.40,'steel')
box('tension.bridge',(.34,-.28,.565),(.36,.066,.036),'cream',.004)
box('tension.lower_grip',(.34,-.34,.24),(.09,.077,.045),'teal',.004);box('tension.upper_grip',(.34,-.34,.456),(.09,.077,.045),'teal',.004)
box('tension.guard_closed',(.34,-.402,.35),(.27,.012,.32),'black',.003)
txt('tension.closed','CLOSED / EMPTY',(.224,-.411,.41),.014,'amber');txt('tension.nocoupon','NO MOUNTED COUPON',(.224,-.411,.36),.012);txt('tension.mdc','MD / CD EXTERNAL',(.224,-.411,.31),.012)
label('tension.label','TENSILE / DISABLED',(.34,-.531,.174),.43,.033,.014)
for key,p,t in [('fixture_origin',(.34,-.31,.162),'tension.base'),('lower_grip',(.34,-.34,.2625),'tension.lower_grip'),('upper_grip',(.34,-.34,.4335),'tension.upper_grip'),('alignment_record',(.34,-.412,.35),'tension.guard_closed'),('disabled_state',(.34,-.535,.174),'tension.label.plate')]:anchor(key,p,t)
root('A_COMPRESSION_FIXTURE')
box('compression.base',(.81,-.27,.16),(.42,.49,.055),'navy',.007)
for x in [.66,.96]:cyl('compression.post',(x,-.19,.383),.014,.42,'steel')
box('compression.bridge',(.81,-.19,.59),(.37,.074,.045),'cream',.005)
cyl('compression.upper_platen',(.81,-.27,.448),.102,.022,'steel');cyl('compression.lower_platen',(.81,-.27,.237),.102,.022,'steel')
rod('compression.static_spindle',(.81,-.19,.485),(.81,-.19,.63),.014,'steel')
box('compression.closed_guard',(.81,-.414,.363),(.31,.012,.32),'navy',.004)
txt('compression.closed','CLOSED / EMPTY',(.673,-.423,.452),.014,'amber');txt('compression.noload','NO LOAD / NO MOTION',(.673,-.423,.397),.012);txt('compression.band','BAND RELEASE: HOLD',(.673,-.423,.342),.012);txt('compression.capacity','12.5 kN: SOURCE RATING',(.673,-.423,.287),.0105)
label('compression.label','COMPRESSION / DISABLED',(.81,-.53,.173),.42,.033,.012)
for key,p,t in [('fixture_origin',(.81,-.27,.16),'compression.base'),('lower_platen',(.81,-.27,.248),'compression.lower_platen'),('upper_platen',(.81,-.27,.437),'compression.upper_platen'),('axis_record',(.81,-.423,.397),'compression.closed_guard'),('band_record',(.81,-.423,.342),'compression.closed_guard'),('disabled_state',(.81,-.534,.173),'compression.label.plate')]:anchor(key,p,t)
root('A_ACQUISITION_RECORDS')
screen('records',(.83,.40,.346),.34,.34,'ACQUISITION RECORDS',[('FORCE / CROSSHEAD','white'),('DIC / CALIBRATION','white'),('NO ACQUIRED DATA','amber')])
# Static camera body faces toward the closed fixture, with no real optical calibration.
box('camera.body',(.64,.04,.40),(.10,.08,.073),'black',.005);cyl('camera.lens',(.64,-.018,.40),.026,.046,'navy','Y');cyl('camera.lens_cap',(.64,-.044,.40),.025,.006,'amber','Y')
rod('camera.stand',(.64,.04,.14),(.64,.04,.358),.008,'steel');box('camera.foot',(.64,.04,.146),(.12,.11,.018),'navy',.004)
label('camera.label','DIC / DISABLED',(.64,-.016,.225),.17,.025,.009)
for key,p,t in [('force_record',(.73,.344,.40),'records.face'),('crosshead_record',(.92,.344,.40),'records.face'),('dic_record',(.64,-.044,.40),'camera.lens_cap'),('timebase_record',(.73,.344,.34),'records.face'),('calibration_record',(.92,.344,.34),'records.face'),('safe_release_record',(.83,.344,.28),'records.face')]:anchor(key,p,t)
root('A_ANALYSIS_CONSOLE')
screen('analysis',(.48,.44,.344),.24,.31,'ANALYSIS',[('EXTERNAL DATA','white'),('NO CURVES','amber'),('NO RESULTS','white')])
for key,z in [('analysis_record',.39),('comparison_record',.33),('archive_slot',.27)]:anchor(key,(.48,.384,z),'analysis.face')
root('A_NUMERICAL_CONSOLE')
screen('numerical',(-.22,.07,.425),.40,.24,'NUMERICAL MODELS',[('EXTERNAL MODEL RECORD','white'),('NO SOLVER / NO SOURCE CODE','amber'),('CONVERGENCE: UNVERIFIED','white')])
for key,x in [('model_record',-.35),('parameter_record',-.22),('convergence_record',-.09)]:anchor(key,(x,.014,.425),'numerical.face')
root('A_HOLD_STORAGE')
box('hold.panel',(.0,.61,.665),(1.47,.022,.13),'navy',.006)
txt('hold.title','PERMANENT EXECUTION HOLD',(-.66,.595,.684),.034,'amber');txt('hold.detail','NO SOURCE CELL CAD / NO CONTACT PHYSICS / NO HARDWARE CONTROL',(-.66,.595,.641),.017)
for x in [-.67,.67]:rod('hold.support',(x,.622,.13),(x,.622,.60),.008,'steel')
box('hold.quarantine_case',(-.83,.075,.202),(.31,.25,.14),'amber',.006);box('hold.quarantine_lid',(-.83,.075,.28),(.32,.26,.025),'navy',.004)
label('hold.case_label','QUARANTINE / SEALED',(-.83,-.057,.207),.31,.04,.012)
for key,p,t in [('qualification_hold',(-.55,.594,.65),'hold.panel'),('configuration_hold',(-.20,.594,.65),'hold.panel'),('calibration_hold',(.20,.594,.65),'hold.panel'),('lineage_hold',(.55,.594,.65),'hold.panel'),('quarantine_slot',(-.83,.075,.292),'hold.quarantine_lid'),('cleanup_record',(-.83,-.061,.207),'hold.case_label.plate')]:anchor(key,p,t)
CUR=None
box('studio.floor',(0,0,-.015),(200,200,.02),'floor',0)
light('LIGHT.key',(-1.6,-1.9,3),750,2.0,(0,0,.3));light('LIGHT.fill',(2,-1,2.6),500,2.3,(0,0,.3));light('LIGHT.rim',(0,2.5,3),800,2.0,(0,0,.3))
CAMS={'overview':camera('CAM.overview',(1.6,-3.7,2.65),(0,0,.36),2.83),'handling':camera('CAM.handling',(-1.35,-2.3,1.72),(-.30,-.28,.275),1.95)}
MAIN.camera=CAMS['overview'];bpy.context.view_layer.update()
assets=[]
for aid,r in ROOTS.items():
 parts=[]
 for o in r.children:
  if o.type in ['MESH','FONT','CURVE']:
   q=o.rotation_euler.to_quaternion();parts.append({'part_id':o.name,'type':o.type,'dimensions_m':list(o.dimensions),'translation_m':list(o.location),'rotation_quaternion_xyzw':[q.x,q.y,q.z,q.w],'scale':list(o.scale),'geometry_basis':'original_authored','physical_geometry_validated':False})
 assets.append({'asset_id':aid,'instance_id':aid+'.01','role':r['role'],'operation_ids':r['operation_ids'].split(','),'display_scale':1,'coordinate_space':'AUTHORED_METRIC','physical_qualified_transform':None,'parts':parts})
(OUT/'asset_inventory.json').write_text(json.dumps({'schema':'lockable_origami_original_scene.v1','units':'m','main_scene_group_count':len(assets),'original_asset_group_count':11,'imported_mesh_count':0,'reused_asset_credit':0,'assets':assets},indent=2)+'\n')
(OUT/'affordances.json').write_text(json.dumps({'implementation':'metadata_only','qualified_robot_poses':False,'anchors':ANCHORS},indent=2)+'\n')
(OUT/'materials/materials.json').write_text(json.dumps([{'id':m.name,'base_color':list(m.diffuse_color),'appearance_only':True,'measured_material_properties':False} for m in M.values()],indent=2)+'\n')
(OUT/'review/kinematic_proxy.json').write_text(json.dumps({'scope':'original open-chain centerline snapshots only; no source origami constraint solution','physical_validation':False,'joint_clearance_validated':False,'snapshots':KIN},indent=2)+'\n')
# Separate uniformly scaled source-dimensional coupon display, with explicit authored layout.
DISPLAY=bpy.data.scenes.new('REFERENCE_DISPLAY_8X');DISPLAY.world=MAIN.world.copy();sc=DISPLAY;bpy.context.window.scene=sc;setup(sc)
CUR=bpy.data.objects.new('DISPLAY.paperboard_reference',None);sc.collection.objects.link(CUR);CUR['display_only']=True;CUR['reference_scale_factor']=8;CUR['paper_exact_geometry']=False
box('display.plinth',(0,0,.010),(.62,.35,.02),'cream',.004)
D=box('display.perforated_coupon',(-.14,0,.028),(.12,.12,.00168),'paper',0);D['native_reference_m']=[.015,.015,.00021];D['display_scale']=8;D['slot_width_authored_m']=.00015;D['interval_interpretation']='authored uncut gap, not certified source pitch'
# Apply four rectangular holes; width is explicitly authored, not source tool kerf.
for i,x in enumerate([-.0051,-.0017,.0017,.0051]):
 tool=box('temporary.slot',(-.14+x*8,0,.028),(.002*8,.00015*8,.008),'black',0)
 bpy.context.view_layer.objects.active=D;mod=D.modifiers.new('Authored reference hole','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=tool;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(tool,do_unlink=True)
# Upright companion coupon: true finite thickness, without visual exaggeration.
E=box('display.edge_coupon',(.105,0,.081),(.12,.00168,.12),'paper',0);E['native_reference_m']=[.015,.00021,.015];E['display_scale']=8
for x in [-.14,.105]:box('display.support',(x,0,.023),(.135,.135,.005),'navy',.002)
box('display.title.plate',(0,.158,.212),(.60,.008,.10),'navy',.003)
txt('display.title.text','PAPERBOARD REFERENCES / UNIFORM 8x DISPLAY',(-.276,.151,.237),.018)
txt('display.cut_info','2 mm CUT / 1.4 mm GAP: AUTHORED INTERPRETATION',(-.276,.151,.209),.0105)
txt('display.slot_info','0.15 mm SLOT WIDTH: AUTHORED / NO SOURCE PANEL CAD',(-.276,.151,.189),.0105)
label('display.native','NATIVE: 0.21 mm THICK / 15 mm AUTHORED SPAN',(-.008,-.171,.048),.61,.04,.014)



CUR=None;box('display.studio.floor',(0,0,-.014),(200,200,.02),'floor',0)
light('DISPLAY.key',(-.7,-.8,1.3),130,1.1,(0,0,.07));light('DISPLAY.fill',(.8,-.2,.8),90,1.0,(0,0,.07));light('DISPLAY.rim',(0,.8,1.0),140,1.0,(0,0,.07))
DISPLAY.camera=camera('CAM.dimensions',(.30,-.89,.75),(0,0,.108),.95)
# The native file preserves editable FONT objects; GLBs get converted copies afterward.
for screen in bpy.data.screens:
 for area in screen.areas:
  for space in area.spaces:
   if space.type=='FILE_BROWSER' and space.params:space.params.directory=b'//'
bpy.context.window.scene=MAIN;bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'geometry/lockable_origami_lab.blend'))
for scene,filename in [(MAIN,'lockable_origami_lab.glb'),(DISPLAY,'paperboard_reference_display.glb')]:
 bpy.context.window.scene=scene
 for o in list(scene.objects):
  if o.type in ['FONT','CURVE']:
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 bpy.ops.object.select_all(action='DESELECT')
 for o in scene.objects:
  if o.type in ['MESH','EMPTY'] and 'studio.floor' not in o.name:o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(OUT/'geometry'/filename),export_format='GLB',use_selection=True,use_active_scene=True,export_apply=True,export_extras=True)
views=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['overview','handling','dimensions']
receipt={'engine':'CYCLES','device':'CPU','blender_version':bpy.app.version_string,'samples':96,'denoising':False,'resolution':[1800,1200],'views':[],'source_pixels_used':False}
for view in views:
 scene=DISPLAY if view=='dimensions' else MAIN;bpy.context.window.scene=scene
 if view!='dimensions':scene.camera=CAMS[view]
 scene.render.filepath=str(OUT/'evidence'/f'{view}.png');bpy.ops.render.render(write_still=True)
 p=OUT/'evidence'/f'{view}.png';raw=p.read_bytes();clean=raw[:8];offset=8
 while offset<len(raw):
  length=struct.unpack('>I',raw[offset:offset+4])[0];kind=raw[offset+4:offset+8];chunk=raw[offset:offset+length+12]
  if kind not in [b'tEXt',b'zTXt',b'iTXt']:clean+=chunk
  offset+=length+12
 p.write_bytes(clean);receipt['views'].append({'id':view,'scene':scene.name,'camera':scene.camera.name,'file':'evidence/'+p.name,'sha256':hashlib.sha256(clean).hexdigest(),'actual_render':True,'text_metadata_removed':True})
if views:(OUT/'review/render_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('LOCKABLE_ORIGAMI_BUILD_COMPLETE')
