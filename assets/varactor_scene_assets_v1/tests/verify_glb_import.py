"""Actual Blender imports of both delivered GLBs, not only header checks."""
import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];plan=json.loads((P/'task_binding_snapshot.json').read_text());aff=json.loads((P/'affordances.json').read_text());rows=[]
for filename in ['varactor_lab.glb','varactor_reference_display.glb']:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'geometry'/filename));checks=[]
 def check(v,n):
  if not v:raise AssertionError(filename+' '+n)
  checks.append(n)
 check(len(bpy.data.objects)>0,'objects imported')
 for o in bpy.data.objects:
  check(o.animation_data is None,o.name+' static')
  if o.type=='MESH':check(len(o.data.vertices)>0 and len(o.data.polygons)>0,o.name+' nonempty mesh')
 if filename=='varactor_lab.glb':
  for a in plan['scene_assets']:
   o=bpy.data.objects[a['asset_id']];check(o['asset_id']==a['asset_id'],'canonical root '+a['asset_id']);check(not o['physical_execution'] and not o['device_io'] and not o['energy_enabled'],'disabled '+a['asset_id'])
  for a in aff['anchors']:
   o=bpy.data.objects[a['scene_object']];check(o.parent.name==a['asset_id'],'anchor parent '+a['scene_object']);check((o.matrix_world.translation-Vector(a['translation_m'])).length<1e-5,'anchor metric position '+a['scene_object'])
  expected={'native.sto.substrate':(.003,.003,.0005),'native.kto.substrate':(.003,.003,.0005),'native.sto.pad0.au':(.00012,.00012,60e-9)}
 else:expected={'display.sto.substrate':(.3,.3,.05),'display.kto.substrate':(.3,.3,.05),'display.sto.pad0.au':(.012,.012,6e-6)}
 for n,ds in expected.items():
  o=bpy.data.objects[n];check(all(abs(a-b)<max(abs(b)*1e-4,1e-10) for a,b in zip(o.dimensions,ds)),n+' nominal dimensions preserved')
 rows.append({'file':'geometry/'+filename,'status':'PASS','checks':len(checks),'objects':len(bpy.data.objects),'mesh_objects':len([o for o in bpy.data.objects if o.type=='MESH']),'assertions':checks})
r={'status':'PASS','actual_reimports':True,'checks':sum(r['checks'] for r in rows),'files':rows};(P/'review/glb_import_validation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps([{k:v for k,v in r.items() if k!='assertions'} for r in rows]))
