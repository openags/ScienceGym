"""Original static ScienceGym scene. No controller, source CAD, or scientific solver."""
import bpy, math, json, os, sys
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1.0
scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=48
scene.cycles.use_denoising=False
scene.render.resolution_x=1680; scene.render.resolution_y=1080; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
scene.world=bpy.data.worlds.new('World'); scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(0.11,.15,.21,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
scene.view_settings.view_transform='AgX'
scene['classification']='ORIGINAL_STATIC_REVIEW_SCENE';scene['physical_execution_enabled']=False
scene['scientific_physics_implemented']=False;scene['geometry_qualified']=False
scene['default_state']='HOLD_QUALIFICATION';scene['paper_doi']='10.1038/s41467-022-34207-7'
scene['source_artwork_copied']=False;scene['render_device']='CPU'
materials={}
def mat(name,color,metal=0,rough=.45,alpha=1):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,alpha);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,alpha);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;p.inputs['Alpha'].default_value=alpha
 if alpha<1: p.inputs['Transmission Weight'].default_value=.6; p.inputs['IOR'].default_value=1.45
 materials[name]=m;return m
navy=mat('Midnight enamel',(.025,.055,.085),.2)
white=mat('Porcelain white',(.81,.86,.88),.1)
metal=mat('Brushed aluminium',(.33,.4,.45),.75,.28)
black=mat('Charcoal rubber',(.015,.023,.028),.0,.65)
teal=mat('Design M1 teal',(.015,.55,.52),.2)
blue=mat('Design M2 blue',(.05,.3,.8),.2)
orange=mat('Design M3 amber',(.95,.38,.045),.2)
yellow=mat('Hold yellow',(.95,.64,.12),.15)
red=mat('Quarantine coral',(.85,.15,.13),.1)
purple=mat('Numerical review violet',(.39,.19,.68),.1)
textmat=mat('Label ivory',(.94,.96,.98),.0,.6)
muted=mat('Secondary type',(.55,.68,.73),.0,.7)
glass=mat('Closed tinted shield',(.12,.34,.40),.0,.13,.2)
floor=mat('Slate stage',(.075,.115,.15),.05,.7)
lightmat=mat('Warm trim',(.75,.84,.82),.3,.35)
current='SCENE';collections={};inventory=[]
def group(name):
 global current
 current=name
 if name not in collections:
  c=bpy.data.collections.new(name);scene.collection.children.link(c);collections[name]=c
 return collections[name]
def reg(obj,name,role='visual'):
 obj.name=name
 for c in list(obj.users_collection):c.objects.unlink(obj)
 collections[current].objects.link(obj)
 obj['asset_family']=current;obj['role']=role;obj['qualified']=False;obj['physical_actuation_enabled']=False
 obj['dimension_class']='illustrative_unqualified'
 return obj

def box(name,p,s,m,bevel=.025):
 bpy.ops.mesh.primitive_cube_add(size=1, location=p);o=reg(bpy.context.object,name);o.dimensions=s;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if bevel:
  mod=o.modifiers.new('Authored edge radii','BEVEL');mod.width=bevel;mod.segments=2
  mod=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o

def cyl(name,p,r,d,m,axis=None):
 bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=r, depth=d,location=p);o=reg(bpy.context.object,name);o.data.materials.append(m)
 if axis:o.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
 bevel=o.modifiers.new('Soft metal edges','BEVEL');bevel.width=min(.014,r*.18);bevel.segments=2;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return o

def link(name,a,b,r,m):
 a,b=Vector(a),Vector(b);return cyl(name,(a+b)/2,r,(b-a).length,m,b-a)
def sphere(name,p,r,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=10,radius=r,location=p);o=reg(bpy.context.object,name);o.data.materials.append(m);return o

def text(name,body,p,size=.07,m=textmat,rot=(math.pi/2,0,0),align='LEFT'):
 cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.extrude=0;cu.bevel_depth=0;cu.resolution_u=2;cu.align_x=align;cu.space_line=1.15
 o=bpy.data.objects.new(name,cu);collections[current].objects.link(o);o.location=p;o.rotation_euler=rot;cu.materials.append(m);o['asset_family']=current;o['role']='annotation';o['qualified']=False;return o

