"""Finite static/symbolic design checks. No device, robot, scientific simulation or experiment runs."""
import copy
import json
import math
import unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
DOI='10.1038/s41467-024-54849-z'
def load(n):return json.loads((R/n).read_text())
def flatten(body):
 for n in body:
  if n['kind'] in ('repeat','for_each'):
   for _ in (range(3) if n['kind']=='repeat' else n['values']):yield from flatten(n['body'])
  else:yield n

def physical_route_valid(route,ops,transfers):
 """Check a finite reference expansion's physical station continuity, not reachability."""
 station=route['initial_robot_station']
 for n in flatten(route['body']):
  if n['kind']=='transfer':
   t=transfers[n['transfer_id']]
   if t['source_station']!=station or not t['measurable_completion']:return False
   station=t['target_station']
  elif n['kind']=='operation':
   o=ops[n['operation_id']]
   if o['actor'] in ('mobile_robot','station_device') and o['source_station']!=station:return False
 return station=='WS_RECORDS'

def gradient_trace_valid(events):
 """Small negative-test oracle over authored symbolic records, not an executable laboratory API."""
 baseline=False; loaded=None; recovered=True;forward=False;computed=False;adjoint=False;paired=False
 for event in events:
  kind=event['kind']
  if kind=='baseline':
   if loaded is not None or not recovered:return False
   baseline=True
  elif kind=='load':
   phase=event['phase']
   if phase not in ('forward','adjoint'):return False
   if not baseline or loaded is not None or not recovered:return False
   if phase=='adjoint' and not computed:return False
   if event['total_g']<0 or event['total_g']>event['limit_g']:return False
   loaded=phase;baseline=False;recovered=False
  elif kind=='capture':
   if event['phase'] not in ('forward','adjoint'):return False
   if loaded!=event['phase'] or not event.get('settled') or not event.get('calibration_valid'):return False
   if loaded=='forward':forward=True
   else:adjoint=True
  elif kind=='unload':loaded=None
  elif kind=='recover':
   if loaded is not None or not event.get('accepted'):return False
   recovered=True
  elif kind=='compute_adjoint':
   if not forward or loaded is not None or not recovered or not event.get('measured_output') or not event.get('force_scale'):return False
   computed=True
  elif kind=='pair':
   if not forward or not adjoint or loaded is not None or not recovered:return False
   if event['specimen_forward']!=event['specimen_adjoint'] or event['geometry_forward']!=event['geometry_adjoint']:return False
   if event['forward_bonds']!=event['adjoint_bonds']:return False
   paired=True
  else:return False
 return forward and adjoint and computed and paired and loaded is None and recovered

def printed_geometry_valid(record):
 return record['specimen_geometry']==record['print_job_geometry'] and record['specimen_id']==record['print_job_specimen_id']
def custody_valid(event):
 return event['source_released'] and event['retained'] and event['zero_load'] and event['destination_receipt'] and event['source']!=event['target']
def source_matched(branch_ids,trial_counts,loads):
 required={b['id'] for b in load('branches.json')['branches'] if b['role']=='reported_physical_route'}
 return set(branch_ids)==required and all(trial_counts.get(b)==3 for b in required) and loads==[0,2,4,6,8,10,12]
