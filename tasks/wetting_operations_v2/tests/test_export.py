"""Hostile export tests on temporary copies, never on source files."""
import unittest,tempfile,shutil,zipfile,json,stat,hashlib
from pathlib import Path
import verify_export as e
class ExportTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)/'package';shutil.copytree(e.ROOT,self.root)
 def tearDown(self):self.temp.cleanup()
 def rejects(self,fn,*args):
  with self.assertRaises(e.ExportError):fn(*args)
 def test_directory_exact(self):self.assertTrue(e.verify_directory()['passed'])
 def test_build_and_check_zip(self):z=Path(self.temp.name)/'out.zip';e.build_zip(self.root,z);self.assertTrue(e.verify_zip(z)['passed'])
 def test_unlisted_source_media(self):(self.root/'source.pdf').write_bytes(b'fake');self.rejects(e.freeze,self.root)
 def test_missing_file(self):(self.root/'README.md').unlink();self.rejects(e.verify_directory,self.root)
 def test_changed_hash(self):(self.root/'README.md').write_text('changed');self.rejects(e.verify_directory,self.root)
 def test_manifest_duplicate_key(self):self.rejects(e.load_bytes,b'{"files":[],"files":[]}')
 def test_manifest_nonfinite(self):self.rejects(e.load_bytes,b'{"x":NaN}')
 def test_manifest_actor_exposure(self):
  m=json.loads((self.root/e.MANIFEST).read_text());m['actor_visible_allowlist'].append('source_outcomes.json');self.rejects(e.manifest_check,m)
 def test_manifest_extra_field(self):m=json.loads((self.root/e.MANIFEST).read_text());m['extra']=1;self.rejects(e.manifest_check,m)
 def test_traversal(self):
  for p in ('../README.md','/README.md','tests/../README.md','tests//contract.py','tests\\contract.py','./README.md'):self.rejects(e.safe_path,p)
 def test_symlink_file(self):(self.root/'README.md').unlink();(self.root/'README.md').symlink_to(e.ROOT/'README.md');self.rejects(e.verify_directory,self.root)
 def test_symlink_dir(self):shutil.rmtree(self.root/'tests');(self.root/'tests').symlink_to(e.ROOT/'tests',target_is_directory=True);self.rejects(e.verify_directory,self.root)
 def test_unknown_directory(self):(self.root/'empty').mkdir();self.rejects(e.freeze,self.root)
 def test_private_path_even_rehashed(self):(self.root/'README.md').write_text('/'+'workspace/private');self.rejects(e.freeze,self.root)
 def test_binary_even_rehashed(self):(self.root/'README.md').write_bytes(b'\xff');self.rejects(e.freeze,self.root)
 def test_nul_even_rehashed(self):(self.root/'README.md').write_text('bad\x00content');self.rejects(e.freeze,self.root)
 def test_zip_duplicate(self):
  z=Path(self.temp.name)/'out.zip';e.build_zip(self.root,z)
  with zipfile.ZipFile(z,'a') as f:f.writestr('README.md','duplicate')
  self.rejects(e.verify_zip,z)
 def test_zip_extra(self):
  z=Path(self.temp.name)/'out.zip';e.build_zip(self.root,z)
  with zipfile.ZipFile(z,'a') as f:f.writestr('extra.json','{}')
  self.rejects(e.verify_zip,z)
 def test_zip_wrong_hash(self):
  z=Path(self.temp.name)/'out.zip'
  with zipfile.ZipFile(z,'w') as f:
   for name in (*e.ALLOWED,e.MANIFEST):f.writestr(name,b'changed' if name=='README.md' else (self.root/name).read_bytes())
  self.rejects(e.verify_zip,z)
 def test_zip_symlink_mode(self):
  z=Path(self.temp.name)/'out.zip'
  with zipfile.ZipFile(z,'w') as f:
   for name in (*e.ALLOWED,e.MANIFEST):
    info=zipfile.ZipInfo(name);info.external_attr=((stat.S_IFLNK if name=='README.md' else stat.S_IFREG)|0o644)<<16;f.writestr(info,(self.root/name).read_bytes())
  self.rejects(e.verify_zip,z)
 def test_archive_inside_package(self):self.rejects(e.build_zip,self.root,self.root/'out.zip')
 def test_zip_nonzip(self):z=Path(self.temp.name)/'out.zip';z.write_text('not zip');self.rejects(e.verify_zip,z)
if __name__=='__main__':unittest.main()
