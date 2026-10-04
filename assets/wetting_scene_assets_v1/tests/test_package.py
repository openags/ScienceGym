import unittest,json,struct,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def read(n):return json.loads((P/n).read_text())
class Package(unittest.TestCase):
 def test_exact_operations(self):
  p=read('operation_binding_contract.json');b=read('operation_bindings.json');self.assertEqual(len(b['bindings']),74);self.assertEqual({x['operation_id'] for x in b['bindings']},{x['operation_id'] for x in p['operation_bindings']})
  for x,y in zip(b['bindings'],p['operation_bindings']):
   for k in ['operation_id','asset_id','anchor_ids','guard_ids','interaction']:self.assertEqual(x[k],y[k])
 def test_anchor_coverage(self):
  a=read('affordances.json')['anchors'];self.assertEqual(len(a),61);self.assertEqual(len({x['scene_object'] for x in a}),61)
  self.assertEqual({x['scene_object'] for x in a},{n for b in read('operation_bindings.json')['bindings'] for n in b['anchor_ids']})
  req=read('task_binding_snapshot.json');self.assertEqual({x['scene_object'] for x in a},{g['id']+'.'+n for g in req['groups'] for n in g['required_anchors']})
  for b in read('operation_bindings.json')['bindings']:
   self.assertEqual({x['scene_object'] for x in b['resolved_anchors']},set(b['anchor_ids']));self.assertFalse(b['physical_execution'])
 def test_assets_and_contacts(self):
  inv=read('asset_inventory.json');self.assertEqual(len(inv['assets']),12);self.assertEqual(inv['imported_mesh_count'],0)
  aff=read('affordances.json');self.assertGreater(len(aff['candidate_carrier_contacts']),10);self.assertGreater(len(aff['exclusion_regions']),5);self.assertGreater(len(aff['collision_proxies']),4)
  self.assertTrue(all(not c['physical_grasp_enabled'] for c in aff['candidate_carrier_contacts']))
 def test_render_receipts(self):
  r=read('review/render_receipt.json');self.assertEqual(r['device'],'CPU');self.assertEqual(len(r['views']),3)
  for v in r['views']:
   raw=(P/v['file']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),v['sha256']);self.assertEqual(raw[:8],b'\x89PNG\r\n\x1a\n');self.assertEqual(struct.unpack('>II',raw[16:24]),(1800,1200));self.assertTrue(v['actual_render'])
 def test_actual_geometry_checks(self):
  b=read('review/blend_validation.json');g=read('review/glb_import_validation.json');self.assertEqual(b['status'],'PASS');self.assertTrue(b['actual_native_reopen']);self.assertEqual(g['status'],'PASS');self.assertTrue(g['actual_reimports']);self.assertEqual(len(g['files']),2)
 def test_boundaries(self):
  m=read('asset_metadata.json');self.assertFalse(m['physical_geometry_validated']);self.assertFalse(m['scientific_success']);self.assertFalse(m['source_pixels_or_CAD_used']);self.assertEqual(m['validated_runnable_whole_paper_tasks'],0)
  s=read('states.json');self.assertEqual(len(s['scene_preview_states']),11);self.assertTrue(s['safe_close_review_accessible_from_every_preview_state'])
if __name__=='__main__':unittest.main()
