"""Read-only base checks; mutations occur only in temporary copied packages."""
import copy,hashlib,json,shutil,tempfile,unittest,zipfile,stat
from pathlib import Path
from verify_export import verify,ROOT,EXPECTED_FILES,allowed_name
class Export(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'task';shutil.copytree(ROOT,self.root);self.archive=Path(self.tmp.name)/'task.zip'
    def tearDown(self):self.tmp.cleanup()
    def make_zip(self,extra=None):
        with zipfile.ZipFile(self.archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for name in list(EXPECTED_FILES)+['EXPORT_ALLOWLIST.json']:z.write(self.root/name,name)
            if extra:extra(z)
    def test_base_package(self):self.assertEqual(verify(self.root),[])
    def test_exact_zip(self):self.make_zip();self.assertEqual(verify(self.root,self.archive),[])
    def test_unknown_source_member(self):
        (self.root/'source.pdf').write_bytes(b'originally absent');self.assertTrue(verify(self.root))
    def test_content_mutation(self):
        (self.root/'README.md').write_text('changed');self.assertTrue(verify(self.root))
    def test_symlink(self):
        (self.root/'alias').symlink_to('README.md');self.assertTrue(verify(self.root))
    def test_empty_extra_directory(self):
        (self.root/'extra').mkdir();self.assertTrue(verify(self.root))
    def test_actor_allowlist_widening(self):
        p=self.root/'EXPORT_ALLOWLIST.json';d=json.loads(p.read_text());d['actor_visible_allowlist'].append('source_outcomes.json');p.write_text(json.dumps(d));self.assertTrue(verify(self.root))
    def test_manifest_enrollment_attack(self):
        data=b'not allowed';(self.root/'source.pdf').write_bytes(data);p=self.root/'EXPORT_ALLOWLIST.json';d=json.loads(p.read_text());d['files'].append({'path':'source.pdf','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()});d['member_count_including_manifest']+=1;p.write_text(json.dumps(d));self.assertTrue(verify(self.root))
    def test_trailing_zip_payload(self):
        self.make_zip();self.archive.write_bytes(self.archive.read_bytes()+b'hidden payload');self.assertTrue(verify(self.root,self.archive))
    def test_prefix_zip_payload(self):
        self.make_zip();self.archive.write_bytes(b'prefix'+self.archive.read_bytes());self.assertTrue(verify(self.root,self.archive))
    def test_zip_comment(self):
        self.make_zip(lambda z:setattr(z,'comment',b'not allowed'));self.assertTrue(verify(self.root,self.archive))
    def test_duplicate_zip_entry(self):
        import warnings
        with warnings.catch_warnings():warnings.simplefilter('ignore');self.make_zip(lambda z:z.writestr('README.md','duplicate'))
        self.assertTrue(verify(self.root,self.archive))
    def test_zip_extra_field(self):
        self.make_zip()
        altered=Path(self.tmp.name)/'altered.zip'
        with zipfile.ZipFile(self.archive) as src,zipfile.ZipFile(altered,'w') as dst:
            for i in src.infolist():
                if i.filename=='README.md':i.extra=b'\xfe\xca\x00\x00'
                dst.writestr(i,src.read(i))
        self.assertTrue(verify(self.root,altered))
    def test_unsafe_names(self):
        for name in ['../source.pdf','/absolute','a/../b','.hidden','a\\b','a:b','a//b','']:
            self.assertFalse(allowed_name(name))
if __name__=='__main__':unittest.main()
