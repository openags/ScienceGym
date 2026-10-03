"""Exact original-file allowlist verifier. Never publishes or copies files."""
from pathlib import Path,PurePosixPath
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def _verify(root=ROOT):
 root=Path(root);errors=[]
 try:a=json.loads((root/'EXPORT_ALLOWLIST.json').read_text())
 except Exception as e:return ['allowlist unavailable: '+str(e)]
 names=a.get('files',[])
 if not isinstance(names,list) or any(not isinstance(n,str) for n in names):return ['malformed allowlist files']
 if not isinstance(a.get('payload_sha256'),dict):return ['malformed payload hashes']
 if not names or len(names)!=len(set(names)):errors.append('empty or duplicate allowlist')
 if a.get('actor_file_allowlist')!=['agent_visible.json']:errors.append('actor export boundary changed')
 if a.get('publisher_files_included') is not False:errors.append('publisher boundary changed')
 for name in names:
  path=PurePosixPath(name)
  if path.is_absolute() or '..' in path.parts or str(path)!=name or path.suffix not in ['.json','.md','.py']:errors.append('invalid export path '+name);continue
  p=root/name
  if p.is_symlink() or any(q.is_symlink() for q in p.parents if q!=root.parent):errors.append('symlink '+name);continue
  if not p.is_file():errors.append('missing '+name);continue
  if name!='EXPORT_ALLOWLIST.json' and hashlib.sha256(p.read_bytes()).hexdigest()!=a.get('payload_sha256',{}).get(name):errors.append('hash mismatch '+name)
 actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() or p.is_symlink()}
 if any(p.is_symlink() for p in root.rglob('*')):errors.append('symlink present in export root')
 if actual!=set(names):errors.append('file-set mismatch: '+str(sorted(actual^set(names))))
 if set(a.get('payload_sha256',{}))!=set(names)-{'EXPORT_ALLOWLIST.json'}:errors.append('hash key mismatch')
 return errors
def verify(root=ROOT):
 try:return _verify(root)
 except (ValueError,KeyError,TypeError,AttributeError,IndexError,OSError) as exc:return ['malformed export contract: '+type(exc).__name__]
if __name__=='__main__':
 errors=verify();print(json.dumps({'check':'exact_export','passed':not errors,'errors':errors},indent=2));raise SystemExit(bool(errors))
