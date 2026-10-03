#!/usr/bin/env python3
"""Finite design checks and synthetic metadata tests; never physical validation."""
import copy, json, unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def load(n): return json.loads((R/n).read_text())
def refs(obj,key):
 out=[]
 if isinstance(obj,dict):
  for k,v in obj.items():
   if k==key:out.extend(v)
   else:out.extend(refs(v,key))
 elif isinstance(obj,list):
  for v in obj:out.extend(refs(v,key))
 return out
def dag(nodes,edges):
 nodes=set(nodes); counts={n:0 for n in nodes}; dest={n:[] for n in nodes}
 for a,b in edges:
  if a not in nodes or b not in nodes:return False
  counts[b]+=1;dest[a].append(b)
 ready=[n for n in nodes if not counts[n]];seen=[]
 while ready:
  n=ready.pop();seen.append(n)
  for k in dest[n]:
   counts[k]-=1
   if not counts[k]:ready.append(k)
 return len(seen)==len(nodes)
def validate_synthetic(record):
 """Illustrative evidence invariants. Does not authenticate any receipt."""
 errors=[]
 if not record.get('robot_preparation'):errors.append('missing_preparation')
 if record.get('unresolved_selected_gates'):errors.append('unresolved_gate')
 if len(record.get('current_locations',[]))!=1:errors.append('nonunique_location')
 if record.get('outer_diameter_mm',0)<=record.get('inner_diameter_mm',0):errors.append('impossible_geometry')
 for m in record.get('moves',[]):
  if not all(m.get(k) for k in ['object_id','origin_observed','carrier','source_released','destination_supported']):errors.append('incomplete_move')
 if record.get('pullout'):
  if not record.get('temperature_trace'):errors.append('missing_temperature')
  d=record.get('max_temperature_deviation_degC')
  if d is None or d>=2:errors.append('temperature_invalid')
 if record.get('new_mechanical_cycle') and not (record.get('cold_reset') and record.get('reinserted')):errors.append('cycle_state_missing')
 if record.get('repacked') and record.get('same_packing_claim'):errors.append('packing_identity_violation')
 if record.get('experimental_n_origin')=='DEM_configurations':errors.append('wrong_repeat_unit')
 if record.get('XCT_unloaded') and not record.get('exposure_off_release'):errors.append('XCT_access_violation')
 if record.get('hold_load_active') and not record.get('catch_and_guard'):errors.append('load_not_contained')
 if record.get('extended_hold') and (record.get('actual_hold_seconds',0)<=15*3600 or not record.get('continuous_hold_evidence')):errors.append('hold_not_demonstrated')
 if record.get('observations_from_source_outcomes'):errors.append('source_observation_leak')
 if not set(record.get('required_controls',[]))<=set(record.get('completed_controls',[])):errors.append('missing_control')
 raw=set(record.get('raw_ids',[]))
 if not raw:errors.append('missing_raw')
 for d in record.get('derived',[]):
  if not d.get('parents') or not set(d['parents'])<=raw:errors.append('orphan_derived')
 if record.get('discarded_invalid_attempt'):errors.append('hidden_invalid_attempt')
 if not record.get('dispositions_complete'):errors.append('unreconciled_end_state')
 return errors
