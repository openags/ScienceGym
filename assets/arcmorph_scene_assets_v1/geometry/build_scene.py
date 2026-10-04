"""Original Arc-Morph representative laboratory. Run with Blender --background --python.
Primitive equipment, explicit panel graphs and static state exemplars; no source CAD.
Units are metres. This is not a qualified folding model, simulator, or controller.
"""
import bpy, json, math, sys, hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
S=bpy.context.scene; S.name='ARC_MORPH_ORIGINAL_STATIC_LAB'
S.unit_settings.system='METRIC';S.unit_settings.scale_length=1
S.render.engine='CYCLES';S.cycles.device='CPU';S.cycles.samples=96;S.cycles.use_denoising=False;S.cycles.seed=41
S.render.resolution_x=1920;S.render.resolution_y=1280;S.render.resolution_percentage=100
S.render.image_settings.file_format='PNG';S.render.use_stamp=False
S.world=bpy.data.worlds.new('Soft neutral studio');S.world.use_nodes=True
S.world.node_tree.nodes['Background'].inputs[0].default_value=(.37,.45,.53,1)
S.world.node_tree.nodes['Background'].inputs[1].default_value=.45
S.view_settings.view_transform='AgX'; S.view_settings.exposure=-.8
CUR=None;ROOTS={};TARGETS={};CONTACTS=[];EXCLUSIONS=[];PROXIES=[];TOPO=[];STATE_OBJECTS={};M={}
def material(k,color,metal=0,rough=.45,trans=0):
 m=bpy.data.materials.new(k);m.diffuse_color=(*color,1);m.use_nodes=True;q=m.node_tree.nodes['Principled BSDF'];q.inputs['Base Color'].default_value=(*color,1);q.inputs['Metallic'].default_value=metal;q.inputs['Roughness'].default_value=rough;q.inputs['Transmission Weight'].default_value=trans;M[k]=m
for args in [('navy',(.025,.055,.080),.25),('teal',(.025,.34,.34),.3),('cream',(.76,.82,.80),.1),('metal',(.42,.52,.59),.75),('black',(.012,.016,.023),.1),('white',(.96,.98,.92)),('cyan',(.06,.64,.76),.12),('amber',(.97,.48,.06)),('coral',(.75,.18,.09)),('paper',(.81,.68,.43)),('paper2',(.57,.73,.59)),('paper3',(.78,.45,.37)),('paper4',(.53,.53,.78)),('polymer',(.040,.052,.065),.1),('guard',(.79,.91,.95),0,.15,.78),('floor',(.36,.43,.50),0,.85)]:material(*args)
def root(aid):
 global CUR
 CUR=bpy.data.objects.new('ASSET.'+aid,None);S.collection.objects.link(CUR);CUR.empty_display_size=.05;CUR['asset_id']=aid;CUR['physical_geometry_validated']=False;CUR['physical_execution_enabled']=False;CUR['geometry_basis']='original_authored';CUR['units']='m';ROOTS[aid]=CUR;TARGETS[aid]={};return CUR
def finish(o,n,m=None):
 o.name=n
 if CUR:o.parent=CUR
 if m:o.data.materials.append(M[m])
 o['geometry_basis']='original_authored';o['physical_geometry_validated']=False;o['physical_execution_enabled']=False;o['graspable']=False
 return o
def box(n,p,d,m='navy',bev=.004):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.dimensions=d;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(o,n,m)
 if bev:
  b=o.modifiers.new('Nominal edge rounding','BEVEL');b.width=min(bev,min(d)*.25);b.segments=3;o.modifiers.new('Face normals','WEIGHTED_NORMAL')
 return o
def cyl(n,p,r,h,m='metal',axis='Z',verts=32):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=h,location=p);o=bpy.context.object
 if axis=='Y':o.rotation_euler.x=math.pi/2
 if axis=='X':o.rotation_euler.y=math.pi/2
 finish(o,n,m)
 for f in o.data.polygons:f.use_smooth=True
 return o
def rod(n,a,b,r=.003,m='metal',verts=16):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,verts=verts);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def text(n,body,p,size=.023,m='white',flat=False):
 c=bpy.data.curves.new(n,'FONT');c.body=body;c.size=size;c.extrude=.00006;o=bpy.data.objects.new(n,c);S.collection.objects.link(o);o.location=p
 if not flat:o.rotation_euler=(math.pi/2,0,0)
 return finish(o,n,m)
def label(n,body,p,w=.6,h=.07,size=.020,col='navy'):
 box(n+'.plate',p,(w,.009,h),col,.002);return text(n+'.text',body,(p[0]-w*.46,p[1]-.0055,p[2]-h*.19),size)
