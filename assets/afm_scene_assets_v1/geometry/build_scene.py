"""Original parametric AFM scene. Blender 4.3+, CPU Cycles. No imported CAD/images.
All coordinates in metres. Microscopy insets explicitly magnified; apparatus sizes authored.
"""
import bpy, math, json, os, sys
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.materials): bpy.data.materials.remove(d)
sc=bpy.context.scene
sc.unit_settings.system='METRIC'; sc.unit_settings.scale_length=1
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=160
sc.cycles.use_denoising=False
sc.render.resolution_x=1600; sc.render.resolution_y=1100; sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'
sc.world.color=(.18,.18,.18)
sc.view_settings.view_transform='AgX';sc.view_settings.exposure=-1.5
ROOTS={}; CUR=None

def mat(n,c,metal=0,rough=.4,alpha=1):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,alpha);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,alpha);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 return m
M={'ivory':mat('Powdercoat • warm ceramic',(.75,.79,.78),.12,.3),'navy':mat('Anodized • midnight',(.025,.064,.078),.65,.32),'teal':mat('Authored interface • teal',(.03,.52,.48),.3,.28),'gold':mat('Authored datum • brass',(.72,.43,.13),.7,.3),'steel':mat('Brushed metal • visual only',(.43,.50,.53),.85,.26),'black':mat('Graphite elastomer • visual only',(.018,.025,.028),.05,.52),'silicon':mat('Silicon appearance • nonmeasured',(.13,.18,.24),.82,.18),'sapphire':mat('Sapphire appearance • nonmeasured',(.29,.68,.79),.3,.24),'pdms':mat('PDMS appearance • nonmeasured',(.70,.60,.77),.1,.38),'aluminum':mat('Reflective Al appearance • nonmeasured',(.76,.82,.87),.93,.22),'white':mat('Label • ivory',(.93,.96,.92),.05,.6),'orange':mat('Hold / authored placeholder',(.94,.34,.11),.25,.4),'floor':mat('Studio floor',(.79,.84,.85),0,.8)}

def root(id,label,kind,ops,source,scale=1):
 global CUR
 o=bpy.data.objects.new(id,None);sc.collection.objects.link(o);o.empty_display_type='PLAIN_AXES';o.empty_display_size=.025
 for k,v in {'asset_id':id,'asset_version':'1.0.0','label':label,'readiness':'static_kinematic_semantic_only','dimension_provenance':kind,'operation_ids':','.join(ops),'source_evidence':','.join(source),'display_scale':scale,'physical_execution':False}.items():o[k]=v
 ROOTS[id]=o;CUR=o;return o

def finish(o,n,m):
 o.name=n
 if m:o.data.materials.append(M[m])
 if CUR:o.parent=CUR
 o['authored_original_geometry']=True
 return o

def box(n,p,d,m='navy',bevel=.002):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.dimensions=d;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(o,n,m)
 if bevel:
  b=o.modifiers.new('Manufactured edge radii (authored)','BEVEL');b.width=min(bevel,min(d)/3);b.segments=3
  o.modifiers.new('Surface normals','WEIGHTED_NORMAL')
 return o

def cyl(n,p,r,h,m='steel',vertices=48,axis='Z'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=h,location=p);o=bpy.context.object
 if axis=='X':o.rotation_euler.y=math.pi/2
 if axis=='Y':o.rotation_euler.x=math.pi/2
 finish(o,n,m)
 for f in o.data.polygons:f.use_smooth=True
 return o

def cone(n,p,r,h,m='aluminum',down=True,r2=0):
 bpy.ops.mesh.primitive_cone_add(vertices=24,radius1=r2 if down else r,radius2=r if down else r2,depth=h,location=p);return finish(bpy.context.object,n,m)

def rod(n,a,b,r=.003,m='steel'):
 mid=(Vector(a)+Vector(b))/2;o=cyl(n,mid,r,(Vector(b)-Vector(a)).length,m);o.rotation_euler=(Vector(b)-Vector(a)).to_track_quat('Z','Y').to_euler();return o

