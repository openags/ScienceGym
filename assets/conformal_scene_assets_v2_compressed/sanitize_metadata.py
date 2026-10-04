"""Strip PNG nonpixel metadata while proving decoded pixel identity."""
from pathlib import Path
from PIL import Image
import json,hashlib
P=Path(__file__).resolve().parent
out=[]
for f in sorted((P/'evidence').glob('*.png')):
 with Image.open(f) as im:
  im.load();pixels=im.tobytes();before=hashlib.sha256(pixels).hexdigest();mode=im.mode;size=im.size
  if im.info: Image.frombytes(mode,size,pixels).save(f)
 with Image.open(f) as im:
  after=hashlib.sha256(im.tobytes()).hexdigest();assert before==after;assert not im.info
 out.append({'file':str(f.relative_to(P)),'pixel_sha256':after,'pixel_unchanged':True,'metadata_empty':True,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
native_clean=[]
for name in ['geometry/conformal_lab.blend','geometry/conformal_lab.glb']:
 raw=(P/name).read_bytes()
 if name.endswith('.blend') and raw[:4]==bytes.fromhex('28b52ffd'):
  import io,zstandard
  with zstandard.ZstdDecompressor().stream_reader(io.BytesIO(raw)) as reader:raw=reader.read()
  assert raw.startswith(b'BLENDER'), 'Not a decoded Blender payload'
 for part in ['workspace','tmp','home','root']:
  prefix=('/'+part+'/').encode()
  for encoded in [prefix,prefix.decode().encode('utf-16-le'),prefix.decode().encode('utf-16-be')]:
   assert encoded not in raw, 'Private filesystem string in '+name
 native_clean.append(name)
(P/'review'/'metadata_sanitization.json').write_text(json.dumps({'images':out,'native_portable_private_path_scan':'PASS','scanned_geometry':native_clean,'compressed_native_decompressed_before_scan':True},indent=2)+'\n')
rp=P/'review'/'render_receipt.json'
if rp.exists():
 r=json.loads(rp.read_text())
 for x in r['renders']:
  if 'rendered_file_sha256' not in x:x['rendered_file_sha256']=x['sha256']
  x['sha256']=hashlib.sha256((P/x['file']).read_bytes()).hexdigest();x['metadata_stripped_pixel_preserved']=True
 rp.write_text(json.dumps(r,indent=2)+'\n')
print('SANITIZED',len(out),'original PNGs')
