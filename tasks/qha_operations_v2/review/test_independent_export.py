"""Independent archive attacks, using tiny original in-memory test content only.
All temporary files are below review/ and deleted when their test ends.
"""
import hashlib
import json
from pathlib import Path
import stat
import sys
import tempfile
import unittest
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from verify_export import validate_archive, validate_directory, safe_path


def make_archive(folder, *, body=b'Original synthetic review fixture.\n', name='README.md',
                 extra=None, manifest_mutation=None, manifest_only=False, symlink=False):
    manifest = {
        'schema_version': 'sciencegym.qha.export.v1',
        'files': [{'path': name, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}],
        'member_count_including_manifest': 2,
        'actor_visible_allowlist': ['agent_visible.json'],
        'all_other_files_are_evaluator_audit_only': True,
    }
    if manifest_mutation: manifest_mutation(manifest)
    p = Path(folder) / 'original_test.zip'
    with zipfile.ZipFile(p, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('qha_operations_v2/EXPORT_ALLOWLIST.json', json.dumps(manifest))
        if not manifest_only:
            if symlink:
                info = zipfile.ZipInfo('qha_operations_v2/' + name)
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                z.writestr(info, body)
            else: z.writestr('qha_operations_v2/' + name, body)
        if extra: z.writestr(*extra)
    return p

class IndependentExport(unittest.TestCase):
    def directory(self): return tempfile.TemporaryDirectory(prefix='review-export-', dir=ROOT / 'review')

    def test_positive_tiny_original_archive(self):
        with self.directory() as d:
            result = validate_archive(make_archive(d))
            self.assertEqual(result['status'], 'PASS')
            self.assertEqual(result['members'], 2)

    def test_traversal_absolute_backslash_and_normalization_rejected(self):
        for p in ('../README.md', '/README.md', 'a/../README.md', 'a\\README.md', 'a//README.md', './README.md', 'x/./README.md'):
            with self.subTest(path=p), self.assertRaises(ValueError): safe_path(p)

    def test_unknown_extra_file_rejected(self):
        with self.directory() as d, self.assertRaises(ValueError):
            validate_archive(make_archive(d, extra=('qha_operations_v2/not_allowlisted.md', b'Extra')))

    def test_missing_allowlisted_file_rejected(self):
        with self.directory() as d, self.assertRaises(ValueError): validate_archive(make_archive(d, manifest_only=True))

    def test_duplicate_member_rejected(self):
        with self.directory() as d:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                p = make_archive(d, extra=('qha_operations_v2/README.md', b'duplicate'))
            with self.assertRaises(ValueError): validate_archive(p)

    def test_tampered_bytes_and_count_rejected(self):
        mutations = [lambda m: m['files'][0].update(sha256='0' * 64),
                     lambda m: m['files'][0].update(bytes=0),
                     lambda m: m.update(member_count_including_manifest=10)]
        for mutate in mutations:
            with self.directory() as d, self.assertRaises(ValueError):
                validate_archive(make_archive(d, manifest_mutation=mutate))

    def test_binary_original_disguises_rejected(self):
        for magic in (b'%PDF-1.7', b'\x89PNG\r\n\x1a\n', b'\xff\xd8\xff', b'PK\x03\x04', b'glTF', b'BLENDER'):
            with self.subTest(magic=magic), self.directory() as d, self.assertRaises(ValueError):
                validate_archive(make_archive(d, body=magic + b' original synthetic test bytes'))

    def test_forbidden_member_types_rejected(self):
        for name in ('source.pdf', 'original.png', 'model.blend', 'cache.pyc', 'data.csv', 'archive.zip'):
            with self.subTest(name=name), self.directory() as d, self.assertRaises(ValueError):
                validate_archive(make_archive(d, name=name))

    def test_symlink_member_rejected(self):
        with self.directory() as d, self.assertRaises(ValueError): validate_archive(make_archive(d, symlink=True))

    def test_secret_and_signed_url_patterns_rejected(self):
        # Constructed markers are demonstrably dummy strings, not live credentials.
        bodies = [('ghp_' + 'A' * 30).encode(), ('sk-' + 'A' * 30).encode(),
                  b'-----BEGIN ' + b'PRIVATE KEY-----', b'https://example.invalid/file?' + b'sig=TEST_ONLY']
        for body in bodies:
            with self.directory() as d, self.assertRaises(ValueError): validate_archive(make_archive(d, body=body))

    def test_manifest_itself_is_scanned_for_secret_material(self):
        with self.directory() as d, self.assertRaises(ValueError):
            validate_archive(make_archive(d, manifest_mutation=lambda m: m.update(schema_version='ghp_' + 'A' * 30)))

    def test_actor_scope_cannot_widen(self):
        with self.directory() as d, self.assertRaises(ValueError):
            validate_archive(make_archive(d, manifest_mutation=lambda m: m.update(actor_visible_allowlist=['agent_visible.json', 'source_outcomes_reference.json'])))

if __name__ == '__main__': unittest.main()
