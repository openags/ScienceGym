"""Independent exact-export adversarial checks; all mutations use temp files.

Integrity and bounded envelope checks do not authenticate the file's author.
"""
from pathlib import Path
import hashlib
import io
import json
import os
import shutil
import stat
import struct
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
import verify_export as v

FIXED_FILES = tuple('''EXPORT_SCOPE.md README.md RELEASE_BOUNDARY.json STATUS.json TASK_DESIGN.md VERIFICATION.json adversarial_cases.json agent_visible.json analysis_contracts.json asset_binding_plan.json branches.json control_packages.json coverage_matrix.json dependencies.json design_assumptions.json episode_input_contract.json evaluator_reference.json evidence_map.json lifecycle_contract.json lineage_contract.json material_cards.json mock_contract.json nonmanual_scope.json operations.json preparation_routes.json provenance.json source_access_audit.json source_conflicts.json source_outcomes.json source_parameters.json station_contracts.json transport_routes.json unknown_parameters.json tests/contract.py tests/test_contract.py tests/test_export.py tests/verify_export.py tests/verify_package.py review/INDEPENDENT_REVIEW.json review/INDEPENDENT_REVIEW.md review/test_independent_contract.py review/test_independent_export.py'''.split())


class IndependentExport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'original'
        self.root.mkdir()
        for name in FIXED_FILES:
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('Original synthetic export fixture for ' + name + '\n')
        self.seal()
        self.archive = Path(self.tmp.name) / 'bundle.zip'

    def tearDown(self):
        self.tmp.cleanup()

    def seal(self):
        manifest = {
            'schema_version': 'lockable_origami_export.v1',
            'files': [{'path': name, 'bytes': (self.root / name).stat().st_size,
                       'sha256': hashlib.sha256((self.root / name).read_bytes()).hexdigest()} for name in FIXED_FILES],
            'member_count_including_manifest': len(FIXED_FILES) + 1,
            'actor_visible_allowlist': ['agent_visible.json'],
            'all_other_files_are_evaluator_audit_only': True,
        }
        (self.root / 'EXPORT_ALLOWLIST.json').write_text(json.dumps(manifest))

    def change_manifest(self, fn):
        p = self.root / 'EXPORT_ALLOWLIST.json'
        m = json.loads(p.read_text())
        fn(m)
        p.write_text(json.dumps(m))

    def make_zip(self, method=zipfile.ZIP_DEFLATED, transform=None):
        with zipfile.ZipFile(self.archive, 'w') as z:
            for name in FIXED_FILES + ('EXPORT_ALLOWLIST.json',):
                info = zipfile.ZipInfo(name)
                info.compress_type = method
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                if transform:
                    transform(info)
                z.writestr(info, (self.root / name).read_bytes())

    def test_fixed_inventory_matches_independent_listing(self):
        self.assertEqual(set(v.EXPECTED_FILES), set(FIXED_FILES))
        self.assertEqual(len(FIXED_FILES), 42)

    def test_canonical_stored_and_deflated_archives_pass(self):
        self.assertEqual(v.verify(self.root), [])
        for method in [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED]:
            self.make_zip(method)
            self.assertEqual(v.verify(self.root, self.archive), [])

    def test_duplicate_json_manifest_key_rejected(self):
        p = self.root / 'EXPORT_ALLOWLIST.json'
        p.write_text(p.read_text()[:-1] + ',"actor_visible_allowlist":["agent_visible.json"]}')
        self.assertTrue(v.verify(self.root))

    def test_manifest_boolean_size_is_not_integer(self):
        self.change_manifest(lambda m: m['files'][0].__setitem__('bytes', True))
        self.assertTrue(v.verify(self.root))

    def test_manifest_boolean_count_is_not_integer(self):
        self.change_manifest(lambda m: m.__setitem__('member_count_including_manifest', True))
        self.assertTrue(v.verify(self.root))

    def test_manifest_extra_keys_and_widened_visibility_rejected(self):
        for mutation in [lambda m: m.__setitem__('private_payload', 'extra'),
                         lambda m: m.__setitem__('all_other_files_are_evaluator_audit_only', False),
                         lambda m: m['actor_visible_allowlist'].append('evaluator_reference.json')]:
            self.seal()
            self.change_manifest(mutation)
            self.assertTrue(v.verify(self.root))

    def test_manifest_omitted_row_and_duplicate_row_rejected(self):
        self.change_manifest(lambda m: m['files'].pop())
        self.assertTrue(v.verify(self.root))
        self.seal()
        self.change_manifest(lambda m: m['files'].append(m['files'][0]))
        self.assertTrue(v.verify(self.root))

    def test_manifest_nan_size_rejected(self):
        self.change_manifest(lambda m: m['files'][0].__setitem__('bytes', float('nan')))
        self.assertTrue(v.verify(self.root))

    def test_non_utf8_even_with_updated_hash_rejected(self):
        (self.root / 'README.md').write_bytes(b'\xff\xfe')
        self.seal()
        self.assertTrue(v.verify(self.root))

    def test_unknown_file_cannot_be_enrolled_with_valid_hash(self):
        data = b'not an approved original artifact'
        (self.root / 'unapproved.png').write_bytes(data)
        self.change_manifest(lambda m: m['files'].append({'path': 'unapproved.png', 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest()}))
        self.assertTrue(v.verify(self.root))

    def test_root_symlink_rejected(self):
        alias = Path(self.tmp.name) / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        self.assertTrue(v.verify(alias))

    def test_nested_symlink_rejected(self):
        p = self.root / 'tests' / 'contract.py'
        p.unlink()
        p.symlink_to('../README.md')
        self.assertTrue(v.verify(self.root))

    def test_nonregular_fifo_rejected_without_reading(self):
        os.mkfifo(self.root / 'unexpected-fifo')
        self.assertTrue(v.verify(self.root))

    def test_entry_symlink_and_directory_modes_rejected(self):
        for mode in [stat.S_IFLNK, stat.S_IFDIR]:
            self.make_zip(transform=lambda i: setattr(i, 'external_attr', (mode | 0o644) << 16)
                          if i.filename == 'README.md' else None)
            self.assertTrue(v.verify(self.root, self.archive))

    def test_entry_comment_rejected(self):
        self.make_zip(transform=lambda i: setattr(i, 'comment', b'unapproved metadata')
                      if i.filename == 'README.md' else None)
        self.assertTrue(v.verify(self.root, self.archive))

    def test_local_filename_mismatch_rejected(self):
        self.make_zip()
        data = bytearray(self.archive.read_bytes())
        data[30] ^= 1
        self.archive.write_bytes(data)
        self.assertTrue(v.verify(self.root, self.archive))

    def test_local_size_mismatch_rejected(self):
        self.make_zip()
        data = bytearray(self.archive.read_bytes())
        struct.pack_into('<I', data, 22, struct.unpack_from('<I', data, 22)[0] + 1)
        self.archive.write_bytes(data)
        self.assertTrue(v.verify(self.root, self.archive))

    def test_noncanonical_local_flags_rejected(self):
        self.make_zip()
        data = bytearray(self.archive.read_bytes())
        struct.pack_into('<H', data, 6, 8)
        self.archive.write_bytes(data)
        self.assertTrue(v.verify(self.root, self.archive))

    def test_archive_corruption_and_truncation_fail_closed(self):
        for data in [b'', b'PK', b'not a zip', b'PK\x05\x06' + b'\0' * 17]:
            self.archive.write_bytes(data)
            self.assertTrue(v.verify(self.root, self.archive))
        self.make_zip()
        self.archive.write_bytes(self.archive.read_bytes()[:-1])
        self.assertTrue(v.verify(self.root, self.archive))

    def test_archive_content_must_match_local_original(self):
        self.make_zip()
        (self.root / 'README.md').write_text('different but correctly rehashed local text')
        self.seal()
        self.assertEqual(v.verify(self.root), [])
        self.assertTrue(v.verify(self.root, self.archive))

    def test_prefix_and_eocd_trailer_payload_rejected(self):
        for prefix, suffix in [(b'launcher', b''), (b'', b'\0'), (b'', b'publisher payload')]:
            self.make_zip()
            self.archive.write_bytes(prefix + self.archive.read_bytes() + suffix)
            self.assertTrue(v.verify(self.root, self.archive))

    def test_unused_deflate_payload_rejected_even_with_consistent_sizes(self):
        stream = io.BytesIO()
        content = b'original synthetic text\n'
        with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('README.md', content)
        data = stream.getvalue()
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            self.assertEqual(v.envelope_errors(data, z, {'README.md': len(content)}), [])
            start_dir = z.start_dir
        extra = b'unapproved bytes inside compressed member'
        changed = bytearray(data[:start_dir] + extra + data[start_dir:])
        compressed = struct.unpack_from('<I', changed, 18)[0]
        struct.pack_into('<I', changed, 18, compressed + len(extra))
        struct.pack_into('<I', changed, start_dir + len(extra) + 20, compressed + len(extra))
        struct.pack_into('<I', changed, len(changed) - 22 + 16, start_dir + len(extra))
        with zipfile.ZipFile(io.BytesIO(changed)) as z:
            self.assertEqual(z.read('README.md'), content)
            self.assertTrue(v.envelope_errors(changed, z, {'README.md': len(content)}))

    def test_unsafe_and_noncanonical_names_rejected(self):
        for name in ['../escape', '/absolute', './same', 'a/../b', 'a//b',
                     'a\\b', 'drive:x', '.hidden', 'nested/.hidden', '', 'README.md/']:
            self.assertFalse(v.allowed_name(name), name)


if __name__ == '__main__':
    unittest.main()
