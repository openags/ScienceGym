"""Inspect the planned ordinary-tool pickup in the full laboratory.

This local episode has declared optical staging initial conditions. It does
not claim that earlier paper steps delivered these objects to the workbench.
"""
import base64,hashlib,json,os
from playwright.sync_api import sync_playwright
from optical_choreography import HERE

INSPECTION='''
window.inspectOpticalPickup=async(which,index,close)=>{
 const data=await read('viewer/cooling_concept_v2/previews/optical_tool_pickup_path.json'),fit=await read('viewer/cooling_concept_v2/previews/specimen_tool_fit.json'),row=data[which][index];renderAt(referenceStore.end+.01);
 const base=M(data.root),position=new THREE.Vector3().setFromMatrixPosition(base),r={...robotAt(referenceStore.end+.01),position,rootZ:position.z,yaw:data.stance.yaw};
 const originalJointPose=jointPose,originalConstrain=constrainHands;jointPose=()=>({...row.q});constrainHands=(_,q)=>q;poseRobot(r);jointPose=originalJointPose;constrainHands=originalConstrain;
 let tool=M(data.tool_rest);if(row.tool_held)tool=base.clone().multiply(handIK.forward(row.q).world.get('right_palm_force_sensor')).multiply(M(fit.tool_T_palm).invert());
 tool.decompose(groups.get('tweezers_white').position,groups.get('tweezers_white').quaternion,groups.get('tweezers_white').scale);
 M(data.tray_matrix).decompose(groups.get('tray_white').position,groups.get('tray_white').quaternion,groups.get('tray_white').scale);
 for(const [kind,matrix]of Object.entries(data.specimen_staging)){const group=groups.get('optical_witness_'+kind);M(matrix).decompose(group.position,group.quaternion,group.scale);}
 scene.updateMatrixWorld(true);const target=new THREE.Vector3().setFromMatrixPosition(tool).add(V([0,0,.04]));
 if(close){camera.position.copy(target).add(V([.25,-.32,.30]));camera.lookAt(target);}
 else{camera.position.copy(position).add(V([1.10,-1.5,1.9]));camera.lookAt(position.clone().add(V([.15,.20,.85])));}
 localKey.position.copy(position).add(V([1,-.2,2.4]));localKey.target.position.copy(target);renderer.render(scene,camera);return renderer.domElement.toDataURL('image/jpeg',.96).split(',')[1];
};
'''


def main():
    out=HERE/'previews/optical_pickup_inspection';out.mkdir(exist_ok=True);source=(HERE/'main.js').read_text();errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':1280,'height':720});page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/cooling_concept_v2/main.js',lambda r:r.fulfill(status=200,content_type='application/javascript',body=source+INSPECTION));page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean',timeout=120000);page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000)
        for which,index in [('entry',1),('contact',0),('contact',40),('contact',81),('contact',122)]:
            for close in [False,True]:
                (out/(f'{which}_{index}'+('_close' if close else '')+'.jpg')).write_bytes(base64.b64decode(page.evaluate('(x)=>inspectOpticalPickup(x.which,x.index,x.close)',dict(which=which,index=index,close=close))))
        assert not errors;browser.close()
    (out/'preview.json').write_text(json.dumps(dict(scope=__doc__,source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['main.js','runtime_scene.json','previews/optical_tool_pickup_path.json','preview_optical_pickup.py']},errors=errors),indent=2)+'\n');print('saved pickup inspection',flush=True)


if __name__=='__main__':main()
