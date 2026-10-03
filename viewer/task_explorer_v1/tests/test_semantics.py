import os, unittest, json, pathlib, hashlib, collections, xml.etree.ElementTree as ET, re, importlib.util
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('builder',ROOT/'build.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
TASKS=pathlib.Path(os.environ['SCIENCEGYM_TASKS']) if 'SCIENCEGYM_TASKS'in os.environ else None

def decode(f,v):
 if isinstance(v,dict) and '$shared'in v:return decode(f,f['shared'][v['$shared']])
 if isinstance(v,dict):return {k:decode(f,x) for k,x in v.items()}
 if isinstance(v,list):return [decode(f,x) for x in v]
 return v

def get(key):
 f=json.loads((ROOT/'data'/f'{key}.json').read_text());return decode(f,f)
def ids(nodes):return [n['id'] for n,d in builder.walk(nodes) if n['type']=='op']

class BundleTests(unittest.TestCase):
 def test_thirteen_families(self):self.assertEqual(len(list((ROOT/'data').glob('*.json'))),13)
 def test_all_operation_references_resolve(self):
  for key in builder.ADAPTERS:
   f=get(key);mapping={o['id']:o for o in f['operations']};self.assertEqual(len(mapping),len(f['operations']))
   for r in f['routes']:
    for oid in ids(r['nodes']):self.assertIn(oid,mapping,(key,r['id'],oid))
 def test_pooled_values_are_lossless_shapes(self):
  for key in builder.ADAPTERS:
   f=get(key)
   for o in f['operations']:
    self.assertIsInstance(o['actions'],list)
    for field in ['pre','post','sources','objects','recovery','acceptance','unknowns','provenance']:self.assertIn(field,o)
    if o.get('action_macro'):self.assertIn(o['action_macro'],f['macros'])
 def test_compact_payloads(self):
  for path in (ROOT/'data').glob('*.json'):self.assertLess(path.stat().st_size,1500000 if path.stem=='perovskite' else 400000 if path.stem in ('prismatic','emvp','wavefront') else 200000,path.name)
 def test_js_payload_matches_json(self):
  for key in builder.ADAPTERS:
   js=(ROOT/'data'/f'{key}.js').read_text();payload=js.split('['+json.dumps(key)+']=',1)[1].rsplit(';',1)[0]
   self.assertEqual(json.loads(payload),json.loads((ROOT/'data'/f'{key}.json').read_text()))
 def test_all_svg_parse_and_inline_styles(self):
  for key in builder.ADAPTERS:
   tree=ET.parse(ROOT/'diagrams'/f'{key}.svg');texts=tree.findall('.//{http://www.w3.org/2000/svg}text');self.assertGreater(len(texts),10)
   for t in texts:self.assertIn('fill',t.attrib);self.assertIn('font-family',t.attrib)
 def test_release_manifest_inventory_and_checksums(self):
  manifest=json.loads((ROOT/'release_manifest.json').read_text())
  self.assertEqual(manifest['source_commit'],builder.COMMIT)
  entries=manifest['files'];self.assertEqual(len(entries),len({entry['path'] for entry in entries}))
  expected={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()
   and not any(part.startswith('.') or part=='__pycache__' for part in p.relative_to(ROOT).parts)
   and p.name not in {'release_manifest.json','ScienceGym-Task-Explorer.html'}
   and p.suffix in {'.md','.js','.json','.py','.html','.css','.svg'}}
  self.assertEqual({entry['path'] for entry in entries},expected)
  for entry in entries:
   payload=(ROOT/entry['path']).read_bytes()
   self.assertEqual(len(payload),entry['bytes'],entry['path'])
   self.assertEqual(hashlib.sha256(payload).hexdigest(),entry['sha256'],entry['path'])
 def test_local_assets_and_no_network_runtime(self):
  page=(ROOT/'index.html').read_text()
  for file in re.findall(r'(?:src|href)="([^"#]+)"',page):
   if not file.startswith('http'):self.assertTrue((ROOT/file).exists(),file)
  app=(ROOT/'app.js').read_text();self.assertNotRegex(app,r'\b(?:fetch|XMLHttpRequest|WebSocket|eval)\s*\(');self.assertNotIn('innerHTML',app)
 def test_microscopy_obligation_groups(self):
  f=get('microscopy');self.assertEqual(len(f['routes']),13)
  for r in f['routes'][6:]:self.assertEqual(r['nodes'][0]['type'],'obligations')
  for r in f['routes'][:6]:self.assertEqual(sum(n.get('type')=='obligations' for n in r['nodes'] if isinstance(n,dict)),1)
 def test_dispim_repeated_occurrences(self):
  r=get('dispim')['routes'][0];counts=collections.Counter(ids(r['nodes']));self.assertEqual(counts['P001'],2);self.assertEqual(counts['P004'],2)
 def test_acoustic_nested_loop_fidelity(self):
  f=get('acoustic');r=next(r for r in f['routes'] if r['id']=='WHOLE_PAPER_PRACTICAL');loops=[(n,d) for n,d in builder.walk(r['nodes']) if n['type']=='loop']
  self.assertGreater(len(loops),5);self.assertTrue(any(d>1 for n,d in loops));self.assertTrue(all('values'in n['meta'] and 'completion_rule'in n['meta'] for n,d in loops))
 @unittest.skipUnless(TASKS,'SCIENCEGYM_TASKS not set; source comparison not run')
 def test_source_routes_exact(self):
  for key,field in [('chiral','operation_sequence'),('fibre','full_operation_sequence'),('thermoelectric','full_operation_sequence'),('perovskite','full_operation_sequence')]:
   raw=json.loads((TASKS/(key+'_operations_v2')/'branches.json').read_text())
   for source,route in zip(raw['branches'],get(key)['routes']):self.assertEqual(source[field],ids(route['nodes']))
  raw=json.loads((TASKS/'dispim_operations_v2'/'BRANCHES.json').read_text())
  for source,route in zip(raw['route_templates'],get('dispim')['routes']):self.assertEqual(source['operation_sequence'],ids(route['nodes']))
 @unittest.skipUnless(TASKS,'SCIENCEGYM_TASKS not set; source comparison not run')
 def test_actions_states_and_recovery_exact(self):
  for key in ['chiral','fibre','thermoelectric','acoustic']:
   raw=json.loads((TASKS/(key+'_operations_v2')/'operations.json').read_text())
   for original,mapped in zip(raw['operations'],get(key)['operations']):
    for a,b in [('actions','actions'),('preconditions','pre'),('postconditions','post'),('recovery','recovery'),('target_asset_roles','objects')]:self.assertEqual(original[a],mapped[b],(key,original['id'],a))
 @unittest.skipUnless(TASKS,'SCIENCEGYM_TASKS not set; source comparison not run')
 def test_source_hashes(self):
  for key in builder.ADAPTERS:
   f=get(key)
   for name,record in f['source_files'].items():self.assertEqual(record['sha256'],hashlib.sha256((TASKS/builder.package_name(key)/name).read_bytes()).hexdigest())
 @unittest.skipUnless(TASKS,'SCIENCEGYM_TASKS not set; source comparison not run')
 def test_acoustic_rebuild_keeps_every_nested_value(self):
  expected=builder.adapt_acoustic(TASKS/'acoustic_operations_v2')
  actual=get('acoustic')
  for a,b in zip(expected['routes'],actual['routes']):self.assertEqual(a['nodes'],b['nodes'])
 @unittest.skipUnless(TASKS,'SCIENCEGYM_TASKS not set; source comparison not run')
 def test_microscopy_preparation_and_macros(self):
  raw=json.loads((TASKS/'microscopy_operations_v2'/'operation_sequences.json').read_text());f=get('microscopy');ops={o['id']:o for o in f['operations']}
  for b,r in zip(raw['wet_lab_branches'],f['routes']):
   self.assertEqual([o['id']for o in b['preparation']],ids(r['nodes'])[:len(b['preparation'])])
   for original in b['preparation']:
    op=ops[original['id']];self.assertEqual(op['pre'],[original['precondition_state']]);self.assertEqual(op['post'],[original['output_state']]);self.assertEqual(op['detail']['reported_parameters'],original['reported_parameters'])
  self.assertEqual(f['macros'],json.loads((TASKS/'microscopy_operations_v2'/'interaction_design.json').read_text())['macros'])
 @unittest.skipUnless(TASKS,'SCIENCEGYM_TASKS not set; source comparison not run')
 def test_perovskite_unknowns_and_services_exact(self):
  raw=json.loads((TASKS/'perovskite_operations_v2'/'operations.json').read_text()); f=get('perovskite')
  self.assertEqual(f['context']['service_definitions'],raw['service_definitions'])
  self.assertEqual(len(f['operations']),len(raw['operations']))
  for original,mapped in zip(raw['operations'],f['operations']):
   for a,b in [('actions','actions'),('preconditions','pre'),('postconditions','post'),('recovery','recovery'),('unknown_ids','unknowns'),('evidence_ids','sources')]:self.assertEqual(original[a],mapped[b])
   candidates=[s for sid,s in raw['service_definitions'].items() if original['id'].startswith(sid+'_')]
   if candidates:self.assertEqual(mapped['detail']['service_card'],max(candidates,key=lambda s:len(s['id'])))
 @unittest.skipUnless(TASKS,'SCIENCEGYM_TASKS not set; source comparison not run')
 def test_perovskite_condition_contracts_exact(self):
  raw=json.loads((TASKS/'perovskite_operations_v2'/'branches.json').read_text()); f=get('perovskite')
  for a,b in zip(raw['branches'],f['routes']):
   self.assertEqual(b['detail'],builder.without(a,{'id','label','full_operation_sequence'}))
  for name in ['control_packages','material_cards','granularity_gaps','RELEASE_BOUNDARY','agent_visible','coverage_matrix']:
   self.assertEqual(f['context'][name],json.loads((TASKS/'perovskite_operations_v2'/(name+'.json')).read_text()))
if __name__=='__main__':unittest.main()
