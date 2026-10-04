"""Independent synthetic-contract regression tests; no apparatus execution."""
import sys, pathlib, unittest, copy
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from contract import fixture,validate,B

class IndependentAFMTests(unittest.TestCase):
 def test_baseline_all_branches(self): self.assertEqual(validate(*fixture(list(B))), [])
 def rejected(self, mutate):
  ctx,events=fixture(list(B));mutate(ctx,events);self.assertTrue(validate(ctx,events))
 def test_exchange_known_contact_rejected(self):
  for phase in ['DOCK','MOUNT']:
   with self.subTest(phase=phase):
    self.rejected(lambda c,e,p=phase:next(o for o in c['observations'].values() if o['phase']==p).__setitem__('contact_state','contact'))
 def test_exchange_unknown_contact_rejected(self):
  for phase in ['DOCK','MOUNT']:
   with self.subTest(phase=phase):
    self.rejected(lambda c,e,p=phase:next(o for o in c['observations'].values() if o['phase']==p).__setitem__('contact_state','unknown'))
 def test_exchange_nonstationary_rejected(self):
  self.rejected(lambda c,e:next(o for o in c['observations'].values() if o['phase']=='MOUNT').__setitem__('stationary',False))
 def test_sensor_release_false_rejected(self):
  self.rejected(lambda c,e:next(o for o in c['observations'].values() if o['phase'].startswith('VERIFY_RELEASE:')).__setitem__('force_release_measured',False))
 def test_cross_episode_field_rejected(self):
  self.rejected(lambda c,e:c['observations'][e[0]['event_id']].__setitem__('episode_id','other_episode'))
 def test_missing_terminal_cleanup_rejected(self):
  self.rejected(lambda c,e:e.pop())
 def test_actor_contact_assertion_rejected(self):
  self.rejected(lambda c,e:e[0].__setitem__('contact_state','released'))
 def test_context_episode_mismatch_rejected(self):
  self.rejected(lambda c,e:c.__setitem__('episode_id','other_episode'))
 def test_context_actor_target_leak_rejected(self):
  self.rejected(lambda c,e:c.__setitem__('actor_targets_exposed',True))
 def test_extra_execution_claim_rejected(self):
  self.rejected(lambda c,e:c.__setitem__('physical_execution',True))
 def test_card_type_rejected(self):
  self.rejected(lambda c,e:next(iter(c['cards'].values())).__setitem__('qualified_for_fixture_only',1))
 def test_fabrication_boolean_type_rejected(self):
  self.rejected(lambda c,e:c['input_qualification'].__setitem__('fabrication_performed',0))
 def test_specimen_version_boolean_type_rejected(self):
  def mutate(c,e):
   for j in c['jobs'].values():j['binding']['specimen_version']=True
   for o in c['observations'].values():o['binding']['specimen_version']=True
  self.rejected(mutate)
 def test_production_scope_rejected(self):
  self.rejected(lambda c,e:c.__setitem__('production_authority',True))
if __name__=='__main__':unittest.main(verbosity=2)
