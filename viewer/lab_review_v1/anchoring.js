import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
const $=id=>document.getElementById(id),root='../../',folder='assets/cooling_lab_v1/',cache=new Map(),parts=new Map();
async function bytes(path){if(cache.has(path))return cache.get(path);const r=await fetch(root+path);if(!r.ok)throw Error('无法读取：'+path);const buffer=await r.arrayBuffer(),sha=[...new Uint8Array(await crypto.subtle.digest('SHA-256',buffer))].map(v=>v.toString(16).padStart(2,'0')).join('');const result={buffer,sha};cache.set(path,result);return result}
async function json(path){return JSON.parse(new TextDecoder().decode((await bytes(path)).buffer))}
async function verify(ref){const r=await bytes(ref.path);if(r.sha!==ref.sha256)throw Error('文件与检查版本不一致：'+ref.path);return r.buffer}
let renderer,scene,camera,controls,light,view='oblique',radius=1,pending=false;const centre=new THREE.Vector3();
function render(){if(pending||!renderer)return;pending=true;requestAnimationFrame(()=>{pending=false;const d=camera.position.distanceTo(centre);camera.near=Math.max(.00005,d-radius*1.4);camera.far=d+radius*1.4;camera.updateProjectionMatrix();renderer.render(scene,camera)})}
function fit(){
 const box=new THREE.Box3();for(const m of parts.values())if(m.visible)box.union(new THREE.Box3().setFromObject(m));const size=box.getSize(new THREE.Vector3());box.getCenter(centre);radius=size.length()/2;
 const direction={oblique:[-1,-1,1],top:[0,-.001,1],side:[-1,0,.001],end:$('anchoring-select').value==='ground_clamp'?[1,.2,.3]:[0,1,.25]}[view],halfVertical=THREE.MathUtils.degToRad(camera.fov/2),halfHorizontal=Math.atan(Math.tan(halfVertical)*camera.aspect),distance=radius/Math.sin(Math.min(halfVertical,halfHorizontal))*1.1;
 controls.target.copy(centre);camera.position.copy(centre).addScaledVector(new THREE.Vector3(...direction).normalize(),distance);camera.lookAt(centre);controls.update();
 light.position.copy(centre).addScaledVector(new THREE.Vector3(-.6,-.7,1).normalize(),radius*4);light.target.position.copy(centre);light.target.updateMatrixWorld();const s=light.shadow;s.camera.left=s.camera.bottom=-radius*1.2;s.camera.right=s.camera.top=radius*1.2;s.camera.near=radius;s.camera.far=radius*7;s.normalBias=radius*.0002;s.camera.updateProjectionMatrix();$('anchoring-size').textContent='当前部件包围尺寸：'+size.toArray().map(v=>(v*1000).toFixed(1)).join(' × ')+' mm';render();
}
function update(){
 const selected=$('anchoring-select').value;
 const include={all:()=>true,collar:n=>n.startsWith('guy_collar_'),turnbuckle:n=>n.startsWith('turnbuckle_1_'),hook:n=>n==='s_hook_1',clamp:n=>n.startsWith('wire_clamp_1_'),stakes:n=>n.includes('_stake_'),guy_stake:n=>n==='guy_stake_1',foot_stake:n=>n==='foot_stake_1',ground:n=>n.startsWith('ground_'),rod:n=>n==='ground_rod',ground_clamp:n=>n.startsWith('ground_rod_clamp_'),ground_mast:n=>n.startsWith('ground_mast_'),wires:n=>n.startsWith('uncut_')};
 for(const [name,m] of parts)m.visible=include[selected](name);fit();
}
try{
 const record=await json(folder+'weather_anchoring_assets.json'),checks=await json(folder+'weather_anchoring_checks.json');
 for(const ref of [...record.source_artifacts,...checks.source_artifacts])await verify(ref);
 if(!checks.passed||record.staged_in_lab||record.installation_qualified||record.structural_load_qualified||record.electrical_grounding_qualified||checks.installation_qualified||checks.structural_load_qualified||checks.electrical_grounding_qualified||checks.robot_use_qualified||record.owner_acceptance!==null||checks.owner_acceptance!==null)throw Error('候选与检查范围不一致');
 const source=await new GLTFLoader().parseAsync(await verify(record.geometry),root),assembly=new THREE.Group();source.scene.updateMatrixWorld(true);source.scene.traverse(o=>{if(!o.isMesh)return;const index=source.parser.associations.get(o)?.nodes,name=source.parser.json.nodes[index]?.name||o.name,m=new THREE.Mesh(o.geometry.clone().applyMatrix4(o.matrixWorld),o.material.clone());m.name=name;m.castShadow=true;m.receiveShadow=!name.startsWith('uncut_');parts.set(name,m);assembly.add(m)});if(parts.size!==record.geometry.parts)throw Error('模型部件数量不一致');
 renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(Math.max(devicePixelRatio,1.5),2));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.toneMapping=THREE.ACESFilmicToneMapping;$('lift-viewport').append(renderer.domElement);
 scene=new THREE.Scene();scene.background=new THREE.Color('#e0e6e5');scene.add(assembly);camera=new THREE.PerspectiveCamera(38,1,.00005,10);camera.up.set(0,0,1);controls=new OrbitControls(camera,renderer.domElement);controls.minDistance=.01;controls.maxDistance=12;controls.addEventListener('change',render);
 const pmrem=new THREE.PMREMGenerator(renderer),room=new RoomEnvironment();scene.environment=pmrem.fromScene(room,.04).texture;scene.environmentIntensity=.3;scene.environmentRotation.x=Math.PI/2;room.dispose();pmrem.dispose();scene.add(new THREE.HemisphereLight(0xf3f6ff,0xb5b2a9,.45));light=new THREE.DirectionalLight(0xfff9ef,2.1);light.castShadow=true;light.shadow.mapSize.set(2048,2048);light.shadow.bias=-.00001;scene.add(light,light.target);
 for(const el of document.querySelectorAll('.lift-controls select,.lift-controls button'))el.disabled=false;$('anchoring-select').addEventListener('change',update);$('anchoring-views').addEventListener('click',e=>{const v=e.target.closest('button')?.dataset.view;if(v){view=v;fit()}});
 new ResizeObserver(()=>{renderer.setSize($('lift-viewport').clientWidth,$('lift-viewport').clientHeight);camera.aspect=$('lift-viewport').clientWidth/$('lift-viewport').clientHeight;fit()}).observe($('lift-viewport'));
 $('anchoring-status').textContent=parts.size+' 个散件实体 · 未放入库存 · 未验收';$('anchoring-findings').textContent=checks.checks.length+' 项实际几何检查通过，包含封闭实体、穿插、眼环、线夹孔、螺钉凹槽及整卷线长。';update();window.scienceGymAnchoringInspection=()=>({selected:$('anchoring-select').value,visible:[...parts].filter(([,m])=>m.visible).map(([n])=>n),staged:record.staged_in_lab});document.documentElement.dataset.anchoringLoaded='true';
}catch(error){renderer?.dispose();$('lift-viewport').replaceChildren();$('lift-error').textContent=String(error);$('anchoring-status').textContent='版本与检查不匹配，暂不显示。';document.documentElement.dataset.anchoringLoaded='error'}
