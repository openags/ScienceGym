"""Native scene integrity only; never physical, safety or scientific qualification."""
import bpy,json,hashlib,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];plan=json.loads((P/'task_binding_snapshot.json').read_text());checks=[]
def check(n,v):
 assert v,n
 checks.append({'check':n,'passed':True})
main=bpy.data.scenes['WOVEN_AUTHORED_METRIC'];display=bpy.data.scenes['DISPLAY_ONLY_1000X']
check('two separated scenes',len(bpy.data.scenes)==2)
check('exact eleven roots',{o['asset_id'] for o in main.objects if 'asset_id' in o}=={a['asset_id'] for a in plan['scene_assets']})
aff=json.loads((P/'affordances.json').read_text())['anchors'];check('exact anchors',{o.name for o in main.objects if 'anchor_id' in o}=={a['scene_object'] for a in aff})
for a in aff:
 check('anchor target '+a['scene_object'],a['target_object'] in main.objects and main.objects[a['scene_object']].parent.name==a['asset_id'])
 check('anchor coordinates '+a['scene_object'],all(math.isclose(main.objects[a['scene_object']].location[i],a['translation_m'][i],abs_tol=1e-7) for i in range(3)))
for a in plan['scene_assets']:
 for key in a['required_anchor_ids']:check('canonical anchor '+a['asset_id']+'.'+key,a['asset_id']+'.'+key in main.objects)
 check('exact operation IDs '+a['asset_id'],set(main.objects[a['asset_id']]['operation_ids'].split(','))==set(a['bind_operation_ids']))
check('editable native labels',sum(o.type=='FONT' for o in main.objects)>40 and sum(o.type=='FONT' for o in display.objects)>10)
check('no source textures',all(i.source=='VIEWER' and not i.filepath and not i.packed_file for i in bpy.data.images))
check('no embedded scripts',not bpy.data.texts);check('no linked libraries',not bpy.data.libraries)
check('no physical simulation',all(not o.rigid_body and not o.rigid_body_constraint and not o.particle_systems for o in bpy.data.objects))
check('no animation or drivers',all(not o.animation_data for o in bpy.data.objects))
check('CPU Cycles',all(s.render.engine=='CYCLES' and s.cycles.device=='CPU' for s in bpy.data.scenes))
check('metric unit',main.unit_settings.scale_length==1)
check('separate display root',display.objects['DISPLAY.woven_reference']['display_only'] and not any('asset_id' in o for o in display.objects))
n=main.objects['native.cell_reference']
for i in range(3):check('native cell dimension '+str(i),math.isclose(n.dimensions[i],60e-6,abs_tol=1e-10))
for kind in ['BCC','CUBIC']:
 d=display.objects['display.'+kind+'.cell_reference']
 for i in range(3):check('display 1000x '+kind+str(i),math.isclose(d.dimensions[i],.06,abs_tol=1e-8))
check('native fiber radius',math.isclose(main.objects['native.fiber_radius_reference'].dimensions.x/2,1e-6,abs_tol=1e-10))
check('display fiber radius',math.isclose(display.objects['display.fiber_radius_reference'].dimensions.x/2,.001,abs_tol=1e-8))
for prefix in ['fab','cpd','coat','plasma']:check('sealed disabled '+prefix,prefix+'.sealed_door' in main.objects and main.objects[prefix+'.disabled'].data.body=='NO ACTUATION')
check('closed SEM','sem.opaque_cover' in main.objects);check('closed carrier','carrier.opaque_lid' in main.objects)
check('empty fixture',not main.objects['tension.empty_gap']['specimen_present']);check('silicon support role','tension.silicon_support_role' in main.objects)
check('held geometry absent',not any('tetrakaidecahedron' in o.name.lower() for o in bpy.data.objects))
check('open display nodes',all(not o['connectivity_qualified'] for o in display.objects if 'connectivity_qualified' in o))
for o in main.objects:
 if 'asset_id' in o:check('root disabled '+o.name,not o['energy_enabled'] and not o['physical_execution'] and not o['device_io'])
receipt={'status':'PASS','blend_sha256':hashlib.sha256((P/'geometry/woven_material_lab.blend').read_bytes()).hexdigest(),'blender_version':bpy.app.version_string,'checks':checks,'counts':{s.name:len(s.objects) for s in bpy.data.scenes},'limitations':'Static integrity only; no device, safety, calibration, physics or scientific validation.'}
(P/'review/blend_validation.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':'PASS','checks':len(checks)}))
