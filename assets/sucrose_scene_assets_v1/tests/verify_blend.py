import bpy,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];plan=json.loads((P/'task_binding_snapshot.json').read_text());main=bpy.data.scenes['SUCROSE_AUTHORED_METRIC'];display=bpy.data.scenes['DISPLAY_ONLY_NOT_TO_SCALE'];checks=[]
def check(name,condition):
 assert condition,name
 checks.append({'check':name,'passed':True})
check('two separated editable scenes',len(bpy.data.scenes)==2)
expected={a['asset_id'] for a in plan['scene_assets']}
check('six exact main asset roots',{o['asset_id'] for o in main.objects if 'asset_id' in o}==expected)
check('31 task anchors',len([o for o in main.objects if 'anchor_id' in o])==31)
for asset in plan['scene_assets']:
 root=bpy.data.objects[asset['asset_id']]
 check(asset['asset_id']+' anchors',{o['anchor_id'] for o in root.children if 'anchor_id' in o}==set(asset['required_anchor_ids']))
check('native labels remain editable',len([o for o in main.objects if o.type=='FONT'])>=30 and len([o for o in display.objects if o.type=='FONT'])>=10)
check('no source images',all(i.source=='VIEWER' and not i.filepath and not i.packed_file for i in bpy.data.images))
check('no embedded scripts',len(bpy.data.texts)==0)
check('no linked source library',len(bpy.data.libraries)==0)
check('CPU Cycles both scenes',all(s.render.engine=='CYCLES' and s.cycles.device=='CPU' for s in [main,display]))
check('no physics',all(not o.rigid_body and not o.rigid_body_constraint and not o.particle_systems for o in bpy.data.objects))
check('no animation drivers',all(not o.animation_data for o in bpy.data.objects))
check('display contains no main asset root',not any('asset_id' in o or 'anchor_id' in o for o in display.objects))
check('closed pump present','pump.closed_proxy' in main.objects)
check('closed optics present','optics.sealed_body' in main.objects)
check('no source-shaped SPP mesh',not any('SPP' in o.name.upper() for o in main.objects if o.type=='MESH'))
reuse=json.loads((P/'geometry/reused_carrier_components.json').read_text())
for part in reuse['parts']:
 o=main.objects['reuse.'+part['source_part_id']]
 check('reuse topology '+part['source_part_id'],len(o.data.vertices)==len(part['vertices']) and [list(p.vertices) for p in o.data.polygons]==part['faces'])
 check('reuse local vertices '+part['source_part_id'],all(max(abs(v.co[i]-ref[i]) for i in range(3))<1e-8 for v,ref in zip(o.data.vertices,part['vertices'])))
 check('reuse no new credit '+part['source_part_id'],o['new_unique_asset_credit']==0)
receipt={'status':'PASS','blend_sha256':hashlib.sha256((P/'geometry/sucrose_operations_lab.blend').read_bytes()).hexdigest(),'blender_version':bpy.app.version_string,'checks':checks,'main_object_count':len(main.objects),'display_object_count':len(display.objects),'limitations':'Static visual and data integrity only; no physical qualification or source geometry accuracy claim'}
(P/'review/blend_validation.json').write_text(json.dumps(receipt,indent=2));print(json.dumps({'status':'PASS','checks':len(checks)}))
