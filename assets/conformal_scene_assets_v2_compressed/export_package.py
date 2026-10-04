"""Create a deterministic, strict-allowlist original-assets release ZIP."""
from pathlib import Path
import json,hashlib,zipfile,re,struct
P=Path(__file__).resolve().parent
base=['README.md','asset_metadata.json','requirements_snapshot.json','source_facts_snapshot.json','unknowns_snapshot.json','source_conflicts_snapshot.json','branches_snapshot.json','stations_snapshot.json','operation_binding_contract.json','operation_bindings.json','asset_inventory.json','affordances.json','specimen_geometry.json','states.json','assembly_contract.json','semantic_controls.py','sanitize_metadata.py','export_package.py','materials/materials.json','geometry/build_scene.py','geometry/compress_scene.py','tests/independent_compression_audit.py','review/compression_equivalence.json','geometry/conformal_lab.blend','geometry/conformal_lab.glb','evidence/overview.png','evidence/specimen.png','evidence/stations.png','LICENSES/ATTRIBUTION.md','LICENSES/Apache-2.0.txt','LICENSES/Blender-font-notice.txt','tests/test_semantic_controls.py','tests/test_package.py','review/render_receipt.json','review/metadata_sanitization.json']
# Only named accepted evidence can be added; no recursive directory packaging.
optional=['tests/independent_geometry_audit.py','tests/test_independent_semantic_audit.py','tests/independent_package_audit.py','review/independent_native_geometry.json','review/independent_glb_geometry.json','review/independent_package_audit.json','review/independent_review.json','review/INDEPENDENT_REVIEW.md','paired_task_receipt.json','task_binding_snapshot.json','verify_pair.py','core_freeze.json']
files=base+[x for x in optional if (P/x).is_file()]
for name in files:
 f=P/name
 assert f.is_file(),name
 assert f.resolve().is_relative_to(P.resolve()) and not f.is_symlink(),name
 if f.suffix in {'.md','.json','.py','.txt'}:
  s=f.read_text();assert ('/'+'workspace'+'/') not in s and ('/'+'tmp'+'/') not in s,name+' private filesystem path'
 assert not name.lower().endswith(('.pdf','.mp4','.blend1','.pyc')),name
# Require all images genuine and pixel-preserving metadata scrub complete.
rr=json.loads((P/'review/render_receipt.json').read_text());assert len(rr['renders'])==3
for x in rr['renders']:
 assert x['engine']=='CYCLES' and x['device']=='CPU' and x['metadata_stripped_pixel_preserved']
 assert hashlib.sha256((P/x['file']).read_bytes()).hexdigest()==x['sha256']
allow={'schema':'sciencegym.strict_export_allowlist.v1','files':sorted(files+['EXPORT_ALLOWLIST.json','MANIFEST.sha256']),'excluded':'Sources, logs, backups, caches, external CAD, publisher images, raw source code/data and upload receipts'}
(P/'EXPORT_ALLOWLIST.json').write_text(json.dumps(allow,indent=2)+'\n');files.append('EXPORT_ALLOWLIST.json')
hashes={n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in sorted(files)}
(P/'MANIFEST.sha256').write_text(''.join(v+'  '+n+'\n' for n,v in hashes.items()));files.append('MANIFEST.sha256')
out=P/'conformal_scene_assets_v2_compressed_public.zip'
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n in sorted(files):
  zi=zipfile.ZipInfo(n,(2026,10,4,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;zi.external_attr=0o100644<<16;z.writestr(zi,(P/n).read_bytes())
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None;assert set(z.namelist())==set(files)
 for n,h in hashes.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
receipt={'status':'verified','archive':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size,'file_count':len(files),'all_manifest_hashes_verified':True,'contains_source_files':False,'review_scope':'Static artifact checks only; no physical or scientific validation'}
(P/'export_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
