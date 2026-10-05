"""Original procedural static review scene. Apache-2.0. No physics or hardware control."""
import bpy, math, json, pathlib, time
from mathutils import Vector
P=pathlib.Path(__file__).resolve().parents[1]
C=json.loads((P/'scene_binding_contract.json').read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.materials):bpy.data.materials.remove(d)
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
s['paper_id']=C['paper_id'];s['source_doi']=C['source_doi'];s['physical_actuation_enabled']=False;s['physics_simulation_performed']=False;s['geometry_interface_qualified']=False
s['scope']='Original illustrative service-boundary assets; no measured data or scientific solver'
s['profile_number_mapping']='Authored visual selector pairing, not source-verified X/Y numbering'
M={}
def mat(n,c,metal=0,rough=.4,trans=0):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough
 if trans:
  nt=m.node_tree;nt.nodes.clear();o=nt.nodes.new('ShaderNodeOutputMaterial');mix=nt.nodes.new('ShaderNodeMixShader');tr=nt.nodes.new('ShaderNodeBsdfTransparent');pb=nt.nodes.new('ShaderNodeBsdfPrincipled');pb.inputs['Base Color'].default_value=(.7,.86,.92,1);pb.inputs['Roughness'].default_value=.22;mix.inputs[0].default_value=.07;nt.links.new(tr.outputs[0],mix.inputs[1]);nt.links.new(pb.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],o.inputs[0]);m['illustrative_panel_shader']=True
 M[n]=m
for a in [('ink',(.018,.043,.068)),('navy',(.035,.09,.14)),('floor',(.64,.71,.74)),('white',(.87,.91,.92)),('pale',(.61,.76,.78)),('metal',(.35,.47,.52),.7),('teal',(.03,.54,.53)),('violet',(.43,.29,.64)),('coral',(.83,.29,.23)),('gold',(.8,.56,.2),.55),('amber',(.98,.62,.1)),('red',(.62,.12,.19)),('black',(.018,.021,.025)),('glass',(.88,.96,.99),0,.06,.95)]:mat(*a)
roots={}
def root(n,aid=None):
 o=bpy.data.objects.new(n,None);s.collection.objects.link(o);o['physical_actuation_enabled']=False
 if aid:o.parent=roots[aid];o['asset_id']=aid
 roots[n]=o;return o
for a in C['assets']:
 o=root(a['asset_id']);o['asset_id']=a['asset_id'];o['geometry_status']='original_illustrative_unqualified';o['stage_ids']=','.join(a['stage_ids'])
def own(o,g):
 if g:o.parent=roots[g];o['asset_id']=g if g.startswith('A') else 'A02'
 o['physical_actuation_enabled']=False;return o
def box(n,loc,dim,m='white',g=None,bev=.007):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(M[m]);own(o,g)
 if bev:
  b=o.modifiers.new('Rounded illustrative edges','BEVEL');b.width=min(bev,min(dim)/4);b.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=b.name)
 return o
def cyl(n,loc,r,d,m='metal',g=None,vertices=32):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=d,location=loc);o=bpy.context.object;o.name=n;o.data.materials.append(M[m]);own(o,g)
 for f in o.data.polygons:f.use_smooth=True
 return o
def line(n,a,b,r=.007,m='metal',g=None):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,g,16);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def text(n,t,p,size=.06,m='white',g=None,flat=False,align='LEFT'):
 cu=bpy.data.curves.new(n,'FONT');cu.body=t;cu.size=size;cu.extrude=.00012;cu.resolution_u=2;cu.align_x=align
 o=bpy.data.objects.new(n,cu);s.collection.objects.link(o);o.location=p
 if not flat:o.rotation_euler=(math.pi/2,0,0)
 o.data.materials.append(M[m]);own(o,g);return o
