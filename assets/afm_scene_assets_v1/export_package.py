"""Export only explicit public allowlist; no recursive source-directory upload."""
import json,hashlib,zipfile,pathlib
P=pathlib.Path(__file__).resolve().parent
spec=json.loads((P/'EXPORT_ALLOWLIST.json').read_text());files=spec['files']
assert len(files)==len(set(files))
for n in files:
 p=P/n
 assert not pathlib.Path(n).is_absolute() and '..' not in pathlib.Path(n).parts
 assert p.is_file() and not p.is_symlink(),n
 assert p.suffix.lower() not in ['.pdf','.html','.blend1','.pem','.key'],n
 assert 'source-archive' not in n and 'microscopy_sources' not in n,n
hashes=[hashlib.sha256((P/n).read_bytes()).hexdigest()+'  '+n for n in files if n!='MANIFEST.sha256']
(P/'MANIFEST.sha256').write_text('\n'.join(hashes)+'\n')
output=P/'afm_scene_assets_v1_public.zip'
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
 for n in files:z.write(P/n,'afm_scene_assets_v1/'+n)
print(json.dumps({'zip':str(output),'files':len(files),'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}))
