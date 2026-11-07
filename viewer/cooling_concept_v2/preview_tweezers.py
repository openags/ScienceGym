"""Inspect the actual source-hand and tweezer meshes used by the local fit."""
import base64,json,os
from pathlib import Path
import numpy as np
from playwright.sync_api import sync_playwright
from source_geometry import ROOT,robot_meshes,fk
from tweezers_geometry import meshes
import trimesh

HERE=Path(__file__).resolve().parent


def main():
    source=json.loads((HERE/'previews/tweezers_closure.json').read_text());hand=robot_meshes('right');palm=np.array(source['palm_matrix']);states=[]
    specimen=json.loads((HERE/'previews/specimen_tool_fit.json').read_text())
    selected=[source['rows'][0],source['rows'][-1],dict(q=specimen['carrier_grip_q'],closure=specimen['carrier_grip_closure'])]
    for index,row in enumerate(selected):
        world=fk(row['q']);base=palm@np.linalg.inv(world['right_palm_force_sensor']);parts=[]
        for name,mesh in {**hand,**meshes(row['closure'])}.items():
            transform=base@world[name] if name in hand else np.eye(4)
            vertices=mesh.vertices@transform[:3,:3].T+transform[:3,3]
            parts.append(dict(name=name,vertices=vertices.reshape(-1).tolist(),indices=mesh.faces.reshape(-1).tolist(),color='#747b82' if name in hand else '#e8e7d7'))
        if index==2:
            carrier=trimesh.load(ROOT/'assets/cooling_optical_specimens_v1/witness_white.glb',force='scene',process=False)
            for name in carrier.graph.nodes_geometry:
                local,key=carrier.graph[name];transform=np.linalg.inv(np.array(specimen['holder_T_tool']))@local;mesh=carrier.geometry[key]
                vertices=mesh.vertices@transform[:3,:3].T+transform[:3,3]
                parts.append(dict(name=name,vertices=vertices.reshape(-1).tolist(),indices=mesh.faces.reshape(-1).tolist(),color='#b66c39' if name=='copper_witness' else '#dddccf' if name.startswith('paint') else '#5e6870'))
        states.append(parts)
    script='''import * as T from 'three';
const renderer=new T.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setSize(1280,720);renderer.outputColorSpace=T.SRGBColorSpace;document.body.innerHTML='';document.body.append(renderer.domElement);
const scene=new T.Scene();scene.background=new T.Color('#d5dce0');const camera=new T.PerspectiveCamera(40,1280/720,.001,10);camera.up.set(0,0,1);scene.add(new T.HemisphereLight(0xffffff,0x657484,2));const light=new T.DirectionalLight(0xffffff,3);light.position.set(-.3,-.2,.4);scene.add(light);let group;
window.inspectTool=(parts,angle)=>{if(group)scene.remove(group);group=new T.Group();scene.add(group);for(const p of parts){const g=new T.BufferGeometry();g.setAttribute('position',new T.Float32BufferAttribute(p.vertices,3));g.setIndex(p.indices);g.computeVertexNormals();const m=new T.Mesh(g,new T.MeshStandardMaterial({color:p.color,roughness:.6}));group.add(m);}camera.position.set(...(angle===0?[-.18,-.25,.17]:[-.13,.25,.15]));camera.lookAt(.025,.02,.01);renderer.render(scene,camera);return renderer.domElement.toDataURL('image/jpeg',.96).split(',')[1];};window.ready=true;'''
    out=HERE/'previews/tweezers_fit';out.mkdir(exist_ok=True)
    geometry=out/'geometry.json';geometry.write_text(json.dumps(states,separators=(',',':')))
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':1280,'height':720});page.route('**/cooling_concept_v2/main.js',lambda r:r.fulfill(status=200,content_type='application/javascript',body=script));page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean');page.wait_for_function('window.ready===true')
        page.evaluate("async()=>{window.previewStates=await(await fetch('./previews/tweezers_fit/geometry.json')).json()}")
        for i in range(len(states)):
            for angle in [0,1]:(out/f'closure_{i}_view_{angle}.jpg').write_bytes(base64.b64decode(page.evaluate('(x)=>inspectTool(previewStates[x.i],x.angle)',dict(i=i,angle=angle))))
        browser.close()
    geometry.unlink()
    (out/'preview.json').write_text(json.dumps(dict(states=['open_tool','maximum_selected_closure','carrier_wall_grip'],source_files=['previews/tweezers_closure.json','previews/specimen_tool_fit.json'],scope=__doc__),indent=2)+'\n')
    print('saved',len(states)*2,flush=True)


if __name__=='__main__':main()
