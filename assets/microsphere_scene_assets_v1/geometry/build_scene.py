"""Original procedural ScienceGym review scene. No optical solver or hardware controls.
SPDX-License-Identifier: Apache-2.0
"""
import bpy, math, json, pathlib, time, sys
from mathutils import Vector
P=pathlib.Path(__file__).resolve().parents[1]
if (P/'scene_core_manifest.json').exists():raise RuntimeError('Sealed package: rebuild only in a new unsealed revision')
C=json.loads((P/'shared_binding_contract.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene; scene.name=C['scene_name'];scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene['source_doi']=C['source_doi'];scene['physical_actuation_enabled']=False;scene['scientific_simulation_performed']=False
scene['geometry_status']='Original unqualified review geometry; no measurement evidence';scene['default_state']='HOLD_QUALIFICATION'
M={}
def material(n,c,metal=0,rough=.4):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True
 b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough;M[n]=m
for a in [('ink',(.027,.058,.079)),('floor',(.60,.70,.71)),('white',(.91,.94,.89)),('steel',(.28,.43,.46),.65),('teal',(.015,.40,.42)),('cyan',(.26,.83,.79)),('amber',(.96,.57,.16)),('violet',(.46,.34,.66)),('gold',(.79,.53,.20),.65),('red',(.72,.19,.22)),('glass',(.22,.45,.51),.1),('pale',(.73,.84,.82))]:material(*a)
roots={};collections={}
for n in ['LAB_REVIEW','SOURCE_SCALE','SCHEMATIC_ENLARGEMENTS']:
 c=bpy.data.collections.new(n);scene.collection.children.link(c);collections[n]=c
for a in C['assets']:
 o=bpy.data.objects.new(a['asset_id'],None);collections['LAB_REVIEW'].objects.link(o);o['asset_id']=a['asset_id'];o['physical_actuation_enabled']=False;o['geometry_status']='original_illustrative_unqualified';roots[a['asset_id']]=o
contacts=[]
def own(o,g=None,collection='LAB_REVIEW'):
 for c in list(o.users_collection):c.objects.unlink(o)
 collections[collection].objects.link(o)
 if g:o.parent=roots[g];o['asset_id']=g
 o['physical_actuation_enabled']=False;o['geometry_status']='source_scale_context_not_qualified' if collection=='SOURCE_SCALE' else 'original_illustrative_unqualified'
 o['representation_class']=collection
 return o

def box(n,loc,dim,m='white',g=None,bevel=.012,collection='LAB_REVIEW'):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(M[m]);own(o,g,collection)
 if bevel:
  b=o.modifiers.new('Authored rounded edges','BEVEL');b.width=min(bevel,min(dim)/4);b.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=b.name)
 return o

def cyl(n,loc,r,d,m='steel',g=None,verts=32,collection='LAB_REVIEW'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc);o=bpy.context.object;o.name=n;o.data.materials.append(M[m]);own(o,g,collection)
 for f in o.data.polygons:f.use_smooth=True
 return o

def sphere(n,loc,r,m='cyan',g=None,collection='LAB_REVIEW'):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=r,location=loc);o=bpy.context.object;o.name=n;o.data.materials.append(M[m]);own(o,g,collection)
 for f in o.data.polygons:f.use_smooth=True
 return o

def line(n,a,b,r=.013,m='teal',g=None,collection='LAB_REVIEW'):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,g,16,collection);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def txt(n,s,loc,size=.14,m='ink',g=None,flat=False,collection='LAB_REVIEW'):
 cu=bpy.data.curves.new(n,'FONT');cu.body=s;cu.size=size;cu.extrude=.0003;cu.resolution_u=2
 o=bpy.data.objects.new(n,cu);scene.collection.objects.link(o);o.location=loc
 if not flat:o.rotation_euler=(math.pi/2,0,0)
 o.data.materials.append(M[m]);return own(o,g,collection)

