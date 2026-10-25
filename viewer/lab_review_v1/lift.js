import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

const $=id=>document.getElementById(id),root='../../',folder='assets/thorlabs_l200_v1/';
const cache=new Map();
async function bytes(path){
 if(cache.has(path))return cache.get(path);
 const response=await fetch(root+path);
 if(!response.ok)throw Error(path.includes('/geometry/')||path.includes('/cache/')?'本机缺少厂家资源，请按下方命令下载并生成：'+path:'无法读取检查文件：'+path);
 const buffer=await response.arrayBuffer(),sha=[...new Uint8Array(await crypto.subtle.digest('SHA-256',buffer))].map(v=>v.toString(16).padStart(2,'0')).join('');
 const record={buffer,sha};cache.set(path,record);return record;
}
async function json(path){return JSON.parse(new TextDecoder().decode((await bytes(path)).buffer))}
async function verify(ref){const data=await bytes(ref.path);if(data.sha!==ref.sha256)throw Error('文件版本与检查记录不一致：'+ref.path);return data.buffer}
const names={all:'全部',upper_plate:'上板',lower_plate:'下板',pantograph_links:'16 根连杆',adjuster:'内六角调节螺杆',bearing_blocks:'4 个横向支承块',pins_and_hardware:'销、滚珠及其他紧固件'};
let renderer,scene,camera,controls,model,report,assembly,markers,parts=new Map(),view='oblique',pending=false;
function render(){if(pending||!renderer)return;pending=true;requestAnimationFrame(()=>{pending=false;renderer.render(scene,camera)})}
function setView(next){
 view=next;const exploded=Number($('lift-explode').value)/1000;
 const target=new THREE.Vector3(0,0,.0107+exploded/3),direction={oblique:[1,-1.4,.9],side:[0,-1,.04],drive:[1,0,.04],top:[0,-.001,1],bottom:[0,-.001,-1]}[next];
 controls.target.copy(target);camera.position.copy(target).addScaledVector(new THREE.Vector3(...direction).normalize(),.22/Math.min(camera.aspect,1));
 camera.lookAt(target);controls.update();document.documentElement.dataset.liftView=view;render();
}
function update(){
 const selected=$('lift-group').value,isolated=$('lift-isolate').checked,offset=Number($('lift-explode').value)/1000;
 let shown=0;
 for(const record of model.parts){const mesh=parts.get(record.id),match=selected==='all'||record.display_group===selected;
  mesh.visible=!isolated||match;mesh.position.z=record.display_group==='upper_plate'?offset:0;
  mesh.material.emissive.set(selected!=='all'&&match?'#193638':'#000000');if(mesh.visible)shown++;
 }
 markers.visible=$('lift-holes').checked&&(!isolated||selected==='all'||selected==='upper_plate');markers.position.z=offset;
 $('lift-offset').textContent=$('lift-explode').value+' mm';
 $('lift-selection').textContent=(selected==='all'?'全部 86 个源实体':names[selected]+' · '+model.inspection_groups[selected].length+' 个源实体')+'；当前可见 '+shown+' 个。';
 $('lift-status').textContent=offset?'上板移开 '+(offset*1000).toFixed(0)+' mm 的静态拆解检查；不是实际升降姿态。':'厂家 STEP 的收拢姿态 · 底面 Z=0 · 未安装验收';
 document.documentElement.dataset.liftGroup=selected;document.documentElement.dataset.liftVisible=String(shown);document.documentElement.dataset.liftOffset=String(offset);render();
}
try{
 [model,report]=await Promise.all([json(folder+'model.json'),json(folder+'checks.json')]);
 const source=await json(folder+'sources.json');
 for(const ref of [...model.source_artifacts,...report.source_artifacts])await verify(ref);
 if(!report.passed||model.accepted||model.physical_installation_qualified||model.collision_or_dynamics_qualified)throw Error('候选检查状态不一致');
 const gltf=await new GLTFLoader().parseAsync(await verify(model.geometry),root);
 assembly=new THREE.Group();
 gltf.scene.updateMatrixWorld(true);
 gltf.scene.traverse(o=>{
  if(!o.isMesh)return;
  const node=gltf.parser.associations.get(o)?.nodes,name=gltf.parser.json.nodes[node]?.name||o.name;
  const mesh=new THREE.Mesh(o.geometry.clone().applyMatrix4(o.matrixWorld),o.material.clone());mesh.name=name;
  if(!mesh.geometry.attributes.normal)mesh.geometry.computeVertexNormals();parts.set(name,mesh);assembly.add(mesh);
 });
 if(parts.size!==86||model.parts.some(p=>!parts.has(p.id)))throw Error('厂家实体清单与模型不一致');
 renderer=new THREE.WebGLRenderer({antialias:false,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(Math.max(devicePixelRatio,1.5),2));renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.1;
 $('lift-viewport').append(renderer.domElement);scene=new THREE.Scene();scene.background=new THREE.Color('#d6e2e5');scene.add(assembly);
 camera=new THREE.PerspectiveCamera(38,1,.0002,5);camera.up.set(0,0,1);
 controls=new OrbitControls(camera,renderer.domElement);controls.minDistance=.025;controls.maxDistance=.8;controls.addEventListener('change',render);
 const pmrem=new THREE.PMREMGenerator(renderer),room=new RoomEnvironment();scene.environment=pmrem.fromScene(room,.04).texture;scene.environmentIntensity=.45;scene.environmentRotation.x=Math.PI/2;room.dispose();pmrem.dispose();
 scene.add(new THREE.HemisphereLight(0xf3f6ff,0xa4afa6,1));const light=new THREE.DirectionalLight(0xfff6e8,2.5);light.position.set(.3,-.5,.6);scene.add(light);
 markers=new THREE.Group();scene.add(markers);
 for(const hole of report.plates[0].holes){const dot=new THREE.Mesh(new THREE.SphereGeometry(.00065,12,8),new THREE.MeshBasicMaterial({color:hole.thread==='M6'?0xd47620:hole.thread==='M4'?0x167db4:0x1a9d6e}));dot.position.set(...hole.center_xy_m,model.source_pose_height_m+.0002);markers.add(dot)}
 for(const group of Object.keys(model.inspection_groups)){const option=document.createElement('option');option.value=group;option.textContent=names[group];$('lift-group').append(option)}
 for(const element of document.querySelectorAll('.lift-controls input,.lift-controls select,.lift-controls button'))element.disabled=false;
 for(const id of ['lift-group','lift-isolate','lift-holes','lift-explode'])$(id).addEventListener('input',update);
 $('lift-views').addEventListener('click',event=>{const next=event.target.closest('button')?.dataset.view;if(next)setView(next)});
 new ResizeObserver(()=>{const w=$('lift-viewport').clientWidth,h=$('lift-viewport').clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();setView(view)}).observe($('lift-viewport'));
 const dims=model.geometry.bounds_m[0].map((v,i)=>(1000*(model.geometry.bounds_m[1][i]-v)).toFixed(3));
 $('lift-counts').textContent='86 个原始实体、'+model.parts.reduce((n,p)=>n+p.faces,0).toLocaleString('zh-CN')+' 个三角面；未缩放厂家几何。显示颜色为检查用配色。';
 const rows=[['源姿态外形 X / Y / Z',dims.join(' × ')+' mm'],['上、下板尺寸','101.6 × 76.2 mm'],['图纸收拢 / 伸展高度','21.3 / 47.8 mm；仅提供收拢姿态'],['每块板的螺孔','18 × M3、4 × M4、7 × M6'],['每块板的开口安装槽','4 × M3、2 × M6 / 1/4-20'],['调节工具','1/8 英寸内六角；不得超过机械行程'],['转换接缝','4 个支承块细分 14 条边，86 个实体网格均闭合'],['装入论文装置 / 机器人操作','均待完成']];
 $('lift-metrics').replaceChildren(...rows.map(([label,value])=>{const tr=document.createElement('tr'),th=document.createElement('th'),td=document.createElement('td');th.textContent=label;td.textContent=value;tr.append(th,td);return tr}));
 $('lift-finding').textContent='两块板的实际孔洞和 16 根连杆均已保留。4 个支承块的共线网格接缝已修复，未移动顶点或填补真实孔洞，原始失败网格仍保留。86 个实体网格闭合，但装配间隙、接触和螺杆约束仍需验证。';
 const requirements=['底板和平台的螺钉、孔位、接触与承载','调节螺杆的工具空间、约束与行程','装配间隙及碰撞描述','两台实物的库存、材料和装配分配','完整场景的用户验收'];
 $('lift-requirements').replaceChildren(...requirements.map(text=>{const li=document.createElement('li');li.textContent=text;return li}));
 update();setView('oblique');document.documentElement.dataset.liftLoaded='true';
 // Read-only diagnostic snapshots for independent browser checks.
 window.scienceGymLiftInspection=()=>({source:model.candidate,visible:[...parts].filter(([,m])=>m.visible).map(([id])=>id),matrices:[...parts].map(([id,m])=>{m.updateMatrix();return {id,matrix:m.matrix.toArray()}}),markerCount:markers.children.length});
}catch(error){
 renderer?.dispose();$('lift-viewport').replaceChildren();$('lift-error').textContent=String(error);$('lift-status').textContent='资源未通过版本检查，暂不显示模型。';document.documentElement.dataset.liftLoaded='error';
}
