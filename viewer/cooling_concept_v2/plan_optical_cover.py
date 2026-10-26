"""Search continuous, outward-elbow arm solutions for the optical cover."""
import hashlib,json
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parent
source=HERE/'previews/optical_cover_search.json';search=json.loads(source.read_text())
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page();page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean')
    result=page.evaluate('''async(search)=>{
      const {HandIK}=await import('./hand_ik.js'),T=await import('three');
      const m=await(await fetch('../../assets/cooling_lab_v1/scene.json')).json(),poses=await(await fetch('./motion_poses.json')).json();
      const kin=m.inspection_states.find(s=>s.id==='g1_hands_inspection').kinematics;
      // An additional planning constraint; source hardware limits are unchanged.
      kin.joints.find(j=>j.name==='right_shoulder_roll_joint').limits.upper=-.025;
      const ik=new HandIK(kin),passed=[],failed=[];
      for(const [id,c] of search.candidates.entries())for(const waist of [.15,.3,.45])for(const rootX of [9.05,9.15,9.25]){
        const root=new T.Matrix4().makeRotationZ(Math.PI/2).setPosition(rootX,7.85,-.025).invert();
        const profile=new T.Matrix4().fromArray(c.palm_matrix.flat()).transpose(),hinge=new T.Vector3(9.189,8.4452500052,1.10),center=new T.Vector3(...search.handle_center_m);
        const q={...poses.poses.rest,...poses.poses.stance,...c.q,waist_pitch_joint:waist,left_shoulder_yaw_joint:.6};
        const knots=[];let worst=0,rotWorst=0,maxJump=0,ok=true,previous=null;
        for(let degree=0;degree<=65;degree+=5){
          const rotation=new T.Matrix4().makeRotationX(-degree*Math.PI/180);
          const world=rotation.clone().setPosition(center.clone().sub(hinge).applyMatrix4(rotation).add(hinge)).multiply(profile);
          const target=root.clone().multiply(world),position=new T.Vector3().setFromMatrixPosition(target);
          const error=degree===0?ik.solve(q,'right',position,target):ik.iterate(q,'right',position,target,100).error;
          const actual=ik.forward(q).world.get('right_palm_force_sensor');
          const rotationError=new T.Quaternion().setFromRotationMatrix(actual).angleTo(new T.Quaternion().setFromRotationMatrix(target));
          worst=Math.max(worst,error);rotWorst=Math.max(rotWorst,rotationError);
          if(previous)maxJump=Math.max(maxJump,...ik.arm.right.map(j=>Math.abs(q[j.name]-previous[j.name])));
          knots.push({angle_rad:-degree*Math.PI/180,q:{...q},position_error_m:error,orientation_error_rad:rotationError});previous={...q};
          if(error>.003||rotationError>.025||maxJump>.6){ok=false;break;}
        }
        const row={candidate:id,waist,root_position_m:[rootX,7.85],yaw:Math.PI/2,maximum_position_error_m:worst,maximum_orientation_error_rad:rotWorst,maximum_joint_step_rad:maxJump,knots};
        (ok?passed:failed).push(row);
      }return {passed,failed};
    }''',search)
    browser.close()
result['passed'].sort(key=lambda r:r['maximum_position_error_m']+.1*r['maximum_orientation_error_rad'])
report=dict(scope=__doc__,search_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),**result)
(HERE/'previews/optical_cover_plans.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=len(result['passed']),failed=len(result['failed']),best=[{k:v for k,v in r.items() if k!='knots'} for r in result['passed'][:3]])),flush=True)
