"""Verify exact exported member inventory, bytes and hashes without network access."""
from pathlib import Path, PurePosixPath
import hashlib,json,zipfile
from verify_package import read
ROOT=Path(__file__).resolve().parents[1]

def sha(data):return hashlib.sha256(data).hexdigest()
def allowed_name(name):
    if type(name) is not str or not name:return False
    p=PurePosixPath(name)
    return not p.is_absolute() and str(p)==name and '..' not in p.parts and not any(x.startswith('.') for x in p.parts) and '\\' not in name

def verify(root=ROOT,archive=None):
    errors=[]
    try:manifest=read(root/'EXPORT_ALLOWLIST.json')
    except Exception as e:return ['manifest unreadable: '+str(e)]
    if type(manifest) is not dict:return ['manifest schema']
    rows=manifest.get('files')
    if type(rows) is not list or not all(type(r) is dict and set(r)=={'path','bytes','sha256'} for r in rows):return ['manifest row schema']
    names=[r['path'] for r in rows]
    if not names or not all(allowed_name(n) for n in names) or len(names)!=len(set(names)):return ['invalid allowlist names']
    if manifest.get('actor_visible_allowlist')!=['agent_visible.json'] or manifest.get('all_other_files_are_evaluator_audit_only') is not True:errors.append('actor projection invalid')
    expected=set(names)|{'EXPORT_ALLOWLIST.json'}
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if actual!=expected:errors.append('package inventory differs: '+repr(sorted(actual^expected)))
    for row in rows:
        p=root/row['path']
        if p.is_symlink() or not p.is_file():errors.append('missing or symlink '+row['path']);continue
        data=p.read_bytes()
        if len(data)!=row['bytes'] or sha(data)!=row['sha256']:errors.append('content mismatch '+row['path'])
    if any(p.is_symlink() for p in root.rglob('*')):errors.append('symlink forbidden')
    if archive is not None:
        try:
            with zipfile.ZipFile(archive) as z:
                zn=z.namelist()
                if len(zn)!=len(set(zn)) or set(zn)!=expected:errors.append('archive exact-member mismatch')
                for name in zn:
                    if not allowed_name(name):errors.append('unsafe archive member');continue
                    if name in expected and z.read(name)!=(root/name).read_bytes():errors.append('archive bytes differ '+name)
        except (ValueError,KeyError,OSError,zipfile.BadZipFile) as e:errors.append('archive invalid '+str(e))
    return errors
if __name__=='__main__':
    import sys
    errors=verify(archive=Path(sys.argv[1]) if len(sys.argv)>1 else None)
    print(json.dumps(dict(passed=not errors,errors=errors,scope='exact original-text/code export'),indent=2));raise SystemExit(bool(errors))