def screen(n,p,w,h,title,lines):
 x,y,z=p;o=box(n+'.body',p,(w,.045,h),'navy',.01);f=box(n+'.screen',(x,y-.026,z),(w-.023,.008,h-.023),'black',.002)
 text(n+'.title',title,(x-w*.45,y-.032,z+h*.31),w*.049,'cyan')
 for i,s in enumerate(lines):text(n+'.line'+str(i),s,(x-w*.45,y-.032,z+h*.07-i*h*.2),w*.034,'amber' if i==0 else 'white')
 return f
def contact(n,p,d,kind='carrier_grip'):
 o=box(n,p,d,'teal',.003);o['candidate_grasp_region']=True;o['qualified_grasp']=False
 CONTACTS.append({'scene_object':n,'asset_id':CUR['asset_id'],'kind':kind,'translation_m':list(p),'dimensions_m':list(d),'physical_grasp_enabled':False,'qualified_pose':None,'required_before_motion':['robot/end-effector compatibility','contact pressure and friction','collision clearance','fixture-specific supported state']});return o
def exclude(o,reason):
 o['contact_excluded']=True;EXCLUSIONS.append({'scene_object':o.name,'reason':reason,'robot_contact_allowed':False})
def collision(n,p,d):
 o=box(n,p,d,'amber',0);o.display_type='WIRE';o.hide_render=True;o['geometry_role']='disabled_collision_proxy';o['collision_enabled']=False;PROXIES.append({'scene_object':n,'shape':'box','translation_m':list(p),'dimensions_m':list(d),'fit_qualified':False,'collision_enabled':False})
def table(n,x,y,w,d):
 box(n+'.top',(x,y,.77),(w,d,.055),'cream',.014)
 for dx in [-w*.42,w*.42]:
  for dy in [-d*.40,d*.40]:box(n+'.leg',(x+dx,y+dy,.385),(.06,.06,.74),'navy',.007)
def carrier(n,p,w=.49,d=.40):
 x,y,z=p;o=box(n+'.base',p,(w,d,.024),'navy',.007)
 for dx in [-w*.32,w*.32]:box(n+'.wide_rest',(x+dx,y,z+.018),(.028,d*.78,.014),'cream',.004)
 for dx in [-w*.55,w*.55]:contact(n+'.grip'+('L' if dx<0 else 'R'),(x+dx,y,z),(.05,.13,.036))
 lock=cyl(n+'.retention_lock',(x-w*.4,y-d*.37,z+.03),.014,.017,'amber')
 box(n+'.id_window',(x,y-d*.40,z+.015),(w*.4,.035,.004),'cream',.001)
 text(n+'.id','CARRIER / NOMINAL',(x-w*.18,y-d*.41,z+.018),.012,'navy',True)
 o['carrier_identity']=n;o['exclusive_occupancy']=True;return o,lock
# A01: allocation records.
root('A01');table('records.table',-1.72,.87,.96,.74)
console=screen('records.console',(-1.72,1.05,1.17),.78,.48,'A01 / RECORDS & ALLOCATION',['NO EXPERIMENTAL DATA','IDENTITY / HISTORY / PAIRING','ACTOR VIEW: ALLOWLIST ONLY'])
queue=box('records.branch_queue',(-1.72,.74,.825),(.64,.27,.04),'navy')
for i in range(7):box('records.route_token.'+str(i),(-1.99+i*.09,.74,.855),(.065,.16,.018),'cyan' if i<4 else 'amber',.002)
label('records.front','IMMUTABLE IDs / REVIEW HOLD',(-1.72,.487,.75),.9,.05,.020)
TARGETS['A01']={'primary':queue,'control':console};collision('COLLISION.A01',(-1.72,.90,1.04),(.98,.82,.59))
# A02: separately identified stock, no closed service recipe.
root('A02');table('stock.table',-1.72,-.05,.96,.78)
for j,(mat,tag) in enumerate([('paper','CARDSTOCK / SEPARATE LOTS'),('polymer','POLYMER / LOT HOLD')]):
 z=.86+j*.18;box('stock.shelf.'+str(j),(-1.72,-.01,z),(.79,.57,.025),'navy')
 for k in range(3):box('stock.sheet.'+str(j)+'.'+str(k),(-1.72,-.05,z+.025+k*.004),(.43,.40,.001 if j else .00035),mat,0)
 label('stock.label.'+str(j),tag,(-1.72,-.303,z+.052),.73,.047,.017)
contact('stock.pickup_support',(-1.72,-.05,1.10),(.55,.47,.018),'broad_sheet_support')
TARGETS['A02']={'primary':bpy.data.objects['stock.sheet.0.0'],'control':bpy.data.objects['stock.pickup_support']};collision('COLLISION.A02',(-1.72,-.05,.99),(.96,.81,.48))
# A03: retained transport carriers and static robotic end-effector.
root('A03');table('carriers.table',-1.64,-1.08,1.12,.80)
a,al=carrier('carrier.flat',(-1.90,-1.08,.825),.43,.43);b,bl=carrier('carrier.folded',(-1.35,-1.08,.825),.43,.43)
for dx in [-.13,.13]:box('carrier.folded.deep_rest',(-1.35+dx,-1.08,.875),(.027,.31,.06),'cream',.003)
box('robot.wrist',(-1.92,-1.28,1.11),(.12,.15,.09),'metal',.008)
for dx in [-.247,.247]:
 box('robot.finger',(-1.90+dx,-1.08,.945),(.042,.12,.12),'teal',.004)
