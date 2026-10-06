"""Original static frictional-fluid review geometry. No fluid solver or device controls.
SPDX-License-Identifier: Apache-2.0
"""
import bpy, math, json, pathlib, time, sys
from mathutils import Vector
P=pathlib.Path(__file__).resolve().parents[1]
if (P/'scene_core_manifest.json').exists():raise RuntimeError('Sealed package: build a new revision')
for folder in ['geometry','previews','review']:
 if any(x.is_symlink() for x in [P/folder,*(P/folder).parents]):raise ValueError('Symlinked build directory or ancestor')
for name in ['geometry/frictional_lab.raw.blend','geometry/frictional_lab.glb','scene_manifest.json','review/render_receipt.json','previews/preview_01_overview.png','previews/preview_02_closed_service.png','previews/preview_03_evidence.png']:
 if (P/name).is_symlink():raise ValueError('Symlinked build output')
C=json.loads((P/'shared_binding_contract.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.name='Frictional fluid / static review';scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene['source_doi']='10.1038/ncomms1289';scene['physical_actuation_enabled']=False;scene['scientific_simulation_performed']=False
scene['default_state']='HOLD_QUALIFICATION';scene['qualification_holds']=20;scene['no_measurements_generated']=True
M={}
def material(n,c,metal=0,rough=.42):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough;M[n]=m
for a in [('ink',(.018,.038,.055)),('floor',(.25,.37,.41)),('white',(.87,.92,.89)),('steel',(.28,.44,.48),.65),('teal',(.012,.38,.39)),('cyan',(.21,.81,.79)),('amber',(.97,.54,.15)),('violet',(.45,.34,.69)),('red',(.78,.21,.23)),('pale',(.66,.79,.79)),('glass',(.24,.58,.64),.2),('granular',(.76,.61,.37))]:material(*a)
# The closed front guard is transparent for review visibility only, with no door or actuated opening.
m=bpy.data.materials.new('closed_guard');m.use_nodes=True;m.diffuse_color=(.45,.8,.85,.08);m.surface_render_method='DITHERED';pr=m.node_tree.nodes.get('Principled BSDF');pr.inputs['Base Color'].default_value=(.45,.8,.85,1);pr.inputs['Roughness'].default_value=.18;pr.inputs['Alpha'].default_value=.08;M['guard']=m
collections={};roots={};contacts=[]
for n in ['LAB_REVIEW','SOURCE_SCALE','SCHEMATIC_TOKENS','EVIDENCE_ANCHORS']:
 c=bpy.data.collections.new(n);scene.collection.children.link(c);collections[n]=c
for i in range(1,9):
 g=f'A{i:02d}';o=bpy.data.objects.new(g,None);collections['LAB_REVIEW'].objects.link(o);o['asset_id']=g;o['physical_actuation_enabled']=False;roots[g]=o

def own(o,g=None,collection='LAB_REVIEW'):
 for c in list(o.users_collection):c.objects.unlink(o)
 collections[collection].objects.link(o)
 if g:o.parent=roots[g];o['asset_id']=g
 o['physical_actuation_enabled']=False;o['representation_class']=collection;o['geometry_status']='source_dimension_context_unqualified' if collection=='SOURCE_SCALE' else 'original_static_illustration_unqualified'
 return o

def box(n,loc,dim,m='white',g=None,bevel=.012,collection='LAB_REVIEW'):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(M[m]);own(o,g,collection)
 if bevel:
  b=o.modifiers.new('Original edge rounding','BEVEL');b.width=min(bevel,min(dim)/4);b.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=b.name)
 return o

def cyl(n,loc,r,d,m='steel',g=None,verts=32,collection='LAB_REVIEW'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc);o=bpy.context.object;o.name=n;o.data.materials.append(M[m]);own(o,g,collection)
 for f in o.data.polygons:f.use_smooth=True
 return o

def line(n,a,b,r=.012,m='cyan',g=None,collection='LAB_REVIEW'):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,g,16,collection);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def txt(n,s,loc,size=.09,m='ink',g=None,flat=False,collection='LAB_REVIEW'):
 cu=bpy.data.curves.new(n,'FONT');cu.body=s;cu.size=size;cu.extrude=.0002;cu.resolution_u=2;o=bpy.data.objects.new(n,cu);scene.collection.objects.link(o);o.location=loc
 if not flat:o.rotation_euler=(math.pi/2,0,0)
 o.data.materials.append(M[m]);return own(o,g,collection)

