"""Static task-contract checks. These do not validate physical execution."""
import copy
import json
import pathlib
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/name).read_text())
def strings(x):
 if isinstance(x,str):yield x
 elif isinstance(x,list):
  for y in x:yield from strings(y)
 elif isinstance(x,dict):
  for y in x.values():yield from strings(y)
def validate(packet):
 ops=packet['operations']['operations']; branches=packet['branches']['branches']
 oi={o['id']:o for o in ops};bi={b['id']:b for b in branches}
 assert len(oi)==len(ops) and len(bi)==len(branches),'duplicate IDs'
 ev={e['id'] for e in packet['provenance']['evidence']}; un={u['id'] for u in packet['unknown_parameters']['parameters']};stations={s['id']:s for s in packet['station_contracts']['stations']}
 for o in ops:
  for field in ['actor','objects','tool','station_id','interface','preconditions','action','completion_evidence','translation_kind']:
   assert o.get(field),f'missing operation field {o["id"]}/{field}'
  assert o['station_id'] in stations,'unknown station'
  assert set(o['source_evidence_ids'])<=ev,'unknown operation evidence'
  assert set(o['unknown_input_ids'])<=un,'unknown input ID'
  if o['translation_kind']=='device_process':assert o['actor']=='device','automatic process mislabeled as robot'
 for b in branches:
  assert b['preparation_route'] in packet['branches']['preparation_routes'],'unknown prep route'
  assert set(b['source_evidence_ids'])<=ev and set(b['required_input_ids'])<=un,'branch references'
  for s in strings(b['test_body']):
   if s.isupper() or s.startswith('@'):
    assert b['operation_bindings'].get(s,s) in oi,'unknown route operation'
  if b['execution_mode']=='mechanical':assert 'ANALYZE_ELEMENT' in b['test_body'],'quantitative analysis unreachable'
  if b['execution_mode']=='torsion':
   assert 'ANALYZE_TORQUE' in b['test_body'] and b.get('upstream_measurement_dependency'),'missing measured torque parents'
 for b in branches:
  assert b.get('condition_transition',{}).get('no_label_only_transition') is True,'missing physical condition transition'
  if b['id'] in ['ARRAY_COMPRESSION','ARRAY_TENSION']:assert 'ARRAY_PIN' in b['condition_transition']['reuse_path']['operations'],'array angle changes without pin operation'
 for a,c in [('ARRAY_COMPRESSION','C_III'),('ARRAY_TENSION','C_I')]:
  assert [v['angle_deg'] for v in bi[a]['conditions']]==[22.5,45,67.5,90,112.5,135,157.5],'missing array angle'
  assert all(v['class']==c for v in bi[a]['conditions']),'array roles mixed'
 assert bi['CREASE_TENDENCY']['preparation_route']=='PREP_THICK_PARTS','coupon consumes assembled element'
 coupon=packet['branches']['preparation_routes']['PREP_THICK_PARTS']
 assert 'ELEMENT_CLOSE' not in list(strings(coupon)),'coupon preassembled then reassembled'
 assert stations['WS_OBSERVE']['physical_location'] is False and stations['WS_OBSERVE']['specimen_movement']=='none','observation teleports mounted sample'
 assert len(packet['lineage_contract']['array_ratio_required_parents'])>=6,'missing array lineage'
 assert packet['lineage_contract']['no_actual_records_created'],'fabricated experimental records'
 assert packet['source_access_audit']['source_packet_closed'] is False,'unread packet falsely closed'
 movie9=next(m for m in packet['source_access_audit']['movies'] if m['number']==9)
 assert movie9['status']=='unread' and movie9['method_bearing'],'Movie9 evidence overstated'
 covered={b for row in packet['coverage_matrix']['rows'] for b in row['task_branch_ids']}
 assert set(bi)<=covered,'uncovered physical branch'
 assert packet['RELEASE_BOUNDARY']['physical_execution'] is False and packet['RELEASE_BOUNDARY']['feasibility_validated'] is False,'physical validation overclaim'
 return True
FILES=['operations','branches','provenance','unknown_parameters','station_contracts','lineage_contract','source_access_audit','coverage_matrix','RELEASE_BOUNDARY']
class ContractTests(unittest.TestCase):
 def setUp(self):self.p={f:read(f+'.json') for f in FILES}
 def test_baseline_contract(self):self.assertTrue(validate(self.p))
 def test_reject_missing_element_analysis(self):
  for b in self.p['branches']['branches']:
   if b['id']=='ELEMENT_RESPONSE':b['test_body'].remove('ANALYZE_ELEMENT')
  with self.assertRaisesRegex(AssertionError,'analysis'):validate(self.p)
 def test_reject_torque_without_measured_parents(self):
  next(b for b in self.p['branches']['branches'] if b['id']=='TRI_TORSION').pop('upstream_measurement_dependency')
  with self.assertRaisesRegex(AssertionError,'torque parents'):validate(self.p)
 def test_reject_coupon_from_completed_element(self):
  next(b for b in self.p['branches']['branches'] if b['id']=='CREASE_TENDENCY')['preparation_route']='PREP_THICK'
  with self.assertRaisesRegex(AssertionError,'coupon'):validate(self.p)
 def test_reject_missing_array_angle(self):
  next(b for b in self.p['branches']['branches'] if b['id']=='ARRAY_COMPRESSION')['conditions'].pop()
  with self.assertRaisesRegex(AssertionError,'array angle'):validate(self.p)
 def test_reject_observation_teleport(self):
  next(s for s in self.p['station_contracts']['stations'] if s['id']=='WS_OBSERVE')['specimen_movement']='move mounted specimen'
  with self.assertRaisesRegex(AssertionError,'teleports'):validate(self.p)
 def test_reject_movie_access_overclaim(self):
  next(m for m in self.p['source_access_audit']['movies'] if m['number']==9)['status']='inspected'
  with self.assertRaisesRegex(AssertionError,'Movie9'):validate(self.p)
 def test_reject_label_only_angle_change(self):
  next(b for b in self.p['branches']['branches'] if b['id']=='ARRAY_TENSION')['condition_transition']['reuse_path']['operations']=[]
  with self.assertRaisesRegex(AssertionError,'pin operation'):validate(self.p)
 def test_allowlist_excludes_sources(self):
  allow=read('EXPORT_ALLOWLIST.json')['files']
  self.assertIn('TASK_DESIGN.md',allow)
  for f in allow:
   self.assertNotIn('.private',f);self.assertTrue((ROOT/f).is_file())
   self.assertNotIn(pathlib.Path(f).suffix.lower(),['.pdf','.png','.jpg','.mp4','.xlsx'])
 def test_all_public_json_parse(self):
  for p in ROOT.glob('*.json'):self.assertIsInstance(json.loads(p.read_text()),dict)
if __name__=='__main__':unittest.main()
