"""Verify scene core and exact paired task semantic core without circular hashes."""
import argparse,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--task-root',required=True,type=Path);args=parser.parse_args()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(items):return hashlib.sha256(json.dumps(items,sort_keys=True,separators=(',',':')).encode()).hexdigest()
scene=json.loads((ROOT/'scene_core_manifest.json').read_text());task=json.loads((ROOT/'paired_task_core_reference.json').read_text())
assert canonical(scene['files'])==scene['core_sha256']
assert canonical(task['files'])==task['semantic_core_sha256']
for manifest,base,key in [(scene,ROOT,'file'),(task,args.task_root,'path')]:
 for item in manifest['files']:
  p=Path(item[key]);assert not p.is_absolute() and '..' not in p.parts
  f=base/p;assert f.stat().st_size==item['bytes'] and digest(f)==item['sha256'],p
assert digest(ROOT/'asset_binding_contract.json')==task['shared_binding_contract_sha256']
assert (ROOT/'asset_binding_contract.json').read_bytes()==(args.task_root/'shared_binding_contract.json').read_bytes()
print(json.dumps({'status':'PASS','scene_core_sha256':scene['core_sha256'],'task_semantic_core_sha256':task['semantic_core_sha256'],'physical_execution_enabled':False}))