def contact(a,b):contacts.append({'supported_object':a,'support_object':b,'axis':'Z','expected_gap_m':0,'tolerance_m':2e-6,'scope':'static visual support only, not qualified robot collision/contact'})
def bench(st,x,y,g):
 n=st+'.bench';box(n+'.top',(x,y,.80),(2.13,1.48,.10),'white',g)
 for dx in [-.94,.94]:
  for dy in [-.61,.61]:box(n+'.leg',(x+dx,y+dy,.375),(.075,.075,.75),'steel',g)
 box(n+'.shelf',(x,y,.23),(1.95,1.30,.06),'teal',g)
 return n+'.top'
def plaque(n,title,sub,x,y,z,w,g,color='cyan'):
 box(n+'.back',(x,y,z),(w,.034,.29),'ink',g)
 txt(n+'.title',title,(x-w/2+.075,y-.020,z+.035),.082,'white',g)
 txt(n+'.sub',sub,(x-w/2+.075,y-.020,z-.086),.048,color,g)
def dock(n,x,y,g):
 box(n+'.base',(x,y,.9075),(.55,.49,.115),'steel',g);contact(n+'.base',{'A01':'ST01','A02':'ST01','A03':'ST02','A04':'ST03','A05':'ST04','A06':'ST04','A07':'ST05','A08':'ST06'}[g]+'.bench.top')
 o=box(n+'.carrier',(x,y,1.0),(.46,.40,.07),'teal',g);contact(n+'.carrier',n+'.base')
 box(n+'.lid',(x,y,1.044),(.46,.40,.018),'pale',g);contact(n+'.lid',n+'.carrier')
 for dx in [-.25,.25]:box(n+'.handle',(x+dx,y,1.0),(.04,.17,.04),'amber',g)
 txt(n+'.sealed','SEALED',(x-.13,y-.03,1.056),.060,'ink',g,True)
 return n+'.lid'
def screen(n,x,y,z,w,h,g,lines):
 box(n+'.base',(x,y,.89),(w*.48,.37,.08),'steel',g)
 box(n+'.post',(x,y,1.045),(.055,.06,.23),'steel',g)
 box(n+'.panel',(x,y,z),(w,.055,h),'ink',g)
 for i,(s,col) in enumerate(lines):txt(n+'.line_'+str(i),s,(x-w/2+.08,y-.033,z+h/2-.12-i*.112),.060,col,g)
 return n+'.panel'
# Original room. All architectural and fixture dimensions are illustrative.
box('Environment.floor',(0,0,-.07),(7.9,6.15,.14),'floor',bevel=.05)
box('Environment.backwall',(0,2.62,1.38),(7.9,.08,2.76),'pale')
txt('Environment.title','FRICTIONAL FLUID / EVIDENCE LAB',(-3.62,2.575,2.32),.225,'ink')
txt('Environment.subtitle','ORIGINAL STATIC ASSETS  /  DOI 10.1038/ncomms1289',(-3.60,2.570,2.08),.103,'teal')
txt('Environment.limit','ILLUSTRATION ONLY  |  NO FLUID DYNAMICS  |  20 QUALIFICATION HOLDS',(-3.62,-2.81,.009),.111,'white',flat=True)
positions={'ST01':(-2.4,1.5),'ST02':(0,1.5),'ST03':(2.4,1.5),'ST04':(-2.4,-1.5),'ST05':(0,-1.5),'ST06':(2.4,-1.5)}
for st,g in [('ST01','A01'),('ST02','A03'),('ST03','A04'),('ST04','A05'),('ST05','A07'),('ST06','A08')]:bench(st,*positions[st],g)
# A01 sealed stocks, preparation identity and lot paperwork.
box('A01.stock_rack',(-2.89,1.74,.90),(.63,.85,.10),'teal','A01');contact('A01.stock_rack','ST01.bench.top')
for i,(y,label) in enumerate([(1.48,'GRAINS'),(1.99,'HOST')]):
 cyl('A01.contained_stock_'+str(i),(-2.89,y,1.075),.13,.25,'white','A01');contact('A01.contained_stock_'+str(i),'A01.stock_rack')
 cyl('A01.stock_cap_'+str(i),(-2.89,y,1.218),.139,.036,'amber','A01');contact('A01.stock_cap_'+str(i),'A01.contained_stock_'+str(i))
 txt('A01.stock_label_'+str(i),label,(-3.014,y-.126,1.10),.055,'ink','A01')
