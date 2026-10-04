"""Independent exact-export adversarial checks in isolated synthetic directories."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
import warnings
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
spec = importlib.util.spec_from_file_location('laser_export_independent', ROOT/'tests'/'verify_export.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class IndependentExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='laser-review-')
        self.base = Path(self.temp.name)
        self.root = self.base/'package'
        self.root.mkdir()
        self.rows=[]
        for name in v.EXPECTED_FILES:
            dest = self.root/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            src = ROOT/name
            data = src.read_bytes() if src.is_file() else b'Original isolated validator fixture.\n'
            dest.write_bytes(data)
            self.rows.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        self.manifest={'files':self.rows,'actor_visible_allowlist':['agent_visible.json'],
                       'all_other_files_are_evaluator_audit_only':True,
                       'member_count_including_manifest':len(v.EXPECTED_FILES)+1}
        self.write_manifest()

    def tearDown(self):
        self.temp.cleanup()

    def write_manifest(self):
        (self.root/'EXPORT_ALLOWLIST.json').write_text(json.dumps(self.manifest))

    def archive(self, changes=None, extra=None, duplicate=None):
        out = self.base/'test.zip'
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',UserWarning)
            with zipfile.ZipFile(out,'w') as z:
                for name in list(v.EXPECTED_FILES)+['EXPORT_ALLOWLIST.json']:
                    payload=(self.root/name).read_bytes()
                    if changes and name in changes: payload=changes[name]
                    z.writestr(name,payload)
                if extra:
                    for name,payload in extra: z.writestr(name,payload)
                if duplicate: z.writestr(duplicate,(self.root/duplicate).read_bytes())
        return out

    def test_exact_synthetic_inventory_and_archive_are_accepted(self):
        self.assertEqual(v.verify(self.root),[])
        self.assertEqual(v.verify(self.root,self.archive()),[])

    def test_fixed_inventory_is_not_redefined_by_self_rehashed_manifest(self):
        name='retained_source.txt'; data=b'not permitted'
        (self.root/name).write_bytes(data)
        self.rows.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        self.manifest['member_count_including_manifest']+=1
        self.write_manifest()
        self.assertTrue(v.verify(self.root))

    def test_extra_missing_and_changed_local_files_are_rejected(self):
        extra=self.root/'unlisted.txt';extra.write_text('unexpected')
        self.assertTrue(v.verify(self.root)); extra.unlink()
        target=self.root/'README.md';data=target.read_bytes();target.unlink()
        self.assertTrue(v.verify(self.root));target.write_bytes(data+b'changed')
        self.assertTrue(v.verify(self.root))

    def test_local_symlink_file_directory_and_root_are_rejected(self):
        target=self.root/'README.md'; data=target.read_bytes()
        outside=self.base/'outside.txt';outside.write_bytes(data)
        target.unlink();target.symlink_to(outside)
        self.assertTrue(v.verify(self.root));target.unlink();target.write_bytes(data)
        link=self.root/'linked-directory';link.symlink_to(self.base,target_is_directory=True)
        self.assertTrue(v.verify(self.root));link.unlink()
        root_link=self.base/'root-link';root_link.symlink_to(self.root,target_is_directory=True)
        self.assertTrue(v.verify(root_link))

    def test_local_fifo_is_rejected_as_nonregular_inventory(self):
        os.mkfifo(self.root/'unexpected-fifo')
        self.assertTrue(v.verify(self.root))

    def test_manifest_traversal_and_noncanonical_names_are_rejected(self):
        original=self.rows[0]['path']
        for name in ['../escape','/absolute','a/../b','a/./b','a//b','a\\b','C:/drive',
                     './README.md','.hidden','x/.hidden','README.md/','',None,True,1,[]]:
            self.rows[0]['path']=name;self.write_manifest()
            with self.subTest(name=repr(name)):self.assertTrue(v.verify(self.root))
        self.rows[0]['path']=original

    def test_manifest_duplicate_paths_keys_and_nonfinite_values_are_rejected(self):
        self.rows.append(dict(self.rows[0]));self.write_manifest()
        self.assertTrue(v.verify(self.root));self.rows.pop()
        p=self.root/'EXPORT_ALLOWLIST.json'
        p.write_text('{"files":[],"files":[]}')
        self.assertTrue(v.verify(self.root))
        p.write_text('{"files":NaN}')
        self.assertTrue(v.verify(self.root))

    def test_manifest_types_hashes_and_actor_projection_are_strict(self):
        original=self.rows[0].copy()
        for field,bad in [('bytes',True),('bytes','1'),('bytes',-1),('sha256','f'*63),
                          ('sha256','G'*64),('sha256',0)]:
            self.rows[0].update(original);self.rows[0][field]=bad;self.write_manifest()
            with self.subTest(field=field,bad=bad):self.assertTrue(v.verify(self.root))
        self.rows[0].update(original)
        self.manifest['member_count_including_manifest']=True;self.write_manifest()
        self.assertTrue(v.verify(self.root))
        self.manifest['member_count_including_manifest']=len(v.EXPECTED_FILES)+1
        self.manifest['actor_visible_allowlist']=['agent_visible.json','source_outcomes.json'];self.write_manifest()
        self.assertTrue(v.verify(self.root))

    def test_archive_changed_and_duplicate_members_are_rejected(self):
        self.assertTrue(v.verify(self.root,self.archive(changes={'README.md':b'altered'})))
        self.assertTrue(v.verify(self.root,self.archive(duplicate='README.md'))) 

    def test_archive_traversal_extra_source_and_directory_members_are_rejected(self):
        for name in ['../outside','/absolute','a/../b','./README.md','source.pdf','cache/',
                     '__pycache__/cached.pyc','a\\b','C:/drive']:
            with self.subTest(name=name):
                self.assertTrue(v.verify(self.root,self.archive(extra=[(name,b'not allowed')])))

    def test_archive_symlink_and_special_modes_are_rejected(self):
        for mode in [stat.S_IFLNK,stat.S_IFDIR,stat.S_IFIFO,stat.S_IFSOCK,stat.S_IFCHR]:
            archive=self.archive()
            info=zipfile.ZipInfo('unexpected');info.create_system=3
            info.external_attr=(mode|0o644)<<16
            with zipfile.ZipFile(archive,'a') as z:z.writestr(info,b'target')
            with self.subTest(mode=mode):self.assertTrue(v.verify(self.root,archive))

    def test_archive_same_name_symlink_mode_is_rejected(self):
        out=self.base/'mode.zip'
        with zipfile.ZipFile(out,'w') as z:
            for name in list(v.EXPECTED_FILES)+['EXPORT_ALLOWLIST.json']:
                info=zipfile.ZipInfo(name);info.create_system=3
                info.external_attr=((stat.S_IFLNK if name=='README.md' else stat.S_IFREG)|0o644)<<16
                z.writestr(info,(self.root/name).read_bytes())
        self.assertTrue(v.verify(self.root,out))

    def test_corrupt_and_non_zip_archive_is_rejected(self):
        archive=self.base/'corrupt.zip';archive.write_bytes(b'not an archive')
        self.assertTrue(v.verify(self.root,archive))


if __name__=='__main__':unittest.main()
