import sys,unittest,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from semantic_controls import *
def cards():return dict(specimen_id='A-001',specimen_version=1,design_id='GENERIC-1',carrier_id='C-1',fixture_id='F-1',camera_id='CAM-1',direction_card_id='DIR-1',direction_disposition='reviewed_orthogonal_branch',axis_map_id='AX-1',calibration_id='CAL-1',calibration_revision=1)
def ready():
 f=MetrologyFixture('A-001');f.register_cards(cards(),f.claim('cards_reviewed'));f.dock();f.fix_base(f.claim('base_fixed'));f.register_calibration(f.claim('calibration_registered'));return f
class Guards(unittest.TestCase):
 def test_identity(self):
  for x in [None,'',42]:
   with self.assertRaises(GuardError):MetrologyFixture(x)
 def test_version(self):
  for x in [0,-1,True,1.0]:
   with self.assertRaises(GuardError):MetrologyFixture('A',x)
 def test_default_hold(self):
  f=MetrologyFixture('A-001')
  with self.assertRaises(GuardError):f.dock()
 def test_lifecycle(self):
  f=ready();f.register_before('IM-0','RUN-1',f.claim('before_image_registered'));f.register_input(f.claim('input_verified'));f.register_after('IM-1','RUN-1',f.claim('after_image_registered'));m=f.pair_manifest();self.assertIsNone(m['efficiency']);self.assertIsNone(m['displacements']);self.assertFalse(m['physical_execution']);f.release_intent();f.verify_unloaded(f.claim('unloaded_verified'));f.unfix();f.retrieve();f.inspect(f.claim('inspection_registered'));self.assertEqual(f.snapshot()['state'],'CUSTODY')
 def test_wrong_instance(self):
  f=MetrologyFixture('A-001');g=MetrologyFixture('A-001')
  with self.assertRaises(GuardError):f.register_cards(cards(),g.claim('cards_reviewed'))
 def test_stale(self):
  f=MetrologyFixture('A-001');c=f.claim('cards_reviewed');f.register_cards(cards(),c)
  with self.assertRaises(GuardError):f.register_cards(cards(),c)
 def test_incomplete_cards(self):
  for key in cards():
   f=MetrologyFixture('A-001');d=cards();del d[key]
   with self.assertRaises(GuardError):f.register_cards(d,f.claim('cards_reviewed'))
 def test_acknowledgement_not_disposition(self):
  for val in ['acknowledged','default','orthogonal',None]:
   f=MetrologyFixture('A-001');d=cards();d['direction_disposition']=val
   with self.assertRaises(GuardError):f.register_cards(d,f.claim('cards_reviewed'))
 def test_card_identity(self):
  f=MetrologyFixture('A-001');d=cards();d['specimen_id']='OTHER'
  with self.assertRaises(GuardError):f.register_cards(d,f.claim('cards_reviewed'))
 def test_wrong_claim_kind(self):
  f=ready()
  with self.assertRaises(GuardError):f.register_before('I','R',f.claim('after_image_registered'))
 def test_run_binding(self):
  f=ready();f.register_before('I','R',f.claim('before_image_registered'));f.register_input(f.claim('input_verified'))
  for i,r in [('I','R'),('J','OTHER'),('','R')]:
   with self.assertRaises(GuardError):f.register_after(i,r,f.claim('after_image_registered'))
 def test_pair_before_input(self):
  f=ready();f.register_before('I','R',f.claim('before_image_registered'))
  with self.assertRaises(GuardError):f.register_after('J','R',f.claim('after_image_registered'))
 def test_no_unfix_on_intent(self):
  f=ready();f.register_before('I','R',f.claim('before_image_registered'));f.register_input(f.claim('input_verified'));f.release_intent()
  with self.assertRaises(GuardError):f.unfix()
 def test_stale_unloaded(self):
  f=ready();c=f.claim('unloaded_verified');f.register_before('I','R',f.claim('before_image_registered'));f.register_input(f.claim('input_verified'));f.release_intent()
  with self.assertRaises(GuardError):f.verify_unloaded(c)
 def test_defensive_copy(self):
  f=ready();s=f.snapshot();s['cards']['camera_id']='BAD';self.assertEqual(f.snapshot()['cards']['camera_id'],'CAM-1')
 def test_physical_rejected(self):
  f=ready()
  for op in ['REQUEST_INPUT','RELEASE_INPUT','CAPTURE_BEFORE','CAPTURE_AFTER','REQUEST_FABRICATION','REQUEST_DEM','REQUEST_FEM','REQUEST_CNN','MEASURE_NODES','COMPUTE_EFFICIENCY']:
   with self.assertRaises(PhysicalExecutionUnavailable):f.request_physical_service(op)
 def test_quarantine_terminal(self):
  f=ready();f.quarantine()
  with self.assertRaises(GuardError):f.dock()
 def test_invalid_claim_types(self):
  f=MetrologyFixture('A-001')
  for kind in [None,[],{},1,'not_a_kind']:
   with self.assertRaises(GuardError):f.claim(kind)
 def test_invalid_card_types(self):
  for key in cards():
   for bad in [[],{},True]:
    f=MetrologyFixture('A-001');d=cards();d[key]=bad
    with self.assertRaises(GuardError):f.register_cards(d,f.claim('cards_reviewed'))
 def test_invalid_image_types(self):
  for bad in [[],{},True,None,' ']:
   f=ready()
   with self.assertRaises(GuardError):f.register_before(bad,'R',f.claim('before_image_registered'))
 def test_rejected_action_atomic(self):
  f=ready();before=f.snapshot();c=f.claim('before_image_registered')
  with self.assertRaises(GuardError):f.register_before('', 'R',c)
  self.assertEqual(before,f.snapshot());f.register_before('I','R',c)
 def test_conflicts_never_resolved(self):self.assertFalse(ready().snapshot()['source_conflicts_resolved'])
if __name__=='__main__':unittest.main()
