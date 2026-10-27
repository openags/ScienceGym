"""Capture delivery posture, turning, Cary collection and FTIR placement."""
import base64,hashlib,json,os
from playwright.sync_api import sync_playwright
from export_audit import BROWSER,HERE
from preview_optical_episode import CAMERA_INSPECTOR


def main():
    out=HERE/'previews/optical_delivery_inspection';out.mkdir(exist_ok=True);config=json.loads((HERE/'optical_delivery_episode.json').read_text());segments={s['id']:s for s in config['segments']};source=(HERE/'main.js').read_text();errors=[];captures=[]
    selected=[('white_delivery_walk_to_cary_forward_walk',.30,False),('white_delivery_walk_to_cary_forward_walk',.60,False),('white_delivery_close_tweezers',1,False),('white_delivery_close_tweezers',1,True),('white_delivery_carry_to_ftir_forward_walk',.50,False),('white_delivery_place_lift_witness',1,False),('black_delivery_close_tweezers',1,True),('black_delivery_carry_to_ftir_forward_walk',.50,False),('black_delivery_place_lift_witness',1,True),('white_mount_seat',1,False)]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=BROWSER,args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':1280,'height':720});page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/cooling_concept_v2/main.js',lambda r:r.fulfill(status=200,content_type='application/javascript',body=source+CAMERA_INSPECTOR))
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean&episode=ftir_delivery',timeout=120000);page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000)
        for name,fraction,close in selected:
            segment=segments[name];time=segment['start']+fraction*segment['duration_s'];file=name+'_'+str(fraction)+('_close' if close else '_wide')+'.jpg';encoded=page.evaluate('(t)=>'+('opticalContactJpeg(t)' if close else 'concept.frameJpeg(t)'),time);(out/file).write_bytes(base64.b64decode(encoded));captures.append(dict(path=file,time_s=time,phase=name,contact_camera=close))
        assert not errors;browser.close()
    (out/'preview.json').write_text(json.dumps(dict(scope=__doc__,captures=captures,errors=errors,source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['main.js','optical_episode.js','optical_delivery_episode.json','preview_optical_delivery.py','preview_optical_episode.py']}),indent=2)+'\n');print('captured',len(captures),flush=True)


if __name__=='__main__':main()
