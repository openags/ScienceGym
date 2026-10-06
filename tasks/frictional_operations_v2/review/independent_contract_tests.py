"""Independent adversarial bookkeeping review; no measurements or device operations.

The producer's synthetic fixture supplies only a known-good input skeleton. All
mutations, expectations and review assertions below were authored independently.
"""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
from contract import ContractError, EvidenceLedger, digest, load_contract
from fixtures import make_fixture


class IndependentContractTests(unittest.TestCase):
    def setUp(self):
        self.plan, self.receipts, self.order = make_fixture()

    def ledger(self):
        return EvidenceLedger(ROOT, 'CAM_SYNTHETIC', 'EPOCH_1', self.plan, self.receipts)

    def before(self, target):
        ledger = self.ledger()
        for action in self.order:
            if action['evidence_id'] == target:
                return ledger, action
            ledger.propose(action)
        self.fail('Unknown fixture target')

    def reject(self, target, mutate):
        mutate(self.receipts[target])
        ledger, action = self.before(target)
        before = (ledger.completed, ledger.jobs, ledger.closeouts)
        with self.assertRaises(ContractError):
            ledger.propose(action)
        self.assertEqual(before, (ledger.completed, ledger.jobs, ledger.closeouts))
        self.assertFalse(ledger.history[-1]['accepted'])
        self.assertFalse(ledger.physical_execution_enabled)

    def test_positive_whole_ledger_never_becomes_science(self):
        ledger = self.ledger()
        for action in self.order:
            ledger.propose(action)
        self.assertTrue(ledger.design_complete)
        self.assertEqual(set(ledger.jobs), set(ledger.closeouts))
        final = ledger.completed['R12']['receipt']['payload']
        self.assertEqual(final['qualification_holds'], ['U%02d' % i for i in range(1, 21)])
        self.assertFalse(final['scientific_execution_complete'])
        self.assertEqual(set(final['branch_dispositions'].values()), {'UNRUN', 'SOURCE_CONTEXT_ONLY'})

    def test_preparation_closeout_can_precede_instrument_and_all_measurements(self):
        ledger, _ = self.before('REC_R04')
        job = self.receipts['REC_R03']['service_jobs'][0]['job_id']
        action = {'operation_id': 'R11', 'evidence_id': 'CLOSE_' + job}
        ledger.propose(action)
        self.assertIn(job, ledger.closeouts)
        self.assertNotIn('R04', ledger.completed)
        self.assertNotIn('R08', ledger.completed)

    def test_external_record_reference_is_not_scientific_certification(self):
        receipt = self.receipts['REC_R05']
        receipt['origin'] = 'external_qualified_record'
        for run in receipt['payload']['runs']:
            for field in ('pressure_raw', 'image_raw'):
                run[field].update(origin='external_qualified_record', raw_acquisition=True,
                                  record_kind='external_raw_record_reference')
        ledger, action = self.before('REC_R05')
        ledger.propose(action)
        self.assertFalse(ledger.physical_execution_enabled)
        self.assertEqual(ledger.final_branch_dispositions()['B02'], 'UNRUN')

    def test_caller_cannot_mutate_accepted_evidence(self):
        ledger = self.ledger()
        result = ledger.propose(self.order[0])
        result['receipt']['payload']['publisher_exports'] = True
        completed = ledger.completed
        completed['R01']['receipt']['payload']['main_pages'] = 0
        self.assertFalse(ledger.completed['R01']['receipt']['payload']['publisher_exports'])
        self.assertEqual(ledger.completed['R01']['receipt']['payload']['main_pages'], 8)

    def test_rejection_chain_links_exact_previous_events(self):
        ledger = self.ledger()
        for value in (None, [], {}, {'operation_id': 'R99', 'evidence_id': 'NOPE'}):
            with self.assertRaises(ContractError):
                ledger.propose(value)
        events = ledger.history
        self.assertIsNone(events[0]['prior_event_hash'])
        for prior, event in zip(events, events[1:]):
            self.assertEqual(event['prior_event_hash'], digest(prior))

    def test_shape_mutations_reject_without_partial_commit(self):
        cases = [
            ('payload', None), ('payload', []), ('branch_results', []),
            ('qualification_refs', []), ('input_receipt_hashes', []),
            ('service_jobs', [None]), ('service_jobs', [{'job_id': []}]),
            ('origin', []), ('status', {}), ('physical_execution', 0),
        ]
        for key, value in cases:
            with self.subTest(field=key, value=value):
                self.setUp()
                self.reject('REC_R05', lambda row, k=key, v=value: row.update({k: v}))

    def test_bad_actor_identifiers_and_noncanonical_values(self):
        for value in ('', '../R01', 'R01\n', 'R' * 129, True, 1, {}, []):
            with self.subTest(value=value):
                ledger = self.ledger()
                with self.assertRaises(ContractError):
                    ledger.propose({'operation_id': value, 'evidence_id': 'REC_R01'})
        for value in (float('nan'), float('inf'), float('-inf')):
            ledger = self.ledger()
            with self.assertRaises(ContractError):
                ledger.propose({'operation_id': 'R01', 'evidence_id': value})

    def test_epoch_and_operation_identity_mismatch(self):
        for field, value in [('epoch', 'EPOCH_OLD'), ('operation_id', 'R06')]:
            with self.subTest(field=field):
                self.setUp()
                self.reject('REC_R05', lambda row, f=field, v=value: row.update({f: v}))

    def test_exact_receipt_fields_reject_hidden_observations(self):
        self.reject('REC_R05', lambda row: row.update(measured_morphology='coral'))

    def test_spent_state_cannot_alias_other_preparation_state(self):
        other = self.receipts['REC_R03']['payload']['preparations'][1]['settled_state_id']
        self.reject('REC_R05', lambda row: row['payload']['runs'][0].update(spent_state_id=other))

    def test_spent_state_cannot_reuse_own_loaded_state(self):
        prior = self.receipts['REC_R03']['payload']['preparations'][0]['loaded_state_id']
        self.reject('REC_R05', lambda row: row['payload']['runs'][0].update(spent_state_id=prior))

    def test_requested_and_observed_condition_references_are_distinct(self):
        self.reject('REC_R05', lambda row: row['payload']['runs'][0].update(
            observed_condition_receipt_id=row['payload']['runs'][0]['requested_condition_receipt_id']))

    def test_derived_ids_are_unique_across_runs(self):
        self.reject('REC_R08', lambda row: row['payload']['derived_records'][1].update(
            derived_evidence_id=row['payload']['derived_records'][0]['derived_evidence_id']))

    def test_job_kind_matches_route(self):
        for target, bad_kind in [('REC_R03', 'measurement'), ('REC_R04', 'preparation'), ('REC_R05', 'qualification')]:
            with self.subTest(target=target):
                self.setUp()
                self.reject(target, lambda row, kind=bad_kind: row['service_jobs'][0].update(job_kind=kind))

    def test_reviewed_job_cannot_close_as_not_started(self):
        self.reject('CLOSE_RUN_JOB_CON_LOW', lambda row: row['payload'].update(disposition='not_started'))

    def test_closeout_binds_whole_origin_receipt(self):
        self.reject('CLOSE_RUN_JOB_CON_LOW', lambda row: row['payload'].update(job_receipt_hash='a' * 64))

    def test_failed_job_cannot_return_to_service(self):
        self.plan, self.receipts, self.order = make_fixture(held=('R06', 'R08', 'R09'))
        self.reject('CLOSE_RUN_JOB_CON_RATE', lambda row: row['payload'].update(disposition='return_contained'))

    def test_failed_route_job_cannot_be_accepted_service(self):
        self.reject('REC_R05', lambda row: row['service_jobs'][0].update(job_status='failed'))

    def test_service_job_replay_cross_route_rejects(self):
        prior = self.receipts['REC_R05']['service_jobs'][0]['job_id']
        def mutate(row):
            row['service_jobs'][0]['job_id'] = prior
            row['payload']['runs'][0]['service_job_id'] = prior
        self.reject('REC_R06', mutate)

    def test_grain_and_host_lot_ids_do_not_alias(self):
        self.reject('REC_R02', lambda row: row['payload']['grain_lot'].update(
            lot_id=row['payload']['host_lot']['lot_id']))

    def test_batch_identity_cannot_have_different_host_parents(self):
        def mutate(row):
            preps = row['payload']['preparations']
            baseline = next(x for x in preps if x['material_id'] == 'M03')
            altered = next(x for x in preps if x['material_id'] == 'M07')
            altered['dispersion_batch_id'] = baseline['dispersion_batch_id']
        self.reject('REC_R03', mutate)

    def test_missing_low_high_comparison_partner_rejects_plan(self):
        self.plan['condition_plan'] = [x for x in self.plan['condition_plan'] if x['condition_id'] != 'CON_HIGH']
        with self.assertRaises(ContractError):
            self.ledger()

    def test_wrong_branch_condition_roles_reject_plan(self):
        for branch, role in [('B03', 'high_filling'), ('B05', 'high_filling'), ('B07', 'sweep')]:
            with self.subTest(branch=branch):
                self.setUp()
                next(x for x in self.plan['condition_plan'] if x['branch_id'] == branch)['condition_role'] = role
                with self.assertRaises(ContractError):
                    self.ledger()

    def test_each_required_experimental_branch_cannot_disappear(self):
        for branch in ('B02', 'B03', 'B05', 'B06', 'B07'):
            with self.subTest(branch=branch):
                self.setUp()
                self.plan['condition_plan'] = [x for x in self.plan['condition_plan'] if x['branch_id'] != branch]
                with self.assertRaises(ContractError):
                    self.ledger()

    def test_malformed_plan_rows_raise_contract_error(self):
        for value in (None, [], 'bad', {}, {'condition_id': []}):
            with self.subTest(value=value):
                self.setUp()
                self.plan['condition_plan'][0] = value
                with self.assertRaises(ContractError):
                    self.ledger()

    def test_source_counts_and_rights_cannot_drift(self):
        for key, value in [('main_pages', 7), ('figures', 4), ('equations', 8),
                           ('supplement_descriptions', 1), ('rights_scope', 'source_media_allowed'),
                           ('conflicts_preserved', ['C01', 'C03', 'C04'])]:
            with self.subTest(field=key):
                self.setUp()
                self.reject('REC_R01', lambda row, k=key, v=value: row['payload'].update({k: v}))

    def test_no_fake_science_promotion_in_analysis_and_model_routes(self):
        for target, field in [('REC_R08', 'metrics_generated'), ('REC_R08', 'source_plot_used_as_raw')]:
            with self.subTest(field=field):
                self.setUp()
                self.reject(target, lambda row, f=field: row['payload']['derived_records'][0].update({f: True}))
        for target, field in [('REC_R09', 'model_executed'), ('REC_R09', 'source_threshold_is_acceptance_band'),
                              ('REC_R10', 'model_executed'), ('REC_R10', 'borrowed_media_exported'),
                              ('REC_R10', 'context_counted_as_new_experiment')]:
            with self.subTest(field=field):
                self.setUp()
                self.reject(target, lambda row, f=field: row['payload'].update({f: True}))

    def test_archive_rejects_closeout_omission_and_hold_removal(self):
        self.reject('REC_R12', lambda row: row['payload']['job_closeout_hashes'].pop('RUN_JOB_CON_LOW'))
        self.setUp()
        self.reject('REC_R12', lambda row: row['payload']['qualification_holds'].pop())


    def test_matched_pair_membership_and_cell_variant_are_enforced(self):
        for branch in ('B02', 'B06'):
            for field, value in [('matched_pair_id', 'UNMATCHED_PAIR'), ('cell_variant', 'cell_19mm')]:
                with self.subTest(branch=branch, field=field):
                    self.setUp()
                    next(x for x in self.plan['condition_plan'] if x['branch_id'] == branch)[field] = value
                    with self.assertRaises(ContractError):
                        self.ledger()

    def test_matched_pairs_do_not_conflate_statistical_repeat_groups(self):
        for index, row in enumerate(self.plan['condition_plan']):
            row['repeat_group_id'] = 'INDEPENDENT_STATISTICAL_GROUP_' + str(index)
        self.ledger()

    def test_each_reported_control_remains_present_and_typed(self):
        for index in range(1, 10):
            control = 'CR%02d' % index
            with self.subTest(control=control, mutation='omitted'):
                self.setUp()
                self.reject('REC_R09', lambda row, c=control: row['payload']['control_links'].pop(c))
            for field, value in [('evidence_kind', 'new_observed_measurement'), ('new_measurement', True)]:
                with self.subTest(control=control, mutation=field):
                    self.setUp()
                    self.reject('REC_R09', lambda row, c=control, f=field, v=value:
                                row['payload']['control_links'][c].update({f: v}))

    def test_control_condition_scope_cannot_swap_or_omit_conditions(self):
        for control in ('CR01', 'CR02', 'CR03', 'CR04', 'CR05'):
            with self.subTest(control=control):
                self.setUp()
                self.reject('REC_R09', lambda row, c=control:
                            row['payload']['control_links'][c].update(condition_ids=[]))

    def test_closeout_branch_scope_is_exactly_one_registered_job(self):
        target = 'CLOSE_RUN_JOB_CON_LOW'
        self.assertEqual(set(self.receipts[target]['branch_results']), {'B02'})
        self.reject(target, lambda row: row['branch_results'].update(B06='CONTRACT_REVIEWED'))

    def test_service_subject_branch_cannot_change(self):
        self.reject('REC_R05', lambda row: row['service_jobs'][0].update(branch_ids=['B03']))

    def test_derived_id_cannot_alias_a_raw_id(self):
        raw_id = self.receipts['REC_R05']['payload']['runs'][0]['pressure_raw']['raw_evidence_id']
        self.reject('REC_R08', lambda row: row['payload']['derived_records'][0].update(derived_evidence_id=raw_id))


if __name__ == '__main__':
    unittest.main()
