import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from exporter import *

def seed(p):
    (p/'README.md').write_text('Original fixture only\n')
    (p/'EXPORT_ALLOWLIST.json').write_text(json.dumps({'files':['README.md','EXPORT_ALLOWLIST.json','DELIVERABLE_MANIFEST.json']}))
    files=[{'path':f,'bytes':len((p/f).read_bytes()),'sha256':sha((p/f).read_bytes())} for f in ['README.md','EXPORT_ALLOWLIST.json']]
    (p/'DELIVERABLE_MANIFEST.json').write_text(json.dumps({'files':files,'publisher_material_included':False,'physical_execution':False}))

class ExportTests(unittest.TestCase):
    def test_reject_names(self):
        for name in ['../bad.py','/absolute.json','a/../b.py','.secret','a\\b.py','image.pdf','a//b.py','./a.py']:
            with self.subTest(name=name):
                with self.assertRaises(ExportError):safe_name(name)
    def test_roundtrip_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'package';p.mkdir();seed(p)
            a=Path(td)/'a.zip';b=Path(td)/'b.zip';build_archive(p,a);build_archive(p,b)
            self.assertEqual(a.read_bytes(),b.read_bytes());self.assertTrue(verify_archive(a,p))
    def test_unlisted_file_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);seed(p);(p/'extra.md').write_text('extra')
            with self.assertRaises(ExportError):inspect(p)
    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);seed(p);(p/'link.md').symlink_to(p/'README.md')
            with self.assertRaises(ExportError):inspect(p)
    def test_stale_hash_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);seed(p);(p/'README.md').write_text('changed')
            with self.assertRaises(ExportError):inspect(p)
    def test_duplicate_json(self):
        with self.assertRaises(ExportError):load('{"a":1,"a":2}')
    def test_nonfinite_json(self):
        with self.assertRaises(ExportError):load('{"a":NaN}')
    def test_in_package_archive_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);seed(p)
            with self.assertRaises(ExportError):build_archive(p,p/'archive.zip')

if __name__=='__main__':unittest.main()