def plate(name,title,p,w=1.15,sub=None,color=teal):
 x,y,z=p;box(name+'_plate',(x,y,z),(w,.035,.25),navy,.014);box(name+'_stripe',(x-w/2+.025,y-.024,z),(.035,.012,.2),color,.002)
 text(name+'_title',title,(x-w/2+.07,y-.025,z+.025),.063)
 if sub:text(name+'_subtitle',sub,(x-w/2+.07,y-.026,z-.065),.035,muted)

def bench(name,x,y,w=1.45,d=.92,h=.79):
 box(name+'_top',(x,y,h),(w,d,.09),white,.035)
 for dx in (-w*.4,w*.4):
  for dy in (-d*.35,d*.35):box(name+'_leg',(x+dx,y+dy,h/2),(.075,.075,h),metal,.013)
 box(name+'_lower',(x,y,.24),(w*.86,d*.77,.06),navy,.02)

def boundary(name,x,y,w,d,bottom,top,transparent=False):
 # All panels retained: closed on four sides and roof, static geometry only.
 m=glass if transparent else navy
 z=(top+bottom)/2;h=top-bottom
 box(name+'_rear',(x,y+d/2,z),(w,.035,h),m,.004)
 box(name+'_left',(x-w/2,y,z),(.035,d,h),m,.004)
 box(name+'_right',(x+w/2,y,z),(.035,d,h),m,.004)
 box(name+'_front',(x,y-d/2,z),(w,.035,h),m,.004)
 box(name+'_roof',(x,y,top),(w,d,.04),white,.014)
 for dx in(-w/2,w/2):
  for dy in(-d/2,d/2):box(name+'_frame',(x+dx,y+dy,z),(.042,.042,h+.04),metal,.008)
 box(name+'_base',(x,y,bottom),(w,d,.05),metal,.012)

# Base and title.
group('SCENE')
box('Foundation',(0,.1,-.12),(8,6.4,.24),floor,.14)
box('Perimeter trim',(0,.1,-.255),(8.08,6.48,.045),metal,.035)
text('Header','SCATTERING  /  EVIDENCE WORKCELL',(-3.63,-2.82,.027),.23,textmat,rot=(0,0,0))
text('Footer','ORIGINAL STATIC REVIEW  |  ACTUATION DISABLED  |  NO EXPERIMENT EXECUTED',(-3.6,-3.08,.028),.094,muted,rot=(0,0,0))
# floor guide strips, decorative not trajectories
for y in(-.55,-.43):box('Station zoning stripe',(0,y,.012),(6.9,.026,.015),muted,.004)
text('Zone front','SUPPORTED CUSTODY',(-3.42,-.84,.019),.095,muted,rot=(0,0,0))
text('Zone back','CLOSED SERVICES / REVIEW ONLY',(-3.42,.02,.019),.095,muted,rot=(0,0,0))
# AS01 plan console
group('AS01');bench('Review console',-2.8,-1.63,1.3,.85)
box('Review display',(-2.8,-1.44,1.2),(1.04,.12,.66),navy,.03)
box('Review screen',(-2.8,-1.508,1.2),(.94,.016,.54),black,.007)
text('Review headline','PLAN + RECEIPTS',(-3.22,-1.52,1.38),.071)
text('Review body','R01 / R02 / R07 / R10\nSOURCE REVIEW ACCEPTED\nPHYSICAL BINDING: HOLD',(-3.22,-1.522,1.24),.045,muted)
box('Plan receipt slot',(-3.05,-1.9,.862),(.39,.22,.025),teal,.012)
box('Receipt record slot',(-2.55,-1.9,.862),(.39,.22,.025),yellow,.012)
text('Plan tablet label','PLAN',(-3.2,-1.9,.88),.049,textmat,rot=(0,0,0))
text('Receipt tablet label','RECEIPT',(-2.73,-1.9,.88),.038,black,rot=(0,0,0))
plate('AS01 sign','01 / REVIEW',(-2.8,-2.08,.64),1.25,'NONPHYSICAL EVIDENCE')
# AS02 carriers and AS03 stylized profiles
group('AS02');bench('Carrier staging',-1.02,-1.61,1.6,.85)
colors=[teal,blue,orange];carrier_positions={};spec_positions={}
for i,(design,c) in enumerate(zip(['M1','M2','M3'],colors)):
 x=-1.51+i*.49;y=-1.6;carrier_positions[design]=(x,y,.85)
 box(design+'_carrier_base',(x,y,.865),(.445,.3,.075),navy,.02)
 box(design+'_support_pad',(x,y,.912),(.39,.18,.025),c,.012)
 for dy in(-.129,.129):box(design+'_carrier_rim',(x,y+dy,.955),(.445,.025,.12),metal,.007)
 for dx in(-.20,.20):box(design+'_carrier_rail',(x+dx,y,.958),(.025,.27,.12),white,.007)
 # supported pickup tab is illustrative only; carrier stays parked
 box(design+'_grip_tab',(x,y+.18,.91),(.14,.07,.045),c,.01)
 text(design+'_identity',design,(x-.15,y-.152,.938),.063,navy)
 text(design+'_family','FAMILY',(x-.15,y-.152,.894),.027,navy)
 group('AS03')
 if design=='M1':dims=(.3108,.0808,.0444)
 elif design=='M2':dims=(.30,.09,.05)
 else:dims=(.205,.084,.048)
 sx,sy,sz=dims;z=.9245+sz/2
 base=box(design+'_groove_illustration',(x,y,z-sz*.25),(sx,sy,sz*.5),c,.004)
 base['design_id']=design;base['material_family']='GROOVE_'+design;base['source_exact_geometry']=False;base['manufacturing_model']=False
 base['profile_definition']='Original symbolic stepped-ridge form; no table-driven CAD'
 base['source_reported_cell_count']={'M1':30,'M2':30,'M3':20}[design]
 if design=='M1':base['source_envelope_mm']=[77.7,20.2,11.1];base['illustration_scale']=4.0;base['dimension_class']='source_envelope_at_authored_4x_display_scale_only'
 else:base['source_envelope_known']=False;base['dimension_class']='illustrative_envelope_not_transferred_from_M1'
 n=9 if design!='M3' else 6
 for j in range(n):
  f=(j+1)/(n+1);height=sz*(.36+.12*(math.sin((j+1)*1.4) if design!='M2' else math.cos(abs(j-(n-1)/2))))
  if j==0:height=sz*.5
  box(design+'_symbolic_ridge_%02d'%j,(x-sx/2+(j+.5)*sx/n,y,.9245+sz*.5+height/2),(sx/n*.45,sy,height),c,.002)
 spec_positions[design]=(x,y,.9615)
 # original orientation pointer, not an executable rotation
 box(design+'_orientation_label',(x+.14,y+.072,.9285),(.07,.015,.009),yellow,.002)
 group('AS02')
