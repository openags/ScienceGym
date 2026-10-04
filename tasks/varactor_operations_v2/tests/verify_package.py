"""Read-only structural checks, not scientific or physical validation."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
def pairs(items):
 d={}
 for k,v in items:
  if k in d:raise ValueError('duplicate JSON key')
  d[k]=v
 return d
def read(p):return json.loads(Path(p).read_text(),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def verify(root=ROOT):
 root=Path(root);errors=[]
 def check(ok,msg):
  if not ok:errors.append(msg)
 try:
  docs={p.name:read(p) for p in root.glob('*.json') if p.name!='EXPORT_ALLOWLIST.json'}
  branches=docs['branches.json']['branches'];operations=docs['operations.json']['operations'];assets=docs['asset_binding_plan.json']['scene_assets'];evidence=docs['evidence_map.json']['evidence']
  bid={b['id'] for b in branches};oid={o['id'] for o in operations};aid={a['asset_id'] for a in assets};eid={e['id'] for e in evidence}
  check(len(branches)==len(bid)==28,'28 unique scientific routes');check(len(operations)==len(oid)==80,'80 unique operations');check(len(assets)==len(aid)==12,'12 unique asset groups');check(sum(len(a['required_anchor_ids']) for a in assets)==65,'65 anchors');check(len(evidence)==len(eid)==49,'49 evidence locators')
  check(set(docs['agent_visible.json']['allowed_operations'])==oid,'actor operation set');check(docs['evaluator_reference.json']['actor_visible_allowlist']==['agent_visible.json'],'actor projection')
  for b in branches:
   check(bool(b['source_evidence_ids']) and set(b['source_evidence_ids'])<=eid,'branch source '+b['id']);check(set(b['operation_ids'])<=oid and set(b['route_operation_ids'])<=set(b['operation_ids']),'branch operations '+b['id']);check(b['design_covered'] is True and b['physical_executed'] is False and b['numerical_executed'] is False,'branch boundary '+b['id'])
  for o in operations:
   check(bool(o['branch_ids']) and set(o['branch_ids'])<=bid,'operation branches '+o['id']);check(set(o['source_evidence_ids'])<=eid,'operation sources '+o['id']);check(set(o['asset_ids'])<=aid,'operation assets '+o['id']);check(o['device_command_implemented'] is False and o['physical_execution_authority'] is False,'operation boundary '+o['id'])
   check(set(o['branch_ids'])=={b['id'] for b in branches if o['id'] in b['operation_ids']},'reciprocal operation '+o['id'])
  bound=[op for a in assets for op in a['bind_operation_ids']];check(set(bound)==oid and len(bound)==len(set(bound)),'one-group operation binding')
  for a in assets:check(a['physical_geometry_validated'] is False and len(a['required_anchor_ids'])==len(set(a['required_anchor_ids'])),'asset boundary/anchors')
  for c in docs['source_conflicts.json']['conflicts']:check(set(c['branch_ids'])<=bid and set(c['source_evidence_ids'])<=eid,'conflict references')
  check(len(docs['source_conflicts.json']['conflicts'])==12,'12 conflicts and scope distinctions')
  coverage=docs['coverage_matrix.json']
  for key,n in [('main_figures',5),('supplementary_figures',5),('supplementary_sections',4)]:
   check(len(coverage[key])==n,'coverage '+key)
   for refs in coverage[key].values():check(bool(refs) and set(refs)<=bid,'coverage references '+key)
  audit=docs['source_access_audit.json'];check(audit['main_read']['visual_figures']==[1,2,3,4,5],'main visual read');check(audit['si_read']['pdf_pages']==6 and audit['si_read']['visual_figures']==[1,2,3,4,5],'SI read')
  check(docs['shared_specimen_contract.json']['same_physical_varactor_pair'] is True,'shared STO identity')
  cards=docs['circuit_family_cards.json']['cards'];check({c['id'] for c in cards}=={'FIXED_LOAD','SQD','DQD'},'three circuit families')
  status=docs['STATUS.json'];check(status['operation_count']==80 and status['design_route_count']==28,'status counts')
  for k in ('whole_paper_execution_complete','full_paper_execution_eligible','whole_paper_complete','qualifies_for_full_paper_execution_count','scientific_reproduction_run','physical_geometry_validated'):check(status[k] is False,'status gate '+k)
  boundary=docs['RELEASE_BOUNDARY.json']
  for k in ('whole_paper_execution_complete','physical_execution','numerical_execution','scientific_reproduction','source_files_exported','exact_geometry_validated'):check(boundary[k] is False,'release boundary '+k)
  check(boundary['validated_runnable_whole_paper_tasks']==0,'zero executable tasks')
  for p in root.rglob('*'):
   if p.is_file() and p.suffix in ('.json','.md','.py'):
    s=p.read_text();check(('/'+'workspace/') not in s and ('/'+'root/') not in s and ('sediment'+':/'+'/') not in s,'private path '+p.name)
 except (OSError,ValueError,KeyError,TypeError) as e:errors.append('unreadable contract: '+str(e))
 return errors
if __name__=='__main__':
 e=verify();print(json.dumps({'passed':not e,'errors':e},indent=2));sys.exit(bool(e))
