"""Capture reference handling from inspection cameras without changing motion."""
import base64
import hashlib
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent
CAMERA_ONLY='''
window.referencePreview=(t,closeup)=>{
 renderAt(t);const r=robotAt(t),target=new THREE.Vector3().setFromMatrixPosition(r.referenceState.reference);
 if(closeup){camera.position.copy(target).add(V([-.45,-.4,.35]));camera.lookAt(target.clone().add(V([0,0,.06])));}
 else{camera.position.set(r.position.x-1.1,r.position.y-1.6,1.85);camera.lookAt(r.position.clone().add(V([0,.2,.80])));}
 renderer.render(scene,camera);return renderer.domElement.toDataURL('image/jpeg',.95).split(',')[1];
};
'''


def main():
    out=HERE/'previews/reference_integrated_02';out.mkdir(exist_ok=True)
    source=(HERE/'main.js').read_text();records=[];errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':1280,'height':720});page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('**/cooling_concept_v2/main.js',lambda route:route.fulfill(status=200,content_type='application/javascript',body=source+CAMERA_ONLY))
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean',timeout=120000);page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000)
        phase=page.evaluate('concept.phases.find(p=>p.id==="reference_store")');data=json.loads((HERE/'reference_transfer.json').read_text())
        for name in ['close_grip','lift','sidestep','seat_in_cap','release_grip']:
            segment=next(s for s in data['segments'] if s['id']==name);t=phase['start']+(segment['start']+segment['end'])/2
            for closeup in [False,True]:
                file=out/(name+('_closeup' if closeup else '')+'.jpg');jpeg=page.evaluate('(p)=>referencePreview(p.t,p.closeup)',dict(t=t,closeup=closeup));file.write_bytes(base64.b64decode(jpeg));records.append(dict(file=file.name,time_s=t,closeup=closeup))
        assert not errors
        (out/'preview.json').write_text(json.dumps(dict(main_sha256=hashlib.sha256(source.encode()).hexdigest(),camera_only_injection=CAMERA_ONLY,records=records),indent=2)+'\n');browser.close();print('saved',len(records),flush=True)


if __name__=='__main__':main()
