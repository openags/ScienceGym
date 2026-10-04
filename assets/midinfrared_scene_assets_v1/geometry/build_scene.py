"""Original MIR laboratory: nominal static equipment and protected sample assets.
Run Blender --background --threads 8 --python geometry/build_scene.py.
No source meshes, images, optical simulation, device I/O, or physical motion.
"""
import bpy, json, math, hashlib, sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
S=bpy.context.scene; S.name='MIDINFRARED_ORIGINAL_STATIC_LAB'
S.unit_settings.system='METRIC'; S.unit_settings.scale_length=1
S.render.engine='CYCLES'; S.cycles.device='CPU'; S.cycles.samples=64; S.cycles.use_denoising=False; S.cycles.seed=37
S.render.resolution_x=1800; S.render.resolution_y=1200; S.render.resolution_percentage=100
S.render.image_settings.file_format='PNG'; S.render.use_stamp=False
S.world=bpy.data.worlds.new('Neutral studio'); S.world.use_nodes=True
S.world.node_tree.nodes['Background'].inputs[0].default_value=(.35,.42,.48,1)
S.world.node_tree.nodes['Background'].inputs[1].default_value=.42
S.view_settings.view_transform='AgX'; S.view_settings.exposure=-.8
CUR=None; ROOTS={}; M={}; CONTACTS=[]; EXCLUSIONS=[]; PROXIES=[]; SPECIMENS=[]
def save(n,d):(P/n).write_text(json.dumps(d,indent=2)+'\n')
def material(k,c,metal=0,rough=.42,trans=0):
 m=bpy.data.materials.new(k); m.diffuse_color=(*c,1);m.use_nodes=True;q=m.node_tree.nodes['Principled BSDF'];q.inputs['Base Color'].default_value=(*c,1);q.inputs['Metallic'].default_value=metal;q.inputs['Roughness'].default_value=rough;q.inputs['Transmission Weight'].default_value=trans;M[k]=m
for a in [('navy',(.025,.06,.10),.3),('teal',(.025,.32,.35),.35),('cream',(.73,.82,.82),.12),('metal',(.42,.52,.58),.75),('black',(.009,.018,.025),.12),('white',(.96,.98,.94)),('cyan',(.02,.66,.80),.12),('amber',(.98,.48,.055)),('coral',(.76,.16,.07)),('copper',(.68,.26,.095),.8,.27),('silicon',(.11,.14,.20),.68,.20),('etched',(.44,.53,.61),.55,.43),('guard',(.82,.92,.97),0,.08,.92),('floor',(.31,.38,.45),0,.85)]: material(*a)
def root(aid):
 global CUR
 CUR=bpy.data.objects.new('ASSET.'+aid,None);S.collection.objects.link(CUR);CUR.empty_display_size=.04
 for k,v in {'asset_id':aid,'units':'m','physical_geometry_validated':False,'physical_execution_enabled':False,'geometry_basis':'original_authored'}.items():CUR[k]=v
 ROOTS[aid]=CUR
def finish(o,n,m=None):
 o.name=n
 if CUR:o.parent=CUR
 if m:o.data.materials.append(M[m])
 for k,v in {'geometry_basis':'original_authored','physical_geometry_validated':False,'physical_execution_enabled':False,'graspable':False}.items():o[k]=v
 return o
def box(n,p,d,m='navy',bev=.004):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.dimensions=d;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(o,n,m)
 if bev:b=o.modifiers.new('Nominal rounding','BEVEL');b.width=min(bev,min(d)*.23);b.segments=3;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o
def cyl(n,p,r,h,m='metal',axis='Z',verts=48):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=h,location=p);o=bpy.context.object
 if axis=='Y':o.rotation_euler.x=math.pi/2
 if axis=='X':o.rotation_euler.y=math.pi/2
 finish(o,n,m)
 for f in o.data.polygons:f.use_smooth=True
 return o
