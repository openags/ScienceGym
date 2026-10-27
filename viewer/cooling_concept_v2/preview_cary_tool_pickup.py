"""Inspect the exact planned forceps pickup in the established full laboratory.

These are development snapshots of the candidate and explicit extra ordinary
equipment, not a continuous delivered episode or a physical execution record.
"""
import argparse
import base64
import hashlib
import json
import os
import numpy as np
import trimesh
from playwright.sync_api import sync_playwright
from export_audit import HERE,BROWSER
from long_forceps import meshes
from source_geometry import ROOT,fk
from render_capture_checks import save_checked_jpeg


INSPECTOR='''
let pickupPreview;
window.inspectPickup=async({row,path,sha,tool,close})=>{
 window.renderAt(concept.duration);
 if(pickupPreview)scene.remove(pickupPreview);
 pickupPreview=await load(path,sha);scene.add(pickupPreview);
 const root=row.root,position=V([root[0][3],root[1][3],root[2][3]]);
 const r={position,rootZ:position.z,yaw:Math.atan2(root[1][0],root[0][0])};
 const oldJoint=jointPose,oldConstrain=constrainHands;
 jointPose=()=>({...row.q});constrainHands=(_,q)=>q;
 try{poseRobot(r)}finally{jointPose=oldJoint;constrainHands=oldConstrain;}
 const point=V(tool);
 if(close){camera.position.copy(point).add(V([.15,.30,.15]));camera.lookAt(point.clone().add(V([0,0,.03])));}
 else{camera.position.copy(position).add(V([1.05,-1.55,1.95]));camera.lookAt(position.clone().add(V([.05,.35,.85])));}
 localKey.position.copy(point).add(V([.4,-.5,.8]));localKey.target.position.copy(point);
 scene.updateMatrixWorld(true);renderer.render(scene,camera);
 if(renderer.getContext().isContextLost())throw Error('WebGL context lost during pickup inspection');
 return renderer.domElement.toDataURL('image/jpeg',.96).split(',')[1];
};
'''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plan',default='previews/cary_tool_pickup_02/plan.json');args=parser.parse_args()
    plan=json.loads((HERE/args.plan).read_text());assert plan['passed'];candidate=plan['candidates'][0]
    staging=json.loads((HERE/plan['staging']).read_text());tray=trimesh.load(ROOT/staging['tray_geometry'],force='scene',process=False)
    tray_pose=np.eye(4);tray_pose[:3,3]=staging['tray_position_m']
    out=(HERE/args.plan).parent/'inspection';out.mkdir(exist_ok=True)
    selected=[('rest',candidate['entry'][0]),('pregrasp',candidate['rows'][0])]
    selected += [(stage,[r for r in candidate['rows'] if r['stage']==stage][-1]) for stage in ['close_hand','lift_tool']]
    captures=[]
    for name,row in selected:
        source=trimesh.Scene();pose=np.array(row.get('tool_matrix',candidate['tool_rest']))
        if row['tool_held']:
            actual=np.array(row['root'])@fk(row['q'])['right_palm_force_sensor']@np.linalg.inv(candidate['tool_T_palm'])
            assert np.max(abs(actual-pose))<1e-8
        for part,mesh in meshes(row['closure']).items():source.add_geometry(mesh,node_name='long_forceps::'+part,transform=pose)
        for part in tray.graph.nodes_geometry:
            local,key=tray.graph[part];source.add_geometry(tray.geometry[key],node_name='cary_tool_tray::'+part,transform=tray_pose@local)
        path=out/(name+'.glb');path.write_bytes(source.export(file_type='glb'))
        captures.append(dict(name=name,row=row,path=str(path.relative_to(ROOT)),sha=hashlib.sha256(path.read_bytes()).hexdigest(),tool=pose[:3,3].tolist()))
    errors=[];source=(HERE/'main.js').read_text()
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=BROWSER,args=['--no-sandbox','--disable-dev-shm-usage',
            '--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],
            env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':1280,'height':960});page.on('pageerror',lambda error:errors.append(str(error)))
        page.route('**/cooling_concept_v2/main.js',lambda route:route.fulfill(status=200,content_type='application/javascript',body=source+INSPECTOR))
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?episode=cary_access&clean',timeout=120000)
        page.wait_for_function('document.documentElement.dataset.ready==="true" && window.concept?.caryEpisode',timeout=120000)
        for capture in captures:
            for close in [False,True]:
                encoded=page.evaluate('(x)=>inspectPickup(x)',{**capture,'close':close})
                save_checked_jpeg(encoded,out/(capture['name']+('_close' if close else '_wide')+'.jpg'))
        browser.close()
    assert not errors,errors
    report=dict(scope=__doc__,captures=captures,errors=errors,source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in
        [args.plan,plan['staging'],'main.js','cary_episode.js','cary_access_episode.json','long_forceps.py','preview_cary_tool_pickup.py','render_capture_checks.py']})
    (out/'capture.json').write_text(json.dumps(report,indent=2)+'\n');print('captured',len(captures)*2,'views',flush=True)


if __name__=='__main__':main()
