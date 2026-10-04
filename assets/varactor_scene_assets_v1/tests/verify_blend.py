"""Actual reopen of editable native file, hierarchy, dimensions and closed boundaries."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'geometry/varactor_lab.blend'));checks=[]
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def dims(n,expected,tol=1e-8):
 o=bpy.data.objects[n];check(all(abs(a-b)<max(tol,abs(b)*1e-5) for a,b in zip(o.dimensions,expected)),n+' nominal reference dimensions');return o
plan=json.loads((P/'task_binding_snapshot.json').read_text());aff=json.loads((P/'affordances.json').read_text());states=json.loads((P/'states.json').read_text())
check(len(bpy.data.scenes)==2,'two isolated scenes')
for s in bpy.data.scenes:
 check(s.unit_settings.system=='METRIC' and s.unit_settings.scale_length==1,s.name+' metric units');check(s.render.engine=='CYCLES' and s.cycles.device=='CPU',s.name+' CPU');check(not s.rigidbody_world,s.name+' no rigidbody world');check(not s.render.use_stamp_filename,s.name+' no filename stamps')
for a in plan['scene_assets']:
 o=bpy.data.objects[a['asset_id']];check(o.type=='EMPTY',a['asset_id']+' canonical root')
 for k in ['physical_execution','device_io','energy_enabled','physical_geometry_validated']:check(o[k]==False,a['asset_id']+' '+k+' disabled')
 check(set(o['operation_ids'].split(','))==set(a['bind_operation_ids']),a['asset_id']+' exact operation IDs')
for a in aff['anchors']:
 o=bpy.data.objects[a['scene_object']];check(o.type=='EMPTY' and o.parent.name==a['asset_id'],a['scene_object']+' hierarchy');check((o.location-Vector(a['translation_m'])).length<1e-6,a['scene_object']+' coordinate match');check(o['target_object']==a['target_object'] and a['target_object'] in bpy.data.objects,a['scene_object']+' target exists');check(not o['physical_execution'],a['scene_object']+' metadata only')
for prefix in ['native.sto','native.kto']:dims(prefix+'.substrate',(.003,.003,.0005))
for prefix in ['display.sto','display.kto']:dims(prefix+'.substrate',(.3,.3,.05))
for prefix,S in [('native.sto',1),('display.sto',100)]:
 for i in [0,1]:
  dims(prefix+'.pad'+str(i)+'.ti',(.00012*S,.00012*S,5e-9*S),1e-12)
  dims(prefix+'.pad'+str(i)+'.au',(.00012*S,.00012*S,60e-9*S),1e-12)
 a=bpy.data.objects[prefix+'.pad0.au'];b=bpy.data.objects[prefix+'.pad1.au'];check(abs((a.location-b.location).length-.002*S)<1e-7,prefix+' approximate spacing reference');check(a['spacing_status'].startswith('about'),prefix+' nominal spacing disclaimer')
for prefix,S in [('native.sto',1),('native.kto',1),('display.sto',100),('display.kto',100)]:
 dims(prefix+'.back_ti',(.003*S,.003*S,5e-9*S),1e-12);dims(prefix+'.back_au',(.003*S,.003*S,60e-9*S),1e-12)
for n in states['closed_service_objects']:check(bpy.data.objects[n]['closed']==True,n+' closed geometry')
check(bpy.data.objects['DISPLAY.varactor_reference']['reference_scale_factor']==100,'explicit uniform 100x display');check(bpy.data.objects['circuit.module.DRAIN']['branch_scope'].startswith('SQD only'),'drain excludes DQD')
check(len([o for o in bpy.data.objects if o.type=='FONT'])>40,'native editable text')
for o in bpy.data.objects:
 check(o.animation_data is None,o.name+' no animation or driver');check(o.rigid_body is None,o.name+' no rigidbody');check(len(o.constraints)==0,o.name+' no control constraint')
check(not any(i.source=='FILE' or i.packed_file for i in bpy.data.images),'no imported image assets');check(len(bpy.data.texts)==0,'no embedded executable text');check(not any(m.library for m in bpy.data.meshes),'no linked external meshes')
r={'status':'PASS','checks':len(checks),'scenes':[s.name for s in bpy.data.scenes],'objects':len(bpy.data.objects),'native_fonts':len([o for o in bpy.data.objects if o.type=='FONT']),'nominal_dimensions_verified':True,'physical_geometry_validated':False,'no_hardware_or_physics':True,'assertions':checks};(P/'review/blend_validation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='assertions'}))
