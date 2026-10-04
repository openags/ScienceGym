import unittest,copy,math
from contract import *
class Records(unittest.TestCase):
    def setUp(self):self.fid='COMPRESS_N4_A2:FULL:GOOD';self.f=fixture(self.fid)
    def reject(self,events=None,receipts=None,fid=None):
        with self.assertRaises(ContractError):evaluate(events if events is not None else self.f['events'],receipts if receipts is not None else self.f['receipts'],fid or self.fid)
    def test_all_143_fixtures(self):
        self.assertEqual(len(FIXTURE_IDS),143)
        for fid in FIXTURE_IDS:
            with self.subTest(fid=fid):
                f=fixture(fid);r=evaluate(f['events'],f['receipts'],fid);self.assertTrue(r['contract_passed']);self.assertFalse(r['physical_execution']);self.assertFalse(r['numerical_solver_execution']);self.assertFalse(r['whole_campaign_complete'])
    def test_alternate_topological_order(self):
        events=self.f['events'];receipts=self.f['receipts'];done=set();ordered=[];remaining=list(reversed(events))
        while remaining:
            for e in remaining:
                if set(receipts[e['evidence_id']]['depends_on'])<=done:break
            else:self.fail('cycle')
            remaining.remove(e);ordered.append(e);done.add(e['evidence_id'])
        self.assertNotEqual(ordered,events);self.assertTrue(evaluate(ordered,receipts,self.fid)['contract_passed'])
    def test_missing_event(self):self.reject(events=self.f['events'][:-1])
    def test_duplicate_event(self):self.reject(events=self.f['events'][:-1]+[self.f['events'][0]])
    def test_unknown_event(self):self.f['events'][0]['event_id']='unknown';self.reject()
    def test_extra_event(self):self.reject(events=self.f['events']+[self.f['events'][0]])
    def test_wrong_operation(self):self.f['events'][0]['operation_id']='REQUEST_CYCLES';self.reject()
    def test_wrong_evidence(self):self.f['events'][0]['evidence_id']=self.f['events'][1]['evidence_id'];self.reject()
    def test_actor_sensor_value(self):self.f['events'][0]['force']=123;self.reject()
    def test_actor_success(self):self.f['events'][0]['success']=True;self.reject()
    def test_nonstring_id(self):self.f['events'][0]['event_id']=True;self.reject()
    def test_dependency_violation(self):self.reject(events=list(reversed(self.f['events'])))
    def test_all_lineage_fields_pinned(self):
        for key in CONTEXT_KEYS:
            with self.subTest(key=key):
                f=copy.deepcopy(self.f);next(iter(f['receipts'].values()))['context'][key]='stale';self.reject(receipts=f['receipts'])
    def test_registry_injected(self):self.f['receipts']['new']={};self.reject()
    def test_registry_missing(self):self.f['receipts'].pop(next(iter(self.f['receipts'])));self.reject()
    def test_receipt_role(self):next(iter(self.f['receipts'].values()))['payload']['role']='actor_claim';self.reject()
    def test_safeoff_not_ack(self):
        for r in self.f['receipts'].values():
            if r['operation_id']=='VERIFY_SAFE_OFF':r['payload']['safe_release_observed']=False
        self.reject()
    def test_skipped_preparation(self):
        for op in ['VERIFY_CUT','VERIFY_FOLD','VERIFY_STACK_BOND','VERIFY_CURE']:
            with self.subTest(op=op):self.reject(events=[e for e in self.f['events'] if e['operation_id']!=op])
    def test_prepared_no_preparation_credit(self):
        fid='COMPRESS_N4_A2:PREPARED:GOOD';f=fixture(fid);r=evaluate(f['events'],f['receipts'],fid);self.assertFalse(r['synthetic_preparation_lineage_checked']);self.assertNotIn('REQUEST_CUT',[e['operation_id'] for e in f['events']])
    def test_material_coupon_not_folded(self):
        f=fixture('BASE_MATERIAL_TENSION:FULL:GOOD');ops=[e['operation_id'] for e in f['events']];self.assertIn('REQUEST_CUT',ops);self.assertNotIn('REQUEST_FOLD',ops);self.assertNotIn('REQUEST_RECONFIGURATION',ops)
    def test_damaged_not_complete_or_reusable(self):
        f=fixture('COMPRESS_N4_A2:FULL:DAMAGED');r=evaluate(f['events'],f['receipts'],f['fixture_id']);self.assertFalse(r['synthetic_instance_complete']);self.assertFalse(r['virgin_sample_reusable']);self.assertIn('QUARANTINE_SAMPLE',[e['operation_id'] for e in f['events']])
    def test_isolation_hold_no_undock(self):
        f=fixture('COMPRESS_N4_A2:FULL:ISOLATION_HOLD');self.assertNotIn('UNDOCK_SAMPLE',[e['operation_id'] for e in f['events']]);self.assertFalse(evaluate(f['events'],f['receipts'],f['fixture_id'])['synthetic_instance_complete'])
    def test_cycle_specimen_not_virgin(self):
        f=fixture('CYCLIC_N4_A2:FULL:GOOD');self.assertFalse(evaluate(f['events'],f['receipts'],f['fixture_id'])['virgin_sample_reusable'])
    def test_unknown_fixture(self):self.reject(fid='madeup')
    def test_no_prepared_full_fabrication(self):
        with self.assertRaises(ContractError):fixture('FULL_FABRICATION:PREPARED:GOOD')
    def test_corrupt_raw_hash(self):
        for r in self.f['receipts'].values():
            if r['operation_id']=='ACQUIRE_RECORDS':r['payload']['raw']['force_N'][1]+=1
        self.reject()
    def test_model_cannot_supply_measurement(self):
        f=fixture('MODEL:KINEMATIC_MOBILITY');r=evaluate(f['events'],f['receipts'],f['fixture_id']);self.assertTrue(r['numerical_metadata_checked']);self.assertFalse(r['synthetic_measurement_checked'])
    def test_band_release_verified(self):
        f=fixture('RUBBER_BAND_CONTROL:FULL:GOOD');ev=[e for e in f['events'] if e['operation_id']!='VERIFY_BAND_RELEASE'];self.reject(ev,f['receipts'],f['fixture_id'])
    def test_nan_receipt(self):next(iter(self.f['receipts'].values()))['payload']['value']=math.nan;self.reject()
