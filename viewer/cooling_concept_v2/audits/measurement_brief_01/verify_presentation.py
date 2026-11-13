import json,hashlib,math,subprocess
from pathlib import Path
import cv2
import numpy as np
base=Path('/home/amax/data/media/xyl_ps/scigym/ScienceGym/viewer/cooling_concept_v2')
d=json.loads((base/'measurement_brief_delivery.json').read_text())
m=json.loads((base/d['frame_mapping']).read_text())
e=json.loads((base/'single_measurement_episode.json').read_text())
route=json.loads((base/d['route']).read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(base/d['video'])==d['video_sha256']
assert sha(base/m['source_video'])==m['source_video_sha256']
assert [s['id'] for s in m['segments']]==[s['id'] for s in e['segments']]
indices=m['source_frame_per_output_frame']
assert indices[0]==0 and indices[-1]==m['source_frame_count']-1
assert all(a<b for a,b in zip(indices,indices[1:]))
for s,original in zip(m['segments'],e['segments']):
 lo,hi=s['output_frames'];a,b=s['source_frames']
 assert a==math.ceil(original['start']*24-1e-8)
 assert all(a<=n<b for n in indices[lo:hi])
 if original['kind']=='move' or original['duration_s']<=1.25:
  assert indices[lo:hi]==list(range(a,b))
assert route['video_sha256']==d['video_sha256']
assert all(a[0]<=b[0] for a,b in zip(route['samples'],route['samples'][1:]))
subprocess.run(['ffmpeg','-v','error','-i',str(base/d['video']),'-f','null','-'],check=True)
a=cv2.VideoCapture(str(base/m['source_video']));b=cv2.VideoCapture(str(base/d['video']))
checks=[]
frames=sorted({0,len(indices)-1}|{(s['output_frames'][0]+s['output_frames'][1]-1)//2 for s in m['segments']})
for j in frames:
 a.set(cv2.CAP_PROP_POS_FRAMES,indices[j]);ok,x=a.read();assert ok
 b.set(cv2.CAP_PROP_POS_FRAMES,j);ok,y=b.read();assert ok
 psnr=float(cv2.PSNR(x,y)); mae=float(np.abs(x.astype(np.int16)-y.astype(np.int16)).mean())
 assert psnr>30,(j,psnr)
 checks.append(dict(output_frame=j,source_frame=indices[j],psnr_db=psnr,mean_absolute_error=mae))
for j,name in [(int(d['chapters'][1]['time_s']*24)+450,'outbound'),(int(d['chapters'][3]['time_s']*24)+400,'loaded_return'),(len(indices)-1,'finished')]:
 b.set(cv2.CAP_PROP_POS_FRAMES,j);ok,frame=b.read();assert ok
 cv2.imwrite(str(base/f'audits/measurement_brief_01/{name}.jpg'),frame)
a.release();b.release()
r=dict(passed=True,scope='Presentation only: full decode, monotonic source mapping, all 103 stages, original-speed movement/contact frames, sampled encoded-frame correspondence.',video_sha256=d['video_sha256'],source_video_sha256=m['source_video_sha256'],duration_s=d['video_duration_s'],frames=len(indices),operations=len(m['segments']),sampled_encoded_frames=len(checks),minimum_sample_psnr_db=min(x['psnr_db'] for x in checks),encoded_frame_samples=checks,physics_qualified=False,full_paper_complete=False)
(base/'audits/measurement_brief_01/presentation_review.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:v for k,v in r.items() if k!='encoded_frame_samples'}),flush=True)
