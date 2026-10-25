import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

const $=id=>document.getElementById(id),root='../../',folder='assets/cooling_lab_v1/',cache=new Map(),parts=new Map();
async function bytes(path){if(cache.has(path))return cache.get(path);const r=await fetch(root+path);if(!r.ok)throw Error('无法读取：'+path);const buffer=await r.arrayBuffer(),sha=[...new Uint8Array(await crypto.subtle.digest('SHA-256',buffer))].map(v=>v.toString(16).padStart(2,'0')).join('');const result={buffer,sha};cache.set(path,result);return result}
async function json(path){return JSON.parse(new TextDecoder().decode((await bytes(path)).buffer))}
async function verify(ref){const r=await bytes(ref.path);if(r.sha!==ref.sha256)throw Error('文件与检查版本不一致：'+ref.path);return r.buffer}
let renderer,scene,camera,controls,light,view='oblique',radius=1,pending=false;
const centre=new THREE.Vector3(),clip=new THREE.Plane(new THREE.Vector3(1,0,0),0);
function render(){if(pending||!renderer)return;pending=true;requestAnimationFrame(()=>{pending=false;const d=camera.position.distanceTo(centre);camera.near=Math.max(.00005,d-radius*1.4);camera.far=d+radius*1.4;camera.updateProjectionMatrix();renderer.render(scene,camera)})}
function fit(){
 const selected=$('tripod-select').value,box=new THREE.Box3();
 if(selected==='joint'){box.min.set(-.09,-.09,1.01);box.max.set(.09,.09,1.16)}else for(const m of parts.values())if(m.visible)box.union(new THREE.Box3().setFromObject(m));
 const size=box.getSize(new THREE.Vector3());box.getCenter(centre);radius=size.length()/2;
 const direction={oblique:[-1,-1,.55],top:[0,-.001,1],side:[-1,0,.001],end:[0,-1,.001]}[view];
 const halfVertical=THREE.MathUtils.degToRad(camera.fov/2),halfHorizontal=Math.atan(Math.tan(halfVertical)*camera.aspect),distance=radius/Math.sin(Math.min(halfVertical,halfHorizontal))*1.1;
 controls.target.copy(centre);camera.position.copy(centre).addScaledVector(new THREE.Vector3(...direction).normalize(),distance);camera.lookAt(centre);controls.update();
 light.position.copy(centre).addScaledVector(new THREE.Vector3(-.6,-.7,1).normalize(),radius*4);light.target.position.copy(centre);light.target.updateMatrixWorld();const s=light.shadow;s.camera.left=s.camera.bottom=-radius*1.2;s.camera.right=s.camera.top=radius*1.2;s.camera.near=radius;s.camera.far=radius*7;s.normalBias=radius*.0002;s.camera.updateProjectionMatrix();
 $('tripod-size').textContent=(selected==='joint'?'局部观察范围：':'当前部件包围尺寸：')+size.toArray().map(v=>(v*1000).toFixed(1)).join(' × ')+' mm';render();
}
function update(){
 const selected=$('tripod-select').value,mast=n=>n.includes('_mast_with_')||n==='slotted_flush_mast_plug',splice=n=>n.startsWith('mast_splice_');
 if(selected==='joint'){clip.normal.set(0,0,-1);clip.constant=1.08}else{clip.normal.set(1,0,0);clip.constant=0}
 const oneLeg=n=>['leg_1','leg_brace_1','foot_plate_and_fork_1'].includes(n)||['upper_leg_1_pivot_','foot_1_pivot_','inner_brace_1_pivot_','outer_brace_1_pivot_'].some(p=>n.startsWith(p));
 for(const [name,m] of parts){m.visible=selected==='all'||(selected==='base'&&!mast(name)&&!splice(name))||(selected==='masts'&&mast(name))||(selected==='upper'&&name.startsWith('upper_leg_clamp_'))||(selected==='lower'&&name.startsWith('lower_brace_clamp_'))||(selected==='leg'&&oneLeg(name))||(selected==='splice'&&splice(name))||(selected==='joint'&&(splice(name)||name.includes('_mast_with_')));m.material.clippingPlanes=$('tripod-section').checked?[clip]:[]}
 fit();
}
try{
 const record=await json(folder+'tripod_assets.json'),checks=await json(folder+'tripod_checks.json'),site=await json(folder+'weather_site_review.json');
 for(const ref of [...record.source_artifacts,...checks.source_artifacts,...site.source_artifacts])await verify(ref);
 if(!checks.passed||record.staged_in_lab||record.installation_qualified||checks.installation_qualified||checks.structural_load_qualified||checks.robot_use_qualified||record.owner_acceptance!==null||checks.owner_acceptance!==null||site.staged_in_lab||site.owner_acceptance!==null)throw Error('候选与检查范围不一致');
 const source=await new GLTFLoader().parseAsync(await verify(record.geometry),root),assembly=new THREE.Group();source.scene.updateMatrixWorld(true);
 source.scene.traverse(o=>{if(!o.isMesh)return;const index=source.parser.associations.get(o)?.nodes,name=source.parser.json.nodes[index]?.name||o.name;const m=new THREE.Mesh(o.geometry.clone().applyMatrix4(o.matrixWorld),o.material.clone());m.name=name;m.material.side=THREE.DoubleSide;m.castShadow=true;m.receiveShadow=true;parts.set(name,m);assembly.add(m)});if(parts.size!==record.geometry.parts)throw Error('模型部件数量不一致');
 renderer=new THREE.WebGLRenderer({antialias:false,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(Math.max(devicePixelRatio,1.5),2));renderer.localClippingEnabled=true;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.toneMapping=THREE.ACESFilmicToneMapping;$('lift-viewport').append(renderer.domElement);
 scene=new THREE.Scene();scene.background=new THREE.Color('#e0e6e5');scene.add(assembly);camera=new THREE.PerspectiveCamera(38,1,.00005,10);camera.up.set(0,0,1);controls=new OrbitControls(camera,renderer.domElement);controls.minDistance=.01;controls.maxDistance=12;controls.addEventListener('change',render);
 const pmrem=new THREE.PMREMGenerator(renderer),room=new RoomEnvironment();scene.environment=pmrem.fromScene(room,.04).texture;scene.environmentIntensity=.3;scene.environmentRotation.x=Math.PI/2;room.dispose();pmrem.dispose();scene.add(new THREE.HemisphereLight(0xf3f6ff,0xb5b2a9,.45));light=new THREE.DirectionalLight(0xfff9ef,2.1);light.castShadow=true;light.shadow.mapSize.set(2048,2048);light.shadow.bias=-.00001;scene.add(light,light.target);
 for(const el of document.querySelectorAll('.lift-controls input,.lift-controls select,.lift-controls button'))el.disabled=false;
 $('tripod-select').addEventListener('change',update);$('tripod-section').addEventListener('change',update);$('tripod-views').addEventListener('click',e=>{const v=e.target.closest('button')?.dataset.view;if(v){view=v;fit()}});
 new ResizeObserver(()=>{renderer.setSize($('lift-viewport').clientWidth,$('lift-viewport').clientHeight);camera.aspect=$('lift-viewport').clientWidth/$('lift-viewport').clientHeight;fit()}).observe($('lift-viewport'));
 $('tripod-status').textContent=parts.size+' 个本体部件 · 未放入库存 · 未验收';$('tripod-findings').textContent=checks.checks.length+' 项检查通过，包含实际导出实体、分离部件、穿插、孔道及错误朝向的反例。拉线和地面尚未纳入本体装配。';
 $('site-plan').src=URL.createObjectURL(new Blob([await verify(site.plan_diagram)],{type:'image/svg+xml'}));$('site-status').textContent=site.checks.length+' 项空间预留检查，结果：'+(site.spatial_reservations_clear?'当前候选几何通过。':'仍有冲突。')+' 地面条件和安装验收仍未完成。';
 update();window.scienceGymTripodInspection=()=>({selected:$('tripod-select').value,visible:[...parts].filter(([,m])=>m.visible).map(([n])=>n),section:$('tripod-section').checked,siteStaged:site.staged_in_lab});document.documentElement.dataset.tripodLoaded='true';
}catch(error){renderer?.dispose();$('lift-viewport').replaceChildren();$('site-plan').removeAttribute('src');$('lift-error').textContent=String(error);$('tripod-status').textContent='版本与检查不匹配，暂不显示。';document.documentElement.dataset.tripodLoaded='error'}