def plaque(n,title,sub,p,w,g,m='teal',h=.22):
 x,y,z=p;box(n+'_panel',p,(w,.035,h),'navy',g)
 box(n+'_accent',(x-w/2+.023,y-.02,z),(.015,.007,h*.8),m,g,.002)
 text(n+'_title',title,(x-w/2+.048,y-.022,z+.025),min(.053,w/max(len(title),1)*1.4),'white',g)
 text(n+'_sub',sub,(x-w/2+.048,y-.023,z-.055),min(.032,w/max(len(sub),1)*1.4),'amber' if m=='amber' else 'pale',g)
def bench(n,x,y,w,d,g,top=.86):
 box(n+'_top',(x,y,top-.035),(w,d,.07),'white',g)
 for dx in [-w/2+.06,w/2-.06]:
  for dy in [-d/2+.06,d/2-.06]:box(n+'_leg',(x+dx,y+dy,(top-.07)/2),(.055,.055,top-.07),'metal',g)
 box(n+'_shelf',(x,y,.24),(w-.06,d-.06,.045),'navy',g)
def screen(n,x,y,z,w,h,g,rows):
 box(n+'_body',(x,y,z),(w,.065,h),'navy',g)
 for i,(t,col) in enumerate(rows):text(n+'_row'+str(i),t,(x-w/2+.04,y-.036,z+h/2-.09-i*.081),.039,col,g)
def arrow(n,x,y,z,angle,g,m):
 # Static orientation reference only: no telemetry or simulated flux.
 u=Vector((math.cos(angle),math.sin(angle),0));v=Vector((-u.y,u.x,0));a=Vector((x,y,z))-u*.043;b=Vector((x,y,z))+u*.043
 line(n+'_shaft',a,b,.0015,m,g)
 for sign in [-1,1]:line(n+'_head',b,b-u*.017+sign*v*.009,.0015,m,g)
# architectural setting
box('environment.floor',(0,.25,-.07),(5.85,4.9,.14),'floor',bev=.03)
box('environment.backdrop',(0,2.58,1.2),(5.85,.10,2.54),'pale')
text('title','THERMAL META-DEVICES',(-2.55,2.515,2.20),.16,'ink')
text('subtitle','ORIGINAL STATIC SCENE / QUALIFICATION HELD',(-2.53,2.512,1.98),.066,'navy')
text('front_rule','ILLUSTRATIVE GEOMETRY  /  NO HARDWARE CONTROL  /  NO THERMAL DATA',(-2.60,-2.01,.009),.075,'ink',flat=True)
# A01 review terminal and held planning tokens
bench('A01.review_bench',-1.73,.65,1.35,.64,'A01')
box('A01.monitor_foot',(-1.80,.76,.875),(.32,.22,.03),'navy','A01');line('A01.monitor_stem',(-1.8,.82,.89),(-1.8,.82,1.06),.024,'metal','A01')
screen('A01.review',-1.8,.85,1.25,1.02,.42,'A01',[('DOI 10.1038/s41467-024-49630-1','white'),('SOURCE REVIEW ACCEPTED','pale'),('DESIGN + FIT: UNQUALIFIED','amber'),('P01 / P02 / P03','white')])
for i,t in enumerate(['PLAN','DESIGN','HOLDS']):
 box('A01.token_'+t,(-2.05+i*.26,.48,.877),(.22,.19,.025),'teal' if i<2 else 'amber','A01')
 text('A01.token_text_'+t,t,(-2.14+i*.26,.445,.892),.033,'ink','A01',True)
plaque('A01.label','01 / SOURCE + PLAN','READ-ONLY REVIEW',(-1.73,.306,.69),1.3,'A01')
# A03 manufacturing/casting opaque boundary
box('A03.sealed_enclosure',(-2.08,1.93,.89),(1.1,.65,1.78),'white','A03',.03)
box('A03.closed_front',(-2.08,1.582,.93),(.94,.025,1.4),'navy','A03')
plaque('A03.label','03 / FABRICATION SERVICE','CLOSED QUALIFIED PROVIDER',(-2.08,1.553,1.59),1.08,'A03','amber')
text('A03.disabled','NO PROCESS CONTROLS',(-2.46,1.561,1.25),.045,'amber','A03')
text('A03.no_recipe','NO RECIPE / NO ACTUATION',(-2.46,1.56,1.13),.039,'white','A03')
for i,t in enumerate(['LATTICE','FILLED','FINAL']):
 x=-2.36+i*.28;box('A03.receipt_'+t,(x,1.54,.91),(.245,.07,.15),'teal','A03');text('A03.receipt_text_'+t,t,(x-.10,1.50,.895),.030,'white','A03')
