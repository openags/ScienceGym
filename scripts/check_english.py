#!/usr/bin/env python3
"""Reject untranslated CJK characters in tracked-style repository text files.

This is a language hygiene check, not a translation-quality evaluation.
JSON values are decoded so escaped Unicode cannot hide untranslated content.
"""
import argparse
import json
from pathlib import Path
import re

CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0002fa1f]")
TEXT_SUFFIXES = {".md", ".txt", ".json", ".py", ".tex", ".html", ".js", ".css", ".yaml", ".yml", ".toml"}

def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    failures = []
    checked = 0
    for path in sorted(args.root.rglob("*")):
        relative = path.relative_to(args.root)
        if any(part in {".git", "__pycache__", ".venv", "node_modules"} for part in relative.parts):
            continue
        if not path.is_file() or (path.suffix not in TEXT_SUFFIXES and path.name != "LICENSE"):
            continue
        checked += 1
        try:
            text = path.read_text(encoding="utf-8")
            values = strings(json.loads(text)) if path.suffix == ".json" else [text]
            if CJK.search(str(relative)) or any(CJK.search(value) for value in values):
                failures.append(f"Untranslated CJK: {relative}")
        except (UnicodeError, json.JSONDecodeError) as exc:
            failures.append(f"Invalid text: {relative}: {exc}")
    for failure in failures:
        print(failure)
    print(f"Checked {checked} text files; {len(failures)} failures")
    return int(bool(failures))

if __name__ == "__main__":
    raise SystemExit(main())
