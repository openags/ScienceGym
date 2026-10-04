"""Pinned text-only export. Consistency checks are not security or scientific certification."""
from pathlib import Path
import json,hashlib,sys
EXPECTED=set('''EXPORT_ALLOWLIST.json EXPORT_SCOPE.md README.md RELEASE_BOUNDARY.json REVIEW_NOTES.md STATUS.json TASK_DESIGN.md VERIFICATION.json adversarial_cases.json agent_visible.json analysis_contracts.json asset_binding_plan.json branches.json control_packages.json coverage_matrix.json design_assumptions.json episode_input_contract.json evaluator_reference.json evidence_map.json lineage_contract.json material_cards.json mock_contract.json nonmanual_scope.json operations.json preparation_routes.json provenance.json source_access_audit.json source_conflicts.json station_contracts.json transport_routes.json unknown_parameters.json tests/contract.py tests/test_contract.py tests/test_export.py tests/verify_package.py tests/verify_export.py review/REPORT.md review/audit.json review/adversarial_review.py'''.split())
def verify(root):
 root=Path(root);errors=[]
 try:m=json.loads((root/'EXPORT_ALLOWLIST.json').read_text())
 except (OSError,ValueError):return ['invalid manifest']
 if type(m) is not dict:return ['manifest type']
 try:
  if set(m.get('files',[]))!=EXPECTED or len(m.get('files',[]))!=len(EXPECTED):errors.append('independently pinned inventory mismatch')
  if set(m.get('payload_sha256',{}))!=EXPECTED-{'EXPORT_ALLOWLIST.json'}:errors.append('hash inventory mismatch')
  if m.get('actor_file_allowlist')!=['agent_visible.json']:errors.append('actor boundary broadened')
  if m.get('publisher_files_included') is not False:errors.append('publisher-source claim changed')
  paths=list(root.rglob('*'));actual={str(p.relative_to(root)) for p in paths if p.is_file() or p.is_symlink()}
  if actual!=EXPECTED:errors.append('actual inventory mismatch')
  for p in paths:
   if p.is_symlink():errors.append('symlink forbidden')
   if p.is_dir() and str(p.relative_to(root)) not in ['tests','review']:errors.append('unexpected directory')
  for name in EXPECTED-{'EXPORT_ALLOWLIST.json'}:
   p=root/name
   if not p.is_file() or p.is_symlink():errors.append('missing/nonregular '+name);continue
   if not p.resolve().is_relative_to(root.resolve()):errors.append('path escape');continue
   raw=p.read_bytes()
   if hashlib.sha256(raw).hexdigest()!=m.get('payload_sha256',{}).get(name):errors.append('hash mismatch '+name)
   try:text=raw.decode('utf8')
   except UnicodeDecodeError:errors.append('nontext '+name);continue
   if any('\u4e00'<=c<='\u9fff' for c in text):errors.append('non-English CJK '+name)
   if any(s in text for s in ['/work'+'space/','/ho'+'me/','/ro'+'ot/']):errors.append('machine path '+name)
   if p.suffix=='.json':
    try:json.loads(text,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
    except ValueError:errors.append('invalid/nonfinite JSON '+name)
 except (ValueError,TypeError,AttributeError,OSError):errors.append('malformed export fails closed')
 return sorted(set(errors))
if __name__=='__main__':
 e=verify(Path(__file__).resolve().parents[1]);print(json.dumps(dict(passed=not e,errors=e,scope='fixed original text-only export')));sys.exit(bool(e))
