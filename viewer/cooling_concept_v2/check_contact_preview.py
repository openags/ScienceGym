"""Review representative corrected manipulation frames before any film export."""
import base64,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parent
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
    page=browser.new_page(viewport={'width':1280,'height':720});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean',timeout=120000);page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000)
    phases=page.evaluate('concept.phases');output=HERE/'previews';output.mkdir(exist_ok=True);report=[]
    for name in ['pick_white','carry_white','place_white','carry_black','take_cart_handle','outdoor_transfer','unload_black','unload_white','open_white','cover_white']:
        phase=next(x for x in phases if x['id']==name);t=phase['start']+phase['duration']*.55
        frame=page.evaluate('(t)=>auditFrame(t)',t);report.append(dict(phase=name,time_s=t,targets=frame['hand_targets']))
        (output/(name+'.jpg')).write_bytes(base64.b64decode(page.evaluate('(t)=>concept.frameJpeg(t)',t)))
    (output/'contact_preview.json').write_text(json.dumps(dict(errors=errors,frames=report),indent=2)+'\n')
    print(json.dumps(dict(errors=errors,maximum_hand_target_error_m=max(t['position_error_m'] for f in report for t in f['targets']))),flush=True)
    browser.close()
