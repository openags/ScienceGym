from pathlib import Path
import json,shutil,tempfile,unittest,zipfile
from verify_export import ROOT,verify,allowed_name
class Export(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)/'package';shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('__pycache__'))
    def test_exact_root(self):self.assertEqual(verify(self.root),[])
    def test_extra_file(self):(self.root/'source.xml').write_text('forbidden');self.assertTrue(verify(self.root))
    def test_mutated_file(self):(self.root/'README.md').write_text('changed');self.assertTrue(verify(self.root))
    def test_missing_file(self):(self.root/'README.md').unlink();self.assertTrue(verify(self.root))
    def test_symlink(self):(self.root/'linked').symlink_to(self.root/'README.md');self.assertTrue(verify(self.root))
    def test_actor_expansion(self):
        p=self.root/'EXPORT_ALLOWLIST.json';d=json.loads(p.read_text());d['actor_visible_allowlist'].append('source_outcomes.json');p.write_text(json.dumps(d));self.assertTrue(verify(self.root))
    def test_unsafe_names(self):
        for name in ('../secret','/secret','x/../secret','x//y','./x','x\\y','x:y','.secret','x/.hidden'):self.assertFalse(allowed_name(name))
    def test_archive_corruption(self):
        z=Path(self.temp.name)/'bad.zip'
        with zipfile.ZipFile(z,'w') as f:
            for p in self.root.rglob('*'):
                if p.is_file():f.writestr(p.relative_to(self.root).as_posix(),p.read_bytes())
            f.writestr('../extra',b'x')
        self.assertTrue(verify(self.root,z))
if __name__=='__main__':unittest.main()