plate('AS02 sign','02 / DESIGN CARRIERS',(-1.02,-2.06,.64),1.53,'M1 / M2 / M3  |  SUPPORTED')
# AS04 closed fabrication enclosure
group('AS04');x,y=-2.8,.9
boundary('Fabrication service',x,y,1.35,1.1,.08,1.86,False)
box('Fabrication grounded plinth',(x,y,.0275),(1.35,1.1,.055),metal,.01)
box('Fabrication closed door',(x,y-.563,1.03),(1.13,.03,1.37),white,.024)
box('Fabrication status panel',(x,y-.586,1.39),(.96,.012,.48),navy,.013)
text('Fabrication title','FAB + QA',(x-.40,y-.602,1.52),.115)
text('Fabrication scope','CLOSED SERVICE\nQUALIFICATION HOLD',(x-.40,y-.603,1.34),.056,yellow)
box('Output receipt port',(x,y-.625,.82),(.54,.12,.105),black,.012)
text('Output port label','RECEIPT ONLY',(x-.25,y-.69,.79),.041)
plate('AS04 sign','04 / FABRICATION',(x,y-.595,.32),1.18,'NO PROCESS INTERNALS',yellow)
# AS05 array characterization, nonfunctional sealed forms
group('AS05');x,y=-1.07,.89;bench('Array table',x,y,1.43,1.10)
boundary('Array enclosure',x,y,1.32,.99,.86,1.94,True)
# solid sealed flat and curved shapes, no inferred transducer count
box('Flat array support',(x-.30,y,.8925),(.35,.30,.015),metal,.004)
box('Curved array support',(x+.28,y,.98),(.18,.29,.19),metal,.012)
box('Flat array sealed proxy',(x-.30,y,.98),(.40,.34,.16),teal,.04)
text('Flat array ID','FLAT',(x-.455,y-.179,.985),.05)
# curved solid hood is independently authored as shell from 9 face segments, not transducer count
for j in range(9):
 angle=(j-4)*.13;xx=x+.28+math.sin(angle)*.23;zz=1.12+(.23-math.cos(angle)*.23)
 o=box('Curved shell segment_%02d'%j,(xx,y,zz),(.042,.35,.09),blue,.013);o.rotation_euler[1]=-angle
