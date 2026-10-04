import tempfile,shutil,json,hashlib,unittest
from pathlib import Path
from verify_export import verify
ROOT=Path(__file__).resolve().parents[1]
class ExportTests(unittest.TestCase):
 def copied(self,mutate):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d)/'package';shutil.copytree(ROOT,r);mutate(r);self.assertTrue(verify(r))
 def test_baseline(self):self.assertEqual(verify(ROOT),[])
 def test_changed_payload(self):self.copied(lambda r:(r/'README.md').write_text('changed'))
 def test_missing_file(self):self.copied(lambda r:(r/'agent_visible.json').unlink())
 def test_self_consistent_publisher_addition(self):
  def edit(r):
   (r/'publisher.pdf').write_bytes(b'Synthetic forbidden-extension test')
   p=r/'EXPORT_ALLOWLIST.json';m=json.loads(p.read_text());m['files'].append('publisher.pdf');m['payload_sha256']['publisher.pdf']=hashlib.sha256((r/'publisher.pdf').read_bytes()).hexdigest();p.write_text(json.dumps(m))
  self.copied(edit)
 def test_actor_boundary_broadening(self):
  def edit(r):
   p=r/'EXPORT_ALLOWLIST.json';m=json.loads(p.read_text());m['actor_file_allowlist'].append('evaluator_reference.json');p.write_text(json.dumps(m))
  self.copied(edit)
 def test_symlink_rejected(self):
  def edit(r):
   p=r/'README.md';p.unlink();p.symlink_to(r/'TASK_DESIGN.md')
  self.copied(edit)
if __name__=='__main__':unittest.main()
