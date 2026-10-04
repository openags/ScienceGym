import unittest,json,struct,pathlib,sys,hashlib,zipfile
P=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
from semantic_controls import StaticSceneState,Hold

def load(n):return json.loads((P/n).read_text())
def glb(n):
 data=(P/'geometry'/n).read_bytes();magic,version,length=struct.unpack_from('<4sII',data);assert magic==b'glTF' and version==2 and length==len(data)
 ln,tp=struct.unpack_from('<II',data,12);assert tp==0x4e4f534a
 return json.loads(data[20:20+ln])

class Contracts(unittest.TestCase):
 def setUp(self):self.plan=load('task_binding_snapshot.json');self.inv=load('asset_inventory.json');self.aff=load('affordances.json');self.meta=load('asset_metadata.json')
 def test_six_stable_groups(self):self.assertEqual([x['asset_id'] for x in self.plan['scene_assets']],[x['asset_id'] for x in self.inv['assets']]);self.assertEqual(len(self.inv['assets']),6)
 def test_all_31_anchors(self):
  expected={(x['asset_id'],a) for x in self.plan['scene_assets'] for a in x['required_anchor_ids']};actual={(x['asset_id'],x['anchor_id']) for x in self.aff['anchors']};self.assertEqual(expected,actual);self.assertEqual(len(actual),31)
 def test_anchor_targets_exist(self):
  parts={x['part_id'] for a in self.inv['assets'] for x in a['parts']}
  for a in self.aff['anchors']:self.assertIn(a['target_object'],parts);self.assertIsNone(a['physical_qualified_transform'])
 def test_bindings_synchronized(self):
  b=load('operation_bindings.json');self.assertEqual(b['source_plan_sha256'],hashlib.sha256((P/'task_binding_snapshot.json').read_bytes()).hexdigest())
  for a,r in zip(self.plan['scene_assets'],b['bindings']):self.assertEqual(a['bind_operation_ids'],r['operation_ids']);self.assertEqual(set(a['required_anchor_ids']),set(r['anchors']))
 def test_no_physical_claim(self):
  for k in ['physical_execution','physical_geometry_validated','source_flow_resolved','collision_validated','calibration_execution']:self.assertFalse(self.meta['readiness'][k])
 def test_all_dimensions_authored(self):
  for a in self.inv['assets']:
   self.assertEqual(a['display_scale'],1);self.assertIsNone(a['physical_qualified_transform'])
   for p in a['parts']:self.assertEqual(p['source_dimension_status'],'authored_unqualified');self.assertEqual(len(p['dimensions_m']),3)
 def test_volume_distinctions(self):
  d={x['parameter']:x for x in self.meta['dimension_ledger']};self.assertEqual(d['chamber_nominal_volume']['value_m3'],22e-9);self.assertEqual(d['optically_interrogated_region']['value_m3'],300e-15);self.assertIsNone(d['total_handling_volume']['value']);self.assertNotEqual(d['chamber_nominal_volume']['unit'],d['optically_interrogated_region']['unit'])
 def test_reuse_count_no_inflation(self):
  r=load('geometry/reused_carrier_components.json');self.assertEqual(len(r['parts']),15);self.assertEqual(r['reuse_family_count'],2);self.assertEqual(r['new_unique_asset_credit'],0);self.assertIsNone(self.inv['unique_asset_count']);self.assertEqual(len(self.inv['reused_families']),2)
 def test_reuse_inventory_ids(self):
  reused=[p for a in self.inv['assets'] for p in a['parts'] if p['geometry_basis']=='reused_original_afm_mesh'];self.assertEqual(len(reused),15);self.assertTrue(all(p['source_part_id'] for p in reused))
 def test_closed_proxy_required(self):
  parts={x['part_id'] for a in self.inv['assets'] for x in a['parts']};self.assertIn('pump.closed_proxy',parts);self.assertIn('optics.sealed_body',parts);self.assertIn('cartridge.closed_shell',parts)
 def test_license_source_exclusion(self):
  self.assertEqual(self.meta['provenance']['source_reference']['license'],'CC BY-NC-ND 4.0');self.assertFalse(self.meta['provenance']['source_reference']['source_art_redistributed']);self.assertFalse(self.meta['provenance']['source_reference']['source_shape_accuracy_claimed'])

