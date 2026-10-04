"""Freeze only explicitly allowlisted public files, never a recursive source upload."""
import json,hashlib,zipfile,pathlib
P=pathlib.Path(__file__).resolve().parent
spec=json.loads((P/'EXPORT_ALLOWLIST.json').read_text());files=spec['files']
assert len(files)==len(set(files))
for name in files:
    p=P/name
    assert not pathlib.Path(name).is_absolute() and '..' not in pathlib.Path(name).parts,name
    assert not p.is_symlink(),name
    if name=='MANIFEST.sha256':continue  # generated below on first freeze
    assert p.is_file() and not p.is_symlink(),name
    assert p.suffix.lower() not in ['.pdf','.html','.blend1','.pem','.key'],name
    assert not any(s in name.lower() for s in ['source-archive','si.pdf','source_reading','__pycache__']),name
manifest=''.join(hashlib.sha256((P/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in files if n!='MANIFEST.sha256')
(P/'MANIFEST.sha256').write_text(manifest)
output=P/'cooling_scene_assets_v1_public.zip'
assert not output.is_symlink()
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for n in files:
        info=zipfile.ZipInfo('cooling_scene_assets_v1/'+n,date_time=(2026,10,4,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
        z.writestr(info,(P/n).read_bytes())
with zipfile.ZipFile(output) as z:
    assert z.testzip() is None
    assert sorted(z.namelist())==sorted('cooling_scene_assets_v1/'+n for n in files)
    for n in files:assert z.read('cooling_scene_assets_v1/'+n)==(P/n).read_bytes(),n
assert output.stat().st_size<=30*1024*1024,'ZIP exceeds reasonable 30 MiB budget'
receipt={'zip_name':output.name,'files':len(files),'raw_bytes':sum((P/n).stat().st_size for n in files),'zip_bytes':output.stat().st_size,'zip_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'zip_integrity':'pass','manifest_exact':'pass','deterministic_member_timestamp':'2026-10-04T00:00:00','publication_performed':False}
(P/'review'/'freeze_receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