box('A03.custody_slot',(-2.08,1.54,.58),(.62,.07,.11),'black','A03');text('A03.port','RECEIPTS ONLY',(-2.32,1.494,.565),.039,'pale','A03')
# A02 six views of three symbolic identities, source envelope at nominal scale
bench('A02.condition_display',0,-.49,1.12,.83,'A02')
plaque('A02.label','02 / THREE FAMILIES x X / Y','SIX VIEW STATES, NOT SIX INDEPENDENT SPECIMENS',(0,-.928,.68),1.55,'A02',h=.24)
contacts=[]
for c in C['condition_views']:
 n=c['condition_id'];root(n,'A02');roots[n]['condition_id']=n;roots[n]['specimen_id']=c['specimen_id'];roots[n]['geometry_status']='original_semantic_proxy'
 x,y,z=c['position_m'];family=c['sample_family_id'];color={'CLOAK':'teal','ROTATOR45':'violet','CONCENTRATOR18':'coral'}[family]
 base=box(n+'.protected_carrier',(x,y,.86875),(.198,.232,.0175),'navy',n,.004)
 pad=box(n+'.support_pad',(x,y,.879125),(.122,.122,.00325),'pale',n,0)
 plate=box(n+'.source_envelope',(x,y,z),(.12,.12,.0045),'white',n,0);plate['source_nominal_mm']='120 x 120 x 4.5';plate['qualified_geometry']=False;plate['specimen_id']=c['specimen_id']
 # Authored geometric silhouettes: deliberately coarse symbols, not source lattice/CAD.
 N=96;pts=[]
 for i in range(N):
  a=2*math.pi*i/N
  if family=='CLOAK':r=.038*(1+.20*math.cos(6*a));px=r*math.cos(a);py=r*math.sin(a)
  elif family=='ROTATOR45':r=.036*(1+.25*math.cos(4*(a-.16)));px=r*math.cos(a);py=r*math.sin(a)
  else:px=.0027*16*math.sin(a)**3;py=.0027*(13*math.cos(a)-5*math.cos(2*a)-2*math.cos(3*a)-math.cos(4*a))
  ang=math.radians(c['rotation_deg']);px,py=px*math.cos(ang)-py*math.sin(ang),px*math.sin(ang)+py*math.cos(ang)
  pts.append((x+px,y+py,z+.00265))
 me=bpy.data.meshes.new(n+'.symbol_mesh');me.from_pydata(pts,[],[tuple(range(N))]);me.materials.append(M[color]);ob=bpy.data.objects.new(n+'.family_symbol',me);s.collection.objects.link(ob);own(ob,n);ob['geometry']='independently_authored_semantic_outline_not_source_CAD'
 # Three decorative inset contour paths. They do not encode thermal performance.
 for j,scale in enumerate([.62,.77,.91]):
  q=[(x+(p[0]-x)*scale,y+(p[1]-y)*scale,p[2]+.0004) for p in pts]
  for k in range(0,N,2):line(n+'.symbol_contour_'+str(j)+'_'+str(k),q[k],q[(k+2)%N],.00060,'gold',n)
 core=cyl(n+'.core_symbol',(x,y,z+.0031),.011,.0006,'pale' if family!='CLOAK' else 'navy',n,32);core['core_material_reference']='PDMS' if family=='CLOAK' else 'background_encapsulant'
 # Enclosed carrier rim and clear lid. Empty gap is intentional protective clearance.
 for dx in [-.09,.09]:box(n+'.rim',(x+dx,y,.892),(.007,.222,.031),'metal',n,.001)
 for dy in [-.1075,.1075]:box(n+'.rim',(x,y+dy,.892),(.187,.007,.031),'metal',n,.001)
 cover=box(n+'.closed_clear_cover',(x,y,.909),(.182,.21,.003),'glass',n,.0006)
 for dx in [-.11,.11]:box(n+'.handle',(x+dx,y,.87),(.025,.075,.015),color,n,.002)
 text(n+'.family_label',{'CLOAK':'CLOAK','ROTATOR45':'ROTATOR 45','CONCENTRATOR18':'CONCENTRATOR 1.8'}[family],(x-.084,y+.074,.879),.0102,'white',n,True)
 text(n+'.condition_label',c['orientation']+' / '+c['profile_id']+'  |  VIEW ONLY',(x-.079,y-.093,.879),.012,'white',n,True)
 # Data-independent direction arrows and registered-profile selector at left/right margins.
 ang=0 if c['orientation']=='X' else math.pi/2
 arrow(n+'.orientation',x,y,.917,ang,n,color)
 pang=ang+(math.pi/2 if family=='ROTATOR45' else 0);u=Vector((math.cos(pang),math.sin(pang),0));center=Vector((x,y,.916))
 for k in range(5):
  a=center+u*(-.046+k*.020);b=a+u*.010;line(n+'.profile_selector' if k==0 else n+'.profile_dash_'+str(k),a,b,.0007,'black',n)
 contacts.append({'supported_object':plate.name,'support_object':pad.name,'contact_type':'authored_static_vertical_support','expected_vertical_gap_m':0,'tolerance_m':1e-6,'physical_fit_qualified':False})