def rod(n,a,b,r=.008,m='metal'):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,verts=24);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def text(n,body,p,size=.022,m='white',flat=False):
 c=bpy.data.curves.new(n,'FONT');c.body=body;c.size=size;c.extrude=.00006;o=bpy.data.objects.new(n,c);S.collection.objects.link(o);o.location=p
 if not flat:o.rotation_euler=(math.pi/2,0,0)
 return finish(o,n,m)
def label(n,body,p,w=.6,h=.055,size=.019,col='navy'):
 box(n+'.plate',p,(w,.009,h),col,.002);return text(n+'.text',body,(p[0]-w*.46,p[1]-.006,p[2]-h*.18),size)
def screen(n,p,w,h,title,lines):
 x,y,z=p;box(n+'.body',p,(w,.045,h),'navy',.01);f=box(n+'.screen',(x,y-.027,z),(w-.022,.008,h-.022),'black',.002)
 text(n+'.title',title,(x-w*.45,y-.033,z+h*.31),w*.045,'cyan')
 for i,s in enumerate(lines):text(n+'.line'+str(i),s,(x-w*.45,y-.033,z+h*.06-i*h*.19),w*.030,'amber' if i==0 else 'white')
 return f
def contact(n,p,d,kind='carrier_contact'):
 o=box(n,p,d,'teal',.003);o['candidate_contact']=True;o['qualified_grasp']=False
 CONTACTS.append({'scene_object':n,'asset_id':CUR['asset_id'],'kind':kind,'translation_m':list(p),'dimensions_m':list(d),'qualified_pose':None,'physical_grasp_enabled':False,'limits':{'force_N':None,'payload_kg':None,'friction':None,'tolerance_m':None}});return o
def exclude(o,why):
 o['contact_excluded']=True;EXCLUSIONS.append({'scene_object':o.name,'robot_contact_allowed':False,'reason':why})
def collision(n,p,d):
 o=box(n,p,d,'amber',0);o.hide_render=True;o.display_type='WIRE';o['geometry_role']='disabled_collision_proxy';o['collision_enabled']=False
 PROXIES.append({'scene_object':n,'translation_m':list(p),'dimensions_m':list(d),'fit_qualified':False,'collision_enabled':False})
def table(n,x,y,w,d):
 box(n+'.top',(x,y,.77),(w,d,.055),'cream',.012)
 for dx in [-w*.42,w*.42]:
  for dy in [-d*.39,d*.39]:box(n+'.leg',(x+dx,y+dy,.38),(.065,.065,.74),'navy',.005)
def slot(n,p,w=.12):return box(n,p,(w,.018,.025),'amber',.002)
def cassette(n,p,kind):
 x,y,z=p;w=.24;h=.25
 # Four-piece frame leaves the aperture open; clear cover is a display material only.
 for dx in [-.104,.104]:box(n+'.frame_side'+str(dx),(x+dx,y,z),(.032,.044,h),'navy',.004)
 for dz in [-.111,.111]:box(n+'.frame_end'+str(dz),(x,y,z+dz),(.24,.044,.028),'navy',.004)
 for dx,side in [(-.135,'L'),(.135,'R')]:contact(n+'.grip'+side,(x+dx,y,z),(.034,.075,.09))
 box(n+'.edge_support',(x,y+.008,z-.083),(.15,.018,.018),'cream',.002)
 cover=box(n+'.closed_cover',(x,y-.03,z),(.187,.0015,.194),'guard',0);exclude(cover,'Protected optical area; no direct robot contact; material is illustrative only')
 latch=box(n+'.latch',(x+.104,y-.034,z+.08),(.032,.025,.035),'amber',.003);latch['latch_state']='unverified'
 box(n+'.orientation_key',(x-.085,y-.031,z+.106),(.024,.012,.024),'cyan',.002)
 box(n+'.fiducial',(x-.083,y-.039,z-.10),(.018,.005,.018),'white',0)
 text(n+'.tag',kind,(x-.073,y-.04,z-.112),.013,'white')
 for dx in [-.09,.09]:box(n+'.stand_support'+str(dx),(x+dx,y,z-.1675),(.045,.075,.095),'metal',.003)
 return cover,latch
