"""Deterministic frozen ZIP from explicit allowlist only. Run after final review/tests."""
import json,hashlib,zipfile,pathlib
P=pathlib.Path(__file__).resolve().parent
files=json.loads((P/'EXPORT_ALLOWLIST.json').read_text())['files']
assert len(files)==len(set(files))
for n in files:
 p=P/n;assert not pathlib.Path(n).is_absolute() and '..' not in pathlib.Path(n).parts
 assert not p.is_symlink(),n
 assert n=='MANIFEST.sha256' or p.is_file(),n
 assert p.suffix.lower() not in ['.pdf','.html','.blend1','.pem','.key','.zip','.log','.pyc'],n
 assert not any(x in n.lower() for x in ['private/','source_archive','chem_instrument_sources']),n
(P/'MANIFEST.sha256').write_text('\n'.join(hashlib.sha256((P/n).read_bytes()).hexdigest()+'  '+n for n in files if n!='MANIFEST.sha256')+'\n')
output=P/'laser_scene_assets_v1_public.zip'
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n in sorted(files):
  info=zipfile.ZipInfo('laser_scene_assets_v1/'+n,(2026,10,4,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,(P/n).read_bytes())
print(json.dumps({'zip':str(output),'files':len(files),'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}))