def plaque(n,title,sub,x,y,z,w,g,accent='teal'):
 box(n+'.back',(x,y,z),(w,.045,.47),'ink',g)
 box(n+'.stripe',(x-w/2+.025,y-.027,z),(.035,.008,.37),accent,g,.002)
 txt(n+'.title',title,(x-w/2+.09,y-.03,z+.06),.120,'white',g)
 txt(n+'.sub',sub,(x-w/2+.09,y-.03,z-.12),.080,'cyan' if accent=='teal' else 'amber',g)

def bench(n,x,y,w,d,g):
 box(n+'.top',(x,y,.99),(w,d,.12),'white',g)
 for dx in [-w/2+.10,w/2-.10]:
  for dy in [-d/2+.10,d/2-.10]:box(n+'.leg',(x+dx,y+dy,.465),(.075,.075,.93),'steel',g)
 box(n+'.shelf',(x,y,.28),(w-.1,d-.1,.06),'teal',g)
 return n+'.top'

def contact(supported,support):contacts.append({'supported_object':supported,'support_object':support,'axis':'Z','expected_gap_m':0,'tolerance_m':2e-6,'scope':'authored illustrative static support only; no qualified contact or collision model'})
def carrier(n,x,y,z,g):
 o=box(n+'.body',(x,y,z+.01),(.42,.29,.02),'steel',g)
 for dx in [-.20,.20]:box(n+'.side_rim',(x+dx,y,z+.04),(.02,.29,.04),'steel',g)
 for dy in [-.135,.135]:box(n+'.end_rim',(x,y+dy,z+.04),(.38,.02,.04),'steel',g)
 box(n+'.lid',(x,y,z+.072),(.42,.29,.024),'pale',g)
 for dx in [-.245,.245]:box(n+'.handle',(x+dx,y,z+.033),(.07,.12,.045),'gold',g)
 txt(n+'.label','SEALED',(x-.11,y-.05,z+.085),.054,'ink',g,True)
 return o
# Original architectural lab layout, all facility dimensions unqualified.
box('Environment.floor',(0,0,-.09),(10.8,8.5,.18),'floor',bevel=.05)
box('Environment.backwall',(0,3.9,1.57),(10.8,.10,3.14),'pale')
txt('Environment.title','MICROSPHERE / WHITE-LIGHT REVIEW',(-4.9,3.839,2.72),.31,'ink')
txt('Environment.subtitle','INERT TARGETS  /  ORIGINAL ASSETS  /  ALL PHYSICAL WORK HELD',(-4.85,3.835,2.36),.128,'teal')
txt('Environment.warning','ILLUSTRATION ONLY  |  NO OPTICAL MEASUREMENTS  |  NO HARDWARE COMMANDS',(-4.8,-3.88,.01),.157,'ink',flat=True)
# ST01 intake with four supported protected carriers; safe specimen targets stay closed.
b=bench('A01.intake_bench',-3.58,-1.2,2.75,1.28,'A01')
for i,(x,y) in enumerate([(-4.20,-.90),(-3.03,-.90),(-4.20,-1.43),(-3.03,-1.43)]):
 n=f'A01.carrier_{i+1:02}';carrier(n,x,y,1.05,'A01');contact(n+'.body',b)
plaque('A01.station','ST01 / INTAKE + CUSTODY','PROTECTED CARRIERS / IDENTITY FIRST',-3.58,-1.88,.93,2.77,'A01')
# Source-scale representatives live inside a closed carrier. Source numbers are size context only.
# The slide/coupon exterior is an original unqualified proxy, never exact experimental CAD.
slide=box('A02.source_scale_slide_proxy',(-4.2,-.9,1.0705),(.075,.025,.001),'glass','A02',0,'SOURCE_SCALE');slide['dimensions_status']='Authored slide proxy dimensions; source exterior unknown'
for i,um in enumerate([1,3,4.74,10,50]):
 o=sphere('A03.source_scale_sphere_'+str(um).replace('.','p')+'um',(-4.22+i*.005,-.9,1.071+um*1e-6/2),um*1e-6/2,'cyan','A03','SOURCE_SCALE');o['reported_diameter_um']=um;o['optical_properties_qualified']=False
