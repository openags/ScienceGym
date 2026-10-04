"""Strip PNG text metadata without changing image chunks and reject private paths.
The native file is never broadly rewritten; unexpected private paths fail closed.
"""
from pathlib import Path
import struct,hashlib,json
P=Path(__file__).resolve().parent
changed=[]
for p in sorted((P/'evidence').glob('*.png')):
 raw=p.read_bytes();clean=raw[:8];pos=8
 while pos<len(raw):
  n=struct.unpack_from('>I',raw,pos)[0];kind=raw[pos+4:pos+8]
  if kind not in {b'tEXt',b'zTXt',b'iTXt'}:clean+=raw[pos:pos+n+12]
  pos+=n+12
 if clean!=raw:changed.append(p.name);p.write_bytes(clean)
# Blender currently saves no source workspace path in this scene. Fail closed if
# future versions do; never broad-replace arbitrary native data fields.
blend=P/'geometry/lockable_origami_lab.blend';raw=blend.read_bytes();prefixes=[b'/'+b'workspace/',b'/'+b'root/',b'/'+b'home/agent/',b'/'+b'tmp/']
for n in ['geometry/lockable_origami_lab.blend','geometry/lockable_origami_lab.glb','geometry/paperboard_reference_display.glb']:
 b=(P/n).read_bytes()
 for p in prefixes:
  for q in [p,p.decode().encode('utf-16-le'),p.decode().encode('utf-16-be')]:assert q not in b,'Private path remains in '+n
r={'status':'PASS','png_text_chunks_absent':True,'native_private_path_scan':'PASS','glb_private_path_scan':'PASS','encodings':['ASCII/UTF-8','UTF-16-LE','UTF-16-BE'],'png_files_changed_by_this_run':changed,'native_rewrite_required':False,'native_sha256':hashlib.sha256(raw).hexdigest(),'image_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((P/'evidence').glob('*.png'))}}
(P/'review/metadata_sanitization.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
