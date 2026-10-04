"""Exact allowlist verification, including file hashes and symlink rejection."""
from pathlib import Path, PurePosixPath
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_FILES={'asset_needs.json', 'STATUS.json', 'transport_routes.json', 'source_dataset_registry.json', 'source_conflicts.json', 'material_cards.json', 'VERIFICATION.json', 'station_contracts.json', 'branches.json', 'EXPORT_ALLOWLIST.json', 'source_outcomes.json', 'state_contract.json', 'operations.json', 'TASK_DESIGN.md', 'provenance.json', 'unknown_parameters.json', 'REVIEW_NOTES.md', 'dependencies.json', 'tests/test_export.py', 'agent_visible.json', 'lineage_contract.json', 'tests/test_contract.py', 'design_assumptions.json', 'nonmanual_scope.json', 'mount_lease_contract.json', 'EXPORT_SCOPE.md', 'source_access_audit.json', 'mock_contract.json', 'evaluator_reference.json', 'review/audit.json', 'coverage_matrix.json', 'tests/verify_package.py', 'tests/verify_export.py', 'review/REPORT.md', 'RELEASE_BOUNDARY.json', 'control_packages.json', 'README.md', 'tests/contract.py', 'episode_input_contract.json', 'adversarial_cases.json'}
def verify(root=ROOT):
 errors=[]
 try:
  manifest=root/'EXPORT_ALLOWLIST.json'
  if manifest.is_symlink():raise ValueError('symlink manifest')
  d=json.loads(manifest.read_text());files=d['files'];hashes=d['payload_sha256']
  if not isinstance(files,list) or not files or len(files)!=len(set(files)):raise ValueError('invalid/duplicate allowlist')
  if set(files)!=EXPECTED_FILES:errors.append('unrecognized or omitted export path')
  for n in files:
   p=PurePosixPath(n)
   if not isinstance(n,str) or p.is_absolute() or '..' in p.parts or str(p)!=n or any(c in n for c in '*?[]\\') or n.startswith('.') or n.endswith('/'):errors.append('unsafe path: '+str(n))
   if any((root/Path(*p.parts[:i])).is_symlink() for i in range(1,len(p.parts)+1)):errors.append('symlink: '+n)
   if not (root/n).is_file():errors.append('missing file: '+n)
  actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() or p.is_symlink()}
  if actual!=set(files):errors.append('exact file set mismatch')
  if set(hashes)!=set(files)-{'EXPORT_ALLOWLIST.json'}:errors.append('payload hash coverage mismatch')
  for n,h in hashes.items():
   if n not in files or not isinstance(h,str) or len(h)!=64:errors.append('invalid hash entry');continue
   p=root/n
   if p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()!=h:errors.append('hash mismatch: '+n)
  if d.get('actor_file_allowlist')!=['agent_visible.json']:errors.append('actor allowlist expansion')
  if d.get('publisher_files_included') is not False:errors.append('publisher exclusion missing')
 except Exception as e:errors.append(type(e).__name__+': '+str(e))
 return {'check':'exact_export','passed':not errors,'errors':errors}
if __name__=='__main__':
 r=verify();print(json.dumps(r,indent=2));raise SystemExit(not r['passed'])
