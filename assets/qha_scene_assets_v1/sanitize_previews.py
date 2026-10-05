"""Remove PNG ancillary metadata without changing any image data or pixels."""
from pathlib import Path
import struct,hashlib,json
P=Path(__file__).resolve().parent
results=[]
for p in sorted((P/'previews').glob('*.png')):
 original=p.read_bytes();assert original[:8]==b'\x89PNG\r\n\x1a\n'
 pos=8;kept=[original[:8]];removed=[];idat=[]
 while pos<len(original):
  n=struct.unpack('>I',original[pos:pos+4])[0];kind=original[pos+4:pos+8];chunk=original[pos:pos+n+12];assert len(chunk)==n+12
  if kind in {b'tEXt',b'iTXt',b'zTXt',b'eXIf'}:removed.append(kind.decode())
  else:kept.append(chunk)
  if kind==b'IDAT':idat.append(chunk)
  pos+=n+12
 output=b''.join(kept);p.write_bytes(output)
 results.append({'file':p.relative_to(P).as_posix(),'removed_metadata_chunk_types':removed,'before_sha256':hashlib.sha256(original).hexdigest(),'after_sha256':hashlib.sha256(output).hexdigest(),'image_data_preserved_byte_exact':True,'idat_sha256':hashlib.sha256(b''.join(idat)).hexdigest(),'bytes':len(output)})
(P/'review/metadata_sanitization.json').write_text(json.dumps({'method':'Drop text and EXIF chunks; preserve PNG image payload byte for byte','results':results,'visual_pixels_changed':False},indent=2)+'\n')
