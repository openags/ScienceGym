import base64,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path('/home/amax/data/media/xyl_ps/scigym/ScienceGym');here=root/'viewer/cooling_concept_v2';config=json.loads((here/'optical_delivery_episode.json').read_text());phase=next(s for s in config['segments'] if s['id']=='white_delivery_carry_to_ftir');t=(phase['start']+phase['end'])/2
extra='''
window.lowerCarryPreview=async t=>{
 window.renderAt(t);const frame=window.auditFrame(t),fit=await read('viewer/cooling_concept_v2/previews/optical_delivery_carry.json'),config=await read('viewer/cooling_concept_v2/optical_delivery_episode.json');
 const q={...frame.joints};for(const [n,v]of Object.entries(fit.selected.q))if(n.startsWith('waist')||(n.startsWith('right_')&&/shoulder|elbow|wrist/.test(n)))q[n]=v;
 const root=new THREE.Matrix4().fromArray(frame.groups.g1),position=new THREE.Vector3().setFromMatrixPosition(root),r={position,rootZ:position.z,yaw:Math.atan2(root.elements[1],root.elements[0])},oldJoint=jointPose,oldConstrain=constrainHands;
 jointPose=()=>({...q});constrainHands=(_,v)=>v;try{poseRobot(r)}finally{jointPose=oldJoint;constrainHands=oldConstrain;}
 const tool=root.clone().multiply(handIK.forward(q).world.get('right_palm_force_sensor')).multiply(M(config.tool_T_palm).invert()),holder=tool.clone().multiply(M(config.holder_T_tool).invert());
 for(const[id,m]of [['tweezers_white',tool],['optical_witness_white',holder]])m.decompose(groups.get(id).position,groups.get(id).quaternion,groups.get(id).scale);
 scene.updateMatrixWorld(true);renderer.render(scene,camera);return renderer.domElement.toDataURL('image/jpeg',.96).split(',')[1];
};
'''
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'});page=b.new_page(viewport={'width':1280,'height':720});page.route('**/cooling_concept_v2/main.js',lambda r:r.fulfill(status=200,content_type='application/javascript',body=(here/'main.js').read_text()+extra));page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean&episode=ftir_delivery',timeout=120000);page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000);encoded=page.evaluate('(t)=>lowerCarryPreview(t)',t);(here/'previews/optical_delivery_lower_carry_candidate.jpg').write_bytes(base64.b64decode(encoded));b.close();print('saved lower carry candidate',flush=True)
