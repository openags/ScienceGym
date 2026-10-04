"""Verify final task-to-scene semantic and byte binding; no physical validation."""
from pathlib import Path,PurePosixPath
import json,hashlib,sys,math
ROOT=Path(__file__).resolve().parents[1]
REQUIRED_PINS={'affordances.json','asset_inventory.json','assembly_contract.json','operation_binding_contract.json','operation_bindings.json','semantic_controls.py','states.json','station_layout.json','specimen_geometry.json','asset_metadata.json','geometry/midinfrared_lab.glb','geometry/midinfrared_lab.blend'}
class PairingError(ValueError):pass
def require(ok,message):
 if not ok:raise PairingError(message)
def verify(asset_root):
 a=Path(asset_root);require(a.is_dir() and not a.is_symlink(),'regular asset directory');task=json.loads((ROOT/'asset_binding_plan.json').read_text());require(task['status']=='frozen_nominal_pairing','final asset freeze required')
 pins=task['final_asset_hashes'];require(len(pins)==len({x['path'] for x in pins}) and {x['path'] for x in pins}==REQUIRED_PINS,'exact required semantic/geometry pins')
 for pin in pins:
  n=pin['path'];p=PurePosixPath(n);require(not p.is_absolute() and str(p)==n and '..' not in p.parts,'canonical pin path');f=a/n;require(f.is_file() and not f.is_symlink(),'regular asset pin file');data=f.read_bytes();require(len(data)==pin['bytes'] and hashlib.sha256(data).hexdigest()==pin['sha256'],'final asset byte hash: '+n)
 def read(n):return json.loads((a/n).read_text())
 contract=read('operation_binding_contract.json');second=read('operation_bindings.json');aff=read('affordances.json');inv=read('asset_inventory.json');meta=read('asset_metadata.json')
 require(contract['operations']==second['operations'],'duplicate binding views agree');require(meta['asset_pack_id']==task['asset_pack_id'] and meta['task_id']=='midinfrared_operations_v2','package identity')
 require(meta['physical_geometry_validated'] is False and meta['physical_execution_enabled'] is False,'nominal qualification boundary')
 roots={x['asset_id']:x['root'] for x in inv['assets']};owners={p['scene_object']:x['asset_id'] for x in inv['assets'] for p in x['parts']};parts={p['scene_object']:p for x in inv['assets'] for p in x['parts']};anchors={x['anchor_id']:x for x in aff['anchors']};scene_ops={x['operation_id']:x for x in contract['operations']}
 require(len(roots)==13 and len(anchors)==44 and len(scene_ops)==22,'pairing counts');require(len(owners)==sum(len(x['parts']) for x in inv['assets']),'unique concrete objects');count=0
 for b in task['operation_bindings']:
  o=scene_ops[b['operation_id']]
  for k in ['asset_ids','primary_asset_id','primary_target','control_target']:require(b[k]==o[k],'exact scene/task '+k+' '+b['operation_id'])
  require(b['root_node_ids']==[roots[x] for x in b['asset_ids']],'canonical root ownership')
  for kind in ('primary','control'):
   name=o[kind+'_anchor'];require(name in b['anchor_ids'] and name in anchors,'anchor identity');r=anchors[name];target=o[kind+'_target'];require(target in parts and r['target_object_id']==target and r['asset_id']==owners[target]==o['primary_asset_id'],'concrete target ownership')
   pos=r['translation_m'];require(len(pos)==3 and all(type(x) in (float,int) and math.isfinite(x) for x in pos),'finite nominal anchor')
   require(all(abs(x-y)<1e-6 for x,y in zip(pos,parts[target]['translation_m'])),'world-space target correspondence')
   require(b['anchor_positions_m'][name]==pos,'task pinned nominal anchor coordinates');require(r['qualified_pose'] is None and r['physical_execution_enabled'] is False,'unqualified nominal anchor');count+=1
 return {'passed':True,'operation_bindings':22,'anchor_bindings':count,'pinned_asset_files':len(pins),'physical_execution':False,'geometry_qualification':False}
if __name__=='__main__':
 try:
  require(len(sys.argv)==2,'Supply the separate asset package directory');print(json.dumps(verify(sys.argv[1]),indent=2))
 except (PairingError,OSError,KeyError,ValueError) as e:print(str(e));sys.exit(1)
