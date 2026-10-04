from copy import deepcopy
import unittest
from contract import *
class Lifecycle(unittest.TestCase):
    def setUp(self):self.fid='TENSION_BCC:FULL:OK';self.f=fixture(self.fid)
    def reject(self,e=None,r=None,fid=None):
        with self.assertRaises(ContractError):evaluate(self.f['events'] if e is None else e,self.f['receipts'] if r is None else r,self.fid if fid is None else fid)
    def test_all_fixtures(self):
        for fid in FIXTURE_IDS:
            f=fixture(fid);r=evaluate(f['events'],f['receipts'],fid);self.assertTrue(r['contract_passed']);self.assertFalse(r['physical_execution']);self.assertFalse(r['scientific_reproduction']);self.assertFalse(r['whole_paper_execution_complete'])
    def test_actor_claim_injection(self):
        for k in ('success','safe','measurement','qualification','raw_hash'):
            e=deepcopy(self.f['events']);e[0][k]=True;self.reject(e=e)
    def test_remove_each_event(self):
        for i in range(len(self.f['events'])):
            e=deepcopy(self.f['events']);del e[i];self.reject(e=e)
    def test_duplicate_each_event(self):
        for i in range(len(self.f['events'])):
            e=deepcopy(self.f['events']);e.insert(i,deepcopy(e[i]));self.reject(e=e)
    def test_adjacent_swaps(self):
        for i in range(len(self.f['events'])-1):
            e=deepcopy(self.f['events']);e[i],e[i+1]=e[i+1],e[i];self.reject(e=e)
    def test_changed_operation(self):
        e=deepcopy(self.f['events']);e[0]['operation_id']='PRINT_NOW';self.reject(e=e)
    def test_event_wrong_types(self):
        for v in (None,False,1,[],{},''):
            e=deepcopy(self.f['events']);e[0]['evidence_id']=v;self.reject(e=e)
    def test_unknown_fixture(self):
        for v in ('UNKNOWN',None,True,0,[],{}):
            with self.assertRaises(ContractError):fixture(v)
    def test_missing_extra_registry(self):
        r=deepcopy(self.f['receipts']);r.pop(next(iter(r)));self.reject(r=r);r=deepcopy(self.f['receipts']);r['extra']={};self.reject(r=r)
    def test_all_context_fields(self):
        for k in self.f['context']:
            r=deepcopy(self.f['receipts']);r[next(iter(r))]['context'][k]='stale';self.reject(r=r)
    def test_cross_fixture_replay(self):
        for fid in FIXTURE_IDS:
            if fid!=self.fid:
                f=fixture(fid);self.reject(e=f['events'],r=f['receipts'])
    def test_request_not_observation(self):
        e=deepcopy(self.f['events']);req=next(x for x in e if x['operation_id']=='REQUEST_PRINT');obs=next(x for x in e if x['operation_id']=='VERIFY_PRINT');obs['evidence_id']=req['evidence_id'];self.reject(e=e)
    def test_raw_rehash_forgery(self):
        r=deepcopy(self.f['receipts']);row=next(x for x in r.values() if x['operation_id']=='ACQUIRE_TEST_DATA');row['payload']['raw']['force_N'][1]*=2;row['payload']['raw_hash']=digest(row['payload']['raw']);self.reject(r=r)
    def test_nonfinite_registry(self):
        for v in (float('nan'),float('inf'),float('-inf'),10**1000):
            r=deepcopy(self.f['receipts']);r[next(iter(r))]['payload']['bad']=v;self.reject(r=r)
    def test_prepared_no_credit(self):
        f=fixture('TENSION_BCC:PREPARED:OK');self.assertFalse(evaluate(f['events'],f['receipts'],f['fixture_id'])['synthetic_preparation_lineage_checked'])
    def test_tetra_and_algorithm_holds(self):
        for fid in ('HOLD:TETRAKAIDECAHEDRON','HOLD:CUBIC_CONNECTIVITY'):
            f=fixture(fid);r=evaluate(f['events'],f['receipts'],fid);self.assertEqual(r['terminal_state'],'HELD_CONTAINED');self.assertFalse(r['synthetic_measurement_complete']);self.assertNotIn('REQUEST_PRINT',sequence_for(fid))
    def test_bcc_cubic_unaffected(self):
        for t in ('BCC','CUBIC'):
            f=fixture('TENSION_'+t+':FULL:OK');self.assertTrue(evaluate(f['events'],f['receipts'],f['fixture_id'])['synthetic_measurement_complete'])
    def test_both_support_orders(self):
        for route in ('PLASMA_FIRST','COAT_FIRST'):
            s=sequence_for('PROGRAMMED_FAILURE_EXPERIMENT:'+route+':OK');self.assertLess(s.index('VERIFY_CPD'),s.index('REQUEST_SUPPORT_REMOVAL'));self.assertLess(s.index('VERIFY_COATING'),s.index('DOCK_SAMPLE'));self.assertLess(s.index('VERIFY_SUPPORT_REMOVAL'),s.index('DOCK_SAMPLE'));self.assertEqual(s.index('REQUEST_SUPPORT_REMOVAL')<s.index('REQUEST_COATING'),route=='PLASMA_FIRST')
    def test_order_card_required(self):
        f=fixture('PROGRAMMED_FAILURE_EXPERIMENT:COAT_FIRST:OK');r=deepcopy(f['receipts']);row=next(x for x in r.values() if x['operation_id']=='VERIFY_SUPPORT_REMOVAL');del row['payload']['external_order_card']
        with self.assertRaises(ContractError):evaluate(f['events'],r,f['fixture_id'])
    def test_isolation_contained(self):
        f=fixture('TENSION_BCC:FULL:ISOLATION_HOLD');r=evaluate(f['events'],f['receipts'],f['fixture_id']);self.assertEqual(r['terminal_state'],'HELD_CONTAINED');self.assertFalse(r['sample_reusable']);self.assertNotIn('UNDOCK_SAMPLE',sequence_for(f['fixture_id']))
    def test_damage_quarantine(self):
        f=fixture('TENSION_BCC:FULL:DAMAGED');r=evaluate(f['events'],f['receipts'],f['fixture_id']);self.assertEqual(r['terminal_state'],'QUARANTINED_SYNTHETIC');self.assertFalse(r['sample_reusable'])
    def test_data_hold_incomplete(self):
        f=fixture('TENSION_BCC:FULL:DATA_HOLD');r=evaluate(f['events'],f['receipts'],f['fixture_id']);self.assertFalse(r['synthetic_measurement_complete']);self.assertIn('VERIFY_SAFE_OFF',sequence_for(f['fixture_id']))
    def test_models_metadata_only(self):
        for b in MODEL_OPS:
            f=fixture('MODEL:'+b);r=evaluate(f['events'],f['receipts'],f['fixture_id']);self.assertTrue(r['numerical_metadata_contract_checked']);self.assertFalse(r['numerical_solver_execution']);self.assertFalse(r['synthetic_measurement_complete'])
    def test_independent_fixture_copy(self):self.f['events'].clear();self.assertTrue(fixture(self.fid)['events'])
