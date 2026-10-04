"""Independent export attacks against isolated temporary trees only."""
import copy
import hashlib
import importlib.util
import json
import pathlib
import tempfile
import unittest

BASE=pathlib.Path(__file__).resolve().parents[1]
ROOT=BASE if (BASE/'branches.json').exists() else BASE/'transistor_operations_v2'
spec=importlib.util.spec_from_file_location('transistor_export_review_target',ROOT/'tests/verify_export.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class ExportReview(unittest.TestCase):
    def tree(self):
        td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);root=pathlib.Path(td.name)
        (root/'original.json').write_bytes(b'{}\n');(root/'EXPORT_ALLOWLIST.json').write_bytes(b'{}\n')
        manifest={'allowlist':['original.json','EXPORT_ALLOWLIST.json'],'files':{'original.json':{'bytes':3,'sha256':hashlib.sha256(b'{}\n').hexdigest()}},'payload_file_count':1,'total_file_count_including_manifest':2}
        return root,manifest
    def add(self,root,manifest,name,data=b'fake'):
        (root/name).write_bytes(data)
        manifest['allowlist'].append(name)
        manifest['files'][name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
        manifest['payload_file_count']+=1;manifest['total_file_count_including_manifest']+=1
    def reject(self,root,manifest):self.assertTrue(m.validate_manifest(root,manifest))
    def test_pristine(self):
        root,manifest=self.tree();self.assertEqual(m.validate_manifest(root,manifest),[])
    def test_same_size_tampering(self):
        root,manifest=self.tree();(root/'original.json').write_bytes(b'[]\n');self.reject(root,manifest)
    def test_truncated_payload(self):
        root,manifest=self.tree();(root/'original.json').write_bytes(b'{}');self.reject(root,manifest)
    def test_missing_payload(self):
        root,manifest=self.tree();(root/'original.json').unlink();self.reject(root,manifest)
    def test_unlisted_cache(self):
        root,manifest=self.tree();(root/'cache.pyc').write_bytes(b'fake');self.reject(root,manifest)
    def test_allowlisted_pdf_rejected(self):
        root,manifest=self.tree();self.add(root,manifest,'publisher.pdf');self.reject(root,manifest)
    def test_allowlisted_png_rejected(self):
        root,manifest=self.tree();self.add(root,manifest,'publisher.png');self.reject(root,manifest)
    def test_allowlisted_source_text_rejected(self):
        root,manifest=self.tree();self.add(root,manifest,'main.txt');self.reject(root,manifest)
    def test_private_json_name_rejected(self):
        root,manifest=self.tree();self.add(root,manifest,'source_manifest.json');self.reject(root,manifest)
    def test_file_symlink_rejected(self):
        root,manifest=self.tree();(root/'original.json').unlink();(root/'original.json').symlink_to('EXPORT_ALLOWLIST.json');self.reject(root,manifest)
    def test_directory_symlink_rejected(self):
        root,manifest=self.tree();(root/'linked').symlink_to(root,target_is_directory=True);self.reject(root,manifest)
    def test_traversal_rejected(self):
        root,manifest=self.tree();manifest['allowlist'].append('../escaped.json');self.reject(root,manifest)
    def test_absolute_path_rejected(self):
        root,manifest=self.tree();manifest['allowlist'].append('/escaped.json');self.reject(root,manifest)
    def test_backslash_path_rejected(self):
        root,manifest=self.tree();manifest['allowlist'].append('nested\\escaped.json');self.reject(root,manifest)
    def test_duplicate_path_rejected(self):
        root,manifest=self.tree();manifest['allowlist'].append('original.json');self.reject(root,manifest)
    def test_boolean_bytes_rejected(self):
        root,manifest=self.tree();manifest['files']['original.json']['bytes']=True;self.reject(root,manifest)
    def test_digest_omission_rejected(self):
        root,manifest=self.tree();manifest['files'].pop('original.json');self.reject(root,manifest)
    def test_count_mismatch_rejected(self):
        root,manifest=self.tree();manifest['payload_file_count']=2;self.reject(root,manifest)

if __name__=='__main__':unittest.main(verbosity=2)
