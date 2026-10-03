#!/usr/bin/env python3
"""Design-only validation. Synthetic records do not authenticate physical events."""
import copy
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/name).read_text())
def collect_refs(value,key):
 found=[]
 if isinstance(value,dict):
  for k,v in value.items():
   if k==key:found.extend(v)
   else:found.extend(collect_refs(v,key))
 elif isinstance(value,list):
  for v in value:found.extend(collect_refs(v,key))
 return found
def dag(nodes,edges):
 nodes=set(nodes);incoming={n:0 for n in nodes};out={n:[] for n in nodes}
 for a,b in edges:
  if a not in nodes or b not in nodes:return False
  incoming[b]+=1;out[a].append(b)
 ready=[n for n in nodes if incoming[n]==0];seen=[]
 while ready:
  n=ready.pop();seen.append(n)
  for v in out[n]:
   incoming[v]-=1
   if incoming[v]==0:ready.append(v)
 return len(seen)==len(nodes)
def validate_fixture(x):
 """Small adversarial metadata contract, not a robot evaluator implementation."""
 errors=[]
 if not x.get('prepared_by_robot'):errors.append('preparation evidence missing')
 if x.get('unresolved_selected_gates'):errors.append('dependent inputs unresolved')
 if len(x.get('current_locations',[]))!=1:errors.append('nonunique location')
 for move in x.get('moves',[]):
  if not all(move.get(k) for k in ['sample_id','from_station','to_station','source_released','destination_supported']):errors.append('incomplete handoff')
 if x.get('intact_use_after_disassembly'):errors.append('destructive lineage violation')
 if x.get('state_arm')=='Stage1' and x.get('postcured_before_collision'):errors.append('wrong Stage1 state')
 if x.get('state_arm')=='adapted' and not x.get('postcured_before_collision'):errors.append('missing shape adaptation')
 if x.get('collision') and not x.get('prechallenge_image_id'):errors.append('missing target baseline')
 if x.get('baseline_sample_id')!=x.get('post_sample_id'):errors.append('unmatched pre/post sample')
 if x.get('observations_from_source_outcomes'):errors.append('source outcomes masquerade as measurements')
 if not set(x.get('required_controls',[])) <= set(x.get('completed_controls',[])):errors.append('missing control')
 if x.get('denominator_changed_without_record'):errors.append('hidden missingness')
 if x.get('seven_day_challenge') and x.get('actual_exposure_seconds',0)<7*24*3600:errors.append('incomplete dwell')
 raw=set(x.get('raw_ids',[]))
 if not raw:errors.append('no acquired raw records')
 for d in x.get('derived',[]):
  if not d.get('parents') or not set(d['parents'])<=raw:errors.append('unresolved raw parents')
 if x.get('specimen_count_basis')=='pair_comparisons':errors.append('comparison count substituted for specimens')
 return errors
class PackageTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ops=load('operations.json')['operations'];cls.opids={o['id'] for o in cls.ops}
  cls.configs=load('branches.json')['configurations'];cls.routes=load('dependencies.json')['routes']
 def test_01_json_parse(self):
  self.assertGreaterEqual(len(list(ROOT.glob('*.json'))),20)
  for f in ROOT.glob('*.json'):self.assertIsInstance(json.loads(f.read_text()),dict)
 def test_02_source_refs(self):
  known={r['id'] for r in load('provenance.json')['references']}
  for f in ROOT.glob('*.json'):
   for ref in collect_refs(json.loads(f.read_text()),'source_refs'):self.assertIn(ref,known,(f.name,ref))
 def test_03_operation_ids_and_gates(self):
  self.assertEqual(len(self.ops),len(self.opids))
  gates={u['id'] for u in load('unknown_parameters.json')['unknowns']}
  for c in self.configs:
   self.assertTrue(set(c['operation_ids'])<=self.opids)
   self.assertTrue(set(c['required_unknowns'])<=gates)
   needed={u for o in self.ops if o['id'] in c['operation_ids'] for u in o['required_unknowns']}
   self.assertTrue(needed<=set(c['required_unknowns']),c['id'])
 def test_04_actor_and_stations(self):
  stations={s['id'] for s in load('station_contracts.json')['stations']}
  for o in self.ops:
   self.assertIn(o['station'],stations)
   for k in ['robot_actions','manipulated_objects_and_tools','source_station','target_station','preconditions','completion_evidence','completion_state']:
    self.assertTrue(o[k],(o['id'],k))
   self.assertIn('device_actions',o)
   self.assertIn('mobile',o['actor'])
 def test_05_graphs(self):
  self.assertEqual({r['configuration_id'] for r in self.routes},{c['id'] for c in self.configs})
  for r in self.routes:
   self.assertTrue(dag(r['suggested_operation_ids'],r['causal_edges']),r['configuration_id'])
   for a in r.get('arm_routes',[]):self.assertTrue(dag(a['operation_ids'],a['causal_edges']),a['arm'])
 def test_06_collision_arms(self):
  r=next(r for r in self.routes if r['configuration_id']=='TRAPPED_COLLISION')
  for a in r['arm_routes']:
   self.assertIn(['COLLISION_BASELINE','COLLIDE_TRAPPED'],a['causal_edges'])
   self.assertIn(['COLLIDE_TRAPPED','IMAGE'],a['causal_edges'])
   if a['arm']=='Stage1trapped':
    self.assertNotIn('POSTCURE',a['operation_ids']);self.assertIn('postcured',a['forbidden_prior_states'])
   else:
    self.assertIn(['POSTCURE','COLLISION_BASELINE'],a['causal_edges'])
    self.assertIn(['POSTCURE','COLLIDE_TRAPPED'],a['causal_edges'])
 def test_07_acquisition_order(self):
  r=next(r for r in self.routes if r['configuration_id']=='FREEFALL_SURFACES')
  self.assertIn(['DROP_BEAD','IMAGE'],r['causal_edges'])
  r=next(r for r in self.routes if r['configuration_id']=='PUF_HIERARCHY')
  self.assertIn(['AUTH_IMAGE','CONTACT_ANALYSIS'],r['causal_edges'])
  self.assertIn(['CONTACT_ANALYSIS','AUTH_ANALYSIS'],r['causal_edges'])
 def test_08_controls_resolve(self):
  ids={c['id'] for c in load('control_packages.json')['control_packages']}
  for c in self.configs:self.assertTrue(set(c['control_package_ids'])<=ids,c['id'])
 def test_09_coverage(self):
  ids={c['id'] for c in self.configs}
  listed={c for row in load('coverage_matrix.json')['coverage'] for c in row['configuration_ids']}
  self.assertEqual(ids,listed)
 def test_10_preparation_not_receipt_only(self):
  for id in ['SANDWICH','FILM','COAT','CUSTOM_PARTICLES','GUIDE_FAB']:
   o=next(o for o in self.ops if o['id']==id)
   self.assertGreaterEqual(len(o['robot_actions']),3)
   self.assertTrue(o['required_unknowns'])
 def test_11_count_and_duration_semantics(self):
  p={p['id']:p for p in load('source_parameters.json')['parameters']}
  self.assertEqual(p['AGING']['value']['duration'],7)
  self.assertEqual(p['STABILITY_CONTACTS']['value'],50)
  self.assertIn('not',p['STABILITY_CONTACTS']['applies_to'])
  self.assertEqual(p['PUF_PAIR_COUNTS']['value'],{'total':40000,'intra':200,'inter':39800})
 def test_12_release(self):
  x=load('RELEASE_BOUNDARY.json')
  for k in ['source_asset_export','physics_execution','robot_execution','scientific_validation','loader_implemented']:self.assertFalse(x[k])
  self.assertIn('source_outcomes.json',load('agent_visible.json')['exclude'])
 def test_13_no_source_assets(self):
  for f in ROOT.rglob('*'):
   if '_work' in f.parts or not f.is_file():continue
   self.assertNotIn(f.suffix.lower(),['.pdf','.png','.jpg','.jpeg','.mp4','.html'],str(f))
 def test_14_gate_nulls(self):
  for u in load('unknown_parameters.json')['unknowns']:
   self.assertIsNone(u['default']);self.assertTrue(u['resolution_required'])
 def test_15_source_access_honesty(self):
  x=load('source_access_audit.json')
  movies=[s for s in x['sources_unread'] if s['id'].startswith('MOVIE_')]
  self.assertEqual(len(movies),5)
  self.assertTrue(all('Unread' in s['status'] for s in movies))
 def test_33_variant_manufacturing_order(self):
  for r in self.routes:
   if r['configuration_id'].startswith('SHAPED_'):
    for edge in [['CUSTOM_PARTICLES','WEIGH_CHARGE'],['IMAGE','FLUORESCENCE'],['FLUORESCENCE','CONTACT_ANALYSIS']]:self.assertIn(edge,r['causal_edges'])
 def test_34_reuse_cycle_order(self):
  r=next(r for r in self.routes if r['configuration_id']=='TRAP_REUSE')
  self.assertIn(['IMAGE','REUSE_RESET'],r['causal_edges'])
  x=r['cycle_expansion']['cross_cycle_required_edge']
  self.assertEqual((x['from_operation'],x['to_operation']),('REUSE_RESET','LOAD_TUBE'))
  self.assertEqual((x['from_cycle'],x['to_cycle']),('n','n+1'))
 def test_35_patterned_surface_order(self):
  r=next(r for r in self.routes if r['configuration_id']=='SURFACE_TRIO')
  self.assertIn(['VERIFY_TRAPS','DROP_BEAD'],r['causal_edges'])
