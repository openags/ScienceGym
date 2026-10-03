"""Static design checks only; no robot, device, mechanics, simulation or experiment is run."""
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name): return json.loads((ROOT/name).read_text())
class Contract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ops={o['id']:o for o in load('operations.json')['operations']}
  cls.branches={b['id']:b for b in load('branches.json')['branches']}
  cls.evidence=set(load('provenance.json')['evidence'])
  cls.unknowns={u['id'] for u in load('unknown_parameters.json')['unknowns']}
 def test_all_json_parse_and_shared_doi(self):
  for p in ROOT.glob('*.json'):
   d=json.loads(p.read_text()); self.assertEqual(d['doi'],'10.1038/s41467-017-00670-w')
 def test_ids_and_counts(self):
  d=load('operations.json'); self.assertEqual(d['operation_count'],len(d['operations'])); self.assertEqual(len(self.ops),len(d['operations']))
  d=load('branches.json'); self.assertEqual(d['branch_count'],len(d['branches'])); self.assertEqual(d['physical_configuration_count'],10)
 def test_operation_robot_device_contract(self):
  for o in self.ops.values():
   for k in ['actor','source_station','target_station','manipulated_objects_tools','actions','preconditions','completion_state','recoveries']:
    self.assertTrue(o[k],(o['id'],k))
   self.assertIn(o['actor'],['mobile_robot','station_device','analysis_service'])
   self.assertEqual(o['execution_mode'],'symbolic_design_only')
   self.assertEqual(o['provenance']['fine_actions'],'task_authored_not_source_trajectory')
 def test_branch_references(self):
  for b in self.branches.values():
   self.assertFalse(set(b['operation_ids'])-set(self.ops),b['id'])
   self.assertFalse(set(b['required_input_ids'])-self.unknowns,b['id'])
   self.assertFalse(set(b['evidence_ids'])-self.evidence,b['id'])
 def test_branch_covers_selected_operation_gaps(self):
  for b in self.branches.values():
   required=set(b['required_input_ids'])
   for oid in b['operation_ids']:
    o=self.ops[oid]; active=set(o['unknown_parameter_ids'])
    for uid,condition in o.get('conditional_unknown_parameter_ids',{}).items():
     if b['id'] in condition['branch_ids']:active.add(uid)
    self.assertFalse(active-required,(b['id'],oid,active-required))
 def test_operation_references(self):
  for o in self.ops.values():
   self.assertFalse(set(o['evidence_ids'])-self.evidence,o['id'])
   self.assertFalse(set(o['unknown_parameter_ids'])-self.unknowns,o['id'])
 def test_dependency_references(self):
  for e in load('dependencies.json')['edges']:
   self.assertIn(e['from'],self.ops); self.assertIn(e['to'],self.ops)
 def test_coverage_references(self):
  for row in load('coverage_matrix.json')['rows']:
   self.assertFalse(set(row['task_branch_ids'])-set(self.branches))
   self.assertFalse(set(row['evidence_ids'])-self.evidence)
 def test_all_ops_in_campaign(self):
  self.assertEqual(set(self.ops),set(self.branches['WHOLE_PAPER_CAMPAIGN']['operation_ids']))
 def test_all_physical_routes_in_campaign(self):
  self.assertEqual(set(self.branches)-{'WHOLE_PAPER_CAMPAIGN'},set(self.branches['WHOLE_PAPER_CAMPAIGN']['subbranch_ids']))
 def test_fabrication_robot_and_device_separate(self):
  for prefix in ['CUT','PRINT']:
   self.assertEqual(self.ops[prefix+'_LOAD']['actor'],'mobile_robot')
   self.assertEqual(self.ops[prefix+'_PROCESS']['actor'],'station_device')
   self.assertEqual(self.ops[prefix+'_UNLOAD']['actor'],'mobile_robot')
 def test_compression_baselines_are_separated(self):
  for b in ['SINGLE_MONOSTABLE','SINGLE_BISTABLE','SINGLE_ZERO_STIFFNESS','BIFURCATION_FREE','BIFURCATION_CONSTRAINED']:
   ids=self.branches[b]['operation_ids']
   self.assertLess(ids.index('CALIBRATE'),ids.index('CELL_MOUNT'))
   self.assertLess(ids.index('CELL_MOUNT'),ids.index('MOUNT_CHECK'))
   self.assertLess(ids.index('MOUNT_CHECK'),ids.index('COMPRESSION_ACQUIRE'))
 def test_guide_conditions_are_real_configuration_ops(self):
  for b in ['BIFURCATION_FREE','BIFURCATION_CONSTRAINED']:
   self.assertIn('GUIDE_CONFIG',self.branches[b]['operation_ids'])
  self.assertNotEqual(self.branches['BIFURCATION_FREE']['condition_card']['guide_condition'],self.branches['BIFURCATION_CONSTRAINED']['condition_card']['guide_condition'])
 def test_onebit_program_has_robot_readback(self):
  ids=self.branches['ONE_BIT_TORQUE']['operation_ids']
  self.assertLess(ids.index('MEMORY_PROGRAM'),ids.index('ONEBIT_ACQUIRE'))
  self.assertEqual(self.ops['MEMORY_PROGRAM']['actor'],'mobile_robot')
  self.assertTrue(any('Read back' in s for s in self.ops['MEMORY_PROGRAM']['actions']))
 def test_preparation_is_not_test_epoch(self):
  ids=self.branches['TWO_BIT_01_TO_10']['operation_ids']
  self.assertLess(ids.index('PREP_TARGET2'),ids.index('PREP_01'))
  self.assertLess(ids.index('PREP_01'),ids.index('DRIVE_HANDOFF'))
  self.assertLess(ids.index('DRIVE_HANDOFF'),ids.index('COUPLED_ACQUIRE'))
  self.assertNotIn('PREP_01',self.branches['TWO_BIT_00_TO_11']['operation_ids'])
  self.assertTrue(any('read back' in s.lower() and 'pulse' in s.lower() for s in self.ops['PREP_TARGET2']['actions']))
 def test_fabrication_robot_requests_start(self):
  for prefix in ['CUT','PRINT']:
   self.assertTrue(any('request start' in a.lower() for a in self.ops[prefix+'_LOAD']['actions']))
 def test_comparison_observation_starts_before_fold(self):
  ids=self.branches['PAPER_TRUSS_COMPARE']['operation_ids']
  self.assertLess(ids.index('COMPARE_SETUP'),ids.index('COMPARE_FOLD'))
  self.assertTrue(any('before' in a for a in self.ops['COMPARE_SETUP']['actions']))
  self.assertTrue(any('during' in a for a in self.ops['COMPARE_OBSERVE']['actions']))
 def test_manual_release_and_sensing_are_explicit(self):
  ids=self.branches['ONE_BIT_MANUAL']['operation_ids']
  self.assertIn('STATE_SENSOR_CHECK',ids)
  self.assertNotIn('CRANK_ATTACH',ids)
  self.assertTrue(any('manual route' in a.lower() and 'grip release' in a.lower() for a in self.ops['RELEASE_TORQUE']['actions']))
 def test_empty_global_dependency_graph_is_acyclic(self):
  # Scoped reset/loop relations are outside this global edge inventory.
  graph={o:[] for o in self.ops}
  for e in load('dependencies.json')['edges']: graph[e['from']].append(e['to'])
  seen=set(); active=set()
  def visit(n):
   self.assertNotIn(n,active,n)
   if n in seen:return
   active.add(n)
   for m in graph[n]:visit(m)
   active.remove(n);seen.add(n)
  for n in graph:visit(n)
 def test_preloads_not_conflated(self):
  self.assertEqual(self.branches['ONE_BIT_TORQUE']['condition_card']['pair_precompression_mm'],45)
  for b in ['TWO_BIT_00_TO_11','TWO_BIT_01_TO_10']:
   self.assertEqual(self.branches[b]['condition_card']['pair_precompression_mm'],[50,47.5])
 def test_zero_mode_geometry_preserves_physical_92(self):
  zero=next(g for g in load('material_cards.json')['geometries'] if g['id']=='ZERO')
  self.assertEqual(zero['theta0_deg'],92)
 def test_repeats_have_no_fictional_source_count(self):
  for b in self.branches.values():
   if b['id']=='WHOLE_PAPER_CAMPAIGN': continue
   self.assertIsNone(b['source_repetition_count'])
   self.assertEqual(b['loops'][0]['cardinality'],'positive_integer_required')
 def test_proposals_not_physical_branches(self):
  scopes=load('nonmanual_scope.json')['items']
  self.assertEqual({x['id'] for x in scopes},{'N_MODEL','N_TORQUE_READ','N_FREQ','N_NETWORK'})
  self.assertFalse(any('PERTURB' in b or 'FREQUENCY' in b for b in self.branches))
 def test_retention_requires_release_and_input(self):
  for b in ['ONE_BIT_TORQUE','ONE_BIT_MANUAL','TWO_BIT_00_TO_11','TWO_BIT_01_TO_10']:
   ids=self.branches[b]['operation_ids']; self.assertLess(ids.index('RELEASE_TORQUE'),ids.index('RETENTION_OBSERVE'))
   self.assertIn('U_RETAIN',self.branches[b]['required_input_ids'])
 def test_all_physical_routes_have_safe_closure(self):
  for b in self.branches.values():
   for o in ['SAFE_UNLOAD','MOVE','ARCHIVE','CLEANUP','REPORT']: self.assertIn(o,b['operation_ids'])
  self.assertIn('WS_MEMORY',load('station_contracts.json')['safe_unload_variants'])
 def test_private_sources_not_exported(self):
  boundary=load('RELEASE_BOUNDARY.json')
  for f in boundary['design_package_allowlist']:
   self.assertNotIn('_private',f)
   self.assertNotIn(Path(f).suffix,['.pdf','.png','.mp4'])
 def test_movie_inspection_honesty(self):
  a=load('source_access_audit.json')['movies']
  self.assertEqual(len(a),7)
  self.assertEqual([x['movie'] for x in a if x['status']=='downloaded_sampled_frames_inspected'],[1,5])
  for x in a:
   if x['movie'] not in [1,5]: self.assertIn('unread',x['status'])
 def test_actor_excludes_references(self):
  a=load('agent_visible.json'); self.assertIn('expected source outcomes',a['exclude']); self.assertIn('future measurements',a['exclude'])
 def test_no_execution_claim(self):
  e=load('provenance.json')['execution']; self.assertTrue(all(v is False for v in e.values()))
if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Contract)
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 report={'schema_version':'origami_memory_static_validation.v1','doi':'10.1038/s41467-017-00670-w','tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful(),'scope':'Static contract and reference checks only; no physics, robot or station validation','test_names':[str(t) for t,_ in result.failures+result.errors]}
 (ROOT/'tests/validation_report.json').write_text(json.dumps(report,indent=2)+'\n')
 raise SystemExit(0 if result.wasSuccessful() else 1)
