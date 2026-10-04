"""Independent original text-export adversarial tests using disposable synthetic trees.

These tests check serialization and local file boundaries, not source authenticity,
scientific completeness, physical execution or production signing.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
import pathlib
import stat
import sys
import tempfile
import unittest
import warnings
import zipfile
sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[1]

class IndependentExportNegatives(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / 'tests'))
        spec = importlib.util.spec_from_file_location('independent_target_export', ROOT / 'tests' / 'verify_export.py')
        cls.v = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.v)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='varactor-independent-')
        self.addCleanup(self.tmp.cleanup)
        self.work = pathlib.Path(self.tmp.name)
        self.root = self.work / 'package'
        self.root.mkdir()
        for name in self.v.ALLOWED:
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('Original synthetic export-test content: ' + name + '\n', encoding='utf-8')
        self.v.freeze(self.root)

    def manifest(self):
        return json.loads((self.root / self.v.MANIFEST).read_text())

    def write_manifest(self, value):
        (self.root / self.v.MANIFEST).write_text(json.dumps(value, indent=2) + '\n')

    def reject_directory(self):
        with self.assertRaises(self.v.ExportError): self.v.verify_directory(self.root)

    def zip_members(self):
        return {n:(self.root/n).read_bytes() for n in (*self.v.ALLOWED,self.v.MANIFEST)}

    def write_zip(self, members=None, name='case.zip', overrides=None):
        dest = self.work / name
        members = self.zip_members() if members is None else members
        with zipfile.ZipFile(dest, 'w') as z:
            for n,data in members.items():
                info = zipfile.ZipInfo(n)
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                if overrides and n in overrides:
                    for key,val in overrides[n].items(): setattr(info,key,val)
                z.writestr(info,data)
        return dest

    def test_exact_synthetic_directory_and_zip_pass(self):
        self.assertIs(self.v.verify_directory(self.root)['passed'], True)
        dest = self.work / 'clean.zip'
        self.assertIs(self.v.build_zip(self.root,dest)['passed'], True)
        with zipfile.ZipFile(dest) as z:
            self.assertEqual(sorted(z.namelist()),sorted((*self.v.ALLOWED,self.v.MANIFEST)))

    def test_missing_extra_and_tampered_files_rejected(self):
        first=self.root/self.v.ALLOWED[0]
        old=first.read_bytes();first.write_bytes(old+b'changed')
        self.reject_directory();first.write_bytes(old)
        first.unlink();self.reject_directory();first.write_bytes(old)
        (self.root/'unlisted-source.pdf').write_text('source payload must not export')
        self.reject_directory()

    def test_unlisted_empty_directory_rejected(self):
        (self.root/'unlisted-empty-directory').mkdir()
        self.reject_directory()
        with self.assertRaises(self.v.ExportError):self.v.freeze(self.root)

    def test_manifest_hash_mutation_rejected(self):
        m=self.manifest();m['files'][0]['sha256']='0'*64;self.write_manifest(m)
        self.reject_directory()

    def test_manifest_boolean_size_and_count_rejected(self):
        original=self.manifest()
        for target in ['bytes','member_count_including_manifest']:
            m=json.loads(json.dumps(original))
            if target=='bytes':m['files'][0][target]=True
            else:m[target]=True
            self.write_manifest(m);self.reject_directory()

    def test_manifest_duplicate_key_rejected(self):
        raw=(self.root/self.v.MANIFEST).read_text()
        raw=raw.replace('"schema_version": "varactor_export.v1",',
                        '"schema_version": "varactor_export.v1", "schema_version": "varactor_export.v1",',1)
        (self.root/self.v.MANIFEST).write_text(raw)
        self.reject_directory()

    def test_manifest_duplicate_path_and_unauthorized_member_rejected(self):
        original=self.manifest()
        for path in [original['files'][0]['path'],'source-image.png']:
            m=json.loads(json.dumps(original));m['files'][1]['path']=path
            self.write_manifest(m);self.reject_directory()

    def test_noncanonical_paths_are_rejected(self):
        p=self.v.ALLOWED[0]
        paths=['../'+p,'./'+p,'nested/../'+p,'/'+p,'nested//'+p,
               'nested\\'+p,'C:\\'+p,p+'\x00','tests/./contract.py']
        for alias in paths:
            with self.subTest(alias=alias):
                with self.assertRaises(self.v.ExportError):self.v.safe_path(alias)

    def test_regular_member_replaced_by_symlink_rejected(self):
        p=self.root/self.v.ALLOWED[0];data=p.read_bytes();p.unlink()
        outside=self.work/'source-copy.txt';outside.write_bytes(data);p.symlink_to(outside)
        self.reject_directory()
        with self.assertRaises(self.v.ExportError):self.v.freeze(self.root)

    def test_symlink_directory_and_root_rejected(self):
        target=self.work/'outside-tests';(self.root/'tests').rename(target)
        (self.root/'tests').symlink_to(target,target_is_directory=True)
        self.reject_directory()
        with self.assertRaises(self.v.ExportError):self.v.freeze(self.root)
        link=self.work/'linked-root';link.symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(self.v.ExportError):self.v.verify_directory(link)

    def test_special_files_rejected_without_reading_them(self):
        os.mkfifo(self.root/'unlisted-fifo')
        self.reject_directory()

    def test_freeze_symlink_manifest_never_overwrites_outside_target(self):
        manifest=self.root/self.v.MANIFEST;manifest.unlink()
        outside=self.work/'protected-sentinel.txt';sentinel=b'unchanged sentinel\n';outside.write_bytes(sentinel)
        manifest.symlink_to(outside)
        with self.assertRaises(self.v.ExportError):self.v.freeze(self.root)
        self.assertEqual(outside.read_bytes(),sentinel,'rejection must precede any symlink-target write')

    def test_freeze_extra_file_does_not_rewrite_existing_manifest(self):
        manifest=self.root/self.v.MANIFEST;original=manifest.read_bytes()
        (self.root/'unlisted.txt').write_text('unexpected')
        p=self.root/self.v.ALLOWED[0];p.write_text('modified but not releasable')
        with self.assertRaises(self.v.ExportError):self.v.freeze(self.root)
        self.assertEqual(manifest.read_bytes(),original,'preflight must reject extra members before publishing new hashes')

    def test_zip_missing_extra_duplicate_and_alias_names_rejected(self):
        clean=self.zip_members();first=self.v.ALLOWED[0]
        variants=[]
        m=dict(clean);m.pop(first);variants.append(m)
        m=dict(clean);m['source-data.xml']=b'not releasable';variants.append(m)
        for alias in ['../'+first,'./'+first,'/'+first,'dir\\'+first]:
            m=dict(clean);m[alias]=m.pop(first);variants.append(m)
        for i,m in enumerate(variants):
            z=self.write_zip(m,name=f'bad-{i}.zip')
            with self.assertRaises(self.v.ExportError):self.v.verify_zip(z)
        z=self.write_zip()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',UserWarning)
            with zipfile.ZipFile(z,'a') as archive:archive.writestr(first,clean[first])
        with self.assertRaises(self.v.ExportError):self.v.verify_zip(z)

    def test_zip_symlink_and_special_modes_rejected(self):
        first=self.v.ALLOWED[0]
        for i,mode in enumerate([stat.S_IFLNK,stat.S_IFIFO,stat.S_IFSOCK,stat.S_IFDIR]):
            z=self.write_zip(name=f'mode-{i}.zip',overrides={first:{'external_attr':(mode|0o644)<<16}})
            with self.assertRaises(self.v.ExportError):self.v.verify_zip(z)

    def test_zip_tampered_hash_and_empty_member_rejected(self):
        first=self.v.ALLOWED[0]
        for data in [b'',b'replaced content']:
            m=self.zip_members();m[first]=data;z=self.write_zip(m)
            with self.assertRaises(self.v.ExportError):self.v.verify_zip(z)

    def test_zip_oversized_member_rejected(self):
        m=self.zip_members();m[self.v.ALLOWED[0]]=b'x'*(self.v.LIMIT+1)
        z=self.write_zip(m)
        with self.assertRaises(self.v.ExportError):self.v.verify_zip(z)

    def test_private_path_rejected_even_with_matching_manifest_hash(self):
        for payload in [('/'+'workspace/'+'private/source.xml'),
                        ('/'+'root/'+'private/source.xml'),
                        ('sediment'+':/'+'/'+'private-file')]:
            members=self.zip_members();first=self.v.ALLOWED[0]
            members[first]=payload.encode()
            manifest=json.loads(members[self.v.MANIFEST])
            entry=next(e for e in manifest['files'] if e['path']==first)
            entry.update(bytes=len(members[first]),sha256=hashlib.sha256(members[first]).hexdigest())
            members[self.v.MANIFEST]=json.dumps(manifest).encode()
            with self.assertRaises(self.v.ExportError):self.v.verify_zip(self.write_zip(members))

    def test_binary_bytes_rejected_even_with_matching_hash(self):
        for data in [b'hello\x00world',b'\xff\xfe']:
            members=self.zip_members();first=self.v.ALLOWED[0];members[first]=data
            manifest=json.loads(members[self.v.MANIFEST])
            entry=next(e for e in manifest['files'] if e['path']==first)
            entry.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
            members[self.v.MANIFEST]=json.dumps(manifest).encode()
            with self.assertRaises(self.v.ExportError):self.v.verify_zip(self.write_zip(members))

    def test_archive_destination_inside_root_is_rejected(self):
        with self.assertRaises(self.v.ExportError):self.v.build_zip(self.root,self.root/'release.zip')
        self.assertFalse((self.root/'release.zip').exists())

    def test_archive_destination_symlink_never_overwrites_outside_target(self):
        target=self.work/'protected-output.txt';sentinel=b'unchanged output\n';target.write_bytes(sentinel)
        link=self.work/'linked.zip';link.symlink_to(target)
        with self.assertRaises(self.v.ExportError):self.v.build_zip(self.root,link)
        self.assertEqual(target.read_bytes(),sentinel)

if __name__ == '__main__':
    unittest.main()
