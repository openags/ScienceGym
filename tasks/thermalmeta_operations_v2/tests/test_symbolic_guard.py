import unittest
from copy import deepcopy
from runtime.symbolic_guard import SymbolicEpisode, Held, verify_preparation, check_receipt, FAMILIES, CONDITIONS, NUMERICAL_BRANCHES
from fixtures import *

class PreparationTests(unittest.TestCase):
    def test_all_family_chains(self):
        for f in FAMILIES: self.assertEqual(verify_preparation(chain(f))['sample_family_id'],f)
    def test_missing_each_stage(self):
        for i in range(5):
            c=chain(); c.pop(i)
            with self.subTest(stage=i),self.assertRaises(Held): verify_preparation(c)
    def test_cross_identity(self):
        for field in ('paper_id','sample_family_id','design_id','design_revision','specimen_id','service_job_id'):
            for i in range(1,5):
                c=chain(); c[i]=reseal(c[i],**{field:'WRONG'})
                with self.subTest(field=field,stage=i),self.assertRaises(Held): verify_preparation(c)
    def test_wrong_parent_each_node(self):
        for i in range(5):
            c=chain(); c[i]=reseal(c[i],parent_id='WRONG')
            with self.subTest(stage=i),self.assertRaises(Held): verify_preparation(c)
    def test_wrong_lattice_parent(self):
        c=chain(); c[-1]=reseal(c[-1],lattice_parent_id='WRONG')
        with self.assertRaises(Held): verify_preparation(c)
    def test_wrong_intermediate_parent(self):
        c=chain(); c[-1]=reseal(c[-1],intermediate_parent_id='WRONG')
        with self.assertRaises(Held): verify_preparation(c)
    def test_wrong_core(self):
        for f in FAMILIES:
            c=chain(f); c[-1]=reseal(c[-1],core_assignment='WRONG')
            with self.subTest(family=f),self.assertRaises(Held): verify_preparation(c)
    def test_lot_missing(self):
        c=chain(); c[2]=reseal(c[2],material_lot_ids=[])
        with self.assertRaises(Held): verify_preparation(c)
    def test_invalid_release(self):
        for key in ('safe_release','dry_ambient'):
            c=chain(); c[-1]=reseal(c[-1],**{key:False})
            with self.subTest(key=key),self.assertRaises(Held): verify_preparation(c)
    def test_unqualified_geometry(self):
        c=chain(); c[0]=reseal(c[0],geometry_qualification=False)
        with self.assertRaises(Held): verify_preparation(c)
    def test_tamper_hash(self):
        c=chain(); c[0]['design_revision']='R99'
        with self.assertRaises(Held): verify_preparation(c)
    def test_source_receipt_rejected(self):
        c=chain(); c[0]['evidence_class']='source_reported_reference'
        with self.assertRaises(Held): verify_preparation(c)
    def test_real_observation_rejected(self):
        c=chain(); c[0]['evidence_class']='qualified_observation_external'
        with self.assertRaises(Held): verify_preparation(c)
    def test_duplicate_specimen(self):
        e=SymbolicEpisode(plan()); e.receive(chain())
        with self.assertRaises(Held): e.receive(chain())

