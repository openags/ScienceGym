"""Recheck exact final nominal task/asset pairing. No hardware or device operations.

Pass the separately distributed task directory, or use the default sibling
midinfrared_operations_v2. --write saves snapshot/receipt after all checks pass.
"""
from pathlib import Path
import hashlib,json,sys
P=Path(__file__).resolve().parent
args=[a for a in sys.argv[1:] if a!='--write'];T=Path(args[0]) if args else P.parent/'midinfrared_operations_v2'
def j(p):return json.loads(p.read_text())
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
c=j(P/'operation_binding_contract.json');a=j(P/'affordances.json');task=j(T/'operations.json');b=j(T/'asset_binding_plan.json')
expected={f'R{i:02}' for i in range(1,23)}
ops={o['id']:o for o in task['operations']};plan={o['operation_id']:o for o in b['operation_bindings']};scene={o['operation_id']:o for o in c['operations']};anchors={o['anchor_id']:o for o in a['anchors']}
checks=[]
def check(n,v):
    checks.append({'check':n,'passed':bool(v)})
check('exact_22_ids',set(ops)==set(plan)==set(scene)==expected and len(task['operations'])==len(b['operation_bindings'])==len(c['operations'])==22)
check('frozen_nominal_status',b['status']=='frozen_nominal_pairing')
for rid in sorted(expected):
    o,p,s=ops[rid],plan[rid],scene[rid]
    check(rid+'_memberships',o['asset_ids']==p['asset_ids']==s['asset_ids'])
    check(rid+'_owner',p['primary_asset_id']==s['primary_asset_id'])
    check(rid+'_roots',p['root_node_ids']==['ASSET.'+x for x in s['asset_ids']])
    check(rid+'_targets',all(p[k]==s[k] for k in ['primary_target','control_target']))
    check(rid+'_anchors',p['anchor_ids']==[s['primary_anchor'],s['control_anchor']])
    check(rid+'_physical_hold',p['physical_qualified'] is False and p['qualified_pose'] is None and s['physical_execution_enabled'] is False and o['physical_execution_qualified'] is False)
    for role in ['primary','control']:
        aid=s[role+'_anchor'];position=p['anchor_positions_m'][aid]
        check(rid+'_'+role+'_coordinates',position==anchors[aid]['translation_m'] and anchors[aid]['target_object']==s[role+'_target'])
check('exact_12_pinned_asset_files',len(b['final_asset_hashes'])==12 and len({x['path'] for x in b['final_asset_hashes']})==12)
for f in b['final_asset_hashes']:
    p=P/f['path'];check('pinned_'+f['path'],p.is_file() and p.stat().st_size==f['bytes'] and h(p)==f['sha256'])
source_files=[{'task_file':n,'sha256':h(T/n),'bytes':(T/n).stat().st_size} for n in ['operations.json','asset_binding_plan.json']]
receipt={'schema':'sciencegym.midinfrared.exact_pair_recheck.v1','passed':all(x['passed'] for x in checks),'asset_pack_id':'midinfrared_scene_assets_v1','task_id':'midinfrared_operations_v2','operation_count':22,'anchor_count':44,'pinned_asset_file_count':12,'task_files':source_files,'checks':checks,'scope':'Final nominal selector and exact-byte pairing after core asset and task contract edits','physical_validation':False,'scientific_validation':False,'archive_pair_seal':'Both final ZIP hashes must be bound externally to avoid circular self-hashes'}
if not receipt['passed']:
    print(json.dumps(receipt,indent=2));raise SystemExit(1)
if '--write' in sys.argv:
    snapshot={'schema':'sciencegym.midinfrared.task_binding_snapshot.v1','task_id':'midinfrared_operations_v2','source_files':source_files,'operation_summary':[{'id':o['id'],'name':o['name'],'asset_ids':o['asset_ids']} for o in task['operations']],'binding_plan':b,'physical_execution_enabled':False}
    (P/'task_binding_snapshot.json').write_text(json.dumps(snapshot,indent=2)+'\n')
    (P/'paired_task_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'passed':receipt['passed'],'checks':len(checks),'task_files':source_files},indent=2))
