"""Independent exact-export adversarial probes on disposable authored fixtures."""
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

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
SPEC=importlib.util.spec_from_file_location('independent_conformal_export',ROOT/'tests'/'verify_export.py')
E=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(E)


class IndependentExportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='conformal-review-')
        self.work=Path(self.temp.name)
        self.root=self.work/'package';self.root.mkdir()
        for name in E.ALLOWED:
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text('{}\n' if p.suffix=='.json' else 'Independent authored export probe.\n',encoding='utf-8')
        E.freeze(self.root)

    def tearDown(self):self.temp.cleanup()

    def reject(self,fn,*args):
        with self.assertRaises(E.ExportError):fn(*args)

    def archive(self, change=None, omit=None, comment=b'', prefix=b''):
        dest=self.work/'case.zip'
        with zipfile.ZipFile(dest,'w') as z:
            z.comment=comment
            for name in (*E.ALLOWED,E.MANIFEST):
                if name==omit:continue
                info=zipfile.ZipInfo(name);info.external_attr=(stat.S_IFREG|0o644)<<16
                data=(self.root/name).read_bytes()
                if change is not None:info,data=change(info,data)
                z.writestr(info,data)
        if prefix:dest.write_bytes(prefix+dest.read_bytes())
        return dest

    def replace_payload(self,payload,name='README.md'):
        (self.root/name).write_bytes(payload)
        self.reject(E.freeze,self.root)

    def test_exact_valid_directory_and_zip_roundtrip(self):
        self.assertTrue(E.verify_directory(self.root)['passed'])
        dest=self.work/'valid.zip';self.assertTrue(E.build_zip(self.root,dest)['passed'])
        with zipfile.ZipFile(dest) as z:
            self.assertEqual(sorted(z.namelist()),sorted((*E.ALLOWED,E.MANIFEST)))
            self.assertEqual(z.comment,b'')
            self.assertTrue(all(not i.comment and not i.extra for i in z.infolist()))

    def test_manifest_rejects_duplicate_keys_and_nonfinite_values(self):
        for raw in (b'{"a":1,"a":2}',b'{"a":NaN}',b'{"a":Infinity}',b'{"a":-Infinity}',b'\xff'):
            with self.subTest(raw=raw):self.reject(E.load_bytes,raw)

    def test_manifest_rejects_count_type_hash_case_and_extra_fields(self):
        original=json.loads((self.root/E.MANIFEST).read_text())
        for field,value in [('member_count_including_manifest',True),('schema_version','foreign'),('extra',True)]:
            m=copy.deepcopy(original);m[field]=value;self.reject(E.manifest_check,m)
        for field,value in [('bytes',True),('bytes',0),('bytes',E.LIMIT+1),('sha256','A'*64),('extra',1)]:
            m=copy.deepcopy(original);m['files'][0][field]=value;self.reject(E.manifest_check,m)

    def test_manifest_cannot_broaden_actor_view_or_allowlist(self):
        original=json.loads((self.root/E.MANIFEST).read_text())
        m=copy.deepcopy(original);m['actor_visible_allowlist'].append('source_outcomes.json');self.reject(E.manifest_check,m)
        m=copy.deepcopy(original);m['all_other_files_are_evaluator_audit_only']=False;self.reject(E.manifest_check,m)
        m=copy.deepcopy(original);m['files'][0]['path']='source.pdf';self.reject(E.manifest_check,m)
        m=copy.deepcopy(original);m['files'].reverse();self.reject(E.manifest_check,m)
        m=copy.deepcopy(original);m['files'][1]=m['files'][0];self.reject(E.manifest_check,m)

    def test_canonical_paths_reject_aliases_traversal_absolute_and_backslash(self):
        for name in ('../README.md','/README.md','./README.md','tests//contract.py','tests/../README.md',
                     'tests'+chr(92)+'contract.py','README.md/','README.md'+chr(0),'review'):
            with self.subTest(name=name):self.reject(E.safe_path,name)

    def test_unknown_file_and_empty_directory_rejected(self):
        (self.root/'source.pdf').write_text('unlisted');self.reject(E.freeze,self.root)
        (self.root/'source.pdf').unlink();(self.root/'unknown').mkdir();self.reject(E.freeze,self.root)

    def test_missing_file_and_rehashed_missing_member_rejected(self):
        (self.root/'README.md').unlink();self.reject(E.verify_directory,self.root);self.reject(E.freeze,self.root)

    def test_byte_change_cannot_keep_old_hash(self):
        (self.root/'README.md').write_text('changed');self.reject(E.verify_directory,self.root)

    def test_symlink_file_directory_root_and_ancestor_rejected(self):
        original=self.work/'outside.txt';original.write_text('outside')
        p=self.root/'README.md';p.unlink();p.symlink_to(original);self.reject(E.freeze,self.root)
        p.unlink();p.write_text('Independent authored export probe.\n')
        tests=self.root/'tests';shutil.rmtree(tests);tests.symlink_to(self.work,target_is_directory=True);self.reject(E.freeze,self.root)
        alias=self.work/'alias';alias.symlink_to(self.root,target_is_directory=True);self.reject(E.verify_directory,alias)
        holder=self.work/'holder';holder.mkdir();parent_alias=self.work/'holder-alias';parent_alias.symlink_to(holder,target_is_directory=True)
        nested=holder/'package';shutil.copytree(self.root,nested,symlinks=True);self.reject(E.root_path,parent_alias/'package')

    def test_manifest_symlink_cannot_be_overwritten(self):
        target=self.work/'manifest-target';target.write_text('leave me')
        p=self.root/E.MANIFEST;p.unlink();p.symlink_to(target)
        self.reject(E.freeze,self.root);self.assertEqual(target.read_text(),'leave me')

    def test_oversize_member_rejected_before_export(self):
        (self.root/'README.md').write_bytes(b'x'*(E.LIMIT+1));self.reject(E.freeze,self.root)

    def test_invalid_utf8_nul_and_control_characters_rejected_even_when_rehashed(self):
        for data in (b'\xff',b'hello\x00world',b'hello\x01world'):
            with self.subTest(data=data):self.replace_payload(data)

    def test_media_signatures_rejected_under_allowed_text_name(self):
        for data in (b'%PDF-1.7\n',b'GIF89a',b'RIFFpayload',b'<?xml version="1.0"?><svg/>',b'<svg/>',b'0000ftypisom'):
            with self.subTest(data=data):self.replace_payload(data)

    def test_bom_does_not_hide_media_signature(self):
        self.replace_payload(bytes([239,187,191])+b'%PDF-1.7\n')

    def test_plain_private_paths_rejected_even_when_rehashed(self):
        for prefix in ('workspace','workspaces','root','home','tmp','Users','Volumes','private'):
            with self.subTest(prefix=prefix):self.replace_payload(('/'+prefix+'/review-secret').encode())

    def test_json_escaped_windows_private_path_rejected(self):
        path='C:'+chr(92)+'Users'+chr(92)+'review-user'+chr(92)+'private.txt'
        self.replace_payload(json.dumps({'path':path}).encode(),'STATUS.json')

    def test_unicode_escaped_private_path_rejected(self):
        slash=chr(92)
        raw='{"path":"/'+ 'work'+slash+'u0073pace/private"}'
        self.replace_payload(raw.encode(),'STATUS.json')

    def test_local_file_and_upload_locator_rejected(self):
        for value in ('file'+':/'+'/local/name','sediment'+':/'+'/file_secret'):
            with self.subTest(value=value):self.replace_payload(value.encode())

    def test_zip_missing_duplicate_and_extra_member_rejected(self):
        self.reject(E.verify_zip,self.archive(omit='README.md'))
        dest=self.archive()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',UserWarning)
            with zipfile.ZipFile(dest,'a') as z:z.writestr('README.md','duplicate')
        self.reject(E.verify_zip,dest)
        dest=self.archive()
        with zipfile.ZipFile(dest,'a') as z:z.writestr('source.pdf','unlisted')
        self.reject(E.verify_zip,dest)

    def test_zip_rejects_wrong_hash_and_directory_member(self):
        def wrong(info,data):return info,b'wrong' if info.filename=='README.md' else data
        self.reject(E.verify_zip,self.archive(wrong))
        def directory(info,data):
            if info.filename=='README.md':info.filename+='/'
            return info,data
        self.reject(E.verify_zip,self.archive(directory))

    def test_zip_rejects_symlink_and_special_mode(self):
        for mode in (stat.S_IFLNK,stat.S_IFIFO,stat.S_IFSOCK):
            def change(info,data):
                if info.filename=='README.md':info.external_attr=(mode|0o644)<<16
                return info,data
            with self.subTest(mode=mode):self.reject(E.verify_zip,self.archive(change))

    def test_zip_archive_comment_cannot_hide_unlisted_payload(self):
        self.reject(E.verify_zip,self.archive(comment=b'%PDF-1.7 hidden source'))

    def test_zip_member_comment_cannot_hide_unlisted_payload(self):
        def change(info,data):
            if info.filename=='README.md':info.comment=b'%PDF-1.7 hidden source'
            return info,data
        self.reject(E.verify_zip,self.archive(change))

    def test_zip_extra_field_cannot_hide_unlisted_payload(self):
        def change(info,data):
            if info.filename=='README.md':info.extra=b'\xfe\xca\x04\x00hide'
            return info,data
        self.reject(E.verify_zip,self.archive(change))

    def test_archive_destination_cannot_be_inside_package_or_linked(self):
        self.reject(E.build_zip,self.root,self.root/'output.zip')
        target=self.work/'target.zip';target.write_bytes(b'unchanged')
        alias=self.work/'alias.zip';alias.symlink_to(target);self.reject(E.build_zip,self.root,alias)
        self.assertEqual(target.read_bytes(),b'unchanged')

    def test_nonzip_and_truncated_zip_rejected(self):
        p=self.work/'broken.zip';p.write_text('not an archive');self.reject(E.verify_zip,p)
        p=self.archive();p.write_bytes(p.read_bytes()[:-15]);self.reject(E.verify_zip,p)


if __name__=='__main__':unittest.main()
