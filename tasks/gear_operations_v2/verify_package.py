#!/usr/bin/env python3
"""Read-only package integrity check. No source retrieval or physical execution."""
import hashlib,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tests'))
from record_contract import load_packet,validate_design

def verify():
 validate_design(load_packet())
 allow=json.loads((ROOT/'EXPORT_ALLOWLIST.json').read_text())
 files=allow['files']
 if len(files)!=len(set(files)):raise ValueError('duplicate allowlist path')
 for name in files:
  path=pathlib.PurePosixPath(name)
  if path.is_absolute() or '..' in path.parts or path.suffix not in {'.md','.json','.py'}:raise ValueError('unsafe or source-media export path')
  actual=ROOT/name
  if not actual.is_file() or actual.is_symlink():raise ValueError('missing or symlinked export')
  if name!='EXPORT_ALLOWLIST.json' and hashlib.sha256(actual.read_bytes()).hexdigest()!=allow['sha256'].get(name):raise ValueError('allowlist hash mismatch: '+name)
  text=actual.read_text()
  if any(token in text for token in ('/work'+'space/','/tm'+'p/','/ro'+'ot/')):raise ValueError('private absolute path in export: '+name)
  if path.suffix=='.json':json.loads(text)
 if set(allow['sha256'])!=set(files)-{'EXPORT_ALLOWLIST.json'}:raise ValueError('hash map coverage')
 return {'result':'pass','allowlisted_files':len(files),'scope':'Authored-file hashes, paths, JSON and static design references; no hardware or scientific verification'}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
