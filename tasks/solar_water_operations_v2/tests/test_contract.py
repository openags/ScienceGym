import copy, unittest
from contract import *
class ContractTests(unittest.TestCase):
 def test_all_routes(self):
  c,e=fixture();r=validate(c,e);self.assertEqual(r['jobs'],15);self.assertFalse(r['full_paper_complete']);self.assertGreater(r['events'],500)
 def test_every_route_individually(self):
  for b in BRANCHES:
   with self.subTest(branch=b):c,e=fixture([b]);self.assertEqual(validate(c,e)['status'],'passed')
 def test_each_plan_has_safe_retrieval(self):
  for b in BRANCHES:
   for step in plan_for(b):
    p=step['payload']
    if p['operation_id'] in ['DISCONNECT','RETRIEVE']:self.assertTrue(p['independent_safe_state']);self.assertFalse(p['light_active'])
 def test_all_acquisitions_calibrated(self):
  for b in BRANCHES:
   for s in plan_for(b):
    if s['operation_id'].endswith('_ACQUIRE'):self.assertIsNotNone(s['payload']['calibration_id'])
 def test_light_interlocks(self):
  for b in BRANCHES:
   for s in plan_for(b):
    if s['operation_id'] in ['LIGHT_ACQUIRE','THERMAL_ACQUIRE']:self.assertTrue(s['payload']['interlocks_current'])
 def test_wet_and_transfer_supports_differ(self):
  self.assertEqual(CONTROLS['TRANSFER'][0]['source_constraints']['coupon_support'],'external to reservoir balance')
  self.assertEqual(CONTROLS['HORIZONTAL'][0]['source_constraints']['balance_contains'],'whole floating assembly and reservoir')
 def test_cleanup_changes_surface_and_calibration(self):
  p=plan_for('REUSE');before=[s for s in p if s['operation_id']=='CALIBRATE'][0]['payload'];after=[s for s in p if s['operation_id']=='CALIBRATE'][1]['payload']
  self.assertGreater(after['coupon_version'],before['coupon_version']);self.assertGreater(after['surface_state_revision'],before['surface_state_revision']);self.assertNotEqual(after['calibration_id'],before['calibration_id'])
 def test_changed_orientation_recalibrates(self):
  p=plan_for('ANGLE')
  for i,s in enumerate(p):
   if s['operation_id']=='ORIENT':self.assertIsNone(s['payload']['calibration_id']);self.assertEqual(p[i+2]['operation_id'],'CALIBRATE')
 def test_dark_before_light_each_wet_case(self):
  for b in ['HORIZONTAL','VERTICAL','ANGLE','BIFACIAL','CONDENSATE','OUTDOOR']:
   current=[]
   for s in plan_for(b):
    if s['operation_id']=='RECEIVE':current=[]
    current.append(s['operation_id'])
    if s['operation_id']=='LIGHT_ACQUIRE':self.assertIn('DARK_ACQUIRE',current);self.assertIn('RESET_WATER',current)
 def test_no_science_values(self):
  c,_=fixture();self.assertTrue(all(p['scientific_measurement_values'] is None for p in c['record_store'].values()))
 def test_14_conflicts(self):self.assertEqual(CONFLICTS,['C'+str(n) for n in range(1,15)])
 def test_read_coverage_not_execution(self):
  d=load('coverage_matrix.json');self.assertEqual(len(d['pages']),55);self.assertFalse(d['full_paper_complete']);self.assertEqual(d['si_note_labels_absent'],[18,19,20])

def mutation_test(mut):
 def run(self):
  c,e=fixture(['BIFACIAL']);mut(c,e)
  with self.assertRaises(ValueError):validate(c,e)
 return run