text('Array closed review','ARRAY RECORDS',(x-.55,y-.519,1.67),.083)
text('Array boundary','NO DRIVE / NO FIELD',(x-.55,y-.520,1.55),.047,yellow)
plate('AS05 sign','05 / ARRAY REVIEW',(x,y-.596,.65),1.35,'CALIBRATION EPOCH: UNBOUND',yellow)
# AS06/AS07 guarded supported pendulum with stylized optical widgets
group('AS06');x,y=.65,.9;bench('Metrology table',x,y,1.53,1.20)
boundary('Pendulum shield',x,y,1.43,1.1,.86,2.25,True)
box('Pendulum upper support',(x,y,2.14),(.86,.17,.09),metal,.013)
box('Pendulum roof bracket',(x,y,2.2075),(.18,.17,.045),metal,.006)
link('Illustrative suspension',(x,y,2.1),(x,y,1.49),.007,metal)
link('Illustrative pendulum rod',(x-.50,y,1.49),(x+.47,y,1.49),.016,metal)
cyl('Counterweight',(x-.42,y,1.49),.075,.12,black,(0,1,0))
box('Specimen mount placeholder',(x+.4,y,1.49),(.19,.13,.065),white,.012)
box('Retained support lock',(x+.4,y,1.16),(.14,.19,.55),yellow,.012)
box('Supported service cradle',(x+.4,y,1.455),(.24,.22,.045),teal,.01)
text('Pendulum support label','SUPPORTED',(x-.58,y-.569,2.025),.081,yellow)
text('Pendulum lease label','LEASE RETAINED',(x-.58,y-.57,1.907),.057)
plate('AS06 sign','06 / TORSION HOLD',(x,y-.656,.65),1.39,'NO DYNAMICS / NO FORCE MODEL',yellow)
group('AS07')
box('Mirror placeholder',(x,y-.028,1.51),(.13,.027,.17),metal,.007)
box('Screen grounded pedestal',(x-.46,y+.31,1.0025),(.08,.09,.235),metal,.008)
box('Tracking camera grounded foot',(x-.47,y-.30,.9075),(.17,.18,.045),metal,.008)
box('Screen reference proxy',(x-.46,y+.31,1.30),(.33,.025,.36),white,.012)
text('Screen blank','NO DATA',(x-.60,y+.29,1.29),.047,navy)
box('Tracking camera proxy',(x-.47,y-.30,1.01),(.19,.20,.16),navy,.02)
cyl('Covered camera aperture',(x-.47,y-.403,1.01),.051,.02,black,(0,1,0))
link('Covered optical route',(x-.47,y-.20,1.02),(x-.47,y+.27,1.02),.028,black)
text('Optics label','07 / CLOSED OPTICS',(x-.59,y-.57,1.78),.068)
text('Optics no beam','NO LIVE BEAM',(x-.59,y-.571,1.67),.049,yellow)
# AS08 source positioning
group('AS08');x,y=2.34,.9;bench('Motion table',x,y,1.42,1.1)
boundary('Motion boundary',x,y,1.29,.99,.86,1.94,True)
box('Positioning rail support',(x,y,.915),(.86,.26,.06),navy,.008)
box('Positioning rail proxy',(x,y,1.0),(.88,.28,.11),metal,.025)
box('Observed pose proxy',(x-.17,y,1.17),(.30,.27,.26),orange,.025)
box('Independent pose sensor proxy',(x+.37,y,1.19),(.12,.17,.33),navy,.018)
# static envelope without animated trajectory or operational limits
text('Motion headline','POSE READBACK',(x-.53,y-.517,1.68),.084)
text('Motion field distinction','ANGLE != OFFSET\nSIGN MAP: HOLD',(x-.53,y-.519,1.54),.058,yellow)
plate('AS08 sign','08 / MOTION HOLD',(x,y-.596,.65),1.35,'NO TRAJECTORY / NO CONTROLLER',yellow)
# AS09 occupied safe-hold support
group('AS09');x,y=.7,-1.67;bench('Safe hold',x,y,1.35,.84)
box('Hold cradle',(x,y,.89),(.91,.46,.15),navy,.025)
box('Hold occupied neutral carrier',(x,y,.997),(.56,.30,.09),yellow,.02)
box('Hold locking support left',(x-.35,y,1.035),(.08,.47,.19),metal,.01)
box('Hold locking support right',(x+.35,y,1.035),(.08,.47,.19),metal,.01)
box('Hold evidence panel',(x,y+.26,1.21),(.99,.07,.30),navy,.012)
text('Hold condition','ILLUSTRATIVE OCCUPANCY',(x-.44,y+.217,1.28),.049)
text('Hold independent state','SAFE STATE: UNKNOWN',(x-.44,y+.216,1.18),.055,yellow)
plate('AS09 sign','09 / SAFE HOLD',(x,y-.46,.64),1.27,'LEASE RETAINED  |  NO RELEASE',yellow)
# AS10 return and quarantine
group('AS10');x,y=2.37,-1.69
box('Custody cabinet body',(x,y,.595),(1.37,.83,1.19),navy,.04)
for dx,color,title in[(-.34,teal,'RETURN'),(.34,red,'QUARANTINE')]:
 box(title+'_closed_door',(x+dx,y-.432,.68),(.62,.04,.94),white,.016)
 box(title+'_state_panel',(x+dx,y-.459,.79),(.55,.015,.30),color,.009)
 text(title+'_label',title,(x+dx-.245,y-.471,.84),.047,black)
 text(title+'_state','ACCEPTANCE\nUNBOUND',(x+dx-.245,y-.472,.755),.032,black)
 box(title+'_receipt_slot',(x+dx,y-.481,.49),(.36,.04,.055),black,.008)
