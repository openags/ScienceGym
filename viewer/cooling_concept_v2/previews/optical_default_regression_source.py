import hashlib,json,os,subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path('/home/amax/data/media/xyl_ps/scigym/ScienceGym');here=root/'viewer/cooling_concept_v2';old=subprocess.check_output(['git','show','HEAD:viewer/cooling_concept_v2/main.js'],cwd=root).decode();current=(here/'main.js').read_text();results=[];errors=[]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
 for source in [old,current]:
  page=b.new_page(viewport={'width':960,'height':540});page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/cooling_concept_v2/main.js',lambda r:r.fulfill(status=200,content_type='application/javascript',body=source));page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean',timeout=120000);page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000);results.append(page.evaluate('({duration:concept.duration,frames:[0,200,600].map(t=>auditFrame(t))})'));page.close()
 b.close()
for result in results:
 for frame in result['frames']:frame['parts'].sort(key=lambda p:(p['asset'],p['name']))
Path('/tmp/sciencegym-optical-default-regression-states.json').write_text(json.dumps(results))
report=dict(scope='Default full-film state unchanged at three regression times; no full-film acceptance claim',passed=not errors and results[0]==results[1],times_s=[0,200,600],duration_s=results[1]['duration'],errors=errors,baseline_sha256=hashlib.sha256(old.encode()).hexdigest(),current_sha256=hashlib.sha256(current.encode()).hexdigest())
(here/'previews/optical_default_regression.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True);assert report['passed']
