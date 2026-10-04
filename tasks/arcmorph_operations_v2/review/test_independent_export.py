"""Independent adversarial tests of the text-only allowlisted export boundary.
All mutations occur in disposable copies; reviewed source files remain unchanged.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import sys
import tempfile
import unittest
import warnings
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
SPEC=importlib.util.spec_from_file_location('independent_exporter',ROOT/'tests'/'verify_export.py')
E=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(E)

class IndependentExport(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='arcmorph-independent-')
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.root=self.base/'copy'
        self.root.mkdir()
        for name in E.ALLOWED:
            target=self.root/name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,target)
        self.manifest=E.freeze(self.root)
    def reject_directory(self):
        with self.assertRaises(E.ExportError):E.verify_directory(self.root)
    def write_manifest(self,m):
        (self.root/E.MANIFEST).write_text(json.dumps(m))
    def rehash(self,name,data):
        (self.root/name).write_bytes(data)
        m=deepcopy(self.manifest)
        row=next(x for x in m['files'] if x['path']==name)
        row.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        self.write_manifest(m)
    def zip_mutation(self,change):
        original=self.base/'original.zip';E.build_zip(self.root,original)
        with zipfile.ZipFile(original) as z:
            rows=[(deepcopy(i),z.read(i.filename)) for i in z.infolist()]
        rows=change(rows)
        bad=self.base/'bad.zip'
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',UserWarning)
            with zipfile.ZipFile(bad,'w',zipfile.ZIP_DEFLATED) as z:
                for info,data in rows:z.writestr(info,data)
        with self.assertRaises(E.ExportError):E.verify_zip(bad)
    def test_export_inventory_has_only_reviewed_text_families(self):
        self.assertEqual(len(E.ALLOWED),45)
        self.assertEqual(len(set(E.ALLOWED)),45)
        self.assertTrue(all(name=='LICENSE' or Path(name).suffix in {'.json','.md','.py'} for name in E.ALLOWED))
        self.assertEqual({Path(name).parts[0] for name in E.ALLOWED if len(Path(name).parts)>1},{'review','tests'})
        self.assertEqual(self.manifest['actor_visible_allowlist'],['agent_visible.json'])
        self.assertEqual(self.manifest['member_count_including_manifest'],46)
    def test_roundtrip_is_deterministic_and_exact(self):
        self.assertTrue(E.verify_directory(self.root)['passed'])
        a=self.base/'one.zip';b=self.base/'two.zip'
        self.assertTrue(E.build_zip(self.root,a)['passed'])
        E.build_zip(self.root,b)
        self.assertEqual(a.read_bytes(),b.read_bytes())
        with zipfile.ZipFile(a) as z:
            self.assertEqual(set(z.namelist()),set(E.ALLOWED)|{E.MANIFEST})
            self.assertTrue(all(not i.is_dir() for i in z.infolist()))
            for i in z.infolist():z.read(i.filename).decode('utf-8')
    def test_modified_or_missing_member_rejected(self):
        name='README.md';original=(self.root/name).read_bytes()
        (self.root/name).write_bytes(original+b'\nchanged')
        self.reject_directory()
        (self.root/name).unlink()
        self.reject_directory()
    def test_extra_source_and_private_files_rejected(self):
        for name in ('source.pdf','figure.png','raw.zip','notebook.ipynb','source_model.py','.secret'):
            with self.subTest(name=name):
                p=self.root/name;p.write_text('not permitted')
                self.reject_directory()
                with self.assertRaises(E.ExportError):E.freeze(self.root)
                p.unlink()
    def test_unknown_empty_directory_rejected(self):
        (self.root/'unknown').mkdir();self.reject_directory()
        with self.assertRaises(E.ExportError):E.freeze(self.root)
    def test_member_and_manifest_symlinks_rejected(self):
        for name in ('README.md',E.MANIFEST):
            original=(self.root/name).read_bytes();outside=self.base/'outside';outside.write_bytes(original)
            (self.root/name).unlink();(self.root/name).symlink_to(outside)
            self.reject_directory()
            with self.assertRaises(E.ExportError):E.freeze(self.root)
            (self.root/name).unlink();(self.root/name).write_bytes(original)
    def test_root_or_ancestor_symlink_rejected(self):
        link=self.base/'linked';link.symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(E.ExportError):E.verify_directory(link)
        parent=self.base/'parent';parent.symlink_to(self.base,target_is_directory=True)
        with self.assertRaises(E.ExportError):E.verify_directory(parent/'copy')
    def test_fifo_rejected_without_read(self):
        fifo=self.root/'README.md';fifo.unlink();os.mkfifo(fifo)
        self.reject_directory()
        with self.assertRaises(E.ExportError):E.freeze(self.root)
    def test_rehashed_binary_and_private_paths_rejected(self):
        bad=[b'\xff\xfe',b'text\x00binary',('/'+'workspace/'+'private').encode(),
             ('/'+'root/'+'private').encode(),('sediment'+':/'+'/secret').encode()]
        for data in bad:
            with self.subTest(data=data):
                self.rehash('README.md',data);self.reject_directory()
    def test_manifest_exact_schema_types_and_actor_boundary(self):
        mutations=[('schema_version','wrong'),('member_count_including_manifest',True),
                   ('member_count_including_manifest',len(E.ALLOWED)),('actor_visible_allowlist',['source_outcomes.json']),
                   ('all_other_files_are_evaluator_audit_only',False),('extra','not allowed')]
        for key,value in mutations:
            with self.subTest(field=key):
                m=deepcopy(self.manifest);m[key]=value;self.write_manifest(m);self.reject_directory()
    def test_manifest_duplicate_missing_reordered_entries(self):
        variants=[]
        m=deepcopy(self.manifest);m['files'][1]=deepcopy(m['files'][0]);variants.append(m)
        m=deepcopy(self.manifest);m['files'].pop();variants.append(m)
        m=deepcopy(self.manifest);m['files'].reverse();variants.append(m)
        for m in variants:self.write_manifest(m);self.reject_directory()
    def test_manifest_rejects_duplicate_json_keys_and_nonfinite_values(self):
        for blob in (b'{"a":1,"a":2}',b'{"a":NaN}',b'{"a":Infinity}',b'{"a":-Infinity}',b'\xff'):
            with self.assertRaises(E.ExportError):E.load_bytes(blob)
    def test_manifest_member_field_types_sizes_hashes_and_paths(self):
        for key,value in [('bytes',0),('bytes',True),('bytes',E.LIMIT+1),('sha256','a'*63),
                          ('sha256','G'*64),('path',E.MANIFEST),('path','source.pdf'),('extra',1)]:
            with self.subTest(field=key,value=value):
                m=deepcopy(self.manifest);m['files'][0][key]=value
                with self.assertRaises(E.ExportError):E.manifest_check(m)
    def test_noncanonical_paths_rejected(self):
        for name in ('../README.md','/README.md','./README.md','tests//contract.py',
                     'tests/../README.md','tests\\contract.py','README.md\x00','.','',None):
            with self.subTest(path=name):
                with self.assertRaises(E.ExportError):E.safe_path(name)
    def test_archive_destination_cannot_replace_package_or_follow_links(self):
        with self.assertRaises(E.ExportError):E.build_zip(self.root,self.root/'release.zip')
        link=self.base/'linked.zip';link.symlink_to(self.base/'target.zip')
        with self.assertRaises(E.ExportError):E.build_zip(self.root,link)
        parent=self.base/'link-dir';parent.symlink_to(self.base,target_is_directory=True)
        with self.assertRaises(E.ExportError):E.build_zip(self.root,parent/'out.zip')
    def test_zip_duplicate_missing_and_extra_members_rejected(self):
        self.zip_mutation(lambda rows:rows+[rows[0]])
        self.zip_mutation(lambda rows:rows[1:])
        self.zip_mutation(lambda rows:rows+[(zipfile.ZipInfo('source.pdf'),b'forbidden')])
    def test_zip_directory_alias_and_symlink_metadata_rejected(self):
        def change_name(name):
            def mutate(rows):rows[0][0].filename=name;return rows
            return mutate
        for name in ('./README.md','../README.md','review/'):
            self.zip_mutation(change_name(name))
        def symlink(rows):rows[0][0].external_attr=(stat.S_IFLNK|0o777)<<16;return rows
        self.zip_mutation(symlink)
    def test_zip_corrupted_contents_rejected(self):
        def mutation(rows):
            i,data=rows[0];rows[0]=(i,data+b'bad');return rows
        self.zip_mutation(mutation)
    def test_zip_encryption_flag_rejected(self):
        p=self.base/'plain.zip';E.build_zip(self.root,p);data=bytearray(p.read_bytes())
        self.assertEqual(data[:4],b'PK\x03\x04')
        flags=struct.unpack_from('<H',data,6)[0];struct.pack_into('<H',data,6,flags|1)
        central=data.index(b'PK\x01\x02');flags=struct.unpack_from('<H',data,central+8)[0]
        struct.pack_into('<H',data,central+8,flags|1)
        bad=self.base/'encrypted.zip';bad.write_bytes(data)
        with self.assertRaises(E.ExportError):E.verify_zip(bad)
    def test_rehashed_bad_bytes_also_rejected_from_zip(self):
        for data in (b'\xff',b'\x00',('/'+'workspace/'+'private').encode()):
            def mutate(rows):
                new=[]
                m=deepcopy(self.manifest);entry=next(x for x in m['files'] if x['path']=='README.md')
                entry.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
                for i,old in rows:
                    new.append((i,data if i.filename=='README.md' else json.dumps(m).encode() if i.filename==E.MANIFEST else old))
                return new
            self.zip_mutation(mutate)
    def test_reviewed_manifest_when_present(self):
        # The author may re-freeze after review; this test checks the actual delivered tree.
        if not (ROOT/E.MANIFEST).is_file():self.skipTest('Author has not frozen release manifest')
        self.assertTrue(E.verify_directory(ROOT)['passed'])

if __name__=='__main__':unittest.main()
