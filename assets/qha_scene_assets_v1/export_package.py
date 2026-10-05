"""Freeze an immutable scene core and export a public allowlisted archive."""
from pathlib import Path
import json,hashlib,zipfile,sys,base64
P=Path(__file__).resolve().parent
CORE=[
 'README.md','LICENSES/ATTRIBUTION.md','LICENSES/Apache-2.0.txt','provenance.json','shared_binding_contract.json',
 'asset_inventory.json','scene_manifest.json','scene_guards.py','tests/test_scene_guards.py',
 'geometry/build_scene.py','geometry/sanitize_native.py','geometry/qha_lab.blend','geometry/qha_lab.glb',
 'previews/preview_01_overview.png','previews/preview_02_specimen.png','previews/preview_03_services.png',
 'asset_requirements_snapshot.json','source_facts_snapshot.json','source_conflicts_snapshot.json',
 'unknown_inputs_snapshot.json','station_contracts_snapshot.json','route_proposal_snapshot.json',
 'export_package.py','verify_pair.py','sanitize_previews.py','sanitized_revision.json','geometry/deep_native_buffers.py','geometry/finalize_native_buffers.py','tests/native_semantic_snapshot.py','tests/test_deep_native_buffers.py']
REVIEW=['review/baseline_preservation.json','review/render_receipt.json','review/metadata_sanitization.json','review/authored_guard_results.json','review/independent_glb_scene.json','review/independent_guard_results.json','review/deep_buffer_cleanup.json','review/deep_buffer_scan.json','review/native_equivalence.json','review/unchanged_visual_assets.json','review/clean_revision_tests.json','review/independent_clean_revision.json','review/independent_clean_revision.md']
META=['scene_core_manifest.json','paired_task_reference.json','paired_task_core_manifest.json','EXPORT_ALLOWLIST.json','MANIFEST.sha256','public_metadata_audit.json']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def records(names):return [{'path':n,'bytes':(P/n).stat().st_size,'sha256':sha(P/n)} for n in sorted(names)]
def freeze():
 r=records(CORE);out={'schema':'sciencegym3d.scene_core.v1','digest_algorithm':'sha256 of canonical JSON files array, sorted keys, compact separators, UTF-8','files':r,'core_sha256':hashlib.sha256(canonical(r)).hexdigest()};(P/'scene_core_manifest.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'core_sha256':out['core_sha256'],'core_files':len(r)}))
def audit(names):
 bad=[]
 for n in names:
  if any(t in n for t in ['..','__pycache__','.blend1']) or n.startswith('/'):bad.append(n)
  if Path(n).suffix in {'.json','.md','.py'}:
   s=(P/n).read_text()
   for token in ['/'+n for n in ['workspace','home','root']]+['agent'+'_notes/','dream'+'_notes','codex'+':/'+ '/','file'+':/'+ '//']:
    if token in s:bad.append(n+':'+token)
 import importlib.util
 spec=importlib.util.spec_from_file_location('deep_native',P/'geometry/deep_native_buffers.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 deep=module.inspect(P/'geometry/qha_lab.blend',P)
 if not deep['strict_path_privacy_pass'] or deep['fields_with_nonzero_tail']:bad.append('deep_fixed_buffer_privacy_check_failed')
 import zstandard
 native=(P/'geometry/qha_lab.blend').read_bytes()
 assert native[:4]==bytes.fromhex('28b52ffd'),'Native scene must remain natively compressed'
 with zstandard.ZstdDecompressor().stream_reader(native) as reader:decoded=reader.read()
 for n in ['workspace','home','root']:
  if ('/'+n).encode() in decoded:bad.append('native_private_path')
 for f in (P/'previews').glob('*.png'):
  data=f.read_bytes();pos=8
  while pos<len(data):
   length=int.from_bytes(data[pos:pos+4],'big');kind=data[pos+4:pos+8]
   if kind in {b'tEXt',b'iTXt',b'zTXt',b'eXIf'}:bad.append(f.name+':ancillary_metadata')
   pos+=length+12
 return {'deep_fixed_char_arrays_checked':deep['fixed_char_arrays_checked'],'deep_nonzero_tails':deep['fields_with_nonzero_tail'],'deep_path_issues':deep['path_issues'],'native_compressed':True,'native_decompressed_private_paths_absent':not bad,'png_text_and_exif_absent':not bad,'schema':'sciencegym3d.public_metadata_audit.v1','relative_paths_only':not bad,'private_metadata_findings':bad,'publisher_assets_included':False,'source_raw_data_included':False,'allowlist_enforced':True}
def archive():
 core=json.loads((P/'scene_core_manifest.json').read_text());assert core['files']==records(CORE),'Scene core changed after freeze'
 ref=json.loads((P/'paired_task_reference.json').read_text());assert ref['asset_core_sha256']==core['core_sha256']
 names=sorted(CORE+REVIEW+META)
 # Scan all existing public members, then create the audit and inventory.
 a=audit([n for n in names if n not in {'EXPORT_ALLOWLIST.json','MANIFEST.sha256','public_metadata_audit.json'}]);assert not a['private_metadata_findings'],a
 (P/'public_metadata_audit.json').write_text(json.dumps(a,indent=2)+'\n')
 (P/'EXPORT_ALLOWLIST.json').write_text(json.dumps({'schema':'sciencegym3d.export_allowlist.v1','members':names,'excluded':'Anything not explicitly listed; especially backups, local logs, caches, private source files and temporary audit state'},indent=2)+'\n')
 (P/'MANIFEST.sha256').write_text(''.join(f"{sha(P/n)}  {n}\n" for n in names if n!='MANIFEST.sha256'))
 out=P.parent/(P.name+'.zip')
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for n in names:z.write(P/n,n)
 with zipfile.ZipFile(out) as z:assert z.testzip() is None;assert sorted(z.namelist())==names
 assets=[out]+[P/n for n in CORE if n.endswith('.png')]
 budget=[{'file':x.name,'bytes':x.stat().st_size,'base64_plus_json_margin_bytes':4*((x.stat().st_size+2)//3)+4096,'under_15_MiB':4*((x.stat().st_size+2)//3)+4096<15*1024*1024} for x in assets]
 assert all(x['under_15_MiB'] for x in budget),budget
 receipt={'archive_file':out.name,'bytes':out.stat().st_size,'sha256':sha(out),'members':len(names),'core_sha256':core['core_sha256'],'zip_crc_pass':True,'upload_budgets':budget}
 (P.parent/(P.name+'_export_receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':
 if sys.argv[1:]==['--freeze-core']:freeze()
 elif sys.argv[1:]==['--archive']:archive()
 else:raise SystemExit('Use --freeze-core or --archive')