# A04 metrology empty supported cradle / measurement gantry
bench('A04.inspection_bench',-1.7,-.71,1.12,.72,'A04')
box('A04.cradle_base',(-1.7,-.70,.88),(.31,.27,.04),'navy','A04')
for dx in [-.079,.079]:box('A04.support_contact',(-1.7+dx,-.70,.908),(.025,.17,.016),'teal','A04',.002)
box('A04.empty_recess',(-1.7,-.70,.903),(.12,.12,.006),'pale','A04',0)
for dx in [-.23,.23]:box('A04.gantry_leg',(-1.7+dx,-.66,1.08),(.035,.055,.44),'metal','A04')
box('A04.gantry_bar',(-1.7,-.66,1.29),(.50,.06,.04),'metal','A04')
box('A04.inspection_camera',(-1.7,-.66,1.22),(.095,.09,.08),'navy','A04');cyl('A04.camera_lens',(-1.7,-.66,1.167),.027,.028,'black','A04')
box('A04.ruler',(-1.7,-.92,.879),(.32,.035,.012),'metal','A04')
for i in range(13):box('A04.ruler_mark_'+str(i),(-1.82+i*.02,-.92,.886),(.001,.021 if i%3==0 else .012,.001),'ink','A04',0)
plaque('A04.label','04 / DRY INSPECTION','FIT / FORCE / TOLERANCE HELD',(-1.7,-1.095,.69),1.13,'A04')
# A05 calibration service / target not qualified
bench('A05.calibration_bench',-.28,1.71,1.24,.71,'A05')
box('A05.target_foot',(-.48,1.66,.88),(.24,.20,.04),'metal','A05');line('A05.target_post',(-.48,1.67,.90),(-.48,1.67,1.15),.015,'metal','A05')
box('A05.reference_target',(-.48,1.65,1.19),(.17,.028,.17),'black','A05')
box('A05.reference_frame',(-.48,1.67,1.19),(.20,.026,.20),'metal','A05')
text('A05.no_epsilon','EMISSIVITY: UNKNOWN',(-.83,1.475,.915),.033,'ink','A05')
screen('A05.cert',.05,1.74,1.17,.48,.43,'A05',[('IR CALIBRATION','white'),('REFERENCE ID: HOLD','amber'),('CERTIFICATE: NONE','pale'),('NO ARBITRARY VALUE','white')])
for i,t in enumerate(['HOMOGENEOUS','BARE CONTROL']):
 box('A05.control_token'+str(i),(-.63+i*.41,1.45,.886),(.36,.14,.022),'teal','A05');text('A05.control_label'+str(i),t,(-.79+i*.41,1.42,.899),.027,'white','A05',True)
