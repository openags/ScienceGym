import copy,pathlib,unittest
from contract import *
P=load_package(pathlib.Path(__file__).resolve().parents[1])
def fixture(storage=False):
 r=dict(record_id='r1',branch_id='NOR',case_id='00',attempt_id='a1',specimen_ids=['s1'],assembly_revision='v1',program_revision='p1',setup_revision='setup1',calibration_id='cal1',reset_receipt_id='reset1',raw_sha256='a'*64,timestamp_utc='2026-10-03T00:00:00Z',data_class='synthetic_observation',quality='accepted',synthetic_fixture=True,receipt_id='receipt1',input_bits=[0,0],observed_input_bits=[0,0],output_bit=1,input_event_index=1,output_event_index=2,mask_verified=True,excitation_origin='hardware_qualification_card',custody_receipt_id='move1',row_events=[dict(active_rows=[1,2],within_limits=True)])
 if storage:r.update(branch_id='VOLATILE_STORAGE',specimen_ids=['s1','s2'],hold_continuity_receipt=dict(hold_epoch='h1',uninterrupted=True,rows=[4,5],coverage='post_write_through_after_read',source='event_stream'),storage_pair_ids=['s1','s2'],storage_rows=[4,5],baseline_phase='post_write_pre_upstream_release',baseline_hold_epoch='h1',hold_epoch='h1',hold_samples=[dict(rows=[4,5],powered=True,within_limits=True)],upstream_released=True,before_pair=[0,1],after_pair=[0,1])
 c=dict(current_program_revision='p1',current_setup_revision='setup1',objects={'s1':'v1','s2':'v1'},calibrations={'cal1':'setup1'},receipts={},resets={'reset1':dict(case_id='00',attempt_id='a1',verified_zero=True,setup_revision='setup1')},previous_records={},custody=['move1'],qualified_handoffs=['ARRAY_PREP'],cleanup_verified=True)
 sync(r,c);return r,c
def sync(r,c):c['receipts'][r['receipt_id']]=dict(copy.deepcopy(r),limits_respected=True)
class PackageTests(unittest.TestCase):
 def test_valid(self):self.assertGreaterEqual(validate_package(P)['operations'],53)
 def bad(self,fn):
  p=copy.deepcopy(P);fn(p)
  with self.assertRaises((ContractError,KeyError)):validate_package(p)
 def test_wrong_doi(self):self.bad(lambda p:p['operations.json'].update(doi='wrong'))
 def test_duplicate_operation(self):self.bad(lambda p:p['operations.json']['operations'].append(p['operations.json']['operations'][0]))
 def test_missing_file(self):self.bad(lambda p:p.pop('lineage_contract.json'))
 def test_missing_action(self):self.bad(lambda p:p['operations.json']['operations'][0].update(actions=[]))
 def test_unknown_evidence(self):self.bad(lambda p:p['operations.json']['operations'][0]['evidence_ids'].append('false'))
 def test_unknown_gate(self):self.bad(lambda p:p['operations.json']['operations'][0]['unknown_parameter_ids'].append('false'))
 def test_gate_default(self):self.bad(lambda p:p['unknown_parameters.json']['unknowns'][0].update(default=1))
 def test_source_promotion(self):self.bad(lambda p:p['STATUS.json'].update(source_complete=True))
 def test_execution_promotion(self):self.bad(lambda p:p['STATUS.json'].update(robot_execution_run=True))
 def test_panels_promotion(self):self.bad(lambda p:p['source_access_audit.json']['main'].update(panels='read'))
 def test_movie_promotion(self):self.bad(lambda p:p['source_access_audit.json']['movies'].update(contents='read'))
 def test_access_stop_removed(self):self.bad(lambda p:p['source_access_audit.json']['main'].update(pdf='retried'))
 def test_physical_nand(self):self.bad(lambda p:p['branches.json']['branches'][0].update(id='NAND'))
 def test_repeat_invention(self):self.bad(lambda p:p['dependencies.json']['loops'][0].update(repeat_count=3))
 def test_empty_loop(self):self.bad(lambda p:p['dependencies.json']['loops'][0].update(empty_schedule_allowed=True))
 def test_cycle(self):self.bad(lambda p:p['dependencies.json']['edges'].append(dict(source='FAB_RELEASE',target='FAB_START')))
 def test_branch_cycle(self):self.bad(lambda p:p['branches.json']['branches'][0]['required_branch_ids'].append('ARRAY_PREP'))
 def test_operation_gate_lost(self):self.bad(lambda p:p['branches.json']['branches'][0].update(direct_unknown_parameter_ids=[]))
 def test_transitive_gate_lost(self):self.bad(lambda p:next(b for b in p['branches.json']['branches'] if b['id']=='NOR').update(unknown_parameter_ids=[]))
 def test_coverage_omission(self):self.bad(lambda p:p['coverage_matrix.json']['physical_coverage'].pop())
 def test_numerical_omission(self):self.bad(lambda p:p['nonmanual_scope.json']['dispositions'].pop())
 def test_actor_leak(self):self.bad(lambda p:p['agent_visible.json']['public_file_allowlist'].append('source_outcomes.json'))
 def test_actor_answer(self):self.bad(lambda p:p['agent_visible.json'].update(expected_output=1))
 def test_one_row_storage(self):self.bad(lambda p:p['state_contract.json']['volatile_storage'].update(pair_size=1))
 def test_signal_bistable(self):self.bad(lambda p:p['state_contract.json']['signal'].update(type='bistable'))
 def test_four_rows(self):self.bad(lambda p:p['state_contract.json']['switch'].update(maximum_active_rows=4))
 def test_fem_force_hardware(self):self.bad(lambda p:p['source_outcomes.json']['numerical_cases']['NAND'].update(hardware_setting=True))
 def test_crossovers_merged(self):self.bad(lambda p:p['source_outcomes.json']['numerical_cases']['COMPACT_CROSSOVER'].update(elements=176))
 def test_latch_invalid_hidden(self):self.bad(lambda p:p['source_outcomes.json']['numerical_cases']['SR_LATCH'].update(invalid_input=[]))
 def test_asset_promoted(self):self.bad(lambda p:p['asset_needs.json']['assets'][0].update(readiness='built'))
 def test_transport_invention(self):self.bad(lambda p:p['transport_routes.json']['routes'][0].update(geometry={'x':1}))
