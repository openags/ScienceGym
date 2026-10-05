"""Independent adversarial tests of the finite, synthetic evaluator contract.
Acceptance here means metadata only. These tests never supply numerical observations.
"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
from contract import (ContractError, MetadataContract, SyntheticStore, measurement_fixture,
                      closeout_fixture, SAFE_CHANNELS)


def measurement_review(mutator=None, op='R05', pair=('Array1', 'Array2')):
    m, c, l = measurement_fixture(op, pair)
    if mutator: mutator(m, c)
    return MetadataContract(SyntheticStore([m, c, l])).review(
        {'operation_id': op, 'evidence_ids': [m['id'], c['id'], l['id']]})


class IndependentFiniteValidator(unittest.TestCase):
    def test_positive_is_metadata_only(self):
        r = measurement_review()
        self.assertEqual(r['status'], 'SYNTHETIC_METADATA_ACCEPTED')
        self.assertIs(r['physical_execution_enabled'], False)
        self.assertEqual(r['physical_qualification'], 'HOLD_QUALIFICATION')
        self.assertIs(r['scientific_observation_generated'], False)

    def test_wrong_calibration_method_mount_terminal_rejected(self):
        for field in ('method_revision', 'sample_mount_id', 'terminal_map_revision'):
            with self.subTest(field=field), self.assertRaises(ContractError):
                measurement_review(lambda m, c: c.update({field: 'WRONG_UNRELATED_REVISION'}))

    def test_missing_calibration_method_mount_terminal_rejected(self):
        for field in ('method_revision', 'sample_mount_id', 'terminal_map_revision'):
            with self.subTest(field=field), self.assertRaises(ContractError):
                measurement_review(lambda m, c: c.pop(field, None))

    def test_unknown_characterization_device_rejected(self):
        with self.assertRaises(ContractError):
            measurement_review(op='R04', pair=('UNREGISTERED_X', 'UNREGISTERED_Y'))

    def test_unbound_measurement_lease_rejected(self):
        with self.assertRaises(ContractError):
            measurement_review(lambda m, c: m.update(lease_ids=['DOES_NOT_EXIST']))

    def test_closeout_channels_cannot_all_be_one_untyped_evidence_id(self):
        r = closeout_fixture()
        r['independent_safety_evidence'] = {ch: 'SYNTHETIC_OBS_SAME' for ch in SAFE_CHANNELS}
        with self.assertRaises(ContractError):
            MetadataContract(SyntheticStore([r])).review({'operation_id': 'R14', 'evidence_ids': [r['id']]})

    def test_measurement_negative_cases(self):
        mutations = {
            'source_values_as_observations': lambda m, c: m.update(new_observation=True),
            'copied_outcome': lambda m, c: m.update(source_outcome_ids=['O01']),
            'source_target_reward': lambda m, c: m.update(source_derived_threshold=True),
            'scientific_value': lambda m, c: m.update(scientific_values={'invented': 1}),
            'ratio_reversed': lambda m, c: m.update(ratio_direction='Array2/Array1'),
            'two_chips': lambda m, c: m.update(region_chip_ids={'Array1': 'A', 'Array2': 'B'}),
            'missing_power': lambda m, c: m.update(per_device_power_records={'Array1': 'SYNTHETIC_ONLY'}),
            'missing_current': lambda m, c: m.update(per_device_current_records={}),
            'calibration_expires_mid_run': lambda m, c: c.update(valid_until='2000-01-01T00:00:01Z'),
            'calibration_starts_mid_run': lambda m, c: c.update(valid_from='2000-01-01T00:00:01Z'),
            'configuration_change': lambda m, c: c.update(configuration_change=True),
            'reference_change': lambda m, c: c.update(reference_change=True),
            'invented_chip_count': lambda m, c: m.update(independent_chip_count=45),
            'raw_length_mismatch': lambda m, c: m.update(per_reading_SD_record_ids=['A', 'B']),
            'raw_outside_interval': lambda m, c: m.update(raw_timestamps=['2001-01-01T00:00:00Z']),
            'unknown_store_origin': lambda m, c: m.update(origin='source_paper'),
            'unknown_provider': lambda m, c: m.update(provider='UNTRUSTED'),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), self.assertRaises(ContractError):
                measurement_review(mutate)

    def test_reference_bath_and_external_identity_rejected(self):
        with self.assertRaises(ContractError):
            measurement_review(lambda m, c: m.update(reference_baths={'REF100':'AIR12K9'}), 'R06', ('HB', 'REF100'))
        with self.assertRaises(ContractError):
            measurement_review(lambda m, c: m.update(source_SI4_identity_resolved=True), 'R11', ('Array1', 'REF12K9'))
        with self.assertRaises(ContractError):
            measurement_review(lambda m, c: m.update(runtime_region_evidence=''), 'R11', ('Array1', 'REF12K9'))

    def test_short_screen_cannot_claim_allan_sem(self):
        with self.assertRaises(ContractError):
            measurement_review(lambda m, c: m.update(uncertainty_semantics='Allan_SEM', allan_used=True), 'R10')

    def test_closeout_failure_cases(self):
        mutations = {
            'missing_channel': lambda r: r['independent_safety_evidence'].pop('accessible_field'),
            'timer_basis': lambda r: r.update(safe_basis='timer_elapsed'),
            'unjoined_started_job': lambda r: r['started_jobs'].append('OTHER_ACTUALLY_STARTED_JOB'),
            'pending_job': lambda r: r.update(pending_jobs=['STILL_RUNNING']),
            'analysis_gate': lambda r: r.update(analysis_success_required=True),
            'custody_not_accepted': lambda r: r.update(custody_accepted=False),
            'lease_not_acknowledged': lambda r: r.update(lease_release_ack=False),
            'branch_falsely_complete': lambda r: r['branch_statuses'].update(R05='success'),
            'real_release_claim': lambda r: r.update(physical_release_performed=True),
        }
        for name, mutate in mutations.items():
            r = closeout_fixture(); mutate(r)
            with self.subTest(name=name), self.assertRaises(ContractError):
                MetadataContract(SyntheticStore([r])).review({'operation_id': 'R14', 'evidence_ids': [r['id']]})

    def test_closeout_partial_failed_optional_unattempted_valid(self):
        r = closeout_fixture()
        r['branch_statuses'].update(R05='failed_observation', R06='partial_evidence', R09='held_qualification', R10='unattempted', R11='unattempted')
        result = MetadataContract(SyntheticStore([r])).review({'operation_id': 'R14', 'evidence_ids': [r['id']]})
        self.assertEqual(result['status'], 'SYNTHETIC_METADATA_ACCEPTED')
        self.assertIs(result['physical_execution_enabled'], False)

    def test_actor_cannot_supply_receipts_or_hardware_arguments(self):
        m, c, l = measurement_fixture()
        contract = MetadataContract(SyntheticStore([m, c, l]))
        for extra in ({'current': 1}, {'receipt': m}, {'command': 'execute'}, {'endpoint': 'instrument'}):
            action = {'operation_id': 'R05', 'evidence_ids': [m['id'], c['id'], l['id']]}; action.update(extra)
            with self.subTest(extra=next(iter(extra))), self.assertRaises(ContractError): contract.review(action)
        with self.assertRaises(ContractError):
            contract.review({'operation_id': 'R05', 'evidence_ids': ['UNKNOWN']})

    def test_store_isolated_from_caller_mutation(self):
        m, c, l = measurement_fixture(); store = SyntheticStore([m, c, l]); m['new_observation'] = True
        result = MetadataContract(store).review({'operation_id': 'R05', 'evidence_ids': [m['id'], c['id'], l['id']]})
        self.assertEqual(result['status'], 'SYNTHETIC_METADATA_ACCEPTED')
        looked_up = store.lookup(m['id']); looked_up['new_observation'] = True
        self.assertIs(store.lookup(m['id'])['new_observation'], False)


    def test_r03_custody_lease_identity_is_bound(self):
        def custody():
            c = {'id':'INDEPENDENT_CUSTODY', 'origin':'synthetic_evaluator_fixture',
                 'provider':'SYNTHETIC_QUALIFIED_PROVIDER', 'status':'accepted', 'operation_id':'R03', 'kind':'custody'}
            c.update({k:'INDEPENDENT_'+k for k in ['event_id','sample_id','chip_id','from_custodian','to_custodian',
                     'from_support','to_support','carrier_id','mount_id','condition_before','condition_after','orientation_evidence','acceptance_id']})
            c.update(receiver_accepted=True, receiving_support_observed=True, identity_occupancy_observed=True,
                     releases_previous_support=False, unresolved_hazards=[], support_observed_at='2000-01-01T00:00:00Z',
                     accepted_at='2000-01-01T00:00:01Z')
            return c
        for field in ('chip_id', 'custodian_id', 'sample_mount_id'):
            c = custody(); l = measurement_fixture('R03')[2]
            l.update(chip_id=c['chip_id'], custodian_id=c['to_custodian'], sample_mount_id=c['mount_id'])
            baseline = MetadataContract(SyntheticStore([c,l])).review({'operation_id':'R03','evidence_ids':[c['id'], l['id']]})
            self.assertEqual(baseline['status'], 'SYNTHETIC_METADATA_ACCEPTED')
            l[field] = 'WRONG_UNRELATED_ID'
            with self.subTest(field=field), self.assertRaises(ContractError):
                MetadataContract(SyntheticStore([c,l])).review({'operation_id':'R03','evidence_ids':[c['id'], l['id']]})

    def test_analysis_holds_and_invalid_branch_status_rejected(self):
        base = {'id':'INDEPENDENT_ANALYSIS','origin':'synthetic_evaluator_fixture',
                'provider':'SYNTHETIC_QUALIFIED_PROVIDER','status':'accepted','operation_id':'R13','kind':'analysis',
                'raw_bundle_ids':['INDEPENDENT_SYNTHETIC_RAW'], 'raw_source_class':'synthetic_metadata_only',
                'source_outcome_ids':[], 'unresolved_equation_holds':[],
                'qualified_method_revision':'SYNTHETIC_APPROVED_METADATA_METHOD', 'numerical_analysis_performed':False,
                'covariance_record':'INDEPENDENT_SYNTHETIC_COV', 'exclusion_log':'INDEPENDENT_SYNTHETIC_LOG',
                'source_graph_edge_ids':['E01','E02','E03','E04','E05'], 'acquired_direct_edge_ids':[],
                'edge_statuses':{e:'held_qualification' for e in ('E01','E02','E03','E04','E05')}, 'simple_loop_count':3, 'independent_cycle_count':2,
                'derived_paths_are_independent':False, 'claims_exact_absolute_quantization':False,
                'branch_statuses':{'R09':'held_qualification','R10':'unattempted','R11':'unattempted'}}
        baseline = MetadataContract(SyntheticStore([base])).review({'operation_id':'R13','evidence_ids':[base['id']]})
        self.assertEqual(baseline['status'], 'SYNTHETIC_METADATA_ACCEPTED')
        mutations = [lambda r: r.update(unresolved_equation_holds=['AH_ALLAN_INPUT']),
                     lambda r: r.update(derived_paths_are_independent=True),
                     lambda r: r.update(numerical_analysis_performed=True),
                     lambda r: r.update(independent_cycle_count=3),
                     lambda r: r.update(acquired_direct_edge_ids=['E01']),
                     lambda r: r.update(branch_statuses={'R09':'MADE_UP','R10':'MADE_UP','R11':'MADE_UP'})]
        for mutate in mutations:
            r = copy.deepcopy(base); mutate(r)
            with self.assertRaises(ContractError):
                MetadataContract(SyntheticStore([r])).review({'operation_id':'R13','evidence_ids':[r['id']]})


    def test_characterization_paths_and_proxy_scope(self):
        r = {'id':'INDEPENDENT_CHARACTERIZATION','origin':'synthetic_evaluator_fixture',
             'provider':'SYNTHETIC_QUALIFIED_PROVIDER','status':'accepted','operation_id':'R04','kind':'characterization',
             'chip_id':'INDEPENDENT_CHIP','mount_id':'INDEPENDENT_MOUNT','configuration_revision':'INDEPENDENT_REV',
             'region_chip_ids':{x:'INDEPENDENT_CHIP' for x in ('HB','Array1','Array2')},
             'path_receipts':{x:'INDEPENDENT_PATH_'+x for x in ('HB_Rxx','HB_Rxy','HB_contacts',
                 'subarray_transition','subarray_magnetotransport','voltmeter_offset','noise_floor')},
             'calibration_receipt_id':'INDEPENDENT_CALIBRATION','terminal_map_revision':'INDEPENDENT_TERMINAL',
             'source_outcome_ids':[], 'scientific_values':None, 'apparent_plateau_certifies_quantization':False,
             'HB_density_is_direct_subarray_measurement':False}
        def check(obj):
            return MetadataContract(SyntheticStore([obj])).review({'operation_id':'R04','evidence_ids':[obj['id']]})
        self.assertEqual(check(r)['status'], 'SYNTHETIC_METADATA_ACCEPTED')
        for key in ('apparent_plateau_certifies_quantization','HB_density_is_direct_subarray_measurement'):
            changed = copy.deepcopy(r); changed[key] = True
            with self.subTest(key=key), self.assertRaises(ContractError): check(changed)
        for key in r['path_receipts']:
            changed = copy.deepcopy(r); changed['path_receipts'].pop(key)
            with self.subTest(path=key), self.assertRaises(ContractError): check(changed)
        changed = copy.deepcopy(r); changed['region_chip_ids']['Array2'] = 'UNRELATED_CHIP'
        with self.assertRaises(ContractError): check(changed)

if __name__ == '__main__': unittest.main()