class PlanTests(unittest.TestCase):
    def test_unapproved_slot(self):
        p=plan();p[0]['approved']=False
        with self.assertRaises(Held): SymbolicEpisode(p)
    def test_duplicate_slot(self):
        p=plan();p.append(deepcopy(p[0]))
        with self.assertRaises(Held): SymbolicEpisode(p)
    def test_unknown_condition(self):
        p=plan();p[0]['condition_id']='COND_CLOAK_Z'
        with self.assertRaises(Held): SymbolicEpisode(p)
    def test_missing_repeat_label(self):
        p=plan();p[0]['repeat_kind']=None
        with self.assertRaises(Held): SymbolicEpisode(p)
    def test_technical_repeat_same_specimen(self):
        p=plan();q=dict(p[0],slot_id='REPEAT',repeat_kind='technical',replicate_of_slot_id=p[0]['slot_id']);p.append(q)
        self.assertEqual(len(SymbolicEpisode(p).plan),7)
    def test_technical_repeat_new_specimen_rejected(self):
        p=plan();p.append(dict(p[0],slot_id='REPEAT',specimen_id='DIFFERENT',repeat_kind='technical',replicate_of_slot_id=p[0]['slot_id']))
        with self.assertRaises(Held): SymbolicEpisode(p)
    def test_independent_repeat_same_specimen_rejected(self):
        p=plan();p.append(dict(p[0],slot_id='REPEAT',repeat_kind='independent',replicate_of_slot_id=p[0]['slot_id']))
        with self.assertRaises(Held): SymbolicEpisode(p)
    def test_independent_repeat_new_specimen(self):
        p=plan();p.append(dict(p[0],slot_id='REPEAT',specimen_id='INDEPENDENT',repeat_kind='independent',replicate_of_slot_id=p[0]['slot_id']))
        e=SymbolicEpisode(p);e.receive(chain(specimen='INDEPENDENT'));self.assertIn('INDEPENDENT',e.specimens)
    def test_repeat_requires_parent(self):
        p=plan();p.append(dict(p[0],slot_id='REPEAT',repeat_kind='technical'))
        with self.assertRaises(Held): SymbolicEpisode(p)
    def test_repeated_base_rejected(self):
        p=plan();p.append(dict(p[0],slot_id='OTHER'))
        with self.assertRaises(Held): SymbolicEpisode(p)