def cutout_letter(n,letter,p):
 x,y,z=p;o=box(n,p,(.16,.0015,.165),'copper',0)
 # Independently designed block-letter openings, not source-traced glyph outlines.
 bars={'E':[(-.033,0,.018,.108),(0,.047,.080,.017),(0,0,.072,.017),(0,-.047,.080,.017)],
 'C':[(-.033,0,.018,.108),(0,.047,.080,.017),(0,-.047,.080,.017)],
 'N':[(-.037,0,.018,.108),(.037,0,.018,.108),(0,0,.018,.122)],
 'U':[(-.037,.01,.018,.09),(.037,.01,.018,.09),(0,-.043,.09,.020)]}[letter]
 for i,(dx,dz,w,h) in enumerate(bars):
  c=box(n+'.temporary_cutter',(x+dx,y,z+dz),(w,.012,h),'black',0)
  if letter=='N' and i==2:c.rotation_euler.y=-.59
  bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Original aperture boolean','BOOLEAN');mod.operation='DIFFERENCE';mod.object=c;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(c,do_unlink=True)
 exclude(o,'Copper optical target. Candidate contact only on cassette handles; no exposed-sample manipulation')
 o['source_material_role']='copper';o['letter_role']=letter;o['authored_thickness_m']=.0015;o['source_thickness_known']=False
 SPECIMENS.append({'id':'CU-'+letter,'asset_id':'A01','scene_object':n,'shape_role':'original letter aperture','source_fact_id':'F02','authored_nominal_dimensions_m':[.16,.0015,.165],'physical_geometry_validated':False,'source_geometry_reproduced':False})
 return o
def star_surface(n,p,r=.059):
 x,y,z=p;v=[(x,y,z)]+[(x+(r if i%2==0 else r*.44)*math.sin(i*math.pi/5),y,z+(r if i%2==0 else r*.44)*math.cos(i*math.pi/5)) for i in range(10)]
 faces=[(0,i+1,(i+1)%10+1) for i in range(10)];me=bpy.data.meshes.new(n+'.mesh');me.from_pydata(v,[],faces);me.update();o=bpy.data.objects.new(n,me);S.collection.objects.link(o);finish(o,n,'etched');exclude(o,'Illustrative etched-mark surface. Etch depth/profile is unknown, not modeled');return o
# A01 and A02: real original target shapes in protected carriers on the front bench.
root('A01');table('samples.table',-.70,-1.20,2.15,.75)
for i,ch in enumerate('ECNU'):
 x=-1.43+i*.34;cassette('copper.'+ch,(x,-1.24,1.04),'CU-'+ch);cutout_letter('copper.'+ch+'.mask',ch,(x,-1.24,1.04));box('copper.'+ch+'.stand',(x,-1.2,.815),(.28,.24,.035),'navy',.004)
label('samples.front','A01 / COPPER MASKS / ORIGINAL CUTOUTS',(-.72,-1.582,.76),2.06,.056,.033)
collision('COLLISION.A01',(-.92,-1.20,1.03),(1.48,.30,.36))
root('A02');cassette('silicon.star',(.00,-1.24,1.04),'SI-STAR');si=cyl('silicon.wafer',(.00,-1.24,1.04),.080,.0002,'silicon','Y',96);exclude(si,'200 um source thickness reference is not sufficient to qualify a wafer or carrier')
si['source_nominal_thickness_m']=.0002;si['authored_radius_m']=.080;star_surface('silicon.star_mark',(.00,-1.24016,1.04));box('silicon.stand',(.00,-1.2,.815),(.28,.24,.035),'navy',.004)
SPECIMENS.append({'id':'SI-STAR','asset_id':'A02','scene_object':'silicon.wafer','mark_object':'silicon.star_mark','source_fact_id':'F03','source_nominal_thickness_m':.0002,'authored_radius_m':.080,'etch_depth_m':None,'etch_profile':None,'source_geometry_reproduced':False,'physical_geometry_validated':False})
label('silicon.annotation','A02 / Si STAR / 200 um SOURCE THICKNESS',(.00,-1.565,.87),.62,.065,.012)
collision('COLLISION.A02',(.00,-1.24,1.04),(.32,.22,.30))
# A03 receiving and quarantine, safe storage roles and custody.
root('A03');table('receiving.table',-2.05,.1,1.0,1.15)
box('receiving.rack',(-2.05,.33,1.03),(.90,.50,.48),'navy',.009)
for i in range(3):
 x=-2.34+i*.29;box('receiving.slot.'+str(i),(x,.28,1.04),(.23,.49,.29),'black',.004);label('receiving.slot_label.'+str(i),['RECEIVED','RETURN','QUARANTINE'][i],(x,.024,.872),.26,.04,.014)