rod('robot.bridge',(-2.15,-1.10,1.035),(-1.65,-1.10,1.035),.025,'metal')
label('carriers.label','A03 / CARRIER CONTACTS ONLY',(-1.64,-1.49,.755),1.07,.06,.022)
text('robot.warning','STATIC GRIPPER / NO ROBOT MOTION',(-2.10,-1.38,.815),.014,'navy',True)
TARGETS['A03']={'primary':a,'control':al};collision('COLLISION.A03',(-1.64,-1.10,.99),(1.15,.85,.48))
# A04: closed fabrication appliance; visual guard not certified.
root('A04');table('fab.table',-.56,.94,1.17,.84)
body=box('fab.enclosure',(-.56,1.00,1.16),(1.05,.63,.70),'cream',.021)
guard=box('fab.closed_guard',(-.56,.674,1.18),(.94,.018,.53),'navy',.008);guard['closed']=True;guard['qualified_guard']=False
box('fab.window',(-.64,.660,1.21),(.61,.008,.34),'guard',.004)
dock=box('fab.load_dock',(-.56,.46,.90),(.67,.28,.07),'teal',.004);dock['dual_purpose_load_and_safe_output']=True;dock['safe_release_requires_trusted_receipt']=True
contact('fab.dock_handle',(-.56,.306,.90),(.31,.045,.04),'dock_handle')
token=box('fab.job_token_slot',(-.14,.65,1.18),(.10,.009,.042),'amber',.002);token['receipt_roles']='job_identity,safe_release';token['trusted_evidence_required']=True
label('fab.title','A04 / CLOSED FABRICATION',(-.56,.664,1.48),.94,.05,.023)
label('fab.hold','SAFE-RELEASE RECEIPT REQUIRED',(-.56,.658,.982),.91,.045,.021)
box('fab.reject_compartment',(-.92,.66,.975),(.16,.018,.065),'coral',.002)
TARGETS['A04']={'primary':dock,'control':token};collision('COLLISION.A04',(-.56,.86,1.16),(1.12,.99,.77))
# A05 panel topology: original embeddings, not a source crease solution.
root('A05');table('families.table',.13,-1.08,2.23,.88)
FAM=[('CS1','ARC-MIURA ROLE',.30,.20,.00035,'paper',(-.77,-1.06,.88)),('CS2','EXTENDED ROLE',.32,.20,.00035,'paper2',(-.31,-1.06,.88)),('CS3','SPIRAL ROLE',.30,.22,.00035,'paper3',(.15,-1.06,.88)),('CS4','LEMNISCATE ROLE',.32,.22,.00035,'paper4',(.61,-1.06,.88)),('PP1','POLYMER ROLE',.42,.36,.001,'polymer',(1.13,-1.06,.88))]
def specimen(family,w,d,t,mat,center,state,visible=True):
 nx,ny=6,4;x,y,z=center;amp={'flat':0,'part_folded':.012,'illustrative_folded':.025,'damaged':.025}[state]
 coords=[]
 for j in range(ny+1):
  for i in range(nx+1):
   u=i/nx-.5;v=j/ny-.5
   px=w*u + (.011 if j%2 else -.011)*(1-abs(u)*1.5)
   py=d*v + (.012*math.sin(i*math.pi/nx) if family=='CS3' else 0)
   pz=amp*(i%2) + amp*.30*math.cos(u*math.pi)
   if family=='CS2':px*=1+.16*v
   if family=='CS3':px+=.045*v*v;py+=.025*u*u
   if family=='CS4':px+=.021*math.sin(v*math.pi*2);pz+=amp*.45*math.sin(u*math.pi*2)
   if family=='PP1':py+=.012*math.sin(u*math.pi);pz+=amp*.3*math.cos(v*math.pi)
   if state=='damaged' and i==nx and j==ny:pz+=.018
   coords.append((x+px,y+py,z+pz))
 objs=[];panel_ids=[];creases=[]
 for j in range(ny):
  for i in range(nx):
   ids=[j*(nx+1)+i,j*(nx+1)+i+1,(j+1)*(nx+1)+i+1,(j+1)*(nx+1)+i]
   vs=[coords[k] for k in ids];c=sum((Vector(v) for v in vs),Vector())/4
   mesh=bpy.data.meshes.new(f'{family}.{state}.P{j*nx+i:03d}.mesh');mesh.from_pydata([Vector(v)-c for v in vs],[],[(0,1,2,3)]);mesh.update()
   o=bpy.data.objects.new(f'{family}.{state}.P{j*nx+i:03d}',mesh);S.collection.objects.link(o);o.location=c;finish(o,o.name,mat);so=o.modifiers.new('Authored sheet thickness','SOLIDIFY');so.thickness=t;so.offset=0
   o['family_id']=family;o['panel_id']=f'P{j*nx+i:03d}';o['static_state']=state;o['physical_fold_validated']=False;o['nominal_thickness_m']=t;exclude(o,'Unqualified panel surface; carrier-only handling until an external panel-contact plan is approved')
   objs.append(o);panel_ids.append(o.name)
 edges={}
 for j in range(ny):
  for i in range(nx):
   ids=[j*(nx+1)+i,j*(nx+1)+i+1,(j+1)*(nx+1)+i+1,(j+1)*(nx+1)+i]
   for a,b in zip(ids,ids[1:]+ids[:1]):edges.setdefault(tuple(sorted((a,b))),[]).append(f'P{j*nx+i:03d}')
 for e,(pair,panels) in enumerate((x for x in edges.items() if len(x[1])==2)):
  aa,bb=pair;a=Vector(coords[aa]);b=Vector(coords[bb]);a.z+=t/2+.00035;b.z+=t/2+.00035
  o=rod(f'{family}.{state}.E{e:03d}',a,b,.0006,'amber' if e%2 else 'cyan',8);o['crease_id']=f'E{e:03d}';o['family_id']=family;o['crease_assignment']='unqualified';o['static_state']=state;exclude(o,'Illustrative crease line; not a hinge, fold axis or contact permission');objs.append(o)
  creases.append({'crease_id':f'E{e:03d}','scene_object':o.name,'adjacent_panel_ids':panels,'mountain_valley':None,'fold_order':None,'fold_motion_limit':None})
 if not visible:
  col=bpy.data.collections.new(f'STATIC_VARIANT.{family}.{state}');S.collection.children.link(col)
  for o in objs:
   for c in list(o.users_collection):c.objects.unlink(o)
   col.objects.link(o)
  col.hide_render=True;col.hide_viewport=True
 STATE_OBJECTS[family+'.'+state]=[o.name for o in objs]
 TOPO.append({'family_id':family,'state':state,'panel_count':len(panel_ids),'panels':panel_ids,'creases':creases,'qualified':False,'illustration_not_physical_fold':True,'displayed_in_default_scene':visible,'nominal_generation_span_m':[w,d],'panel_surface_bounds_m':{'min':[min(c[k] for c in coords) for k in range(3)],'max':[max(c[k] for c in coords) for k in range(3)]},'panel_surface_extent_m':[max(c[k] for c in coords)-min(c[k] for c in coords) for k in range(3)]})
 return bpy.data.objects[panel_ids[0]]
