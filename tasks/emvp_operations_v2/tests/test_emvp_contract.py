#!/usr/bin/env python3
"""Independent, standard-library-only EmVP design/record contract tests.

These are static assertions over authored files and synthetic bookkeeping
fixtures. They are not a loader, robot task runner, printer controller, physical
model, scientific reproduction, or evidence of experimental success. Numeric
fixture values are arbitrary checker examples, never operating instructions.

Run from the package root: python -m unittest discover -s tests -v
Use the companion run_validation.py for JSON and Markdown test reports.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(os.environ.get("EMVP_TASK_ROOT", Path(__file__).resolve().parents[1]))
SOURCE_DIR = None  # An explicit runner --source-dir argument is required.


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    def reject_constant(value):
        raise ValueError(f"nonfinite number: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8"),
                      object_pairs_hook=reject_duplicates, parse_constant=reject_constant)


def walk(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield path + (str(key),), key, child
            yield from walk(child, path + (str(key),))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, path + (str(index),))


def index_records(records, name="records"):
    if not isinstance(records, list) or not records:
        raise ValueError(f"{name}: expected a nonempty list")
    result = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str) or not record["id"]:
            raise ValueError(f"{name}: missing string ID")
        if record["id"] in result:
            raise ValueError(f"{name}: duplicate ID {record['id']}")
        result[record["id"]] = record
    return result


def validate_dag(node_ids, edges):
    nodes = set(node_ids)
    adjacency = {node: set() for node in nodes}
    indegree = {node: 0 for node in nodes}
    for before, after in edges:
        if before not in nodes or after not in nodes:
            raise ValueError(f"dangling edge: {before} -> {after}")
        if after not in adjacency[before]:
            adjacency[before].add(after)
            indegree[after] += 1
    frontier = [node for node, count in indegree.items() if count == 0]
    ordered = []
    while frontier:
        node = frontier.pop()
        ordered.append(node)
        for child in adjacency[node]:
            indegree[child] -= 1
            if indegree[child] == 0:
                frontier.append(child)
    if len(ordered) != len(nodes):
        raise ValueError("cyclic dependencies")
    return ordered


def require_resolved(required_ids, resolutions):
    for identifier in required_ids:
        record = resolutions.get(identifier)
        if not isinstance(record, dict):
            raise ValueError(f"unresolved input {identifier}")
        value = record.get("value")
        if value is None or value in ("", [], {}) or isinstance(value, bool) or (isinstance(value, (int, float)) and not math.isfinite(value)):
            raise ValueError(f"unresolved input {identifier}")
        if record.get("origin") not in {"qualified_episode_input", "authored_qualified_input"}:
            raise ValueError(f"unqualified input {identifier}")
        if not record.get("qualification_record_id"):
            raise ValueError(f"unqualified input {identifier}")
    return True


def validate_geometry(card):
    if not isinstance(card, dict) or not card.get("geometry_id") or not card.get("qualification_record_id"):
        raise ValueError("qualified geometry is missing")
    if not card.get("feature_ids") or len(set(card["feature_ids"])) != len(card["feature_ids"]):
        raise ValueError("geometry must contain distinct intended features")
    if card.get("no_op") is not False or not card.get("coordinate_frame_id") or not card.get("alignment_record_id"):
        raise ValueError("no-op, unaligned or unknown-frame geometry is blocked")
    if card.get("geometry_origin") not in {"qualified_episode_input", "authored_qualified_input"}:
        raise ValueError("unqualified geometry is blocked")
    return True


def validate_printer(card):
    if not isinstance(card, dict) or not card.get("printer_id") or card.get("qualification_status") != "qualified":
        raise ValueError("no qualified printer")
    if not card.get("configuration_record_id") or not card.get("calibration_record_id"):
        raise ValueError("printer configuration or calibration missing")
    if card.get("hardware_origin") not in {"existing_custom_configured", "qualified_equivalent"}:
        raise ValueError("reported custom configuration is not a fabrication recipe")
    return True


def validate_transfer(record):
    required = {"sample_id", "from_station_id", "to_station_id", "before_frame_id", "after_frame_id", "orientation_record_id", "transfer_record_id"}
    if any(not record.get(key) for key in required):
        raise ValueError("transfer context is incomplete")
    if record.get("frame_retained") is not True or record["before_frame_id"] != record["after_frame_id"]:
        raise ValueError("off-frame transfer breaks retained-frame lineage")
    if record.get("orientation_verified") is not True:
        raise ValueError("orientation not verified")
    return True


def validate_postcure(record):
    if record.get("branch") not in {"positive", "negative"}:
        raise ValueError("unknown branch")
    if not record.get("sample_id") or not record.get("postcure_record_id"):
        raise ValueError("postcure identity missing")
    if record["branch"] == "negative":
        if record.get("flush_status") != "verified_complete" or not record.get("flush_record_id"):
            raise ValueError("negative channels must be flushed before postcure")
        if type(record.get("flush_ordinal")) is not int or type(record.get("postcure_ordinal")) is not int or record["flush_ordinal"] >= record["postcure_ordinal"]:
            raise ValueError("flush must precede postcure")
    return True


def validate_lineage(records):
    by_id = index_records(records, "sample/entity ledger")
    edges = []
    for record in records:
        if not isinstance(record.get("location_id"), str) or not record["location_id"]:
            raise ValueError("entity location must be singular")
        for parent in record.get("parent_ids", []):
            if parent not in by_id:
                raise ValueError("missing lineage parent")
            edges.append((parent, record["id"]))
    validate_dag(by_id, edges)
    return True


def validate_raw_and_derived(raw_records, derived_records):
    raw = index_records(raw_records, "raw records")
    required = {"sample_id", "trial_id", "condition_id", "instrument_id", "calibration_id", "settings_id", "acquisition_timestamp", "context_id", "raw_sha256"}
    for record in raw_records:
        if any(not record.get(key) for key in required):
            raise ValueError("raw acquisition context missing")
        if record.get("origin") != "acquisition_record" or record.get("authenticity_status") != "verified":
            raise ValueError("absent, synthetic, forged, or unverified acquisition evidence")
        if not re.fullmatch(r"[0-9a-f]{64}", record["raw_sha256"]):
            raise ValueError("invalid raw digest")
    index_records(derived_records, "derived records")
    for record in derived_records:
        parents = record.get("raw_record_ids")
        if not parents or len(set(parents)) != len(parents) or set(parents) - set(raw):
            raise ValueError("derived record has absent or invalid raw lineage")
        if not record.get("analysis_version") or not record.get("method_id"):
            raise ValueError("derived analysis provenance missing")
        if any(raw[identifier]["sample_id"] != record.get("sample_id") or raw[identifier]["condition_id"] != record.get("condition_id") for identifier in parents):
            raise ValueError("derived record combines a different sample or condition")
    return True


def validate_clocks(record):
    for key in ["led_on_event_id", "measurement_start_event_id", "led_on_timestamp", "measurement_start_timestamp", "measurement_clock_origin", "reported_clock_origin"]:
        if record.get(key) is None:
            raise ValueError("both clocks and event identities are required")
    if record["led_on_event_id"] == record["measurement_start_event_id"]:
        raise ValueError("LED-on and measurement-start events must remain distinct")
    if record["measurement_clock_origin"] != "measurement_start" or record["reported_clock_origin"] not in {"measurement_start", "led_on"}:
        raise ValueError("clock origins have been conflated")
    for key in ["led_on_timestamp", "measurement_start_timestamp", "led_to_measurement_offset"]:
        if type(record.get(key)) not in (int, float) or not math.isfinite(record[key]):
            raise ValueError("clock values must be finite numeric values")
    offset = record["measurement_start_timestamp"] - record["led_on_timestamp"]
    if not isinstance(record.get("led_to_measurement_offset"), (float, int)) or not math.isclose(offset, record["led_to_measurement_offset"]):
        raise ValueError("clock translation is not supported by paired timestamps")
    return True


def validate_diameter(record):
    if not record.get("sample_id") or not record.get("needle_id") or record.get("needle_nominal_size") is None:
        raise ValueError("needle metadata missing")
    if record.get("reported_diameter") is not None:
        if record.get("diameter_basis") != "measured" or not record.get("measurement_record_id"):
            raise ValueError("needle nominal size is not a measured channel/filament diameter")
    return True


def validate_timing_row(record, rows):
    if record.get("source_row_id") not in rows:
        raise ValueError("timing row missing")
    source = rows[record["source_row_id"]]
    for key in ["chip_id", "branch", "geometry_id", "reported_seconds"]:
        if record.get(key) != source.get(key):
            raise ValueError(f"timing row/context mismatch: {key}")
    if record.get("unit") != "seconds":
        raise ValueError("source printing time is tabulated in seconds")
    return True


def validate_oozing(record):
    if record.get("pre_cure_observation") == "oozing" and record.get("final_outcome") == "failed":
        if record.get("post_cure_observed") is not True or not record.get("post_cure_record_id"):
            raise ValueError("oozing alone cannot establish final post-cure failure")
    return True


def validate_trials(acquired, reported_ids, exclusions, counts):
    by_id = index_records(acquired, "attempt ledger")
    ordinals = [record.get("ordinal") for record in acquired]
    if any(type(value) is not int for value in ordinals) or ordinals != sorted(set(ordinals)):
        raise ValueError("attempt ledger order is not append-only")
    if len(set(reported_ids)) != len(reported_ids) or set(reported_ids) - set(by_id):
        raise ValueError("invalid reported trial IDs")
    if set(reported_ids) & set(exclusions) or set(reported_ids) | set(exclusions) != set(by_id):
        raise ValueError("unreported or cherry-picked attempts")
    for identifier, exclusion in exclusions.items():
        if not exclusion.get("reason") or not exclusion.get("prespecified_rule_id"):
            raise ValueError("post-hoc unexplained trial exclusion")
    expected_counts = {"attempt_count": len(acquired), "reported_count": len(reported_ids), "excluded_count": len(exclusions), "independent_sample_count": len({row["sample_id"] for row in acquired})}
    if counts != expected_counts:
        raise ValueError("sample/trial counts are underreported or conflated")
    return True


def validate_sample_route(record):
    if record.get("measurement") == "hardness" and record.get("preparation_route") != "printed":
        raise ValueError("reported hardness samples were printed")
    if record.get("measurement") == "tensile" and record.get("preparation_route") != "cast":
        raise ValueError("reported tensile samples were cast")
    return True


def validate_append_only(previous, current):
    if len(current) < len(previous) or current[:len(previous)] != previous:
        raise ValueError("raw ledger deleted, reordered or overwritten")
    index_records(current)
    return True


def validate_export_member(value):
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", value) or "\\" in value:
        raise ValueError("export members must be safe package-relative paths")
    if any(part in {".git", "source_cache", "publisher_assets"} for part in path.parts):
        raise ValueError("remote or source-cache content is outside export")
    if path.suffix.lower() in {".pdf", ".tif", ".tiff", ".png", ".jpg", ".jpeg", ".mp4", ".zip"}:
        raise ValueError("source or opaque binary bytes are outside this authored-text export")
    return True


class CheckerMutationTests(unittest.TestCase):
    """Adversarial synthetic records establish that checkers fail closed."""

    def test_duplicate_keys_nonfinite_json_and_bad_graphs(self):
        with self.assertRaises(ValueError):
            json.loads('{"x": 1, "x": 2}', object_pairs_hook=reject_duplicates)
        with tempfile.TemporaryDirectory() as directory:
            bad_json = Path(directory) / "bad.json"
            for value in ["NaN", "Infinity", "-Infinity"]:
                bad_json.write_text('{"x": ' + value + '}', encoding="utf-8")
                with self.subTest(value=value), self.assertRaises(ValueError):
                    read_json(bad_json)
        self.assertEqual(set(validate_dag({"A", "B"}, [("A", "B")])), {"A", "B"})
        for edges in [[("A", "A")], [("A", "B"), ("B", "A")], [("A", "unknown")]]:
            with self.subTest(edges=edges), self.assertRaises(ValueError):
                validate_dag({"A", "B"}, edges)

    def test_missing_recipe_ambiguity_resolution_is_blocked(self):
        required = ["acetone_quantity", "cq_edab_mass_fraction_interpretation"]
        good = {key: {"value": "explicitly supplied recipe field", "origin": "qualified_episode_input", "qualification_record_id": "Q1"} for key in required}
        self.assertTrue(require_resolved(required, good))
        for bad in [None, "", [], {}, False, float("nan"), float("inf")]:
            changed = copy.deepcopy(good)
            changed[required[0]]["value"] = bad
            with self.subTest(value=bad), self.assertRaises(ValueError):
                require_resolved(required, changed)
        for mutation in [lambda x: x.pop(required[1]), lambda x: x[required[0]].update(origin="source_inferred"), lambda x: x[required[0]].pop("qualification_record_id")]:
            changed = copy.deepcopy(good)
            mutation(changed)
            with self.assertRaises(ValueError):
                require_resolved(required, changed)

    def test_missing_and_noop_geometry_are_rejected(self):
        good = {"geometry_id": "G1", "qualification_record_id": "QG", "feature_ids": ["F1"], "coordinate_frame_id": "FRAME1", "alignment_record_id": "ALIGN1", "no_op": False, "geometry_origin": "qualified_episode_input"}
        self.assertTrue(validate_geometry(good))
        for changes in [{"feature_ids": []}, {"no_op": True}, {"geometry_id": None}, {"alignment_record_id": None}, {"geometry_origin": "guessed_from_figure"}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_geometry({**good, **changes})

    def test_no_qualified_printer_blocks_and_fabrication_is_not_inferred(self):
        good = {"printer_id": "P1", "qualification_status": "qualified", "configuration_record_id": "CONFIG1", "calibration_record_id": "CAL1", "hardware_origin": "existing_custom_configured"}
        self.assertTrue(validate_printer(good))
        for changes in [{"printer_id": None}, {"qualification_status": "assumed"}, {"calibration_record_id": None}, {"hardware_origin": "fabricated_from_public_paper"}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_printer({**good, **changes})

    def test_off_frame_or_unverified_orientation_transfer_is_rejected(self):
        good = {"sample_id": "S1", "from_station_id": "A", "to_station_id": "B", "before_frame_id": "FRAME1", "after_frame_id": "FRAME1", "orientation_record_id": "ORIENT1", "transfer_record_id": "MOVE1", "frame_retained": True, "orientation_verified": True}
        self.assertTrue(validate_transfer(good))
        for changes in [{"after_frame_id": "FRAME2"}, {"frame_retained": False}, {"orientation_verified": False}, {"orientation_record_id": None}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_transfer({**good, **changes})

    def test_negative_unflushed_postcure_is_rejected(self):
        good = {"branch": "negative", "sample_id": "S1", "flush_status": "verified_complete", "flush_record_id": "FLUSH1", "flush_ordinal": 1, "postcure_ordinal": 2, "postcure_record_id": "CURE1"}
        self.assertTrue(validate_postcure(good))
        for changes in [{"flush_status": "not_done"}, {"flush_record_id": None}, {"flush_ordinal": 3}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_postcure({**good, **changes})

    def record_fixture(self):
        raw = [{"id": "RAW1", "sample_id": "S1", "trial_id": "T1", "condition_id": "COND1", "instrument_id": "INST1", "calibration_id": "CAL1", "settings_id": "SET1", "acquisition_timestamp": "fixture-clock", "context_id": "CTX1", "raw_sha256": "a" * 64, "origin": "acquisition_record", "authenticity_status": "verified"}]
        derived = [{"id": "D1", "sample_id": "S1", "condition_id": "COND1", "raw_record_ids": ["RAW1"], "analysis_version": "fixture_v1", "method_id": "M1"}]
        return raw, derived

    def test_forged_absent_or_context_free_data_are_rejected(self):
        raw, derived = self.record_fixture()
        self.assertTrue(validate_raw_and_derived(raw, derived))
        for changes in [{"origin": "invented"}, {"authenticity_status": "forged"}, {"authenticity_status": "unknown"}, {"calibration_id": None}, {"context_id": None}, {"raw_sha256": "invalid"}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_raw_and_derived([{**raw[0], **changes}], derived)
        for changes in [{"raw_record_ids": []}, {"raw_record_ids": ["ABSENT"]}, {"sample_id": "S2"}, {"condition_id": "COND2"}, {"analysis_version": None}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_raw_and_derived(raw, [{**derived[0], **changes}])

    def test_led_on_and_measurement_start_clocks_cannot_be_conflated(self):
        good = {"led_on_event_id": "LED1", "measurement_start_event_id": "ACQ1", "led_on_timestamp": 10, "measurement_start_timestamp": 20, "led_to_measurement_offset": 10, "measurement_clock_origin": "measurement_start", "reported_clock_origin": "led_on"}
        self.assertTrue(validate_clocks(good))
        for changes in [{"measurement_start_event_id": "LED1"}, {"measurement_clock_origin": "led_on"}, {"led_to_measurement_offset": 0}, {"led_on_timestamp": None}, {"led_on_timestamp": float("nan")}, {"led_to_measurement_offset": True}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_clocks({**good, **changes})

    def test_needle_size_is_not_measured_diameter(self):
        good = {"sample_id": "S1", "needle_id": "N1", "needle_nominal_size": "nominal_metadata", "reported_diameter": 1.23, "diameter_basis": "measured", "measurement_record_id": "MEAS1"}
        self.assertTrue(validate_diameter(good))
        for changes in [{"diameter_basis": "needle_nominal"}, {"measurement_record_id": None}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_diameter({**good, **changes})

    def test_print_timing_chip_row_mismatch_and_unit_drift_are_rejected(self):
        rows = {"ROW1": {"chip_id": "CHIP1", "branch": "positive", "geometry_id": "G1", "reported_seconds": 9}}
        good = {"source_row_id": "ROW1", **rows["ROW1"], "unit": "seconds"}
        self.assertTrue(validate_timing_row(good, rows))
        for changes in [{"chip_id": "CHIP2"}, {"branch": "negative"}, {"geometry_id": "G2"}, {"reported_seconds": 99}, {"unit": "hours"}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_timing_row({**good, **changes}, rows)

    def test_oozing_does_not_automatically_fail_before_cure(self):
        good = {"pre_cure_observation": "oozing", "final_outcome": "unresolved", "post_cure_observed": False}
        self.assertTrue(validate_oozing(good))
        with self.assertRaises(ValueError):
            validate_oozing({**good, "final_outcome": "failed"})
        self.assertTrue(validate_oozing({**good, "final_outcome": "failed", "post_cure_observed": True, "post_cure_record_id": "OBS1"}))

    def test_cherry_picked_trials_and_underreported_counts_are_rejected(self):
        acquired = [{"id": "T1", "ordinal": 1, "sample_id": "S1", "status": "valid"}, {"id": "T2", "ordinal": 2, "sample_id": "S1", "status": "failed"}, {"id": "T3", "ordinal": 3, "sample_id": "S2", "status": "valid"}]
        counts = {"attempt_count": 3, "reported_count": 3, "excluded_count": 0, "independent_sample_count": 2}
        self.assertTrue(validate_trials(acquired, ["T1", "T2", "T3"], {}, counts))
        with self.assertRaises(ValueError):
            validate_trials(acquired, ["T1", "T3"], {}, counts)
        with self.assertRaises(ValueError):
            validate_trials(acquired, ["T1", "T3"], {"T2": {"reason": "unfavorable"}}, {**counts, "reported_count": 2, "excluded_count": 1})
        for changes in [{"attempt_count": 2}, {"independent_sample_count": 3}, {"reported_count": 2}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_trials(acquired, ["T1", "T2", "T3"], {}, {**counts, **changes})

    def test_sample_routes_are_printed_hardness_and_cast_tensile(self):
        for measurement, route in [("hardness", "printed"), ("tensile", "cast")]:
            self.assertTrue(validate_sample_route({"measurement": measurement, "preparation_route": route}))
            with self.assertRaises(ValueError):
                validate_sample_route({"measurement": measurement, "preparation_route": "cast" if route == "printed" else "printed"})

    def test_lineage_cycles_missing_parents_and_overwrite_are_rejected(self):
        good = [{"id": "LOT1", "parent_ids": [], "location_id": "STOCK"}, {"id": "S1", "parent_ids": ["LOT1"], "location_id": "FRAME1"}]
        self.assertTrue(validate_lineage(good))
        for mutation in [lambda x: x[1].update(parent_ids=["ABSENT"]), lambda x: x[0].update(parent_ids=["S1"]), lambda x: x[1].update(location_id=["A", "B"])]:
            changed = copy.deepcopy(good)
            mutation(changed)
            with self.assertRaises(ValueError):
                validate_lineage(changed)
        self.assertTrue(validate_append_only(good[:1], good))
        for bad in [good[:1], good[::-1], [{**good[0], "location_id": "REWRITTEN"}, good[1]]]:
            with self.assertRaises(ValueError):
                validate_append_only(good, bad)

    def test_no_remote_export_paths_or_public_source_bytes(self):
        self.assertTrue(validate_export_member("operations.json"))
        for bad in ["/tmp/source.pdf", "../source.pdf", "https://host/design.json", "file:///source", "publisher_assets/page.png", "source_cache/article.txt", "paper.pdf", "SI.mp4", ".git/config", "..\\secrets"]:
            with self.subTest(path=bad), self.assertRaises(ValueError):
                validate_export_member(bad)


class SourceContractTests(unittest.TestCase):
    """Package source metadata checks, independent of scientific outcomes."""

    @classmethod
    def setUpClass(cls):
        cls.documents = {path.name: read_json(path) for path in ROOT.glob("*.json")}

    def test_strict_json_and_all_source_unknown_references_resolve(self):
        self.assertTrue(self.documents)
        provenance = self.documents["provenance.json"]
        locators = set(index_records(provenance["locators"], "source locators"))
        unknowns = set(index_records(self.documents["unknown_parameters.json"]["unknowns"], "unknowns"))
        for name, document in self.documents.items():
            for path, key, value in walk(document):
                if key in {"source_refs", "required_unknowns", "unknown_ids", "unresolved_source_groups"}:
                    allowed = locators if key == "source_refs" else unknowns
                    self.assertIsInstance(value, list, (name, path))
                    self.assertEqual(len(value), len(set(value)), (name, path))
                    self.assertFalse(set(value) - allowed, (name, path, set(value) - allowed))

    def test_source_identity_and_locator_pages_are_consistent(self):
        provenance = self.documents["provenance.json"]
        self.assertEqual(provenance["doi"], "10.1038/s41467-025-62057-6")
        self.assertIs(provenance["source_bytes_in_export"], False)
        sources = index_records(provenance["sources"], "sources")
        self.assertEqual(set(sources), {"MAIN", "SI"})
        for source in sources.values():
            self.assertRegex(source["sha256"], r"^[0-9a-f]{64}$")
            self.assertGreater(source["pages"], 0)
            name = Path(source["filename"])
            self.assertFalse(name.is_absolute())
            self.assertNotIn("..", name.parts)
            self.assertFalse((ROOT / name).exists(), "source bytes must stay outside authored export")
        for locator in provenance["locators"]:
            self.assertIn(locator["source"], sources)
            self.assertTrue(locator["pdf_pages"])
            self.assertTrue(all(1 <= page <= sources[locator["source"]]["pages"] for page in locator["pdf_pages"]))
            self.assertTrue(locator["locator"])
            self.assertTrue(locator["scope"])

    def test_unknowns_remain_explicit_qualified_input_gates(self):
        unknowns = index_records(self.documents["unknown_parameters.json"]["unknowns"])
        required = {"U_ACETONE", "U_CQ_EDAB", "U_RECIPE_BASIS", "U_BATCH_ALLOCATION", "U_DEVICE_QUAL", "U_EXTRUSION_QUAL", "U_VAM_QUAL", "U_GEOMETRY", "U_TOOLPATH", "U_PROJECTIONS", "U_ALIGNMENT", "U_SHADOWGRAM", "U_FLUSH", "U_POSTCURE", "U_PHOTORHEO", "U_HARDNESS", "U_CAST_TENSILE", "U_SCHEDULE"}
        self.assertTrue(required <= set(unknowns), required - set(unknowns))
        for unknown in unknowns.values():
            self.assertIsNone(unknown["value"], unknown["id"])
            self.assertIn("qualified", unknown["resolution_contract"].lower())
            self.assertIn("provenance", unknown["resolution_contract"].lower())
            self.assertIn("block", unknown["if_missing"].lower())
            self.assertIn("never", unknown["if_missing"].lower())
            self.assertIn("zero", unknown["if_missing"].lower())

    def test_recipe_ambiguities_are_gated_per_material(self):
        materials = index_records(self.documents["material_cards.json"]["materials"])
        self.assertIn("U_ACETONE", materials["MAT2"]["required_unknowns"])
        self.assertIn("U_CQ_EDAB", materials["MAT1"]["required_unknowns"])
        self.assertNotIn("U_CQ_EDAB", materials["MAT2"]["required_unknowns"])
        self.assertFalse({"U_ACETONE", "U_CQ_EDAB"} & set(materials["SACRIFICIAL"]["required_unknowns"]))
        initiator = next(component for component in materials["MAT1"]["components"] if component["name"] == "CQ and EDAB")
        self.assertEqual(initiator["each_or_combined"], "unresolved")
        self.assertNotIn("cq_wt_percent", initiator)
        self.assertNotIn("edab_wt_percent", initiator)
        self.assertIn("capacity", self.documents["material_cards.json"]["unit_warning"])

    def test_custom_configured_hardware_is_not_missing_fabrication(self):
        station_document = self.documents["station_contracts.json"]
        stations = index_records(station_document["stations"])
        self.assertTrue({"U_DEVICE_QUAL", "U_EXTRUSION_QUAL"} <= set(stations["EMB"]["required_unknowns"]))
        self.assertTrue({"U_DEVICE_QUAL", "U_VAM_QUAL"} <= set(stations["VAM"]["required_unknowns"]))
        text = station_document["hardware_boundary"].lower()
        for token in ["construction", "external", "never", "reconstructed"]:
            self.assertIn(token, text)
        for station in stations.values():
            self.assertIn("no operational asset", station["status"].lower())

    def test_optional_source_bytes_sha256(self):
        if SOURCE_DIR is None:
            self.skipTest("source bytes not bundled; no explicit --source-dir supplied")
        for source in self.documents["provenance.json"]["sources"]:
            relative = Path(source["filename"])
            self.assertFalse(relative.is_absolute())
            self.assertNotIn("..", relative.parts)
            path = (SOURCE_DIR / relative).resolve()
            self.assertTrue(path.is_relative_to(SOURCE_DIR.resolve()))
            self.assertTrue(path.is_file(), source["filename"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), source["sha256"], source["id"])


class OperationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = read_json(ROOT / "operations.json")
        cls.operations = index_records(cls.document["operations"], "operations")

    def test_each_operation_has_physical_context_evidence_and_recovery(self):
        stations = set(index_records(read_json(ROOT / "station_contracts.json")["stations"]))
        for operation in self.operations.values():
            with self.subTest(operation=operation["id"]):
                self.assertIn(operation["station"], stations)
                for key in ["label", "physical_action", "preconditions", "completion_evidence", "recovery", "source_refs"]:
                    self.assertTrue(operation[key], key)
                self.assertIn(operation["kind"], {"researcher_operation", "qualified_analysis_handoff"})
                self.assertRegex(operation["recovery"].lower(), r"retain|preserve|keep|record actual")
        self.assertIn("no controller", self.document["robot_scope"].lower())
        self.assertIn("independent n", self.document["reuse"])

    def test_physical_transfer_and_alignment_are_explicit(self):
        transfer = self.operations["O_TRANSFER_ALIGN"]
        self.assertIn("U_ALIGNMENT", transfer["required_unknowns"])
        text = json.dumps(transfer).lower()
        for token in ["same vial", "orientation", "frame transform", "source-release", "transit", "target-dock", "no teleportation"]:
            self.assertIn(token, text)
        self.assertIn("U_ALIGNMENT", self.operations["O_DOCK_EMB"]["required_unknowns"])
        self.assertIn("U_ALIGNMENT", self.operations["O_VAM_DIRECT"]["required_unknowns"])

    def test_acquisitions_require_actual_raw_records(self):
        for identifier in ["O_UVVIS_SCAN", "O_CT_SCAN", "O_TENSILE"]:
            text = json.dumps(self.operations[identifier]).lower()
            self.assertIn("raw", text, identifier)
        reconstruction = json.dumps(self.operations["O_CT_RECON_HANDOFF"]).lower()
        for token in ["actual", "projection", "settings", "derived", "provenance"]:
            self.assertIn(token, reconstruction)
        distance = json.dumps(self.operations["O_DISTANCE_HANDOFF"]).lower()
        self.assertIn("paper mean is context, not acceptance tolerance", distance)

    def test_needle_observation_and_precure_oozing_keep_distinct_semantics(self):
        negative = json.dumps(self.operations["O_DEPOSIT_NEG"]).lower()
        self.assertIn("needle id and measured channel diameter are separate", negative)
        positive = json.dumps(self.operations["O_DEPOSIT_POS"]).lower()
        self.assertIn("no final-part failure inferred solely from uncured oozing", positive)
        inspect = json.dumps(self.operations["O_INSPECT_EMBED"]).lower()
        self.assertIn("no automatic final-geometry judgment", inspect)

    def test_printed_hardness_and_cast_tensile_have_distinct_lineage(self):
        hardness = json.dumps(self.operations["O_SHORE_MOUNT"]).lower()
        tensile = json.dumps(self.operations["O_TENSILE_MOUNT"]).lower()
        self.assertIn("printed manufacture lineage", hardness)
        self.assertIn("cast", tensile)
        self.assertIn("U_HARDNESS", self.operations["O_SHORE_MOUNT"]["required_unknowns"])
        self.assertIn("U_CAST_TENSILE", self.operations["O_TENSILE_MOUNT"]["required_unknowns"])
        self.assertIn("cast identity cannot be relabelled as a printed control", json.dumps(self.operations["O_CAST"]).lower())
        self.assertIn("specimen count kept separate", json.dumps(self.operations["O_SHORE_PROBE"]).lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