def text(n,s,p,size=.018,m='white',flat=False):
 c=bpy.data.curves.new(n,'FONT');c.body=s;c.size=size;c.extrude=.0001;c.space_character=1.05
 o=bpy.data.objects.new(n,c);sc.collection.objects.link(o);o.location=p
 if not flat:o.rotation_euler=(math.pi/2,0,0)
 return finish(o,n,m)

def frontlabel(n,s,p,w=.28,h=.055,size=.018):
 box(n+'.plate',p,(w,.005,h),'navy',.003);text(n+'.text',s,(p[0]-w*.45,p[1]-.003,p[2]-.007),size)

def bolt(n,x,y,z,r=.003):
 cyl(n,(x,y,z),r,.002,'steel',6)

def ring(n,p,r,t,m='steel'):
 bpy.ops.mesh.primitive_torus_add(major_segments=64,minor_segments=8,location=p,major_radius=r,minor_radius=t);return finish(bpy.context.object,n,m)

def camera(n,p,target,lens=50,ortho=None):
 c=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,c);sc.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();c.lens=lens;c.clip_start=.00001;c.clip_end=100
 if ortho:c.type='ORTHO';c.ortho_scale=ortho
 return o

def light(n,p,power,size,target=(0,0,.4)):
 d=bpy.data.lights.new(n,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(n,d);sc.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()

# LAB CONTEXT / source-independent authored environment
root('afm.lab_bench','Optical metrology bench','authored_design',[],[])
box('bench.top',(0,0,.08),(1.65,.92,.10),'ivory',.018)
box('bench.inset',(0,0,.134),(1.53,.82,.016),'steel',.012)
for x in [-.65,.65]:
 for y in [-.30,.30]:box('bench.isolator',(x,y,.026),(.105,.105,.085),'black',.016)
for x in [-.72,-.56,-.4,-.24,-.08,.08,.24,.4,.56,.72]:
 for y in [-.32,-.16,0,.16,.32]:cyl('bench.threaded_grid',(x,y,.143),.0025,.001,'black',16)
frontlabel('bench.title','CANTILEVER-FREE AFM  /  OPERATIONS LAB',(0,-.465,.085),1.25,.057,.027)
text('bench.subtitle','ORIGINAL ASSETS  |  STATIC / SEMANTIC STUDY  |  SOURCE SCALE HOLD',(-.59,-.469,.046),.014)
box('studio.floor',(0,0,-.06),(200,200,.06),'floor',0)
# MAIN PARALLEL INSTRUMENT
root('afm.parallel_instrument','Parallel imaging / Mitutoyo configuration','authored_apparatus_envelope',['MOUNT_ARRAY','LEVEL','BASELINE','CALIBRATE_CONTACT','RASTER','LINE'],['E_SETUP','E_ARRAY_CAL','E_RELEASE'])
X=-.39
box('parallel.base',(X,.08,.168),(.62,.55,.048),'navy',.014)
for x in [X-.235,X+.235]:
 cyl('parallel.column',(x,.225,.45),.026,.53,'steel');cyl('parallel.column.foot',(x,.225,.206),.042,.035,'black')
box('parallel.bridge',(X,.23,.64),(.56,.11,.16),'ivory',.014)
box('parallel.z_carriage',(X,.13,.548),(.16,.10,.29),'navy',.008)
for x in [X-.054,X+.054]:rod('parallel.z_rail',(x,.075,.43),(x,.075,.667),.008)
box('parallel.optical_arm',(X,.025,.67),(.13,.29,.067),'ivory',.01)
# Camera and objective looking down through sapphire
box('parallel.camera',(X,-.05,.794),(.10,.075,.115),'navy',.007)
box('parallel.camera.teal',(X,-.092,.80),(.08,.004,.012),'teal',.001)
cyl('parallel.tube',(X,-.05,.688),.030,.105,'steel')
cyl('parallel.objective_body',(X,-.05,.585),.038,.105,'navy')
cyl('parallel.objective_ring',(X,-.05,.613),.041,.015,'gold')
cyl('parallel.objective_nose',(X,-.05,.515),.027,.04,'steel')
cyl('parallel.lens',(X,-.05,.494),.022,.003,'sapphire')
frontlabel('parallel.config','A / PARALLEL',(X,.169,.676),.28,.048,.021)
frontlabel('parallel.optics','10x MITUTOYO / NA 0.28',(X,-.31,.242),.42,.048,.019)
frontlabel('parallel.static','PIEZO XYZ + TILT / VISUAL ONLY',(X,-.244,.193),.48,.035,.014)
# Source roles, original hardware proportions. Two stacked translation rails.
box('parallel.x_stage',(X,-.045,.222),(.37,.34,.045),'steel',.006)
box('parallel.y_stage',(X,-.055,.257),(.30,.25,.028),'navy',.005)
for dx in [-.11,.11]:box('parallel.y_rail',(X+dx,-.055,.278),(.019,.25,.016),'steel',.002)
box('parallel.sample_stage',(X,-.065,.292),(.245,.20,.020),'ivory',.003)
cyl('parallel.x_knob',(X+.23,-.04,.225),.024,.067,'black',48,'X')
cyl('parallel.y_knob',(X,-.247,.256),.022,.073,'black',48,'Y')
for i in range(8):box('parallel.micrometer_ticks',(X-.019+i*.005,-.288,.262),(.0008,.001,.007),'white',0)
# Semantically movable mount assembly, raised no-contact pose. Bounds are authored.
root('afm.array_mount','Array perimeter support mount','authored_design',['MOUNT_ARRAY','LEVEL'],['E_SETUP'])
for dx in [-.072,.072]:
 box('array.mount.rail',(X+dx,-.05,.44),(.026,.125,.025),'steel',.004)
 box('array.mount.retainer',(X+dx,-.05,.421),(.018,.07,.01),'teal',.002)
 rod('array.mount.hanger',(X+dx,.001,.452),(X+dx,.11,.568),.009)
box('array.mount.front',(X,-.103,.44),(.12,.02,.025),'steel',.003)
box('array.mount.rear',(X,.003,.44),(.12,.02,.025),'steel',.003)
# Carrier-sized sapphire envelope; extent is explicitly authored, no whole-array span inferred
root('afm.probe_array','Downward probe subset on sapphire / PDMS / reflective film','mixed_source_structure_authored_extent',['MOUNT_ARRAY','BASELINE','CALIBRATE_CONTACT','RASTER','LINE'],['E_FAB','E_ARRAY_CAL','E_SI2'])
box('array.sapphire',(X,-.05,.438),(.10,.077,.002),'sapphire',.0001)
box('array.pdms',(X,-.05,.4365),(.081,.062,.001),'pdms',.0001)
box('array.reflective_film',(X,-.05,.435999985),(.08,.061,30e-9),'aluminum',0)
# True metre-scale source-model subset. 49 probes is illustrative; not the reported 1088 allocation.
for j in range(7):
 for i in range(7):
  x=X+(i-3+(j%2)*.5)*15e-6;y=-.05+(j-3)*15e-6*math.sqrt(3)/2
  o=cone('array.microcone.%02d.%02d'%(j,i),(x,y,.43599997-3e-6),3e-6,6e-6,r2=1e-7);o['parameter_class']='SI_numerical_model_not_measured_probe'
# Source-bound target + authored carrier on mounted rig
root('afm.sample_carrier','Retained sample carrier / grasp tabs','authored_design',['RECEIVE','TRANSFER_IN','MOUNT_TARGET','TRANSFER_OUT','CLEAN_STORE'],[])
box('carrier.loaded.base',(X,-.065,.315),(.185,.145,.022),'navy',.006)
for dx in [-.103,.103]:
 box('carrier.loaded.grasp_tab',(X+dx,-.065,.315),(.027,.052,.016),'teal',.004)
 for dy in [-.015,0,.015]:box('carrier.loaded.grip_rib',(X+dx,-.065+dy,.324),(.020,.002,.0015),'black',.0002)
root('afm.silicon_target','Inert silicon calibration target','authored_extent_source_material_and_region_roles',['MOUNT_TARGET','REGISTER_TARGET','RASTER','LINE'],['E_ARROW','E_LINE','E_COMPLEX','E_SETUP'])
box('target.silicon',(X,-.065,.329),(.097,.079,.002),'silicon',.0006)
# Macroscopic target motif is conspicuously authored, not TGXYZ02 layout/dimensions
for i in range(5):box('target.authored_line_motif',(X-.032+i*.009,-.061,.3301),(.002,.031,.0001),'steel',0)
for i in range(3):
 for j in range(3):cyl('target.authored_pit_motif',(X+.021+i*.008,-.086+j*.008,.3301),.002,.0001,'black',24)
# reusable clamp individual moving objects
root('afm.retention_clamps','Authored swing clamps','authored_design',['MOUNT_TARGET','TRANSFER_IN','TRANSFER_OUT'],[])
for dx in [-.073,.073]:
 cyl('clamp.loaded.pivot',(X+dx,-.038,.340),.009,.025,'gold')
 box('clamp.loaded.arm',(X+dx/1.5,-.038,.346),(.051,.018,.013),'steel',.003)
 cyl('clamp.loaded.handle',(X+dx,-.038,.357),.012,.010,'black')
# Port / semantic control fixture, distinct, no electrical simulation
root('afm.interface_panel','Authored state and connector panel','authored_design',['VERIFY_INPUT','RELEASE','INSPECT'],[])
box('interface.panel',(X+.25,-.12,.315),(.09,.16,.14),'ivory',.005)
for iz,col in enumerate(['teal','orange']):
 o=cyl('interface.'+('release_readback' if iz==0 else 'hold_ack'),(X+.25,-.202,.345-iz*.04),.014,.008,col,48,'Y');o['mechanism']='semantic_state_only_no_device_IO'
text('interface.release_label','REL',(X+.222,-.208,.362),.008)
text('interface.hold_label','HOLD',(X+.221,-.208,.284),.008)
cyl('interface.sensor_port',(X+.299,-.13,.32),.011,.012,'black',32,'X')
# CHARACTERIZATION CONFIGURATION (not swapped into parallel system)
root('afm.characterization_instrument','SI characterization / inverted Olympus optics','authored_apparatus_envelope',['MOUNT_LEVER','MOUNT_COUPON','THERMAL_PSD','GLASS_SENSITIVITY','LOCATE_CENTER','FORCE_DISTANCE','SYNCHRONIZED_FORCE_OPTICS','OFF_CENTER_SCHEDULE'],['E_SI3','E_SI5','E_SI7'])
C=.42
box('character.base',(C,.13,.172),(.53,.48,.06),'ivory',.012)
box('character.rear_column',(C,.28,.352),(.115,.09,.34),'navy',.008)
box('character.upper_arm',(C,.14,.506),(.18,.34,.058),'ivory',.008)
box('character.afm_head',(C,.035,.443),(.135,.10,.072),'navy',.008)
for dx in [-.16,.16]:
 rod('character.table_leg',(C+dx,.04,.212),(C+dx,.04,.343),.015)
box('character.open_frame.left',(C-.12,.04,.350),(.08,.22,.025),'steel',.004)
box('character.open_frame.right',(C+.12,.04,.350),(.08,.22,.025),'steel',.004)
box('character.open_frame.back',(C,.125,.350),(.25,.05,.025),'steel',.004)
# inverted objective pointing upward
cyl('character.olympus_body',(C,.025,.275),.032,.083,'navy')
cyl('character.olympus_ring',(C,.025,.300),.035,.012,'teal')
cyl('character.olympus_nose',(C,.025,.325),.023,.025,'steel')
cyl('character.olympus_lens',(C,.025,.338),.020,.001,'sapphire')
box('character.camera',(C+.115,.025,.236),(.09,.075,.055),'navy',.004)
rod('character.optical_tube',(C,.025,.235),(C+.09,.025,.235),.021,'black')
frontlabel('character.config','B / CHARACTERIZATION',(C,-.036,.528),.43,.040,.017)
frontlabel('character.optics','10x OLYMPUS / NA UNREPORTED',(C,-.039,.491),.44,.027,.012)
# cylindrical coupon physical structure; whole envelope authored
root('afm.cylinder_coupon','Cylinder test coupon / source dimensions','mixed_source_dimensions_authored_allocation',['MOUNT_COUPON','LOCATE_CENTER','FORCE_DISTANCE','SYNCHRONIZED_FORCE_OPTICS','OFF_CENTER_SCHEDULE'],['E_SI3','E_SI5'])
box('coupon.sapphire',(C,.025,.367),(.13,.11,.001),'sapphire',.0001)
box('coupon.pdms',(C,.025,.367507),(.09,.08,14e-6),'pdms',0)
for i,r in enumerate([3e-6,4e-6,5e-6,6e-6,7e-6,8e-6]):
 o=cyl('coupon.micro_cylinder.%d'%i,(C+(i-2.5)*40e-6,.025,.367517),r,6e-6,'aluminum',24);o['radius_allocation']='illustrative_range_samples_not_experiment_map'
root('afm.conventional_lever','AFM cantilever visualization','authored_visual_placeholder',['MOUNT_LEVER','THERMAL_PSD','GLASS_SENSITIVITY','FORCE_DISTANCE'],['E_SI3'])
box('lever.holder',(C,.041,.396),(.043,.04,.016),'steel',.002)
box('lever.visible_placeholder',(C,.012,.384),(.008,.05,.0015),'gold',.0001)
cone('lever.visible_tip',(C,-.009,.380),.0015,.006,'gold',True)
# source dimensions here are not asserted; visible lever deliberately enlarged placeholder
# Handling workcell foreground with retained target, empty dock and abstract gripper proxy
root('afm.handling_dock','Reusable kinematic dock and access frame','authored_design',['TRANSFER_IN','MOUNT_TARGET','TRANSFER_OUT','CLEAN_STORE','INSPECT'],[])
H=.40;Y=-.29
box('handling.dock',(H,Y,.17),(.41,.20,.04),'navy',.008)
for dx in [-.12,.12]:
 cyl('handling.locator',(H+dx,Y+.04,.201),.007,.023,'gold')
box('handling.datum',(H,Y+.07,.193),(.20,.016,.012),'teal',.002)
frontlabel('handling.label','CARRIER / AUTHORED INTERFACES',(H,-.398,.179),.49,.038,.014)
# removable carrier, lifted onto authored illustrative hover pose
root('afm.sample_carrier_demo','Same design, separate handling instance','authored_design',['TRANSFER_IN','MOUNT_TARGET','TRANSFER_OUT'],[])
box('carrier.demo.base',(H,Y,.257),(.185,.145,.022),'navy',.005)
for dx in [-.103,.103]:box('carrier.demo.grasp_tab',(H+dx,Y,.257),(.027,.052,.016),'teal',.003)
box('carrier.demo.inert_sample',(H,Y,.272),(.097,.079,.002),'silicon',.0005)
for dx in [-.073,.073]:
 cyl('clamp.demo.pivot',(H+dx,Y+.027,.281),.009,.025,'gold')
 o=box('clamp.demo.open_arm',(H+dx,Y+.048,.29),(.018,.051,.013),'steel',.003);o['state']='open'
# Dashed approach path authored, no reachability claim
root('afm.robot_grasp_proxy','Authored parallel-jaw access proxy','authored_visual_placeholder',['TRANSFER_IN','TRANSFER_OUT'],[])
for dx in [-.128,.128]:
 box('gripper.finger',(H+dx,Y-.045,.304),(.018,.095,.12),'orange',.004)
 box('gripper.contact_pad',(H+dx*.92,Y-.015,.259),(.013,.050,.026),'black',.002)
box('gripper.bridge',(H,Y-.088,.367),(.30,.03,.035),'orange',.004)
for z in [.39,.415,.44]:rod('gripper.approach_dash',(H,Y-.09,z),(H,Y-.09,z+.014),.002,'orange')
text('gripper.placeholder_label','GRASP PROXY',(H-.12,Y-.105,.402),.018,'navy')
# Authored handling datum axes: visible frame convention, not a robot registration.
for axis,end,col in [('X',(.245,-.36,.214),'orange'),('Y',(.19,-.305,.214),'teal'),('Z',(.19,-.36,.269),'gold')]:
 rod('handling.datum_axis.'+axis,(.19,-.36,.214),end,.0015,col)
 text('handling.axis_label.'+axis,axis,(end[0]+.004,end[1]-.005,end[2]+.003),.014,'navy')
# 100 mm authored ruler for apparatus scale, not the unresolved scientific field span
root('afm.scale_reference','100 mm reference ruler','authored_exact_reference',[],[])
box('ruler.body',(-.57,-.32,.157),(.22,.043,.010),'ivory',.002)
for i in range(11):box('ruler.tick',(-.65+i*.01,-.325,.163),(.0009,.016 if i%5==0 else .009,.0007),'navy',0)
text('ruler.text','100 mm',(-.647,-.312,.164),.009,'navy',True)
# EXPLODED MICROASSEMBLY EXPLANATORY DISPLAY, separate from apparatus world
root('afm.probe_explainer','Exploded 7x7 source-model subset','magnified_source_model_and_authored_separation',['MOUNT_ARRAY','BASELINE'],['E_FAB','E_SI2'],1000)
EX=0;EY=1.65;EZ=.35
box('explainer.card',(EX,EY,.10),(1.20,.70,.025),'ivory',.013)
box('explainer.sapphire',(EX-.19,EY,.53),(.15,.14,.035),'sapphire',.003)
box('explainer.pdms',(EX-.19,EY,.46),(.135,.12,.014),'pdms',.001)
box('explainer.al_film',(EX-.19,EY,.423),(.135,.12,30e-6),'aluminum',.0002)
for j in range(7):
 for i in range(7):cone('explainer.cone.%02d.%02d'%(j,i),(EX-.19+(i-3+(j%2)*.5)*.015,EY+(j-3)*.015*math.sqrt(3)/2,.401),.003,.006,r2=.0001)
# Display-only long cones overlay? retain genuine scaled 6um length, camera close enough.
box('explainer.target',(EX-.19,EY,.35),(.16,.14,.018),'silicon',.003)
for i in range(4):box('explainer.target_line',(EX-.235+i*.02,EY,.360),(.008,.065,.001),'steel',.0002)
# original arrow motif
for label,z,col in [('SAPPHIRE',.54,'sapphire'),('PDMS BACKING',.465,'pdms'),('REFLECTIVE Al',.428,'steel'),('CONICAL SUBSET',.40,'navy'),('SILICON TARGET',.35,'silicon')]:
 rod('explainer.leader.'+label,(EX-.1,EY,z),(EX+.085,EY,z),.001,col)
 text('explainer.label.'+label,label,(EX+.10,EY-.003,z-.005),.016,'navy')
text('explainer.title','DISTRIBUTED OPTICAL LEVER',(-.53,EY-.24,.128),.031,'navy',True)
text('explainer.warning','1000x microfeatures | support slabs and gaps authored',(-.53,EY-.29,.128),.014,'navy',True)
text('explainer.scalehold','Whole-array span: HOLD / 0.5 mm vs 5 mm source conflict',(-.53,EY-.33,.128),.014,'orange',True)
# Cylinder characterization magnified detail, physically supported values separate from conical model
root('afm.cylinder_explainer','Source-dimension cylinder detail','magnified_source_dimensions_authored_allocation',['MOUNT_COUPON','FORCE_DISTANCE'],['E_SI3'],1000)
for i,r in enumerate([.003,.004,.005,.006,.007,.008]):
 cyl('explainer.cylinder.%d'%i,(.28+(i%3)*.035,EY-.02+(i//3)*.04,.244),r,.006,'aluminum',32)
box('explainer.cylinder_pdms',(.315,EY,.234),(.125,.10,.014),'pdms',.001)
box('explainer.cylinder_sapphire',(.315,EY,.215),(.14,.12,.02),'sapphire',.002)
text('explainer.cylinders_title','CYLINDER COUPON',(.16,EY-.13,.165),.017,'navy')
text('explainer.cylinders_dims','6 um tall / R 3-8 um',(.16,EY-.13,.145),.014,'navy')
text('explainer.cylinders_note','Radius allocation authored',(.16,EY-.13,.125),.011,'orange')
CUR=None
# Two separate apparatus sites remain visible in overview; explainer isolated by camera.
light('Key softbox',(-1.6,-1.4,2.7),380,2.0)
light('Fill softbox',(1.8,-.6,1.5),220,1.8)
light('Rim softbox',(.2,1.7,2.0),450,1.6)
light('Explainer softbox',(-.4,1.3,1.5),100,1.0,(0,1.65,.3))
CAMS={
'overview':camera('CAM.overview',(1.5,-2.35,1.55),(-.04,0,.42),50,1.95),
'equipment_closeup':camera('CAM.equipment_closeup',(.45,.05,.97),(0,1.65,.30),55,1.42),
'sample_handling':camera('CAM.sample_handling',(.96,-1.17,.99),(.30,-.20,.27),55,.87)}
# hide microscopy-only explanatory display for main apparatus views by collection-independent flags.
for id in ['afm.probe_explainer','afm.cylinder_explainer']:
 for o in ROOTS[id].children:o.hide_render=True
sc.camera=CAMS['overview']
# Save canonical inventory before export. Transforms are local-to-parent, explicit metric dimensions.
bpy.context.view_layer.update()
assets=[]
for aid,r in ROOTS.items():
 parts=[]
 for o in r.children:
  if o.type in ['MESH','FONT']:
   parts.append({'part_id':o.name,'type':o.type,'dimensions_m':[round(float(v),10) for v in o.dimensions],'translation_m':list(o.location),'rotation_quaternion_xyzw':[o.rotation_euler.to_quaternion()[i] for i in [1,2,3,0]],'scale':list(o.scale),'source_dimension_status':r['dimension_provenance']})
 assets.append({'asset_id':aid,'asset_version':'1.0.0','instance_id':aid+'.01','dimension_provenance':r['dimension_provenance'],'display_scale':r['display_scale'],'parts':parts,'operation_ids':r['operation_ids'].split(',') if r['operation_ids'] else [],'source_evidence_ids':r['source_evidence'].split(',') if r['source_evidence'] else [],'readiness':'static_kinematic_semantic_only'})
(OUT/'asset_inventory.json').write_text(json.dumps({'schema':'afm_original_scene.v1','units':'metres','assets':assets},indent=2))
(OUT/'materials'/'materials.json').write_text(json.dumps([{'id':m.name,'base_color':list(m.diffuse_color),'appearance_only':True,'measured_optical_properties':False} for m in M.values()],indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'geometry'/'afm_operations_lab.blend'))
# Convert labels in the export working copy; editable Blender file retains FONT objects.
for o in list(sc.objects):
 if o.type=='FONT':
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
# Export visible apparatus separately from microscope explainer to prevent display magnification confusion.
for o in bpy.context.selected_objects:o.select_set(False)
for o in sc.objects:
 if o.type in ['MESH','EMPTY'] and 'explainer' not in o.name and not (o.parent and 'explainer' in o.parent.name) and not o.name.startswith('studio.'):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'geometry'/'afm_operations_lab.glb'),export_format='GLB',use_selection=True,export_apply=True,export_extras=True)
# Also export the explicitly magnified display as separate portable asset.
for o in bpy.context.selected_objects:o.select_set(False)
for id in ['afm.probe_explainer','afm.cylinder_explainer']:
 ROOTS[id].select_set(True)
 for o in ROOTS[id].children:
  if o.type=='MESH':o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'geometry'/'afm_magnified_explainer.glb'),export_format='GLB',use_selection=True,export_apply=True,export_extras=True)
# Render CPU evidence. Explicitly restore each requested view's visibility.
views=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(CAMS)
for view in views:
 isdetail=view=='equipment_closeup'
 for id,r in ROOTS.items():
  for o in r.children:o.hide_render=('explainer' in id)!=isdetail and o.name!='studio.floor'
 sc.camera=CAMS[view];sc.render.filepath=str(OUT/'evidence'/f'{view}.png');bpy.ops.render.render(write_still=True)
print('AFM_ASSET_BUILD_COMPLETE')
