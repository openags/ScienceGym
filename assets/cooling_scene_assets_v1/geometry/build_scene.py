"""Original directional-cooling lab; Blender 4.3+, CPU Cycles.
SI dimensions only where explicitly tagged. Apparatus, fixtures, gaps and paths authored.
No imported mesh, image, manufacturer CAD or measured material/thermal model.
Primitive helper idioms adapted from original afm_scene_assets_v1 (Apache-2.0).
"""
import bpy, math, json, sys, time
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
START=time.time()
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene
sc.unit_settings.system='METRIC'; sc.unit_settings.scale_length=1
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=192
sc.cycles.use_denoising=False
sc.render.resolution_x=1500; sc.render.resolution_y=1080; sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'; sc.render.film_transparent=False
sc.world.color=(.25,.25,.25);sc.view_settings.view_transform='AgX';sc.view_settings.exposure=-1.45
ROOTS={}; CUR=None

def mat(n,c,metal=0,rough=.4):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 return m
M={k:mat(n,c,m,r) for k,n,c,m,r in [
 ('ivory','Ceramic enamel / authored',(.75,.81,.79),.12,.29),('navy','Midnight anodized / authored',(.017,.052,.066),.6,.29),
 ('teal','Interface teal / authored',(.018,.44,.37),.3,.3),('gold','Datum brass / authored',(.75,.43,.12),.7,.27),
 ('steel','Brushed steel / appearance only',(.44,.54,.59),.82,.3),('al','Polished aluminum / unmeasured',(.8,.87,.91),.92,.21),
 ('black','Flat black emitter / unmeasured',(.012,.016,.018),0,.75),('white','Flat white emitter / unmeasured',(.91,.93,.87),0,.63),
 ('pe','Nanoporous PE / unmeasured',(.87,.92,.82),0,.55),('foam','XPS insulation / unmeasured',(.47,.31,.48),0,.7),
 ('cu','Copper edge / unmeasured',(.65,.29,.12),.78,.3),('amber','Heater insulation / unmeasured',(.69,.25,.035),.15,.43),
 ('rubber','Soft pads / authored',(.027,.032,.035),0,.72),('orange','Unresolved gate marker',(.88,.26,.055),.25,.36),
 ('floor','Studio floor',(.72,.79,.79),0,.8),('screen','Unlit readback panel',(.015,.026,.036),.1,.42)]}

def root(n,label,ops=(),source=(),kind='authored_design',display=False):
 global CUR
 o=bpy.data.objects.new(n,None);sc.collection.objects.link(o);o.empty_display_type='PLAIN_AXES';o.empty_display_size=.02
 props={'asset_id':n,'asset_version':'1.0.0','label':label,'operation_ids':','.join(ops),'source_evidence':','.join(source),'dimension_provenance':kind,'display_only':display,'physical_execution':False,'readiness':'static_semantic_only'}
 for k,v in props.items():o[k]=v
 ROOTS[n]=o;CUR=o;return o

def finish(o,n,m,source=None):
 o.name=n
 if m:o.data.materials.append(M[m])
 if CUR:o.parent=CUR
 o['authored_original_geometry']=True;o['dimension_status']=source or 'authored_design_not_source_measurement'
 return o

def box(n,p,d,m='navy',b=.002,source=None):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.dimensions=d;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(o,n,m,source)
 if b:
  mod=o.modifiers.new('Authored edge radii','BEVEL');mod.width=min(b,min(d)/3);mod.segments=3
  o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o

def cyl(n,p,r,h,m='steel',N=64,source=None,axis='Z'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=N,radius=r,depth=h,location=p);o=bpy.context.object
 if axis=='X':o.rotation_euler.y=math.pi/2
 if axis=='Y':o.rotation_euler.x=math.pi/2
 finish(o,n,m,source)
 for f in o.data.polygons:f.use_smooth=True
 return o

def ann(n,p,ri,ro,h,m='al',N=96,source=None):
 verts=[]
 for z,r in [(-h/2,ri),(-h/2,ro),(h/2,ri),(h/2,ro)]:
  verts.extend([(p[0]+r*math.cos(2*math.pi*i/N),p[1]+r*math.sin(2*math.pi*i/N),p[2]+z) for i in range(N)])
 faces=[]
 for i in range(N):
  j=(i+1)%N
  faces.extend([(i,j,N+j,N+i),(2*N+i,3*N+i,3*N+j,2*N+j),(i,2*N+i,2*N+j,j),(N+i,N+j,3*N+j,3*N+i)])
 mesh=bpy.data.meshes.new(n+'.mesh');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(n,mesh);sc.collection.objects.link(o);return finish(o,n,m,source)

