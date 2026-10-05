"""Regression tests for full-buffer privacy cleanup; fixtures are mutated in memory."""
from pathlib import Path
import sys,tempfile,unittest,zstandard,hashlib,subprocess,shutil
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'geometry'))
from deep_native_buffers import decoded,arrays,inspect,clean,STRING_FIELDS
class DeepBufferTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.native=P/'geometry/qha_lab.blend';cls.raw,cls.data=decoded(cls.native);cls.fields,_=arrays(cls.data)
 def field(self,typ,name):return next(x for x in self.fields if x['declaring_struct']==typ and x['base_name']==name)
 def temporary(self):
  t=tempfile.TemporaryDirectory();root=Path(t.name);(root/'geometry').mkdir();(root/'previews').mkdir();return t,root
 def mutate(self,field,payload):
  b=bytearray(self.data);b[field['start']:field['end']]=payload+bytes(field['size']-len(payload));return bytes(b)
 def save(self,p,data):p.write_bytes(zstandard.ZstdCompressor().compress(data))
 def test_01_scans_all_buffers(self):self.assertEqual(inspect(self.native,P)['fixed_char_arrays_checked'],6055)
 def test_02_zero_nonzero_tails(self):self.assertEqual(inspect(self.native,P)['fields_with_nonzero_tail'],0)
 def test_03_no_path_issues(self):self.assertEqual(inspect(self.native,P)['path_issues'],[])
 def test_04_no_unsupported_layouts(self):self.assertEqual(inspect(self.native,P)['unsupported_layouts'],[])
 def test_05_no_unclassified_tails(self):self.assertEqual(inspect(self.native,P)['unclassified_nonzero_tails'],[])
 def test_06_source_output_must_differ(self):
  with self.assertRaises(ValueError):clean(self.native,self.native,P)
 def test_07_directory_entire_buffer_canonicalized(self):
  field=self.field('FileSelectParams','dir');data=self.mutate(field,b'//\0TAIL_SENTINEL')
  with self.temporary()[0] as temp:
   root=Path(temp);(root/'geometry').mkdir(exist_ok=True);src=root/'geometry/in.blend';dst=root/'geometry/out.blend';self.save(src,data);r=clean(src,dst,root);out=decoded(dst)[1];self.assertEqual(out[field['start']:field['end']],b'//'+bytes(field['size']-2));self.assertTrue(r['bytes_outside_declared_buffers_identical'])
 def test_08_file_entire_buffer_canonicalized(self):
  field=self.field('FileSelectParams','file');data=self.mutate(field,b'\0TAIL_SENTINEL')
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'geometry').mkdir();src=root/'geometry/in.blend';dst=root/'geometry/out.blend';self.save(src,data);clean(src,dst,root);self.assertEqual(decoded(dst)[1][field['start']:field['end']],bytes(field['size']))
 def test_09_sequencer_directory_reset(self):
  field=self.field('Editing','act_imagedir');data=self.mutate(field,b'//'+b'../'*4+b'UNQUALIFIED_LOCATION/')
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'geometry').mkdir();src=root/'geometry/in.blend';dst=root/'geometry/out.blend';self.save(src,data);self.assertFalse(inspect(src,root)['strict_path_privacy_pass']);clean(src,dst,root);self.assertEqual(decoded(dst)[1][field['start']:field['end']],b'//'+bytes(field['size']-2))
 def test_10_unsupported_header_fails(self):
  with tempfile.TemporaryDirectory() as temp:
   src=Path(temp)/'bad.blend';src.write_bytes(b'INVALID');
   with self.assertRaises(ValueError):decoded(src)
 def test_11_unknown_tails_fail_closed(self):
  field=next(x for x in self.fields if x['base_name'] not in STRING_FIELDS.get(x['declaring_struct'],set()) and self.data[x['start']:x['end']].find(b'\0')<x['size']-8)
  block=bytearray(self.data[field['start']:field['end']]);i=block.find(b'\0');block[i+1:i+5]=b'TEST';data=self.mutate(field,bytes(block))
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'geometry').mkdir();src=root/'geometry/in.blend';dst=root/'geometry/out.blend';self.save(src,data)
   with self.assertRaises(ValueError):clean(src,dst,root)
   self.assertFalse(dst.exists())
 def test_12_bad_non_ui_path_preserves_existing_destination(self):
  field=self.field('RenderData','pic');data=self.mutate(field,b'//'+b'../'*4+b'UNQUALIFIED_OUTPUT/')
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'geometry').mkdir();src=root/'geometry/in.blend';dst=root/'geometry/out.blend';self.save(src,data);dst.write_bytes(b'KEEP_EXISTING_BYTES')
   with self.assertRaises(ValueError):clean(src,dst,root)
   self.assertEqual(dst.read_bytes(),b'KEEP_EXISTING_BYTES')
 def test_13_clean_is_idempotent(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'geometry').mkdir();src=root/'geometry/in.blend';dst=root/'geometry/out.blend';src.write_bytes(self.raw);r=clean(src,dst,root);self.assertEqual(r['changed_buffer_count'],0);self.assertEqual(dst.read_bytes(),self.raw)
 def test_14_no_buffer_contents_in_public_report(self):
  r=inspect(self.native,P);self.assertTrue(r['contents_redacted']);self.assertTrue(all('active_value_escaped' not in x and 'nonzero_tail_escaped' not in x for x in r['fields']))
 def test_15_known_render_path_preserved(self):
  f=self.field('RenderData','pic');self.assertEqual(self.data[f['start']:f['end']].split(b'\0',1)[0],b'//../previews/preview_01_overview.png')
 def test_16_source_size_preserved(self):self.assertEqual(len(self.data),2464528)
 def test_17_finalizer_wrapper_preserves_clean_bytes(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'geometry').mkdir();(root/'review').mkdir();(root/'previews').mkdir()
   for n in ['qha_lab.blend','deep_native_buffers.py','finalize_native_buffers.py']:shutil.copyfile(P/'geometry'/n,root/'geometry'/n)
   subprocess.run([sys.executable,str(root/'geometry/finalize_native_buffers.py')],check=True,capture_output=True)
   self.assertEqual((root/'geometry/qha_lab.blend').read_bytes(),self.raw)
if __name__=='__main__':unittest.main(verbosity=2)