GOOD={'robot_preparation':True,'unresolved_selected_gates':[],'current_locations':['supported_station'],'outer_diameter_mm':80,'inner_diameter_mm':32,'moves':[{'object_id':'assemblyA','origin_observed':True,'carrier':'qualifiedA','source_released':True,'destination_supported':True}],'pullout':True,'temperature_trace':'raw_temp','max_temperature_deviation_degC':1.9,'new_mechanical_cycle':True,'cold_reset':True,'reinserted':True,'repacked':False,'same_packing_claim':True,'experimental_n_origin':'independent_physical_packings','XCT_unloaded':True,'exposure_off_release':True,'hold_load_active':True,'catch_and_guard':True,'extended_hold':True,'actual_hold_seconds':54001,'continuous_hold_evidence':True,'observations_from_source_outcomes':False,'required_controls':['A'],'completed_controls':['A'],'raw_ids':['force','raw_temp'],'derived':[{'parents':['force','raw_temp']}],'discarded_invalid_attempt':False,'dispositions_complete':True}
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ops=load('operations.json')['operations'];cls.cfg=load('branches.json')['configurations'];cls.routes=load('dependencies.json')['routes']
 def test_01_json_parse(self):
  for p in R.glob('*.json'):self.assertIsInstance(json.loads(p.read_text()),dict,p.name)
 def test_02_source_references(self):
  known={r['id'] for r in load('provenance.json')['references']}
  for p in R.glob('*.json'):self.assertTrue(set(refs(json.loads(p.read_text()),'source_refs'))<=known,p.name)
 def test_03_operations(self):
  ids=[o['id'] for o in self.ops];self.assertEqual(len(ids),len(set(ids)))
  stations={s['id'] for s in load('station_contracts.json')['stations']}
  for o in self.ops:
   self.assertIn(o['station'],stations)
   for key in ['actor','manipulated_objects_and_tools','source_station','target_station','robot_actions','interfaces','preconditions','completion_state','completion_evidence']:self.assertTrue(o[key],(o['id'],key))
   self.assertIn('device_actions',o);self.assertEqual(o['provenance_class'],'authored_robot_translation')
 def test_04_gates_and_controls(self):
  gates={u['id'] for u in load('unknown_parameters.json')['unknowns']};controls={c['id'] for c in load('control_packages.json')['controls']};oids={o['id'] for o in self.ops}
  for c in self.cfg:
   self.assertTrue(set(c['operation_ids'])<=oids)
   self.assertTrue(set(c['required_unknowns'])<=gates)
   needed={g for o in self.ops if o['id'] in c['operation_ids'] for g in o['required_unknowns']}
   self.assertTrue(needed<=set(c['required_unknowns']),c['id'])
   self.assertTrue(set(c['required_controls'])<=controls,c['id'])
 def test_05_routes(self):
  self.assertEqual({r['configuration_id'] for r in self.routes},{c['id'] for c in self.cfg})
  for r in self.routes:
   self.assertTrue(dag(r['suggested_operation_ids'],r['causal_edges']),r['configuration_id'])
   self.assertEqual(r['suggested_operation_ids'],next(c['operation_ids'] for c in self.cfg if c['id']==r['configuration_id']))
   for loop in r['loop_contracts']:self.assertTrue(set(loop['repeat_operation_ids'])<=set(r['suggested_operation_ids']))
 def test_06_full_practical_scope(self):
  self.assertEqual(len(self.cfg),13)
  required={'TEMP_PHI','CYCLE_PULL','ASPECT_RATIO','CONTAINER_SIZE','BALL_FIXED_RODS','BALL_FIXED_TOTAL','MATERIAL_DSC','SINGLE_ROD_BEND','FRICTION_PAIRS','XCT_STATES','XCT_CYCLES','HOLD_RELEASE','EXTENDED_HOLD'}
  self.assertEqual({c['id'] for c in self.cfg},required)
  for row in load('coverage_matrix.json')['coverage']:self.assertTrue(set(row['configuration_ids'])<=required)
 def test_07_physical_preparation(self):
  for c in self.cfg:
   self.assertIn('CUT_RODS',c['operation_ids'])
   if c['id'] not in ['MATERIAL_DSC','SINGLE_ROD_BEND','FRICTION_PAIRS']:
    for op in ['PMMA_FAB','NYLON_FAB','PACK_CLOSE','INSERT_STICK']:self.assertIn(op,c['operation_ids'])
 def test_08_cycle_separation(self):
  x=next(c for c in self.cfg if c['id']=='XCT_CYCLES');m=next(c for c in self.cfg if c['id']=='CYCLE_PULL')
  self.assertNotIn('C_CYCLE',x['required_controls']);self.assertIn('C_XCT_CYCLE',x['required_controls']);self.assertIn('C_CYCLE',m['required_controls'])
  for r in self.routes:
   if r['configuration_id']=='CYCLE_PULL':
    loop=r['loop_contracts'][0]['repeat_operation_ids'];self.assertLess(loop.index('COOL_RESET'),loop.index('REINSERT'))
 def test_09_source_ambiguities(self):
  ids={i['id'] for i in load('source_conflicts.json')['conflicts']}
  self.assertTrue({'CONTAINER_OUTER','XCT_VOLTAGE','ROD_INITIAL_STATE','XCT_CYCLE_SEQUENCE'}<=ids)
  ps={p['id']:p for p in load('source_parameters.json')['parameters']}
  self.assertEqual(ps['P_SIZE_DINS']['value'][-1],84);self.assertEqual(ps['P_OUTER']['value'][0],80)
  self.assertIn('Not evidence',ps['P_XCT_RATING']['qualification_note']);self.assertIn('Not a count of physical',ps['P_DEM_REPEATS']['qualification_note'])
 def test_10_export_boundary(self):
  allow=load('EXPORT_ALLOWLIST.json')['files'];self.assertEqual(len(allow),len(set(allow)))
  for p in allow:
   self.assertTrue((R/p).is_file(),p);self.assertNotIn(Path(p).suffix.lower(),['.pdf','.png','.jpg','.jpeg','.mp4','.xlsx','.docx'])
   self.assertFalse(Path(p).is_absolute());self.assertNotIn('..',Path(p).parts)
  self.assertNotIn('build_package.py',allow)
 def test_11_release_truth(self):
  b=load('RELEASE_BOUNDARY.json')
  for k in ['physical_execution','device_execution','remote_writes','cad_or_viewer_work','publisher_assets_included','repository_license_change']:self.assertFalse(b[k])
  self.assertFalse(load('source_access_audit.json')['source_completeness_claim'])
 def test_12_good_synthetic_record(self):self.assertEqual(validate_synthetic(GOOD),[])
 def test_13_reject_incomplete_preparation(self):
  r=copy.deepcopy(GOOD);r['robot_preparation']=False;self.assertIn('missing_preparation',validate_synthetic(r))
 def test_14_reject_gate_and_transport(self):
  r=copy.deepcopy(GOOD);r['unresolved_selected_gates']=['U_PULL'];r['moves'][0]['carrier']=None
  self.assertIn('unresolved_gate',validate_synthetic(r));self.assertIn('incomplete_move',validate_synthetic(r))
 def test_15_reject_temperature_boundary(self):
  for value in [2,2.1,None]:
   r=copy.deepcopy(GOOD);r['max_temperature_deviation_degC']=value;self.assertIn('temperature_invalid',validate_synthetic(r))
 def test_16_reject_absent_temperature(self):
  r=copy.deepcopy(GOOD);r['temperature_trace']=None;self.assertIn('missing_temperature',validate_synthetic(r))
 def test_17_reject_cycle_shortcut(self):
  r=copy.deepcopy(GOOD);r['reinserted']=False;self.assertIn('cycle_state_missing',validate_synthetic(r))
 def test_18_reject_repack_identity(self):
  r=copy.deepcopy(GOOD);r['repacked']=True;self.assertIn('packing_identity_violation',validate_synthetic(r))
 def test_19_reject_DEM_n(self):
  r=copy.deepcopy(GOOD);r['experimental_n_origin']='DEM_configurations';self.assertIn('wrong_repeat_unit',validate_synthetic(r))
 def test_20_reject_XCT_access(self):
  r=copy.deepcopy(GOOD);r['exposure_off_release']=False;self.assertIn('XCT_access_violation',validate_synthetic(r))
 def test_21_reject_load_duration(self):
  r=copy.deepcopy(GOOD);r['catch_and_guard']=False;r['actual_hold_seconds']=54000
  self.assertIn('load_not_contained',validate_synthetic(r));self.assertIn('hold_not_demonstrated',validate_synthetic(r))
 def test_22_reject_outcome_and_raw_shortcuts(self):
  r=copy.deepcopy(GOOD);r['observations_from_source_outcomes']=True;r['derived'][0]['parents']=['paper_figure']
  self.assertIn('source_observation_leak',validate_synthetic(r));self.assertIn('orphan_derived',validate_synthetic(r))
 def test_23_reject_hidden_failure(self):
  r=copy.deepcopy(GOOD);r['discarded_invalid_attempt']=True;self.assertIn('hidden_invalid_attempt',validate_synthetic(r))
 def test_24_reject_impossible_geometry(self):
  r=copy.deepcopy(GOOD);r['inner_diameter_mm']=84;self.assertIn('impossible_geometry',validate_synthetic(r))
 def test_25_reject_missing_control_endstate(self):
  r=copy.deepcopy(GOOD);r['completed_controls']=[];r['dispositions_complete']=False
  self.assertIn('missing_control',validate_synthetic(r));self.assertIn('unreconciled_end_state',validate_synthetic(r))
if __name__=='__main__':unittest.main(verbosity=2)
