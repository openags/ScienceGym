"""Independent allowlist checks using only original sentinel files in review scratch."""
from pathlib import Path
import copy,hashlib,importlib.util,json,tempfile,datetime,sys
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('hydrogel_export_verify',ROOT/'tests/verify_export.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
results=[]
def write_manifest(p,a): (p/'EXPORT_ALLOWLIST.json').write_text(json.dumps(a))
def probe(name,mutate,expected='reject'):
 with tempfile.TemporaryDirectory(prefix='export_probe_',dir=ROOT/'review') as scratch:
  p=Path(scratch);(p/'agent_visible.json').write_text('{"original_sentinel":true}\n')
  a={'files':['EXPORT_ALLOWLIST.json','agent_visible.json'],'actor_file_allowlist':['agent_visible.json'],'publisher_files_included':False,'payload_sha256':{'agent_visible.json':hashlib.sha256((p/'agent_visible.json').read_bytes()).hexdigest()}}
  write_manifest(p,a)
  try:
   mutate(p,a);errors=v.verify(p);actual='reject' if errors else 'accept'
  except Exception as e:actual='exception';errors=[type(e).__name__+': '+str(e)]
  results.append({'name':name,'expected':expected,'actual':actual,'passed':expected==actual,'diagnostic':errors})
def extra(p,a,name):
 f=p/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('Original review sentinel. No publisher bytes.\n')
def manifest_value(p,a,key,val):a[key]=val;write_manifest(p,a)
def add_symlink_directory(p,a):
 (p/'unlisted_link').symlink_to(p/'nonexistent_target',target_is_directory=True)
def add_symlink_file(p,a):
 (p/'original.md').write_text('Original review sentinel.\n');(p/'linked.md').symlink_to(p/'original.md')
 a['files']+=['original.md','linked.md'];a['payload_sha256'].update({n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in ['original.md','linked.md']});write_manifest(p,a)
probe('baseline',lambda p,a:None,'accept')
for name in ['extra.json','unlisted.pdf','.hidden.md','__pycache__/unlisted.pdf','nested/__pycache__/unlisted.json']:
 probe('unlisted_'+name.replace('/','_'),lambda p,a,n=name:extra(p,a,n))
probe('unlisted_directory_symlink',add_symlink_directory)
probe('listed_file_symlink',add_symlink_file)
probe('hash_mismatch',lambda p,a:(p/'agent_visible.json').write_text('{}'))
probe('actor_allowlist_expanded',lambda p,a:manifest_value(p,a,'actor_file_allowlist',['agent_visible.json','source_outcomes.json']))
probe('publisher_boundary_changed',lambda p,a:manifest_value(p,a,'publisher_files_included',True))
probe('duplicate_manifest_entry',lambda p,a:manifest_value(p,a,'files',a['files']+['agent_visible.json']))
probe('path_traversal',lambda p,a:manifest_value(p,a,'files',a['files']+['../outside.json']))
for value in [None,{},[None],[{}]]:probe('malformed_files_'+str(value),lambda p,a,x=value:manifest_value(p,a,'files',x))
receipt={'review_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Original sentinel export-root checks; no publisher assets or actual export','verifier_sha256':hashlib.sha256((ROOT/'tests/verify_export.py').read_bytes()).hexdigest(),'cases':results,'passed':sum(r['passed'] for r in results),'failed':sum(not r['passed'] for r in results)}
(ROOT/'review/export_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'cases':len(results),'passed':receipt['passed'],'failed':receipt['failed']}))
for r in results:
 if not r['passed']:print(r)
sys.exit(bool(receipt['failed']))
