import copy
import math
import unittest
from contract import *

FID='DFB1:FULL:V0:OK'
class ContractTests(unittest.TestCase):
    def setUp(self): self.f=fixture(FID)
    def valid(self,f=None):
        f=f or self.f;return evaluate(f['events'],f['receipts'],f['fixture_id'])
    def rejects(self,f=None):
        f=f or self.f
        with self.assertRaises(ContractError): self.valid(f)
    def test_all_55_configuration_lifecycles(self):
        self.assertEqual(len(FIXTURE_IDS),55)
        for fid in FIXTURE_IDS:
            with self.subTest(fid=fid):self.assertTrue(self.valid(fixture(fid))['contract_passed'])
    def test_source_outcomes_not_fixture_values(self):
        r=self.valid()['analysis'];self.assertNotEqual(r['independent_rms_free_Hz'],4.28e6)
        self.assertTrue(any(v<0 for v in r['suppression_dB']))
    def test_full_preparation_credit(self):self.assertTrue(self.valid()['design_route_receipts_checked'])
    def test_prepared_intake_no_preparation_credit(self):self.assertFalse(self.valid(fixture('DFB1:PREPARED:V0:OK'))['design_route_receipts_checked'])
    def test_hold_never_measures(self):
        r=self.valid(fixture('HOLD'));self.assertIsNone(r['analysis']);self.assertEqual(r['closure'],'qualification_hold')
    def test_lock_loss_safe_closure(self):
        r=self.valid(fixture('DFB2:FULL:V1:LOCK_LOSS'));self.assertIsNone(r['analysis']);self.assertEqual(r['closure'],'lock_loss_safe_closed')
    def test_damage_quarantine(self):self.assertEqual(self.valid(fixture('DFB3:PREPARED:V2:DAMAGED'))['closure'],'quarantined')
    def test_all_step_deletions_rejected(self):
        for i in range(len(self.f['events'])):
            f=copy.deepcopy(self.f);f['events'].pop(i);self.rejects(f)
    def test_all_adjacent_swaps_rejected(self):
        for i in range(len(self.f['events'])-1):
            f=copy.deepcopy(self.f);f['events'][i],f['events'][i+1]=f['events'][i+1],f['events'][i];self.rejects(f)
    def test_extra_actor_success(self):self.f['events'][0]['success']=True;self.rejects()
    def test_actor_cannot_submit_psd(self):self.f['events'][0]['psd']=[1,2,3];self.rejects()
    def test_duplicate_evidence(self):self.f['events'][1]['evidence_id']=self.f['events'][0]['evidence_id'];self.rejects()
    def test_duplicate_event(self):self.f['events'][1]['event_id']=self.f['events'][0]['event_id'];self.rejects()
    def test_cross_configuration_replay(self):
        for fid in FIXTURE_IDS:
            if fid!=FID:
                with self.assertRaises(ContractError):evaluate(self.f['events'],self.f['receipts'],fid)
    def test_receipt_tampering_even_rehashed(self):
        rid=self.f['events'][0]['evidence_id'];self.f['receipts'][rid]['context']['package_id']='OTHER'
        self.f['receipts'][rid]['receipt_hash']=digest({k:v for k,v in self.f['receipts'][rid].items() if k!='receipt_hash'})
        self.rejects()
    def test_boolean_and_numeric_type_mutation(self):
        rid=self.f['events'][0]['evidence_id'];self.f['receipts'][rid]['payload']['verified']=1;self.rejects()
    def test_tuple_json_coercion_rejected(self):
        rid=next(k for k,v in self.f['receipts'].items() if v['operation_id']=='CALIBRATE_DISCRIMINATOR');self.f['receipts'][rid]['payload']['linear_range_Hz']=(-10000.,10000.);self.rejects()
    def test_unknown_fixture(self):
        for fid in ('DFB4:FULL:V0:OK','',None,True):
            with self.assertRaises(ContractError):fixture(fid)
    def test_registry_extra_record(self):self.f['receipts']['extra']={};self.rejects()
    def test_gain_sign_does_not_change_psd_conversion(self):self.assertEqual(voltage_psd_to_frequency([1e-12],-1e-7),voltage_psd_to_frequency([1e-12],1e-7))
    def test_gain_zero_invalid(self):
        with self.assertRaises(ContractError):voltage_psd_to_frequency([1],0)
    def test_constant_rms_and_clipping(self):self.assertAlmostEqual(rms_frequency([1,2,3],[4,4,4],1.5,2.5),2)
    def test_beta_below_line_zero(self):self.assertEqual(beta_linewidth([1,2,3],[0,0,0],1,3),0)
    def test_beta_constant_above_line(self):self.assertAlmostEqual(beta_linewidth([1,2,3],[10,10,10],1,3),math.sqrt(8*math.log(2)*20))
    def test_beta_crossing_clips_segment(self):
        beta=8*math.log(2)/math.pi**2
        # Constant S=2 beta crosses at f=2; integral over [1,2] equals 2 beta.
        self.assertAlmostEqual(beta_linewidth([1,2,3],[2*beta]*3,1,3),math.sqrt(8*math.log(2)*2*beta))
    def test_invalid_psd_types_and_values(self):
        for v in (True,-1,float('nan'),float('inf'),'1',10**400):
            with self.subTest(value=str(v)[:20]),self.assertRaises(ContractError):validate_arrays([1,2,3],[1,v,1])
    def test_invalid_frequency_support(self):
        for f in ([1,1,3],[3,2,1],[0,2,3],[1,float('nan'),3],[1,2,10**400]):
            with self.assertRaises(ContractError):validate_arrays(f,[1,1,1])
    def test_rms_no_extrapolation(self):
        with self.assertRaises(ContractError):rms_frequency([1,2,3],[1,1,1],0,3)
    def test_zero_psd_suppression_undefined(self):
        with self.assertRaises(ContractError):suppression_dB([1],[0])
    def test_crossing_directions_and_plateau(self):
        r=unity_crossing_details([1,2,3,4],[2,1,2,1],[1,2,1,2]);self.assertEqual([x['direction'] for x in r],['downward','upward','downward'])
        p=unity_crossing_details([1,2,3,4],[2,1,1,0],[1,1,1,1]);self.assertEqual(p[0]['kind'],'unity_plateau')
    def test_large_crossing_stays_correct(self):self.assertEqual(unity_crossings([1,2,3],[1e308,1,1],[1,1e308,1e308]),[1.5])
    def test_large_beta_no_infinite_result(self):self.assertTrue(math.isfinite(beta_linewidth([1,2,3],[4e307]*3,1,3)))
    def test_spectrum_channel_substitution_rejected(self):
        c=self.f['context'];s=spectrum('locked_fpga_in_loop',c,0)
        with self.assertRaises(ContractError):validate_spectrum(s,'locked_comb_heterodyne',c)
    def test_raw_spectrum_hash_change_rejected(self):
        c=self.f['context'];s=spectrum('locked_comb_heterodyne',c,0);s['psd_Hz2_per_Hz'][0]+=1
        with self.assertRaises(ContractError):validate_spectrum(s,'locked_comb_heterodyne',c)
    def test_unsafe_state_mutation(self):
        rid=next(k for k,v in self.f['receipts'].items() if v['operation_id']=='VERIFY_SAFE_OFF');self.f['receipts'][rid]['payload']['electrical_isolated']=False;self.rejects()
    def test_acknowledgement_is_not_lock_evidence(self):
        rid=next(k for k,v in self.f['receipts'].items() if v['operation_id']=='VERIFY_LOCK');self.f['receipts'][rid]['payload']['evidence_type']='request_acknowledgement';self.rejects()
    def test_reference_revision_mutation(self):
        rid=next(k for k,v in self.f['receipts'].items() if v['operation_id']=='ACQUIRE_HETERODYNE');self.f['receipts'][rid]['context']['reference_lock_revision']='STALE';self.rejects()
    def test_actor_event_non_ids(self):self.f['events'][0]['event_id']=True;self.rejects()
    def test_outputs_do_not_claim_physical_execution(self):
        r=self.valid();self.assertFalse(r['physical_execution']);self.assertFalse(r['scientific_reproduction']);self.assertTrue(r['synthetic_only'])
if __name__=='__main__':unittest.main()