plate('AS10 sign','10 / FINAL CUSTODY',(x,y-.472,.19),1.26,'NO AUTO DISPOSAL / NO CLEANING',yellow)
# AS11 evidence wall: data schemas without fabricated curves
group('AS11')
for x in(-1.68,1.62):
 box('Evidence wall support',(x,2.22,1.09),(.08,.15,2.18),metal,.015)
box('Evidence panel',(0,2.25,2.12),(5.7,.14,.95),navy,.028)
text('Evidence main','11 / EVIDENCE TYPES REMAIN DISTINCT',(-2.64,2.168,2.45),.123)
for x,title,subtitle,c in[(-1.86,'EXPERIMENTAL','B01-B05 | RAW RECORDS',teal),(0,'NUMERICAL SOURCE','A01-A04 | NOT EXECUTED',purple),(1.86,'AUTHORED TASK','GUARDED SEMANTICS ONLY',yellow)]:
 box(title+'_tile',(x,2.16,2.015),(1.68,.035,.52),c,.015)
 text(title+'_type',title,(x-.76,2.133,2.16),.068,textmat if c!=yellow else black)
 text(title+'_subtitle',subtitle,(x-.76,2.132,2.04),.042,textmat if c!=yellow else black)
 text(title+'_empty','NO OBSERVATIONS GENERATED',(x-.76,2.131,1.925),.035,textmat if c!=yellow else black)
# Static illustrative robot at custody interface.
group('ROBOT')
base=(-.70,-.45,.09);cyl('Robot dock',base,.31,.18,navy)
points=[(-.70,-.45,.21),(-.70,-.45,.65),(-.60,-.63,1.1),(-.90,-1.16,1.36),(-1.015,-1.40,1.15),(-1.02,-1.42,1.00)]
for i in range(len(points)-1):
 link('Robot link_%02d'%i,points[i],points[i+1],.080 if i<3 else .045,white)
 sphere('Robot joint_%02d'%i,points[i],.10 if i<3 else .06,teal)
