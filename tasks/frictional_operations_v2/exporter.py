"""Deterministic original-only exporter with explicit trusted manifest pin."""
from pathlib import Path,PurePosixPath
import argparse
import hashlib
import json
import math
import re
import stat
import zipfile

class ExportError(ValueError):pass
def require(ok,msg):
    if not ok:raise ExportError(msg)
def sha(data):return hashlib.sha256(data).hexdigest()
def decode(data):
    def no_duplicates(items):
        d={}
        for k,v in items:
            require(k not in d,'Duplicate JSON key');d[k]=v
        return d
    def finite_float(value):
        result=float(value);require(math.isfinite(result),'Nonfinite JSON number');return result
    def reject_constant(value):raise ExportError('Nonfinite JSON constant')
    try:return json.loads(data,object_pairs_hook=no_duplicates,parse_constant=reject_constant,parse_float=finite_float)
    except (UnicodeError,ValueError,TypeError) as exc:raise ExportError('Invalid JSON') from exc

def path_check(root,name):
    require(type(name) is str,'Path must be string');p=PurePosixPath(name)
    require(not p.is_absolute() and str(p)==name and all(x not in {'','..','.'} and not x.startswith('.') for x in p.parts),'Unsafe path')
    require('\\' not in name and ':' not in name,'Unsafe path syntax')
    current=root
    for part in p.parts:
        current=current/part;require(not current.is_symlink(),'Symlink prohibited')
    require(current.is_file() and stat.S_ISREG(current.stat().st_mode),'Regular file required')
    require(current.resolve().is_relative_to(root.resolve()),'Path escapes root')
    return current

def snapshot(root,expected_manifest_sha256):
    root=Path(root);require(root.is_dir() and not root.is_symlink(),'Root must be real directory')
    require(type(expected_manifest_sha256) is str and re.fullmatch('[0-9a-f]{64}',expected_manifest_sha256) is not None,'Trusted manifest SHA256 required')
    mbytes=path_check(root,'DELIVERABLE_MANIFEST.json').read_bytes();require(sha(mbytes)==expected_manifest_sha256,'Manifest pin mismatch');manifest=decode(mbytes)
    require(type(manifest) is dict,'Manifest object required');require(set(manifest)=={'schema','files','total_bytes','original_only'},'Manifest shape');require(manifest['schema']=='sciencegym.deliverable_manifest.v1' and manifest['original_only'] is True,'Manifest classification')
    allow=decode(path_check(root,'EXPORT_ALLOWLIST.json').read_bytes());require(type(allow) is dict,'Allowlist object required');require(set(allow)=={'schema','files','excluded_classes'},'Allowlist shape');require(allow['schema']=='sciencegym.export_allowlist.v1','Allowlist schema')
    names=allow['files'];require(type(names) is list and all(type(n) is str for n in names) and names==sorted(set(names)),'Allowlist order or duplicate');require('DELIVERABLE_MANIFEST.json' in names and 'EXPORT_ALLOWLIST.json' in names,'Missing control files')
    actual=[]
    for p in root.rglob('*'):
        require(not p.is_symlink(),'Undeclared symlink prohibited')
        if p.is_file():actual.append(p.relative_to(root).as_posix())
        else:require(p.is_dir(),'Special file prohibited')
    require(sorted(actual)==names,'Extra or missing tree members')
    rows=manifest['files'];require(type(rows) is list and all(type(x) is dict for x in rows) and [x.get('path') for x in rows]==[n for n in names if n!='DELIVERABLE_MANIFEST.json'],'Manifest coverage/order mismatch')
    blobs={};total=0
    for row in rows:
        require(set(row)=={'path','bytes','sha256'},'Manifest record shape');name=row['path'];data=path_check(root,name).read_bytes()
        require(type(row['bytes']) is int and row['bytes']==len(data) and row['sha256']==sha(data),'File hash/length mismatch: '+name)
        require(name=='LICENSE' or Path(name).suffix in {'.json','.md','.py'},'Non-original binary/source-media extension prohibited')
        try:text=data.decode('utf-8')
        except UnicodeError as exc:raise ExportError('Binary content prohibited') from exc
        require('\x00' not in text,'Binary/null bytes prohibited')
        # Public provenance URLs remain legitimate. Runtime local machine paths do not.
        require(re.search(r'/(?:workspace|tmp|home|root)/|file:'+r'//|sediment:'+r'//|Bearer\s+[A-Za-z0-9_-]{12}',text) is None,'Local path or secret-like token prohibited')
        if name.endswith('.json'):decode(data)
        blobs[name]=data;total+=len(data)
    require(type(manifest['total_bytes']) is int and manifest['total_bytes']==total,'Manifest total mismatch')
    blobs['DELIVERABLE_MANIFEST.json']=mbytes
    return blobs

def export_package(root,destination,expected_manifest_sha256):
    root=Path(root);destination=Path(destination);require(not destination.resolve().is_relative_to(root.resolve()),'ZIP must remain outside payload tree');require(not destination.is_symlink(),'Destination symlink prohibited')
    blobs=snapshot(root,expected_manifest_sha256)
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_STORED) as z:
        for name in sorted(blobs):
            info=zipfile.ZipInfo(name,date_time=(2026,10,5,0,0,0));info.create_system=3;info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_STORED;z.writestr(info,blobs[name])
    data=destination.read_bytes()
    return {'file_count':len(blobs),'bytes':len(data),'sha256':sha(data),'manifest_sha256':expected_manifest_sha256,'original_only':True}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('destination');p.add_argument('--manifest-sha256',required=True);a=p.parse_args();print(json.dumps(export_package(a.root,a.destination,a.manifest_sha256),indent=2))
