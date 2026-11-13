"""Capture supported optical specimens inside the complete development lab."""
import base64,hashlib,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent
CAMERA_ONLY='''
window.specimenPreview=close=>{renderAt(0);const target=V([3.115,8.2,.85]);camera.position.copy(target).add(V(close?[.08,-.10,.12]:[.42,-.60,.45]));camera.lookAt(target);localKey.position.copy(target).add(V([0,-.4,1]));localKey.target.position.copy(target);renderer.render(scene,camera);return renderer.domElement.toDataURL('image/jpeg',.96).split(',')[1];};
'''


def main():
    out=HERE/'previews/specimen_staging';out.mkdir(exist_ok=True);source=(HERE/'main.js').read_text();errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':1280,'height':720});page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/cooling_concept_v2/main.js',lambda r:r.fulfill(status=200,content_type='application/javascript',body=source+CAMERA_ONLY))
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean',timeout=120000);page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000)
        for close in [False,True]:(out/('closeup.jpg' if close else 'bench.jpg')).write_bytes(base64.b64decode(page.evaluate('(close)=>specimenPreview(close)',close)))
        workflow=page.evaluate('({duration_s:concept.duration,phases:concept.phases,asset_count:concept.assetCount})')
        (out/'preview.json').write_text(json.dumps(dict(main_sha256=hashlib.sha256(source.encode()).hexdigest(),runtime_scene_sha256=hashlib.sha256((HERE/'runtime_scene.json').read_bytes()).hexdigest(),workflow=workflow,camera_only_injection=CAMERA_ONLY,errors=errors),indent=2,ensure_ascii=False)+'\n');assert not errors
        browser.close();print('saved lab previews',workflow['asset_count'],flush=True)


if __name__=='__main__':main()
