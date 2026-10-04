"""Resolve all symbolic task bindings to actual scene anchors without authorizing motion."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
plan=json.loads((P/'operation_binding_contract.json').read_text());aff=json.loads((P/'affordances.json').read_text());inventory=json.loads((P/'asset_inventory.json').read_text())
anchors={a['scene_object']:a for a in aff['anchors']};rows=[]
for b in plan['operation_bindings']:
 assert all(a in anchors for a in b['anchor_ids'])
 rows.append({**b,'resolved_anchors':[anchors[a] for a in b['anchor_ids']],'static_asset_available':True,'physical_execution':False,'physics_implemented':False})
for a in inventory['assets']:a['operation_ids']=next(x['bind_operation_ids'] for x in plan['assets'] if x['asset_id']==a['asset_id'])
(P/'asset_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
(P/'operation_bindings.json').write_text(json.dumps({'schema':'wetting_original_scene_bindings.v1','operation_count':len(rows),'anchor_count':len(anchors),'asset_group_count':len(inventory['assets']),'bindings':rows,'safe_close_operation_ids':['R15_O01','R15_O02','R15_O03','R15_O04'],'physical_execution':False},indent=2)+'\n')
print(f"Resolved {len(rows)} exact operations to {len(anchors)} anchors in {len(inventory['assets'])} groups")
