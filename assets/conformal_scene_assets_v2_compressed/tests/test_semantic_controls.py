import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from semantic_controls import StaticSceneGuard, GuardRejected, analysis_guard

FIELDS={'mechanics':['commissioned_limits','calibrated_loadcell','contact_zero','fixture_locked','safe_stop_policy'],'camera':['scale_distortion','focus_visibility','reference_frame','pad_identity_mask'],'sync':['clock_mapping','capture_ready','buffer_ready','load_unload_tags'],'plan':['frozen_repeat_policy','order_policy','recovery_policy','stopping_policy']}
def prepared():
 g=StaticSceneGuard();g.prepare(specimen='sample1',geometry_revision='illustration1',build_receipt='test-build',fixture_receipt='test-fixture',treatment_revision='none');return g
def docked():
 g=prepared();g.dock(specimen='sample1',carrier='carrier1',branch='B02',grasp_zone='carrier.handle_left',supported=True);return g
def qualify(g):
 for kind,fields in FIELDS.items():g.record_test_receipt(kind=kind,specimen=g.specimen,carrier=g.carrier,branch=g.branch,epoch=g.epoch,test_only=True,fields={x:True for x in fields})
 return g
class Guards(unittest.TestCase):
 def test_initial_state(self):self.assertFalse(StaticSceneGuard().physical_execution_enabled)
 def test_hardware_always_rejected(self):
  for g in [StaticSceneGuard(),qualify(docked())]:
   with self.assertRaises(GuardRejected):g.execute_physical('move')
 def test_unprepared_dock(self):
  with self.assertRaises(GuardRejected):StaticSceneGuard().dock(specimen='s',carrier='c',branch='B02',grasp_zone='carrier.handle_left',supported=True)
 def test_bad_grasps(self):
  for zone in ['hinge','pad','beam','free','']:
   with self.subTest(zone=zone),self.assertRaises(GuardRejected):prepared().dock(specimen='sample1',carrier='c',branch='B02',grasp_zone=zone,supported=True)
 def test_wrong_identity_and_branch_and_support(self):
  for change in [{'specimen':'wrong'},{'branch':'B08'},{'supported':False},{'carrier':''}]:
   kw=dict(specimen='sample1',carrier='c',branch='B02',grasp_zone='carrier.handle_left',supported=True);kw.update(change)
   with self.subTest(change=change),self.assertRaises(GuardRejected):prepared().dock(**kw)
 def test_unknown_treatment(self):
  with self.assertRaises(GuardRejected):StaticSceneGuard().prepare(specimen='s',geometry_revision='g',build_receipt='b',fixture_receipt='f',treatment_revision='unknown powder')
 def test_leased_dock(self):
  g=docked()
  with self.assertRaises(GuardRejected):g.dock(specimen='sample1',carrier='c2',branch='B02',grasp_zone='carrier.handle_left',supported=True)
 def test_bad_receipts(self):
  for delta in [{'specimen':'wrong'},{'carrier':'wrong'},{'branch':'B03'},{'epoch':0},{'test_only':False},{'fields':{}},{'kind':'source_stroke'}]:
   g=docked();kw=dict(kind='mechanics',specimen=g.specimen,carrier=g.carrier,branch=g.branch,epoch=g.epoch,test_only=True,fields={x:True for x in FIELDS['mechanics']});kw.update(delta)
   with self.subTest(delta=delta),self.assertRaises(GuardRejected):g.record_test_receipt(**kw)
 def test_missing_qualifications(self):
  with self.assertRaises(GuardRejected):docked().arm_static(run_id='r1',visual_guard_closed=True)
 def test_open_guard(self):
  with self.assertRaises(GuardRejected):qualify(docked()).arm_static(run_id='r1',visual_guard_closed=False)
 def test_nominal_never_permission(self):
  g=qualify(docked());self.assertFalse(g.arm_static(run_id='r1',visual_guard_closed=True)['physical_permission']);self.assertFalse(g.physical_execution_enabled)
 def test_unsafe_finish(self):
  for kwargs in [{'unloaded':False,'disarmed':True},{'unloaded':True,'disarmed':False}]:
   g=qualify(docked());g.arm_static(run_id='r1',visual_guard_closed=True)
   with self.assertRaises(GuardRejected):g.finish_static(**kwargs,recovery_ok=True)
 def test_repeat_requires_requalify(self):
  g=qualify(docked());g.arm_static(run_id='r1',visual_guard_closed=True);g.finish_static(unloaded=True,disarmed=True,recovery_ok=True)
  with self.assertRaises(GuardRejected):g.arm_static(run_id='r2',visual_guard_closed=True)
 def test_repeated_id(self):
  g=qualify(docked());g.arm_static(run_id='r1',visual_guard_closed=True);g.finish_static(unloaded=True,disarmed=True,recovery_ok=True);qualify(g)
  with self.assertRaises(GuardRejected):g.arm_static(run_id='r1',visual_guard_closed=True)
 def test_fixture_change_resets(self):
  g=qualify(docked());g.arm_static(run_id='r1',visual_guard_closed=True);g.finish_static(unloaded=True,disarmed=True,recovery_ok=True);r=g.change_fixture(next_branch='B03',specimen='sample1',treatment_revision='none');self.assertFalse(g.docked);self.assertEqual(g.receipts,{});self.assertFalse(r['physical_permission'])
 def test_replacement_invalidates_preparation(self):
  g=docked();g.change_fixture(next_branch='B03',specimen='sample2',treatment_revision='none')
  with self.assertRaises(GuardRejected):g.dock(specimen='sample2',carrier='c',branch='B03',grasp_zone='carrier.handle_left',supported=True)
 def test_treatment_invalidates_preparation(self):
  g=docked();self.assertTrue(g.change_fixture(next_branch='B03',specimen='sample1',treatment_revision='changed')['preparation_reentry_required'])
 def test_armed_fixture_change(self):
  g=qualify(docked());g.arm_static(run_id='r1',visual_guard_closed=True)
  with self.assertRaises(GuardRejected):g.change_fixture(next_branch='B03',specimen='sample1',treatment_revision='none')
 def test_recovery_quarantine(self):
  g=qualify(docked());g.arm_static(run_id='r1',visual_guard_closed=True);g.finish_static(unloaded=True,disarmed=True,recovery_ok=False)
  with self.assertRaises(GuardRejected):g.closeout(safe_state_receipt=True,disposition='storage')
 def test_fault_retains_evidence(self):
  g=qualify(docked());g.fault('sync lost');self.assertFalse(g.unloaded);self.assertTrue(g.events)
  with self.assertRaises(GuardRejected):g.arm_static(run_id='r1',visual_guard_closed=True)
  with self.assertRaises(GuardRejected):g.closeout(safe_state_receipt=False,disposition='quarantine')
  self.assertFalse(g.closeout(safe_state_receipt=True,disposition='quarantine')['scientific_validation'])
 def test_analysis_guards(self):
  base=dict(mode='boundary_inference',physical_or_numerical='physical',interior_targets_used=False,det_f_positive=True,global_injectivity_verified=False,normalization_nonzero=True,closed_boundary=True,conventions_reviewed=True,source_conflicts_resolved=True)
  for k,v in [('interior_targets_used',True),('det_f_positive',False),('normalization_nonzero',False),('closed_boundary',False),('conventions_reviewed',False),('source_conflicts_resolved',False),('physical_or_numerical','mixed')]:
   with self.subTest(k=k),self.assertRaises(GuardRejected):analysis_guard(**{**base,k:v})
  self.assertEqual(analysis_guard(**base)['global_geometry_status'],'unverified');self.assertFalse(analysis_guard(**base)['scientific_success'])
if __name__=='__main__':unittest.main()
