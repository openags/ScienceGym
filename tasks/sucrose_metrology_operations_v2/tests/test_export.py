import json,hashlib,shutil,tempfile,unittest
from pathlib import Path
from verify_export import verify
ROOT=Path(__file__).resolve().parents[1]
class Export(unittest.TestCase):
 def mutate(self,fn):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d)/'package';shutil.copytree(ROOT,r);fn(r);self.assertTrue(verify(r))
 def test_baseline(self):self.assertEqual(verify(ROOT),[])
 def test_changed_payload(self):self.mutate(lambda r:(r/'README.md').write_text('forged'))
 def test_missing_file(self):self.mutate(lambda r:(r/'agent_visible.json').unlink())
 def test_symlink(self):
  def edit(r):
   p=r/'README.md';p.unlink();p.symlink_to(r/'TASK_DESIGN.md')
  self.mutate(edit)
 def test_source_extension_self_consistent_manifest(self):
  def edit(r):
   p=r/'publisher.pdf';p.write_bytes(b'Synthetic forbidden-file test');m=json.loads((r/'EXPORT_ALLOWLIST.json').read_text());m['files'].append(p.name);m['payload_sha256'][p.name]=hashlib.sha256(p.read_bytes()).hexdigest();(r/'EXPORT_ALLOWLIST.json').write_text(json.dumps(m))
  self.mutate(edit)
 def test_actor_broadening(self):
  def edit(r):
   p=r/'EXPORT_ALLOWLIST.json';m=json.loads(p.read_text());m['actor_file_allowlist'].append('evaluator_reference.json');p.write_text(json.dumps(m))
  self.mutate(edit)
 def test_manifest_type(self):self.mutate(lambda r:(r/'EXPORT_ALLOWLIST.json').write_text('[]'))
 def test_unknown_directory(self):self.mutate(lambda r:(r/'private').mkdir())
if __name__=='__main__':unittest.main()
