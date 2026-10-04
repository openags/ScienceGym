"""Independent semantic-only negative controls. No scene mutation or device access."""
import copy
import unittest
from semantic_controls import GuardedStaticScene, TestReceipt, GuardHold

class IndependentGuardAudit(unittest.TestCase):
    def setup_scene(self,mode='analog',carrier='CU-E',sensor='spatial-test-only'):
        s=GuardedStaticScene();r=TestReceipt('e1',carrier,mode,sensor);s.configure(r)
        if carrier:
            s.record_safe_access(r);s.set_door(False);s.load(carrier,r);s.set_door(True)
        return s,r
    def reject_unchanged(self,s,f):
        before=copy.deepcopy(s.__dict__)
        with self.assertRaises(GuardHold):f()
        self.assertEqual(s.__dict__,before,'Rejected semantic action changed ledger state')
    def test_all_branch_positive_fixtures_remain_nonphysical(self):
        for i in range(1,9):
            b=f'B{i:02}';mode='analog' if i<4 else 'photon_count';carrier=None if i==1 else 'SI-STAR' if i==8 else 'CU-E'
            with self.subTest(branch=b):
                s,r=self.setup_scene(mode,carrier);s.reserve_acquisition(b,r,dynamic_plan_id='TEST-ONLY')
                self.assertEqual(s.lease,'acquisition:'+b)
                self.assertFalse(s.outcome()['physical_execution_enabled']);self.assertFalse(s.outcome()['scientific_success'])
                s.release(r);self.assertIsNone(s.lease);self.assertFalse(s.energy_safe)
    def test_wrong_branch_mode_material_matrix_is_atomic(self):
        for b in ['B02','B03','B04','B05','B06','B07','B08']:
            for mode in ['analog','photon_count']:
                for carrier in ['CU-E','SI-STAR','BLANK','REFERENCE',None]:
                    allowed= (b in {'B02','B03'} and mode=='analog' and carrier=='CU-E') or (b in {'B04','B05','B06','B07'} and mode=='photon_count' and carrier=='CU-E') or (b=='B08' and mode=='photon_count' and carrier=='SI-STAR')
                    if allowed:continue
                    with self.subTest(branch=b,mode=mode,carrier=carrier):
                        s,r=self.setup_scene(mode,carrier);self.reject_unchanged(s,lambda:s.reserve_acquisition(b,r,dynamic_plan_id='TEST-ONLY'))
    def test_active_lease_rejects_all_conflicts_without_side_effects(self):
        s,r=self.setup_scene();s.reserve_acquisition('B02',r)
        fs=[lambda:s.configure(TestReceipt('e2',mode='photon_count')),lambda:s.record_safe_access(r),lambda:s.set_door(False),lambda:s.set_door(True),lambda:s.load('CU-E',r),lambda:s.unload(r),lambda:s.quarantine('CU-E'),lambda:s.reserve_acquisition('B02',r),lambda:s.release(TestReceipt('old','CU-E','analog')),lambda:s.release(r,failed=True)]
        for i,f in enumerate(fs):
            with self.subTest(action=i):self.reject_unchanged(s,f)
    def test_stale_load_and_unload_are_atomic(self):
        s,r=self.setup_scene(carrier=None);s.record_safe_access(r);s.set_door(False)
        self.reject_unchanged(s,lambda:s.load('CU-E',TestReceipt('old','CU-E','analog')))
        r=TestReceipt('e1','CU-E','analog');s.load('CU-E',r)
        self.reject_unchanged(s,lambda:s.unload(TestReceipt('old','CU-E','analog')))
        self.reject_unchanged(s,lambda:s.unload(TestReceipt('e1','SI-STAR','analog')))
    def test_same_epoch_mode_change_rejected(self):
        s,r=self.setup_scene(carrier=None)
        self.reject_unchanged(s,lambda:s.configure(TestReceipt('e1',mode='photon_count',spatial_sensor_id='spatial-test-only')))
    def test_same_epoch_sensor_change_rejected(self):
        s,r=self.setup_scene(carrier=None)
        self.reject_unchanged(s,lambda:s.configure(TestReceipt('e1',mode='analog',spatial_sensor_id='different-sensor')))
    def test_old_epoch_cannot_be_recycled(self):
        s,r=self.setup_scene(carrier=None);s.configure(TestReceipt('e2',mode='photon_count'))
        self.reject_unchanged(s,lambda:s.configure(r))
    def test_quarantined_loaded_carrier_cannot_acquire(self):
        s,r=self.setup_scene();s.quarantine('CU-E')
        self.reject_unchanged(s,lambda:s.reserve_acquisition('B02',r))
    def test_release_wrong_carrier_rejected(self):
        s,r=self.setup_scene();s.reserve_acquisition('B02',r)
        self.reject_unchanged(s,lambda:s.release(TestReceipt('e1','SI-STAR','analog')))
    def test_release_wrong_mode_rejected(self):
        s,r=self.setup_scene();s.reserve_acquisition('B02',r)
        self.reject_unchanged(s,lambda:s.release(TestReceipt('e1','CU-E','photon_count')))
    def test_mapping_receipt_cannot_claim_present_carrier(self):
        s,r=self.setup_scene(carrier=None)
        self.reject_unchanged(s,lambda:s.reserve_acquisition('B01',TestReceipt('e1','CU-E','analog','spatial-test-only')))
    def test_blank_spatial_identity_rejected(self):
        s=GuardedStaticScene()
        self.reject_unchanged(s,lambda:s.configure(TestReceipt('e1',mode='analog',spatial_sensor_id='   ')))
    def test_release_failure_flag_explicit_boolean(self):
        s,r=self.setup_scene();s.reserve_acquisition('B02',r)
        self.reject_unchanged(s,lambda:s.release(r,failed='False',failure_id='TEST-ID'))
    def test_source_video_rate_never_photon_reassigned(self):
        for branch in ['B04','B05','B06','B07','B08']:
            s,r=self.setup_scene('photon_count','SI-STAR' if branch=='B08' else 'CU-E')
            for grid,hz in [((16,16),10),((32,32),2.5)]:
                with self.subTest(branch=branch,grid=grid):self.reject_unchanged(s,lambda:s.reserve_acquisition(branch,r,grid=grid,source_rate_hz=hz))
    def test_dynamic_source_rates_not_interchangeable(self):
        for grid,hz in [((16,16),10),((32,32),2.5)]:
            s,r=self.setup_scene();s.reserve_acquisition('B03',r,dynamic_plan_id='TEST-ONLY',grid=grid,source_rate_hz=hz)
        for grid,hz in [((16,16),2.5),((32,32),10),((64,64),10)]:
            s,r=self.setup_scene();self.reject_unchanged(s,lambda:s.reserve_acquisition('B03',r,dynamic_plan_id='TEST-ONLY',grid=grid,source_rate_hz=hz))
    def test_physical_calls_reject_without_state_changes(self):
        s,r=self.setup_scene()
        for action in ['move_robot','open_beam','acquire','connect_device']:
            with self.subTest(action=action):self.reject_unchanged(s,lambda:s.physical_action(action))

if __name__=='__main__':unittest.main()
