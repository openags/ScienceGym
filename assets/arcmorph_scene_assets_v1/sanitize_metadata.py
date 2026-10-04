"""Drop private PNG text chunks; fail closed on private native/portable strings."""
from pathlib import Path
import json,hashlib,struct
P=Path(__file__).resolve().parent
changes=[]
for p in sorted((P/'evidence').glob('*.png')):
 raw=p.read_bytes();out=raw[:8];pos=8
 while pos<len(raw):
  n=struct.unpack_from('>I',raw,pos)[0];kind=raw[pos+4:pos+8]
  if kind not in {b'tEXt',b'zTXt',b'iTXt'}:out+=raw[pos:pos+n+12]
  pos+=n+12
 if out!=raw:p.write_bytes(out);changes.append(p.name)
for path in ['geometry/arcmorph_lab.blend','geometry/arcmorph_lab.glb']:
 raw=(P/path).read_bytes()
 for prefix in [b'/'+b'workspace/',b'/'+b'root/',b'/'+b'home/agent/',b'/'+b'tmp/']:
  for encoded in [prefix,prefix.decode().encode('utf-16-le'),prefix.decode().encode('utf-16-be')]:
   assert encoded not in raw,'Private string in '+path
receipt=json.loads((P/'review/render_receipt.json').read_text())
for entry in receipt['images']:entry['sha256']=hashlib.sha256((P/entry['path']).read_bytes()).hexdigest()
(P/'review/render_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
r={'status':'PASS','png_text_chunks_removed':changes,'private_native_and_glb_strings_absent':True,'native_rewritten':False,'render_hashes_refreshed_after_lossless_metadata_strip':True}
(P/'review/metadata_sanitization.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
