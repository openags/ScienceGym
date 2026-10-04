import unittest,json,struct,hashlib,zipfile
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def get(f):return json.loads((P/f).read_text())
class Package(unittest.TestCase):
 def test_full_operations(self):
  p=get('task_binding_snapshot.json');b=get('operation_bindings.json');expected={op for a in p['scene_assets'] for op in a['bind_operation_ids']};actual=[o['operation_id'] for o in b['operations']];self.assertEqual(set(actual),expected);self.assertEqual(len(actual),len(set(actual)));self.assertEqual(len(actual),48);self.assertTrue(all(not o['physical_execution'] and not o['energy_enabled'] and o['hardware_adapter'] is None for o in b['operations']))
 def test_exact_assets(self):self.assertEqual({a['asset_id'] for a in get('asset_inventory.json')['assets']},{a['asset_id'] for a in get('task_binding_snapshot.json')['scene_assets']});self.assertEqual(len(get('asset_inventory.json')['assets']),11)
 def test_anchors(self):
  aff=get('affordances.json')['anchors'];names=[a['scene_object'] for a in aff];self.assertEqual(len(names),len(set(names)));self.assertEqual(len(names),43)
  for a in get('operation_bindings.json')['canonical_anchors']:self.assertIn(a['scene_object'],names)
 def test_targets(self):
  parts={p['part_id'] for a in get('asset_inventory.json')['assets'] for p in a['parts']}
  for a in get('affordances.json')['anchors']:self.assertIn(a['target_object'],parts);self.assertIsNone(a['physical_qualified_transform']);self.assertFalse(a['physical_execution'])
 def test_no_physical_claims(self):
  r=get('asset_metadata.json')['readiness']
  for k,v in r.items():
   if k.endswith('_enabled') or k in ['physical_execution','device_io','physics','collision_validated','physical_geometry_validated','whole_paper_complete']:self.assertFalse(v)
  self.assertIsNone(r['scientific_outputs'])
 def test_source_boundaries(self):
  m=get('asset_metadata.json');self.assertIsNone(m['frame_convention']['source_to_scene_axis_map']);self.assertFalse(m['authored_geometry']['known_source_cad']);self.assertFalse(m['provenance']['source_reference']['source_code_reused']);self.assertFalse(m['provenance']['source_reference']['source_art_redistributed']);self.assertIn('CC BY-NC-ND',m['provenance']['source_reference']['license']);self.assertFalse(m['display_separation']['tetrakaidecahedron_modelled'])
 def test_native_display_distinction(self):
  d=get('asset_metadata.json')['display_separation'];self.assertEqual(d['native_cell_m'],60e-6);self.assertEqual(d['display_cell_m'],.06);self.assertEqual(d['reference_scale_factor'],1000);self.assertAlmostEqual(d['native_fiber_radius_m']*1000,d['display_fiber_radius_m'])
 def test_zero_reuse_credit(self):
  i=get('asset_inventory.json');self.assertEqual(i['reused_mesh_count'],0);self.assertEqual(i['reused_new_unique_asset_credit'],0);self.assertIsNone(i['unique_asset_count'])
 def test_glbs_self_contained(self):
  for name in ['woven_material_lab.glb','woven_reference_display.glb']:
   b=(P/'geometry'/name).read_bytes();magic,v,n=struct.unpack('<4sII',b[:12]);self.assertEqual((magic,v,n),(b'glTF',2,len(b)));ln,typ=struct.unpack('<II',b[12:20]);self.assertEqual(typ,0x4E4F534A);j=json.loads(b[20:20+ln]);self.assertTrue(all('uri' not in q for q in j.get('buffers',[])));self.assertFalse(j.get('images'));self.assertFalse(j.get('animations'))
 def test_renders(self):
  r=get('review/render_receipt.json');self.assertEqual({v['id'] for v in r['views']},{'overview','package_handling','measurement'});self.assertEqual(r['device'],'CPU');self.assertFalse(r['source_pixels_used'])
  for v in r['views']:
   b=(P/v['file']).read_bytes();self.assertEqual(b[:8],b'\x89PNG\r\n\x1a\n');self.assertEqual(struct.unpack('>II',b[16:24]),(1600,1100));self.assertEqual(hashlib.sha256(b).hexdigest(),v['sha256']);self.assertTrue(v['actual_render'])
 def test_native_receipt(self):self.assertEqual(hashlib.sha256((P/'geometry/woven_material_lab.blend').read_bytes()).hexdigest(),get('review/blend_validation.json')['blend_sha256'])
 def test_glb_receipt(self):
  for r in get('review/glb_import_validation.json')['files']:self.assertEqual(hashlib.sha256((P/r['file']).read_bytes()).hexdigest(),r['sha256'])
 def test_allowlist(self):
  a=get('EXPORT_ALLOWLIST.json');self.assertEqual(a['total_files'],len(a['files']));self.assertEqual(len(a['files']),len(set(a['files'])));self.assertFalse(a['source_assets_included'])
  for n in a['files']:self.assertFalse(Path(n).is_absolute());self.assertNotIn('..',Path(n).parts);self.assertNotIn(Path(n).suffix.lower(),['.zip','.pdf','.blend1','.pyc','.log','.html'])
 def test_public_binary_metadata(self):
  files=['geometry/woven_material_lab.blend','geometry/woven_material_lab.glb','geometry/woven_reference_display.glb','evidence/overview.png','evidence/package_handling.png','evidence/measurement.png']
  for n in files:
   data=(P/n).read_bytes()
   for part in ['workspace','home','tmp','root']:self.assertNotIn(('/'+part+'/').encode(),data)
   if n.endswith('.png'):
    offset=8
    while offset<len(data):
     size=struct.unpack('>I',data[offset:offset+4])[0];self.assertNotIn(data[offset+4:offset+8],[b'tEXt',b'zTXt',b'iTXt']);offset+=size+12
if __name__=='__main__':unittest.main()
