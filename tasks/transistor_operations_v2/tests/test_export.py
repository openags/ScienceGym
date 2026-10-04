import hashlib,json,tempfile,unittest
from pathlib import Path
from verify_export import validate_manifest

class ExportTests(unittest.TestCase):
 def make(self):
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);r=Path(td.name);(r/'original.json').write_text('{}\n');(r/'EXPORT_ALLOWLIST.json').write_text('{}\n')
  m={'allowlist':['original.json','EXPORT_ALLOWLIST.json'],'files':{'original.json':{'sha256':hashlib.sha256((r/'original.json').read_bytes()).hexdigest(),'bytes':3}},'payload_file_count':1,'total_file_count_including_manifest':2};return r,m
 def test_clean(self):
  r,m=self.make();self.assertEqual(validate_manifest(r,m),[])
 def test_changed_bytes(self):
  r,m=self.make();(r/'original.json').write_text('[]\n');self.assertTrue(validate_manifest(r,m))
 def test_extra_source(self):
  r,m=self.make();(r/'source.pdf').write_bytes(b'fake');self.assertTrue(validate_manifest(r,m))
 def test_unlisted_file(self):
  r,m=self.make();(r/'unknown.md').write_text('extra');self.assertTrue(validate_manifest(r,m))
 def test_missing_file(self):
  r,m=self.make();(r/'original.json').unlink();self.assertTrue(validate_manifest(r,m))
 def test_symlink(self):
  r,m=self.make();(r/'original.json').unlink();(r/'original.json').symlink_to('EXPORT_ALLOWLIST.json');self.assertTrue(validate_manifest(r,m))
 def test_traversal(self):
  r,m=self.make();m['allowlist'].append('../outside.json');self.assertTrue(validate_manifest(r,m))
 def test_duplicate(self):
  r,m=self.make();m['allowlist'].append('original.json');self.assertTrue(validate_manifest(r,m))
 def test_private_source_name(self):
  r,m=self.make();(r/'source_manifest.json').write_text('{}\n');m['allowlist'].append('source_manifest.json');m['files']['source_manifest.json']={'sha256':hashlib.sha256(b'{}\n').hexdigest(),'bytes':3};m['payload_file_count']=2;m['total_file_count_including_manifest']=3;self.assertTrue(validate_manifest(r,m))
if __name__=='__main__':unittest.main()