class LifecycleTests(unittest.TestCase):
    def setUp(self): self.e=ready(SymbolicEpisode(plan())); self.slot=self.e.plan[0]
    def test_mount_missing_preparation(self):
        e=SymbolicEpisode(plan());e.calibrate(calibration())
        with self.assertRaises(Held):e.mount(self.slot['slot_id'],mount(self.slot))
    def test_mount_missing_calibration(self):
        e=SymbolicEpisode(plan());e.receive(chain())
        with self.assertRaises(Held):e.mount(self.slot['slot_id'],mount(self.slot))
    def test_wrong_orientation(self):
        m=reseal(mount(self.slot),orientation='Y')
        with self.assertRaises(Held):self.e.mount(self.slot['slot_id'],m)
    def test_mount_false_qualification(self):
        for key in ('zero_energy','dry_ambient','qualified_fit','registered_transform','supported_carrier'):
            with self.subTest(key=key),self.assertRaises(Held):self.e.mount(self.slot['slot_id'],reseal(mount(self.slot),**{key:False}))
    def test_expired_calibration(self):
        e=SymbolicEpisode(plan())
        with self.assertRaises(Held):e.calibrate(reseal(calibration(),current=False))
    def test_handoff_without_mount(self):
        with self.assertRaises(Held):self.e.handoff('RUN_001',handoff(self.slot,'RUN_001'))
    def test_indeterminate_handoff_routes_release(self):
        self.e.mount(self.slot['slot_id'],mount(self.slot)); self.e.handoff('RUN_001',reseal(handoff(self.slot,'RUN_001'),acceptance='unknown'))
        self.assertEqual(self.e.state,'P15');self.assertEqual(self.e.custody,'service')
    def test_normal_powered_path_no_intermediate_release(self):
        slot=start(self.e);capture(self.e,slot);self.assertEqual(self.e.state,'P14');self.assertEqual(self.e.custody,'service')
    def test_skipped_observation_rejected(self):
        slot=start(self.e)
        with self.assertRaises(Held):self.e.observe('P14',result(slot,'RUN_001'))
    def test_each_powered_stage_can_stop(self):
        for stop_stage in ('P11','P12','P13','P14'):
            e=ready(SymbolicEpisode(plan()));s=start(e)
            if stop_stage in ('P12','P13','P14'):e.observe('P12',transient('RUN_001'))
            if stop_stage in ('P13','P14'):e.observe('P13',stable('RUN_001'))
            if stop_stage=='P14':e.observe('P14',result(s,'RUN_001'))
            e.stop('synthetic fault'); self.assertEqual(e.state,'P15');self.assertEqual(e.custody,'service')
    def test_stop_without_service_rejected(self):
        with self.assertRaises(Held):self.e.stop('fault')
    def test_elapsed_time_not_stability(self):
        start(self.e);self.e.observe('P12',transient('RUN_001'))
        with self.assertRaises(Held):self.e.observe('P13',reseal(stable('RUN_001'),qualified_stable=False,elapsed_minutes=45))
        self.assertEqual(self.e.state,'P15')
    def test_transient_missing_boundary_routes_release(self):
        start(self.e)
        with self.assertRaises(Held):self.e.observe('P12',reseal(transient('RUN_001'),boundary_metadata=False))
        self.assertEqual(self.e.state,'P15')
    def test_invalid_registered_metadata_routes_release(self):
        for key in ('masks_registered','transform_registered','measured_boundaries_present','ambient_present','uncertainty_valid','data_hash_valid'):
            e=ready(SymbolicEpisode(plan()));s=start(e);e.observe('P12',transient('RUN_001'));e.observe('P13',stable('RUN_001'))
            with self.subTest(key=key),self.assertRaises(Held):e.observe('P14',reseal(result(s,'RUN_001'),**{key:False}))
            self.assertEqual(e.state,'P15')
    def test_rotator_requires_transverse_profile(self):
        s=start(self.e,index=2);self.e.observe('P12',transient('RUN_001'));self.e.observe('P13',stable('RUN_001'))
        with self.assertRaises(Held):self.e.observe('P14',reseal(result(s,'RUN_001'),profile_direction='parallel'))
    def test_reference_cannot_be_observation(self):
        s=start(self.e);self.e.observe('P12',transient('RUN_001'));self.e.observe('P13',stable('RUN_001'))
        with self.assertRaises(Held):self.e.observe('P14',reseal(result(s,'RUN_001'),data_origin='source_simulation'))
    def test_release_does_not_retrieve(self):
        s=start(self.e);capture(self.e,s);self.e.release(release(s,'RUN_001'));self.assertEqual(self.e.custody,'service');self.e.retrieve();self.assertEqual(self.e.custody,'handler')
    def test_missing_release_blocks_retrieval(self):
        s=start(self.e);capture(self.e,s)
        with self.assertRaises(Held):self.e.retrieve()
    def test_wrong_release_holds_custody(self):
        s=start(self.e);self.e.stop('fault')
        with self.assertRaises(Held):self.e.release(reseal(release(s,'RUN_001'),run_id='WRONG'))
        self.assertEqual(self.e.state,'SERVICE_CUSTODY_HOLD');self.assertEqual(self.e.custody,'service')
    def test_missing_each_release_attestation(self):
        for key in ('zero_energy','cool','dry','supported_carrier','receiver_accepts','condition_assessed'):
            e=ready(SymbolicEpisode(plan()));s=start(e);e.stop('fault')
            with self.subTest(key=key),self.assertRaises(Held):e.release(reseal(release(s,'RUN_001'),**{key:False}))
            self.assertEqual(e.state,'SERVICE_CUSTODY_HOLD')
    def test_recovery_after_release_hold(self):
        s=start(self.e);self.e.stop('fault')
        with self.assertRaises(Held):self.e.release(reseal(release(s,'RUN_001'),dry=False))
        self.e.release(release(s,'RUN_001','_RECOVERED'));self.e.retrieve();self.assertEqual(self.e.custody,'handler');self.assertEqual(len(self.e.failures),1)
    def test_admin_close_keeps_open_obligation(self):
        start(self.e);self.e.stop('fault');c=self.e.close();self.assertTrue(c['open_service_obligation']);self.assertFalse(c['scientific_success'])
        with self.assertRaises(Held):self.e.retrieve()
    def test_admin_close_blocks_new_work_but_allows_release(self):
        s=start(self.e);self.e.stop('fault');self.e.close();self.e.release(release(s,'RUN_001'));self.e.retrieve()
        with self.assertRaises(Held):self.e.mount(s['slot_id'],mount(s,'_NEW'))
    def test_no_rotation_in_service_custody(self):
        start(self.e);s=self.e.plan[1]
        with self.assertRaises(Held):self.e.mount(s['slot_id'],mount(s))
    def test_no_receiving_new_specimen_during_service(self):
        start(self.e)
        with self.assertRaises(Held):self.e.receive(chain(specimen='NEW'))
    def test_failed_attempt_preserved_on_retry(self):
        s=start(self.e);self.e.stop('fault');self.e.release(release(s,'RUN_001'));self.e.retrieve();start(self.e,run_id='RUN_002',suffix='_RETRY');finish(self.e,s,'RUN_002')
        self.assertEqual(len(self.e.runs),2);self.assertEqual(self.e.runs['RUN_001']['status'],'failed');self.assertEqual(len(self.e.failures),1)
    def test_run_id_cannot_be_reused(self):
        s=start(self.e);self.e.stop('fault');self.e.release(release(s,'RUN_001'));self.e.retrieve();self.e.mount(s['slot_id'],mount(s,'_RETRY'))
        with self.assertRaises(Held):self.e.handoff('RUN_001',reseal(handoff(s,'RUN_001','_RETRY'),receipt_id='OTHER_HANDOFF'))
    def test_full_six_cell_symbolic_episode(self):
        for i in range(6):
            rid='RUN_'+str(i);s=start(self.e,index=i,run_id=rid);finish(self.e,s,rid)
        self.e.reconcile_controls(controls());self.e.assess(assessment());self.e.register_numerical({b:'unexecuted' for b in NUMERICAL_BRANCHES})
        c=self.e.close(success=True,archive_valid=True,dispositions_valid=True);self.assertFalse(c['scientific_success']);self.assertEqual(c['experiments_performed'],0)
    def test_incomplete_matrix_cannot_close_success(self):
        with self.assertRaises(Held):self.e.close(success=True,archive_valid=True,dispositions_valid=True)
    def test_no_success_in_custody(self):
        start(self.e)
        with self.assertRaises(Held):self.e.close(success=True,archive_valid=True,dispositions_valid=True)
    def test_missing_controls(self):
        with self.assertRaises(Held):self.e.assess(assessment())
    def test_zero_denominator_blocks_controls(self):
        with self.assertRaises(Held):self.e.reconcile_controls(reseal(controls(),denominator_safe=False))
    def test_simulated_controls_rejected(self):
        with self.assertRaises(Held):self.e.reconcile_controls(reseal(controls(),data_origin='source_simulation'))
    def test_unmatched_controls_rejected(self):
        with self.assertRaises(Held):self.e.reconcile_controls(reseal(controls(),matched=False))
    def test_numerical_claim_rejected(self):
        self.e.reconcile_controls(controls())
        with self.assertRaises(Held):self.e.assess(reseal(assessment(),numerical_computation_performed=True))
    def test_experimental_claim_rejected(self):
        self.e.reconcile_controls(controls())
        with self.assertRaises(Held):self.e.assess(reseal(assessment(),claim_kind='paper_reproduced'))
    def test_silent_source_hold_resolution_rejected(self):
        self.e.reconcile_controls(controls())
        with self.assertRaises(Held):self.e.assess(reseal(assessment(),source_holds_preserved=False))
    def test_executed_numerical_branch_rejected(self):
        self.e.reconcile_controls(controls());self.e.assess(assessment());d={b:'unexecuted' for b in NUMERICAL_BRANCHES};d['B10']='executed'
        with self.assertRaises(Held):self.e.register_numerical(d)

if __name__=='__main__':unittest.main()
