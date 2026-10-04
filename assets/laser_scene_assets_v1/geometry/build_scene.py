"""Original static laser-control scene. No publisher art, CAD, signal or hardware IO.
Source facts are reference metadata; every apparatus dimension/placement is authored.
Blender CPU Cycles. Main metric scene and separate 1000x nominal footprint display.
"""
import bpy, math, json, sys, hashlib
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[1]
PLAN=json.loads((OUT/'task_binding_snapshot.json').read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.materials):bpy.data.materials.remove(d)
MAIN=bpy.context.scene;MAIN.name='LASER_AUTHORED_METRIC';sc=MAIN
ROOTS={};CUR=None;ANCHORS=[]
def setup(s):
 s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
 s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=40;s.cycles.use_denoising=False
 s.render.resolution_x=1600;s.render.resolution_y=1100;s.render.resolution_percentage=100
 s.render.image_settings.file_format='PNG';s.world.color=(.15,.17,.20)
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
 for k,v in {'asset_id':aid,'asset_version':'1.0.0','role':a['role'],'authored_dimension_status':'unqualified_authored_metres','physical_execution':False,'device_io':False,'laser_energy_enabled':False,'display_only':False,'operation_ids':','.join(a['bind_operation_ids'])}.items():o[k]=v
 ROOTS[aid]=o;CUR=o;return o

def finish(o,n,m=None):
 o.name=n
 if m:o.data.materials.append(M[m])
 if CUR:o.parent=CUR
 o['geometry_basis']='original_authored';o['physical_geometry_validated']=False;o['device_io']=False;o['laser_energy_enabled']=False
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

def cable(n,pts,m='teal',r=.0025):
 c=bpy.data.curves.new(n,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=3;s=c.splines.new('BEZIER');s.bezier_points.add(len(pts)-1)
 for b,p in zip(s.bezier_points,pts):b.co=p;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
 o=bpy.data.objects.new(n,c);sc.collection.objects.link(o);finish(o,n,m);o['signal_present']=False;o['route_status']='authored_dormant_visual_only';return o

def port(n,p,r=.012):
 cyl(n+'.collar',p,r,.011,'steel','Y');o=cyl(n+'.cap',(p[0],p[1]-.008,p[2]),r*.73,.008,'black','Y');o['capped']=True;return o

def camera(n,p,target,scale):
 c=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,c);sc.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();c.type='ORTHO';c.ortho_scale=scale;c.clip_start=.000001;c.clip_end=100;return o