# A04 actual-size half-ball proxy controls; shapes are original and prescriptions unqualified.
def hemi(n,x,y,z,d,g,collection):
 vs=[(x,y,z+d/2)];fs=[];rings=10;segments=32;r=d/2
 for j in range(1,rings+1):
  th=j*math.pi/2/rings
  for i in range(segments):
   ph=i*2*math.pi/segments;vs.append((x+r*math.sin(th)*math.cos(ph),y+r*math.sin(th)*math.sin(ph),z+r*math.cos(th)))
 for i in range(segments):fs.append((0,1+i,1+(i+1)%segments))
 for j in range(rings-1):
  for i in range(segments):a=1+j*segments+i;b=1+j*segments+(i+1)%segments;fs.append((a,b,b+segments,a+segments))
 fs.append(tuple(reversed([1+(rings-1)*segments+i for i in range(segments)])))
 mesh=bpy.data.meshes.new(n+'.mesh');mesh.from_pydata(vs,[],fs);mesh.update();o=bpy.data.objects.new(n,mesh);scene.collection.objects.link(o);o.data.materials.append(M['cyan']);own(o,g,collection);return o
for x,d in [(-3.05,.0005),(-3.01,.0025)]:
 o=hemi('A04.source_scale_sil_'+str(d*1000).replace('.','p')+'mm',x,-.9,1.07,d,'A04','SOURCE_SCALE');o['reported_diameter_mm']=d*1000;o['optical_prescription_qualified']=False
# ST02/ST05 closed service doors, no internal beam/process geometry.
for prefix,x,label,sub in [('prep',-4.10,'ST02 / PREPARATION','QUALIFIED SERVICE / NO RECIPE'),('sem',-2.36,'ST05 / SEM REFERENCE','CLOSED SERVICE / NO BEAM CONTROL')]:
 box('A06.'+prefix+'_enclosure',(x,2.28,1.05),(1.54,1.45,2.10),'white','A06',.045)
 box('A06.'+prefix+'_door',(x,1.536,1.13),(1.34,.035,1.55),'ink','A06')
 box('A06.'+prefix+'_receipt_slot',(x,1.509,.99),(.99,.025,.20),'teal','A06')
 txt('A06.'+prefix+'_receipt_text','RECEIPT MISSING',(x-.44,1.49,.958),.097,'white','A06')
 plaque('A06.'+prefix+'_station',label,sub,x,1.50,1.92,1.62,'A06','amber')
 txt('A06.'+prefix+'_hold','HOLD',(x-.32,1.48,1.39),.225,'amber','A06')
# ST03 contained sphere stock and assembly, no exposed stock or recipe.
b=bench('A03.assembly_bench',-.49,2.34,1.90,1.50,'A03')
box('A03.closed_assembly',( -.49,2.34,1.395),(1.6,1.15,.69),'teal','A03');contact('A03.closed_assembly',b)
box('A03.assembly_lid',(-.49,2.34,1.76),(1.67,1.20,.04),'pale','A03')
for i,x in enumerate([-.94,-.49,-.04]):
 cyl('A03.sealed_stock_'+str(i),(x,2.36,1.90),.085,.24,'white','A03');cyl('A03.stock_cap_'+str(i),(x,2.36,2.04),.091,.04,'amber','A03');contact('A03.sealed_stock_'+str(i),'A03.assembly_lid')
