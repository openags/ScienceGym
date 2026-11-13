"""Inspect the composed measurement in the original complete laboratory."""
import argparse
import hashlib
import json
import os
from playwright.sync_api import sync_playwright
from export_audit import BROWSER, HERE
from render_capture_checks import save_checked_jpeg


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--trial',default='01');args=parser.parse_args()
    out=HERE/'previews'/('measurement_inspection_'+args.trial);out.mkdir(exist_ok=False)
    episode=json.loads((HERE/'single_measurement_episode.json').read_text())
    names=['main.js','measurement_episode.js','measurement_source_actions.js','single_measurement_episode.json',
           'reference_motion.js','reference_transfer.json','optical_setup.json','grasp_profile.json',
           'runtime_scene.json','preview_measurement_episode.py','render_capture_checks.py']
    pins={}
    for name in names:
        data=(HERE/name).read_bytes();dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(data);pins[name]=hashlib.sha256(data).hexdigest()
    selected={
      'initial_open':.6,'white_delivery_walk_to_cary_forward_walk':.5,
      'white_delivery_lift_witness':.9,'white_delivery_carry_to_ftir_forward_walk':.5,
      'install_gold_reference':.65,'background_select_touch_and_press':1.,
      'background_acquisition':.5,'store_gold_reference':.7,
      'white_mount_seat':.9,'sample_select_touch_and_press':1.,
      'sample_acquisition':.5,'white_retrieve_seat':.9,'final_close':1.}
    errors=[];console=[];images=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=BROWSER,args=['--no-sandbox','--disable-dev-shm-usage',
            '--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],
            env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':1280,'height':720})
        def error(value):
            errors.append(str(value));print('pageerror',str(value),flush=True)
        page.on('pageerror',error)
        page.on('console',lambda message:console.append(dict(type=message.type,text=message.text)) if message.type in ['warning','error'] else None)
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?episode=ftir_measurement&clean',timeout=120000)
        try:
            page.wait_for_function('document.documentElement.dataset.ready==="true" && window.concept?.measurementEpisode',timeout=120000)
            for segment in episode['segments']:
                if segment['id'] not in selected:continue
                t=segment['start']+segment['duration_s']*selected[segment['id']]
                encoded=page.evaluate('t=>concept.frameJpeg(t)',t);path=out/(segment['id']+'.jpg')
                quality=save_checked_jpeg(encoded,path)
                images.append(dict(phase=segment['id'],time_s=t,path=path.name,quality=quality,
                                   sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
                print('captured',segment['id'],flush=True)
            checks=page.evaluate('''segments=>{
              const matrixError=(a,b)=>Math.max(...a.map((v,i)=>Math.abs(v-b[i])));
              const boundaries=[];
              for(const s of segments.slice(1)){
                const a=auditFrame(s.start-1e-6),b=auditFrame(s.start+1e-6);
                const jointError=Math.max(...Object.keys(a.joints).map(n=>Math.abs(a.joints[n]-b.joints[n])));
                const groupError=Math.max(...Object.keys(a.groups).map(n=>matrixError(a.groups[n],b.groups[n])));
                const parts=new Map(b.parts.map(p=>[p.asset+'::'+p.name,p.matrix]));
                const partError=Math.max(...a.parts.map(p=>matrixError(p.matrix,parts.get(p.asset+'::'+p.name))));
                boundaries.push({phase:s.id,joint_error_rad:jointError,group_matrix_error:groupError,part_matrix_error:partError,
                  passed:jointError<1e-4&&groupError<1e-4&&partError<1e-4});
              }
              const first=auditFrame(0),last=auditFrame(concept.duration);
              return {boundaries,asset_count:concept.assetCount,robot_count:concept.robotCount,
                first,last,duration_s:concept.duration};
            }''',episode['segments'])
            assert not errors,errors
        except Exception:
            (out/'failure.json').write_text(json.dumps(dict(errors=errors,console=console,
                page_state=page.evaluate('({ready:document.documentElement.dataset.ready,text:document.body.innerText.slice(0,1500)})')),
                indent=2)+'\n');raise
        browser.close()
    assert all(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==sha for n,sha in pins.items())
    (out/'capture.json').write_text(json.dumps(dict(scope=__doc__,images=images,errors=errors,console=console,
        source_sha256=pins,boundary_checks=checks['boundaries'],asset_count=checks['asset_count'],robot_count=checks['robot_count'],
        duration_s=checks['duration_s'],passed_boundary_checks=all(v['passed'] for v in checks['boundaries']),
        limitations=['Snapshots and continuity checks do not establish collision-free motion or physical qualification.']),indent=2)+'\n')
    (out/'endpoints.json').write_text(json.dumps({k:checks[k] for k in ['first','last']},separators=(',',':'))+'\n')
    print(json.dumps(dict(images=len(images),duration_s=checks['duration_s'],
                          bad_boundaries=[v for v in checks['boundaries'] if not v['passed']])),flush=True)


if __name__=='__main__':main()
