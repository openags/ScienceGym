"""Reopen/import audit of static geometry; not a physical-interface qualification."""
import bpy,json,pathlib,math
from mathutils import Vector
P=pathlib.Path(__file__).resolve().parents[1];C=json.loads((P/'scene_binding_contract.json').read_text());report={'native':{},'glb':{},'checks':[]}
def require(cond,name,detail=None):
 report['checks'].append({'check':name,'passed':bool(cond),'detail':detail})
 if not cond:raise AssertionError(name+': '+str(detail))
def dims(o):return [float(v) for v in o.dimensions]
def bb(o):
 p=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(v[i] for v in p),max(v[i] for v in p)] for i in range(3)]
bpy.ops.wm.open_mainfile(filepath=str(P/'geometry/thermalmeta_lab.blend'));s=bpy.context.scene;bpy.context.view_layer.update()
require(s.render.engine=='CYCLES' and s.cycles.device=='CPU','cpu_render_configuration')
require(s.get('physical_actuation_enabled') is False,'actuation_disabled')
require(s.get('physics_simulation_performed') is False,'no_physics_claim')
require(not any(o.rigid_body or o.rigid_body_constraint for o in s.objects),'no_rigid_body_physics')
require(len(bpy.data.texts)==0,'no_embedded_scripts')
require(not any(i.filepath for i in bpy.data.images if i.source not in {'GENERATED','VIEWER'}),'no_external_image_textures')
require(len(s.timeline_markers)==0 and not any(o.animation_data for o in s.objects),'no_animated_telemetry')
for a in C['anchors']:
 require(a['object_name'] in bpy.data.objects,'native_anchor_exists_'+a['anchor_id'])
 o=bpy.data.objects[a['object_name']];require(o.type=='EMPTY' and o.get('anchor_id')==a['anchor_id'],'native_anchor_semantics_'+a['anchor_id']);require((o.matrix_world.translation-Vector(a['position_m'])).length<1e-6,'native_anchor_position_'+a['anchor_id'])
for c in C['condition_views']:
 o=bpy.data.objects[c['envelope_object']];pad=bpy.data.objects[c['support_object']];cover=bpy.data.objects[c['cover_object']]
 require(all(abs(a-b)<1e-6 for a,b in zip(dims(o),[.12,.12,.0045])),'nominal_envelope_'+c['condition_id'],dims(o))
 gap=bb(o)[2][0]-bb(pad)[2][1];require(abs(gap)<1e-6,'static_support_'+c['condition_id'],gap)
 require(bb(cover)[2][0]>bb(o)[2][1]+.01,'closed_cover_clearance_'+c['condition_id'])
 require(o.get('specimen_id')==c['specimen_id'],'shared_specimen_identity_'+c['condition_id'])
for pair in json.loads((P/'contact_contract.json').read_text())['contacts']:
 gap=bb(bpy.data.objects[pair['supported_object']])[2][0]-bb(bpy.data.objects[pair['support_object']])[2][1];require(abs(gap-pair['expected_vertical_gap_m'])<=pair['tolerance_m'],'all_static_supports_'+pair['supported_object'],gap)
for n in ['A06.closed_glass_front','A06.closed_lid','A06.guard_back','A06.bath_lid','A03.closed_front','A10.parking_support']:
 require(n in bpy.data.objects,'guard_or_support_'+n)
expected={a['object_name']:list(bpy.data.objects[a['object_name']].matrix_world.translation) for a in C['anchors']}
expected_dims={c['envelope_object']:dims(bpy.data.objects[c['envelope_object']]) for c in C['condition_views']}
report['native']={'objects':len(s.objects),'meshes':len([o for o in s.objects if o.type=='MESH']),'text_objects':len([o for o in s.objects if o.type=='FONT']),'anchors':len(C['anchors']),'compressed_file':True,'render_filepath':s.render.filepath,'no_external_images':True}
# Refresh exact manifest from final native object contents.
manifest={'schema':'sciencegym3d.thermalmeta.scene.v1','source_doi':C['source_doi'],'asset_package':C['asset_package'],'physical_actuation_enabled':False,'physics_simulation_performed':False,'coordinate_system':C['coordinate_system'],'objects':[],'contacts':json.loads((P/'contact_contract.json').read_text())['contacts'],'render_engine':'CYCLES','render_device':'CPU'}
for o in s.objects:manifest['objects'].append({'name':o.name,'type':o.type,'asset_id':o.get('asset_id'),'anchor_id':o.get('anchor_id'),'parent':o.parent.name if o.parent else None,'location_m':[round(v,8) for v in o.matrix_world.translation],'dimensions_m':[round(v,8) for v in o.dimensions]})
(P/'scene_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'geometry/thermalmeta_lab.glb'));bpy.context.view_layer.update()
for n,pos in expected.items():
 require(n in bpy.data.objects,'glb_anchor_exists_'+n)
 o=bpy.data.objects[n];require((o.matrix_world.translation-Vector(pos)).length<2e-5,'glb_anchor_position_'+n)
 require(o.get('anchor_id')==n,'glb_anchor_metadata_'+n)
for n,d in expected_dims.items():
 require(n in bpy.data.objects,'glb_envelope_exists_'+n);require(all(abs(a-b)<2e-5 for a,b in zip(dims(bpy.data.objects[n]),d)),'glb_nominal_dimensions_'+n)
require(abs(bpy.data.materials['glass'].node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value-.07)<1e-6,'glb_portable_clear_panel_alpha')
report['glb']={'objects':len(bpy.context.scene.objects),'anchors':len(expected),'all_nominal_envelopes_preserved':True,'all_anchor_extras_preserved':True,'units_reimported':'metres','portable_text':'mesh geometry'}
report['passed']=all(x['passed'] for x in report['checks']);report['limits']=['Numerical contact tests cover 20 authored static specimen and fixture supports only','No collision dynamics, gripper force, safety clearance, reachability, instrument calibration or real hardware fit qualified','No source solver or thermal simulation executed']
(P/'review/geometry_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('AUDIT_PASS',len(report['checks']))
