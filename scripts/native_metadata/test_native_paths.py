from pathlib import Path
import copy,json,tempfile,unittest,subprocess,sys,os,runpy,types
from unittest import mock
from maintain_native_paths import ALLOWLIST,clean,rewrite
from sdna_buffers import arrays,decoded,sha
BASE=Path(__file__).resolve().parents[2]
RECEIPTS=BASE/'docs/maintenance/native_metadata_20261005'
class MaintenanceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.policies=json.loads((RECEIPTS/'path_policy.json').read_text())
  cls.current={r['path']:r for r in json.loads((RECEIPTS/'native_hashes.json').read_text())['files']}
  cls.path=BASE/next(iter(cls.policies));cls.raw,cls.data=decoded(cls.path);cls.fields,_=arrays(cls.data)
 def test_all_fourteen_current_native_outputs(self):
  self.assertEqual(len(self.policies),14)
  for rel,p in self.policies.items():
   with self.subTest(path=rel):
    raw,data=decoded(BASE/rel)
    self.assertEqual(sha(raw),self.current[rel]['destination_sha256'])
    twice,report=rewrite(data)
    self.assertEqual(twice,data);self.assertEqual(report['changed_buffer_count'],0)
    self.assertTrue(report['bytes_outside_changed_allowlisted_buffers_identical'])
 def test_refuses_in_place_change(self):
  with self.assertRaises(ValueError):clean(self.path,self.path,sha(self.raw))
 def test_refuses_stale_source_pin(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'new.blend'
   with self.assertRaises(ValueError):clean(self.path,p,'0'*64)
   self.assertFalse(p.exists())
 def test_refuses_existing_candidate(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'existing.blend';p.write_bytes(b'keep')
   with self.assertRaises(FileExistsError):clean(self.path,p,sha(self.raw))
   self.assertEqual(p.read_bytes(),b'keep')
 def test_unterminated_target_fails_closed(self):
  f=next(x for x in self.fields if (x['declaring_struct'],x['base_name']) in ALLOWLIST)
  b=bytearray(self.data);b[f['start']:f['end']]=b'x'*f['size']
  with self.assertRaises(ValueError):rewrite(bytes(b))
 def test_unapproved_absolute_render_fails_closed(self):
  f=next(x for x in self.fields if (x['declaring_struct'],x['base_name'])==('RenderData','pic'))
  b=bytearray(self.data);v=b'/unapproved-output/';b[f['start']:f['end']]=v+bytes(f['size']-len(v))
  with self.assertRaises(ValueError):rewrite(bytes(b))
 def test_non_path_name_tail_preserved(self):
  f=next(x for x in self.fields if x['declaring_struct']=='ID' and x['base_name']=='name')
  b=bytearray(self.data);b[f['end']-2]=ord('Z')
  new,_=rewrite(bytes(b))
  self.assertEqual(new[f['start']:f['end']],b[f['start']:f['end']])
 def test_unsupported_header_fails_closed(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'bad.blend';p.write_bytes(b'not a native file')
   with self.assertRaises(ValueError):clean(p,Path(d)/'out.blend',sha(p.read_bytes()))
 def test_truncated_block_fails_closed(self):
  with self.assertRaises(ValueError):rewrite(self.data[:-5])
 def test_destination_appearing_after_preflight_is_not_overwritten(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);source=d/'source.blend';source.write_bytes(self.raw);destination=d/'output.blend';real_link=os.link
   def appeared(temporary,target):
    Path(target).write_bytes(b'appeared-after-preflight')
    return real_link(temporary,target)
   with mock.patch('maintain_native_paths.os.link',side_effect=appeared):
    with self.assertRaises(FileExistsError):clean(source,destination,sha(self.raw))
   self.assertEqual(source.read_bytes(),self.raw);self.assertEqual(destination.read_bytes(),b'appeared-after-preflight');self.assertEqual(list(d.glob('.metadata-*')),[])
 def test_cli_report_path_guards(self):
  script=Path(__file__).with_name('maintain_native_paths.py')
  for kind in ['source','destination','existing','symlink','hardlink','missing_parent']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as d:
    d=Path(d);source=d/'source.blend';source.write_bytes(self.raw);destination=d/'output.blend';report=d/'report.json';saved=None
    if kind=='source':report=source
    elif kind=='destination':report=destination
    elif kind=='existing':report.write_bytes(b'preserve-report');saved=report.read_bytes()
    elif kind=='symlink':report.symlink_to(source)
    elif kind=='hardlink':os.link(source,report)
    elif kind=='missing_parent':report=d/'missing'/'report.json'
    z=subprocess.run([sys.executable,'-B',str(script),str(source),str(destination),'--expected-sha256',sha(self.raw),'--report',str(report)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    self.assertNotEqual(z.returncode,0);self.assertEqual(source.read_bytes(),self.raw);self.assertFalse(destination.exists())
    if saved is not None:self.assertEqual(report.read_bytes(),saved)
 def test_cli_separate_report_success(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);source=d/'source.blend';source.write_bytes(self.raw);destination=d/'output.blend';report=d/'report.json'
   z=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('maintain_native_paths.py')),str(source),str(destination),'--expected-sha256',sha(self.raw),'--report',str(report)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   self.assertEqual(z.returncode,0,z.stderr.decode());self.assertEqual(source.read_bytes(),self.raw);self.assertTrue(json.loads(report.read_text())['passed']);self.assertEqual(decoded(destination)[1],self.data)
 def test_snapshot_output_guards_precede_native_loading(self):
  script=Path(__file__).with_name('native_semantic_snapshot.py')
  for kind in ['source','existing','symlink','hardlink','missing_parent']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as d:
    d=Path(d);source=d/'source.blend';source.write_bytes(self.raw);output=d/'snapshot.json'
    if kind=='source':output=source
    elif kind=='existing':output.write_bytes(b'preserve-snapshot')
    elif kind=='symlink':output.symlink_to(source)
    elif kind=='hardlink':os.link(source,output)
    elif kind=='missing_parent':output=d/'missing'/'snapshot.json'
    before=output.read_bytes() if output.exists() else None
    native_loader=mock.Mock(side_effect=AssertionError('Native loading must not begin for an invalid output'))
    fake=types.SimpleNamespace(ops=types.SimpleNamespace(wm=types.SimpleNamespace(open_mainfile=native_loader)))
    with mock.patch.dict(sys.modules,{'bpy':fake}),mock.patch.object(sys,'argv',[str(script),'--',str(source),str(output)]):
     with self.assertRaises((ValueError,FileExistsError)):runpy.run_path(str(script),run_name='__main__')
    native_loader.assert_not_called();self.assertEqual(source.read_bytes(),self.raw)
    if before is not None:self.assertEqual(output.read_bytes(),before)
if __name__=='__main__':unittest.main(verbosity=2)
