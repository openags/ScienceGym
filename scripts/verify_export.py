#!/usr/bin/env python3
"""Verify public-export byte integrity only; this is not a task runtime."""
import hashlib
import json
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "EXPORT_MANIFEST.json").read_text(encoding="utf-8"))
errors = []
seen = set()
json_count = 0
for entry in manifest["files"]:
    rel = Path(entry["path"])
    if rel.is_absolute() or ".." in rel.parts or str(rel) in seen:
        errors.append(f"Invalid or duplicate manifest path: {rel}")
        continue
    seen.add(str(rel))
    path = root / rel
    if not path.is_file():
        errors.append(f"Missing file: {rel}")
        continue
    data = path.read_bytes()
    if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
        errors.append(f"Byte/hash mismatch: {rel}")
    text = data.decode("utf-8")
    if re.search(r"/(?:workspace|home|Users|root|mnt)/", text):
        errors.append(f"Machine-root path: {rel}")
    if rel.suffix == ".json":
        try:
            json.loads(text)
            json_count += 1
        except ValueError as exc:
            errors.append(f"Invalid JSON: {rel}: {exc}")
if errors:
    print("EXPORT INTEGRITY FAILED\n" + "\n".join(errors))
    sys.exit(1)
print(f"PASS: {len(seen)} manifest-covered files; {json_count} JSON files parsed.")
print("Integrity only. Sources, scenes, runtime and scientific results were not validated.")