plaque('A03.station','ST03 / CONTAINED ASSEMBLY','LOT + COATING STATE / SOP MISSING',-.49,1.555,1.02,1.94,'A03','amber')
# ST04 prominent conventional microscope, within a closed enclosure and front service face.
b=bench('A05.microscope_bench',.25,-.83,2.75,2.18,'A05')
box('A05.base',(.25,-.68,1.12),(1.70,1.22,.14),'ink','A05');contact('A05.base',b)
box('A05.upright',(.77,-.23,1.80),(.28,.31,1.22),'white','A05')
box('A05.optical_head',(.28,-.36,2.43),(1.20,.41,.20),'white','A05')
cyl('A05.turret_connector',(.07,-.56,2.3175),.10,.025,'steel','A05')
cyl('A05.objective_turret',(.07,-.56,2.22),.24,.17,'steel','A05')
cyl('A05.objective_proxy',(.07,-.56,2.055),.083,.16,'ink','A05')
box('A05.stage_support',(.07,-.56,1.54),(.74,.66,.06),'steel','A05')
for x in [-.26,.40]:box('A05.stage_post',(x,-.28,1.35),(.08,.08,.32),'steel','A05')
carrier('A05.stage_carrier',.07,-.56,1.57,'A05');contact('A05.stage_carrier.body','A05.stage_support')
cyl('A05.illumination_support',(.07,-.56,1.2025),.12,.025,'steel','A05')
cyl('A05.illumination_proxy',(.07,-.56,1.33),.12,.23,'white','A05')
# Closed enclosure represented by original solid back/side panels, open-looking front is dark opaque window.
box('A05.enclosure_back',(.25,.05,1.855),(2.18,.06,1.61),'pale','A05')
for x in [-.86,1.36]:box('A05.enclosure_side',(x,-.76,1.855),(.045,1.69,1.61),'pale','A05')
box('A05.enclosure_top',(.25,-.76,2.68),(2.265,1.69,.04),'white','A05')
# Closed transparent front guard: original stationary material, no movable door or script
m=bpy.data.materials.new('closed_guard_glass');m.use_nodes=True;m.diffuse_color=(.7,.9,.9,.13);nd=m.node_tree.nodes;nd.clear();out=nd.new('ShaderNodeOutputMaterial');mix=nd.new('ShaderNodeMixShader');tr=nd.new('ShaderNodeBsdfTransparent');pr=nd.new('ShaderNodeBsdfPrincipled');pr.inputs['Base Color'].default_value=(.45,.8,.8,1);pr.inputs['Roughness'].default_value=.12;mix.inputs[0].default_value=.10;m.node_tree.links.new(tr.outputs[0],mix.inputs[1]);m.node_tree.links.new(pr.outputs[0],mix.inputs[2]);m.node_tree.links.new(mix.outputs[0],out.inputs[0]);M['guard']=m
box('A05.closed_front_guard',(.25,-1.591,1.855),(2.18,.008,1.61),'guard','A05',0)
for x in [-.84,1.34]:box('A05.front_frame',(x,-1.59,1.855),(.045,.045,1.61),'teal','A05')
box('A05.front_guard_plate',(.25,-1.585,1.23),(2.18,.045,.35),'teal','A05')
txt('A05.safe_label','CLOSED GUARD / STATE ONLY',(-.66,-1.62,1.23),.119,'white','A05')
plaque('A05.station','ST04 / WHITE-LIGHT MICROSCOPE','TRANSMISSION / REFLECTION / ACQUISITION HELD',.25,-1.96,.98,2.83,'A05')
# A02 stand-alone magnified diagram board, physically detached from source-scale objects.
b=bench('A02.diagram_bench',-1.06,-3.00,4.03,1.15,'A02')
board=box('A02.diagram_board',(-1.06,-2.91,1.085),(3.82,.97,.07),'ink','A02',.014,'SCHEMATIC_ENLARGEMENTS');contact('A02.diagram_board',b)
txt('A02.diagram_title','FOUR TARGET FAMILIES / ORIGINAL CATEGORY ICONS',(-2.84,-2.61,1.124),.119,'white','A02',True,'SCHEMATIC_ENLARGEMENTS')
for i,(name,label,col) in enumerate([('grating','GRATING','gold'),('aao','Au / AAO','amber'),('disc','DISC TRACKS','cyan'),('star','STAR FILM ?','violet')]):
 x=-2.44+i*.92;box('A02.icon_tile_'+name,(x,-2.98,1.138),(.75,.42,.028),'teal','A02',.01,'SCHEMATIC_ENLARGEMENTS')
 if name in {'grating','disc'}:
  for j in range(5):box('A02.icon_'+name+'_'+str(j),(x-.23+j*.11,-2.98,1.163),(.055,.32,.022),col,'A02',0,'SCHEMATIC_ENLARGEMENTS')
 elif name=='aao':
  for j in range(3):
   for k in range(2):cyl('A02.icon_pore_'+str(j)+'_'+str(k),(x-.19+j*.19,-3.055+k*.15,1.163),.043,.022,'amber','A02',16,'SCHEMATIC_ENLARGEMENTS')
 else:
  vs=[]
  for j in range(10):a=math.pi/2+j*math.pi/5;r=.17 if j%2==0 else .073;vs.append((x+r*math.cos(a),-2.98+r*math.sin(a),1.176))
  me=bpy.data.meshes.new('A02.original_star.mesh');me.from_pydata(vs,[],[list(range(10))]);o=bpy.data.objects.new('A02.original_star_icon',me);scene.collection.objects.link(o);o.data.materials.append(M[col]);own(o,'A02','SCHEMATIC_ENLARGEMENTS')
 txt('A02.icon_label_'+name,label,(x-.34,-3.32,1.123),.088,'white','A02',True,'SCHEMATIC_ENLARGEMENTS')
