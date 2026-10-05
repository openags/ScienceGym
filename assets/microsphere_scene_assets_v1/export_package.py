"""Freeze immutable original scene core and export allowlisted bytes. SPDX-License-Identifier: Apache-2.0"""
from pathlib import Path
import hashlib,json,zipfile,sys,struct,importlib.util
P=Path(__file__).resolve().parent
CORE=['README.md','LICENSES/ATTRIBUTION.md','LICENSES/Apache-2.0.txt','provenance.json','shared_binding_contract.json','asset_inventory.json','scene_manifest.json','scene_guards.py','tests/test_scene_guards.py','tests/native_semantic_snapshot.py','geometry/build_scene.py','geometry/deep_native_buffers.py','geometry/finalize_native.py','geometry/microsphere_lab.blend','geometry/microsphere_lab.glb','previews/preview_01_overview.png','previews/preview_02_targets.png','previews/preview_03_services.png','source_facts_snapshot.json','source_conflicts_snapshot.json','route_proposal_snapshot.json','station_contracts_snapshot.json','asset_requirements_snapshot.json','unknown_inputs_snapshot.json','coverage_map_snapshot.json','controls_and_repeats_snapshot.json','lineage_contract_snapshot.json','sample_custody_snapshot.json','verify_pair.py','sanitize_previews.py','export_package.py']
REVIEW=['review/render_receipt.json','review/preview_sanitization.json','review/authored_guard_results.json','review/deep_buffer_scan.json','review/deep_buffer_cleanup.json','review/native_equivalence.json','review/independent_scene_review.json','review/independent_scene_review.md','review/independent_guard_results.json','review/independent_geometry_results.json','review/independent_privacy_results.json','review/paired_verification.json']
META=['scene_core_manifest.json','paired_task_reference.json','paired_task_core_manifest.json','EXPORT_ALLOWLIST.json','MANIFEST.sha256','public_metadata_audit.json']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
def records(names):return [{'path':n,'bytes':(P/n).stat().st_size,'sha256':sha(P/n)} for n in sorted(names)]
def freeze():
 dest=P/'scene_core_manifest.json'
 if dest.exists():raise FileExistsError('Already frozen; new revision required for changes')
 r=records(CORE);m={'schema':'sciencegym.microsphere.scene_core.v1','package':P.name,'canonicalization':'UTF-8 JSON sort_keys=true separators=comma/colon ensure_ascii=false; digest of sorted files array','files':r,'core_sha256':hashlib.sha256(canonical(r)).hexdigest()};dest.write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({'core_sha256':m['core_sha256'],'files':len(r)}))
def audit(names):
 findings=[]
 for n in names:
  if Path(n).is_absolute() or '..' in Path(n).parts or any(x in n for x in ['__pycache__','.blend1','.raw.blend']):findings.append('unsafe_member')
  if Path(n).suffix in {'.json','.md','.py'}:
   text=(P/n).read_text()
   if any(x in text for x in ['/'+x for x in ['workspace/','home/','root/','tmp/']]+['dream'+'_notes','agent'+'_notes','codex'+':/'+'/','file'+':/'+'/']):findings.append('private_path_or_context:'+n)
 sys.path.insert(0,str(P/'geometry'));from deep_native_buffers import inspect,decoded
 scan=inspect(P/'geometry/microsphere_lab.blend',P);raw,data=decoded(P/'geometry/microsphere_lab.blend')
 if raw[:4]!=bytes.fromhex('28b52ffd'):findings.append('native_not_compressed')
 if not scan['strict_path_privacy_pass'] or scan['fields_with_nonzero_tail']:findings.append('native_fixed_buffer_privacy')
 if any(x in data for x in [('/'+x).encode() for x in ['workspace/','home/','root/','tmp/']]):findings.append('native_private_path')
 png=[]
 for p in (P/'previews').glob('*.png'):
  d=p.read_bytes();pos=8;kinds=[]
  while pos<len(d):n=int.from_bytes(d[pos:pos+4],'big');kinds.append(d[pos+4:pos+8]);pos+=n+12
  ok=not set(kinds)&{b'tEXt',b'iTXt',b'zTXt',b'eXIf',b'tIME'}
  if not ok:findings.append('png_metadata')
  png.append({'file':p.name,'metadata_absent':ok})
 g=(P/'geometry/microsphere_lab.glb').read_bytes();n,typ=struct.unpack_from('<I4s',g,12);j=json.loads(g[20:20+n]);external=[x['uri'] for k in ['buffers','images'] for x in j.get(k,[]) if x.get('uri')]
 if external:findings.append('glb_external_uri')
 return {'schema':'sciencegym.public_metadata_audit.v1','passed':not findings,'findings':findings,'native_compressed':True,'fixed_char_arrays_checked':scan['fixed_char_arrays_checked'],'nonzero_tails':scan['fields_with_nonzero_tail'],'path_issues_count':len(scan['path_issues']),'png_checks':png,'glb_external_uri_count':len(external),'raw_buffer_contents_disclosed':False,'publisher_or_author_media_bundled':False}
def archive():
 core=json.loads((P/'scene_core_manifest.json').read_text());assert core['files']==records(CORE),'Frozen scene core changed'
 ref=json.loads((P/'paired_task_reference.json').read_text());assert ref['scene_core_sha256']==core['core_sha256']
 names=sorted(CORE+REVIEW+META);a=audit([n for n in names if n not in {'EXPORT_ALLOWLIST.json','MANIFEST.sha256','public_metadata_audit.json'}]);assert a['passed'],a
 (P/'public_metadata_audit.json').write_text(json.dumps(a,indent=2)+'\n');(P/'EXPORT_ALLOWLIST.json').write_text(json.dumps({'members':names,'excluded':'All nonallowlisted source files, raw binaries, backups, caches, logs and temporary/private audit artifacts'},indent=2)+'\n')
 (P/'MANIFEST.sha256').write_text(''.join(f'{sha(P/n)}  {n}\n' for n in names if n!='MANIFEST.sha256'))
 out=P.parent/(P.name+'.zip')
 if out.exists():raise FileExistsError('Archive exists; do not replace accepted bytes')
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for n in names:z.write(P/n,n)
 with zipfile.ZipFile(out) as z:assert z.testzip() is None and sorted(z.namelist())==names
 budget=[]
 for f in [out]+list((P/'previews').glob('*.png')):
  b=f.stat().st_size;v=4*((b+2)//3)+4096;budget.append({'file':f.name,'bytes':b,'base64_plus_json_margin_bytes':v,'under_15_MiB':v<15*1024*1024})
 assert all(x['under_15_MiB'] for x in budget)
 r={'archive':out.name,'bytes':out.stat().st_size,'sha256':sha(out),'member_count':len(names),'scene_core_sha256':core['core_sha256'],'task_core_sha256':ref['task_core_sha256'],'zip_crc_pass':True,'blob_budgets':budget};(P.parent/(P.name+'_export_receipt.json')).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':
 if sys.argv[1:]==['--freeze-core']:freeze()
 elif sys.argv[1:]==['--archive']:archive()
 else:raise SystemExit('Use --freeze-core or --archive')