class RecordTests(unittest.TestCase):
 def bad(self,fn,storage=False,synchronize=False):
  r,c=fixture(storage);fn(r,c)
  if synchronize:sync(r,c)
  with self.assertRaises(ContractError):validate_record(r,c,allow_synthetic=True)
 def test_positive(self):r,c=fixture();self.assertTrue(validate_record(r,c,True))
 def test_positive_storage(self):r,c=fixture(True);self.assertTrue(validate_record(r,c,True))
 def test_not_real_execution(self):
  r,c=fixture()
  with self.assertRaises(ContractError):validate_record(r,c)
 def test_source_numerical(self):self.bad(lambda r,c:r.update(data_class='source_numerical'))
 def test_half_adder_is_not_physical(self):self.bad(lambda r,c:r.update(branch_id='HALF_ADDER'))
 def test_record_overwrite(self):self.bad(lambda r,c:c['previous_records'].update(r1=copy.deepcopy(r)))
 def test_stale_revision(self):self.bad(lambda r,c:r.update(assembly_revision='v0'))
 def test_quarantine(self):self.bad(lambda r,c:c.update(quarantined=['s1']))
 def test_missing_receipt(self):self.bad(lambda r,c:c['receipts'].clear())
 def test_receipt_bit_disagreement(self):self.bad(lambda r,c:r.update(output_bit=0))
 def test_ambiguous_output(self):self.bad(lambda r,c:r.update(output_bit=None),synchronize=True)
 def test_wrong_actual_input(self):self.bad(lambda r,c:r.update(observed_input_bits=[1,0]),synchronize=True)
 def test_output_before_input(self):self.bad(lambda r,c:r.update(output_event_index=0),synchronize=True)
 def test_fem_window(self):self.bad(lambda r,c:r.update(excitation_origin='SI3N'),synchronize=True)
 def test_mask_not_verified(self):self.bad(lambda r,c:r.update(mask_verified=False),synchronize=True)
 def test_stale_program(self):self.bad(lambda r,c:c.update(current_program_revision='p2'))
 def test_missing_row_history(self):self.bad(lambda r,c:r.update(row_events=[]),synchronize=True)
 def test_four_active_rows(self):self.bad(lambda r,c:r['row_events'][0].update(active_rows=[1,2,3,4]),synchronize=True)
 def test_missing_continuity(self):self.bad(lambda r,c:r.pop('hold_continuity_receipt'),True,True)
 def test_snapshot_is_not_continuity(self):self.bad(lambda r,c:r['hold_continuity_receipt'].update(source='snapshot'),True,True)
 def test_wrong_storage_lineage(self):self.bad(lambda r,c:r.update(storage_pair_ids=['s1','alien']),True,True)
 def test_stale_reset(self):self.bad(lambda r,c:c['resets']['reset1'].update(case_id='11'))
 def test_unverified_reset(self):self.bad(lambda r,c:c['resets']['reset1'].update(verified_zero=False))
 def test_stale_calibration(self):self.bad(lambda r,c:c['calibrations'].update(cal1='oldsetup'))
 def test_bad_hash(self):self.bad(lambda r,c:r.update(raw_sha256='picture'))
 def test_unsafe_receipt(self):self.bad(lambda r,c:c['receipts']['receipt1'].update(limits_respected=False))
 def test_retry_without_predecessor(self):self.bad(lambda r,c:r.update(predecessor_id='lost'))
 def test_missing_custody(self):self.bad(lambda r,c:r.update(custody_receipt_id='lost'),synchronize=True)
 def test_single_store_element(self):self.bad(lambda r,c:r.update(storage_pair_ids=['s1']),True,True)
 def test_nonadjacent_rows(self):self.bad(lambda r,c:r.update(storage_rows=[2,5]),True,True)
 def test_before_write_baseline(self):self.bad(lambda r,c:r.update(baseline_phase='before_write'),True,True)
 def test_wrong_epoch(self):self.bad(lambda r,c:r.update(baseline_hold_epoch='old'),True,True)
 def test_power_gap(self):self.bad(lambda r,c:r['hold_samples'][0].update(powered=False),True,True)
 def test_empty_hold(self):self.bad(lambda r,c:r.update(hold_samples=[]),True,True)
 def test_one_row_held(self):self.bad(lambda r,c:r['hold_samples'][0].update(rows=[5]),True,True)
 def test_upstream_not_released(self):self.bad(lambda r,c:r.update(upstream_released=False),True,True)
 def test_unknown_pair(self):self.bad(lambda r,c:r.update(after_pair=[None,1]),True,True)
 def test_scientific_mismatch_preserved(self):
  r,c=fixture();r['output_bit']=0;sync(r,c);self.assertTrue(validate_record(r,c,True))
