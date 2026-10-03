#!/usr/bin/env python3
"""Independent, standard-library-only checks for the prismatic design package.

This is a static contract checker, not a task runner, controller, physical model,
or scientific reproduction. Synthetic record fixtures test bookkeeping rules
only. Run: python -m unittest discover -s tests -v
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import sys
from pathlib import Path
import unittest

ROOT = Path(os.environ.get("PRISMATIC_TASK_ROOT", Path(__file__).resolve().parents[1]))
SOURCE_DIR = None  # Only an explicit --source-dir enables optional byte verification.


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"),
                      object_pairs_hook=reject_duplicates,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"nonfinite number: {value}")))


def walk(value, path=()):
    """Yield every dictionary field with its unambiguous traversal path."""
    if isinstance(value, dict):
        for key, child in value.items():
            yield path + (str(key),), key, child
            yield from walk(child, path + (str(key),))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, path + (str(index),))


def index_records(records, name="records"):
    if not isinstance(records, list) or not records:
        raise ValueError(f"{name}: expected nonempty record list")
    result = {}
    for record in records:
        identifier = record.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise ValueError(f"{name}: record lacks a nonempty string id")
        if identifier in result:
            raise ValueError(f"{name}: duplicate id {identifier}")
        result[identifier] = record
    return result


def validate_dag(nodes, edges):
    """Verify concrete operation references and a directed acyclic graph."""
    nodes = set(nodes)
    adjacency = {node: set() for node in nodes}
    indegree = {node: 0 for node in nodes}
    for before, after in edges:
        if before not in nodes or after not in nodes:
            raise ValueError(f"unknown dependency endpoint: {before} -> {after}")
        if after not in adjacency[before]:
            adjacency[before].add(after)
            indegree[after] += 1
    frontier = [node for node, count in indegree.items() if count == 0]
    visited = []
    while frontier:
        node = frontier.pop()
        visited.append(node)
        for neighbor in adjacency[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                frontier.append(neighbor)
    if len(visited) != len(nodes):
        raise ValueError("cyclic operation dependencies")
    return visited


def require_resolved(required_ids, resolutions):
    """Reject missing, null or unqualified authored inputs without inventing defaults."""
    for identifier in required_ids:
        record = resolutions.get(identifier)
        if not isinstance(record, dict) or record.get("value") is None or record.get("value") in ([], {}, ""):
            raise ValueError(f"blocked unresolved input: {identifier}")
        if record.get("origin") not in {"authored", "qualified_episode_input"}:
            raise ValueError(f"blocked unqualified input: {identifier}")
    return True


def validate_last_five(cycles, selected_ids):
    """Validate static paired raw-cycle records, never calculate physical forces.

    The last five *acquired* records must themselves be complete and valid; a
    failed late cycle cannot be silently removed to promote an earlier one.
    """
    by_id = index_records(cycles, "cycle ledger")
    if len(cycles) < 5 or len(selected_ids) != 5 or len(set(selected_ids)) != 5:
        raise ValueError("five distinct acquired cycles required")
    if any(identifier not in by_id for identifier in selected_ids):
        raise ValueError("unknown cycle reference")
    orders = [record["ordinal"] for record in cycles]
    if orders != sorted(set(orders)):
        raise ValueError("cycle ledger order is not append-only")
    expected = [record["id"] for record in cycles[-5:]]
    if selected_ids != expected:
        raise ValueError("selection must preserve the last five acquired cycles in order")
    signatures = set()
    for identifier in selected_ids:
        record = by_id[identifier]
        if record.get("status") != "valid" or set(record.get("directions", [])) != {"loading", "unloading"}:
            raise ValueError("last-five selection contains incomplete or invalid cycle")
        signatures.add(tuple(record.get(key) for key in ("specimen_id", "assembly_version", "run_id", "condition_id", "fixture_id", "calibration_id")))
        if not record.get("raw_record_ids"):
            raise ValueError("cycle lacks independent raw evidence")
    if len(signatures) != 1 or any(None in signature for signature in signatures):
        raise ValueError("cycle selection mixes specimen or condition")
    return True


def validate_attempt_records(attempts):
    by_id = index_records(attempts, "attempt ledger")
    ordinals = [record["ordinal"] for record in attempts]
    if ordinals != sorted(set(ordinals)):
        raise ValueError("attempt ledger must be append-only")
    for record in attempts:
        if not record.get("specimen_id") or not record.get("condition_id"):
            raise ValueError("attempt identity missing")
        if record.get("reachability") not in {"reached", "not_reached", "blocked", "unknown"}:
            raise ValueError("reachability is not an observation status")
        release = record.get("release_performed")
        postrelease = record.get("postrelease_classification")
        if postrelease not in {"stable", "relaxed", "unresolved", "not_observed"}:
            raise ValueError("postrelease observation status missing")
        if postrelease in {"stable", "relaxed"} and (not release or record["reachability"] != "reached"):
            raise ValueError("cannot infer postrelease stability from target reachability")
        parent = record.get("retry_of")
        if parent is not None:
            if parent not in by_id or by_id[parent]["ordinal"] >= record["ordinal"]:
                raise ValueError("retry lineage must reference an earlier retained attempt")
    return True


def validate_array_slots(slots):
    if len(slots) != 8:
        raise ValueError("2x2x2 array requires eight unit slots")
    if len({slot["slot_id"] for slot in slots}) != 8:
        raise ValueError("array slot IDs must be unique")
    if len({slot["unit_id"] for slot in slots}) != 8:
        raise ValueError("one physical unit cannot occupy multiple slots")
    expected = {(x, y, z) for x in range(2) for y in range(2) for z in range(2)}
    if {tuple(slot["coordinate"]) for slot in slots} != expected:
        raise ValueError("array slot coordinates must cover 2x2x2 exactly")
    return True


def validate_lineage(records):
    """Check identity/parentage only, without making objects or mutating history."""
    by_id = index_records(records, "entity ledger")
    edges = []
    for record in records:
        if not record.get("location_id"):
            raise ValueError("entity must have exactly one declared current location")
        if not isinstance(record["location_id"], str):
            raise ValueError("entity location is not singular")
        for parent in record.get("parent_ids", []):
            if parent not in by_id:
                raise ValueError("unresolved parent lineage")
            edges.append((parent, record["id"]))
    validate_dag(by_id, edges)
    return True


class CheckerMutationTests(unittest.TestCase):
    """Self-tests ensure the static checker detects representative corruptions."""

    def test_duplicate_and_nonfinite_json_are_rejected(self):
        with self.assertRaises(ValueError):
            json.loads('{"a": 1, "a": 2}', object_pairs_hook=reject_duplicates)
        with self.assertRaises(ValueError):
            json.loads('{"a": NaN}', parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))

    def test_dependency_cycles_and_dangling_ids_are_rejected(self):
        self.assertEqual(set(validate_dag({"A", "B", "C"}, [("A", "B"), ("B", "C")])), {"A", "B", "C"})
        for edges in [[("A", "A")], [("A", "B"), ("B", "A")], [("A", "MISSING")]]:
            with self.subTest(edges=edges), self.assertRaises(ValueError):
                validate_dag({"A", "B"}, edges)

    def test_unknowns_do_not_turn_into_zero_or_empty_completion(self):
        for resolutions in [{}, {"U": {"value": None}}, {"U": {"value": [], "origin": "authored"}}, {"U": {"value": {}, "origin": "authored"}}, {"U": {"value": "", "origin": "authored"}}, {"U": {"value": 1, "origin": "source_inferred"}}]:
            with self.subTest(resolutions=resolutions), self.assertRaises(ValueError):
                require_resolved(["U"], resolutions)
        self.assertTrue(require_resolved(["U"], {"U": {"value": 0, "origin": "authored"}}))

    def cycle_fixture(self):
        return [{"id": f"C{i}", "ordinal": i, "status": "valid", "specimen_id": "S1", "condition_id": "COND1",
                 "assembly_version": 1, "run_id": "RUN1", "fixture_id": "FIX1", "calibration_id": "CAL1", "directions": ["loading", "unloading"], "raw_record_ids": [f"RAW{i}"]} for i in range(1, 8)]

    def test_last_five_integrity_rejects_cherry_picking_and_mixed_records(self):
        cycles = self.cycle_fixture()
        self.assertTrue(validate_last_five(cycles, ["C3", "C4", "C5", "C6", "C7"]))
        for selected in [["C1", "C2", "C3", "C4", "C5"], ["C3", "C4", "C5", "C6", "C6"], ["C3", "C4", "C5", "C6", "C8"]]:
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                validate_last_five(cycles, selected)
        for key, value in [("status", "invalid"), ("specimen_id", "S2"), ("condition_id", "COND2"), ("assembly_version", 2), ("run_id", "RUN2"), ("fixture_id", "FIX2"), ("calibration_id", "CAL2"), ("directions", ["loading"]), ("raw_record_ids", [])]:
            changed = copy.deepcopy(cycles)
            changed[-1][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_last_five(changed, ["C3", "C4", "C5", "C6", "C7"])

    def attempt_fixture(self):
        return [{"id": "A1", "ordinal": 1, "specimen_id": "S1", "condition_id": "MYLAR", "reachability": "not_reached", "release_performed": False, "postrelease_classification": "not_observed"},
                {"id": "A2", "ordinal": 2, "specimen_id": "S1", "condition_id": "MYLAR", "reachability": "reached", "release_performed": True, "postrelease_classification": "relaxed", "retry_of": "A1"}]

    def test_reachability_is_separate_from_postrelease_outcome(self):
        attempts = self.attempt_fixture()
        self.assertTrue(validate_attempt_records(attempts))
        for reachability, release in [("not_reached", True), ("reached", False), ("blocked", False)]:
            changed = copy.deepcopy(attempts)
            changed[-1]["reachability"] = reachability
            changed[-1]["release_performed"] = release
            changed[-1]["postrelease_classification"] = "stable"
            with self.subTest(reachability=reachability, release=release), self.assertRaises(ValueError):
                validate_attempt_records(changed)

    def test_failed_attempts_and_retry_lineage_cannot_be_overwritten(self):
        attempts = self.attempt_fixture()
        for mutation in [lambda a: a.append(copy.deepcopy(a[0])), lambda a: a[1].update(retry_of="MISSING"), lambda a: a[0].update(retry_of="A2"), lambda a: a[1].update(ordinal=1)]:
            changed = copy.deepcopy(attempts)
            mutation(changed)
            with self.assertRaises(ValueError):
                validate_attempt_records(changed)

    def test_eight_array_slots_are_not_eight_specimen_replicates(self):
        slots = [{"slot_id": f"slot{i}", "unit_id": f"unit{i}", "coordinate": [x, y, z]} for i, (x, y, z) in enumerate((x, y, z) for x in range(2) for y in range(2) for z in range(2))]
        self.assertTrue(validate_array_slots(slots))
        for mutation in [lambda s: s.pop(), lambda s: s[0].update(unit_id=s[1]["unit_id"]), lambda s: s[0].update(slot_id=s[1]["slot_id"]), lambda s: s[0].update(coordinate=s[1]["coordinate"])]:
            changed = copy.deepcopy(slots)
            mutation(changed)
            with self.assertRaises(ValueError):
                validate_array_slots(changed)

    def test_missing_or_circular_parent_lineage_is_rejected(self):
        records = [{"id": "LOT", "parent_ids": [], "location_id": "stock"}, {"id": "S1", "parent_ids": ["LOT"], "location_id": "carrier"}]
        self.assertTrue(validate_lineage(records))
        for mutation in [lambda r: r[1].update(parent_ids=["UNKNOWN"]), lambda r: r[0].update(parent_ids=["S1"]), lambda r: r[1].update(location_id=["carrier", "fixture"])]:
            changed = copy.deepcopy(records)
            mutation(changed)
            with self.assertRaises(ValueError):
                validate_lineage(changed)


class SourceContractTests(unittest.TestCase):
    """Source identity/material assertions do not imply experimental success."""

    def test_all_json_is_strict_and_source_identifiers_resolve(self):
        documents = {path.name: read_json(path) for path in ROOT.glob("*.json")}
        self.assertTrue(documents)
        provenance = documents["provenance.json"]
        evidence_ids = set(provenance["evidence"])
        unknown_ids = set(index_records(documents["unknown_parameters.json"]["unknowns"], "unknowns"))
        for name, document in documents.items():
            for path, key, value in walk(document):
                if key in {"evidence_ids", "unknown_ids", "required_unknown_ids", "unknown_parameter_ids", "required_input_ids", "blocked_by", "unresolved_source_groups"}:
                    allowed = evidence_ids if key == "evidence_ids" else unknown_ids
                    self.assertIsInstance(value, list, (name, path))
                    self.assertFalse(set(value) - allowed, (name, path, set(value) - allowed))

    def test_source_manifest_metadata_is_internally_consistent(self):
        provenance = read_json(ROOT / "provenance.json")
        audit = read_json(ROOT / "source_access_audit.json")
        rows = {row["file"]: row for row in audit["sources"]}
        self.assertEqual(len(rows), len(audit["sources"]))
        for record in provenance["sources"]:
            with self.subTest(source=record["file"]):
                self.assertTrue(record["bytes"] > 0)
                self.assertEqual(len(record["sha256"]), 64)
                self.assertTrue(all(character in "0123456789abcdef" for character in record["sha256"]))
                self.assertEqual(rows[record["file"]]["verified_sha256"], record["sha256"])
                self.assertTrue(rows[record["file"]]["hash_matches_manifest"])
                self.assertFalse(Path(record["file"]).is_absolute())
                self.assertNotIn("..", Path(record["file"]).parts)
        self.assertEqual(provenance["doi"], "10.1038/s41467-019-13319-7")
        self.assertFalse(provenance["execution"]["physical_simulation"])
        self.assertFalse(provenance["execution"]["robot_execution"])
        self.assertFalse(provenance["execution"]["new_scientific_measurements"])

    def test_optional_source_artifact_bytes(self):
        if SOURCE_DIR is None:
            self.skipTest("source bytes not bundled; use --source-dir PATH for optional hash verification")
        provenance = read_json(ROOT / "provenance.json")
        for record in provenance["sources"]:
            with self.subTest(source=record["file"]):
                relative = Path(record["file"])
                self.assertFalse(relative.is_absolute())
                self.assertNotIn("..", relative.parts)
                path = SOURCE_DIR / relative
                self.assertTrue(path.is_file(), str(path))
                data = path.read_bytes()
                self.assertEqual(len(data), record["bytes"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), record["sha256"])

    def test_material_controls_and_noninheritance(self):
        document = read_json(ROOT / "material_cards.json")
        materials = document["materials"]
        self.assertEqual(materials["cardboard"]["face_side_mm"], 24)
        self.assertEqual(materials["cardboard"]["face_thickness_mm"], 0.4)
        self.assertEqual(materials["pla_mylar"]["printed_parts_per_face"], 2)
        self.assertEqual(materials["pla_mylar"]["part_thickness_mm"], 0.5)
        self.assertEqual(materials["pla_mylar"]["hinge_thickness_um"], 50)
        self.assertNotIn("face_side_mm", materials["pla_mylar"])
        self.assertEqual(materials["cube_elastomer"]["hinge_thickness_mm"], 0.5)
        for key, thickness in [("array_50", 50), ("array_125", 125)]:
            self.assertEqual(materials[key]["hinge_thickness_um"], thickness)
            self.assertEqual(materials[key]["unit_array"], [2, 2, 2])
            self.assertEqual(math.prod(materials[key]["unit_array"]), 8)
            self.assertIsNone(materials[key]["face_material"])
        self.assertIsNone(materials["si_unspecified"]["face_material"])
        self.assertIsNone(materials["si_unspecified"]["hinge_material"])
        self.assertIsNone(materials["pneumatic_unspecified"]["pressure"])
        self.assertIn("No cross-material", document["inheritance_rule"])

    def test_unknown_critical_parameters_retain_explicit_gates(self):
        unknowns = index_records(read_json(ROOT / "unknown_parameters.json")["unknowns"], "unknowns")
        required = {"U_GEOM", "U_PRINT", "U_CUT", "U_LENGTH", "U_LOAD", "U_CYCLES", "U_ACTUATION", "U_ELASTOMER", "U_ARRAY_FACE", "U_ARRAY_TOPOLOGY", "U_SI_MATERIAL", "U_POUCH", "U_REPLICATES", "U_TARGETS", "U_HISTORY"}
        self.assertTrue(required <= set(unknowns), required - set(unknowns))
        for identifier, record in unknowns.items():
            with self.subTest(unknown=identifier):
                self.assertTrue(record["description"])
                gate = record["execution_gate"].lower()
                self.assertTrue("do not execute" in gate or "blocked" in gate)
                self.assertTrue("resolves" in gate or "until supplied" in gate)
                self.assertIn("qualified", gate)

    def test_source_disagreements_are_not_silently_removed(self):
        conflicts = index_records(read_json(ROOT / "source_conflicts.json")["conflicts"], "conflicts")
        self.assertTrue({"Q_PANEL", "Q_CYCLES", "Q_INSTABILITY", "Q_RELAXATION"} <= set(conflicts))
        self.assertIn("unknown", conflicts["Q_CYCLES"]["policy"].lower())
        self.assertIn("success oracle", conflicts["Q_INSTABILITY"]["policy"].lower())
        self.assertIn("unresolved", conflicts["Q_RELAXATION"]["policy"].lower())


class OperationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = read_json(ROOT / "operations.json")
        cls.operations = index_records(cls.document["operations"], "operations")

    def test_operation_count_fields_and_acyclic_dependencies(self):
        self.assertEqual(self.document["operation_count"], len(self.operations))
        self.assertEqual(self.document["visibility"], "evaluator_reference_only")
        edges = []
        for identifier, operation in self.operations.items():
            with self.subTest(operation=identifier):
                for key in ["location_id", "actions", "preconditions", "postconditions", "recovery"]:
                    self.assertTrue(operation[key], (identifier, key))
                self.assertEqual(operation["execution_mode"], "symbolic_design_only")
                self.assertEqual(len(operation["depends_on"]), len(set(operation["depends_on"])))
                edges.extend((dependency, identifier) for dependency in operation["depends_on"])
        self.assertTrue(edges, "a graph without edges cannot establish dependencies")
        self.assertEqual(set(validate_dag(self.operations, edges)), set(self.operations))

    def test_observe_follows_release_and_release_follows_actuation(self):
        for after, before in [("ACTUATE", "TARGET_STAGE"), ("RELEASE", "ACTUATE"), ("OBSERVE", "RELEASE"), ("TARGET_SUMMARY", "OBSERVE")]:
            self.assertIn(before, self.operations[after]["depends_on"])
        text = json.dumps(self.operations["RELEASE"]).lower()
        self.assertIn("held", text)
        self.assertIn("stable", text)

    def test_pneumatic_operations_retain_required_unknown_gate(self):
        for identifier in ["PNEU_PREP", "PNEU_CONNECT", "PNEU_PROGRAM", "PNEU_ACTUATE", "PNEU_VENT", "PNEU_DISCONNECT"]:
            self.assertIn("U_POUCH", self.operations[identifier]["unknown_parameter_ids"])
        for after, before in [("PNEU_CONNECT", "PNEU_PREP"), ("PNEU_PROGRAM", "PNEU_CONNECT"), ("PNEU_ACTUATE", "PNEU_PROGRAM"), ("PNEU_VENT", "PNEU_ACTUATE"), ("PNEU_DISCONNECT", "PNEU_VENT")]:
            self.assertIn(before, self.operations[after]["depends_on"])

    def test_numerical_model_increments_do_not_become_machine_settings(self):
        forbidden_setting_keys = {"numerical_stiffness_ratio", "physical_loading_increments", "instron_increments", "instron_steps", "load_increment_count", "unload_increment_count"}
        for identifier, operation in self.operations.items():
            for path, key, value in walk(operation):
                self.assertNotIn(key, forbidden_setting_keys, (identifier, path))
                if key.endswith(("_settings", "_settings_card", "_parameters")) and isinstance(value, dict):
                    self.assertNotIn(1000, value.values(), (identifier, path))


class PackageContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = {path.name: read_json(path) for path in ROOT.glob("*.json")}
        cls.ops = index_records(cls.documents["operations.json"]["operations"], "operations")
        cls.branch_document = cls.documents["branches.json"]
        cls.branches = index_records(cls.branch_document["branches"], "branches")
        cls.families = index_records(cls.branch_document["families"], "families")

    def test_artifacts_and_explicit_local_file_references_exist(self):
        required = {"TASK_DESIGN.md", "README.md", "agent_visible.json", "asset_needs.json", "branches.json", "control_packages.json", "coverage_matrix.json", "dependencies.json", "evaluator_reference.json", "episode_input_contract.json", "lineage_contract.json", "material_cards.json", "mock_contract.json", "nonmanual_scope.json", "operations.json", "provenance.json", "RELEASE_BOUNDARY.json", "source_conflicts.json", "source_outcomes.json", "station_contracts.json", "unknown_parameters.json", "independent_source_audit/audit.json"}
        self.assertFalse({name for name in required if not (ROOT / name).is_file()})
        for name, document in self.documents.items():
            for path, key, value in walk(document):
                if key.endswith("_file") and isinstance(value, str):
                    self.assertTrue((ROOT / value).is_file(), (name, path, value))
        release = self.documents["RELEASE_BOUNDARY.json"]
        for name in release["evaluator_only"] + release["author_review_only"]:
            self.assertTrue((ROOT / name).exists(), name)

    def test_all_operational_branch_family_station_and_control_refs_resolve(self):
        ids = {
            "operation_ids": set(self.ops),
            "conditional_recovery_operation_ids": set(self.ops),
            "family_ids": set(self.families),
            "branch_ids": set(self.branches),
            "task_branch_ids": set(self.branches),
            "nonmanual_ids": set(index_records(self.documents["nonmanual_scope.json"]["items"], "nonmanual")),
        }
        for name, document in self.documents.items():
            for path, key, value in walk(document):
                if key in ids:
                    self.assertIsInstance(value, list, (name, path))
                    self.assertFalse(set(value) - ids[key], (name, path, set(value) - ids[key]))
        stations = set(index_records(self.documents["station_contracts.json"]["stations"], "stations"))
        for operation in self.ops.values():
            self.assertIn(operation["location_id"], stations | {"route_destination", "all_selected_stations"})
        for branch in self.branches.values():
            for loop in branch["loops"]:
                for key in ["body", "between_conditions"]:
                    if isinstance(loop.get(key), list):
                        self.assertFalse(set(loop[key]) - set(branch["operation_ids"]), (branch["id"], loop["loop_id"], key))

    def test_dependency_artifact_equals_operation_graph_and_branches_are_closed(self):
        expected = {(dependency, op["id"]) for op in self.ops.values() for dependency in op["depends_on"]}
        actual = [(edge["from"], edge["to"]) for edge in self.documents["dependencies.json"]["edges"]]
        self.assertEqual(set(actual), expected)
        self.assertEqual(len(actual), len(set(actual)))
        validate_dag(self.ops, actual)
        for identifier, branch in self.branches.items():
            op_ids = set(branch["operation_ids"])
            self.assertEqual(len(op_ids), len(branch["operation_ids"]), identifier)
            missing = {dependency for op_id in op_ids for dependency in self.ops[op_id]["depends_on"]} - op_ids
            self.assertFalse(missing, (identifier, missing))
            validate_dag(op_ids, [(before, after) for before, after in actual if before in op_ids and after in op_ids])

    def test_seven_hands_on_families_and_twelve_configurations_are_covered(self):
        coverage = self.documents["coverage_matrix.json"]
        self.assertEqual(len(self.families), 7)
        self.assertEqual(len(self.branches), 12)
        self.assertEqual(self.branch_document["branch_count"], len(self.branches))
        self.assertEqual(coverage["hands_on_family_count"], len(self.families))
        self.assertEqual(coverage["task_configuration_count"], len(self.branches))
        rows = coverage["rows"]
        physical = [row for row in rows if row["classification"] == "hands_on_family"]
        self.assertEqual(len(physical), 7)
        covered = {identifier for row in physical for identifier in row["task_branch_ids"]}
        self.assertEqual(covered, set(self.branches) - {"WHOLE_PAPER_PRACTICAL"})
        campaign = self.branches["WHOLE_PAPER_PRACTICAL"]["loops"][0]
        self.assertEqual(set(campaign["values"]), covered)
        for row in physical:
            expected = {op for identifier in row["task_branch_ids"] for op in self.branches[identifier]["operation_ids"]}
            self.assertEqual(set(row["operation_ids"]), expected, row["source_branch_id"])
        for row in rows:
            if row["classification"] == "numerical_or_outlook_only":
                self.assertEqual(row["task_branch_ids"], [])
                self.assertEqual(row["operation_ids"], [])
                self.assertTrue(row["nonmanual_ids"])
        self.assertFalse(coverage["whole_paper_scope"]["full_operational_reconstruction"])

    def test_actor_projection_excludes_evaluator_graphs_and_source_oracles(self):
        actor = self.documents["agent_visible.json"]
        goals = index_records(actor["goals"], "actor goals")
        self.assertEqual(set(goals), set(self.branches))
        blocked_keys = {"operation_ids", "depends_on", "reference_sequence", "expected_outcome", "expected_outcomes", "retained_ids", "relax_after_release_ids", "fault_seed", "hidden_faults", "acceptance", "test_cases", "source_outcomes", "elastomer_retained_ids"}
        for path, key, value in walk(actor):
            self.assertNotIn(key, blocked_keys, path)
            if isinstance(value, str) and key.endswith("_file"):
                self.assertEqual(value, "material_cards.json")
        self.assertIn("only one selected", actor["release_rule"].lower())
        boundary = self.documents["RELEASE_BOUNDARY.json"]
        excluded = set(boundary["evaluator_only"])
        self.assertTrue({"operations.json", "branches.json", "dependencies.json", "evaluator_reference.json", "mock_contract.json", "source_outcomes.json", "tests/"} <= excluded)
        self.assertFalse(boundary["loader_implemented"])
        allowed = " ".join(boundary["actor_allowlist"])
        self.assertNotIn("source_outcomes.json", allowed)
        self.assertNotIn("evaluator_reference.json", allowed)

    def test_last_five_and_append_only_contracts_preserve_raw_truth(self):
        mock = self.documents["mock_contract.json"]
        self.assertEqual(mock["raw_mutability"], "append_only")
        self.assertIs(mock["missing_is_zero"], False)
        self.assertIs(mock["physical_simulation"], False)
        self.assertIs(mock["aggregation"]["require_same_condition"], True)
        self.assertIs(mock["aggregation"]["require_complete_load_unload"], True)
        self.assertIn("never backfill", mock["aggregation"]["invalid_final_cycle"])
        self.assertIsNone(mock["aggregation"]["unreported_independent_n"])
        self.assertTrue({"sample_id", "assembly_version", "run_id", "cycle_index", "leg", "condition_signature", "fixture_id", "calibration_id"} <= set(mock["binding_keys"]["compression"]))
        loops = {loop["loop_id"]: loop for loop in self.branches["PLA_MYLAR_CYCLIC"]["loops"]}
        self.assertIsNone(loops["cycles"]["count"])
        self.assertEqual(loops["cycles"]["minimum_for_summary"], 5)
        self.assertEqual(loops["cycles"]["body"], ["COMP_LOAD", "COMP_UNLOAD"])
        self.assertIn("invalid final", loops["cycles"]["aggregation"].lower())
        lineage = self.documents["lineage_contract.json"]
        self.assertTrue({"parent_ids", "assembly_version", "condition_history", "current_location"} <= set(lineage["required_entity_fields"]))
        invariants = " ".join(lineage["invariants"]).lower()
        self.assertIn("append-only", invariants)
        self.assertIn("never erases", invariants)
        self.assertIn("new id", invariants)

    def test_si6_labels_are_eleven_and_fifteen_arabic_display_identifiers(self):
        for identifier, total in [("SI6_TRUNCATED_CUBE", 11), ("SI6_RHOMBICUBOCTAHEDRON", 15)]:
            branch = self.branches[identifier]
            loop = next(loop for loop in branch["loops"] if loop["loop_id"] == "target_attempts")
            self.assertEqual(loop["values"], [str(i) for i in range(1, total + 1)])
            self.assertIn("not_exhaustive_or_replicate_count", loop["values_status"])
            self.assertIn("U_SI_MATERIAL", branch["required_input_ids"])
            self.assertIsNone(loop["inner_repetitions"]["value"])

    def test_array_unit_slots_and_material_control_inventory(self):
        branch = self.branches["ARRAY_THICKNESS_PAIR"]
        loops = {loop["loop_id"]: loop for loop in branch["loops"]}
        coordinates = loops["array_slots"]["values"]
        self.assertEqual(len(coordinates), 8)
        self.assertEqual({tuple(value) for value in coordinates}, {(x, y, z) for x in range(2) for y in range(2) for z in range(2)})
        self.assertIn("not 8 experimental specimens", loops["array_slots"]["semantics"])
        self.assertEqual(loops["array_thickness"]["values"], ["mylar_50um", "mylar_125um"])
        controls = index_records(self.documents["control_packages.json"]["control_packages"], "controls")
        self.assertEqual(controls["C_THICKNESS"]["conditions"], ["mylar_50um", "mylar_125um"])
        self.assertEqual(controls["C_HINGE"]["conditions"], ["mylar", "elastomer_0p5mm"])
        self.assertEqual(set(controls["C_FINITE"]["conditions"]), {"bulk_compatible", "edge_or_corner", "longer_than_one_cell"})

    def test_pneumatic_unknowns_block_program_expansion_and_truth_table_inference(self):
        branch = self.branches["PNEUMATIC_TWO_POUCH"]
        self.assertTrue({"U_GEOM", "U_POUCH", "U_ACTUATION"} <= set(branch["required_input_ids"]))
        loop = branch["loops"][0]
        self.assertIsNone(loop["values"])
        self.assertEqual(loop["values_from"], "pneumatic_card.program_ids")
        self.assertIn("unknown", loop["reported_context"])
        self.assertIn("Null loop", self.branch_document["cardinality_policy"])
        self.assertIn("block", self.branch_document["cardinality_policy"])
        source = index_records(self.documents["source_outcomes.json"]["outcomes"], "source outcomes")
        self.assertIsNone(source["O_PNEU"]["program_mapping"])

    def test_no_hard_coded_paper_outcome_success(self):
        evaluator = self.documents["evaluator_reference.json"]
        self.assertEqual(evaluator["visibility"], "never_include_in_agent_prompt")
        self.assertIn("never used as target acceptance", evaluator["independence"]["source_outcomes"])
        self.assertIn("scientific agreement is reported separately", evaluator["outcomes"]["complete"])
        self.assertIn("non-paper-trend", self.documents["mock_contract.json"]["no_source_oracle"])
        tests = index_records(evaluator["test_cases"], "declared adversarial cases")
        self.assertIn("Procedural pass permitted", tests["T_NONPAPER"]["expected"])
        outcome_keys = {"retained_ids", "relax_after_release_ids", "stretch_limited_ids", "elastomer_retained_ids", "expected_retained_count", "required_paper_result", "target_success_values"}
        for name in ["agent_visible.json", "operations.json", "branches.json", "evaluator_reference.json", "mock_contract.json"]:
            for path, key, value in walk(self.documents[name]):
                self.assertNotIn(key, outcome_keys, (name, path))


    def test_nested_material_target_coverage_is_explicit(self):
        cube = self.branches["CUBE_HINGE_COMPARISON"]["loop_expansion"]
        self.assertEqual(cube["outer"], "hinge_material")
        self.assertEqual(cube["inner"], ["target_attempts", "attempts_per_target"])
        grid = cube["condition_target_grid"]
        self.assertIs(grid["cartesian_product_required"], True)
        self.assertEqual(grid["conditions"], ["mylar", "elastomer_0p5mm"])
        self.assertEqual(grid["targets"], ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii"])
        self.assertEqual(grid["minimum_distinct_condition_target_cells"], 16)
        self.assertIn("not samples", grid["counts_are"])
        array = self.branches["ARRAY_THICKNESS_PAIR"]["loop_expansion"]
        self.assertEqual(array["outer"], "array_thickness")
        self.assertEqual(array["per_outer_setup_loop"], "array_slots")
        self.assertEqual(array["unit_slots_per_outer"], 8)
        self.assertIs(array["condition_target_grid"]["cartesian_product_required"], True)
        self.assertIs(array["condition_target_grid"]["null_target_list_blocks"], True)
        self.assertEqual(array["condition_target_grid"]["conditions"], ["mylar_50um", "mylar_125um"])
        for branch in self.branches.values():
            self.assertIn("QUARANTINE", branch["conditional_recovery_operation_ids"])
        used = {op for branch in self.branches.values() for op in branch["operation_ids"] + branch["conditional_recovery_operation_ids"]}
        self.assertEqual(used, set(self.ops))


    def test_episode_inputs_are_null_gated_without_physical_defaults(self):
        contract = self.documents["episode_input_contract.json"]
        self.assertIs(contract["implemented_loader"], False)
        self.assertIn("never substitute zero/empty list", contract["unknown_rule"])
        cards = index_records(contract["cards"], "episode input cards")
        for card in cards.values():
            self.assertTrue(card["required_fields"])
            self.assertEqual(len(card["required_fields"]), len(set(card["required_fields"])))
            self.assertTrue(card["unresolved_source_groups"])
        compression = cards["compression_card"]
        self.assertIsNone(compression["total_cycles_value"])
        self.assertIsNone(compression["loading_rate_value"])
        self.assertIsNone(compression["L_value"])
        self.assertIs(compression["numerical_settings_allowed_as_defaults"], False)
        self.assertEqual(compression["source_summary_cycle_count"], 5)
        pneumatic = cards["pneumatic_card"]
        for key in ["program_ids_value", "pressure_value", "mapping_value"]:
            self.assertIsNone(pneumatic[key])
        self.assertIs(pneumatic["source_state_count_is_program_count"], False)
        self.assertTrue({"eight_distinct_unit_ids", "slot_xyz_map", "unit_preparation_receipts"} <= set(cards["array_card"]["required_fields"]))


def validate_append_only(previous, current):
    """Compare two static ledger snapshots; no event generation occurs."""
    if len(current) < len(previous) or current[:len(previous)] != previous:
        raise ValueError("prior ledger records were deleted, reordered, or rewritten")
    index_records(current, "current ledger")
    return True


class PackageMutationTests(unittest.TestCase):
    """Mutations of actual package data prove important assertions fail closed."""

    @classmethod
    def setUpClass(cls):
        cls.baseline = {path.name: read_json(path) for path in ROOT.glob("*.json")}

    def probe(self, method, mutation):
        checker = PackageContractTests(method)
        checker.documents = copy.deepcopy(self.baseline)
        checker.ops = index_records(checker.documents["operations.json"]["operations"])
        checker.branch_document = checker.documents["branches.json"]
        checker.branches = index_records(checker.branch_document["branches"])
        checker.families = index_records(checker.branch_document["families"])
        mutation(checker)
        with self.assertRaises((AssertionError, ValueError)):
            getattr(checker, method)()

    def test_mutated_dependency_reference_is_rejected(self):
        self.probe("test_dependency_artifact_equals_operation_graph_and_branches_are_closed", lambda c: c.ops["PLAN"]["depends_on"].append("REPORT"))

    def test_mutated_branch_operation_reference_is_rejected(self):
        self.probe("test_all_operational_branch_family_station_and_control_refs_resolve", lambda c: c.branches["PLA_MYLAR_CYCLIC"]["operation_ids"].append("MISSING"))

    def test_actor_oracle_leak_is_rejected(self):
        self.probe("test_actor_projection_excludes_evaluator_graphs_and_source_oracles", lambda c: c.documents["agent_visible.json"]["goals"][0].update(retained_ids=["vi"]))

    def test_last_five_mixed_conditions_permission_is_rejected(self):
        self.probe("test_last_five_and_append_only_contracts_preserve_raw_truth", lambda c: c.documents["mock_contract.json"]["aggregation"].update(require_same_condition=False))

    def test_changed_si6_label_scheme_is_rejected(self):
        self.probe("test_si6_labels_are_eleven_and_fifteen_arabic_display_identifiers", lambda c: c.branches["SI6_TRUNCATED_CUBE"]["loops"][0]["values"].__setitem__(0, "i"))

    def test_missing_array_unit_slot_is_rejected(self):
        self.probe("test_array_unit_slots_and_material_control_inventory", lambda c: next(loop for loop in c.branches["ARRAY_THICKNESS_PAIR"]["loops"] if loop["loop_id"] == "array_slots")["values"].pop())

    def test_dropped_material_condition_is_rejected(self):
        self.probe("test_array_unit_slots_and_material_control_inventory", lambda c: next(control for control in c.documents["control_packages.json"]["control_packages"] if control["id"] == "C_HINGE")["conditions"].pop())

    def test_inferred_pneumatic_truth_table_is_rejected(self):
        self.probe("test_pneumatic_unknowns_block_program_expansion_and_truth_table_inference", lambda c: c.branches["PNEUMATIC_TWO_POUCH"]["loops"][0].update(values=["00", "01", "10", "11"]))

    def test_hardcoded_source_success_is_rejected(self):
        self.probe("test_no_hard_coded_paper_outcome_success", lambda c: c.documents["evaluator_reference.json"].update(expected_retained_count=7))

    def test_flattened_material_target_grid_is_rejected(self):
        self.probe("test_nested_material_target_coverage_is_explicit", lambda c: c.branches["CUBE_HINGE_COMPARISON"]["loop_expansion"]["condition_target_grid"].update(cartesian_product_required=False))

    def test_attempt_snapshot_deletion_or_rewrite_is_rejected(self):
        before = [{"id": "A1", "status": "failed"}]
        after = before + [{"id": "A2", "status": "complete", "retry_of": "A1"}]
        self.assertTrue(validate_append_only(before, after))
        for changed in [[], [{"id": "A1", "status": "complete"}], after[::-1], before + before]:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                validate_append_only(before, changed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--source-dir", type=Path, help="Optional external cache of source files named in provenance.json; never read paths embedded in the package")
    options, remaining = parser.parse_known_args()
    SOURCE_DIR = options.source_dir
    unittest.main(argv=[sys.argv[0], *remaining], verbosity=2)
