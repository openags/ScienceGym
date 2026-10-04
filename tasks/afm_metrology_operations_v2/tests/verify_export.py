"""Exact original-file export boundary; not a scientific/security certification."""
from pathlib import Path
import hashlib,json,sys
EXPECTED=set('''EXPORT_ALLOWLIST.json EXPORT_SCOPE.md README.md RELEASE_BOUNDARY.json REVIEW_NOTES.md STATUS.json TASK_DESIGN.md VERIFICATION.json adversarial_cases.json agent_visible.json analysis_contracts.json asset_needs.json branches.json control_packages.json coverage_matrix.json design_assumptions.json episode_input_contract.json evaluator_reference.json lineage_contract.json material_cards.json mock_contract.json nonmanual_scope.json operations.json preparation_routes.json provenance.json source_access_audit.json source_conflicts.json station_contracts.json transport_routes.json unknown_parameters.json tests/contract.py tests/test_contract.py tests/test_export.py tests/verify_package.py tests/verify_export.py review/REPORT.md review/audit.json review/adversarial_review.py review/export_receipt.json'''.split())
def verify(root):
 root=Path(root);errors=[]
 try:m=json.loads((root/'EXPORT_ALLOWLIST.json').read_text())
 except (OSError,ValueError):return ['missing or invalid manifest']
 if set(m.get('files',[]))!=EXPECTED or len(m.get('files',[]))!=len(EXPECTED):errors.append('manifest does not match independently pinned path set')
 if set(m.get('payload_sha256',{}))!=EXPECTED-{'EXPORT_ALLOWLIST.json'}:errors.append('hash inventory mismatch')
 if m.get('actor_file_allowlist')!=['agent_visible.json']:errors.append('actor boundary changed')
 if m.get('publisher_files_included') is not False:errors.append('publisher-source claim changed')
 all_paths=list(root.rglob('*'));actual={str(p.relative_to(root)) for p in all_paths if p.is_file() or p.is_symlink()}
 if actual!=EXPECTED:errors.append('actual file inventory differs from fixed boundary')
 for p in all_paths:
  if p.is_symlink():errors.append('symlink forbidden')
 for name in EXPECTED-{'EXPORT_ALLOWLIST.json'}:
  p=root/name
  if not p.is_file() or p.is_symlink():errors.append('missing/nonregular '+name);continue
  if not p.resolve().is_relative_to(root.resolve()):errors.append('path escapes package');continue
  raw=p.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=m.get('payload_sha256',{}).get(name):errors.append('hash mismatch '+name)
  try:text=raw.decode('utf8')
  except UnicodeDecodeError:errors.append('nontext payload '+name);continue
  # Byte scanning is a conservative export hygiene check, not language certification.
  if any('\u4e00'<=c<='\u9fff' for c in text):errors.append('non-English CJK text '+name)
  if any(x in text for x in ['/work'+'space/','/ho'+'me/','/ro'+'ot/']):errors.append('machine-root path '+name)
  if p.suffix=='.json':
   try:json.loads(text)
   except ValueError:errors.append('invalid JSON '+name)
 return sorted(set(errors))
if __name__=='__main__':
 e=verify(Path(__file__).resolve().parents[1]);print(json.dumps({'passed':not e,'errors':e,'scope':'exact original-file export'}));sys.exit(bool(e))
