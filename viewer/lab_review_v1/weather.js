import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

const $=id=>document.getElementById(id),root='../../',folder='assets/cooling_lab_v1/';
const cache=new Map(),groups=new Map(),details=new Map();
async function bytes(path){
 if(cache.has(path))return cache.get(path);
 const response=await fetch(root+path);if(!response.ok)throw Error('无法读取：'+path);
 const buffer=await response.arrayBuffer(),sha=[...new Uint8Array(await crypto.subtle.digest('SHA-256',buffer))].map(v=>v.toString(16).padStart(2,'0')).join('');
 const value={buffer,sha};cache.set(path,value);return value;
}
async function json(path){return JSON.parse(new TextDecoder().decode((await bytes(path)).buffer))}
async function verify(ref){const value=await bytes(ref.path);if(value.sha!==ref.sha256)throw Error('文件与检查版本不一致：'+ref.path);return value.buffer}

let renderer,scene,camera,controls,keyLight,pending=false,view='oblique',radius=.2;
const centre=new THREE.Vector3(),section=new THREE.Plane(new THREE.Vector3(0,1,0),0);
function render(){
 if(pending||!renderer)return;pending=true;
 requestAnimationFrame(()=>{pending=false;const distance=camera.position.distanceTo(centre);camera.near=Math.max(.00002,distance-radius*1.2);camera.far=distance+radius*1.2;camera.updateProjectionMatrix();renderer.render(scene,camera)});
}
function fit(){
 const box=new THREE.Box3().setFromObject(groups.get($('weather-select').value)),size=box.getSize(new THREE.Vector3());
 box.getCenter(centre);radius=size.length()/2;
 section.constant=['rs3','shield','clearance'].includes($('weather-select').value)?0:-centre.y;
 if(keyLight){
  keyLight.position.copy(centre).addScaledVector(new THREE.Vector3(-.6,-.7,1).normalize(),radius*4);
  keyLight.target.position.copy(centre);keyLight.target.updateMatrixWorld();
  const shadow=keyLight.shadow;shadow.camera.left=shadow.camera.bottom=-radius*1.2;shadow.camera.right=shadow.camera.top=radius*1.2;shadow.camera.near=radius;shadow.camera.far=radius*7;shadow.normalBias=radius*.0002;shadow.camera.updateProjectionMatrix();
 }
 const direction={oblique:[-.55,-1,.8],top:[0,-.001,1],side:[0,-1,.001],end:[-1,-.001,.001]}[view];
 controls.target.copy(centre);camera.position.copy(centre).addScaledVector(new THREE.Vector3(...direction).normalize(),size.length()*1.45/Math.min(camera.aspect,1));camera.lookAt(centre);controls.update();
 $('weather-size').textContent='当前所选部件包围尺寸：'+size.toArray().map(v=>(v*1000).toFixed(2)).join(' × ')+' mm（X / Y / Z）';render();
}
function update(){
 const id=$('weather-select').value;
 for(const [name,g] of groups){g.visible=name===id;g.traverse(o=>{if(o.isMesh)o.material.clippingPlanes=$('weather-section').checked?[section]:[]})}
 $('weather-detail').textContent=details.get(id);fit();
}
function addGroup(assembly,id,label,source,filter,detail){
 const group=new THREE.Group();source.scene.updateMatrixWorld(true);
 source.scene.traverse(o=>{
  if(!o.isMesh)return;
  const index=source.parser.associations.get(o)?.nodes,name=source.parser.json.nodes[index]?.name||o.name;
  if(!filter(name))return;
  const mesh=new THREE.Mesh(o.geometry.clone().applyMatrix4(o.matrixWorld),o.material.clone());mesh.name=name;
  // Back faces are shown only as a viewing aid, not added physical geometry.
  mesh.material.side=THREE.DoubleSide;mesh.castShadow=mesh.material.opacity>=.99;mesh.receiveShadow=true;group.add(mesh);
 });
 if(!group.children.length)throw Error('部件筛选为空：'+id);
 groups.set(id,group);details.set(id,detail);assembly.add(group);$('weather-select').add(new Option(label,id));
}
try{
 const [record,checks]=await Promise.all([json(folder+'weather_assets.json'),json(folder+'weather_asset_checks.json')]);
 for(const ref of [...record.source_artifacts,...checks.source_artifacts])await verify(ref);
 if(!checks.passed||record.staged_in_lab||record.weather_station_complete||record.owner_acceptance!==null||checks.assembly_qualified||checks.robot_use_qualified||checks.owner_acceptance!==null)throw Error('当前部件检查范围不一致');
 const loaded=new Map();for(const item of record.items)loaded.set(item.id,await new GLTFLoader().parseAsync(await verify(item.geometry),root));
 const sample=await new GLTFLoader().parseAsync(await verify(checks.inspection_sample),root),assembly=new THREE.Group();
 const shield=loaded.get('onset_rs3'),sensor=loaded.get('onset_sthb_m002');
 const core=n=>!n.startsWith('loose_')&&!n.startsWith('optional_')&&!n.startsWith('band_')&&!n.startsWith('mast_');
 addGroup(assembly,'rs3','RS3 防辐射罩与套件',shield,()=>true,'防辐射罩、支架、两只旋紧螺母、六根扎带、两枚选装墙面螺钉和松置抱箍。局部五金尺寸为推断。');
 addGroup(assembly,'shield','仅看防辐射罩与支架',shield,core,'可剖开查看叶片、内孔、支撑杆和分离垫套。两处螺纹采用名义包络，未建牙型。');
 addGroup(assembly,'sensor','完整探头与连续线缆',sensor,()=>true,'连续 2.0 m 探头线段与 0.5 m 网络线段；适配器和接头均为可见实体。收纳姿态为手工设定。');
 addGroup(assembly,'head','探头与膜帽近看',sensor,n=>['probe_receptacle','rh_membrane_cap','sensor_board_envelope','probe_strain_relief_candidate'].includes(n),'直径 10 mm、头部长 35 mm；膜帽与探头座分离建模，传感器内部仅为尺寸假设。');
 addGroup(assembly,'plug','RJ12 接头近看',sensor,n=>n.startsWith('plug_')||n.startsWith('modular_'),'按 Cinch 圆线插头的尺寸选择接口包络，含六个触点、开口线腔与可见锁扣。尚无 Onset 原配型号与电气针脚证据。');
 addGroup(assembly,'clearance','探头置于罩内：净空示例',sample,()=>true,'仅检查刚性头部与罩体净空：探头顶部距第一层闭合顶盖约 15 mm。没有计入安装线缆、扎带固定或传感器性能。');
 renderer=new THREE.WebGLRenderer({antialias:false,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(Math.max(devicePixelRatio,1.5),2));renderer.localClippingEnabled=true;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1;$('lift-viewport').append(renderer.domElement);
 scene=new THREE.Scene();scene.background=new THREE.Color('#e0e6e5');scene.add(assembly);
 camera=new THREE.PerspectiveCamera(38,1,.00002,3);camera.up.set(0,0,1);controls=new OrbitControls(camera,renderer.domElement);controls.minDistance=.006;controls.maxDistance=2;controls.addEventListener('change',render);
 const pmrem=new THREE.PMREMGenerator(renderer),room=new RoomEnvironment();scene.environment=pmrem.fromScene(room,.04).texture;scene.environmentIntensity=.3;scene.environmentRotation.x=Math.PI/2;room.dispose();pmrem.dispose();scene.add(new THREE.HemisphereLight(0xf3f6ff,0xb5b2a9,.45));
 keyLight=new THREE.DirectionalLight(0xfff9ef,2.1);keyLight.castShadow=true;keyLight.shadow.mapSize.set(2048,2048);keyLight.shadow.bias=-.00001;scene.add(keyLight,keyLight.target);
 for(const element of document.querySelectorAll('.lift-controls input,.lift-controls select,.lift-controls button'))element.disabled=false;
 $('weather-select').addEventListener('change',update);$('weather-section').addEventListener('change',update);
 $('weather-views').addEventListener('click',event=>{const next=event.target.closest('button')?.dataset.view;if(next){view=next;fit()}});
 new ResizeObserver(()=>{renderer.setSize($('lift-viewport').clientWidth,$('lift-viewport').clientHeight);camera.aspect=$('lift-viewport').clientWidth/$('lift-viewport').clientHeight;fit()}).observe($('lift-viewport'));
 $('weather-status').textContent='独立部件候选 · 尚未计入主场景库存 · 未验收';
 $('weather-findings').textContent=checks.checks.length+' 项检查通过，覆盖闭合实体、厂家尺寸、实际线长、非相邻线段间隙及罩内头部净空。两处杆／螺母的名义螺纹包络重叠已单独记录。';
 for(const row of checks.cable_clearances){const tr=$('weather-cables').tBodies[0].insertRow();for(const text of [row.id==='probe_lead'?'探头线段':'网络线段',row.actual_length_m.toFixed(6)+' m',(row.conservative_nonlocal_surface_gap_m*1000).toFixed(3)+' mm'])tr.insertCell().textContent=text}
 update();window.scienceGymWeatherInspection=()=>({selected:$('weather-select').value,section:$('weather-section').checked,visible:[...groups].filter(([,g])=>g.visible).map(([id,g])=>({id,parts:g.children.length}))});document.documentElement.dataset.weatherLoaded='true';
}catch(error){renderer?.dispose();$('lift-viewport').replaceChildren();$('lift-error').textContent=String(error);$('weather-status').textContent='来源或几何检查不匹配，暂不显示模型。';document.documentElement.dataset.weatherLoaded='error'}