def rod(n,a,b,r=.002,m='steel'):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,N=24);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def path(n,points,r=.001,m='rubber'):
 c=bpy.data.curves.new(n,'CURVE');c.dimensions='3D';c.resolution_u=12;c.bevel_depth=r;c.bevel_resolution=3
 s=c.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
 for bp,p in zip(s.bezier_points,points):bp.co=p;bp.handle_left_type='AUTO';bp.handle_right_type='AUTO'
 o=bpy.data.objects.new(n,c);sc.collection.objects.link(o);return finish(o,n,m)

def text(n,s,p,size=.013,m='navy',flat=False):
 c=bpy.data.curves.new(n,'FONT');c.body=s;c.size=size;c.extrude=.00008;c.space_character=1.03
 o=bpy.data.objects.new(n,c);sc.collection.objects.link(o);o.location=p
 if not flat:o.rotation_euler.x=math.pi/2
 return finish(o,n,m)

def label(n,s,p,w,h=.032,size=.012,m='ivory'):
 box(n+'.plate',p,(w,.003,h),'navy',.001)
 text(n+'.text',s,(p[0]-w*.46,p[1]-.002,p[2]-size*.35),size,m)

def bolt(n,p):return cyl(n,p,.003,.002,'steel',6)
def frame(n,x,y,z,w,d):
 for xx in [x-w/2,x+w/2]:
  box(n+'.rail',(xx,y,z),(.016,d,.022),'al',.001)
  box(n+'.groove',(xx,y,z+.0112),(.004,d-.007,.0006),'navy',0)

def camera(n,p,t,ortho):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);sc.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=ortho;d.clip_start=.0001;return o

def light(n,p,e,size,t=(0,0,.2)):
 d=bpy.data.lights.new(n,'AREA');d.energy=e;d.shape='DISK';d.size=size;o=bpy.data.objects.new(n,d);sc.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()

# One coherent authored lab bench. All meters, Z-up.
root('cooling.lab_bench','Directional cooling workcell',(),(),kind='authored_laboratory')
box('bench.top',(0,0,.095),(1.62,1.00,.08),'ivory',.022)
box('bench.inset',(0,0,.14),(1.54,.91,.014),'steel',.013)
for x in [-.66,.66]:
 for y in [-.35,.35]:box('bench.foot',(x,y,.026),(.105,.11,.075),'rubber',.013)
for x in [-.72+i*.08 for i in range(19)]:
 for y in [-.4+i*.08 for i in range(11)]:cyl('bench.grid',(x,y,.1478),.0019,.0005,'navy',12)
label('bench.title','DIRECTIONAL COOLING  /  OPERATIONS LAB',(0,-.505,.10),1.33,.051,.024)
text('bench.subtitle','ORIGINAL METRIC ASSETS   |   STATIC / SEMANTIC STUDY',(-.49,-.507,.065),.013,'navy')
box('studio.floor',(0,0,-.032),(200,200,.045),'floor',0)