box('receiving.return_slot',(-2.05,.02,.925),(.25,.25,.025),'teal',.002)
box('receiving.inspection_cradle',(-2.05,-.23,.82),(.58,.40,.04),'teal',.005)
slot('receiving.plan_token',(-2.38,-.43,.848),.14);slot('receiving.custody_port',(-1.70,-.32,.87),.09)
box('receiving.id_reader',(-1.72,-.17,1.10),(.15,.08,.22),'cream',.006);box('receiving.id_reader_lens',(-1.72,-.215,1.11),(.09,.006,.065),'black',.002)
for i in range(3):cyl('receiving.occupancy_sensor.'+str(i),(-2.34+i*.29,-.001,1.19),.009,.005,'amber','Y')
label('receiving.front','S01 / RECEIVING & CUSTODY',(-2.05,-.485,.75),.94,.06,.026)
collision('COLLISION.A03',(-2.05,.08,1.04),(1.06,1.20,.6))
# A04 closed fabrication handoff. No cutting/etching internals or recipe.
root('A04');table('fabrication.table',-1.85,1.35,1.42,.91)
box('fabrication.closed_shell',(-1.86,1.48,1.25),(1.22,.60,.89),'cream',.015)
box('fabrication.closed_guard',(-1.86,1.17,1.25),(1.1,.021,.64),'navy',.008)
box('fabrication.load_dock',(-2.02,.95,.89),(.55,.32,.09),'teal',.005)
slot('fabrication.receipt_port',(-1.40,1.147,1.29),.18)
box('fabrication.reject_bin',(-1.40,1.12,.97),(.19,.16,.12),'coral',.003)
label('fabrication.label','S02 / QUALIFIED SAMPLE SERVICE',(-1.86,1.146,1.60),1.1,.07,.033)
label('fabrication.hold','CLOSED SERVICE / RECEIPT REQUIRED',(-1.86,1.143,1.43),1.07,.05,.025)
contact('fabrication.dock_handle',(-2.02,.778,.89),(.24,.035,.035),'dock_handle')
collision('COLLISION.A04',(-1.86,1.29,1.22),(1.35,1.04,.98))
# A05 optical service boundary: opaque closed shell, empty safe-load dock.
root('A05');table('optics.table',.00,1.32,1.95,1.22)
box('optics.closed_enclosure',(.00,1.47,1.35),(1.78,.87,1.04),'navy',.019)
box('optics.closed_door',(.00,1.018,1.37),(1.61,.029,.81),'cream',.012)
box('optics.load_dock',(-.27,.74,.91),(.67,.43,.11),'teal',.006)
box('optics.dock_latch',(.10,.55,.95),(.06,.045,.07),'amber',.004)
slot('optics.safe_access_port',(.58,.989,1.21),.18)
box('optics.interlock_status',(.58,.989,1.40),(.17,.021,.075),'amber',.003)
for dx in [-.27,.27]:box('optics.docking_datum',(-.27+dx,.75,.98),(.022,.30,.025),'metal',.002)
box('optics.occupancy_sensor',(-.27,.956,.997),(.05,.02,.023),'black',.002)
label('optics.title','S03 / ENCLOSED MIR IMAGING',(.00,.989,1.72),1.56,.08,.048)
label('optics.door_notice','NO OPEN-BEAM ACCESS / NO INTERNAL OPTICAL LAYOUT',(-.02,.989,1.57),1.54,.065,.026)
label('optics.dock_notice','EMPTY DOCK / ACCESS NOT QUALIFIED',(-.27,.51,.86),.91,.055,.024)
collision('COLLISION.A05',(.0,1.20,1.37),(1.95,1.52,1.14))
# A06 sealed instrument modules physically distinct analog and photon-count paths.
root('A06');table('instruments.table',1.65,1.45,1.15,.90)
modules=[('source','SEALED MIR SOURCE',1.27,1.44),('pump','STRUCTURED PUMP',1.66,1.44),('convert','UPCONVERSION ROLE',2.04,1.44),('analog','ANALOG DETECTOR',1.35,1.16),('photon','PHOTON COUNTER',1.91,1.16)]
for tag,title,x,y in modules:
 box('instruments.'+tag+'.shell',(x,y,1.00),(.32,.25,.34),'navy' if tag in ['analog','photon'] else 'cream',.008)
 slot('instruments.'+tag+'.typed_port',(x,y-.134,.99),.075);label('instruments.'+tag+'.tag',title,(x,y-.132,1.10),.30,.05,.013)
