"""Refresh concrete operation selectors and native/portable asset metadata.
No visible geometry changes, no physical contacts or execution authorization.
"""
import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'geometry/arcmorph_lab.blend'));S=bpy.context.scene
hidden_cols=[c for c in bpy.data.collections if c.name.startswith('STATIC_VARIANT.')]
for c in hidden_cols:c.hide_viewport=False
bpy.context.view_layer.update()
fix={'R06':('fab.load_dock','fab.job_token_slot'),'R10':('rig.mount.0','rig.M2_reference_bolt.0'),'R13':('rig.L_plate_upright.0','rig.plate_control.0'),'R14':('rig.sample_slider.0','rig.sample_lock.0'),'R19':('rig.sample_slider.0','rig.sample_lock.0'),'R26':('qual.rigid_demo_support','qual.rigid.support_handle-0.25'),'R27':('qual.rigid_demo_support','qual.rigid.support_handle-0.25'),'R30':('rig.mount.0','rig.M2_reference_bolt.0')}
aff=json.loads((P/'affordances.json').read_text());bindings=json.loads((P/'operation_bindings.json').read_text())
for op in bindings['operations']:
 if op['operation_id'] not in fix:continue
 if op['operation_id']=='R06':op['primary_asset_id']='A04'
 for role,target_name in zip(['primary','control'],fix[op['operation_id']]):
  anchor_name=f"ANCHOR.{op['operation_id']}.{role}";target=bpy.data.objects[target_name];anchor=bpy.data.objects[anchor_name];anchor.parent=bpy.data.objects['ASSET.'+op['primary_asset_id']];anchor.location=target.matrix_world.translation;anchor['target_object']=target_name;op[role+'_target']=target_name
  for a in aff['anchors']:
   if a['anchor_id']==anchor_name:a['target_object']=target_name;a['translation_m']=list(anchor.location);a['asset_id']=op['primary_asset_id']
bpy.data.objects['fab.job_token_slot']['receipt_roles']='job_identity,safe_release'
bpy.data.objects['fab.job_token_slot']['trusted_evidence_required']=True
bpy.data.objects['fab.load_dock']['dual_purpose_load_and_safe_output']=True
bpy.data.objects['fab.load_dock']['safe_release_requires_trusted_receipt']=True
bpy.context.view_layer.update()
for a in aff['anchors']:a['translation_m']=list(bpy.data.objects[a['scene_object']].matrix_world.translation)
(P/'affordances.json').write_text(json.dumps(aff,indent=2)+'\n');(P/'operation_bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
top=json.loads((P/'specimen_topology.json').read_text());meta=json.loads((P/'asset_metadata.json').read_text())
for variant in top['static_variants']:
 points=[bpy.data.objects[n].matrix_world@v.co for n in variant['panels'] for v in bpy.data.objects[n].data.vertices]
 lo=[min(v[k] for v in points) for k in range(3)];hi=[max(v[k] for v in points) for k in range(3)]
 variant['nominal_generation_span_m']=[q/1000 for q in meta['authored_template_generation_parameters_mm'][variant['family_id']][:2]]
 variant['panel_surface_bounds_m']={'min':lo,'max':hi};variant['panel_surface_extent_m']=[b-a for a,b in zip(lo,hi)]
(P/'specimen_topology.json').write_text(json.dumps(top,indent=2)+'\n')
assets=[]
for aid in [f'A{i:02d}' for i in range(1,13)]:
 root=bpy.data.objects['ASSET.'+aid]
 parts=[{'scene_object':o.name,'type':o.type,'dimensions_m':list(o.dimensions),'translation_m':list(o.matrix_world.translation),'geometry_basis':'original_authored','displayed_in_default':not any(c.hide_render for c in o.users_collection),'graspable':False} for o in S.objects if o.parent==root]
 assets.append({'asset_id':aid,'root':root.name,'physical_geometry_validated':False,'parts':parts})
(P/'asset_inventory.json').write_text(json.dumps({'schema':'sciencegym.arcmorph.inventory.v1','units':'m','asset_group_count':12,'imported_mesh_count':0,'assets':assets},indent=2)+'\n')
for c in hidden_cols:c.hide_viewport=True
bpy.context.view_layer.update()
# Fonts are cloned for GLB only, then removed before saving editable native.
for o in S.objects:o.select_set(False)
font_copies=[]
for o in list(S.objects):
 if o.type=='FONT' and not any(c.hide_render for c in o.users_collection):
  cp=o.copy();cp.data=o.data.copy();S.collection.objects.link(cp);cp.name=o.name+'.portable';font_copies.append(cp);cp.select_set(True);bpy.context.view_layer.objects.active=cp;bpy.ops.object.convert(target='MESH');cp.select_set(False);o.hide_set(True)
for o in S.objects:o.select_set(o.type in {'MESH','EMPTY'} and not o.hide_render and not any(c.hide_render for c in o.users_collection) and o.name!='studio.floor' and not o.hide_get())
bpy.ops.export_scene.gltf(filepath=str(P/'geometry/arcmorph_lab.glb'),export_format='GLB',use_selection=True,export_extras=True,export_apply=True,export_yup=True)
for o in font_copies:bpy.data.objects.remove(o,do_unlink=True)
for o in S.objects:
 if o.type=='FONT':o.hide_set(False)
 o.select_set(False)
S.render.filepath='//../evidence/overview.png';S.camera=bpy.data.objects['CAM.overview'];bpy.ops.wm.save_as_mainfile(filepath=str(P/'geometry/arcmorph_lab.blend'))
print('REPAIRED_OPERATION_SELECTORS',sorted(fix),'ACTUAL_STATIC_EXTENTS_RECORDED',len(top['static_variants']))