class Exports(unittest.TestCase):
 def test_main_glb_isolated(self):
  g=glb('sucrose_operations_lab.glb');self.assertEqual(len(g['scenes']),1);names={n.get('name','') for n in g['nodes']};expected={x['asset_id'] for x in load('task_binding_snapshot.json')['scene_assets']};actual={n['extras']['asset_id'] for n in g['nodes'] if 'asset_id' in n.get('extras',{})};self.assertEqual(expected,actual);self.assertNotIn('DISPLAY.volume_lineage',names);self.assertFalse(any('studio.floor' in n for n in names));self.assertEqual(len([n for n in g['nodes'] if 'anchor_id' in n.get('extras',{})]),31)
 def test_display_glb_isolated(self):
  g=glb('sucrose_volume_lineage_display.glb');self.assertEqual(len(g['scenes']),1);names={n.get('name','') for n in g['nodes']};self.assertIn('DISPLAY.volume_lineage',names);self.assertFalse(any('asset_id' in n.get('extras',{}) or 'anchor_id' in n.get('extras',{}) for n in g['nodes']));self.assertFalse(any('studio.floor' in n for n in names));self.assertFalse(any(n.startswith('A_') for n in names))
 def test_no_glb_external_resources(self):
  for f in ['sucrose_operations_lab.glb','sucrose_volume_lineage_display.glb']:
   g=glb(f);self.assertFalse(g.get('images'));self.assertFalse(g.get('animations'));self.assertTrue(all('uri' not in b for b in g.get('buffers',[])))
 def test_cpu_png_evidence(self):
  from PIL import Image,ImageStat
  for f in ['overview','cartridge_service','volume_lineage']:
   im=Image.open(P/'evidence'/f'{f}.png').convert('RGB');self.assertEqual(im.size,(1600,1100));self.assertGreater(max(ImageStat.Stat(im).stddev),15)
 def test_allowlist_safe(self):
  files=load('EXPORT_ALLOWLIST.json')['files'];self.assertEqual(len(files),len(set(files)))
  for f in files:
   p=P/f;self.assertFalse(pathlib.Path(f).is_absolute());self.assertNotIn('..',pathlib.Path(f).parts);self.assertTrue(p.is_file(),f);self.assertFalse(p.is_symlink());self.assertNotIn(p.suffix.lower(),['.pdf','.html','.blend1','.log','.pyc','.zip']);self.assertNotIn('private',f.lower());self.assertNotIn('chem_instrument_sources',f)