box('Robot wrist',(points[-1][0],points[-1][1],1.01),(.13,.095,.12),navy,.015)
for dx in(-.088,.088):box('Illustrative parked gripper',(-1.02+dx,-1.42,.961),(.031,.095,.13),metal,.006)
text('Robot qualification','STATIC ROBOT / NO MOTION',(-.48,-.61,.15),.065,yellow,rot=(0,0,0))
# Exact anchor definitions. Empty axes preserve portable semantics and never qualify poses.
group('ANCHORS')
anchor_positions={
 'AS01.plan_slot':(-3.05,-1.9,.883),'AS01.receipt_slot':(-2.55,-1.9,.883),
 'AS04.service_output_receipt':(-2.8,.205,.82),
 'AS05.array_identity':(-1.07,.89,1.19),'AS05.service_state':(-1.07,.295,1.67),
 'AS06.support_lock':(1.05,.9,1.16),'AS06.mount_lease':(.65,.33,1.91),'AS06.containment':(.65,.9,1.56),
 'AS07.camera_stream':(.18,.6,1.01),'AS07.screen_reference':(.19,1.21,1.30),'AS07.calibration_epoch':(.65,.33,1.78),
 'AS08.source_pose_readback':(2.17,.9,1.17),'AS08.motion_safe':(2.34,.305,1.54),
 'AS09.safe_hold_occupancy':(.7,-1.67,.997),'AS09.access_release':(.7,-1.454,1.18),
 'AS10.return_acceptance':(2.03,-2.161,.755),'AS10.quarantine_acceptance':(2.71,-2.161,.755),
 'AS11.raw_evidence':(-1.86,2.13,2.04),'AS11.transform':(0,2.13,2.04),'AS11.analysis_record':(1.86,2.13,2.04)}
for design,p in carrier_positions.items():
 anchor_positions['AS02.'+design+'.carrier_acceptance']=p;anchor_positions['AS02.'+design+'.specimen_identity']=(p[0],p[1]-.152,.938)
 anchor_positions['AS03.'+design+'.supported_specimen_pose']=spec_positions[design];anchor_positions['AS03.'+design+'.orientation_reference']=(p[0]+.14,p[1]+.072,.9285)
for name,p in anchor_positions.items():
 o=bpy.data.objects.new(name,None);collections[current].objects.link(o);o.empty_display_type='PLAIN_AXES';o.empty_display_size=.065;o.location=p
 o['semantic_anchor']=True;o['qualified']=False;o['physical_actuation_enabled']=False;o['frame']='scene_world_illustrative';o['runtime_binding']='UNBOUND';o['anchor_id']=name
# Render setup, original studio lighting.
group('RENDER')
def area(name,p,power,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);collections[current].objects.link(o);o.location=p;o.rotation_euler=(Vector((0,.3,.7))-o.location).to_track_quat('-Z','Y').to_euler()
area('Key softbox',(1,-4,8),1900,6,(.86,.93,1.0));area('Fill softbox',(-5,-1,4),1350,5,(.63,.82,1));area('Rim softbox',(3,5,7),2200,4,(1,.79,.57))
def camera(name,p,target,scale):
 d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=scale;o=bpy.data.objects.new(name,d);collections[current].objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
cams=[camera('CAM_01_overview',(8,-11,9.0),(0,.05,.9),10.4),camera('CAM_02_preparation',(-4.2,-7,5.4),(-.85,-1.38,.90),4.7),camera('CAM_03_metrology',(5.6,-6,4.5),(.68,1.05,1.35),6.4)]
scene.camera=cams[0]
# Camera-facing 3D review caption, rendered in Cycles with the scene.
captionmat=mat('Caption emission',(.86,.93,.97),0,1)
cp=captionmat.node_tree.nodes['Principled BSDF'];cp.inputs['Emission Color'].default_value=(.86,.93,.97,1);cp.inputs['Emission Strength'].default_value=1
captionbacks=[];captions=[]
for i,cam in enumerate(cams):
 scale=cam.data.ortho_scale;hh=scale*1080/1680
 back=box('CAM_CAPTION_BACK_'+str(i),(0,0,0),(scale*.96,.21*(scale/10.4),.008),navy,.002)
 back.parent=cam;back.location=(0,-hh*.46,-.54);back.rotation_euler=(0,0,0);back.hide_render=i!=0
 t=text('CAM_CAPTION_'+str(i),'STATIC REVIEW ONLY  |  NO EXPERIMENT EXECUTED  |  PHYSICAL ACTUATION DISABLED',(0,0,0),scale*.0077,captionmat,rot=(0,0,0))
 t.parent=cam;t.location=(-scale*.463,-hh*.465,-.525);t.hide_render=i!=0
 captionbacks.append(back);captions.append(t)
