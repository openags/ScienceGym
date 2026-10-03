import copy
import json
import pathlib
import unittest
from contract import ContractError, load_package, validate_package, validate_record, validate_coverage, validate_transport
ROOT=pathlib.Path(__file__).resolve().parents[1]
P=load_package(ROOT)

def fixture():
    r=dict(record_id='test-record-1',run_id='test-run-1',attempt_id='test-attempt-1',synthetic_fixture=True,record_role='specimen_measurement',data_class='measurement_raw',branch_id='NORMAL_INCIDENCE',condition_key='high-0deg-3000',sample_id='test-array-1',assembly_revision='rev-1',gradient_multiple_2pi_rad_per_m=6.7,gradient_reference_frequency_hz=3000,angle_deg=0,frequency_hz=3000,setup_signature='test-setup-A',calibration_id='test-cal-1',calibration_signature='test-setup-A',reference_id='test-ref-1',reference_signature='test-setup-A',grid_id='test-grid-far',point_key='x0-y0-pulse1',position=[0.0,0.4],environment_id='test-env-1',timestamp_utc='2026-10-03T00:00:00Z',raw_sha256='a'*64,quality='accepted',acquisition_receipt='test-acq-1',transport_receipt_ids=['test-move-1'])
    c=dict(objects={'test-array-1':'rev-1'},calibrations={'test-cal-1':'test-setup-A'},references={'test-ref-1':'test-setup-A'},environments=['test-env-1'],acquisitions={'test-acq-1':dict(r,outputs_within_limits=True,actual_position_verified=True)},transports=['test-move-1'],previous_records={},angle_schedules={'OBLIQUE_SWEEP':[10,20]},expected_trace_keys=[['NORMAL_INCIDENCE','high-0deg-3000','x0-y0-pulse1']])
    c['condition_manifest']=[{k:r[k] for k in ['branch_id','condition_key','angle_deg','frequency_hz','gradient_multiple_2pi_rad_per_m','gradient_reference_frequency_hz','sample_id','assembly_revision','grid_id']}]
    return r,c

def sync(r,c):
    c['acquisitions'][r['acquisition_receipt']]=dict(r,outputs_within_limits=True,actual_position_verified=True)

