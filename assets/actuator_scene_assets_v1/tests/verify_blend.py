"""Static native-scene integrity; not scientific or physical qualification."""
import bpy,json,hashlib,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];plan=json.loads((P/'task_binding_snapshot.json').read_text());checks=[]
def check(n,v):
 assert v,n
 checks.append({'check':n,'passed':True})
main=bpy.data.scenes['ACTUATOR_AUTHORED_METRIC'];display=bpy.data.scenes['DISPLAY_ONLY_10X']
check('two separated scenes',len(bpy.data.scenes)==2)
check('seven exact roots',{o['asset_id'] for o in main.objects if 'asset_id' in o}=={a['asset_id'] for a in plan['scene_assets']})
aff=json.loads((P/'affordances.json').read_text())['anchors']
check('exact anchors',{o.name for o in main.objects if 'anchor_id' in o}=={a['scene_object'] for a in aff})
for a in aff:check('anchor target '+a['scene_object'],a['target_object'] in main.objects and main.objects[a['scene_object']].parent.name==a['asset_id'])
for a in plan['scene_assets']:
 for key in a['required_anchor_ids']:check('canonical anchor '+a['asset_id']+'.'+key,a['asset_id']+'.'+key in main.objects)
check('editable native labels',sum(o.type=='FONT' for o in main.objects)>25 and sum(o.type=='FONT' for o in display.objects)>5)
check('no source textures',all(i.source=='VIEWER' and not i.filepath and not i.packed_file for i in bpy.data.images))
check('no embedded scripts',not bpy.data.texts)
check('no linked libraries',not bpy.data.libraries)
check('no mechanical physics',all(not o.rigid_body and not o.rigid_body_constraint and not o.particle_systems for o in bpy.data.objects))
check('no animation or drivers',all(not o.animation_data for o in bpy.data.objects))
check('CPU Cycles',all(s.render.engine=='CYCLES' and s.cycles.device=='CPU' for s in bpy.data.scenes))
check('metre native scene',main.unit_settings.scale_length==1)
check('separated display root',display.objects['DISPLAY.representative_lattice']['display_only'] and not any('asset_id' in o for o in display.objects))
check('native 5mm gauge',math.isclose(main.objects['reference_5mm.length'].dimensions.z,.005,abs_tol=1e-7))
check('display 50mm gauge',math.isclose(display.objects['display.5mm.length'].dimensions.z,.05,abs_tol=1e-7))
check('ruler 1mm spacing',all(math.isclose(main.objects['ruler.tick.'+str(i+1)].location.z-main.objects['ruler.tick.'+str(i)].location.z,.001,abs_tol=3e-8) for i in range(60)))
check('static ruler 60mm extent',math.isclose(main.objects['ruler.tick.60'].location.z-main.objects['ruler.tick.0'].location.z,.060,abs_tol=3e-8))
for o in main.objects:
 if o.name.startswith('actuator_specimen_representative.'):
  check('generic lattice '+o.name,o.get('representative_only') and not o['optimized_design'] and not o['material_physics'])
  d=display.objects[o.name.replace('actuator_specimen_representative.','display.lattice.')]
  check('10x lattice dimensions '+o.name,all(math.isclose(d.dimensions[i],10*o.dimensions[i],abs_tol=1e-6) for i in range(3)))
check('one specimen plus explanatory copy',sum(o.name.startswith('actuator_specimen_representative.base') for o in main.objects)==1)
check('parked stage positive x gap',main.objects['actuator_moving_clamp'].location.x-main.objects['actuator_moving_clamp'].dimensions.x/2 > max((o.matrix_world@v.co).x for o in main.objects if o.name.startswith('actuator_specimen_representative.cell') for v in o.data.vertices))
check('fabrication sealed','fabrication.sealed_door' in main.objects)
check('direction hold visible','DIRECTION: HOLD'==main.objects['hold.title'].data.body)
reuse=json.loads((P/'geometry/reused_carrier_components.json').read_text())
for p in reuse['parts']:
 o=main.objects['reuse.'+p['source_part_id']]
 check('reuse topology '+p['source_part_id'],[list(x.vertices) for x in o.data.polygons]==p['faces'])
 check('reuse local vertices '+p['source_part_id'],all(max(abs(v.co[i]-ref[i]) for i in range(3))<1e-8 for v,ref in zip(o.data.vertices,p['vertices'])))
 check('reuse zero credit '+p['source_part_id'],o['new_unique_asset_credit']==0)
 check('reuse original scale '+p['source_part_id'],all(abs(o.scale[i]-p['scale'][i])<1e-7 for i in range(3)))
receipt={'status':'PASS','blend_sha256':hashlib.sha256((P/'geometry/actuator_metrology_lab.blend').read_bytes()).hexdigest(),'blender_version':bpy.app.version_string,'checks':checks,'counts':{s.name:len(s.objects) for s in bpy.data.scenes},'limitations':'Static integrity only. No physics, calibration, physical execution or performance validation.'}
(P/'review/blend_validation.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':'PASS','checks':len(checks)}))
