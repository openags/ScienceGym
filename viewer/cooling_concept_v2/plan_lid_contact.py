"""Create continuous aperture-cover arm seeds between planned free-arm endpoints.

Forward and backward IK continuations preserve each path's endpoint branch.
A smooth interior blend is projected back onto the authored palm targets.
Whole-scene sampled contact/velocity review is still required afterward.
"""
import hashlib
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent


def main():
    names=['main.js','manipulation_motion.js','manipulation_approach_paths.json','hand_ik.js','grasp_profile.json','motion_poses.json']
    pins={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names}
    packet=json.loads((HERE/'previews/manipulation_approach_inputs.json').read_text())
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',
            args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],
            env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':640,'height':360});page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean',timeout=120000)
        page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000)
        paths=page.evaluate('''async inputs=>{
          const {HandIK}=await import('./hand_ik.js'),T=await import('three');
          const m=await(await fetch('../../assets/cooling_lab_v1/scene.json')).json();
          const profile=(await(await fetch('./grasp_profile.json')).json()).lid;
          const kin=m.inspection_states.find(s=>s.id==='g1_hands_inspection').kinematics;
          const ik=new HandIK(kin),result={};
          for(const id of ['open_white','open_black','cover_white','cover_black']){
            const phase=concept.phases.find(p=>p.id===id),entry=inputs[id+'_entry'].target,exit=inputs[id+'_exit'].target;
            const root=new T.Matrix4().fromArray(entry.groups.g1),inverse=root.clone().invert();
            const lid=new T.Matrix4().fromArray(entry.extra_matrices['aperture_lid_'+(id.includes('white')?'white':'black')]);
            const rotation=inverse.clone().multiply(lid).multiply(new T.Matrix4().fromArray(profile.palm_matrix.flat()).transpose());
            const points=[],times=[],forward=[],backward=[],knots=[];
            for(let i=0;i<=352;i++){
              const oldElapsed=2+8.8*i/352,time=phase.start+phase.motionTiming.entry+oldElapsed-2;
              const target=handCheck(time).targets.find(t=>t.side==='right').target_m;
              times.push(oldElapsed);points.push(new T.Vector3(...target).applyMatrix4(inverse));
            }
            const forwardErrors=[],backwardErrors=[];
            let q={...entry.joints};
            for(const point of points){forwardErrors.push(ik.iterate(q,'right',point,rotation,120));forward.push({...q});}
            q={...exit.joints};
            for(let i=points.length-1;i>=0;i--){backwardErrors[i]=ik.iterate(q,'right',points[i],rotation,120);backward[i]={...q};}
            let maximumError=0,maximumRotation=0,maximumJointStep=0;
            for(let i=0;i<points.length;i++){
              const u=i/(points.length-1),amount=u*u*(3-2*u);q={...entry.joints};
              for(const j of ik.arm.right)q[j.name]=forward[i][j.name]+amount*(backward[i][j.name]-forward[i][j.name]);
              const solved=ik.iterate(q,'right',points[i],rotation,120);
              if(i===0)for(const j of ik.arm.right)q[j.name]=entry.joints[j.name];
              if(i===points.length-1)for(const j of ik.arm.right)q[j.name]=exit.joints[j.name];
              const palm=ik.forward(q).world.get('right_palm_force_sensor');
              const error=new T.Vector3().setFromMatrixPosition(palm).distanceTo(points[i]);
              const rotationError=new T.Quaternion().setFromRotationMatrix(palm).angleTo(new T.Quaternion().setFromRotationMatrix(rotation));
              maximumError=Math.max(maximumError,error);maximumRotation=Math.max(maximumRotation,rotationError);
              const values=Object.fromEntries(ik.arm.right.map(j=>[j.name,q[j.name]]));
              if(i)maximumJointStep=Math.max(maximumJointStep,...ik.arm.right.map(j=>Math.abs(q[j.name]-knots[i-1].q[j.name])));
              knots.push({elapsed_s:times[i],q:values,position_error_m:error,orientation_error_rad:rotationError});
            }
            const branch=values=>values.map((q,i)=>({elapsed_s:times[i],q:Object.fromEntries(ik.arm.right.map(j=>[j.name,q[j.name]]))}));
            result[id]={knots,forward:branch(forward),backward:branch(backward),forward_errors:forwardErrors,backward_errors:backwardErrors,maximum_position_error_m:maximumError,maximum_orientation_error_rad:maximumRotation,maximum_joint_step_rad:maximumJointStep,
              forward_maximum_error_m:Math.max(...forwardErrors.map(e=>e.error)),backward_maximum_error_m:Math.max(...backwardErrors.map(e=>e.error))};
          }
          return result;
        }''',packet['frames'])
        browser.close()
    assert all(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==sha for n,sha in pins.items())
    report=dict(scope=__doc__,source_sha256=pins,generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),paths=paths)
    (HERE/'previews/lid_contact_candidates.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({name:{k:v for k,v in value.items() if not isinstance(v,list)} for name,value in paths.items()}),flush=True)


if __name__=='__main__':main()
