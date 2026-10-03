import unittest,copy
from contract import fixture,validate,BRANCHES,load
class ContractTests(unittest.TestCase):
 def mutate(self,fn,selected=None):
  c,e=fixture(selected);fn(c,e);self.assertTrue(validate(c,e))
 def test_all_selected_branches(self):
  for b in BRANCHES:
   with self.subTest(branch=b):
    c,e=fixture([b]);self.assertEqual(validate(c,e),[])
 def test_whole_campaign(self):
  c,e=fixture(mode='whole_physical_campaign');self.assertEqual(validate(c,e),[])
 def test_negative_mutations(self):
  cases={
  'empty_selected':lambda c,e:c.update(selected_branches=[]),
  'unknown_branch':lambda c,e:c['selected_branches'].append('invented'),
  'missing_plan':lambda c,e:c['plans'].pop(next(iter(c['plans']))),
  'empty_cycles':lambda c,e:next(iter(c['plans'].values())).update(cycles=[]),
  'null_cycles':lambda c,e:next(iter(c['plans'].values())).update(cycles=None),
  'zero_cycles':lambda c,e:next(iter(c['plans'].values())).update(cycles=[0]),
  'bool_cycles':lambda c,e:next(iter(c['plans'].values())).update(cycles=[True]),
  'unknown_as_source':lambda c,e:next(iter(c['plans'].values())).update(count_origin='source_cycle_count'),
  'omit_condition':lambda c,e:c['plans']['BEAM_POWER']['conditions'].pop(),
  'missing_job':lambda c,e:c['jobs'].pop(next(iter(c['jobs']))),
  'open_service':lambda c,e:next(iter(c['jobs'].values())).update(closed_service=False),
  'unqualified_service':lambda c,e:next(iter(c['jobs'].values())).update(qualified=False),
  'unsafe_release':lambda c,e:next(iter(c['jobs'].values())).update(safe_release=False),
  'destroyed':lambda c,e:next(iter(c['jobs'].values())).update(destroyed=True),
  'source_as_sensor':lambda c,e:next(iter(c['jobs'].values())).update(source_kind='source_reported'),
  'real_authority':lambda c,e:c.update(fixture_only=False),
  'actor_forgery':lambda c,e:c.update(authority_id='actor'),
  'missing_card':lambda c,e:c['cards'].pop('U_PRINT'),
  'stale_card':lambda c,e:c['cards']['U_PRINT'].update(revision='old'),
  'missing_conflict':lambda c,e:c['conflict_resolutions'].pop('C1'),
  'column_silent_swap':lambda c,e:c['conflict_resolutions'].update(C2='automatically_swapped'),
  'real_time_video':lambda c,e:c['conflict_resolutions'].update(C10='real_time'),
  'no_release_image':lambda c,e:next(j for j in c['jobs'].values() if j['service_id']=='RELEASE').update(optical_self_peeling=False),
  'no_release_motion':lambda c,e:next(j for j in c['jobs'].values() if j['service_id']=='RELEASE').update(optical_free_movement=False),
  'missing_parent':lambda c,e:next(j for j in c['jobs'].values() if j['parents']).update(parents=[]),
  'wrong_order':lambda c,e:e[0].update(phase='COMMIT'),
  'missing_phase':lambda c,e:e.pop(),
  'duplicate_event':lambda c,e:e[1].update(event_id=e[0]['event_id']),
  'stale_event_version':lambda c,e:e[0].update(input_version=999),
  'wrong_specimen':lambda c,e:e[0].update(specimen_id='other'),
  'wrong_condition':lambda c,e:e[0].update(condition_id='other'),
  'wrong_station':lambda c,e:e[0].update(station_id='WS_OTHER'),
  'wrong_fixture':lambda c,e:e[0].update(fixture_id='other'),
  'wrong_calibration':lambda c,e:e[0].update(calibration_id='old'),
  'future_record':lambda c,e:e[0].update(raw_record_id='future'),
  'wrong_hash':lambda c,e:e[0].update(record_hash='altered'),
  'untrusted_job':lambda c,e:e[0].update(job_id='actor_job'),
  'unsafe_guard':lambda c,e:e[0].update(guard_closed=False),
  'unsafe_exchange':lambda c,e:e[0].update(safe_exchange=False),
  'active_hazard':lambda c,e:e[0].update(hazard_isolated=False),
  'failed_receipt':lambda c,e:e[0].update(receipt_status='failed'),
  'missing_controls':lambda c,e:c.update(controls={}),
  'missing_archive':lambda c,e:c.update(archive_complete=False),
  'missing_cleanup':lambda c,e:c.update(cleanup_complete=False),
  'answer_leakage':lambda c,e:c.update(actor_source_targets_exposed=True),
  }
  for name,fn in cases.items():
   with self.subTest(case=name):self.mutate(fn)
 def test_cycle_lineages(self):
  for b,n in [('LATTICE_CYCLES',25),('IMAGE_CYCLES',27)]:
   self.mutate(lambda c,e:c['plans'][b].update(cycles=list(range(1,n+1))),[b])
 def test_whole_omission(self):
  c,e=fixture();c['mode']='whole_physical_campaign';self.assertTrue(validate(c,e))
 def test_actor_boundary(self):
  a=load('agent_visible.json');self.assertFalse(a['source_targets_included']);self.assertFalse(a['future_measurements_included'])
  self.assertIsNone(a['qualified_cards']);self.assertEqual(a['current_observations'],[])
 def test_source_gaps(self):
  a=load('source_access_audit.json');self.assertEqual(a['extended_data_images_inspected'],0);self.assertFalse(a['source_complete_for_entire_paper'])
  self.assertEqual(a['frames_per_video'],8);self.assertEqual(a['video_count'],9)
 def test_reference_integrity(self):
  op={o['id'] for o in load('operations.json')['operations']};ev={e['id'] for e in load('provenance.json')['evidence']};u={v['id'] for v in load('unknown_parameters.json')['unknowns']}
  for b in BRANCHES.values():
   self.assertTrue(set(b['operation_ids'])<=op);self.assertTrue(set(b['source_evidence_ids'])<=ev);self.assertTrue(set(b['unknown_parameter_ids'])<=u)
  for o in load('operations.json')['operations']:
   self.assertTrue(set(o['source_evidence_ids'])<=ev);self.assertFalse(o['physical_execution_implemented'])
if __name__=='__main__':unittest.main()
