import copy
import unittest
from fixtures import *
from contract import ContractError

class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.receipts=make_fixture()
    def reject(self,op,change):
        receipts=copy.deepcopy(self.receipts);change(receipts[f'fixture.receipt.{op}'])
        ledger=new_ledger(receipts);run_until(ledger,op)
        before=len(ledger.history)
        with self.assertRaises(ContractError):ledger.propose(dict(operation_id=op,evidence_id=f'fixture.receipt.{op}'))
        self.assertEqual(len(ledger.history),before+1);self.assertFalse(ledger.history[-1]['accepted']);self.assertNotIn(op,ledger.completed)
    def test_complete_design_with_star_hold(self):
        ledger=run_until(new_ledger(self.receipts))
        self.assertTrue(ledger.design_complete);self.assertFalse(ledger.physical_execution_enabled)
        self.assertEqual(ledger.final_branch_dispositions()['E04'],'HELD')
        self.assertEqual(ledger.final_branch_dispositions()['E05'],'SOURCE_CONTEXT_ONLY')
        self.assertEqual(ledger.final_branch_dispositions()['N04'],'UNRUN')
    def test_common_context_and_unknown_fields(self):
        changes=[lambda r:r.update(origin='source_report'),lambda r:r.update(campaign_id='other'),lambda r:r.update(epoch='later'),lambda r:r.update(frozen_plan_id='other'),lambda r:r.update(semantic_core_sha256='0'*64),lambda r:r.update(physical_execution=True),lambda r:r.update(beam_voltage=1),lambda r:r.update(status='COMPLETE'),lambda r:r.update(qualification_refs={'U01':None})]
        for change in changes:
            with self.subTest(change=change):self.reject('R01',change)
    def test_unhashable_nested_values_fail_closed(self):
        for field in ['origin','status']:
            with self.subTest(field=field):self.reject('R01',lambda r:r.update({field:{}}))
        self.reject('R01',lambda r:r['branch_results'].update(E01={}))
        self.reject('R05',lambda r:r['payload']['sphere_lots'].__setitem__(0,{}))
    def test_foreign_receipt_identity_rejected_at_input(self):
        receipts=copy.deepcopy(self.receipts);receipts['fixture.receipt.R01']['receipt_id']='foreign'
        with self.assertRaises(ContractError):new_ledger(receipts)
    def test_actor_payload_and_fake_receipt(self):
        for action in [dict(operation_id='R01',evidence_id='made.up'),dict(operation_id='R01',evidence_id='fixture.receipt.R01',payload={}),dict(operation_id='OPERATE',evidence_id='fixture.receipt.R01'),{'operation_id':'R01'}]:
            ledger=new_ledger(self.receipts)
            with self.assertRaises(ContractError):ledger.propose(action)
            self.assertEqual(len(ledger.history),1)
    def test_budget_and_dependency(self):
        ledger=new_ledger(self.receipts)
        for _ in range(3):
            with self.assertRaises(ContractError):ledger.propose(dict(operation_id='R02',evidence_id='fixture.receipt.R02'))
        self.assertIn('budget',ledger.history[-1]['reason'])
    def test_duplicate_stage(self):
        ledger=new_ledger(self.receipts);action=dict(operation_id='R01',evidence_id='fixture.receipt.R01');ledger.propose(action)
        with self.assertRaises(ContractError):ledger.propose(action)
    def test_receipt_input_is_snapshot(self):
        receipts=copy.deepcopy(self.receipts);ledger=new_ledger(receipts);receipts['fixture.receipt.R01']['physical_execution']=True
        ledger.propose(dict(operation_id='R01',evidence_id='fixture.receipt.R01'))
    def test_output_is_copy(self):
        ledger=new_ledger(self.receipts);r=ledger.propose(dict(operation_id='R01',evidence_id='fixture.receipt.R01'));r['receipt']['physical_execution']=True
        history=ledger.history;history.clear();done=ledger.completed;done.clear()
        self.assertEqual(len(ledger.history),1);self.assertEqual(len(ledger.completed),1);self.assertFalse(ledger.completed['R01']['physical_execution'])
    def test_source_and_material_gates(self):
        self.reject('R01',lambda r:r['payload'].update(publisher_exports=True))
        self.reject('R01',lambda r:r['payload'].update(main_pages=True))
        self.reject('R02',lambda r:r['payload']['E02'].update(material_id='M02'))
        self.reject('R02',lambda r:r['payload']['E04'].update(status='CONTRACT_REVIEWED',surface_identity='unresolved',identity_receipt_id='fake'))
        self.reject('R03',lambda r:r['payload']['E01'].update(state_id='fixture.E01.received'))
        self.reject('R03',lambda r:r['payload']['E04'].update(certificate_id='fake'))
    def test_spheres_and_controls(self):
        self.reject('R05',lambda r:r['payload'].update(star_sphere_diameter_um=4.74))
        self.reject('R05',lambda r:r['payload']['sphere_lots'][0].update(nominal_diameter_um=True))
        self.reject('R05',lambda r:r['payload']['sil_controls']['SIL_2p5mm'].update(objective_magnification=80))
        self.reject('R06',lambda r:r['payload']['E01'].update(sphere_lot_id='unqualified'))
        self.reject('R06',lambda r:r['payload']['E04'].update(child_state_id='invented'))
        self.reject('R06',lambda r:r['payload']['C01'].update(bare_state_id='fixture.E03.sphere'))
    def test_measurement_identity_and_mode(self):
        for field,value in [('mode','reflection'),('frame_id','FRAME_VIRTUAL'),('state_id','wrong'),('specimen_id','wrong'),('origin','source_report'),('outcome','resolved'),('raw_record_sha256','x')]:
            with self.subTest(field=field):self.reject('R07',lambda r:r['payload']['E01']['optical'].update({field:value}))
        self.reject('R08',lambda r:r['payload']['E04'].update(optical=measurement('E04','optical','fake')))
    def test_bare_and_sil_linkage(self):
        self.reject('R09',lambda r:r['payload']['bare']['optical'].update(state_id='fixture.E03.sphere'))
        self.reject('R09',lambda r:r['payload']['SIL_0p5mm']['optical'].update(state_id='foreign'))
        self.reject('R09',lambda r:r['payload']['SIL_2p5mm'].update(contact_receipt_id='foreign'))
        self.reject('R09',lambda r:r['payload']['SIL_0p5mm']['optical'].update(focus_receipt_id='fixture.focus.E03.bare'))
    def test_claims_and_theory_never_promoted(self):
        self.reject('R10',lambda r:r['payload']['E05'].update(evidence_class='figure_backed'))
        self.reject('R10',lambda r:r['payload']['C03'].update(new_data=True))
        self.reject('R12',lambda r:r['payload']['N01'].update(simulation_run=True))
    def test_cross_device_and_metric_guards(self):
        self.reject('R11',lambda r:r['payload']['E01'].update(correspondence='exact_state_ROI'))
        self.reject('R11',lambda r:r['payload']['E01'].update(optical_record_id='fixture.E02.optical.sphere'))
        self.reject('R11',lambda r:r['payload']['E01'].update(metric_policy_id='post.hoc.metric'))
        self.reject('R11',lambda r:r['payload']['E02'].update(resolution_certified=True))
    def test_branch_and_dependency_binding(self):
        self.reject('R08',lambda r:r['branch_results'].update(E04='CONTRACT_REVIEWED'))
        self.reject('R10',lambda r:r['branch_results'].update(E05='CONTRACT_REVIEWED'))
        self.reject('R03',lambda r:r['input_receipt_hashes'].update(R02='0'*64))
    def test_closeout_cannot_promote_or_omit(self):
        self.reject('R13',lambda r:r['payload']['branch_dispositions'].update(E04='CONTRACT_REVIEWED'))
        self.reject('R13',lambda r:r['payload']['specimen_dispositions']['E01'].update(specimen_id='foreign'))
        self.reject('R13',lambda r:r['payload']['specimen_dispositions']['E04'].update(disposition='archive'))
        self.reject('R13',lambda r:r['payload']['archive_receipt_hashes'].pop('R04'))
        self.reject('R13',lambda r:r['payload'].update(scientific_execution_complete=True))
    def test_post_closeout_actions_rejected(self):
        ledger=run_until(new_ledger(self.receipts))
        with self.assertRaises(ContractError):ledger.propose(dict(operation_id='R01',evidence_id='fixture.receipt.R01'))
        self.assertEqual(len(ledger.history),14)

if __name__=='__main__':unittest.main()
