"""Check optical grasp candidates with the source G1 seven-joint arm."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent
inputs={kind:json.loads((HERE/f'previews/optical_{kind}_search.json').read_text()) for kind in ['reference','cover']}
setup=json.loads((HERE/'optical_setup.json').read_text())
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page();page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean')
    result=page.evaluate('''async(data)=>{
      const {HandIK}=await import('./hand_ik.js'),T=await import('three');
      const m=await(await fetch('../../assets/cooling_lab_v1/scene.json')).json(),poses=await(await fetch('./motion_poses.json')).json();
      const ik=new HandIK(m.inspection_states.find(s=>s.id==='g1_hands_inspection').kinematics);
      const rows=[];
      for(const [kind,search] of Object.entries(data.inputs))for(const [id,c] of search.candidates.entries()){
        const profile=new T.Matrix4().fromArray(c.palm_matrix.flat()).transpose();
        for(const waist of [.15,.3,.45])for(const rootY of [7.85])for(const rootX of [8.95,9.05,9.15]){
          const root=new T.Matrix4().makeRotationZ(Math.PI/2).setPosition(rootX,rootY,-.025).invert();
          const knots=[];
          if(kind==='reference'){
            const port=data.setup.ports.ftir_sample.position_m;
            for(const offset of [[0,0,0],[0,0,.08],[0,-.10,.15],[.05,-.20,.15]])knots.push(new T.Matrix4().makeTranslation(...port.map((x,i)=>x+offset[i])).multiply(profile));
          }else{
            const center=new T.Vector3(...search.handle_center_m),hinge=new T.Vector3(9.189,8.4452500052,1.10);
            for(let i=0;i<=8;i++){
              const rotation=new T.Matrix4().makeRotationX(-Math.PI/2*i/8);
              const local=center.clone().sub(hinge).applyMatrix4(rotation).add(hinge);
              knots.push(rotation.clone().setPosition(local).multiply(profile));
            }
          }
          let maximum=0,orientation=0;const errors=[];
          for(const world of knots){
            const target=root.clone().multiply(world),q={...poses.poses.rest,...poses.poses.stance,waist_pitch_joint:waist};
            const e=ik.solve(q,'right',new T.Vector3().setFromMatrixPosition(target),target);
            maximum=Math.max(maximum,e);orientation=Math.max(orientation,ik.lastRotationError);errors.push(e);
          }
          rows.push({kind,candidate:id,waist,root_y_m:rootY,root_x_m:rootX,maximum_position_error_m:maximum,maximum_orientation_error_rad:orientation,errors});
        }
      }
      return rows;
    }''',dict(inputs=inputs,setup=setup))
    browser.close()
result.sort(key=lambda r:r['maximum_position_error_m']+.1*r['maximum_orientation_error_rad'])
(HERE/'previews/optical_reach_search.json').write_text(json.dumps(dict(scope=__doc__,candidates=result),indent=2)+'\n')
for kind in inputs:
    print(kind,json.dumps([r for r in result if r['kind']==kind][:3]),flush=True)
