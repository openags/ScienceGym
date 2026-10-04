"""Actual GLB imports and metric object/anchor checks, not a header-only audit."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];plan=json.loads((P/'operation_binding_contract.json').read_text());aff=json.loads((P/'affordances.json').read_text());rows=[]
for file in ['wetting_lab.glb','wetting_dimension_references.glb']:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'geometry'/file));checks=[]
 def check(v,n):
  if not v:raise AssertionError(file+' '+n)
  checks.append(n)
 check(len(bpy.data.objects)>0,'populated real import')
 for o in bpy.data.objects:
  check(o.animation_data is None,o.name+' static');check(o.rigid_body is None,o.name+' no physics')
  if o.type=='MESH':
   check(len(o.data.vertices)>0 and len(o.data.polygons)>0,o.name+' nonempty mesh');check(all(math.isfinite(v) for vert in o.data.vertices for v in vert.co),o.name+' finite vertices')
 if file=='wetting_lab.glb':
  for a in plan['assets']:
   o=bpy.data.objects[a['asset_id']];check(o['asset_id']==a['asset_id'],'canonical root '+a['asset_id']);check(not o['physical_execution'] and not o['device_io'] and not o['energy_enabled'],a['asset_id']+' disabled')
  for a in aff['anchors']:
   o=bpy.data.objects[a['scene_object']];check(o.parent.name==a['asset_id'],'canonical anchor parent '+o.name);check((o.matrix_world.translation-Vector(a['translation_m'])).length<1e-5,'anchor metric position '+o.name);check(a['target_object'] in bpy.data.objects,'actual mesh target '+o.name)
  expected={'specimen.pdms.glass':(.024,.024,.00017),'specimen.pdms.film':(.024,.024,.00003),'specimen.cy.film':(.024,.024,.000035),'chamber.native_carrier.film':(.024,.024,.000035)}
  check(not any(o.get('geometry_role')=='collision_proxy' for o in bpy.data.objects),'collision proxies not confused with portable visual meshes')
 else:
  expected={'display.slide.glass':(.48,.48,.0034),'display.slide.pdms':(.48,.48,.0006),'display.micro.cy_patch':(.56,.40,.035)}
  for n,S in [('DISPLAY.WHOLE_SLIDE_20X',20),('DISPLAY.MICROSCOPY_CROP_1000X',1000)]:check(bpy.data.objects[n]['uniform_display_scale']==S,n+' explicit magnification')
 for n,ds in expected.items():check(all(abs(a-b)<max(abs(b)*1e-4,2e-8) for a,b in zip(bpy.data.objects[n].dimensions,ds)),n+' nominal metric dimensions preserved')
 rows.append({'file':'geometry/'+file,'status':'PASS','checks':len(checks),'objects':len(bpy.data.objects),'mesh_objects':len([o for o in bpy.data.objects if o.type=='MESH']),'assertions':checks})
r={'status':'PASS','actual_reimports':True,'checks':sum(r['checks'] for r in rows),'files':rows};(P/'review/glb_import_validation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps([{k:v for k,v in r.items() if k!='assertions'} for r in rows]))
