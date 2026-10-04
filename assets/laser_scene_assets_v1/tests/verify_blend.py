"""Native scene integrity only; never physical or scientific qualification."""
import bpy,json,hashlib,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];plan=json.loads((P/'task_binding_snapshot.json').read_text());checks=[]
def check(n,v):
 assert v,n
 checks.append({'check':n,'passed':True})
main=bpy.data.scenes['LASER_AUTHORED_METRIC'];display=bpy.data.scenes['DISPLAY_ONLY_1000X']
check('two separated scenes',len(bpy.data.scenes)==2)
check('ten exact roots',{o['asset_id'] for o in main.objects if 'asset_id' in o}=={a['asset_id'] for a in plan['scene_assets']})
aff=json.loads((P/'affordances.json').read_text())['anchors']
check('exact anchors',{o.name for o in main.objects if 'anchor_id' in o}=={a['scene_object'] for a in aff})
for a in aff:check('anchor target '+a['scene_object'],a['target_object'] in main.objects and main.objects[a['scene_object']].parent.name==a['asset_id'])
for a in plan['scene_assets']:
 for key in a['required_anchor_ids']:check('canonical anchor '+a['asset_id']+'.'+key,a['asset_id']+'.'+key in main.objects)
check('editable native labels',sum(o.type=='FONT' for o in main.objects)>45 and sum(o.type=='FONT' for o in display.objects)>10)
check('no source textures',all(i.source=='VIEWER' and not i.filepath and not i.packed_file for i in bpy.data.images))
check('no embedded scripts',not bpy.data.texts)
check('no linked libraries',not bpy.data.libraries)
check('no physical simulation',all(not o.rigid_body and not o.rigid_body_constraint and not o.particle_systems for o in bpy.data.objects))
check('no animation or drivers',all(not o.animation_data for o in bpy.data.objects))
check('CPU Cycles',all(s.render.engine=='CYCLES' and s.cycles.device=='CPU' for s in bpy.data.scenes))
check('metre native scene',main.unit_settings.scale_length==1)
check('separate display root',display.objects['DISPLAY.pic_nominal_footprint']['display_only'] and not any('asset_id' in o for o in display.objects))
n=main.objects['pic.native_footprint_reference'];d=display.objects['display.pic_footprint_reference']
for i,expected in enumerate([.00095,.00048]):check('native footprint dimension '+str(i),math.isclose(n.dimensions[i],expected,abs_tol=1e-10));check('display 1000x dimension '+str(i),math.isclose(d.dimensions[i],expected*1000,abs_tol=1e-7))
check('no die thickness or traced circuit',n.dimensions.z==0 and d.dimensions.z==0 and not n['physical_die'] and not n['die_thickness_modelled'])
check('footprint area',math.isclose(n.dimensions.x*n.dimensions.y,4.56e-7,rel_tol=1e-7))
for i in range(1,4):check('sealed disabled DFB '+str(i),f'dfb{i}.sealed_module' in main.objects and main.objects[f'dfb{i}.output.cap']['capped'] and main.objects[f'dfb{i}.disabled'].data.body=='DISABLED')
check('laser disabled label',main.objects['enclosure.energy'].data.body=='ENERGY DISABLED')
check('heaters off label',main.objects['enclosure.heaters'].data.body=='HEATERS 1 + 2: OFF')
check('SiN numerical only',main.objects['design.sin'].data.body=='SiN: NUMERICAL ONLY')
check('reference comb route',main.objects['reference.title'].data.body=='COMB-REFERENCED')
check('FPGA relative only',main.objects['fpga.relative'].data.body=='RELATIVE ERROR ONLY')
check('empty output panels',main.objects['fpga.no_signal'].data.body=='NO SIGNAL / NO PSD' and main.objects['control.none'].data.body=='NO LOCK / NO CURRENT CONTROL')
check('opaque enclosure exists','enclosure.closed_cover' in main.objects and 'package.opaque_lid' in main.objects)
check('no light emission materials',all(m.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value==0 for m in bpy.data.materials if m.use_nodes and m.node_tree.nodes.get('Principled BSDF')))
for o in main.objects:
 if 'asset_id' in o:check('root disabled '+o.name,not o['laser_energy_enabled'] and not o['physical_execution'] and not o['device_io'])
 if o.name.startswith('routing.'):check('dormant visual route '+o.name,not o['signal_present'] and o['route_status']=='authored_dormant_visual_only')
reuse=json.loads((P/'geometry/reused_carrier_components.json').read_text())
for p in reuse['parts']:
 o=main.objects['reuse.'+p['source_part_id']]
 check('reuse topology '+p['source_part_id'],[list(x.vertices) for x in o.data.polygons]==p['faces'])
 check('reuse local vertices '+p['source_part_id'],len(o.data.vertices)==len(p['vertices']) and all(max(abs(v.co[i]-ref[i]) for i in range(3))<1e-8 for v,ref in zip(o.data.vertices,p['vertices'])))
 check('reuse zero credit '+p['source_part_id'],o['new_unique_asset_credit']==0)
 check('reuse original scale '+p['source_part_id'],all(abs(o.scale[i]-p['scale'][i])<1e-7 for i in range(3)))
check('package separate from empty carrier',main.objects['package.closed_case'].location.y-main.objects['package.closed_case'].dimensions.y/2 > main.objects['reuse.carrier.loaded.base'].location.y+main.objects['reuse.carrier.loaded.base'].dimensions.y/2)
receipt={'status':'PASS','blend_sha256':hashlib.sha256((P/'geometry/laser_control_lab.blend').read_bytes()).hexdigest(),'blender_version':bpy.app.version_string,'checks':checks,'counts':{s.name:len(s.objects) for s in bpy.data.scenes},'limitations':'Static integrity only; no device, safety, calibration, physics or scientific validation.'}
(P/'review/blend_validation.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':'PASS','checks':len(checks)}))
