import unittest,tempfile,shutil,json
from pathlib import Path
from verify_export import ROOT,verify
class ExportTests(unittest.TestCase):
 def clone(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);dst=Path(t.name)/'package';shutil.copytree(ROOT,dst,ignore=shutil.ignore_patterns('__pycache__'));return dst
 def manifest(self,p,fn):
  f=p/'EXPORT_ALLOWLIST.json';d=json.loads(f.read_text());fn(d);f.write_text(json.dumps(d))
 def test_exact_export(self):self.assertEqual(verify(),[])
 def test_export_mutations(self):
  cases={
  'extra_file':lambda p:(p/'publisher.pdf').write_bytes(b'not actual publisher bytes'),
  'missing_file':lambda p:(p/'README.md').unlink(),
  'changed_payload':lambda p:(p/'README.md').write_text('changed'),
  'duplicate_name':lambda p:self.manifest(p,lambda d:d['files'].append(d['files'][0])),
  'traversal':lambda p:self.manifest(p,lambda d:d['files'].append('../outside.json')),
  'absolute':lambda p:self.manifest(p,lambda d:d['files'].append('/outside.json')),
  'binary_allow':lambda p:self.manifest(p,lambda d:d['files'].append('source.mp4')),
  'actor_answer_leak':lambda p:self.manifest(p,lambda d:d['actor_file_allowlist'].append('source_outcomes.json')),
  'publisher_flag':lambda p:self.manifest(p,lambda d:d.update(publisher_files_included=True)),
  'missing_hash':lambda p:self.manifest(p,lambda d:d['payload_sha256'].pop('README.md')),
  'extra_hash':lambda p:self.manifest(p,lambda d:d['payload_sha256'].update(extra='0')),
  }
  for name,fn in cases.items():
   with self.subTest(case=name):p=self.clone();fn(p);self.assertTrue(verify(p))
 def test_symlink(self):
  p=self.clone();f=p/'README.md';f.unlink();f.symlink_to(p/'TASK_DESIGN.md');self.assertTrue(verify(p))
if __name__=='__main__':unittest.main()
