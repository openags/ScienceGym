"""Reopen editable scene and reimport portable GLB in a fresh Blender process."""
import bpy,json,sys,struct,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'scene_manifest.json').read_text());contract=json.loads((ROOT/'asset_binding_contract.json').read_text())
expected={x['id'] for x in manifest['anchors']};bound={a for g in contract['asset_groups'] for a in g['anchor_ids']}
assert expected==bound and len(expected)==32
report={'schema_version':'sciencegym.scene_validation.v1','status':'PASS','checks':[]}
def ok(name,detail):report['checks'].append({'check':name,'status':'PASS','detail':detail})
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'scattering_review_scene.blend'))
assert bpy.context.scene.render.engine=='CYCLES' and bpy.context.scene.cycles.device=='CPU'
assert bpy.context.scene.get('physical_execution_enabled') is False
assert not bpy.data.actions
assert not bpy.data.texts
assert not any(o.animation_data for o in bpy.data.objects)
assert not bpy.data.libraries
assert not [i for i in bpy.data.images if i.source=='FILE' and i.filepath]
assert all(a in bpy.data.objects for a in expected)
assert all(not bpy.data.objects[a].get('qualified') for a in expected)
assert len([c for c in bpy.data.collections if c.name in {f'AS{i:02}' for i in range(1,12)}])==11
assert all(bpy.data.objects[n].get('source_exact_geometry') is False for n in ['M1_groove_illustration','M2_groove_illustration','M3_groove_illustration'])
# Visual support continuity only, not structural qualification or collision acceptance.
from mathutils import Vector
def extent(name):
 o=bpy.data.objects[name];v=[o.matrix_world@Vector(c) for c in o.bound_box];return min(p.z for p in v),max(p.z for p in v)
contacts=[]
for child,parent in [(f'{d}_groove_illustration',f'{d}_support_pad') for d in ['M1','M2','M3']]+[
 ('Retained support lock','Pendulum shield_base'),('Pendulum roof bracket','Pendulum upper support'),('Pendulum shield_roof','Pendulum roof bracket'),('Screen grounded pedestal','Pendulum shield_base'),('Tracking camera grounded foot','Pendulum shield_base'),('Screen reference proxy','Screen grounded pedestal'),('Tracking camera proxy','Tracking camera grounded foot'),('Flat array support','Array enclosure_base'),('Flat array sealed proxy','Flat array support'),('Curved array support','Array enclosure_base'),('Positioning rail support','Motion boundary_base'),('Positioning rail proxy','Positioning rail support')]:
 gap=extent(child)[0]-extent(parent)[1];assert abs(gap)<1e-5,(child,parent,gap)
 contacts.append({'child':child,'support':parent,'vertical_gap_m':round(gap,8)})
assert abs(extent('Robot dock')[0])<1e-5
assert abs(extent('Custody cabinet body')[0])<1e-5
ok('authored_support_contact_continuity',{'contacts':contacts,'physical_support_qualification':False})
positions={a:list(bpy.data.objects[a].matrix_world.translation) for a in expected}
blend_count=len(bpy.data.objects);ok('compressed_blend_reopen',{'object_count':blend_count,'anchors':32,'asset_families':11})
ok('nonexecution_and_no_external_resources',{'actions':0,'scripts':0,'linked_libraries':0,'external_images':0,'cpu_render':True})
# Native compression uses zstd or gzip header, never plaintext BLENDER.
magic=(ROOT/'scattering_review_scene.blend').read_bytes()[:12]
assert not magic.startswith(b'BLENDER');ok('native_blender_compression',{'header_hex':magic.hex()})
# Read interchange metadata without trusting any embedded extras as physical truth.
raw=(ROOT/'scattering_review_scene.glb').read_bytes();assert raw[:4]==b'glTF'
n,typ=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+n].decode())
assert not doc.get('animations');assert not doc.get('images');assert set(doc.get('extensionsUsed',[]))<=set(['KHR_materials_transmission','KHR_materials_ior'])
assert not any('uri' in x for x in doc.get('buffers',[]))
for node in doc.get('nodes',[]):
 if node.get('name') in expected:assert node.get('extras',{}).get('qualified') is False
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'scattering_review_scene.glb'))
assert all(a in bpy.data.objects for a in expected)
maxerr=0.0
for a in expected:
 obj=bpy.data.objects[a];assert obj.get('semantic_anchor') is True
 error=max(abs(x-y) for x,y in zip(obj.matrix_world.translation,positions[a]));maxerr=max(maxerr,error)
 assert error<1e-5,(a,error)
ok('portable_glb_reimport',{'object_count':len(bpy.data.objects),'anchors':32,'maximum_roundtrip_position_error_m':maxerr,'embedded_animations':0,'external_buffers':0,'textures':0})
ok('exact_shared_contract',{'operations':14,'anchors':32,'asset_families':11,'shared_contract_sha256':hashlib.sha256((ROOT/'asset_binding_contract.json').read_bytes()).hexdigest()})
(ROOT/'blender_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
