"""Pure, static Arc-Morph record examples. NOT a controller or physical proof.

These guards only check consistency of caller-supplied, synthetic records. A
passing check neither authenticates evidence nor qualifies/authorizes a person,
service, drawing, motion, load, measurement, or laboratory operation. No I/O,
robot/device interface, simulation, numerical scientific oracle, or source code
is included. A real integration must independently authenticate evidence,
qualify limits, enforce isolation, and validate the complete execution system.

All transitions return new immutable records. No function completes an edge,
removes a load, or repairs damage by inference. The module implements selected
negative-path semantics; the R00-R30 registry is not a complete runtime.
"""
from dataclasses import dataclass, replace
from hashlib import sha256
from math import isfinite

PAPER_DOI = "10.1038/s41467-025-57089-x"
OPERATION_IDS = tuple(f"R{i:02d}" for i in range(31))
ASSET_IDS = tuple(f"A{i:02d}" for i in range(1, 13))
ROUTE_FAMILIES = ("CS1", "CS2", "CS3", "CS4", "PP_PREP", "PP_RIGID", "PP_SHEAR")
SPECIMEN_FAMILIES = ("CS1", "CS2", "CS3", "CS4", "PP")
C01_SOURCE_READINGS_MM = (383.63, 383.65)  # Preserved disagreement; neither selected.
CLAIM = "Semantic examples only; no physical proof, qualification, or execution authorization."


class SemanticHold(ValueError):
    """A caller-supplied candidate is incomplete or inconsistent."""
    def __init__(self, code: str, detail: str):
        self.code = code
        super().__init__(f"{code}: {detail}")


def require(condition, code, detail):
    if not condition:
        raise SemanticHold(code, detail)


def known(value):
    return isinstance(value, str) and bool(value.strip())


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


