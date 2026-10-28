"""Refine the optical-reference stance without relaxing grasp or arm limits."""
import argparse,hashlib,json
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--side',choices=['right','left'],default='right');args=parser.parse_args()
source=HERE/('previews/optical_reference_left_search.json' if args.side=='left' else 'previews/optical_reference_search.json')
records=json.loads(source.read_text())['candidates']
selected=[dict(candidate=i,**r) for i,r in enumerate(records) if max(r['finger_gap_m'],r['thumb_gap_m'])<.003]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page();page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean')
    result=page.evaluate('''async(data)=>{
      const {candidates,side}=data;
      const {HandIK}=await import('./hand_ik.js'),T=await import('three');
      const m=await(await fetch('../../assets/cooling_lab_v1/scene.json')).json(),poses=await(await fetch('./motion_poses.json')).json(),setup=await(await fetch('./optical_setup.json')).json();
      const kin=m.inspection_states.find(s=>s.id==='g1_hands_inspection').kinematics;
      if(side==='left')kin.joints.find(j=>j.name==='left_shoulder_roll_joint').limits.lower=.025;
      const ik=new HandIK(kin),rows=[];
      for(const c of candidates){
        const profile=new T.Matrix4().fromArray(c.palm_matrix.flat()).transpose();
        for(const waist of [.15,.3,.45])for(const rootY of [7.85,7.90])for(const rootX of (side==='left'?[9.25,9.35]:[8.95,9.05]))for(const yaw of (side==='left'?[1.5,1.7,1.9]:[1.1,1.3,1.5])){
          const root=new T.Matrix4().makeRotationZ(yaw).setPosition(rootX,rootY,-.025).invert();
          let maximum=0,orientation=0;const errors=[];
          for(const offset of [[0,0,0],[0,0,.08],[0,-.1,.15],[.05,-.2,.15]]){
            const target=new T.Matrix4().makeTranslation(...setup.ports.ftir_sample.position_m.map((x,i)=>x+offset[i])).multiply(profile).premultiply(root);
            const q={...poses.poses.rest,...poses.poses.stance,waist_pitch_joint:waist};
            const error=ik.solve(q,side,new T.Vector3().setFromMatrixPosition(target),target);
            maximum=Math.max(maximum,error);orientation=Math.max(orientation,ik.lastRotationError);errors.push(error);
            if(error>.005||ik.lastRotationError>.04)break;
          }
          rows.push({candidate:c.candidate,waist,root_position_m:[rootX,rootY],yaw,maximum_position_error_m:maximum,maximum_orientation_error_rad:orientation,errors,complete:errors.length===4});
        }
      }return rows;
    }''',dict(candidates=selected,side=args.side))
    browser.close()
passed=[r for r in result if r['complete'] and r['maximum_position_error_m']<.003 and r['maximum_orientation_error_rad']<.02]
passed.sort(key=lambda r:r['maximum_position_error_m']+.1*r['maximum_orientation_error_rad'])
report=dict(scope=__doc__,side=args.side,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),tried=len(result),passed=passed,candidates=result)
(HERE/f'previews/optical_reference_{args.side}_stance.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(tried=len(result),passed=len(passed),best=passed[:3])),flush=True)