class Guards(unittest.TestCase):
 def prepared(self):
  s=StaticSceneState();s.dock();s.retain();s.isolate_inlet();s.verify_clamp(observed_closed=True);s.switch_sample('S','A');s.bind_reference('REF');s.acknowledge_fixture_service();s.bind_fixture_calibration('CAL');return s
 def test_default_flow_block(self):
  s=StaticSceneState();self.assertTrue(s.flow_hold);self.assertFalse(s.source_flow_resolved);self.assertFalse(s.physical_execution)
  with self.assertRaisesRegex(Hold,'FLOW_40X'):s.request_pump()
 def test_fixture_ack_never_unlocks_pump(self):
  s=self.prepared();self.assertFalse(s.acknowledge_fixture_service()['pump_enabled']);self.assertTrue(s.flow_hold)
  with self.assertRaisesRegex(Hold,'FLOW_40X'):s.request_pump(50)
  with self.assertRaisesRegex(Hold,'NO_PHYSICAL'):s.request_acquisition()
 def test_retain_requires_dock(self):
  with self.assertRaisesRegex(Hold,'NOT_DOCKED'):StaticSceneState().retain()
 def test_repeated_dock_rejected(self):
  s=StaticSceneState();s.dock()
  with self.assertRaisesRegex(Hold,'ALREADY'):s.dock()
 def test_undock_requires_release(self):
  s=self.prepared()
  with self.assertRaisesRegex(Hold,'RETENTION'):s.undock()
  s.release_retention();s.undock();self.assertIsNone(s.fixture_calibration_id)
 def test_sample_switch_requires_isolation(self):
  s=StaticSceneState();s.dock();s.inlet_isolated=False
  with self.assertRaisesRegex(Hold,'ISOLATED'):s.switch_sample('S','A')
 def test_sample_requires_identity(self):
  s=StaticSceneState();s.dock();s.isolate_inlet();s.verify_clamp(observed_closed=True)
  with self.assertRaisesRegex(Hold,'MISSING_SAMPLE'):s.switch_sample('','')
 def test_sample_switch_requires_independent_clamp_observation(self):
  s=StaticSceneState();s.dock();s.isolate_inlet()
  with self.assertRaisesRegex(Hold,'CLAMP_NOT_VERIFIED'):s.switch_sample('S','A')
  with self.assertRaisesRegex(Hold,'CLAMP_NOT_VERIFIED'):s.verify_clamp(observed_closed=False)
  with self.assertRaisesRegex(Hold,'INVALID_CLAMP'):s.verify_clamp(observed_closed='closed')
  s.verify_clamp(observed_closed=True);s.switch_sample('S','A');s.isolate_inlet()
  with self.assertRaisesRegex(Hold,'CLAMP_NOT_VERIFIED'):s.switch_sample('S2','A2')
 def test_every_switch_consumes_observation_and_requires_fresh_cycle(self):
  s=self.prepared();self.assertFalse(s.inlet_isolation_verified);self.assertIsNone(s.inlet_verified_cycle)
  with self.assertRaisesRegex(Hold,'CLAMP_NOT_VERIFIED'):s.switch_sample('S2','A2')
  self.assertEqual((s.sample_id,s.aliquot_id),('S','A'))
  with self.assertRaisesRegex(Hold,'FRESH_CLAMP_CYCLE'):s.verify_clamp(observed_closed=True)
  s.isolate_inlet()
  with self.assertRaisesRegex(Hold,'CLAMP_NOT_VERIFIED'):s.switch_sample('S2','A2')
  s.verify_clamp(observed_closed=True);s.switch_sample('S2','A2')
  self.assertEqual((s.sample_id,s.aliquot_id),('S2','A2'));self.assertEqual(s.inlet_consumed_cycle,2);self.assertFalse(s.inlet_isolation_verified)
  with self.assertRaisesRegex(Hold,'CLAMP_NOT_VERIFIED'):s.switch_sample('S3','A3')
 def test_initial_verify_requires_clamp_command(self):
  s=StaticSceneState();s.dock()
  with self.assertRaisesRegex(Hold,'FRESH_CLAMP_CYCLE'):s.verify_clamp(observed_closed=True)
 def test_new_clamp_invalidates_previous_cycle_observation(self):
  s=StaticSceneState();s.dock();s.isolate_inlet();s.verify_clamp(observed_closed=True);s.isolate_inlet()
  with self.assertRaisesRegex(Hold,'CLAMP_NOT_VERIFIED'):s.switch_sample('S','A')
  s.verify_clamp(observed_closed=True);s.switch_sample('S','A');self.assertEqual(s.inlet_consumed_cycle,2)
 def test_clamp_cycle_and_switch_require_docked_cartridge(self):
  s=StaticSceneState()
  with self.assertRaisesRegex(Hold,'NOT_DOCKED'):s.isolate_inlet()
  with self.assertRaisesRegex(Hold,'NOT_DOCKED'):s.verify_clamp(observed_closed=True)
  with self.assertRaisesRegex(Hold,'NOT_DOCKED'):s.switch_sample('S','A')
 def test_undock_invalidates_pending_clamp_observation(self):
  s=StaticSceneState();s.dock();s.isolate_inlet();s.verify_clamp(observed_closed=True);s.undock();s.dock()
  with self.assertRaisesRegex(Hold,'CLAMP_NOT_VERIFIED'):s.switch_sample('S','A')
  with self.assertRaisesRegex(Hold,'FRESH_CLAMP_CYCLE'):s.verify_clamp(observed_closed=True)
  s.isolate_inlet();s.verify_clamp(observed_closed=True);s.switch_sample('S','A')
 def test_sample_switch_clears_reference(self):
  s=self.prepared();s.isolate_inlet();s.verify_clamp(observed_closed=True);s.switch_sample('S2','A2');self.assertIsNone(s.reference_id)
  with self.assertRaisesRegex(Hold,'INCOMPLETE'):s.fixture_pair(run_id='R',beam_frame_id='B',speckle_frame_id='SP')
 def test_config_changes_invalidate_calibration(self):
  for kw in [{'plate_id':'P2'},{'wavelength_profile_id':'W2'},{'setup_version':'V2'}]:
   s=self.prepared();s.change_setup(**kw);self.assertIsNone(s.fixture_calibration_id);self.assertEqual(s.calibration_epoch,1)
   with self.assertRaises(Hold):s.fixture_pair(run_id='R',beam_frame_id='B',speckle_frame_id='SP')
 def test_fixture_lineage_complete_and_not_measurement(self):
  r=self.prepared().fixture_pair(run_id='R',beam_frame_id='B',speckle_frame_id='SP')
  for k in ['sample_id','aliquot_id','setup_version','plate_id','wavelength_profile_id','reference_id','calibration_id','frame_pair','run_id']:self.assertTrue(r[k])
  self.assertEqual(r['origin'],'authored_fixture_not_measurement');self.assertIsNone(r['measurement_value']);self.assertIsNone(r['image_data']);self.assertFalse(r['source_flow_resolved']);self.assertFalse(r['physical_execution'])
 def test_all_receipt_ids_reject_blank_and_nonstrings(self):
  for field in ['sample_id','aliquot_id','setup_version','plate_id','wavelength_profile_id','reference_id','fixture_calibration_id']:
   for invalid in ['', '   ', None, 0, 1, [], {}]:
    s=self.prepared();setattr(s,field,invalid)
    with self.assertRaisesRegex(Hold,'INCOMPLETE'):s.fixture_pair(run_id='R',beam_frame_id='B',speckle_frame_id='SP')
  for field in ['run_id','beam_frame_id','speckle_frame_id']:
   for invalid in ['', '   ', None, 0, 1, [], {}]:
    args={'run_id':'R','beam_frame_id':'B','speckle_frame_id':'SP'};args[field]=invalid
    with self.assertRaisesRegex(Hold,'INCOMPLETE'):self.prepared().fixture_pair(**args)
 def test_configuration_rejects_invalid_ids(self):
  for field in ['setup_version','plate_id','wavelength_profile_id']:
   for invalid in ['', '   ', 0, 1, [], {}]:
    with self.assertRaisesRegex(Hold,'INVALID_CONFIGURATION'):self.prepared().change_setup(**{field:invalid})
 def test_config_update_is_atomic_on_invalid_input(self):
  s=self.prepared();old=(s.plate_id,s.wavelength_profile_id,s.fixture_calibration_id)
  with self.assertRaisesRegex(Hold,'INVALID_CONFIGURATION'):s.change_setup(plate_id='NEW',wavelength_profile_id='')
  self.assertEqual((s.plate_id,s.wavelength_profile_id,s.fixture_calibration_id),old)
 def test_direct_config_mutation_rejects_stale_calibration(self):
  s=self.prepared();s.plate_id='DIFFERENT_VALID_ID'
  with self.assertRaisesRegex(Hold,'CONTEXT_MISMATCH'):s.fixture_pair(run_id='R',beam_frame_id='B',speckle_frame_id='SP')
 def test_frame_roles_distinct(self):
  with self.assertRaisesRegex(Hold,'COLLISION'):self.prepared().fixture_pair(run_id='R',beam_frame_id='SAME',speckle_frame_id='SAME')
 def test_unacknowledged_fixture_rejected(self):
  s=self.prepared();s.fixture_acknowledged=False
  with self.assertRaisesRegex(Hold,'NOT_ACKNOWLEDGED'):s.fixture_pair(run_id='R',beam_frame_id='B',speckle_frame_id='SP')

if __name__=='__main__':unittest.main()
