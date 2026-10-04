import unittest,json,struct,hashlib,math,zlib
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def J(n):return json.loads((P/n).read_text())
def glb(n):
 b=(P/n).read_bytes();assert b[:4]==b'glTF';assert struct.unpack_from('<I',b,4)[0]==2;assert struct.unpack_from('<I',b,8)[0]==len(b);l,t=struct.unpack_from('<II',b,12);assert t==0x4e4f534a;return json.loads(b[20:20+l])
class PackageTests(unittest.TestCase):
 def test_source_doi(self):self.assertEqual(J('asset_metadata.json')['source_doi'],'10.1038/s41467-022-29484-1')
 def test_groups(self):
  a=J('asset_inventory.json')['assets'];p=J('task_binding_snapshot.json')['scene_assets'];self.assertEqual(len(a),11);self.assertEqual({x['asset_id'] for x in a},{x['asset_id'] for x in p})
 def test_anchors_exact(self):
  a={(x['asset_id'],x['anchor_id']) for x in J('affordances.json')['anchors']};p={(x['asset_id'],y) for x in J('task_binding_snapshot.json')['scene_assets'] for y in x['required_anchor_ids']};self.assertEqual(a,p);self.assertEqual(len(a),53)
 def test_operations_exact(self):
  a=J('operation_bindings.json')['bindings'];p={y for x in J('task_binding_snapshot.json')['scene_assets'] for y in x['bind_operation_ids']};self.assertEqual({x['operation_id'] for x in a},p);self.assertEqual(len(a),60)
 def test_anchors_targets_exist(self):
  parts={p['part_id'] for a in J('asset_inventory.json')['assets'] for p in a['parts']}
  for a in J('affordances.json')['anchors']:self.assertIn(a['target_object'],parts)
 def test_anchor_coordinates_finite(self):
  for a in J('affordances.json')['anchors']:self.assertTrue(all(math.isfinite(x) for x in a['translation_m']));self.assertEqual(len(a['translation_m']),3);self.assertIsNone(a['physical_qualified_transform'])
 def test_binding_disabled(self):
  for a in J('operation_bindings.json')['bindings']:self.assertFalse(a['physical_execution']);self.assertFalse(a['energy_enabled']);self.assertFalse(a['source_geometry_validated']);self.assertFalse(a['request_is_observation'])
 def test_materials_are_appearance(self):
  for m in J('materials/materials.json'):self.assertTrue(m['appearance_only']);self.assertFalse(m['measured_material_properties'])
 def test_no_reused_asset_credit(self):self.assertEqual(J('asset_inventory.json')['imported_mesh_count'],0);self.assertEqual(J('asset_inventory.json')['reused_asset_credit'],0)
 def test_no_source_physics_claim(self):
  m=J('asset_metadata.json')
  for k in ['source_geometry_reconstruction','source_mode_reconstruction','physical_qualification','hardware_io','energy_enabled','numerical_solver','contact_or_force_simulation']:self.assertFalse(m[k])
 def test_three_proxy_snapshots(self):
  k=J('review/kinematic_proxy.json');self.assertEqual(len(k['snapshots']),3)
  for s in k['snapshots']:
   self.assertIsNone(s['source_mode']);self.assertFalse(s['locking_or_contact']);self.assertFalse(s['is_source_theta'])
   for a,b in zip(s['centerline_vertices_m'],s['centerline_vertices_m'][1:]):self.assertAlmostEqual(math.dist(a,b),s['centerline_link_length_m'],places=7)
 def test_source_conflicts_held(self):
  c=J('review/source_comparison.json')['source_conflicts'];self.assertEqual(len(c),10);self.assertTrue(all(x['status']=='HOLD' for x in c))
 def test_display_scale(self):self.assertEqual(J('asset_metadata.json')['display_scene']['uniform_scale'],8);self.assertTrue(J('asset_metadata.json')['display_scene']['no_thickness_exaggeration'])
 def test_two_glbs_valid(self):
  for n in ['geometry/lockable_origami_lab.glb','geometry/paperboard_reference_display.glb']:
   g=glb(n);self.assertEqual(g['asset']['version'],'2.0');self.assertGreater(len(g['meshes']),5);self.assertNotIn('animations',g);self.assertNotIn('images',g)
 def test_glb_group_anchor_coverage(self):
  names={n.get('name') for n in glb('geometry/lockable_origami_lab.glb')['nodes']}
  for a in J('asset_inventory.json')['assets']:self.assertIn(a['asset_id'],names)
  for a in J('affordances.json')['anchors']:self.assertIn(a['scene_object'],names)
 def test_glb_no_external_uri(self):
  for n in ['geometry/lockable_origami_lab.glb','geometry/paperboard_reference_display.glb']:
   g=glb(n)
   for b in g.get('buffers',[]):self.assertNotIn('uri',b)
 def test_actual_render_receipts(self):
  r=J('review/render_receipt.json');self.assertEqual(r['engine'],'CYCLES');self.assertEqual(r['device'],'CPU');self.assertEqual(len(r['views']),3);self.assertFalse(r['source_pixels_used'])
  for v in r['views']:self.assertTrue(v['actual_render']);self.assertEqual(v['sha256'],hashlib.sha256((P/v['file']).read_bytes()).hexdigest())
 def test_png_integrity_and_metadata(self):
  for n in ['overview','handling','dimensions']:
   b=(P/'evidence'/f'{n}.png').read_bytes();self.assertEqual(b[:8],b'\x89PNG\r\n\x1a\n');pos=8;types=[]
   while pos<len(b):
    l=struct.unpack_from('>I',b,pos)[0];t=b[pos+4:pos+8];d=b[pos+8:pos+8+l];crc=struct.unpack_from('>I',b,pos+8+l)[0];self.assertEqual(crc,zlib.crc32(t+d)&0xffffffff);types.append(t);pos+=l+12
   self.assertEqual(pos,len(b));self.assertEqual(types[-1],b'IEND');self.assertFalse(set(types)&{b'tEXt',b'zTXt',b'iTXt'})
 def test_native_reopen_passed(self):self.assertEqual(J('review/blend_validation.json')['status'],'PASS');self.assertGreater(J('review/blend_validation.json')['checks'],200)
 def test_actual_reimports_passed(self):self.assertEqual(J('review/glb_import_validation.json')['status'],'PASS');self.assertTrue(J('review/glb_import_validation.json')['actual_reimports'])
 def test_public_allowlist(self):
  a=J('EXPORT_ALLOWLIST.json');self.assertEqual(len(a['files']),36);self.assertEqual(len(set(a['files'])),36)
  for n in a['files']:
   self.assertFalse(Path(n).is_absolute());self.assertNotIn('..',Path(n).parts);self.assertTrue((P/n).is_file());self.assertFalse((P/n).is_symlink());self.assertNotIn(Path(n).suffix,['.zip','.log','.pdf','.html','.blend1','.pyc'])
 def test_public_files_no_private_path(self):
  prefixes=[b'/'+b'workspace/',b'/'+b'home/agent/',b'/'+b'root/',b'/'+b'tmp/']
  for n in J('EXPORT_ALLOWLIST.json')['files']:
   b=(P/n).read_bytes()
   for p in prefixes:
    for q in [p,p.decode().encode('utf-16-le'),p.decode().encode('utf-16-be')]:self.assertNotIn(q,b,n)
if __name__=='__main__':unittest.main()
