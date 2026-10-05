"""Final schema-aware cleanup. Run after Blender save, before hashes. SPDX-License-Identifier: Apache-2.0"""
from pathlib import Path
import json
from deep_native_buffers import clean,inspect
P=Path(__file__).resolve().parents[1]
source=P/'geometry/microsphere_lab.raw.blend';out=P/'geometry/microsphere_lab.blend'
if out.exists():raise FileExistsError('Final native file exists; do not overwrite a sealed revision')
r=clean(source,out,P);(P/'review/deep_buffer_cleanup.json').write_text(json.dumps(r,indent=2)+'\n')
s=inspect(out,P);(P/'review/deep_buffer_scan.json').write_text(json.dumps(s,indent=2)+'\n')
assert s['strict_path_privacy_pass'] and not s['fields_with_nonzero_tail']
