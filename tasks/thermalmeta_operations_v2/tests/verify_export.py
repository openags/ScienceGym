"""Strict allowlist, sanitization, digest and pairing checks for original export."""
import hashlib
import json
import pathlib
import sys
import zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
EXCLUDED_FROM_CONTENT_MANIFEST={'CONTENT_MANIFEST.json','PAIR_SEAL.json'}
BANNED_EXTENSIONS={'.pdf','.png','.jpg','.jpeg','.mp4','.mat','.blend','.glb','.stl','.step','.cad','.so','.pyc'}
PRIVATE_PREFIXES=['/'+'workspace/','/'+'home/','/'+'root/','/'+'tmp/','file'+':/','sediment'+':/']

def sha(b):return hashlib.sha256(b).hexdigest()
def names_valid(names):
    assert len(names)==len(set(names)), 'duplicate names'
    for name in names:
        assert isinstance(name,str) and name and '\\' not in name and ':' not in name and all(ord(c)>=32 for c in name), 'nonportable path'
        p=pathlib.PurePosixPath(name)
        assert name==str(p) and not p.is_absolute() and '..' not in p.parts, 'unsafe path'
        assert all(not part.startswith('.') for part in p.parts), 'hidden path'
        assert p.suffix.lower() not in BANNED_EXTENSIONS, 'prohibited content type'

def verify_members(members, require_seal=True):
    names=list(members);names_valid(names)
    allow=json.loads(members['EXPORT_ALLOWLIST.json'])['files']
    names_valid(allow)
    assert set(names)==set(allow), 'allowlist mismatch'
    for name,data in members.items():
        text=data.decode('utf-8')
        assert not any(p in text for p in PRIVATE_PREFIXES), 'private path in '+name
        assert not any(x in text for x in ('-----BEGIN '+'PRIVATE KEY-----','Bearer '+'eyJ')), 'secret-like content'
    manifest=json.loads(members['CONTENT_MANIFEST.json'])
    entries=manifest['files']
    assert {x['path'] for x in entries}==set(names)-EXCLUDED_FROM_CONTENT_MANIFEST, 'manifest coverage mismatch'
    assert len(entries)==len({x['path'] for x in entries}), 'duplicate manifest entry'
    for entry in entries:
        data=members[entry['path']]
        assert entry['sha256']==sha(data) and entry['bytes']==len(data), 'digest/size mismatch '+entry['path']
    if require_seal:
        seal=json.loads(members['PAIR_SEAL.json'])
        assert seal['task_content_manifest_sha256']==sha(members['CONTENT_MANIFEST.json']), 'task seal mismatch'
        assert seal['shared_binding_sha256']==sha(members['scene_binding_contract.json']), 'binding seal mismatch'
        assert len(seal['scene_content_manifest_sha256'])==64, 'scene hash missing'
        assert seal['physical_or_scientific_execution_validated'] is False, 'invalid execution claim'
    return {'members':len(names),'content_manifest_entries':len(entries),'sanitized':True,'manifest_valid':True,'scope':'original design only'}

def verify_tree(root=ROOT):
    allow=json.loads((root/'EXPORT_ALLOWLIST.json').read_text())['files']
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
    assert actual==set(allow), 'unlisted/missing file in package tree'
    for n in allow:assert not (root/n).is_symlink(), 'symlink prohibited'
    return verify_members({n:(root/n).read_bytes() for n in allow})

def verify_zip(path):
    with zipfile.ZipFile(path) as z:
        names=z.namelist();names_valid(names)
        assert z.testzip() is None, 'archive CRC failure'
        for i in z.infolist():assert (i.external_attr>>16)&0o170000 != 0o120000, 'symlink archive member'
        return verify_members({n:z.read(n) for n in names})

if __name__=='__main__':
    result=verify_zip(pathlib.Path(sys.argv[1])) if len(sys.argv)>1 else verify_tree()
    print(json.dumps(result,indent=2))
