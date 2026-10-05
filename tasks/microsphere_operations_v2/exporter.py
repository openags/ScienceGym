"""Fail-closed original-only deterministic task exporter; no network or subprocesses."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import zipfile

class ExportError(ValueError): pass

def check(ok,msg):
    if not ok: raise ExportError(msg)

def sha(data): return hashlib.sha256(data).hexdigest()

def unique_object(pairs):
    d={}
    for k,v in pairs:
        check(k not in d,'Duplicate JSON key')
        d[k]=v
    return d

def load(data):
    return json.loads(data,object_pairs_hook=unique_object,parse_constant=lambda _:(_ for _ in ()).throw(ExportError('Nonfinite JSON')))

def safe_name(name):
    check(type(name) is str,'Invalid member name')
    p=PurePosixPath(name)
    check(not p.is_absolute() and str(p)==name and '\\' not in name and all(x not in ('','.','..') and not x.startswith('.') for x in p.parts),'Unsafe member path')
    check(p.suffix in {'.json','.md','.py'} or name=='LICENSE','Unexpected export type')
    return p

def inspect(root):
    root=Path(root)
    check(root.is_dir() and not root.is_symlink(),'Invalid package root')
    for meta in ('EXPORT_ALLOWLIST.json','DELIVERABLE_MANIFEST.json'):
        check(not (root/meta).is_symlink() and stat.S_ISREG((root/meta).lstat().st_mode),'Unsafe metadata file')
    policy=load((root/'EXPORT_ALLOWLIST.json').read_bytes())
    manifest=load((root/'DELIVERABLE_MANIFEST.json').read_bytes())
    names=policy['files']
    check(type(names) is list and len(names)==len(set(names)),'Duplicate allowlist entry')
    for name in names:safe_name(name)
    actual=[]
    for p in root.rglob('*'):
        check(not p.is_symlink(),'Symlink forbidden')
        if p.is_file():actual.append(p.relative_to(root).as_posix())
        elif not p.is_dir():raise ExportError('Special file forbidden')
    check(set(actual)==set(names),'Unlisted or missing file')
    records={r['path']:r for r in manifest['files']}
    check(len(records)==len(manifest['files']),'Duplicate manifest entry')
    check(set(records)==set(names)-{'DELIVERABLE_MANIFEST.json'},'Incomplete manifest')
    payload={};total=0
    for name in sorted(names):
        p=root/name
        check(stat.S_ISREG(p.lstat().st_mode),'Not a regular file')
        data=p.read_bytes();total+=len(data)
        check(len(data)<8*1024*1024 and total<50*1024*1024,'Export size bound exceeded')
        text=data.decode('utf-8')
        check('\x00' not in text,'Embedded binary')
        check(not any(s in text for s in tuple('/'+part+'/' for part in ('workspace','home','root','tmp'))+tuple(part+'://' for part in ('file','sediment'))),'Private path or locator')
        if name.endswith('.json'):load(data)
        if name!='DELIVERABLE_MANIFEST.json':
            rec=records[name];check(rec['bytes']==len(data) and rec['sha256']==sha(data),'Stale file hash')
        payload[name]=data
    check(manifest['publisher_material_included'] is False and manifest['physical_execution'] is False,'Invalid release boundary')
    return payload

def build_archive(root,destination):
    root=Path(root);destination=Path(destination)
    check(not root.is_symlink(),'Symlinked package root')
    check(not destination.is_symlink(),'Symlinked archive destination')
    root=root.resolve()
    check(root not in destination.resolve().parents,'Archive must be outside source package')
    payload=inspect(root)
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in payload.items():
            item=zipfile.ZipInfo(root.name+'/'+name,date_time=(2026,10,5,0,0,0))
            item.create_system=3;item.external_attr=(stat.S_IFREG|0o644)<<16
            item.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(item,data)
    return {'members':len(payload),'bytes':destination.stat().st_size,'sha256':sha(destination.read_bytes())}

def verify_archive(path,root):
    payload=inspect(root);prefix=Path(root).name+'/'
    with zipfile.ZipFile(path) as z:
        check(not z.comment,'Unexpected archive comment')
        names=z.namelist()
        check(len(names)==len(set(names)),'Duplicate archive member')
        check(set(names)=={prefix+n for n in payload},'Archive member drift')
        for name,data in payload.items():
            info=z.getinfo(prefix+name)
            check(stat.S_ISREG(info.external_attr>>16),'Archive symlink or special file')
            check(not info.extra and not info.comment,'Unexpected ZIP metadata')
            check(z.read(prefix+name)==data,'Archive byte drift')
    return True
