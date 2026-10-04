"""Author exact-inventory and hostile export checks."""
from pathlib import Path
import tempfile,shutil,json,unittest,zipfile,stat
import verify_export as e
class ExportTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'package';shutil.copytree(e.ROOT,self.root)
 def tearDown(self):self.tmp.cleanup()
 def test_current_directory(self):self.assertTrue(e.verify_directory(self.root)['passed'])
 def test_zip_roundtrip(self):self.assertTrue(e.build_zip(self.root,Path(self.tmp.name)/'out.zip')['passed'])
 def test_extra_file(self):
  (self.root/'injected.txt').write_text('not allowed')
  with self.assertRaises(e.ExportError):e.verify_directory(self.root)
 def test_missing_file(self):
  (self.root/'README.md').unlink()
  with self.assertRaises(e.ExportError):e.verify_directory(self.root)
 def test_modified_content(self):
  (self.root/'README.md').write_text('modified')
  with self.assertRaises(e.ExportError):e.verify_directory(self.root)
 def test_symlink(self):
  p=self.root/'README.md';p.unlink();p.symlink_to('TASK_DESIGN.md')
  with self.assertRaises(e.ExportError):e.verify_directory(self.root)
 def test_manifest_duplicate_key(self):
  (self.root/e.MANIFEST).write_text('{"files":[],"files":[]}')
  with self.assertRaises(e.ExportError):e.verify_directory(self.root)
 def test_manifest_allowlist_expansion(self):
  p=self.root/e.MANIFEST;m=json.loads(p.read_text());m['files'].append({'path':'evil.py','bytes':1,'sha256':'0'*64});p.write_text(json.dumps(m))
  with self.assertRaises(e.ExportError):e.verify_directory(self.root)
 def test_zip_duplicate(self):
  p=Path(self.tmp.name)/'x.zip';e.build_zip(self.root,p)
  with zipfile.ZipFile(p,'a') as z:z.writestr('README.md','bad')
  with self.assertRaises(e.ExportError):e.verify_zip(p)
 def test_zip_traversal(self):
  p=Path(self.tmp.name)/'x.zip';e.build_zip(self.root,p)
  with zipfile.ZipFile(p,'a') as z:z.writestr('../outside','bad')
  with self.assertRaises(e.ExportError):e.verify_zip(p)
 def test_no_archive_inside_package(self):
  with self.assertRaises(e.ExportError):e.build_zip(self.root,self.root/'out.zip')
 def test_bad_paths(self):
  for p in ('../README.md','/README.md','tests//contract.py','tests/./contract.py','tests/../README.md','tests\\contract.py',''):
   with self.subTest(path=p),self.assertRaises(e.ExportError):e.safe_path(p)
if __name__=='__main__':unittest.main()
