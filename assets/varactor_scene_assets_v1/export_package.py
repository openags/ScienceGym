"""Deterministic public allowlist archive; no raw source or scratch files."""
from pathlib import Path
import json,hashlib,zipfile
P=Path(__file__).resolve().parent
files=json.loads((P/'EXPORT_ALLOWLIST.json').read_text())['files']
assert len(files)==37 and len(set(files))==37
for n in files:
 assert not Path(n).is_absolute() and '..' not in Path(n).parts
 p=P/n;assert not p.is_symlink(),n
 assert n=='MANIFEST.sha256' or p.is_file(),n
 assert p.suffix not in ['.pdf','.html','.zip','.log','.blend1','.pyc','.pem','.key'],n
 if p.exists():
  for prefix in [b'/'+b'workspace/',b'/'+b'root/',b'/'+b'home/agent/',b'/'+b'tmp/']:
   for pat in [prefix,prefix.decode().encode('utf-16-le'),prefix.decode().encode('utf-16-be')]:assert pat not in p.read_bytes(),'Private path in '+n
(P/'MANIFEST.sha256').write_text('\n'.join(hashlib.sha256((P/n).read_bytes()).hexdigest()+'  '+n for n in sorted(files) if n!='MANIFEST.sha256')+'\n')
output=P/'varactor_scene_assets_v1_public.zip'
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n in sorted(files):
  info=zipfile.ZipInfo('varactor_scene_assets_v1/'+n,(2026,10,4,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,(P/n).read_bytes())
r={'filename':output.name,'files':len(files),'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest()};(P/'export_receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
