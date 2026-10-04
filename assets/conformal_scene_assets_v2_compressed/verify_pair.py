"""Verify exact final task-to-scene selectors and byte pins; no hardware action."""
from pathlib import Path
import json,hashlib,sys
P=Path(__file__).resolve().parent
args=[x for x in sys.argv[1:] if x!='--write'];T=Path(args[0]) if args else P.parent/'conformal_operations_v3_compressed'
j=lambda p:json.loads(p.read_text());h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=j(P/'operation_binding_contract.json');aff={x['name']:x for x in j(P/'affordances.json')['anchors']};o=j(T/'operations.json');b=j(T/'asset_binding_plan.json');ops={x['id']:x for x in o['operations']};plan={x['operation_id']:x for x in b['operation_bindings']};scene={x['operation_id']:x for x in c['operations']}
checks=[]
def check(n,v):checks.append({'check':n,'passed':bool(v)})
expected={f'R{i:02}' for i in range(1,17)}
check('exact_16_operations',set(ops)==set(plan)==set(scene)==expected and len(o['operations'])==len(b['operation_bindings'])==len(c['operations'])==16)
check('frozen_nominal_status',b['status']=='frozen_nominal_pairing')
check('exact_9_branches',{x['id'] for x in j(T/'branches.json')['branches']}==set(c['branch_ids']))
for rid in sorted(expected):
 r,p,s=ops[rid],plan[rid],scene[rid]
 check(rid+'_memberships',r['asset_ids']==p['asset_ids']==s['asset_ids'])
 check(rid+'_owner',p['primary_asset_id']==s['primary_asset_id'])
 check(rid+'_roots',p['root_node_ids']==['ASSET.'+x for x in s['asset_ids']])
 check(rid+'_targets',all(p[k]==s[k] for k in ['primary_target','control_target']))
 check(rid+'_anchors',p['anchor_ids']==[s['primary_anchor'],s['control_anchor']])
 check(rid+'_physical_hold',p['physical_qualified'] is False and s['physical_execution_enabled'] is False and r['physical_execution_qualified'] is False and s['qualified_pose'] is None)
 for role in ['primary','control']:
  anchor=aff[s[role+'_anchor']]
  check(rid+'_'+role+'_coordinates',p['anchor_positions_m'][s[role+'_anchor']]==anchor['position_m'] and anchor['target_mesh']==s[role+'_target'] and anchor['owner']==s['primary_asset_id'])
check('exact_11_scene_pins',len(b['final_asset_hashes'])==11 and len({x['path'] for x in b['final_asset_hashes']})==11)
for pin in b['final_asset_hashes']:
 f=P/pin['path'];check('pin_'+pin['path'],f.is_file() and f.stat().st_size==pin['bytes'] and h(f)==pin['sha256'])
files=['operations.json','branches.json','unknown_parameters.json','controls_and_repeats.json','lineage_contract.json','tests/contract.py','tests/verify_pairing.py','RELEASE_BOUNDARY.json','asset_binding_plan.json']
source=[{'task_file':f,'sha256':h(T/f),'bytes':(T/f).stat().st_size} for f in files]
receipt={'schema':'sciencegym.conformal.exact_pair_recheck.v1','passed':all(x['passed'] for x in checks),'asset_pack_id':'conformal_scene_assets_v2_compressed','task_id':'conformal_operations_v3_compressed','operation_count':16,'branch_count':9,'operation_anchor_count':32,'pinned_asset_file_count':11,'task_files':source,'checks':checks,'physical_validation':False,'scientific_validation':False,'archive_pair_seal':'Final archive hashes must be bound externally; no self-hash cycle'}
if not receipt['passed']:
 print(json.dumps(receipt,indent=2));raise SystemExit(1)
if '--write' in sys.argv:
 (P/'paired_task_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 (P/'task_binding_snapshot.json').write_text(json.dumps({'schema':'sciencegym.conformal.task_binding_snapshot.v1','task_id':'conformal_operations_v3_compressed','task_files':source,'binding_plan':b,'operation_summary':[{'id':x['id'],'name':x['name'],'asset_ids':x['asset_ids']} for x in o['operations']],'physical_execution_enabled':False},indent=2)+'\n')
print(json.dumps({'passed':receipt['passed'],'checks':len(checks),'task_files':source},indent=2))
