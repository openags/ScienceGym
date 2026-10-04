"""Freeze deterministic archive from an exact public allowlist only."""
from pathlib import Path
import json,hashlib,zipfile
P=Path(__file__).resolve().parent
files=json.loads((P/'EXPORT_ALLOWLIST.json').read_text())['files']
assert len(files)==36 and len(set(files))==36
for n in files:
 assert not Path(n).is_absolute() and '..' not in Path(n).parts
 p=P/n;assert not p.is_symlink(),n
 assert n=='MANIFEST.sha256' or p.is_file(),n
 assert p.suffix not in ['.pdf','.html','.zip','.log','.blend1','.pyc','.pem','.key'],n
(P/'MANIFEST.sha256').write_text('\n'.join(hashlib.sha256((P/n).read_bytes()).hexdigest()+'  '+n for n in sorted(files) if n!='MANIFEST.sha256')+'\n')
output=P/'lockable_origami_scene_assets_v1_public.zip'
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n in sorted(files):
  info=zipfile.ZipInfo('lockable_origami_scene_assets_v1/'+n,(2026,10,4,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,(P/n).read_bytes())
print(json.dumps({'filename':output.name,'files':len(files),'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}))
