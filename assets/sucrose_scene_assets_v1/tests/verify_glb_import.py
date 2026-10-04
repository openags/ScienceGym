"""Independent Blender GLB re-import smoke test, without saving either imported scene."""
import bpy,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];receipts=[]
for name,expected in [('sucrose_operations_lab.glb',6),('sucrose_volume_lineage_display.glb',0)]:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 f=P/'geometry'/name;bpy.ops.import_scene.gltf(filepath=str(f));s=bpy.context.scene
 roots=[o for o in s.objects if 'asset_id' in o];assert len(roots)==expected,(name,len(roots))
 anchors=[o for o in s.objects if 'anchor_id' in o];assert len(anchors)==(31 if expected else 0)
 assert not any('studio.floor' in o.name for o in s.objects)
 assert not bpy.data.images
 if expected:
  assert 'pump.closed_proxy' in s.objects and 'optics.sealed_body' in s.objects
  assert not any('DISPLAY.' in o.name for o in s.objects)
 else:assert 'DISPLAY.volume_lineage' in s.objects and not any(o.name.startswith('A_') for o in s.objects)
 receipts.append({'file':'geometry/'+name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'imported_object_count':len(s.objects),'asset_root_count':len(roots),'anchor_count':len(anchors),'status':'PASS'})
(P/'review/glb_import_validation.json').write_text(json.dumps({'status':'PASS','blender_version':bpy.app.version_string,'files':receipts},indent=2));print('GLB_IMPORT_PASS')
