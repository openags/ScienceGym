"""Authored static consistency checks; no physical or scientific assertions."""
import unittest, json, hashlib, struct
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def read(n):return json.loads((P/n).read_text())
class PackageTests(unittest.TestCase):
    def test_counts_ids_and_disabled_physics(self):
        m=read('asset_metadata.json');self.assertEqual((m['groups'],m['stations'],m['branches'],m['proposed_operations'],m['operation_anchor_count']),(13,5,8,22,44))
        for k in ['physical_geometry_validated','physical_execution_enabled','scientific_success','source_pixels_or_CAD_used','raw_data_or_author_code_read']:self.assertIs(m[k],False)
    def test_bindings_and_roots_match(self):
        c=read('operation_binding_contract.json');b=read('operation_bindings.json');a=read('affordances.json');inv=read('asset_inventory.json')
        self.assertEqual(c['operations'],b['operations']);self.assertEqual(set(c['roots']),{f'A{i:02}' for i in range(1,14)})
        self.assertEqual([o['operation_id'] for o in b['operations']],[f'R{i:02}' for i in range(1,23)])
        by={p['scene_object']:(v['asset_id'],p) for v in inv['assets'] for p in v['parts']};anchors={v['anchor_id']:v for v in a['anchors']};self.assertEqual(len(anchors),44)
        for op in b['operations']:
            self.assertIs(op['physical_execution_enabled'],False);self.assertIsNone(op['qualified_pose']);self.assertIn(op['primary_asset_id'],op['asset_ids'])
            for role in ['primary','control']:
                target=op[role+'_target'];anchor=anchors[op[role+'_anchor']]
                self.assertEqual(by[target][0],op['primary_asset_id']);self.assertEqual(anchor['target_object'],target);self.assertEqual(anchor['asset_id'],op['primary_asset_id'])
                for x,y in zip(anchor['translation_m'],by[target][1]['translation_m']):self.assertAlmostEqual(x,y,places=6)
    def test_state_and_station_contract(self):
        b=read('operation_bindings.json');s=read('states.json');inv=read('asset_inventory.json');objects={p['scene_object'] for v in inv['assets'] for p in v['parts']}
        self.assertEqual({o['id']:o['asset_ids'] for o in s['operations']},{o['operation_id']:o['asset_ids'] for o in b['operations']})
        stations=read('station_layout.json')['stations'];self.assertEqual({s['station_id'] for s in stations},{f'S{i:02}' for i in range(1,6)})
        for station in stations:self.assertIn(station['scene_label'],objects)
        self.assertEqual(s['initial_state']['optical_dock'],'empty');self.assertFalse(s['scientific_success'])
    def test_13_requirement_roles(self):
        a=read('assembly_contract.json')['assets'];r=read('requirements_snapshot.json')['assets'];self.assertEqual({v['asset_id'] for v in a},{v['id'] for v in r})
        self.assertEqual(len(read('branches_snapshot.json')['branches']),8)
    def test_sample_dimension_boundary(self):
        s=read('specimen_geometry.json');self.assertEqual(len(s['specimens']),5);si=next(x for x in s['specimens'] if x['id']=='SI-STAR')
        self.assertEqual(si['source_nominal_thickness_m'],.0002);self.assertIsNone(si['etch_depth_m'])
        for x in s['specimens']:self.assertFalse(x['source_geometry_reproduced']);self.assertFalse(x['physical_geometry_validated'])
    def test_affordances_disabled(self):
        a=read('affordances.json')
        self.assertTrue(a['candidate_contacts']);self.assertEqual(len(a['collision_proxies']),13)
        self.assertTrue(all(not x['physical_grasp_enabled'] and x['qualified_pose'] is None for x in a['candidate_contacts']))
        self.assertTrue(all(not x['collision_enabled'] and not x['fit_qualified'] for x in a['collision_proxies']))
    def test_three_nonempty_cpu_previews(self):
        r=read('review/render_receipt.json');self.assertEqual(r['device'],'CPU');self.assertEqual(r['renderer'],'Blender Cycles');self.assertEqual(len(r['images']),3)
        for image in r['images']:
            data=(P/image['path']).read_bytes();self.assertGreater(len(data),100000);self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n');self.assertEqual(struct.unpack('>II',data[16:24]),(1800,1200));self.assertEqual(hashlib.sha256(data).hexdigest(),image['sha256'])
    def test_glb_single_selfcontained_scene(self):
        data=(P/'geometry/midinfrared_lab.glb').read_bytes();magic,version,size=struct.unpack_from('<4sII',data);self.assertEqual((magic,version,size),(b'glTF',2,len(data)))
        n,kind=struct.unpack_from('<I4s',data,12);self.assertEqual(kind,b'JSON');d=json.loads(data[20:20+n]);self.assertEqual(len(d['scenes']),1);self.assertEqual(d.get('scene',0),0)
        self.assertFalse(d.get('images'));self.assertFalse(d.get('animations'));self.assertFalse(d.get('cameras'));self.assertTrue(all('uri' not in x for x in d['buffers']))
    def test_r07_r20_key_memberships(self):
        b={x['operation_id']:x for x in read('operation_bindings.json')['operations']}
        self.assertEqual(b['R07']['primary_asset_id'],'A13');self.assertIn('A07',b['R20']['asset_ids']);self.assertIn('branch-specific',b['R20']['anchor_scope'])
if __name__=='__main__':unittest.main()
