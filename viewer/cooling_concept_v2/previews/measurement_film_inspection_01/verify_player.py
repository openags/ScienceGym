import json,os,hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path('/home/amax/data/media/xyl_ps/scigym/ScienceGym/viewer/cooling_concept_v2');errors=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
 page=browser.new_page(viewport={'width':1440,'height':1050});page.on('pageerror',lambda e:errors.append(str(e)))
 response=page.goto('http://localhost:8769/viewer/cooling_concept_v2/measurement_demo.html',timeout=120000);assert response.status==200
 page.wait_for_function('document.querySelector("video").readyState>=2',timeout=120000)
 info=page.evaluate('''()=>{const v=document.querySelector('video');return {duration:v.duration,width:v.videoWidth,height:v.videoHeight,error:v.error,chapters:document.querySelectorAll('.chapter').length,status:document.getElementById('state').textContent}}''')
 assert abs(info['duration']-541.166667)<.002 and info['width']==1280 and info['height']==720 and info['chapters']==10 and info['error'] is None,info
 page.get_by_role('button',name='携样返回 FTIR').click()
 page.wait_for_function('document.querySelector("video").currentTime>94 && document.querySelector("video").currentTime<99 && !document.querySelector("video").seeking',timeout=60000)
 page.evaluate('document.querySelector("video").pause()')
 page.screenshot(path=str(root/'previews/measurement_film_inspection_01/player.png'),full_page=True)
 assert not errors,errors
 record=dict(passed=True,url=page.url,video_metadata=info,javascript_errors=errors,chapter_seek_s=page.evaluate('document.querySelector("video").currentTime'),page_sha256=hashlib.sha256((root/'measurement_demo.html').read_bytes()).hexdigest(),delivery_sha256=hashlib.sha256((root/'measurement_delivery.json').read_bytes()).hexdigest())
 (root/'previews/measurement_film_inspection_01/player_review.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n');print(json.dumps(record,ensure_ascii=False))
 browser.close()