def digest_valid(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


@dataclass(frozen=True)
class EdgePlan:
    edge_id: str
    dependencies: tuple[str, ...] = ()
    contact_patch_id: str = ""
    motion_envelope_id: str = ""


@dataclass(frozen=True)
class Qualification:
    family_id: str
    drawing_revision: str | None = None
    stock_qualified: bool | None = None
    drawing_qualified: bool | None = None
    service_qualified: bool | None = None
    fold_qualified: bool | None = None
    evidence_id: str | None = None
    dimensional_basis: str | None = None
    dimensional_spec_revision: str | None = None
    sheet_dimension_mm: float | None = None
    fold_plan: tuple[EdgePlan, ...] = ()


@dataclass(frozen=True)
class Event:
    revision: int
    operation_id: str
    evidence_id: str
    label: str


@dataclass(frozen=True)
class EdgeObservation:
    edge_id: str
    evidence_id: str
    before_observation_id: str
    after_observation_id: str
    result: str  # "accepted" or "failed"; result is supplied, never inferred.
    drawing_revision: str
    tool_disengaged: bool | None
    support_confirmed: bool | None


@dataclass(frozen=True)
class DamageObservation:
    evidence_id: str
    description: str
    revision: int


@dataclass(frozen=True)
class RestObservation:
    evidence_id: str
    kind: str  # baseline or rest
    image_id: str
    baseline_evidence_id: str | None
    disposition: str  # unchanged, changed, damaged
    revision: int
    qualified_interval_id: str


@dataclass(frozen=True)
class Mount:
    fixture_id: str
    fixture_revision: str
    kind: str  # rigid_metrology, rigid_demo, corner
    lease_id: str
    attachment_ids: tuple[str, ...]
    job_id: str | None = None
    job_status: str = "idle"


@dataclass(frozen=True)
class State:
    specimen_id: str
    stock_id: str
    material_batch: str
    family_id: str
    route_id: str
    carrier_id: str
    station: str = "stock"
    phase: str = "stock"
    drawing_revision: str | None = None
    fabrication_job_id: str | None = None
    qualification_evidence_id: str | None = None
    dimensional_spec_revision: str | None = None
    dimensional_basis: str | None = None
    sheet_dimension_mm: float | None = None
    fold_plan: tuple[EdgePlan, ...] = ()
    revision: int = 0
    configuration_revision: str | None = None
    supported: bool = True
    carrier_retained: bool = True
    tools_engaged: tuple[str, ...] = ()
    mount: Mount | None = None
    load_state: str = "removed"
    load_removal_evidence_id: str | None = None
    safe_release: bool | None = None
    active_capture_token_id: str | None = None
    edge_records: tuple[EdgeObservation, ...] = ()
    baseline_evidence_id: str | None = None
    rest_history: tuple[RestObservation, ...] = ()
    damage_history: tuple[DamageObservation, ...] = ()
    history: tuple[Event, ...] = ()


def initial_state(*, specimen_id, stock_id, material_batch, route_id, carrier_id):
    require(route_id in ROUTE_FAMILIES, "unknown_route", "Use one of the seven reviewed route identities.")
    require(all(known(v) for v in (specimen_id, stock_id, material_batch, carrier_id)), "identity_missing", "Custody identities must be explicit.")
    family = route_id if route_id.startswith("CS") else "PP"
    return State(specimen_id, stock_id, material_batch, family, route_id, carrier_id)


def _append(state, operation_id, evidence_id, label, **changes):
    require(operation_id in OPERATION_IDS, "unknown_operation", "Unknown operation ID.")
    require(known(evidence_id), "evidence_missing", "An explicit evidence identity is required.")
    require(evidence_id not in {e.evidence_id for e in state.history}, "duplicate_evidence", "Append a new record instead of overwriting an earlier event.")
    revision = state.revision + 1
    return replace(state, revision=revision, history=state.history + (Event(revision, operation_id, evidence_id, label),), **changes)


def check_qualification(state, qualification, *, service=False, fold=False):
    q = qualification
    require(q.family_id == state.family_id, "qualification_family", "Qualification must name the actual specimen family.")
    require(q.stock_qualified is True and q.drawing_qualified is True, "qualification_unknown", "Unknown stock/drawing qualification is a hold.")
    require(known(q.drawing_revision) and known(q.evidence_id), "drawing_unknown", "A named drawing revision and qualification evidence are required.")
    if state.drawing_revision is not None:
        require(q.drawing_revision == state.drawing_revision, "drawing_changed", "Prepared material cannot silently adopt a new drawing.")
        require(q.evidence_id == state.qualification_evidence_id, "qualification_changed", "Prepared material retains its original qualification evidence identity.")
    if state.family_id == "PP":
        require(q.dimensional_basis in ("reconciled_drawing", "explicit_authored_spec") and known(q.dimensional_spec_revision), "C01_unresolved", "383.63 mm and 383.65 mm remain conflicting readings until an explicit specification is supplied.")
        require(finite_number(q.sheet_dimension_mm) and q.sheet_dimension_mm > 0, "dimension_unknown", "The explicit specification must supply its dimension; no source value is selected automatically.")
        if state.drawing_revision is not None:
            require((q.dimensional_spec_revision, q.dimensional_basis, q.sheet_dimension_mm) == (state.dimensional_spec_revision, state.dimensional_basis, state.sheet_dimension_mm), "dimensional_spec_changed", "Prepared material cannot silently adopt a different dimensional specification, basis, or value.")
    if service:
        require(q.service_qualified is True, "service_unknown", "Service qualification is unknown or rejected.")
    if fold:
        require(q.fold_qualified is True and bool(q.fold_plan), "fold_plan_unknown", "A qualified per-edge fold plan is required.")
        if state.phase != "stock":
            require(q.fold_plan == state.fold_plan, "fold_plan_changed", "Prepared material retains its original per-edge plan; do not silently remove required edges.")
        ids = tuple(p.edge_id for p in q.fold_plan)
        require(len(ids) == len(set(ids)) and all(known(i) for i in ids), "fold_plan_identity", "Edge identities must be unique and nonempty.")
        seen = set()
        for edge in q.fold_plan:
            require(known(edge.contact_patch_id) and known(edge.motion_envelope_id), "fold_limits_unknown", "Every edge requires supplied contact and motion records.")
            require(set(edge.dependencies) <= seen, "fold_plan_order", "Dependencies must be earlier supplied edges; cycles and missing edges hold.")
            seen.add(edge.edge_id)


def fabricate_candidate(state, qualification, *, job_id, input_stock_id, output_specimen_id, receipt_id, safe_release):
    """Append a synthetic service receipt; this does not operate a fabricator."""
    check_qualification(state, qualification, service=True, fold=True)
    require(state.phase == "stock", "fabrication_phase", "Only identified stock can enter this example service transition.")
    require(input_stock_id == state.stock_id and output_specimen_id == state.specimen_id and known(job_id), "fabrication_lineage", "Receipt must bind exact input, output, and job IDs.")
    require(safe_release is True, "fabrication_release", "Unknown service safe-release cannot be inferred from completion.")
    require(state.mount is None and state.load_state == "removed", "fabrication_occupied", "Mounted/loaded input is inconsistent.")
    return _append(state, "R05", receipt_id, "synthetic_prepared_receipt", phase="processed", drawing_revision=qualification.drawing_revision, fabrication_job_id=job_id, qualification_evidence_id=qualification.evidence_id, dimensional_spec_revision=qualification.dimensional_spec_revision, dimensional_basis=qualification.dimensional_basis, sheet_dimension_mm=qualification.sheet_dimension_mm, fold_plan=qualification.fold_plan, safe_release=True, carrier_retained=False)


def inspect_prepared_candidate(state, *, evidence_id, output_specimen_id, parent_stock_id, findings, tools_accounted):
    require(state.phase == "processed" and state.safe_release is True, "inspection_release", "R06 follows a released service output; service completion is not inspection.")
    require(output_specimen_id == state.specimen_id and parent_stock_id == state.stock_id, "inspection_lineage", "Inspection must retain output-to-stock lineage.")
    required = ("cut_boundary", "vertex_relief", "crease_map", "sheet_condition")
    require(tuple(k for k, _ in findings) == required and all(value is True for _, value in findings), "inspection_failed", "Every supplied inspection check requires an explicit accepted observation.")
    require(tools_accounted is True and state.supported is True, "inspection_inventory", "Tools and supported carrier must be accounted for before transfer.")
    return _append(state, "R06", evidence_id, "synthetic_prepared_inspection", phase="prepared", carrier_retained=True)


def record_edge_candidate(state, qualification, observation):
    check_qualification(state, qualification, fold=True)
    require(state.phase in ("prepared", "folding"), "fold_phase", "A service completion cannot stand in for edge folding.")
    require(state.mount is None and state.load_state == "removed", "fold_loaded", "Fold observation requires unmounted, unloaded support.")
    require(state.supported is True and observation.support_confirmed is True and observation.tool_disengaged is True, "fold_support", "Support and tool disengagement observations must be explicit.")
    plan = {p.edge_id: p for p in qualification.fold_plan}
    require(observation.edge_id in plan, "unknown_edge", "Do not add an edge absent from the supplied plan.")
    require(observation.drawing_revision == qualification.drawing_revision, "edge_drawing", "Edge observation drawing revision must match.")
    require(observation.result in ("accepted", "failed") and known(observation.before_observation_id) and known(observation.after_observation_id), "edge_evidence", "Both edge observations and an explicit result are required.")
    latest = {o.edge_id: o.result for o in state.edge_records}
    require(all(latest.get(e) == "accepted" for e in plan[observation.edge_id].dependencies), "edge_dependency", "Every required predecessor needs its own latest accepted observation.")
    return _append(state, "R07", observation.evidence_id, "synthetic_edge_observation", phase="folding", edge_records=state.edge_records + (observation,))


def finish_folding_candidate(state, qualification, *, final_inspection_id):
    check_qualification(state, qualification, fold=True)
    require(state.phase == "folding", "fold_incomplete", "No per-edge observations have established a folded candidate.")
    latest = {o.edge_id: o.result for o in state.edge_records}
    require(all(latest.get(e.edge_id) == "accepted" for e in qualification.fold_plan), "fold_incomplete", "Each supplied edge needs its own latest accepted result.")
    require(state.tools_engaged == () and state.supported is True and state.carrier_retained is True, "fold_tool_engaged", "Fold tools must be disengaged and carrier support retained.")
    return _append(state, "R07", final_inspection_id, "synthetic_fold_record_complete", phase="folded")


def transport_candidate(state, *, source, destination, carrier_id, custody_receipt_id):
    require(state.mount is None, "transport_mounted", "Close the actual mount lease before transport.")
    require(state.load_state == "removed", "transport_loaded", "Present or unknown load prevents transport.")
    require(state.supported is True and state.carrier_retained is True and state.tools_engaged == (), "transport_support", "Carrier support and tool disengagement are required.")
    require(carrier_id == state.carrier_id and source == state.station and known(destination), "transport_custody", "Source, destination, object, and carrier binding must agree.")
    return _append(state, "R03", custody_receipt_id, "synthetic_custody_transfer", station=destination, active_capture_token_id=None)


def mount_candidate(state, mount, *, evidence_id, interface_qualified):
    require(state.mount is None and state.load_state == "removed", "mount_occupied", "Cannot mount a mounted or loaded specimen.")
    require(state.baseline_evidence_id is not None and not state.damage_history, "mount_baseline", "An undamaged specimen with preserved baseline is required.")
    require(interface_qualified is True and state.supported is True, "mount_unqualified", "Unknown support qualification holds.")
    require(mount.kind in ("rigid_metrology", "rigid_demo", "corner"), "mount_kind", "Fixture kinds are distinct.")
    require(all(known(v) for v in (mount.fixture_id, mount.fixture_revision, mount.lease_id)) and isinstance(mount.attachment_ids, tuple) and bool(mount.attachment_ids) and all(known(a) for a in mount.attachment_ids) and len(set(mount.attachment_ids)) == len(mount.attachment_ids), "mount_identity", "Fixture, exclusive lease, and attachment records are required.")
    if mount.kind == "corner":
        require(known(mount.job_id), "mount_job_unknown", "A corner mount requires its explicit load-job identity before creating a lease.")
    if mount.kind == "rigid_metrology":
        require(state.family_id == "PP", "mount_family", "Rigid metrology candidate is assigned to the polypropylene family.")
    if mount.kind == "rigid_demo":
        require(state.family_id.startswith("CS"), "mount_family", "Rigid demonstration candidate is assigned to a cardstock family.")
    operation = {"rigid_metrology": "R10", "rigid_demo": "R26", "corner": "R20"}[mount.kind]
    return _append(state, operation, evidence_id, "synthetic_mount_membership", mount=mount, carrier_retained=False, load_removal_evidence_id=None, safe_release=None, active_capture_token_id=None)


@dataclass(frozen=True)
class LoadJob:
    job_id: str
    specimen_id: str
    fixture_revision: str
    magnitude: float | None
    unit: str | None
    envelope_id: str | None
    qualified: bool | None
    controller_receipt_id: str | None
    guard_closed: bool | None


def qualitative_load_candidate(state, job):
    require(state.mount is not None and state.mount.kind == "corner", "load_fixture", "Corner-load semantics cannot use a rigid support lease.")
    require(state.baseline_evidence_id is not None and state.supported is True and not state.damage_history, "load_baseline", "Baseline, intact state, and support are required.")
    require(state.load_state == "removed", "load_already_present", "Unknown or existing load cannot be enlarged.")
    require(finite_number(job.magnitude) and job.magnitude > 0 and known(job.unit), "load_magnitude_unknown", "Qualitative does not mean an unknown load magnitude is acceptable.")
    require(job.qualified is True and known(job.envelope_id) and job.guard_closed is True and known(job.controller_receipt_id), "load_unqualified", "The bounded job and external controller receipt must be supplied.")
    require(known(job.job_id) and known(state.mount.job_id) and job.specimen_id == state.specimen_id and job.fixture_revision == state.mount.fixture_revision and job.job_id == state.mount.job_id, "load_binding", "Load job must bind the exact specimen and fixture revision.")
    return _append(state, "R21", job.controller_receipt_id, "synthetic_load_present", load_state="present", load_removal_evidence_id=None, safe_release=None, active_capture_token_id=None, mount=replace(state.mount, job_status="complete"))


def remove_load_candidate(state, *, evidence_id, fixture_revision, removal_confirmed, method_id, support_confirmed, safe_to_open):
    require(state.mount is not None and fixture_revision == state.mount.fixture_revision, "release_fixture", "Removal evidence must bind the actual fixture revision.")
    require(removal_confirmed is True and known(method_id) and support_confirmed is True and safe_to_open is True, "load_removal_unknown", "Safe release requires explicit, supported load-removal evidence.")
    return _append(state, "R19", evidence_id, "synthetic_load_removed", load_state="removed", load_removal_evidence_id=evidence_id, supported=True, safe_release=True, active_capture_token_id=None)


@dataclass(frozen=True)
class ReleaseEvidence:
    evidence_id: str
    specimen_id: str
    fixture_revision: str
    lease_id: str
    carrier_id: str
    detached_attachment_ids: tuple[str, ...]
    fixture_empty: bool | None
    supported: bool | None
    method_id: str | None
    hardware_accounted: bool | None = None


def release_mount_candidate(state, operation_id, evidence):
    mount = state.mount
    require(mount is not None, "release_unmounted", "No mount lease exists to release.")
    expected = "R22" if mount.kind == "corner" else "R30"
    require(operation_id == expected, "wrong_release_route", "Use R22 for corner fixtures and R30 for rigid fixtures; never both for one mount.")
    require(state.load_state == "removed" and known(state.load_removal_evidence_id) and state.safe_release is True, "release_before_unload", "R19 load-removal evidence must precede detachment.")
    require(state.active_capture_token_id is None, "release_live_token", "Invalidate capture tokens before release.")
    require(evidence.specimen_id == state.specimen_id and evidence.fixture_revision == mount.fixture_revision and evidence.lease_id == mount.lease_id and evidence.carrier_id == state.carrier_id, "release_binding", "Release identities must bind current specimen, fixture, lease, and carrier.")
    require(isinstance(evidence.detached_attachment_ids, tuple) and all(known(a) for a in evidence.detached_attachment_ids) and set(evidence.detached_attachment_ids) == set(mount.attachment_ids) and len(evidence.detached_attachment_ids) == len(mount.attachment_ids), "attachment_uncertain", "Every attachment must have explicit separation evidence.")
    require(evidence.fixture_empty is True and evidence.supported is True and known(evidence.method_id), "release_support", "Fixture-empty, supported carrier, and unmount method are required.")
    if mount.kind == "corner":
        require(mount.job_status in ("complete", "aborted") and evidence.hardware_accounted is True, "corner_hardware", "Corner release additionally requires job termination and load-hardware inventory.")
    return _append(state, operation_id, evidence.evidence_id, "synthetic_lease_closed", mount=None, carrier_retained=True, supported=True, active_capture_token_id=None)


def append_rest_candidate(state, *, evidence_id, image_id, disposition, qualified_interval_id, baseline=False):
    require(type(baseline) is bool, "rest_kind_unknown", "Baseline versus recovery must be an explicit boolean selection.")
    require(state.mount is None and state.load_state == "removed" and state.supported is True, "rest_loaded", "Rest observation requires an unloaded, unmounted, supported specimen.")
    require(known(image_id) and known(qualified_interval_id), "rest_evidence", "Rest image and qualified interval records are required.")
    require(disposition in ("unchanged", "changed", "damaged"), "rest_disposition", "Rest disposition must be explicit.")
    if baseline:
        require(state.phase == "folded" and state.baseline_evidence_id is None and not state.rest_history, "baseline_overwrite", "A baseline can be established once; later observations append.")
    else:
        require(known(state.baseline_evidence_id) and known(state.load_removal_evidence_id), "rest_baseline", "Recovery inspection must link preserved baseline and load-removal evidence.")
    record = RestObservation(evidence_id, "baseline" if baseline else "rest", image_id, state.baseline_evidence_id, disposition, state.revision + 1, qualified_interval_id)
    damage = state.damage_history
    if disposition == "damaged":
        damage += (DamageObservation(evidence_id, "observed damage", state.revision + 1),)
    return _append(state, "R08" if baseline else "R29", evidence_id, "synthetic_rest_observation", baseline_evidence_id=evidence_id if baseline else state.baseline_evidence_id, rest_history=state.rest_history + (record,), damage_history=damage, carrier_retained=True)


def check_append_only(previous, candidate):
    """Validate snapshots at an integration boundary; frozen Python is not security."""
    for name in ("specimen_id", "stock_id", "material_batch", "family_id", "route_id"):
        require(getattr(previous, name) == getattr(candidate, name), "identity_rewrite", "Identity and lineage cannot be rewritten.")
    for name in ("history", "rest_history", "damage_history", "edge_records"):
        old, new = getattr(previous, name), getattr(candidate, name)
        require(len(new) >= len(old) and new[:len(old)] == old, "history_erasure", f"{name} must be append-only.")
    require(candidate.revision >= previous.revision, "revision_rewind", "A state revision cannot move backwards.")
    if candidate != previous:
        require(candidate.revision > previous.revision and len(candidate.history) > len(previous.history), "revision_missing", "Every change requires a new recorded revision.")
    if previous.drawing_revision is not None:
        require(candidate.drawing_revision == previous.drawing_revision and candidate.fold_plan == previous.fold_plan and candidate.dimensional_spec_revision == previous.dimensional_spec_revision and candidate.dimensional_basis == previous.dimensional_basis and candidate.sheet_dimension_mm == previous.sheet_dimension_mm and candidate.qualification_evidence_id == previous.qualification_evidence_id, "preparation_rewrite", "Prepared drawing, dimensional specification, qualification, and per-edge plan cannot be rewritten.")
    if previous.baseline_evidence_id is not None:
        require(candidate.baseline_evidence_id == previous.baseline_evidence_id, "baseline_overwrite", "Baseline identity cannot be changed.")
    return True


@dataclass(frozen=True)
class CameraConfig:
    view: str
    camera_id: str
    lens_id: str
    mount_revision: str
    configuration_revision: str


@dataclass(frozen=True)
class MetrologyContext:
    fixture_revision: str
    cameras: tuple[CameraConfig, ...]
    reference_revisions: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class Calibration:
    calibration_id: str
    context: MetrologyContext
    valid_from_tick: int
    expires_at_tick: int
    method_id: str
    qualified: bool | None


def check_calibration(calibration, current_context, now_tick):
    require(calibration.qualified is True and known(calibration.method_id) and known(calibration.calibration_id), "calibration_unknown", "Calibration qualification and identity must be explicit.")
    require(type(now_tick) is int and type(calibration.valid_from_tick) is int and type(calibration.expires_at_tick) is int and calibration.valid_from_tick <= now_tick < calibration.expires_at_tick, "calibration_expired", "Calibration must cover the supplied logical time.")
    require(calibration.context == current_context, "calibration_revision_changed", "Camera, lens, mount, configuration, fixture, or reference changes invalidate calibration.")
    cameras = current_context.cameras
    require(len(cameras) == 2 and {c.view for c in cameras} == {"front", "lateral"} and len({c.camera_id for c in cameras}) == 2, "camera_views", "Two identified cameras with distinct front/lateral roles are required.")
    require(len({c.lens_id for c in cameras}) == 2, "lens_identity", "Distinct camera assemblies require distinct physical lens identities; shared model names are not lens IDs.")
    require(all(all(known(v) for v in (c.camera_id, c.lens_id, c.mount_revision, c.configuration_revision)) for c in cameras) and known(current_context.fixture_revision), "camera_identity", "Camera/lens/geometry identities cannot be empty.")
    refs = current_context.reference_revisions
    require(len(refs) >= 2 and len({r[0] for r in refs}) == len(refs) and all(known(a) and known(b) for a, b in refs), "references_unknown", "At least two distinct, revisioned references are required.")
    return True


@dataclass(frozen=True)
class CaptureToken:
    token_id: str
    campaign_id: str
    session_id: str
    specimen_id: str
    configuration_revision: str
    lock_interval: str
    calibration_id: str
    issued_at_tick: int
    expires_at_tick: int


def token_candidate(state, calibration, context, *, token_id, campaign_id, session_id, lock_interval, now_tick, expires_at_tick, required_locks, observed_locks, required_positions, readings, tolerance, stability_confirmed):
    check_calibration(calibration, context, now_tick)
    require(state.mount is not None and state.mount.kind == "rigid_metrology" and state.family_id == "PP" and state.mount.fixture_revision == context.fixture_revision and known(state.configuration_revision), "token_mount", "R15 belongs to the current polypropylene rigid-metrology mount; corner and rigid-demo fixtures cannot issue quantitative capture tokens.")
    require(state.supported is True and state.load_state == "removed" and state.tools_engaged == (), "token_state", "This static metrology example requires explicit support, no qualitative load, and disengaged tools.")
    require(all(known(v) for v in (token_id, campaign_id, session_id, lock_interval)), "token_identity", "Capture scope identities must be explicit.")
    require(type(expires_at_tick) is int and now_tick < expires_at_tick <= calibration.expires_at_tick, "token_expiry", "Token lifetime must be known and contained in calibration validity.")
    require(isinstance(required_locks, tuple) and bool(required_locks) and all(known(k) for k in required_locks) and len(set(required_locks)) == len(required_locks) and tuple(k for k, _ in observed_locks) == tuple(required_locks) and all(v is True for _, v in observed_locks), "locks_unknown", "Every required lock needs explicit current readback.")
    require(isinstance(required_positions, tuple) and len(required_positions) >= 2 and all(known(p) for p in required_positions) and len(set(required_positions)) == len(required_positions) and tuple(k for k, _ in readings) == tuple(required_positions), "uniformity_positions", "Readings must cover the supplied distinct positions exactly.")
    require(finite_number(tolerance) and tolerance >= 0 and all(finite_number(v) for _, v in readings), "uniformity_unknown", "Tolerance and actual readings must be finite supplied values.")
    values = [v for _, v in readings]
    require(max(values) - min(values) <= tolerance and stability_confirmed is True, "uniformity_failed", "A numeric target or a still image cannot replace observed uniformity/stability.")
    token = CaptureToken(token_id, campaign_id, session_id, state.specimen_id, state.configuration_revision, lock_interval, calibration.calibration_id, now_tick, expires_at_tick)
    return _append(state, "R15", token_id, "synthetic_capture_token", active_capture_token_id=token_id), token


@dataclass(frozen=True)
class Capture:
    capture_id: str
    campaign_id: str
    session_id: str
    specimen_id: str
    configuration_revision: str
    lock_interval: str
    token_id: str
    calibration_id: str
    camera: CameraConfig
    reference_revisions: tuple[tuple[str, str], ...]
    fixture_revision: str
    timestamp_tick: int
    file_sha256: str
    quality_accepted: bool | None


@dataclass(frozen=True)
class FileReceipt:
    capture_id: str
    original_sha256: str


@dataclass(frozen=True)
class SealedPair:
    front_capture_id: str
    lateral_capture_id: str
    original_hashes: tuple[str, str]
    pair_sha256: str
    claim: str = CLAIM


def pair_candidate(state, token, calibration, context, front, lateral, receipts, *, now_tick):
    """Check supplied hashes against supplied receipts, without reading any file.

    This checks record consistency only. It cannot authenticate captures, assess
    image quality, or prove byte integrity; a real custody boundary must do that.
    """
    check_calibration(calibration, context, now_tick)
    require(state.mount is not None and state.mount.kind == "rigid_metrology" and state.family_id == "PP" and state.mount.fixture_revision == context.fixture_revision, "pair_mount_mismatch", "The capture pair must retain its current mounted fixture geometry.")
    require(state.supported is True and state.load_state == "removed" and state.tools_engaged == (), "pair_state", "Pair custody cannot seal an unsupported, qualitatively loaded, or tool-engaged candidate.")
    require(all(known(getattr(token, name)) for name in ("token_id", "campaign_id", "session_id", "specimen_id", "configuration_revision", "lock_interval", "calibration_id")), "token_identity", "Token scope identities cannot be empty.")
    require(type(token.issued_at_tick) is int and type(token.expires_at_tick) is int and calibration.valid_from_tick <= token.issued_at_tick < token.expires_at_tick <= calibration.expires_at_tick, "token_calibration_interval", "The complete token interval must be covered by calibration; no backfilled calibration.")
    require(state.active_capture_token_id == token.token_id and token.specimen_id == state.specimen_id and token.configuration_revision == state.configuration_revision, "token_stale", "Only the current specimen/configuration token may seal a pair.")
    require(token.calibration_id == calibration.calibration_id and token.issued_at_tick <= now_tick < token.expires_at_tick, "token_expired", "Token and calibration must be current.")
    require(front.camera.view == "front" and lateral.camera.view == "lateral" and front.camera.camera_id != lateral.camera.camera_id, "pair_views", "Front and lateral captures must come from distinct registered cameras.")
    require(front.capture_id != lateral.capture_id and known(front.capture_id) and known(lateral.capture_id), "pair_identity", "Two distinct capture records are required.")
    require(len(receipts) == 2 and len({r.capture_id for r in receipts}) == 2, "receipt_identity", "Exactly two distinct original-file receipts are required.")
    by_id = {r.capture_id: r.original_sha256 for r in receipts}
    for capture in (front, lateral):
        for name in ("campaign_id", "session_id", "specimen_id", "configuration_revision", "lock_interval", "token_id", "calibration_id"):
            require(getattr(capture, name) == getattr(token, name), "pair_scope_mismatch", f"Capture {name} must match the shared token.")
        require(capture.camera in context.cameras and capture.fixture_revision == context.fixture_revision and capture.reference_revisions == context.reference_revisions, "pair_revision_mismatch", "Camera, lens, fixture, and reference revisions must match current calibration.")
        require(type(capture.timestamp_tick) is int and token.issued_at_tick <= capture.timestamp_tick <= now_tick and capture.timestamp_tick < token.expires_at_tick, "capture_outside_interval", "Capture must lie within the live token interval.")
        require(digest_valid(capture.file_sha256) and by_id.get(capture.capture_id) == capture.file_sha256, "capture_hash_mismatch", "Each capture hash must match its own original-file receipt.")
        require(capture.quality_accepted is True, "capture_quality_unknown", "Missing quality evidence cannot be inferred.")
    require(front.file_sha256 != lateral.file_sha256, "duplicate_image", "Reusing one image for both views cannot form a pair.")
    require(front.timestamp_tick <= lateral.timestamp_tick, "capture_order", "Lateral capture follows the frontal capture in the reviewed route.")
    # Length-prefix encoding avoids ambiguous concatenation; no files are read.
    fields = (front.capture_id, front.file_sha256, lateral.capture_id, lateral.file_sha256, token.token_id, token.specimen_id, token.configuration_revision, token.calibration_id)
    payload = "".join(f"{len(v)}:{v}" for v in fields).encode("utf-8")
    return SealedPair(front.capture_id, lateral.capture_id, (front.file_sha256, lateral.file_sha256), sha256(payload).hexdigest())


def configuration_candidate(state, *, configuration_revision, evidence_id):
    require(state.mount is not None and state.mount.kind == "rigid_metrology" and state.family_id == "PP", "configuration_scope", "R13 applies only to polypropylene rigid-metrology membership; cardstock rigid demonstration is R27 and remains unimplemented.")
    require(state.mount is not None and known(configuration_revision) and configuration_revision != state.configuration_revision, "configuration_identity", "Reconfiguration needs a mounted specimen and new revision.")
    require(state.load_state == "removed" and known(state.load_removal_evidence_id), "configuration_loaded", "Load removal must precede reconfiguration.")
    return _append(state, "R13", evidence_id, "synthetic_configuration_change", configuration_revision=configuration_revision, active_capture_token_id=None)


def closeout_candidate(states, *, expected_tools, observed_tools, open_leases, occupied_stations, controls_parked, custody_reconciled):
    require(isinstance(states, tuple) and bool(states) and len({s.specimen_id for s in states}) == len(states), "closeout_custody", "Declare nonduplicate specimen custody.")
    require(all(s.mount is None for s in states) and isinstance(open_leases, tuple) and open_leases == (), "closeout_leases", "Every exclusive lease must be accounted for and closed.")
    require(all(s.load_state == "removed" for s in states), "closeout_load", "Present/unknown load is a hold, never completed closeout.")
    require(isinstance(occupied_stations, tuple) and occupied_stations == () and controls_parked is True, "closeout_station", "Station occupancy and parked controls must be explicit.")
    require(isinstance(expected_tools, tuple) and isinstance(observed_tools, tuple) and all(known(t) for t in expected_tools + observed_tools) and len(expected_tools) == len(set(expected_tools)) and len(observed_tools) == len(set(observed_tools)) and set(expected_tools) == set(observed_tools), "closeout_tools", "Missing, duplicate, or unexplained tools prevent closeout.")
    require(custody_reconciled is True and all(s.supported is True and s.carrier_retained is True and s.tools_engaged == () and s.station in ("storage", "quarantine") for s in states), "closeout_custody", "Every specimen must be retained in declared storage or quarantine.")
    return {"status": "semantic_candidate_complete", "specimen_ids": tuple(s.specimen_id for s in states), "claim": CLAIM}


def actor_observation(state, *, permitted_operation_ids=(), requested_target_height=None):
    """Strict projection, not an isolation mechanism or evaluator authorization.

    Only the caller's current public state and own history IDs are exposed.
    No qualification records, hidden defects, acceptance rules, source curves,
    future captures, reference routes, or reviewer metadata are exported here.
    """
    require(all(i in OPERATION_IDS for i in permitted_operation_ids), "unknown_operation", "Only registered operation identifiers may be advertised.")
    require(requested_target_height is None or finite_number(requested_target_height), "target_invalid", "An optional requested target must be finite.")
    return {
        "specimen_id": state.specimen_id,
        "stock_id": state.stock_id,
        "material_batch": state.material_batch,
        "family_id": state.family_id,
        "requested_route_id": state.route_id,
        "requested_target_height": requested_target_height,
        "permitted_operation_ids": tuple(permitted_operation_ids),
        "current_observations": {
            "station": state.station,
            "phase": state.phase,
            "revision": state.revision,
            "configuration_revision": state.configuration_revision,
            "carrier_id": state.carrier_id,
            "supported": state.supported,
            "mounted": state.mount is not None,
            "load_state": state.load_state,
            "observed_damage_record_ids": tuple(d.evidence_id for d in state.damage_history),
        },
        "own_history_record_ids": tuple(e.evidence_id for e in state.history),
        "limitations": CLAIM,
    }
