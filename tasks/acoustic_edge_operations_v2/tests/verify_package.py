"""Static exact-payload verifier. No robot, network, or physical/numerical simulation."""
from pathlib import Path
import hashlib,json,sys

EXPECTED = {
 'README.md','TASK_DESIGN.md','EXPORT_SCOPE.md','EXPORT_ALLOWLIST.json','STATUS.json','VERIFICATION.json',
 'provenance.json','source_access_audit.json','operations.json','branches.json','dependencies.json','material_cards.json',
 'station_contracts.json','lineage_contract.json','control_packages.json','source_conflicts.json','source_outcomes.json',
 'nonmanual_scope.json','coverage_matrix.json','unknown_parameters.json','episode_input_contract.json','agent_visible.json',
 'RELEASE_BOUNDARY.json','evaluator_reference.json','mock_contract.json','asset_needs.json',
 'tests/record_contract.py','tests/verify_package.py','tests/test_acoustic_edge_contract.py','tests/VALIDATION_REPORT.md',
 'tests/validation_report.json','tests/SOURCE_FIDELITY_REVIEW.md'
}

def verify(root, hashes=True):
 root=Path(root); errors=[]
 actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() or p.is_symlink()}
 if actual!=EXPECTED:errors.append('exact_path_set_mismatch:'+str(sorted(actual^EXPECTED)))
 for name in actual:
  p=root/name
  if p.is_symlink():errors.append('symlink:'+name)
  if p.suffix in ('.pdf','.jpg','.png','.jpeg','.zip'):errors.append('forbidden_source_binary:'+name)
  if p.is_file() and not p.is_symlink() and p.suffix in ('.json','.md','.py'):
   try:text=p.read_text(encoding='utf-8')
   except UnicodeError:errors.append('nontext:'+name);continue
   if any(x in text for x in ['/'+'workspace/','/'+'tmp/','/'+'root/.codex','sediment'+':/'+'/']):errors.append('private_path:'+name)
   if any('\u4e00'<=c<='\u9fff' for c in text):errors.append('non_english_cjk:'+name)
   if p.suffix=='.json':
    try:json.loads(text)
    except ValueError:errors.append('invalid_json:'+name)
 if errors and any(x.startswith(('exact_path','invalid_json')) for x in errors):return errors
 try:
  load=lambda n:json.loads((root/n).read_text())
  ops=load('operations.json')['operations']; by={o['id']:o for o in ops}; ev=load('provenance.json')['evidence']; us={u['id'] for u in load('unknown_parameters.json')['unknowns']}
  if len(by)!=len(ops) or load('operations.json')['operation_count']!=len(ops):errors.append('operation_count')
  for o in ops:
   for key in ['preconditions','postconditions','actions','required_observations','failure_handling','object_roles']:
    if not o.get(key):errors.append('empty_operation_contract:'+o['id']+':'+key)
   if not set(o['depends_on'])<=set(by):errors.append('unknown_dependency')
   if not set(o['evidence_ids'])<=set(ev):errors.append('unknown_evidence')
   if not set(o['unknown_parameter_ids'])<=us:errors.append('unknown_gate')
  edges={(x['before'],x['after']) for x in load('dependencies.json')['edges']}
  if edges!={(d,o['id']) for o in ops for d in o['depends_on']}:errors.append('dependency_file_disagreement')
  station_ids={s['id'] for s in load('station_contracts.json')['stations']}|{'route_destination','current_station'}
  if any(o['station_id'] not in station_ids for o in ops):errors.append('undefined_station')
  active=set();done=set()
  def visit(i):
   if i in active:raise ValueError('dependency_cycle')
   if i in done:return
   active.add(i)
   for d in by[i]['depends_on']:visit(d)
   active.remove(i);done.add(i)
  for i in by:visit(i)
  branches=load('branches.json'); bs={b['id'] for b in branches['branches']}
  if bs!={'NO_OBJECT','HALF_APERTURE','SINGLE_EDGE_1D','PLATE_32_1D','ROD_10_1D','DISC_2D','ETH_2D'}:errors.append('physical_branch_set')
  for b in branches['branches']:
   if not set(b['operation_ids'])<=set(by):errors.append('unknown_branch_operation')
   if not set(b['unknown_parameter_ids'])<=us:errors.append('unknown_branch_gate')
  if set(branches['campaign']['required_branch_ids'])!=bs:errors.append('incomplete_campaign')
  for row in load('coverage_matrix.json')['rows']:
   if not set(row['evidence_ids'])<=set(ev) or not set(row['operation_ids'])<=set(by) or not set(row['task_branch_ids'])<=bs:errors.append('coverage_reference')
  access=load('source_access_audit.json')
  if access['main']['source_byte_sha256'] is not None or access['main']['local_pdf_bytes_obtained'] is not False:errors.append('invented_main_source_bytes')
  if access['main']['record_hash_is_source_hash'] is not False:errors.append('receipt_hash_misrepresented')
  status=load('STATUS.json')
  if any(status[k] is not False for k in ['exact_replication_ready','robot_execution_ready','scene_asset_binding_ready','trusted_runtime_evaluator_ready','numerical_execution_ready']):errors.append('unsupported_readiness')
  if any(status[k]!=0 for k in ['physical_execution_count','physics_run_count','public_write_count']):errors.append('unsupported_execution')
  actor=load('agent_visible.json')
  if any(actor[k] is not False for k in ['reference_routes_included','literature_targets_included','numerical_oracle_included']):errors.append('actor_leakage_flag')
  for g in actor['goals']:
   if g.get('expected_scientific_outcomes') is not None or any(k in g for k in ['operation_ids','reference_route','source_outcomes','hidden_faults']):errors.append('actor_oracle')
  m=load('EXPORT_ALLOWLIST.json')
  if set(m.get('allowlist',[]))!=EXPECTED or len(m.get('allowlist',[]))!=len(EXPECTED):errors.append('manifest_allowlist_broadened')
  records=m.get('files',[]); paths=[f.get('path') for f in records]
  if len(paths)!=len(set(paths)) or set(paths)!=(EXPECTED-{'EXPORT_ALLOWLIST.json'}):errors.append('manifest_payload_set')
  if m.get('payload_file_count')!=len(EXPECTED)-1 or m.get('total_file_count_including_manifest')!=len(EXPECTED):errors.append('manifest_count')
  if hashes:
   for f in records:
    name=f.get('path')
    if name not in EXPECTED or name=='EXPORT_ALLOWLIST.json':continue
    p=root/name
    if p.is_symlink():continue
    data=p.read_bytes()
    if len(data)!=f.get('bytes') or hashlib.sha256(data).hexdigest()!=f.get('sha256'):errors.append('payload_hash:'+name)
 except (KeyError,TypeError,ValueError) as ex:errors.append('invalid_contract:'+str(ex))
 return sorted(set(errors))

if __name__=='__main__':
 root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
 errors=verify(root)
 print(json.dumps({'scope':'static_contract_and_exact_payload_only','passed':not errors,'errors':errors},indent=2))
 raise SystemExit(bool(errors))
