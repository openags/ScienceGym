import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

const $=id=>document.getElementById(id),root='../../',folder='assets/cooling_lab_v1/',cache=new Map(),parts=new Map();
async function bytes(path){
 if(cache.has(path))return cache.get(path);const r=await fetch(root+path);if(!r.ok)throw Error('无法读取：'+path);
 const buffer=await r.arrayBuffer(),sha=[...new Uint8Array(await crypto.subtle.digest('SHA-256',buffer))].map(v=>v.toString(16).padStart(2,'0')).join('');const value={buffer,sha};cache.set(path,value);return value;
}
async function json(path){return JSON.parse(new TextDecoder().decode((await bytes(path)).buffer))}
async function verify(ref){const value=await bytes(ref.path);if(value.sha!==ref.sha256)throw Error('文件与检查版本不一致：'+ref.path);return value.buffer}
let renderer,scene,camera,controls,light,record,leads,leadChecks,kit,kitChecks,sweep,pending=false,view='oblique',radius=.4;
const mechanicalNames=new Set(),leadNames=new Set(),kitNames=new Set(),fitNames=new Set(),literalNames=new Set();
const centre=new THREE.Vector3(),clip=new THREE.Plane(new THREE.Vector3(0,1,0),0);
function render(){if(pending||!renderer)return;pending=true;requestAnimationFrame(()=>{pending=false;const d=camera.position.distanceTo(centre);camera.near=Math.max(.00005,d-radius*1.2);camera.far=d+radius*1.2;camera.updateProjectionMatrix();renderer.render(scene,camera)})}
function fit(){
 const box=new THREE.Box3();for(const m of parts.values())if(m.visible)box.union(new THREE.Box3().setFromObject(m));const size=box.getSize(new THREE.Vector3());box.getCenter(centre);radius=size.length()/2;
 const direction={oblique:[-.5,-1,.6],top:[0,-.001,1],side:[0,-1,.001],end:[-1,-.001,.001]}[view];
 controls.target.copy(centre);camera.position.copy(centre).addScaledVector(new THREE.Vector3(...direction).normalize(),size.length()*1.45/Math.min(camera.aspect,1));camera.lookAt(centre);controls.update();
 light.position.copy(centre).addScaledVector(new THREE.Vector3(-.6,-.7,1).normalize(),radius*4);light.target.position.copy(centre);light.target.updateMatrixWorld();
 const s=light.shadow;s.camera.left=s.camera.bottom=-radius*1.2;s.camera.right=s.camera.top=radius*1.2;s.camera.near=radius;s.camera.far=radius*7;s.normalBias=radius*.0002;s.camera.updateProjectionMatrix();
 $('wind-size').textContent='当前部件包围尺寸：'+size.toArray().map(v=>(v*1000).toFixed(2)).join(' × ')+' mm';render();
}
function update(refit=true){
 const selected=$('wind-select').value,cups=new Set(record.rotor_axes.cups.parts),vane=new Set(record.rotor_axes.vane.parts);
 const base=n=>n.startsWith('mast_')||n.startsWith('arm_');
 const adapter=n=>n.startsWith('wind_adapter_'),plug=n=>n.startsWith('plug_')||n==='modular_plug_body_and_latch';
 for(const [name,m] of parts){
  m.visible=(selected==='all'&&!fitNames.has(name)&&!literalNames.has(name))||(selected==='mechanical'&&mechanicalNames.has(name))||(selected==='head'&&mechanicalNames.has(name)&&!base(name)&&name!=='bent_hollow_arm')||(selected==='cups'&&cups.has(name))||(selected==='vane'&&vane.has(name))||(selected==='base'&&base(name))||(selected==='arm'&&name==='bent_hollow_arm')||(selected==='leads'&&leadNames.has(name))||(selected==='adapter'&&adapter(name))||(selected==='plug'&&plug(name))||(selected==='route'&&(base(name)||name==='wind_sensor_lead'))||(selected==='kit'&&kitNames.has(name))||(selected==='key'&&name==='supplied_0050_hex_key_candidate')||(selected==='fit'&&fitNames.has(name))||(selected==='comparison'&&(literalNames.has(name)||name==='three_cup_rotor'));
  m.material.clippingPlanes=$('wind-section').checked?[clip]:[];
 }
 clip.constant=selected==='adapter'?.30:selected==='plug'?.16:0;
 for(const [name,axis] of Object.entries(record.rotor_axes)){
  const control=name==='cups'?'cup':'vane',degrees=Number($('wind-'+control+'-angle').value);$('wind-'+control+'-value').textContent=degrees+'°';
  const [x,y,z]=axis.origin_m,matrix=new THREE.Matrix4().makeTranslation(x,y,z).multiply(new THREE.Matrix4().makeRotationZ(degrees*Math.PI/180)).multiply(new THREE.Matrix4().makeTranslation(-x,-y,-z));
  for(const part of axis.parts){const mesh=parts.get(part);mesh.matrix.copy(matrix);mesh.matrixWorldNeedsUpdate=true;}
  if(name==='cups')for(const part of literalNames){const mesh=parts.get(part);mesh.matrix.copy(matrix);mesh.matrixWorldNeedsUpdate=true;}
 }
 sweep.visible=$('wind-sweep').checked;
 for(const child of sweep.children)child.visible=selected==='all'||selected==='mechanical'||selected==='head'||selected===child.name;
 if(refit)fit();else render();
}
try{
 const checks=await json(folder+'wind_sensor_checks.json');record=await json(folder+'wind_sensor_assets.json');
 leads=await json(folder+'wind_lead_assets.json');leadChecks=await json(folder+'wind_lead_checks.json');
 kit=await json(folder+'wind_kit_assets.json');kitChecks=await json(folder+'wind_kit_checks.json');
 for(const ref of [...record.source_artifacts,...checks.source_artifacts,...leads.source_artifacts,...leadChecks.source_artifacts,...kit.source_artifacts,...kitChecks.source_artifacts])await verify(ref);
 if(!checks.passed||checks.installation_qualified||checks.robot_use_qualified||record.staged_in_lab||record.assembly_qualified||record.owner_acceptance!==null||checks.owner_acceptance!==null)throw Error('机械候选的检查范围不一致');
 if(!leadChecks.passed||leadChecks.installation_qualified||leadChecks.robot_use_qualified||leads.staged_in_lab||leads.assembly_qualified||leads.owner_acceptance!==null||leadChecks.owner_acceptance!==null||leads.mechanical_geometry.sha256!==record.geometry.sha256)throw Error('线缆候选与机械版本或检查范围不一致');
 if(!kitChecks.passed||kitChecks.installed_tool_access_qualified||kitChecks.torque_qualified||kit.staged_in_lab||kit.initial_stock_credit||kit.owner_acceptance!==null||kitChecks.owner_acceptance!==null)throw Error('工具套件候选的检查范围不一致');
 const assembly=new THREE.Group();
 for(const [ref,names] of [[record.geometry,mechanicalNames],[leads.geometry,leadNames],[kit.geometry,kitNames],[kitChecks.fit_geometry,fitNames],[record.unresolved_cup_radius.literal_interpretation_geometry,literalNames]]){
  const source=await new GLTFLoader().parseAsync(await verify(ref),root);source.scene.updateMatrixWorld(true);
  source.scene.traverse(o=>{if(!o.isMesh)return;const index=source.parser.associations.get(o)?.nodes,name=source.parser.json.nodes[index]?.name||o.name;
   const identity=names===fitNames?'fit__'+name:name;if(parts.has(identity))throw Error('重复部件名称：'+identity);
   const material=names===literalNames?new THREE.MeshBasicMaterial({color:0xc18426,transparent:true,opacity:.25,depthWrite:false}):o.material.clone();
   const mesh=new THREE.Mesh(o.geometry.clone().applyMatrix4(o.matrixWorld),material);mesh.name=identity;mesh.matrixAutoUpdate=false;mesh.material.side=THREE.DoubleSide;mesh.castShadow=names!==literalNames;mesh.receiveShadow=true;parts.set(identity,mesh);names.add(identity);assembly.add(mesh);
  });if(names.size!==ref.parts)throw Error('模型部件数量不一致');
 }
 const envelope=await new GLTFLoader().parseAsync(await verify(checks.sweep_geometry),root);envelope.scene.updateMatrixWorld(true);sweep=new THREE.Group();
 envelope.scene.traverse(o=>{if(!o.isMesh)return;const index=envelope.parser.associations.get(o)?.nodes,name=envelope.parser.json.nodes[index]?.name||o.name;const m=new THREE.Mesh(o.geometry.clone().applyMatrix4(o.matrixWorld),new THREE.MeshBasicMaterial({color:name==='cups'?0xd09a34:0x39899a,transparent:true,opacity:.18,depthWrite:false,side:THREE.DoubleSide}));m.name=name;sweep.add(m)});
 renderer=new THREE.WebGLRenderer({antialias:false,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(Math.max(devicePixelRatio,1.5),2));renderer.localClippingEnabled=true;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1;$('lift-viewport').append(renderer.domElement);
 scene=new THREE.Scene();scene.background=new THREE.Color('#e0e6e5');scene.add(assembly,sweep);camera=new THREE.PerspectiveCamera(38,1,.00005,4);camera.up.set(0,0,1);controls=new OrbitControls(camera,renderer.domElement);controls.minDistance=.01;controls.maxDistance=3;controls.addEventListener('change',render);
 const pmrem=new THREE.PMREMGenerator(renderer),room=new RoomEnvironment();scene.environment=pmrem.fromScene(room,.04).texture;scene.environmentIntensity=.3;scene.environmentRotation.x=Math.PI/2;room.dispose();pmrem.dispose();scene.add(new THREE.HemisphereLight(0xf3f6ff,0xb5b2a9,.45));
 light=new THREE.DirectionalLight(0xfff9ef,2.1);light.castShadow=true;light.shadow.mapSize.set(2048,2048);light.shadow.bias=-.00001;scene.add(light,light.target);
 for(const element of document.querySelectorAll('.lift-controls input,.lift-controls select,.lift-controls button'))element.disabled=false;
 $('wind-select').addEventListener('change',()=>update());for(const id of ['wind-cup-angle','wind-vane-angle'])$(id).addEventListener('input',()=>update(false));for(const id of ['wind-section','wind-sweep'])$(id).addEventListener('change',()=>update(false));
 $('wind-views').addEventListener('click',e=>{const next=e.target.closest('button')?.dataset.view;if(next){view=next;fit()}});
 new ResizeObserver(()=>{renderer.setSize($('lift-viewport').clientWidth,$('lift-viewport').clientHeight);camera.aspect=$('lift-viewport').clientWidth/$('lift-viewport').clientHeight;fit()}).observe($('lift-viewport'));
 $('wind-status').textContent=mechanicalNames.size+' 个机械部件 + '+leadNames.size+' 个外接部件 + '+kitNames.size+' 件散装套件 · 未放入库存 · 未验收';
 $('wind-findings').textContent=checks.checks.length+' 项检查通过。每个转子检查了 12 个角度，并用独立整圈包络检查固定结构。D 形轴随风向标旋转，避免把正确机械关系误判为卡死。';
 $('wind-orbit').textContent='风杯扫掠采用环面，按几何对称性与距离界验证整圈容纳风杯实体；实际三角面同时检查保守包络。余量与数值误差保留在原始记录中。';
 $('wind-lead-findings').textContent=leadChecks.checks.length+' 项线缆检查通过：选用 2.5 m + 0.5 m 连续线长，穿过实际安装座开口，与机械部件无实体穿插。该长度解释、3 mm 线径及适配器局部尺寸均明确标注，仍需核实厂家资料中的 3 m / 12.2 m 冲突。';
 $('wind-kit-findings').textContent=kitChecks.checks.length+' 项散装套件检查通过：两枚可选木螺钉和一把 0.05 英寸内六角扳手。分离的螺钉与工具检查了短端插入和触底，尚未验证装机后的工具接近与拧紧。';
 update();window.scienceGymWindInspection=()=>({selected:$('wind-select').value,visible:[...parts].filter(([,m])=>m.visible).map(([n])=>n),angles:{cups:Number($('wind-cup-angle').value),vane:Number($('wind-vane-angle').value)},section:$('wind-section').checked,sweep:$('wind-sweep').checked,shaftMatrices:{cups:parts.get('lower_speed_shaft').matrix.toArray(),vane:parts.get('upper_direction_d_shaft').matrix.toArray()}});document.documentElement.dataset.windLoaded='true';
}catch(error){renderer?.dispose();$('lift-viewport').replaceChildren();$('lift-error').textContent=String(error);$('wind-status').textContent='版本与检查不匹配，暂不显示。';document.documentElement.dataset.windLoaded='error'}
