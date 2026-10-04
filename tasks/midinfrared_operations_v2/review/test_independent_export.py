"""Independent hostile-export tests on disposable copies of the bounded text release."""
import copy
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
SPEC=importlib.util.spec_from_file_location('independently_loaded_exporter',ROOT/'tests'/'verify_export.py')
E=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(E)


class IndependentExportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='independent-export-')
        self.base=Path(self.temp.name)
        self.root=self.base/'package'
        self.root.mkdir()
        for name in E.ALLOWED:
            target=self.root/name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,target)
        E.freeze(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def reject(self,func,*args):
        with self.assertRaises(E.ExportError):
            func(*args)

    def make_zip(self,transform=None):
        target=self.base/'hostile.zip'
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
            for name in sorted((*E.ALLOWED,E.MANIFEST)):
                info=zipfile.ZipInfo(name)
                info.create_system=3
                info.external_attr=(stat.S_IFREG|0o644)<<16
                data=(self.root/name).read_bytes()
                if transform:
                    info,data=transform(info,data)
                if info is not None:
                    archive.writestr(info,data)
        return target

    def test_exact_directory_and_exported_zip(self):
        self.assertTrue(E.verify_directory(self.root)['passed'])
        target=self.base/'valid.zip'
        self.assertTrue(E.build_zip(self.root,target)['passed'])
        with zipfile.ZipFile(target) as archive:
            self.assertEqual(set(archive.namelist()),set(E.ALLOWED)|{E.MANIFEST})
            self.assertEqual(len(archive.namelist()),48)
            self.assertTrue(all(not i.is_dir() for i in archive.infolist()))

    def test_repeated_export_has_identical_bytes(self):
        a,b=self.base/'a.zip',self.base/'b.zip'
        E.build_zip(self.root,a);E.build_zip(self.root,b)
        self.assertEqual(a.read_bytes(),b.read_bytes())

    def test_unknown_file_and_empty_directory_rejected(self):
        target=self.root/'unexpected.pdf';target.write_bytes(b'not source content')
        self.reject(E.freeze,self.root);target.unlink()
        target=self.root/'empty';target.mkdir();self.reject(E.freeze,self.root)

    def test_missing_and_changed_file_rejected(self):
        target=self.root/'README.md';target.write_text('mutated',encoding='utf-8')
        self.reject(E.verify_directory,self.root)
        target.unlink();self.reject(E.verify_directory,self.root)

    def test_private_absolute_path_families_rejected_after_rehash(self):
        prefixes=[('/'+'workspace/'),('/'+'root/'),('/'+'home/'),('/'+'tmp/'),('/'+'Users/'),('/'+'Volumes/'),('file'+':/'+ '/'),('sediment'+':/'+ '/')]
        original=(self.root/'README.md').read_bytes()
        for prefix in prefixes:
            with self.subTest(prefix=prefix):
                (self.root/'README.md').write_text(prefix+'private-artifact',encoding='utf-8')
                self.reject(E.freeze,self.root)
                (self.root/'README.md').write_bytes(original)

    def test_recognized_binary_signatures_cannot_hide_under_text_name(self):
        original=(self.root/'README.md').read_bytes()
        for payload in (b'%PDF-1.7\ntext-only-shaped-payload',b'PK\x03\x04ascii-shaped-payload',b'\x7fELFascii-shaped-payload'):
            with self.subTest(signature=repr(payload[:4])):
                (self.root/'README.md').write_bytes(payload)
                self.reject(E.freeze,self.root)
                (self.root/'README.md').write_bytes(original)

    def test_invalid_utf8_nul_empty_and_oversized_files_rejected(self):
        original=(self.root/'README.md').read_bytes()
        for payload in (b'\xff',b'hello\0world',b'',b'a'*(E.LIMIT+1)):
            with self.subTest(length=len(payload)):
                (self.root/'README.md').write_bytes(payload)
                self.reject(E.freeze,self.root)
                (self.root/'README.md').write_bytes(original)

    def test_file_and_directory_symlinks_rejected(self):
        target=self.root/'README.md';target.unlink();target.symlink_to(ROOT/'README.md')
        self.reject(E.verify_directory,self.root)
        target.unlink();shutil.copyfile(ROOT/'README.md',target)
        shutil.rmtree(self.root/'tests');(self.root/'tests').symlink_to(ROOT/'tests',target_is_directory=True)
        self.reject(E.freeze,self.root)

    def test_symlinked_root_and_ancestor_rejected(self):
        alias=self.base/'alias';alias.symlink_to(self.root,target_is_directory=True)
        self.reject(E.verify_directory,alias)
        outer=self.base/'outer';outer.mkdir();alias2=self.base/'outer-alias';alias2.symlink_to(outer,target_is_directory=True)
        shutil.copytree(self.root,outer/'nested')
        self.reject(E.verify_directory,alias2/'nested')

    def test_named_pipe_rejected_without_reading(self):
        target=self.root/'README.md';target.unlink();os.mkfifo(target)
        self.reject(E.freeze,self.root)

    def test_manifest_destination_symlink_rejected(self):
        target=self.root/E.MANIFEST;target.unlink();target.symlink_to(self.base/'outside.json')
        self.reject(E.freeze,self.root)

    def test_manifest_duplicate_keys_nonfinite_bad_schema_and_visibility(self):
        for data in (b'{"files":[],"files":[]}',b'{"number":Infinity}',b'{"number":NaN}'):
            self.reject(E.load_bytes,data)
        m=json.loads((self.root/E.MANIFEST).read_text())
        for key,value in [('schema_version','wrong'),('member_count_including_manifest',True),('actor_visible_allowlist',['agent_visible.json','source_outcomes.json']),('all_other_files_are_evaluator_audit_only',False)]:
            bad=copy.deepcopy(m);bad[key]=value;self.reject(E.manifest_check,bad)

    def test_manifest_entry_mutations(self):
        m=json.loads((self.root/E.MANIFEST).read_text())
        for key,value in [('bytes',True),('bytes',0),('bytes',E.LIMIT+1),('sha256','f'*63),('sha256','F'*64),('path','unknown.txt')]:
            bad=copy.deepcopy(m);bad['files'][0][key]=value;self.reject(E.manifest_check,bad)
        bad=copy.deepcopy(m);bad['files'].reverse();self.reject(E.manifest_check,bad)
        bad=copy.deepcopy(m);bad['files'][1]=bad['files'][0];self.reject(E.manifest_check,bad)

    def test_alias_absolute_windows_and_traversal_names_rejected(self):
        for path in ('../README.md','/README.md','./README.md','tests/../README.md','tests//contract.py','tests\\contract.py','C:/README.md','README.md/','README.md\x00hidden','README.md '):
            with self.subTest(path=path):
                self.reject(E.safe_path,path)

    def test_zip_duplicate_and_unknown_member_rejected(self):
        target=self.make_zip()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',UserWarning)
            with zipfile.ZipFile(target,'a') as archive:archive.writestr('README.md','duplicate')
        self.reject(E.verify_zip,target)
        target=self.make_zip()
        with zipfile.ZipFile(target,'a') as archive:archive.writestr('unknown.txt','unknown')
        self.reject(E.verify_zip,target)

    def test_zip_missing_member_and_hash_mismatch_rejected(self):
        target=self.make_zip(lambda info,data:(None,data) if info.filename=='README.md' else (info,data))
        self.reject(E.verify_zip,target)
        target=self.make_zip(lambda info,data:(info,b'changed') if info.filename=='README.md' else (info,data))
        self.reject(E.verify_zip,target)

    def test_zip_path_aliases_rejected(self):
        for replacement in ('./README.md','../README.md','tests/../README.md','README.md/'):
            def mutate(info,data):
                if info.filename=='README.md':info.filename=replacement
                return info,data
            self.reject(E.verify_zip,self.make_zip(mutate))

    def test_zip_symlink_fifo_directory_and_device_modes_rejected(self):
        for mode in (stat.S_IFLNK,stat.S_IFIFO,stat.S_IFDIR,stat.S_IFCHR,stat.S_IFBLK,stat.S_IFSOCK):
            def mutate(info,data):
                if info.filename=='README.md':info.external_attr=(mode|0o644)<<16
                return info,data
            self.reject(E.verify_zip,self.make_zip(mutate))

    def test_zip_encrypted_flag_rejected(self):
        target=self.make_zip();data=bytearray(target.read_bytes())
        index=0
        while True:
            index=data.find(b'PK\x01\x02',index)
            if index<0:break
            flags=struct.unpack_from('<H',data,index+8)[0]
            struct.pack_into('<H',data,index+8,flags|1);index+=4
        target.write_bytes(data);self.reject(E.verify_zip,target)

    def test_zip_local_header_name_disagreement_rejected(self):
        target=self.make_zip();data=bytearray(target.read_bytes());central=data.find(b'PK\x01\x02')
        self.assertGreaterEqual(central,0)
        local_offset=struct.unpack_from('<I',data,central+42)[0]
        name_length=struct.unpack_from('<H',data,local_offset+26)[0]
        self.assertGreater(name_length,0)
        data[local_offset+30]=ord('X');target.write_bytes(data)
        self.reject(E.verify_zip,target)

    def test_zip_fake_magic_truncation_and_missing_archive_rejected(self):
        target=self.base/'bad.zip';target.write_bytes(b'PK\x03\x04truncated')
        self.reject(E.verify_zip,target)
        target.unlink();self.reject(E.verify_zip,target)

    def test_archive_destination_cannot_be_inside_or_symlinked(self):
        self.reject(E.build_zip,self.root,self.root/'archive.zip')
        target=self.base/'alias.zip';target.symlink_to(self.base/'target.zip')
        self.reject(E.build_zip,self.root,target)
        directory=self.base/'real';directory.mkdir();alias=self.base/'alias';alias.symlink_to(directory,target_is_directory=True)
        self.reject(E.build_zip,self.root,alias/'archive.zip')


if __name__=='__main__':
    unittest.main()
