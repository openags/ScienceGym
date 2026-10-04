"""Exact original-file allowlist verifier. Never writes or publishes files."""
import hashlib,json,sys
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1]
ALLOWED_SUFFIXES={'.json','.md','.py'}

def validate_manifest(root,manifest):
 errors=[]
 def ck(v,m):
  if not v:errors.append(m)
 files=manifest.get('allowlist');hashes=manifest.get('files')
 if not isinstance(files,list) or not isinstance(hashes,dict):return ['invalid manifest shape']
 ck(len(files)==len(set(files)),'duplicate export path');ck('EXPORT_ALLOWLIST.json' in files,'manifest not included')
 ck(set(hashes)==set(files)-{'EXPORT_ALLOWLIST.json'},'digest coverage mismatch')
 actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() or p.is_symlink()}
 ck(actual==set(files),'unexpected or missing files')
 for name in files:
  if not isinstance(name,str) or '\\' in name or ':' in name:errors.append('unsafe export path');continue
  parts=PurePosixPath(name)
  if parts.is_absolute() or '..' in parts.parts or str(parts)!=name:errors.append('unsafe export path');continue
  p=root/name
  if p.is_symlink():errors.append('symlink export');continue
  if not p.is_file():errors.append('missing payload');continue
  ck(p.suffix in ALLOWED_SUFFIXES,'unsupported/source-asset suffix')
  ck(not any(x in p.name.lower() for x in ['main_raw','si_raw','source_audit','source_manifest','main_repository']),'private source filename')
  if name=='EXPORT_ALLOWLIST.json':continue
  row=hashes.get(name,{})
  ck(type(row.get('bytes')) is int and row.get('bytes')==p.stat().st_size,'byte count mismatch '+name)
  ck(row.get('sha256')==hashlib.sha256(p.read_bytes()).hexdigest(),'digest mismatch '+name)
 ck(manifest.get('payload_file_count')==len(hashes),'payload count mismatch')
 ck(manifest.get('total_file_count_including_manifest')==len(files),'file count mismatch')
 return errors
if __name__=='__main__':
 try:errors=validate_manifest(ROOT,json.loads((ROOT/'EXPORT_ALLOWLIST.json').read_text()))
 except Exception as e:errors=[str(e)]
 print(json.dumps({'passed':not errors,'errors':errors,'scope':'exact-file original export only'},indent=2));raise SystemExit(bool(errors))
