"""Reopen editable native file and verify metric geometry and static boundaries."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'geometry/lockable_origami_lab.blend'))
checks=[]
def check(v,name):
 if not v:raise AssertionError(name)
 checks.append(name)
def dims(name,expected,tol=1e-7):
 o=bpy.data.objects[name];check(all(abs(a-b)<tol for a,b in zip(o.dimensions,expected)),name+' native dimensions');return o
plan=json.loads((P/'task_binding_snapshot.json').read_text());aff=json.loads((P/'affordances.json').read_text());kin=json.loads((P/'review/kinematic_proxy.json').read_text())
check(len(bpy.data.scenes)==2,'two separate scenes')
for s in bpy.data.scenes:
 check(s.unit_settings.system=='METRIC' and s.unit_settings.scale_length==1,s.name+' metric unit scale')
 check(s.render.engine=='CYCLES' and s.cycles.device=='CPU',s.name+' CPU render')
 check(not s.rigidbody_world,s.name+' no rigidbody world')
 check(not s.render.use_stamp_filename,s.name+' no filename stamps')
for a in plan['scene_assets']:
 o=bpy.data.objects[a['asset_id']];check(o.type=='EMPTY',a['asset_id']+' canonical root')
 for key in ('physical_execution','device_io','energy_enabled','physical_geometry_validated'):check(o[key]==False,a['asset_id']+' '+key+' disabled')
 check(set(o['operation_ids'].split(','))==set(a['bind_operation_ids']),a['asset_id']+' operation identity')
for a in aff['anchors']:
 o=bpy.data.objects[a['scene_object']];check(o.type=='EMPTY' and o.parent.name==a['asset_id'],a['scene_object']+' hierarchy')
 check((o.location-Vector(a['translation_m'])).length<1e-6,a['scene_object']+' coordinate match')
 check(o['target_object']==a['target_object'] and a['target_object'] in bpy.data.objects,a['scene_object']+' target exists')
 check(not o['physical_execution'],a['scene_object']+' metadata only')
dims('native.paperboard_coupon',(.015,.015,.00021));dims('native.tensile_strip',(.24,.005,.00021));dims('display.perforated_coupon',(.12,.12,.00168));dims('display.edge_coupon',(.12,.00168,.12))
check(bpy.data.objects['display.perforated_coupon']['display_scale']==8,'explicit uniform display scale')
check(len([o for o in bpy.data.objects if o.type=='FONT'])>20,'editable native text preserved')
for o in bpy.data.objects:
 check(o.animation_data is None,o.name+' no animation/driver')
 check(o.rigid_body is None,o.name+' no rigidbody')
 check(len(o.constraints)==0,o.name+' no actuation constraints')
for state in kin['snapshots']:
 verts=[Vector(v) for v in state['centerline_vertices_m']]
 for i in range(4):check(abs((verts[i+1]-verts[i]).length-state['centerline_link_length_m'])<1e-8,state['id']+' rigid centerline '+str(i))
 for name in state['panel_objects']:dims(name,(.029,.03,.00021))
 check(state['source_mode'] is None and not state['locking_or_contact'],state['id']+' no source mode/contact')
check(not any(i.source=='FILE' or i.packed_file for i in bpy.data.images),'no file-based or packed image assets')
check(len(bpy.data.texts)==0,'no embedded executable text')
check(not any(m.library for m in bpy.data.meshes),'no linked external mesh libraries')
report={'status':'PASS','checks':len(checks),'scenes':[s.name for s in bpy.data.scenes],'objects':len(bpy.data.objects),'native_fonts':len([o for o in bpy.data.objects if o.type=='FONT']),'source_geometry_validated':False,'metric_reference_dimensions_verified':True,'no_hardware_or_physics':True,'assertions':checks}
(P/'review/blend_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='assertions'}))
