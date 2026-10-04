"""Exact-path, exact-byte export verification. Does not copy or publish files."""
from pathlib import Path,PurePosixPath
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[1]
def unique(pairs):
 out={}
 for k,v in pairs:
  if k in out:raise ValueError('duplicate key')
  out[k]=v
 return out

def _verify(root):
 errors=[];root=Path(root)
 def check(ok,msg):
  if not ok:errors.append(msg)
 if root.is_symlink():return ['root is symlink']
 a=json.loads((root/'EXPORT_ALLOWLIST.json').read_text(),object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite')))
 names=a.get('files');hashes=a.get('payload_sha256')
 if not isinstance(names,list) or not all(isinstance(x,str) for x in names) or not isinstance(hashes,dict):return ['malformed allowlist']
 check(bool(names) and len(names)==len(set(names)),'empty or duplicate names')
 check(names==sorted(names),'allowlist not canonical')
 check(a.get('publisher_files_included') is False,'publisher boundary')
 check(a.get('actor_file_allowlist')==['agent_visible.json'],'actor boundary')
 check(a.get('publication_authority')=='parent_only','publication boundary')
 check(set(hashes)==set(names)-{'EXPORT_ALLOWLIST.json'},'hash key set')
 check('EXPORT_ALLOWLIST.json' in names,'self path missing')
 actual=set()
 for p in root.rglob('*'):
  if p.is_symlink():errors.append('symlink '+p.relative_to(root).as_posix())
  if p.is_file() or p.is_symlink():actual.add(p.relative_to(root).as_posix())
 check(actual==set(names),'file set mismatch: '+str(sorted(actual^set(names))))
 for name in names:
  path=PurePosixPath(name)
  if not name or path.is_absolute() or '..' in path.parts or str(path)!=name or '\\' in name or ':' in name or path.suffix not in ['.json','.md','.py']:
   errors.append('unsafe export path '+name);continue
  p=root/name
  if p.is_symlink() or any(q.is_symlink() for q in p.parents if q!=root.parent):errors.append('symlink path');continue
  if not p.is_file():errors.append('missing file '+name);continue
  if name!='EXPORT_ALLOWLIST.json':
   expected=hashes.get(name)
   check(isinstance(expected,str) and re.fullmatch('[0-9a-f]{64}',expected) is not None,'invalid hash '+name)
   check(hashlib.sha256(p.read_bytes()).hexdigest()==expected,'changed payload '+name)
 return errors

def verify(root=ROOT):
 try:return _verify(root)
 except (OSError,ValueError,TypeError,KeyError,AttributeError,IndexError) as exc:return ['malformed export: '+type(exc).__name__]
if __name__=='__main__':
 errors=verify();print(json.dumps({'check':'exact_export','passed':not errors,'errors':errors},indent=2));raise SystemExit(bool(errors))
