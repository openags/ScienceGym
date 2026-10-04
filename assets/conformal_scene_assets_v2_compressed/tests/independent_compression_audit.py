"""Independent exact semantic scene snapshot and compressed-save comparison.

Run in fresh Blender processes with -- snapshot <blend> <snapshot-output>.
Run with ordinary Python using compare <baseline-package> <candidate-package>
<baseline-snapshot> <candidate-snapshot>. No source file is saved or modified.
Snapshots hash exact float.hex values; all mesh coordinates/topology/attributes,
ID references, hierarchy, transforms, materials/node trees, lights, cameras,
world/render settings, custom properties and visibility are compared without
numeric tolerance. Runtime pointers, UI workspace state and file serialization
preferences are not scene semantics. Per-datablock snapshots stay outside the export; records are hashed one at a time to bound memory.
"""
import argparse, collections, copy, hashlib, json, math, sys
from pathlib import Path

SCHEMA='sciencegym.conformal.exact_scene_equivalence.v1'
EXCLUDED_RNA_PROPERTIES={
    'rna_type', 'id_data', 'original', 'preview', 'library_weak_reference',
    'is_evaluated', 'is_runtime_data', 'session_uid', 'tag',
    # Computed runtime cache/pointers do not represent saved scene state.
    'tool_settings', 'depsgraph', 'rna_path', 'is_updated', 'is_updated_data',
    'is_updated_transform', 'is_updated_geometry', 'is_updated_shading',
}
# These groups are runtime/window/editor bookkeeping rather than scene content.
EXCLUDED_DATA_COLLECTIONS={'screens','workspaces','window_managers'}

