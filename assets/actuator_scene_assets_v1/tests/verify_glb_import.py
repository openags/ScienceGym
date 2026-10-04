import bpy,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];receipts=[];na=len(json.loads((P/'affordances.json').read_text())['anchors'])
for name,count in [('actuator_metrology_lab.glb',7),('actuator_measurement_display.glb',0)]:
 bpy.ops.wm.read_factory_settings(use_empty=True);f=P/'geometry'/name;bpy.ops.import_scene.gltf(filepath=str(f));s=bpy.context.scene
 roots=[o for o in s.objects if 'asset_id' in o];anchors=[o for o in s.objects if 'anchor_id' in o]
 assert len(roots)==count and len(anchors)==(na if count else 0)
 assert not bpy.data.images and not any('studio.floor' in o.name for o in s.objects)
 assert not any(o.type=='FONT' for o in s.objects)
 if count:assert 'actuator_fixed_clamp' in s.objects and 'camera_metrology' in s.objects and not any(o.name.startswith('DISPLAY.') for o in s.objects)
 else:assert 'DISPLAY.representative_lattice' in s.objects and s.objects['DISPLAY.representative_lattice']['uniform_scale_factor']==10
 receipts.append({'file':'geometry/'+name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'object_count':len(s.objects),'root_count':len(roots),'anchor_count':len(anchors),'status':'PASS'})
(P/'review/glb_import_validation.json').write_text(json.dumps({'status':'PASS','blender_version':bpy.app.version_string,'files':receipts},indent=2)+'\n');print('GLB_IMPORT_PASS')