box('instruments.detector_mode_port',(1.66,.992,.845),(.19,.02,.035),'amber',.002)
slot('instruments.mode_receipt_slot',(1.93,.994,.845),.16)
label('instruments.front','A06 / MODE CHANGE REQUIRES FRESH EPOCH',(1.65,.986,.752),1.1,.055,.022)
collision('COLLISION.A06',(1.65,1.38,1.02),(1.16,.90,.52))
# A07 guarded static dynamic-target fixture; no trajectory or motor.
root('A07');table('dynamic.table',.37,-.10,1.04,.77)
box('dynamic.base',(.37,-.10,.844),(.78,.55,.085),'navy',.008)
box('dynamic.retained_mount',(.37,-.10,1.025),(.28,.09,.25),'teal',.004)
box('dynamic.static_target',(.37,-.155,1.04),(.14,.004,.14),'copper',0)
text('dynamic.target_mark','E',(.327,-.159,1.002),.10,'black')
for dx in [-.38,.38]:box('dynamic.guard_side',(.37+dx,-.10,1.06),(.02,.56,.42),'cream',.003)
box('dynamic.guard_top',(.37,-.10,1.275),(.79,.56,.02),'cream',.003)
box('dynamic.closed_front',(.37,-.39,1.06),(.76,.005,.38),'guard',0)
slot('dynamic.service_port',(.70,-.405,.9),.12)
label('dynamic.warning','A07 / STATIC FIXTURE / MOTION HELD',(.37,-.413,.755),1.0,.055,.025)
exclude(bpy.data.objects['dynamic.static_target'],'Dynamic target is a retained static exemplar; motion, path and retention force unknown')
collision('COLLISION.A07',(.37,-.10,1.06),(.86,.62,.50))
# A08 timing and data console: blank/held records, no synthetic scientific values.
root('A08');table('timing.table',1.72,.24,1.08,.84)
screen('timing.console',(1.72,.42,1.17),.92,.62,'S04 / TIMING & RECORDS',['NO RAW DATA / ALL BRANCHES HELD','PATTERN <-> EVENT / CHECKSUM','ANALOG 16x16: 10 Hz SOURCE ONLY'])
for nm,x,col in [('configuration_port',1.32,'amber'),('photon_port',1.55,'cyan'),('encoding_port',1.78,'teal'),('event_ledger',2.02,'cream')]:box('timing.'+nm,(x,.13,.834),(.17,.15,.055),col,.003)
slot('timing.configuration_token',(1.32,.041,.866),.12)
label('timing.front','A08 / NO CONTROLLER / NO LIVE TELEMETRY',(1.72,-.190,.756),1.02,.052,.021)
collision('COLLISION.A08',(1.72,.23,1.09),(1.1,.9,.74))
# A09 separately identified reference and blank carriers, kept closed.
root('A09');table('references.table',-1.02,-.05,.95,.76)
for i,tag in enumerate(['BLANK','REFERENCE']):
 x=-1.24+i*.43;box('reference.'+tag+'.body',(x,-.06,.856),(.35,.39,.11),'navy',.004)
 box('reference.'+tag+'.closed_cover',(x,-.06,.920),(.33,.37,.019),'cream',.004)
 for dx in [-.188,.188]:contact('reference.'+tag+'.grip'+str(dx),(x+dx,-.06,.86),(.038,.10,.035))
 text('reference.'+tag+'.tag',tag,(x-.135,-.04,.932),.025,'navy',True)
