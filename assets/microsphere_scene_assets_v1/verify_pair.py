"""Verify reciprocal immutable task/scene cores using real files. SPDX-License-Identifier: Apache-2.0"""
from pathlib import Path
import hashlib,json,sys
P=Path(__file__).resolve().parent
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate(root,manifest):
 m=json.loads(manifest.read_text());files=m['files'];assert files==sorted(files,key=lambda x:x['path'])
 assert len({x['path'] for x in files})==len(files)
 for x in files:
  f=(root/x['path']).resolve();assert f.is_relative_to(root.resolve()) and f.is_file()
  assert f.stat().st_size==x['bytes'] and sha(f)==x['sha256'],x['path']
 assert hashlib.sha256(canonical(files)).hexdigest()==m['core_sha256'];return m

def verify(task_root):
 T=Path(task_root);s=validate(P,P/'scene_core_manifest.json');t=validate(T,T/'task_core_manifest.json');r=json.loads((P/'paired_task_reference.json').read_text())
 assert r['scene_core_sha256']==s['core_sha256'] and r['task_core_sha256']==t['core_sha256']
 assert json.loads((P/'paired_task_core_manifest.json').read_text())==t
 assert (P/'shared_binding_contract.json').read_bytes()==(T/'shared_binding_contract.json').read_bytes()
 b=json.loads((T/'asset_binding_plan.json').read_text())
 assert b.get('scene_core_sha256',b.get('asset_core_sha256'))==s['core_sha256']
 assert b.get('task_core_sha256')==t['core_sha256']
 return {'passed':True,'task_core_sha256':t['core_sha256'],'scene_core_sha256':s['core_sha256'],'task_files_verified':len(t['files']),'scene_files_verified':len(s['files']),'contract_byte_identical':True,'reciprocal_pins_match':True}
if __name__=='__main__':print(json.dumps(verify(sys.argv[1]),indent=2))
