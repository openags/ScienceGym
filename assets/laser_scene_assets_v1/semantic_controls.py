"""Caller-owned, nonphysical laser-scene metadata controls.

This module is an original local state machine, not laboratory control software.
It neither imports Blender nor addresses a device, file, network, actuator or
signal. Every state describes a caller's symbolic claim. A record ID is an
unverified label: it does not establish alignment, custody, qualification,
calibration, acquisition, interlocks, safety, or a scientific result. Issuing a
Claim is not authentication and its hashes are not signatures or evidence.
Python callers own this object; it is not a security boundary against a caller
who edits private attributes or executable code.

API
---
Create ``LaserControlFixture(sample_id, sample_version=1)``. Each record is an
exact plain dict containing BINDING_FIELDS plus ACTION_FIELDS[action]. All
values are nonempty strings except the two positive integer version fields;
booleans are never integers here. For every action, first call
``claim(action, target_id, record)`` and pass that Claim and the unchanged
record to the identically named method. TARGET_FIELDS defines each target.
The claim binds the instance, current revision, sample/version, entire active
context, action, target and exact record payload. Failed actions are atomic.
Only successfully consumed, locally issued claims change the metadata state.

Normal sequence: register_custody, dock, register_alignment, select_module,
register_disabled_controller, bind_acquisition_records, disconnect,
register_unloaded, retrieve. Disconnect is also permitted after docking and
before downstream records are present. Retrieval clears all downstream
bindings; retained custody can be explicitly replaced or docked again.
Fresh acquisition run/record IDs are required across cycles of one instance.
quarantine() is a terminal local hold; a repeated quarantine is idempotent.
snapshot() and acquisition_manifest() return detached deep copies.

Laser energy and controller execution remain DISABLED in every state. Both
on-chip heaters remain off; there is no heater activation API. The
disabled-controller record is descriptive only. request_physical_service()
always raises, including for laser enable, PID changes, acquisition, alignment,
simulation and measurement. No method emits real signals, calibrated data,
linewidth, noise, locking status or fabricated results.

Source labels: DOI 10.1038/s41467-024-46319-3, Fig. 5 / Methods, and Supplementary
Table 2. The three DFB identities remain separate. The SiN example in
Supplementary Note 5 is numerical-only and is not a selectable physical
platform. These labels do not assert that the caller owns source equipment.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType
import uuid


class GuardError(ValueError):
    """The requested metadata transition or its local claim is invalid."""


class PhysicalExecutionUnavailable(GuardError):
    """There is deliberately no physical, scientific or device adapter."""


SOURCE_DOI = "10.1038/s41467-024-46319-3"
EXPERIMENTAL_PLATFORM = "AIM_100NM_SOI"
SIN_BRANCH = "NUMERICAL_ONLY_NOT_SELECTABLE"
SOURCE_DFB_MODELS = MappingProxyType({
    "DFB_1": "AeroDiode 1550LD-2-0-0-1",
    "DFB_2": "Gooch & Housego-AA1401",
    "DFB_3": "AeroDiode 1550LD-6-0-0-1",
})
BINDING_FIELDS = frozenset({
    "sample_id", "sample_version", "pic_id", "carrier_id", "dock_id",
    "configuration_id", "configuration_version", "platform",
})
ACTION_FIELDS = MappingProxyType({
    "register_custody": frozenset({"custody_record_id"}),
    "dock": frozenset({"docking_record_id"}),
    "register_alignment": frozenset({
        "alignment_record_id", "external_qualification_record_id",
        "qualifier_id", "alignment_status",
    }),
    "select_module": frozenset({
        "module_id", "source_dfb_id", "source_model", "seal_record_id",
        "module_status",
    }),
    "register_disabled_controller": frozenset({
        "module_id", "source_dfb_id", "controller_id", "disabled_record_id",
        "controller_status",
    }),
    "bind_acquisition_records": frozenset({
        "module_id", "source_dfb_id", "controller_id", "run_id",
        "record_set_id", "comb_reference_id", "comb_reference_record_id",
        "heterodyne_receiver_id", "heterodyne_record_id", "fpga_id",
        "fpga_record_id", "record_status",
    }),
    "disconnect": frozenset({"disconnect_record_id", "disconnect_status"}),
    "register_unloaded": frozenset({"unload_record_id", "unload_status"}),
    "retrieve": frozenset({"custody_return_record_id"}),
})
TARGET_FIELDS = MappingProxyType({
    "register_custody": "carrier_id", "dock": "dock_id",
    "register_alignment": "pic_id", "select_module": "module_id",
    "register_disabled_controller": "controller_id",
    "bind_acquisition_records": "record_set_id", "disconnect": "dock_id",
    "register_unloaded": "carrier_id", "retrieve": "carrier_id",
})
REQUIRED_SYMBOLS = MappingProxyType({
    "register_alignment": ("alignment_status", "externally_qualified_symbolic_claim"),
    "select_module": ("module_status", "sealed_symbolic_claim"),
    "register_disabled_controller": ("controller_status", "disabled_symbolic_claim"),
    "bind_acquisition_records": ("record_status", "external_record_ids_only"),
    "disconnect": ("disconnect_status", "disconnected_symbolic_claim"),
    "register_unloaded": ("unload_status", "unloaded_symbolic_claim"),
})


def _string(value: object, label: str) -> None:
    if type(value) is not str or not value.strip():
        raise GuardError(label + " must be a nonempty plain string")


def _integer(value: object, label: str, minimum: int = 1) -> None:
    if type(value) is not int or value < minimum:
        raise GuardError(label + " must be a plain integer >= " + str(minimum))


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Claim:
    """Untrusted local intent token, bound to exactly one proposed action."""

    instance: str
    revision: int
    sample_id: str
    sample_version: int
    context_hash: str
    action: str
    target_id: str
    payload_hash: str
    claim_id: str


class LaserControlFixture:
    """Store symbolic records for one immutable PIC sample identity/version."""

    def __init__(self, sample_id: str, sample_version: int = 1):
        _string(sample_id, "sample_id")
        _integer(sample_version, "sample_version")
        self._instance = uuid.uuid4().hex
        self._sample_id = sample_id
        self._sample_version = sample_version
        self._revision = 0
        self._state = "CUSTODY"
        self._records: dict[str, dict] = {}
        self._issued: dict[str, Claim] = {}
        self._consumed: set[str] = set()
        self._used_runs: set[str] = set()
        self._used_acquisition_records: set[str] = set()

    def snapshot(self) -> dict:
        """Detached metadata only; invariant flags never claim physical truth."""
        return copy.deepcopy({
            "instance": self._instance, "revision": self._revision,
            "sample_id": self._sample_id, "sample_version": self._sample_version,
            "state": self._state, "records": self._records,
            "scope": "caller_owned_untrusted_local_metadata_only",
            "claims_are_evidence": False, "physical_execution": False,
            "geometry_coupling": False, "laser_energy_state": "DISABLED",
            "laser_enabled": False, "controller_state": "DISABLED",
            "controller_enabled": False, "real_signals": None,
            "heater1_enabled": False, "heater2_enabled": False,
            "calibrated_data": None, "scientific_outputs": None,
            "silicon_nitride_branch": SIN_BRANCH,
        })

    def _context(self) -> str:
        return _digest(self.snapshot())

    def _validate_record(self, action: str, record: dict) -> None:
        if type(record) is not dict or set(record) != BINDING_FIELDS | ACTION_FIELDS[action]:
            raise GuardError("exact complete record fields required for " + action)
        for key, value in record.items():
            if key in {"sample_version", "configuration_version"}:
                _integer(value, key)
            else:
                _string(value, key)
        if (record["sample_id"], record["sample_version"]) != (
            self._sample_id, self._sample_version
        ):
            raise GuardError("sample identity/version mismatch")
        if record["platform"] != EXPERIMENTAL_PLATFORM:
            raise GuardError("only source SOI metadata is selectable; SiN is numerical-only")
        if action != "register_custody":
            custody = self._records.get("register_custody")
            if custody is None or any(record[key] != custody[key] for key in BINDING_FIELDS):
                raise GuardError("carrier/PIC/dock/configuration binding mismatch")
        if action in REQUIRED_SYMBOLS:
            key, expected = REQUIRED_SYMBOLS[action]
            if record[key] != expected:
                raise GuardError("explicit symbolic-only disposition required: " + key)
        if action == "select_module":
            if SOURCE_DFB_MODELS.get(record["source_dfb_id"]) != record["source_model"]:
                raise GuardError("one exact source DFB identity/model pair required")
        if action in {"register_disabled_controller", "bind_acquisition_records"}:
            module = self._records.get("select_module")
            if module is None or any(record[key] != module[key] for key in ("module_id", "source_dfb_id")):
                raise GuardError("selected sealed module binding mismatch")
        if action == "bind_acquisition_records":
            controller = self._records.get("register_disabled_controller")
            if controller is None or record["controller_id"] != controller["controller_id"]:
                raise GuardError("disabled controller binding mismatch")
            record_ids = {record[key] for key in (
                "record_set_id", "comb_reference_record_id", "heterodyne_record_id", "fpga_record_id"
            )}
            if len(record_ids) != 4 or record_ids & self._used_acquisition_records:
                raise GuardError("distinct fresh paired acquisition record IDs required")
            if record["comb_reference_id"] == record["heterodyne_receiver_id"] or record["fpga_id"] in {
                record["comb_reference_id"], record["heterodyne_receiver_id"]
            }:
                raise GuardError("comb, heterodyne receiver and FPGA identities must be distinct")
            if record["run_id"] in self._used_runs:
                raise GuardError("fresh acquisition run ID required")

    def claim(self, action: str, target_id: str, record: dict) -> Claim:
        """Issue a local proposal for this exact payload; never evidence of work."""
        if self._state == "QUARANTINE":
            raise GuardError("quarantine is terminal")
        _string(action, "action")
        if action not in ACTION_FIELDS:
            raise GuardError("unknown metadata action")
        _string(target_id, "target_id")
        self._validate_record(action, record)
        if target_id != record[TARGET_FIELDS[action]]:
            raise GuardError("claim target does not match record")
        claim = Claim(
            self._instance, self._revision, self._sample_id, self._sample_version,
            self._context(), action, target_id, _digest(record), uuid.uuid4().hex,
        )
        self._issued[claim.claim_id] = claim
        return claim

    def _check_claim(self, claim: Claim, action: str, record: dict) -> None:
        if type(claim) is not Claim:
            raise GuardError("typed local Claim required")
        _integer(claim.revision, "claim revision", minimum=0)
        _integer(claim.sample_version, "claim sample_version")
        for key in ("instance", "sample_id", "context_hash", "action", "target_id", "payload_hash", "claim_id"):
            _string(getattr(claim, key), "claim " + key)
        expected = (
            self._instance, self._revision, self._sample_id, self._sample_version,
            self._context(), action, record[TARGET_FIELDS[action]], _digest(record),
        )
        actual = (
            claim.instance, claim.revision, claim.sample_id, claim.sample_version,
            claim.context_hash, claim.action, claim.target_id, claim.payload_hash,
        )
        if actual != expected or self._issued.get(claim.claim_id) != claim or claim.claim_id in self._consumed:
            raise GuardError("unissued, stale, replayed, cross-instance or mismatched claim")

    def _apply(self, action: str, record: dict, claim: Claim, allowed: set[str], state: str) -> dict:
        if self._state not in allowed:
            raise GuardError("state precondition failed for " + action)
        self._validate_record(action, record)
        self._check_claim(claim, action, record)
        # Validation and copying precede mutation. No user callbacks or adapters.
        detached = copy.deepcopy(record)
        if action == "register_custody":
            self._records.clear()
        elif action == "dock":
            self._records.pop("retrieve", None)
        elif action == "retrieve":
            self._records = {"register_custody": self._records["register_custody"]}
        self._records[action] = detached
        if action == "bind_acquisition_records":
            self._used_runs.add(record["run_id"])
            self._used_acquisition_records.update(record[key] for key in (
                "record_set_id", "comb_reference_record_id", "heterodyne_record_id", "fpga_record_id"
            ))
        self._consumed.add(claim.claim_id)
        self._issued.clear()
        self._state = state
        self._revision += 1
        return self.snapshot()

    def register_custody(self, record: dict, claim: Claim) -> dict:
        """Bind or replace caller-owned custody metadata while in custody."""
        return self._apply("register_custody", record, claim, {"CUSTODY"}, "CUSTODY")

    def dock(self, record: dict, claim: Claim) -> dict:
        """Record a docking claim; move no object."""
        return self._apply("dock", record, claim, {"CUSTODY"}, "DOCKED")

    def register_alignment(self, record: dict, claim: Claim) -> dict:
        """Store the label of external qualification without verifying it."""
        return self._apply("register_alignment", record, claim, {"DOCKED"}, "ALIGNMENT_CLAIMED")

    def select_module(self, record: dict, claim: Claim) -> dict:
        """Select one sealed-module symbolic identity without enabling energy."""
        return self._apply("select_module", record, claim, {"ALIGNMENT_CLAIMED"}, "MODULE_SELECTED")

    def register_disabled_controller(self, record: dict, claim: Claim) -> dict:
        """Record a disabled-controller label; accept no controller parameters."""
        return self._apply("register_disabled_controller", record, claim, {"MODULE_SELECTED"}, "CONTROLLER_DISABLED_CLAIMED")

    def bind_acquisition_records(self, record: dict, claim: Claim) -> dict:
        """Bind external comb-heterodyne and FPGA in-loop IDs; acquire nothing."""
        return self._apply("bind_acquisition_records", record, claim, {"CONTROLLER_DISABLED_CLAIMED"}, "ACQUISITION_RECORDS_BOUND")

    def acquisition_manifest(self) -> dict:
        """Return record labels only, never signals, PSD, linewidth or evidence."""
        if self._state != "ACQUISITION_RECORDS_BOUND":
            raise GuardError("current paired acquisition record binding required")
        return copy.deepcopy({
            "sample_id": self._sample_id, "sample_version": self._sample_version,
            "binding": {key: self._records["register_custody"][key] for key in sorted(BINDING_FIELDS)},
            "module": self._records["select_module"],
            "records": self._records["bind_acquisition_records"],
            "roles": {"heterodyne_record_id": "comb_reference_heterodyne", "fpga_record_id": "in_loop_error"},
            "scope": "unverified_external_record_identifiers_only",
            "claims_are_evidence": False, "physical_execution": False,
            "laser_enabled": False, "controller_enabled": False,
            "heater1_enabled": False, "heater2_enabled": False,
            "real_signals": None, "calibrated_data": None, "scientific_outputs": None,
        })

    def disconnect(self, record: dict, claim: Claim) -> dict:
        """Record symbolic disconnection even for an incomplete metadata cycle."""
        return self._apply("disconnect", record, claim, {
            "DOCKED", "ALIGNMENT_CLAIMED", "MODULE_SELECTED",
            "CONTROLLER_DISABLED_CLAIMED", "ACQUISITION_RECORDS_BOUND",
        }, "DISCONNECTED_CLAIMED")

    def register_unloaded(self, record: dict, claim: Claim) -> dict:
        """Record symbolic unloading only after symbolic disconnection."""
        return self._apply("register_unloaded", record, claim, {"DISCONNECTED_CLAIMED"}, "UNLOADED_CLAIMED")

    def retrieve(self, record: dict, claim: Claim) -> dict:
        """Return local custody and invalidate all downstream active records."""
        return self._apply("retrieve", record, claim, {"UNLOADED_CLAIMED"}, "CUSTODY")

    def quarantine(self) -> dict:
        """Enter terminal metadata hold. This performs no physical shutdown."""
        if self._state != "QUARANTINE":
            self._state = "QUARANTINE"
            self._revision += 1
            self._issued.clear()
        return self.snapshot()

    def request_physical_service(self, operation_id: object, *args, **kwargs) -> None:
        """Reject every physical/scientific request without executing callbacks."""
        raise PhysicalExecutionUnavailable(
            "No laser-enable, heater, PID, alignment, acquisition, signal, calibration, "
            "measurement, simulation, geometry or hardware adapter exists"
        )
