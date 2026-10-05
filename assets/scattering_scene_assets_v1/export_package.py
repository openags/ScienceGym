"""Reproducible allowlisted sanitized scene archive with verified byte manifest."""
from pathlib import Path
import json,hashlib,zipfile,base64
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/(ROOT.name+'.zip')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data): (ROOT/name).write_text(json.dumps(data,indent=2)+'\n')
core=['README.md','asset_binding_contract.json','build_scene.py','scene_guards.py','test_scene_guards.py','verify_scene.py','verify_pair.py','sanitize_metadata.py','export_package.py','scene_manifest.json','provenance.json','scattering_review_scene.blend','scattering_review_scene.glb','preview_01_overview.png','preview_02_preparation.png','preview_03_metrology.png','paired_task_core_reference.json']
reports=['blender_validation.json','guard_test_results.json','metadata_sanitization.json','render_receipt.json','independent_review.json','independent_review.md','independent_guard_probes.py','independent_guard_probe_results.json']
for n in core+reports:
 assert (ROOT/n).is_file(),n
 assert Path(n).name==n and not n.startswith('.')
 if n.endswith(('.json','.md','.py')):
  content=(ROOT/n).read_text()
  for prefix in ('/'+'workspace/','/'+'home/','/'+'root/'):
   assert prefix not in content, ('private_path',n)
items=[{'file':n,'bytes':(ROOT/n).stat().st_size,'sha256':sha(ROOT/n)} for n in sorted(core)]
core_hash=hashlib.sha256(json.dumps(items,sort_keys=True,separators=(',',':')).encode()).hexdigest()
write('scene_core_manifest.json',{'schema_version':'sciencegym.scene_core.v1','digest_algorithm':'sha256 of UTF-8 canonical JSON files array (sorted keys, compact separators)','files':items,'core_sha256':core_hash,'physical_execution_enabled':False,'scientific_physics_implemented':False})
files=sorted(core+reports+['scene_core_manifest.json','EXPORT_ALLOWLIST.json','DELIVERABLE_MANIFEST.json','MANIFEST.sha256'])
write('EXPORT_ALLOWLIST.json',{'files':files,'excluded':['process logs','backup scenes','bytecode','publisher material','absolute-path receipts','Library transfer metadata'],'all_paths_relative':True})
manifest_files=[n for n in files if n not in ['DELIVERABLE_MANIFEST.json','MANIFEST.sha256']]
write('DELIVERABLE_MANIFEST.json',{'schema_version':'sciencegym.deliverable_manifest.v1','self_hash_policy':'Manifest and MANIFEST.sha256 excluded from this inventory to avoid self-reference; MANIFEST.sha256 authenticates this manifest','files':[{'file':n,'bytes':(ROOT/n).stat().st_size,'sha256':sha(ROOT/n)} for n in manifest_files],'file_count_with_integrity_files':len(files),'scene_core_sha256':core_hash,'physical_execution_enabled':False})
(ROOT/'MANIFEST.sha256').write_text(''.join(sha(ROOT/n)+'  '+n+'\n' for n in files if n!='MANIFEST.sha256'))
with zipfile.ZipFile(OUT,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name in files:
  zi=zipfile.ZipInfo(name,date_time=(2026,10,4,0,0,0));zi.create_system=3;zi.external_attr=(0o100644<<16);zi.compress_type=zipfile.ZIP_DEFLATED;zi.comment=b'';zi.extra=b''
  z.writestr(zi,(ROOT/name).read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
with zipfile.ZipFile(OUT) as z:
 assert z.namelist()==files and z.testzip() is None
 assert not z.comment
 for item in z.infolist():
  assert item.filename in files and not item.filename.startswith('/') and '..' not in Path(item.filename).parts
  assert item.comment==b'' and item.extra==b'' and z.read(item.filename)==(ROOT/item.filename).read_bytes()
 for item in json.loads(z.read('DELIVERABLE_MANIFEST.json'))['files']:
  assert hashlib.sha256(z.read(item['file'])).hexdigest()==item['sha256']
# Measure actual JSON serialization with base64 overhead and reserve 64 KiB for
# tool-specific envelope fields. Final upload callers must preserve this cap.
raw=OUT.read_bytes();encoded=json.dumps({'filename':OUT.name,'content_base64':base64.b64encode(raw).decode()},separators=(',',':')).encode()
assert len(encoded)+65536<15*1024*1024
receipt={'status':'PASS','archive_file':OUT.name,'archive_bytes':len(raw),'archive_sha256':sha(OUT),'members':len(files),'core_sha256':core_hash,'verified_manifest':True,'all_archive_members_byte_verified':True,'sanitized_zip_metadata':True,'json_base64_bytes':len(encoded),'json_with_64KiB_envelope_reserve':len(encoded)+65536,'json_request_limit_bytes':15*1024*1024,'physical_execution_enabled':False,'stable_files':{n:{'bytes':(ROOT/n).stat().st_size,'sha256':sha(ROOT/n)} for n in ['scene_core_manifest.json','scene_manifest.json','asset_binding_contract.json','scattering_review_scene.blend','scattering_review_scene.glb']}}
(ROOT.parent/(ROOT.name+'_export_receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