class Arithmetic(unittest.TestCase):
    def setUp(self):self.raw=raw_data('COMPRESS_N4_A2:FULL:GOOD')
    def test_first_peak_not_global(self):
        r=compression(self.raw,[1,2,3],4);self.assertAlmostEqual(r['yield_first_peak_Pa'],1000);self.assertAlmostEqual(r['engaged_modulus_Pa'],30000)
        with self.assertRaises(ContractError):compression(self.raw,[1,2,3],7)
    def test_fit_rejects_toe_override_late_interval(self):
        with self.assertRaises(ContractError):compression(self.raw,[1,4],4)
    def test_fit_support_ceiling(self):
        with self.assertRaises(ContractError):linear_fit([0,.04,.06],[0,1,2],[1,2],.05)
    def test_invalid_numbers(self):
        for x in [True,False,float('inf'),float('-inf'),float('nan'),'1',None,10**1000]:
            with self.subTest(x=str(x)[:30]):
                with self.assertRaises(ContractError):number(x)
    def test_zero_geometry(self):
        for k in ['area_m2','height_m']:
            r=copy.deepcopy(self.raw);r[k]=0
            with self.assertRaises(ContractError):raw_check(r)
    def test_duplicate_time(self):
        self.raw['time_s'][1]=0
        with self.assertRaises(ContractError):raw_check(self.raw)
    def test_units(self):
        self.raw['units']['force']='kN'
        with self.assertRaises(ContractError):raw_check(self.raw)
    def test_missing_image(self):
        self.raw['image_ids'].pop()
        with self.assertRaises(ContractError):raw_check(self.raw)
    def test_sign(self):
        self.raw['force_N'][1]=-1
        with self.assertRaises(ContractError):raw_check(self.raw)
    def test_directional_reference(self):
        self.raw['loading_kind']='tension'
        for d in ['MD','CD']:self.assertEqual(tensile(self.raw,[1,2,3],d,d)['direction'],d)
        with self.assertRaises(ContractError):tensile(self.raw,[1,2,3],'CD','MD')
    def test_cycle_count_and_residual(self):
        for b,n in [('CYCLIC_N4_A2',10),('CYCLIC_N6_A3',4)]:
            r=raw_data(b+':FULL:GOOD');out=cyclic(r,r['cycle_segments'],10,n);self.assertEqual(len(out),n);self.assertGreater(out[0]['residual_strain'],0);self.assertFalse(out[0]['closed_loop_loss_claimed'])
            with self.assertRaises(ContractError):cyclic(r,r['cycle_segments'],10,n+1)
    def test_cycle_baseline_zero(self):
        r=raw_data('CYCLIC_N4_A2:FULL:GOOD')
        with self.assertRaises(ContractError):cyclic(r,r['cycle_segments'],0,10)
    def test_unsegmented_cycle_tail(self):
        r=raw_data('CYCLIC_N4_A2:FULL:GOOD');seg=copy.deepcopy(r['cycle_segments']);seg[-1][-1]-=1
        with self.assertRaises(ContractError):cyclic(r,seg,10,10)
    def test_mixed_baselines(self):
        r=mixed_ratios(5,2,10,1);self.assertEqual(r['modulus_relative_to_configuration1'],.5);self.assertEqual(r['channel_area_relative_to_configuration4'],2);self.assertFalse(r['measured_permeability'])
        with self.assertRaises(ContractError):mixed_ratios(5,2,10,0)
    def test_specimen_statistics(self):
        r=specimen_statistics([{'sample_id':'a','value':1},{'sample_id':'b','value':3}]);self.assertEqual(r['mean'],2);self.assertAlmostEqual(r['sample_sd'],math.sqrt(2))
        with self.assertRaises(ContractError):specimen_statistics([{'sample_id':'a','value':1},{'sample_id':'a','value':3}])
    def test_unknown_repeat_not_empty_success(self):
        with self.assertRaises(ContractError):specimen_statistics([])
    def test_irregular_tessellation(self):
        self.assertTrue(compatible_mode(6,'IRREGULAR',False))
        with self.assertRaises(ContractError):compatible_mode(6,'IRREGULAR',True)
        with self.assertRaises(ContractError):compatible_mode(8,'IRREGULAR',False)
    def test_regular_mode_word(self):
        self.assertTrue(compatible_mode(6,'AAO',True))
        with self.assertRaises(ContractError):compatible_mode(6,'A2O',True)
    def test_decimal_overflow_underflow(self):
        self.assertAlmostEqual(ratio(1e-300,1e-300),1)
        for a,b in [(1e308,1e-308),(1e-308,1e308)]:
            with self.assertRaises(ContractError):ratio(a,b)
    def test_loading_kind_not_interchangeable(self):
        with self.assertRaises(ContractError):tensile(self.raw,[1,2,3],'MD','MD')
        self.raw['loading_kind']='tension'
        with self.assertRaises(ContractError):compression(self.raw,[1,2,3],4)
    def test_boolean_index(self):
        with self.assertRaises(ContractError):compression(self.raw,[True,2,3],4)
if __name__=='__main__':unittest.main()
