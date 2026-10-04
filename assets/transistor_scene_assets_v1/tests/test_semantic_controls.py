"""Local metadata guard tests. Passing never qualifies a physical scene or service."""
import copy
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semantic_controls import (  # noqa: E402
    CONFLICT_IDS, FIXTURE_AUTHORITY, FIXTURE_SCOPE, NETLISTS, STACK_IDS,
    GuardError, PhysicalServiceRejected, SceneControls, ordered_pairs,
    state_specification,
)


class StaticSemanticTests(unittest.TestCase):
    def setUp(self):
        self.count = 0
        self.scene = self.new_scene()

    @staticmethod
    def args():
        return dict(sample_id="sample_A", specimen_version=2, carrier_id="carrier_A",
                    chip_id="chip_A", pcb_id="pcb_A", cohort_id="cohort_A",
                    architecture_id="DG", stack_ids=list(STACK_IDS), retained=True)

    def new_scene(self, **updates):
        args = self.args()
        args.update(updates)
        return SceneControls(**args)

    def marker(self, kind="safe_zero", scene=None):
        scene = scene or self.scene
        self.count += 1
        return {"receipt_id": f"fixture_observation_{self.count}", "kind": kind,
                "authority": FIXTURE_AUTHORITY, "scope": FIXTURE_SCOPE,
                "binding": scene.receipt_binding(), "outcome": "fixture_" + kind}

    def observe(self, kind="safe_zero", scene=None):
        scene = scene or self.scene
        observation = self.marker(kind, scene)
        scene.record_fixture_observation(observation)
        return observation["receipt_id"]

    def mount(self):
        self.scene.mount(self.observe())

    def rewire_args(self, **updates):
        data = dict(netlist_id="ORDINARY_INVERTER_FIG4", driver_stack_id="S1",
                    load_stack_id="S2", terminal_map=dict(NETLISTS["ORDINARY_INVERTER_FIG4"]),
                    netlist_revision=self.scene.receipt_binding()["netlist_revision"] + 1,
                    safe_zero_receipt_id=self.observe())
        data.update(updates)
        return data

    def configure(self):
        self.mount()
        self.scene.rewire(**self.rewire_args())

    def continuity(self):
        self.observe()
        return self.observe("continuity")

    def assert_unchanged_failure(self, call, exc=GuardError):
        before = self.scene.snapshot()
        with self.assertRaises(exc):
            call()
        self.assertEqual(before, self.scene.snapshot())

    def test_initial_state_is_retained_unknown_unqualified(self):
        snap = self.scene.snapshot()
        self.assertEqual(snap["binding"]["custody"], "storage_retained")
        self.assertIs(snap["binding"]["retained"], True)
        self.assertTrue(all(x == "unknown" for x in snap["terminal_map"].values()))
        for field in ("physical_execution_implemented", "physical_reachability_proven",
                      "safety_qualified", "scientific_replication", "electrical_outputs_implemented"):
            self.assertIs(snap[field], False)

    def test_positive_custody_identity(self):
        self.scene.verify_custody(sample_id="sample_A", specimen_version=2,
                                  carrier_id="carrier_A", retained=True)

    def test_custody_cannot_relabel_identity(self):
        base = dict(sample_id="sample_A", specimen_version=2, carrier_id="carrier_A", retained=True)
        for key, value in (("sample_id", "sample_B"), ("specimen_version", 3),
                           ("carrier_id", "carrier_B"), ("retained", False)):
            with self.subTest(key=key):
                args = dict(base, **{key: value})
                self.assert_unchanged_failure(lambda: self.scene.verify_custody(**args))

    def test_identity_frozen_and_snapshot_detached(self):
        with self.assertRaises(FrozenInstanceError):
            self.scene.identity.specimen_version = 99
        snap = self.scene.snapshot()
        snap["identity"]["sample_id"] = "fake"
        snap["binding"]["stack_ids"].clear()
        self.assertEqual(self.scene.identity.sample_id, "sample_A")
        self.assertEqual(len(self.scene.receipt_binding()["stack_ids"]), 10)

    def test_version_type_guards(self):
        for bad in (True, False, 2.0, "2", 0, -1, None):
            with self.subTest(value=bad), self.assertRaises(GuardError):
                self.new_scene(specimen_version=bad)

    def test_custody_type_guards(self):
        for field, bad in (("sample_id", 1), ("carrier_id", None), ("retained", 1),
                           ("retained", "true"), ("specimen_version", True)):
            with self.subTest(field=field), self.assertRaises(GuardError):
                args = dict(sample_id="sample_A", specimen_version=2, carrier_id="carrier_A", retained=True)
                args[field] = bad
                self.scene.verify_custody(**args)

    def test_missing_empty_duplicate_or_invalid_stack_inventory_rejected(self):
        for stacks in (None, [], list(STACK_IDS[:-1]), ["S1"] * 10,
                       [*STACK_IDS[:-1], "S11"], [*STACK_IDS[:-1], 10], "S1,S2"):
            with self.subTest(stacks=stacks), self.assertRaises(GuardError):
                self.new_scene(stack_ids=stacks)
        args = self.args()
        del args["stack_ids"]
        with self.assertRaises(TypeError):
            SceneControls(**args)

    def test_no_release_custody_control(self):
        self.assert_unchanged_failure(lambda: self.scene.apply("release", {}), PhysicalServiceRejected)
        with self.assertRaises(GuardError):
            self.new_scene(retained=False)

    def test_deenergize_intent_does_not_prove_safe_zero(self):
        self.scene.request_deenergize()
        self.assertIsNone(self.scene.snapshot()["current_safe_zero_fixture_receipt_id"])
        self.assert_unchanged_failure(lambda: self.scene.mount("off_command"))

    def test_deenergize_invalidates_existing_observation(self):
        rid = self.observe()
        self.scene.request_deenergize()
        self.assert_unchanged_failure(lambda: self.scene.mount(rid))

    def test_mount_requires_current_independent_fixture_observation(self):
        self.assert_unchanged_failure(lambda: self.scene.mount("missing"))
        rid = self.observe()
        self.scene.mount(rid)
        self.assertEqual(self.scene.receipt_binding()["mount_revision"], 1)
        self.assertIsNone(self.scene.snapshot()["current_safe_zero_fixture_receipt_id"])

    def test_actor_dispatch_cannot_submit_observation(self):
        self.assert_unchanged_failure(
            lambda: self.scene.apply("record_fixture_observation", self.marker()), PhysicalServiceRejected)

    def test_real_or_actor_authority_rejected(self):
        for authority in ("actor", "measured_hardware", "real_independent_service", True, None):
            marker = self.marker()
            marker["authority"] = authority
            with self.subTest(authority=authority):
                self.assert_unchanged_failure(lambda: self.scene.record_fixture_observation(marker))

    def test_receipt_extra_electrical_payload_rejected(self):
        marker = self.marker()
        marker["voltage_V"] = 0
        self.assert_unchanged_failure(lambda: self.scene.record_fixture_observation(marker))

    def test_receipt_missing_and_wrong_type_fields_rejected(self):
        for key in self.marker():
            marker = self.marker()
            del marker[key]
            with self.subTest(missing=key):
                self.assert_unchanged_failure(lambda: self.scene.record_fixture_observation(marker))
        for key, bad in (("kind", True), ("scope", "hardware"), ("outcome", True),
                         ("receipt_id", 1), ("binding", [])):
            marker = self.marker()
            marker[key] = bad
            with self.subTest(field=key):
                self.assert_unchanged_failure(lambda: self.scene.record_fixture_observation(marker))

    def test_receipt_identity_version_and_retention_type_binding(self):
        for key, bad in (("sample_id", "sample_B"), ("specimen_version", 2.0),
                         ("retained", 1), ("mount_revision", False),
                         ("carrier_id", "other"), ("stack_ids", [])):
            marker = self.marker()
            marker["binding"][key] = bad
            with self.subTest(field=key):
                self.assert_unchanged_failure(lambda: self.scene.record_fixture_observation(marker))

    def test_duplicate_receipt_id_rejected(self):
        marker = self.marker()
        self.scene.record_fixture_observation(marker)
        self.assert_unchanged_failure(lambda: self.scene.record_fixture_observation(marker))

    def test_superseded_safe_zero_receipt_rejected(self):
        old = self.observe()
        new = self.observe()
        self.assert_unchanged_failure(lambda: self.scene.mount(old))
        self.scene.mount(new)

    def test_identical_lineage_other_fixture_instance_receipt_rejected(self):
        other = self.new_scene()
        self.assertNotEqual(self.scene.receipt_binding()["fixture_instance_id"],
                            other.receipt_binding()["fixture_instance_id"])
        marker = self.marker(scene=other)
        self.assert_unchanged_failure(lambda: self.scene.record_fixture_observation(marker))

    def test_stale_observation_binding_rejected(self):
        old = self.marker()
        self.mount()
        self.assert_unchanged_failure(lambda: self.scene.record_fixture_observation(old))

    def test_ordinary_fig4_mapping_explicit(self):
        self.configure()
        self.assertEqual(self.scene.terminal_state("driver_BG"), "VIN")
        self.assertEqual(self.scene.terminal_state("driver_TG"), "VIN")
        self.assertEqual(self.scene.terminal_state("load_BG"), "VDD")
        self.assertEqual(self.scene.terminal_state("load_TG"), "VOUT")

    def test_independent_s31_mapping_explicit_and_distinct(self):
        self.mount()
        self.scene.rewire(**self.rewire_args(netlist_id="INDEPENDENT_INVERTER_S31",
                           terminal_map=dict(NETLISTS["INDEPENDENT_INVERTER_S31"])))
        self.assertEqual(self.scene.terminal_state("driver_BG"), "VBG")
        self.assertEqual(self.scene.terminal_state("driver_TG"), "VTG1")
        self.assertEqual(self.scene.terminal_state("load_BG"), "VOUT")
        self.assertEqual(self.scene.terminal_state("load_TG"), "VTG2")

    def test_crossed_fig4_s31_map_rejected(self):
        self.mount()
        args = self.rewire_args(netlist_id="INDEPENDENT_INVERTER_S31")
        self.assert_unchanged_failure(lambda: self.scene.rewire(**args))

    def test_missing_unknown_floating_or_extra_terminal_rejected(self):
        self.mount()
        for value in ("unknown", "floating", None, 0):
            mapping = dict(NETLISTS["ORDINARY_INVERTER_FIG4"])
            mapping["load_TG"] = value
            args = self.rewire_args(terminal_map=mapping)
            with self.subTest(value=value):
                self.assert_unchanged_failure(lambda: self.scene.rewire(**args))
        for mode in ("missing", "extra"):
            mapping = dict(NETLISTS["ORDINARY_INVERTER_FIG4"])
            if mode == "missing":
                del mapping["load_TG"]
            else:
                mapping["spare_gate"] = "floating"
            args = self.rewire_args(terminal_map=mapping)
            self.assert_unchanged_failure(lambda: self.scene.rewire(**args))

    def test_unknown_terminal_never_inferred_floating(self):
        self.assertEqual(self.scene.terminal_state("driver_BG"), "unknown")
        with self.assertRaises(GuardError):
            self.scene.terminal_state("undeclared_terminal")

    def test_rewire_without_safe_zero_rejected(self):
        self.mount()
        args = self.rewire_args(safe_zero_receipt_id="off_command")
        self.assert_unchanged_failure(lambda: self.scene.rewire(**args))

    def test_rewire_revision_must_be_next_strict_integer(self):
        self.mount()
        for revision in (True, 1.0, "1", 0, -1, 2):
            args = self.rewire_args(netlist_revision=revision)
            with self.subTest(revision=revision):
                self.assert_unchanged_failure(lambda: self.scene.rewire(**args))

    def test_rewire_distinct_registered_stack_ids_required(self):
        self.mount()
        for driver, load in (("S1", "S1"), ("S0", "S2"), ("S1", "S11"),
                             (None, "S2"), ("S1", ""), (True, "S2")):
            args = self.rewire_args(driver_stack_id=driver, load_stack_id=load)
            with self.subTest(driver=driver, load=load):
                self.assert_unchanged_failure(lambda: self.scene.rewire(**args))
        args = self.rewire_args()
        del args["load_stack_id"]
        self.assert_unchanged_failure(lambda: self.scene.apply("rewire", args))

    def test_unmapped_parallel_and_unknown_netlists_rejected(self):
        self.mount()
        for name in ("PARALLEL_INVERTER_S30", "made_up"):
            args = self.rewire_args(netlist_id=name)
            self.assert_unchanged_failure(lambda: self.scene.rewire(**args))

    def test_rewire_invalidates_old_continuity_and_safe_zero(self):
        self.configure()
        old_continuity = self.continuity()
        args = self.rewire_args(load_stack_id="S3")
        consumed_safe = args["safe_zero_receipt_id"]
        self.scene.rewire(**args)
        self.assertIsNone(self.scene.snapshot()["current_continuity_fixture_receipt_id"])
        self.assert_unchanged_failure(lambda: self.scene.create_record(
            record_id="stale", case_id="case_A", continuity_receipt_id=old_continuity))
        self.assert_unchanged_failure(lambda: self.scene.disconnect(consumed_safe))

    def test_continuity_requires_configured_fixture_and_fresh_safe_zero(self):
        self.assert_unchanged_failure(lambda: self.scene.record_fixture_observation(self.marker("continuity")))
        self.mount()
        self.assert_unchanged_failure(lambda: self.scene.record_fixture_observation(self.marker("continuity")))
        self.scene.rewire(**self.rewire_args())
        self.assert_unchanged_failure(lambda: self.scene.record_fixture_observation(self.marker("continuity")))
        self.continuity()

    def test_continuity_ties_exact_netlist_pair_revision_and_map(self):
        self.configure()
        self.observe()
        for key, wrong in (("netlist_id", "INDEPENDENT_INVERTER_S31"),
                           ("netlist_revision", 2), ("driver_stack_id", "S2"),
                           ("load_stack_id", "S3"), ("terminal_map_hash", "wrong")):
            marker = self.marker("continuity")
            marker["binding"][key] = wrong
            with self.subTest(key=key):
                self.assert_unchanged_failure(lambda: self.scene.record_fixture_observation(marker))

    def test_continuity_rejects_missing_stack_binding(self):
        self.configure()
        self.observe()
        for key in ("stack_ids", "driver_stack_id", "load_stack_id"):
            marker = self.marker("continuity")
            del marker["binding"][key]
            self.assert_unchanged_failure(lambda: self.scene.record_fixture_observation(marker))

    def test_record_metadata_only_and_hash_stable(self):
        self.configure()
        rid = self.continuity()
        result = self.scene.create_record(record_id="record_A", case_id="case_A", continuity_receipt_id=rid)
        self.assertEqual(result["record_kind"], "fixture_metadata_only")
        self.assertIs(result["measurement_created"], False)
        self.assertEqual(result["binding"]["driver_stack_id"], "S1")
        self.assertEqual(result["binding"]["load_stack_id"], "S2")
        self.assertEqual(result["source_conflict_ids_unresolved"], list(CONFLICT_IDS))
        forbidden = {"voltage", "current", "voltage_V", "current_A", "values", "raw_columns", "electrical_results"}
        self.assertTrue(forbidden.isdisjoint(result))
        self.assertEqual(len(result["metadata_hash"]), 64)
        result["binding"]["sample_id"] = "edited"
        self.assertEqual(self.scene.snapshot()["records"][0]["binding"]["sample_id"], "sample_A")

    def test_record_cannot_accept_measurement_payload(self):
        self.configure()
        rid = self.continuity()
        self.assert_unchanged_failure(lambda: self.scene.apply("create_record", {
            "record_id": "record_A", "case_id": "case_A", "continuity_receipt_id": rid,
            "electrical_results": {"voltage_V": 0}}))

    def test_continuity_receipt_is_single_use(self):
        self.configure()
        rid = self.continuity()
        self.scene.create_record(record_id="record_A", case_id="case_A", continuity_receipt_id=rid)
        self.assert_unchanged_failure(lambda: self.scene.create_record(
            record_id="record_B", case_id="case_A", continuity_receipt_id=rid))
        fresh = self.observe("continuity")
        self.scene.create_record(record_id="record_B", case_id="case_A", continuity_receipt_id=fresh)

    def test_record_id_reuse_rejected_without_consuming_new_receipt(self):
        self.configure()
        self.scene.create_record(record_id="record_A", case_id="case_A", continuity_receipt_id=self.continuity())
        fresh = self.observe("continuity")
        self.assert_unchanged_failure(lambda: self.scene.create_record(
            record_id="record_A", case_id="case_B", continuity_receipt_id=fresh))
        self.scene.create_record(record_id="record_B", case_id="case_B", continuity_receipt_id=fresh)

    def test_safe_zero_marker_cannot_substitute_for_continuity(self):
        self.configure()
        safe = self.observe()
        self.assert_unchanged_failure(lambda: self.scene.create_record(
            record_id="record_A", case_id="case_A", continuity_receipt_id=safe))

    def test_lifecycle_preserves_identity_and_retention(self):
        initial = self.scene.snapshot()["identity"]
        self.configure()
        self.scene.disconnect(self.observe())
        self.scene.retrieve(self.observe())
        self.assertEqual(self.scene.snapshot()["identity"], initial)
        self.assertEqual(self.scene.receipt_binding()["custody"], "storage_retained")
        self.assertIs(self.scene.receipt_binding()["retained"], True)

    def test_disconnect_and_retrieve_require_new_observation(self):
        self.configure()
        safe = self.observe()
        self.scene.disconnect(safe)
        self.assert_unchanged_failure(lambda: self.scene.retrieve(safe))
        self.scene.retrieve(self.observe())

    def test_illegal_lifecycle_order_rejected(self):
        self.assert_unchanged_failure(lambda: self.scene.disconnect("missing"))
        self.assert_unchanged_failure(lambda: self.scene.retrieve("missing"))
        self.mount()
        safe = self.observe()
        self.assert_unchanged_failure(lambda: self.scene.mount(safe))
        self.assert_unchanged_failure(lambda: self.scene.retrieve(safe))

    def test_remount_invalidates_configuration_and_all_old_receipts(self):
        self.configure()
        old = self.continuity()
        self.scene.disconnect(self.observe())
        self.scene.retrieve(self.observe())
        self.scene.mount(self.observe())
        self.assertEqual(self.scene.receipt_binding()["mount_revision"], 2)
        self.assertIsNone(self.scene.receipt_binding()["netlist_id"])
        self.assertEqual(self.scene.terminal_state("driver_BG"), "unknown")
        self.assert_unchanged_failure(lambda: self.scene.create_record(
            record_id="stale", case_id="case_A", continuity_receipt_id=old))

    def test_all_ten_conflicts_remain_unresolved_after_acknowledgement(self):
        for conflict in CONFLICT_IDS:
            result = self.scene.acknowledge_conflict(conflict, "ack_" + conflict)
            self.assertIs(result["resolved"], False)
            self.assertIs(result["qualification_gate"], True)
        conflicts = self.scene.snapshot()["source_conflicts"]
        self.assertEqual(len(conflicts), 10)
        self.assertTrue(all(c["fixture_acknowledged"] and not c["resolved"] for c in conflicts))
        self.assertTrue(all(c["qualification_gate"] for c in conflicts))

    def test_conflict_cannot_be_resolved_by_actor_or_receipt(self):
        self.assert_unchanged_failure(lambda: self.scene.apply("resolve_conflict", {"id": "C01"}), PhysicalServiceRejected)
        self.assert_unchanged_failure(lambda: self.scene.apply("acknowledge_conflict", {
            "conflict_id": "C01", "acknowledgement_id": "ack_A", "resolved": True}))
        for bad in ("C00", "C11", 1):
            self.assert_unchanged_failure(lambda: self.scene.acknowledge_conflict(bad, "ack_A"))

    def test_all_physical_services_always_rejected_even_after_acknowledgements(self):
        for conflict in CONFLICT_IDS:
            self.scene.acknowledge_conflict(conflict, "ack_" + conflict)
        for service in ("set_voltage", "set_current", "ACQUIRE", "VTC", "SUPPLY_CURRENT",
                        "THERMAL_SERVICE", "COOLDOWN", "LAYER_SERVICE", "DIELECTRIC_SERVICE",
                        "BOND_SERVICE", "wirebond", "fabrication", "physical_move",
                        "CONTINUITY_CHECK", "COMPUTE_GAIN", "COMPUTE_RATIO", "unknown"):
            with self.subTest(service=service):
                self.assert_unchanged_failure(lambda: self.scene.request_service(
                    service, fixture_only=True, approved=True), PhysicalServiceRejected)
                self.assert_unchanged_failure(lambda: self.scene.apply(service, {}), PhysicalServiceRejected)

    def test_dispatch_strict_types_and_extra_fields(self):
        for action in (True, [], None, ""):
            self.assert_unchanged_failure(lambda: self.scene.apply(action, {}))
        for payload in ([], True, {"safe": True}):
            self.assert_unchanged_failure(lambda: self.scene.apply("request_deenergize", payload))

    def test_dispatch_positive_path(self):
        self.scene.apply("request_deenergize")
        self.scene.apply("mount", {"safe_zero_receipt_id": self.observe()})
        self.scene.apply("rewire", self.rewire_args())
        self.scene.apply("create_record", {"record_id": "record_A", "case_id": "case_A",
                                            "continuity_receipt_id": self.continuity()})
        self.scene.apply("disconnect", {"safe_zero_receipt_id": self.observe()})
        self.scene.apply("retrieve", {"safe_zero_receipt_id": self.observe()})

    def test_90_ordered_pairs_keep_driver_and_load_distinct(self):
        pairs = ordered_pairs()
        self.assertEqual(len(pairs), 90)
        self.assertEqual(len({p["pair_id"] for p in pairs}), 90)
        self.assertTrue(all(p["driver_stack_id"] != p["load_stack_id"] for p in pairs))
        identities = {(p["driver_stack_id"], p["load_stack_id"]) for p in pairs}
        self.assertIn(("S1", "S2"), identities)
        self.assertIn(("S2", "S1"), identities)
        self.assertEqual(len(identities), 90)

    def test_specification_matches_implementation_and_conflicts(self):
        spec = state_specification()
        self.assertEqual(spec["netlists"], {k: dict(v) for k, v in NETLISTS.items()})
        self.assertEqual(spec["identity"]["registered_stack_ids"], list(STACK_IDS))
        self.assertEqual(spec["identity"]["ordered_pair_count"], 90)
        ledger = spec["source_conflicts"]
        self.assertIs(ledger["automatic_correction_allowed"], False)
        self.assertEqual([c["id"] for c in ledger["conflicts"]], list(CONFLICT_IDS))
        self.assertTrue(all(c["resolved"] is False and c["qualification_gate"] is True
                            for c in ledger["conflicts"]))
        self.assertTrue(all(c["source_difference"] and c["required_handling"]
                            for c in ledger["conflicts"]))
        self.assertTrue(all(value is False for value in spec["claims"].values()))
        self.assertEqual(json.loads(json.dumps(spec)), spec)


if __name__ == "__main__":
    unittest.main()
