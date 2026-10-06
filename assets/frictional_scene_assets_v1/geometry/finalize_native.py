"""SDNA-aware final sanitation before immutable hashing. SPDX-License-Identifier: Apache-2.0"""
from pathlib import Path
import json
from deep_native_buffers import clean,inspect
P=Path(__file__).resolve().parents[1]
source=P/'geometry/frictional_lab.raw.blend';out=P/'geometry/frictional_lab.blend'
if any(x.is_symlink() for x in [source,out,source.parent,P/'review',P/'review/deep_buffer_cleanup.json',P/'review/deep_buffer_scan.json',*source.parent.parents]):raise ValueError('Symlinked native input/output or ancestor')
if not source.resolve().is_relative_to(P) or not out.resolve().is_relative_to(P):raise ValueError('Native path escapes package')
if (P/'scene_core_manifest.json').exists() or out.exists():raise FileExistsError('Refusing to overwrite sealed or final native revision')
r=clean(source,out,P);(P/'review/deep_buffer_cleanup.json').write_text(json.dumps(r,indent=2)+'\n')
s=inspect(out,P);(P/'review/deep_buffer_scan.json').write_text(json.dumps(s,indent=2)+'\n')
assert s['strict_path_privacy_pass'] and not s['fields_with_nonzero_tail']
