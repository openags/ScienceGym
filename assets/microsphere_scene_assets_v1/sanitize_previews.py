"""Remove PNG ancillary metadata without editing pixels. SPDX-License-Identifier: Apache-2.0"""
from pathlib import Path
import hashlib,json,struct,zlib
P=Path(__file__).resolve().parent
r=[]
for p in sorted((P/'previews').glob('*.png')):
 raw=p.read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n';pos=8;out=bytearray(raw[:8]);removed=[]
 while pos<len(raw):
  n=struct.unpack_from('>I',raw,pos)[0];kind=raw[pos+4:pos+8];chunk=raw[pos:pos+n+12];assert zlib.crc32(chunk[4:-4])&0xffffffff==int.from_bytes(chunk[-4:],'big')
  if kind in {b'tEXt',b'zTXt',b'iTXt',b'eXIf',b'tIME'}:removed.append(kind.decode())
  else:out.extend(chunk)
  pos+=n+12
 assert pos==len(raw);p.write_bytes(out);r.append({'file':'previews/'+p.name,'sha256':hashlib.sha256(out).hexdigest(),'removed_chunk_types':removed,'pixel_IDAT_bytes_unchanged':True})
(P/'review/preview_sanitization.json').write_text(json.dumps({'schema':'sciencegym.png_sanitation.v1','images':r},indent=2)+'\n')
