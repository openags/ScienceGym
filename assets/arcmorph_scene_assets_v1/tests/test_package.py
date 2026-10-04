"""Independent-of-Blender integrity and claims-boundary checks."""
import unittest,json,hashlib,struct
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def read(n):return json.loads((P/n).read_text())
class PackageTests(unittest.TestCase):
 def test_twelve_groups(self):
  inv=read('asset_inventory.json');self.assertEqual([a['asset_id'] for a in inv['assets']],[f'A{i:02d}' for i in range(1,13)]);self.assertEqual(inv['units'],'m');self.assertEqual(inv['imported_mesh_count'],0)
 def test_operation_bindings(self):
  b=read('operation_bindings.json')['operations'];a={x['anchor_id']:x for x in read('affordances.json')['anchors']};inv={p['scene_object']:p for r in read('asset_inventory.json')['assets'] for p in r['parts']}
  self.assertEqual([o['operation_id'] for o in b],[f'R{i:02d}' for i in range(31)])
  for o in b:
   for role in ['primary','control']:
    n=o[role+'_anchor'];self.assertIn(n,a);self.assertEqual(a[n]['target_object'],o[role+'_target']);self.assertIn(o[role+'_target'],inv)
    for x,y in zip(inv[n]['translation_m'],a[n]['translation_m']):self.assertAlmostEqual(x,y,6)
 def test_rigid_demo_separate(self):
  b={o['operation_id']:o for o in read('operation_bindings.json')['operations']}
  for op in ['R26','R27']:self.assertEqual(b[op]['primary_target'],'qual.rigid_demo_support')
  for op in ['R20','R21','R22']:self.assertEqual(b[op]['primary_target'],'qual.corner.base')
 def test_twenty_original_states(self):
  t=read('specimen_topology.json');self.assertFalse(t['physical_folding_validated']);self.assertFalse(t['source_geometry_used']);self.assertEqual(len(t['static_variants']),20)
  for v in t['static_variants']:
   self.assertEqual(v['panel_count'],24);self.assertEqual(len(v['creases']),38);self.assertFalse(v['qualified']);self.assertTrue(v['illustration_not_physical_fold']);self.assertEqual(len(v['panel_surface_extent_m']),3)
   for c in v['creases']:self.assertEqual(len(c['adjacent_panel_ids']),2);self.assertIsNone(c['fold_order']);self.assertIsNone(c['fold_motion_limit']);self.assertIsNone(c['mountain_valley'])
 def test_dims_hold(self):
  m=read('asset_metadata.json');self.assertEqual(m['dimensional_hold']['conflict_id'],'C01');self.assertIsNone(m['dimensional_hold']['resolution']);self.assertFalse(m['dimensional_hold']['fabrication_from_source_dimensions_allowed']);self.assertEqual(m['source_known_dimensions']['PP_length_methods_mm'],383.63);self.assertEqual(m['source_known_dimensions']['PP_length_figure_mm'],383.65);self.assertEqual(m['family_aliases'],{'PP1':'PP'});self.assertEqual(m['task_id'],'arcmorph_operations_v2')
 def test_no_physical_contacts(self):
  a=read('affordances.json');self.assertGreater(len(a['candidate_contacts']),20)
  for x in a['anchors']:self.assertIsNone(x['qualified_pose']);self.assertFalse(x['physical_execution_enabled'])
  for x in a['candidate_contacts']:self.assertFalse(x['physical_grasp_enabled']);self.assertIsNone(x['qualified_pose'])
  for x in a['collision_proxies']:self.assertFalse(x['collision_enabled']);self.assertFalse(x['fit_qualified'])
 def test_three_real_renders(self):
  r=read('review/render_receipt.json');self.assertEqual(r['device'],'CPU');self.assertEqual(r['renderer'],'Blender Cycles');self.assertEqual(len(r['images']),3)
  for v in r['images']:
   raw=(P/v['path']).read_bytes();self.assertTrue(raw.startswith(b'\x89PNG\r\n\x1a\n'));self.assertEqual(list(struct.unpack('>II',raw[16:24])),[1920,1280]);self.assertEqual(hashlib.sha256(raw).hexdigest(),v['sha256'])
   pos=8
   while pos<len(raw):
    n=struct.unpack_from('>I',raw,pos)[0];self.assertNotIn(raw[pos+4:pos+8],{b'tEXt',b'zTXt',b'iTXt'});pos+=n+12
 def test_native_and_glb_signature(self):
  self.assertTrue((P/'geometry/arcmorph_lab.blend').read_bytes().startswith(b'BLENDER'))
  data=(P/'geometry/arcmorph_lab.glb').read_bytes();magic,version,length=struct.unpack_from('<4sII',data);self.assertEqual((magic,version,length),(b'glTF',2,len(data)))
 def test_portable_no_external_assets(self):
  data=(P/'geometry/arcmorph_lab.glb').read_bytes();n,kind=struct.unpack_from('<II',data,12);self.assertEqual(kind,0x4e4f534a);j=json.loads(data[20:20+n]);self.assertFalse(j.get('images'));self.assertTrue(all('uri' not in x for x in j.get('buffers',[])));self.assertEqual(len([n for n in j['nodes'] if n.get('name','').startswith('ASSET.')]),12)
 def test_inventory_names_unique(self):
  names=[p['scene_object'] for r in read('asset_inventory.json')['assets'] for p in r['parts']];self.assertEqual(len(names),len(set(names)))
if __name__=='__main__':unittest.main()
