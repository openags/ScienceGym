import unittest,json,hashlib,struct,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
load=lambda f:json.loads((P/f).read_text())
class PackageTests(unittest.TestCase):
 def test_identity(self):
  self.assertEqual(load('asset_metadata.json')['task_family'],'transistor_operations_v2')
 def test_all_operations_once(self):
  b=load('operation_bindings.json')['operations'];p=load('task_binding_snapshot.json');self.assertEqual(len(b),44);self.assertEqual({x['operation_id'] for x in b},{x['id'] for x in p['operations']})
 def test_bindings_resolve(self):
  names={x['asset_id'] for x in load('asset_inventory.json')['assets']};self.assertTrue(all(x['scene_object'] in names and not x['physical_execution'] for x in load('operation_bindings.json')['operations']))
 def test_six_groups_not_unique_claims(self):
  d=load('asset_inventory.json');self.assertEqual(d['main_scene_group_count'],6);self.assertIsNone(d['unique_asset_count'])
 def test_anchor_targets(self):
  d=load('asset_inventory.json');parts={p['part_id'] for a in d['assets'] for p in a['parts']};a=load('affordances.json')['anchors'];self.assertEqual(len(a),30);self.assertTrue(all(x['target_object'] in parts for x in a));self.assertEqual(len({x['scene_object'] for x in a}),len(a))
 def test_no_collision_claim(self):
  d=load('affordances.json');self.assertFalse(d['collision_meshes_supplied']);self.assertFalse(d['qualified_robot_poses'])
 def test_native_layer_accounting(self):
  d=load('task_binding_snapshot.json')['layer_contract'];self.assertEqual(d['layer_count'],72);self.assertEqual(len(d['layers']),72);self.assertEqual(d['active_layer_count'],60);self.assertEqual(d['interstack_buffer_count'],9);self.assertEqual(d['final_cap_count'],1)
 def test_native_reference_thickness(self):
  d=load('task_binding_snapshot.json')['layer_contract'];self.assertAlmostEqual(sum(x['source_thickness']*(1e-6 if x['unit']=='um' else 1e-9) for x in d['layers']),.0005287,places=12)
 def test_buffers_no_execution_default(self):
  ls=load('task_binding_snapshot.json')['layer_contract']['layers'];bb=[x for x in ls if x['role'] in ['interstack_buffer','final_cap']];self.assertEqual(len(bb),10);self.assertTrue(all(x['execution_thickness_default'] is None for x in bb))
 def test_native_separate_display(self):
  m=load('asset_metadata.json');self.assertFalse(m['display_separation']['native_reference_scene_exported_to_glb']);self.assertIsNone(m['display_separation']['uniform_scale_factor']);self.assertEqual(m['display_separation']['display_layer_thickness_m'],.003)
 def test_ten_unresolved_conflicts(self):
  c=load('asset_metadata.json')['source_conflicts'];self.assertEqual({x['id'] for x in c},{'C%02d'%i for i in range(1,11)});self.assertTrue(all(not x['resolved'] and x['qualification_gate'] for x in c))
 def test_conflicts_exact_task_snapshot(self):
  self.assertEqual(load('asset_metadata.json')['source_conflicts'],load('task_binding_snapshot.json')['source_conflicts']['conflicts'])
 def test_netlists_distinct(self):
  n=load('task_binding_snapshot.json')['netlist_contracts']['netlists'];o=n[0]['source_visual_interpretation'];i=n[2]['source_visual_interpretation'];self.assertEqual(o['load_left_gate_BG'],'VDD');self.assertEqual(i['load_BG'],'VOUT');self.assertEqual(o['driver_TG'],'VIN');self.assertEqual(i['driver_TG'],'VTG1')
 def test_station_ids_and_targets(self):
  b=load('operation_bindings.json');stations=b['station_bindings'];self.assertEqual({x['station_id'] for x in stations},{'fabrication','packaging','electrical','thermal_electrical','storage_electrical','metrology'});parts={p['part_id'] for a in load('asset_inventory.json')['assets'] for p in a['parts']};self.assertTrue(all(x['scene_object'] in parts for x in stations))
 def test_cross_station_lifecycle(self):
  b=load('operation_bindings.json')['cross_station_lifecycle_boundaries'];self.assertEqual(set(b),{'HIGHK','THERMAL','LONG_TERM','STRUCTURAL'});self.assertEqual(b['HIGHK']['sequence'].count('A_PROBE_READOUT'),2)
 def test_main_original_parts(self):
  a=load('asset_inventory.json')['assets'];self.assertGreater(sum(len(x['parts']) for x in a),100)
 def test_exact_reuse_count(self):
  r=load('geometry/reused_carrier_components.json');a=load('asset_inventory.json')['assets'];p=[p for a in a for p in a['parts'] if p['geometry_basis']=='reused_original_afm_mesh'];self.assertEqual(len(p),15);self.assertEqual({x['source_part_id'] for x in p},{x['source_part_id'] for x in r['parts']})
 def test_zero_new_reuse_credit(self):
  m=load('asset_metadata.json')['provenance'];self.assertEqual(m['reused_new_unique_asset_credit'],0);self.assertEqual(len(m['reused_asset_families']),2)
 def test_no_scientific_physics(self):
  r=load('asset_metadata.json')['readiness'];self.assertFalse(r['physical_execution']);self.assertFalse(r['device_io']);self.assertFalse(r['electrical_physics']);self.assertFalse(r['thermal_physics'])
 def test_png_evidence(self):
  for name in ['overview','sample_handling','equipment_closeup']:
   b=(P/'evidence'/f'{name}.png').read_bytes();self.assertEqual(b[:8],b'\x89PNG\r\n\x1a\n');self.assertEqual(struct.unpack('>II',b[16:24]),(1600,1100))
 def test_actual_render_receipts(self):
  r=load('review/render_receipt.json');self.assertEqual(r['device'],'CPU');self.assertEqual(len(r['views']),3)
  for v in r['views']:self.assertTrue(v['actual_render']);self.assertEqual(hashlib.sha256((P/v['file']).read_bytes()).hexdigest(),v['sha256'])
 def test_glb_self_contained(self):
  for f in ['transistor_operations_lab.glb','transistor_layer_ledger_display.glb']:
   b=(P/'geometry'/f).read_bytes();self.assertEqual(b[:4],b'glTF');l,t=struct.unpack_from('<II',b,12);d=json.loads(b[20:20+l]);self.assertFalse(any('uri' in x for x in d.get('buffers',[])));self.assertFalse(d.get('images'));self.assertFalse(d.get('textures'))
 def test_blend_and_glb_budget(self):
  self.assertLess(sum(p.stat().st_size for p in (P/'geometry').iterdir() if p.suffix in ['.blend','.glb']),18_000_000)
 def test_public_allowlist(self):
  a=load('EXPORT_ALLOWLIST.json')['files'];self.assertEqual(len(a),len(set(a)));self.assertTrue(all((P/f).is_file() for f in a));self.assertTrue(all(not Path(f).is_absolute() and '..' not in Path(f).parts for f in a))
 def test_public_exclusions(self):
  for f in load('EXPORT_ALLOWLIST.json')['files']:
   self.assertNotIn(Path(f).suffix.lower(),['.pdf','.html','.log','.pyc','.blend1','.zip']);self.assertNotIn('__pycache__',f);self.assertNotIn('private',f.lower())
 def test_license_notices(self):
  self.assertTrue((P/'LICENSES/Apache-2.0.txt').is_file());self.assertTrue((P/'LICENSES/Blender-font-notice.txt').is_file());self.assertIn('original', (P/'LICENSES/ATTRIBUTION.md').read_text().lower())
if __name__=='__main__':unittest.main()