class CompletionTests(unittest.TestCase):
 def args(self):
  r,c=fixture();records=[]
  for i,bits in enumerate([[0,0],[0,1],[1,0],[1,1]]):
   q=copy.deepcopy(r);q.update(record_id='r'+str(i),case_id=''.join(map(str,bits)),attempt_id='a'+str(i),input_bits=bits,observed_input_bits=bits,output_bit=int(not any(bits)),receipt_id='receipt'+str(i),reset_receipt_id='reset'+str(i));c['resets'][q['reset_receipt_id']]=dict(case_id=q['case_id'],attempt_id=q['attempt_id'],verified_zero=True,setup_revision='setup1');sync(q,c);records.append(q)
  return [['NOR'],{'NOR':['00','01','10','11']},records,{u['id']:True for u in P['unknown_parameters.json']['unknowns']},P,c,True]
 def bad(self,fn):
  a=self.args();fn(a)
  with self.assertRaises(ContractError):validate_coverage(*a)
 def test_positive(self):self.assertTrue(validate_coverage(*self.args()))
 def test_incomplete_truth_table(self):self.bad(lambda a:a[1].update(NOR=['00']))
 def test_duplicate_truth_label(self):self.bad(lambda a:a[2][1].update(input_bits=[0,0],observed_input_bits=[0,0]))
 def test_no_selection(self):self.bad(lambda a:a[0].clear())
 def test_no_schedule(self):self.bad(lambda a:a[1]['NOR'].clear())
 def test_missing_case(self):self.bad(lambda a:a[1]['NOR'].append('extra'))
 def test_duplicate_record(self):self.bad(lambda a:a[2].append(copy.deepcopy(a[2][0])))
 def test_unresolved_gate(self):self.bad(lambda a:a[3].update(U_ELECTRIC=False))
 def test_missing_preparation(self):self.bad(lambda a:a[5]['qualified_handoffs'].clear())
 def test_no_cleanup(self):self.bad(lambda a:a[5].update(cleanup_verified=False))
class TransportTests(unittest.TestCase):
 def fixture(self):return dict(payload_ids=['s1'],origin='WS_ASSEMBLY',destination='WS_LOGIC',supported=True,outputs_isolated=True,tethers_released=True,path_qualified=True,destination_verified=True,post_transport_integrity=True),{'s1':'WS_ASSEMBLY'}
 def test_good(self):self.assertTrue(validate_transport(*self.fixture()))
 def test_teleport(self):
  t,c=self.fixture();c['s1']='WS_STOCK'
  with self.assertRaises(ContractError):validate_transport(t,c)
 def test_live_payload(self):
  t,c=self.fixture();t['outputs_isolated']=False
  with self.assertRaises(ContractError):validate_transport(t,c)
 def test_tether(self):
  t,c=self.fixture();t['tethers_released']=False
  with self.assertRaises(ContractError):validate_transport(t,c)

class RegressionTests(unittest.TestCase):
 def test_terminal_operation_must_be_member(self):
  p=copy.deepcopy(P);b=next(x for x in p['branches.json']['branches'] if x['id']=='ARRAY_PREP');b['operation_ids'].remove('CLEAN')
  with self.assertRaises(ContractError):validate_package(p)
 def test_second_storage_specimen_quarantine(self):
  r,c=fixture(True);c['quarantined']=['s2']
  with self.assertRaises(ContractError):validate_record(r,c,True)
 def test_second_storage_specimen_revision(self):
  r,c=fixture(True);c['objects']['s2']='old'
  with self.assertRaises(ContractError):validate_record(r,c,True)

if __name__=='__main__':unittest.main()
