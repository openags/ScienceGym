"""Independent binary inspection and fresh Blender GLB reimport; no asset edits."""
import bpy,json,struct,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];f=P/'geometry/arcmorph_lab.glb';raw=f.read_bytes();checks=[];metrics={}
def check(n,c,d=None):checks.append({'check':n,'passed':bool(c),**({'detail':d} if d is not None else {})})
magic,version,length=struct.unpack_from('<4sII',raw,0);check('glb2_header',magic==b'glTF' and version==2 and length==len(raw))
pos=12;chunks=[];document=None
while pos<len(raw):
    size,kind=struct.unpack_from('<I4s',raw,pos);body=raw[pos+8:pos+8+size];chunks.append((kind.decode('ascii'),size));pos+=8+size
    if kind==b'JSON':document=json.loads(body)
check('embedded_binary_only',len(document.get('buffers',[]))==1 and 'uri' not in document['buffers'][0] and any(c[0]=='BIN\x00' for c in chunks))
check('no_copied_images_or_external_dependencies',not document.get('images') and not document.get('textures') and not any('uri' in x for x in document.get('buffers',[])))
check('no_animation_or_render_cameras',not document.get('animations') and not document.get('cameras'))
nodes=document.get('nodes',[]);names={n.get('name') for n in nodes};check('exact_twelve_asset_root_nodes',len([n for n in names if n and n.startswith('ASSET.')])==12 and all(f'ASSET.A{i:02}' in names for i in range(1,13)))
check('all_sixty_two_primary_control_anchors',all(f'ANCHOR.R{i:02}.{r}' in names for i in range(31) for r in ['primary','control']))
check('no_static_alternative_states_exported',not any(n and any(n.startswith(f+'.'+s+'.') for f in ['CS1','CS2','CS3','CS4','PP1'] for s in ['flat','part_folded','damaged']) for n in names))
check('no_disabled_collision_proxies_or_studio_floor',not any(n and (n.startswith('COLLISION.') or n=='studio.floor') for n in names))
check('no_true_execution_flag',not any(n.get('extras',{}).get('physical_execution_enabled') is True for n in nodes))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(f));bpy.context.view_layer.update();O=bpy.data.objects
check('fresh_import_retains_twelve_roots',all(f'ASSET.A{i:02}' in O for i in range(1,13)))
check('fresh_import_is_mesh_and_empty_only',all(o.type in {'MESH','EMPTY'} for o in O))
check('portable_text_is_mesh',len([o for o in O if '.portable' in o.name and o.type=='MESH'])>30)
check('fresh_import_no_alternate_state_geometry',not any(any(o.name.startswith(f+'.'+s+'.') for f in ['CS1','CS2','CS3','CS4','PP1'] for s in ['flat','part_folded','damaged']) for o in O))
counts={}
for fam in ['CS1','CS2','CS3','CS4','PP1']:
    prefix=fam+'.illustrative_folded.';counts[fam]={'panels':len([o for o in O if o.name.startswith(prefix+'P')]),'creases':len([o for o in O if o.name.startswith(prefix+'E')])}
check('five_default_families_with_24_panels_38_creases',all(c=={'panels':24,'creases':38} for c in counts.values()),counts)
def near(a,b,tol=3e-6):return len(a)==len(b) and all(abs(x-y)<tol for x,y in zip(a,b))
err=[]
for b in json.loads((P/'operation_bindings.json').read_text())['operations']:
    for role in ['primary','control']:
        a=O.get(b[role+'_anchor']);t=O.get(b[role+'_target'])
        if not a or not t or a.get('target_object')!=t.name or not near(a.matrix_world.translation,t.matrix_world.translation):err.append(b['operation_id']+'.'+role)
check('imported_operation_anchors_retain_targets_and_positions',not err,err)
check('nominal_metre_reference_scale_survives_import',abs(O['DIMREF.PP.width_source'].dimensions.x-.42878)<1e-6 and abs(O['DIMREF.PP.length_methods'].dimensions.x-.38363)<1e-6 and abs(O['DIMREF.PP.length_figure'].dimensions.x-.38365)<1e-6)
check('separate_qualitative_fixture_identities_survive',O['qual.corner.base'].get('fixture_id')=='Q-CORNER' and O['qual.rigid_demo_support'].get('fixture_id')=='Q-RIGID')
check('materials_survive',len(bpy.data.materials)>=15)
metrics.update(imported_objects=len(O),imported_meshes=sum(o.type=='MESH' for o in O),imported_materials=len(bpy.data.materials),glb_bytes=len(raw),glb_nodes=len(nodes),glb_meshes=len(document.get('meshes',[])),chunks=chunks)
report={'schema':'arcmorph.independent_glb_review.v1','artifact':'geometry/arcmorph_lab.glb','sha256':hashlib.sha256(raw).hexdigest(),'blender_version':bpy.app.version_string,'fresh_import_completed':True,'passed':all(c['passed'] for c in checks),'checks':checks,'metrics':metrics,'limitations':['Default visible state only; all 20 alternatives are in native Blender.','GLB visual materials and object extras do not implement motion or physics.','No independent third-party engine import was attempted.']}
(P/'review/glb_import_verification.json').write_text(json.dumps(report,indent=2)+'\n');print('INDEPENDENT_GLB_RESULT',report['passed'],len(checks),json.dumps([c for c in checks if not c['passed']]))
