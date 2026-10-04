"""Bind task metadata to canonical original scene anchors; no execution code."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
plan=json.loads((P/'task_binding_snapshot.json').read_text());aff=json.loads((P/'affordances.json').read_text())
anchors={(a['asset_id'],a['anchor_id']):a for a in aff['anchors']}
ops=[]
for asset in plan['scene_assets']:
 for op in asset['bind_operation_ids']:
  ops.append({'operation_id':op,'asset_id':asset['asset_id'],'anchor_ids':asset['required_anchor_ids'],'scene_objects':[anchors[(asset['asset_id'],a)]['scene_object'] for a in asset['required_anchor_ids']],'binding_kind':'symbolic_external_record_role','implementation':'metadata_only','physical_execution':False,'energy_enabled':False,'source_geometry_validated':False,'request_is_observation':False,'qualified_transform':None})
(P/'operation_bindings.json').write_text(json.dumps({'schema':'scene_operation_bindings.v1','task_id':plan['task_id'],'asset_package':plan['asset_package'],'operation_count':len(ops),'binding_status':'ALL_TASK_OPERATIONS_BOUND_TO_STATIC_ORIGINAL_ROLES','does_not_implement_task_services':True,'bindings':ops},indent=2)+'\n')