class Contract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ops={o['id']:o for o in load('operations.json')['operations']}
  cls.branches={b['id']:b for b in load('branches.json')['branches']}
  cls.ev=set(load('provenance.json')['evidence'])
  cls.unknowns={u['id'] for u in load('unknown_parameters.json')['unknowns']}
  cls.routes=load('reference_routes.json')['routes']
  cls.transfers={t['id']:t for t in load('reference_routes.json')['transfers']}
 def valid_trace(self):
  z=[]
  for phase,mass in [('forward',10),('adjoint',5)]:
   if phase=='adjoint':z.append({'kind':'compute_adjoint','measured_output':True,'force_scale':True})
   z += [{'kind':'baseline'},{'kind':'load','phase':phase,'total_g':mass,'limit_g':20},{'kind':'capture','phase':phase,'settled':True,'calibration_valid':True},{'kind':'unload'},{'kind':'recover','accepted':True}]
  z.append({'kind':'pair','specimen_forward':'S1','specimen_adjoint':'S1','geometry_forward':'G1','geometry_adjoint':'G1','forward_bonds':['b1','b2'],'adjoint_bonds':['b1','b2']})
  return z
 def test_json_and_doi(self):
  for p in R.glob('*.json'):self.assertEqual(json.loads(p.read_text())['doi'],DOI,p.name)
 def test_counts_unique(self):
  d=load('operations.json');self.assertEqual(len(self.ops),d['operation_count']);self.assertEqual(len(self.ops),len(d['operations']));self.assertEqual(len(self.branches),10);self.assertEqual(load('branches.json')['physical_configuration_count'],9)
 def test_operation_contract_fields(self):
  for o in self.ops.values():
   for k in ['actor','source_station','target_station','manipulated_objects_tools','interface','actions','preconditions','completion_state','recoveries']:self.assertTrue(o[k],(o['id'],k))
   self.assertEqual(o['execution_mode'],'symbolic_design_only');self.assertEqual(o['provenance']['fine_actions'],'task_authored_not_source_trajectory')
 def test_all_references_resolve(self):
  for o in self.ops.values():self.assertFalse(set(o['evidence_ids'])-self.ev);self.assertFalse(set(o['unknown_parameter_ids'])-self.unknowns)
  for b in self.branches.values():
   self.assertFalse(set(b['operation_ids'])-set(self.ops));self.assertFalse(set(b['evidence_ids'])-self.ev);self.assertFalse(set(b['required_input_ids'])-self.unknowns)
   for oid in b['operation_ids']:self.assertFalse(set(self.ops[oid]['unknown_parameter_ids'])-set(b['required_input_ids']),(b['id'],oid))
 def test_gate_values_are_missing(self):
  for u in load('unknown_parameters.json')['unknowns']:self.assertIsNone(u['value']);self.assertEqual(u['status'],'qualified_input_required')
 def test_fabrication_handoffs(self):
  for i in ['PRINT_LOAD','PRINT_START','PRINT_UNLOAD','POST_LOAD','POST_UNLOAD']:self.assertEqual(self.ops[i]['actor'],'mobile_robot')
  for i in ['PRINT_PROCESS','POST_PROCESS']:self.assertEqual(self.ops[i]['actor'],'station_device')
 def test_analysis_not_physical_update(self):
  self.assertEqual(self.ops['TRAIN_RUN']['actor'],'analysis_service')
  self.assertTrue(any('never mutate' in a for a in self.ops['TRAIN_RUN']['actions']))
  self.assertTrue(any('no physical width change' in a for a in self.ops['PAIR_GRADIENT']['actions']))
 def test_numerical_geometry_cannot_update_printed_specimen(self):
  r={'specimen_geometry':'G1','print_job_geometry':'G1','specimen_id':'S1','print_job_specimen_id':'S1'};self.assertTrue(printed_geometry_valid(r));r['specimen_geometry']='G2';self.assertFalse(printed_geometry_valid(r))
 def test_route_ids_and_operation_coverage(self):
  self.assertEqual(len(self.routes),9)
  for r in self.routes:
   self.assertIn(r['branch_id'],self.branches)
   ids={n['operation_id'] if n['kind']=='operation' else 'MOVE' for n in flatten(r['body'])}
   self.assertEqual(ids,set(self.branches[r['branch_id']]['operation_ids']),r['id'])
 def test_physical_station_continuity(self):
  for r in self.routes:self.assertTrue(physical_route_valid(r,self.ops,self.transfers),r['id'])
 def test_missing_transfer_rejected(self):
  r=copy.deepcopy(self.routes[0]);r['body']=[n for n in r['body'] if n.get('transfer_id')!='T_PRINT_POST'];self.assertFalse(physical_route_valid(r,self.ops,self.transfers))
 def test_transfer_contract_complete(self):
  for t in self.transfers.values():
   for k in ['source_station','target_station','carrier','preconditions','measurable_completion']:self.assertTrue(t[k])
   self.assertTrue(any('Zero active' in p for p in t['preconditions']))
   self.assertTrue(any('Custody' in p for p in t['measurable_completion']))
 def test_custody_receipt_required(self):
  e=dict(source_released=True,retained=True,zero_load=True,destination_receipt=True,source='A',target='B');self.assertTrue(custody_valid(e));e['destination_receipt']=False;self.assertFalse(custody_valid(e))
 def test_loaded_transport_rejected(self):
  e=dict(source_released=True,retained=True,zero_load=False,destination_receipt=True,source='A',target='B');self.assertFalse(custody_valid(e))
 def test_digital_analysis_preserves_station(self):
  for i in ['CAL_SOLVE','TRACK','ADJOINT_COMPUTE','PAIR_GRADIENT','BEHAVIOR_ANALYZE','REGRESSION_ANALYZE','IRIS_CLASSIFY']:self.assertEqual(self.ops[i]['actor'],'analysis_service')
  self.assertTrue(all(physical_route_valid(r,self.ops,self.transfers) for r in self.routes))
 def test_regression_loop_analysis_scope(self):
  r=next(r for r in self.routes if r['branch_id']=='REGRESSION_SWEEP');rep=next(n for n in r['body'] if n['kind']=='repeat');loop=rep['body'][0]
  self.assertEqual(loop['kind'],'for_each');self.assertEqual(loop['values'],[0,2,4,6,8,10,12]);self.assertEqual(rep['body'][1]['operation_id'],'REGRESSION_ANALYZE');self.assertNotIn('REGRESSION_ANALYZE',[n['operation_id'] for n in loop['body']])
 def test_gradient_repeat_wraps_both_fields(self):
  for r in self.routes:
   if not r['branch_id'].startswith('GRADIENT'):continue
   rep=next(n for n in r['body'] if n['kind']=='repeat');ids=[n['operation_id'] for n in rep['body']]
   self.assertEqual(ids.count('BASELINE'),2);self.assertEqual(ids.count('WEIGHT_REMOVE'),2);self.assertEqual(ids.count('RECOVERY'),2);self.assertEqual(ids[-1],'PAIR_GRADIENT');self.assertLess(ids.index('RECOVERY'),ids.index('ADJOINT_COMPUTE'))
 def test_source_gradient_conditions(self):
  self.assertEqual(self.branches['GRADIENT_SEPARATE']['condition_card']['forward_mass_g'],10);self.assertEqual(self.branches['GRADIENT_SAME']['condition_card']['forward_mass_g'],20)
  for b in ['GRADIENT_SEPARATE','GRADIENT_SAME']:self.assertTrue(self.branches[b]['condition_card']['forward_absent_in_adjoint'])
 def test_valid_symbolic_gradient_trace(self):self.assertTrue(gradient_trace_valid(self.valid_trace()))
 def test_missing_gradient_pair_rejected(self):
  z=self.valid_trace();z.pop();self.assertFalse(gradient_trace_valid(z))
 def test_unknown_gradient_phase_rejected(self):
  z=self.valid_trace()
  for e in z:
   if e.get('phase')=='adjoint':e['phase']='unknown_phase'
  self.assertFalse(gradient_trace_valid(z))
 def test_missing_forward_unload_rejected(self):
  z=self.valid_trace();z.pop(3);self.assertFalse(gradient_trace_valid(z))
 def test_stale_or_missing_baseline_rejected(self):
  z=self.valid_trace();z.pop(6);self.assertFalse(gradient_trace_valid(z))
 def test_overload_rejected(self):
  z=self.valid_trace();z[1]['total_g']=21;self.assertFalse(gradient_trace_valid(z))
 def test_unsettled_capture_rejected(self):
  z=self.valid_trace();z[2]['settled']=False;self.assertFalse(gradient_trace_valid(z))
 def test_missing_calibration_rejected(self):
  z=self.valid_trace();z[2]['calibration_valid']=False;self.assertFalse(gradient_trace_valid(z))
 def test_missing_force_scale_rejected(self):
  z=self.valid_trace();z[5]['force_scale']=False;self.assertFalse(gradient_trace_valid(z))
 def test_source_output_cannot_replace_measurement(self):
  z=self.valid_trace();z[5]['measured_output']=False;self.assertFalse(gradient_trace_valid(z))
 def test_mixed_specimen_pair_rejected(self):
  z=self.valid_trace();z[-1]['specimen_adjoint']='S2';self.assertFalse(gradient_trace_valid(z))
 def test_mixed_geometry_pair_rejected(self):
  z=self.valid_trace();z[-1]['geometry_adjoint']='G2';self.assertFalse(gradient_trace_valid(z))
 def test_wrong_bond_pair_rejected(self):
  z=self.valid_trace();z[-1]['adjoint_bonds']=['b2','b1'];self.assertFalse(gradient_trace_valid(z))
 def test_actor_goal_tokens_no_expected_labels(self):
  a=load('agent_visible.json')
  for v in a['selected_goal_templates'].values():
   s=json.dumps(v).lower()
   for forbidden in ['virginica','versicolor','setosa','behavior_left','behavior_right','96%','-0.82']:self.assertNotIn(forbidden,s)
  self.assertIn('expected source outcomes',a['exclude']);self.assertIn('future measurements',a['exclude'])
 def test_numerical_proposed_scope_not_physical(self):
  ns={n['id']:n for n in load('nonmanual_scope.json')['items']}
  for k in ['N_MSE','N_PENGUIN','N_SWITCH','N_DAMAGE','N_IMPORTANCE','N_FUTURE']:self.assertIn(k,ns);self.assertFalse(ns[k]['executed_for_this_package'])
  self.assertEqual(ns['N_FUTURE']['classification'],'proposed_not_implemented')
 def test_geometry_ancestry_conditional(self):
  l=load('lineage_contract.json');self.assertFalse(any(c[0]=='numerical_job_id' for c in l['required_chains']));self.assertTrue(any(c['when']=='geometry created by numerical training' for c in l['conditional_chains']))
 def test_source_repeats_not_specimen_count(self):
  for b in self.branches.values():
   if b['role']=='reported_physical_route':self.assertEqual(b['source_repetition_count'],3);self.assertIsNone(b['source_specimen_count'])
 def test_partial_campaign_not_source_matched(self):
  ids=[b for b in self.branches if b!='WHOLE_PAPER_CAMPAIGN'];counts={b:3 for b in ids};m=[0,2,4,6,8,10,12]
  self.assertTrue(source_matched(ids,counts,m));self.assertFalse(source_matched(ids[:-1],counts,m));counts[ids[0]]=1;self.assertFalse(source_matched(ids,counts,m));self.assertFalse(source_matched(ids,{b:3 for b in ids},m[1:]))
 def test_campaign_covers_operations_and_physical_routes(self):
  c=self.branches['WHOLE_PAPER_CAMPAIGN'];self.assertEqual(set(c['operation_ids']),set(self.ops));self.assertEqual(set(c['subbranch_ids']),set(self.branches)-{c['id']})
 def test_coverage_and_controls_resolve(self):
  for c in load('coverage_matrix.json')['rows']:self.assertFalse(set(c['task_branch_ids'])-set(self.branches));self.assertFalse(set(c['evidence_ids'])-self.ev)
  for c in load('control_packages.json')['controls']:self.assertIn(c['gates_operation'],self.ops)
 def test_source_audit_does_not_claim_viewed_movies(self):
  a=load('source_access_audit.json');self.assertEqual(len(a['movies']),5);self.assertTrue(all(m['status']=='unviewed_description_read' for m in a['movies']));self.assertFalse(a['source_packet_complete']);self.assertFalse(a['exhaustive_source_read_complete'])
 def test_no_execution_claims(self):self.assertTrue(all(v is False for v in load('provenance.json')['execution'].values()))
 def test_no_raw_sources_in_allowlist(self):
  for f in load('RELEASE_BOUNDARY.json')['design_package_allowlist']:
   self.assertNotIn('_private',f);self.assertNotIn(Path(f).suffix.lower(),['.pdf','.png','.jpg','.mov','.mp4','.xlsx'])
 def test_source_license_and_project_preservation(self):
  l=load('provenance.json')['license'];self.assertEqual(l['article'],'CC BY-NC-ND 4.0');self.assertIn('left unchanged',l['project'])
 def test_closure_contains_archive_inventory_cleanup(self):
  for r in self.routes:
   ids=[n.get('operation_id') for n in r['body']]
   for k in ['STRING_REMOVE','UNDOCK','ARCHIVE','CLEANUP','RETURN_TOOLS','REPORT']:self.assertIn(k,ids)
   self.assertEqual(ids[-1],'REPORT')
if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Contract)
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 report={'schema_version':'mechanical_backprop_static_validation.v1','doi':DOI,'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful(),'scope':'Finite static and symbolic contract checks only; no robot, station, mechanics or scientific validation','failed_test_names':[str(t) for t,_ in result.failures+result.errors]}
 (R/'tests/validation_report.json').write_text(json.dumps(report,indent=2)+'\n')
 raise SystemExit(0 if result.wasSuccessful() else 1)