plaque('A05.label','05 / IR CALIBRATION + CONTROLS','AUTHORED CONTROL PLAN / QUALIFICATION HELD',(-.28,1.33,.66),1.5,'A05')
# A06 closed thermal-service enclosure, transparent inspection wall and noninteractive contents
bench('A06.thermal_bench',1.85,.72,1.30,1.12,'A06')
box('A06.guard_floor',(1.85,.80,.9),(1.16,.89,.075),'navy','A06')
box('A06.guard_back',(1.85,1.26,1.30),(1.16,.045,.8),'white','A06')
for dx in [-.565,.565]:box('A06.guard_side',(1.85+dx,.80,1.30),(.035,.9,.8),'pale','A06')
box('A06.closed_glass_front',(1.85,.33,1.30),(1.12,.020,.8),'glass','A06')
box('A06.closed_lid',(1.85,.80,1.72),(1.21,.97,.045),'glass','A06')
for dx in [-.57,.57]:
 for dy in [-.46,.46]:box('A06.guard_post',(1.85+dx,.80+dy,1.30),(.035,.035,.84),'metal','A06')
# Empty slotted fixture and source/sink proxies use neutral colors, no heat-map gradients.
box('A06.fixture_support',(1.85,.73,1.00),(.40,.28,.1),'metal','A06')
for dx in [-.078,.078]:
 box('A06.slot_rail',(1.85+dx,.73,1.073),(.023,.18,.045),'navy','A06')
 box('A06.boundary_plate',(1.85+dx,.73,1.12),(.031,.19,.07),'metal','A06')