label('references.front','A09 / INDEPENDENT REFERENCE HELD',(-1.02,-.438,.756),.91,.055,.021)
collision('COLLISION.A09',(-1.02,-.04,.87),(.95,.76,.24))
# A10 metrology appliance with an actual camera-role shell, lens and stage.
root('A10');table('metrology.table',1.52,-1.09,1.42,.9)
box('metrology.reference_cradle',(1.38,-1.13,.84),(.58,.42,.075),'teal',.006)
box('metrology.column',(1.75,-.87,1.20),(.095,.09,.84),'metal',.005)
box('metrology.arm',(1.52,-.87,1.58),(.56,.10,.09),'metal',.005)
box('metrology.camera_body',(1.35,-1.02,1.52),(.23,.24,.16),'navy',.010)
cyl('metrology.lens',(1.35,-1.02,1.394),.068,.10,'black');cyl('metrology.glass',(1.35,-1.02,1.34),.056,.009,'guard')
slot('metrology.registration_token',(2.00,-1.08,.87),.14)
box('metrology.no_measurement_card',(1.38,-1.13,.884),(.31,.21,.008),'cream',.001)
text('metrology.card_text','NO MEASUREMENTS',(1.24,-1.14,.890),.02,'navy',True)
label('metrology.front','A10 / INDEPENDENT IMAGING / UNCALIBRATED',(1.52,-1.55,.755),1.36,.057,.028)
collision('COLLISION.A10',(1.52,-1.09,1.23),(1.43,.91,.9))
# A11 archive/evaluation console and separate failure-retention bin.
root('A11');table('archive.table',2.93,.52,1.05,1.39)
screen('archive.console',(2.93,.88,1.20),.89,.68,'S05 / EVIDENCE ARCHIVE',['AUTHOR CODE / RAW DATA UNAVAILABLE','8 BRANCHES / OUTCOMES UNESTABLISHED','FAILED RUNS RETAINED / HASH LINEAGE'])
for n,x,y in [('evaluation_port',2.60,.30),('analysis_port',2.88,.30),('manifest_port',3.16,.30),('branch_ledger',2.88,.04)]:box('archive.'+n,(x,y,.831),(.20,.18,.045),'teal',.003)
slot('archive.reference_token',(2.60,.194,.856),.14);slot('archive.version_token',(2.88,.194,.856),.14)
box('archive.failure_bin',(3.15,-.035,.90),(.22,.25,.18),'coral',.005)
label('archive.front','A11 / DESIGN RECORDS ONLY',(2.93,-.186,.755),1.00,.052,.022)
collision('COLLISION.A11',(2.93,.52,1.12),(1.10,1.44,.79))
# A12 static robotic handoff representation. No robot arm/reach/dynamics claims.
root('A12');table('transport.table',-2.12,-1.21,.78,.77)
box('transport.supported_cradle',(-2.12,-1.20,.835),(.51,.43,.075),'teal',.006)
box('transport.wrist',(-2.12,-1.17,1.20),(.13,.15,.11),'metal',.008)
rod('transport.bridge',(-2.38,-1.17,1.135),(-1.86,-1.17,1.135),.025)
for dx in [-.25,.25]:
 box('transport.finger',(-2.12+dx,-1.18,1.055),(.038,.11,.16),'navy',.004)
 contact('transport.pad'+str(dx),(-2.12+dx*.94,-1.18,1.007),(.017,.075,.062),'candidate_gripper_pad')
