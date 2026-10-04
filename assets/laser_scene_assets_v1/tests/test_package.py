import unittest,json,struct,hashlib,zipfile
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def get(f):return json.loads((P/f).read_text())
class Package(unittest.TestCase):
 def test_full_operations(self):
  p=get('task_binding_snapshot.json');b=get('operation_bindings.json');expected={op for a in p['scene_assets'] for op in a['bind_operation_ids']};actual=[o['operation_id'] for o in b['operations']];self.assertEqual(set(actual),expected);self.assertEqual(len(actual),len(set(actual)));self.assertEqual(len(actual),44);self.assertTrue(all(not o['physical_execution'] and not o['energy_enabled'] and o['hardware_adapter'] is None for o in b['operations']))
 def test_exact_assets(self):self.assertEqual({a['asset_id'] for a in get('asset_inventory.json')['assets']},{a['asset_id'] for a in get('task_binding_snapshot.json')['scene_assets']});self.assertEqual(len(get('asset_inventory.json')['assets']),10)
 def test_anchors(self):
  aff=get('affordances.json')['anchors'];names=[a['scene_object'] for a in aff];self.assertEqual(len(names),len(set(names)));self.assertEqual(len(get('operation_bindings.json')['canonical_anchors']),46)
  for a in get('operation_bindings.json')['canonical_anchors']:self.assertIn(a['scene_object'],names)
 def test_all_targets(self):
  parts={p['part_id'] for a in get('asset_inventory.json')['assets'] for p in a['parts']}
  for a in get('affordances.json')['anchors']:self.assertIn(a['target_object'],parts);self.assertIsNone(a['physical_qualified_transform']);self.assertFalse(a['physical_execution'])
 def test_no_physical_claims(self):
  r=get('asset_metadata.json')['readiness']
  for k in ['physical_execution','device_io','laser_energy_enabled','heater1_enabled','heater2_enabled','servo_control','optical_physics','thermal_physics','electronic_physics','collision_validated','physical_geometry_validated','whole_paper_complete']:self.assertFalse(r[k])
  self.assertIsNone(r['scientific_outputs'])
 def test_source_boundaries(self):
  m=get('asset_metadata.json');self.assertIsNone(m['frame_convention']['source_to_scene_axis_map']);self.assertFalse(m['authored_geometry']['known_source_cad']);self.assertFalse(m['provenance']['source_reference']['source_code_reused']);self.assertFalse(m['provenance']['source_reference']['source_art_redistributed'])
 def test_native_display_distinction(self):
  d=get('asset_metadata.json')['display_separation'];self.assertEqual(d['native_footprint_m'],[.00095,.00048]);self.assertEqual(d['display_footprint_m'],[.95,.48]);self.assertEqual(d['planar_footprint_scale_factor'],1000);self.assertFalse(d['die_thickness_modelled']);self.assertFalse(d['source_circuit_layout_modelled'])
 def test_reuse_zero_credit(self):
  r=get('geometry/reused_carrier_components.json');self.assertEqual(len(r['parts']),15);self.assertEqual(r['new_unique_asset_credit'],0);self.assertEqual(get('asset_inventory.json')['reused_new_unique_asset_credit'],0)
 def test_glbs_self_contained(self):
  for name in ['laser_control_lab.glb','laser_pic_display.glb']:
   b=(P/'geometry'/name).read_bytes();magic,v,n=struct.unpack('<4sII',b[:12]);self.assertEqual((magic,v,n),(b'glTF',2,len(b)));ln,typ=struct.unpack('<II',b[12:20]);self.assertEqual(typ,0x4E4F534A);j=json.loads(b[20:20+ln]);self.assertTrue(all('uri' not in q for q in j.get('buffers',[])));self.assertFalse(j.get('images'));self.assertFalse(j.get('animations'))
 def test_renders(self):
  r=get('review/render_receipt.json');self.assertEqual({v['id'] for v in r['views']},{'overview','package_handling','measurement'});self.assertEqual(r['device'],'CPU');self.assertFalse(r['source_pixels_used'])
  for v in r['views']:
   b=(P/v['file']).read_bytes();self.assertEqual(b[:8],b'\x89PNG\r\n\x1a\n');self.assertEqual(struct.unpack('>II',b[16:24]),(1600,1100));self.assertEqual(hashlib.sha256(b).hexdigest(),v['sha256']);self.assertTrue(v['actual_render'])
 def test_all_eighteen_source_roles(self):
  j=get('review/source_comparison.json');self.assertEqual({x for a in j['ten_group_to_eighteen_source_role_map'] for x in a['audit_role_ids']},{'A%02d'%i for i in range(1,19)});self.assertFalse(j['source_outcomes_drawn_or_emitted'])
 def test_allowlist(self):
  a=get('EXPORT_ALLOWLIST.json');self.assertEqual(a['total_files'],len(a['files']));self.assertEqual(len(a['files']),len(set(a['files'])));self.assertFalse(a['source_assets_included'])
  for n in a['files']:self.assertFalse(Path(n).is_absolute());self.assertNotIn('..',Path(n).parts);self.assertNotIn(Path(n).suffix.lower(),['.zip','.pdf','.blend1','.pyc','.log','.html'])
if __name__=='__main__':unittest.main()