txt('A02.diagram_warning','SCHEMATIC ONLY / NO LENGTH SCALE / NOT AN OPTICAL IMAGE',(-2.86,-3.45,1.124),.099,'amber','A02',True,'SCHEMATIC_ENLARGEMENTS')
# A04 explicitly enlarged lens explanation board on a separate ST01-side table.
b=bench('A04.control_bench',3.42,-1.13,2.76,1.54,'A04')
box('A04.control_board',(3.42,-1.05,1.075),(2.56,1.27,.05),'ink','A04',.02,'SCHEMATIC_ENLARGEMENTS');contact('A04.control_board',b)
for x,d,label,mag in [(2.66,.10,'0.5 mm SIL / 80x',200),(3.56,.50,'2.5 mm SIL / 40x',200)]:
 o=hemi('A04.magnified_sil_'+str(mag)+'_'+str(x),x,-1.05,1.10,d,'A04','SCHEMATIC_ENLARGEMENTS');o['illustration_magnification']=mag;o['diameter_display_rule']='source diameter times illustration magnification; not optical magnification'
 txt('A04.control_label_'+str(x),label,(x-.35,-1.49,1.103),.086,'white','A04',True,'SCHEMATIC_ENLARGEMENTS')
o=sphere('A04.magnified_sphere_40000x',(4.25,-1.05,1.1948),.0948,'cyan','A04','SCHEMATIC_ENLARGEMENTS');o['illustration_magnification']=40000;o['reported_diameter_um']=4.74
# Source-scale spheres remain separate and invisible at this wide framing, never scaled in place.
txt('A04.sphere_size_label','4.74 um',(3.99,-1.49,1.103),.092,'white','A04',True,'SCHEMATIC_ENLARGEMENTS')
txt('A04.scale_labels','SIL DISPLAY x200   |   SPHERE DISPLAY x40000',(2.23,-.54,1.104),.089,'cyan','A04',True,'SCHEMATIC_ENLARGEMENTS')
plaque('A04.controls','LENS CONTEXT / NOT OPTICAL SIMULATION','DIFFERENT DISPLAY SCALES / CONTROLS RETAINED',3.42,-1.94,.98,2.8,'A04')
# ST06 evidence panel and plane distinction panel, no simulated optical image or detector plot.
box('A08.evidence_base',(3.03,2.28,.21),(3.58,1.26,.42),'white','A08')
box('A08.evidence_panel',(3.03,2.73,1.59),(3.58,.12,2.34),'ink','A08')
txt('A08.heading','ST06 / EVIDENCE REVIEW',(1.43,2.659,2.61),.20,'white','A08')
for i,(label,col) in enumerate([('REPORTED EXAMPLES: E01 / E02 / E03 / E04','cyan'),('BARE + SIL COMPARATORS: RETAINED','white'),('SIZE / COATING / EXTENSIONS: TEXT-ONLY','amber'),('ARRAY COMBINATION: PROPOSED','amber'),('MIE / FDTD / RAY / FLOW: UNRUN','violet'),('NEW DATA: NONE   |   16 INPUT GAPS','white')]):txt('A08.ledger_'+str(i),label,(1.43,2.651,2.28-i*.225),.102,col,'A08')
plaque('A08.hold','HOLD_QUALIFICATION','PAPER VALUES ARE CONTEXT, NEVER SUCCESS TARGETS',3.03,2.64,.73,3.30,'A08','amber')
# A07 plane cards are logical coordinates, no literal optical distances in lab-space.
for i,(label,color) in enumerate([('OBJECT','gold'),('VIRTUAL','violet'),('DETECTOR','cyan')]):
 x=1.93+i*1.06;box('A07.plane_'+label,(x,1.25,1.26),(.90,.055,.55),color,'A07',.009,'SCHEMATIC_ENLARGEMENTS')
 txt('A07.label_'+label,label,(x-.37,1.212,1.27),.11,'ink','A07',False,'SCHEMATIC_ENLARGEMENTS')
 for dy in [-.05,.05]:box('A07.support_'+label+str(dy),(x,1.25+dy,.615),(.06,.06,1.23),'steel','A07')