class Arithmetic(unittest.TestCase):
    def tension(self,**kw):
        a=dict(time=[0,1,2],displacement=[0,1,2],force=[0,2,4],area=2,height=4,relative_density=.5,solid_density=4,solid_modulus=8,fit_indices=[0,1,2]);a.update(kw);return reduce_tension(**a)
    def test_analytic_tension(self):
        r=self.tension();self.assertEqual(r['stress_Pa'],[0,1,2]);self.assertEqual(r['strain'],[0,.25,.5]);self.assertEqual(r['stretch'],[1,1.25,1.5]);self.assertAlmostEqual(r['fit_modulus_Pa'],4);self.assertAlmostEqual(r['loading_work_J_m3'],.5);self.assertAlmostEqual(r['specific_loading_work_J_kg'],.25);self.assertAlmostEqual(r['relative_specific_modulus'],1);self.assertAlmostEqual(r['source_figure_specific_modulus_m3_kg'],.25)
    def test_fit_subset(self):self.assertAlmostEqual(self.tension(force=[0,2,10],fit_indices=[0,1])['fit_modulus_Pa'],4)
    def test_bad_geometry(self):
        for k in ('area','height','relative_density','solid_density','solid_modulus'):
            for v in (0,-1,False,None,float('inf'),float('nan')):
                with self.assertRaises(ContractError):self.tension(**{k:v})
        with self.assertRaises(ContractError):self.tension(relative_density=1.1)
    def test_bad_vectors(self):
        for kw in (dict(time=[0,0,2]),dict(time=[2,1,0]),dict(force=[0,1]),dict(displacement=[0,1,1]),dict(force=[0,-1,1]),dict(displacement=[-1,0,1]),dict(time=(0,1,2)),dict(force=[0,True,1]),dict(force=[0,float('nan'),1])):
            with self.assertRaises(ContractError):self.tension(**kw)
    def test_bad_fit(self):
        for f in ([0],[1,0],[0,0],[0,3],[0,True],None):
            with self.assertRaises(ContractError):self.tension(fit_indices=f)
    def test_overflow(self):
        for kw in (dict(force=[0,1e308,1e308],area=1e-308),dict(area=1e-320),dict(height=1e-320),dict(relative_density=1e-320,solid_density=1e-320)):
            with self.assertRaises(ContractError):self.tension(**kw)
    def test_signed_integral(self):self.assertAlmostEqual(integrate([0,1,2,1,0],[0,2,3,1,0]),1)
    def test_cycle_tension_compression(self):
        for s in (1,-1):
            r=cycle_loss([0,1,2,3,4],[s*x for x in [0,1,2,1,0]],[s*x for x in [0,2,3,1,0]],1,1,[[0,2,4]],0);self.assertEqual(r[0]['loss_J_m3'],1);self.assertEqual(r[0]['relative_to_first'],1);self.assertEqual(r[0]['direction'],'tension' if s==1 else 'compression')
    def test_cycle_unclosed(self):
        with self.assertRaises(ContractError):cycle_loss([0,1,2,3,4],[0,1,2,1,.1],[0,2,3,1,0],1,1,[[0,2,4]],0)
    def test_cycle_negative_work(self):
        with self.assertRaises(ContractError):cycle_loss([0,1,2,3,4],[0,1,2,1,0],[0,1,3,2,0],1,1,[[0,2,4]],0)
    def test_cycle_zero_baseline(self):
        with self.assertRaises(ContractError):cycle_loss([0,1,2,3,4],[0,1,2,1,0],[0,1,2,1,0],1,1,[[0,2,4]],0)
    def test_bad_cycle_segmentation(self):
        for seg in ([],[[0,1,2]],[[0,3,2]],[[0,2,True]],[[1,2,4]],[[0,2,4],[0,2,4]]):
            with self.assertRaises(ContractError):cycle_loss([0,1,2,3,4],[0,1,2,1,0],[0,2,3,1,0],1,1,seg,0)
    def test_explicit_cycle_closing_segment(self):
        r=cycle_loss([0,1,2,3,4],[0,1,2,1,.01],[0,2,3,1,0],1,1,[[0,2,4]],.02);self.assertTrue(r[0]['closure_segment_included']);self.assertAlmostEqual(r[0]['residual_strain'],.01)
    def test_strict_canonical(self):
        self.assertEqual(digest({'a':1,'b':2}),digest({'b':2,'a':1}))
        for v in ({1:'x'},{'x':set()},float('nan'),10**1000):
            with self.assertRaises(ContractError):canonical(v)
if __name__=='__main__':unittest.main()
