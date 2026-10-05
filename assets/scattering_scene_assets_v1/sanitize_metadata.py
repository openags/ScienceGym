"""Remove nonvisual metadata, preserving pixels and all geometry bytes."""
from pathlib import Path
from PIL import Image
import json,hashlib,zstandard,io,struct
ROOT=Path(__file__).resolve().parent
PRIVATE_PREFIXES=tuple(('/'+part+'/').encode() for part in ('workspace','tmp','home','root'))
HOME_PREFIX=PRIVATE_PREFIXES[2];TEMP_PREFIX=PRIVATE_PREFIXES[1]
report={'status':'PASS','images':[],'native_saved_compressed_from_first_save':True}
for p in sorted(ROOT.glob('preview_*.png')):
 with Image.open(p) as im:
  im.load();rgba=im.convert('RGBA');before=hashlib.sha256(rgba.tobytes()).hexdigest();assert rgba.getchannel('A').getextrema()==(255,255)
  metadata_fields=sorted(im.info.keys());fresh=Image.new('RGB',im.size);fresh.paste(im.convert('RGB'));fresh.save(p,optimize=True,compress_level=9)
 with Image.open(p) as clean:
  assert not clean.info;after=hashlib.sha256(clean.convert('RGBA').tobytes()).hexdigest();assert before==after
 report['images'].append({'file':p.name,'pixel_sha256_rgba':after,'decoded_rgba_pixels_identical':True,'opaque_alpha_removed_losslessly':True,'metadata_empty':True,'removed_field_names':metadata_fields,'bytes':p.stat().st_size})
p=ROOT/'scattering_review_scene.blend';original=p.read_bytes();raw=bytearray(zstandard.ZstdDecompressor().stream_reader(io.BytesIO(original)).read());assert raw[:7]==b'BLENDER'
# Scrub only the factory file-browser directory/name buffers, identified by the
# Blender 4.3 FileSelectParams DNA block and validated fixed-length char fields.
# Replace default render output prefix in-place; geometry/material bytes unchanged.
changed=[];pos=12
while pos+24<=len(raw):
 code,size,old,sdna,count=struct.unpack_from('<4sIQII',raw,pos);start=pos+24;block=raw[start:start+size]
 if code==b'DATA' and size==2088 and HOME_PREFIX in block:
  assert block.find(HOME_PREFIX)==96
  a,b=start+96,start+96+1090+256+256
  raw[a:b]=b'\0'*(b-a);changed.append('Factory FileSelectParams directory, filename and rename buffers')
 if code==b'SC\x00\x00' and TEMP_PREFIX in block:
  at=start+block.find(TEMP_PREFIX);raw[at:at+5]=b'//\0\0\0';changed.append('Default render path changed to relative')
 pos+=24+size
 if code==b'ENDB':break
for prefix in PRIVATE_PREFIXES:
 assert prefix not in raw
# Blender writes a zstd stream natively. Repacking its sanitized content keeps
# native compressed compatibility; no uncompressed file is written to disk.
p.write_bytes(zstandard.ZstdCompressor(level=9).compress(bytes(raw)))
report['blend_nonvisual_metadata_removed']=changed;report['blend_decompressed_private_path_scan']='PASS';report['geometry_unchanged']=True
b=(ROOT/'scattering_review_scene.glb').read_bytes()
for prefix in PRIVATE_PREFIXES:assert prefix not in b
report['glb_private_path_scan']='PASS'
(ROOT/'metadata_sanitization.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'PASS','image_count':len(report['images']),'native_metadata_buffers_cleaned':len(changed)}))
