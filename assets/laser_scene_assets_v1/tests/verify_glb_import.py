"""Roundtrip each actual GLB through Blender; no physical qualification."""
import bpy,json,hashlib,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];receipts=[];na=len(json.loads((P/'affordances.json').read_text())['anchors'])
for name,count in [('laser_control_lab.glb',10),('laser_pic_display.glb',0)]:
 bpy.ops.wm.read_factory_settings(use_empty=True);f=P/'geometry'/name;bpy.ops.import_scene.gltf(filepath=str(f));s=bpy.context.scene
 roots=[o for o in s.objects if 'asset_id' in o];anchors=[o for o in s.objects if 'anchor_id' in o]
 assert len(roots)==count and len(anchors)==(na if count else 0)
 assert not bpy.data.images and not any('studio.floor' in o.name for o in s.objects)
 assert not any(o.type in ['FONT','CURVE'] for o in s.objects)
 if count:
  assert 'pic.native_footprint_reference' in s.objects and 'enclosure.closed_cover' in s.objects and not any(o.name.startswith('DISPLAY.') for o in s.objects)
  assert all(not r['laser_energy_enabled'] and not r['physical_execution'] for r in roots)
  assert all(f'dfb{i}.sealed_module' in s.objects for i in range(1,4))
 else:
  assert 'DISPLAY.pic_nominal_footprint' in s.objects and s.objects['DISPLAY.pic_nominal_footprint']['footprint_scale_factor']==1000
 receipts.append({'file':'geometry/'+name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'object_count':len(s.objects),'root_count':len(roots),'anchor_count':len(anchors),'status':'PASS'})
(P/'review/glb_import_validation.json').write_text(json.dumps({'status':'PASS','blender_version':bpy.app.version_string,'files':receipts},indent=2)+'\n');print('GLB_IMPORT_PASS')
