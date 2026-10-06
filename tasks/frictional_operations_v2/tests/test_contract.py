import copy
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from contract import EvidenceLedger,ContractError,digest
from fixtures import make_fixture

class ContractTests(unittest.TestCase):
    def setUp(self):self.plan,self.receipts,self.order=make_fixture()
    def ledger(self):return EvidenceLedger(ROOT,'CAM_SYNTHETIC','EPOCH_1',self.plan,self.receipts)
    def before(self,eid):
        l=self.ledger()
        for a in self.order:
            if a['evidence_id']==eid:return l,a
            l.propose(a)
        self.fail('unknown test evidence')
    def reject(self,eid,mutate):
        mutate(self.receipts[eid]);l,a=self.before(eid)
        with self.assertRaises(ContractError):l.propose(a)
        self.assertFalse(l.history[-1]['accepted']);self.assertFalse(l.physical_execution_enabled)
    def test_complete_contract_only(self):
        l=self.ledger()
        for a in self.order:l.propose(a)
        self.assertTrue(l.design_complete);self.assertEqual(len(l.jobs),15);self.assertEqual(len(l.closeouts),15);self.assertFalse(l.physical_execution_enabled)
    def test_closeout_before_next_independent_branch(self):
        l,a=self.before('REC_R06');self.assertEqual(len(l.closeouts),3);self.assertNotIn('R08',l.completed)
    def test_hold_and_failed_job_closure(self):
        self.plan,self.receipts,self.order=make_fixture(held=('R06','R08','R09'));l=self.ledger()
        for a in self.order:l.propose(a)
        self.assertTrue(l.design_complete);self.assertEqual(l.closeouts['RUN_JOB_CON_RATE']['receipt']['payload']['disposition'],'quarantine')
    def test_actor_cannot_supply_values(self):
        l=self.ledger()
        with self.assertRaises(ContractError):l.propose(dict(self.order[0],payload={'rate':1}))
    def test_evaluator_copy_isolation(self):
        l=self.ledger();self.receipts['REC_R01']['payload']['publisher_exports']=True;l.propose(self.order[0]);h=l.history;h.clear();self.assertEqual(len(l.history),1)
    def test_source_outcome_origin_rejected(self):self.reject('REC_R05',lambda r:r.update(origin='source_reference'))
    def test_source_outcome_not_generated(self):self.reject('REC_R05',lambda r:r['payload']['runs'][0].update(scientific_outcome='bubble_observed'))
    def test_synthetic_acquisition_rejected(self):self.reject('REC_R05',lambda r:r['payload']['runs'][0]['pressure_raw'].update(raw_acquisition=True))
    def test_stale_campaign(self):self.reject('REC_R01',lambda r:r.update(campaign_id='OTHER'))
    def test_plan_drift(self):self.reject('REC_R01',lambda r:r.update(frozen_plan_sha256='0'*64))
    def test_semantic_drift(self):self.reject('REC_R01',lambda r:r.update(semantic_core_sha256='0'*64))
    def test_dependency_hash(self):self.reject('REC_R05',lambda r:r['input_receipt_hashes'].update(R03='0'*64))
    def test_missing_dependency(self):
        l=self.ledger()
        with self.assertRaises(ContractError):l.propose({'operation_id':'R05','evidence_id':'REC_R05'})
    def test_missing_qualification(self):self.reject('REC_R04',lambda r:r['qualification_refs'].update(U01=None))
    def test_physical_execution(self):self.reject('REC_R01',lambda r:r.update(physical_execution=True))
    def test_wrong_host(self):self.reject('REC_R03',lambda r:r['payload']['preparations'][5].update(host_lot_id='HOST'))
    def test_reused_state(self):self.reject('REC_R03',lambda r:r['payload']['preparations'][0].update(settled_state_id=r['payload']['preparations'][0]['loaded_state_id']))
    def test_alias_aliquot(self):self.reject('REC_R03',lambda r:r['payload']['preparations'][1].update(aliquot_id=r['payload']['preparations'][0]['aliquot_id']))
    def test_cell_variant_mismatch(self):self.reject('REC_R03',lambda r:r['payload']['preparations'][0].update(cell_id='CELL_cell_19mm'))
    def test_movie_clock(self):self.reject('REC_R04',lambda r:r['payload'].update(clock_domain='movie_file_time'))
    def test_camera_pressure_mismatch(self):self.reject('REC_R05',lambda r:r['payload']['runs'][0]['image_raw'].update(clock_map_id='OTHER_CLOCK'))
    def test_raw_origin_laundering(self):self.reject('REC_R05',lambda r:r['payload']['runs'][0]['image_raw'].update(origin='external_qualified_record'))
    def test_duplicate_raw_hash(self):self.reject('REC_R05',lambda r:r['payload']['runs'][0]['image_raw'].update(sha256=r['payload']['runs'][0]['pressure_raw']['sha256']))
    def test_cross_route_raw_id_reuse(self):self.reject('REC_R06',lambda r:r['payload']['runs'][0]['image_raw'].update(raw_evidence_id=self.receipts['REC_R05']['payload']['runs'][0]['image_raw']['raw_evidence_id']))
    def test_changed_analysis_policy(self):self.reject('REC_R08',lambda r:r['payload']['derived_records'][0].update(analysis_policy_id='OTHER_POLICY'))
    def test_raw_lineage(self):self.reject('REC_R08',lambda r:r['payload']['derived_records'][0]['raw_hashes'].update(image_raw='0'*64))
    def test_pseudoreplication(self):self.reject('REC_R09',lambda r:r['payload'].update(within_image_samples_are_repeats=True))
    def test_sparse_negative(self):self.reject('REC_R09',lambda r:r['payload'].update(missing_grid_cells_are_negative=True))
    def test_sensitivity_not_ci(self):self.reject('REC_R09',lambda r:r['payload'].update(parameter_sensitivity_is_confidence_interval=True))
    def test_control_scope(self):self.reject('REC_R09',lambda r:r['payload']['control_links']['CR04'].update(condition_ids=['CON_BASE']))
    def test_control_promoted(self):self.reject('REC_R09',lambda r:r['payload']['control_links']['CR07'].update(evidence_kind='independent_experiments'))
    def test_missing_low_rate_pair(self):
        self.plan['condition_plan']=[x for x in self.plan['condition_plan'] if x['condition_id']!='CON_LOW']
        with self.assertRaises(ContractError):self.ledger()
    def test_borrowed_attribution(self):self.reject('REC_R10',lambda r:r['payload'].update(porous_medium_attribution='this_paper'))
    def test_silent_sign_repair(self):self.reject('REC_R10',lambda r:r['payload'].update(boyle_sign_resolved=True))
    def test_safe_release_missing(self):self.reject('CLOSE_RUN_JOB_CON_LOW',lambda r:r['payload'].update(safe_release_receipt_id=None))
    def test_job_identity_mismatch(self):self.reject('CLOSE_RUN_JOB_CON_LOW',lambda r:r['payload'].update(subject_id='OTHER'))
    def test_open_job_blocks_archive(self):
        l=self.ledger()
        for a in self.order:
            if a['evidence_id']=='CLOSE_RUN_JOB_CON_LOW':continue
            if a['operation_id']=='R12':
                with self.assertRaises(ContractError):l.propose(a)
            else:l.propose(a)
    def test_hold_does_not_promote_branch(self):self.reject('REC_R12',lambda r:r['payload']['branch_dispositions'].update(B06='CONTRACT_REVIEWED'))
    def test_failed_attempts_archive_required(self):
        l=self.ledger()
        with self.assertRaises(ContractError):l.propose({'operation_id':'R99','evidence_id':'missing'})
        for a in self.order:
            if a['operation_id']=='R12':
                with self.assertRaises(ContractError):l.propose(a)
            else:l.propose(a)
    def test_replay(self):
        l=self.ledger();l.propose(self.order[0])
        with self.assertRaises(ContractError):l.propose(self.order[0])
    def test_bounded_digital_attempts(self):
        self.receipts['REC_R01']['payload']['publisher_exports']=True;l=self.ledger()
        for _ in range(3):
            with self.assertRaises(ContractError):l.propose(self.order[0])
        self.assertIn('budget',l.history[-1]['reason'])
    def test_missing_viscosity_control_pair(self):
        self.plan['condition_plan']=[x for x in self.plan['condition_plan'] if x['condition_id']!='CON_BASE']
        with self.assertRaises(ContractError):self.ledger()
    def test_boolean_not_page_count(self):self.reject('REC_R01',lambda r:r['payload'].update(main_pages=True))
    def test_nonfinite_json(self):
        l=self.ledger()
        with self.assertRaises(ContractError):l.propose({'operation_id':float('nan'),'evidence_id':'REC_R01'})
    def test_unregistered_closeout(self):
        l=self.ledger()
        with self.assertRaises(ContractError):l.propose({'operation_id':'R11','evidence_id':'CLOSE_RUN_JOB_CON_LOW'})

if __name__=='__main__':unittest.main()