for dy in [-.11,.11]:box('A06.side_foam',(1.85,.73+dy,1.10),(.17,.027,.07),'black','A06')
box('A06.closed_bath',(2.12,1.06,1.06),(.37,.29,.22),'white','A06');box('A06.bath_lid',(2.12,1.06,1.185),(.39,.31,.03),'navy','A06')
box('A06.disabled_source',(1.53,1.03,1.08),(.28,.29,.23),'white','A06');text('A06.source_no_control','SERVICE', (1.412,.874,1.11),.029,'ink','A06')
# IR camera fully outside the protected volume
box('A06.ir_camera_base',(1.43,1.51,.89),(.24,.20,.06),'navy','A06');line('A06.ir_camera_post',(1.43,1.51,.92),(1.43,1.51,1.93),.024,'metal','A06')
box('A06.ir_camera',(1.43,1.40,1.95),(.20,.25,.15),'navy','A06');line('A06.ir_camera_lens',(1.43,1.27,1.95),(1.50,1.19,1.89),.050,'black','A06')
plaque('A06.label','06 / GUARDED THERMAL SERVICE','CLOSED / NO HEATING / NO ACTUATION',(1.85,.287,1.55),1.19,'A06','amber',.20)
screen('A06.evidence',2.47,.20,1.02,.47,.58,'A06',[('STATE: HOLD','amber'),('DATA: NONE','white'),('STABILITY: NONE','white'),('RELEASE: NONE','amber'),('45 min != SAFE','pale')])
box('A06.handoff_pad',(1.49,.07,.885),(.27,.20,.05),'teal','A06');text('A06.handoff_label','SAFE HANDOFF', (1.375,.025,.914),.025,'white','A06',True)
# A07 original registration key: static coordinate relationships
box('A07.registration_board',(0,-.02,1.10),(1.13,.04,.39),'navy','A07')
text('A07.heading','07 / ORIENTATION + PROFILES',(-.51,-.046,1.22),.044,'white','A07')
text('A07.profiles','K1/K2 + C1/C2: ALONG DIRECTION',(-.51,-.046,1.12),.038,'pale','A07')
text('A07.rotator','R1/R2: TRANSVERSE TO DIRECTION',(-.51,-.046,1.04),.036,'pale','A07')
text('A07.no_data','ARROWS ARE LABELS / NOT HEAT FLOW',(-.51,-.046,.96),.034,'amber','A07')
text('A07.profile_mapping_caution','NUMBER PAIRING: AUTHORED / NOT SOURCE-VERIFIED',(-.51,-.046,.917),.025,'amber','A07')
# A08 analysis screen: raw / source / synthetic channels explicit, no charts
bench('A08.analysis_bench',.84,2.03,1.14,.53,'A08')
screen('A08.analysis',.84,2.10,1.28,1.10,.72,'A08',[('08 / DATA + ANALYSIS','white'),('MEASURED / SIMULATED: NONE / UNRUN','pale'),('METRIC NORM / SQUARED RATIO: HOLD','amber'),('MAPPING INDEX + FEATURE LABEL: HOLD','amber'),('ABSOLUTE FLUX / PHYSICAL UNITS: HOLD','amber'),('SOURCE OUTCOMES != TARGETS','white'),('NUMERICAL BRANCHES: NOT EXECUTED','pale')])
# A09 storage, service-return and quarantine are visually distinct
bench('A09.closeout',1.8,-1.11,1.45,.62,'A09')
for i,(t,col) in enumerate([('STORAGE','teal'),('RETURN','violet'),('QUARANTINE','red')]):
 x=1.31+i*.49;box('A09.'+t+'_bin',(x,-1.1,.98),(.44,.42,.24),'white','A09');box('A09.'+t+'_lid',(x,-1.1,1.112),(.46,.44,.035),col,'A09');text('A09.'+t+'_label',t,(x-.20,-1.324,1.015),.038,'ink','A09');text('A09.'+t+'_hold','CUSTODY HELD',(x-.185,-1.324,.93),.030,'ink','A09')
plaque('A09.label','09 / SAFE CLOSEOUT','NO RELEASE INFERRED FROM STOP OR TIME',(1.8,-1.45,.66),1.49,'A09','amber')
# A10 parked robot surrogate only; no motion data, load limits, IK or end effector control
cyl('A10.robot_base',(-.64,-1.53,.09),.23,.18,'navy','A10')
cyl('A10.robot_column',(-.64,-1.53,.39),.09,.42,'metal','A10')
for i,(a,b) in enumerate([((-.64,-1.53,.62),(-.64,-1.50,1.02)),((-.64,-1.50,1.02),(-.29,-1.47,1.13)),((-.29,-1.47,1.13),(-.04,-1.47,.98))]):
 line('A10.parked_link_'+str(i),a,b,.052,'white','A10');cyl('A10.joint_'+str(i),a,.078,.10,'teal','A10')
box('A10.parked_wrist',(-.04,-1.47,.96),(.13,.11,.1),'navy','A10')
for dx in [-.075,.075]:box('A10.protected_gripper_pad',(-.04+dx,-1.47,.865),(.035,.11,.09),'teal','A10')
box('A10.parking_support',(-.04,-1.47,.71),(.35,.24,.07),'metal','A10');box('A10.parking_column',(-.04,-1.47,.3375),(.09,.09,.675),'metal','A10')
plaque('A10.label','10 / PARKED HANDLER','NO TRAJECTORY / CARRIER CONTACTS ONLY',(-.38,-1.85,.42),1.27,'A10','amber')
# Identity/evidence tokens contain no people, credentials or signatures.
for i,t in enumerate(['ID','REV','RUN','HASH']):
 box('A10.lineage_token_'+t,(.28+i*.145,-1.19,.07),(.12,.16,.04),'navy','A10');text('A10.lineage_text_'+t,t,(.236+i*.145,-1.225,.092),.032,'white','A10',True)

