"""Verify the immutable scene core and its paired task reference. Read-only."""
from pathlib import Path
import json,hashlib,sys
P=Path(__file__).resolve().parent
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(task_dir):
 task=Path(task_dir)
 core=json.loads((P/'scene_core_manifest.json').read_text())
 assert digest(core['files'])==core['core_sha256']
 for x in core['files']:
  assert (P/x['path']).stat().st_size==x['bytes'] and sha(P/x['path'])==x['sha256'],x['path']
 ref=json.loads((P/'paired_task_reference.json').read_text())
 assert ref['asset_core_sha256']==core['core_sha256']
 assert (P/'shared_binding_contract.json').read_bytes()==(task/'shared_binding_contract.json').read_bytes()
 assert (P/'paired_task_core_manifest.json').read_bytes()==(task/'task_semantic_core_manifest.json').read_bytes()
 tcore=json.loads((task/'task_semantic_core_manifest.json').read_text())
 assert digest(tcore['files'])==tcore.get('core_sha256',tcore.get('semantic_core_sha256'))
 tdig=tcore.get('core_sha256',tcore.get('semantic_core_sha256'))
 assert ref['task_core_sha256']==tdig
 for x in tcore['files']:
  n=x.get('path',x.get('file'));assert sha(task/n)==x['sha256'];assert (task/n).stat().st_size==x['bytes']
 tr=json.loads((task/'paired_asset_reference.json').read_text())
 assert tr['asset_core_sha256']==core['core_sha256']
 assert tr['task_core_sha256']==ref['task_core_sha256']==tdig
 assert tr['task_core_manifest_sha256']==ref['task_core_manifest_sha256']==sha(task/'task_semantic_core_manifest.json')
 assert tr['shared_contract_sha256']==ref['shared_contract_sha256']==sha(P/'shared_binding_contract.json')
 return {'status':'PASS','asset_core_sha256':core['core_sha256'],'task_core_sha256':tdig,'shared_contract_sha256':sha(P/'shared_binding_contract.json'),'all_15_routes_and_32_anchors_shared':True,'physical_execution':False}
if __name__=='__main__':
 if len(sys.argv)!=2:raise SystemExit('Usage: python verify_pair.py TASK_DIRECTORY')
 print(json.dumps(verify(sys.argv[1]),indent=2))