class PackageTests(unittest.TestCase):
    def test_valid_package(self): self.assertGreaterEqual(validate_package(P)['operations'],68)
    def bad(self,mutate):
        p=copy.deepcopy(P); mutate(p)
        with self.assertRaises((ContractError,KeyError)): validate_package(p)
    def test_historical_frequency_invention(self):self.bad(lambda p:next(x for x in p['branches.json']['branches'] if x['id']=='NEAR_FIELD')['conditions'].update(historical_acquisition_frequency_hz=3000))
    def test_missing_state_contract(self): self.bad(lambda p:p.pop('state_contract.json'))
    def test_missing_file(self): self.bad(lambda p:p.pop('branches.json'))
    def test_wrong_doi(self): self.bad(lambda p:p['operations.json'].update(doi='10.1038/ncomms11731'))
    def test_duplicate_operation(self): self.bad(lambda p:p['operations.json']['operations'].append(copy.deepcopy(p['operations.json']['operations'][0])))
    def test_unknown_default(self): self.bad(lambda p:p['unknown_parameters.json']['unknowns'][0].update(default=1))
    def test_broken_source(self): self.bad(lambda p:p['operations.json']['operations'][0]['evidence_ids'].append('fiction'))
    def test_broken_gate(self): self.bad(lambda p:p['branches.json']['branches'][0]['unknown_parameter_ids'].append('fiction'))
    def test_broken_station(self): self.bad(lambda p:p['operations.json']['operations'][0].update(location_id='fiction'))
    def test_missing_actions(self): self.bad(lambda p:p['operations.json']['operations'][0].update(actions=[]))
    def test_operation_promotion(self): self.bad(lambda p:p['operations.json']['operations'][0].update(execution_mode='robot_executed'))
    def test_branch_cycle(self): self.bad(lambda p:p['branches.json']['branches'][0]['required_branch_ids'].append('ASSEMBLE_ARRAYS'))
    def test_operation_cycle(self): self.bad(lambda p:p['dependencies.json']['edges'].append({'source':'STOCK','target':'PLAN'}))
    def test_loop_repeat_invention(self): self.bad(lambda p:p['dependencies.json']['loops'][0].update(repeat_count=3))
    def test_transport_geometry_invention(self): self.bad(lambda p:p['transport_routes.json']['routes'][0].update(geometry={'x':1}))
    def test_coverage_omission(self): self.bad(lambda p:p['coverage_matrix.json']['physical_coverage'].pop())
    def test_numeric_coverage_omission(self): self.bad(lambda p:p['coverage_matrix.json']['nonmanual_coverage'].pop())
    def test_coupling_becomes_physical(self): self.bad(lambda p:p['nonmanual_scope.json'].update(numerical_to_physical_promotion_allowed=True))
    def test_loss_angle_collapse(self): self.bad(lambda p:next(x for x in p['source_outcomes.json']['outcomes'] if x['id']=='S_SI_LOSSY_25').update(incident_angle_deg=20))
    def test_source_simulation_becomes_measurement(self): self.bad(lambda p:next(x for x in p['source_outcomes.json']['outcomes'] if x['id']=='S_MAIN_20').update(data_class='measurement_raw'))
    def test_actor_outcome_exposure(self): self.bad(lambda p:p['agent_visible.json']['public_inputs'].append('source_outcomes.json'))
    def test_actor_hidden_answer(self): self.bad(lambda p:p['agent_visible.json'].update(expected_angles=[42]))
    def test_second_layer_omitted(self): self.bad(lambda p:next(x for x in p['branches.json']['branches'] if x['id']=='ASSEMBLE_ARRAYS')['conditions'].update(transmissive_layers=1))
    def test_schedule_invention(self): self.bad(lambda p:next(x for x in p['branches.json']['branches'] if x['id']=='OBLIQUE_SWEEP')['conditions'].update(incident_angle_schedule_deg=[0,10,20]))
    def test_physical_execution_claim(self): self.bad(lambda p:p['STATUS.json'].update(robot_execution_run=True))
    def test_hash_drift(self): self.bad(lambda p:p['provenance.json']['source_files'][0].update(sha256='b'*64))

    def test_actor_provenance_leakage(self): self.bad(lambda p:p['agent_visible.json']['public_file_allowlist'].append('provenance.json'))
    def test_missing_branch_operation_gate(self): self.bad(lambda p:next(x for x in p['branches.json']['branches'] if x['id']=='APPARATUS')['unknown_parameter_ids'].remove('U_ENV'))
    def test_dimensional_acceptance_bypass(self): self.bad(lambda p:next(x for x in p['operations.json']['operations'] if x['id']=='ASM_LAYOUT')['preconditions'].remove('dimensional_accepted'))
    def test_unconditional_array_acceptance(self): self.bad(lambda p:next(x for x in p['operations.json']['operations'] if x['id']=='ASM_QC')['postconditions'].append('array_revision_qualified'))
    def test_missing_calibration_state(self): self.bad(lambda p:next(x for x in p['operations.json']['operations'] if x['id']=='CAL_REVIEW').update(conditional_postconditions=[]))
    def test_partial_grid_promotion(self): self.bad(lambda p:next(x for x in p['operations.json']['operations'] if x['id']=='FFT')['preconditions'].remove('scan_complete'))