plaque('A01.station','ST01 / INTAKE + CUSTODY','CONTAINED STOCKS / IDENTITY FIRST',-2.4,.72,.78,2.12,'A01')
# A02 finished pressure-cell variants: exact nominal source exterior/channel dimensions only.
for i,(x,y,t) in enumerate([(-2.12,1.29,.010),(-2.12,1.91,.019)]):
 n='A02.cell_'+str(int(t*1000))+'mm';base=box(n+'.protected_carrier',(x,y,.886),(.51,.47,.072),'steel','A02');contact(base.name,'ST01.bench.top')
 bottom=.922
 a=box(n+'.lower_plate',(x,y,bottom+t/2),(.350,.350,t),'glass','A02',0,'SOURCE_SCALE');a['nominal_source_dimensions_m']=[.350,.350,t];a['source_fact']='F02';a['pressure_rating']='UNKNOWN'
 contact(a.name,base.name)
 gap=box(n+'.channel_proxy',(x,y,bottom+t+.00025),(.200,.300,.0005),'granular','A02',0,'SOURCE_SCALE');gap['nominal_source_dimensions_m']=[.200,.300,.0005];gap['source_fact']='F02';gap['fluid_simulation']=False;contact(gap.name,a.name)
 b=box(n+'.upper_plate',(x,y,bottom+t+.0005+t/2),(.350,.350,t),'glass','A02',0,'SOURCE_SCALE');b['nominal_source_dimensions_m']=[.350,.350,t];b['source_fact']='F02';b['pressure_rating']='UNKNOWN';contact(b.name,gap.name)
 txt(n+'.label',str(int(t*1000))+' mm PLATES / UNQUALIFIED',(x-.23,y-.213,bottom+2*t+.003),.044,'white','A02',True)
# A03 closed prep service with external sealed carrier and receipt interface.
box('A03.closed_prep_enclosure',(0,1.78,1.35),(1.70,.77,1.0),'teal','A03');contact('A03.closed_prep_enclosure','ST02.bench.top')
box('A03.service_face',(0,1.386,1.41),(1.53,.022,.65),'ink','A03')
txt('A03.closed_label','CLOSED PREPARATION',(-.65,1.369,1.61),.093,'white','A03')
for i,s in enumerate(['ACCEPTED CELL + CONTAINED DISPERSION','FORMULATION / PHI / SETTLING: HELD','QUALIFIED SERVICE RECEIPT REQUIRED']):txt('A03.line_'+str(i),s,(-.65,1.369,1.43-i*.12),.052,'cyan' if i!=1 else 'amber','A03')
dock('A03.job_dock',0,1.00,'A03')
plaque('A03.station','ST02 / QUALIFIED PREPARATION','NO FABRICATION OR MIXING RECIPE',0,.72,.78,2.12,'A03','amber')
# A04 closed synchronized measurement station. No operative pump controls or movable doors.
box('A04.enclosure_base',(2.4,1.52,.90),(1.95,1.28,.10),'ink','A04');contact('A04.enclosure_base','ST03.bench.top')
box('A04.enclosure_back',(2.4,2.145,1.535),(1.95,.045,1.17),'teal','A04')
for x in [1.4475,3.3525]:box('A04.enclosure_side',(x,1.52,1.535),(.045,1.205,1.17),'pale','A04')
box('A04.enclosure_top',(2.4,1.52,2.1425),(1.95,1.28,.045),'white','A04')
box('A04.closed_front_guard',(2.4,.893,1.535),(1.86,.012,1.17),'guard','A04',0)
for x in [1.455,3.345]:box('A04.front_frame',(x,.882,1.535),(.045,.046,1.17),'cyan','A04')
box('A04.closed_guard_footer',(2.4,.869,1.04),(1.87,.050,.18),'teal','A04')
txt('A04.guard_label','CLOSED / SAFE RELEASE REQUIRED',(1.52,.838,1.04),.071,'white','A04')
# Camera BELOW the source-dimension plate stack; white screen above it. Apparatus exterior generic.
box('A04.camera_mount',(2.23,1.50,1.015),(.38,.33,.13),'steel','A04');contact('A04.camera_mount','A04.enclosure_base')
box('A04.camera_body',(2.23,1.50,1.13),(.26,.23,.10),'ink','A04');contact('A04.camera_body','A04.camera_mount')
cyl('A04.camera_lens',(2.23,1.50,1.235),.075,.11,'steel','A04');contact('A04.camera_lens','A04.camera_body')
for x in [1.96,2.50]:box('A04.stage_leg',(x,1.53,1.165),(.035,.44,.43),'steel','A04')
box('A04.stage',(2.23,1.53,1.40),(.62,.54,.04),'steel','A04')
for name,loc,dim,col in [('lower_plate',(2.23,1.53,1.425),(.350,.350,.010),'glass'),('channel_proxy',(2.23,1.53,1.43025),(.200,.300,.0005),'granular'),('upper_plate',(2.23,1.53,1.4355),(.350,.350,.010),'glass')]:
 o=box('A04.source_cell_'+name,loc,dim,col,'A04',0,'SOURCE_SCALE');o['nominal_source_dimensions_m']=list(dim);o['source_fact']='F02';o['fluid_simulation']=False;o['pressure_rating']='UNKNOWN'
