import unittest,sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from semantic_controls import ReviewGuard,SCENE_STATES,VIEWS,FORBIDDEN,RECORD_KEYS
class Controls(unittest.TestCase):
 def test_all_preview_states_passive_and_closeable(self):
  for s in SCENE_STATES:
   g=ReviewGuard();r=g.apply('preview_scene_state',value=s);self.assertEqual(r['preview_state'],s)
   for k in ['physical_execution','energy_enabled','evidence_verified','safe_to_remove_sample','scientific_success']:self.assertIs(r[k],False)
   self.assertEqual(g.apply('request_safe_close')['review_state'],'SAFE_CLOSE_REVIEW_REQUESTED')
 def test_all_views(self):
  for v in VIEWS:self.assertEqual(ReviewGuard().apply('select_view',value=v)['view'],v)
 def test_labels_do_not_become_evidence(self):
  g=ReviewGuard();g.apply('attach_record_labels',records={k:'unverified-reference' for k in RECORD_KEYS});r=g.apply('request_review');self.assertEqual(r['review_state'],'REVIEW_REQUESTED');self.assertFalse(r['evidence_verified']);self.assertFalse(g.safe_to_remove_sample)
  with self.assertRaises(TypeError):g.record_labels['age_record']='forged'
  g.apply('clear_record_labels');self.assertEqual(g.review_state,'HOLD')
 def test_forbidden_actions(self):
  for a in FORBIDDEN:
   with self.subTest(action=a),self.assertRaises(PermissionError):ReviewGuard().apply(a)
 def test_no_actor_authority_fields(self):
  for k in ['success','qualified','age_weeks','safe_to_remove','humidity','voltage','calibration_valid','raw_values','force','timestamp']:
   with self.subTest(key=k),self.assertRaises(ValueError):ReviewGuard().apply('attach_record_labels',records={k:'true'})
 def test_malformed_record_labels(self):
  for v in [None,True,1,0.5,math.nan,math.inf,[],{},'', ' ', 'x'*161,'bad\nvalue']:
   with self.subTest(value=v),self.assertRaises(ValueError):ReviewGuard().apply('attach_record_labels',records={'sample_id':v})
  for r in [None,{},[],True,1,'forged']:
   with self.subTest(records=r),self.assertRaises(ValueError):ReviewGuard().apply('attach_record_labels',records=r)
 def test_bad_transitions_and_fields(self):
  for a in [None,True,1,{},'declare_evidence','../control','VERIFY','']:
   with self.subTest(action=a),self.assertRaises(ValueError):ReviewGuard().apply(a)
  with self.assertRaises(ValueError):ReviewGuard().apply('request_review')
  for a in ['request_review','clear_record_labels','request_safe_close']:
   with self.subTest(action=a),self.assertRaises(ValueError):ReviewGuard().apply(a,records={'isolation_record':'claim'})
  for v in [True,None,'qualified',[],float('nan')]:
   with self.subTest(value=v),self.assertRaises(ValueError):ReviewGuard().apply('preview_scene_state',value=v)
 def test_held_initialization(self):
  for kw in [{'review_state':'SUCCESS'},{'preview_state':'mounted'},{'view':'dimensions'},{'_labels':{'sample_id':'forged'}}]:
   with self.assertRaises(ValueError):ReviewGuard(**kw)
 def test_physical_flags_readonly(self):
  g=ReviewGuard()
  for k in ['physical_execution','energy_enabled','evidence_verified','safe_to_remove_sample']:
   with self.assertRaises(AttributeError):setattr(g,k,True)
  g.review_state='SUCCESS';g.preview_state='qualified_patterned';self.assertFalse(g.physical_execution);self.assertFalse(g.evidence_verified)
 def test_mutable_input_is_copied(self):
  d={'sample_id':'old'};g=ReviewGuard();g.apply('attach_record_labels',records=d);d['sample_id']='mutated';self.assertEqual(g.record_labels['sample_id'],'old')
if __name__=='__main__':unittest.main()
