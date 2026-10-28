"""Inspect candidate FTIR extraction poses inside the existing full lab.

This isolated inspection starts with the witness already gripped at the port.
It does not insert a shortcut, teleport or credited operation into the film.
The original workflow and specimen staging are restored by reloading it.
"""
import base64,hashlib,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent
INSPECTION='''
window.inspectSpecimenPort=async(index,close)=>{
 const fit=await read('viewer/cooling_concept_v2/previews/specimen_tool_fit.json');
 const data=await read('viewer/cooling_concept_v2/previews/specimen_port_refined.json'),path=data.candidates[0],row=path.rows[index];
 renderAt(referenceStore.end+.01);
 const base=new THREE.Matrix4().fromArray(path.root),position=new THREE.Vector3().setFromMatrixPosition(base),r={...robotAt(referenceStore.end+.01),position,rootZ:position.z,yaw:path.stance.yaw};
 const originalJointPose=jointPose,originalConstrain=constrainHands;jointPose=()=>({...row.q});constrainHands=(_,q)=>q;poseRobot(r);jointPose=originalJointPose;constrainHands=originalConstrain;
 const palm=base.clone().multiply(handIK.forward(row.q).world.get('right_palm_force_sensor')),tool=palm.clone().multiply(M(fit.tool_T_palm).invert()),holder=tool.clone().multiply(M(fit.holder_T_tool).invert());
 const group=groups.get('tweezers_white');
 group.traverse(n=>{if(!n.isMesh||!n.name.startsWith('ptfe_spring_arm_'))return;if(!n.userData.openVertices)n.userData.openVertices=n.geometry.attributes.position.array.slice();const rest=n.userData.openVertices,p=n.geometry.attributes.position,sign=Number(n.name.split('_').at(-1));for(let i=0;i<p.count;i++){const x=rest[i*3],a=1-Math.min(1,Math.max(0,x/.130));p.setXYZ(i,x,rest[i*3+1]-sign*.001775*fit.carrier_grip_closure*a*a*(3-a)/2,rest[i*3+2]);}p.needsUpdate=true;n.geometry.computeVertexNormals();});
 tool.decompose(group.position,group.quaternion,group.scale);holder.decompose(witness.position,witness.quaternion,witness.scale);scene.updateMatrixWorld(true);
 const center=new THREE.Vector3().setFromMatrixPosition(holder);
 if(close){camera.position.copy(center).add(V([-.45,-.22,.40]));camera.lookAt(center.clone().add(V([0,0,.07])));}
 else{camera.position.set(10.35,6.35,1.9);camera.lookAt(9.1,8.05,.92);}
 localKey.position.set(9.9,7.7,2.4);localKey.target.position.copy(center);renderer.render(scene,camera);
 return renderer.domElement.toDataURL('image/jpeg',.96).split(',')[1];
};
'''


def main():
    out=HERE/'previews/specimen_port_inspection';out.mkdir(exist_ok=True);source=(HERE/'main.js').read_text();errors=[]
    # Retain individual source spring-arm nodes for this deformed-tool preview.
    patched=source.replace("a.id.startsWith('optical_witness_')||", "a.id.startsWith('optical_witness_')||a.id==='tweezers_white'||")
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':1280,'height':720});page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/cooling_concept_v2/main.js',lambda r:r.fulfill(status=200,content_type='application/javascript',body=patched+INSPECTION))
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean',timeout=120000);page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000)
        for index in [0,20,40,60]:
            for close in [False,True]:(out/(str(index)+('_close' if close else '')+'.jpg')).write_bytes(base64.b64decode(page.evaluate('(p)=>inspectSpecimenPort(p.index,p.close)',dict(index=index,close=close))))
        assert not errors;browser.close()
    (out/'preview.json').write_text(json.dumps(dict(scope=__doc__,source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['main.js','runtime_scene.json','previews/specimen_tool_fit.json','previews/specimen_port_refined.json','preview_specimen_port.py']},errors=errors),indent=2)+'\n');print('saved port inspection',flush=True)


if __name__=='__main__':main()