contact('A04.source_cell_lower_plate','A04.stage');contact('A04.source_cell_channel_proxy','A04.source_cell_lower_plate');contact('A04.source_cell_upper_plate','A04.source_cell_channel_proxy')
box('A04.brightfield_screen',(2.23,1.54,1.94),(.77,.64,.024),'white','A04')
for x in [1.74,2.75]:box('A04.light_proxy',(x,1.60,1.82),(.055,.54,.055),'cyan','A04')
# Closed abstract pump/pressure service volume and sealed receipt connector; no internal design, commands or rating.
box('A04.closed_injection_service',(2.995,1.72,1.305),(.40,.64,.71),'pale','A04');contact('A04.closed_injection_service','A04.enclosure_base')
box('A04.service_record',(2.995,1.389,1.42),(.32,.012,.28),'ink','A04')
txt('A04.service_record_title','SERVICE',(2.864,1.380,1.47),.057,'cyan','A04');txt('A04.service_record_state','HELD',(2.90,1.380,1.35),.063,'amber','A04')
plaque('A04.station','ST03 / CLOSED MEASUREMENT','PRESSURE + CAMERA / CLOCK MAP REQUIRED',2.4,.72,.78,2.12,'A04','amber')
# A05 metrology metadata objects have no synthetic acquisition traces.
screen('A05.metrology',-2.72,-1.08,1.39,1.43,.70,'A05',[
 ('ST04 / READ-ONLY METROLOGY','white'),('PRESSURE / IMAGE CLOCKS: UNBOUND','amber'),('SCALE + CALIBRATION IDS: MISSING','cyan'),('RAW DATA: NONE / NO SYNTHETIC TRACE','white'),('AREA / PERIMETER / EVENTS: UNRUN','cyan')])
box('A05.receipt_shelf',(-1.86,-1.09,.892),(.46,.49,.084),'steel','A05');contact('A05.receipt_shelf','ST04.bench.top')
for i,(s,c) in enumerate([('CLOCK','cyan'),('SCALE','amber'),('RAW ID','violet')]):
 box('A05.metadata_card_'+str(i),(-1.86,-1.26+i*.16,.946),(.35,.13,.024),c,'A05');contact('A05.metadata_card_'+str(i),'A05.receipt_shelf')
 txt('A05.metadata_label_'+str(i),s,(-2.00,-1.28+i*.16,.960),.044,'ink','A05',True)
