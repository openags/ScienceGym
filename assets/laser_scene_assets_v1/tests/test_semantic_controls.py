"""Independent local metadata guard tests; no devices or scientific fixtures."""

import ast
from dataclasses import asdict, replace
import importlib.util
from pathlib import Path
import sys
import unittest

# Load this exact sibling module, not another scene's same-named module.
MODULE_PATH = Path(__file__).resolve().parents[1] / "semantic_controls.py"
SPEC = importlib.util.spec_from_file_location("laser_scene_semantic_controls_under_test", MODULE_PATH)
controls = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = controls
SPEC.loader.exec_module(controls)
GuardError = controls.GuardError
PhysicalExecutionUnavailable = controls.PhysicalExecutionUnavailable
LaserControlFixture = controls.LaserControlFixture

SEQUENCE = (
    "register_custody", "dock", "register_alignment", "select_module",
    "register_disabled_controller", "bind_acquisition_records", "disconnect",
    "register_unloaded", "retrieve",
)


def binding():
    return dict(
        sample_id="PIC-SAMPLE-001", sample_version=1, pic_id="PIC-001",
        carrier_id="CARRIER-001", dock_id="DOCK-001",
        configuration_id="CONFIG-001", configuration_version=1,
        platform=controls.EXPERIMENTAL_PLATFORM,
    )


def record(action, *, cycle="1", dfb="DFB_1", **changes):
    data = binding()
    details = {
        "register_custody": {"custody_record_id": "CUSTODY-" + cycle},
        "dock": {"docking_record_id": "DOCKING-" + cycle},
        "register_alignment": dict(
            alignment_record_id="ALIGNMENT-" + cycle,
            external_qualification_record_id="EXTERNAL-QUALIFICATION-" + cycle,
            qualifier_id="EXTERNAL-QUALIFIER-001",
            alignment_status="externally_qualified_symbolic_claim",
        ),
        "select_module": dict(
            module_id="SEALED-" + dfb, source_dfb_id=dfb,
            source_model=controls.SOURCE_DFB_MODELS[dfb],
            seal_record_id="SEAL-" + cycle, module_status="sealed_symbolic_claim",
        ),
        "register_disabled_controller": dict(
            module_id="SEALED-" + dfb, source_dfb_id=dfb,
            controller_id="CONTROLLER-001", disabled_record_id="DISABLED-" + cycle,
            controller_status="disabled_symbolic_claim",
        ),
        "bind_acquisition_records": dict(
            module_id="SEALED-" + dfb, source_dfb_id=dfb,
            controller_id="CONTROLLER-001", run_id="RUN-" + cycle,
            record_set_id="SET-" + cycle, comb_reference_id="COMB-001",
            comb_reference_record_id="COMB-RECORD-" + cycle,
            heterodyne_receiver_id="HETERODYNE-RECEIVER-001",
            heterodyne_record_id="HETERODYNE-RECORD-" + cycle,
            fpga_id="FPGA-001", fpga_record_id="FPGA-INLOOP-RECORD-" + cycle,
            record_status="external_record_ids_only",
        ),
        "disconnect": dict(
            disconnect_record_id="DISCONNECT-" + cycle,
            disconnect_status="disconnected_symbolic_claim",
        ),
        "register_unloaded": dict(
            unload_record_id="UNLOAD-" + cycle,
            unload_status="unloaded_symbolic_claim",
        ),
        "retrieve": {"custody_return_record_id": "RETURN-" + cycle},
    }
    data.update(details[action])
    data.update(changes)
    return data


def apply(fixture, action, data=None, **options):
    data = record(action, **options) if data is None else data
    token = fixture.claim(action, data[controls.TARGET_FIELDS[action]], data)
    return getattr(fixture, action)(data, token)


def through(last_action, **options):
    fixture = LaserControlFixture("PIC-SAMPLE-001")
    for action in SEQUENCE:
        apply(fixture, action, **options)
        if action == last_action:
            return fixture
    raise AssertionError("unknown helper action")


