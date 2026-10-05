#!/usr/bin/env python3
"""Independent negative tests for the symbolic evidence ledger.

Author fixtures supply document-shaped inputs only. All mutations and assertions
below are reviewer-authored. No facility receipt authentication is claimed.
"""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
import contract
spec = importlib.util.spec_from_file_location('independent_author_fixtures', ROOT/'tests'/'fixtures.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


class IndependentRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pristine = fixtures.make_fixture(ROOT)

    def fresh(self, change=None):
        records = copy.deepcopy(self.pristine)
        if change:
            change(records)
        return fixtures.new_ledger(records, ROOT)

    def reject_at(self, operation, mutate):
        receipt_id = 'fixture.receipt.' + operation
        ledger = self.fresh(lambda rs: mutate(rs[receipt_id]))
        fixtures.run_until(ledger, operation)
        before = ledger.completed
        history = ledger.history
        with self.assertRaises(contract.ContractError):
            ledger.propose({'operation_id': operation, 'evidence_id': receipt_id})
        self.assertEqual(ledger.completed, before)
        self.assertEqual(len(ledger.history), len(history) + 1)
        self.assertFalse(ledger.history[-1]['accepted'])
        self.assertFalse(ledger.physical_execution_enabled)

    def test_01_full_symbolic_closeout_retains_holds_and_unrun_models(self):
        ledger = self.fresh()
        fixtures.run_until(ledger)
        self.assertTrue(ledger.design_complete)
        self.assertFalse(ledger.physical_execution_enabled)
        self.assertEqual(len(ledger.completed), 13)
        self.assertEqual(ledger.final_branch_dispositions()['E04'], 'HELD')
        for branch in ('N01', 'N02', 'N03', 'N04'):
            self.assertEqual(ledger.final_branch_dispositions()[branch], 'UNRUN')
        for branch in ('C02', 'C03', 'C04', 'E05'):
            self.assertEqual(ledger.final_branch_dispositions()[branch], 'SOURCE_CONTEXT_ONLY')
        self.assertTrue(all(x['physical_execution'] is False for x in ledger.completed.values()))

    def test_02_actor_cannot_supply_receipt_or_operational_fields(self):
        for field in ('payload', 'physical_execution', 'device_command', 'origin', 'receipt'):
            with self.subTest(field=field):
                ledger = self.fresh()
                action = {'operation_id': 'R01', 'evidence_id': 'fixture.receipt.R01', field: 'forbidden'}
                with self.assertRaises(contract.ContractError):
                    ledger.propose(action)
                self.assertFalse(ledger.completed)
                self.assertEqual(len(ledger.history), 1)

    def test_03_malformed_common_fields_fail_closed_and_are_logged(self):
        for field in ('origin', 'status'):
            for bad in ({}, [], None, 7, True):
                with self.subTest(field=field, value=bad):
                    self.reject_at('R01', lambda r, f=field, b=bad: r.update({f:b}))
        self.reject_at('R01', lambda r: r['branch_results'].update(E01={}))
        self.reject_at('R05', lambda r: r['payload']['sphere_lots'][0].pop('nominal_diameter_um'))

    def test_04_campaign_epoch_plan_and_semantic_drift_are_rejected(self):
        for field in ('campaign_id', 'epoch', 'frozen_plan_id', 'semantic_core_sha256'):
            with self.subTest(field=field):
                self.reject_at('R01', lambda r, f=field: r.update({f:'foreign'}))

    def test_05_qualification_and_dependency_contracts_are_enforced(self):
        self.reject_at('R01', lambda r: r['qualification_refs'].update(U01=None))
        self.reject_at('R03', lambda r: r['input_receipt_hashes'].update(R02='0'*64))
        ledger = self.fresh()
        with self.assertRaises(contract.ContractError):
            ledger.propose({'operation_id':'R03','evidence_id':'fixture.receipt.R03'})
        self.assertFalse(ledger.completed)
        self.assertEqual(len(ledger.history), 1)

    def test_06_source_scene_or_actor_records_never_become_observations(self):
        for origin in ('source_report', 'scene_render', 'actor_generated'):
            with self.subTest(origin=origin):
                self.reject_at('R07', lambda r, o=origin: r['payload']['E01']['optical'].update(origin=o))
        self.reject_at('R07', lambda r: r['payload']['E01']['optical'].update(outcome='resolved'))
        self.reject_at('R12', lambda r: r['payload']['N01'].update(simulation_run=True))

    def test_07_unknown_star_values_and_held_evidence_cannot_be_filled(self):
        self.reject_at('R05', lambda r: r['payload'].update(star_sphere_diameter_um=4.74))
        self.reject_at('R03', lambda r: r['payload']['E04'].update(state_id='fabricated.child'))
        self.reject_at('R06', lambda r: r['payload']['E04'].update(specimen_id='foreign.held.specimen'))
        self.reject_at('R08', lambda r: r['payload']['E04'].update(optical={'fabricated':True}))
        self.reject_at('R02', lambda r: r['branch_results'].update(E04='CONTRACT_REVIEWED'))

    def test_08_planes_raw_record_identity_and_child_lineage_are_checked(self):
        self.reject_at('R04', lambda r: r['payload']['E01']['reference'].update(raw_record_sha256='not-a-hash'))
        self.reject_at('R07', lambda r: r['payload']['E01'].update(virtual_frame='FRAME_OBJECT'))
        self.reject_at('R07', lambda r: r['payload']['E01']['optical'].update(specimen_id='wrong.specimen'))
        self.reject_at('R03', lambda r: r['payload']['E01'].update(state_id=r['payload']['E01']['parent_state_id']))

    def test_09_controls_retain_focus_objective_and_contact_state_lineage(self):
        self.reject_at('R09', lambda r: r['payload']['SIL_2p5mm'].update(objective_magnification=80))
        self.reject_at('R09', lambda r: r['payload']['SIL_0p5mm']['optical'].update(focus_receipt_id=r['payload']['bare']['optical']['focus_receipt_id']))
        self.reject_at('R09', lambda r: r['payload']['SIL_0p5mm']['optical'].update(state_id='unqualified.contact.state'))
        self.reject_at('R09', lambda r: r['payload']['SIL_0p5mm'].update(contact_receipt_id='unqualified.contact.receipt'))
        self.reject_at('R09', lambda r: r['payload']['SIL_0p5mm']['optical'].update(specimen_id='unqualified.specimen'))

    def test_10_frozen_metric_and_honest_pairing_are_preserved(self):
        self.reject_at('R11', lambda r: r['payload']['E01'].update(metric_policy_id='post.hoc.policy'))
        self.reject_at('R11', lambda r: r['payload']['E01'].update(correspondence='exact_state_ROI'))
        self.reject_at('R11', lambda r: r['payload']['E01'].update(resolution_certified=True))

    def test_11_archive_cannot_promote_status_or_swap_specimens(self):
        self.reject_at('R13', lambda r: r['payload']['branch_dispositions'].update(E04='CONTRACT_REVIEWED'))
        self.reject_at('R13', lambda r: r['payload']['branch_dispositions'].update(N01='CONTRACT_REVIEWED'))
        self.reject_at('R13', lambda r: r['payload']['specimen_dispositions']['E01'].update(specimen_id='wrong.specimen'))
        self.reject_at('R13', lambda r: r['payload']['archive_receipt_hashes'].pop('R02'))

    def test_12_receipts_and_exposed_snapshots_are_immutable(self):
        records = copy.deepcopy(self.pristine)
        ledger = fixtures.new_ledger(records, ROOT)
        records['fixture.receipt.R01']['payload']['publisher_exports'] = True
        ledger.propose({'operation_id':'R01','evidence_id':'fixture.receipt.R01'})
        completed = ledger.completed
        completed['R01']['receipt']['payload']['publisher_exports'] = True
        history = ledger.history
        history[0]['accepted'] = False
        self.assertFalse(ledger.completed['R01']['receipt']['payload']['publisher_exports'])
        self.assertTrue(ledger.history[0]['accepted'])
        with self.assertRaises(contract.ContractError):
            ledger.propose({'operation_id':'R01','evidence_id':'fixture.receipt.R01'})
        self.assertEqual(len(ledger.history), 2)

    def test_13_retry_budget_retains_all_rejections(self):
        ledger = self.fresh()
        for _ in range(2):
            with self.assertRaises(contract.ContractError):
                ledger.propose({'operation_id':'R01','evidence_id':'not.supplied'})
        with self.assertRaises(contract.ContractError):
            ledger.propose({'operation_id':'R01','evidence_id':'fixture.receipt.R01'})
        self.assertEqual(len(ledger.history), 3)
        self.assertFalse(ledger.completed)
        for index, event in enumerate(ledger.history):
            self.assertFalse(event['accepted'])
            if index:
                self.assertEqual(event['prior_event_hash'], contract.digest(ledger.history[index-1]))

    def all_held_records(self):
        records = {}
        ledger = fixtures.new_ledger({}, ROOT)
        for index in range(1, 14):
            operation = f'R{index:02}'
            receipt = copy.deepcopy(self.pristine['fixture.receipt.' + operation])
            receipt['input_receipt_hashes'] = {key:ledger.completed[key]['receipt_hash'] for key in receipt['input_receipt_hashes']}
            if operation != 'R13':
                receipt['status'] = 'HOLD'
                receipt['qualification_refs'] = {key:None for key in receipt['qualification_refs']}
                receipt['payload'] = {'reason':'qualification_missing','safe_state_receipt_id':'fixture.no_activity.safe'}
                receipt['branch_results'] = {branch:('UNRUN' if branch.startswith('N') else 'HELD') for branch in receipt['branch_results']}
            else:
                receipt['payload']['archive_receipt_hashes'] = {key:row['receipt_hash'] for key,row in ledger.completed.items()}
                receipt['payload']['branch_dispositions'] = ledger.final_branch_dispositions()
                receipt['payload']['specimen_dispositions'] = {branch:{'specimen_id':None,'destination_id':None,'disposition':'not_received'} for branch in contract.TARGETS}
                receipt['branch_results'] = copy.deepcopy(receipt['payload']['branch_dispositions'])
            records[receipt['receipt_id']] = receipt
            ledger = fixtures.new_ledger(records, ROOT)
            for key,row in records.items():
                ledger.propose({'operation_id':row['operation_id'],'evidence_id':key})
        return records

    def test_15_all_held_intake_closes_without_invented_specimens(self):
        records = self.all_held_records()
        ledger = fixtures.new_ledger(records, ROOT)
        fixtures.run_until(ledger)
        self.assertTrue(ledger.design_complete)
        self.assertFalse(ledger.physical_execution_enabled)
        dispositions = ledger.completed['R13']['receipt']['payload']['specimen_dispositions']
        self.assertTrue(all(row == {'specimen_id':None,'destination_id':None,'disposition':'not_received'} for row in dispositions.values()))
        records['fixture.receipt.R13']['payload']['specimen_dispositions']['E01'] = {'specimen_id':'invented.specimen','destination_id':'invented.archive','disposition':'archive'}
        ledger = fixtures.new_ledger(records, ROOT)
        fixtures.run_until(ledger, 'R13')
        with self.assertRaises(contract.ContractError):
            ledger.propose({'operation_id':'R13','evidence_id':'fixture.receipt.R13'})
        self.assertFalse(ledger.design_complete)

    def test_14_closeout_cannot_erase_a_rejected_attempt(self):
        ledger = self.fresh()
        with self.assertRaises(contract.ContractError):
            ledger.propose({'invalid':'action'})
        fixtures.run_until(ledger, 'R13')
        with self.assertRaises(contract.ContractError):
            ledger.propose({'operation_id':'R13','evidence_id':'fixture.receipt.R13'})
        self.assertFalse(ledger.design_complete)
        self.assertFalse(ledger.history[0]['accepted'])


if __name__ == '__main__':
    unittest.main()
