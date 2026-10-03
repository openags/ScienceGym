#!/usr/bin/env python3
"""Run with Python 3.9+; validates local authored contracts only."""
import hashlib
import json
import pathlib
import sys
from contract import load_package, validate_package, require
ROOT=pathlib.Path(__file__).resolve().parents[1]

def main():
    require(not any(p.is_symlink() for p in ROOT.rglob('*')), 'symlink in export')
    summary=validate_package(load_package(ROOT))
    manifest=json.loads((ROOT/'EXPORT_ALLOWLIST.json').read_text())
    listed=set(manifest['files'])
    actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    require(actual==listed, 'export allowlist differs from files')
    require(all(p.endswith(('.json','.md','.py')) for p in listed),'disallowed export type')
    for name in listed:
        text=(ROOT/name).read_text()
        require(all(prefix not in text for prefix in [chr(47)+'workspace'+chr(47),chr(47)+'root'+chr(47)]), 'host path leaked: '+name)
        require(not any('\u4e00'<=c<='\u9fff' for c in text),'non-English text: '+name)
    for name, digest in manifest.get('payload_sha256',{}).items():
        require(name in listed and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest, 'payload hash drift: '+name)
    require(set(manifest.get('payload_sha256',{})) == listed-{'EXPORT_ALLOWLIST.json','VERIFICATION.json'}, 'incomplete payload hash set')
    print(json.dumps({'status':'passed','scope':'static_contracts_and_export_hygiene_only',**summary},indent=2))
if __name__=='__main__':
    main()
