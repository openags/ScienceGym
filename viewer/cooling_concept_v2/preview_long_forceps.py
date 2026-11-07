"""Inspect both reconstructed long-forceps states on the actual lab bench."""
import base64
import hashlib
import json
import os
from playwright.sync_api import sync_playwright
from export_audit import HERE, BROWSER
from long_forceps import OUT

INSPECTOR = '''
let forcepsPreview;
window.previewForceps=async({path,sha})=>{
 window.renderAt(81.0900131285031);
 if(forcepsPreview)scene.remove(forcepsPreview);
 forcepsPreview=await load(path,sha);
 forcepsPreview.position.set(3.48,8.63,.850001);
 forcepsPreview.rotation.z=.18;
 scene.add(forcepsPreview);
 const target=new THREE.Vector3(3.48,8.63,.856);
 camera.position.copy(target).add(new THREE.Vector3(.06,-.28,.24));camera.lookAt(target);
 localKey.intensity=2.;localKey.position.copy(target).add(new THREE.Vector3(-.15,-.25,.4));localKey.target.position.copy(target);
 scene.updateMatrixWorld(true);renderer.render(scene,camera);
 return renderer.domElement.toDataURL('image/jpeg',.96).split(',')[1];
};
'''


def main():
    config=json.loads((OUT/'revision.json').read_text())
    folder=OUT/'previews';folder.mkdir(exist_ok=True)
    source=(HERE/'main.js').read_text();errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=BROWSER,args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':1280,'height':960})
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('**/cooling_concept_v2/main.js',lambda r:r.fulfill(status=200,content_type='application/javascript',body=source+INSPECTOR))
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean&episode=cary_access',timeout=120000)
        page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000)
        for name,variant in config['variants'].items():
            encoded=page.evaluate('(x)=>previewForceps(x)',dict(path=variant['geometry'],sha=variant['sha256']))
            (folder/(name+'.jpg')).write_bytes(base64.b64decode(encoded))
        browser.close()
    assert not errors,errors
    (folder/'capture.json').write_text(json.dumps(dict(scope=__doc__,errors=errors,
        staging_is_inspection_only=True,source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest()
        for n in ['main.js','cary_episode.js','cary_access_episode.json','preview_long_forceps.py']},
        asset_revision_sha256=hashlib.sha256((OUT/'revision.json').read_bytes()).hexdigest()),indent=2)+'\n')
    print('Captured 2 long-forceps views',flush=True)


if __name__=='__main__':main()
