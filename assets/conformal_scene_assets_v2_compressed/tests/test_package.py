import unittest,json,struct,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
class Package(unittest.TestCase):
 def test_counts(self):
  c=json.loads((P/'operation_binding_contract.json').read_text());self.assertEqual(len(c['roots']),12);self.assertEqual(len(c['operations']),16);self.assertEqual(len(c['branch_ids']),9)
 def test_selectors(self):
  inv=json.loads((P/'asset_inventory.json').read_text());names={o['name']:a['id'] for a in inv['assets'] for o in a['objects']};c=json.loads((P/'operation_binding_contract.json').read_text())
  for r in c['operations']:
   for role in ['primary','control']:
    self.assertEqual(names[r[role+'_target']],r['primary_asset_id']);self.assertEqual(names[r[role+'_anchor']],r['primary_asset_id'])
 def test_required_semantics(self):
  req=json.loads((P/'requirements_snapshot.json').read_text());aff={a['name'] for a in json.loads((P/'affordances.json').read_text())['anchors']}
  for a in req['assets']:
   for role in a['required_semantic_anchors']:self.assertIn('ANCHOR.'+a['id']+'.'+role,aff)
 def test_glb_portability(self):
  b=(P/'geometry/conformal_lab.glb').read_bytes();magic,version,length=struct.unpack('<4sII',b[:12]);self.assertEqual(magic,b'glTF');self.assertEqual(length,len(b));self.assertEqual(version,2);n,t=struct.unpack('<II',b[12:20]);g=json.loads(b[20:20+n]);self.assertFalse(g.get('images'));self.assertFalse(g.get('animations'));self.assertFalse(g.get('cameras'));self.assertTrue(all('uri' not in x for x in g.get('buffers',[])))
 def test_source_limits(self):
  meta=json.loads((P/'asset_metadata.json').read_text());self.assertFalse(meta['physical_execution_enabled']);self.assertEqual(meta['completed_conversion_increment'],0);self.assertIn('unread',meta['source_review_status']);self.assertFalse(json.loads((P/'specimen_geometry.json').read_text())['source_mesh_or_code_used'])
 def test_forbidden_content(self):
  for p in list(P.glob('*.json'))+list((P/'LICENSES').glob('*.md')):
   if p.name in {'library_delivery_result.json','library_delivery_receipt.json'}:continue
   s=p.read_text();self.assertNotIn(('/'+'workspace'+'/'),s);self.assertNotIn(('/'+'tmp'+'/'),s)
if __name__=='__main__':unittest.main()
