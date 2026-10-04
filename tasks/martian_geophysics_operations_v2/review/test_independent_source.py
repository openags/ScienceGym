"""Independent source-aware static review; does not execute scientific software."""
from pathlib import Path
import json,unittest
P=Path(__file__).resolve().parents[1]
EXPECT=json.loads((Path(__file__).parent/'source_expectations.json').read_text())
def read(n):return json.loads((P/n).read_text())
class IndependentStatic(unittest.TestCase):
 def setUp(self):
  self.b={x['id']:x for x in read('branches.json')['branches']}
  self.o=read('operations.json')['operations']
  self.c={x['id']:x for x in read('source_conflicts.json')['conflicts']}
 def test_ten_original_conflicts_preserved(self):
  src=EXPECT['conflicts'];self.assertEqual(set(self.c),{x['id'] for x in src})
  for a in src:
   b=self.c[a['id']]
   self.assertEqual(a['finding'],b['finding']);self.assertEqual(a['locator'],b['locator']);self.assertEqual(a['conversion_rule'],b['gate'])
   self.assertEqual(b['status'],'unresolved');self.assertIs(b['actor_can_resolve'],False)
 def test_conflict_branch_references_consistent(self):
  for c in self.c.values():
   for b in c['affected_branch_ids']:self.assertIn(c['id'],self.b[b]['conflict_ids'])
  for b in self.b.values():
   for c in b['conflict_ids']:self.assertIn(b['id'],self.c[c]['affected_branch_ids'])
 def test_all_thirteen_source_routes_covered(self):
  routes=read('coverage_matrix.json')['routes'];self.assertEqual({x['route_id'] for x in routes},{f'R{i:02}' for i in range(1,14)})
  for x in routes:self.assertTrue(x['branch_ids']);self.assertTrue(set(x['branch_ids'])<=set(self.b))
 def test_numerical_branches_are_not_physical(self):
  ids={'SOLIDUS_FIT','LIQUID_EOS','RESIDUE_EOS','BULK_EOS','EXCESS_VOLUME','BML_VOLUME','COMPARE'}
  self.assertEqual({b for b,x in self.b.items() if x['classification']=='numerical_analysis'},ids)
  for x in self.o:
   if x['branch_id'] in ids:self.assertNotIn(x['phase'],['request_closed_service','retrieve_safe'])
 def test_source_lineage_not_fabricated(self):
  for r in ['S3630','S3565','S3632','S3631']:
   b=self.b['STACK_'+r];self.assertEqual(b['required_branch_ids'],['SYNTH_ALLOC']);self.assertIn('U_PARENTMAP',b['unknown_parameter_ids'])
  u={x['id']:x for x in read('episode_input_contract.json')['required_cards']};self.assertIsNone(u['U_PARENTMAP']['default'])
  self.assertIn('not established',self.b['SYNTH_ALLOC']['design_note'])
 def test_redox_and_phase_composition_coverage(self):
  u={x['source_unit']:x for x in read('coverage_matrix.json')['coverage']}
  self.assertTrue({'EPMA','MODES','COMPARE'}<=set(u['S07']['branch_ids']))
  self.assertTrue({'GLASS_QC','RUN_S3631','SEM','COMPARE'}<=set(u['M02']['branch_ids']))
 def test_all_audited_source_units_accounted_for(self):
  src=set(EXPECT['source_unit_ids'])
  self.assertEqual(src,{x['source_unit'] for x in read('coverage_matrix.json')['coverage']})
 def test_source_parameters_not_invented(self):
  for b in self.b.values():self.assertEqual(b['source_parameters'],{});self.assertIsNone(b['source_independent_replicates'])
 def test_release_boundary_and_actor_limits(self):
  r=read('RELEASE_BOUNDARY.json')
  for k in ['execution_ready','real_actuation_implemented','physical_simulation_run','numerical_reproduction_run','production_signature_verification_implemented','source_complete_for_entire_paper','main_and_extended_data_pixels_verified','publisher_assets_included','temperature_correction_sign_resolved','H5897_H5898_assignment_resolved']:self.assertIs(r[k],False,k)
  self.assertIs(r['written_source_coverage_complete'],True)
  self.assertEqual(r['actor_file_allowlist'],['agent_visible.json'])
  self.assertIs(read('agent_visible.json')['source_outcomes_included'],False)
  for o in self.o:self.assertIs(o['actor_may_command_hazard'],False)
 def test_source_outcomes_evaluator_only(self):
  r=read('source_outcomes.json');self.assertEqual(r['audience'],'evaluator_reference_only');self.assertIs(r['not_completion_targets'],True)
  self.assertIs(read('evaluator_reference.json')['source_conflict_resolution_claim_allowed'],False)
 def test_physical_and_numerical_no_run_ready_claim(self):
  for b in self.b.values():self.assertIs(b['execution_ready'],False);self.assertIs(b['expected_results_actor_visible'],False)
  self.assertIs(read('mock_contract.json')['real_execution_always_rejected'],True)
 def test_key_measurement_origin_boundaries(self):
  self.assertIn('never zero',self.b['ACOUSTIC']['design_note'])
  self.assertIn('mass-balance-derived',self.b['EPMA']['design_note'])
  self.assertIn('No thermocouple',self.b['EXSITU_H6050']['design_note'])
  self.assertEqual(self.b['GRAPHITE_FEED']['required_branch_ids'],['PRECURSOR'])
  self.assertIn('cold and warm regions independently',self.b['SEM']['design_note'])
if __name__=='__main__':unittest.main(verbosity=2)