def light(n,p,power,size,target):
 d=bpy.data.lights.new(n,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(n,d);sc.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()

root('A_DESIGN_CONSOLE')
box('bench.base',(0,.04,.052),(1.92,1.14,.09),'ivory',.017)
box('bench.top',(0,.04,.108),(1.87,1.09,.022),'steel',.007)
label('bench.title','MODULATION-FREE LASER CONTROL / STATIC RESEARCH ASSETS',(0,-.54,.056),1.79,.05,.025)
box('design.body',(-.64,.43,.28),(.36,.15,.31),'navy',.012)
box('design.screen',(-.64,.349,.303),(.316,.014,.208),'black',.004)
txt('design.title','DESIGN RECORDS',(-.78,.339,.377),.020)
txt('design.scope','SOI PHYSICAL SOURCE',(-.78,.339,.339),.015,'cyan')
txt('design.sin','SiN: NUMERICAL ONLY',(-.78,.339,.305),.015,'amber')
txt('design.result','NO SOLVER / NO RESULTS',(-.78,.339,.264),.013)
txt('design.cad','NO SOURCE CAD',(-.78,.339,.231),.014)
for key,z in [('requirements_card',.34),('model_card',.30),('design_release',.26)]:anchor(key,(-.64,.333,z),'design.screen')
root('A_FABRICATION_SERVICE')
box('foundry.body',(-.24,.44,.248),(.30,.23,.25),'ivory',.012)
box('foundry.sealed_door',(-.24,.317,.261),(.26,.014,.186),'navy',.003)
txt('foundry.title','PIC FOUNDRY',(-.356,.307,.320),.017)
txt('foundry.closed','CLOSED SERVICE',(-.356,.307,.280),.014,'amber')
txt('foundry.process','100 nm SOI PROCESS',(-.356,.307,.242),.012)
txt('foundry.no_recipe','NO RECIPE / NO GDS',(-.356,.307,.207),.012)
for key,x in [('design_in',-.31),('fabrication_status',-.24),('pic_carrier_out',-.17)]:anchor(key,(x,.307,.245),'foundry.sealed_door')
root('A_PCB_SERVICE')
box('pcb.body',(.10,.44,.248),(.30,.23,.25),'ivory',.012)
box('pcb.sealed_door',(.10,.317,.261),(.26,.014,.186),'navy',.003)
txt('pcb.title','PCB / PACKAGING',(-.016,.307,.320),.016)
txt('pcb.closed','CLOSED SERVICE',(-.016,.307,.280),.014,'amber')
txt('pcb.no_layout','NO BOARD LAYOUT',(-.016,.307,.242),.012)
txt('pcb.no_bond','NO BOND MAP',(-.016,.307,.207),.012)
for key,x in [('pcb_design_in',.03),('package_status',.10),('package_out',.17)]:anchor(key,(x,.307,.245),'pcb.sealed_door')
root('A_PACKAGE_CUSTODY')
box('custody.dock',(-.65,-.31,.139),(.33,.29,.04),'navy',.007)
reuse=json.loads((OUT/'geometry/reused_carrier_components.json').read_text());origin=(-.65,-.31,.174)
for p in reuse['parts']:
 mesh=bpy.data.meshes.new('reuse.'+p['source_part_id']);mesh.from_pydata(p['vertices'],[],p['faces']);mesh.update();o=bpy.data.objects.new('reuse.'+p['source_part_id'],mesh);sc.collection.objects.link(o);o.parent=CUR
 o.location=tuple(origin[i]+p['translation_m'][i] for i in range(3));o.rotation_euler=p['rotation_euler_rad'];o.scale=p['scale']
 for q,smooth in zip(mesh.polygons,p['smooth_faces']):q.use_smooth=smooth
 name=p['source_material'].lower();key='teal' if 'teal' in name else 'steel' if 'metal' in name else 'gold' if 'brass' in name else 'black' if 'graphite' in name else 'navy';mesh.materials.append(M[key])
 for mod in p['modifiers']:
  m=o.modifiers.new('Preserved original '+mod['type'],mod['type'])
  if m.type=='BEVEL':m.width=mod['width'];m.segments=mod['segments']
 o['geometry_basis']='reused_original_afm_mesh';o['source_asset_family']=p['source_asset_family'];o['source_part_id']=p['source_part_id'];o['new_unique_asset_credit']=0;o['physical_geometry_validated']=False;o['laser_energy_enabled']=False
# Carrier remains empty. Sealed package is a separate authored object on a separate pedestal.
box('package.pedestal',(-.63,-.042,.143),(.23,.18,.048),'navy',.005)
box('package.closed_case',(-.63,-.042,.195),(.18,.135,.063),'teal',.006)
box('package.opaque_lid',(-.63,-.042,.232),(.184,.14,.012),'ivory',.002)
for x in [-.705,-.555]:
 for y in [-.095,.010]:cyl('package.lid_fastener',(x,y,.240),.004,.003,'steel',vertices=12)
txt('package.identity','PIC-001 / SEALED',(-.703,-.073,.24),.011,'navy',True)
label('custody.label','EMPTY CARRIER / NO FIT CLAIM',(-.65,-.463,.145),.34,.036,.0105)
# Nominal native XY extent is a 2D reference plane, not a fabricated die or thickness assertion.
verts=[(-.000475,-.00024,0),(.000475,-.00024,0),(.000475,.00024,0),(-.000475,.00024,0)]
mesh=bpy.data.meshes.new('pic.nominal_extent');mesh.from_pydata(verts,[],[(0,1,2,3)]);mesh.update();o=bpy.data.objects.new('pic.native_footprint_reference',mesh);sc.collection.objects.link(o);o.location=(-.63,-.042,.2401);finish(o,o.name,'gold');o['source_footprint_m']=[.00095,.00048];o['source_area_m2']=.000000456;o['die_thickness_modelled']=False;o['physical_die']=False
for key,p,t in [('package_origin',(-.63,-.042,.195),'package.closed_case'),('carrier_slot',(-.65,-.31,.185),'reuse.carrier.loaded.base'),('identity_card',(-.63,-.073,.24),'package.identity'),('inspection_view',(-.63,-.07,.25),'package.opaque_lid'),('pic_native_extent',(-.63,-.042,.2401),'pic.native_footprint_reference'),('grasp_left',(-.753,-.31,.174),'reuse.carrier.loaded.grasp_tab'),('grasp_right',(-.547,-.31,.174),'reuse.carrier.loaded.grasp_tab.001')]:anchor(key,p,t)
root('A_SAFETY_ENCLOSURE')
box('enclosure.base',(-.15,-.17,.149),(.54,.39,.065),'navy',.008)
box('enclosure.closed_cover',(-.15,-.16,.246),(.49,.34,.143),'ivory',.009)
box('enclosure.top_plate',(-.15,-.16,.325),(.45,.30,.012),'navy',.003)
txt('enclosure.title','OPTICAL SERVICE',(-.341,-.244,.333),.022,'white',True)
txt('enclosure.energy','ENERGY DISABLED',(-.341,-.191,.333),.024,'amber',True)
txt('enclosure.no_beam','NO BEAM / NO SIGNAL',(-.341,-.14,.333),.018,'white',True)
txt('enclosure.heaters','HEATERS 1 + 2: OFF',(-.341,-.091,.333),.017,'white',True)
box('enclosure.status_panel',(-.15,-.337,.244),(.41,.010,.085),'navy',.002)
txt('enclosure.sealed','SEALED / EXTERNAL QUALIFICATION',(-.337,-.344,.262),.012)
txt('enclosure.not_safe','STATIC VIEW IS NOT SAFETY EVIDENCE',(-.337,-.344,.232),.011,'amber')
port('enclosure.alignment',(.050,-.347,.192),.016)
txt('enclosure.port_label','CAPPED',(.011,-.362,.164),.010,'navy')
for key,p,t in [('closed_cover',(-.15,-.16,.325),'enclosure.closed_cover'),('interlock_card',(-.25,-.348,.26),'enclosure.status_panel'),('safe_state',(-.13,-.348,.23),'enclosure.status_panel'),('alignment_port',(.050,-.362,.192),'enclosure.alignment.cap')]:anchor(key,p,t)
root('A_OPEN_LOOP_STATION')
box('open_loop.body',(-.58,.17,.192),(.40,.18,.142),'navy',.010)
box('open_loop.face',(-.58,.073,.203),(.354,.014,.102),'black',.003)
txt('open_loop.title','OPEN-LOOP SERVICE',(-.738,.062,.235),.016)
txt('open_loop.cal','20 MHz MZI / NO CALIBRATION',(-.738,.062,.207),.0105,'cyan')
txt('open_loop.readouts','SNIFFER: NONE   ERROR: NONE',(-.738,.062,.176),.0105,'amber')
for key,x in [('ecdl_port',-.72),('voa_port',-.63)]:port('open_loop.'+key,(x,.074,.142),.009);anchor(key,(x,.060,.142),'open_loop.'+key+'.cap')
for key,x,z in [('temperature_card',-.50,.23),('mzi_frequency_reference',-.48,.207),('sniffer_record',-.67,.177),('balanced_error_record',-.48,.177)]:anchor(key,(x,.06,z),'open_loop.face')
root('A_DFB_CONTROL_STATION')
box('dfb.bank',(.33,-.34,.150),(.44,.23,.058),'navy',.007)
for i,x in enumerate([.19,.33,.47],1):
 box(f'dfb{i}.sealed_module',(x,-.34,.21),(.119,.158,.059),'ivory',.006)
 box(f'dfb{i}.opaque_lid',(x,-.34,.244),(.114,.152,.01),'teal',.002)
 txt(f'dfb{i}.identity',f'DFB {i}',(x-.044,-.395,.251),.020,'white',True)
 txt(f'dfb{i}.disabled','DISABLED',(x-.044,-.355,.251),.010,'white',True)
 port(f'dfb{i}.output',(x,-.429,.208),.011);anchor(f'dfb{i}_slot',(x,-.34,.244),f'dfb{i}.sealed_module')
box('control.body',(.32,-.10,.187),(.38,.19,.136),'navy',.007)
box('control.face',(.32,-.202,.200),(.339,.014,.083),'black',.003)
txt('control.title','TIA / PID: DISABLED',(.166,-.212,.224),.017,'amber')
txt('control.none','NO LOCK / NO CURRENT CONTROL',(.166,-.212,.194),.0105)
txt('control.settings','SETTINGS: EXTERNAL',(.166,-.212,.171),.0105)
for key,x,z in [('tia_record',.20,.225),('pid_record',.39,.225),('bias_noise_card',.24,.174),('lock_evidence',.40,.194)]:anchor(key,(x,-.214,z),'control.face')
# Dormant authorship-only cable arcs. Caps stay present; no optical connectivity asserted.
cable('routing.dormant_fiber',[(.48,-.22,.152),(.54,-.04,.153),(.40,.035,.154),(.18,.06,.154),(.06,-.03,.17)],'teal',.003)
cable('routing.dormant_cable',[(.14,-.09,.145),(.07,.06,.147),(-.05,.095,.146),(-.31,.06,.148),(-.37,-.01,.153)],'black',.004)
root('A_REFERENCE_CHAIN')
box('reference.body',(.60,.33,.288),(.44,.38,.334),'navy',.014)
box('reference.face',(.60,.131,.303),(.39,.016,.260),'black',.004)
txt('reference.title','COMB-REFERENCED',(.425,.118,.406),.021)
txt('reference.subtitle','HETERODYNE SERVICE',(.425,.118,.371),.017,'cyan')
txt('reference.independent','INDEPENDENT / NO ACQUISITION',(.425,.118,.336),.011)
for key,x,z,caption in [('reference_laser',.47,.291,'REF'),('fp_cavity',.60,.291,'FP'),('comb',.73,.291,'COMB'),('filter',.47,.215,'FILTER'),('receiver',.60,.215,'RX'),('digitizer_record',.73,.215,'DIG')]:
 port('reference.'+key,(x,.115,z),.019);txt('reference.label.'+key,caption,(x-.027,.101,z-.035),.010,'white');anchor(key,(x,.096,z),'reference.'+key+'.cap')
root('A_FPGA_ANALYSIS')
box('fpga.body',(.75,-.23,.190),(.28,.34,.140),'ivory',.012)
box('fpga.face',(.75,-.408,.207),(.242,.014,.098),'navy',.003)
txt('fpga.title','FPGA / IN-LOOP',(.642,-.419,.235),.016)
txt('fpga.relative','RELATIVE ERROR ONLY',(.642,-.419,.210),.011,'cyan')
txt('fpga.no_signal','NO SIGNAL / NO PSD',(.642,-.419,.185),.011,'amber')
box('fpga.top',(.75,-.23,.267),(.24,.29,.013),'navy',.003)
txt('fpga.distinct','IN-LOOP != ABSOLUTE',(.645,-.32,.275),.011,'white',True)
txt('fpga.archive','RECORDS EMPTY',(.645,-.26,.275),.014,'white',True)
for key,x,z in [('fpga_record',.67,.233),('psd_record',.78,.208),('analysis_card',.72,.182),('archive_slot',.84,.182)]:anchor(key,(x,-.421,z),'fpga.face')
root('A_HOLD_PANEL')
box('hold.panel',(-.09,.195,.497),(.52,.022,.16),'navy',.008)
txt('hold.title','DEFAULT: HOLD',(-.321,.18,.548),.032,'amber')
txt('hold.no_energy','LASER ENERGY DISABLED',(-.321,.18,.507),.022)
txt('hold.no_io','NO HARDWARE IO / NO PHYSICS',(-.321,.18,.472),.015)
txt('hold.records','RECORDS DO NOT ENABLE HARDWARE',(-.321,.18,.442),.012)
for key,x in [('qualification_hold',-.29),('calibration_hold',-.19),('reference_hold',-.09),('lock_hold',.01),('damage_hold',.11)]:anchor(key,(x,.178,.46),'hold.panel')
for x in [-.31,.13]:rod('hold.support',(x,.209,.12),(x,.209,.42),.009,'steel')
CUR=None
box('studio.floor',(0,0,-.02),(200,200,.02),'floor',0)
light('LIGHT.key',(-1.2,-1.5,2.7),490,1.8,(0,0,.23));light('LIGHT.fill',(2,-.3,1.9),270,1.9,(0,0,.25));light('LIGHT.rim',(-.2,1.8,2.4),500,1.7,(0,0,.25))
CAMS={'overview':camera('CAM.overview',(1.40,-2.5,1.85),(0,.035,.28),2.45),'package_handling':camera('CAM.package_handling',(-.92,-1.03,1.15),(-.56,-.18,.20),.98)}
MAIN.camera=CAMS['overview'];bpy.context.view_layer.update()
assets=[]
for aid,r in ROOTS.items():
 parts=[]
 for o in r.children:
  if o.type in ['MESH','FONT','CURVE']:
   q=o.rotation_euler.to_quaternion();parts.append({'part_id':o.name,'type':o.type,'dimensions_m':list(o.dimensions),'translation_m':list(o.location),'rotation_quaternion_xyzw':[q.x,q.y,q.z,q.w],'scale':list(o.scale),'geometry_basis':o.get('geometry_basis','original_authored'),'physical_geometry_validated':False,'source_part_id':o.get('source_part_id')})
 assets.append({'asset_id':aid,'instance_id':aid+'.01','role':r['role'],'operation_ids':r['operation_ids'].split(','),'display_scale':1,'coordinate_space':'AUTHORED_METRIC','physical_qualified_transform':None,'parts':parts})
(OUT/'asset_inventory.json').write_text(json.dumps({'schema':'laser_original_scene.v1','units':'m','main_scene_group_count':len(assets),'unique_asset_count':None,'reused_mesh_count':15,'reused_new_unique_asset_credit':0,'assets':assets},indent=2)+'\n')
(OUT/'affordances.json').write_text(json.dumps({'implementation':'metadata_only','qualified_robot_poses':False,'anchors':ANCHORS},indent=2)+'\n')
(OUT/'materials/materials.json').write_text(json.dumps([{'id':m.name,'base_color':list(m.diffuse_color),'appearance_only':True,'measured_material_properties':False,'emission':False} for m in M.values()],indent=2)+'\n')
# Separate original explanatory display: footprint only is exactly 1000x.
DISPLAY=bpy.data.scenes.new('DISPLAY_ONLY_1000X');DISPLAY.world=MAIN.world.copy();sc=DISPLAY;bpy.context.window.scene=sc;setup(sc)
CUR=bpy.data.objects.new('DISPLAY.pic_nominal_footprint',None);sc.collection.objects.link(CUR);CUR['display_only']=True;CUR['footprint_scale_factor']=1000;CUR['scale_applies_to']='nominal planar footprint only';CUR['native_scene']='LASER_AUTHORED_METRIC';CUR['physical_die']=False
mesh=bpy.data.meshes.new('display.nominal_extent');mesh.from_pydata([(-.475,-.24,0),(.475,-.24,0),(.475,.24,0),(-.475,.24,0)],[],[(0,1,2,3)]);mesh.update();o=bpy.data.objects.new('display.pic_footprint_reference',mesh);sc.collection.objects.link(o);o.location=(0,0,.125);finish(o,o.name,'teal');o['display_only']=True;o['native_dimensions_m']=[.00095,.00048];o['uniform_planar_scale_factor']=1000
box('display.plinth',(0,0,.059),(1.15,.65,.115),'ivory',.017)
for x in [-.475,.475]:rod('display.x_extent', (x,-.275,.13),(x,-.255,.13),.0025,'gold')
rod('display.width_gauge',(-.475,-.265,.13),(.475,-.265,.13),.002,'gold')
for y in [-.24,.24]:rod('display.y_extent',(.499,y,.13),(.519,y,.13),.0025,'gold')
rod('display.height_gauge',(.509,-.24,.13),(.509,.24,.13),.002,'gold')
txt('display.width','0.95 mm native / 0.95 m display',(-.37,-.30,.137),.025,'navy',True)
txt('display.height','0.48 mm',(.535,-.06,.137),.023,'navy',True)
txt('display.area','0.456 mm2 NOMINAL FOOTPRINT',(-.42,.173,.132),.033,'white',True)
txt('display.no_layout','NO CIRCUIT LAYOUT / NO DIE THICKNESS',(-.42,.112,.132),.025,'white',True)
# Floating labeled blocks are role legend only, do not represent a circuit topology or mask.
for x,w,n,title in [(-.28,.27,'coupler','COUPLING'),(.03,.25,'ring','CAVITY'),(.32,.25,'detector','DETECTION')]:
 box('display.role.'+n,(x,-.06,.155),(w,.18,.04),'navy',.007);txt('display.role_label.'+n,title,(x-w*.43,-.055,.182),.020,'white',True)
txt('display.roles_note','ROLE LEGEND ONLY / ORIGINAL ARRANGEMENT',(-.42,-.20,.134),.023,'white',True)
label('display.title','PIC NOMINAL EXTENT / 1000x PLANAR DISPLAY',(0,-.331,.068),1.08,.06,.026)
box('display.info_panel',(0,.32,.337),(1.22,.021,.32),'navy',.013)
txt('display.info_title','REFERENCE DIMENSIONS, NOT DEVICE CAD',(-.545,.305,.445),.036,'white')
txt('display.info_1','MAIN SCENE: 0.95 x 0.48 mm planar reference',(-.545,.305,.380),.027,'cyan')
txt('display.info_2','PACKAGE / PORTS / ROUTING: AUTHORED, UNQUALIFIED',(-.545,.305,.326),.022)
txt('display.info_3','220 nm silicon layer; 100 nm SOI process label',(-.545,.305,.273),.025)
txt('display.info_4','ENERGY DISABLED / NO SIGNAL / NO SIMULATION',(-.545,.305,.219),.025,'amber')
CUR=None
box('display.studio.floor',(0,0,-.02),(200,200,.02),'floor',0)
light('DISPLAY.key',(-1,-1.5,2),380,1.8,(0,0,.25));light('DISPLAY.fill',(1.4,-.3,1.3),160,1.5,(0,0,.25));light('DISPLAY.rim',(0,1,2),280,1.5,(0,0,.2))
DISPLAY.camera=camera('CAM.measurement',(1.2,-2.5,1.8),(0,0,.22),1.67)
bpy.context.window.scene=MAIN;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'geometry/laser_control_lab.blend'))
for scene,path in [(MAIN,'laser_control_lab.glb'),(DISPLAY,'laser_pic_display.glb')]:
 bpy.context.window.scene=scene
 for o in list(scene.objects):
  if o.type in ['FONT','CURVE']:
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 bpy.ops.object.select_all(action='DESELECT')
 for o in scene.objects:
  if o.type in ['MESH','EMPTY'] and 'studio.floor' not in o.name:o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(OUT/'geometry'/path),export_format='GLB',use_selection=True,use_active_scene=True,export_apply=True,export_extras=True)
views=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['overview','package_handling','measurement']
receipt={'engine':'CYCLES','device':'CPU','blender_version':bpy.app.version_string,'samples':MAIN.cycles.samples,'resolution':[1600,1100],'views':[],'source_pixels_used':False}
for view in views:
 scene=DISPLAY if view=='measurement' else MAIN;bpy.context.window.scene=scene
 if view!='measurement':scene.camera=CAMS[view]
 scene.render.filepath=str(OUT/'evidence'/f'{view}.png');bpy.ops.render.render(write_still=True)
 p=OUT/'evidence'/f'{view}.png';receipt['views'].append({'id':view,'scene':scene.name,'camera':scene.camera.name,'file':'evidence/'+p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'actual_render':True})
if views:(OUT/'review/render_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('LASER_ASSET_BUILD_COMPLETE')