txt('A07.warning','DISTINCT FRAMES / TRANSFORM + CALIBRATION MISSING',(1.47,1.20,.89),.107,'ink','A07',False,'SCHEMATIC_ENLARGEMENTS')
# ST07 supported return/quarantine and immutable archive illustration.
b=bench('A09.return_bench',3.35,-3.12,2.92,1.03,'A09')
box('A09.quarantine_nest',(2.80,-3.06,1.08),(.79,.62,.06),'amber','A09');contact('A09.quarantine_nest',b)
carrier('A09.return_carrier',2.8,-3.06,1.11,'A09');contact('A09.return_carrier.body','A09.quarantine_nest')
box('A09.archive_box',(4.1,-3.06,1.25),(.66,.53,.40),'teal','A09');contact('A09.archive_box',b)
box('A09.archive_lid',(4.1,-3.06,1.47),(.69,.56,.04),'pale','A09')
plaque('A09.station','ST07 / CLOSEOUT + ARCHIVE','CONTAINMENT / CUSTODY / SERVICE RELEASE',3.35,-3.69,.97,2.94,'A09','amber')
# Contract anchors are evidence selectors, never physical manipulation targets.
locs={
'A01':[(-3.58,-1.2,1.05),(-4.2,-.9,1.14),(-3.58,-1.9,.93)],
'A02':[(-2.44,-2.98,1.17),(-1.52,-2.98,1.17),(-.60,-2.98,1.17),(.32,-2.98,1.17),(-1.06,-3.45,1.12)],
'A03':[(-.49,2.36,2.06),(-.49,2.34,1.76),(-.49,1.55,1.02)],
'A04':[(2.66,-1.05,1.1),(3.56,-1.05,1.1),(3.42,-1.94,.98)],
'A05':[(.25,-1.62,1.23),(.07,-.56,1.57),(.25,-1.96,.98),(.07,-.56,1.89)],
'A06':[(-4.1,1.49,.99),(-2.36,1.49,.99),(-2.36,1.49,1.39)],
'A07':[(1.93,1.21,1.26),(2.99,1.21,1.26),(4.05,1.21,1.26),(3.03,1.2,.89)],
'A08':[(1.43,2.65,1.15),(1.43,2.65,2.28),(1.43,2.65,1.38),(3.03,2.64,.73)],
'A09':[(2.8,-3.06,1.11),(2.8,-3.06,1.19),(4.1,-3.06,1.49),(3.35,-3.69,.97)]}
for a in C['assets']:
 for an,loc in zip(a['anchors'],locs[a['asset_id']]):
  o=bpy.data.objects.new(an['object_name'],None);scene.collection.objects.link(o);o.location=loc;o.empty_display_type='PLAIN_AXES';o.empty_display_size=.10;own(o,a['asset_id']);o['anchor_id']=an['anchor_id'];o['mode']='evidence_only';o['qualified']=False