for fam,role,w,d,t,col,pos in FAM:
 carrier('display.'+fam,(pos[0],pos[1],.827),w+.04,d+.06)
 specimen(fam,w,d,t,col,pos,'illustrative_folded')
 for state in ['flat','part_folded','damaged']:specimen(fam,w,d,t,col,pos,state,False)
 text(f'family.{fam}.label',fam+' / '+role,(pos[0]-w*.5,-1.37,.812),.014,'navy',True)
label('families.warning','A05 / ORIGINAL REPRESENTATIVE TEMPLATES / NO VALIDATED FOLDING',(.18,-1.535,.758),2.57,.06,.024)
TARGETS['A05']={'primary':bpy.data.objects['PP1.illustrative_folded.P000'],'control':bpy.data.objects['families.warning.plate']}
# A06: broad supporting folding workstation and rounded crease tool.
root('A06');table('fold.table',-.56,-.10,1.12,.73)
support=box('fold.removable_support',(-.58,-.10,.825),(.62,.46,.06),'teal',.008)
for dx in [-.37,.37]:contact('fold.support_grip'+str(dx),(-.58+dx,-.10,.83),(.09,.15,.04),'removable_support_handle')
box('fold.broad_contact_pad',(-.58,-.10,.864),(.52,.36,.018),'cream',.004)
handle=contact('fold.tool_handle',(-.09,-.10,.855),(.06,.28,.05),'crease_tool_handle')
rod('fold.rounded_tool',(-.09,-.28,.855),(-.09,-.19,.855),.018,'metal')
label('fold.front','A06 / PER-EDGE PLAN REQUIRED',(-.56,-.476,.755),1.06,.05,.023)
TARGETS['A06']={'primary':support,'control':handle};collision('COLLISION.A06',(-.56,-.1,.89),(1.1,.77,.25))
# A07: source-count-based sliders; geometry and spacing independently nominal.
root('A07');table('rig.table',.64,.28,1.12,1.03)
base=box('rig.base',(.64,.28,.832),(.96,.81,.07),'navy',.012)
rail=box('rig.rail_datum',(.64,.35,.889),(.83,.05,.042),'metal',.006)
sliders=[]
for i,dx in enumerate([-.31,0,.31]):
 o=box('rig.sample_slider.'+str(i),(.64+dx,.35,.931),(.105,.15,.07),'cream',.005);sliders.append(o)
 lock=cyl('rig.sample_lock.'+str(i),(.64+dx,.278,.954),.021,.027,'amber','Y');lock['state']='unverified';contact('rig.sample_handle.'+str(i),(.64+dx,.445,.958),(.07,.055,.042),'sample_slider_handle')
 spacer=box('rig.PMMA_spacer.'+str(i),(.64+dx,.35,1.011),(.072,.085,.09),'guard',.002);spacer['source_material_role']='PMMA; optical appearance only'
 mount=box('rig.mount.'+str(i),(.64+dx,.35,1.07),(.07,.11,.026),'teal',.003)
 bolt=cyl('rig.M2_reference_bolt.'+str(i),(.64+dx,.35,1.089),.001,.012,'metal',verts=20);bolt['source_nominal_diameter_m']=.002;bolt['torque_qualified']=False
