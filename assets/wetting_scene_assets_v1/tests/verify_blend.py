"""Reopen real editable Blender file and check geometry, scale and interaction boundaries."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'geometry/wetting_lab.blend'));checks=[]
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def dims(n,expected):
 o=bpy.data.objects[n];check(all(abs(a-b)<max(2e-8,abs(b)*2e-5) for a,b in zip(o.dimensions,expected)),n+' nominal dimensions');return o
plan=json.loads((P/'operation_binding_contract.json').read_text());aff=json.loads((P/'affordances.json').read_text());states=json.loads((P/'states.json').read_text())
check(len(bpy.data.scenes)==2,'two isolated scenes')
for s in bpy.data.scenes:
 check(s.unit_settings.system=='METRIC' and s.unit_settings.scale_length==1,s.name+' SI metres');check(s.render.engine=='CYCLES' and s.cycles.device=='CPU',s.name+' CPU');check(s.rigidbody_world is None,s.name+' no physical world');check(not s.render.use_stamp,s.name+' no stamps')
for a in plan['assets']:
 o=bpy.data.objects[a['asset_id']];check(o.type=='EMPTY',a['asset_id']+' root')
 for key in ['physical_execution','device_io','energy_enabled','physical_geometry_validated']:check(o[key]==False,a['asset_id']+' '+key+' false')
 check(set(o['operation_ids'].split(','))==set(a['bind_operation_ids']),a['asset_id']+' exact operations')
for a in aff['anchors']:
 o=bpy.data.objects[a['scene_object']];target=bpy.data.objects[a['target_object']]
 check(o.type=='EMPTY' and o.parent.name==a['asset_id'],a['scene_object']+' hierarchy');check((o.matrix_world.translation-Vector(a['translation_m'])).length<1e-6,a['scene_object']+' recorded position');check((o.matrix_world.translation-target.matrix_world.translation).length<1e-6,a['scene_object']+' actual target position');check(o['target_object']==target.name,a['scene_object']+' target linkage');check(not o['physical_execution'] and not o['graspable'],a['scene_object']+' not motion or grasp')
for prefix,poly in [('specimen.pdms','pdms'),('specimen.cy','cy'),('chamber.native_carrier','cy')]:
 dims(prefix+'.glass',(.024,.024,.00017));dims(prefix+'.film',(.024,.024,.000030 if poly=='pdms' else .000035));check(bpy.data.objects[prefix+'.film']['contact_excluded'],prefix+' active face excluded')
dims('display.slide.glass',(.48,.48,.0034));dims('display.slide.pdms',(.48,.48,.0006));dims('display.micro.cy_patch',(.56,.40,.035))
check(bpy.data.objects['DISPLAY.WHOLE_SLIDE_20X']['uniform_display_scale']==20,'uniform whole-slide 20x declared');check(bpy.data.objects['DISPLAY.MICROSCOPY_CROP_1000X']['uniform_display_scale']==1000,'uniform micro 1000x declared')
check(not bpy.data.objects['display.micro.synthetic_drop']['telemetry_authority'],'synthetic drop cannot supply telemetry')
for g in aff['candidate_carrier_contacts']:
 o=bpy.data.objects[g['scene_object']];check(o['candidate_grasp_region'] and not o['graspable'],o.name+' candidate only')
for e in aff['exclusion_regions']:check(bpy.data.objects[e['scene_object']]['contact_excluded'],e['scene_object']+' exclusion')
for c in aff['collision_proxies']:
 o=bpy.data.objects[c['scene_object']];check(o.hide_render and not o['collision_qualified'],o.name+' disabled hidden proxy')
for n in states['closed_service_objects']:check(bpy.data.objects[n]['closed']==True,n+' closed boundary')
check(len([o for o in bpy.data.objects if o.type=='FONT'])>65,'editable native text')
for o in bpy.data.objects:
 check(o.animation_data is None,o.name+' no animations/drivers');check(o.rigid_body is None,o.name+' no physics body');check(len(o.constraints)==0,o.name+' no motion constraints')
 if o.type=='MESH':
  check(len(o.data.vertices)>0 and len(o.data.polygons)>0,o.name+' populated mesh');check(all(math.isfinite(v) for vert in o.data.vertices for v in vert.co),o.name+' finite vertices')
check(not any(i.source=='FILE' or i.packed_file for i in bpy.data.images),'no imported raster assets');check(not bpy.data.texts,'no embedded executable text');check(not any(m.library for m in bpy.data.meshes),'no externally linked meshes')
r={'status':'PASS','checks':len(checks),'actual_native_reopen':True,'scenes':[s.name for s in bpy.data.scenes],'objects':len(bpy.data.objects),'native_fonts':len([o for o in bpy.data.objects if o.type=='FONT']),'nominal_dimensions_verified':True,'physical_geometry_validated':False,'no_hardware_or_physics':True,'assertions':checks};(P/'review/blend_validation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='assertions'}))
