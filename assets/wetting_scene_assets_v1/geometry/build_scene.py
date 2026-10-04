"""Independently authored metric laboratory assets. Static services only.
No imported source pixels, apparatus CAD, device I/O, physical simulation or telemetry.
Run from any directory with Blender; outputs resolve relative to this script.
"""
import bpy, math, json, sys, hashlib, struct
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
PLAN=json.loads((P/'task_binding_snapshot.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
MAIN=bpy.context.scene; MAIN.name='WETTING_ORIGINAL_LAB_METRIC';sc=MAIN;CUR=None;ROOTS={};TARGETS={};GRIPS=[];EXCLUSIONS=[];PROXIES=[]
def setup(s):
 s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
 s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=96;s.cycles.use_denoising=False;s.cycles.seed=33
 s.render.resolution_x=1800;s.render.resolution_y=1200;s.render.resolution_percentage=100
 s.render.image_settings.file_format='PNG';s.render.filepath='//evidence/';s.render.use_stamp=False
 s.world=bpy.data.worlds.new(s.name+'.world');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.49,.55,.59,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.35
 s.view_settings.view_transform='AgX';s.view_settings.exposure=-1.6
setup(sc)
def mat(n,c,metal=0,rough=.42,trans=0):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;p.inputs['Transmission Weight'].default_value=trans;return m
M={'navy':mat('Deep blue / authored equipment',(.017,.054,.079),.3),'teal':mat('Teal / carrier only',(.025,.32,.30),.3),'cream':mat('Pale enamel / generic enclosure',(.79,.85,.84),.13),'metal':mat('Metal appearance only',(.4,.5,.57),.7),'black':mat('Graphite / inactive display',(.007,.013,.021),.15),'white':mat('White lettering',(.97,.99,.96)),'amber':mat('Amber / hold or exclusion',(.99,.45,.035),.05),'cyan':mat('Cyan / observation role only',(.12,.72,.84),.1),'magenta':mat('Magenta / imputed role only',(.81,.19,.55),.05),'violet':mat('Violet / inferred role only',(.38,.24,.70),.08),'red':mat('Coral / quarantine',(.71,.12,.07),.08),'glass':mat('Glass reference / appearance only',(.45,.66,.76),0,.2,.25),'guard':mat('Clear guard appearance / no protective rating',(.85,.93,.96),0,.055,1.),'pdms':mat('PDMS appearance / no mechanical model',(.39,.67,.72),.1,.36),'cy':mat('CY appearance / no mechanical model',(.51,.76,.63),.1,.38),'water':mat('Synthetic water illustration / no physics',(.14,.55,.81),0,.14,.30),'floor':mat('Studio floor',(.55,.61,.65),0,.88)}
def root(aid):
 global CUR
 spec=next(x for x in PLAN['groups'] if x['id']==aid);o=bpy.data.objects.new(aid,None);sc.collection.objects.link(o);o.empty_display_size=.01
 for k,v in {'asset_id':aid,'role':spec['name'],'authored_geometry':True,'physical_execution':False,'device_io':False,'energy_enabled':False,'display_scale':1.,'physical_geometry_validated':False}.items():o[k]=v
 op_plan=json.loads((P/'operation_binding_contract.json').read_text());o['operation_ids']=','.join(next(a['bind_operation_ids'] for a in op_plan['assets'] if a['asset_id']==aid))
 ROOTS[aid]=o;CUR=o;TARGETS[aid]={};return o
def finish(o,n,m=None):
 o.name=n
 if m:o.data.materials.append(M[m])
 if CUR:o.parent=CUR
 o['geometry_basis']='original_authored';o['physical_geometry_validated']=False;o['device_io']=False;o['energy_enabled']=False;o['graspable']=False
 return o
def box(n,p,d,m='navy',bevel=.003):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.dimensions=d;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(o,n,m)
 if bevel:
  b=o.modifiers.new('Authored edge radius','BEVEL');b.width=min(bevel,min(d)/3);b.segments=3;o.modifiers.new('Surface normals','WEIGHTED_NORMAL')
 return o
def cyl(n,p,r,h,m='metal',axis='Z'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=r,depth=h,location=p);o=bpy.context.object
 if axis=='Y':o.rotation_euler.x=math.pi/2
 if axis=='X':o.rotation_euler.y=math.pi/2
 finish(o,n,m)
 for f in o.data.polygons:f.use_smooth=True
 return o
def rod(n,a,b,r=.002,m='metal'):
 va,vb=Vector(a),Vector(b);o=cyl(n,(va+vb)/2,r,(vb-va).length,m);o.rotation_euler=(vb-va).to_track_quat('Z','Y').to_euler();return o
def txt(n,s,p,size=.012,m='white',flat=False):
 c=bpy.data.curves.new(n,'FONT');c.body=s;c.size=size;c.extrude=.000015;c.space_character=1.01;o=bpy.data.objects.new(n,c);sc.collection.objects.link(o);o.location=p
 if not flat:o.rotation_euler=(math.pi/2,0,0)
 return finish(o,n,m)
def label(n,s,p,w=.3,h=.034,size=.012,m='navy'):
 box(n+'.plate',p,(w,.005,h),m,.001);return txt(n+'.text',s,(p[0]-.46*w,p[1]-.0035,p[2]-.15*h),size)
def screen(n,p,w,h,title,lines):
 x,y,z=p;body=box(n+'.body',p,(w,.037,h),'navy',.004);face=box(n+'.face',(x,y-.022,z),(w-.014,.007,h-.014),'black',.001)
 txt(n+'.title',title,(x-w*.45,y-.027,z+h*.32),w*.045,'cyan')
 for i,line in enumerate(lines):txt(n+'.line.'+str(i),line,(x-w*.45,y-.027,z+h*.06-i*h*.20),w*.033,'amber' if i==0 else 'white')
 return face
def set_targets(**kw):TARGETS[CUR.name].update(kw)
def proxy(n,p,d,title):
 x,y,z=p;w,dep,h=d;body=box(n+'.body',p,d,'cream',.009);door=box(n+'.sealed_face',(x,y-dep/2-.006,z),(w-.02,.011,h-.02),'navy',.002);door['closed']=True;door['qualified']=False
 txt(n+'.title',title,(x-w*.44,y-dep/2-.013,z+h*.30),w*.047)
 txt(n+'.disabled','EXTERNAL / NO CONTROLS',(x-w*.44,y-dep/2-.013,z+h*.08),w*.032,'amber')
 return body,door
def grip(n,p,d):
 o=box(n,p,d,'teal',.002);o['graspable']=False;o['candidate_grasp_region']=True;o['requires_qualification']=True;GRIPS.append({'asset_id':CUR.name,'scene_object':n,'translation_m':list(p),'dimensions_m':list(d),'allowed_interaction':'candidate carrier-contact label only','qualified_robot_pose':None,'physical_grasp_enabled':False,'active_region_contact_allowed':False});return o
def exclusion(o,why):
 o['contact_excluded']=True;EXCLUSIONS.append({'scene_object':o.name,'reason':why,'robot_contact_allowed':False,'geometry_or_boundary_qualified':False})
def collision(n,p,d):
 o=box(n,p,d,'amber',0);o.display_type='WIRE';o.hide_render=True;o['geometry_role']='collision_proxy';o['collision_qualified']=False;PROXIES.append({'scene_object':n,'shape':'box','translation_m':list(p),'dimensions_m':list(d),'collision_enabled':False,'fit_qualified':False});return o
def carrier(n,p,poly='pdms',sample=True):
 x,y,z=p;base=box(n+'.body',(x,y,z),(.092,.069,.013),'navy',.003);box(n+'.well',(x,y,z+.008),(.073,.052,.006),'cream',.001)
 left=grip(n+'.left_grip',(x-.055,y,z+.002),(.022,.034,.015));right=grip(n+'.right_grip',(x+.055,y,z+.002),(.022,.034,.015))
 for dx in [-.025,.025]:cyl(n+'.rest',(x+dx,y,z+.013),.004,.005,'teal')
 marker=box(n+'.orientation',(x-.032,y-.023,z+.013),(.008,.007,.003),'amber',0)
 if sample:
  s=cyl(n+'.glass',(x,y,z+.015),.012,.00017,'glass');s['source_dimensions_m']=[.024,.024,.00017];s['source_evidence']='E01';s['source_nominal_not_tolerance']=True;exclusion(s,'Fragile slide; handle carrier only')
  h=.000030 if poly=='pdms' else .000035;film=cyl(n+'.film',(x,y,z+.015+.000085+h/2),.012,h,poly);film['source_dimensions_m']=[.024,.024,h];film['source_evidence']='E01';film['source_nominal_not_tolerance']=True;film['composition_geometry_not_material_model']=True;exclusion(film,'Active coating face; never a robot grasp or collision contact')
  return base,left,right,s,film,marker
 return base,left,right,None,None,marker
# Room-scale original bench.
root('A01');box('bench.base',(0,0,.09),(2.72,1.68,.16),'cream',.020);box('bench.top',(0,0,.181),(2.71,1.67,.022),'metal',.006)
for x in [-1.2,1.2]:
 for y in [-.68,.68]:cyl('bench.foot',(x,y,.015),.05,.03,'black')
label('bench.title','WETTING TRANSITIONS / ORIGINAL STATIC LABORATORY',(0,-.851,.092),2.58,.062,.03)
x,y=-1.08,.28;tray=box('formulation.batch_tray',(x,y,.224),(.42,.34,.055),'navy',.006)
containers=[]
for i,(name,dx,col) in enumerate([('base',-.12,'pdms'),('component',0,'cy'),('additive',.12,'cream')]):
 o=cyl('formulation.'+name+'.container',(x+dx,y,.305),.042,.13,col);cyl('formulation.'+name+'.closed_cap',(x+dx,y,.382),.045,.024,'navy');o['sealed']=True;containers.append(o)
 txt('formulation.'+name+'.tag',name.upper(),(x+dx-.034,y-.044,.307),.010,'navy')
f=screen('formulation.receipt',(x,y+.19,.415),.43,.155,'A01 / FORMULATION',[ 'LOT / RECEIPT HOLD','CURE IS AN EXTERNAL SERVICE','NO PROCESS TELEMETRY'])
set_targets(base_container=containers[0],component_container=containers[1],additive_container=containers[2],balance_receipt=f,batch_tray=tray)
collision('collision.formulation',(x,y,.29),(.43,.35,.21))
# Protected custody rack with visible carrier-sized pockets and no ageing assertion.
root('A02');x,y=-1.03,-.51
rack=box('custody.rack',(x,y,.273),(.51,.43,.17),'navy',.007)
for i,dx in enumerate([-.17,0,.17]):
 box('custody.slot.'+str(i),(x+dx,y-.12,.32),(.145,.015,.11),'black',.001);label('custody.slot_label.'+str(i),['ID / HOLD','AGE / HOLD','QUARANTINE'][i],(x+dx,y-.224,.239),.155,.025,.009,'red' if i==2 else 'teal')
 for off in [-.04,.04]:grip('custody.carrier_tab.'+str(i)+str(off),(x+dx+off,y-.14,.35),(.019,.023,.018))
age=screen('custody.age_label',(x,y+.17,.440),.46,.17,'A02 / PROTECTED CUSTODY',['AGE REQUIRES REAL RECORDS','PDMS / CY LINEAGES SEPARATE','NO TIMER CERTIFIES STORAGE'])
spot=box('custody.spot_map',(x,y-.12,.367),(.13,.05,.006),'cream',.001);txt('custody.map_note','SPOT IDs',(x-.053,y-.137,.371),.010,'navy',True)
contain=box('custody.containment_slot',(x+.165,y+.065,.37),(.143,.14,.035),'red',.002)
set_targets(sample_rack=rack,age_label=age,spot_map=spot,quarantine_slot=bpy.data.objects['custody.slot.2'],containment_slot=contain)
collision('collision.custody',(x,y,.325),(.52,.44,.27))
# Film samples and distinct illustrative companion coupon.
root('A03');x,y=-.31,-.50
box('specimen.tray',(x,y,.211),(.75,.44,.038),'cream',.006)
a=carrier('specimen.pdms',(-.52,-.43,.246),'pdms');b=carrier('specimen.cy',(-.27,-.43,.246),'cy')
for prefix,cx,text in [('pdms',-.52,'PDMS / 30 um NOMINAL'),('cy',-.27,'CY / 35 um NOMINAL')]:
 txt('specimen.'+prefix+'.identity',text,(cx-.071,-.514,.236),.0075,'navy',True)
# Generic coupon is expressly a geometry placeholder, never a qualified tensile bar.
cp=box('specimen.coupon_carrier',(-.02,-.43,.244),(.12,.08,.020),'navy',.002)
gauge=box('specimen.coupon_gauge',(-.02,-.43,.257),(.038,.011,.002),'cy',0)
for dx in [-.027,.027]:box('specimen.coupon_grip_tab',(-.02+dx,-.43,.257),(.016,.026,.002),'cy',0)
for dx in [-.07,.07]:grip('specimen.coupon_carrier_grip',(-.02+dx,-.43,.245),(.018,.025,.018))
exclusion(gauge,'Illustrative coupon; dimensions and load geometry unqualified')
label('specimen.label','A03 / CARRIERS ONLY / FILMS AND COUPON NOT GRASP TARGETS',(-.31,-.728,.218),.75,.035,.012)
txt('specimen.coupon.note','COUPON: SIZE UNKNOWN',(-.095,-.513,.236),.0072,'navy',True)
set_targets(glass_slide=a[3],coating_surface=a[4],coupon=gauge,gauge_region=gauge,grip_tabs=bpy.data.objects['specimen.coupon_grip_tab'])
# Original robot end-effector illustration approaching carrier tabs, never touching sample.
robot=box('handling.illustrative_wrist',(-.52,-.647,.377),(.075,.085,.055),'metal',.004);robot['illustrative_robot_only']=True
for dx in [-.055,.055]:
 box('handling.gripper_finger',(-.52+dx,-.609,.324),(.018,.06,.095),'teal',.002)
label('handling.robot_label','STATIC TOOL / NO MOTION',(-.18,-.675,.287),.30,.026,.010)
# External specialist receipt interface only; no processing hardware.
root('A04');x,y=-.63,.48
body,door=proxy('patterning',(x,y,.315),(.32,.28,.245),'A04 / PATTERN RECEIPT')
i=box('patterning.sealed_input',(x-.08,y-.151,.267),(.115,.013,.046),'teal',.002);o=box('patterning.sealed_output',(x+.08,y-.151,.267),(.115,.013,.046),'metal',.002)
receipt=box('patterning.receipt',(x,y-.157,.335),(.27,.007,.021),'black',.001)
origin=box('patterning.array_origin_token',(x-.04,y,.451),(.035,.035,.008),'violet',.001);boundary=box('patterning.array_boundary_token',(x+.04,y,.451),(.038,.038,.008),'cyan',.001)
label('patterning.safe','SEALED CUSTODY ONLY',(x,y-.152,.210),.30,.022,.010)
set_targets(sealed_input_port=i,sealed_output_port=o,pattern_receipt=receipt,array_origin=origin,array_boundary=boundary)
collision('collision.patterning',(x,y,.325),(.33,.29,.27))
# Chamber: closed glazed frame, native slide carrier, sensor tokens and capped services.
root('A05');x,y=.03,.245
ch=box('chamber.base',(x,y,.235),(.62,.50,.09),'navy',.006);roof=box('chamber.roof',(x,y,.644),(.62,.50,.026),'cream',.005)
for dx in [-.285,.285]:
 for dy in [-.225,.225]:box('chamber.frame',(x+dx,y+dy,.438),(.024,.024,.39),'metal',.003)
# Back and side panels remain visually transparent; the front is a thin closed window.
window=box('chamber.closed_front_window',(x,y-.229,.436),(.54,.002,.35),'guard',0);window['closed']=True;window['service_qualified']=False
# Low transmission keeps glass readable; no real safety properties are implied.
for dx in [-.274,.274]:box('chamber.side_window',(x+dx,y,.436),(.002,.425,.35),'guard',0)
mount=box('chamber.sample_mount',(x,y,.370),(.13,.10,.031),'teal',.003)
mounted=carrier('chamber.native_carrier',(x,y,.397),'cy')
rh=cyl('chamber.RH_probe',(x-.21,y+.15,.48),.013,.065,'cyan');tp=cyl('chamber.temperature_probe',(x+.20,y+.15,.48),.008,.065,'amber')
ports=[]
for j,(dx,name) in enumerate([(-.16,'dry'),(0,'wet'),(.16,'exhaust')]):
 c=cyl('chamber.'+name+'.capped_port',(x+dx,y+.225,.56),.022,.045,'metal','Y');cyl('chamber.'+name+'.cap',(x+dx,y+.250,.56),.024,.01,'navy','Y');ports.append(c)
label('chamber.label','A05 / ENVIRONMENT CHAMBER',(x,y-.260,.248),.58,.044,.021)
label('chamber.hold','NO GAS OR MOTION / QUALIFICATION HOLD',(x,y-.262,.60),.55,.028,.012)
set_targets(sample_mount=mount,door=window,RH_probe=rh,temperature_probe=tp,dry_gas_receipt=ports[0],wet_gas_receipt=ports[1],exhaust_receipt=ports[2])
collision('collision.chamber',(x,y,.43),(.63,.51,.44))
# Water dispenser: fragile tip excluded; graspable-candidate carrier cradle only.
root('A06');x,y=.54,-.36
tray=box('dispense.waste_tray',(x,y,.216),(.32,.48,.047),'navy',.005);res=cyl('dispense.closed_water_reservoir',(x+.09,y+.12,.296),.052,.11,'glass');cyl('dispense.water_cap',(x+.09,y+.12,.361),.056,.025,'cream')
cradle=box('dispense.pipette_carrier',(x-.045,y-.075,.263),(.15,.20,.038),'cream',.003)
for dx in [-.092,.092]:grip('dispense.carrier_grip',(x-.045+dx,y-.075,.27),(.025,.067,.024))
pip=rod('dispense.pipette_body',(x-.045,y-.139,.299),(x-.045,y+.01,.299),.007,'glass');tip=rod('dispense.fragile_tip',(x-.045,y-.186,.299),(x-.045,y-.14,.299),.001,'glass');exclusion(pip,'Fragile pipette body, supported by carrier');exclusion(tip,'Micropipette tip is never graspable; source opening range is a reference, not a motion tolerance')
rec=screen('dispense.receipt',(x,y+.20,.434),.31,.135,'A06 / WATER',[ 'DISPENSER RECEIPT HOLD','NO GENERATED VOLUME','TIP: NO CONTACT'])
set_targets(water_reservoir=res,pipette_carrier=cradle,dispense_target=mounted[4],dispenser_receipt=rec,waste_tray=tray)
# Camera right of chamber with isolated optical path.
root('A07');x,y=.49,.31
camera_body=box('side.camera_housing',(x,y,.438),(.14,.16,.12),'navy',.008);lens=cyl('side.lens',(x-.083,y,.438),.037,.045,'black','X')
box('side.camera_mount',(x,y,.316),(.06,.08,.15),'metal',.003)
backlight=box('side.backlight',(-.28,.25,.443),(.018,.125,.12),'cream',.003)
scale=box('side.scale_target',(x,y-.092,.44),(.08,.009,.027),'cream',.001)
for j in range(7):box('side.scale_tick',(x-.033+j*.011,y-.098,.442),(.001,.002,.018 if j%2==0 else .008),'navy',0)
axis=rod('side.optical_axis_reference',(x-.105,y,.438),(.10,y,.438),.0008,'cyan');axis['geometry_role']='noninteractive_optical_guide';axis['source_tilt_approximately_deg']=5.;axis['pose_calibrated']=False
stream=screen('side.stream',(.81,.54,.51),.32,.16,'A07 / SIDE VIEW',['NO RAW FRAMES LOADED','5 DEG SOURCE APPROX.','POSE MUST BE CALIBRATED'])
set_targets(side_camera=camera_body,backlight=backlight,scale_target=scale,optical_axis=axis,side_frame_stream=stream)
# Bottom microscope drawn as guarded service beneath sample deck; no illumination controls.
root('A08');x,y=.03,.245
obj=cyl('bottom.objective',(x,y,.320),.039,.066,'metal');cyl('bottom.objective_barrel',(x,y,.28),.052,.024,'navy');zstage=box('bottom.z_stage',(x,y,.265),(.22,.16,.025),'black',.003)
origin=cyl('bottom.scan_origin',(x,y,.356),.012,.004,'cyan');exclusion(obj,'Optical objective and scan path; no robot contact')
f=screen('bottom.focus',(.09,.59,.803),.51,.185,'A08 / BOTTOM MICROSCOPY',['CLOSED OPTICAL SERVICE','FOCUS / TIMESTAMPS: HOLD','NO LASER OR SCAN CONTROLS'])
set_targets(bottom_objective=obj,z_stage=zstage,scan_origin=origin,focus_receipt=f,image_stream=f)
# Guarded mechanical frame and separate coupon mount.
root('A09');x,y=-1.10,.66
box('mechanics.base',(x,y,.252),(.37,.27,.11),'cream',.008)
for dx in [-.142,.142]:rod('mechanics.column',(x+dx,y,.30),(x+dx,y,.77),.019,'metal')
box('mechanics.top',(x,y,.784),(.36,.10,.046),'navy',.004)
mount=box('mechanics.coupon_mount',(x,y-.014,.464),(.085,.085,.055),'teal',.003);force=box('mechanics.force_sensor',(x,y,.653),(.062,.062,.10),'metal',.003)
rod('mechanics.specimen_placeholder',(x,y,.50),(x,y,.60),.011,'cy')
guard=box('mechanics.front_guard',(x,y-.086,.542),(.262,.002,.39),'guard',0);guard['closed']=True
strain=box('mechanics.strain_sensor',(x+.103,y-.02,.565),(.027,.025,.105),'black',.002)
raw=screen('mechanics.receipt',(x,y+.056,.886),.38,.15,'A09 / MECHANICS',['GUARDED / LOAD UNQUALIFIED','COUPON GEOMETRY UNKNOWN','NO TRACE OR MODULUS'])
set_targets(coupon_mount=mount,force_sensor_receipt=force,strain_sensor_receipt=strain,test_guard=guard,raw_trace_port=raw)
collision('collision.mechanics',(x,y,.60),(.39,.30,.75))
# Rheometer generic shape, plates as illustrative placeholders only.
root('A10');x,y=1.12,.48
box('rheology.base',(x,y,.254),(.34,.34,.12),'cream',.008);box('rheology.spine',(x,y+.09,.485),(.085,.09,.45),'navy',.004)
head=box('rheology.head',(x,y,.672),(.23,.25,.12),'cream',.008);rod('rheology.spindle',(x,y,.42),(x,y,.63),.018,'metal')
c=cyl('rheology.carrier',(x,y,.331),.10,.024,'teal');plate=cyl('rheology.geometry_placeholder',(x,y,.39),.063,.017,'metal');plate['measurement_geometry_qualified']=False
for dx in [-.12,.12]:grip('rheology.carrier_tab',(x+dx,y,.331),(.028,.05,.025))
guard=box('rheology.guard',(x,y-.13,.48),(.26,.002,.29),'guard',0);guard['closed']=True
raw=screen('rheology.receipt',(x,y+.115,.839),.36,.14,'A10 / RHEOLOGY',['GEOMETRY / AGE: HOLD','NO OSCILLATION CONTROLS','NO RHEOLOGY VALUES'])
set_targets(rheology_carrier=c,geometry_receipt=plate,oscillation_receipt=head,raw_rheology_port=raw)
collision('collision.rheology',(x,y,.55),(.37,.38,.72))
# Analysis is visibly separated by evidence kind. Every label states an absent dataset.
root('A11');x,y=1.07,-.35
box('analysis.base',(x,y,.228),(.48,.49,.07),'navy',.008)
f=screen('analysis.review',(x,y+.14,.49),.46,.35,'A11 / ANALYSIS & PROVENANCE',['NO DATA / NO SOLVER','OBSERVED != IMPUTED != INFERRED','SOURCE VALUES ARE NOT RESULTS'])
items={}
for name,col,dx,dy,tag in [('raw_archive','cyan',-.125,-.12,'RAW'),('point_annotation','magenta',0,-.12,'IMPUTED'),('array_match','cream',.125,-.12,'MATCH'),('reference_inference','violet',-.125,.025,'INFERRED'),('FE_service','amber',0,.025,'FE HOLD')]:
 o=box('analysis.'+name,(x+dx,y+dy,.28),(.10,.09,.024),col,.002);txt('analysis.'+name+'.label',tag,(x+dx-.043,y+dy-.013,.294),.008,'navy',True);items[name]=o
set_targets(**items,result_review=f)
label('analysis.label','RAW EVIDENCE RETAINED / DERIVED RESULTS HELD',(x,y-.255,.22),.47,.03,.010)
# Closeout remains independently accessible from every state.
root('A12');x,y=.44,-.69
body=box('closeout.archive_case',(x,y,.272),(.37,.17,.15),'navy',.005)
i=box('closeout.isolation_receipt',(x-.09,y-.09,.282),(.14,.009,.072),'amber',.002);cust=box('closeout.custody_receipt',(x+.09,y-.09,.282),(.14,.009,.072),'teal',.002)
q=box('closeout.quarantine_bin',(.84,-.72,.245),(.22,.17,.11),'red',.004);box('closeout.quarantine_lid',(.84,-.72,.308),(.23,.18,.016),'navy',.002)
mani=box('closeout.manifest',(x,y,.354),(.31,.10,.006),'cream',.001);txt('closeout.manifest.text','HASH / RAW / FAILURES',(x-.139,y-.017,.359),.012,'navy',True)
label('closeout.label','A12 / SAFE CLOSE REQUIRES RECEIPTS',(x,y-.094,.204),.37,.027,.011)
set_targets(isolation_receipt=i,custody_receipt=cust,quarantine_bin=q,immutable_manifest=mani)
# Large frame states limits visibly without reproducing any source figure.
CUR=None;box('lab.banner',(0,.87,1.065),(2.72,.025,.205),'navy',.008)
txt('lab.banner.title','WETTING TRANSITIONS',(-1.27,.853,1.102),.071)
txt('lab.banner.sub','STATIC LAB ROLES / 12 GROUPS / 74 OPERATION BINDINGS',(-1.26,.853,1.036),.036,'cyan')
txt('lab.banner.limit','ILLUSTRATIVE HARDWARE / NO LIVE CONTROL / NO MEASUREMENT TELEMETRY',(-1.26,.853,.987),.026,'amber')
box('studio.floor',(0,0,-.018),(200,200,.020),'floor',0)
def cam(n,p,target,scale):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);sc.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=scale;d.clip_start=1e-7;d.clip_end=100;return o
def light(n,p,power,size,target):
 d=bpy.data.lights.new(n,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(n,d);sc.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
light('LAB.key',(-2,-3,4),900,4,(0,0,.4));light('LAB.fill',(3,-1,3),550,3,(0,0,.4));light('LAB.rim',(0,3,3),1000,3,(0,0,.5))
CAMS={'overview':cam('CAM.overview',(3.15,-5.6,4.0),(0,.06,.46),3.80),'handling':cam('CAM.handling',(-.25,-1.75,1.47),(-.31,-.49,.29),1.12)};MAIN.camera=CAMS['overview']
bpy.context.view_layer.update()
# Canonical anchors refer to concrete geometry. No anchor is an authorized grasp.
anchors=[]
for spec in PLAN['groups']:
 r=ROOTS[spec['id']]
 for local in spec['required_anchors']:
  target=TARGETS[spec['id']][local];o=bpy.data.objects.new(spec['id']+'.'+local,None);MAIN.collection.objects.link(o);o.parent=r;o.location=target.matrix_world.translation;o.empty_display_type='PLAIN_AXES';o.empty_display_size=.015
  o['anchor_id']=local;o['asset_id']=spec['id'];o['target_object']=target.name;o['physical_execution']=False;o['coordinate_status']='authored_unqualified';o['graspable']=False
  anchors.append({'asset_id':spec['id'],'anchor_id':local,'scene_object':o.name,'target_object':target.name,'translation_m':list(o.location),'rotation_quaternion_xyzw':[0,0,0,1],'coordinate_status':'authored_unqualified','physical_qualified_transform':None,'interaction':'metadata_selector_only','physical_execution':False,'physical_grasp_enabled':False})
assets=[]
for aid,r in ROOTS.items():
 parts=[]
 for o in r.children:
  if o.type in ['MESH','FONT','CURVE']:
   parts.append({'part_id':o.name,'type':o.type,'dimensions_m':list(o.dimensions),'translation_m':list(o.location),'geometry_role':o.get('geometry_role','visual_mesh'),'geometry_basis':o.get('geometry_basis'),'source_dimensions_m':list(o['source_dimensions_m']) if 'source_dimensions_m' in o else None,'graspable':False,'contact_excluded':o.get('contact_excluded',False)})
 assets.append({'asset_id':aid,'role':r['role'],'display_scale':1,'physical_qualified_transform':None,'parts':parts})
(P/'asset_inventory.json').write_text(json.dumps({'schema':'wetting_original_scene.v1','units':'m','main_scene_group_count':len(assets),'original_asset_group_count':12,'imported_mesh_count':0,'assets':assets},indent=2)+'\n')
(P/'affordances.json').write_text(json.dumps({'implementation':'metadata_only','qualified_robot_poses':False,'anchors':anchors,'candidate_carrier_contacts':GRIPS,'exclusion_regions':EXCLUSIONS,'collision_proxies':PROXIES,'collision_limitations':'Only loose visual envelope boxes for selected large enclosures; no collision engine, dynamic contact, kinematics, torque, reachability or safe motion claims.'},indent=2)+'\n')
(P/'materials/materials.json').write_text(json.dumps([{'id':m.name,'base_color':list(m.diffuse_color),'appearance_only':True,'measured_material_properties':False} for m in M.values()],indent=2)+'\n')
# Display scene entirely separate from lab: whole slide 20x, microscope crop 1000x.
DISP=bpy.data.scenes.new('WETTING_SEPARATE_DIMENSION_REFERENCES');sc=DISP;bpy.context.window.scene=sc;setup(sc);CUR=None
box('display.base',(0,0,.015),(1.70,.72,.030),'cream',.009)
def display_root(name,scale,role):
 global CUR
 o=bpy.data.objects.new(name,None);sc.collection.objects.link(o);o['display_only']=True;o['uniform_display_scale']=scale;o['physical_execution']=False;o['role']=role;CUR=o;return o
whole=display_root('DISPLAY.WHOLE_SLIDE_20X',20.,'Source nominal reference; no robot interaction')
S=20.;x,y=-.46,-.035
slide=cyl('display.slide.glass',(x,y,.034),.012*S,.00017*S,'glass');slide['source_dimensions_m']=[.024,.024,.00017];slide['display_scale']=S
film=cyl('display.slide.pdms',(x,y,.034+.000085*S+.000015*S),.012*S,.000030*S,'pdms');film['source_dimensions_m']=[.024,.024,.000030];film['display_scale']=S
for dx in [-.24,.24]:rod('display.slide.width_tick',(x+dx,y-.27,.068),(x+dx,y-.25,.068),.0012,'navy')
rod('display.slide.width',(x-.24,y-.26,.068),(x+.24,y-.26,.068),.0012,'navy')
txt('display.slide.diameter','24 mm NOMINAL DIAMETER',(-.677,-.361,.075),.019,'navy',True)
label('display.slide.label','WHOLE SLIDE / UNIFORM 20x',(-.46,-.369,.026),.76,.043,.024)
label('display.slide.height','GLASS: 0.17 mm / PDMS: 30 um',(-.46,.256,.126),.74,.038,.020)
label('display.slide.height_limit','THICKNESSES ARE NOT EXAGGERATED',(-.46,.256,.083),.74,.032,.018)
micro=display_root('DISPLAY.MICROSCOPY_CROP_1000X',1000.,'Authored synthetic microscopy illustration, not source data')
S=1000.;x,y=.46,-.015
patch=box('display.micro.cy_patch',(x,y,.070),(.00056*S,.00040*S,.000035*S),'cy',0);patch['native_dimensions_m']=[.00056,.00040,.000035];patch['source_nominal_thickness_m']=.000035;patch['lateral_extent_status']='authored crop, not field of view';patch['display_scale']=S
# Synthetic cap from a smooth analytic surface, without any measurement claim.
verts=[(x,y,.0875+.080)];faces=[];N=64;R=.145;H=.080
for j in range(1,13):
 r=R*j/12
 for i in range(N):
  a=2*math.pi*i/N;verts.append((x+r*math.cos(a),y+r*math.sin(a),.0875+H*(1-(r/R)**2)))
for i in range(N):faces.append((0,1+i,1+(i+1)%N))
for j in range(11):
 for i in range(N):
  a=1+j*N+i;b=1+j*N+(i+1)%N;c=1+(j+1)*N+(i+1)%N;d=1+(j+1)*N+i;faces.append((a,b,c,d))
mesh=bpy.data.meshes.new('Synthetic cap mesh');mesh.from_pydata(verts,[],faces);mesh.update();drop=bpy.data.objects.new('display.micro.synthetic_drop',mesh);sc.collection.objects.link(drop);finish(drop,drop.name,'water');drop['synthetic']=True;drop['telemetry_authority']=False;drop['native_radius_m']=R/S;drop['shape_is_source_measurement']=False
for f in mesh.polygons:f.use_smooth=True
# Only illustrative triangular lattice nodes. Count/pitch are not source values.
for row in range(4):
 for col in range(6):
  px=x-.24+col*.080+(row%2)*.04;py=y-.155+row*.088
  if px>x+.255:continue
  p=cyl('display.micro.synthetic_marker',(px,py,.090),.005,.004,'cyan');p['synthetic']=True;p['observed_data']=False;p['source_pitch_known']=False
# Distinct shapes for imputed/reference roles; none are newly acquired data.
bpy.ops.mesh.primitive_torus_add(major_radius=.012,minor_radius=.002,major_segments=32,minor_segments=8,location=(x+.215,y-.12,.094));finish(bpy.context.object,'display.micro.imputed_role','magenta')['observed_data']=False
inf=box('display.micro.inferred_role',(x-.20,y+.10,.098),(.022,.022,.008),'violet',0);inf.rotation_euler.z=math.pi/4;inf['observed_data']=False
rod('display.micro.derived_direction_role',(x+.22,y+.13,.092),(x+.22,y+.13,.19),.003,'amber')
for dx in [-.02,.02]:rod('display.micro.derived_arrow',(x+.22+dx,y+.13,.166),(x+.22,y+.13,.19),.003,'amber')
label('display.micro.label','MICROSCOPY CROP / UNIFORM 1000x',(.46,-.369,.026),.82,.043,.022)
label('display.micro.thickness','CY: 35 um / CROP EXTENT AUTHORED',(.46,.258,.13),.76,.038,.019)
label('display.micro.limit','SYNTHETIC CAP + ARRAY / NO MEASUREMENTS',(.46,.258,.088),.76,.034,.0175)
# Scale bar describes native distance, not a metrological calibration.
rod('display.micro.scale',(.24,-.282,.115),(.34,-.282,.115),.0015,'navy')
txt('display.micro.scale_label','100 um NATIVE',(.37,-.292,.115),.018,'navy',True)
CUR=None;box('display.banner',(0,.40,.43),(1.7,.025,.34),'navy',.008)
txt('display.title','DIMENSIONAL REFERENCES / TWO DECLARED SCALES',(-.79,.384,.548),.035)
txt('display.subtitle','SOURCE NOMINAL DIMENSIONS / AUTHORED SHAPES / NO CALIBRATED PHYSICS',(-.79,.384,.495),.023,'cyan')
for i,(word,col) in enumerate([('RAW ROLE / EMPTY','cyan'),('IMPUTED ROLE','magenta'),('INFERRED ROLE','violet'),('DERIVED / HOLD','amber')]):
 txt('display.legend.'+str(i),word,(-.79+i*.405,.384,.422),.019,col)
txt('display.limit','MICROSCOPY PATCH IS NOT A ROBOT-GRASPABLE PART',(-.79,.384,.352),.026,'amber')
txt('display.source','Gerber et al. / Nature Communications 2019 / DOI 10.1038/s41467-019-12093-w',(-.79,.384,.298),.017)
box('display.studio.floor',(0,0,-.018),(200,200,.02),'floor',0)
light('DISPLAY.key',(-2,-3,3),650,2.5,(0,0,.15));light('DISPLAY.fill',(2,-1,2),400,2,(0,0,.15));light('DISPLAY.rim',(0,2,3),750,2,(0,0,.2))
DISP.camera=cam('CAM.dimensions',(1.0,-3.6,2.65),(0,.04,.24),2.14)
# Save native editable objects before text conversion for portable GLB export.
for scr in bpy.data.screens:
 for area in scr.areas:
  for sp in area.spaces:
   if sp.type=='FILE_BROWSER' and sp.params:sp.params.directory=b'//'
bpy.context.window.scene=MAIN;bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(P/'geometry/wetting_lab.blend'))
for scene,file in [(MAIN,'wetting_lab.glb'),(DISP,'wetting_dimension_references.glb')]:
 bpy.context.window.scene=scene
 for o in list(scene.objects):
  if o.type in ['FONT','CURVE']:
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 bpy.ops.object.select_all(action='DESELECT')
 for o in scene.objects:
  if o.type in ['MESH','EMPTY'] and 'studio.floor' not in o.name and not o.get('geometry_role')=='collision_proxy':o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(P/'geometry'/file),export_format='GLB',use_selection=True,use_active_scene=True,export_apply=True,export_extras=True)
