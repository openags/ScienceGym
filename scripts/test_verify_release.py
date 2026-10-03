"""Failure-path tests for the offline release checker (synthetic fixtures only)."""

from contextlib import redirect_stdout, redirect_stderr
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("verify_release", Path(__file__).with_name("verify_release.py"))
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


class ReleaseVerifierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write_json(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def image_fixture(self):
        """Minimal byte fixtures test hashing, without pretending to decode JPEGs."""
        exports = []
        for player in verify.PLAYERS:
            base = self.root / "viewer" / player
            entries = []
            for name in ("frames/01_TEST.jpg", "overview.jpg", "keyframes_contact_sheet.jpg"):
                path = base / name
                path.parent.mkdir(parents=True, exist_ok=True)
                data = (player + "/" + name).encode("utf-8")
                path.write_bytes(data)
                digest = hashlib.sha256(data).hexdigest()
                entries.append({"path": name, "sha256": digest, "bytes": len(data)})
            self.write_json(base / "frame_manifest.json", {
                "overview": "overview.jpg",
                "frames": [{"image": entries[0]["path"], "image_sha256": entries[0]["sha256"]}],
            })
            key = "final_image_hashes" if player == "embodied_r01" else "frame_sha256"
            self.write_json(base / "render_receipt.json", {
                key: {entries[0]["path"]: entries[0]["sha256"]},
                "overview_sha256": entries[1]["sha256"],
                "source_scene_sha256": "unbundled source is deliberately not checked",
            })
            if player == "embodied_r01":
                exports = [dict(entry, path=f"viewer/{player}/{entry['path']}") for entry in entries]
            else:
                self.write_json(base / "PUBLIC_FILE_MANIFEST.json", {"files": entries})
                (base / "SHA256SUMS").write_text("".join(
                    f"{entry['sha256']}  {entry['path']}\n" for entry in entries), encoding="utf-8")
        # Stale text hashes in historical receipts must not be claimed as current.
        exports.append({"path": "README.md", "sha256": "historical", "bytes": 0})
        self.write_json(self.root / "EXPORT_MANIFEST.json", {"files": exports})
        return self.root / "viewer" / verify.PLAYERS[0]

    def test_valid_images_and_historical_scope(self):
        self.image_fixture()
        self.assertIn("2 frames; 6 unique images", verify.verify_images(self.root))

    def test_corrupt_image_fails(self):
        base = self.image_fixture()
        (base / "frames/01_TEST.jpg").write_bytes(b"corrupt")
        with self.assertRaisesRegex(verify.VerificationError, "SHA-256 mismatch"):
            verify.verify_images(self.root)

    def test_missing_frame_fails(self):
        base = self.image_fixture()
        (base / "frames/01_TEST.jpg").unlink()
        with self.assertRaisesRegex(verify.VerificationError, "Missing required file"):
            verify.verify_images(self.root)

    def test_missing_overview_fails(self):
        base = self.image_fixture()
        (base / "overview.jpg").unlink()
        with self.assertRaisesRegex(verify.VerificationError, "Missing required file"):
            verify.verify_images(self.root)

    def test_receipt_must_cover_every_frame(self):
        base = self.image_fixture()
        self.write_json(base / "render_receipt.json", {"final_image_hashes": {}})
        with self.assertRaisesRegex(verify.VerificationError, "hash coverage"):
            verify.verify_images(self.root)

    def test_duplicate_frames_fail(self):
        base = self.image_fixture()
        manifest = verify.read_json(base / "frame_manifest.json")
        manifest["frames"] *= 2
        self.write_json(base / "frame_manifest.json", manifest)
        with self.assertRaisesRegex(verify.VerificationError, "Duplicate frame image"):
            verify.verify_images(self.root)

    def test_invalid_digest_fails(self):
        base = self.image_fixture()
        self.write_json(base / "render_receipt.json", {"final_image_hashes": {"frames/01_TEST.jpg": "bad"}})
        with self.assertRaisesRegex(verify.VerificationError, "Invalid SHA-256"):
            verify.verify_images(self.root)

    def test_per_frame_digest_mismatch_fails(self):
        base = self.image_fixture()
        manifest = verify.read_json(base / "frame_manifest.json")
        manifest["frames"][0]["image_sha256"] = "0" * 64
        self.write_json(base / "frame_manifest.json", manifest)
        with self.assertRaisesRegex(verify.VerificationError, "frame_manifest.json"):
            verify.verify_images(self.root)

    def test_export_byte_count_mismatch_fails(self):
        self.image_fixture()
        path = self.root / "EXPORT_MANIFEST.json"
        manifest = verify.read_json(path)
        manifest["files"][0]["bytes"] = 0
        self.write_json(path, manifest)
        with self.assertRaisesRegex(verify.VerificationError, "byte-count mismatch"):
            verify.verify_images(self.root)

    def test_path_traversal_rejected(self):
        for name in ("../outside.jpg", "/absolute.jpg", "C:\\file.jpg", "https://example.invalid/image.jpg"):
            with self.subTest(name=name), self.assertRaisesRegex(verify.VerificationError, "Invalid local file path"):
                verify.local_file(self.root, name)

    def test_symlink_escape_rejected(self):
        base = self.root / "package"
        base.mkdir()
        outside = self.root / "outside.jpg"
        outside.write_bytes(b"fixture")
        (base / "linked.jpg").symlink_to(outside)
        with self.assertRaisesRegex(verify.VerificationError, "escapes package"):
            verify.local_file(base, "linked.jpg")

    def test_enumerated_json_and_javascript_cannot_escape_checkout(self):
        checkout = self.root / "checkout"
        checkout.mkdir()
        for suffix in (".json", ".js"):
            with self.subTest(suffix=suffix):
                outside = self.root / ("outside" + suffix)
                outside.write_text("outside checkout; must not be read", encoding="utf-8")
                (checkout / ("linked" + suffix)).symlink_to(outside)
                with self.assertRaisesRegex(verify.VerificationError, "escapes package"):
                    list(verify.published_files(checkout, suffix))
        with self.assertRaisesRegex(verify.VerificationError, "escapes package"):
            verify.parse_json(checkout)
        with patch.object(verify, "run_command") as command:
            with self.assertRaisesRegex(verify.VerificationError, "escapes package"):
                verify.check_javascript(checkout, "node", {})
            command.assert_not_called()

    def test_invalid_json_rejected(self):
        path = self.root / "invalid.json"
        for value in ('{"x":', '{"x": 1, "x": 2}', '{"x": NaN}', '{"x": Infinity}'):
            with self.subTest(value=value):
                path.write_text(value, encoding="utf-8")
                with self.assertRaisesRegex(verify.VerificationError, "Invalid JSON"):
                    verify.read_json(path)

    def test_json_scan_includes_new_drafts_and_ignores_caches(self):
        self.write_json(self.root / "tasks/new_draft/data.json", {"ok": True})
        for directory in verify.IGNORED:
            path = self.root / directory / "invalid.json"
            path.parent.mkdir(parents=True)
            path.write_text("invalid", encoding="utf-8")
        self.assertIn("1 working-tree JSON files", verify.parse_json(self.root))

    def test_missing_node_fails_clearly(self):
        with patch.object(verify.shutil, "which", return_value=None):
            with self.assertRaisesRegex(verify.VerificationError, "Node.js is required"):
                verify.toolchain()

    def test_missing_python_executable_fails_clearly(self):
        with patch.object(verify.sys, "executable", ""):
            with self.assertRaisesRegex(verify.VerificationError, "Python executable"):
                verify.toolchain()

    def test_missing_required_file_fails_clearly(self):
        (self.root / "tasks").mkdir()
        with self.assertRaisesRegex(verify.VerificationError, "check_english.py"):
            verify.preflight(self.root)

    def test_runner_rejects_empty_and_skipped_suites(self):
        path = self.root / "test_probe.py"
        fixtures = (
            ("", False),
            ("import unittest\nclass Probe(unittest.TestCase):\n @unittest.skip('fixture')\n def test_probe(self): pass\n", False),
            ("import unittest\nclass Probe(unittest.TestCase):\n def test_probe(self): pass\n", True),
        )
        for source, succeeds in fixtures:
            with self.subTest(succeeds=succeeds, source=source):
                path.write_text(source, encoding="utf-8")
                result = subprocess.run([sys.executable, "-B", "-c", verify.UNITTEST_RUNNER,
                                         str(self.root), "test_probe.py"],
                                        capture_output=True, text=True, check=False, timeout=30)
                self.assertEqual(result.returncode == 0, succeeds, result.stdout + result.stderr)

    def test_main_binds_checkout_sources_even_if_environment_is_wrong(self):
        environments = []
        def record(command, root, env):
            environments.append(env)
        with patch.dict(os.environ, {"SCIENCEGYM_TASKS": "wrong-checkout"}), \
             patch.object(verify, "toolchain", return_value=(sys.executable, "node")), \
             patch.object(verify, "preflight"), patch.object(verify, "parse_json"), \
             patch.object(verify, "verify_images"), patch.object(verify, "check_javascript"), \
             patch.object(verify, "run_command", side_effect=record), \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(verify.main(["--root", str(self.root)]), 0)
        self.assertTrue(environments)
        for env in environments:
            self.assertEqual(env["SCIENCEGYM_TASKS"], str(self.root / "tasks"))
            self.assertEqual(env["PYTHONDONTWRITEBYTECODE"], "1")


if __name__ == "__main__":
    unittest.main()
