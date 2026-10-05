"""Portable contract checks; these do not test physics or execute Blender.
Run: python -m unittest discover -s tests -v
The native check is separate: blender -b geometry/cooling_operations_lab.blend
    --python tests/verify_blend.py
"""
import copy
from collections import deque
from dataclasses import asdict, replace
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
import unittest

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P))
from semantic_controls import State, transition, validate, EVENT_TO_OPERATION


def read(name):
    return json.loads((P / name).read_text())


def glb(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from('<4sII', data)
    if (magic, version, length) != (b'glTF', 2, len(data)):
        raise AssertionError('Invalid GLB header: ' + str(path))
    chunks = {}; pos = 12
    while pos < len(data):
        size, kind = struct.unpack_from('<II', data, pos)
        pos += 8
        if pos + size > len(data):
            raise AssertionError('Truncated GLB chunk')
        chunks[kind] = data[pos:pos + size]
        pos += size
    if pos != len(data):
        raise AssertionError('Invalid GLB chunk length')
    return json.loads(chunks[0x4E4F534A]), chunks.get(0x004E4942, b'')


def vertices(gltf, binary, name):
    node = next(n for n in gltf['nodes'] if n.get('name') == name)
    result = []
    for primitive in gltf['meshes'][node['mesh']]['primitives']:
        accessor = gltf['accessors'][primitive['attributes']['POSITION']]
        if accessor['componentType'] != 5126 or accessor['type'] != 'VEC3':
            raise AssertionError('Expected float32 VEC3')
        view = gltf['bufferViews'][accessor['bufferView']]
        start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        stride = view.get('byteStride', 12)
        result += [struct.unpack_from('<fff', binary, start + i * stride)
                   for i in range(accessor['count'])]
    return result


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = read('asset_inventory.json')
        cls.meta = read('asset_metadata.json')
        cls.bindings = read('operation_bindings.json')
        cls.affordances = read('affordances.json')
        cls.assets = {a['asset_id']: a for a in cls.inventory['assets']}
        cls.parts = {p['part_id']: p for a in cls.assets.values() for p in a['parts']}
        cls.owner = {p['part_id']: a['asset_id'] for a in cls.assets.values() for p in a['parts']}
        cls.scene, cls.binary = glb(P / 'geometry/cooling_operations_lab.glb')
        cls.module, _ = glb(P / 'geometry/cooling_handling_module.glb')

    def assertDims(self, object_id, expected, tolerance=1e-7):
        for actual, target in zip(self.parts[object_id]['dimensions_m'], expected):
            self.assertAlmostEqual(actual, target, delta=tolerance, msg=object_id)

    def test_required_deliverables_exist(self):
        names = ['README.md', 'asset_metadata.json', 'asset_inventory.json',
                 'operation_bindings.json', 'affordances.json', 'states.json', 'semantic_controls.py',
                 'geometry/build_scene.py', 'geometry/apply_demo_state.py',
                 'geometry/cooling_operations_lab.blend',
                 'geometry/cooling_operations_lab.glb', 'geometry/cooling_handling_module.glb',
                 'materials/materials.json', 'tests/test_package.py', 'tests/verify_blend.py',
                 'evidence/overview.png', 'evidence/sample_handling.png',
                 'evidence/equipment_closeup.png', 'review/render_receipt.json',
                 'LICENSES/Apache-2.0.txt', 'LICENSES/Blender-font-notice.txt',
                 'LICENSES/ATTRIBUTION.md']
        for name in names:
            with self.subTest(file=name):
                self.assertTrue((P/name).is_file())
                self.assertGreater((P/name).stat().st_size, 0)
        header = (P/'geometry/cooling_operations_lab.blend').read_bytes()[:16]
        self.assertTrue(header.startswith(b'BLENDER') or header.startswith(b'\x28\xb5\x2f\xfd'),
                        'Expected native Blend or Blender zstd-compressed Blend')

    def test_exact_unique_inventory_counts(self):
        self.assertEqual(len(self.inventory['assets']), 8)
        self.assertEqual(len(self.assets), 8)
        total = sum(len(a['parts']) for a in self.assets.values())
        self.assertEqual(total, len(self.parts))
        self.assertEqual(total, 438)
        self.assertEqual(len({a['instance_id'] for a in self.assets.values()}), 8)
        self.assertEqual(self.meta['inventory']['distinct_asset_root_count'], 8)
        self.assertEqual(self.meta['inventory']['part_count'], total)
        self.assertEqual(set(self.meta['inventory']['root_ids']), set(self.assets))
        self.assertEqual(sum(a['part_count'] for a in self.meta['assets']), total)
        self.assertEqual(self.meta['inventory']['paired_experimental_display_instances'],
                         ['cooling.white', 'cooling.black'])

    def test_glb_static_object_bindings_and_scope(self):
        names = [n.get('name') for n in self.scene['nodes']]
        self.assertEqual(len(names), len(set(names)))
        exclusions = set(self.meta['inventory']['glb_intentionally_excluded_part_ids'])
        self.assertEqual(exclusions, {'studio.floor', 'handling.film.lower.torn_variant'})
        self.assertEqual(set(names), set(self.assets) | (set(self.parts) - exclusions))
        module_roots = set(self.meta['inventory']['handling_module_root_ids'])
        expected = module_roots | {p['part_id'] for aid in module_roots
                                 for p in self.assets[aid]['parts'] if p['part_id'] not in exclusions}
        self.assertEqual({n.get('name') for n in self.module['nodes']}, expected)
        for doc in [self.scene, self.module]:
            self.assertEqual(doc['asset']['version'], '2.0')
            self.assertFalse(doc.get('animations'))
            self.assertFalse(doc.get('images'))
            self.assertTrue(all('uri' not in b for b in doc.get('buffers', [])))
        for n in self.scene['nodes']:
            if n.get('name') in self.assets:
                self.assertIs(n['extras']['physical_execution'], False)
                self.assertEqual(n['extras']['readiness'], 'static_semantic_only')

    def test_units_frames_and_scale_are_explicit(self):
        self.assertEqual(self.inventory['units'], 'metres')
        self.assertEqual(self.meta['units']['length'], 'metre')
        self.assertEqual(self.meta['frames']['handedness'], 'right')
        self.assertEqual(self.meta['frames']['native_up_axis'], '+Z')
        self.assertIn('Y-up', self.meta['frames']['glb_export'])
        for part in self.parts.values():
            self.assertEqual(len(part['translation_m']), 3)
            self.assertEqual(len(part['rotation_quaternion_xyzw']), 4)
            self.assertTrue(all(math.isfinite(v) for v in part['dimensions_m']))
            self.assertTrue(all(v >= 0 for v in part['dimensions_m']))

    def test_source_component_dimensions(self):
        for color in ['white', 'black']:
            self.assertDims(color+'.emitter_copper', [.05, .05, .0005])
            for layer in [1, 2]:
                self.assertDims(color+f'.insulation.{layer}', [.05, .05, .025])
            self.assertDims(color+'.pe_support', [.102, .102, .052])
            self.assertDims(color+'.film_frame', [.127, .127, .0064])
            self.assertDims(color+'.radiation_shield', [.152, .152, .057])
            self.assertDims(color+'.aperture_plate', [.152, .152, .002])
            self.assertDims(color+'.reflector_disk', [.06, .06, .0015])
            self.assertAlmostEqual(self.parts[color+'.track_placeholder']['dimensions_m'][2], .0015)
        self.assertDims('handling.film_frame', [.127, .127, .0064])
        self.assertDims('backside.emitter_copper', [.05, .05, .0005])

    def test_annular_holes_in_exported_meshes(self):
        # glTF positions of these meshes bake world-space centers; Y is native Z.
        cases = []
        for color, x in [('white', -.49), ('black', -.13)]:
            for suffix, ri, ro, h in [('film_frame', .0535, .0635, .0064),
                                      ('pe_support', .038, .051, .052),
                                      ('radiation_shield', .070, .076, .057),
                                      ('aperture_plate', .025, .076, .002)]:
                cases.append((color+'.'+suffix, x, .17, ri, ro, h))
        cases.append(('handling.film_frame', -.48, -.275, .0535, .0635, .0064))
        for name, x, y, ri, ro, h in cases:
            points = vertices(self.scene, self.binary, name)
            radii = [math.hypot(p[0]-x, p[2]+y) for p in points]
            with self.subTest(mesh=name):
                self.assertAlmostEqual(min(radii), ri, delta=1e-7)
                self.assertAlmostEqual(max(radii), ro, delta=1e-7)
                self.assertAlmostEqual(max(p[1] for p in points)-min(p[1] for p in points), h, delta=1e-7)

    def test_film_thickness_identity_and_display_exaggeration(self):
        ids = []
        for color in ['white', 'black']:
            for layer in ['lower', 'upper']:
                p = self.parts[f'{color}.film.{layer}']
                self.assertAlmostEqual(p['dimensions_m'][2], .000016, delta=1e-9)
                self.assertEqual(p['properties']['display_thickness_scale'], 1)
                ids.append(p['properties']['component_identity'])
        for layer in ['lower', 'upper']:
            p = self.parts['handling.film.'+layer]
            self.assertAlmostEqual(p['dimensions_m'][2], .0008, delta=1e-8)
            self.assertEqual(p['properties']['physical_target_thickness_m'], .000016)
            self.assertEqual(p['properties']['display_thickness_scale'], 50)
            self.assertAlmostEqual(p['dimensions_m'][0], .124, delta=1e-7)
            ids.append(p['properties']['component_identity'])
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn('handling.film.lower.torn_variant', self.parts)
        self.assertEqual(self.parts['handling.film.lower.torn_variant']['properties']['state_variant'], 'torn_demo')

    def test_height_conflict_remains_unknown(self):
        conflict = self.meta['unresolved_source_conflicts'][0]
        self.assertEqual(conflict['id'], 'SC_HEIGHT')
        self.assertEqual(conflict['source_values_m'], [.1, .15])
        self.assertIsNone(conflict['physical_target_height_m'])
        self.assertEqual(conflict['display_height_m'], .15)
        for color in ['white', 'black']:
            p = self.parts[color+'.reflector_disk']
            self.assertEqual(p['properties']['physical_target_height_m'], 'UNKNOWN')
            self.assertEqual(p['properties']['display_height_m'], .15)
            diff = p['translation_m'][2] - self.parts[color+'.emitter_copper']['translation_m'][2]
            self.assertAlmostEqual(diff, .15, delta=1e-7)
            self.assertIs(self.parts[color+'.reflector_carriage']['properties']['track_qualified'], False)

    def test_sensor_schematic_present_but_coordinates_unqualified(self):
        sensors = self.meta['sensor_geometry_boundary']
        self.assertIs(sensors['schematic_position_evidence_exists'], True)
        self.assertIsNone(sensors['qualified_coordinate_map'])
        self.assertIsNone(sensors['mounting_tolerances'])
        self.assertEqual(sensors['six_extra_sensor_objects'], ['map_probe.'+str(i) for i in range(1, 7)])
        self.assertTrue(all(x in self.parts for x in sensors['six_extra_sensor_objects']))
        self.assertIn('rack', sensors['implemented_pose'])
        self.assertIn('Figure 5', sensors['source_locator'])

    def test_source_and_rights_records(self):
        sources = {s['source_id']: s for s in self.meta['source_references']}
        self.assertEqual(sources['MAIN']['doi'], '10.1038/s41467-018-07293-9')
        self.assertEqual(sources['MAIN']['url'], 'https://www.nature.com/articles/s41467-018-07293-9')
        self.assertEqual(sources['SI']['local_reference_sha256'],
                         '61f8587c1b34a45072fac9b25591b89f1a1b00b212b61e9c29c41e2e73a340b3')
        self.assertEqual(sources['SI']['local_text_sha256'],
                         'fc3e668bddd6d3835d9239c7e50eb47a0502fc50d71c29d3558732941a340200')
        self.assertIs(self.meta['reuse']['source_pixels_or_CAD_copied'], False)
        self.assertIs(self.meta['reuse']['embedded_third_party_images'], False)
        self.assertEqual(self.meta['license']['id'], 'Apache-2.0')
        self.assertIn('Apache License', (P/self.meta['license']['text']).read_text())
        for record in self.meta['source_dimensions']:
            self.assertTrue(record['source_locator'])
            self.assertIsNone(record['physical_tolerance_m'])
            for object_id in record['object_ids']:
                self.assertIn(object_id, self.parts)

    def test_operation_coverage_and_all_named_ids_resolve(self):
        entries = self.bindings['bindings']
        self.assertEqual(len(entries), 56)
        self.assertEqual(len({r['operation_id'] for r in entries}), 56)
        self.assertEqual(sum(r['binding_status'] == 'partial_visual_or_semantic_only' for r in entries), 29)
        self.assertEqual(sum(r['binding_status'] == 'not_built' for r in entries), 27)
        self.assertEqual(self.bindings['fully_implemented_operation_count'], 0)
        for row in entries:
            self.assertIs(row['physical_operation_implemented'], False)
            self.assertIs(row['operation_completion_receipt'], False)
            for aid in row['asset_ids']:
                self.assertIn(aid, self.assets)
            for part in row['object_ids']:
                self.assertIn(part, self.parts)
                self.assertIn(self.owner[part], row['asset_ids'])
            if row['binding_status'] == 'not_built':
                self.assertEqual(row['object_ids'], [])
                self.assertEqual(row['asset_ids'], [])
        all_ops = {r['operation_id'] for r in entries}
        for asset in self.assets.values():
            self.assertTrue(set(asset['operation_ids']).issubset(all_ops))

    def test_upstream_contract_hash_and_operation_ids_if_available(self):
        upstream = P.parent/'afm-assets-release-candidate/tasks/directional_cooling_operations_v2/operations.json'
        if not upstream.exists():
            self.skipTest('Reference checkout absent; portable package checks still run')
        expected = json.loads(upstream.read_text())['operations']
        self.assertEqual([o['id'] for o in expected], [o['operation_id'] for o in self.bindings['bindings']])
        digest = hashlib.sha256(upstream.read_bytes()).hexdigest()
        self.assertEqual(self.bindings['task_operations_sha256'], digest)
        self.assertEqual(self.meta['task_operations_sha256'], digest)
        for actual, source in zip(self.bindings['bindings'], expected):
            self.assertEqual(actual['task_station_id'], source['location_id'])
            self.assertEqual(actual['title'], source['title'])

    def test_declared_state_catalog_matches_runtime(self):
        catalog = read('states.json')
        self.assertEqual(catalog['canonical_state'], asdict(State()))
        self.assertEqual({e['id']: e['source_task_operation_id'] for e in catalog['events']},
                         EVENT_TO_OPERATION)
        self.assertEqual(len(catalog['events']), len(EVENT_TO_OPERATION))
        self.assertTrue(all(e['physical_receipt'] is False for e in catalog['events']))
        self.assertIs(catalog['geometry_qualified'], False)
        self.assertIn('sensor_measurement', catalog['forbidden_claims'])

    def test_authored_clearance_offsets_are_labeled_and_separated(self):
        authored = self.meta['authored_clearance_design']
        self.assertEqual(authored['pe_support_height_m'], .052)
        self.assertEqual(authored['upper_insulation_heater_recess']['depth_m'], .0012)
        self.assertIs(authored['upper_insulation_heater_recess']['source_dimension'], False)
        for color in ['white', 'black']:
            self.assertDims(color+'.assembly_support_pedestal', [.156, .156, .0093])
            self.assertDims(color+'.shield_adapter', [.152, .152, .0035])
            film = self.parts[color+'.film.lower']
            paint = self.parts[color+'.emitter_paint_visual']
            # Bound-order check only, not a collision/contact or physical support test.
            film_bottom = film['translation_m'][2] - film['dimensions_m'][2]/2
            paint_top = paint['translation_m'][2] + paint['dimensions_m'][2]/2
            self.assertGreater(film_bottom, paint_top)
            self.assertIn('Authored', self.parts[color+'.shield_adapter']['dimension_status'])

    def test_event_to_operation_mapping_exact(self):
        documented = {e: row['operation_id'] for row in self.bindings['bindings']
                      for e in row['semantic_events']}
        self.assertEqual(documented, EVENT_TO_OPERATION)
        self.assertEqual(self.meta['controls']['event_to_operation'], EVENT_TO_OPERATION)
        self.assertEqual(self.meta['controls']['default_state'], asdict(State()))

    def test_affordance_frames_objects_and_operation_ids(self):
        frames = {f['frame_id']: f for f in self.affordances['frames']}
        records = self.affordances['affordances']
        self.assertEqual(len(records), 20)
        self.assertEqual(len({r['affordance_id'] for r in records}), 20)
        self.assertEqual(len(frames), len(records))
        operation_ids = {r['operation_id'] for r in self.bindings['bindings']}
        for row in records:
            frame = frames[row['local_frame_id']]
            self.assertIn(row['asset_id'], self.assets)
            self.assertEqual(frame['parent_asset_id'], row['asset_id'])
            self.assertEqual(len(frame['translation_m']), 3)
            self.assertEqual(frame['rotation_quaternion_xyzw'], [0, 0, 0, 1])
            self.assertTrue(row['preconditions'])
            self.assertTrue(row['failure_or_stop_conditions'])
            self.assertTrue(row['allowed_tool_or_gripper'])
            self.assertIs(row['physical_qualification'], False)
            for part in row['object_ids']:
                self.assertIn(part, self.parts)
                self.assertEqual(self.owner[part], row['asset_id'])
            self.assertTrue(set(row['operation_ids']).issubset(operation_ids))
            for event in row['semantic_events']:
                self.assertIn(event, EVENT_TO_OPERATION)
                self.assertIn(EVENT_TO_OPERATION[event], row['operation_ids'])

    def test_materials_and_collision_are_unqualified(self):
        for material in read('materials/materials.json'):
            self.assertIs(material['appearance_only'], True)
            self.assertIs(material['measured_optical_properties'], False)
        collision = self.meta['collision']
        self.assertIs(collision['separate_collision_proxies'], False)
        self.assertIs(collision['simulation_contacts_enabled'], False)
        self.assertIsNone(collision['mass_friction_compliance'])
        self.assertIsNone(collision['backend_groups'])

    def test_no_device_success_claims_in_machine_scope(self):
        ready = self.meta['readiness']
        for key in ['physical_execution', 'robot_feasibility_validated', 'full_task_executable',
                    'source_reproduction_established']:
            self.assertIs(ready[key], False)
        self.assertIsNone(ready['physics_backend'])
        self.assertIsNone(ready['hardware_or_DAQ_backend'])
        self.assertGreaterEqual(len(self.meta['not_built']), 10)
        self.assertIn('No physical operation is complete.', (P/'README.md').read_text())
        self.assertNotIn('Measured cooling:', (P/'README.md').read_text())

    def test_png_evidence_and_render_receipt(self):
        receipt = read('review/render_receipt.json')
        self.assertEqual({r['view'] for r in receipt['renders']},
                         {'overview', 'sample_handling', 'equipment_closeup'})
        for record in receipt['renders']:
            self.assertEqual(record['engine'], 'CYCLES')
            self.assertEqual(record['device'], 'CPU')
            self.assertIs(record['actual_render'], True)
            self.assertGreater(record['samples'], 0)
            self.assertGreater(record['seconds'], 0)
            data = (P/record['path']).read_bytes()
            self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
            width, height = struct.unpack_from('>II', data, 16)
            self.assertEqual([width, height], record['resolution'])
            self.assertEqual([width, height], [1500, 1080])


class StateTests(unittest.TestCase):
    def walk(self, *events):
        state = State()
        for event in events:
            before = asdict(state)
            new = transition(state, event)
            self.assertEqual(asdict(state), before)
            self.assertIsNot(new, state)
            state = new
        return state

    def test_initial_state_and_validation(self):
        state = State()
        self.assertIs(validate(state), state)
        self.assertEqual((state.carrier, state.clamp, state.logger), ('docked', 'closed', 'idle'))
        self.assertFalse(state.geometry_qualified)
        self.assertFalse(state.physical_execution)

    def test_positive_handling_cycle(self):
        s = self.walk('open_clamp', 'grasp_carrier', 'dock_carrier', 'close_clamp')
        self.assertEqual((s.carrier, s.clamp), ('docked', 'closed'))

    def test_independent_film_replacement_revisions(self):
        s = self.walk('open_clamp', 'remove_lower_film', 'replace_lower_film')
        self.assertEqual((s.lower_film, s.lower_film_revision, s.upper_film_revision), ('intact', 2, 1))
        s = transition(transition(s, 'remove_upper_film'), 'replace_upper_film')
        self.assertEqual((s.lower_film_revision, s.upper_film_revision), (2, 2))

    def test_damage_preserves_revision_then_replacement_increments(self):
        s = self.walk('open_clamp', 'tear_lower_film')
        self.assertEqual((s.lower_film, s.lower_film_revision), ('torn_demo', 1))
        s = transition(s, 'replace_lower_film')
        self.assertEqual((s.lower_film, s.lower_film_revision), ('intact', 2))
        s = transition(s, 'tear_lower_film')
        self.assertEqual((s.lower_film, s.lower_film_revision), ('torn_demo', 2))

    def test_positive_lid_logger_reflector_and_optical_states(self):
        s = self.walk('cover_apertures', 'arm_logger', 'uncover_apertures',
                      'reflector_left', 'reflector_center', 'reflector_right', 'stop_logger')
        self.assertEqual((s.lid, s.logger, s.reflector_pose), ('parked', 'idle', 'right'))
        for event, config in [('select_uvvis', 'uvvis'), ('select_ftir_sphere', 'ftir_sphere'),
                              ('select_ftir_angle', 'ftir_angle')]:
            s = self.walk(event, 'mount_reference')
            self.assertEqual((s.optical_config, s.optical_sample), (config, 'authored_reference_demo'))
            s = transition(s, 'unload_optical')
            self.assertEqual(s.optical_sample, 'none')

    def test_reject_unsafe_demo_handling_and_missing_film(self):
        for state, event in [(State(), 'grasp_carrier'), (State(), 'dock_carrier'),
                             (State(), 'remove_lower_film'), (State(), 'remove_upper_film'),
                             (State(), 'tear_lower_film'),
                             (self.walk('arm_logger'), 'open_clamp'),
                             (self.walk('open_clamp'), 'arm_logger'),
                             (self.walk('open_clamp', 'grasp_carrier'), 'close_clamp'),
                             (self.walk('open_clamp', 'grasp_carrier'), 'cover_apertures'),
                             (self.walk('open_clamp', 'remove_lower_film', 'close_clamp'), 'arm_logger'),
                             (self.walk('open_clamp', 'remove_upper_film', 'close_clamp'), 'arm_logger'),
                             (self.walk('open_clamp', 'tear_lower_film', 'close_clamp'), 'arm_logger')]:
            before = asdict(state)
            with self.subTest(event=event, state=before):
                with self.assertRaises(ValueError):
                    transition(state, event)
                self.assertEqual(asdict(state), before)

    def test_reject_replacement_and_optical_misuse(self):
        for state, event in [(self.walk('open_clamp'), 'replace_lower_film'),
                             (self.walk('open_clamp'), 'replace_upper_film'),
                             (self.walk('open_clamp', 'remove_lower_film'), 'tear_lower_film'),
                             (self.walk('open_clamp', 'tear_lower_film'), 'tear_lower_film'),
                             (State(), 'mount_reference'),
                             (self.walk('select_uvvis', 'mount_reference'), 'mount_reference'),
                             (self.walk('select_uvvis', 'mount_reference'), 'select_ftir_angle')]:
            with self.subTest(event=event):
                with self.assertRaises(ValueError): transition(state, event)

    def test_reject_invalid_injected_states(self):
        bad = [replace(State(), **{field: value}) for field, value in
               [('carrier', 'flying'), ('clamp', 'half'), ('lower_film', 'healed'),
                ('upper_film', 'torn_demo'), ('lid', 'missing'), ('logger', 'acquiring'),
                ('optical_config', 'calibrated'), ('optical_sample', 'measured'),
                ('reflector_pose', 'sun_tracking'), ('lower_film_revision', 0),
                ('upper_film_revision', True), ('lower_film_revision', 1.5),
                ('physical_execution', True), ('geometry_qualified', True),
                ('mode', 'real_device')]]
        bad += [State(carrier='held_demo'), State(clamp='open', logger='armed_demo'),
                State(optical_sample='authored_reference_demo')]
        for state in bad:
            with self.subTest(state=asdict(state)):
                with self.assertRaises(ValueError): validate(state)
                with self.assertRaises(ValueError): transition(state, 'stop_logger')

    def test_reject_physical_and_unknown_commands(self):
        for event in ['heat', 'start_pid', 'energize_heater', 'acquire_spectrum',
                      'calibrate', 'qualify_geometry', 'execute_robot', 'complete_task',
                      'tear_upper_film', 'unknown', '']:
            with self.subTest(event=event):
                with self.assertRaises(ValueError): transition(State(), event)

    def test_bounded_reachable_state_sweep_never_claims_device_success(self):
        # Complete graph only within revision values 1..2, not a physics proof.
        initial = State(); queue = deque([initial]); seen = {tuple(asdict(initial).values())}
        succeeded = set(); rejected = set()
        while queue:
            state = queue.popleft()
            for event in EVENT_TO_OPERATION:
                snapshot = asdict(state)
                try:
                    new = transition(state, event)
                except ValueError:
                    rejected.add(event)
                    self.assertEqual(asdict(state), snapshot)
                    continue
                succeeded.add(event)
                self.assertEqual(asdict(state), snapshot)
                self.assertIs(new.physical_execution, False)
                self.assertIs(new.geometry_qualified, False)
                self.assertEqual(new.mode, 'static_semantic_demo')
                if max(new.lower_film_revision, new.upper_film_revision) > 2:
                    continue
                key = tuple(asdict(new).values())
                if key not in seen:
                    seen.add(key); queue.append(new)
        self.assertEqual(succeeded, set(EVENT_TO_OPERATION))
        self.assertGreater(len(seen), 500)
        self.assertTrue({'open_clamp', 'close_clamp', 'grasp_carrier', 'arm_logger',
                         'mount_reference', 'replace_lower_film'} <= rejected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
