"""Independent export probes. All archive attacks use disposable authored fixtures."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import stat
import struct
import sys
import tempfile
import unittest
import warnings
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
SPEC = importlib.util.spec_from_file_location('scattering_independent_export', ROOT / 'tests' / 'verify_export.py')
E = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(E)


class IndependentExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='scattering-independent-')
        self.work = Path(self.temp.name)
        self.root = self.work / 'package'
        self.root.mkdir()
        for name in E.ALLOWED:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{}\n' if path.suffix == '.json' else 'Original disposable review fixture.\n')
        E.freeze(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def reject(self, fn, *args):
        with self.assertRaises(E.ExportError):
            fn(*args)

    def archive(self, change=None, omit=None, comment=b''):
        destination = self.work / 'probe.zip'
        with zipfile.ZipFile(destination, 'w') as archive:
            archive.comment = comment
            for name in (*E.ALLOWED, E.MANIFEST):
                if name == omit:
                    continue
                info = zipfile.ZipInfo(name)
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                data = (self.root / name).read_bytes()
                if change:
                    info, data = change(info, data)
                archive.writestr(info, data)
        return destination

    def replace_and_reseal(self, data, name='README.md'):
        (self.root / name).write_bytes(data)
        self.reject(E.freeze, self.root)

    def test_valid_text_directory_and_actual_zip_roundtrip(self):
        self.assertTrue(E.verify_directory(self.root)['passed'])
        destination = self.work / 'valid.zip'
        self.assertTrue(E.build_zip(self.root, destination)['passed'])
        self.assertTrue(E.verify_zip(destination)['passed'])
        with zipfile.ZipFile(destination) as archive:
            self.assertEqual(sorted(archive.namelist()), sorted((*E.ALLOWED, E.MANIFEST)))
            self.assertEqual(archive.comment, b'')

    def test_json_duplicate_keys_nonfinite_and_invalid_encoding_rejected(self):
        for data in (b'{"k":1,"k":2}', b'{"k":NaN}', b'{"k":Infinity}', b'{"k":-Infinity}', b'\xff'):
            with self.subTest(data=data):
                self.reject(E.load_bytes, data)

    def test_manifest_shape_schema_and_boolean_counts_rejected(self):
        baseline = json.loads((self.root / E.MANIFEST).read_text())
        for key, value in [('member_count_including_manifest', True), ('schema_version', 'foreign'), ('extra', 1)]:
            item = copy.deepcopy(baseline)
            item[key] = value
            with self.subTest(key=key):
                self.reject(E.manifest_check, item)
        for key, value in [('bytes', True), ('bytes', 0), ('bytes', E.LIMIT + 1), ('sha256', 'A' * 64), ('extra', 1)]:
            item = copy.deepcopy(baseline)
            item['files'][0][key] = value
            with self.subTest(key=key, value=value):
                self.reject(E.manifest_check, item)

    def test_manifest_cannot_broaden_visibility_or_inventory(self):
        baseline = json.loads((self.root / E.MANIFEST).read_text())
        bad = copy.deepcopy(baseline)
        bad['actor_visible_allowlist'].append('evaluator_reference.json')
        self.reject(E.manifest_check, bad)
        bad = copy.deepcopy(baseline)
        bad['all_other_files_are_evaluator_audit_only'] = False
        self.reject(E.manifest_check, bad)
        bad = copy.deepcopy(baseline)
        bad['files'][0]['path'] = 'source.pdf'
        self.reject(E.manifest_check, bad)
        bad = copy.deepcopy(baseline)
        bad['files'].reverse()
        self.reject(E.manifest_check, bad)
        bad = copy.deepcopy(baseline)
        bad['files'][1] = copy.deepcopy(bad['files'][0])
        self.reject(E.manifest_check, bad)

    def test_paths_reject_traversal_aliases_absolute_and_backslash(self):
        paths = ('../README.md', '/README.md', './README.md', 'tests//contract.py',
                 'tests/../README.md', 'tests' + chr(92) + 'contract.py',
                 'README.md/', 'README.md' + chr(0), 'review')
        for name in paths:
            with self.subTest(name=name):
                self.reject(E.safe_path, name)

    def test_missing_extra_and_unknown_empty_directory_rejected(self):
        extra = self.root / 'source.pdf'
        extra.write_text('not exported')
        self.reject(E.freeze, self.root)
        extra.unlink()
        extra.mkdir()
        self.reject(E.freeze, self.root)
        extra.rmdir()
        (self.root / 'README.md').unlink()
        self.reject(E.freeze, self.root)
        self.reject(E.verify_directory, self.root)

    def test_directory_byte_tampering_rejected(self):
        (self.root / 'README.md').write_text('Different bytes')
        self.reject(E.verify_directory, self.root)

    def test_file_directory_root_and_ancestor_symlinks_rejected(self):
        target = self.work / 'outside.txt'
        target.write_text('outside')
        path = self.root / 'README.md'
        path.unlink()
        path.symlink_to(target)
        self.reject(E.freeze, self.root)
        path.unlink()
        path.write_text('restored fixture')
        tests = self.root / 'tests'
        shutil.rmtree(tests)
        tests.symlink_to(self.work, target_is_directory=True)
        self.reject(E.freeze, self.root)
        alias = self.work / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        self.reject(E.verify_directory, alias)
        holder = self.work / 'holder'
        holder.mkdir()
        child = holder / 'package'
        child.mkdir()
        parent_alias = self.work / 'holder-alias'
        parent_alias.symlink_to(holder, target_is_directory=True)
        self.reject(E.root_path, parent_alias / 'package')

    def test_manifest_link_cannot_overwrite_external_target(self):
        target = self.work / 'untouched.txt'
        target.write_text('untouched')
        path = self.root / E.MANIFEST
        path.unlink()
        path.symlink_to(target)
        self.reject(E.freeze, self.root)
        self.assertEqual(target.read_text(), 'untouched')

    def test_oversize_empty_nontext_and_control_content_rejected(self):
        for data in (b'x' * (E.LIMIT + 1), b'', b'\xff', b'one\x00two', b'one\x01two', b'one\x7ftwo'):
            with self.subTest(size=len(data)):
                self.replace_and_reseal(data)

    def test_media_signatures_and_bom_cannot_hide_under_text_name(self):
        for data in (b'%PDF-1.7\n', b'GIF89a', b'RIFFpayload', b'\x7fELF', b'<svg/>', b'<?xml version="1.0"?><svg/>',
                     b'0000ftypisom', bytes([239, 187, 191]) + b'%PDF-1.7\n'):
            with self.subTest(data=data):
                self.replace_and_reseal(data)

    def test_private_locations_and_encoded_json_paths_rejected(self):
        for prefix in ('workspace', 'workspaces', 'root', 'home', 'tmp', 'Users', 'Volumes', 'private'):
            self.replace_and_reseal(('/' + prefix + '/secret').encode())
        path = 'C:' + chr(92) + 'Users' + chr(92) + 'review-user' + chr(92) + 'secret.txt'
        self.replace_and_reseal(json.dumps({'path': path}).encode(), 'STATUS.json')
        data = ('{"path":"/' + 'work' + chr(92) + 'u0073pace/secret"}').encode()
        self.replace_and_reseal(data, 'STATUS.json')

    def test_local_file_and_upload_locators_rejected(self):
        for prefix in ('file', 'sediment'):
            self.replace_and_reseal((prefix + ':' + '/' + '/secret').encode())
        self.replace_and_reseal(('file' + ':' + '/secret').encode())

    def test_windows_private_path_matching_is_case_insensitive(self):
        for root in ('users', 'USERS', 'Documents and Settings'):
            path = 'c:' + chr(92) + root + chr(92) + 'review-user' + chr(92) + 'secret.txt'
            with self.subTest(root=root):
                self.replace_and_reseal(json.dumps({'path': path}).encode(), 'STATUS.json')

    def test_zip_missing_extra_duplicate_and_wrong_hash_rejected(self):
        self.reject(E.verify_zip, self.archive(omit='README.md'))
        destination = self.archive()
        with zipfile.ZipFile(destination, 'a') as archive:
            archive.writestr('source.pdf', 'unlisted')
        self.reject(E.verify_zip, destination)
        destination = self.archive()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(destination, 'a') as archive:
                archive.writestr('README.md', 'duplicate')
        self.reject(E.verify_zip, destination)
        def change(info, data):
            return info, b'changed' if info.filename == 'README.md' else data
        self.reject(E.verify_zip, self.archive(change))

    def test_zip_traversal_and_alias_names_rejected(self):
        for name in ('../README.md', '/README.md', './README.md', 'README.md/', 'tests' + chr(92) + 'contract.py'):
            def change(info, data):
                if info.filename == 'README.md':
                    info.filename = name
                return info, data
            with self.subTest(name=name):
                self.reject(E.verify_zip, self.archive(change))

    def test_zip_symlink_and_special_member_modes_rejected(self):
        for mode in (stat.S_IFLNK, stat.S_IFIFO, stat.S_IFSOCK, stat.S_IFCHR):
            def change(info, data):
                if info.filename == 'README.md':
                    info.external_attr = (mode | 0o644) << 16
                return info, data
            with self.subTest(mode=mode):
                self.reject(E.verify_zip, self.archive(change))

    def test_zip_archive_member_comments_and_extra_fields_rejected(self):
        self.reject(E.verify_zip, self.archive(comment=b'hidden payload'))
        for attribute, value in [('comment', b'hidden payload'), ('extra', b'\xfe\xca\x04\x00hide')]:
            def change(info, data):
                if info.filename == 'README.md':
                    setattr(info, attribute, value)
                return info, data
            with self.subTest(attribute=attribute):
                self.reject(E.verify_zip, self.archive(change))

    def test_zip_prepended_payload_rejected(self):
        destination = self.archive()
        destination.write_bytes(b'Unlisted prefix payload\n' + destination.read_bytes())
        self.reject(E.verify_zip, destination)

    def test_zip_trailing_payload_rejected(self):
        destination = self.archive()
        destination.write_bytes(destination.read_bytes() + b'Unlisted trailing payload\n')
        self.reject(E.verify_zip, destination)

    def test_zip_local_and_central_filename_disagreement_rejected(self):
        destination = self.archive()
        raw = bytearray(destination.read_bytes())
        self.assertEqual(raw[:4], bytes([80, 75, 3, 4]))
        name_length = struct.unpack_from('<H', raw, 26)[0]
        raw[30:30 + name_length] = b'x' * name_length
        destination.write_bytes(raw)
        self.reject(E.verify_zip, destination)

    def test_archive_destination_inside_package_or_symlink_rejected(self):
        self.reject(E.build_zip, self.root, self.root / 'output.zip')
        target = self.work / 'existing.zip'
        target.write_bytes(b'unchanged')
        alias = self.work / 'alias.zip'
        alias.symlink_to(target)
        self.reject(E.build_zip, self.root, alias)
        self.assertEqual(target.read_bytes(), b'unchanged')

    def test_nonzip_and_truncated_archive_rejected(self):
        destination = self.work / 'bad.zip'
        destination.write_text('not an archive')
        self.reject(E.verify_zip, destination)
        destination = self.archive()
        destination.write_bytes(destination.read_bytes()[:-15])
        self.reject(E.verify_zip, destination)


if __name__ == '__main__':
    unittest.main()
