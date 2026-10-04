import unittest,json,struct,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def get(f):return json.loads((P/f).read_text())
class Package(unittest.TestCase):
 def test_full_operations(self):
  p=get('task_binding_snapshot.json');b=get('operation_bindings.json');expected={op for a in p['scene_assets'] for op in a['bind_operation_ids']};actual=[o['operation_id'] for o in b['operations']];self.assertEqual(set(actual),expected);self.assertEqual(len(actual),len(set(actual)));self.assertTrue(all(not o['physical_execution'] for o in b['operations']))
 def test_exact_assets(self):self.assertEqual({a['asset_id'] for a in get('asset_inventory.json')['assets']},{a['asset_id'] for a in get('task_binding_snapshot.json')['scene_assets']})
 def test_anchors(self):
  aff=get('affordances.json')['anchors'];names=[a['scene_object'] for a in aff];self.assertEqual(len(names),len(set(names)))
  for a in get('operation_bindings.json')['canonical_anchors']:self.assertIn(a['scene_object'],names)
 def test_all_targets(self):
  parts={p['part_id'] for a in get('asset_inventory.json')['assets'] for p in a['parts']}
  for a in get('affordances.json')['anchors']:self.assertIn(a['target_object'],parts)
 def test_no_physical_claims(self):
  m=get('asset_metadata.json')['readiness']
  for x in ['physical_execution','device_io','mechanics_physics','optical_physics','deformation_prediction','collision_validated','physical_geometry_validated','source_conflicts_resolved']:self.assertFalse(m[x])
 def test_source_boundaries(self):
  m=get('asset_metadata.json');self.assertIsNone(m['frame_convention']['source_to_scene_axis_map']);self.assertTrue(all(not c['resolved'] for c in m['source_conflicts']));self.assertFalse(m['authored_geometry']['known_source_cad']);self.assertFalse(m['provenance']['source_reference']['source_code_reused'])
 def test_reuse(self):
  r=get('geometry/reused_carrier_components.json');self.assertEqual(len(r['parts']),15);self.assertEqual(r['new_unique_asset_credit'],0)
 def test_glbs_self_contained(self):
  for name in ['actuator_metrology_lab.glb','actuator_measurement_display.glb']:
   b=(P/'geometry'/name).read_bytes();magic,v,n=struct.unpack('<4sII',b[:12]);self.assertEqual((magic,v,n),(b'glTF',2,len(b)));ln,typ=struct.unpack('<II',b[12:20]);self.assertEqual(typ,0x4E4F534A);j=json.loads(b[20:20+ln]);self.assertTrue(all('uri' not in q for q in j.get('buffers',[])));self.assertFalse(j.get('images'));self.assertFalse(j.get('animations'))
 def test_renders(self):
  r=get('review/render_receipt.json');self.assertEqual({v['id'] for v in r['views']},{'overview','sample_handling','measurement'});self.assertEqual(r['device'],'CPU');self.assertFalse(r['source_pixels_used'])
  for v in r['views']:
   b=(P/v['file']).read_bytes();self.assertEqual(b[:8],b'\x89PNG\r\n\x1a\n');self.assertEqual(struct.unpack('>II',b[16:24]),(1600,1100));self.assertEqual(hashlib.sha256(b).hexdigest(),v['sha256'])
if __name__=='__main__':unittest.main()
