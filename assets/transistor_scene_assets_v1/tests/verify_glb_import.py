"""Re-import both portable GLBs in fresh Blender scenes without saving changes."""
import bpy,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];receipts=[];expected_anchors=len(json.loads((P/'affordances.json').read_text())['anchors'])
for name,count in [('transistor_operations_lab.glb',6),('transistor_layer_ledger_display.glb',0)]:
 bpy.ops.wm.read_factory_settings(use_empty=True);f=P/'geometry'/name;bpy.ops.import_scene.gltf(filepath=str(f));s=bpy.context.scene
 roots=[o for o in s.objects if 'asset_id' in o];anchors=[o for o in s.objects if 'anchor_id' in o]
 assert len(roots)==count and len(anchors)==(expected_anchors if count else 0)
 assert not bpy.data.images and not any('studio.floor' in o.name for o in s.objects)
 assert not any(o.name.startswith('native.layer.') for o in s.objects)
 if count:assert 'probe.closed_chamber' in s.objects and 'bias.closed_console' in s.objects and not any(o.name.startswith('DISPLAY.') for o in s.objects)
 else:assert 'DISPLAY.layer_ledger' in s.objects and sum('layer_index' in o for o in s.objects)==72
 receipts.append({'file':'geometry/'+name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'object_count':len(s.objects),'root_count':len(roots),'anchor_count':len(anchors),'status':'PASS'})
(P/'review/glb_import_validation.json').write_text(json.dumps({'status':'PASS','blender_version':bpy.app.version_string,'files':receipts},indent=2)+'\n');print('GLB_IMPORT_PASS')
