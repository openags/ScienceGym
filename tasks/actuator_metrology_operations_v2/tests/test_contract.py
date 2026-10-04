import unittest
from copy import deepcopy
from contract import BRANCHES,SCENARIOS,fixture,validate,project_ratio,mean_delta,digest,strict_equal

class ContractTests(unittest.TestCase):
    def setUp(self):self.c,self.e=fixture('PHYSICAL_ORTHOGONAL')
    def reject(self,c=None,e=None):self.assertFalse(validate(self.c if c is None else c,self.e if e is None else e)['accepted'])
    def event(self,op):return next(e for e in self.e if e['operation_id']==op)
    def receipt(self,c,op):return c['receipts'][self.event(op)['evidence_id']]
    def test_all_synthetic_lifecycles(self):
        for b in BRANCHES:
            for s in SCENARIOS if b!='DIRECTION_HOLD' else ['valid']:
                for variant in range(4) if b!='DIRECTION_HOLD' else [0]:
                    with self.subTest(b=b,s=s,v=variant):
                        c,e=fixture(b,s,variant);r=validate(c,e);self.assertTrue(r['accepted'],r);self.assertFalse(r['physical_validated']);self.assertFalse(r['whole_paper_complete'])
    def test_wrong_way_is_valid_negative_measurement(self):
        for b in BRANCHES[:2]:
            c,e=fixture(b,'wrong_way');r=validate(c,e);self.assertTrue(r['accepted']);self.assertTrue(all(x['signed_displacement_ratio']<0 for x in r['synthetic_measurements']))
    def test_default_is_no_motion_hold(self):
        c,e=fixture();self.assertTrue(validate(c,e)['accepted']);self.assertEqual(c['frames'],{});self.assertEqual(c['calibrations'],{});self.assertEqual(len(e),3)
    def test_failures_preserve_safe_quarantine(self):
        for s in ('short_input','base_slip','occluded_after'):
            c,e=fixture('PHYSICAL_ORTHOGONAL',s);r=validate(c,e);self.assertTrue(r['accepted']);self.assertEqual(r['synthetic_measurements'],[]);self.assertEqual(c['terminal'],'safe_quarantined')
    def test_damage_preserves_attempt_but_prohibits_reuse(self):
        c,e=fixture('PHYSICAL_ANTIPARALLEL','damage');r=validate(c,e);self.assertTrue(r['accepted']);self.assertEqual(len(r['synthetic_measurements']),2)
        for o in c['receipts'].values():
            if o['operation_id']=='QUARANTINE':self.assertIs(o['details']['reuse_permitted'],False)
    def test_every_operation_is_required(self):
        for i in range(len(self.e)):
            with self.subTest(i=i):self.reject(e=self.e[:i]+self.e[i+1:])
    def test_every_receipt_is_required(self):
        for rid in self.c['receipts']:
            c=deepcopy(self.c);del c['receipts'][rid];self.reject(c=c)
    def test_every_adjacent_order_swap_rejected(self):
        for i in range(len(self.e)-1):
            e=deepcopy(self.e);e[i],e[i+1]=e[i+1],e[i];self.reject(e=e)
    def test_event_replay_and_cross_episode_rejected(self):
        self.reject(e=self.e+[self.e[-1]])
        other,events=fixture('PHYSICAL_ORTHOGONAL',episode_id='synthetic_episode_002');self.reject(e=events);self.assertFalse(validate(other,self.e)['accepted'])
    def test_cross_configuration_replay_rejected(self):
        c,e=fixture('PHYSICAL_ORTHOGONAL','valid',0)
        for b,s,v in [('PHYSICAL_ANTIPARALLEL','valid',0),('PHYSICAL_ORTHOGONAL','wrong_way',0),('PHYSICAL_ORTHOGONAL','valid',1)]:
            other,events=fixture(b,s,v)
            self.assertNotEqual(c['fixture_instance_id'],other['fixture_instance_id'])
            self.assertFalse(validate(c,events)['accepted']);self.assertFalse(validate(other,e)['accepted'])
    def test_actor_cannot_supply_observations_or_cards(self):
        for key,val in [('success',True),('efficiency',2.4),('measurement',[0,-5]),('qualified',True),('frame',{}),('source_outcome',153)]:
            e=deepcopy(self.e);e[0][key]=val;self.reject(e=e)
    def test_source_conflict_and_completion_flags_fail_closed(self):
        for key,val in [('source_conflicts_resolved',True),('whole_paper_complete',True),('physical_execution',True),('production_authority',True),('numerical_reproduction',True),('source_conflicts_preserved',[])]:
            c=deepcopy(self.c);c[key]=val;self.reject(c=c)
    def test_missing_and_extra_keys(self):
        for key in self.c:
            c=deepcopy(self.c);del c[key];self.reject(c=c)
        c=deepcopy(self.c);c['allow_override']=True;self.reject(c=c)
    def test_frame_binding_tampering(self):
        for f_id in self.c['frames']:
            for key in self.c['frames'][f_id]['binding']:
                c=deepcopy(self.c);c['frames'][f_id]['binding'][key]='foreign';self.reject(c=c)
    def test_rehashed_forged_frame_rejected(self):
        c=deepcopy(self.c);f=next(iter(c['frames'].values()));f['nodes']['O1'][0]+=5.0;f['raw_record_hash']=digest({k:v for k,v in f.items() if k!='raw_record_hash'});self.reject(c=c)
    def test_rehashed_forged_receipt_rejected(self):
        c=deepcopy(self.c);o=self.receipt(c,'VERIFY_INPUT');o['details']['measured_input_vector_mm']=[0.0,-3.0];o['raw_record_hash']=digest({k:v for k,v in o.items() if k!='raw_record_hash'});self.reject(c=c)
    def test_sign_metric_and_source_oracle_tampering(self):
        c,e=fixture('PHYSICAL_ORTHOGONAL','wrong_way');op=next(o for o in c['receipts'].values() if o['operation_id']=='COMPUTE_EFFICIENCY');op['details']['value']=abs(op['details']['value']);self.assertFalse(validate(c,e)['accepted'])
        for key,val in [('n',3),('source_outcome_used',True),('value',1.53)]:
            c=deepcopy(self.c);self.receipt(c,'COMPUTE_EFFICIENCY')['details'][key]=val;self.reject(c=c)
    def test_calibration_and_node_map_mutants(self):
        for field,val in [('n',3),('matrix_mm_per_pixel',[[0.1,0.0],[0.0,0.1]]),('source_physical_n',2),('qualified_for_real_use',True),('input_tolerance_mm',999.0),('node_groups',{'input':['O1'],'output':['I1'],'base':['B1']})]:
            c=deepcopy(self.c);next(iter(c['calibrations'].values()))[field]=val;self.reject(c=c)
    def test_receipt_observations_are_not_command_acknowledgements(self):
        for op,key,val in [('VERIFY_BASE','base_fixed',False),('VERIFY_INPUT','independent_observation',False),('VERIFY_UNLOADED','unloaded',False),('CLEAN_STORE','cleanup_observed',False),('ARCHIVE','failed_attempts_preserved',False),('VERIFY_BASE','output_free',False)]:
            c=deepcopy(self.c);self.receipt(c,op)['details'][key]=val;self.reject(c=c)
    def test_no_one_control_shortcut(self):self.reject(e=self.e[:len(self.e)//2])
    def test_bool_int_substitution_rejected(self):
        c=deepcopy(self.c);c['whole_paper_complete']=0;self.reject(c=c)
        c=deepcopy(self.c);next(iter(c['receipts'].values()))['sequence']=True;self.reject(c=c)
    def test_nonfinite_and_malformed_data_fail_closed(self):
        for val in [None,True,[],{},float('nan'),float('inf'),'not-a-number']:
            c=deepcopy(self.c);next(iter(c['frames'].values()))['nodes']['I1']=val;self.reject(c=c)
        for c,e in [(None,[]),({},{}),([],[]),({'branch_id':[]},[]),({'branch_id':True},[])]:self.assertFalse(validate(c,e)['accepted'])
    def test_projection_preserves_sign_and_rejects_magnitude_shortcut(self):
        self.assertEqual(project_ratio([0.0,-5.0],[-2.0,8.0],[0.0,-1.0],[-1.0,0.0]),0.4)
        self.assertEqual(project_ratio([0.0,-5.0],[2.0,8.0],[0.0,-1.0],[-1.0,0.0]),-0.4)
    def test_nonpositive_denominator_and_nonunit_directions(self):
        for args in [([0,0],[-2,0],[0,-1],[-1,0]),([0,5],[-2,0],[0,-1],[-1,0]),([0,-5],[-2,0],[0,-2],[-1,0]),([0,-5],[-2,float('nan')],[0,-1],[-1,0]),([0,-5],[-2,0],[0,-1],[True,0])]:
            with self.assertRaises(ValueError):project_ratio(*args)
    def test_group_mean_and_pixel_y_inversion(self):
        a={'a':[0,0],'b':[10,10]};b={'a':[0,50],'b':[10,40]}
        self.assertEqual(mean_delta(a,b,['a','b'],[[0.1,0.0],[0.0,-0.1]]),[0.0,-4.0])
        with self.assertRaises(ValueError):mean_delta(a,b,['a','a'],[[0.1,0.0],[0.0,-0.1]])
        with self.assertRaises(ValueError):mean_delta(a,b,['a'],[[0,0],[0,0]])
    def test_strict_type_and_fixture_ids(self):
        self.assertFalse(strict_equal(True,1));self.assertFalse(strict_equal(1,1.0))
        for kw in [dict(branch='FORCE_PLIERS'),dict(variant=True),dict(variant=4),dict(episode_id='live_run'),dict(branch='DIRECTION_HOLD',scenario='wrong_way')]:
            with self.assertRaises(ValueError):fixture(**kw)
if __name__=='__main__':unittest.main()
