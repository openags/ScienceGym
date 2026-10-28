"""Reject local pinch fits that the actual seven-joint arm cannot reach."""
import hashlib,json
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parent
source=HERE/'previews/lid_grasp_search.json';candidates=json.loads(source.read_text())['candidates']
selected=[dict(candidate_id=i,**c) for i,c in enumerate(candidates) if c['opposed'] and max(c['finger_gap_m'],c['thumb_gap_m'])<.006]
with sync_playwright() as playwright:
    browser=playwright.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page();page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean')
    result=page.evaluate('''async(candidates)=>{
      const {HandIK}=await import('./hand_ik.js'),THREE=await import('three');
      const m=await(await fetch('../../assets/cooling_lab_v1/scene.json')).json(),p=await(await fetch('./motion_poses.json')).json();
      const ik=new HandIK(m.inspection_states.find(s=>s.id==='g1_hands_inspection').kinematics);
      const root=new THREE.Matrix4().makeRotationZ(Math.PI/2).setPosition(0,0,-.025).invert();
      const knots=[[0,.43,1.001006],[0,.41,1.021006],[0,.31,1.041006],[.30,.30,1.021],[.30,.30,.901]],out=[];
      for(const candidate of candidates){
        const profile=new THREE.Matrix4().fromArray(candidate.palm_matrix.flat()).transpose();profile.elements[14]-=.101006;
        let maximum=0,rotationMax=0;const errors=[];
        const points=[...knots,[0,.37,1.081006],[.30,.24,.981]];
        for(let i=1;i<knots.length;i++)for(const u of [.25,.5,.75])points.push(knots[i-1].map((x,k)=>x+(knots[i][k]-x)*u));
        for(const v of points){
          const target=new THREE.Matrix4().makeTranslation(...v).multiply(profile).premultiply(root);
          const q={...p.poses.rest,...p.poses.stance,waist_pitch_joint:.15};
          const error=ik.solve(q,'right',new THREE.Vector3().setFromMatrixPosition(target),target);
          maximum=Math.max(maximum,error);rotationMax=Math.max(rotationMax,ik.lastRotationError);errors.push(error);
        }
        out.push({candidate_id:candidate.candidate_id,maximum_position_error_m:maximum,maximum_orientation_error_rad:rotationMax,errors});
      }return out;
    }''',selected)
    browser.close()
result.sort(key=lambda c:c['maximum_position_error_m']+.1*c['maximum_orientation_error_rad'])
report=dict(search_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),candidates=result,scope='Sampled arm reach of geometry-qualified local fits; not collision or dynamics qualification')
(HERE/'previews/lid_reach_search.json').write_text(json.dumps(report,indent=2)+'\n')
print('tested',len(result),'best',json.dumps(result[:4]),flush=True)
