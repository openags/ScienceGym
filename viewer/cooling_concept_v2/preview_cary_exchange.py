"""Inspect planned bimanual approaches/extraction in the existing laboratory.

Snapshots reflect the selected plan's initial condition. They do not depict
tool pickup, reference storage, a continuous composed episode or dynamics.
"""
import argparse
import base64
import hashlib
import json
import os
import numpy as np
import trimesh
from playwright.sync_api import sync_playwright
from cary_clamp_scene import CaryClampScene,object_pose
from export_audit import HERE,BROWSER
from long_forceps import meshes
from source_geometry import ROOT,fk
from render_capture_checks import save_checked_jpeg

INSPECTOR='''
let exchangePreview;
window.inspectExchange=async({row,path,sha,close})=>{
 window.renderAt(concept.duration);
 for(const item of nodeRest.filter(n=>n.asset==='dra')){
  if(item.node.name.startsWith('sample_clamp_')||['large_reference_holder','large_PTFE_reference'].includes(item.node.name))item.node.visible=false;
 }
 if(exchangePreview)scene.remove(exchangePreview);
 exchangePreview=await load(path,sha);scene.add(exchangePreview);
 const root=row.root,position=V([root[0][3],root[1][3],root[2][3]]);
 const r={position,rootZ:position.z,yaw:Math.atan2(root[1][0],root[0][0])};
 const oldJoint=jointPose,oldConstrain=constrainHands;
 jointPose=()=>({...row.q});constrainHands=(_,q)=>q;
 try{poseRobot(r)}finally{jointPose=oldJoint;constrainHands=oldConstrain;}
 const port=V(opticalSetup.ports.cary_reflectance.position_m);
 if(close){camera.position.copy(port).add(V([-.08,-.30,.38]));camera.lookAt(port.clone().add(V([row.reference_delta[0][3],row.reference_delta[1][3],row.reference_delta[2][3]])));}
 else{camera.position.copy(position).add(V([1.05,-1.55,1.95]));camera.lookAt(position.clone().add(V([.05,.35,.85])));}
 localKey.position.copy(port).add(V([.4,-.5,.8]));localKey.target.position.copy(port);
 scene.updateMatrixWorld(true);renderer.render(scene,camera);
 if(renderer.getContext().isContextLost())throw Error('WebGL context lost during exchange inspection');
 return renderer.domElement.toDataURL('image/jpeg',.96).split(',')[1];
};
'''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plan',default='previews/cary_bimanual_exchange_04/plan.json');args=parser.parse_args()
    plan=json.loads((HERE/args.plan).read_text());candidate=plan['candidates'][0]
    out=(HERE/args.plan).parent/'inspection';out.mkdir(exist_ok=True)
    scene=CaryClampScene(local_only=True);captures=[]
    rows=candidate['rows'];selected=[('supported_start',rows[0])]
    for stage in ['left_close','right_lower','retract_clamp','park_clamp','withdraw_reference']:
        matches=[r for r in rows if r['stage']==stage]
        if matches:selected.append((stage,matches[-1]))
    for name,row in selected:
        scene.set_clamp(row['gap_m'],row['angle_rad']);scene.set_reference(row['reference_delta'])
        source=trimesh.Scene()
        for part,mesh in scene.clamp_meshes.items():
            source.add_geometry(mesh,node_name='clamp::'+part,transform=scene.clamp_poses[part])
        for part,mesh in scene.reference_meshes.items():
            source.add_geometry(mesh,node_name='reference::'+part,transform=object_pose(scene.reference._objs['dra::'+part]))
        world=np.array(row['root'])@fk(row['q'])['right_palm_force_sensor']
        assert np.max(abs(world-np.array(row['right_palm'])))<1e-8
        tool=world@np.linalg.inv(np.array(candidate['tool_T_palm']))
        for part,mesh in meshes(row.get('closure',1.)).items():source.add_geometry(mesh,node_name='forceps::'+part,transform=tool)
        if plan.get('staging'):
            staging=json.loads((HERE/plan['staging']).read_text());tray=trimesh.load(ROOT/staging['tray_geometry'],force='scene',process=False)
            pose=np.eye(4);pose[:3,3]=staging['tray_position_m']
            for part in tray.graph.nodes_geometry:
                local,key=tray.graph[part];source.add_geometry(tray.geometry[key],node_name='cary_tool_tray::'+part,transform=pose@local)
        path=out/(name+'.glb');path.write_bytes(source.export(file_type='glb'))
        captures.append(dict(name=name,row=row,path=str(path.relative_to(ROOT)),sha=hashlib.sha256(path.read_bytes()).hexdigest()))
    errors=[];console=[];quality={};source=(HERE/'main.js').read_text()
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=BROWSER,args=['--no-sandbox','--disable-dev-shm-usage',
            '--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],
            env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':1280,'height':960});page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda message:console.append(dict(type=message.type,text=message.text)) if message.type in ['warning','error'] else None)
        page.route('**/cooling_concept_v2/main.js',lambda route:route.fulfill(status=200,content_type='application/javascript',body=source+INSPECTOR))
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?episode=cary_access&clean',timeout=120000)
        page.wait_for_function('document.documentElement.dataset.ready==="true" && window.concept?.caryEpisode',timeout=120000)
        for capture in captures:
            for close in [False,True]:
                encoded=page.evaluate('(x)=>inspectExchange(x)',{**capture,'close':close})
                path=out/(capture['name']+('_close' if close else '_wide')+'.jpg');quality[path.name]=save_checked_jpeg(encoded,path)
        browser.close()
    assert not errors,errors
    inputs=[args.plan,'main.js','cary_episode.js','cary_access_episode.json','cary_clamp_scene.py','cary_clamp.py','long_forceps.py','preview_cary_exchange.py','render_capture_checks.py']
    if plan.get('staging'):inputs.append(plan['staging'])
    report=dict(scope=__doc__,captures=captures,errors=errors,console=console,image_quality=quality,
        device_selection={n:os.environ[n] for n in ['DRI_PRIME','MESA_VK_DEVICE_SELECT_FORCE_DEFAULT_DEVICE',
            'VK_LAYER_PATH','VK_INSTANCE_LAYERS','ENABLE_DEVICE_CHOOSER_LAYER','VULKAN_DEVICE_INDEX'] if n in os.environ},
        source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in inputs})
    (out/'capture.json').write_text(json.dumps(report,indent=2)+'\n');print('captured',len(captures)*2,'views',flush=True)


if __name__=='__main__':main()
