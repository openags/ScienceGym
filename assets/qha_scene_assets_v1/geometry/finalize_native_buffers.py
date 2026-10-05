"""Finish a freshly saved native file with schema-aware full-buffer cleanup.

Run after the last Blender save. Reopening for read-only inspection is safe;
any later save must repeat this finalization because native writers may repopulate
inactive UI strings. The input is retained until a validated temporary output is
ready, and reports never include recovered buffer contents.
"""
from pathlib import Path
import json,sys
HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path:sys.path.insert(0,str(HERE))
from deep_native_buffers import clean,inspect
P=Path(__file__).resolve().parents[1]
source=P/'geometry/qha_lab.blend';temporary=P/'geometry/qha_lab.buffer-clean.blend'
receipt=clean(source,temporary,P)
temporary.replace(source)
receipt['destination_file']='qha_lab.blend'
(P/'review/deep_buffer_cleanup.json').write_text(json.dumps(receipt,indent=2)+'\n')
(P/'review/deep_buffer_scan.json').write_text(json.dumps(inspect(source,P),indent=2)+'\n')