plaque('A05.station','ST04 / METROLOGY + PATTERNS','ORIGINAL CATEGORY TOKENS / NEVER DATA',-2.4,-2.27,.78,2.12,'A05')
# A06 five original non-source-derived abstract pattern icons. No dynamic field or figure tracing.
board=box('A06.token_board',(-2.4,-1.83,.886),(1.98,.65,.072),'ink','A06');contact(board.name,'ST04.bench.top')
patterns=[('FINGERS','cyan'),('BURSTS','amber'),('CORAL','violet'),('SUSPENSION','cyan'),('GRANULAR','amber')]
for i,(label,col) in enumerate(patterns):
 x=-3.18+i*.39;y=-1.76;tile=box('A06.tile_'+str(i),(x,y,.935),(.35,.40,.026),'teal','A06',.008,'SCHEMATIC_TOKENS');contact(tile.name,board.name)
 z=.958
 if i==0:
  seg=[((-.13,-.13),(-.015,.015)),((-.015,.015),(-.12,.14)),((-.015,.015),(.105,.115)),((-.01,-.03),(.12,-.01))]
 elif i==2:
  seg=[((0,-.15),(0,.13)),((0,-.065),(-.12,.00)),((-.12,.00),(-.14,.10)),((0,.035),(.12,.10)),((.12,.10),(.13,.15)),((-.035,-.05),(-.065,.115))]
 elif i==4:
  seg=[((-.12,-.15),(-.01,-.03)),((-.01,-.03),(.005,.15)),((-.01,-.03),(.135,.045)),((-.015,.06),(-.12,.12))]
 else:seg=[]
 for j,(a,b) in enumerate(seg):line('A06.icon_'+str(i)+'_'+str(j),(x+a[0],y+a[1],z),(x+b[0],y+b[1],z),.014,col,'A06','SCHEMATIC_TOKENS')
 if i==1:
  for j,(dx,dy,r) in enumerate([(-.08,-.11,.046),(.063,-.005,.062),(-.04,.125,.040)]):cyl('A06.burst_'+str(j),(x+dx,y+dy,z),r,.022,col,'A06',24,'SCHEMATIC_TOKENS')
 if i==3:
  for j in range(4):
   for k in range(3):cyl('A06.suspension_dot_'+str(j)+'_'+str(k),(x-.11+j*.07,y-.105+k*.10,z),.018,.022,col,'A06',16,'SCHEMATIC_TOKENS')
 txt('A06.token_label_'+str(i),label,(x-.16,-2.078,.926),.039,'white','A06',True,'SCHEMATIC_TOKENS')
txt('A06.warning','STATIC SYMBOLS / NO LENGTH SCALE',(-3.26,-2.137,.926),.050,'amber','A06',True,'SCHEMATIC_TOKENS')
# A07 review separates experimental branches, external context and unresolved theory.
screen('A07.branch_dashboard',0,-1.18,1.57,1.95,1.17,'A07',[
 ('ST05 / SCIENTIFIC REVIEW','white'),('B01 PREP   B02 LOW RATE   B03 SPARSE GRID','cyan'),('B04 MORPHOMETRY   B05 RATE BRANCH','cyan'),('B06 VISCOSITY   B07 GRANULAR FRACTURE','cyan'),('B08 EXTERNAL CONTEXT / NOT NEW RUNS','violet'),('B09 MODEL CONTEXT / NOT EXECUTED','violet'),('CORAL: 0.1 vs 1.0 ml/min / UNRESOLVED','amber'),('BOYLE SIGN: UNRESOLVED / NO REPAIR','amber'),('20 LOCAL WIDTHS != 20 PREPARATIONS','white')])
