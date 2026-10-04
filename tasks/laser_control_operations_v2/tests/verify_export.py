"""Exact original-file export checks. This is integrity, not authentication."""
from pathlib import Path, PurePosixPath
import hashlib,json,stat,zipfile
from verify_package import read
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_FILES=tuple('''EXPORT_SCOPE.md README.md RELEASE_BOUNDARY.json STATUS.json TASK_DESIGN.md VERIFICATION.json adversarial_cases.json agent_visible.json analysis_contracts.json asset_binding_plan.json branches.json control_packages.json coverage_matrix.json design_assumptions.json episode_input_contract.json evaluator_reference.json evidence_map.json lifecycle_contract.json lineage_contract.json material_cards.json mock_contract.json nonmanual_scope.json operations.json preparation_routes.json provenance.json source_access_audit.json source_conflicts.json source_outcomes.json station_contracts.json transport_routes.json unknown_parameters.json tests/contract.py tests/test_contract.py tests/test_export.py tests/verify_export.py tests/verify_package.py review/INDEPENDENT_REVIEW.json review/INDEPENDENT_REVIEW.md review/test_independent_adversarial.py review/test_independent_export.py'''.split())
def sha(data):return hashlib.sha256(data).hexdigest()
def allowed_name(name):
    if type(name) is not str or not name:return False
    p=PurePosixPath(name)
    return not p.is_absolute() and str(p)==name and '..' not in p.parts and not any(x.startswith('.') for x in p.parts) and '\\' not in name and ':' not in name

def verify(root=ROOT,archive=None):
    root=Path(root);errors=[]
    try:
        entries=list(root.rglob('*'))
        if root.is_symlink() or any(p.is_symlink() for p in entries):return ['symlink forbidden']
        if any(not (stat.S_ISREG(p.lstat().st_mode) or stat.S_ISDIR(p.lstat().st_mode)) for p in entries):return ['nonregular filesystem entry forbidden']
    except OSError as exc:return ['filesystem inventory unreadable: '+str(exc)]
    try:manifest=read(root/'EXPORT_ALLOWLIST.json')
    except Exception as e:return ['manifest unreadable: '+str(e)]
    if type(manifest) is not dict:return ['manifest schema']
    rows=manifest.get('files')
    if type(rows) is not list or not all(type(r) is dict and set(r)=={'path','bytes','sha256'} for r in rows):return ['manifest row schema']
    names=[r['path'] for r in rows]
    if not names or not all(allowed_name(n) for n in names) or len(names)!=len(set(names)):return ['invalid allowlist names']
    if set(names)!=set(EXPECTED_FILES):errors.append('manifest differs from fixed original-file allowlist')
    if manifest.get('actor_visible_allowlist')!=['agent_visible.json'] or manifest.get('all_other_files_are_evaluator_audit_only') is not True:errors.append('actor projection invalid')
    if type(manifest.get('member_count_including_manifest')) is not int or manifest['member_count_including_manifest']!=len(EXPECTED_FILES)+1:errors.append('manifest member count')
    expected=set(EXPECTED_FILES)|{'EXPORT_ALLOWLIST.json'}
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if actual!=expected:errors.append('package inventory differs: '+repr(sorted(actual^expected)))
    for row in rows:
        name=row['path']
        if name not in EXPECTED_FILES:continue
        if type(row['bytes']) is not int or row['bytes']<0 or type(row['sha256']) is not str or len(row['sha256'])!=64 or any(c not in '0123456789abcdef' for c in row['sha256']):errors.append('invalid row '+name);continue
        p=root/name
        if not p.is_file():errors.append('missing '+name);continue
        data=p.read_bytes()
        if len(data)!=row['bytes'] or sha(data)!=row['sha256']:errors.append('content mismatch '+name)
    if archive is not None:
        try:
            with zipfile.ZipFile(archive) as z:
                zi=z.infolist();zn=[i.filename for i in zi]
                if len(zn)!=len(set(zn)) or set(zn)!=expected:errors.append('archive exact-member mismatch')
                for item in zi:
                    name=item.filename
                    if not allowed_name(name):errors.append('unsafe archive member');continue
                    mode=(item.external_attr>>16)&0o170000
                    if mode not in (0,stat.S_IFREG):errors.append('nonregular archive member '+name);continue
                    if name in expected and z.read(item)!=(root/name).read_bytes():errors.append('archive bytes differ '+name)
        except (ValueError,KeyError,OSError,RuntimeError,zipfile.BadZipFile) as e:errors.append('archive invalid '+str(e))
    return errors
if __name__=='__main__':
    import sys
    e=verify(archive=Path(sys.argv[1]) if len(sys.argv)>1 else None)
    print(json.dumps(dict(passed=not e,errors=e,scope='exact original-text/code export'),indent=2));raise SystemExit(bool(e))