bpy.context.view_layer.update()
# No external resources; built-in font and self-contained meshes/materials.
for o in scene.objects:
 if o.type in {'MESH','FONT'}:
  inventory.append({'name':o.name,'asset_family':o.get('asset_family'),'object_type':o.type,'role':o.get('role','visual'),'dimensions_m':[round(v,6) for v in o.dimensions],'location_m':[round(v,6) for v in o.location],'qualified':False})
manifest={
 'schema_version':'1.0','scene_id':'SCATTERING_STATIC_SCENE_V1','paper_doi':'10.1038/s41467-022-34207-7',
 'classification':'original_static_review_assets','physical_execution_enabled':False,'default_state':'HOLD_QUALIFICATION','scientific_physics_implemented':False,
 'source_exact_geometry':False,'source_artwork_copied':False,'illustrative_robot_only':True,'physical_robot_controller':False,
 'coordinate_system':{'units':'meters','handedness':'right','up_axis':'Z','laboratory_frame_mapping':None,'source_angle_to_offset_mapping':None,'status':'ILLUSTRATIVE_UNQUALIFIED'},
 'specimen_identity':{'M1':'GROOVE_M1','M2':'GROOVE_M2','M3':'GROOVE_M3','runtime_specimen_id':None,'runtime_carrier_id':None,'illustrated_family_count':3,'physical_specimen_count':None,'replicate_count':None},
 'source_dimension_boundaries':{'M1':{'source_envelope_mm':[77.7,20.2,11.1],'illustration_scale':4.0,'source_fact':'F04','profile':'independently authored symbolic grooves; not table-driven'},'M2':{'source_envelope_mm':None,'illustrative_envelope_m':[.30,.09,.05]},'M3':{'source_envelope_mm':None,'illustrative_envelope_m':[.205,.084,.048]},'all_other_geometry':'authored illustrative layout, no qualified dimensions'},
 'asset_families':[f'AS{i:02}' for i in range(1,12)],'operation_ids':[f'R{i:02}' for i in range(1,15)],
 'anchors':[{'id':n,'object_name':n,'position_m':list(p),'rotation_euler_rad':[0,0,0],'frame':'scene_world_illustrative','pose_qualified':False,'grasp_qualified':False,'collision_qualified':False,'physical_binding':None} for n,p in sorted(anchor_positions.items())],
 'objects':inventory,'render_settings':{'engine':'Cycles','device':'CPU','samples':48,'denoising':False,'resolution':[1680,1080],'color_management':'AgX','genuine_3d_render':True,'composited_source_artwork':False},
 'closed_services':['fabrication','acoustic_array','optical_tracking','source_positioning','mounting_and_containment'],
 'nonphysical_branches':['A01','A02','A03','A04'],'experimental_review_branches':['B01','B02','B03','B04','B05'],
 'no_embedded_scripts_or_drivers':True,'transportable_objects_supported':True}
(ROOT/'scene_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Compression is native from the first save, never an uncompressed intermediate.
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'scattering_review_scene.blend'),compress=True)
# Exclude render rig from interchange; convert text to mesh in the export copy only.
for o in scene.objects:o.select_set(False)
for o in list(scene.objects):
 if o.type=='FONT':
  o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');o.select_set(False)
for o in scene.objects:o.select_set(o.type not in {'LIGHT','CAMERA'} and o.get('asset_family')!='RENDER')
bpy.ops.export_scene.gltf(filepath=str(ROOT/'scattering_review_scene.glb'),export_format='GLB',use_selection=True,export_extras=True,export_animations=False,export_cameras=False,export_lights=False)
# Reopen the original editable compressed scene, then render with CPU only.
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'scattering_review_scene.blend'))
scene=bpy.context.scene;scene.cycles.device='CPU'
if '--no-render' not in sys.argv:
 for i,name in enumerate(['CAM_01_overview','CAM_02_preparation','CAM_03_metrology'],1):
  scene.camera=bpy.data.objects[name]
  for j in range(3):
   bpy.data.objects['CAM_CAPTION_'+str(j)].hide_render=j!=i-1;bpy.data.objects['CAM_CAPTION_BACK_'+str(j)].hide_render=j!=i-1
  scene.render.filepath=str(ROOT/(f'preview_0{i}_'+['overview','preparation','metrology'][i-1]+'.png'))
  bpy.ops.render.render(write_still=True)
print('SCENE_BUILD_COMPLETE')