for i,dx in enumerate([-.36,.36]):
 ps=box('rig.plate_slider.'+str(i),(.64+dx,.06,.94),(.11,.17,.07),'metal',.004)
 foot=box('rig.L_plate_foot.'+str(i),(.64+dx,.025,.991),(.18,.19,.018),'cream',.002)
 plate=box('rig.L_plate_upright.'+str(i),(.64+dx,.115,1.12),(.18,.018,.27),'cream',.002)
 contact('rig.plate_control.'+str(i),(.64+dx,-.041,.975),(.07,.055,.04),'plate_slider_handle')
 cyl('rig.plate_lock.'+str(i),(.64+dx,-.045,.931),.017,.018,'amber','Y')
label('rig.front','A07 / 3 SAMPLE + 2 PLATE SLIDERS',(.64,-.252,.80),1.04,.05,.022)
text('rig.empty_note','FIXTURE EMPTY / NO MOUNT LEASE',(.20,-.15,.878),.017,'white',True)
TARGETS['A07']={'primary':rail,'control':bpy.data.objects['rig.plate_control.0']};collision('COLLISION.A07',(.64,.26,1.06),(1.09,1.01,.57))
# A08 front optical station, authored camera housing and protected carry handle.
root('A08')
front=box('camera.front.body',(.64,-.63,1.26),(.23,.12,.15),'navy',.014)
lens=cyl('camera.front.lens',(.64,-.532,1.26),.054,.11,'black','Y');exclude(lens,'Lens and optical axis are no-contact regions')
cyl('camera.front.glass',(.64,-.468,1.26),.046,.009,'guard','Y')
rod('camera.front.column',(.64,-.63,.13),(.64,-.63,1.17),.024,'metal')
for dx,dy in [(-.25,-.12),(.25,-.12),(0,.22)]:rod('camera.front.tripod',(.64,-.63,.53),(.64+dx,-.63+dy,.055),.019,'navy')
frontmount=contact('camera.front.carry_handle',(.64,-.63,1.37),(.17,.065,.035),'camera_carry_handle')
label('camera.front.label','A08 / FRONT / C-F',(.64,-.702,1.26),.23,.052,.012)
front['camera_id']='C-F';front['lens_id']='L-F';front['view_role']='front';front['calibrated']=False
TARGETS['A08']={'primary':front,'control':frontmount}
# A09 lateral orthogonal view, separately identified.
root('A09')
side=box('camera.side.body',(1.50,.35,1.26),(.13,.22,.15),'navy',.014)
lens=cyl('camera.side.lens',(1.40,.35,1.26),.044,.10,'black','X');exclude(lens,'Lens and optical axis are no-contact regions')
cyl('camera.side.glass',(1.343,.35,1.26),.037,.009,'guard','X')
rod('camera.side.column',(1.50,.35,.13),(1.50,.35,1.17),.023,'metal')
for dx,dy in [(-.13,-.24),(-.13,.24),(.21,0)]:rod('camera.side.tripod',(1.50,.35,.53),(1.50+dx,.35+dy,.055),.018,'navy')
sm=contact('camera.side.carry_handle',(1.50,.35,1.37),(.06,.16,.035),'camera_carry_handle')
label('camera.side.label','A09 / SIDE / C-S',(1.50,.228,1.26),.21,.045,.011)
side['camera_id']='C-S';side['lens_id']='L-S';side['view_role']='side';side['calibrated']=False
TARGETS['A09']={'primary':side,'control':sm}
# A10: two independent scales, tape, calibration target, source-only dimension bars.
root('A10');x,y=.64,.35
r1=box('reference.height_ruler',(.17,.53,1.20),(.045,.01,.55),'cream',.001)
r2=box('reference.image_scale',(.64,.55,1.045),(.51,.012,.04),'cream',.001)
for i in range(51):
 box('reference.height_tick.'+str(i),(.17+(.006 if i%5 else 0),.523,.95+i*.01),(.018 if i%5 else .032,.003,.001),'navy',0)
 box('reference.image_tick.'+str(i),(.39+i*.01,.541,1.050+(.005 if i%5 else 0)),(.001,.003,.012 if i%5 else .022),'navy',0)
 if i%10==0:text('reference.number.h'+str(i),str(i),(.19,.520,.948+i*.01),.011,'navy')
