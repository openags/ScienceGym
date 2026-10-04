"""Independent exact-export and actor projection regressions.

Copies only the named original text/code package members into temporary local
review directories. No source media is accessed, copied, or embedded.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import warnings
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tests'))
import verify_export as V


class IndependentExportReview(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='actuator_export_review_')
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.root = self.parent/'package'
        self.root.mkdir()
        self.manifest = json.loads((ROOT/'EXPORT_ALLOWLIST.json').read_text())
        for name in [r['path'] for r in self.manifest['files']]+['EXPORT_ALLOWLIST.json']:
            dest = self.root/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/name,dest)
        self.assertEqual(V.verify(self.root), [])

    def save_manifest(self, manifest):
        (self.root/'EXPORT_ALLOWLIST.json').write_text(json.dumps(manifest, indent=2)+'\n')

    def make_zip(self, extras=None, omit=None, replacement=None):
        path = self.parent/'review.zip'
        names = [r['path'] for r in self.manifest['files']]+['EXPORT_ALLOWLIST.json']
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',UserWarning)
            with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
                for name in names:
                    if name == omit: continue
                    content = (self.root/name).read_bytes()
                    if replacement and replacement[0] == name: content = replacement[1]
                    z.writestr(name, content)
                for name,content in extras or []: z.writestr(name,content)
        return path

    def test_final_inventory_and_byte_hashes(self):
        self.assertEqual(V.verify(ROOT), [], 'Freeze the named review outputs before this final release test')
        names = [r['path'] for r in self.manifest['files']]
        self.assertEqual(self.manifest['member_count_including_manifest'],len(names)+1)
        self.assertEqual(len(names),len(set(names)))
        for row in self.manifest['files']:
            self.assertNotIn('*',row['path'])
            self.assertNotIn('..',Path(row['path']).parts)
            self.assertFalse(Path(row['path']).is_absolute())
            self.assertIn(Path(row['path']).suffix,{'.py','.json','.md'})
            data = (ROOT/row['path']).read_bytes()
            self.assertEqual(len(data),row['bytes'])
            self.assertEqual(hashlib.sha256(data).hexdigest(),row['sha256'])
        self.assertEqual(V.verify(self.root,self.make_zip()),[])

    def test_actor_projection_is_one_exact_safe_file(self):
        evaluator = json.loads((self.root/'evaluator_reference.json').read_text())
        actor = json.loads((self.root/'agent_visible.json').read_text())
        self.assertEqual(self.manifest['actor_visible_allowlist'], ['agent_visible.json'])
        self.assertEqual(evaluator['actor_visible_allowlist'],['agent_visible.json'])
        self.assertTrue(self.manifest['all_other_files_are_evaluator_audit_only'])
        self.assertTrue(evaluator['all_unlisted_files_are_evaluator_audit_only'])
        self.assertIn('evidence_map.json',evaluator['files'])
        self.assertFalse(actor['source_outcomes_exposed'])
        self.assertFalse(actor['can_submit_raw_observations'])
        self.assertFalse(actor['can_declare_service_qualification'])
        self.assertFalse(actor['can_declare_measurement_success'])
        m = copy.deepcopy(self.manifest)
        m['actor_visible_allowlist'].append('evidence_map.json')
        self.save_manifest(m)
        self.assertTrue(V.verify(self.root))

    def test_unlisted_file_and_missing_member(self):
        rogue = self.root/'unlisted.json'
        rogue.write_text('{}')
        self.assertTrue(V.verify(self.root))
        rogue.unlink()
        target = self.root/'README.md'
        target.unlink()
        self.assertTrue(V.verify(self.root))

    def test_byte_mutation_and_false_hash(self):
        target = self.root/'README.md'
        target.write_bytes(target.read_bytes()+b'\nAltered\n')
        self.assertTrue(V.verify(self.root))
        target.write_bytes((ROOT/'README.md').read_bytes())
        m = copy.deepcopy(self.manifest)
        m['files'][0]['sha256'] = '0'*64
        self.save_manifest(m)
        self.assertTrue(V.verify(self.root))

    def test_symlink_is_rejected(self):
        target = self.root/'README.md'
        data = target.read_bytes()
        other = self.parent/'owned_review_text.md'
        other.write_bytes(data)
        target.unlink()
        target.symlink_to(other)
        self.assertTrue(V.verify(self.root))

    def test_archive_extra_missing_duplicate_and_modified_bytes(self):
        for name in ['source/main.xml','source/figure.png','tests/__pycache__/contract.pyc','../outside.txt','/absolute.txt']:
            # Original placeholder bytes only; never actual publisher media.
            with self.subTest(extra=name):
                self.assertTrue(V.verify(self.root,self.make_zip(extras=[(name,b'authored adversarial placeholder')])) )
        self.assertTrue(V.verify(self.root,self.make_zip(omit='README.md')))
        self.assertTrue(V.verify(self.root,self.make_zip(extras=[('README.md',b'duplicate')])) )
        self.assertTrue(V.verify(self.root,self.make_zip(replacement=('README.md',b'altered'))))

    def test_allowlist_traversal_duplicate_and_malformed_rows(self):
        cases = [[], None, [{}], [{'path':'../outside.txt'}], [{'path':'/absolute.txt'}],
                 [{'path':True}], [{'path':None}], 'not a file list']
        for rows in cases:
            m = copy.deepcopy(self.manifest)
            m['files'] = rows
            self.save_manifest(m)
            with self.subTest(rows=rows):
                self.assertTrue(V.verify(self.root))
        m = copy.deepcopy(self.manifest)
        m['files'].append(copy.deepcopy(m['files'][0]))
        self.save_manifest(m)
        self.assertTrue(V.verify(self.root))


if __name__ == '__main__':
    unittest.main(verbosity=2)
