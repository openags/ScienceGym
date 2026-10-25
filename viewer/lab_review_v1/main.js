import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {batchStaticMeshes} from './render_batches.js';
import {SensorReview} from './sensors.js';

const $=id=>document.getElementById(id),root='../../',folder=root+'assets/cooling_lab_v1/';
const fetchedHashes=new Map();
const digest=async buffer=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',buffer)),x=>x.toString(16).padStart(2,'0')).join('');
const read=async p=>{const r=await fetch(p);if(!r.ok)throw Error(p+' HTTP '+r.status);const buffer=await r.arrayBuffer();fetchedHashes.set(p,await digest(buffer));return JSON.parse(new TextDecoder().decode(buffer))};
const scene=new THREE.Scene();scene.background=new THREE.Color('#c9dce4');
const camera=new THREE.PerspectiveCamera(42,1,.02,200);camera.up.set(0,0,1);
// SwiftShader MSAA produces depth artifacts on the thin cylindrical labels,
// including with their container hidden. Supersample the review canvas instead;
// retain normal depth testing and leave the fixed sensor render targets intact.
const renderer=new THREE.WebGLRenderer({antialias:false,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(Math.max(devicePixelRatio,1.5),2));renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;
const pmrem=new THREE.PMREMGenerator(renderer),reflectionRoom=new RoomEnvironment();
scene.environment=pmrem.fromScene(reflectionRoom,.04).texture;scene.environmentIntensity=.32;scene.environmentRotation.x=Math.PI/2;reflectionRoom.dispose();pmrem.dispose();
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.shadowMap.autoUpdate=false;
$('viewport').prepend(renderer.domElement);
renderer.domElement.tabIndex=0;renderer.domElement.setAttribute('aria-label','实验室三维视图，室内模式可用方向键移动视点');
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.maxPolarAngle=Math.PI*.49;controls.minDistance=.12;controls.maxDistance=80;
let renderPending=false;
function requestRender(){if(renderPending)return;renderPending=true;requestAnimationFrame(()=>{renderPending=false;const changing=controls.enabled&&controls.update();renderer.render(scene,camera);if(changing)requestRender()})}
controls.addEventListener('change',requestRender);
const ambient=new THREE.HemisphereLight(0xf0f6ff,0xb4b8ac,.62);ambient.position.set(0,0,10);scene.add(ambient);
const keyLight=new THREE.DirectionalLight(0xfff8e8,1.8);keyLight.position.set(10,-5,24);keyLight.target.position.set(3,9,0);keyLight.castShadow=true;
Object.assign(keyLight.shadow.camera,{left:-20,right:20,top:20,bottom:-20,near:.5,far:65});keyLight.shadow.mapSize.set(2048,2048);keyLight.shadow.normalBias=.008;keyLight.shadow.bias=-.0001;scene.add(keyLight,keyLight.target);
const fillLight=new THREE.DirectionalLight(0xe5f1ff,.22);fillLight.position.set(-10,9,13);scene.add(fillLight);
const roomLights=new THREE.Group();scene.add(roomLights);
function installRoomLights(){
 const positions=manifest.room_design.light_positions_m;
 for(const [i,p] of positions.entries()){
  const lamp=new THREE.SpotLight(0xfff7ec,p[0]<0?23:30,17,1.24,.78,2);
  lamp.position.set(...p);lamp.target.position.set(p[0],p[1],0);
  lamp.castShadow=[0,3,4,6,8].includes(i);lamp.shadow.mapSize.set(p[0]<0?512:1024,p[0]<0?512:1024);
  lamp.shadow.bias=-.0002;lamp.shadow.normalBias=.003;lamp.shadow.camera.near=.12;
  roomLights.add(lamp,lamp.target);
 }
 document.documentElement.dataset.roomLightCount=positions.length;
}
const overlays=new THREE.Group(),labels=new THREE.Group(),measurements=new THREE.Group();scene.add(overlays,labels,measurements);
let architecture,manifest,inventory,risks,report,bodyReport,readiness,allocation,workspace,selected=null,measureMode=false,measurePoints=[],pointerStart;
let sensors=null,sensorRig=null;let robotRest=[];const accessMarker=new THREE.Group();scene.add(accessMarker);
const groups=new Map(),states=new Map(),assetList=[],renderBatches=[];
const loader=new GLTFLoader();
const loadPinned=async(path,expected)=>{const r=await fetch(root+path+'?revision='+expected);if(!r.ok)throw Error(path+' HTTP '+r.status);const buffer=await r.arrayBuffer();if(await digest(buffer)!==expected)throw Error(path+' 的模型哈希与当前场景不一致');return loader.parseAsync(buffer,new URL(root+path,location.href).href)};
const textSprite=(text,color='#164a42',scale=1)=>{
 const c=document.createElement('canvas'),ctx=c.getContext('2d');ctx.font='600 36px system-ui';c.width=Math.ceil(ctx.measureText(text).width)+48;c.height=72;
 ctx.fillStyle='#fffffff0';ctx.roundRect(0,0,c.width,c.height,8);ctx.fill();ctx.fillStyle=color;ctx.font='600 36px system-ui';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(text,c.width/2,36);
 const tex=new THREE.CanvasTexture(c);tex.colorSpace=THREE.SRGBColorSpace;const material=new THREE.SpriteMaterial({map:tex,depthTest:false,transparent:true,toneMapped:false});const sprite=new THREE.Sprite(material);sprite.scale.set(c.width/c.height*.8*scale,.8*scale,1);sprite.renderOrder=5;return sprite;
};
const line=(points,color,width=1)=>new THREE.Line(new THREE.BufferGeometry().setFromPoints(points.map(p=>new THREE.Vector3(...p))),new THREE.LineBasicMaterial({color,linewidth:width}));
let roomMode=false,lookYaw=0,lookPitch=0,lookDrag=null;
const recordCamera=()=>{document.documentElement.dataset.cameraPosition=camera.position.toArray().map(v=>v.toFixed(3)).join(',');document.documentElement.dataset.cameraMode=roomMode?'room':'orbit'};
const aimRoom=()=>{camera.lookAt(camera.position.clone().add(new THREE.Vector3(Math.cos(lookYaw)*Math.cos(lookPitch),Math.sin(lookYaw)*Math.cos(lookPitch),Math.sin(lookPitch))));recordCamera();requestRender()};
const setView=(pos,target,inside=false)=>{
 roomMode=inside;controls.enabled=!inside;camera.fov=inside?68:42;camera.updateProjectionMatrix();camera.position.set(...pos);controls.target.set(...target);
 if(inside){const d=new THREE.Vector3(...target).sub(camera.position);lookYaw=Math.atan2(d.y,d.x);lookPitch=Math.atan2(d.z,Math.hypot(d.x,d.y));aimRoom()}else{controls.update();camera.lookAt(controls.target)}
 $('walk-controls').hidden=!inside;
 $('scene-caption').textContent=inside?'室内视点 · 拖动环顾 · 方向键 / WASD 移动 · 滚轮调视野':'剖切 / 资产视图 · 拖动旋转 · 滚轮缩放 · 点击设备查看来源';
 recordCamera();requestRender();
};
const views={all:[[19,-13,22],[3.1,9.5,0]],indoor:[[7.4,.7,1.65],[4.8,8.7,1.25],true],details:[[4.5,1.4,1.65],[2.65,3,.75],true],service:[[7.45,1.65,1.65],[8.35,.43,.92],true],rear:[[6.9,9.3,1.65],[5.5,1.8,1.3],true],outdoor:[[16,7,12],[6,16,.4]],optics:[[7,6.9,1.65],[9.3,8.8,1.25],true],wet:[[5.4,4.1,1.65],[1.8,5.9,1.1],true],annex:[[-.9,1,1.65],[-4.4,3.5,1.35],true],coating:[[-1,5.8,1.65],[-4.4,8.5,1.4],true],top:[[3,9.5,32],[3,9.5,0]]};
setView(...views.indoor);document.documentElement.dataset.view='indoor';
const resize=()=>{const w=$('viewport').clientWidth,h=$('viewport').clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();requestRender()};new ResizeObserver(resize).observe($('viewport'));resize();
function resetStates(){for(const state of states.values())for(const item of state.parts){item.node.position.copy(item.position);item.node.quaternion.copy(item.quaternion)}
 for(const item of robotRest){item.node.position.copy(item.position);item.node.quaternion.copy(item.quaternion)}
 const robot=groups.get('g1');if(robot){robot.position.set(...assetList.find(a=>a.id==='g1').position_m);robot.rotation.set(0,0,0)}
 if(sensors){const k=states.get('g1_hands_inspection').config.kinematics;sensors.update(new Map(Object.entries(k.bind_world).map(([n,t])=>[n,new THREE.Matrix4().fromArray(t.flat()).transpose()])))}
 accessMarker.clear();delete document.documentElement.dataset.workspacePose;
 if($('workspace-pose-status'))$('workspace-pose-status').textContent='选择检查点可查看静态姿态。';
 renderer.shadowMap.needsUpdate=true;requestRender()}
function inspectWorkspace(target){
 resetStates();const result=target.result,group=groups.get('g1'),asset=assetList.find(a=>a.id==='g1');
 const k=states.get('g1_hands_inspection').config.kinematics;
 const world=new Map([[k.root_link,new THREE.Matrix4().fromArray(k.root_matrix.flat()).transpose()]]);
 const q={...result.joint_coordinates};
 for(const j of k.joints){if(j.mimic)q[j.name]=Number(j.mimic.offset||0)+Number(j.mimic.multiplier||1)*(q[j.mimic.joint]||0);
  const t=new THREE.Matrix4().fromArray(j.origin_matrix.flat()).transpose();
  if(q[j.name])t.multiply(new THREE.Matrix4().makeRotationAxis(new THREE.Vector3(...j.axis),q[j.name]));
  world.set(j.id,world.get(j.parent).clone().multiply(t));
 }
 const n=new THREE.Matrix4().fromArray(asset.normalization_matrix.flat()).transpose(),ni=n.clone().invert();
 for(const item of robotRest){const link=k.part_links[item.node.name];if(!link)continue;
  const bind=new THREE.Matrix4().fromArray(k.bind_world[link].flat()).transpose();
  item.node.updateMatrix();item.node.applyMatrix4(n.clone().multiply(world.get(link)).multiply(bind.invert()).multiply(ni));
 }
 group.position.set(result.base_position_m[0],result.base_position_m[1],result.base_position_m[2]-k.root_matrix[2][3]);group.rotation.z=result.base_yaw_rad;if(sensors)sensors.update(world);
 const marker=new THREE.Mesh(new THREE.SphereGeometry(.018),new THREE.MeshBasicMaterial({color:result.position_candidate?'#dc891f':'#c53c37',depthTest:false}));marker.position.set(...target.point_m);accessMarker.add(marker);
 $('isolate').checked=false;$('show-walls').checked=false;visibility();const p=result.base_position_m;
 setView([p[0]+1.8,p[1]-2.1,2.0],[target.point_m[0],target.point_m[1],.8]);
 $('workspace-pose-status').textContent=target.id+' · 静态位置检查，误差 '+(result.position_error_m*1000).toFixed(1)+' mm；'+result.external_overlaps.length+' 处外部包围盒冲突；自碰撞 '+(result.self_contacts_checked?result.self_penetrations_over_0_5mm.length+' 对超过 0.5 mm':'尚未检查（位置未到达）')+'；候选相机与其他机器人部件相交 '+result.candidate_rig_other_link_intersections.length+' 对，适配抱环刚性间隙已检查，衬垫预紧仍待确认。手掌方向、目标设备内部碰撞、平衡与进入路径尚未验证。';
 document.documentElement.dataset.workspacePose=target.id;$('viewport').scrollIntoView({block:'center'});renderer.shadowMap.needsUpdate=true;requestRender();
}
function applyState(id,fraction){
 resetStates();const state=states.get(id);if(!state)return;
 if(state.config.kind==='joint_tree'){
  const k=state.config.kinematics,world=new Map([[k.root_link||'palm',k.root_matrix?new THREE.Matrix4().fromArray(k.root_matrix.flat()).transpose():new THREE.Matrix4()]]),n=new THREE.Matrix4().fromArray(state.normalization.flat()).transpose(),ni=n.clone().invert();
  for(const j of k.joints){const translation=j.origin_matrix?new THREE.Matrix4().fromArray(j.origin_matrix.flat()).transpose():new THREE.Matrix4().makeTranslation(...j.origin_m),rotation=new THREE.Matrix4().makeRotationAxis(new THREE.Vector3(...j.axis),fraction*j.inspection_angle_rad);world.set(j.id,world.get(j.parent).clone().multiply(translation).multiply(rotation))}
  for(const item of state.parts){const link=k.part_links[item.node.name],bind=new THREE.Matrix4().fromArray(k.bind_world[link].flat()).transpose();const delta=n.clone().multiply(world.get(link)).multiply(bind.invert()).multiply(ni);item.node.updateMatrix();item.node.applyMatrix4(delta)}
  if(sensors&&state.config.asset==='g1')sensors.update(world);
  document.documentElement.dataset.openState=id+':'+fraction;renderer.shadowMap.needsUpdate=true;requestRender();return;
 }
 const axis=new THREE.Vector3(...state.config.axis),angle=state.config.maximum*fraction,q=new THREE.Quaternion().setFromAxisAngle(axis,angle);
 for(const item of state.parts){
  if(state.config.kind==='slide')item.node.position.addScaledVector(axis,angle);
  else {item.node.position.sub(state.pivot).applyQuaternion(q).add(state.pivot);item.node.quaternion.premultiply(q)}
 }
 document.documentElement.dataset.openState=id+':'+fraction;
 if(state.config.frame_separated_parts&&$('isolate').checked){
  const box=new THREE.Box3().setFromObject(groups.get(state.config.asset)),center=box.getCenter(new THREE.Vector3());
  const direction=camera.position.clone().sub(controls.target).normalize(),distance=Math.max(...box.getSize(new THREE.Vector3()).toArray())*1.8/Math.min(1,camera.aspect);
  setView(center.clone().addScaledVector(direction,distance).toArray(),center.toArray());
  camera.updateMatrixWorld();const projected=[];
  for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z])projected.push(new THREE.Vector3(x,y,z).project(camera));
  document.documentElement.dataset.inspectionInFrame=String(projected.every(p=>Math.abs(p.x)<1&&Math.abs(p.y)<1&&Math.abs(p.z)<1));
 }
 renderer.shadowMap.needsUpdate=true;
 requestRender();
}
function visibility(){
 const isolate=$('isolate').checked&&selected;
 if(architecture)architecture.visible=!isolate;
 for(const [id,group] of groups)group.visible=!isolate||id===selected;
 overlays.visible=!isolate&&$('show-space').checked;labels.visible=!isolate&&$('show-labels').checked;
 if(architecture)architecture.traverse(o=>{if(o.isMesh&&o.userData.cutaway)o.visible=$('show-walls').checked});
 roomLights.visible=!isolate;
 document.documentElement.dataset.roomShellVisible=String(!isolate&&$('show-walls').checked);
 renderer.shadowMap.needsUpdate=true;
 requestRender();
}
function detailRow(label,value){const d=document.createElement('div');d.className='detail-row';const b=document.createElement('b');b.textContent=label;const s=document.createElement('span');s.textContent=value;d.append(b,s);$('asset-detail').append(d)}
function selectAsset(id,focus=true){
 selected=id;const asset=assetList.find(a=>a.id===id);if(!asset)return;
 $('asset-select').value=id;$('asset-detail').replaceChildren();const h=document.createElement('h3');h.textContent=asset.label;$('asset-detail').append(h);
 $('asset-views').hidden=false;
 detailRow('当前状态',asset.status);const size=asset.normalized_bounds_m[1].map((v,i)=>v-asset.normalized_bounds_m[0][i]);
 detailRow('模型包围尺寸（含已建附件）',size.map(v=>(v*1000).toFixed(1)+' mm').join(' × '));detailRow('物理比例 / 部件', '1 : 1 · '+asset.part_count+' 个部件');detailRow('工位',asset.station);
 if(asset.note)detailRow('待确认内容',asset.note);
 const stockRole=allocation?.physical_instances.find(p=>p.id===id);if(stockRole)detailRow('库存角色',stockRole.note);
 const resourceIds=asset.resource_ids||[asset.resource_id];
 const requirements=readiness?.manual_step_requirements.filter(s=>s.resource_requirements.some(r=>resourceIds.includes(r)))||[];
 detailRow('论文操作关联',requirements.length?requirements.length+' 个操作定义涉及此资源；均待人形机器人验证':'机器人或设施支持项；不计作已完成的论文操作');
 const units={tool:'件',vessel:'个',probe:'支',sheet:'张',roll:'卷',blank:'块',cart:'辆',tray:'个',connector_pair:'对',kit:'套',lead:'根','T-nut':'个'};
 for(const requirement of readiness?.requirements||[])for(const component of requirement.components){const staged=component.staged_candidates;if(!staged)continue;const count=staged.members.filter(m=>m.asset_id===id).length;if(count)detailRow('逐件候选 · '+component.label,count+' '+(units[staged.unit]||staged.unit)+'；按用途绑定，可共享，不代表完整实验用量或已完成操作')}
 const a=document.createElement('a');a.href=root+(asset.sources||asset.source_artifact.path);a.target='_blank';a.textContent='查看模型来源与重构依据 ↗';$('asset-detail').append(a);
 if(['fine_cutter','meter_leads_white','meter_leads_black','workholding_kit','deburring_tool','g1_spare_battery','g1_disconnected_charger','coating_white_stock','coating_black_stock','silver_paste_stock'].includes(id)){const review=document.createElement('a');review.href=root+'assets/cooling_lab_v1/preparation_review.json';review.target='_blank';review.textContent='备料、接线、涂覆与服务资产的比对和检查视图 ↗';$('asset-detail').append(review)}
 if(manifest.reference_comparisons?.[id]){const ref=manifest.reference_comparisons[id];if(ref.dimensions_label)detailRow(ref.dimensions_kind==='inferred'?'推断尺寸（待核实）':'厂家标注尺寸',ref.dimensions_label);detailRow('比对边界',ref.model_scope);for(const source of ref.sources){const link=document.createElement('a');link.href=source.url;link.target='_blank';link.rel='noopener';link.textContent=source.label+' ↗';if(source.scope)link.title=source.scope;$('asset-detail').append(link)}}
 resetStates();const state=[...states.values()].find(s=>s.config.asset===id);$('state-control').hidden=!state;$('state-slider').value=0;
 if(state){$('state-label').textContent=state.config.label;$('state-slider').oninput=()=>applyState(state.config.id,Number($('state-slider').value)/100)}
 if(focus){$('isolate').checked=true;const bounds=new THREE.Box3().setFromObject(groups.get(id));const c=bounds.getCenter(new THREE.Vector3());const extent=Math.max(...bounds.getSize(new THREE.Vector3()).toArray());setView([c.x+extent*1.2,c.y-extent*1.8,c.z+extent*1.3],c.toArray())}
 visibility();document.documentElement.dataset.selectedAsset=id;
}
function renderInventory(){
 const query=$('search').value.toLowerCase(),filter=$('filter').value;let count=0;$('inventory').replaceChildren();
 for(const item of inventory.items){const placed=assetList.filter(a=>(a.resource_ids||[a.resource_id]).includes(item.id)),authored=item.authored_scene_components||[],hasGeometry=placed.length||authored.length,historical=item.requirement_role==='superseded_embodiment_reference';if(query&&!JSON.stringify(item).toLowerCase().includes(query))continue;if(filter==='historical'&&!historical||filter!=='all'&&filter!=='historical'&&historical||filter==='placed'&&!hasGeometry||filter==='missing'&&hasGeometry)continue;
  const tr=document.createElement('tr');const first=document.createElement('td');
  if(placed.length){const b=document.createElement('button');b.textContent=item.label;b.onclick=()=>{selectAsset(placed[0].id);$('viewport').scrollIntoView({behavior:'smooth',block:'center'})};first.append(b)}else first.textContent=item.label;
  tr.append(first);const categories={equipment:'论文设备',tools:'工具与夹具',consumables:'材料与耗材',additional_reconstructed_materials:'补充材料/夹具',accessory:'独立附件',robot:'机器人',authored_facility_requirement:'实验室设施'};
  for(const text of [categories[item.category]||item.category,historical?'历史选型 · 已被 G1 / Inspire 替代':placed.length?'已放置 '+placed.length+' 个实例':authored.length?'已建部分设计几何（'+authored.length+' 组），待完整性审查':'尚未放入场景',historical?'不参与当前验收':'待验收']){const td=document.createElement('td');td.textContent=text;tr.append(td)}$('inventory').append(tr);count++;
 }
 $('inventory-count').textContent='显示 '+count+' / '+inventory.items.length+' 个需求条目';
}
function buildOverlays(){
 const material=color=>new THREE.MeshBasicMaterial({color,transparent:true,opacity:.20,depthWrite:false,side:THREE.DoubleSide});
 for(const route of manifest.corridors){
  const pts=route.points_m;
  for(let i=0;i<pts.length-1;i++){const a=pts[i],b=pts[i+1],length=Math.hypot(b[0]-a[0],b[1]-a[1]);const m=new THREE.Mesh(new THREE.PlaneGeometry(length,route.width_m),material('#26856b'));m.position.set((a[0]+b[0])/2,(a[1]+b[1])/2,.011);m.rotation.z=Math.atan2(b[1]-a[1],b[0]-a[0]);overlays.add(m)}
 }
 for(const s of manifest.spaces){const m=new THREE.Mesh(s.kind==='turn'?new THREE.CircleGeometry(s.radius_m,80):new THREE.PlaneGeometry(...s.size_m),material(s.kind==='turn'?'#3c88b1':'#d69e45'));m.position.set(...s.center_m,.019);overlays.add(m);
  if(s.kind==='turn'){const label=textSprite('转身预留 Ø '+(s.radius_m*2).toFixed(1)+' m','#25698c',.55);label.position.set(...s.center_m,.35);labels.add(label)}
 }
 for(const z of manifest.zones){const label=textSprite(z.label,'#254c42',1.1);label.position.set((z.bounds_m[0]+z.bounds_m[2])/2,z.bounds_m[1]+.4,1.8);labels.add(label)}
 for(const [points,text,position] of [[[[0,-1.7,.02],[12,-1.7,.02]],'12.0 m',[6,-1.7,.3]],[[[-6.8,0,.02],[-6.8,10,.02]],'10.0 m',[-6.8,5,.3]],[[[12.8,12,.02],[12.8,20,.02]],'8.0 m',[12.8,16,.3]]]){overlays.add(line(points,'#4b7164'));const label=textSprite(text,'#356254',.5);label.position.set(...position);labels.add(label)}
}
const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();
function moveView(forward,side){
 if(!roomMode||!manifest)return;
 const step=.25,x=camera.position.x+step*(Math.cos(lookYaw)*forward+Math.sin(lookYaw)*side),y=camera.position.y+step*(Math.sin(lookYaw)*forward-Math.cos(lookYaw)*side),r=.18;
 const onFloor=manifest.zones.some(z=>x>=z.bounds_m[0]+r&&x<=z.bounds_m[2]-r&&y>=z.bounds_m[1]+r&&y<=z.bounds_m[3]-r)||x>4.7&&x<7.3&&y>=.18&&y<=12.3||x>-.3&&x<.3&&(y>1.7&&y<3.3||y>6.7&&y<8.3);
 const bodySolids=manifest.assets.filter(a=>a.station==='circulation').map(a=>({bounds_m:a.normalized_bounds_m.map(b=>b.map((v,i)=>v+a.position_m[i]))}));
 const blocked=[...manifest.obstacles,...bodySolids].some(o=>{const [a,b]=o.bounds_m;return a[2]<1.85&&b[2]>.05&&x>a[0]-r&&x<b[0]+r&&y>a[1]-r&&y<b[1]+r});
 if(onFloor&&!blocked){camera.position.set(x,y,1.65);aimRoom()}
 document.documentElement.dataset.cameraBlocked=String(!onFloor||blocked);
}
renderer.domElement.addEventListener('keydown',e=>{const keys={ArrowUp:[1,0],w:[1,0],ArrowDown:[-1,0],s:[-1,0],ArrowLeft:[0,-1],a:[0,-1],ArrowRight:[0,1],d:[0,1]};if(roomMode&&keys[e.key]){e.preventDefault();moveView(...keys[e.key])}});
$('walk-controls').onclick=e=>{const direction=e.target.closest('button')?.dataset.move;if(direction){moveView(...{forward:[1,0],back:[-1,0],left:[0,-1],right:[0,1]}[direction]);renderer.domElement.focus({preventScroll:true})}};
renderer.domElement.addEventListener('wheel',e=>{if(roomMode){e.preventDefault();camera.fov=THREE.MathUtils.clamp(camera.fov+e.deltaY*.025,45,85);camera.updateProjectionMatrix();requestRender()}},{passive:false});
renderer.domElement.addEventListener('pointerdown',e=>{pointerStart=[e.clientX,e.clientY];renderer.domElement.focus({preventScroll:true});if(roomMode&&!measureMode){lookDrag=[e.clientX,e.clientY,lookYaw,lookPitch];renderer.domElement.setPointerCapture(e.pointerId)}});
renderer.domElement.addEventListener('pointermove',e=>{if(lookDrag){lookYaw=lookDrag[2]-(e.clientX-lookDrag[0])*.003;lookPitch=THREE.MathUtils.clamp(lookDrag[3]-(e.clientY-lookDrag[1])*.003,-1.15,1.15);aimRoom()}});
renderer.domElement.addEventListener('pointercancel',()=>{lookDrag=null;pointerStart=null});
renderer.domElement.addEventListener('pointerup',e=>{
 lookDrag=null;
 if(!pointerStart||Math.hypot(e.clientX-pointerStart[0],e.clientY-pointerStart[1])>5)return;
 const r=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);raycaster.setFromCamera(pointer,camera);
 const hits=raycaster.intersectObjects([...(architecture?[architecture]:[]),...groups.values()],true).filter(h=>{let n=h.object;while(n){if(!n.visible)return false;n=n.parent}return true});if(!hits.length)return;
 if(measureMode){measurePoints.push(hits[0].point.clone());const dot=new THREE.Mesh(new THREE.SphereGeometry(.025),new THREE.MeshBasicMaterial({color:'#b55620',depthTest:false}));dot.position.copy(hits[0].point);measurements.add(dot);requestRender();
  if(measurePoints.length===2){measurements.add(line(measurePoints.map(p=>p.toArray()),'#b55620'));$('measurement').textContent=measurePoints[0].distanceTo(measurePoints[1]).toFixed(3)+' m';measureMode=false;$('measure').classList.remove('active');document.documentElement.dataset.measurementComplete='true'}return;
 }
 const object=hits.find(h=>h.object.userData.assetId);if(object)selectAsset(object.object.userData.assetId,false);
});
$('measure').onclick=()=>{measurements.clear();measurePoints=[];measureMode=true;$('measure').classList.add('active');$('measurement').style.display='block';$('measurement').textContent='依次点击两个模型表面点';document.documentElement.dataset.measurementComplete='false';requestRender()};
$('clear-measure').onclick=()=>{measurements.clear();measurePoints=[];measureMode=false;$('measurement').style.display='none';$('measure').classList.remove('active');requestRender()};
$('views').onclick=e=>{const key=e.target.dataset.view;if(!key)return;$('isolate').checked=false;$('show-walls').checked=!['all','top'].includes(key);resetStates();$('state-slider').value=0;visibility();setView(...views[key]);for(const b of $('views').children)b.classList.toggle('active',b.dataset.view===key);document.documentElement.dataset.view=key};
for(const id of ['show-walls','show-space','show-labels','isolate'])$(id).onchange=visibility;
$('asset-select').onchange=()=>selectAsset($('asset-select').value);$('search').oninput=renderInventory;$('filter').onchange=renderInventory;
$('asset-views').onclick=e=>{const direction=e.target.dataset.direction;if(!direction||!selected)return;const b=new THREE.Box3().setFromObject(groups.get(selected)),c=b.getCenter(new THREE.Vector3()),d=Math.max(...b.getSize(new THREE.Vector3()).toArray())*1.8;const v=(selected==='g1'?{front:[d,0,0],back:[-d,0,0],side:[0,-d,0],top:[.001,0,d]}:{front:[0,-d,0],back:[0,d,0],side:[d,0,0],top:[0,-.001,d]})[direction];$('isolate').checked=true;visibility();setView(c.clone().add(new THREE.Vector3(...v)).toArray(),c.toArray());document.documentElement.dataset.assetView=direction};
const storageKey='sciencegym-lab-review-notes-v1';try{$('review-notes').value=localStorage.getItem(storageKey)||''}catch{}
$('review-notes').oninput=()=>{try{localStorage.setItem(storageKey,$('review-notes').value);$('notes-status').textContent='已保存到此浏览器'}catch{$('notes-status').textContent='浏览器存储不可用，可下载保存'}};
$('export-notes').onclick=()=>{const record={scene_revision:report?.scene_sha256,created_at:new Date().toISOString(),notes:$('review-notes').value,kind:'review_comments_not_acceptance'};const url=URL.createObjectURL(new Blob([JSON.stringify(record,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='sciencegym-lab-review.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
try{
 [manifest,inventory,risks,report,bodyReport,readiness,allocation]=await Promise.all([read(folder+'scene.json'),read(folder+'inventory.json'),read(folder+'risk_register.json'),read(folder+'layout_checks.json'),read(root+'assets/unitree_g1_inspire_v1/space.json'),read(folder+'readiness.json'),read(folder+'campaign_allocation.json')]);
 if(report.scene_sha256!==fetchedHashes.get(folder+'scene.json')||inventory.scene_artifact.sha256!==report.scene_sha256)throw Error('场景版本与几何检查 / 清单记录不一致，请重新生成检查');
 for(const p of readiness.source_artifacts){const url=root+p.path;if(fetchedHashes.has(url)&&fetchedHashes.get(url)!==p.sha256)throw Error('进度记录与场景版本不一致')}
 for(const p of allocation.source_artifacts){const url=root+p.path;if(fetchedHashes.has(url)&&fetchedHashes.get(url)!==p.sha256)throw Error('物品分配与场景版本不一致')}
 const policy=await read(folder+'pilot_contract.json');if(fetchedHashes.get(folder+'pilot_contract.json')!==manifest.pilot_contract.sha256||JSON.stringify(policy)!==JSON.stringify(readiness.policy))throw Error('执行约束版本不一致');
 $('pilot-policy').textContent='本体限定宇树，手型按公开资源选择；当前选型：'+policy.robot.body_candidate+' + '+policy.robot.hands.join(' / ')+'。传感器闭环，仅增加相机和普通工具。资产场景验收后再开发操作序列。场景已使用 G1 和官方 Inspire FTP 双手；仅静态资产集成，操作与动态平衡尚待验证。';
 const rc=readiness.counts;$('pilot-counts').textContent=rc.manual_definitions+' 个操作定义已对应到 '+rc.interfaces+' 类接口与资源需求。当前 '+rc.active_requirement_groups+' 类资源拆出 '+rc.active_component_requirements+' 个待核对组件需求，数量尚未分配完毕。另保留 '+rc.historical_requirement_groups+' 类历史选型供查阅。完整人形机器人分支通过 '+rc.qualified_humanoid_branches+' / '+rc.branches+'。';
 for(const item of readiness.hard_dependencies){const d=document.createElement('div');d.className='risk-card';const h=document.createElement('h3');h.textContent=item.label;const p=document.createElement('p');p.textContent=item.detail;d.append(h,p);$('pilot-dependencies').append(d)}
 for(const branch of readiness.branches){const tr=document.createElement('tr');for(const label of [branch.id+' · '+branch.title,branch.manual_step_ids.length+' 项（含共享步骤）','待执行验证']){const td=document.createElement('td');td.textContent=label;tr.append(td)}$('branch-progress').append(tr)}
 $('legacy-conflicts').textContent='以下旧接口仍需按普通工具约束重新绑定：'+readiness.legacy_interface_review.map(x=>x.interface_id).join('、')+'。历史 Panda 配置及读取真值的身体测试不计入本次传感器闭环验收。';
 if(manifest.envelope.body_evidence.sha256!==fetchedHashes.get(root+'assets/unitree_g1_inspire_v1/space.json'))throw Error('G1 空间测量记录与场景版本不一致');
 const handBound=await read(root+manifest.envelope.hand_evidence.path);if(fetchedHashes.get(root+manifest.envelope.hand_evidence.path)!==manifest.envelope.hand_evidence.sha256)throw Error('重建手空间记录版本不一致');
 $('body-envelope').textContent='G1 官方模型：'+bodyReport.samples+' 个限定通行姿态样本，双手按官方关节链计算全角度半径。当前静态检查半径 '+manifest.envelope.transit_radius_m.toFixed(2)+' m，另加 0.10 m 通道余量。工位检查见下表；相机、实际携物、行走和制动仍待验证。';
 installRoomLights();
 assetList.push(...manifest.assets);$('asset-count').textContent=assetList.length;
 const active=inventory.items.filter(i=>i.requirement_role!=='superseded_embodiment_reference'),present=active.filter(i=>i.scene_instances?.length||i.authored_scene_components?.length).length;$('inventory-coverage').textContent='部分几何 '+present+'/'+active.length+' 项；'+(active.length-present)+' 项尚无几何；历史选型 '+(inventory.items.length-active.length)+' 项';
 // GLTFLoader sanitizes names containing dots; preserve the original identifiers
 // used by the independently checked state manifest.
 let repairedNormals=0;
 const prepare=model=>model.scene.traverse(node=>{const association=model.parser.associations.get(node);const original=association?.nodes===undefined?null:model.parser.json.nodes[association.nodes]?.name;if(original)node.name=original;if(node.isMesh){
   // Trimesh exports can omit NORMAL. GLTFLoader's flat shading masks that
   // omission visually, but a normal-bias shadow coordinate can become invalid.
   // Expand only absent-normal meshes; face positions and source bytes stay intact.
   if(!node.geometry.attributes.normal){if(node.geometry.index)node.geometry=node.geometry.toNonIndexed();node.geometry.computeVertexNormals();repairedNormals++}
   for(const m of (Array.isArray(node.material)?node.material:[node.material])){
    for(const map of [m.map,m.normalMap,m.roughnessMap,m.metalnessMap])if(map)map.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());
   }
   node.castShadow=true;node.receiveShadow=true
  }});
 const built=await loadPinned(manifest.architecture.path,manifest.architecture.sha256);prepare(built);architecture=built.scene;
 const architectureParts=new Map(manifest.architecture.part_records.map(p=>[p.id,p]));
 architecture.traverse(node=>{if(!node.isMesh)return;const part=architectureParts.get(node.name);node.userData.cutaway=part&&(['wall_upper','window','ceiling','ceiling_fixture','identification_label'].includes(part.role)||node.name.startsWith('door_'));if(node.material?.transparent)node.castShadow=false});
 renderBatches.push({id:'architecture',...batchStaticMeshes(architecture)});
 scene.add(architecture);visibility();
 for(let i=0;i<assetList.length;i+=3){await Promise.all(assetList.slice(i,i+3).map(async a=>{const model=await loadPinned(a.geometry,a.geometry_sha256);prepare(model);const group=model.scene;const protectedParts=new Set(a.id==='g1'?a.part_names:manifest.inspection_states.filter(s=>s.asset===a.id).flatMap(s=>s.parts));renderBatches.push({id:a.id,...batchStaticMeshes(group,protectedParts)});group.position.set(...a.position_m);group.traverse(o=>{if(o.isMesh)o.userData.assetId=a.id});groups.set(a.id,group);scene.add(group);const option=document.createElement('option');option.value=a.id;option.textContent=a.label;$('asset-select').append(option)}));$('loading').textContent='载入模型 '+Math.min(i+3,assetList.length)+' / '+assetList.length}
 for(const config of manifest.inspection_states){const group=groups.get(config.asset),asset=assetList.find(a=>a.id===config.asset);const parts=[];group.traverse(node=>{if(config.parts.includes(node.name))parts.push({node,position:node.position.clone(),quaternion:node.quaternion.clone()})});if(parts.length!==config.parts.length)throw Error(config.id+' 的开闭部件未完整匹配');const p=config.pivot_m||[0,0,0];const n=asset.normalization_matrix;states.set(config.id,{config,parts,normalization:n,pivot:new THREE.Vector3(p[0]+n[0][3],p[1]+n[1][3],p[2]+n[2][3])})}
 groups.get('g1').traverse(node=>{if(node.isMesh)robotRest.push({node,position:node.position.clone(),quaternion:node.quaternion.clone()})});
 sensorRig=await read(root+manifest.sensor_rig.path);if(fetchedHashes.get(root+manifest.sensor_rig.path)!==manifest.sensor_rig.sha256)throw Error('相机候选版本不一致');
 const fit=await read(root+'assets/g1_sensor_rig_v1/fit_checks.json');if(fit.rig_sha256!==manifest.sensor_rig.sha256||!fit.checks_passed||fit.active_installation)throw Error('相机装配检查缺失或状态不一致');
 sensors=new SensorReview({renderer,scene,robot:groups.get('g1'),normalization:assetList.find(a=>a.id==='g1').normalization_matrix,rig:sensorRig,hiddenGroups:[overlays,labels,measurements,accessMarker],canvas:$('sensor-canvas'),status:$('sensor-status')});await sensors.load(loadPinned,prepare);
 const kin=states.get('g1_hands_inspection').config.kinematics;sensors.update(new Map(Object.entries(kin.bind_world).map(([n,t])=>[n,new THREE.Matrix4().fromArray(t.flat()).transpose()])));
 $('sensor-fit').textContent='G1 适配抱环保留官方相机臂，重新设计配合孔与螺栓耳座；原版保留为失败对照。刚性径向间隙 '+Math.min(...fit.collar_clearances.map(c=>c.rigid_bore_radial_clearance_m*1000)).toFixed(2)+' mm；'+fit.counts.surface_checks_with_intersections+' / '+fit.counts.surface_checks+' 项静态检查有机器人表面相交；'+fit.counts.workspace_poses_with_attachment_overlaps+' / '+fit.counts.workspace_poses+' 个工位存在外部冲突；'+fit.counts.workspace_poses_with_other_link_intersections+' 个姿态与其他机器人部件相交。相机螺钉伸入 3 mm（厂家上限 4 mm）。衬垫预紧、线缆与动态负载仍待完成。';
 $('show-sensor-rig').onchange=e=>{sensors.group.visible=e.target.checked;renderer.shadowMap.needsUpdate=true;requestRender()};
 $('sensor-mount-views').onclick=e=>{const side=e.target.dataset.wrist;if(!side)return;selectAsset('g1',false);$('show-sensor-rig').checked=true;sensors.group.visible=true;$('isolate').checked=true;visibility();groups.get('g1').updateWorldMatrix(true,false);const t=groups.get('g1').matrixWorld.clone().multiply(sensors.normalization).multiply(sensors.world.get(side+'_wrist_yaw_link')),p=new THREE.Vector3().setFromMatrixPosition(t),sign=side==='left'?1:-1;setView([p.x+.38,p.y+sign*.48,p.z+.28],[p.x+.07,p.y+sign*.055,p.z+.075]);document.documentElement.dataset.mountView=side;renderer.shadowMap.needsUpdate=true;requestRender()};
 $('sensor-buttons').onclick=e=>{const id=e.target.dataset.sensor;if(!id)return;try{sensors.capture(id);requestRender()}catch(error){$('sensor-status').textContent='生成失败：'+error.message;throw error}};
 $('depth-range').onchange=()=>{sensors.depthMaterial.uniforms.displayRange.value=Number($('depth-range').value);if(sensors.selected==='head_depth'){sensors.capture('head_depth');requestRender()}};
 $('sensor-download').onclick=()=>{if(!sensors.metadata)return;const a=document.createElement('a');a.download='sciencegym-'+sensors.selected+'-preview.png';a.href=$('sensor-canvas').toDataURL('image/png');a.click()};
 document.documentElement.dataset.sensorReviewLoaded='true';
 workspace=await read(folder+'workspace_checks.json');if(workspace.scene_sha256!==report.scene_sha256)throw Error('工位检查与场景版本不一致');
 $('workspace-counts').textContent=workspace.counts.targets+' 个检查点：'+workspace.counts.position_candidates+' 个位置候选，'+workspace.counts.needs_revision+' 个需要调整或进一步求解。位置候选尚未通过操作验收。';
 for(const target of workspace.targets){const tr=document.createElement('tr');for(const text of [target.id,target.result.position_candidate?'位置候选':'待解决',(target.result.position_error_m*1000).toFixed(1)+' mm',target.result.external_overlaps.length+' 处',target.result.self_contacts_checked?target.result.self_penetrations_over_0_5mm.length+' 对':'未检查']){const td=document.createElement('td');td.textContent=text;tr.append(td)}const td=document.createElement('td'),button=document.createElement('button');button.textContent='查看静态姿态';button.dataset.target=target.id;button.onclick=()=>inspectWorkspace(target);td.append(button);tr.append(td);$('workspace-targets').append(tr)}
 $('workspace-reset').onclick=resetStates;
 document.documentElement.dataset.normalRepairs=repairedNormals;
 document.documentElement.dataset.renderBatches=JSON.stringify(renderBatches);
 document.documentElement.dataset.geometryPreserved=String(renderBatches.every(b=>b.sourceGeometryPreserved));
 buildOverlays();visibility();renderInventory();
 for(const c of report.routes){const tr=document.createElement('tr');for(const text of [c.label,c.declared_width_m.toFixed(1)+' m',c.provisional_transit_clear&&c.declared_corridor_clear?'几何通过':'存在冲突']){const td=document.createElement('td');td.textContent=text;tr.append(td)}$('route-table').append(tr)}
 for(const risk of risks.items){const d=document.createElement('div');d.className='risk-card';const h=document.createElement('h3');h.textContent=risk.title;const status=document.createElement('strong');status.textContent=risk.status_label;const current=document.createElement('p');current.textContent=risk.current_design;const missing=document.createElement('p');missing.textContent='待完成：'+risk.remaining;d.append(h,status,current,missing);$('risks').append(d)}
 $('loading').remove();$('layout-status').textContent=report.passed?'范围内通过':'需修正';document.documentElement.dataset.sceneLoaded='true';document.documentElement.dataset.assetCount=assetList.length;document.documentElement.dataset.meshCount=renderer.info.render.calls;
}catch(error){$('error').textContent='场景加载失败：'+error.message;$('loading').textContent='加载失败，见页面底部说明';$('layout-status').textContent='未通过版本核对';console.error(error)}
