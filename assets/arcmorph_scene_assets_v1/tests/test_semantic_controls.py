"""Synthetic record tests only; no physical experiment or authorization test."""
import ast
from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import semantic_controls as sc


class SemanticControlTests(unittest.TestCase):
    def stock(self, route="PP_PREP"):
        return sc.initial_state(specimen_id="EXAMPLE-S1", stock_id="EXAMPLE-ST1", material_batch="EXAMPLE-B1", route_id=route, carrier_id="EXAMPLE-C1")

    def qualification(self, family="PP"):
        return sc.Qualification(family_id=family, drawing_revision="EXAMPLE-D1", stock_qualified=True, drawing_qualified=True, service_qualified=True, fold_qualified=True, evidence_id="EXAMPLE-Q1", dimensional_basis="explicit_authored_spec", dimensional_spec_revision="EXAMPLE-DIM1", sheet_dimension_mm=383.63, fold_plan=(sc.EdgePlan("EXAMPLE-E1", (), "EXAMPLE-P1", "EXAMPLE-M1"), sc.EdgePlan("EXAMPLE-E2", ("EXAMPLE-E1",), "EXAMPLE-P2", "EXAMPLE-M2")))

    def prepared(self, route="PP_PREP"):
        state = self.stock(route)
        state = sc.fabricate_candidate(state, self.qualification(state.family_id), job_id="EXAMPLE-J1", input_stock_id=state.stock_id, output_specimen_id=state.specimen_id, receipt_id="EXAMPLE-FAB1", safe_release=True)
        return sc.inspect_prepared_candidate(state, evidence_id="EXAMPLE-INSPECT", output_specimen_id=state.specimen_id, parent_stock_id=state.stock_id, findings=tuple((key, True) for key in ("cut_boundary", "vertex_relief", "crease_map", "sheet_condition")), tools_accounted=True)

    def edge(self, edge_id="EXAMPLE-E1", result="accepted", evidence_id=None):
        return sc.EdgeObservation(edge_id, evidence_id or edge_id + "-OBS", "EXAMPLE-BEFORE", "EXAMPLE-AFTER", result, "EXAMPLE-D1", True, True)

    def folded(self, route="PP_PREP"):
        state = self.prepared(route)
        q = self.qualification(state.family_id)
        for edge in q.fold_plan:
            state = sc.record_edge_candidate(state, q, self.edge(edge.edge_id))
        return sc.finish_folding_candidate(state, q, final_inspection_id="EXAMPLE-FOLD-FINAL")

    def baseline(self, route="PP_PREP"):
        return sc.append_rest_candidate(self.folded(route), evidence_id="EXAMPLE-BASE", image_id="EXAMPLE-BASE-IMAGE", disposition="unchanged", qualified_interval_id="EXAMPLE-INTERVAL", baseline=True)

    def mounted(self, kind="rigid_metrology"):
        route = "CS1" if kind == "rigid_demo" else "PP_PREP"
        mount = sc.Mount("EXAMPLE-FIX", "EXAMPLE-FIX-R1", kind, "EXAMPLE-LEASE", ("EXAMPLE-A1", "EXAMPLE-A2"), "EXAMPLE-LJ1", "idle")
        state = sc.mount_candidate(self.baseline(route), mount, evidence_id="EXAMPLE-MOUNT", interface_qualified=True)
        return replace(state, configuration_revision="EXAMPLE-CONFIG1")

    def load_job(self):
        # Arbitrary synthetic values, never a proposed laboratory load.
        return sc.LoadJob("EXAMPLE-LJ1", "EXAMPLE-S1", "EXAMPLE-FIX-R1", 1.0, "synthetic-unit", "EXAMPLE-ENVELOPE", True, "EXAMPLE-LOAD", True)

    def loaded(self):
        return sc.qualitative_load_candidate(self.mounted("corner"), self.load_job())

    def unloaded(self, state=None):
        return sc.remove_load_candidate(state or self.mounted(), evidence_id="EXAMPLE-REMOVE", fixture_revision="EXAMPLE-FIX-R1", removal_confirmed=True, method_id="EXAMPLE-REMOVE-METHOD", support_confirmed=True, safe_to_open=True)

    def release_evidence(self):
        return sc.ReleaseEvidence("EXAMPLE-RELEASE", "EXAMPLE-S1", "EXAMPLE-FIX-R1", "EXAMPLE-LEASE", "EXAMPLE-C1", ("EXAMPLE-A1", "EXAMPLE-A2"), True, True, "EXAMPLE-UNMOUNT", True)

    def released(self, kind="rigid_metrology"):
        state = self.loaded() if kind == "corner" else self.mounted(kind)
        return sc.release_mount_candidate(self.unloaded(state), "R22" if kind == "corner" else "R30", self.release_evidence())

    def context(self):
        return sc.MetrologyContext("EXAMPLE-FIX-R1", (sc.CameraConfig("front", "EXAMPLE-CAM-F", "EXAMPLE-LENS-F", "EXAMPLE-MR1", "EXAMPLE-CR1"), sc.CameraConfig("lateral", "EXAMPLE-CAM-L", "EXAMPLE-LENS-L", "EXAMPLE-MR1", "EXAMPLE-CR1")), (("EXAMPLE-REF1", "EXAMPLE-RR1"), ("EXAMPLE-REF2", "EXAMPLE-RR1")))

    def calibration(self):
        return sc.Calibration("EXAMPLE-CAL1", self.context(), 0, 100, "EXAMPLE-CAL-METHOD", True)

    def token_args(self):
        return dict(token_id="EXAMPLE-TOKEN1", campaign_id="EXAMPLE-CAMPAIGN1", session_id="EXAMPLE-SESSION1", lock_interval="EXAMPLE-LOCK1", now_tick=10, expires_at_tick=50, required_locks=("EXAMPLE-LOCK-A", "EXAMPLE-LOCK-B"), observed_locks=(("EXAMPLE-LOCK-A", True), ("EXAMPLE-LOCK-B", True)), required_positions=("EXAMPLE-POS-A", "EXAMPLE-POS-B"), readings=(("EXAMPLE-POS-A", 1.0), ("EXAMPLE-POS-B", 1.0)), tolerance=0.0, stability_confirmed=True)

    def tokenized(self):
        return sc.token_candidate(self.mounted(), self.calibration(), self.context(), **self.token_args())

    def pair_inputs(self):
        state, token = self.tokenized()
        context = self.context()
        def capture(identifier, camera, tick, digest):
            return sc.Capture(identifier, token.campaign_id, token.session_id, token.specimen_id, token.configuration_revision, token.lock_interval, token.token_id, token.calibration_id, camera, context.reference_revisions, context.fixture_revision, tick, digest, True)
        front = capture("EXAMPLE-CAP-F", context.cameras[0], 11, "a" * 64)
        lateral = capture("EXAMPLE-CAP-L", context.cameras[1], 12, "b" * 64)
        receipts = (sc.FileReceipt(front.capture_id, front.file_sha256), sc.FileReceipt(lateral.capture_id, lateral.file_sha256))
        return state, token, self.calibration(), context, front, lateral, receipts

    def hold(self, code, function, *args, **kwargs):
        with self.assertRaises(sc.SemanticHold) as caught:
            function(*args, **kwargs)
        self.assertEqual(code, caught.exception.code)

    def fabricate(self, state, q, **changes):
        args = dict(job_id="EXAMPLE-J1", input_stock_id=state.stock_id, output_specimen_id=state.specimen_id, receipt_id="EXAMPLE-FAB1", safe_release=True)
        args.update(changes)
        return sc.fabricate_candidate(state, q, **args)

    def test_registry_preserves_31_operations_12_assets_seven_routes(self):
        self.assertEqual(sc.OPERATION_IDS, tuple(f"R{i:02d}" for i in range(31)))
        self.assertEqual(sc.ASSET_IDS, tuple(f"A{i:02d}" for i in range(1, 13)))
        self.assertEqual(sc.ROUTE_FAMILIES, ("CS1", "CS2", "CS3", "CS4", "PP_PREP", "PP_RIGID", "PP_SHEAR"))

    def test_initial_state_all_seven_routes(self):
        for route in sc.ROUTE_FAMILIES:
            with self.subTest(route=route):
                state = self.stock(route)
                self.assertEqual(state.route_id, route)
                self.assertEqual(state.family_id, route if route.startswith("CS") else "PP")

    def test_unknown_route_held(self):
        self.hold("unknown_route", self.stock, "UNKNOWN")

    def test_frozen_state(self):
        with self.assertRaises(FrozenInstanceError):
            self.stock().phase = "folded"

    def test_unknown_stock_or_drawing_qualification_blocks_fabrication(self):
        for field in ("stock_qualified", "drawing_qualified"):
            for value in (None, False):
                with self.subTest(field=field, value=value):
                    self.hold("qualification_unknown", self.fabricate, self.stock(), replace(self.qualification(), **{field: value}))

    def test_unknown_service_blocks_fabrication(self):
        self.hold("service_unknown", self.fabricate, self.stock(), replace(self.qualification(), service_qualified=None))

    def test_unknown_drawing_identity_blocks_fabrication(self):
        self.hold("drawing_unknown", self.fabricate, self.stock(), replace(self.qualification(), drawing_revision=None))

    def test_unknown_fold_plan_blocks_fabrication_and_folding(self):
        q = replace(self.qualification(), fold_plan=())
        self.hold("fold_plan_unknown", self.fabricate, self.stock(), q)
        self.hold("fold_plan_unknown", sc.record_edge_candidate, self.prepared(), q, self.edge())

    def test_unknown_fold_qualification_blocks_folding(self):
        self.hold("fold_plan_unknown", sc.record_edge_candidate, self.prepared(), replace(self.qualification(), fold_qualified=None), self.edge())

    def test_c01_both_source_readings_held_without_resolution(self):
        self.assertEqual(sc.C01_SOURCE_READINGS_MM, (383.63, 383.65))
        for dimension in sc.C01_SOURCE_READINGS_MM:
            with self.subTest(dimension=dimension):
                q = replace(self.qualification(), dimensional_basis=None, dimensional_spec_revision=None, sheet_dimension_mm=dimension)
                self.hold("C01_unresolved", self.fabricate, self.stock(), q)

    def test_c01_resolution_needs_revision_and_dimension(self):
        self.hold("C01_unresolved", self.fabricate, self.stock(), replace(self.qualification(), dimensional_spec_revision=None))
        for bad in (None, float("nan"), float("inf"), -1, True):
            with self.subTest(dimension=bad):
                self.hold("dimension_unknown", self.fabricate, self.stock(), replace(self.qualification(), sheet_dimension_mm=bad))

    def test_explicit_authored_dimension_is_record_example_only(self):
        state = self.prepared()
        self.assertEqual(state.phase, "prepared")
        self.assertIn("no physical proof", sc.CLAIM)

    def test_fabrication_does_not_fabricate_edge_completion(self):
        state = self.prepared()
        self.assertEqual(state.edge_records, ())
        self.hold("fold_incomplete", sc.finish_folding_candidate, state, self.qualification(), final_inspection_id="EXAMPLE-FINAL")

    def test_service_receipt_does_not_stand_in_for_prepared_inspection(self):
        state = self.fabricate(self.stock(), self.qualification())
        self.assertEqual(state.phase, "processed")
        self.hold("fold_phase", sc.record_edge_candidate, state, self.qualification(), self.edge())
        self.hold("transport_support", sc.transport_candidate, state, source=state.station, destination="folding", carrier_id=state.carrier_id, custody_receipt_id="EXAMPLE-TRANSFER")

    def test_prepared_inspection_requires_lineage_findings_and_inventory(self):
        state = self.fabricate(self.stock(), self.qualification())
        args = dict(evidence_id="EXAMPLE-INSPECT", output_specimen_id=state.specimen_id, parent_stock_id=state.stock_id, findings=tuple((key, True) for key in ("cut_boundary", "vertex_relief", "crease_map", "sheet_condition")), tools_accounted=True)
        self.hold("inspection_lineage", sc.inspect_prepared_candidate, state, **{**args, "parent_stock_id": "WRONG"})
        self.hold("inspection_failed", sc.inspect_prepared_candidate, state, **{**args, "findings": ()})
        self.hold("inspection_inventory", sc.inspect_prepared_candidate, state, **{**args, "tools_accounted": None})

    def test_fabrication_lineage_mismatch_and_safe_release_hold(self):
        self.hold("fabrication_lineage", self.fabricate, self.stock(), self.qualification(), input_stock_id="WRONG")
        self.hold("fabrication_release", self.fabricate, self.stock(), self.qualification(), safe_release=None)

    def test_fold_dependency_requires_observed_predecessor(self):
        self.hold("edge_dependency", sc.record_edge_candidate, self.prepared(), self.qualification(), self.edge("EXAMPLE-E2"))

    def test_fold_plan_rejects_cycles_and_missing_contacts(self):
        q = replace(self.qualification(), fold_plan=(sc.EdgePlan("EXAMPLE-E1", ("EXAMPLE-E1",), "PATCH", "MOTION"),))
        self.hold("fold_plan_order", self.fabricate, self.stock(), q)
        q = replace(self.qualification(), fold_plan=(sc.EdgePlan("EXAMPLE-E1"),))
        self.hold("fold_limits_unknown", self.fabricate, self.stock(), q)

    def test_each_edge_needs_before_after_and_disengagement(self):
        for field, value, code in (("before_observation_id", "", "edge_evidence"), ("after_observation_id", "", "edge_evidence"), ("tool_disengaged", None, "fold_support"), ("support_confirmed", None, "fold_support")):
            with self.subTest(field=field):
                self.hold(code, sc.record_edge_candidate, self.prepared(), self.qualification(), replace(self.edge(), **{field: value}))

    def test_incomplete_edge_set_cannot_be_finished(self):
        state = sc.record_edge_candidate(self.prepared(), self.qualification(), self.edge())
        self.hold("fold_incomplete", sc.finish_folding_candidate, state, self.qualification(), final_inspection_id="EXAMPLE-FINAL")

    def test_latest_failed_edge_is_not_overridden_by_historical_pass(self):
        state = self.prepared()
        for obs in (self.edge(), self.edge("EXAMPLE-E2"), self.edge("EXAMPLE-E2", "failed", "EXAMPLE-RETRY-FAIL")):
            state = sc.record_edge_candidate(state, self.qualification(), obs)
        self.hold("fold_incomplete", sc.finish_folding_candidate, state, self.qualification(), final_inspection_id="EXAMPLE-FINAL")
        self.assertEqual(len(state.edge_records), 3)

    def test_shortened_plan_cannot_fabricate_completion(self):
        state = sc.record_edge_candidate(self.prepared(), self.qualification(), self.edge())
        shortened = replace(self.qualification(), fold_plan=self.qualification().fold_plan[:1])
        self.hold("fold_plan_changed", sc.finish_folding_candidate, state, shortened, final_inspection_id="EXAMPLE-FINAL")

    def test_successful_fold_is_immutable_and_per_edge(self):
        original = self.prepared()
        folded = self.folded()
        self.assertEqual(original.edge_records, ())
        self.assertEqual(folded.phase, "folded")
        self.assertEqual(tuple(o.edge_id for o in folded.edge_records), ("EXAMPLE-E1", "EXAMPLE-E2"))

    def test_transport_rejects_mounted_loaded_and_unknown_load(self):
        args = dict(source="stock", destination="inspection", carrier_id="EXAMPLE-C1", custody_receipt_id="EXAMPLE-TRANSFER")
        self.hold("transport_mounted", sc.transport_candidate, self.mounted(), **args)
        for load in ("present", "unknown"):
            self.hold("transport_loaded", sc.transport_candidate, replace(self.baseline(), load_state=load), **args)

    def test_transport_rejects_wrong_carrier_and_source(self):
        self.hold("transport_custody", sc.transport_candidate, self.baseline(), source="wrong", destination="inspection", carrier_id="EXAMPLE-C1", custody_receipt_id="EXAMPLE-TRANSFER")
        self.hold("transport_custody", sc.transport_candidate, self.baseline(), source="stock", destination="inspection", carrier_id="wrong", custody_receipt_id="EXAMPLE-TRANSFER")

    def test_transport_requires_carrier_retention_and_disengaged_tools(self):
        args = dict(source="stock", destination="inspection", carrier_id="EXAMPLE-C1", custody_receipt_id="EXAMPLE-TRANSFER")
        for changes in ({"carrier_retained": False}, {"supported": False}, {"tools_engaged": ("EXAMPLE-TOOL",)}):
            self.hold("transport_support", sc.transport_candidate, replace(self.baseline(), **changes), **args)

    def test_transport_after_release_retains_lineage(self):
        state = self.released()
        moved = sc.transport_candidate(state, source=state.station, destination="inspection", carrier_id=state.carrier_id, custody_receipt_id="EXAMPLE-TRANSFER")
        self.assertEqual(moved.specimen_id, state.specimen_id)
        self.assertEqual(moved.station, "inspection")
        self.assertTrue(sc.check_append_only(state, moved))

    def test_unknown_load_magnitude_blocks_qualitative_loading(self):
        for magnitude in (None, float("nan"), float("inf"), -1, 0, True):
            with self.subTest(magnitude=magnitude):
                self.hold("load_magnitude_unknown", sc.qualitative_load_candidate, self.mounted("corner"), replace(self.load_job(), magnitude=magnitude))

    def test_qualitative_loading_requires_controller_guard_envelope(self):
        for changes in ({"controller_receipt_id": None}, {"qualified": None}, {"guard_closed": None}, {"envelope_id": None}):
            self.hold("load_unqualified", sc.qualitative_load_candidate, self.mounted("corner"), replace(self.load_job(), **changes))

    def test_mount_attachment_ids_are_nonempty_and_typed(self):
        mount = self.mounted().mount
        for attachments in (("",), ("  ",), (None,), (1,), ["EXAMPLE-A1"]):
            with self.subTest(attachments=attachments):
                self.hold("mount_identity", sc.mount_candidate, self.baseline(), replace(mount, attachment_ids=attachments), evidence_id="EXAMPLE-NEW-MOUNT", interface_qualified=True)

    def test_corner_mount_and_load_require_nonempty_job_identity(self):
        mount = self.mounted("corner").mount
        for job_id in (None, "", "  ", 1):
            with self.subTest(job_id=job_id):
                self.hold("mount_job_unknown", sc.mount_candidate, self.baseline(), replace(mount, job_id=job_id), evidence_id="EXAMPLE-NEW-MOUNT", interface_qualified=True)
                state = replace(self.mounted("corner"), mount=replace(mount, job_id=job_id))
                self.hold("load_binding", sc.qualitative_load_candidate, state, replace(self.load_job(), job_id=job_id))

    def test_prepared_specification_and_qualification_lineage_cannot_change(self):
        state = self.prepared()
        for change in ({"dimensional_spec_revision": "CHANGED"}, {"sheet_dimension_mm": 800.0}, {"dimensional_basis": "reconciled_drawing"}):
            self.hold("dimensional_spec_changed", sc.record_edge_candidate, state, replace(self.qualification(), **change), self.edge())
        self.hold("qualification_changed", sc.record_edge_candidate, state, replace(self.qualification(), evidence_id="CHANGED"), self.edge())

    def test_support_and_retention_require_literal_true(self):
        for value in ("unknown", "false", 1, None, False):
            for field in ("supported", "carrier_retained"):
                self.hold("transport_support", sc.transport_candidate, replace(self.baseline(), **{field: value}), source="stock", destination="inspection", carrier_id="EXAMPLE-C1", custody_receipt_id="EXAMPLE-TRANSFER")
            self.hold("fold_support", sc.record_edge_candidate, replace(self.prepared(), supported=value), self.qualification(), self.edge())
            self.hold("mount_unqualified", sc.mount_candidate, replace(self.baseline(), supported=value), self.mounted().mount, evidence_id="EXAMPLE-NEW-MOUNT", interface_qualified=True)
            self.hold("load_baseline", sc.qualitative_load_candidate, replace(self.mounted("corner"), supported=value), self.load_job())
            self.hold("closeout_custody", self.closeout, replace(self.released(), station="storage", supported=value))

    def test_loading_rejects_wrong_fixture_and_binding(self):
        self.hold("load_fixture", sc.qualitative_load_candidate, self.mounted(), self.load_job())
        self.hold("load_binding", sc.qualitative_load_candidate, self.mounted("corner"), replace(self.load_job(), fixture_revision="WRONG"))

    def test_load_removal_requires_explicit_evidence(self):
        args = dict(evidence_id="EXAMPLE-REMOVE", fixture_revision="EXAMPLE-FIX-R1", removal_confirmed=True, method_id="EXAMPLE-METHOD", support_confirmed=True, safe_to_open=True)
        for field, value in (("removal_confirmed", None), ("support_confirmed", False), ("safe_to_open", None), ("method_id", None)):
            self.hold("load_removal_unknown", sc.remove_load_candidate, self.loaded(), **{**args, field: value})

    def test_load_removal_invalidates_token_and_retains_history(self):
        state = replace(self.loaded(), active_capture_token_id="EXAMPLE-TOKEN")
        new = self.unloaded(state)
        self.assertIsNone(new.active_capture_token_id)
        self.assertEqual(new.load_state, "removed")
        self.assertTrue(sc.check_append_only(state, new))

    def test_release_before_load_removal_held_even_nominally_unloaded(self):
        self.hold("release_before_unload", sc.release_mount_candidate, self.mounted(), "R30", self.release_evidence())
        self.hold("release_before_unload", sc.release_mount_candidate, self.loaded(), "R22", self.release_evidence())

    def test_rigid_and_corner_release_routes_are_distinct(self):
        self.hold("wrong_release_route", sc.release_mount_candidate, self.unloaded(), "R22", self.release_evidence())
        self.hold("wrong_release_route", sc.release_mount_candidate, self.unloaded(self.loaded()), "R30", self.release_evidence())
        self.assertIsNone(self.released().mount)
        self.assertIsNone(self.released("corner").mount)
        self.assertIsNone(self.released("rigid_demo").mount)

    def test_release_must_confirm_every_attachment(self):
        self.hold("attachment_uncertain", sc.release_mount_candidate, self.unloaded(), "R30", replace(self.release_evidence(), detached_attachment_ids=("EXAMPLE-A1",)))

    def test_release_requires_exact_lease_and_fixture_empty(self):
        self.hold("release_binding", sc.release_mount_candidate, self.unloaded(), "R30", replace(self.release_evidence(), lease_id="WRONG"))
        self.hold("release_support", sc.release_mount_candidate, self.unloaded(), "R30", replace(self.release_evidence(), fixture_empty=None))

    def test_corner_release_requires_job_termination_and_hardware_inventory(self):
        self.hold("corner_hardware", sc.release_mount_candidate, self.unloaded(self.mounted("corner")), "R22", self.release_evidence())
        self.hold("corner_hardware", sc.release_mount_candidate, self.unloaded(self.loaded()), "R22", replace(self.release_evidence(), hardware_accounted=None))

    def test_second_release_not_required_or_permitted(self):
        self.hold("release_unmounted", sc.release_mount_candidate, self.released("corner"), "R30", self.release_evidence())

    def test_camera_lens_mount_config_fixture_reference_revision_invalidates_calibration(self):
        context = self.context()
        variants = [replace(context, fixture_revision="NEW"), replace(context, reference_revisions=(("EXAMPLE-REF1", "NEW"), context.reference_revisions[1]))]
        for field in ("camera_id", "lens_id", "mount_revision", "configuration_revision"):
            variants.append(replace(context, cameras=(replace(context.cameras[0], **{field: "NEW"}), context.cameras[1])))
        for new_context in variants:
            with self.subTest(context=new_context):
                self.hold("calibration_revision_changed", sc.check_calibration, self.calibration(), new_context, 12)

    def test_expired_unknown_and_backfilled_calibration_rejected(self):
        self.hold("calibration_expired", sc.check_calibration, self.calibration(), self.context(), 100)
        self.hold("calibration_expired", sc.check_calibration, self.calibration(), self.context(), -1)
        self.hold("calibration_unknown", sc.check_calibration, replace(self.calibration(), qualified=None), self.context(), 12)

    def test_duplicate_camera_or_reference_cannot_be_calibrated(self):
        context = self.context()
        bad = replace(context, cameras=(context.cameras[0], replace(context.cameras[1], camera_id=context.cameras[0].camera_id)))
        self.hold("camera_views", sc.check_calibration, replace(self.calibration(), context=bad), bad, 12)
        bad = replace(context, reference_revisions=(context.reference_revisions[0], context.reference_revisions[0]))
        self.hold("references_unknown", sc.check_calibration, replace(self.calibration(), context=bad), bad, 12)

    def test_two_registered_cameras_require_two_physical_lens_ids(self):
        context = self.context()
        context = replace(context, cameras=(context.cameras[0], replace(context.cameras[1], lens_id=context.cameras[0].lens_id)))
        self.hold("lens_identity", sc.check_calibration, replace(self.calibration(), context=context), context, 12)

    def test_r15_rejects_corner_loaded_corner_and_rigid_demo_mounts(self):
        for state in (self.mounted("corner"), self.loaded(), self.mounted("rigid_demo")):
            self.hold("token_mount", sc.token_candidate, state, self.calibration(), self.context(), **self.token_args())

    def test_r15_requires_literal_support_unloaded_state_and_known_tools(self):
        for change in ({"supported": "unknown"}, {"load_state": "present"}, {"load_state": "unknown"}, {"tools_engaged": None}):
            self.hold("token_state", sc.token_candidate, replace(self.mounted(), **change), self.calibration(), self.context(), **self.token_args())

    def test_unknown_locks_stability_tolerance_or_positions_block_token(self):
        cases = (({"tolerance": None}, "uniformity_unknown"), ({"stability_confirmed": None}, "uniformity_failed"), ({"observed_locks": (("EXAMPLE-LOCK-A", True), ("EXAMPLE-LOCK-B", None))}, "locks_unknown"), ({"readings": (("EXAMPLE-POS-A", 1.0),)}, "uniformity_positions"))
        for changes, code in cases:
            self.hold(code, sc.token_candidate, self.mounted(), self.calibration(), self.context(), **{**self.token_args(), **changes})

    def test_token_lifetime_cannot_outlive_calibration(self):
        self.hold("token_expiry", sc.token_candidate, self.mounted(), self.calibration(), self.context(), **{**self.token_args(), "expires_at_tick": 101})

    def test_valid_synthetic_pair_preserves_two_original_hashes(self):
        pair = sc.pair_candidate(*self.pair_inputs(), now_tick=13)
        self.assertEqual(pair.original_hashes, ("a" * 64, "b" * 64))
        self.assertEqual(len(pair.pair_sha256), 64)
        self.assertIn("no physical proof", pair.claim)

    def test_pair_scope_token_specimen_configuration_session_and_lock_mismatch(self):
        for field in ("campaign_id", "session_id", "specimen_id", "configuration_revision", "lock_interval", "token_id", "calibration_id"):
            args = list(self.pair_inputs())
            args[5] = replace(args[5], **{field: "WRONG"})
            with self.subTest(field=field):
                self.hold("pair_scope_mismatch", sc.pair_candidate, *args, now_tick=13)

    def test_pair_wrong_camera_lens_or_reference_revision_held(self):
        for change in ("camera", "lens", "reference", "fixture"):
            args = list(self.pair_inputs())
            capture = args[5]
            if change in ("camera", "lens"):
                capture = replace(capture, camera=replace(capture.camera, **{"camera_id" if change == "camera" else "lens_id": "WRONG"}))
            elif change == "reference":
                capture = replace(capture, reference_revisions=(("WRONG", "WRONG"),))
            else:
                capture = replace(capture, fixture_revision="WRONG")
            args[5] = capture
            self.hold("pair_revision_mismatch", sc.pair_candidate, *args, now_tick=13)

    def test_pair_each_hash_must_match_original_receipt(self):
        args = list(self.pair_inputs())
        args[5] = replace(args[5], file_sha256="c" * 64)
        self.hold("capture_hash_mismatch", sc.pair_candidate, *args, now_tick=13)
        args = list(self.pair_inputs())
        args[4] = replace(args[4], file_sha256="not-a-sha256")
        self.hold("capture_hash_mismatch", sc.pair_candidate, *args, now_tick=13)

    def test_pair_views_must_be_distinct(self):
        args = list(self.pair_inputs())
        args[5] = replace(args[5], camera=args[4].camera)
        self.hold("pair_views", sc.pair_candidate, *args, now_tick=13)

    def test_one_image_cannot_supply_both_views(self):
        args = list(self.pair_inputs())
        args[5] = replace(args[5], file_sha256=args[4].file_sha256)
        args[6] = (args[6][0], sc.FileReceipt(args[5].capture_id, args[4].file_sha256))
        self.hold("duplicate_image", sc.pair_candidate, *args, now_tick=13)

    def test_capture_after_token_expiry_or_future_rejected(self):
        args = list(self.pair_inputs())
        args[5] = replace(args[5], timestamp_tick=51)
        self.hold("capture_outside_interval", sc.pair_candidate, *args, now_tick=13)
        self.hold("token_expired", sc.pair_candidate, *self.pair_inputs(), now_tick=50)

    def test_pair_rejects_backfilled_calibration_interval(self):
        args = list(self.pair_inputs())
        args[2] = replace(args[2], valid_from_tick=12)
        self.hold("token_calibration_interval", sc.pair_candidate, *args, now_tick=13)
        args = list(self.pair_inputs())
        args[1] = replace(args[1], expires_at_tick=101)
        self.hold("token_calibration_interval", sc.pair_candidate, *args, now_tick=13)

    def test_pair_rejects_lost_mount_membership(self):
        args = list(self.pair_inputs())
        args[0] = replace(args[0], mount=None)
        self.hold("pair_mount_mismatch", sc.pair_candidate, *args, now_tick=13)

    def test_pair_rejects_substituted_corner_or_rigid_demo_mount_kind(self):
        for kind in ("corner", "rigid_demo"):
            args = list(self.pair_inputs())
            args[0] = replace(args[0], mount=replace(args[0].mount, kind=kind))
            self.hold("pair_mount_mismatch", sc.pair_candidate, *args, now_tick=13)

    def test_stale_token_cannot_seal_new_configuration_or_specimen(self):
        for changes in ({"configuration_revision": "NEW"}, {"specimen_id": "NEW"}, {"active_capture_token_id": None}):
            args = list(self.pair_inputs())
            args[0] = replace(args[0], **changes)
            self.hold("token_stale", sc.pair_candidate, *args, now_tick=13)

    def test_reconfiguration_invalidates_token(self):
        state = self.unloaded(self.tokenized()[0])
        new = sc.configuration_candidate(state, configuration_revision="EXAMPLE-CONFIG2", evidence_id="EXAMPLE-CONFIG-EVIDENCE")
        self.assertIsNone(new.active_capture_token_id)
        self.assertTrue(sc.check_append_only(state, new))

    def test_r13_rejects_each_cardstock_family_and_nonmetrology_fixture(self):
        for route in ("CS1", "CS2", "CS3", "CS4"):
            for kind in ("rigid_demo", "corner"):
                with self.subTest(route=route, kind=kind):
                    mount = replace(self.mounted("corner").mount, kind=kind)
                    state = sc.mount_candidate(self.baseline(route), mount, evidence_id="EXAMPLE-CS-MOUNT", interface_qualified=True)
                    state = self.unloaded(state)
                    self.hold("configuration_scope", sc.configuration_candidate, state, configuration_revision="EXAMPLE-NEW-CONFIG", evidence_id="EXAMPLE-NEW-CONFIG-EVIDENCE")
                    self.hold("token_mount", sc.token_candidate, replace(state, configuration_revision="EXAMPLE-CONFIG1"), self.calibration(), self.context(), **self.token_args())
        self.hold("configuration_scope", sc.configuration_candidate, self.unloaded(self.loaded()), configuration_revision="EXAMPLE-NEW-CONFIG", evidence_id="EXAMPLE-NEW-CONFIG-EVIDENCE")

    def test_cardstock_cannot_enter_quantitative_scope_by_replacing_fixture_kind(self):
        for family in ("CS1", "CS2", "CS3", "CS4"):
            with self.subTest(family=family):
                state = replace(self.unloaded(), family_id=family, route_id=family)
                self.hold("configuration_scope", sc.configuration_candidate, state, configuration_revision="EXAMPLE-NEW-CONFIG", evidence_id="EXAMPLE-NEW-CONFIG-EVIDENCE")
                self.hold("token_mount", sc.token_candidate, state, self.calibration(), self.context(), **self.token_args())
                args = list(self.pair_inputs())
                args[0] = replace(args[0], family_id=family, route_id=family)
                self.hold("pair_mount_mismatch", sc.pair_candidate, *args, now_tick=13)

    def test_r27_remains_metadata_only(self):
        states = json.loads((ROOT / "states.json").read_text())
        operation = next(op for op in states["operations"] if op["id"] == "R27")
        self.assertEqual(operation["semantic_api"], [])
        self.assertEqual(operation["implementation_status"], "metadata_only_not_implemented")

    def test_baseline_cannot_be_overwritten(self):
        self.hold("baseline_overwrite", sc.append_rest_candidate, self.baseline(), evidence_id="NEW-BASE", image_id="NEW", disposition="unchanged", qualified_interval_id="EXAMPLE-INTERVAL", baseline=True)

    def test_rest_history_appends_and_changed_shape_is_not_reset(self):
        state = self.released()
        new = sc.append_rest_candidate(state, evidence_id="EXAMPLE-REST1", image_id="EXAMPLE-RI1", disposition="changed", qualified_interval_id="EXAMPLE-INTERVAL")
        self.assertEqual(len(new.rest_history), 2)
        self.assertEqual(new.baseline_evidence_id, state.baseline_evidence_id)
        self.assertEqual(new.rest_history[-1].baseline_evidence_id, state.baseline_evidence_id)
        self.assertTrue(sc.check_append_only(state, new))

    def test_damage_is_not_erased_by_unchanged_rest_observation(self):
        state = sc.append_rest_candidate(self.released(), evidence_id="EXAMPLE-DAMAGE", image_id="EXAMPLE-RI1", disposition="damaged", qualified_interval_id="EXAMPLE-INTERVAL")
        new = sc.append_rest_candidate(state, evidence_id="EXAMPLE-REST2", image_id="EXAMPLE-RI2", disposition="unchanged", qualified_interval_id="EXAMPLE-INTERVAL")
        self.assertEqual(new.damage_history, state.damage_history)
        self.assertEqual(len(new.damage_history), 1)
        self.assertTrue(sc.check_append_only(state, new))

    def test_snapshot_guard_rejects_damage_rest_edge_and_event_erasure(self):
        state = sc.append_rest_candidate(self.released(), evidence_id="EXAMPLE-DAMAGE", image_id="EXAMPLE-RI1", disposition="damaged", qualified_interval_id="EXAMPLE-INTERVAL")
        for name in ("history", "rest_history", "damage_history", "edge_records"):
            self.hold("history_erasure", sc.check_append_only, state, replace(state, **{name: ()}))

    def test_snapshot_guard_rejects_identity_baseline_and_unrecorded_changes(self):
        state = self.baseline()
        self.hold("identity_rewrite", sc.check_append_only, state, replace(state, specimen_id="NEW"))
        self.hold("revision_missing", sc.check_append_only, state, replace(state, station="NEW"))
        new = sc.transport_candidate(state, source=state.station, destination="inspection", carrier_id=state.carrier_id, custody_receipt_id="EXAMPLE-TRANSFER")
        self.hold("baseline_overwrite", sc.check_append_only, state, replace(new, baseline_evidence_id="NEW"))

    def test_snapshot_guard_rejects_preparation_rewrite(self):
        state = self.baseline()
        new = sc.transport_candidate(state, source=state.station, destination="inspection", carrier_id=state.carrier_id, custody_receipt_id="EXAMPLE-TRANSFER")
        self.hold("preparation_rewrite", sc.check_append_only, state, replace(new, fold_plan=new.fold_plan[:1]))

    def closeout(self, state=None, **changes):
        state = state or replace(self.released(), station="storage")
        args = dict(expected_tools=("EXAMPLE-TOOL", "EXAMPLE-REF"), observed_tools=("EXAMPLE-TOOL", "EXAMPLE-REF"), open_leases=(), occupied_stations=(), controls_parked=True, custody_reconciled=True)
        args.update(changes)
        return sc.closeout_candidate((state,), **args)

    def test_closeout_requires_every_tool(self):
        for tools in (("EXAMPLE-TOOL",), ("EXAMPLE-TOOL", "EXAMPLE-REF", "EXTRA"), ("EXAMPLE-TOOL", "EXAMPLE-REF", "EXAMPLE-REF")):
            self.hold("closeout_tools", self.closeout, observed_tools=tools)

    def test_closeout_requires_closed_leases(self):
        self.hold("closeout_leases", self.closeout, open_leases=("EXAMPLE-LEASE",))
        self.hold("closeout_leases", self.closeout, self.mounted())

    def test_closeout_rejects_load_occupancy_and_custody_gap(self):
        self.hold("closeout_load", self.closeout, replace(self.released(), station="storage", load_state="unknown"))
        self.hold("closeout_station", self.closeout, occupied_stations=("EXAMPLE-FIX",))
        self.hold("closeout_custody", self.closeout, custody_reconciled=None)
        self.hold("closeout_custody", self.closeout, self.released())

    def test_unknown_closeout_inventories_are_not_empty_inventories(self):
        self.hold("closeout_leases", self.closeout, open_leases=None)
        self.hold("closeout_station", self.closeout, occupied_stations=None)
        self.hold("closeout_tools", self.closeout, expected_tools=("",), observed_tools=("",))

    def test_baseline_selection_requires_boolean(self):
        self.hold("rest_kind_unknown", sc.append_rest_candidate, self.folded(), evidence_id="EXAMPLE-BASE", image_id="EXAMPLE-IMAGE", disposition="unchanged", qualified_interval_id="EXAMPLE-INTERVAL", baseline="unknown")

    def test_valid_closeout_has_semantic_only_claim(self):
        result = self.closeout()
        self.assertEqual(result["status"], "semantic_candidate_complete")
        self.assertEqual(result["claim"], sc.CLAIM)

    def test_actor_allowlist_excludes_evaluator_data_and_guard_rules(self):
        view = sc.actor_observation(self.baseline(), permitted_operation_ids=("R03",), requested_target_height=31.5)
        self.assertEqual(set(view), {"specimen_id", "stock_id", "material_batch", "family_id", "requested_route_id", "requested_target_height", "permitted_operation_ids", "current_observations", "own_history_record_ids", "limitations"})
        encoded = json.dumps(view)
        for forbidden in ("source_outcomes", "source_curve", "hidden_defect", "future_capture", "canonical_reference", "acceptance_logic", "dimensional_basis", "383.63", "383.65"):
            self.assertNotIn(forbidden, encoded)

    def test_module_contains_no_io_imports_or_calls(self):
        tree = ast.parse((ROOT / "semantic_controls.py").read_text())
        imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(imports, {"dataclasses", "hashlib", "math"})
        calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertFalse({"open", "print", "input", "exec", "eval", "__import__"} & calls)

    def test_states_metadata_preserves_identifiers_and_claim_boundary(self):
        metadata = json.loads((ROOT / "states.json").read_text())
        self.assertEqual(metadata["operation_ids"], list(sc.OPERATION_IDS))
        self.assertEqual(metadata["asset_ids"], list(sc.ASSET_IDS))
        self.assertEqual([r["id"] for r in metadata["route_families"]], list(sc.ROUTE_FAMILIES))
        self.assertEqual(metadata["counts"]["physical_specimen_families"], 5)
        self.assertFalse(metadata["actor_visible"])
        self.assertFalse(metadata["claims"]["physics_implemented"])
        self.assertFalse(metadata["claims"]["execution_authorized"])
        self.assertEqual(len(metadata["operations"]), 31)
        for operation in metadata["operations"]:
            self.assertEqual(operation["primary_anchor"], "ANCHOR." + operation["id"] + ".primary")
            self.assertEqual(operation["control_anchor"], "ANCHOR." + operation["id"] + ".control")


    def test_states_operation_asset_sets_match_binding_contract(self):
        metadata = json.loads((ROOT / "states.json").read_text())
        contract = json.loads((ROOT / "operation_binding_contract.json").read_text())
        bindings = {item["operation_id"]: item for item in contract["operations"]}
        self.assertEqual(set(bindings), set(sc.OPERATION_IDS))
        for operation in metadata["operations"]:
            with self.subTest(operation=operation["id"]):
                bound = bindings[operation["id"]]
                self.assertEqual(operation["asset_ids"], bound["asset_ids"])
                self.assertEqual(operation["primary_anchor"], bound["primary_anchor"])
                self.assertEqual(operation["control_anchor"], bound["control_anchor"])
        for asset in metadata["asset_states"]:
            expected = [item["id"] for item in metadata["operations"] if asset["id"] in item["asset_ids"]]
            self.assertEqual(asset["operation_ids"], expected)


if __name__ == "__main__":
    unittest.main()
