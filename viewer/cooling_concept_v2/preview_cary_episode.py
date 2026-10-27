"""Capture whole-body and handle views of the actual composed Cary episode."""
import base64,hashlib,json,os
from playwright.sync_api import sync_playwright
from export_audit import BROWSER,HERE

INSPECTOR='''
window.caryContactJpeg=({time,part})=>{
 window.renderAt(time);
 const node=nodeRest.find(n=>n.asset==='cary'&&n.node.name===part).node;
 node.geometry.computeBoundingBox();const target=node.geometry.boundingBox.getCenter(new THREE.Vector3()).applyMatrix4(node.matrixWorld);
 camera.position.copy(target).add(new THREE.Vector3(.27,-.38,.32));camera.lookAt(target);
 renderer.render(scene,camera);return renderer.domElement.toDataURL('image/jpeg',.96).split(',')[1];
};
'''


def main():
    out=HERE/'previews/cary_episode_inspection';out.mkdir(exist_ok=True)
    config=json.loads((HERE/'cary_access_episode.json').read_text());segments={s['id']:s for s in config['segments']};source=(HERE/'main.js').read_text();errors=[];captures=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=BROWSER,args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':1280,'height':960});page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('**/cooling_concept_v2/main.js',lambda r:r.fulfill(status=200,content_type='application/javascript',body=source+INSPECTOR))
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean&episode=cary_access',timeout=120000);page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000)
        for name,fraction in [('lid_close',1),('lid_slide',.8),('hood_close',1),('hood_unhook',1),('hood_step_back',.7),('hood_carry_sideways',.5),('hood_lower_onto_support',1),('hood_return_hand',1)]:
            s=segments[name];t=s['start']+fraction*s['duration_s'];part='sample_lid_pull' if name.startswith('lid_') else 'extension_pull_bar'
            for close in [False,True]:
                file=name+('_close' if close else '_wide')+'.jpg'
                encoded=page.evaluate('(x)=>caryContactJpeg(x)',dict(time=t,part=part)) if close else page.evaluate('(t)=>concept.frameJpeg(t)',t)
                (out/file).write_bytes(base64.b64decode(encoded));captures.append(dict(path=file,time_s=t,phase=name,contact_camera=close))
        assert not errors,errors;browser.close()
    report=dict(scope=__doc__,camera_override=INSPECTOR,captures=captures,errors=errors,source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['main.js','cary_episode.js','cary_access_episode.json','runtime_scene.json','preview_cary_episode.py']})
    (out/'preview.json').write_text(json.dumps(report,indent=2)+'\n');print('captured',len(captures),flush=True)


if __name__=='__main__':main()