tape=cyl('reference.tape_case',(.98,.62,.895),.054,.035,'amber')
contact('reference.ruler_handle',(.17,.53,1.49),(.052,.026,.035),'reference_handle')
# Authored checkerboard; no calibration values or claim.
box('reference.calibration_board',(.98,.73,1.18),(.24,.014,.19),'cream',.002)
for j in range(5):
 for i in range(7):
  if (i+j)%2==0:box('reference.checker.'+str(j)+'.'+str(i),(.89+i*.028,.720,1.125+j*.026),(.027,.002,.025),'black',0)
for n,l,z in [('width_source',.42878,.842),('length_methods',.38363,.85),('length_figure',.38365,.858)]:
 o=box('DIMREF.PP.'+n,(-.62,.21,z),(l,.006,.003),'amber',0);o['source_reference_length_m']=l;o['fabrication_allowed']=False;o['dimensional_conflict']='C01' if 'length' in n else 'none';exclude(o,'Source dimension reference only; not a specimen or fabrication drawing')
TARGETS['A10']={'primary':r1,'control':tape}
# A11: corner-load enclosure AND separately identified benign rigid demonstration pad.
root('A11');table('qual.table',1.83,1.02,1.06,.89)
qb=box('qual.corner.base',(1.83,1.07,.85),(.91,.70,.075),'navy',.009)
for dx in [-.41,.41]:
 for dy in [-.28,.28]:rod('qual.corner.post',(1.83+dx,1.07+dy,.89),(1.83+dx,1.07+dy,1.48),.014,'metal')
box('qual.corner.top',(1.83,1.07,1.49),(.90,.69,.028),'cream',.005)
g=box('qual.corner.closed_guard',(1.83,.781,1.18),(.80,.003,.56),'guard',0);g['closed']=True;g['qualified_guard']=False
for dx,dy in [(-.22,-.18),(.22,.18)]:
 box('qual.corner.support',(1.83+dx,1.07+dy,.985),(.10,.10,.16),'teal',.004)
 box('qual.corner.attachment',(1.83+dx,1.07+dy,1.087),(.055,.055,.035),'amber',.004)
