from pathlib import Path
import hashlib,json,shutil,tempfile,unittest
from verify_export import ROOT,verify
class ExportTests(unittest.TestCase):
 def clone(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);p=Path(t.name)/'packet';shutil.copytree(ROOT,p);return p
 def test_exact_export(self):self.assertTrue(verify()['passed'],verify())
 def test_extra_missing_changed(self):
  for mode in ['extra','missing','changed']:
   p=self.clone()
   if mode=='extra':(p/'private_source.pdf').write_bytes(b'not real source')
   if mode=='missing':(p/'README.md').unlink()
   if mode=='changed':(p/'README.md').write_text('Changed')
   self.assertFalse(verify(p)['passed'])
 def test_path_manifest_and_actor_mutations(self):
  for mode in ['absolute','traversal','wildcard','duplicate','unhashed','actor']:
   p=self.clone();m=json.loads((p/'EXPORT_ALLOWLIST.json').read_text())
   if mode=='absolute':m['files'].append('/tmp/escaped')
   if mode=='traversal':m['files'].append('../escaped')
   if mode=='wildcard':m['files'].append('tests/*')
   if mode=='duplicate':m['files'].append(m['files'][0])
   if mode=='unhashed':m['payload_sha256'].pop(next(iter(m['payload_sha256'])))
   if mode=='actor':m['actor_file_allowlist'].append('source_outcomes.json')
   (p/'EXPORT_ALLOWLIST.json').write_text(json.dumps(m));self.assertFalse(verify(p)['passed'])
 def test_self_consistent_publisher_augmentation(self):
  p=self.clone();(p/'publisher.pdf').write_bytes(b'fake publisher fixture');m=json.loads((p/'EXPORT_ALLOWLIST.json').read_text());m['files'].append('publisher.pdf');m['payload_sha256']['publisher.pdf']=hashlib.sha256((p/'publisher.pdf').read_bytes()).hexdigest();(p/'EXPORT_ALLOWLIST.json').write_text(json.dumps(m));self.assertFalse(verify(p)['passed'])
 def test_symlink(self):
  p=self.clone();(p/'README.md').unlink();(p/'README.md').symlink_to(ROOT/'README.md');self.assertFalse(verify(p)['passed'])
if __name__=='__main__':unittest.main()
