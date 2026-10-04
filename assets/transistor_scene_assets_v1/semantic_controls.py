"""Static transistor scene bookkeeping. Standard library only; no device adapter.

This module accepts author-supplied fixture observations, not authenticated or
measured observations. A successful guard proves only local metadata consistency.
It establishes no physical reachability, safe handling, qualification, continuity,
electrical measurement, or experimental replication. Do not connect it to hardware.

Public interface: SceneControls(...), receipt_binding(), snapshot(),
record_fixture_observation(dict), request_deenergize(), mount(receipt_id),
rewire(...), disconnect(receipt_id), retrieve(receipt_id), verify_custody(...),
create_record(...), acknowledge_conflict(...), terminal_state(name), apply(...).
request_service(...) always rejects. ordered_pairs() enumerates 90 ordered pairs.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from types import MappingProxyType
from uuid import uuid4

SCHEMA_VERSION = "transistor_scene_static.v1"
FIXTURE_AUTHORITY = "synthetic_fixture_authority"
FIXTURE_SCOPE = "static_fixture_only"
STACK_IDS = tuple(f"S{i}" for i in range(1, 11))
CONFLICT_IDS = tuple(f"C{i:02d}" for i in range(1, 11))
TERMINALS = (
    "driver_BG", "driver_TG", "driver_source", "driver_drain",
    "load_BG", "load_TG", "load_source", "load_drain",
)
# Diagram interpretations only. Neither mapping is an approved physical pad map.
NETLISTS = MappingProxyType({
    "ORDINARY_INVERTER_FIG4": MappingProxyType({
        "driver_BG": "VIN", "driver_TG": "VIN", "driver_source": "GND",
        "driver_drain": "VOUT", "load_BG": "VDD", "load_TG": "VOUT",
        "load_source": "VOUT", "load_drain": "VDD",
    }),
    "INDEPENDENT_INVERTER_S31": MappingProxyType({
        "driver_BG": "VBG", "driver_TG": "VTG1", "driver_source": "GND",
        "driver_drain": "VOUT", "load_BG": "VOUT", "load_TG": "VTG2",
        "load_source": "VOUT", "load_drain": "VDD",
    }),
})
_IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]{0,95}\Z")


class GuardError(ValueError):
    """A local static fixture invariant was not met; no transition occurred."""


class PhysicalServiceRejected(GuardError):
    """Physical services are permanently outside this package's capabilities."""


def _identifier(value, field):
    if type(value) is not str or not _IDENTIFIER.fullmatch(value):
        raise GuardError(f"{field} must be a nonempty identifier string")
    return value


def _positive_int(value, field):
    if type(value) is not int or value < 1:
        raise GuardError(f"{field} must be a positive integer; bool is invalid")
    return value


def _exact_keys(value, keys, field):
    if type(value) is not dict or set(value) != set(keys):
        raise GuardError(f"{field} has missing, extra, or unsupported fields")