# Explicit support geometry; no physical fit or structural qualification.
specs=[
 ('A05.cert_foot',(.05,1.74,.865),(.22,.17,.01),'metal','A05'),
 ('A05.cert_stem',(.05,1.74,.9125),(.045,.045,.085),'metal','A05'),
 ('A07.left_foot',(-.47,-.02,.01),(.16,.20,.02),'navy','A07'),
 ('A07.right_foot',(.47,-.02,.01),(.16,.20,.02),'navy','A07'),
 ('A07.left_post',(-.47,-.02,.4625),(.035,.035,.885),'metal','A07'),
 ('A07.right_post',(.47,-.02,.4625),(.035,.035,.885),'metal','A07'),
 ('A08.analysis_foot',(.84,2.10,.87),(.30,.18,.02),'metal','A08'),
 ('A08.analysis_stem',(.84,2.10,.90),(.05,.05,.04),'metal','A08'),
 ('A10.lineage_rack',(.4975,-1.19,.025),(.62,.21,.05),'metal','A10'),
 ('A06.ir_camera_pedestal',(1.43,1.51,.43),(.10,.10,.86),'metal','A06'),
 ('A06.handoff_pedestal',(1.49,.07,.43),(.10,.10,.86),'metal','A06'),
 ('A06.fixture_foot',(1.85,.73,.94375),(.30,.22,.0125),'metal','A06'),
 ('A06.bath_foot',(2.12,1.06,.94375),(.28,.22,.0125),'metal','A06'),
 ('A06.source_foot',(1.53,1.03,.95125),(.23,.24,.0275),'metal','A06'),
 ('A06.foam_support_front',(1.85,.62,1.0575),(.17,.027,.015),'metal','A06'),
 ('A06.foam_support_back',(1.85,.84,1.0575),(.17,.027,.015),'metal','A06')]
for n,loc,dim,m,g in specs:box(n,loc,dim,m,g,bev=0)
for n in ['A06.slot_rail','A06.slot_rail.001']:bpy.data.objects[n].location.z=1.0725
pairs=[('A05.cert_body','A05.cert_stem'),('A07.registration_board','A07.left_post'),('A08.analysis_body','A08.analysis_stem'),('A06.ir_camera_base','A06.ir_camera_pedestal'),('A06.handoff_pad','A06.handoff_pedestal'),('A06.fixture_support','A06.fixture_foot'),('A06.closed_bath','A06.bath_foot'),('A06.disabled_source','A06.source_foot'),('A06.slot_rail','A06.fixture_support'),('A06.slot_rail.001','A06.fixture_support')]+[('A10.lineage_token_'+k,'A10.lineage_rack') for k in ['ID','REV','RUN','HASH']]
for a,b in pairs:contacts.append({'supported_object':a,'support_object':b,'contact_type':'authored_static_vertical_support','expected_vertical_gap_m':0,'tolerance_m':1e-6,'physical_fit_qualified':False})
# Canonical empty anchors remain in Blender and GLB. They are evidence reference positions only.
for a in C['anchors']:
 o=bpy.data.objects.new(a['object_name'],None);s.collection.objects.link(o);o.location=a['position_m'];o.empty_display_type='PLAIN_AXES';o.empty_display_size=.045;own(o,a['asset_id']);o['anchor_id']=a['anchor_id'];o['mode']='static_evidence_only';o['qualified']=False
# cameras and soft studio illumination
world=s.world or bpy.data.worlds.new('World');s.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.58,.68,.75,1);world.node_tree.nodes['Background'].inputs[1].default_value=.38
for n,p,power,size in [('key',(1,-3,6),1000,5),('fill',(-4,-1,3),650,4),('rim',(1,4,4),850,3)]:
 ld=bpy.data.lights.new(n,'AREA');lo=bpy.data.objects.new(n,ld);s.collection.objects.link(lo);lo.location=p;ld.energy=power;ld.shape='DISK';ld.size=size;lo.rotation_euler=(Vector((0,.3,.6))-lo.location).to_track_quat('-Z','Y').to_euler()
