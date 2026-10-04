"""Independent static audit; inspect native reopen or fresh GLB import. No scientific execution."""
import bpy, json, sys, re, math, hashlib
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]
pack=Path(args[0]); mode=args[1]
artifact=pack/'geometry'/('conformal_lab.blend' if mode=='native' else 'conformal_lab.glb')
if mode=='native': bpy.ops.wm.open_mainfile(filepath=str(artifact))
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(artifact))
bpy.context.view_layer.update()
req=json.loads((pack/'requirements_snapshot.json').read_text())
contract=json.loads((pack/'operation_binding_contract.json').read_text())
checks=[]
def check(name, condition, detail=None):
    checks.append({'name':name,'passed':bool(condition),'detail':detail})
objects={o.name:o for o in bpy.data.objects}
roots={k for k in objects if re.fullmatch(r'ASSET\.A\d\d',k)}
expected={f'ASSET.A{i:02}' for i in range(1,13)}
check('exact_twelve_root_selectors',roots==expected,sorted(roots))
ops={k for k in objects if re.fullmatch(r'ANCHOR\.R\d\d\.(primary|control)',k)}
expected_ops={f'ANCHOR.R{i:02}.{r}' for i in range(1,17) for r in ['primary','control']}
check('exact_32_operation_selectors',ops==expected_ops,sorted(ops))
sem={f"ANCHOR.{a['id']}.{n}" for a in req['assets'] for n in a['required_semantic_anchors']}
check('all_required_semantic_anchors',sem<=objects.keys(),{'expected_count':len(sem),'missing':sorted(sem-objects.keys())})
check('semantic_anchor_owners_and_flags',all(n in objects and objects[n].type=='EMPTY' and objects[n].parent.name=='ASSET.'+n.split('.')[1] and objects[n].get('qualified_pose')==False and objects[n].get('physical_execution_enabled')==False for n in sem))
for row in contract['operations']:
    for role in ['primary','control']:
        a=objects.get(row[role+'_anchor']); target=objects.get(row[role+'_target'])
        ok=a is not None and target is not None
        if ok:
            delta=(a.matrix_world.translation-target.matrix_world.translation).length
            ok=a.type=='EMPTY' and target.type=='MESH' and target.parent.name=='ASSET.'+row['primary_asset_id'] and a.parent.name=='ASSET.'+row['primary_asset_id'] and delta<1e-6 and a.get('target_mesh')==target.name and a.get('physical_execution_enabled')==False and a.get('qualified_pose')==False
        else: delta=None
        check(row['operation_id']+'_'+role+'_binding',ok,{'target':row[role+'_target'],'distance_m':delta})
squares=[o for o in objects.values() if re.fullmatch(r'beam\.square\.\d\d\.\d\d',o.name)]
pads=[o for o in objects.values() if re.fullmatch(r'pad\.\d\d\.\d\d',o.name)]
check('exact_480_squares',len(squares)==480,len(squares));check('exact_480_pads',len(pads)==480,len(pads))
def box(objs):
    pts=[o.matrix_world@Vector(p) for o in objs for p in o.bound_box]
    lo=[min(p[k] for p in pts) for k in range(3)];hi=[max(p[k] for p in pts) for k in range(3)]
    return {'min_m':lo,'max_m':hi,'span_m':[hi[k]-lo[k] for k in range(3)]}
def close(a,b,tol=1e-6):return len(a)==len(b) and all(abs(x-y)<tol for x,y in zip(a,b))
bounds=box(squares)
check('source_scalar_envelope_306_40_64_mm',close(bounds['span_m'],[.306,.04,.064]),bounds)
check('square_local_dimensions_4_8_40_4_8_mm',all(close(list(o.dimensions),[.0048,.04,.0048]) for o in squares),list(squares[0].dimensions) if squares else None)
check('pad_local_dimensions_3_6_0_5_3_6_mm',all(close(list(o.dimensions),[.0036,.0005,.0036]) for o in pads),list(pads[0].dimensions) if pads else None)
rotations=sorted(set(round(math.degrees(o.matrix_world.to_euler().y),5) for o in squares))
check('authored_alternating_twenty_degree_display',len(rotations)==2 and abs(rotations[0]+20)<.001 and abs(rotations[1]-20)<.001,rotations)
xs=sorted(set(round(o.matrix_world.translation.x,8) for o in squares));zs=sorted(set(round(o.matrix_world.translation.z,8) for o in squares))
check('source_counts_48_by_10',len(xs)==48 and len(zs)==10,{'x':len(xs),'z':len(zs)})
check('disconnected_square_objects_no_hinge_connector',all(o.get('topology_validated')==False and o.parent.name=='ASSET.A01' for o in squares) and {o.name for o in objects.values() if 'hinge' in o.name.lower() and o.type=='MESH'}=={'beam.hinge_gauge','beam.hinge_label'})
gauge=objects.get('beam.hinge_gauge')
check('detached_0_2_mm_hinge_datum',gauge is not None and abs(gauge.dimensions.x-.0002)<1e-7 and box([gauge])['min_m'][0]>bounds['max_m'][0])
cam=objects.get('ANCHOR.A06.optical_center');focus=objects.get('ANCHOR.A06.focus_target')
distance=(cam.matrix_world.translation-focus.matrix_world.translation).length if cam and focus else None
check('four_metre_source_camera_distance',distance is not None and abs(distance-4)<1e-6,distance)
check('no_linked_external_libraries',not bpy.data.libraries,len(bpy.data.libraries))
check('no_external_image_textures',not [im.name for im in bpy.data.images if im.source=='FILE' and im.filepath], [im.filepath for im in bpy.data.images if im.source=='FILE' and im.filepath])
check('no_rigid_or_soft_body_simulators',all(o.rigid_body is None and o.soft_body is None for o in objects.values()))
check('no_object_animation',all(o.animation_data is None for o in objects.values()))
check('all_asset_root_execution_flags_false',all(objects[n].get('physical_execution_enabled')==False for n in expected))
if mode=='native':
    check('scene_no_scientific_or_physical_execution',bpy.context.scene.get('scientific_simulation')==False and bpy.context.scene.get('physical_execution_enabled')==False)
    check('native_metric_metres',bpy.context.scene.unit_settings.system=='METRIC' and bpy.context.scene.unit_settings.scale_length==1)
    check('saved_render_path_relative',bpy.context.scene.render.filepath.startswith('//'),bpy.context.scene.render.filepath)
else:check('portable_has_no_studio_camera_or_light',not any(o.type in ['CAMERA','LIGHT'] or o.name.startswith('Studio.') for o in objects.values()))
receipt={'schema':'sciencegym.independent_static_geometry_audit.v1','mode':mode,'inspected_artifact':str(artifact.relative_to(pack)),'sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),'blender_version':bpy.app.version_string,'object_count':len(objects),'mesh_count':sum(o.type=='MESH' for o in objects.values()),'bounds':bounds,'checks':checks,'passed':all(c['passed'] for c in checks),'boundary':'Static geometry, naming, metadata and import tests only; no scientific, optical, mechanical, robot, collision or physical validation.'}
(pack/'review'/('independent_'+('native' if mode=='native' else 'glb')+'_geometry.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print('INDEPENDENT_STATIC_AUDIT',mode,receipt['passed'],[(c['name'],c['detail']) for c in checks if not c['passed']])
if not receipt['passed']:raise SystemExit(1)