# Both source-layout devices have independent identities. No fake temperature numbers.
for sample,x,paint in [('white',-.49,'white'),('black',-.13,'black')]:
 n='cooling.'+sample
 root(n,'Solar-'+sample+' assembly',('BASE','EMITTER','FILM','SHIELD','REFLECTOR','TC_ATTACH','HEATER_ATTACH','ASSEMBLY_QC','LID_REMOVE','TRACK_ADJUST'),('E_BUILD','E_GEOM_AMBIG','E_CAL','E_POWER'),kind='source_component_dimensions_authored_mounts')
 y=.17; z=.180; ez=z+.05025
 box(sample+'.acrylic_base',(x,y,.164),(.305,.278,.012),'ivory',.004)
 box(sample+'.mylar_base_visual',(x,y,.1703),(.285,.26,.0006),'al',0)
 frame(sample+'.frame',x,y,.182,.275,.27)
 # physical specimens: dimensions from SI Note 2.
 cyl(sample+'.assembly_support_pedestal',(x,y,.17535),.078,.0093,'navy',source='Authored support pedestal; not a source component dimension')
 for k in range(2):
  foam=cyl(sample+f'.insulation.{k+1}',(x,y,z+.0125+k*.025),.025,.025,'foam',source='SI Note 2: 50 mm diameter; 25 mm layer envelope; upper-layer 1.2 mm heater recess authored')
  if k==1:
   cutter=cyl(sample+'.temporary_recess_cutter',(x,y,z+.05),.023,.0024,'foam')
   mod=foam.modifiers.new('Authored heater clearance recess','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
   bpy.context.view_layer.objects.active=foam;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
 cyl(sample+'.emitter_copper',(x,y,ez),.025,.0005,'cu',source='SI Note 2: diameter .05 m; thickness .0005 m')
 cyl(sample+'.emitter_paint_visual',(x,y,ez+.00029),.025,.00008,paint,source='Coat color and count sourced; visual paint thickness authored, actual thickness unknown')
 ann(sample+'.pe_support',(x,y,z+.026),.038,.051,.052,'pe',source='SI ID .076 m and OD .102 m; HEIGHT .052 m AUTHORED, source height unknown')
 # solid PE upper datum and source-size ring; layer separation has authored mounting datum.
 rz=z+.0552
 ann(sample+'.film_frame',(x,y,rz),.0535,.0635,.0064,'al',source='SI Note 2: ID .107 m; OD .127 m; ring thickness .0064 m')
 for k,h in [('lower',rz-.003208),('upper',rz+.003208)]:
  o=cyl(sample+'.film.'+k,(x,y,h),.062,.000016,'pe',source='SI Note 2: thickness 16 um; circular trim radius .062 m authored')
  o['component_identity']=sample+'.nanoporous_pe.'+k+'.rev1';o['display_thickness_scale']=1
 # shield housing source envelope; retain independent aperture and removable baseline lid.
 ann(sample+'.shield_adapter',(x,y,z+.00175),.070,.076,.0035,'navy',source='Authored 3.5 mm spacer beneath source-size shield; not reported')
 ann(sample+'.radiation_shield',(x,y,z+.032),.070,.076,.057,'al',source='SI Note 2: ID .14 m; OD .152 m; height .057 m')
 ann(sample+'.aperture_plate',(x,y,z+.0615),.025,.076,.002,'al',source='SI aperture .05 m; plate thickness .002 m authored')
 # parked lid indicates uncovered state without suggesting a source lid thickness.
 o=cyl(sample+'.aperture_lid',(x+.09,y-.065,.181),.031,.0015,'al');o['semantic_state']='parked';o['closed_pose_m']=[x,y,z+.0633]
 cyl(sample+'.lid_knob',(x+.09,y-.065,.187),.005,.01,'navy')
 # Thin thermocouple and heater are separate backside components. Position schematic only.
 cyl(sample+'.heater_visual',(x,y,ez-.00062),.022,.0005,'amber',source='Kapton heater backside role sourced; envelope and thickness authored')
 cyl(sample+'.temperature_bead',(x,y,ez-.00085),.001,.001,'gold',N=24,source='Rear-near-center role sourced; bead size/installation coordinate authored')
 path(sample+'.sensor_lead',[(x,y,ez-.001),(x+.033,y-.022,ez-.001),(x+.077,y-.068,.183),(x+.12,y-.10,.178)],.00065,'gold')
 for j in range(4):
  path(sample+f'.heater_lead.{j}',[(x+.007*(j-1.5),y,ez-.0015),(x+.048,y+.03+j*.004,.181),(x+.118,y+.045+j*.006,.178)],.0006,'orange' if j<2 else 'navy')
 # Authored straight demonstration carriage, deliberately not the historical track.
 for xx in [x-.13,x+.13]:
  rod(sample+'.reflector_post',(xx,y+.075,.19),(xx,y+.075,ez+.162),.0055)
  cyl(sample+'.post_foot',(xx,y+.075,.19),.012,.016,'navy')
 box(sample+'.track_placeholder',(x,y+.075,ez+.15),(.278,.018,.0015),'al',0,source='Track thickness 1.5 mm sourced; straight path authored placeholder, site/date path unknown')
 # reflector held at authored display datum; actual target separation remains null.
 carriage=box(sample+'.reflector_carriage',(x,y+.075,ez+.155),(.042,.03,.010),'navy');carriage['semantic_state']='center';carriage['track_qualified']=False
 rod(sample+'.reflector_arm',(x,y+.075,ez+.151),(x,y,ez+.151),.0025,'steel')
 o=cyl(sample+'.reflector_disk',(x,y,ez+.150),.03,.0015,'al',source='SI diameter .06 m; disk thickness authored; DISPLAY OFFSET .150 m, target height unresolved')
 o['physical_target_height_m']='UNKNOWN';o['display_height_m']=.15
 label(sample+'.nameplate','SOLAR '+sample.upper()+'  /  '+('W01' if sample=='white' else 'B01'),(x,y-.145,.192),.255,.029,.012)
 # Conflict guides on left upright; illustrative source alternatives, no resolved working height.
 for dz,tag in [(.10,'100'),(.15,'150')]:
  box(sample+'.height_tick.'+tag,(x-.135,y+.065,ez+dz),(.02,.002,.0015),'orange',0)
 text(sample+'.height_warning','100 / 150 mm  HOLD',(x-.142,y+.064,ez+.178),.009,'orange')
 label(sample+'.track_warning','TRACK PATH: AUTHORED DISPLAY',(x,y+.068,ez+.185),.25,.023,.0075,'white')

# General-purpose fixture system: original new geometry, no compatibility inherited from AFM.
root('cooling.handling_fixture','Reusable carrier, clamp and dock',('STOCK','MOVE','LAYOUT','FILM','UNMOUNT','ARCHIVE'),(),kind='authored_fixture_dimensions')
X=-.48;Y=-.275
box('dock.base',(X,Y,.157),(.43,.235,.018),'navy',.007)
box('dock.seating_pad',(X,Y,.170),(.325,.165,.008),'rubber',.003)
for xx in [X-.16,X+.16]:
 box('dock.alignment_key',(xx,Y,.184),(.014,.13,.028),'gold',.001)
box('carrier.tray',(X,Y,.184),(.302,.155,.012),'ivory',.004)
for xx in [X-.18,X+.18]:
 box('carrier.handle_bridge',(xx,Y,.199),(.023,.08,.018),'teal',.006)
 for yy in [Y-.037,Y+.037]:rod('carrier.handle_post',(xx,yy,.185),(xx,yy,.201),.004,'steel')
# captive clamp levers, closed state
for i,xx in enumerate([X-.136,X+.136]):
 o=box(f'clamp.{i}.lever',(xx,Y-.04,.201),(.046,.018,.008),'navy',.003);o['closed_rotation_rad']=0.;o['open_rotation_rad']=math.pi/2;o['semantic_state']='closed'
 cyl(f'clamp.{i}.pivot',(xx-.018,Y-.04,.201),.006,.012,'steel')
# separate retained ring and two membranes, exploded in Z for inspection
ann('handling.film_frame',(X,Y,.224),.0535,.0635,.0064,'al',source='SI Note 2 ring dimensions; staging pose authored')
for k,zv in [('lower',.207),('upper',.243)]:
 o=cyl('handling.film.'+k,(X,Y,zv),.062,.0008,'pe',source='Source target thickness 16 um; inspection display thickness .8 mm (50x only thickness)')
 o['component_identity']='handling.pe.'+k+'.rev1';o['physical_target_thickness_m']=.000016;o['display_thickness_scale']=50.
 # edge tab is authored view/identity accent, not part of physical film
 box('handling.film.'+k+'.display_tab',(X+.070,Y,zv),(.014,.017,.001),'teal',.001)
# Authored torn-film inspection variant, hidden in canonical scene and baseline GLBs.
# A missing wedge conveys a visible defect, not a deformation or fracture simulation.
verts=[]
for zt in [.2066,.2074]:
 verts.append((X,Y,zt))
 for i in range(64):
  a=math.radians(28)+(math.tau-math.radians(28))*i/63
  verts.append((X+.062*math.cos(a),Y+.062*math.sin(a),zt))
faces=[]
for i in range(1,64):faces.extend([(0,i+1,i),(65,65+i,65+i+1),(i,i+1,65+i+1,65+i)])
faces.extend([(0,1,66,65),(0,65,129,64)])
mesh=bpy.data.meshes.new('torn_film.mesh');mesh.from_pydata(verts,[],faces);mesh.update()
o=bpy.data.objects.new('handling.film.lower.torn_variant',mesh);sc.collection.objects.link(o);finish(o,'handling.film.lower.torn_variant','pe','Authored visible damage; display thickness 50x; no fracture physics')
o.hide_render=True;o.hide_viewport=True;o['state_variant']='torn_demo';o['component_identity']='handling.pe.lower.rev1'
label('dock.nameplate','CARRIER  /  DOCKED  /  CLAMPS CLOSED',(X,Y-.125,.162),.405,.028,.010)
label('handling.caption','16 um FILMS / 50x THICKNESS DISPLAY',(X,Y-.125,.207),.405,.026,.010)
# real-size spare black emitter underside on inspection support, heating and TC visible on top only as flipped pose.
root('cooling.backside_inspection','Emitter backside inspection coupon',('TC_ATTACH','HEATER_ATTACH','MAP_ATTACH'),('E_CAL','E_POWER','E_MAP'),kind='source_emitter_authored_probe_heater_envelopes')
X=-.09;Y=-.30
cyl('backside.support',(X,Y,.159),.068,.023,'navy')
cyl('backside.emitter_copper',(X,Y,.174),.025,.0005,'cu',source='SI copper diameter .05 m / thickness .0005 m; flipped inspection pose')
cyl('backside.heater',(X,Y,.175),.022,.0006,'amber',source='Authored visual heater envelope; real dimensions not asserted')
# meander is visual trace, not a heater-resistance reconstruction
for i in range(7):rod('backside.heater_trace',(X-.015,Y-.015+i*.005,.1755),(X+.015,Y-.015+i*.005,.1755),.0004,'gold')
cyl('backside.thermocouple_bead',(X,Y,.1765),.0015,.0015,'gold',N=24)
path('backside.tc_lead',[(X,Y,.177),(X+.021,Y-.018,.182),(X+.06,Y-.025,.169)],.0007,'gold')
label('backside.label','REAR SENSOR / HEATER',(X,Y-.072,.169),.175,.029,.009)
# Six extra map sensors kept in rack, not assigned invented source coordinates.
box('map_probe_rack',(X,Y+.097,.165),(.18,.043,.032),'ivory',.004)
for i in range(6):
 xx=X-.065+i*.026
 cyl('map_probe.'+str(i+1),(xx,Y+.096,.194),.001,.024,'gold',N=16)
 text('map_probe.label.'+str(i+1),str(i+1),(xx-.003,Y+.073,.184),.007,'navy')
label('map_probe.warning','6 PROBES / COORDINATES HOLD',(X,Y+.075,.222),.205,.018,.0064,'white')

# Readout and source/sense front panel. Ports visible; no electrical connectivity implied.
root('cooling.logger_power','Protected logger and isolated power console',('SYNC','STAG_LOG','POWER_CHECK','PID_CONFIG','HEATER_OFF','STOP_SAFE'),('E_ENV','E_POWER'),kind='authored_equipment_envelopes')
X=.38;Y=-.285
box('console.base',(X,Y,.177),(.50,.255,.06),'navy',.008)
box('logger.housing',(X-.10,Y+.018,.247),(.23,.19,.083),'al',.009)
box('logger.display',(X-.10,Y-.080,.257),(.175,.003,.037),'screen',.001)
text('logger.readback','LOGGER: IDLE',(X-.173,Y-.083,.254),.010,'white')
for i,(s,m) in enumerate([('ARM','teal'),('STOP','orange')]):
 xx=X-.154+i*.10
 b=box('control.'+s.lower(),(xx,Y-.083,.220),(.065,.008,.019),m,.003);b['semantic_event']='arm_logger' if i==0 else 'stop_logger'
 text('control.'+s+'.label',s,(xx-.020,Y-.089,.217),.009,'white')
box('sourcemeter.housing',(X+.14,Y+.018,.245),(.22,.19,.08),'ivory',.009)
box('sourcemeter.display',(X+.14,Y-.080,.264),(.17,.003,.03),'screen',.001)
text('sourcemeter.readback','OUTPUT: ISOLATED',(X+.065,Y-.083,.260),.0084,'white')
for i,s in enumerate(['F+','S+','S-','F-']):
 xx=X+.079+i*.04
 cyl('port.'+s,(xx,Y-.086,.224),.007,.012,'orange' if i in [0,3] else 'navy',N=32,axis='Y')
 text('port.'+s+'.label',s,(xx-.007,Y-.089,.204),.0068,'navy')
label('console.caption','STATE DEMO ONLY / NO ACQUISITION OR OUTPUT',(X,Y-.134,.171),.476,.026,.0086)
# Cable bundles terminate in parked connector sockets, not simulated wiring.
for i in range(2):
 path('logger.parked_cable.'+str(i),[(X-.19,Y+.06,.225),(X-.24,Y+.12,.166),(X-.10+i*.045,Y+.16,.161)],.0014,'rubber')
 cyl('logger.parked_connector.'+str(i),(X-.10+i*.045,Y+.16,.161),.004,.015,'steel',axis='Y')

# Optical characterization station. Sphere and variable-angle fixture share a display bench,
# but configuration selectors cannot imply same calibration or simultaneous real acquisition.
root('cooling.optical_bench','Optical sphere and angle fixture',('OPT_REFERENCE','OPT_MOUNT','OPT_SCAN','ANGLE_MOUNT','ANGLE_SCAN','OPT_UNLOAD'),('E_OPT','E_ANGLE'),kind='authored_instrument_not_vendor_CAD')
X=.43;Y=.17
box('optical.base',(X,Y,.174),(.52,.43,.043),'navy',.012)
box('optical.housing',(X+.075,Y+.035,.29),(.29,.29,.19),'ivory',.016)
# integrating-sphere silhouette with visible circular sample port
bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=.070,location=(X+.035,Y-.098,.291));finish(bpy.context.object,'optical.sphere_visual','ivory')
for p in bpy.context.object.data.polygons:p.use_smooth=True
cyl('optical.port_ring',(X+.035,Y-.161,.291),.031,.026,'navy',axis='Y')
cyl('optical.port_dark',(X+.035,Y-.176,.291),.023,.001,'black',axis='Y')
box('optical.reference_tray',(X-.146,Y-.049,.225),(.10,.10,.012),'steel',.004)
cyl('optical.reference_disk',(X-.146,Y-.049,.234),.03,.006,'white',source='Reference role sourced; material and size authored / not a certified standard')
# rotation fixture at front-left; remains unmounted, physical sample identity required to transition
cyl('optical.angle_base',(X-.147,Y+.100,.213),.054,.031,'steel')
ann('optical.angle_scale',(X-.147,Y+.100,.231),.044,.055,.002,'gold')
for i in range(12):
 a=i*math.pi/6
 box('optical.angle_tick',(X-.147+.049*math.cos(a),Y+.100+.049*math.sin(a),.233),(.002,.002,.001),'navy',0)