class SemanticGuards(unittest.TestCase):
    def assert_invariants(self, snapshot):
        self.assertFalse(snapshot["claims_are_evidence"])
        self.assertFalse(snapshot["physical_execution"])
        self.assertFalse(snapshot["geometry_coupling"])
        self.assertFalse(snapshot["laser_enabled"])
        self.assertFalse(snapshot["controller_enabled"])
        self.assertFalse(snapshot["heater1_enabled"])
        self.assertFalse(snapshot["heater2_enabled"])
        self.assertEqual(snapshot["laser_energy_state"], "DISABLED")
        self.assertEqual(snapshot["controller_state"], "DISABLED")
        self.assertIsNone(snapshot["real_signals"])
        self.assertIsNone(snapshot["calibrated_data"])
        self.assertIsNone(snapshot["scientific_outputs"])
        self.assertIn("untrusted", snapshot["scope"])
        self.assertEqual(snapshot["silicon_nitride_branch"], "NUMERICAL_ONLY_NOT_SELECTABLE")

    def test_constructor_rejects_missing_or_nonstring_sample(self):
        for bad in (None, "", " ", 1, True, [], {}):
            with self.subTest(bad=bad), self.assertRaises(GuardError):
                LaserControlFixture(bad)

    def test_constructor_rejects_boolean_and_nonpositive_versions(self):
        for bad in (True, False, 0, -1, 1.0, "1", [], None):
            with self.subTest(bad=bad), self.assertRaises(GuardError):
                LaserControlFixture("PIC", bad)

    def test_initial_custody_is_identity_bound_and_disabled(self):
        fixture = LaserControlFixture("PIC-SAMPLE-001", 2)
        state = fixture.snapshot()
        self.assertEqual(state["state"], "CUSTODY")
        self.assertEqual(state["sample_version"], 2)
        self.assertEqual(state["revision"], 0)
        self.assertEqual(state["records"], {})
        self.assert_invariants(state)

    def test_full_lifecycle_never_enables_energy_or_controller(self):
        fixture = LaserControlFixture("PIC-SAMPLE-001")
        self.assert_invariants(fixture.snapshot())
        expected_states = (
            "CUSTODY", "DOCKED", "ALIGNMENT_CLAIMED", "MODULE_SELECTED",
            "CONTROLLER_DISABLED_CLAIMED", "ACQUISITION_RECORDS_BOUND",
            "DISCONNECTED_CLAIMED", "UNLOADED_CLAIMED", "CUSTODY",
        )
        for revision, (action, expected) in enumerate(zip(SEQUENCE, expected_states), 1):
            state = apply(fixture, action)
            self.assertEqual(state["state"], expected)
            self.assertEqual(state["revision"], revision)
            self.assert_invariants(state)
        self.assertEqual(set(fixture.snapshot()["records"]), {"register_custody", "retrieve"})

    def test_docking_requires_registered_custody(self):
        fixture = LaserControlFixture("PIC-SAMPLE-001")
        with self.assertRaises(GuardError):
            apply(fixture, "dock")
        self.assertEqual(fixture.snapshot()["revision"], 0)

    def test_wrong_sample_identity_rejected(self):
        fixture = LaserControlFixture("PIC-SAMPLE-001")
        with self.assertRaises(GuardError):
            apply(fixture, "register_custody", record("register_custody", sample_id="OTHER"))

    def test_wrong_sample_version_rejected(self):
        fixture = LaserControlFixture("PIC-SAMPLE-001")
        with self.assertRaises(GuardError):
            apply(fixture, "register_custody", record("register_custody", sample_version=2))

    def test_every_missing_custody_field_rejected(self):
        for key in record("register_custody"):
            data = record("register_custody")
            del data[key]
            fixture = LaserControlFixture("PIC-SAMPLE-001")
            with self.subTest(key=key), self.assertRaises(GuardError):
                fixture.claim("register_custody", "CARRIER-001", data)

    def test_extra_fields_cannot_smuggle_signal_or_pid_data(self):
        for key, value in (("signal", "trace"), ("pid_gain", 1), ("laser_enabled", "true"), ("PSD", "result")):
            fixture = LaserControlFixture("PIC-SAMPLE-001")
            data = record("register_custody")
            data[key] = value
            with self.subTest(key=key), self.assertRaises(GuardError):
                apply(fixture, "register_custody", data)

    def test_every_custody_scalar_type_is_strict(self):
        for key in record("register_custody"):
            for bad in (True, [], {}, None, " "):
                data = record("register_custody")
                data[key] = bad
                fixture = LaserControlFixture("PIC-SAMPLE-001")
                with self.subTest(key=key, bad=bad), self.assertRaises(GuardError):
                    fixture.claim("register_custody", "CARRIER-001", data)

    def test_configuration_version_rejects_bool_float_zero(self):
        for bad in (True, 1.0, 0, -1, "1"):
            fixture = LaserControlFixture("PIC-SAMPLE-001")
            with self.subTest(bad=bad), self.assertRaises(GuardError):
                apply(fixture, "register_custody", record("register_custody", configuration_version=bad))

    def test_non_dict_records_rejected(self):
        fixture = LaserControlFixture("PIC-SAMPLE-001")
        for bad in (None, [], "record", True):
            with self.subTest(bad=bad), self.assertRaises(GuardError):
                fixture.claim("register_custody", "CARRIER-001", bad)

    def test_sin_and_unknown_platforms_never_become_selectable(self):
        for bad in ("SiN", "silicon_nitride", "NUMERICAL_ONLY_NOT_SELECTABLE", "simulated", "unknown"):
            fixture = LaserControlFixture("PIC-SAMPLE-001")
            with self.subTest(bad=bad), self.assertRaises(GuardError):
                apply(fixture, "register_custody", record("register_custody", platform=bad))

    def test_three_source_dfb_identities_are_distinct_and_exact(self):
        expected = {
            "DFB_1": "AeroDiode 1550LD-2-0-0-1",
            "DFB_2": "Gooch & Housego-AA1401",
            "DFB_3": "AeroDiode 1550LD-6-0-0-1",
        }
        self.assertEqual(dict(controls.SOURCE_DFB_MODELS), expected)
        for identity, model in expected.items():
            fixture = through("bind_acquisition_records", dfb=identity)
            module = fixture.acquisition_manifest()["module"]
            self.assertEqual(module["source_dfb_id"], identity)
            self.assertEqual(module["source_model"], model)

    def test_source_catalog_is_not_mutable(self):
        with self.assertRaises(TypeError):
            controls.SOURCE_DFB_MODELS["DFB_1"] = "wrong"
        with self.assertRaises(TypeError):
            controls.ACTION_FIELDS["enable"] = frozenset()

    def test_source_model_cannot_be_cross_assigned(self):
        fixture = through("register_alignment")
        for bad in ("other", controls.SOURCE_DFB_MODELS["DFB_2"], controls.SOURCE_DFB_MODELS["DFB_3"]):
            with self.subTest(bad=bad), self.assertRaises(GuardError):
                apply(fixture, "select_module", record("select_module", source_model=bad))

    def test_unknown_source_dfb_identity_rejected(self):
        fixture = through("register_alignment")
        data = record("select_module")
        for bad in ("DFB", "DFB_4", "SiN", "all_three"):
            data["source_dfb_id"] = bad
            with self.subTest(bad=bad), self.assertRaises(GuardError):
                apply(fixture, "select_module", data)

    def test_custody_configuration_cannot_change_while_docked(self):
        fixture = through("dock")
        before = fixture.snapshot()
        data = record("register_custody", configuration_version=2)
        token = fixture.claim("register_custody", "CARRIER-001", data)
        with self.assertRaises(GuardError):
            fixture.register_custody(data, token)
        self.assertEqual(fixture.snapshot(), before)

    def test_all_downstream_binding_fields_must_match_custody(self):
        fixture = through("dock")
        for key in controls.BINDING_FIELDS:
            data = record("register_alignment")
            data[key] = 2 if key.endswith("version") else "OTHER"
            with self.subTest(key=key), self.assertRaises(GuardError):
                fixture.claim("register_alignment", data["pic_id"], data)

    def test_alignment_requires_external_qualification_record(self):
        fixture = through("dock")
        for field in ("external_qualification_record_id", "qualifier_id", "alignment_record_id"):
            data = record("register_alignment")
            data[field] = ""
            with self.subTest(field=field), self.assertRaises(GuardError):
                apply(fixture, "register_alignment", data)

    def test_every_disposition_requires_explicit_symbolic_status(self):
        preceding = {
            "register_alignment": "dock", "select_module": "register_alignment",
            "register_disabled_controller": "select_module",
            "bind_acquisition_records": "register_disabled_controller",
            "disconnect": "dock", "register_unloaded": "disconnect",
        }
        for action, (field, _) in controls.REQUIRED_SYMBOLS.items():
            fixture = through(preceding[action])
            for bad in ("verified", "physical", "enabled", "acknowledged", "measured"):
                data = record(action)
                data[field] = bad
                with self.subTest(action=action, bad=bad), self.assertRaises(GuardError):
                    apply(fixture, action, data)

    def test_module_selection_requires_alignment_state(self):
        fixture = through("dock")
        data = record("select_module")
        token = fixture.claim("select_module", data["module_id"], data)
        with self.assertRaises(GuardError):
            fixture.select_module(data, token)

    def test_disabled_controller_binds_selected_module_identity(self):
        fixture = through("select_module")
        for field in ("module_id", "source_dfb_id"):
            data = record("register_disabled_controller")
            data[field] = "OTHER"
            with self.subTest(field=field), self.assertRaises(GuardError):
                apply(fixture, "register_disabled_controller", data)

    def test_acquisition_binds_module_and_disabled_controller(self):
        fixture = through("register_disabled_controller")
        for field in ("module_id", "source_dfb_id", "controller_id"):
            data = record("bind_acquisition_records")
            data[field] = "OTHER"
            with self.subTest(field=field), self.assertRaises(GuardError):
                apply(fixture, "bind_acquisition_records", data)

    def test_acquisition_requires_all_comb_and_fpga_record_fields(self):
        fixture = through("register_disabled_controller")
        for key in controls.ACTION_FIELDS["bind_acquisition_records"]:
            data = record("bind_acquisition_records")
            del data[key]
            with self.subTest(key=key), self.assertRaises(GuardError):
                fixture.claim("bind_acquisition_records", "SET-1", data)

    def test_comb_heterodyne_and_fpga_records_cannot_alias(self):
        fixture = through("register_disabled_controller")
        fields = ("record_set_id", "comb_reference_record_id", "heterodyne_record_id", "fpga_record_id")
        for first in fields:
            for second in fields:
                if first == second:
                    continue
                data = record("bind_acquisition_records")
                data[first] = data[second]
                with self.subTest(first=first, second=second), self.assertRaises(GuardError):
                    apply(fixture, "bind_acquisition_records", data)

    def test_instrument_roles_cannot_alias(self):
        fixture = through("register_disabled_controller")
        fields = ("comb_reference_id", "heterodyne_receiver_id", "fpga_id")
        for first, second in ((fields[0], fields[1]), (fields[1], fields[2]), (fields[2], fields[0])):
            data = record("bind_acquisition_records")
            data[first] = data[second]
            with self.subTest(first=first), self.assertRaises(GuardError):
                apply(fixture, "bind_acquisition_records", data)

    def test_manifest_is_metadata_only_with_distinct_acquisition_roles(self):
        manifest = through("bind_acquisition_records").acquisition_manifest()
        self.assertEqual(manifest["roles"], {
            "heterodyne_record_id": "comb_reference_heterodyne", "fpga_record_id": "in_loop_error",
        })
        for field in ("laser_enabled", "controller_enabled", "heater1_enabled", "heater2_enabled", "physical_execution", "claims_are_evidence"):
            self.assertFalse(manifest[field])
        for field in ("real_signals", "calibrated_data", "scientific_outputs"):
            self.assertIsNone(manifest[field])

    def test_manifest_requires_current_complete_pair(self):
        for action in SEQUENCE:
            if action == "bind_acquisition_records":
                continue
            fixture = through(action)
            with self.subTest(action=action), self.assertRaises(GuardError):
                fixture.acquisition_manifest()

    def test_untyped_and_mapping_claims_rejected(self):
        fixture = LaserControlFixture("PIC-SAMPLE-001")
        data = record("register_custody")
        token = fixture.claim("register_custody", "CARRIER-001", data)
        for bad in (None, True, "token", {}, asdict(token)):
            with self.subTest(bad=bad), self.assertRaises(GuardError):
                fixture.register_custody(data, bad)

    def test_claims_bind_instance_even_for_identical_sample(self):
        first, second = LaserControlFixture("PIC-SAMPLE-001"), LaserControlFixture("PIC-SAMPLE-001")
        data = record("register_custody")
        token = first.claim("register_custody", "CARRIER-001", data)
        with self.assertRaises(GuardError):
            second.register_custody(data, token)

    def test_claim_is_single_use(self):
        fixture = LaserControlFixture("PIC-SAMPLE-001")
        data = record("register_custody")
        token = fixture.claim("register_custody", "CARRIER-001", data)
        fixture.register_custody(data, token)
        before = fixture.snapshot()
        with self.assertRaises(GuardError):
            fixture.register_custody(data, token)
        self.assertEqual(fixture.snapshot(), before)

    def test_unconsumed_claim_becomes_stale_when_revision_changes(self):
        fixture = LaserControlFixture("PIC-SAMPLE-001")
        data = record("register_custody")
        old = fixture.claim("register_custody", "CARRIER-001", data)
        apply(fixture, "register_custody")
        with self.assertRaises(GuardError):
            fixture.register_custody(data, old)

    def test_claim_rejects_boolean_revision_and_sample_version(self):
        fixture = through("register_custody")  # revision 1 would compare equal to True.
        data = record("register_custody")
        token = fixture.claim("register_custody", "CARRIER-001", data)
        for field in ("revision", "sample_version"):
            with self.subTest(field=field), self.assertRaises(GuardError):
                fixture.register_custody(data, replace(token, **{field: True}))

    def test_every_claim_binding_field_rejects_tampering(self):
        fixture = LaserControlFixture("PIC-SAMPLE-001")
        data = record("register_custody")
        token = fixture.claim("register_custody", "CARRIER-001", data)
        for field, value in asdict(token).items():
            altered = value + 1 if type(value) is int else "ALTERED-" + value
            with self.subTest(field=field), self.assertRaises(GuardError):
                fixture.register_custody(data, replace(token, **{field: altered}))

    def test_claims_are_frozen(self):
        fixture = LaserControlFixture("PIC-SAMPLE-001")
        data = record("register_custody")
        token = fixture.claim("register_custody", "CARRIER-001", data)
        with self.assertRaises(AttributeError):
            token.revision = 3

    def test_wrong_action_claim_rejected(self):
        fixture = through("register_custody")
        docking = record("dock")
        wrong = fixture.claim("dock", "DOCK-001", docking)
        with self.assertRaises(GuardError):
            fixture.register_custody(record("register_custody"), wrong)

    def test_target_must_match_proposed_record(self):
        fixture = LaserControlFixture("PIC-SAMPLE-001")
        with self.assertRaises(GuardError):
            fixture.claim("register_custody", "WRONG-CARRIER", record("register_custody"))

    def test_exact_payload_cannot_change_after_claim_issue(self):
        fixture = LaserControlFixture("PIC-SAMPLE-001")
        data = record("register_custody")
        token = fixture.claim("register_custody", "CARRIER-001", data)
        data["configuration_version"] = 2
        with self.assertRaises(GuardError):
            fixture.register_custody(data, token)

    def test_configuration_target_change_cannot_reuse_claim(self):
        fixture = LaserControlFixture("PIC-SAMPLE-001")
        data = record("register_custody")
        token = fixture.claim("register_custody", "CARRIER-001", data)
        data["carrier_id"] = "CARRIER-OTHER"
        with self.assertRaises(GuardError):
            fixture.register_custody(data, token)

    def test_invalid_action_and_target_types_fail_cleanly(self):
        fixture = LaserControlFixture("PIC-SAMPLE-001")
        for bad in (None, [], {}, True, "", "enable_laser", "set_pid"):
            with self.subTest(bad=bad), self.assertRaises(GuardError):
                fixture.claim(bad, "CARRIER-001", record("register_custody"))
        for bad in (None, [], {}, True, ""):
            with self.subTest(target=bad), self.assertRaises(GuardError):
                fixture.claim("register_custody", bad, record("register_custody"))

    def test_rejected_payload_is_atomic_and_does_not_consume_claim(self):
        fixture = LaserControlFixture("PIC-SAMPLE-001")
        data = record("register_custody")
        token = fixture.claim("register_custody", "CARRIER-001", data)
        before = fixture.snapshot()
        invalid = dict(data, custody_record_id="OTHER")
        with self.assertRaises(GuardError):
            fixture.register_custody(invalid, token)
        self.assertEqual(fixture.snapshot(), before)
        fixture.register_custody(data, token)
        self.assertEqual(fixture.snapshot()["revision"], 1)

    def test_input_records_are_copied(self):
        fixture = LaserControlFixture("PIC-SAMPLE-001")
        data = record("register_custody")
        apply(fixture, "register_custody", data)
        data["pic_id"] = "MUTATED"
        self.assertEqual(fixture.snapshot()["records"]["register_custody"]["pic_id"], "PIC-001")

    def test_snapshots_and_transition_returns_are_deep_copied(self):
        fixture = LaserControlFixture("PIC-SAMPLE-001")
        returned = apply(fixture, "register_custody")
        returned["records"]["register_custody"]["carrier_id"] = "MUTATED"
        snapshot = fixture.snapshot()
        snapshot["records"].clear()
        self.assertEqual(fixture.snapshot()["records"]["register_custody"]["carrier_id"], "CARRIER-001")

    def test_manifest_is_deep_copied(self):
        fixture = through("bind_acquisition_records")
        manifest = fixture.acquisition_manifest()
        manifest["module"]["module_id"] = "MUTATED"
        manifest["records"]["fpga_record_id"] = "MUTATED"
        manifest["binding"]["configuration_version"] = 99
        fresh = fixture.acquisition_manifest()
        self.assertEqual(fresh["module"]["module_id"], "SEALED-DFB_1")
        self.assertEqual(fresh["records"]["fpga_record_id"], "FPGA-INLOOP-RECORD-1")
        self.assertEqual(fresh["binding"]["configuration_version"], 1)

    def test_disconnect_can_close_every_partial_docked_cycle(self):
        for action in SEQUENCE[1:6]:
            fixture = through(action)
            with self.subTest(action=action):
                state = apply(fixture, "disconnect")
                self.assertEqual(state["state"], "DISCONNECTED_CLAIMED")
                self.assert_invariants(state)

    def test_unload_requires_disconnect_and_retrieve_requires_unload(self):
        fixture = through("bind_acquisition_records")
        with self.assertRaises(GuardError):
            apply(fixture, "register_unloaded")
        with self.assertRaises(GuardError):
            apply(fixture, "retrieve")
        apply(fixture, "disconnect")
        with self.assertRaises(GuardError):
            apply(fixture, "retrieve")
        apply(fixture, "register_unloaded")
        self.assertEqual(apply(fixture, "retrieve")["state"], "CUSTODY")

    def test_retrieval_invalidates_all_downstream_records(self):
        fixture = through("retrieve")
        self.assertEqual(set(fixture.snapshot()["records"]), {"register_custody", "retrieve"})
        apply(fixture, "dock", cycle="2")
        self.assertNotIn("retrieve", fixture.snapshot()["records"])
        for action in ("register_disabled_controller", "bind_acquisition_records"):
            with self.subTest(action=action), self.assertRaises(GuardError):
                apply(fixture, action, cycle="2")

    def test_run_ids_cannot_be_reused_across_cycles(self):
        fixture = through("retrieve")
        for action in SEQUENCE[1:5]:
            apply(fixture, action, cycle="2")
        data = record("bind_acquisition_records", cycle="2", run_id="RUN-1")
        with self.assertRaises(GuardError):
            apply(fixture, "bind_acquisition_records", data)
        self.assertEqual(apply(fixture, "bind_acquisition_records", cycle="2")["state"], "ACQUISITION_RECORDS_BOUND")

    def test_each_acquisition_record_id_cannot_be_reused_across_cycles(self):
        fixture = through("retrieve")
        for action in SEQUENCE[1:5]:
            apply(fixture, action, cycle="2")
        for key in ("record_set_id", "comb_reference_record_id", "heterodyne_record_id", "fpga_record_id"):
            data = record("bind_acquisition_records", cycle="2")
            data[key] = record("bind_acquisition_records")[key]
            with self.subTest(key=key), self.assertRaises(GuardError):
                apply(fixture, "bind_acquisition_records", data)

    def test_new_custody_configuration_explicitly_replaces_previous_binding(self):
        fixture = through("retrieve")
        data = record("register_custody", cycle="2", configuration_version=2, carrier_id="CARRIER-002")
        apply(fixture, "register_custody", data)
        self.assertEqual(set(fixture.snapshot()["records"]), {"register_custody"})
        with self.assertRaises(GuardError):
            apply(fixture, "dock", cycle="2")
        docking = record("dock", cycle="2", configuration_version=2, carrier_id="CARRIER-002")
        self.assertEqual(apply(fixture, "dock", docking)["state"], "DOCKED")

    def test_quarantine_is_terminal_and_idempotent(self):
        fixture = through("bind_acquisition_records")
        data = record("disconnect")
        token = fixture.claim("disconnect", "DOCK-001", data)
        held = fixture.quarantine()
        self.assertEqual(held["state"], "QUARANTINE")
        self.assert_invariants(held)
        self.assertEqual(fixture.quarantine(), held)
        with self.assertRaises(GuardError):
            fixture.claim("disconnect", "DOCK-001", data)
        with self.assertRaises(GuardError):
            fixture.disconnect(data, token)
        with self.assertRaises(GuardError):
            fixture.acquisition_manifest()
        self.assertEqual(fixture.snapshot(), held)

    def test_quarantine_available_in_every_state_without_physical_claim(self):
        for action in SEQUENCE:
            fixture = through(action)
            with self.subTest(action=action):
                self.assert_invariants(fixture.quarantine())

    def test_all_physical_and_scientific_requests_are_denied_atomically(self):
        fixture = through("bind_acquisition_records")
        before = fixture.snapshot()
        for operation in (
            "ENABLE_LASER", "ENABLE_HEATER1", "ENABLE_HEATER2", "SET_PID", "TUNE_CURRENT", "ALIGN_PIC", "ACQUIRE_SIGNAL",
            "MEASURE_PSD", "COMPUTE_LINEWIDTH", "CALIBRATE", "RUN_SIN_SIMULATION",
            "MOVE_BLENDER_OBJECT", "UNLOAD_HARDWARE", "DISABLE_LASER", None, True,
        ):
            with self.subTest(operation=operation), self.assertRaises(PhysicalExecutionUnavailable):
                fixture.request_physical_service(operation, "unused", payload={"signal": [1, 2]})
        self.assertEqual(fixture.snapshot(), before)

    def test_denied_service_does_not_execute_arbitrary_object_callbacks(self):
        class DangerousLabel:
            def __str__(self):
                raise AssertionError("must not call user code")

        fixture = LaserControlFixture("PIC-SAMPLE-001")
        with self.assertRaises(PhysicalExecutionUnavailable):
            fixture.request_physical_service(DangerousLabel())

    def test_no_runtime_geometry_io_or_scientific_dependencies(self):
        tree = ast.parse(MODULE_PATH.read_text())
        roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                roots.add(node.module.split(".")[0])
        self.assertEqual(roots, {"__future__", "copy", "dataclasses", "hashlib", "json", "types", "uuid"})
        self.assertFalse(any(name in vars(LaserControlFixture) for name in (
            "enable_laser", "enable_heater1", "enable_heater2", "set_pid", "acquire_signal", "move_geometry", "compute_psd",
        )))


if __name__ == "__main__":
    unittest.main()
