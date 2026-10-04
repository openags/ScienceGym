import unittest,json,pathlib,sys,struct,math
P=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
from semantic_controls import State,transition
class Package(unittest.TestCase):
 def load(self,n):return json.loads((P/n).read_text())
 def test_ids_and_bindings(self):
  inv=self.load('asset_inventory.json');a={x['asset_id']:x for x in inv['assets']};self.assertEqual(len(a),len(inv['assets']))
  b=self.load('operation_bindings.json');allowed=set(b['allowed_operation_ids'])
  for x in b['bindings']:
   self.assertIn(x['asset_id'],a);self.assertTrue(set(x['operation_ids'])<=allowed)
 def test_units_transforms(self):
  inv=self.load('asset_inventory.json');self.assertEqual(inv['units'],'metres')
  for a in inv['assets']:
   for p in a['parts']:
    self.assertTrue(all(math.isfinite(x) for x in p['translation_m']+p['dimensions_m']+p['scale']))
    self.assertTrue(all(x>0 for x in p['scale']))
    self.assertAlmostEqual(sum(q*q for q in p['rotation_quaternion_xyzw']),1,places=5)
 def test_sources_and_scale(self):
  m=self.load('asset_metadata.json');self.assertIsNone(m['scale']['whole_array_span_m']);self.assertFalse(m['scale']['C_SCALE']['resolved'])
  c=m['configurations'];self.assertEqual(c[0]['numerical_aperture'],.28);self.assertIsNone(c[1]['numerical_aperture']);self.assertNotEqual(c[0]['id'],c[1]['id'])
  self.assertFalse(m['readiness']['physical_execution_implemented']);self.assertFalse(m['readiness']['calibration_execution_implemented'])
 def test_glb_actual(self):
  for fn in ['afm_operations_lab.glb','afm_magnified_explainer.glb']:
   b=(P/'geometry'/fn).read_bytes();magic,ver,total=struct.unpack_from('<III',b);self.assertEqual(magic,0x46546c67);self.assertEqual(ver,2);self.assertEqual(total,len(b))
   n,t=struct.unpack_from('<II',b,12);d=json.loads(b[20:20+n]);self.assertTrue(d['meshes']);self.assertTrue(d['nodes']);self.assertNotIn('images',d)
 def test_real_pngs(self):
  for v in ['overview','equipment_closeup','sample_handling']:
   b=(P/'evidence'/(v+'.png')).read_bytes();self.assertEqual(b[:8],b'\x89PNG\r\n\x1a\n');w,h=struct.unpack('>II',b[16:24]);self.assertGreaterEqual(w,1400);self.assertGreaterEqual(h,900)
 def test_valid_state_sequence(self):
  s=State()
  for e in ['open_clamp','grasp_carrier','dock_carrier','close_clamp','illustrative_contact','release','lateral_step']:s=transition(s,e)
  self.assertEqual(s.carrier,'docked');self.assertFalse(s.physical_calibration_valid)
 def test_unsafe_states_rejected(self):
  with self.assertRaises(ValueError):transition(State(),'grasp_carrier')
  with self.assertRaises(ValueError):transition(State(contact='illustrative_contact'),'lateral_step')
  with self.assertRaises(ValueError):transition(State(carrier='held',clamp='open'),'close_clamp')
  with self.assertRaises(ValueError):transition(State(),'run_calibration')
 def test_optics_invalidate(self):
  s=transition(State(),'CFG_CHARACTERIZATION_OLYMPUS');self.assertEqual(s.configuration_revision,2);self.assertFalse(s.physical_calibration_valid)
 def test_allowlist(self):
  a=self.load('EXPORT_ALLOWLIST.json')['files']
  for n in a:
   self.assertTrue((P/n).is_file(),n);self.assertNotIn('..',pathlib.Path(n).parts);self.assertFalse(n.endswith(('.pdf','.html','.blend1')))
  self.assertFalse(any('source' in x.lower() and x.endswith('.png') for x in a))
if __name__=='__main__':unittest.main(verbosity=2)
