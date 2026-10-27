"""Inspect the candidate clamp inside the existing complete Cary workstation.

Camera and candidate-part overrides are confined to this capture. The closed
extension hood is hidden as an inspection cutaway, not claimed to be opened.
Sample states are separate; these images do not depict a robot exchange.
"""
import base64
import hashlib
import json
import os
from playwright.sync_api import sync_playwright
from export_audit import BROWSER,HERE
from source_geometry import ROOT

INSPECTOR = '''
let clampPreview;
window.inspectCaryClamp=async ({state,sha})=>{
 renderAt(cary.start+cary.duration*.5);applyState('cary_lid',1);
 const interfaces=await read('assets/cary_5000_v1/interfaces.json');
 for(const n of nodeRest.filter(n=>n.asset==='cary'&&interfaces.extension_cover_parts.includes(n.node.name)))n.node.visible=false;
 if(clampPreview)scene.remove(clampPreview);
 for(const n of nodeRest.filter(n=>n.asset==='dra')){
   if(n.node.name.startsWith('sample_clamp_'))n.node.visible=false;
   if(['large_reference_holder','large_PTFE_reference'].includes(n.node.name))n.node.visible=state==='reference_closed';
 }
 const asset=manifest.assets.find(a=>a.id==='dra');
 const installed=groups.get('dra').matrixWorld.clone().multiply(M(opticalSetup.parts.dra.sphere_housing.matrix)).multiply(M(asset.normalization_matrix));
 clampPreview=await load('assets/cary_internal_dra_2500_v1/revisions/working_clamp/'+state+'.glb',sha);
 clampPreview.applyMatrix4(installed);scene.add(clampPreview);
 const specimen=groups.get('optical_witness_white');specimen.visible=state==='witness_closed';
 if(specimen.visible){
  const pose=installed.clone().multiply(new THREE.Matrix4().makeTranslation(0,-.122001,.084)).multiply(new THREE.Matrix4().makeRotationX(Math.PI/2));
  pose.decompose(specimen.position,specimen.quaternion,specimen.scale);
 }
 const port=V(opticalSetup.ports.cary_reflectance.position_m);
 camera.position.copy(port).add(V([0,-.25,.17]));camera.lookAt(port.clone().add(V([.012,0,.01])));
 localKey.intensity=3;localKey.position.copy(port).add(V([.05,-.32,.45]));localKey.target.position.copy(port);
 scene.updateMatrixWorld(true);renderer.render(scene,camera);
 return renderer.domElement.toDataURL('image/jpeg',.96).split(',')[1];
};
'''


def main():
    folder=ROOT/'assets/cary_internal_dra_2500_v1/revisions/working_clamp'
    out=folder/'cutaway_previews';out.mkdir(exist_ok=True)
    source=(HERE/'main.js').read_text();errors=[];captures=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=BROWSER,args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':1440,'height':1080});page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('**/cooling_concept_v2/main.js',lambda r:r.fulfill(status=200,content_type='application/javascript',body=source+INSPECTOR))
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean',timeout=120000)
        page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000)
        for state in ['reference_closed','pulled_clear','parked_for_zero','witness_closed']:
            digest=hashlib.sha256((folder/(state+'.glb')).read_bytes()).hexdigest()
            result=page.evaluate('(args)=>inspectCaryClamp(args)',dict(state=state,sha=digest))
            (out/(state+'.jpg')).write_bytes(base64.b64decode(result));captures.append(dict(state=state,geometry_sha256=digest))
        assert not errors,errors
        browser.close()
    (out/'capture.json').write_text(json.dumps(dict(scope=__doc__,captures=captures,errors=errors,source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['main.js','preview_cary_clamp.py','runtime_scene.json','optical_setup.json']}),indent=2)+'\n')
    print('captured',len(captures),flush=True)


if __name__=='__main__':main()