def _strict_equal(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return set(a) == set(b) and all(_strict_equal(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(_strict_equal(x, y) for x, y in zip(a, b))
    return a == b


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode("utf-8")).hexdigest()


def ordered_pairs():
    """Metadata identities only; no pair performance or executable schedule."""
    return [{"pair_id": f"D{d[1:]}_L{l[1:]}", "driver_stack_id": d,
             "load_stack_id": l}
            for d in STACK_IDS for l in STACK_IDS if d != l]


@dataclass(frozen=True)
class SampleIdentity:
    sample_id: str
    specimen_version: int
    carrier_id: str
    chip_id: str
    pcb_id: str
    cohort_id: str
    architecture_id: str

    def __post_init__(self):
        for field, value in asdict(self).items():
            if field == "specimen_version":
                _positive_int(value, field)
            else:
                _identifier(value, field)


class SceneControls:
    """In-memory metadata state machine, deliberately not an equipment interface.

    The fixture observation channel is separate from apply() actor controls, but
    both are caller-owned Python data. This separation is not authentication.
    Every lifecycle-changing action consumes current evidence and invalidates all
    safe-zero/continuity markers. A record consumes its continuity marker once.
    """

    def __init__(self, *, sample_id, specimen_version, carrier_id, chip_id, pcb_id,
                 cohort_id, architecture_id, stack_ids, retained=True):
        if type(retained) is not bool or retained is not True:
            raise GuardError("retained must be exactly True; release is unsupported")
        if type(stack_ids) not in (list, tuple) or len(stack_ids) != 10:
            raise GuardError("all ten explicit registered stack IDs are required")
        for stack in stack_ids:
            _identifier(stack, "stack_id")
        if set(stack_ids) != set(STACK_IDS):
            raise GuardError("stack_ids must contain distinct S1 through S10")
        self._fixture_instance_id = "fixture_" + uuid4().hex
        self._identity = SampleIdentity(sample_id, specimen_version, carrier_id,
                                        chip_id, pcb_id, cohort_id, architecture_id)
        self._custody = "storage_retained"
        self._state_revision = 0
        self._mount_revision = 0
        self._netlist_revision = 0
        self._netlist_id = None
        self._driver = None
        self._load = None
        self._terminal_map = {name: "unknown" for name in TERMINALS}
        self._observations = {}
        self._used_receipts = set()
        self._safe_zero_id = None
        self._continuity_id = None
        self._records = {}
        self._acknowledgements = {}
        self._events = []

    @property
    def identity(self):
        return self._identity

    def receipt_binding(self):
        """Exact current identity/configuration snapshot required by a marker."""
        return {
            **asdict(self._identity), "stack_ids": list(STACK_IDS),
            "fixture_instance_id": self._fixture_instance_id,
            "retained": True, "custody": self._custody,
            "state_revision": self._state_revision,
            "mount_revision": self._mount_revision,
            "netlist_revision": self._netlist_revision,
            "netlist_id": self._netlist_id,
            "driver_stack_id": self._driver, "load_stack_id": self._load,
            "terminal_map_hash": _digest(self._terminal_map),
        }

    def snapshot(self):
        """Return detached metadata; editing it cannot edit the scene."""
        return copy.deepcopy({
            "schema_version": SCHEMA_VERSION, "mode": FIXTURE_SCOPE,
            "physical_execution_implemented": False,
            "physical_reachability_proven": False,
            "safety_qualified": False, "scientific_replication": False,
            "electrical_outputs_implemented": False,
            "observation_authority": FIXTURE_AUTHORITY,
            "identity": asdict(self._identity), "binding": self.receipt_binding(),
            "terminal_map": self._terminal_map,
            "current_safe_zero_fixture_receipt_id": self._safe_zero_id,
            "current_continuity_fixture_receipt_id": self._continuity_id,
            "source_conflicts": [{"id": c, "resolved": False,
                                  "qualification_gate": True,
                                  "fixture_acknowledged": c in self._acknowledgements}
                                 for c in CONFLICT_IDS],
            "records": list(self._records.values()), "events": self._events,
        })

    def _transition(self, operation):
        self._state_revision += 1
        for receipt_id in (self._safe_zero_id, self._continuity_id):
            if receipt_id is not None:
                self._used_receipts.add(receipt_id)
        self._safe_zero_id = self._continuity_id = None
        self._events.append({"operation": operation,
                             "state_revision": self._state_revision,
                             "scope": FIXTURE_SCOPE})

    def _receipt(self, receipt_id, kind):
        _identifier(receipt_id, "receipt_id")
        item = self._observations.get(receipt_id)
        if item is None or item["kind"] != kind:
            raise GuardError(f"missing or wrong-kind {kind} fixture receipt")
        current = self._safe_zero_id if kind == "safe_zero" else self._continuity_id
        if receipt_id in self._used_receipts or receipt_id != current:
            raise GuardError("stale, superseded, or already-used fixture receipt")
        if not _strict_equal(item["binding"], self.receipt_binding()):
            raise GuardError("fixture receipt binding no longer matches scene")
        return item

    def record_fixture_observation(self, observation):
        """Register a symbolic fixture marker. Never record measurement values.

        Required keys: receipt_id, kind ('safe_zero' or 'continuity'), authority
        (FIXTURE_AUTHORITY), scope (FIXTURE_SCOPE), binding (receipt_binding()),
        outcome ('fixture_safe_zero' or 'fixture_continuity'). The independent
        fixture channel is simulated only; these strings prove no real state.
        """
        _exact_keys(observation, {"receipt_id", "kind", "authority", "scope",
                                  "binding", "outcome"}, "fixture observation")
        rid = _identifier(observation["receipt_id"], "receipt_id")
        if rid in self._observations:
            raise GuardError("receipt ID reuse is forbidden, even after invalidation")
        kind = observation["kind"]
        if type(kind) is not str or kind not in {"safe_zero", "continuity"}:
            raise GuardError("unsupported fixture observation kind")
        if type(observation["authority"]) is not str or observation["authority"] != FIXTURE_AUTHORITY:
            raise GuardError("only explicitly synthetic fixture authority is accepted")
        if type(observation["scope"]) is not str or observation["scope"] != FIXTURE_SCOPE:
            raise GuardError("only static_fixture_only scope is accepted")
        if type(observation["outcome"]) is not str or observation["outcome"] != "fixture_" + kind:
            raise GuardError("fixture marker has the wrong outcome")
        if not _strict_equal(observation["binding"], self.receipt_binding()):
            raise GuardError("fixture marker must match exact current identity, pair, map, and revisions")
        if kind == "continuity":
            if self._custody != "mounted_retained" or self._netlist_id is None:
                raise GuardError("continuity metadata requires a mounted configured fixture")
            self._receipt(self._safe_zero_id, "safe_zero")
            previous = self._continuity_id
        else:
            previous = self._safe_zero_id
        if previous is not None:
            self._used_receipts.add(previous)
        self._observations[rid] = copy.deepcopy(observation)
        if kind == "safe_zero":
            self._safe_zero_id = rid
        else:
            self._continuity_id = rid
        return copy.deepcopy(observation)

    def request_deenergize(self):
        """Record an actor intent only; it never generates a safe-zero marker."""
        self._transition("request_deenergize_metadata_only")
        return self.snapshot()

    def mount(self, safe_zero_receipt_id):
        if self._custody != "storage_retained":
            raise GuardError("mount requires storage_retained fixture custody")
        self._receipt(safe_zero_receipt_id, "safe_zero")
        self._custody = "mounted_retained"
        self._mount_revision += 1
        self._netlist_id = self._driver = self._load = None
        self._terminal_map = {name: "unknown" for name in TERMINALS}
        self._transition("mount_metadata_only")
        return self.snapshot()

    def rewire(self, *, netlist_id, driver_stack_id, load_stack_id,
               terminal_map, netlist_revision, safe_zero_receipt_id):
        """Change labels only; no wiring service or physical pad-map approval."""
        if self._custody != "mounted_retained":
            raise GuardError("rewire requires mounted_retained fixture custody")
        _identifier(netlist_id, "netlist_id")
        if netlist_id not in NETLISTS:
            raise GuardError("netlist is unsupported or lacks an explicit terminal map")
        for name, value in (("driver_stack_id", driver_stack_id), ("load_stack_id", load_stack_id)):
            _identifier(value, name)
            if value not in STACK_IDS:
                raise GuardError(f"{name} is not a registered stack")
        if driver_stack_id == load_stack_id:
            raise GuardError("driver and load must retain distinct stack identities")
        _positive_int(netlist_revision, "netlist_revision")
        if netlist_revision != self._netlist_revision + 1:
            raise GuardError("netlist_revision must increase by exactly one")
        if not _strict_equal(terminal_map, dict(NETLISTS[netlist_id])):
            raise GuardError("terminal map must exactly match selected Fig4 or S31 interpretation; unknown is not floating")
        self._receipt(safe_zero_receipt_id, "safe_zero")
        self._netlist_id, self._driver, self._load = netlist_id, driver_stack_id, load_stack_id
        self._netlist_revision = netlist_revision
        self._terminal_map = copy.deepcopy(terminal_map)
        self._transition("rewire_metadata_only")
        return self.snapshot()

    def disconnect(self, safe_zero_receipt_id):
        if self._custody != "mounted_retained":
            raise GuardError("disconnect requires mounted_retained fixture custody")
        self._receipt(safe_zero_receipt_id, "safe_zero")
        self._custody = "disconnected_retained"
        self._transition("disconnect_metadata_only")
        return self.snapshot()

    def retrieve(self, safe_zero_receipt_id):
        if self._custody != "disconnected_retained":
            raise GuardError("retrieve requires disconnected_retained fixture custody")
        self._receipt(safe_zero_receipt_id, "safe_zero")
        self._custody = "storage_retained"
        self._transition("retrieve_metadata_only")
        return self.snapshot()

    def verify_custody(self, *, sample_id, specimen_version, carrier_id, retained):
        _identifier(sample_id, "sample_id")
        _identifier(carrier_id, "carrier_id")
        _positive_int(specimen_version, "specimen_version")
        if type(retained) is not bool or retained is not True:
            raise GuardError("retention must remain exactly True")
        if (sample_id, specimen_version, carrier_id) != (
                self._identity.sample_id, self._identity.specimen_version, self._identity.carrier_id):
            raise GuardError("sample ID, specimen version, and carrier custody cannot be relabeled")
        return self.snapshot()

    def terminal_state(self, terminal):
        _identifier(terminal, "terminal")
        if terminal not in TERMINALS:
            raise GuardError("unknown terminal identity; floating is never inferred")
        return self._terminal_map[terminal]

    def create_record(self, *, record_id, case_id, continuity_receipt_id):
        """Create immutable bookkeeping only, consuming one current marker.

        There is no values argument, scientific payload, voltage/current curve,
        pass/fail measurement, gain/ratio/mobility calculation, or service call.
        """
        _identifier(record_id, "record_id")
        _identifier(case_id, "case_id")
        if record_id in self._records:
            raise GuardError("record ID reuse is forbidden")
        if self._custody != "mounted_retained" or self._netlist_id is None:
            raise GuardError("metadata record requires mounted configured fixture")
        self._receipt(continuity_receipt_id, "continuity")
        record = {"record_id": record_id, "case_id": case_id,
                  "record_kind": "fixture_metadata_only", "scope": FIXTURE_SCOPE,
                  "binding": self.receipt_binding(),
                  "continuity_fixture_receipt_id": continuity_receipt_id,
                  "source_conflict_ids_unresolved": list(CONFLICT_IDS),
                  "measurement_created": False, "physical_execution_implemented": False}
        record["metadata_hash"] = _digest(record)
        self._records[record_id] = copy.deepcopy(record)
        self._used_receipts.add(continuity_receipt_id)
        self._continuity_id = None
        return copy.deepcopy(record)

    def acknowledge_conflict(self, conflict_id, acknowledgement_id):
        _identifier(conflict_id, "conflict_id")
        _identifier(acknowledgement_id, "acknowledgement_id")
        if conflict_id not in CONFLICT_IDS:
            raise GuardError("unknown source conflict")
        if acknowledgement_id in self._acknowledgements.values():
            raise GuardError("acknowledgement ID reuse is forbidden")
        self._acknowledgements[conflict_id] = acknowledgement_id
        return {"id": conflict_id, "fixture_acknowledged": True, "resolved": False,
                "qualification_gate": True, "scope": FIXTURE_SCOPE}

    def request_service(self, service_name, **parameters):
        # Reject unconditionally: no spelling, scope flag, receipt, or conflict
        # acknowledgement can authorize an electrical/thermal/fabrication service.
        raise PhysicalServiceRejected("All physical services and electrical outputs are unimplemented and rejected")

    def apply(self, action, payload=None):
        """Strict actor dispatch. Observations cannot be submitted via this API."""
        _identifier(action, "action")
        if payload is None:
            payload = {}
        allowed = {
            "request_deenergize": (self.request_deenergize, set()),
            "mount": (self.mount, {"safe_zero_receipt_id"}),
            "rewire": (self.rewire, {"netlist_id", "driver_stack_id", "load_stack_id", "terminal_map", "netlist_revision", "safe_zero_receipt_id"}),
            "disconnect": (self.disconnect, {"safe_zero_receipt_id"}),
            "retrieve": (self.retrieve, {"safe_zero_receipt_id"}),
            "verify_custody": (self.verify_custody, {"sample_id", "specimen_version", "carrier_id", "retained"}),
            "create_record": (self.create_record, {"record_id", "case_id", "continuity_receipt_id"}),
            "acknowledge_conflict": (self.acknowledge_conflict, {"conflict_id", "acknowledgement_id"}),
        }
        if action not in allowed:
            raise PhysicalServiceRejected("Action is not a static fixture control; physical services are always rejected")
        method, keys = allowed[action]
        _exact_keys(payload, keys, "actor payload")
        return method(**payload)


def state_specification():
    """Return the adjacent declarative contract for scene/UI inspection."""
    return json.loads(Path(__file__).with_name("states.json").read_text(encoding="utf-8"))
