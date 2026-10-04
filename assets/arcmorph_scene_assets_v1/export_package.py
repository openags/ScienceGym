"""Create an explicitly allowlisted portable release, without local logs or caches."""
from pathlib import Path
import json,hashlib,zipfile
P=Path(__file__).resolve().parent
names=['README.md','asset_metadata.json','asset_inventory.json','requirements_snapshot.json','source_facts_snapshot.json','operation_binding_contract.json','operation_bindings.json','affordances.json','states.json','variants.json','specimen_topology.json','semantic_controls.py','write_contracts.py','sanitize_metadata.py','export_package.py','task_binding_snapshot.json','paired_task_receipt.json','geometry/build_scene.py','geometry/render_scene.py','geometry/repair_bindings.py','geometry/arcmorph_lab.blend','geometry/arcmorph_lab.glb','evidence/overview.png','evidence/handling.png','evidence/metrology.png','materials/materials.json','LICENSES/ATTRIBUTION.md','LICENSES/Apache-2.0.txt','LICENSES/Blender-font-notice.txt','tests/test_package.py','tests/test_semantic_controls.py','tests/test_semantic_adversarial.py','tests/verify_blend.py','tests/verify_glb_import.py','review/render_receipt.json','review/metadata_sanitization.json','review/native_verification.json','review/glb_import_verification.json','review/independent_review.json','review/INDEPENDENT_REVIEW.md']
for n in names:
 assert (P/n).is_file(),f'Missing required release member: {n}'
 assert not (P/n).is_symlink(),f'No symbolic links: {n}'
# Complete bytes are inspected, not merely exported filenames.
for n in names:
 data=(P/n).read_bytes()
 for prefix in [b'/'+b'workspace/',b'/'+b'root/',b'/'+b'home/agent/',b'/'+b'tmp/']:
  for token in [prefix,prefix.decode().encode('utf-16-le'),prefix.decode().encode('utf-16-be')]:assert token not in data,f'Private prefix in {n}'
(P/'EXPORT_ALLOWLIST.json').write_text(json.dumps({'schema':'sciencegym.explicit_export.v1','include':sorted(names+['EXPORT_ALLOWLIST.json','MANIFEST.sha256']),'exclude_policy':['local logs','backup blend files','Python caches','raw source PDFs/images/CAD','local upload receipts','archive self-inclusion'],'portable_relative_paths_only':True},indent=2)+'\n')
names+=['EXPORT_ALLOWLIST.json']
manifest=''.join(hashlib.sha256((P/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in sorted(names))
(P/'MANIFEST.sha256').write_text(manifest);names+=['MANIFEST.sha256']
zpath=P/'arcmorph_scene_assets_v1_public.zip'
with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n in sorted(names):z.write(P/n,n)
with zipfile.ZipFile(zpath) as z:
 assert z.testzip() is None;assert set(z.namelist())==set(names)
 for line in z.read('MANIFEST.sha256').decode().splitlines():
  h,n=line.split('  ',1);assert hashlib.sha256(z.read(n)).hexdigest()==h
receipt={'status':'PASS','archive':zpath.name,'sha256':hashlib.sha256(zpath.read_bytes()).hexdigest(),'bytes':zpath.stat().st_size,'members':len(names),'manifest_payload_entries':len(names)-1,'archive_crc_and_hashes_verified':True,'private_prefix_scan':'PASS','scientific_or_physical_validation':False}
(P/'export_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
