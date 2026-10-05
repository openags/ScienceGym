"""Remove incidental PNG metadata losslessly; rendering pixels are unchanged."""
from PIL import Image
import pathlib,hashlib,json
P=pathlib.Path(__file__).resolve().parent;report=[]
for p in sorted((P/'previews').glob('*.png')):
 im=Image.open(p);im.load();before=hashlib.sha256(im.tobytes()).hexdigest();mode=im.mode;size=im.size;metadata_keys=sorted(im.info)
 out=Image.frombytes(mode,size,im.tobytes());out.save(p,optimize=True)
 check=Image.open(p);check.load();after=hashlib.sha256(check.tobytes()).hexdigest();assert before==after and not check.info
 report.append({'file':p.relative_to(P).as_posix(),'pixel_sha256':after,'pixel_bytes_unchanged':True,'metadata_keys_removed':metadata_keys,'size_px':list(size),'bytes':p.stat().st_size,'potential_json_base64_bytes':4*((p.stat().st_size+2)//3)+2048,'under_15_MiB':4*((p.stat().st_size+2)//3)+2048<15*1024*1024})
(P/'review/preview_sanitization.json').write_text(json.dumps(report,indent=2)+'\n');print('SANITIZED',len(report))
