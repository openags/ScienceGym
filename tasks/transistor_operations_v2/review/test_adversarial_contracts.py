"""Independent mutation tests for the synthetic transistor contract, not apparatus safety."""
import importlib.util
import pathlib
import unittest
import copy
import json

BASE=pathlib.Path(__file__).resolve().parents[1]
ROOT=BASE if (BASE/'branches.json').exists() else BASE/'transistor_operations_v2'
spec=importlib.util.spec_from_file_location('transistor_contract_review_target',ROOT/'tests/contract.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

class AdversarialReview(unittest.TestCase):
    def rejected(self,mutate,selected=None):
        ctx,events=c.fixture(selected or ['STACK'])
        self.assertTrue(c.validate(ctx,events)['accepted'], 'pristine fixture unexpectedly fails')
        mutate(ctx,events)
        r=c.validate(ctx,events)
        self.assertFalse(r['accepted'], 'malformed fixture accepted')
    def payload_change(self,ctx,events,key,value,index=0):
        o=ctx['observations'][events[index]['event_id']]
        record=ctx['record_store'][o['record_id']]
        record['payload'][key]=value
        o['record_hash']=c.digest(record)
    def test_baseline_all_branches(self):
        ctx,e=c.fixture(list(c.BRANCHES));self.assertTrue(c.validate(ctx,e)['accepted'])
    def test_both_buffer_variants_leave_cap_50(self):
        for variant in [25,50]:
            ctx,e=c.fixture(['STACK'],buffer_variant_nm=variant)
            self.assertTrue(c.validate(ctx,e)['accepted'])
            rows=c.cases_for('STACK',variant)
            self.assertEqual([x['thickness'] for x in rows if x['role']=='interstack_buffer'],[variant]*9)
            self.assertEqual([x['thickness'] for x in rows if x['role']=='final_cap'],[50])
    def test_card_true_not_integer(self):
        self.rejected(lambda x,e:x['cards']['U_AUTHORITY'].__setitem__('valid',1))
    def test_card_fixture_flag_not_integer(self):
        self.rejected(lambda x,e:x['cards']['U_AUTHORITY'].__setitem__('qualified_for_fixture_only',1))
    def test_conflict_false_not_zero(self):
        self.rejected(lambda x,e:x['conflict_dispositions']['C01'].__setitem__('source_resolved',0))
    def test_conflict_reviewed_not_integer(self):
        self.rejected(lambda x,e:x['conflict_dispositions']['C01'].__setitem__('reviewed',1))
    def test_job_false_not_zero(self):
        self.rejected(lambda x,e:x['jobs']['STACK'].__setitem__('full_source_population',0))
    def test_payload_specimen_version_not_bool(self):
        self.rejected(lambda x,e:self.payload_change(x,e,'specimen_version',True),['PAIRS'])
    def test_payload_elapsed_not_bool(self):
        self.rejected(lambda x,e:self.payload_change(x,e,'elapsed_s',False),['PAIRS'])
    def test_payload_mount_revision_not_bool(self):
        self.rejected(lambda x,e:self.payload_change(x,e,'mount_revision',False),['PAIRS'])
    def test_rehash_does_not_authorize_payload_change(self):
        self.rejected(lambda x,e:self.payload_change(x,e,'calibration_id','wrong_calibration'),['PAIRS'])
    def test_duplicate_event_rejected(self):
        self.rejected(lambda x,e:e.__setitem__(1,copy.deepcopy(e[0])))
    def test_missing_cleanup_rejected(self):
        self.rejected(lambda x,e:e.pop())
    def test_actor_outcome_rejected(self):
        self.rejected(lambda x,e:e[0].__setitem__('accepted',True))
    def test_no_record_payload_rejected(self):
        self.rejected(lambda x,e:x['record_store'].pop(next(iter(x['record_store']))))
    def test_cross_episode_record_rejected(self):
        def change(x,e):
            o=x['observations'][e[0]['event_id']];r=x['record_store'][o['record_id']]
            r['episode_id']='synthetic_episode_other';o['record_hash']=c.digest(r)
        self.rejected(change)
    def test_qualified_context_cannot_claim_science(self):
        for f in ['production_authority','whole_historical_route_complete','scientific_replication','numerical_reproduction']:
            with self.subTest(flag=f):self.rejected(lambda x,e:x.__setitem__(f,True))
    def test_rehashed_stress_history_reset_rejected(self):
        def change(x,e):
            i=next(i for i,event in enumerate(e) if ':STRESS_SERVICE' in event['phase'])
            self.payload_change(x,e,'exposure_count',0,index=i)
        self.rejected(change,['NBS'])
    def test_rehashed_thermal_cooldown_removed_rejected(self):
        def change(x,e):
            i=next(i for i,event in enumerate(e) if ':COOLDOWN' in event['phase'])
            self.payload_change(x,e,'duration_s',0,index=i)
        self.rejected(change,['THERMAL'])
    def test_rehashed_longterm_clock_shortening_rejected(self):
        def change(x,e):
            i=next(i for i,event in enumerate(e) if ':CUSTODY_CHECK' in event['phase'] and x['record_store'][x['observations'][event['event_id']]['record_id']]['payload']['elapsed_s']>0)
            self.payload_change(x,e,'elapsed_s',1,index=i)
        self.rejected(change,['LONG_TERM'])
    def test_rehashed_circuit_map_swap_rejected(self):
        def change(x,e):
            o=next(o for o in x['observations'].values() if o['operation_id']=='VTC')
            r=x['record_store'][o['record_id']];r['payload']['control']['netlist_id']='INDEPENDENT_INVERTER_S31';o['record_hash']=c.digest(r)
        self.rejected(change,['PAIRS'])
    def test_prep_stack_material_continuity(self):
        ctx,e=c.fixture(['STACK'])
        a=ctx['jobs']['PREP'];b=ctx['jobs']['STACK']
        self.assertEqual(a['specimen_id'],b['specimen_id'])
        final=next(x['payload'] for x in reversed(c.plan_for('PREP')) if x['operation_id']=='CLEAN_STORE')
        self.assertEqual(b['parent_material_bindings'],[{'branch_id':'PREP','specimen_id':final['specimen_id'],'released_specimen_version':final['specimen_version']}])
    def test_mutated_material_parent_rejected(self):
        self.rejected(lambda x,e:x['jobs']['STACK']['parent_material_bindings'][0].__setitem__('specimen_id','unrelated_substrate'))
    def test_highk_distinct_material_specimens(self):
        p=c.plan_for('HIGHK')
        before={x['case_id']:x['payload'] for x in p if x['operation_id']=='BASELINE_ACQUIRE'}
        after={x['case_id']:x['payload'] for x in p if x['operation_id']=='POST_ACQUIRE'}
        self.assertEqual(set(before),{'HfO2','Al2O3'})
        self.assertEqual(len({x['specimen_id'] for x in before.values()}),2)
        for material in before:
            self.assertEqual(before[material]['specimen_id'],after[material]['specimen_id'])
            self.assertGreater(after[material]['specimen_version'],before[material]['specimen_version'])
    def test_longterm_architecture_and_device_binding(self):
        rows=c.cases_for('LONG_TERM')
        self.assertEqual(len(rows),63)
        for architecture in ['BG','TG','DG']:
            subset=[x for x in rows if x['architecture']==architecture]
            self.assertEqual([x['day'] for x in subset],list(range(0,201,10)))
            self.assertEqual(len({x['device_id'] for x in subset}),1)
        self.assertEqual(len({x['device_id'] for x in rows}),3)
    def test_structural_parent_daughter_binding(self):
        p=c.plan_for('STRUCTURAL')
        for x in p:
            if x['operation_id']=='IMAGE_SERVICE':
                self.assertEqual(x['payload']['specimen_id'],x['payload']['control']['daughter'])
                self.assertEqual(x['payload']['parent_specimen_id'],x['payload']['control']['parent_coupon'])
    def test_structural_all_daughters_retrieved_and_inspected(self):
        p=c.plan_for('STRUCTURAL');inventory=c.material_inventory('STRUCTURAL')
        self.assertEqual(len(inventory),3)
        for row in inventory:
            self.assertEqual(row['input_disposition'],'consumed_by_section_service')
            for operation in ['RETRIEVE','INSPECT']:
                self.assertTrue(any(x['operation_id']==operation and x['payload']['specimen_id']==row['output_id'] for x in p))
        for operation in ['ARCHIVE','CLEAN_STORE']:
            step=next(x for x in p if x['operation_id']==operation)
            self.assertEqual(step['payload']['material_dispositions'],inventory)
    def test_missing_daughter_disposition_after_rehash_rejected(self):
        def change(ctx,e):
            o=next(o for o in ctx['observations'].values() if o['operation_id']=='CLEAN_STORE')
            r=ctx['record_store'][o['record_id']];r['payload']['material_dispositions'].pop();o['record_hash']=c.digest(r)
        self.rejected(change,['STRUCTURAL'])
    def test_highk_all_materials_inspected(self):
        p=c.plan_for('HIGHK')
        for row in c.material_inventory('HIGHK'):
            self.assertTrue(any(x['operation_id']=='INSPECT' and x['payload']['specimen_id']==row['output_id'] for x in p))
    def test_every_plan_operation_declared_by_branch(self):
        for b in c.BRANCHES:
            with self.subTest(branch=b):
                self.assertTrue({x['operation_id'] for x in c.plan_for(b)} <= set(c.BRANCHES[b]['operation_ids']))
    def test_safe_transport_preconditions_in_golden_plan(self):
        # A regenerated expected plan must itself satisfy causal handling rules.
        for branch in c.BRANCHES:
            previous=None
            for step in c.plan_for(branch):
                if step['operation_id'] in ['TRANSFER_IN','MOUNT','RETRIEVE']:
                    with self.subTest(branch=branch,phase=step['phase']):
                        self.assertIsNotNone(previous)
                        self.assertIs(previous['payload']['independent_safe_zero'],True)
                previous=step
    def test_no_mount_to_transfer_without_release(self):
        for branch in ['HIGHK','THERMAL','LONG_TERM']:
            previous=None
            for step in c.plan_for(branch):
                if previous and step['operation_id']=='TRANSFER_IN':
                    with self.subTest(branch=branch,phase=step['phase']):
                        self.assertNotEqual(previous['payload']['custody'],'fixture')
                if previous and step['payload']['station']!=previous['payload']['station']:
                    with self.subTest(branch=branch,phase=step['phase']):
                        self.assertNotEqual(previous['payload']['custody'],'fixture')
                previous=step

if __name__=='__main__':unittest.main(verbosity=2)