mutations={
'actor_result':lambda c,e:e[0].update({'success':True}),
'actor_receipt':lambda c,e:e[0].update({'safe_state':True}),
'missing_phase':lambda c,e:e.pop(3),
'extra_phase':lambda c,e:e.append(copy.deepcopy(e[-1])),
'reordered':lambda c,e:e.reverse(),
'replay':lambda c,e:e.__setitem__(2,copy.deepcopy(e[1])),
'wrong_job':lambda c,e:e[0].update({'job_id':'job_BIOLOGY'}),
'phase_type':lambda c,e:e[0].update({'phase':0}),
'production':lambda c,e:c.update({'production_authority':True}),
'full_paper':lambda c,e:c.update({'full_paper_complete':True}),
'biology':lambda c,e:c.update({'biological_operations_included':True}),
'forged_authority':lambda c,e:next(iter(c['observations'].values())).update({'authority':'actor'}),
'dropped_conflict':lambda c,e:c['source_conflicts_preserved'].pop(),
'resolved_conflict':lambda c,e:next(iter(c['conflict_dispositions'].values())).update({'source_resolved':True}),
'missing_card':lambda c,e:c['cards'].pop(next(iter(c['cards']))),
'qualification_type_confusion':lambda c,e:next(iter(c['cards'].values())).update({'production_qualified':0}),
'deleted_parent':lambda c,e:c['jobs']['job_BIFACIAL'].update({'parents':[]}),
'wrong_inventory':lambda c,e:c['input_inventory']['job_BIFACIAL'][0].update({'coupon_id':'unregistered'}),
'wrong_record_hash':lambda c,e:next(iter(c['observations'].values())).update({'record_hash':'0'*64}),
'invented_science':lambda c,e:next(iter(c['record_store'].values())).update({'scientific_measurement_values':[1.26]}),
'silent_time_unit_fix':lambda c,e:next(iter(c['record_store'].values()))['control'].update({'rate_unit':'kg/m2/s'}),
'unknown_context_key':lambda c,e:c.update({'pathogen_efficacy':True}),
'stale_mount':lambda c,e:next(p for p in c['record_store'].values() if p['operation_id']=='LIGHT_ACQUIRE').update({'mount_revision':0}),
'stale_calibration':lambda c,e:next(p for p in c['record_store'].values() if p['operation_id']=='LIGHT_ACQUIRE').update({'calibration_id':None}),
'missing_dark':lambda c,e:e.remove(next(x for x in e if x['phase'].endswith('DARK_ACQUIRE'))),
'missing_reset':lambda c,e:e.remove(next(x for x in e if x['phase'].endswith('RESET_WATER'))),
'missing_rear_flux':lambda c,e:e.remove(next(x for x in e if x['phase'].endswith('REAR_FLUX_ACQUIRE'))),
'unsafe_retrieval':lambda c,e:next(p for p in c['record_store'].values() if p['operation_id']=='RETRIEVE').update({'independent_safe_state':False}),
'missing_cleanup':lambda c,e:e.pop(),
'nonfinite_value':lambda c,e:next(iter(c['record_store'].values())).update({'ordinal_time':float('nan')}),
}
for name,mut in mutations.items():setattr(ContractTests,'test_reject_'+name,mutation_test(mut))

class AdditionalContractTests(unittest.TestCase):
 def test_reject_cross_episode_replay(self):
  a,e=fixture(['BIFACIAL'],episode_id='A');b,_=fixture(['BIFACIAL'],episode_id='B')
  with self.assertRaises(ValueError):validate(b,e)
 def test_receipts_bind_episode(self):
  c,e=fixture(['BIFACIAL'])
  self.assertTrue(all(x['episode_id']==c['episode_id'] for x in c['record_store'].values()))
  self.assertTrue(all(x['episode_id']==c['episode_id'] for x in c['observations'].values()))
 def test_rear_flux_active_and_guarded(self):
  for s in plan_for('BIFACIAL'):
   if s['operation_id']=='REAR_FLUX_ACQUIRE':self.assertTrue(s['payload']['light_active']);self.assertTrue(s['payload']['interlocks_current'])
 def test_exact_target_handoff(self):
  c,_=fixture(['BIFACIAL'])
  inputs=c['input_inventory']['job_BIFACIAL']
  for parent in c['jobs']['job_BIFACIAL']['parents']:
   released=parent['released_target_records']
   self.assertEqual([x['coupon_id'] for x in inputs],[x['coupon_id'] for x in released])
   self.assertEqual([x['assembly_id'] for x in inputs],[x['assembly_id'] for x in released])
   self.assertEqual(parent['parent_release_inventory_hash'],digest(c['release_inventories'][parent['job_id']]))
 def test_source_exposure_cases_explicit(self):
  self.assertEqual(len(CONTROLS['HORIZONTAL']),10)
  self.assertEqual({x['source_constraints']['source_concentration_suns'] for x in CONTROLS['HORIZONTAL']},{1,2,3,4,5})

class ReceiptSchemaTests(unittest.TestCase):
 def test_declared_receipt_fields_present(self):
  c,_=fixture()
  required=set(load('operations.json')['operations'][0]['required_receipt_fields'])
  for o in c['observations'].values():
   p=c['record_store'][o['raw_record_id']]
   self.assertFalse(required-set(o)-set(p))

if __name__=='__main__':unittest.main()
