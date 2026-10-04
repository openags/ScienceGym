"""Independent hostile checks on temporary package/archive copies only.

The exact allowlist and hashes are integrity controls, not a source-rights proof
or a production signature. No protected source repositories are inspected.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import unittest
import warnings
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
spec = importlib.util.spec_from_file_location('independent_wetting_export', ROOT / 'tests' / 'verify_export.py')
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)


class IndependentExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / 'parent' / 'package'
        shutil.copytree(ROOT, self.root)
        E.freeze(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def rejects(self, fn, *args):
        with self.assertRaises(E.ExportError): fn(*args)

    def archive(self, name='clean.zip', mutate=None):
        target = self.base / name
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
            for path in (*E.ALLOWED, E.MANIFEST):
                info = zipfile.ZipInfo(path)
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                data = (self.root / path).read_bytes()
                if mutate:
                    replacement = mutate(info, data)
                    if replacement is None: continue
                    info, data = replacement
                z.writestr(info, data)
        return target

    def test_exact_inventory_and_actor_visibility(self):
        self.assertEqual(len(E.ALLOWED), 45)
        self.assertEqual(len(set(E.ALLOWED)), 45)
        self.assertEqual(list(E.ALLOWED), sorted(E.ALLOWED))
        self.assertEqual(E.verify_directory(self.root)['member_count'], 46)
        m = json.loads((self.root / E.MANIFEST).read_text())
        self.assertEqual(m['actor_visible_allowlist'], ['agent_visible.json'])
        self.assertIs(m['all_other_files_are_evaluator_audit_only'], True)
        self.assertNotIn('source_outcomes.json', m['actor_visible_allowlist'])
        for p in E.ALLOWED:
            self.assertIn(Path(p).suffix, ('.json', '.md', '.py', ''))

    def test_deterministic_regular_text_only_archives(self):
        a = self.base / 'a.zip'; b = self.base / 'b.zip'
        E.build_zip(self.root, a); E.build_zip(self.root, b)
        self.assertEqual(a.read_bytes(), b.read_bytes())
        self.assertTrue(E.verify_zip(a)['passed'])
        with zipfile.ZipFile(a) as z:
            self.assertEqual(z.namelist(), sorted((*E.ALLOWED, E.MANIFEST)))
            for i in z.infolist():
                self.assertEqual((i.external_attr >> 16) & 0o170000, stat.S_IFREG)
                self.assertFalse(i.is_dir())
                self.assertNotIn('\x00', z.read(i).decode('utf-8'))

    def test_unknown_source_media_and_nested_directories_rejected(self):
        for filename in ('source.xml', 'supplementary.zip', 'source_data.xlsx', 'figure.png', 'movie.mp4', 'author_solver.py', '.hidden'):
            with self.subTest(filename=filename):
                p = self.root / filename; p.write_bytes(b'not authorized')
                self.rejects(E.freeze, self.root); self.rejects(E.verify_directory, self.root); p.unlink()
        p = self.root / 'sources'; p.mkdir()
        self.rejects(E.freeze, self.root); self.rejects(E.verify_directory, self.root)

    def test_missing_changed_and_empty_payload_rejected(self):
        p = self.root / 'README.md'; original = p.read_bytes()
        p.unlink(); self.rejects(E.verify_directory, self.root)
        p.write_bytes(original + b'\nmutation'); self.rejects(E.verify_directory, self.root)
        p.write_bytes(b''); self.rejects(E.freeze, self.root)

    def test_payload_limits_encoding_nul_and_private_paths_even_rehashed(self):
        p = self.root / 'README.md'
        for data in (b'\xff\xfe', b'a\x00b', b'x' * (E.LIMIT + 1), ('/' + 'workspace/private').encode(), ('/' + 'root/private').encode(), ('sediment' + '://' + 'file_private').encode()):
            with self.subTest(length=len(data)):
                p.write_bytes(data); self.rejects(E.freeze, self.root)

    def test_exact_manifest_fields_hash_format_and_sorted_members(self):
        m = json.loads((self.root / E.MANIFEST).read_text())
        variants = []
        x = copy.deepcopy(m); x['member_count_including_manifest'] = True; variants.append(x)
        x = copy.deepcopy(m); x['member_count_including_manifest'] -= 1; variants.append(x)
        x = copy.deepcopy(m); x['actor_visible_allowlist'] += ['source_outcomes.json']; variants.append(x)
        x = copy.deepcopy(m); x['all_other_files_are_evaluator_audit_only'] = False; variants.append(x)
        x = copy.deepcopy(m); x['source_files_allowed'] = True; variants.append(x)
        x = copy.deepcopy(m); x['files'].reverse(); variants.append(x)
        x = copy.deepcopy(m); x['files'][0]['bytes'] = True; variants.append(x)
        x = copy.deepcopy(m); x['files'][0]['bytes'] = E.LIMIT + 1; variants.append(x)
        x = copy.deepcopy(m); x['files'][0]['sha256'] = 'A' * 64; variants.append(x)
        x = copy.deepcopy(m); x['files'][0]['extra'] = 'source'; variants.append(x)
        x = copy.deepcopy(m); x['files'][0]['path'] = x['files'][1]['path']; variants.append(x)
        for index, x in enumerate(variants):
            with self.subTest(index=index): self.rejects(E.manifest_check, x)
        for data in (b'{"files":[],"files":[]}', b'{"x":NaN}', b'{"x":Infinity}', b'\xff', b'not json'):
            self.rejects(E.load_bytes, data)

    def test_paths_cannot_alias_allowlisted_names(self):
        for path in ('/README.md', '../README.md', './README.md', 'tests/../README.md', 'tests//contract.py', 'tests\\contract.py', 'README.md/', 'README.md\x00.xml', 'Tests/contract.py', 'README.MD'):
            with self.subTest(path=path): self.rejects(E.safe_path, path)

    def test_symlink_member_directory_root_and_manifest_rejected(self):
        p = self.root / 'README.md'; p.unlink(); p.symlink_to(ROOT / 'README.md')
        self.rejects(E.freeze, self.root); self.rejects(E.verify_directory, self.root)
        p.unlink(); p.write_bytes((ROOT / 'README.md').read_bytes())
        linked = self.base / 'linked_package'; linked.symlink_to(self.root, target_is_directory=True)
        self.rejects(E.freeze, linked); self.rejects(E.verify_directory, linked)
        p = self.root / E.MANIFEST; p.unlink(); p.symlink_to(self.base / 'missing_manifest')
        self.rejects(E.freeze, self.root); self.rejects(E.verify_directory, self.root)

    def test_symlink_ancestor_alias_rejected(self):
        alias = self.base / 'parent_alias'; alias.symlink_to(self.root.parent, target_is_directory=True)
        through_alias = alias / self.root.name
        self.rejects(E.freeze, through_alias)
        self.rejects(E.verify_directory, through_alias)
        self.rejects(E.build_zip, through_alias, self.base / 'alias.zip')

    def test_archive_output_cannot_overwrite_package_or_follow_link(self):
        self.rejects(E.build_zip, self.root, self.root / 'README.md')
        self.rejects(E.build_zip, self.root, self.root / 'archive.zip')
        target = self.base / 'linked.zip'; target.symlink_to(self.base / 'target.zip')
        self.rejects(E.build_zip, self.root, target)
        directory = self.base / 'output'; directory.mkdir()
        alias = self.base / 'output_alias'; alias.symlink_to(directory, target_is_directory=True)
        self.rejects(E.build_zip, self.root, alias / 'archive.zip')

    def test_archive_duplicate_and_extra_members_rejected(self):
        for member in ('README.md', 'source.xml', '../escape', '/absolute', 'tests/../README.md', 'tests\\contract.py', 'tests/'):
            p = self.archive('mutant.zip')
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                with zipfile.ZipFile(p, 'a') as z: z.writestr(member, 'unapproved')
            with self.subTest(member=member): self.rejects(E.verify_zip, p)

    def test_archive_missing_hash_mismatch_and_special_modes_rejected(self):
        p = self.archive('missing.zip', lambda i, d: None if i.filename == 'README.md' else (i, d))
        self.rejects(E.verify_zip, p)
        p = self.archive('mismatch.zip', lambda i, d: (i, b'mutated') if i.filename == 'README.md' else (i, d))
        self.rejects(E.verify_zip, p)
        for mode in (stat.S_IFLNK, stat.S_IFDIR, stat.S_IFIFO, stat.S_IFSOCK, stat.S_IFCHR):
            def special(i, data):
                if i.filename == 'README.md': i.external_attr = (mode | 0o644) << 16
                return i, data
            p = self.archive('special.zip', special)
            with self.subTest(mode=mode): self.rejects(E.verify_zip, p)

    def test_archive_rehashed_private_or_binary_member_still_rejected(self):
        for body in (('/' + 'workspace/secret').encode(), b'\xff', b'\x00'):
            manifest = json.loads((self.root / E.MANIFEST).read_text())
            entry = next(e for e in manifest['files'] if e['path'] == 'README.md')
            entry['bytes'] = len(body); entry['sha256'] = hashlib.sha256(body).hexdigest()
            def mutate(info, data):
                if info.filename == 'README.md': data = body
                if info.filename == E.MANIFEST: data = json.dumps(manifest).encode()
                return info, data
            p = self.archive('rehashed.zip', mutate)
            self.rejects(E.verify_zip, p)

    def test_truncated_nonzip_and_forged_manifest_rejected(self):
        p = self.archive()
        p.write_bytes(p.read_bytes()[:100]); self.rejects(E.verify_zip, p)
        p.write_text('not an archive'); self.rejects(E.verify_zip, p)
        p = self.archive('bad_manifest.zip', lambda i, d: (i, b'{"files":[],"files":[]}') if i.filename == E.MANIFEST else (i, d))
        self.rejects(E.verify_zip, p)


if __name__ == '__main__':
    unittest.main(verbosity=2)