box('optical.angle_holder',(X-.147,Y+.100,.254),(.055,.060,.036),'navy',.003)
box('optical.angle_jaw',(X-.147,Y+.100,.275),(.06,.015,.006),'teal',.002)
label('optical.title','OPTICAL CHARACTERIZATION',(X,Y-.224,.183),.45,.032,.012)
label('optical.config','CONFIG: UVVIS / FTIR / ANGLE  [UNQUALIFIED]',(X+.09,Y-.114,.377),.30,.022,.0067)
text('optical.note','REFERENCE + SAMPLE PORT', (X-.02,Y-.185,.334),.0075,'navy')
# Authored local axes at the sample mount.
for d,col,s in [((.024,0,0),'orange','X'),((0,.024,0),'teal','Y'),((0,0,.024),'gold','Z')]:
 p=(X-.147,Y+.10,.28);rod('optical.local_axis.'+s,p,tuple(p[i]+d[i] for i in range(3)),.0007,col)

# Scale and limitations plate is physically in the scene, legible in detail view.
root('cooling.scale_reference','Metric ruler and source-boundary plaque',(),(),kind='authored_reference')
box('ruler.body',(-.52,-.446,.153),(.205,.024,.004),'ivory',.002)
for i in range(21):box('ruler.tick.'+str(i),(-.62+i*.01,-.448,.1555),(.00065,.017 if i%5==0 else .009,.0006),'navy',0)
text('ruler.label','0         50        100       150       200 mm',(-.620,-.432,.156),.0065,'navy',True)
box('boundary.card',(.37,-.451,.158),(.66,.032,.018),'navy',.003)
text('boundary.text','HEIGHT: 100 / 150 mm UNRESOLVED  |  NO THERMAL MODEL',(.054,-.470,.157),.010,'white')

