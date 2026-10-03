"""Positive contracts and explicit corruptions of the public R01 binding fixture."""
import copy
import importlib.util
import json
import shutil
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PACKAGE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('r01_audit', PACKAGE / 'audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class BindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = audit.read_json(PACKAGE / 'binding.json')

    def setUp(self):
        self.binding = copy.deepcopy(self.original)

    def assert_rejected(self, code, **kwargs):
        report = audit.audit(binding=self.binding, **kwargs)
        self.assertFalse(report['passed'])
        self.assertIn(code, {issue['code'] for issue in report['issues']}, report)

    def test_public_contract_passes_with_gates(self):
        result = audit.audit()
        self.assertTrue(result['passed'], result)
        self.assertEqual(result['status'], 'static_contract_pass_with_execution_gates')
        self.assertEqual(result['counts']['operations'], 11)
        self.assertEqual(result['counts']['resolved_role_bindings'], 14)
        self.assertEqual(result['counts']['explicit_missing_role_bindings'], 1)
        self.assertEqual(result['counts']['execution_gates'], 7)

    def test_all_scope_operation_roles_accounted_for(self):
        ports = {p['id'] for p in self.binding['ports']}
        for entry in self.binding['bindings']:
            self.assertTrue(set(entry['port_ids']) <= ports)

    def test_known_geometry_gaps_remain_explicit(self):
        clip = next(p for p in self.binding['ports'] if p['task_role_id'] == 'transport_clip')
        self.assertIsNone(clip['physical_interface_pose'])
        self.assertEqual(clip['scene_object_ids'], [])
        self.assertIsNone(clip['local_frame_id'])

    def test_local_frames_are_not_grasp_frames(self):
        self.assertTrue(all(f['meaning'] == 'authored_object_origin_not_grasp_or_sensor_frame' for f in self.binding['local_frames']))
        self.assertTrue(all(p['physical_interface_pose'] is None for p in self.binding['ports']))

    def test_source_hash_drift_rejected(self):
        self.binding['source_inputs'][0]['sha256'] = '0' * 64
        self.assert_rejected('SOURCE_HASH')

    def test_source_hash_coverage_cannot_be_shortened(self):
        self.binding['source_inputs'].pop()
        self.assert_rejected('SOURCE_COVERAGE')

    def test_broken_operation_reference_rejected(self):
        self.binding['bindings'][0]['operation_id'] = 'NO_SUCH_OPERATION'
        self.assert_rejected('OPERATION_REFERENCE')

    def test_missing_operation_rejected(self):
        self.binding['bindings'].pop()
        self.assert_rejected('BINDING_COVERAGE')

    def test_duplicate_operation_rejected(self):
        self.binding['bindings'].append(copy.deepcopy(self.binding['bindings'][0]))
        self.assert_rejected('DUPLICATE_ID')

    def test_reordered_segment_rejected(self):
        self.binding['bindings'].reverse()
        self.assert_rejected('BINDING_COVERAGE')

    def test_broken_frame_reference_rejected(self):
        self.binding['bindings'][0]['frame_id'] = 'LOAD'
        self.assert_rejected('FRAME_REFERENCE')

    def test_wrong_storyboard_image_rejected(self):
        self.binding['bindings'][0]['frame_image'] = 'frames/19_LOAD.jpg'
        self.assert_rejected('FRAME_REFERENCE')

    def test_missing_operation_role_rejected(self):
        self.binding['bindings'][0]['port_ids'].pop()
        self.assert_rejected('ROLE_COVERAGE')

    def test_broken_scene_name_rejected(self):
        self.binding['ports'][0]['scene_object_ids'][0] = 'WS_TEST__not_a_real_object'
        self.assert_rejected('SCENE_REFERENCE')

    def test_wildcard_scene_reference_rejected(self):
        self.binding['ports'][0]['scene_object_ids'] = ['WS_TEST__mounted_*']
        self.assert_rejected('SCENE_REFERENCE')

    def test_missing_local_frame_rejected(self):
        self.binding['local_frames'].pop()
        self.assert_rejected('FRAME_REFERENCE')

    def test_frame_from_different_port_rejected(self):
        self.binding['local_frames'][0]['anchor_object_id'] = 'WS_TEST__camera_body'
        self.assert_rejected('FRAME_ANCHOR')

    def test_changed_transform_rejected(self):
        self.binding['local_frames'][0]['matrix_local_to_world'][0][3] += 1
        self.assert_rejected('TRANSFORM')

    def test_nonfinite_transform_rejected(self):
        self.binding['local_frames'][0]['matrix_local_to_world'][0][0] = float('nan')
        self.assert_rejected('TRANSFORM')

    def test_nonhomogeneous_transform_rejected(self):
        self.binding['local_frames'][0]['matrix_local_to_world'][3][0] = 2
        self.assert_rejected('TRANSFORM')

    def test_specimen_substitution_rejected(self):
        self.binding['bindings'][-1]['physical_object_id'] = 'obj.R01.002'
        self.assert_rejected('STATE_IDENTITY')

    def test_state_identity_substitution_rejected(self):
        self.binding['semantic_states'][3]['physical_object_id'] = 'obj.R02.001'
        self.assert_rejected('STATE_IDENTITY')

    def test_condition_change_rejected(self):
        self.binding['semantic_states'][3]['condition_id'] = 'cond.M16'
        self.assert_rejected('STATE_IDENTITY')

    def test_lineage_loss_rejected(self):
        self.binding['semantic_states'][-1]['source_unit_lineage'].pop()
        self.assert_rejected('STATE_IDENTITY')

    def test_boundary_change_rejected(self):
        self.binding['semantic_states'][3]['boundary'] = 'rotation_locked'
        self.assert_rejected('STATE_IDENTITY')

    def test_retrieval_cycle_history_reset_rejected(self):
        self.binding['semantic_states'][-1]['completed_cycles_after'] = 0
        self.assert_rejected('CYCLE_IDENTITY')

    def test_grouped_repeat_is_not_terminal_pose(self):
        self.binding['semantic_states'][-2]['rendered_pose_may_be_intermediate'] = False
        self.assert_rejected('CYCLE_IDENTITY')

    def test_source_total_cycles_cannot_be_invented(self):
        self.binding['sample']['source_total_cycles'] = 2
        self.assert_rejected('CYCLE_IDENTITY')

    def test_millimetres_as_metres_rejected(self):
        self.binding['sample']['physical_reference_envelope_m'] = [65,65,72]
        self.assert_rejected('UNITS')

    def test_physical_scale_cannot_follow_display_deformation(self):
        self.binding['sample']['physical_reference_envelope_m'][2] *= .75
        self.assert_rejected('UNITS')

    def test_wrong_axes_rejected(self):
        self.binding['units']['up_axis'] = '+Y'
        self.assert_rejected('UNITS')

    def test_display_enlargement_undeclared_rejected(self):
        self.binding['display']['nominal_scale'] = 20
        self.assert_rejected('DISPLAY_SCALE')

    def test_render_camera_not_sensor(self):
        self.binding['cameras']['storyboard_review']['intrinsics_calibrated'] = True
        self.assert_rejected('CAMERA_CLAIM')

    def test_changed_camera_metadata_rejected(self):
        self.binding['cameras']['storyboard_review']['per_frame'][0]['declaration']['location'][0] += 2
        self.assert_rejected('CAMERA_DECLARATION')

    def test_missing_camera_declaration_rejected(self):
        self.binding['cameras']['storyboard_review']['per_frame'].pop()
        self.assert_rejected('CAMERA_DECLARATION')

    def test_mesh_proxy_not_sensor(self):
        self.binding['cameras']['task_camera_proxy']['scene_objects_are_sensor'] = True
        self.assert_rejected('SENSOR_GATE')

    def test_hidden_occluder_disclosure_cannot_disappear(self):
        self.binding['occluders']['storyboard_hidden_prefixes'] = []
        self.assert_rejected('OCCLUDER_DECLARATION')

    def test_pretty_render_hiding_is_not_allowed(self):
        self.binding['occluders']['new_source_review_policy'] = 'hide_apparatus'
        self.assert_rejected('OCCLUDER_DECLARATION')

    def test_fake_visibility_claim_rejected(self):
        self.binding['claims']['robot_visibility_validated'] = True
        self.assert_rejected('OVERCLAIM')

    def test_gates_cannot_be_erased(self):
        self.binding['execution_gates'].pop()
        self.assert_rejected('MISSING_GATE')

    def test_operation_provenance_cannot_be_relabelled(self):
        self.binding['bindings'][0]['source_provenance']['authored_connector'] = 'source measured'
        self.assert_rejected('PROVENANCE')

    def test_preconditions_cannot_be_dropped(self):
        self.binding['bindings'][-1]['preconditions'] = []
        self.assert_rejected('PROVENANCE')

    def test_transport_clip_cannot_be_invented(self):
        clip = next(p for p in self.binding['ports'] if p['task_role_id'] == 'transport_clip')
        clip['scene_object_ids'] = ['WS_TEST__rotation_lock_arm']
        self.assert_rejected('MISSING_GEOMETRY')

    def test_inspected_inventory_missing_object_rejected(self):
        inv = audit.read_json(PACKAGE / 'source_evidence/source_inventory.json')
        inv['objects'] = [o for o in inv['objects'] if o['name'] != 'WS_TEST__lower_platen']
        self.assert_rejected('SCENE_REFERENCE', inventory=inv)

    def test_wrong_source_scene_rejected(self):
        self.binding['source_scene']['sha256'] = '0' * 64
        self.assert_rejected('SCENE_HASH')

    def test_malformed_document_fails_closed(self):
        del self.binding['source_scene']
        self.assert_rejected('SCHEMA_OR_INPUT')

    def test_source_path_escape_rejected(self):
        self.binding['source_inputs'][0]['path'] = '../outside.json'
        self.assert_rejected('SCHEMA_OR_INPUT')

    def test_existing_but_wrong_geometry_rejected(self):
        port = next(p for p in self.binding['ports'] if p['task_role_id'] == 'lower_platen')
        port['scene_object_ids'] = ['WS_TEST__upper_platen']
        self.assert_rejected('ROLE_SCENE_IDENTITY')

    def test_robot_view_claim_on_source_render_rejected(self):
        self.binding['cameras']['source_review']['robot_visibility_claim'] = True
        self.assert_rejected('CAMERA_CLAIM')

    def test_hidden_occluder_in_new_receipt_rejected(self):
        receipt = audit.read_json(PACKAGE / 'source_evidence/render_receipt.json')
        receipt['visibility_overrides'] = [{'object':'WS_TEST__guard_front_panel','hide_render':True}]
        self.assert_rejected('RENDER_INTEGRITY', receipt=receipt)

    def test_gpu_execution_claim_in_receipt_rejected(self):
        receipt = audit.read_json(PACKAGE / 'source_evidence/render_receipt.json')
        receipt['render_settings']['cycles_device'] = 'GPU'
        self.assert_rejected('RENDER_INTEGRITY', receipt=receipt)

    def test_changed_repeat_camera_rejected(self):
        receipt = audit.read_json(PACKAGE / 'source_evidence/render_receipt.json')
        receipt['outputs'][1]['camera_unchanged'] = False
        self.assert_rejected('RENDER_INTEGRITY', receipt=receipt)

    def test_changed_repeat_bytes_rejected(self):
        receipt = audit.read_json(PACKAGE / 'source_evidence/render_receipt.json')
        receipt['outputs'][1]['sha256'] = '0' * 64
        self.assert_rejected('RENDER_REPEAT', receipt=receipt)

    def test_source_scale_drift_rejected(self):
        inv = audit.read_json(PACKAGE / 'source_evidence/source_inventory.json')
        inv['mounted_sample']['display_station_local_bounds_m']['dimensions'][0] *= 20
        self.assert_rejected('DISPLAY_SCALE', inventory=inv)

    def test_evidence_hash_mismatch_rejected(self):
        self.binding['source_scene']['evidence_manifest_sha256'] = '0' * 64
        self.assert_rejected('EVIDENCE_HASH')

    def test_snapshot_path_escape_rejected(self):
        self.binding['source_scene']['snapshot_inventory'] = '../outside.json'
        self.assert_rejected('SCHEMA_OR_INPUT')

    def test_cycle_counter_must_not_be_boolean(self):
        self.binding['semantic_states'][7]['completed_cycles_after'] = True
        self.assert_rejected('CYCLE_IDENTITY')

    def test_semantic_states_cannot_claim_observed_telemetry(self):
        self.binding['semantic_states'][0]['meaning'] = 'measured robot telemetry'
        self.assert_rejected('STATE_SEMANTICS')

    def test_null_interface_implementation_fails_cleanly(self):
        self.binding['ports'][0]['implementation'] = None
        self.assert_rejected('SCHEMA_OR_INPUT')

    def test_source_review_role_cannot_be_robot_sensor(self):
        self.binding['cameras']['source_review']['role'] = 'calibrated_robot_sensor'
        self.assert_rejected('CAMERA_CLAIM')

    def test_missing_sensor_fields_cannot_be_a_string(self):
        self.binding['cameras']['task_camera_proxy']['missing'] = 'missing'
        self.assert_rejected('SENSOR_GATE')

    def test_scene_object_ids_must_be_an_array(self):
        self.binding['ports'][0]['scene_object_ids'] = dict.fromkeys(self.binding['ports'][0]['scene_object_ids'])
        self.assert_rejected('ROLE_SCENE_IDENTITY')

    def test_unknown_source_enlargement_cannot_be_invented(self):
        self.binding['display']['source_explicit_enlargement_factor'] = 20
        self.assert_rejected('DISPLAY_SCALE')

    def test_alternate_inventory_cannot_escape_evidence_manifest(self):
        self.binding['source_scene']['snapshot_inventory'] = 'source_contract_excerpt.json'
        self.assert_rejected('EVIDENCE_REFERENCE')

    def test_alternate_receipt_cannot_escape_evidence_manifest(self):
        self.binding['cameras']['source_review']['receipt'] = 'source_contract_excerpt.json'
        self.assert_rejected('EVIDENCE_REFERENCE')

    def test_alternate_manifest_cannot_be_selected(self):
        self.binding['source_scene']['evidence_manifest'] = 'source_contract_excerpt.json'
        self.assert_rejected('EVIDENCE_REFERENCE')

    def clone_fixture(self, root):
        target = root / 'scene_bindings/r01_mount_observe_retrieve_v1'
        shutil.copytree(PACKAGE, target, ignore=shutil.ignore_patterns('__pycache__', '.*', '*repeat.png'))
        for relative in audit.SOURCE_FILES:
            dest = root / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(audit.ROOT / relative, dest)
        return target

    def test_unpinned_alternate_receipt_normal_entrypoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = self.clone_fixture(root)
            receipt = audit.read_json(target / 'source_evidence/render_receipt.json')
            receipt['camera']['matrix_world'][0][3] += 500
            (target / 'alternate_receipt.json').write_text(json.dumps(receipt))
            self.binding['cameras']['source_review']['receipt'] = 'alternate_receipt.json'
            (target / 'binding.json').write_text(json.dumps(self.binding))
            result = audit.audit(root=root)
            self.assertFalse(result['passed'])
            self.assertIn('EVIDENCE_REFERENCE', {i['code'] for i in result['issues']})

    def test_unpinned_alternate_inventory_normal_entrypoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = self.clone_fixture(root)
            inventory = audit.read_json(target / 'source_evidence/source_inventory.json')
            for item in inventory['objects']:
                item['matrix_world'][0][3] += 10
            (target / 'alternate_inventory.json').write_text(json.dumps(inventory))
            receipt = audit.read_json(target / 'source_evidence/render_receipt.json')
            receipt['source_inventory_sha256'] = audit.digest(target / 'alternate_inventory.json')
            (target / 'alternate_receipt.json').write_text(json.dumps(receipt))
            self.binding['source_scene']['snapshot_inventory'] = 'alternate_inventory.json'
            self.binding['cameras']['source_review']['receipt'] = 'alternate_receipt.json'
            for frame in self.binding['local_frames']:
                frame['matrix_local_to_world'][0][3] += 10
            (target / 'binding.json').write_text(json.dumps(self.binding))
            result = audit.audit(root=root)
            self.assertFalse(result['passed'])
            self.assertIn('EVIDENCE_REFERENCE', {i['code'] for i in result['issues']})

    def test_changed_source_excerpt_normal_entrypoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = self.clone_fixture(root)
            excerpt = audit.read_json(target / 'source_contract_excerpt.json')
            excerpt['affordances'][0]['implementation'] = 'calibrated physical guard interlock'
            (target / 'source_contract_excerpt.json').write_text(json.dumps(excerpt))
            result = audit.audit(root=root)
            self.assertFalse(result['passed'])
            self.assertIn('EVIDENCE_HASH', {i['code'] for i in result['issues']})

    def test_source_excerpt_original_hash_disagreement(self):
        excerpt = audit.read_json(PACKAGE / 'source_contract_excerpt.json')
        excerpt['source_files'][0]['sha256'] = '0' * 64
        self.assert_rejected('PROVENANCE', excerpt=excerpt)

    def test_source_excerpt_cannot_claim_recovered_lab(self):
        excerpt = audit.read_json(PACKAGE / 'source_contract_excerpt.json')
        excerpt['station']['physical_lab_layout_recovered'] = True
        self.assert_rejected('PROVENANCE', excerpt=excerpt)

    def test_affordance_ids_must_be_an_array(self):
        port = next(p for p in self.binding['ports'] if p['source_affordance_ids'])
        port['source_affordance_ids'] = dict.fromkeys(port['source_affordance_ids'])
        self.assert_rejected('AFFORDANCE_REFERENCE')

    def test_gate_ids_must_be_an_array(self):
        self.binding['ports'][0]['execution_gate_ids'] = dict.fromkeys(self.binding['ports'][0]['execution_gate_ids'])
        self.assert_rejected('GATE_REFERENCE')

    def test_intermediate_pose_flag_must_be_boolean(self):
        self.binding['semantic_states'][0]['rendered_pose_may_be_intermediate'] = 0
        self.assert_rejected('CYCLE_IDENTITY')

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'fixture.json'
            p.write_text('{"id":1,"id":2}')
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                audit.read_json(p)

    def test_non_json_numbers_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'fixture.json'
            for number in ['NaN','Infinity','-Infinity']:
                p.write_text('{"value":' + number + '}')
                with self.assertRaisesRegex(ValueError, 'non-JSON'):
                    audit.read_json(p)

    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'pkg'
            root.mkdir()
            (Path(tmp) / 'outside').write_text('fixture')
            (root / 'linked').symlink_to(Path(tmp) / 'outside')
            with self.assertRaises(ValueError):
                audit.local_file(root, 'linked')

if __name__ == '__main__':
    unittest.main()
