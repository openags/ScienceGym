"""Verify final reciprocal pins against actual paired files; no scene execution."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
from contract import digest, load_contract

def validate(root, filename):
    root=Path(root)
    if root.is_symlink():raise ValueError('Symlink root')
    manifest=json.loads((root/filename).read_text())
    records=manifest['files']
    if records!=sorted(records,key=lambda x:x['path']) or len({r['path'] for r in records})!=len(records):raise ValueError('Invalid core inventory')
    for record in records:
        name=record['path'];path=PurePosixPath(name)
        if path.is_absolute() or str(path)!=name or any(p in ('','.','..') for p in path.parts) or '\\' in name:raise ValueError('Unsafe core path')
        file=root/name
        if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(root.resolve()):raise ValueError('Invalid core member')
        data=file.read_bytes()
        if len(data)!=record['bytes'] or hashlib.sha256(data).hexdigest()!=record['sha256']:raise ValueError('Core file drift')
    if digest(records)!=manifest['core_sha256']:raise ValueError('Core digest drift')
    return manifest

def verify(scene_root):
    root=Path(__file__).resolve().parent;scene=Path(scene_root)
    task=validate(root,'task_core_manifest.json');assets=validate(scene,'scene_core_manifest.json')
    binding=json.loads((root/'asset_binding_plan.json').read_text())
    reciprocal=json.loads((scene/'paired_task_reference.json').read_text())
    if binding['task_core_sha256']!=task['core_sha256'] or reciprocal['task_core_sha256']!=task['core_sha256']:raise ValueError('Task pin drift')
    if binding['scene_core_sha256']!=assets['core_sha256'] or reciprocal['scene_core_sha256']!=assets['core_sha256']:raise ValueError('Scene pin drift')
    if json.loads((root/'paired_scene_core_manifest.json').read_text())!=assets:raise ValueError('Paired scene manifest drift')
    if json.loads((scene/'paired_task_core_manifest.json').read_text())!=task:raise ValueError('Paired task manifest drift')
    if (root/'shared_binding_contract.json').read_bytes()!=(scene/'shared_binding_contract.json').read_bytes():raise ValueError('Shared semantic contract drift')
    if (root/'semantic_core.json').read_bytes()!=(scene/'semantic_core.json').read_bytes():raise ValueError('Semantic core drift')
    _,semantics=load_contract(root)
    if binding['semantic_core_sha256']!=semantics:raise ValueError('Semantic pin drift')
    return {'passed':True,'task_core_files':len(task['files']),'scene_core_files':len(assets['files']),'physical_execution':False,'task_core_sha256':task['core_sha256'],'scene_core_sha256':assets['core_sha256']}

if __name__=='__main__':print(json.dumps(verify(sys.argv[1]),indent=2))