def cam(n,p,target,ortho):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);s.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=ortho;d.lens=45;d.clip_start=.005;return o
cams=[('preview_01_overview',cam('camera_overview',(6,-9,6.5),(0,.3,1.05),8.25)),('preview_02_condition_views',cam('camera_conditions',(0,-.9,2.9),(0,-.48,.885),.91)),('preview_03_guarded_services',cam('camera_services',(4.8,-4.5,4.1),(1.4,.70,1.1),3.6))]
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=128;s.cycles.use_denoising=False;s.render.resolution_x=1600;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.film_transparent=False;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-.4;s.render.use_file_extension=True;s.camera=cams[0][1]
s.render.filepath='//../previews/preview_01_overview.png';s.render.image_settings.color_mode='RGB';s.render.use_stamp=False
# Exact source dimensions/contact audit before save.
bpy.context.view_layer.update()
manifest={'schema':'sciencegym3d.thermalmeta.scene.v1','source_doi':C['source_doi'],'asset_package':C['asset_package'],'physical_actuation_enabled':False,'physics_simulation_performed':False,'coordinate_system':C['coordinate_system'],'objects':[],'contacts':contacts,'render_engine':'CYCLES','render_device':'CPU'}
for o in s.objects:
 manifest['objects'].append({'name':o.name,'type':o.type,'asset_id':o.get('asset_id'),'anchor_id':o.get('anchor_id'),'parent':o.parent.name if o.parent else None,'location_m':[round(v,8) for v in o.matrix_world.translation],'dimensions_m':[round(v,8) for v in o.dimensions]})
(P/'scene_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(P/'contact_contract.json').write_text(json.dumps({'status':'authored_static_support_only','contacts':contacts,'fit_or_force_qualified':False},indent=2)+'\n')
# Save editable text and curves natively compressed. No external textures.
bpy.ops.wm.save_as_mainfile(filepath=str(P/'geometry/thermalmeta_lab.blend'),compress=True)
import subprocess, hashlib
subprocess.run(['python3',str(P/'geometry/sanitize_native_buffers.py')],check=True)
# Font geometry must exist in portable GLB. Convert only an export copy, then reopen native.
bpy.ops.object.select_all(action='DESELECT')
for o in list(s.objects):
 if o.type=='FONT':o.select_set(True)
if bpy.context.selected_objects:
 bpy.context.view_layer.objects.active=bpy.context.selected_objects[0];bpy.ops.object.convert(target='MESH')
bpy.ops.export_scene.gltf(filepath=str(P/'geometry/thermalmeta_lab.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False,export_yup=True)
import runpy
runpy.run_path(str(P/'geometry/normalize_glb_panels.py'))
bpy.ops.wm.open_mainfile(filepath=str(P/'geometry/thermalmeta_lab.blend'))
s=bpy.context.scene;receipts=[]
native_hash=hashlib.sha256((P/'geometry/thermalmeta_lab.blend').read_bytes()).hexdigest()
for filename,cam_name in [('preview_01_overview','camera_overview'),('preview_02_condition_views','camera_conditions'),('preview_03_guarded_services','camera_services')]:
 s.camera=bpy.data.objects[cam_name];s.render.filepath=str(P/'previews'/(filename+'.png'));start=time.time();bpy.ops.render.render(write_still=True)
 receipts.append({'file':'previews/'+filename+'.png','engine':s.render.engine,'device':s.cycles.device,'samples':s.cycles.samples,'resolution':[s.render.resolution_x,s.render.resolution_y],'seconds':round(time.time()-start,3),'genuine_blender_cpu_render':True,'camera':s.camera.name,'native_scene_sha256':native_hash})
(P/'review/render_receipt.json').write_text(json.dumps(receipts,indent=2)+'\n')
print('THERMALMETA_BUILD_COMPLETE',len(manifest['objects']))