box('A07.hold_ledger',(0,-1.96,.887),(1.89,.37,.074),'ink','A07');contact('A07.hold_ledger','ST05.bench.top')
for i in range(20):
 x=-.845+(i%10)*.187;y=-1.88-(i//10)*.135
 box('A07.hold_'+str(i+1),(x,y,.939),(.16,.11,.030),'amber','A07');contact('A07.hold_'+str(i+1),'A07.hold_ledger')
 txt('A07.hold_label_'+str(i+1),f'U{i+1:02d}',(x-.064,y-.020,.957),.042,'ink','A07',True)
plaque('A07.station','ST05 / 20 QUALIFICATION HOLDS','SOURCE FACT / MODEL / UNKNOWN REMAIN DISTINCT',0,-2.27,.78,2.12,'A07','amber')
# A08 closeout quarantine, safe-release receipt and archive remain distinct supported objects.
dock('A08.return_dock',2.0,-1.68,'A08')
box('A08.quarantine_case',(2.90,-1.63,1.105),(.67,.62,.51),'amber','A08');contact('A08.quarantine_case','ST06.bench.top')
box('A08.quarantine_lid',(2.90,-1.63,1.38),(.69,.64,.040),'ink','A08');contact('A08.quarantine_lid','A08.quarantine_case')
txt('A08.quarantine_title','QUARANTINE',(2.615,-1.950,1.17),.076,'ink','A08')
box('A08.archive',(2.4,-1.00,1.055),(1.64,.29,.41),'teal','A08');contact('A08.archive','ST06.bench.top')
txt('A08.archive_title','CUSTODY / INSPECTION / ARCHIVE',(1.655,-1.151,1.12),.065,'white','A08')
txt('A08.archive_sub','SAFE STATE REQUIRES INDEPENDENT RECEIPT',(1.66,-1.151,.98),.049,'cyan','A08')
plaque('A08.station','ST06 / CLOSEOUT + ARCHIVE','CONTAINED RETURN / NO TIMER-BASED RELEASE',2.4,-2.27,.78,2.12,'A08','amber')
# Contract anchors are review selectors at exact declared coordinates, never robot manipulation targets.
for an in C['anchors']:
 loc=an['position_m']
 o=bpy.data.objects.new(an['object_name'],None);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=an['rotation_euler_rad'];o.empty_display_type='PLAIN_AXES';o.empty_display_size=.055;own(o,an['asset_id'],'EVIDENCE_ANCHORS');o['anchor_id']=an['anchor_id'];o['station_id']=an['station_id'];o['mode']='evidence_only';o['qualified']=False
# Labels are original editable mesh text, with readable content preserved as custom metadata.
for o in list(bpy.data.objects):
 if o.type=='FONT':o['label_text']=o.data.body;bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
def camera(n,loc,target,ortho):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=ortho;return o
cams=[camera('CAM_overview',(9,-12,11),(0,0,.90),11.6),camera('CAM_closed_service',(6,-4,5),(1.73,1.42,1.32),5.75),camera('CAM_evidence',(.2,-8,8.0),(-.76,-1.48,1.08),7.35)]
world=bpy.data.worlds.new('Soft studio');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.57,.69,.75,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.38
for n,loc,power,size in [('Key',(-3,-5,8),1500,6),('Fill',(6,-1,6),1000,5),('Rim',(-3,5,7),1500,4)]:
 d=bpy.data.lights.new(n,'AREA');o=bpy.data.objects.new(n,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler();d.energy=power;d.shape='DISK';d.size=size
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=80;scene.cycles.use_denoising=False;scene.render.resolution_x=1500;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False;scene.view_settings.view_transform='AgX';scene.camera=cams[0];scene.render.filepath='//../previews/preview_01_overview.png';scene.render.use_stamp=False
bpy.context.view_layer.update()
manifest={'schema':'sciencegym.frictional.scene.v1','source_doi':'10.1038/ncomms1289','scene_name':scene.name,'physical_actuation_enabled':False,'scientific_simulation_performed':False,'unit':'meter','up_axis':'Z','objects':[],'static_support_contacts':contacts,'scale_boundary':'SOURCE_SCALE stores source nominal dimensions only. Architecture, carriers and all pattern tokens are illustrative; neither is qualified apparatus CAD, fluid dynamics or measurement evidence.'}
for o in sorted(bpy.data.objects,key=lambda x:x.name):
 manifest['objects'].append({'name':o.name,'type':o.type,'asset_id':o.get('asset_id'),'anchor_id':o.get('anchor_id'),'parent':o.parent.name if o.parent else None,'location_m':list(o.matrix_world.translation),'dimensions_m':list(o.dimensions),'representation_class':o.get('representation_class'),'label_text':o.get('label_text'),'custom':{k:o[k].to_list() if hasattr(o[k],'to_list') else o[k] for k in ['nominal_source_dimensions_m','source_fact','pressure_rating','fluid_simulation'] if k in o}})
(P/'scene_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'geometry/frictional_lab.raw.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(P/'geometry/frictional_lab.glb'),export_format='GLB',export_extras=True,export_cameras=True,export_lights=False)
receipt={'schema':'sciencegym.cpu_render_receipt.v1','engine':'CYCLES','device':'CPU','samples':80,'source':'original procedural geometry; no publisher figures, movie frames or source CAD','renders':[]}
for cam,name in zip(cams,['preview_01_overview.png','preview_02_closed_service.png','preview_03_evidence.png']):
 scene.camera=cam;scene.render.filepath=str(P/'previews'/name);start=time.time();bpy.ops.render.render(write_still=True);receipt['renders'].append({'file':'previews/'+name,'camera':cam.name,'seconds':round(time.time()-start,3),'width':1500,'height':1000,'interpretation':'Real CPU render of static illustration; no fluid dynamics, measurements or reproduced experimental outcomes'})
(P/'review/render_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('SCENE_BUILD_COMPLETE')
