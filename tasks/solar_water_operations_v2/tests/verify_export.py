"""Exact allowlist verifier, safe path/symlink checks and digest validation."""
from pathlib import Path, PurePosixPath
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def verify(root=ROOT):
 root=Path(root);m=json.loads((root/'EXPORT_ALLOWLIST.json').read_text())
 allowed=m['allowlist'];files=m['files']
 if len(allowed)!=len(set(allowed)):raise ValueError('duplicate path')
 if set(allowed)!=set(files)|{'EXPORT_ALLOWLIST.json'}:raise ValueError('manifest membership mismatch')
 if m['payload_file_count']!=len(files) or m['total_file_count_including_manifest']!=len(allowed):raise ValueError('count mismatch')
 for name in allowed:
  p=PurePosixPath(name)
  if not isinstance(name,str) or p.is_absolute() or '..' in p.parts or '\\' in name or str(p)!=name:raise ValueError('unsafe path')
  q=root/name
  if q.is_symlink() or not q.is_file():raise ValueError('missing file or symlink')
  if any(part.is_symlink() for part in q.parents if part!=root and root in part.parents):raise ValueError('symlink ancestor')
 found={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() or p.is_symlink()}
 if found!=set(allowed):raise ValueError('unlisted or missing artifact')
 for name,info in files.items():
  data=(root/name).read_bytes()
  if len(data)!=info['bytes'] or hashlib.sha256(data).hexdigest()!=info['sha256']:raise ValueError('changed payload '+name)
  if Path(name).suffix not in {'.json','.md','.py'}:raise ValueError('source/media extension')
 if m.get('source_assets_exported') is not False:raise ValueError('source export claim')
 return {'status':'passed','payload_files':len(files),'scope':'exact_original_allowlist'}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