box('transport.registration_fiducial',(-2.12,-1.39,.88),(.04,.006,.04),'white',0)
label('transport.front','A12 / STATIC GRIPPER',(-2.12,-1.60,.756),.76,.055,.023)
collision('COLLISION.A12',(-2.12,-1.20,1.04),(.76,.77,.49))
# A13 separate spatial pump/SFG diagnostic imaging service. Cannot be a bucket detector.
root('A13');table('diagnostic.table',1.70,2.43,1.19,.63)
box('diagnostic.support_pedestal',(1.70,2.43,.953),(1.06,.50,.30),'navy',.008)
box('diagnostic.sealed_shell',(1.70,2.44,1.35),(1.00,.45,.49),'cream',.010)
box('diagnostic.spatial_sensor_shell',(1.42,2.202,1.38),(.29,.055,.23),'navy',.005)
cyl('diagnostic.capped_spatial_aperture',(1.42,2.167,1.38),.065,.03,'black','Y')
slot('diagnostic.map_transfer_port',(1.95,2.199,1.42),.22);slot('diagnostic.registration_port',(1.95,2.199,1.29),.22)
label('diagnostic.label','A13 / SPATIAL MAP SERVICE',(1.70,2.198,1.56),.95,.064,.029)
label('diagnostic.hold','PUMP + SFG / SENSOR ID REQUIRED',(1.70,2.198,1.184),.96,.05,.022)
collision('COLLISION.A13',(1.70,2.41,1.22),(1.1,.54,.90))
# Context only. Opaque optical service means no invented beam paths or photon telemetry.
CUR=None;box('studio.floor',(0,0,-.03),(200,200,.045),'floor',0)
box('scene.banner',(.10,2.82,2.02),(5.80,.035,.37),'navy',.009)
text('scene.title','MID-INFRARED / ORIGINAL ROBOT LAB',(-2.62,2.798,2.08),.138)
text('scene.subtitle','13 ASSET FAMILIES / 5 STATIONS / 8 BRANCHES / 22 PROPOSED OPERATIONS',(-2.61,2.797,1.96),.052,'cyan')
text('scene.warning','STATIC GEOMETRY ONLY / CLOSED OPTICS / ALL PHYSICAL QUALIFICATION HELD',(-2.61,2.796,1.88),.046,'amber')
# Bind operation selectors to exact concrete owned target meshes.
bpy.context.view_layer.update();contract=json.loads((P/'operation_binding_contract.json').read_text());anchors=[]
for op in contract['operations']:
 for role in ['primary','control']:
  n=op[role+'_anchor'];t=bpy.data.objects[op[role+'_target']];r=ROOTS[op['primary_asset_id']];assert t.parent==r
  o=bpy.data.objects.new(n,None);S.collection.objects.link(o);o.parent=r;o.location=t.matrix_world.translation;o.empty_display_size=.025;o['target_object']=t.name;o['operation_id']=op['operation_id'];o['physical_execution_enabled']=False
  anchors.append({'anchor_id':n,'asset_id':op['primary_asset_id'],'scene_object':n,'target_object':t.name,'target_object_id':t.name,'translation_m':list(o.location),'rotation_quaternion_xyzw':[0,0,0,1],'qualified_pose':None,'physical_execution_enabled':False})