class RecordTests(unittest.TestCase):
    def bad(self,mutate,sync_receipt=False):
        r,c=fixture();mutate(r,c)
        if sync_receipt:sync(r,c)
        with self.assertRaises(ContractError): validate_record(r,c,allow_synthetic=True)
    def test_synthetic_positive(self):
        r,c=fixture();self.assertTrue(validate_record(r,c,allow_synthetic=True))
    def test_synthetic_rejected_as_real(self):
        r,c=fixture()
        with self.assertRaises(ContractError):validate_record(r,c)
    def test_theory_rejected(self):self.bad(lambda r,c:r.update(data_class='source_theory'))
    def test_source_simulation_rejected(self):self.bad(lambda r,c:r.update(data_class='source_simulation'))
    def test_missing_raw_hash(self):self.bad(lambda r,c:r.pop('raw_sha256'))
    def test_fake_hash_format(self):self.bad(lambda r,c:r.update(raw_sha256='expected figure'))
    def test_wrong_nearfield_angle(self):self.bad(lambda r,c:r.update(branch_id='NEAR_FIELD'),sync_receipt=True)
    def test_missing_gradient_reference(self):self.bad(lambda r,c:r.pop('gradient_reference_frequency_hz'))
    def test_receipt_gradient_switch(self):self.bad(lambda r,c:r.update(gradient_multiple_2pi_rad_per_m=3.3))
    def test_wrong_oblique_specimen(self):self.bad(lambda r,c:r.update(branch_id='OBLIQUE_SWEEP',gradient_multiple_2pi_rad_per_m=3.3,angle_deg=10),sync_receipt=True)
    def test_wrong_oblique_frequency(self):self.bad(lambda r,c:r.update(branch_id='OBLIQUE_SWEEP',frequency_hz=2800,angle_deg=10),sync_receipt=True)
    def test_oblique_angle_not_scheduled(self):self.bad(lambda r,c:r.update(branch_id='OBLIQUE_SWEEP',angle_deg=15),sync_receipt=True)
    def test_oblique_declared_schedule_positive(self):
        r,c=fixture();r.update(branch_id='OBLIQUE_SWEEP',angle_deg=10);sync(r,c)
        self.assertTrue(validate_record(r,c,allow_synthetic=True))
    def test_baseline_bootstrap_positive(self):
        r,c=fixture();r.update(branch_id='QUALIFY_CHAIN',sample_id=None,assembly_revision=None,gradient_multiple_2pi_rad_per_m=0,record_role='baseline',reference_id=None,reference_signature=None);c['references'].clear();sync(r,c)
        self.assertTrue(validate_record(r,c,allow_synthetic=True))
    def test_baseline_with_array_rejected(self):self.bad(lambda r,c:r.update(record_role='baseline',reference_id=None,reference_signature=None),sync_receipt=True)
    def test_nan_angle(self):self.bad(lambda r,c:r.update(angle_deg=float('nan')))
    def test_zero_frequency(self):self.bad(lambda r,c:r.update(frequency_hz=0))
    def test_stale_revision(self):self.bad(lambda r,c:r.update(assembly_revision='rev-0'))
    def test_missing_sample(self):self.bad(lambda r,c:r.update(sample_id=None))
    def test_empty_control_hides_array(self):self.bad(lambda r,c:r.update(gradient_multiple_2pi_rad_per_m=0))
    def test_empty_control_positive(self):
        r,c=fixture();r.update(sample_id=None,assembly_revision=None,gradient_multiple_2pi_rad_per_m=0,record_role='baseline',reference_id=None,reference_signature=None);sync(r,c)
        self.assertTrue(validate_record(r,c,allow_synthetic=True))
    def test_gain_changes_scope(self):self.bad(lambda r,c:r.update(setup_signature='changed-gain'))
    def test_reference_mismatch(self):self.bad(lambda r,c:r.update(reference_signature='other-geometry'))
    def test_missing_environment(self):self.bad(lambda r,c:r.update(environment_id='unknown'))
    def test_missing_receipt(self):self.bad(lambda r,c:c['acquisitions'].clear())
    def test_receipt_angle_mismatch(self):self.bad(lambda r,c:r.update(angle_deg=20))
    def test_receipt_hash_mismatch(self):self.bad(lambda r,c:r.update(raw_sha256='b'*64))
    def test_unsafe_output(self):self.bad(lambda r,c:c['acquisitions']['test-acq-1'].update(outputs_within_limits=False))
    def test_unverified_position(self):self.bad(lambda r,c:c['acquisitions']['test-acq-1'].update(actual_position_verified=False))
    def test_missing_transport(self):self.bad(lambda r,c:r.update(transport_receipt_ids=[]))
    def test_missing_retry_predecessor(self):self.bad(lambda r,c:r.update(predecessor_id='lost'))
    def test_retry_new_identity_positive(self):
        r,c=fixture();old=copy.deepcopy(r);old['quality']='rejected';c['previous_records'][old['record_id']]=old
        r.update(record_id='test-record-2',attempt_id='test-attempt-2',predecessor_id=old['record_id']);sync(r,c)
        self.assertTrue(validate_record(r,c,allow_synthetic=True))
    def test_retry_overwrite(self):
        def mutate(r,c):
            c['previous_records'][r['record_id']]=dict(r,quality='rejected');r['predecessor_id']=r['record_id']
        self.bad(mutate)

