"""Author inventory and deterministic sanitized export tests."""
from pathlib import Path
import hashlib,json,tempfile,unittest,zipfile
import verify_export as E
class AuthorExportTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.work=Path(self.temp.name);self.root=self.work/'package';self.root.mkdir()
  for name in E.ALLOWED:
   p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{}\n' if p.suffix=='.json' else 'Original synthetic fixture.\n')
  E.freeze(self.root)
 def tearDown(self):self.temp.cleanup()
 def test_exact_directory_inventory(self):self.assertTrue(E.verify_directory(self.root)['passed'])
 def test_exact_archive_inventory(self):
  archive=self.work/'release.zip';self.assertTrue(E.build_zip(self.root,archive)['passed'])
  with zipfile.ZipFile(archive) as z:self.assertEqual(set(z.namelist()),set(E.ALLOWED)|{E.MANIFEST})
 def test_archive_is_byte_deterministic(self):
  a=self.work/'a.zip';b=self.work/'b.zip';E.build_zip(self.root,a);E.build_zip(self.root,b);self.assertEqual(a.read_bytes(),b.read_bytes())
 def test_one_modified_byte_fails_hash(self):
  (self.root/'README.md').write_text('tampered')
  with self.assertRaises(E.ExportError):E.verify_directory(self.root)
 def test_additional_file_cannot_be_smuggled(self):
  (self.root/'unlisted.txt').write_text('extra')
  with self.assertRaises(E.ExportError):E.freeze(self.root)
 def test_manifest_self_membership_forbidden(self):
  m=json.loads((self.root/E.MANIFEST).read_text());m['files'][0]['path']=E.MANIFEST
  with self.assertRaises(E.ExportError):E.manifest_check(m)
 def test_nonfinite_or_duplicate_json_forbidden(self):
  for data in (b'{"x":NaN}',b'{"x":1,"x":2}'):
   with self.assertRaises(E.ExportError):E.load_bytes(data)
 def test_manifest_actor_scope_is_exact(self):
  m=json.loads((self.root/E.MANIFEST).read_text());m['actor_visible_allowlist']=['evaluator_reference.json']
  with self.assertRaises(E.ExportError):E.manifest_check(m)
if __name__=='__main__':unittest.main()
