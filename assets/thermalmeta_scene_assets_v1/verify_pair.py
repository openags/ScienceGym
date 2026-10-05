"""Verify both content manifests, binding identity and reciprocal seals locally."""
import json,pathlib,hashlib,sys
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def validate(package):
 m=json.loads((package/'CONTENT_MANIFEST.json').read_text());errors=[]
 for f in m['files']:
  q=pathlib.PurePosixPath(f['path'])
  if q.is_absolute() or '..' in q.parts:errors.append('unsafe_member:'+f['path']);continue
  p=package/q
  if not p.is_file() or p.is_symlink():errors.append('missing_or_symlink:'+f['path']);continue
  if p.stat().st_size!=f['bytes'] or H(p)!=f['sha256']:errors.append('content_mismatch:'+f['path'])
 return errors
if __name__=='__main__':
 here=pathlib.Path(__file__).resolve().parent
 if len(sys.argv)!=2:raise SystemExit('Usage: python3 verify_pair.py PATH_TO_TASK_PACKAGE')
 task=pathlib.Path(sys.argv[1]);errors=validate(here)+validate(task)
 a=json.loads((here/'PAIR_SEAL.json').read_text());b=json.loads((task/'PAIR_SEAL.json').read_text())
 if a!=b:errors.append('reciprocal_seal_mismatch')
 if H(here/'CONTENT_MANIFEST.json')!=a['scene_content_manifest_sha256']:errors.append('scene_manifest_hash_mismatch')
 if H(task/'CONTENT_MANIFEST.json')!=a['task_content_manifest_sha256']:errors.append('task_manifest_hash_mismatch')
 if H(here/'scene_binding_contract.json')!=a['shared_binding_sha256'] or H(task/'scene_binding_contract.json')!=a['shared_binding_sha256']:errors.append('binding_hash_mismatch')
 print(json.dumps({'passed':not errors,'errors':errors,'physical_or_scientific_execution_validated':False},indent=2));raise SystemExit(bool(errors))
