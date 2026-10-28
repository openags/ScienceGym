"""Export exact scene transforms, independently of camera framing or video."""
import argparse,gzip,hashlib,json,os,re,time
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent
BROWSER='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell'

def export(out,step,phase_pattern=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    pins={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['main.js','motion_poses.json','hand_ik.js','grasp_profile.json','optical_setup.json','optical_approach_paths.json','export_audit.py']}
    snapshots=out/'source';snapshots.mkdir(exist_ok=True)
    for name in pins:(snapshots/name).write_bytes((HERE/name).read_bytes())
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=BROWSER,args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':1280,'height':720});errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean',timeout=120000)
        page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000)
        info=page.evaluate('({duration:concept.duration,phases:concept.phases,sourceHashes:concept.sourceHashes,extraGeometry:concept.extraGeometry||[]})')
        selected=[p for p in info['phases'] if not phase_pattern or re.search(phase_pattern,p['id'])]
        if not selected:raise ValueError('No matching phases')
        times={min(i*step,info['duration']) for i in range(int(info['duration']/step)+2)}
        if phase_pattern:times={t for t in times if any(p['start']<=t<=p['end'] for p in selected)}
        for phase in selected:
            times.update([phase['start'],min(phase['end'],phase['start']+.00001),(phase['start']+phase['end'])/2,max(phase['start'],phase['end']-.00001),phase['end']])
        frame_digest=hashlib.sha256()
        with gzip.open(out/'frames.jsonl.gz','wt') as stream:
            for i,t in enumerate(sorted(times)):
                frame=page.evaluate('(t)=>auditFrame(t)',t);line=json.dumps(frame,separators=(',',':'))+'\n';stream.write(line);frame_digest.update(line.encode())
                if i%200==0:print('frame',i,'time',round(t,2),flush=True)
        if errors:raise RuntimeError(errors)
        assert all(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==sha for n,sha in pins.items())
        receipt=dict(source_sha256=pins,sample_step_s=step,phase_pattern=phase_pattern,selected_phases=[p['id'] for p in selected],frame_count=len(times),scene=info,frames_sha256=frame_digest.hexdigest(),compressed_frames_sha256=hashlib.sha256((out/'frames.jsonl.gz').read_bytes()).hexdigest())
        (out/'export.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
        browser.close();print('exported',len(times),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('out');parser.add_argument('--step',type=float,default=.5);parser.add_argument('--phases');args=parser.parse_args();export(args.out,args.step,args.phases)
