"""Capture wide and contact views from the continuous local optical episode."""
import base64
import hashlib
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from export_audit import BROWSER,HERE

CAMERA_INSPECTOR='''
window.opticalContactJpeg=t=>{
 window.renderAt(t);const target=new THREE.Vector3().setFromMatrixPosition(groups.get('tweezers_white').matrixWorld);
 camera.position.copy(target).add(new THREE.Vector3(.28,-.36,.30));camera.lookAt(target);
 renderer.render(scene,camera);return renderer.domElement.toDataURL('image/jpeg',.96).split(',')[1];
};
'''


def main():
    out=HERE/'previews/optical_episode_inspection';out.mkdir(exist_ok=True)
    config=json.loads((HERE/'optical_episode.json').read_text());segments={s['id']:s for s in config['segments']};source=(HERE/'main.js').read_text()
    errors=[];captures=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=BROWSER,args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':1280,'height':720});page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('**/cooling_concept_v2/main.js',lambda route:route.fulfill(status=200,content_type='application/javascript',body=source+CAMERA_INSPECTOR))
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean&episode=ftir',timeout=120000)
        page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000)
        for name,fraction in [('white_mount_close_hand_on_tool',1),('white_mount_close_tweezers',1),('white_mount_to_port',.5),('white_mount_seat',1),('white_retrieve_lift',.5),('black_mount_close_tweezers',1),('black_mount_seat',1),('black_retrieve_seat',1)]:
            segment=segments[name];time=segment['start']+fraction*segment['duration_s']
            for close in [False,True]:
                file=name+('_close' if close else '_wide')+'.jpg'
                encoded=page.evaluate('(t)=>'+('opticalContactJpeg(t)' if close else 'concept.frameJpeg(t)'),time)
                (out/file).write_bytes(base64.b64decode(encoded));captures.append(dict(path=file,time_s=time,phase=name,contact_camera=close))
        assert not errors,errors;browser.close()
    report=dict(scope=__doc__,camera_override=CAMERA_INSPECTOR,captures=captures,errors=errors,source_sha256={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ['main.js','optical_episode.js','optical_episode.json','runtime_scene.json','preview_optical_episode.py']})
    (out/'preview.json').write_text(json.dumps(report,indent=2)+'\n');print('captured',len(captures),flush=True)


if __name__=='__main__':main()