# Convert authored font curves to mesh for native/GLB consistency; retain complete labels in custom fields.
for o in list(bpy.data.objects):
 if o.type=='FONT':
  o['label_text']=o.data.body;bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
# Cameras and real CPU render settings.
def camera(n,loc,target,ortho):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=ortho;return o
cams=[camera('CAM_overview',(10,-15,13),(0,.0,1.22),15.7),camera('CAM_targets',(3.0,-9.0,9.4),(.55,-1.73,1.1),9.1),camera('CAM_services',(8,-12,8.0),(.1,1.68,1.37),10.2)]
world=bpy.data.worlds.new('Soft studio');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.63,.73,.79,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.32
for n,loc,power,size in [('Key',(-3,-6,10),1800,7),('Fill',(6,-2,7),1100,6),('Rim',(-3,5,8),1700,5)]:
 d=bpy.data.lights.new(n,'AREA');o=bpy.data.objects.new(n,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler();d.energy=power;d.shape='DISK';d.size=size
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=128;scene.cycles.use_denoising=False;scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False;scene.view_settings.view_transform='AgX';scene.camera=cams[0]
scene.render.filepath='//../previews/preview_01_overview.png';scene.render.use_stamp=False
bpy.context.view_layer.update()
manifest={'schema':'sciencegym.microsphere.scene.v1','source_doi':C['source_doi'],'scene_name':scene.name,'physical_actuation_enabled':False,'scientific_simulation_performed':False,'unit':'meter','objects':[],'static_support_contacts':contacts,'scale_boundary':'Actual-size context objects are in SOURCE_SCALE; illustrations in SCHEMATIC_ENLARGEMENTS. Neither is qualified experimental CAD or data.'}
for o in sorted(bpy.data.objects,key=lambda x:x.name):
 manifest['objects'].append({'name':o.name,'type':o.type,'asset_id':o.get('asset_id'),'anchor_id':o.get('anchor_id'),'parent':o.parent.name if o.parent else None,'location_m':list(o.matrix_world.translation),'dimensions_m':list(o.dimensions),'representation_class':o.get('representation_class'),'label_text':o.get('label_text'),'custom':{k:o[k] for k in ['reported_diameter_um','reported_diameter_mm','illustration_magnification','dimensions_status'] if k in o}})
(P/'scene_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'geometry/microsphere_lab.raw.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(P/'geometry/microsphere_lab.glb'),export_format='GLB',export_extras=True,export_cameras=True,export_lights=False)
receipt={'schema':'sciencegym.cpu_render_receipt.v1','engine':'CYCLES','device':'CPU','samples':128,'source':'procedural original geometry; no publisher images','renders':[]}
for cam,name in zip(cams,['preview_01_overview.png','preview_02_targets.png','preview_03_services.png']):
 scene.camera=cam;scene.render.filepath=str(P/'previews'/name);start=time.time();bpy.ops.render.render(write_still=True);receipt['renders'].append({'file':'previews/'+name,'camera':cam.name,'seconds':round(time.time()-start,3),'width':1600,'height':1000,'interpretation':'Illustrative scene render, not microscope acquisition or measurement'})
(P/'review/render_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('SCENE_BUILD_COMPLETE')
