"""Read-only static package consistency checks; no measurement validation."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def verify(root=ROOT):
 errors=[]
 def check(x,msg):
  if not x:errors.append(msg)
 def load(n):return json.loads((root/n).read_text())
 try:
  branches=load('branches.json');B={x['id']:x for x in branches['branches']};ops=load('operations.json');O={x['id']:x for x in ops['operations']};S={x['id']:x for x in load('station_contracts.json')['stations']};U={x['id']:x for x in load('unknown_parameters.json')['parameters']};E={x['id']:x for x in load('provenance.json')['evidence']};C={x['id'] for x in load('control_packages.json')['controls']}
  check(len(B)==28 and len(B)==len(branches['branches']),'branch count or uniqueness')
  check({x['family_id'] for x in B.values()}=={'R'+str(i) for i in range(1,9)},'eight-family coverage')
  check(len(O)==196 and len(O)==len(ops['operations']),'operation count or uniqueness')
  for b in B.values():
   check(len(b['operation_ids'])==7 and len(set(b['operation_ids']))==7,'seven distinct phases')
   check(set(b['required_branch_ids'])<=set(B),'unknown dependency')
   check(b['execution_ready'] is False and b['expected_results_actor_visible'] is False,'readiness/leakage flag')
   check(set(b['unknown_parameter_ids'])<=set(U) and set(b['source_evidence_ids'])<=set(E) and set(b['control_ids'])<=C,'dangling contract reference')
   check(b['station_id'] in S,'unknown station')
   for n,i in enumerate(b['operation_ids']):
    op=O.get(i,{});check(op.get('branch_id')==b['id'] and op.get('station_id')==b['station_id'],'operation binding')
    check(op.get('phase')==['PREPARE','LOAD','VERIFY','RUN','READOUT','RETRIEVE','CLEANUP'][n],'phase mismatch')
    check(op.get('authored_translation') is True and op.get('physical_execution_implemented') is False,'operation attribution/readiness')
    check(all(op.get(k) for k in ['sample_or_payload','instrument','pose','transport','actions','control_ids','source_evidence_ids','unknown_parameter_ids','required_receipts','failure_recovery']),'incomplete operation contract')
  def visit(i,stack):
   if i in stack:raise ValueError('dependency cycle')
   for j in B[i]['required_branch_ids']:visit(j,stack+[i])
  for i in B:visit(i,[])
  check(all(u['value'] is None and u['blocks_execution'] is True for u in U.values()),'invented unknown default')
  actor=load('agent_visible.json');check(actor['source_targets_included'] is False and actor['future_measurements_included'] is False and actor['current_observations']==[],'actor future/source leakage')
  check(set(actor)=={'schema_version','doi','visibility','goal','allowed_actions','forbidden_actions','initial_inventory','qualified_cards','current_observations','source_targets_included','future_measurements_included','runtime_observations_must_come_from','simulation_outputs_may_claim_observation'},'actor schema mismatch')
  access=load('source_access_audit.json');check(access['main_figures_pixel_inspected'] is False and access['main_local_byte_complete'] is False and access['source_complete_for_entire_paper'] is False,'source coverage overclaim')
  check(access['main_direct_byte_hold']['retry_permitted_by_this_package'] is False,'identity hold removed')
  conflicts={c['id']:c for c in load('source_conflicts.json')['conflicts']};check(len(conflicts)==6 and all(c['resolved'] is False for c in conflicts.values()),'source conflict lost')
  check(conflicts['C_COVARIANCE']['values']['prose_frames']==1000 and conflicts['C_COVARIANCE']['values']['caption_frames']==7000,'covariance merge')
  check(conflicts['C_FOV']['values']=={'caption_arcsec':856,'prose_and_ed9_arcsec':865},'FOV correction')
  check(conflicts['C_RMSE']['values']=={'prose_reduction_nm':195,'caption_before_nm':224.10,'caption_after_nm':109.84},'RMSE correction')
  check(B['DAYTIME25']['classification']=='physical_observation' and B['SIM_POINTS']['classification']=='numerical_simulation','daytime/point-source classification')
  check(B['DAYTIME25']['source_parameters']['frame_count'] is None and B['DAYTIME25']['source_parameters']['exposure_ms'] is None,'daytime settings fabricated')
  check(B['TIS']['source_parameters']['active_scan'] is False,'active scan fabricated')
  check(B['CORRECTED']['source_parameters']['retain_system_aberration'] is True and B['PREDICT']['source_parameters']['remove_system_aberration'] is True,'mode convention changed')
  rows=load('coverage_matrix.json')['rows'];check({b for r in rows for b in r['branch_ids']}==set(B),'coverage branch omission')
  check(all(r['execution_evidence'] is False for r in rows),'coverage execution overclaim')
  for file in root.rglob('*.json'):
   if file.name=='EXPORT_ALLOWLIST.json' or file.parts[-2]=='review':continue
   d=json.loads(file.read_text());check(d.get('doi')=='10.1038/s41566-024-01466-3','cross-paper DOI '+str(file.relative_to(root)))
 except Exception as e:errors.append(type(e).__name__+': '+str(e))
 return {'check':'static_package','passed':not errors,'errors':errors,'no_execution_or_physics':True}
if __name__=='__main__':
 r=verify();print(json.dumps(r,indent=2));raise SystemExit(not r['passed'])
