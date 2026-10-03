"""Check exact original-file allowlist and payload hashes; never uploads anything."""
import hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
a=json.loads((root/'EXPORT_ALLOWLIST.json').read_text())
assert len(a['files'])==len(set(a['files']))
for name in a['files']:
 p=pathlib.PurePosixPath(name)
 assert not p.is_absolute() and '..' not in p.parts
 assert p.suffix in {'.json','.md','.py'}
 assert (root/name).is_file(),name
 assert not any(x in name for x in ['__pycache__','extracted','main.xml','supplement.pdf'])
for name,digest in a['payload_sha256'].items():
 assert name in a['files']
 assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
assert set(a['payload_sha256'])==set(a['files'])-{'EXPORT_ALLOWLIST.json','VERIFICATION.json'}
assert a['publisher_files_included'] is False
print(json.dumps({'status':'PASS','allowlisted_files':len(a['files']),'payload_hashes':len(a['payload_sha256']),'public_write':False}))
