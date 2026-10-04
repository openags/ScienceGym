"""Reopen exported GLBs; check actual dimensions and preserved reference edges."""
import bpy,json,hashlib,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];receipts=[];na=len(json.loads((P/'affordances.json').read_text())['anchors'])
for name,count in [('woven_material_lab.glb',11),('woven_reference_display.glb',0)]:
 bpy.ops.wm.read_factory_settings(use_empty=True);f=P/'geometry'/name;bpy.ops.import_scene.gltf(filepath=str(f));s=bpy.context.scene
 roots=[o for o in s.objects if 'asset_id' in o];anchors=[o for o in s.objects if 'anchor_id' in o]
 assert len(roots)==count and len(anchors)==(na if count else 0)
 assert not bpy.data.images and not any('studio.floor' in o.name for o in s.objects)
 assert not any(o.type in ['FONT','CURVE'] for o in s.objects)
 if count:
  assert 'native.cell_reference' in s.objects and 'sem.opaque_cover' in s.objects and not any(o.name.startswith('DISPLAY.') for o in s.objects)
  assert all(not r['energy_enabled'] and not r['physical_execution'] for r in roots)
  assert all(math.isclose(s.objects['native.cell_reference'].dimensions[i],60e-6,abs_tol=1e-8) for i in range(3))
  assert math.isclose(s.objects['native.fiber_radius_reference'].dimensions.x/2,1e-6,abs_tol=1e-9)
 else:
  assert s.objects['DISPLAY.woven_reference']['reference_scale_factor']==1000
  for kind in ['BCC','CUBIC']:
   ref=s.objects['display.'+kind+'.cell_reference'];assert ref.type=='MESH' and len(ref.data.edges)==12
   assert all(math.isclose(ref.dimensions[i],.06,abs_tol=1e-7) for i in range(3))
  assert math.isclose(s.objects['display.fiber_radius_reference'].dimensions.x/2,.001,abs_tol=1e-7)
  assert all(not o['connectivity_qualified'] for o in s.objects if 'connectivity_qualified' in o)
 receipts.append({'file':'geometry/'+name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'object_count':len(s.objects),'root_count':len(roots),'anchor_count':len(anchors),'status':'PASS'})
(P/'review/glb_import_validation.json').write_text(json.dumps({'status':'PASS','blender_version':bpy.app.version_string,'files':receipts},indent=2)+'\n');print('GLB_IMPORT_PASS')
