import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
const $=id=>document.getElementById(id),root='../../',folder='assets/cooling_lab_v1/',cache=new Map();
async function bytes(path){if(cache.has(path))return cache.get(path);const r=await fetch(root+path);if(!r.ok)throw Error('缺少本机资源：'+path);const buffer=await r.arrayBuffer(),sha=[...new Uint8Array(await crypto.subtle.digest('SHA-256',buffer))].map(v=>v.toString(16).padStart(2,'0')).join('');const out={buffer,sha};cache.set(path,out);return out}
async function json(path){return JSON.parse(new TextDecoder().decode((await bytes(path)).buffer))}
async function verify(ref){const data=await bytes(ref.path);if(data.sha!==ref.sha256)throw Error('文件版本与检查记录不一致：'+ref.path);return data.buffer}
let renderer,scene,camera,controls,parts=new Map(),pending=false,view='oblique';
const hardware=n=>/screw|tnut|_nut$|washer|pinch/.test(n);
function render(){if(pending||!renderer)return;pending=true;requestAnimationFrame(()=>{pending=false;renderer.render(scene,camera)})}
function fit(){const box=new THREE.Box3();for(const m of parts.values())if(m.visible)box.expandByObject(m);const target=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3()).length();const direction={oblique:[1,-1.4,.9],front:[0,-1,.01],end:[0,-1,0],top:[0,-.001,1],bottom:[0,-.001,-1]}[view];const section=$('frame-group').value==='rail'&&view==='end';if(section)target.y=box.min.y;controls.target.copy(target);camera.position.copy(target).addScaledVector(new THREE.Vector3(...direction).normalize(),(section?.07:Math.max(size*1.65,.12))/Math.min(camera.aspect,1));camera.lookAt(target);controls.update();document.documentElement.dataset.frameView=view;render()}
function update(){const group=$('frame-group').value;let count=0;for(const [name,m] of parts){const n=name.replace('COOLER_WHITE__','');let show=group==='all'||group==='rail'&&n==='frame_rail_right'||group==='base'&&/acrylic|mylar_base|frame_rail|frame_bridge|bumper/.test(n)||group==='uprights'&&/clamp|tube|pinch|frame_track/.test(n)||group==='reflector'&&/reflector_track|solar_reflector|frame_carriage|frame_track|upper_clamp|upper_pinch/.test(n);m.visible=show&&($('frame-hardware').checked||!hardware(n));if(m.visible)count++}$('frame-selection').textContent='显示 '+count+' 个实际零件。隐藏仅用于检查，不代表已经拆装。';document.documentElement.dataset.frameGroup=group;fit()}
try{
 const [record,checks]=await Promise.all([json(folder+'apparatus_stock_reconciliation.json'),json(folder+'apparatus_frame_checks.json')]);
 for(const ref of [...record.source_artifacts,...checks.source_artifacts])await verify(ref);
 if(!checks.passed||checks.physical_installation_qualified||checks.owner_acceptance!==null)throw Error('静态候选状态不一致');
 const white=record.items.find(i=>i.id==='cooler_white'),gltf=await new GLTFLoader().parseAsync(await verify(white.frame_inspection),root),assembly=new THREE.Group();gltf.scene.updateMatrixWorld(true);
 gltf.scene.traverse(o=>{if(!o.isMesh)return;const node=gltf.parser.associations.get(o)?.nodes,name=gltf.parser.json.nodes[node]?.name||o.name;const m=new THREE.Mesh(o.geometry.clone().applyMatrix4(o.matrixWorld),o.material.clone());m.name=name;parts.set(name,m);assembly.add(m)});
 if(parts.size!==white.frame_inspection.parts||white.frame.review_parts.some(n=>!parts.has(n)))throw Error('框架零件清单与模型不一致');
 renderer=new THREE.WebGLRenderer({antialias:false,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(Math.max(devicePixelRatio,1.5),2));renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.1;$('lift-viewport').append(renderer.domElement);
 scene=new THREE.Scene();scene.background=new THREE.Color('#d6e2e5');scene.add(assembly);camera=new THREE.PerspectiveCamera(38,1,.0002,8);camera.up.set(0,0,1);controls=new OrbitControls(camera,renderer.domElement);controls.minDistance=.015;controls.maxDistance=3;controls.addEventListener('change',render);
 const pmrem=new THREE.PMREMGenerator(renderer),room=new RoomEnvironment();scene.environment=pmrem.fromScene(room,.04).texture;scene.environmentIntensity=.45;scene.environmentRotation.x=Math.PI/2;room.dispose();pmrem.dispose();scene.add(new THREE.HemisphereLight(0xf3f6ff,0xa4afa6,1));const light=new THREE.DirectionalLight(0xfff6e8,2.5);light.position.set(.3,-.5,.6);scene.add(light);
 for(const e of document.querySelectorAll('.lift-controls input,.lift-controls select,.lift-controls button'))e.disabled=false;
 $('frame-group').addEventListener('change',update);$('frame-hardware').addEventListener('change',update);$('frame-views').addEventListener('click',e=>{const v=e.target.closest('button')?.dataset.view;if(v){view=v;fit()}});
 new ResizeObserver(()=>{const w=$('lift-viewport').clientWidth,h=$('lift-viewport').clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();fit()}).observe($('lift-viewport'));
 $('frame-status').textContent='实际框架与连接几何 · 静态候选，尚未验收';
 $('frame-measurements').textContent='型材截面：'+checks.section.area_mm2.toFixed(3)+' mm²；厂家名义值 159.1 mm²。截面积接近不等于局部形状、强度或公差合格。';
 $('frame-finding').textContent=checks.checks.length+' 项静态检查通过。名义接触面、槽口、孔和独立连接件有实际几何；接触面与螺纹包络相交另行记录。';
 const remaining=['反射片夹板的锁紧、松开和完整移动范围尚未验证。','夹块弹性、摩擦、螺纹预紧和管壁承压尚未验证。','底脚黏结、压缩、户外耐候与整体承载尚未验证。','框架库存单独核对；加工、工具与重复运行消耗仍未合格。','薄膜、罩体、接线端子和线缆安装仍有缺口。'];
 $('frame-remaining').replaceChildren(...remaining.map(t=>{const li=document.createElement('li');li.textContent=t;return li}));
 update();document.documentElement.dataset.frameLoaded='true';window.scienceGymFrameInspection=()=>({visible:[...parts].filter(([,m])=>m.visible).map(([n])=>n),group:$('frame-group').value,hardware:$('frame-hardware').checked});
}catch(error){renderer?.dispose();$('lift-viewport').replaceChildren();$('lift-error').textContent=String(error);$('frame-status').textContent='资源未通过版本检查，暂不显示模型。';document.documentElement.dataset.frameLoaded='error'}