ctrl=screen('qual.control',(1.83,1.355,1.62),.83,.23,'A11 / QUALITATIVE ONLY',['LOAD / SUPPORT UNQUALIFIED','NO MASS OR FORCE INFERRED','LOAD REMOVAL BEFORE RELEASE'])
rigid=box('qual.rigid_demo_support',(1.83,.54,.851),(.69,.21,.095),'teal',.004);rigid['fixture_id']='Q-RIGID';qb['fixture_id']='Q-CORNER'
for dx in [-.25,.25]:contact('qual.rigid.support_handle'+str(dx),(1.83+dx,.54,.917),(.09,.10,.036),'rigid_demo_handle')
label('qual.front','SEPARATE RIGID SUPPORT / NO LOAD', (1.83,.43,.845),.97,.051,.022)
TARGETS['A11']={'primary':qb,'control':ctrl};collision('COLLISION.A11',(1.83,1.03,1.24),(1.09,1.09,.94))
# A12 inspection and history-preserving quarantine.
root('A12');table('inspection.table',1.92,-.81,1.04,1.15)
cradle=box('inspection.rest_cradle',(1.91,-.57,.84),(.71,.46,.065),'cream',.007)
for dx in [-.24,.24]:box('inspection.broad_rest',(1.91+dx,-.57,.884),(.07,.35,.03),'teal',.004)
q=box('inspection.quarantine_bin',(1.91,-1.14,.91),(.73,.39,.22),'coral',.009)
box('inspection.quarantine_lid',(1.91,-1.14,1.034),(.75,.41,.025),'navy',.007)
contact('inspection.quarantine_handle',(1.91,-1.14,1.065),(.24,.08,.035),'quarantine_case_handle')
ins=screen('inspection.history',(1.91,-.39,1.27),.83,.32,'A12 / REST & HISTORY',['NO RECOVERY ASSUMED','DAMAGE REMAINS IN HISTORY','HELD != RELEASED'])
label('inspection.front','INSPECT / RETAIN / QUARANTINE',(1.92,-1.396,.762),.99,.05,.023)
TARGETS['A12']={'primary':cradle,'control':ins};collision('COLLISION.A12',(1.92,-.80,1.10),(1.10,1.18,.73))
# Studio and visual limits.
CUR=None
box('studio.floor',(0,0,-.035),(200,200,.045),'floor',0)
box('scene.banner',(0,1.80,1.87),(4.62,.035,.35),'navy',.010)
text('scene.title','ARC-MORPH / ORIGINAL ROBOT LAB',(-2.17,1.779,1.925),.115)
text('scene.subtitle','12 ASSET GROUPS / FIVE REPRESENTATIVE FAMILIES / STATIC SEMANTIC CONTROLS',(-2.16,1.778,1.821),.045,'cyan')
text('scene.warning','NO PHYSICAL FOLDING, LIVE LOADS, CALIBRATION OR EXPERIMENTAL MEASUREMENTS',(-2.16,1.777,1.745),.038,'amber')
# Required operation anchor pairs and extra named candidate interfaces.
bpy.context.view_layer.update();contract=json.loads((P/'operation_binding_contract.json').read_text());anchors=[];bindings=[]
OP_TARGETS={'R10':('rig.mount.0','rig.M2_reference_bolt.0'),'R13':('rig.L_plate_upright.0','rig.plate_control.0'),'R14':('rig.sample_slider.0','rig.sample_lock.0'),'R19':('rig.sample_slider.0','rig.sample_lock.0'),'R26':('qual.rigid_demo_support','qual.rigid.support_handle-0.25'),'R27':('qual.rigid_demo_support','qual.rigid.support_handle-0.25'),'R30':('rig.mount.0','rig.M2_reference_bolt.0')}
for op in contract['operations']:
 aid=op['primary_asset_id'];r=ROOTS[aid]
 selected={role:bpy.data.objects[OP_TARGETS[op['operation_id']][i]] if op['operation_id'] in OP_TARGETS else TARGETS[aid][role] for i,role in enumerate(['primary','control'])}
 for role in ['primary','control']:
  target=selected[role];o=bpy.data.objects.new(f"ANCHOR.{op['operation_id']}.{role}",None);S.collection.objects.link(o);o.parent=r;o.location=target.matrix_world.translation;o.empty_display_size=.026;o['target_object']=target.name;o['operation_id']=op['operation_id'];o['physical_execution_enabled']=False
  anchors.append({'anchor_id':o.name,'asset_id':aid,'scene_object':o.name,'target_object':target.name,'translation_m':list(o.location),'rotation_quaternion_xyzw':[0,0,0,1],'qualified_pose':None,'physical_execution_enabled':False})
 bindings.append(dict(op,primary_target=selected['primary'].name,control_target=selected['control'].name))
# Fixture-specific alternatives prevent the generic R19/R30 placeholder hiding the branch.
for name,target,aid in [('ANCHOR.R19.corner_release','qual.corner.base','A11'),('ANCHOR.R19.rigid_demo_release','qual.rigid_demo_support','A11'),('ANCHOR.R30.rigid_demo_unmount','qual.rigid_demo_support','A11'),('ANCHOR.R22.corner_unmount','qual.corner.base','A11')]:
 o=bpy.data.objects.new(name,None);S.collection.objects.link(o);o.parent=ROOTS[aid];o.location=bpy.data.objects[target].matrix_world.translation;o['target_object']=target;o['physical_execution_enabled']=False
 anchors.append({'anchor_id':name,'asset_id':aid,'scene_object':name,'target_object':target,'translation_m':list(o.location),'qualified_pose':None,'physical_execution_enabled':False})
