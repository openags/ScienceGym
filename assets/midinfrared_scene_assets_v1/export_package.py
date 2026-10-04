"""Explicit allowlisted original-only release; no source PDFs, logs or backups."""
from pathlib import Path
import json, hashlib, zipfile
P=Path(__file__).resolve().parent
names=['README.md','asset_metadata.json','asset_inventory.json','requirements_snapshot.json','source_facts_snapshot.json','branches_snapshot.json','stations_snapshot.json','unknowns_snapshot.json','operation_binding_contract.json','operation_bindings.json','affordances.json','specimen_geometry.json','assembly_contract.json','station_layout.json','states.json','semantic_controls.py','sanitize_metadata.py','export_package.py','verify_pair.py','task_binding_snapshot.json','paired_task_receipt.json','geometry/build_scene.py','geometry/midinfrared_lab.blend','geometry/midinfrared_lab.glb','evidence/overview.png','evidence/samples.png','evidence/optics.png','materials/materials.json','LICENSES/ATTRIBUTION.md','LICENSES/Apache-2.0.txt','LICENSES/Blender-font-notice.txt','tests/test_package.py','tests/test_semantic_controls.py','tests/test_independent_semantic_audit.py','tests/independent_geometry_audit.py','tests/independent_package_audit.py','review/render_receipt.json','review/metadata_sanitization.json','review/independent_native_geometry.json','review/independent_glb_geometry.json','review/independent_review.json','review/independent_package_audit.json','review/INDEPENDENT_REVIEW.md']
for n in names:
    p=P/n
    assert p.is_file() and not p.is_symlink(), 'Missing or symlink release member: '+n
    data=p.read_bytes()
    for prefix in [b'/'+b'workspace/',b'/'+b'root/',b'/'+b'home/agent/',b'/'+b'tmp/']:
        for token in [prefix,prefix.decode().encode('utf-16-le'),prefix.decode().encode('utf-16-be')]:
            assert token not in data, 'Private prefix in '+n
assert json.loads((P/'review/independent_review.json').read_text())['passed'] is True
assert json.loads((P/'paired_task_receipt.json').read_text())['passed'] is True
allow={'schema':'sciencegym.explicit_export.v1','include':sorted(names+['EXPORT_ALLOWLIST.json','MANIFEST.sha256']),'excluded':['local logs','backup blend files','Python caches','input source PDFs/images/movies/CAD/code/weights','upload receipts','archive self-inclusion'],'portable_relative_paths_only':True}
(P/'EXPORT_ALLOWLIST.json').write_text(json.dumps(allow,indent=2)+'\n');names+=['EXPORT_ALLOWLIST.json']
(P/'MANIFEST.sha256').write_text(''.join(hashlib.sha256((P/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in sorted(names)));names+=['MANIFEST.sha256']
zpath=P/'midinfrared_scene_assets_v1_public.zip'
with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for n in sorted(names):z.write(P/n,n)
with zipfile.ZipFile(zpath) as z:
    assert z.testzip() is None and set(z.namelist())==set(names)
    for line in z.read('MANIFEST.sha256').decode().splitlines():
        h,n=line.split('  ',1);assert hashlib.sha256(z.read(n)).hexdigest()==h
receipt={'status':'PASS','archive':zpath.name,'sha256':hashlib.sha256(zpath.read_bytes()).hexdigest(),'bytes':zpath.stat().st_size,'members':len(names),'manifest_payload_entries':len(names)-1,'archive_crc_and_hashes_verified':True,'private_prefix_scan':'PASS','scientific_or_physical_validation':False}
(P/'export_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