views=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['overview','handling','dimensions']
rec={'engine':'CYCLES','device':'CPU','blender_version':bpy.app.version_string,'samples':96,'denoising':False,'resolution':[1800,1200],'source_pixels_used':False,'views':[]}
for view in views:
 scene=DISP if view=='dimensions' else MAIN;bpy.context.window.scene=scene
 if view!='dimensions':scene.camera=CAMS[view]
 scene.render.filepath=str(P/'evidence'/f'{view}.png');bpy.ops.render.render(write_still=True)
 p=P/'evidence'/f'{view}.png';raw=p.read_bytes();clean=raw[:8];offset=8
 while offset<len(raw):
  n=struct.unpack('>I',raw[offset:offset+4])[0];kind=raw[offset+4:offset+8]
  if kind not in [b'tEXt',b'zTXt',b'iTXt']:clean+=raw[offset:offset+n+12]
  offset+=n+12
 p.write_bytes(clean);rec['views'].append({'id':view,'scene':scene.name,'camera':scene.camera.name,'file':'evidence/'+p.name,'sha256':hashlib.sha256(clean).hexdigest(),'actual_render':True,'text_metadata_removed':True})
if views:(P/'review/render_receipt.json').write_text(json.dumps(rec,indent=2)+'\n')
print('WETTING_ASSET_BUILD_COMPLETE')