class CoverageTests(unittest.TestCase):
    def setup_args(self):
        r,c=fixture();return ['NORMAL_INCIDENCE'],{'NORMAL_INCIDENCE':[r['condition_key']]},[r],{u['id']:True for u in P['unknown_parameters.json']['unknowns']},copy.deepcopy(P),c
    def test_valid_bookkeeping_only(self):self.assertTrue(validate_coverage(*self.setup_args(),allow_synthetic=True))
    def bad(self,fn):
        args=self.setup_args();fn(args)
        with self.assertRaises(ContractError):validate_coverage(*args,allow_synthetic=True)
    def test_empty_selection(self):self.bad(lambda a:a[0].clear())
    def test_empty_schedule(self):self.bad(lambda a:a[1]['NORMAL_INCIDENCE'].clear())
    def test_missing_grid_point(self):self.bad(lambda a:a[5]['expected_trace_keys'].append(['NORMAL_INCIDENCE','high-0deg-3000','x1-y0-pulse1']))
    def test_missing_structured_condition(self):self.bad(lambda a:a[5]['condition_manifest'].clear())
    def test_condition_label_cannot_hide_gradient(self):
        def change(a):a[2][0]['gradient_multiple_2pi_rad_per_m']=3.3;sync(a[2][0],a[5])
        self.bad(change)
    def test_condition_manifest_cannot_hide_angle(self):self.bad(lambda a:a[5]['condition_manifest'][0].update(angle_deg=10))
    def test_empty_records(self):self.bad(lambda a:a[2].clear())
    def test_unresolved_geometry(self):self.bad(lambda a:a[3].update(U_ASSEMBLY=False))
    def test_missing_condition(self):self.bad(lambda a:a[1]['NORMAL_INCIDENCE'].append('low-0deg-3000'))
    def test_duplicate_record(self):self.bad(lambda a:a[2].append(copy.deepcopy(a[2][0])))
    def test_rejected_trace_not_completed(self):
        def change(a):a[2][0]['quality']='rejected';sync(a[2][0],a[5])
        self.bad(change)

class TransportTests(unittest.TestCase):
    def fixture(self):return dict(entity_ids=['array-A'],from_station='WS_ASSEMBLY',to_station='WS_GUIDE',outputs_safe=True,tethers_disengaged=True,supported=True,path_qualified=True,destination_clear=True,destination_identity_verified=True),{'array-A':'WS_ASSEMBLY'}
    def test_transport_positive(self):self.assertTrue(validate_transport(*self.fixture()))
    def test_teleport_rejected(self):
        r,c=self.fixture();c['array-A']='WS_ARCHIVE'
        with self.assertRaises(ContractError):validate_transport(r,c)
    def test_tethered_transport_rejected(self):
        r,c=self.fixture();r['tethers_disengaged']=False
        with self.assertRaises(ContractError):validate_transport(r,c)
    def test_empty_payload_rejected(self):
        r,c=self.fixture();r['entity_ids']=[]
        with self.assertRaises(ContractError):validate_transport(r,c)

if __name__=='__main__':unittest.main()
