import unittest
from semantic_controls import GuardedStaticScene, TestReceipt, GuardHold

class StaticGuardTests(unittest.TestCase):
    def scene(self,mode='analog',carrier=None,sensor='spatial-test-only'):
        s=GuardedStaticScene();r=TestReceipt('epoch-a',carrier,mode,sensor);s.configure(r)
        if carrier:
            s.record_safe_access(r);s.set_door(False);s.load(carrier,r);s.set_door(True)
        return s,r
    def test_default_physical_and_scientific_holds(self):
        s=GuardedStaticScene();self.assertFalse(s.outcome()['scientific_success']);self.assertEqual(s.outcome()['converted_paper_credit'],0)
        with self.assertRaises(GuardHold):s.physical_action('move_robot')
    def test_same_epoch_copper_static_example(self):
        s,r=self.scene(carrier='CU-E');s.reserve_acquisition('B02',r);self.assertEqual(s.lease,'acquisition:B02');s.release(r);self.assertFalse(s.energy_safe)
    def test_empty_mapping_needs_spatial_sensor(self):
        s,r=self.scene();s.reserve_acquisition('B01',r);s.release(r)
        s,r=self.scene(sensor=None)
        with self.assertRaises(GuardHold):s.reserve_acquisition('B01',r)
    def test_mapping_rejects_present_object(self):
        s,r=self.scene(carrier='CU-E')
        with self.assertRaises(GuardHold):s.reserve_acquisition('B01',r)
    def test_no_unqualified_or_stale_loading(self):
        s,r=self.scene()
        with self.assertRaises(GuardHold):s.load('CU-E',r)
        with self.assertRaises(GuardHold):s.record_safe_access(TestReceipt('old'))
    def test_load_identity_and_exclusive_occupancy(self):
        s,r=self.scene();s.record_safe_access(r);s.set_door(False)
        with self.assertRaises(GuardHold):s.load('CU-E',r)
        correct=TestReceipt('epoch-a','CU-E','analog');s.load('CU-E',correct)
        with self.assertRaises(GuardHold):s.load('CU-E',correct)
    def test_epoch_mode_change_invalidates_access(self):
        s,r=self.scene();s.record_safe_access(r);s.configure(TestReceipt('epoch-b',mode='photon_count'))
        self.assertFalse(s.energy_safe)
        with self.assertRaises(GuardHold):s.record_safe_access(r)
        with self.assertRaises(GuardHold):s.reserve_acquisition('B01',r)
    def test_exclusive_lease_blocks_reconfiguration_open_unload(self):
        s,r=self.scene(carrier='CU-E');s.reserve_acquisition('B02',r)
        for f in [lambda:s.configure(r),lambda:s.set_door(False),lambda:s.unload(r),lambda:s.record_safe_access(r),lambda:s.reserve_acquisition('B02',r)]:
            with self.assertRaises(GuardHold):f()
    def test_photon_branch_rejects_analog_epoch(self):
        s,r=self.scene(carrier='CU-E')
        for branch in ['B04','B05','B06','B07','B08']:
            with self.assertRaises(GuardHold):s.reserve_acquisition(branch,r)
    def test_silicon_branch_requires_separate_material(self):
        s,r=self.scene('photon_count','CU-E')
        with self.assertRaises(GuardHold):s.reserve_acquisition('B08',r)
        s,r=self.scene('photon_count','SI-STAR');s.reserve_acquisition('B08',r)
    def test_dynamic_plan_required(self):
        s,r=self.scene(carrier='CU-E')
        with self.assertRaises(GuardHold):s.reserve_acquisition('B03',r)
        s.reserve_acquisition('B03',r,dynamic_plan_id='TEST-PLAN',grid=(16,16),source_rate_hz=10)
    def test_rate_and_grid_nonconflation(self):
        for branch,mode,carrier,grid,hz in [('B04','photon_count','CU-E',(16,16),10),('B03','analog','CU-E',(32,32),10),('B02','analog','CU-E',(16,16),10)]:
            s,r=self.scene(mode,carrier)
            with self.assertRaises(GuardHold):s.reserve_acquisition(branch,r,dynamic_plan_id='TEST-PLAN',grid=grid,source_rate_hz=hz)
    def test_failure_retention_and_quarantine(self):
        s,r=self.scene(carrier='CU-E');s.reserve_acquisition('B02',r);s.release(r,failed=True,failure_id='TEST-FAIL')
        s.record_safe_access(r);s.set_door(False);s.unload(r);s.quarantine('CU-E')
        with self.assertRaises(GuardHold):s.load('CU-E',r)
        self.assertEqual(len(s.outcome()['failed_records']),1);self.assertGreater(len(s.history),7)
    def test_receipts_are_not_authenticated_real_evidence(self):
        s=GuardedStaticScene()
        with self.assertRaises(GuardHold):s.configure(TestReceipt('epoch',mode='analog',purpose='physical_qualified'))
        with self.assertRaises(GuardHold):s.configure({'epoch':'epoch','mode':'analog'})
    def test_unknown_identifiers_fail_closed(self):
        s,r=self.scene()
        with self.assertRaises(GuardHold):s.reserve_acquisition('B99',r)
        with self.assertRaises(GuardHold):s.configure(TestReceipt('epoch',mode='hybrid'))
        with self.assertRaises(GuardHold):s.quarantine('UNKNOWN')
    def test_epoch_cannot_be_recycled_for_new_mode(self):
        s,r=self.scene()
        with self.assertRaises(GuardHold):s.configure(TestReceipt('epoch-a',mode='photon_count'))
        self.assertEqual(s.mode,'analog')
    def test_loaded_quarantine_blocks_new_acquisition(self):
        s,r=self.scene(carrier='CU-E');s.quarantine('CU-E')
        with self.assertRaises(GuardHold):s.reserve_acquisition('B02',r)
    def test_release_requires_detector_and_carrier_identity(self):
        s,r=self.scene(carrier='CU-E');s.reserve_acquisition('B02',r)
        for wrong in [TestReceipt('epoch-a','CU-C','analog'),TestReceipt('epoch-a','CU-E','photon_count')]:
            with self.assertRaises(GuardHold):s.release(wrong)
        self.assertEqual(s.lease,'acquisition:B02');s.release(r)
    def test_unload_needs_fresh_access_after_acquisition(self):
        s,r=self.scene(carrier='CU-E');s.reserve_acquisition('B02',r);s.release(r)
        with self.assertRaises(GuardHold):s.set_door(False)
        s.record_safe_access(r);s.set_door(False);self.assertEqual(s.unload(r),'CU-E')

if __name__=='__main__':unittest.main()
