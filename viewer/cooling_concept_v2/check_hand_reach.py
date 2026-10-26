"""Review complete grasp transitions, including intermediate IK solutions."""
import hashlib,json,os,time
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parent
pins={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['main.js','hand_ik.js','motion_poses.json','grasp_profile.json','optical_setup.json','optical_approach_paths.json','manipulation_motion.js','manipulation_approach_paths.json','lid_contact_paths.json']}
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
    page=browser.new_page(viewport={'width':1280,'height':720});page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean',timeout=120000);page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000)
    phases=page.evaluate("concept.phases.filter(p=>['pick','place','push_grip','push_release','ftir_open','ftir_close'].includes(p.action)||['carry','push'].includes(p.mode)||p.action?.startsWith('lid_')||p.action?.startsWith('cover_'))")
    records=[];maximum=0;worst={};planned_joint_samples=0
    for phase in phases:
        times=[phase['start']+i/10 for i in range(int(phase['duration']*10)+1)]+[phase['end']-.00001]
        frames=page.evaluate('(times)=>times.map(t=>handCheck(t))',times);records.extend(frames)
        for frame in frames:
            for target in frame['targets']:
                error=target['position_error_m'] if target['position_error_m'] is not None else target['waypoint_position_error_m']
                if error is None:
                    planned_joint_samples+=1;continue
                maximum=max(maximum,error)
                if error>.003:worst[phase['id']]=max(worst.get(phase['id'],0),error)
        print(phase['id'],round(max(t['position_error_m'] or 0 for f in frames for t in f['targets']),5),flush=True)
    assert all(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==sha for n,sha in pins.items())
    report=dict(passed=not worst,maximum_position_error_m=maximum,failed_phases=worst,samples=len(records),planned_joint_samples_without_cartesian_error=planned_joint_samples,sample_frequency_hz=10,source_sha256=pins,scope='Hand-target reach only; planned free-arm joint paths have no Cartesian tracking target here. Collision, grip closure, continuity and support must also pass')
    (HERE/'previews/hand_reach.json').write_text(json.dumps(report,indent=2)+'\n')
    (HERE/'previews/hand_reach_frames.json').write_text(json.dumps(records,separators=(',',':'))+'\n')
    print(json.dumps(report),flush=True);browser.close()
    if not report['passed']:raise SystemExit(1)