def save(n,data):(P/n).write_text(json.dumps(data,indent=2)+'\n')
save('affordances.json',{'schema':'sciencegym.arcmorph.affordances.v1','units':'m','anchors':anchors,'candidate_contacts':CONTACTS,'exclusion_regions':EXCLUSIONS,'collision_proxies':PROXIES,'status':'Nominal metadata selectors and candidate contacts only; all physical grasps disabled'})
save('operation_bindings.json',{'schema':'sciencegym.arcmorph.operation_bindings.v1','operations':bindings,'conditional_anchor_rule':'R19/R30 require actual fixture identity. Corner and qualitative rigid alternatives are explicit in affordances.json; never use a generic rail anchor to release the corner fixture.','unbound_operations':[]})
save('specimen_topology.json',{'schema':'sciencegym.arcmorph.panel_crease.v1','source_geometry_used':False,'physical_folding_validated':False,'static_variants':TOPO,'state_objects':STATE_OBJECTS})
hidden_cols=[c for c in bpy.data.collections if c.name.startswith('STATIC_VARIANT.')]
for c in hidden_cols:c.hide_viewport=False
bpy.context.view_layer.update()
save('asset_inventory.json',{'schema':'sciencegym.arcmorph.inventory.v1','units':'m','asset_group_count':12,'imported_mesh_count':0,'assets':[{'asset_id':aid,'root':r.name,'physical_geometry_validated':False,'parts':[{'scene_object':o.name,'type':o.type,'dimensions_m':list(o.dimensions),'translation_m':list(o.matrix_world.translation),'geometry_basis':'original_authored','displayed_in_default':not any(c.hide_render for c in o.users_collection),'graspable':False} for o in bpy.data.objects if o.parent==r]} for aid,r in ROOTS.items()]})
for c in hidden_cols:c.hide_viewport=True
bpy.context.view_layer.update()
save('materials/materials.json',{'materials':[{'name':k,'display_color_rgba':list(m.diffuse_color),'mechanical_model':None,'optical_calibration':None} for k,m in M.items()]})
# Three genuinely rendered views.
def camera(n,p,target,scale):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);S.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=scale;d.clip_start=.001;d.clip_end=250;return o
def area(n,p,target,power,size):
 d=bpy.data.lights.new(n,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(n,d);S.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('LIGHT.key',(-3,-5,7),(0,0,.9),2200,5);area('LIGHT.fill',(5,-2,5),(0,0,1),1400,4);area('LIGHT.rim',(0,4,6),(0,0,1),2400,4)
CAMS={'overview':camera('CAM.overview',(6.8,-9.5,7.0),(0,.02,1.05),6.65),'handling':camera('CAM.handling',(-3.8,-5.2,4.3),(-.22,-1.08,.84),3.60),'metrology':camera('CAM.metrology',(3.4,-3.1,3.1),(.66,.18,1.06),2.28)}
S.camera=CAMS['overview'];S.render.filepath='//../evidence/overview.png'
# No external paths, scripts, imported images or source raster art are embedded.
bpy.ops.wm.save_as_mainfile(filepath=str(P/'geometry/arcmorph_lab.blend'))
# Portable default display exports: fonts converted only in a temporary scene copy.
export_scene=S.copy();export_scene.name='TEMP_PORTABLE_EXPORT';bpy.context.window.scene=export_scene
for obj in export_scene.objects:obj.select_set(False)
for obj in list(export_scene.objects):
 if obj.type=='FONT' and not any(c.hide_render for c in obj.users_collection):
  cp=obj.copy();cp.data=obj.data.copy();export_scene.collection.objects.link(cp);cp.parent=obj.parent;cp.name=obj.name+'.portable';obj.hide_set(True);cp.select_set(True);bpy.context.view_layer.objects.active=cp;bpy.ops.object.convert(target='MESH');cp.select_set(False)
# Select the scene's visible objects, excluding fonts, studio ground, render cams/lights and disabled proxies.
for obj in export_scene.objects:
 sel=(obj.type in {'MESH','EMPTY'} and not any(c.hide_render for c in obj.users_collection) and not obj.hide_render and obj.name!='studio.floor' and not obj.hide_get())
 obj.select_set(sel)
bpy.ops.export_scene.gltf(filepath=str(P/'geometry/arcmorph_lab.glb'),export_format='GLB',use_selection=True,export_extras=True,export_apply=True,export_yup=True)
bpy.context.window.scene=S;bpy.data.scenes.remove(export_scene)
# Undo hidden native text flag inherited by shallow scene copy.
for obj in list(bpy.data.objects):
 if '.portable' in obj.name:bpy.data.objects.remove(obj,do_unlink=True)
for obj in S.objects:
 if obj.type=='FONT':obj.hide_set(False)
S.camera=CAMS['overview'];S.render.filepath='//../evidence/overview.png'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'geometry/arcmorph_lab.blend'))
receipt={'renderer':'Blender Cycles','blender_version':bpy.app.version_string,'device':'CPU','samples':96,'denoising':False,'source_pixels_used':False,'images':[]}
if '--no-render' not in sys.argv:
 for name,cam in CAMS.items():
  S.camera=cam;S.render.filepath=str(P/'evidence'/f'{name}.png');bpy.ops.render.render(write_still=True)
  f=P/'evidence'/f'{name}.png';receipt['images'].append({'path':f'evidence/{name}.png','sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'camera':cam.name,'resolution':[1920,1280],'kind':'actual CPU path-traced static scene; not measured evidence'})
 save('review/render_receipt.json',receipt)
# Sanitize saved render path, keep all editability.
S.camera=CAMS['overview'];S.render.filepath='//../evidence/overview.png';bpy.ops.wm.save_as_mainfile(filepath=str(P/'geometry/arcmorph_lab.blend'))
print('ARC_MORPH_ASSET_BUILD_COMPLETE',len(bpy.data.objects),len(anchors),len(TOPO))
