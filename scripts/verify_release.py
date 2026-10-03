#!/usr/bin/env python3
"""Run offline static/display checks; never execute a scientific or robot task."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {".git", "__pycache__", ".venv", "node_modules"}
PLAYERS = ("embodied_r01", "embodied_thermoelectric")
SHA256 = re.compile(r"[0-9a-fA-F]{64}\Z")
# A custom runner prevents unittest's successful exit for skipped/empty suites.
UNITTEST_RUNNER = """
import sys, unittest
suite = unittest.defaultTestLoader.discover(sys.argv[1], pattern=sys.argv[2])
if not suite.countTestCases():
    sys.exit('FAIL: no Python tests discovered')
result = unittest.TextTestRunner(verbosity=2).run(suite)
if result.skipped:
    print('FAIL: required Python tests were skipped', file=sys.stderr)
sys.exit(0 if result.wasSuccessful() and not result.skipped else 1)
"""


class VerificationError(Exception):
    """An actionable validation failure, reported without a traceback."""


def require_file(path):
    if not path.is_file():
        raise VerificationError(f"Missing required file: {path}")
    return path


def local_file(base, name):
    """Resolve only published, relative paths within the expected package."""
    if not isinstance(name, str) or not name or "\\" in name:
        raise VerificationError(f"Invalid local file path: {name!r}")
    relative = PurePosixPath(name)
    if relative.is_absolute() or ".." in relative.parts or ":" in name:
        raise VerificationError(f"Invalid local file path: {name!r}")
    path = base / name
    try:
        path.resolve().relative_to(base.resolve())
    except ValueError as exc:
        raise VerificationError(f"File escapes package: {name}") from exc
    return require_file(path)


def published_files(root, suffix):
    for directory, names, files in os.walk(root):
        names[:] = sorted(name for name in names if name not in IGNORED)
        for name in sorted(files):
            path = Path(directory) / name
            if path.suffix.lower() == suffix:
                yield local_file(root, path.relative_to(root).as_posix())


def reject_constant(value):
    raise ValueError(f"Non-JSON numeric constant: {value}")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    try:
        return json.loads(require_file(path).read_text(encoding="utf-8"),
                          parse_constant=reject_constant,
                          object_pairs_hook=unique_object)
    except (OSError, UnicodeError, ValueError) as exc:
        raise VerificationError(f"Invalid JSON: {path}: {exc}") from exc


def parse_json(root):
    paths = list(published_files(root, ".json"))
    if not paths:
        raise VerificationError("No published JSON files found")
    for path in paths:
        read_json(path)
    return f"{len(paths)} working-tree JSON files parsed (including untracked drafts)"


def toolchain():
    if sys.version_info < (3, 9):
        raise VerificationError("Python 3.9 or newer is required")
    if not sys.executable or not Path(sys.executable).is_file():
        raise VerificationError("Cannot locate the running Python executable")
    node = shutil.which("node")
    if not node:
        raise VerificationError("Node.js is required; 'node' was not found on PATH")
    return sys.executable, node


def preflight(root):
    if not (root / "tasks").is_dir():
        raise VerificationError(f"Missing required task directory: {root / 'tasks'}")
    required = ["scripts/check_english.py", "scripts/test_verify_release.py",
                "EXPORT_MANIFEST.json", "scene_bindings/r01_mount_observe_retrieve_v1/audit.py",
                "scene_bindings/r01_mount_observe_retrieve_v1/tests/test_audit.py",
                "viewer/task_explorer_v1/build.py",
                "viewer/task_explorer_v1/app.js", "viewer/task_explorer_v1/index.html",
                "viewer/task_explorer_v1/tests/test_semantics.py",
                "viewer/task_explorer_v1/tests/test_app.js",
                "viewer/embodied_thermoelectric/PUBLIC_FILE_MANIFEST.json",
                "viewer/embodied_thermoelectric/SHA256SUMS"]
    for player in PLAYERS:
        for name in ("frame_manifest.json", "render_receipt.json", "manifest.js",
                     "index.html", "player.js", "test_player.js"):
            required.append(f"viewer/{player}/{name}")
    for name in required:
        local_file(root, name)


def run_command(command, root, env):
    try:
        result = subprocess.run(command, cwd=root, env=env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VerificationError(f"Could not run {command[0]}: {exc}") from exc
    if result.stdout:
        print(result.stdout.rstrip(), flush=True)
    if result.returncode:
        raise VerificationError(f"Command exited {result.returncode}: {' '.join(command)}")


def check_javascript(root, node, env):
    paths = list(published_files(root, ".js"))
    if not paths:
        raise VerificationError("No published JavaScript files found")
    for path in paths:
        run_command([node, "--check", str(path)], root, env)
    return f"{len(paths)} JavaScript files passed node --check"


def verify_images(root):
    checked = set()
    assertions = 0

    def check(base, name, digest, source, size=None):
        nonlocal assertions
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise VerificationError(f"Invalid SHA-256 in {source}: {name}")
        path = local_file(base, name)
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest.lower():
            raise VerificationError(f"Image SHA-256 mismatch: {path} ({source})")
        if size is not None and (type(size) is not int or len(data) != size):
            raise VerificationError(f"Image byte-count mismatch: {path} ({source})")
        checked.add(path.resolve())
        assertions += 1

    frames_total = 0
    for player in PLAYERS:
        base = root / "viewer" / player
        manifest = read_json(base / "frame_manifest.json")
        receipt = read_json(base / "render_receipt.json")
        frames = manifest["frames"]
        if not isinstance(frames, list) or not frames:
            raise VerificationError(f"Empty/invalid frames in {base / 'frame_manifest.json'}")
        images = [frame["image"] for frame in frames]
        if len(set(images)) != len(images):
            raise VerificationError(f"Duplicate frame image in {player}")
        hashes = receipt["final_image_hashes" if player == "embodied_r01" else "frame_sha256"]
        if not isinstance(hashes, dict) or set(hashes) != set(images):
            raise VerificationError(f"Render receipt hash coverage differs from frame manifest: {player}")
        for frame in frames:
            name = frame["image"]
            if not name.startswith("frames/"):
                raise VerificationError(f"Frame outside frames directory: {player}/{name}")
            check(base, name, hashes[name], "render_receipt.json")
            if "image_sha256" in frame:
                check(base, name, frame["image_sha256"], "frame_manifest.json")
        frames_total += len(frames)
        local_file(base, manifest["overview"])
        if player == "embodied_thermoelectric":
            check(base, manifest["overview"], receipt["overview_sha256"], "render_receipt.json")

    # Historical export receipts remain useful for frozen image bytes only.
    # Their old text/source hashes do not describe the current working tree.
    for base, filename in ((root, "EXPORT_MANIFEST.json"),
                           (root / "viewer/embodied_thermoelectric", "PUBLIC_FILE_MANIFEST.json")):
        entries = read_json(base / filename)["files"]
        selected = [entry for entry in entries if entry["path"].lower().endswith(".jpg")]
        if not selected:
            raise VerificationError(f"No published image hashes in {filename}")
        for entry in selected:
            check(base, entry["path"], entry["sha256"], filename, entry["bytes"])
    base = root / "viewer/embodied_thermoelectric"
    checksum_file = base / "SHA256SUMS"
    image_lines = 0
    for line in require_file(checksum_file).read_text(encoding="utf-8").splitlines():
        fields = line.split(maxsplit=1)
        if len(fields) != 2:
            raise VerificationError(f"Malformed checksum line in {checksum_file}")
        digest, name = fields
        if name.lower().endswith(".jpg"):
            check(base, name, digest, "SHA256SUMS")
            image_lines += 1
    if not image_lines:
        raise VerificationError(f"No published image hashes in {checksum_file}")
    return (f"{frames_total} frames; {len(checked)} unique images; "
            f"{assertions} published image hash assertions passed")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT,
                        help="checkout to verify (default: this script's repository)")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    print("ScienceGym static release checks. No browser, physics, hardware or scientific execution.", flush=True)
    try:
        python, node = toolchain()
        preflight(root)
    except VerificationError as exc:
        print(f"FAIL: {exc}\nValidation did not start.", file=sys.stderr)
        return 1
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", SCIENCEGYM_TASKS=str(root / "tasks"))

    def command(*args):
        return lambda: run_command(list(args), root, env)

    checks = [
        ("Working-tree JSON", lambda: parse_json(root)),
        ("English hygiene", command(python, "-B", str(root / "scripts/check_english.py"), str(root))),
        ("Verifier regression tests", command(python, "-B", "-c", UNITTEST_RUNNER,
                                               str(root / "scripts"), "test_verify_release.py")),
        ("Source-bound explorer tests", command(python, "-B", "-c", UNITTEST_RUNNER,
                                                 str(root / "viewer/task_explorer_v1/tests"), "test_*.py")),
        ("R01 scene binding audit", command(python, "-B", str(root / "scene_bindings/r01_mount_observe_retrieve_v1/audit.py"), "--root", str(root))),
        ("R01 binding negative fixtures", command(python, "-B", "-c", UNITTEST_RUNNER,
                                                 str(root / "scene_bindings/r01_mount_observe_retrieve_v1/tests"), "test_*.py")),
        ("JavaScript syntax", lambda: check_javascript(root, node, env)),
        ("Explorer mocked DOM", command(node, str(root / "viewer/task_explorer_v1/tests/test_app.js"))),
    ]
    for player in PLAYERS:
        checks.append((f"{player} mocked DOM", command(node, str(root / "viewer" / player / "test_player.js"))))
    checks.append(("Published image integrity", lambda: verify_images(root)))
    failures = []
    for label, check in checks:
        print(f"\n== {label} ==", flush=True)
        try:
            detail = check()
        except (VerificationError, OSError, KeyError, TypeError, ValueError) as exc:
            failures.append(label)
            print(f"FAIL: {label}: {exc}", flush=True)
        else:
            print(f"PASS: {detail or label}", flush=True)
    print(f"\n{len(checks) - len(failures)}/{len(checks)} static check groups passed.", flush=True)
    if failures:
        print("FAILED: " + ", ".join(failures), flush=True)
    else:
        print("Static/display validation passed. No source completeness, real-browser, robot feasibility or scientific validation is implied.", flush=True)
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
