import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from semantic_controls import ReviewGuard,FORBIDDEN,ALLOWED_RECORD_KEYS
class GuardTests(unittest.TestCase):
 def test_initial_hold(self):
  g=ReviewGuard();self.assertEqual(g.state,'HOLD');self.assertFalse(g.energy_enabled);self.assertFalse(g.physical_execution);self.assertFalse(g.evidence_verified)
 def test_workflow_remains_disabled(self):
  g=ReviewGuard()
  for a,r in [('attach_record_labels',{'sample_id':'REF-001'}),('request_review',None),('clear_record_labels',None)]:
   s=g.apply(a,r);self.assertFalse(s['energy_enabled']);self.assertFalse(s['physical_execution']);self.assertFalse(s['evidence_verified']);self.assertFalse(s['safe_to_remove_sample'])
  self.assertEqual(g.state,'HOLD')
 def test_every_service_forbidden_in_every_state(self):
  for state in ['HOLD','RECORDS_ATTACHED','REVIEW_REQUESTED']:
   for a in FORBIDDEN:
    g=ReviewGuard()
    if state!='HOLD':g.apply('attach_record_labels',{'sample_id':'REF-001'})
    if state=='REVIEW_REQUESTED':g.apply('request_review')
    with self.assertRaises(PermissionError):g.apply(a)
    self.assertEqual(g.state,state)
 def test_no_request_becomes_observation(self):
  g=ReviewGuard();s=g.apply('attach_record_labels',{'isolation_record':'Actor says safe','thermal_record':'Requested cooldown'})
  self.assertFalse(s['evidence_verified']);self.assertFalse(s['safe_to_remove_sample']);self.assertFalse(g.energy_enabled)
 def test_labels_copied(self):
  labels={'sample_id':'A'};g=ReviewGuard();ret=g.apply('attach_record_labels',labels);labels['sample_id']='B';ret['record_labels']['sample_id']='C';self.assertEqual(g.record_labels,{'sample_id':'A'})
 def test_invalid_labels(self):
  for data in [None,{},[],{'unknown':'x'},{'sample_id':''},{'sample_id':' '*5},{'sample_id':False},{'sample_id':'x'*161}]:
   g=ReviewGuard()
   with self.assertRaises(ValueError):g.apply('attach_record_labels',data)
   self.assertEqual(g.state,'HOLD')
 def test_invalid_start(self):
  for kw in [{'state':'RUN'},{'record_labels':{'sample_id':'A'}}]:
   with self.assertRaises(ValueError):ReviewGuard(**kw)
 def test_unavailable_actions(self):
  for a in ['request_review','clear_record_labels','run','set_voltage','approve','',None,[]]:
   with self.assertRaises(ValueError):ReviewGuard().apply(a)
 def test_clear_after_labels(self):
  g=ReviewGuard();g.apply('attach_record_labels',{'sample_id':'A'});g.apply('clear_record_labels');self.assertEqual(g.state,'HOLD');self.assertEqual(g.record_labels,{})
 def test_cannot_set_enable_properties(self):
  g=ReviewGuard()
  for k in ['energy_enabled','physical_execution','evidence_verified']:
   with self.assertRaises(AttributeError):setattr(g,k,True)
if __name__=='__main__':unittest.main()
