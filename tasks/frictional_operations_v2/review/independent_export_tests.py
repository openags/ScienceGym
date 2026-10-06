"""Independent export-negative tests with only original disposable byte fixtures."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from exporter import ExportError, export_package, sha, snapshot


class IndependentExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'payload'
        self.root.mkdir()
        (self.root / 'README.md').write_text('Original adversarial test fixture.\n', encoding='utf-8')
        self.seal()

    def seal(self):
        files = sorted([p.relative_to(self.root).as_posix() for p in self.root.rglob('*')
                        if p.is_file() and p.name not in {'EXPORT_ALLOWLIST.json', 'DELIVERABLE_MANIFEST.json'}]
                       + ['EXPORT_ALLOWLIST.json', 'DELIVERABLE_MANIFEST.json'])
        allow = {'schema': 'sciencegym.export_allowlist.v1', 'files': files,
                 'excluded_classes': ['publisher media', 'private data']}
        (self.root / 'EXPORT_ALLOWLIST.json').write_text(json.dumps(allow), encoding='utf-8')
        rows = []
        for name in files:
            if name == 'DELIVERABLE_MANIFEST.json':
                continue
            data = (self.root / name).read_bytes()
            rows.append({'path': name, 'bytes': len(data), 'sha256': sha(data)})
        manifest = {'schema': 'sciencegym.deliverable_manifest.v1', 'files': rows,
                    'total_bytes': sum(row['bytes'] for row in rows), 'original_only': True}
        self.write_manifest(manifest)

    def write_manifest(self, obj):
        data = json.dumps(obj).encode('utf-8')
        (self.root / 'DELIVERABLE_MANIFEST.json').write_bytes(data)
        self.pin = sha(data)

    def export(self, name='release.zip'):
        return export_package(self.root, self.base / name, self.pin)

    def test_zip_members_modes_times_and_bytes_are_deterministic(self):
        one = self.export('one.zip')
        two = self.export('two.zip')
        self.assertEqual(one, two)
        with zipfile.ZipFile(self.base / 'one.zip') as archive:
            self.assertEqual(archive.namelist(), sorted(archive.namelist()))
            for info in archive.infolist():
                self.assertEqual(info.date_time, (2026, 10, 5, 0, 0, 0))
                self.assertEqual(info.external_attr >> 16, 0o100644)
                self.assertEqual(info.compress_type, zipfile.ZIP_STORED)
                self.assertEqual(archive.read(info.filename), (self.root / info.filename).read_bytes())

    def test_no_unpinned_reseal(self):
        old = self.pin
        (self.root / 'README.md').write_text('Changed fixture.\n')
        self.seal()
        with self.assertRaises(ExportError):
            export_package(self.root, self.base / 'out.zip', old)

    def test_manifest_total_boolean_is_not_an_integer(self):
        manifest = json.loads((self.root / 'DELIVERABLE_MANIFEST.json').read_text())
        manifest['total_bytes'] = True
        self.write_manifest(manifest)
        with self.assertRaises(ExportError):
            self.export()

    def test_manifest_size_boolean_is_not_an_integer(self):
        manifest = json.loads((self.root / 'DELIVERABLE_MANIFEST.json').read_text())
        manifest['files'][0]['bytes'] = True
        self.write_manifest(manifest)
        with self.assertRaises(ExportError):
            self.export()

    def test_source_media_and_archive_extensions_stay_excluded(self):
        for suffix in ('.pdf', '.mov', '.png', '.jpg', '.glb', '.blend', '.zip', '.bin'):
            with self.subTest(suffix=suffix):
                extra = self.root / ('original_fixture' + suffix)
                extra.write_text('Harmless original fixture, intentionally wrong type.')
                self.seal()
                with self.assertRaises(ExportError):
                    self.export()
                extra.unlink()

    def test_local_paths_and_authentication_sentinels_reject(self):
        values = ['/'.join(['', folder, 'private', 'record']) for folder in ('workspace', 'tmp', 'home', 'root')]
        values += ['file' + '://' + 'local-record', 'sediment' + '://' + 'file_fixture',
                   'Bearer ' + 'a' * 24]
        for value in values:
            with self.subTest(kind=value.split(':')[0]):
                (self.root / 'README.md').write_text(value)
                self.seal()
                with self.assertRaises(ExportError):
                    self.export()

    def test_nested_undeclared_file_rejects(self):
        (self.root / 'subdir').mkdir()
        (self.root / 'subdir' / 'cache.md').write_text('fixture')
        with self.assertRaises(ExportError):
            self.export()

    def test_directory_symlink_rejects(self):
        outside = self.base / 'elsewhere'
        outside.mkdir()
        (outside / 'file.md').write_text('fixture')
        (self.root / 'linked').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ExportError):
            self.export()

    def test_root_symlink_rejects(self):
        alias = self.base / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ExportError):
            export_package(alias, self.base / 'out.zip', self.pin)

    def test_destination_symlink_rejects_without_overwrite(self):
        target = self.base / 'target.bin'
        target.write_bytes(b'unchanged')
        destination = self.base / 'link.zip'
        destination.symlink_to(target)
        with self.assertRaises(ExportError):
            export_package(self.root, destination, self.pin)
        self.assertEqual(target.read_bytes(), b'unchanged')

    def test_invalid_utf8_rejects(self):
        (self.root / 'README.md').write_bytes(b'\xff\xfe\xfd')
        self.seal()
        with self.assertRaises(ExportError):
            self.export()

    def test_hidden_nested_file_rejects_even_with_pin(self):
        (self.root / '.hidden').mkdir()
        (self.root / '.hidden' / 'content.md').write_text('fixture')
        self.seal()
        with self.assertRaises(ExportError):
            self.export()

    def test_control_file_mutation_without_manifest_update_rejects(self):
        allow = json.loads((self.root / 'EXPORT_ALLOWLIST.json').read_text())
        allow['excluded_classes'] = []
        (self.root / 'EXPORT_ALLOWLIST.json').write_text(json.dumps(allow))
        with self.assertRaises(ExportError):
            self.export()

    def test_nonfinite_json_is_not_portable_canonical_data(self):
        for value in ('NaN', 'Infinity', '-Infinity', '1e9999'):
            with self.subTest(value=value):
                (self.root / 'extra.json').write_text('{"value":' + value + '}')
                self.seal()
                with self.assertRaises(ExportError):
                    self.export()

    def test_malformed_manifest_records_raise_export_error(self):
        baseline = json.loads((self.root / 'DELIVERABLE_MANIFEST.json').read_text())
        for value in (None, [], 'wrong', 1):
            with self.subTest(value=value):
                manifest = dict(baseline)
                manifest['files'] = [value]
                self.write_manifest(manifest)
                with self.assertRaises(ExportError):
                    self.export()

    def test_malformed_allowlist_members_raise_export_error(self):
        for value in (None, [], {}, 1):
            with self.subTest(value=value):
                allow = {'schema': 'sciencegym.export_allowlist.v1',
                         'files': ['DELIVERABLE_MANIFEST.json', 'EXPORT_ALLOWLIST.json', value],
                         'excluded_classes': []}
                (self.root / 'EXPORT_ALLOWLIST.json').write_text(json.dumps(allow))
                with self.assertRaises(ExportError):
                    self.export()


if __name__ == '__main__':
    unittest.main()
