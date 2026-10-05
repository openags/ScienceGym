import json
import unittest
from verify_export import verify_members, names_valid, sha

def dump(x):return (json.dumps(x,sort_keys=True)+'\n').encode()
def bundle():
    m={'README.md':b'Original offline design\n','scene_binding_contract.json':b'{}\n'}
    names=sorted(list(m)+['EXPORT_ALLOWLIST.json','CONTENT_MANIFEST.json','PAIR_SEAL.json'])
    m['EXPORT_ALLOWLIST.json']=dump({'files':names})
    m['CONTENT_MANIFEST.json']=dump({'files':[{'path':n,'bytes':len(d),'sha256':sha(d)} for n,d in sorted(m.items())]})
    m['PAIR_SEAL.json']=dump({'task_content_manifest_sha256':sha(m['CONTENT_MANIFEST.json']),'scene_content_manifest_sha256':'a'*64,'shared_binding_sha256':sha(m['scene_binding_contract.json']),'physical_or_scientific_execution_validated':False})
    return m

class ExportTests(unittest.TestCase):
    def test_minimal_original_bundle(self):self.assertTrue(verify_members(bundle())['sanitized'])
    def test_unknown_extra_rejected(self):
        b=bundle();b['unknown.txt']=b'unknown'
        with self.assertRaises(AssertionError):verify_members(b)
    def test_missing_file_rejected(self):
        b=bundle();b.pop('README.md')
        with self.assertRaises(AssertionError):verify_members(b)
    def test_digest_tamper_rejected(self):
        b=bundle();b['README.md']=b'changed'
        with self.assertRaises(AssertionError):verify_members(b)
    def test_private_path_rejected(self):
        b=bundle();b['README.md']=('/'+'workspace/'+'private.txt').encode()
        with self.assertRaises(AssertionError):verify_members(b)
    def test_publisher_file_rejected(self):
        b=bundle();b['publisher.pdf']=b'publisher'
        with self.assertRaises(AssertionError):verify_members(b)
    def test_unsafe_paths_rejected(self):
        for name in ('../escape.py','/absolute.py','a/../escape.py','a//file.py','./file.py','a\\..\\escape.py','C:\\escape.py','C:/escape.py','a:file.py','.hidden','folder/.hidden','bad\x00name.py'):
            with self.subTest(name=name),self.assertRaises(AssertionError):names_valid([name])
    def test_duplicate_path_rejected(self):
        with self.assertRaises(AssertionError):names_valid(['a.py','a.py'])
    def test_stale_task_seal_rejected(self):
        b=bundle();s=json.loads(b['PAIR_SEAL.json']);s['task_content_manifest_sha256']='b'*64;b['PAIR_SEAL.json']=dump(s)
        with self.assertRaises(AssertionError):verify_members(b)
    def test_stale_binding_seal_rejected(self):
        b=bundle();s=json.loads(b['PAIR_SEAL.json']);s['shared_binding_sha256']='b'*64;b['PAIR_SEAL.json']=dump(s)
        with self.assertRaises(AssertionError):verify_members(b)
    def test_false_scientific_claim_rejected(self):
        b=bundle();s=json.loads(b['PAIR_SEAL.json']);s['physical_or_scientific_execution_validated']=True;b['PAIR_SEAL.json']=dump(s)
        with self.assertRaises(AssertionError):verify_members(b)
    def test_manifest_coverage_rejected(self):
        b=bundle();m=json.loads(b['CONTENT_MANIFEST.json']);m['files']=m['files'][:-1];b['CONTENT_MANIFEST.json']=dump(m)
        with self.assertRaises(AssertionError):verify_members(b)
if __name__=='__main__':unittest.main()
