import json
from pathlib import Path
import tempfile
import unittest
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from exporter import ExportError,export_package,sha

class ExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name);self.p=self.base/'payload';self.p.mkdir();(self.p/'README.md').write_text('Original fixture contract, no source material.\n');self.seal()
    def seal(self):
        files=sorted([x.relative_to(self.p).as_posix() for x in self.p.rglob('*') if x.is_file() and x.name not in {'EXPORT_ALLOWLIST.json','DELIVERABLE_MANIFEST.json'}]+['EXPORT_ALLOWLIST.json','DELIVERABLE_MANIFEST.json']);(self.p/'EXPORT_ALLOWLIST.json').write_text(json.dumps({'schema':'sciencegym.export_allowlist.v1','files':files,'excluded_classes':['source media']}));rows=[]
        for f in files:
            if f=='DELIVERABLE_MANIFEST.json':continue
            b=(self.p/f).read_bytes();rows.append({'path':f,'bytes':len(b),'sha256':sha(b)})
        b=json.dumps({'schema':'sciencegym.deliverable_manifest.v1','files':rows,'total_bytes':sum(x['bytes'] for x in rows),'original_only':True}).encode();(self.p/'DELIVERABLE_MANIFEST.json').write_bytes(b);self.pin=sha(b)
    def runexport(self,name='out.zip'):return export_package(self.p,self.base/name,self.pin)
    def test_deterministic(self):self.assertEqual(self.runexport(),self.runexport('another.zip'))
    def test_manifest_pin(self):
        with self.assertRaises(ExportError):export_package(self.p,self.base/'out.zip','0'*64)
    def test_modified_bytes(self):
        (self.p/'README.md').write_text('different')
        with self.assertRaises(ExportError):self.runexport()
    def test_undeclared_source_movie(self):
        (self.p/'source.mov').write_bytes(b'source')
        with self.assertRaises(ExportError):self.runexport()
    def test_allowlisted_movie(self):
        (self.p/'source.mov').write_bytes(b'source');self.seal()
        with self.assertRaises(ExportError):self.runexport()
    def test_symlink(self):
        (self.p/'link.md').symlink_to(self.p/'README.md')
        with self.assertRaises(ExportError):self.runexport()
    def test_local_path(self):
        (self.p/'README.md').write_text('Located at '+('/'+'workspace'+'/private/source'));self.seal()
        with self.assertRaises(ExportError):self.runexport()
    def test_null_bytes(self):
        (self.p/'README.md').write_bytes(b'abc\0data');self.seal()
        with self.assertRaises(ExportError):self.runexport()
    def test_hidden_file(self):
        (self.p/'.secret').write_text('private');self.seal()
        with self.assertRaises(ExportError):self.runexport()
    def test_archive_inside_payload(self):
        with self.assertRaises(ExportError):export_package(self.p,self.p/'output.zip',self.pin)
    def test_duplicate_json_keys(self):
        (self.p/'extra.json').write_text('{"a":1,"a":2}');self.seal()
        with self.assertRaises(ExportError):self.runexport()
    def test_duplicate_manifest_row(self):
        m=json.loads((self.p/'DELIVERABLE_MANIFEST.json').read_text());m['files'].append(m['files'][0]);b=json.dumps(m).encode();(self.p/'DELIVERABLE_MANIFEST.json').write_bytes(b);self.pin=sha(b)
        with self.assertRaises(ExportError):self.runexport()

if __name__=='__main__':unittest.main()
