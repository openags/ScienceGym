"""Deterministic sanitized export; only the explicit allowlist is included."""
import pathlib,json,hashlib,zipfile,sys
P=pathlib.Path(__file__).resolve().parent
allow=json.loads((P/'EXPORT_ALLOWLIST.json').read_text())['files']
if len(allow)!=len(set(allow)):raise SystemExit('duplicate export path')
for n in allow:
 q=pathlib.PurePosixPath(n)
 if q.is_absolute() or '..' in q.parts:raise SystemExit('unsafe export path')
 p=P/q
 if not p.is_file() or p.is_symlink():raise SystemExit('missing or unsafe member: '+n)
 if p.suffix.lower() in {'.json','.py','.md','.txt'}:
  for v in ['/'+'workspace/','/'+'tmp/','file:'+'//','__py'+'cache__']:
   if v in p.read_text():raise SystemExit('private or transient content: '+n)
for f in json.loads((P/'CONTENT_MANIFEST.json').read_text())['files']:
 p=P/f['path']
 if p.stat().st_size!=f['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=f['sha256']:raise SystemExit('manifest drift: '+f['path'])
out=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else P.parent/'thermalmeta-scene-assets-v1.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n in allow:
  zi=zipfile.ZipInfo(P.name+'/'+n,date_time=(2026,10,5,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;zi.external_attr=0o100644<<16;z.writestr(zi,(P/n).read_bytes())
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 assert len(z.namelist())==len(allow)
serialized=(out.stat().st_size+2)//3*4+2048
if serialized>=15*1024*1024:raise SystemExit('ZIP potential serialized request is not below 15 MiB')
print(json.dumps({'filename':out.name,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'members':len(allow),'potential_json_base64_bytes':serialized,'below_15_MiB':True},indent=2))