CUR=None
light('Light.key',(-1.4,-1.4,2.5),360,1.8)
light('Light.fill',(1.7,-.4,1.6),230,1.5)
light('Light.rim',(.2,1.5,2.0),380,1.3)
CAMS={
 'overview':camera('CAM.overview',(1.35,-2.35,1.9),(-.02,.035,.22),1.98),
 'sample_handling':camera('CAM.sample_handling',(-.80,-1.35,1.14),(-.31,-.25,.207),.91),
 'equipment_closeup':camera('CAM.equipment_closeup',(1.40,-1.36,1.18),(.37,-.018,.262),1.03)}
sc.camera=CAMS['overview']
# Inventory exported before temporary conversion. The root IDs are counted once only.
bpy.context.view_layer.update()
assets=[]
for aid,r in ROOTS.items():
 parts=[]
 for o in r.children:
  q=o.rotation_euler.to_quaternion()
  parts.append({'part_id':o.name,'type':o.type,'dimensions_m':[round(float(x),10) for x in o.dimensions], 'translation_m':list(o.location),'rotation_quaternion_xyzw':[q.x,q.y,q.z,q.w], 'scale':list(o.scale),'dimension_status':o.get('dimension_status'),'properties':{k:(o[k].to_list() if hasattr(o[k], 'to_list') else o[k]) for k in o.keys() if k!='_RNA_UI'}})
 assets.append({'asset_id':aid,'instance_id':aid+'.01','asset_version':'1.0.0','label':r['label'],'operation_ids':r['operation_ids'].split(',') if r['operation_ids'] else [],'source_evidence_ids':r['source_evidence'].split(',') if r['source_evidence'] else [],'dimension_provenance':r['dimension_provenance'],'parts':parts})