bpy.context.view_layer.update()
save('affordances.json',{'schema':'sciencegym.midinfrared.affordances.v1','units':'m','anchors':anchors,'candidate_contacts':CONTACTS,'exclusion_regions':EXCLUSIONS,'collision_proxies':PROXIES,'physical_execution_enabled':False,'status':'Nominal static selectors, not robot poses or certified collision geometry'})
save('specimen_geometry.json',{'schema':'sciencegym.midinfrared.specimen_geometry.v1','source_pixels_or_CAD_used':False,'specimens':SPECIMENS,'display_example_count_is_not_experimental_n':True,'copper_topology':'Four original solid plates with Boolean transmission apertures; authored independent block glyphs','silicon_topology':'Nominal 200 um-thick disc plus surface marking; etch depth/profile deliberately unknown'})
save('asset_inventory.json',{'schema':'sciencegym.midinfrared.inventory.v1','units':'m','asset_group_count':13,'imported_mesh_count':0,'assets':[{'asset_id':aid,'root':r.name,'physical_geometry_validated':False,'parts':[{'scene_object':o.name,'type':o.type,'dimensions_m':list(o.dimensions),'translation_m':list(o.matrix_world.translation),'geometry_basis':'original_authored','graspable':False} for o in S.objects if o.parent==r]} for aid,r in ROOTS.items()]})
save('materials/materials.json',{'materials':[{'name':k,'display_color_rgba':list(m.diffuse_color),'mechanical_model':None,'optical_calibration':None} for k,m in M.items()],'warning':'Display appearance only; glass does not establish optical transmission or safety'})
def camera(n,p,target,scale):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);S.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=scale;d.clip_start=.001;d.clip_end=250;return o
def area(n,p,target,power,size):
 d=bpy.data.lights.new(n,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(n,d);S.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('LIGHT.key',(-3,-5,7),(0,.3,1),2500,5);area('LIGHT.fill',(5,-2,5),(0,.3,1),1500,4);area('LIGHT.rim',(0,5,7),(0,.3,1),2400,4)
CAMS={'overview':camera('CAM.overview',(8.2,-11,8.3),(.23,.52,1.05),8.15),'samples':camera('CAM.samples',(-2.8,-5.4,3.0),(-1.00,-1.17,.97),2.98),'optics':camera('CAM.optics',(4.7,-4.6,4.1),(.53,1.52,1.17),4.8)}
S.camera=CAMS['overview'];S.render.filepath='//../evidence/overview.png'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'geometry/midinfrared_lab.blend'))
# Export a temporary scene. Native labels remain editable; GLB labels are meshes.
ex=S.copy();ex.name='TEMP_PORTABLE_EXPORT';bpy.context.window.scene=ex
for o in ex.objects:o.select_set(False)
for o in list(ex.objects):
 if o.type=='FONT':
  cp=o.copy();cp.data=o.data.copy();ex.collection.objects.link(cp);cp.parent=o.parent;cp.name=o.name+'.portable';o.hide_set(True);cp.select_set(True);bpy.context.view_layer.objects.active=cp;bpy.ops.object.convert(target='MESH');cp.select_set(False)
for o in ex.objects:o.select_set(o.type in {'MESH','EMPTY'} and not o.hide_render and not o.hide_get() and o.name!='studio.floor')
bpy.ops.export_scene.gltf(filepath=str(P/'geometry/midinfrared_lab.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_extras=True,export_apply=True,export_yup=True)
bpy.context.window.scene=S;bpy.data.scenes.remove(ex)
for o in list(bpy.data.objects):
 if '.portable' in o.name:bpy.data.objects.remove(o,do_unlink=True)
for o in S.objects:
 if o.type=='FONT':o.hide_set(False)
receipt={'renderer':'Blender Cycles','blender_version':bpy.app.version_string,'device':'CPU','samples':64,'denoising':False,'source_pixels_used':False,'images':[]}
if '--no-render' not in sys.argv:
 for n,c in CAMS.items():
  S.camera=c;S.render.filepath=str(P/'evidence'/f'{n}.png');bpy.ops.render.render(write_still=True);f=P/'evidence'/f'{n}.png';receipt['images'].append({'path':'evidence/'+n+'.png','sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'camera':c.name,'resolution':[1800,1200],'kind':'actual CPU path-traced static scene; not measured evidence'})
 save('review/render_receipt.json',receipt)
S.camera=CAMS['overview'];S.render.filepath='//../evidence/overview.png';bpy.ops.wm.save_as_mainfile(filepath=str(P/'geometry/midinfrared_lab.blend'))
print('MIDINFRARED_BUILD_COMPLETE',len(bpy.data.objects),len(anchors),len(SPECIMENS))
