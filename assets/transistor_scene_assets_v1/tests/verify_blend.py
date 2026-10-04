"""Native editable asset integrity. No claim of calibrated physical correctness."""
import bpy,json,hashlib,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];plan=json.loads((P/'task_binding_snapshot.json').read_text());checks=[]
def check(name,v):
 assert v,name
 checks.append({'check':name,'passed':True})
main=bpy.data.scenes['TRANSISTOR_AUTHORED_METRIC'];native=bpy.data.scenes['NATIVE_LAYER_REFERENCE_METRES'];display=bpy.data.scenes['DISPLAY_ONLY_NOT_TO_SCALE']
check('three separated editable scenes',len(bpy.data.scenes)==3)
check('six exact main roots',{o['asset_id'] for o in main.objects if 'asset_id' in o}=={a['asset_id'] for a in plan['scene_assets']})
aff=json.loads((P/'affordances.json').read_text())['anchors']
check('exact anchor set',{o.name for o in main.objects if 'anchor_id' in o}=={a['scene_object'] for a in aff})
for a in aff:check('anchor target '+a['scene_object'],a['target_object'] in main.objects and main.objects[a['scene_object']].parent.name==a['asset_id'])
check('native labels editable',sum(o.type=='FONT' for o in main.objects)>30 and sum(o.type=='FONT' for o in display.objects)>10)
check('no source textures',all(i.source=='VIEWER' and not i.filepath and not i.packed_file for i in bpy.data.images))
check('no embedded text scripts',not bpy.data.texts)
check('no linked libraries',not bpy.data.libraries)
check('no scientific physics',all(not o.rigid_body and not o.rigid_body_constraint and not o.particle_systems for o in bpy.data.objects))
check('no drivers',all(not o.animation_data for o in bpy.data.objects))
check('CPU Cycles',all(s.render.engine=='CYCLES' and s.cycles.device=='CPU' for s in bpy.data.scenes))
check('no main roots in display or native',not any('asset_id' in o for s in [display,native] for o in s.objects))
check('source chip envelope',[round(x,8) for x in main.objects['chip.source_envelope'].dimensions]==[.02,.02,.0005287])
check('probe closed','probe.closed_chamber' in main.objects and 'probe.closed_window' in main.objects)
check('bias controls are closed','bias.closed_console' in main.objects)
check('services closed',all('service.'+n+'_sealed_door' in main.objects for n in ['fab','metrology','thermal']))
check('native 72 layer objects',sum('layer_index' in o for o in native.objects)==72)
check('display 72 bars',sum('layer_index' in o for o in display.objects)==72)
z=0
for l in plan['layer_contract']['layers']:
 name='native.layer.%02d.%s'%(l['index'],l['role']);o=native.objects[name];h=l['source_thickness']*(1e-6 if l['unit']=='um' else 1e-9)
 check('native source thickness '+str(l['index']),math.isclose(o.dimensions.z,h,rel_tol=2e-6,abs_tol=1e-14))
 check('native local layer position '+str(l['index']),abs(o.location.z-(z+h/2))<4e-11)
 check('native unpatterned not electrical '+str(l['index']),o['unpatterned_visualization_envelope'] and not o['electrical_connectivity'] and not o['fabrication_executable'])
 d=display.objects['display.layer.%02d.%s'%(l['index'],l['role'])]
 check('display equal nonuniform bars '+str(l['index']),math.isclose(d.dimensions.z,.003,rel_tol=1e-6) and d['display_only'] and d['uniform_scale_factor']=='NONE')
 if l['role'] in ['interstack_buffer','final_cap']:check('C01 execution null '+str(l['index']),o['execution_thickness_default']=='NULL' and o['conflict_id']=='C01')
 z+=h
check('table reference total',math.isclose(z,.0005287,abs_tol=1e-12))
check('nine interstack buffers',sum(o.get('source_role')=='interstack_buffer' for o in native.objects)==9)
check('one final cap',sum(o.get('source_role')=='final_cap' for o in native.objects)==1)
reuse=json.loads((P/'geometry/reused_carrier_components.json').read_text())
for p in reuse['parts']:
 o=main.objects['reuse.'+p['source_part_id']]
 check('reuse topology '+p['source_part_id'],[list(x.vertices) for x in o.data.polygons]==p['faces'])
 check('reuse local vertices '+p['source_part_id'],all(max(abs(v.co[i]-ref[i]) for i in range(3))<1e-8 for v,ref in zip(o.data.vertices,p['vertices'])))
 check('reuse zero new credit '+p['source_part_id'],o['new_unique_asset_credit']==0)
 check('reuse unscaled '+p['source_part_id'],all(abs(o.scale[i]-p['scale'][i])<1e-7 for i in range(3)))
receipt={'status':'PASS','blend_sha256':hashlib.sha256((P/'geometry/transistor_operations_lab.blend').read_bytes()).hexdigest(),'blender_version':bpy.app.version_string,'checks':checks,'counts':{s.name:len(s.objects) for s in bpy.data.scenes},'limitations':'Static integrity only. No physical or scientific execution qualification.'}
(P/'review/blend_validation.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':'PASS','checks':len(checks)}))
