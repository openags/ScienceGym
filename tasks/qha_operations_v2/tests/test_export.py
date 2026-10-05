import unittest,tempfile,json,zipfile,hashlib,stat
from pathlib import Path
from verify_export import *
class ExportTests(unittest.TestCase):
 def test_unsafe_paths(self):
  for p in ['/absolute.py','../outside.py','a/../b.py','a\\b.py','./a.py','a//b.py','x.pdf','file.png','source.glb','x.pyc','__pycache__/file.py']:
   with self.subTest(path=p):
    with self.assertRaises(ValueError):safe_path(p)
 def test_binary_or_secret_payload(self):
  for b in [b'%PDF-fake',b'PK\x03\x04fake',b'\x89PNGfake',b'glTFfake',b'ghp_'+b'a'*25,b'sk-'+b'a'*30,b'https://test.invalid/file'+b'?'+b'sig=secret',b'-----BEGIN '+b'PRIVATE KEY-----']:
   with self.subTest(payload=b[:10]):
    with self.assertRaises(ValueError):inspect_bytes('x.md',b)
 def test_valid_archive(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'p.zip';b=b'Original authored note';m={'schema_version':'sciencegym.qha.export.v1','files':[{'path':'README.md','bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}],'member_count_including_manifest':2,'actor_visible_allowlist':['agent_visible.json'],'all_other_files_are_evaluator_audit_only':True}
   with zipfile.ZipFile(p,'w') as z:z.writestr(ROOT+'/README.md',b);z.writestr(ROOT+'/EXPORT_ALLOWLIST.json',json.dumps(m))
   self.assertEqual(validate_archive(p)['status'],'PASS')
 def test_archive_hash_and_members(self):
  for defect in ['hash','extra','traversal','symlink','duplicate']:
   with self.subTest(defect=defect),tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/'p.zip';b=b'Original';m={'schema_version':'sciencegym.qha.export.v1','files':[{'path':'README.md','bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}],'member_count_including_manifest':2,'actor_visible_allowlist':['agent_visible.json'],'all_other_files_are_evaluator_audit_only':True}
    with zipfile.ZipFile(p,'w') as z:
     z.writestr(ROOT+'/EXPORT_ALLOWLIST.json',json.dumps(m));z.writestr(ROOT+'/README.md',b if defect!='hash' else b'Changed!')
     if defect=='extra':z.writestr(ROOT+'/extra.md',b)
     if defect=='traversal':z.writestr(ROOT+'/../extra.md',b)
     if defect=='duplicate':z.writestr(ROOT+'/README.md',b)
     if defect=='symlink':
      i=zipfile.ZipInfo(ROOT+'/link.md');i.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(i,b)
    with self.assertRaises(ValueError):validate_archive(p)
if __name__=='__main__':unittest.main()
