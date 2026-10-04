import json,shutil,tempfile,unittest,zipfile
from pathlib import Path
from verify_export import ROOT,verify,allowed_name

class ExportTests(unittest.TestCase):
    def test_current_exact_package(self):self.assertEqual(verify(),[])
    def test_rejects_path_traversal(self):
        for path in [None,False,[],{},'../source.xml','/source.xml','a/../b','a//b','a\\b','.secret','x/.secret']:
            self.assertFalse(allowed_name(path),path)
    def test_missing_added_and_changed_file(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td)/'package';shutil.copytree(ROOT,r,ignore=shutil.ignore_patterns('__pycache__'))
            p=r/'README.md';old=p.read_bytes();p.write_bytes(old+b'changed');self.assertTrue(verify(r));p.write_bytes(old)
            q=r/'unexpected.xml';q.write_text('private source');self.assertTrue(verify(r));q.unlink()
            p.unlink();self.assertTrue(verify(r))
    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td)/'package';shutil.copytree(ROOT,r,ignore=shutil.ignore_patterns('__pycache__'));p=r/'README.md';p.unlink();p.symlink_to(r/'TASK_DESIGN.md');self.assertTrue(verify(r))
    def test_malformed_manifest_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td)
            for value in [[],None,{'files':[None]},{'files':[{'path':[],'bytes':1,'sha256':'x'}]}]:
                (r/'EXPORT_ALLOWLIST.json').write_text(json.dumps(value));self.assertTrue(verify(r))
    def test_actor_projection_not_export_inventory(self):
        d=json.loads((ROOT/'evaluator_reference.json').read_text());self.assertEqual(d['actor_visible_allowlist'],['agent_visible.json']);self.assertTrue(d['all_unlisted_files_are_evaluator_audit_only']);self.assertIn('evidence_map.json',d['files'])
if __name__=='__main__':unittest.main()