(P/'asset_inventory.json').write_text(json.dumps({'schema':'cooling_original_scene.v1','units':'metres','assets':assets},indent=2))
(P/'materials'/'materials.json').write_text(json.dumps([{'id':m.name,'base_color':list(m.diffuse_color),'appearance_only':True,'measured_optical_properties':False} for m in M.values()],indent=2))
sc['package_id']='cooling_scene_assets_v1';sc['physical_execution']=False;sc['height_conflict_resolved']=False;sc['semantic_demo_mode']='static_only'
# Save native sources compressed and no backup copy.
sc.render.filepath=str(P/'evidence'/'overview.png');bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(P/'geometry'/'cooling_operations_lab.blend'),compress=True)
# Portable GLB working copy; native source retains text, curves and modifiers.
for o in list(sc.objects):
 if o.type in ['FONT','CURVE']:
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
for o in sc.objects:o.select_set(o.type in ['MESH','EMPTY'] and not o.name.startswith('studio.') and not o.hide_render)
bpy.ops.export_scene.gltf(filepath=str(P/'geometry'/'cooling_operations_lab.glb'),export_format='GLB',use_selection=True,export_apply=True,export_extras=True)
for o in sc.objects:o.select_set(False)
for aid in ['cooling.handling_fixture','cooling.backside_inspection']:
 ROOTS[aid].select_set(True)
 for o in ROOTS[aid].children:o.select_set(not o.hide_render)
bpy.ops.export_scene.gltf(filepath=str(P/'geometry'/'cooling_handling_module.glb'),export_format='GLB',use_selection=True,export_apply=True,export_extras=True)
views=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(CAMS)
if views==['build-only']:views=[]
receipts=[]
for v in views:
 sc.camera=CAMS[v];sc.render.filepath=str(P/'evidence'/f'{v}.png');a=time.time();bpy.ops.render.render(write_still=True);receipts.append({'view':v,'engine':'CYCLES','device':'CPU','samples':sc.cycles.samples,'seconds':round(time.time()-a,2),'resolution':[sc.render.resolution_x,sc.render.resolution_y],'path':f'evidence/{v}.png','actual_render':True})
if receipts:(P/'review'/'render_receipt.json').write_text(json.dumps({'blender':bpy.app.version_string,'renders':receipts,'total_seconds':round(time.time()-START,2),'pixel_review':'pending'},indent=2))
print('COOLING_SCENE_BUILD_COMPLETE')