class AdversarialTests(unittest.TestCase):
 def setUp(self):
  self.good={'prepared_by_robot':True,'current_locations':['OPTICAL'],'moves':[{'sample_id':'synthetic_array','from_station':'ASSEMBLY','to_station':'OPTICAL','source_released':True,'destination_supported':True}],'state_arm':'adapted','postcured_before_collision':True,'collision':True,'prechallenge_image_id':'synthetic_pre','baseline_sample_id':'synthetic_array','post_sample_id':'synthetic_array','required_controls':['a','b'],'completed_controls':['a','b'],'raw_ids':['synthetic_pre','synthetic_post'],'derived':[{'id':'synthetic_result','parents':['synthetic_pre','synthetic_post']}],'independent_specimen_count':2,'pair_comparison_count':4}
 def reject(self,**kw):
  x=copy.deepcopy(self.good);x.update(kw);self.assertTrue(validate_fixture(x))
 def test_16_valid_metadata_only(self):self.assertEqual(validate_fixture(self.good),[])
 def test_17_prepared_shortcut(self):self.reject(prepared_by_robot=False)
 def test_18_missing_gate(self):self.reject(unresolved_selected_gates=['U_UV'])
 def test_19_phantom_move(self):
  x=copy.deepcopy(self.good);x['moves'][0]['destination_supported']=False;self.assertTrue(validate_fixture(x))
 def test_20_duplicate_location(self):self.reject(current_locations=['OPTICAL','UV'])
 def test_21_destructive_reuse(self):self.reject(intact_use_after_disassembly=True)
 def test_22_wrong_stage(self):self.reject(state_arm='Stage1',postcured_before_collision=True)
 def test_23_missing_adaptation(self):self.reject(postcured_before_collision=False)
 def test_24_missing_baseline(self):self.reject(prechallenge_image_id=None)
 def test_25_swapped_sample(self):self.reject(post_sample_id='another_array')
 def test_26_copied_paper_result(self):self.reject(observations_from_source_outcomes=True)
 def test_27_dropped_control(self):self.reject(completed_controls=['a'])
 def test_28_deleted_missing_site(self):self.reject(denominator_changed_without_record=True)
 def test_29_fake_dwell(self):self.reject(seven_day_challenge=True,actual_exposure_seconds=10)
 def test_30_parentless_analysis(self):self.reject(derived=[{'id':'d','parents':['unacquired']}])
 def test_31_count_inflation(self):self.reject(independent_specimen_count=4,pair_comparison_count=4,specimen_count_basis='pair_comparisons')
 def test_32_no_raw_data(self):self.reject(raw_ids=[])
if __name__=='__main__':
 unittest.main(verbosity=2)
