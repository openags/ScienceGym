import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from semantic_controls import ReviewGuard,FORBIDDEN
class GuardTests(unittest.TestCase):
 def test_initial_hold(self):
  g=ReviewGuard();self.assertEqual(g.state,'HOLD');self.assertFalse(g.energy_enabled);self.assertFalse(g.physical_execution)
 def test_initial_state_cannot_skip(self):
  with self.assertRaises(ValueError):ReviewGuard('REVIEW_REQUESTED')
 def test_initial_records_cannot_skip(self):
  with self.assertRaises(ValueError):ReviewGuard(record_labels={'sample_id':'test'})
 def test_empty_records_refused(self):
  with self.assertRaises(ValueError):ReviewGuard().apply('attach_record_labels',{})
 def test_nonmapping_refused(self):
  with self.assertRaises(ValueError):ReviewGuard().apply('attach_record_labels',['a'])
 def test_unknown_record_key_refused(self):
  with self.assertRaises(ValueError):ReviewGuard().apply('attach_record_labels',{'authorize':'yes'})
 def test_nonstring_record_refused(self):
  with self.assertRaises(ValueError):ReviewGuard().apply('attach_record_labels',{'sample_id':3})
 def test_empty_string_refused(self):
  with self.assertRaises(ValueError):ReviewGuard().apply('attach_record_labels',{'sample_id':' '})
 def test_overlong_refused(self):
  with self.assertRaises(ValueError):ReviewGuard().apply('attach_record_labels',{'sample_id':'x'*161})
 def test_labels_are_copied(self):
  d={'sample_id':'A'};g=ReviewGuard();g.apply('attach_record_labels',d);d['sample_id']='B';self.assertEqual(g.record_labels['sample_id'],'A')
 def test_review_cycle(self):
  g=ReviewGuard();g.apply('attach_record_labels',{'sample_id':'A'});r=g.apply('request_review');self.assertEqual(r['state'],'REVIEW_REQUESTED');self.assertFalse(r['evidence_verified']);self.assertFalse(r['physical_execution']);self.assertFalse(r['energy_enabled']);g.apply('clear_record_labels');self.assertEqual(g.state,'HOLD');self.assertEqual(g.record_labels,{})
 def test_cannot_review_before_records(self):
  with self.assertRaises(ValueError):ReviewGuard().apply('request_review')
 def test_all_physical_actions_refused_in_all_metadata_states(self):
  for state in ['HOLD','RECORDS_ATTACHED','REVIEW_REQUESTED']:
   g=ReviewGuard()
   if state!='HOLD':g.apply('attach_record_labels',{'sample_id':'A'})
   if state=='REVIEW_REQUESTED':g.apply('request_review')
   for action in FORBIDDEN:
    with self.subTest(state=state,action=action):
     with self.assertRaises(PermissionError):g.apply(action)
    self.assertFalse(g.energy_enabled);self.assertFalse(g.physical_execution)
 def test_unknown_action_refused(self):
  with self.assertRaises(ValueError):ReviewGuard().apply('override')
 def test_direct_caller_tampering_cannot_enable(self):
  g=ReviewGuard();g.state='APPROVED';g.record_labels['calibration_record']='fake';self.assertFalse(g.energy_enabled);self.assertFalse(g.physical_execution)
 def test_readonly_enable_flags(self):
  g=ReviewGuard()
  with self.assertRaises(AttributeError):g.energy_enabled=True
  with self.assertRaises(AttributeError):g.physical_execution=True
if __name__=='__main__':unittest.main()
