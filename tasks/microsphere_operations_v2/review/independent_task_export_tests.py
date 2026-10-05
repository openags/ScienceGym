#!/usr/bin/env python3
"""Independent exporter adversarial tests; all adversarial files are temporary."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
import exporter


def serialize(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


class IndependentExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='independent-microsphere-export-')
        self.base = Path(self.tmp.name)
        self.package = self.base/'sample_package'
        self.package.mkdir()
        self.names = ['README.md','EXPORT_ALLOWLIST.json','DELIVERABLE_MANIFEST.json']
        (self.package/'README.md').write_text('Original symbolic contract fixture. No scientific evidence.\n')
        self.refresh()

    def tearDown(self):
        self.tmp.cleanup()

    def refresh(self):
        (self.package/'EXPORT_ALLOWLIST.json').write_bytes(serialize({'files':self.names}))
        entries = []
        for name in self.names:
            if name == 'DELIVERABLE_MANIFEST.json':
                continue
            path = self.package/name
            if not path.is_file():
                continue
            data = path.read_bytes()
            entries.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        (self.package/'DELIVERABLE_MANIFEST.json').write_bytes(serialize({'files':entries,'publisher_material_included':False,'physical_execution':False}))

    def reject(self):
        with self.assertRaises((exporter.ExportError, ValueError)):
            exporter.inspect(self.package)

    def test_01_deterministic_archive_and_exact_bytes(self):
        a, b = self.base/'one.zip', self.base/'two.zip'
        first = exporter.build_archive(self.package, a)
        second = exporter.build_archive(self.package, b)
        self.assertEqual(first, second)
        self.assertTrue(exporter.verify_archive(a, self.package))
        self.assertEqual(a.read_bytes(), b.read_bytes())

    def test_02_unlisted_missing_and_stale_files_fail(self):
        extra = self.package/'extra.md'
        extra.write_text('unlisted')
        self.reject()
        extra.unlink()
        (self.package/'README.md').unlink()
        self.reject()
        (self.package/'README.md').write_text('changed')
        self.reject()

    def test_03_traversal_absolute_hidden_and_backslash_paths_fail(self):
        cases = ('../escape.json','/escape.json','a/../escape.json','.secret.json','a//b.json','a\\b.json')
        for name in cases:
            with self.subTest(name=name):
                (self.package/'EXPORT_ALLOWLIST.json').write_bytes(serialize({'files':self.names+[name]}))
                self.reject()

    def test_04_duplicate_allowlist_and_json_keys_fail(self):
        (self.package/'EXPORT_ALLOWLIST.json').write_bytes(serialize({'files':self.names+self.names[:1]}))
        self.reject()
        (self.package/'EXPORT_ALLOWLIST.json').write_text('{"files":[],"files":[]}')
        self.reject()

    def test_05_member_symlinks_and_symlinked_root_fail(self):
        target = self.base/'safe_original.md'
        target.write_text('temporary test target')
        (self.package/'README.md').unlink()
        (self.package/'README.md').symlink_to(target)
        self.reject()
        (self.package/'README.md').unlink()
        (self.package/'README.md').write_text('Original text')
        self.refresh()
        alias = self.base/'root_alias'
        alias.symlink_to(self.package, target_is_directory=True)
        with self.assertRaises(exporter.ExportError):
            exporter.build_archive(alias, self.base/'symlink-root.zip')

    def test_06_metadata_symlink_is_not_read_before_rejection(self):
        source = self.package/'EXPORT_ALLOWLIST.json'
        target = self.base/'policy.json'
        shutil.copyfile(source, target)
        source.unlink()
        source.symlink_to(target)
        original = Path.read_bytes
        accessed = []
        def watched(path):
            if path == source:
                accessed.append(str(path))
                raise RuntimeError('The symlink was read before validation')
            return original(path)
        with mock.patch.object(Path, 'read_bytes', watched):
            with self.assertRaises(exporter.ExportError):
                exporter.inspect(self.package)
        self.assertFalse(accessed)

    def test_07_binary_nonfinite_and_private_locator_payloads_fail(self):
        for content in (b'\x00binary', b'\xff\xfe', ('/'+'workspace'+'/private/value').encode(), ('file'+':/'+'/private/value').encode()):
            with self.subTest(content=repr(content)):
                (self.package/'README.md').write_bytes(content)
                self.refresh()
                self.reject()
        (self.package/'README.md').write_text('Original text')
        self.names.append('data.json')
        (self.package/'data.json').write_text('{"value":NaN}')
        self.refresh()
        self.reject()

    def test_08_output_inside_source_package_fails(self):
        with self.assertRaises(exporter.ExportError):
            exporter.build_archive(self.package, self.package/'output.zip')

    def test_09_archive_global_and_member_metadata_fail(self):
        good = self.base/'good.zip'
        exporter.build_archive(self.package, good)
        comment = self.base/'comment.zip'
        shutil.copyfile(good, comment)
        with zipfile.ZipFile(comment, 'a') as archive:
            archive.comment = b'unexpected hidden metadata'
        with self.assertRaises(exporter.ExportError):
            exporter.verify_archive(comment, self.package)
        for kind in ('member_comment','member_extra','symlink'):
            bad = self.base/(kind+'.zip')
            with zipfile.ZipFile(good) as source, zipfile.ZipFile(bad, 'w') as output:
                for index, item in enumerate(source.infolist()):
                    if index == 0:
                        if kind == 'member_comment':
                            item.comment = b'unexpected metadata'
                        elif kind == 'member_extra':
                            item.extra = b'\x01\x00\x00\x00'
                        else:
                            item.external_attr = (stat.S_IFLNK|0o777)<<16
                    output.writestr(item, source.read(item.filename))
            with self.subTest(kind=kind), self.assertRaises(exporter.ExportError):
                exporter.verify_archive(bad, self.package)

    def test_10_duplicate_archive_member_fails(self):
        archive = self.base/'duplicate.zip'
        exporter.build_archive(self.package, archive)
        with zipfile.ZipFile(archive, 'a') as output:
            output.writestr('sample_package/README.md', b'duplicate')
        with self.assertRaises(exporter.ExportError):
            exporter.verify_archive(archive, self.package)


if __name__ == '__main__':
    unittest.main()
