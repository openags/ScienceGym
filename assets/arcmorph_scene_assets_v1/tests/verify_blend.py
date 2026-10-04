"""Independent read-only Blender verification. Run with Blender --background --python."""
import bpy, json, math, hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
checks=[];metrics={};warnings=[]
def check(name,condition,detail=None):
    checks.append({'check':name,'passed':bool(condition),**({'detail':detail} if detail is not None else {})})
def j(n):return json.loads((P/n).read_text())
def coords(o):return [o.matrix_world @ v.co for v in o.data.vertices]
def bounds(vs):return [[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
def near(a,b,tol=2e-6):return len(a)==len(b) and all(abs(x-y)<=tol for x,y in zip(a,b))
file=P/'geometry/arcmorph_lab.blend'
bpy.ops.wm.open_mainfile(filepath=str(file));S=bpy.context.scene;bpy.context.view_layer.update()
O=bpy.data.objects
original_hidden={o.name:any(c.hide_render and c.hide_viewport for c in o.users_collection) for o in O}
# Hidden collections are not dependency-graph evaluated on reopening. Reveal only
# in this read-only process before measuring; no save or export is performed.
for collection in bpy.data.collections: collection.hide_viewport=False
bpy.context.view_layer.update()
roots=[o.name for o in O if o.name.startswith('ASSET.')]
check('exact_twelve_roots',set(roots)=={f'ASSET.A{i:02}' for i in range(1,13)})
check('root_units_and_disabled_execution',all(O[n].get('units')=='m' and O[n].get('physical_execution_enabled') is False and O[n].get('physical_geometry_validated') is False for n in roots))
check('native_metric_metre_scale',S.unit_settings.system=='METRIC' and S.unit_settings.scale_length==1)
check('no_linked_libraries',not list(bpy.data.libraries));check('no_image_textures',not [n for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE'])
check('no_embedded_scripts',not list(bpy.data.texts));check('no_physics_world',S.rigidbody_world is None)
check('no_physical_modifiers_or_bodies',all(o.rigid_body is None and o.rigid_body_constraint is None and not any(m.type in {'CLOTH','SOFT_BODY','COLLISION','FLUID'} for m in o.modifiers) for o in O))
check('no_motion_drivers_or_animation',not list(bpy.data.actions) and not [o.name for o in O if o.animation_data and (o.animation_data.action or o.animation_data.drivers)])
check('no_portable_duplicates_in_native',not any('.portable' in o.name for o in O))
fonts=[o for o in O if o.type=='FONT'];check('native_editable_text',len(fonts)>30 and all(o.data.body for o in fonts))
check('saved_render_path_relative',S.render.filepath.startswith('//') and not any(x in S.render.filepath for x in ['/'+name+'/' for name in ('workspace','tmp','root')]))
check('saved_render_path_targets_pack_evidence',Path(bpy.path.abspath(S.render.filepath)).resolve()==(P/'evidence/overview.png').resolve())
check('saved_overview_camera',S.camera is not None and S.camera.name=='CAM.overview')
check('no_external_image_paths',not [i.filepath for i in bpy.data.images if i.filepath and not i.filepath.startswith('//')])
metrics.update(object_count=len(O),mesh_count=sum(o.type=='MESH' for o in O),editable_text_count=len(fonts),material_count=len(bpy.data.materials),image_datablock_count=len(bpy.data.images),saved_render_path=S.render.filepath)
bind=j('operation_bindings.json')['operations'];check('exact_31_operation_bindings',{x['operation_id'] for x in bind}=={f'R{i:02}' for i in range(31)} and len(bind)==31)
errs=[]
for b in bind:
    for role in ('primary','control'):
        a=O.get(b[role+'_anchor']);t=O.get(b[role+'_target'])
        if not(a and t and a.get('target_object')==t.name and a.parent and a.parent.name=='ASSET.'+b['primary_asset_id'] and near(a.matrix_world.translation,t.matrix_world.translation)):
            errs.append(b['operation_id']+'.'+role)
check('all_operation_anchors_resolve_and_align',not errs,errs)
byop={b['operation_id']:b for b in bind}
req=j('requirements_snapshot.json')
check('all_accepted_requirement_operation_memberships_present',all(a['id'] in byop[op]['asset_ids'] for a in req['assets'] for op in a['operation_ids']))
stateops=j('states.json')['operations']
check('state_and_geometry_operation_asset_memberships_agree',all(set(op['asset_ids'])==set(byop[op['id']]['asset_ids']) for op in stateops))
check('rigid_demo_mount_motion_have_separate_targets',all(byop[r]['primary_target']=='qual.rigid_demo_support' and 'corner' not in byop[r]['control_target'] for r in ['R26','R27']))
A=j('affordances.json');ae=[]
for a in A['anchors']:
    obj=O.get(a['scene_object']);target=O.get(a['target_object'])
    if not(obj and target and obj.get('physical_execution_enabled') is False and near(obj.matrix_world.translation,a['translation_m']) and near(obj.matrix_world.translation,target.matrix_world.translation)):ae.append(a['anchor_id'])
check('all_affordance_anchors_resolve_disabled_and_align',not ae,ae)
check('contacts_and_proxies_unqualified',all(c['physical_grasp_enabled'] is False and c['qualified_pose'] is None for c in A['candidate_contacts']) and all(c['collision_enabled'] is False and c['fit_qualified'] is False and O[c['scene_object']].hide_render for c in A['collision_proxies']))
inv=j('asset_inventory.json');ie=[]
for asset in inv['assets']:
    for part in asset['parts']:
        o=O.get(part['scene_object'])
        if not o or not near(part['translation_m'],o.matrix_world.translation) or not near(part['dimensions_m'],o.dimensions):ie.append(part['scene_object'])
check('inventory_transforms_and_dimensions_match_native',not ie,ie[:30]);metrics['inventory_mismatch_count']=len(ie)
top=j('specimen_topology.json');variants=top['static_variants'];families=['CS1','CS2','CS3','CS4','PP1'];states=['flat','part_folded','illustrative_folded','damaged']
check('twenty_exact_family_state_exemplars',{(v['family_id'],v['state']) for v in variants}=={(f,s) for f in families for s in states} and len(variants)==20)
te=[];family_bounds={};signatures={};nonplanarity=[]
for v in variants:
    key=v['family_id']+'.'+v['state'];pn=v['panels'];es=v['creases'];vs=[];local={};g={o:set() for o in pn}
    if len(pn)!=24 or len(es)!=38 or len(set(pn))!=24:te.append(key+':counts')
    for n in pn:
        o=O.get(n)
        if not o or o.type!='MESH' or o.parent.name!='ASSET.A05' or o.get('family_id')!=v['family_id'] or o.get('static_state')!=v['state'] or o.get('physical_fold_validated') is not False:te.append(n+':identity');continue
        pv=coords(o);vs.extend(pv);local[o['panel_id']]={tuple(round(c,7) for c in p) for p in pv}
        if len(pv)!=4:te.append(n+':quad')
        elif (pv[1]-pv[0]).cross(pv[2]-pv[0]).length>1e-12:
            normal=(pv[1]-pv[0]).cross(pv[2]-pv[0]).normalized();nonplanarity.append(abs((pv[3]-pv[0]).dot(normal)))
        hidden=original_hidden[o.name]
        if hidden!=(v['state']!='illustrative_folded'):te.append(n+':visibility')
    for e in es:
        ob=O.get(e['scene_object']);a,b=e['adjacent_panel_ids'];na=key+'.'+a;nb=key+'.'+b
        if not ob or ob.get('crease_id')!=e['crease_id'] or len(local[a]&local[b])!=2:te.append(key+':edge:'+e['crease_id'])
        if any(e[z] is not None for z in ['mountain_valley','fold_order','fold_motion_limit']):te.append(key+':qualified_edge')
        g[na].add(nb);g[nb].add(na)
    seen=set();queue=[pn[0]]
    while queue:
        x=queue.pop()
        if x in seen:continue
        seen.add(x);queue.extend(g[x]-seen)
    if len(seen)!=24:te.append(key+':disconnected')
    bb=bounds(vs)
    if 'panel_surface_extent_m' in v and not near([b-a for a,b in bb],v['panel_surface_extent_m']):te.append(key+':metadata_bounds')
    family_bounds[key]={'world_bounds_m':bb,'extent_m':[b-a for a,b in bb]}
    signatures[key]=hashlib.sha256(json.dumps([[round(c,7) for c in p] for p in vs]).encode()).hexdigest()
    if v['state']=='flat' and bb[2][1]-bb[2][0]>1e-7:te.append(key+':not_flat')
check('panel_crease_identity_adjacency_connectivity_and_visibility',not te,te)
check('four_distinct_static_mesh_states_each_family',all(len({signatures[f+'.'+s] for s in states})==4 for f in families))
metrics['topology']={'states':20,'panels_per_state':24,'interior_creases_per_state':38,'total_panels':480,'total_interior_creases':760,'max_quad_nonplanarity_m':max(nonplanarity)}
metrics['specimen_world_bounds']=family_bounds
check('three_sample_two_plate_sliders',sum(o.name.startswith('rig.sample_slider.') for o in O)==3 and sum(o.name.startswith('rig.plate_slider.') for o in O)==2)
check('two_L_plate_assemblies',sum(o.name.startswith('rig.L_plate_foot.') for o in O)==2 and sum(o.name.startswith('rig.L_plate_upright.') for o in O)==2)
check('separate_corner_and_rigid_demo_support',O['qual.corner.base'].get('fixture_id')=='Q-CORNER' and O['qual.rigid_demo_support'].get('fixture_id')=='Q-RIGID')
front=(O['camera.front.glass'].matrix_world.translation-O['camera.front.body'].matrix_world.translation).normalized();side=(O['camera.side.glass'].matrix_world.translation-O['camera.side.body'].matrix_world.translation).normalized();dot=front.dot(side)
check('camera_role_housing_axes_orthogonal',abs(dot)<1e-7);metrics['camera_role_axis_dot_product']=dot
check('camera_lens_identities_distinct',O['camera.front.body'].get('camera_id')!=O['camera.side.body'].get('camera_id') and O['camera.front.body'].get('lens_id')!=O['camera.side.body'].get('lens_id') and O['camera.front.body'].get('calibrated') is False and O['camera.side.body'].get('calibrated') is False)
md=j('asset_metadata.json');check('PP1_alias_to_task_PP',md['family_aliases']=={'PP1':'PP'})
check('C01_preserved_unresolved',md['dimensional_hold']['resolution'] is None and md['dimensional_hold']['fabrication_from_source_dimensions_allowed'] is False and md['source_known_dimensions']['PP_length_methods_mm']==383.63 and md['source_known_dimensions']['PP_length_figure_mm']==383.65)
for n,length in [('width_source',.42878),('length_methods',.38363),('length_figure',.38365)]:
    o=O['DIMREF.PP.'+n];check('dimension_reference_'+n,abs(o.dimensions.x-length)<1e-7 and o.get('fabrication_allowed') is False)
check('nominal_M2_reference_diameters',all(abs(O[f'rig.M2_reference_bolt.{i}'].dimensions.x-.002)<1e-7 for i in range(3)))
check('authored_render_settings',S.render.engine=='CYCLES' and S.cycles.device=='CPU' and S.cycles.samples==96 and S.render.resolution_x==1920 and S.render.resolution_y==1280)
report={'schema':'arcmorph.independent_native_review.v1','artifact':'geometry/arcmorph_lab.blend','sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'blender_version':bpy.app.version_string,'read_only_reopened':True,'passed':all(c['passed'] for c in checks),'checks':checks,'metrics':metrics,'warnings':['Static panel embeddings may be non-planar and are not a rigid-fold solver.','Role-camera housing axes do not establish physical optical calibration.','No physical execution or source scientific reproduction was tested.']}
(P/'review/native_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('INDEPENDENT_NATIVE_RESULT',report['passed'],len(checks),json.dumps([c for c in checks if not c['passed']]))
