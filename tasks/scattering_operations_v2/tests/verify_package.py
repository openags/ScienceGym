"""Structural cross-file and scientific-boundary checks; no scientific execution."""
from pathlib import Path
import json, math, sys
ROOT=Path(__file__).resolve().parents[1]
def read(path):
 def pairs(items):
  out={}
  for k,v in items:
   if k in out:raise ValueError('duplicate JSON key')
   out[k]=v
  return out
 return json.loads(Path(path).read_text(),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def verify(root=ROOT):
 root=Path(root); checks=[]
 def require(ok,label):
  if not ok:raise ValueError(label)
  checks.append(label)
 for p in root.rglob('*.json'):read(p)
 ops=read(root/'operations.json')['operations']; shared=read(root/'shared_binding_contract.json'); branches=read(root/'branches.json')['branches']
 require([o['id'] for o in ops]==[f'R{i:02}' for i in range(1,15)],'14 stable operations')
 require(shared['operation_ids']==[o['id'] for o in ops],'shared operation equality')
 require(len(shared['asset_groups'])==11,'11 asset groups')
 anchors=[x for a in shared['asset_groups'] for x in a['anchor_ids']]
 require(len(anchors)==len(set(anchors))==32,'32 unique anchors')
 for op,bind in zip(ops,shared['operation_bindings']):
  require(op['id']==bind['operation_id'] and op['asset_ids']==bind['asset_ids'] and op['anchor_ids']==bind['anchor_ids'],'operation/asset/anchor join '+op['id'])
  require(op['physical_execution_enabled'] is False,'disabled operation '+op['id'])
  require(op['action_interface']['allowed_keys']==['operation_id','evidence_ids'],'actor ID-only '+op['id'])
  require(op['action_interface']['numeric_or_hardware_arguments_allowed'] is False,'no numeric actuation '+op['id'])
 require({b['id'] for b in branches if b['source_reported_kind']=='reported_experimental_branch'}=={'B01','B02','B03','B04','B05'},'five experimental source branches')
 require({b['id'] for b in branches if b['source_reported_kind']=='numerical_review_only'}=={'A01','A02','A03','A04'},'four numerical-only source branches')
 require(all(b['default_repeat_count'] is None and b['physical_executed'] is False and b['numerical_executed'] is False for b in branches),'branch null repeats and nonexecution')
 facts={f['id'] for f in read(root/'source_evidence.json')['facts']};unknowns={u['id'] for u in read(root/'unknowns.json')['unknowns']};controls={k['id'] for k in read(root/'controls_and_repeats.json')['controls']}
 require(len(facts)==26 and len(unknowns)==16 and len(controls)==12,'source evidence inventory')
 for branch in branches:
  require(set(branch['source_facts'])<=facts and set(branch['blocking_unknowns'])<=unknowns and set(branch['controls'])<=controls,'branch evidence joins '+branch['id'])
 require(len(read(root/'source_conflicts.json')['records'])==8,'eight source ambiguities')
 tables=read(root/'source_table_inventory.json')
 require(sum(t['entry_count'] for t in tables['tables'])==tables['total_entries_visually_checked']==152,'152 reviewed table entries')
 require([t['entry_count'] for t in tables['tables']]==[30,30,20,36,36] and tables['exported_values'] is False,'table inventory not CAD')
 scope=read(root/'release_boundary.json')
 require(scope['paper_design_count']==1 and scope['actual_hardware_actions']==scope['physical_simulations']==scope['scientific_reproductions']==0,'one design zero experiments')
 require(scope['physical_default']=='HOLD_QUALIFICATION' and scope['physical_execution_enabled'] is False,'physical default held')
 require(read(root/'source_update_status.json')['exhaustive_guarantee'] is False,'bounded update check')
 require(read(root/'controls_and_repeats.json')['source_independent_repeat_count'] is None,'unknown source repeats')
 return {'passed':True,'assertions':len(checks),'scope':'structure_and_design_boundaries_only'}
if __name__=='__main__':
 try: print(json.dumps(verify(),indent=2))
 except (ValueError,KeyError,OSError) as e: print(str(e));sys.exit(1)