def canonical_bytes(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('utf-8')
def digest(value):return hashlib.sha256(canonical_bytes(value)).hexdigest()
def file_sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def runtime_image_probe(source,destination,opened=False):
    import bpy
    if not opened:bpy.ops.wm.open_mainfile(filepath=str(source))
    user_map=bpy.data.user_map()
    images=[]
    for im in bpy.data.images:
        refs=[]
        trees=[]
        for group in ['materials','worlds','scenes']:
            for owner in getattr(bpy.data,group):
                tree=getattr(owner,'node_tree',None)
                if tree:trees.append((group+'/'+owner.name,tree))
        trees.extend(('node_groups/'+tree.name,tree) for tree in bpy.data.node_groups)
        for owner,tree in trees:
            for node in tree.nodes:
                if getattr(node,'image',None)==im:refs.append(owner+'/nodes/'+node.name)
        for tex in bpy.data.textures:
            if getattr(tex,'image',None)==im:refs.append('textures/'+tex.name)
        for cam in bpy.data.cameras:
            for i,bg in enumerate(cam.background_images):
                if bg.image==im:refs.append('cameras/'+cam.name+'/background_images/'+str(i))
        for ob in bpy.data.objects:
            if ob.data==im:refs.append('objects/'+ob.name+'/data')
        images.append({'name':im.name,'type':im.type,'source':im.source,'users':im.users,'use_fake_user':im.use_fake_user,'has_data':im.has_data,'size':list(im.size),'pixels_length':len(im.pixels),'filepath':im.filepath,'packed_file':bool(im.packed_file),'custom_property_count':len(im.keys()),'id_user_map_references':sorted(user.name_full for user in user_map.get(im,set())),'material_world_compositor_node_texture_camera_object_references':sorted(refs)})
    result={'artifact_sha256':file_sha(source),'images':images,'reference_method':'Blender full ID user_map plus every material/world/scene/group node image socket, legacy texture, camera background image and object data image reference'}
    destination.with_suffix('.runtime_images.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

def snapshot(source,destination):
    import bpy
    bpy.ops.wm.open_mainfile(filepath=str(source))
    runtime_image_probe(source,destination,opened=True)
    for scene in bpy.data.scenes:
        for layer in scene.view_layers:layer.update()
    errors=[]
    def reference(value):
        return {'$id':value.bl_rna.identifier,'name':value.name_full,
                'library':value.library.filepath if value.library else None}
    def scalar(value,path,active):
        if value is None or isinstance(value,(str,bool,int)):return value
        if isinstance(value,float):return {'$float':value.hex()}
        if isinstance(value,set):return sorted(value)
        if isinstance(value,bpy.types.ID):return reference(value)
        if hasattr(value,'bl_rna'):return rna(value,path,active)
        if isinstance(value,dict):return {str(k):scalar(v,path+'.'+str(k),active) for k,v in sorted(value.items())}
        if hasattr(value,'to_dict'):return scalar(value.to_dict(),path,active)
        if hasattr(value,'to_list'):return scalar(value.to_list(),path,active)
        if hasattr(value,'__iter__') or (hasattr(value,'__len__') and hasattr(value,'__getitem__')):return [scalar(v,path+'['+str(i)+']',active) for i,v in enumerate(value)]
        errors.append({'path':path,'type':type(value).__name__,'error':'unsupported serialization type'})
        return {'$error':'unsupported type','type':type(value).__name__}
    def custom(value,path,active):
        if not hasattr(value,'keys'):return {}
        try:
            keys=list(value.keys())
        except TypeError:return {}
        props={str(k):scalar(value[k],path+'.custom.'+str(k),active) for k in sorted(keys)}
        return props
    def rna(value,path,active,force_id=False):
        if isinstance(value,bpy.types.ID) and not force_id:return reference(value)
        pointer=value.as_pointer() if hasattr(value,'as_pointer') else id(value)
        if pointer in active:return {'$cycle':active[pointer]}
        active={**active,pointer:path}
        out={'$rna':value.bl_rna.identifier}
        for prop in value.bl_rna.properties:
            name=prop.identifier
            if name in EXCLUDED_RNA_PROPERTIES:continue
            subpath=path+'.'+name
            try:member=getattr(value,name)
            except Exception as exc:
                errors.append({'path':subpath,'error':type(exc).__name__+': '+str(exc)})
                continue
            if prop.type=='COLLECTION':
                try:out[name]=[scalar(v,subpath+'['+str(i)+']',active) for i,v in enumerate(member)]
                except Exception as exc:errors.append({'path':subpath,'error':type(exc).__name__+': '+str(exc)})
            elif prop.type=='POINTER' and isinstance(member,bpy.types.NodeTree):
                # Owned material/world/compositor trees are embedded IDs and must
                # be walked in full, not reduced to an ID reference.
                out[name]=rna(member,subpath,active,force_id=True)
            else:
                try:out[name]=scalar(member,subpath,active)
                except Exception as exc:errors.append({'path':subpath,'error':type(exc).__name__+': '+str(exc)})
        out['$custom_properties']=custom(value,path,active)
        return out
    data={}
    for prop in bpy.data.bl_rna.properties:
        name=prop.identifier
        if prop.type!='COLLECTION' or name in EXCLUDED_DATA_COLLECTIONS:continue
        values=getattr(bpy.data,name)
        data[name]={}
        for v in sorted(values,key=lambda v:v.name_full):
            record=rna(v,name+'['+json.dumps(v.name_full)+']',{},force_id=True)
            data[name][v.name_full]={'canonical_sha256':digest(record),'rna_type':v.bl_rna.identifier,'rna_property_count':len(record)-2}
            del record
        print('SNAPSHOT_COLLECTION',name,len(data[name]),flush=True)
    # hide_get is per-view-layer and not exposed as a persisted Object RNA field.
    visibility={}
    for scene in bpy.data.scenes:
        for layer in scene.view_layers:
            visibility[scene.name+'/'+layer.name]={o.name:{'hide_get':o.hide_get(view_layer=layer),'visible_get':o.visible_get(view_layer=layer)} for o in sorted(layer.objects,key=lambda o:o.name)}
    result={'schema':SCHEMA,'blender_version':bpy.app.version_string,
            'excluded_rna_properties':sorted(EXCLUDED_RNA_PROPERTIES),
            'excluded_data_collections':sorted(EXCLUDED_DATA_COLLECTIONS),
            'datablocks':data,'view_layer_visibility':visibility,'serialization_errors':errors}
    destination.write_bytes(canonical_bytes(result)+b'\n')
    print(json.dumps({'snapshot_file':destination.name,'canonical_sha256':digest(result),
                     'datablock_counts':{k:len(v) for k,v in data.items()},'serialization_error_count':len(errors),'serialization_errors_first_20':errors[:20]}))
    if errors:raise SystemExit(2)

def compare(baseline,candidate,before_file,after_file):
    before=json.loads(before_file.read_text());after=json.loads(after_file.read_text())
    raw_before_digest=digest(before);raw_after_digest=digest(after)
    probes=[json.loads(f.with_suffix('.runtime_images.json').read_text()) for f in [before_file,after_file]]
    assert probes[0]['artifact_sha256']==file_sha(baseline/'geometry/conformal_lab.blend')
    assert probes[1]['artifact_sha256']==file_sha(candidate/'geometry/conformal_lab.blend')
    excluded=[]
    for label,scene,probe in zip(['baseline','candidate'],[before,after],probes):
        for im in probe['images']:
            empty_runtime=(im['name']=='Render Result' and im['type']=='RENDER_RESULT' and im['source']=='VIEWER' and im['users']==0 and im['use_fake_user'] is False and im['has_data'] is False and im['size']==[0,0] and im['pixels_length']==0 and im['filepath']=='' and im['packed_file'] is False and im['custom_property_count']==0 and im['id_user_map_references']==[] and im['material_world_compositor_node_texture_camera_object_references']==[])
            if empty_runtime:
                excluded.append({'side':label,'proof':im,'excluded_canonical_record':scene['datablocks']['images'].pop(im['name'])})
    diffs=[]
    def diff(a,b,path):
        if len(diffs)>=100:return
        if type(a)!=type(b):diffs.append({'path':path,'change':'type'});return
        if isinstance(a,dict):
            for k in sorted(set(a)|set(b)):
                if k not in a or k not in b:diffs.append({'path':path+'/'+k,'change':'missing'});continue
                diff(a[k],b[k],path+'/'+k)
        elif isinstance(a,list):
            if len(a)!=len(b):diffs.append({'path':path,'change':'length','before':len(a),'after':len(b)});return
            for i,(x,y) in enumerate(zip(a,b)):diff(x,y,path+'/'+str(i))
        elif a!=b:diffs.append({'path':path,'change':'value','before':a,'after':b})
    diff(before,after,'scene')
    retained=['geometry/conformal_lab.glb','evidence/overview.png','evidence/specimen.png','evidence/stations.png','semantic_controls.py']
    retained_hashes={p:{'baseline_sha256':file_sha(baseline/p),'candidate_sha256':file_sha(candidate/p),'byte_equal':(baseline/p).read_bytes()==(candidate/p).read_bytes()} for p in retained}
    section_hashes={k:{'baseline_sha256':digest(before['datablocks'][k]),'candidate_sha256':digest(after['datablocks'][k]),'datablock_count':len(after['datablocks'][k]),'equal':before['datablocks'][k]==after['datablocks'][k]} for k in sorted(set(before['datablocks'])|set(after['datablocks']))}
    expected_original='056cfd2253ab5aad183cfbae6ee21c87011439e584a81656c6b259b5cd350a19'
    src=baseline/'geometry/conformal_lab.blend';dst=candidate/'geometry/conformal_lab.blend'
    source_hash=file_sha(src)
    source_archive=baseline/'conformal_scene_assets_v1_public.zip'
    source_archive_hash=file_sha(source_archive)
    checks={'expected_baseline_native_sha256':source_hash==expected_original,
            'expected_baseline_archive_sha256':source_archive_hash=='aaf173b21e34c7245a31df4ef1066bb4f3a0c4a54d268f4a03ac9722ee9c9cce',
            'both_fresh_reopens_without_serialization_errors':not before['serialization_errors'] and not after['serialization_errors'],
            'all_canonical_scene_values_exactly_equal':before==after,
            'sole_excluded_image_is_proven_empty_unreferenced_runtime_cache':len(excluded)==1 and excluded[0]['side']=='baseline' and not probes[1]['images'],
            'portable_and_all_three_png_bytes_unchanged':all(retained_hashes[p]['byte_equal'] for p in retained[:4]),
            'semantic_guard_source_bytes_unchanged':retained_hashes['semantic_controls.py']['byte_equal'],
            'compressed_native_below_10_decimal_megabytes':dst.stat().st_size<10_000_000}
    report={'schema':SCHEMA,'decision':'PASS' if all(checks.values()) else 'FAIL',
            'baseline_package':baseline.name,'candidate_package':candidate.name,
            'method':'Two independent fresh Blender background processes reopen the baseline and compressed native files; exact per-datablock canonical JSON hashes and visibility snapshots are compared without numeric tolerance. Float.hex retains exact loaded values.',
            'scope':'Every saved non-editor scene datablock, all object transforms/hierarchy/visibility/custom properties, full mesh topology/vertices/attributes/material assignments, curves/text, cameras, lights, worlds, material/compositor nodes and links, scene/render/unit/view-layer settings. Portable and preview bytes are separately compared.',
            'checks':checks,'baseline_native_sha256':source_hash,'baseline_archive_sha256':source_archive_hash,'candidate_native_sha256':file_sha(dst),
            'inspected_artifact':'geometry/conformal_lab.blend','audit_script':'tests/independent_compression_audit.py','audit_script_sha256':file_sha(Path(__file__)),
            'baseline_native_bytes':src.stat().st_size,'candidate_native_bytes':dst.stat().st_size,
            'blender_version':after['blender_version'],'baseline_canonical_sha256':digest(before),'candidate_canonical_sha256':digest(after),
            'baseline_raw_snapshot_sha256':raw_before_digest,'candidate_raw_snapshot_sha256':raw_after_digest,
            'sole_non_scene_serialization_difference':{'kind':'Empty unused runtime Render Result image is discarded by official save','excluded_records':excluded,'fresh_image_probes':probes},
            'float_comparison':'Exact float.hex values; no rounding and no tolerance',
            'excluded_rna_properties':before['excluded_rna_properties'],'excluded_data_collections':before['excluded_data_collections'],
            'exclusion_reason':'Editor/window/workspace and sculpt/paint tool brush state, session IDs, evaluated/runtime cache pointers, original self-pointers and previews are outside scene equivalence. The sole image exclusion is separately proved to be an empty unreferenced Render Result runtime cache. Every object, geometry record, custom property, PBR/node graph, camera/light/world and render setting remains in scope.',
            'section_hashes':section_hashes,'retained_artifacts':retained_hashes,
            'differences_first_100':diffs,'serialization_errors':{'baseline':before['serialization_errors'],'candidate':after['serialization_errors']},
            'boundary':'Serialization and static semantics only; no new geometry, scientific result, source paper, physical permission or completed conversion.'}
    output=candidate/'review/compression_equivalence.json';output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'decision':report['decision'],'checks':checks,'differences_first_100':diffs,'canonical_sha256':digest(after)}))
    if not all(checks.values()):raise SystemExit(1)

if __name__=='__main__':
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    if argv[0]=='snapshot':snapshot(Path(argv[1]),Path(argv[2]))
    elif argv[0]=='compare':compare(*map(Path,argv[1:]))
    elif argv[0]=='image-probe':runtime_image_probe(Path(argv[1]),Path(argv[2]))
    else:raise SystemExit('Use snapshot or compare')
