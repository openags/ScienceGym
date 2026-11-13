"""Export the presentation camera as a clean, deterministic MP4."""
import argparse,base64,hashlib,json,os,subprocess,time
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
BROWSER='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell'
def capture(preview=False,fps=24):
 names=['index.html','main.js','hand_ik.js','grasp_profile.json','optical_setup.json','optical_approach_paths.json','manipulation_motion.js','manipulation_approach_paths.json','lid_contact_paths.json','reference_motion.js','reference_transfer.json','runtime_scene.json','motion_poses.json','build_poses.py','capture.py'];pins={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names};errors=[]
 if not preview:
  if not json.loads((HERE/'manipulation_approach_paths.json').read_text()).get('complete'):raise RuntimeError('Manipulation approach planning is incomplete')
  acceptance=HERE/'visual_acceptance.json'
  if not acceptance.exists():raise RuntimeError('Full film export requires a completed visual interaction review')
  review=json.loads(acceptance.read_text())
  if not review.get('passed'):raise RuntimeError('Visual interaction review has unresolved failures')
  for name in ['main.js','hand_ik.js','grasp_profile.json','optical_setup.json','optical_approach_paths.json','manipulation_motion.js','manipulation_approach_paths.json','lid_contact_paths.json','reference_motion.js','reference_transfer.json','runtime_scene.json','motion_poses.json']:
   if review.get('source_sha256',{}).get(name)!=pins[name]:raise RuntimeError('Visual interaction review is stale: '+name)
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=BROWSER,args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
  page=b.new_page(viewport={'width':1280,'height':720},device_scale_factor=1);page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean',timeout=120000);page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000)
  info=page.evaluate('({duration:concept.duration,phases:concept.phases,sourceHashes:concept.sourceHashes,assetCount:concept.assetCount,robotCount:concept.robotCount})');(HERE/'timeline.json').write_text(json.dumps(info,indent=2,ensure_ascii=False)+'\n')
  assert info['robotCount']==1 and info['assetCount']==81
  for a,c in zip(info['phases'],info['phases'][1:]):assert abs(a['end']-c['start'])<1e-8
  renderer=page.evaluate("()=>{const g=document.querySelector('canvas').getContext('webgl2'),e=g.getExtension('WEBGL_debug_renderer_info');return g.getParameter(e.UNMASKED_RENDERER_WEBGL)}")
  print('Loaded',round(info['duration'],2),'seconds;',renderer,flush=True)
  for id in ['intro','calibration','solar','assemble_white','carry_white','outdoor_transfer','open_white','finish']:
   phase=next(x for x in info['phases'] if x['id']==id);t=(phase['start']+phase['end'])/2;jpg=base64.b64decode(page.evaluate('(t)=>concept.frameJpeg(t)',t));(HERE/(id+'.jpg')).write_bytes(jpg)
  if preview:
   begin=time.monotonic()
   for i in range(60):page.evaluate('(t)=>concept.frameJpeg(t)',100+i/fps)
   print('Capture FPS',60/(time.monotonic()-begin),'errors',errors,flush=True);b.close();return
  count=int(info['duration']*fps)+1;start=time.monotonic();output=HERE/'episode.mp4';temporary=HERE/'episode.rendering.mp4';ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','image2pipe','-vcodec','mjpeg','-framerate',str(fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','24','-pix_fmt','yuv420p','-movflags','+faststart',str(temporary)],stdin=subprocess.PIPE)
  for i in range(count):
   data=base64.b64decode(page.evaluate('(t)=>concept.frameJpeg(t)',min(i/fps,info['duration'])));ff.stdin.write(data)
   if i%(fps*20)==0:print('frame',i,'/',count,'video_s',round(i/fps,1),'wall_s',round(time.monotonic()-start,1),flush=True)
  ff.stdin.close();assert ff.wait()==0;assert not errors
  for n,h in pins.items():assert hashlib.sha256((HERE/n).read_bytes()).hexdigest()==h,'Source changed during export'
  temporary.replace(output);receipt=dict(kind='authored_kinematic_concept_video',duration_s=count/fps,scene_duration_s=info['duration'],frames=count,fps=fps,resolution=[1280,720],continuous_scene=True,robot_count=1,asset_count=81,watermarks=False,text_overlays=False,source_sha256=pins,asset_sources=info['sourceHashes'],renderer=renderer,browser=b.version,javascript_errors=errors,wall_seconds=time.monotonic()-start,video_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),physics_validation_claimed=False)
  (HERE/'export_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('Export complete',output.stat().st_size,'bytes',flush=True);b.close()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');p.add_argument('--fps',type=int,default=24);a=p.parse_args();capture(a.preview,a.fps)
