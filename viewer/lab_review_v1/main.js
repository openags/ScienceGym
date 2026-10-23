import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

const $=id=>document.getElementById(id),root='../../',folder=root+'assets/cooling_lab_v1/';
const fetchedHashes=new Map();
const digest=async buffer=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',buffer)),x=>x.toString(16).padStart(2,'0')).join('');
const read=async p=>{const r=await fetch(p);if(!r.ok)throw Error(p+' HTTP '+r.status);const buffer=await r.arrayBuffer();fetchedHashes.set(p,await digest(buffer));return JSON.parse(new TextDecoder().decode(buffer))};
const scene=new THREE.Scene();scene.background=new THREE.Color('#c9dce4');
const camera=new THREE.PerspectiveCamera(42,1,.02,200);camera.up.set(0,0,1);
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;
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
for(const [x,y] of [[3,2],[9,2],[3,5],[9,5],[3,8],[9,8],[-3,2.5],[-3,7.5]]){
 const lamp=new THREE.PointLight(0xfff6e9,1.3,14,2);lamp.position.set(x,y,3.13);roomLights.add(lamp);
}
for(const [x,y] of [[4,3],[8,8]]){
 const lamp=new THREE.SpotLight(0xfffaf0,30,18,1.25,.75,2);lamp.position.set(x,y,3.16);lamp.target.position.set(x,y,0);lamp.castShadow=true;
 lamp.shadow.mapSize.set(1024,1024);lamp.shadow.bias=-.0003;lamp.shadow.normalBias=.006;lamp.shadow.camera.near=.1;
 roomLights.add(lamp,lamp.target);
}
const overlays=new THREE.Group(),labels=new THREE.Group(),measurements=new THREE.Group();scene.add(overlays,labels,measurements);
let architecture,manifest,inventory,risks,report,bodyReport,selected=null,measureMode=false,measurePoints=[],pointerStart;
const groups=new Map(),states=new Map(),assetList=[];
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
const views={all:[[19,-13,22],[3.1,9.5,0]],indoor:[[7.4,.7,1.65],[4.8,8.7,1.25],true],rear:[[6.9,9.3,1.65],[5.5,1.8,1.3],true],outdoor:[[16,7,12],[6,16,.4]],optics:[[7,6.9,1.65],[9.3,8.8,1.25],true],wet:[[5.4,4.1,1.65],[1.8,5.9,1.1],true],annex:[[-.9,1,1.65],[-4.4,3.5,1.35],true],coating:[[-1,5.8,1.65],[-4.4,8.5,1.4],true],top:[[3,9.5,32],[3,9.5,0]]};
setView(...views.indoor);document.documentElement.dataset.view='indoor';
const resize=()=>{const w=$('viewport').clientWidth,h=$('viewport').clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();requestRender()};new ResizeObserver(resize).observe($('viewport'));resize();
function resetStates(){for(const state of states.values())for(const item of state.parts){item.node.position.copy(item.position);item.node.quaternion.copy(item.quaternion)}renderer.shadowMap.needsUpdate=true;requestRender()}
function applyState(id,fraction){
 resetStates();const state=states.get(id);if(!state)return;
 const axis=new THREE.Vector3(...state.config.axis),angle=state.config.maximum*fraction,q=new THREE.Quaternion().setFromAxisAngle(axis,angle);
 for(const item of state.parts){
  if(state.config.kind==='slide')item.node.position.addScaledVector(axis,angle);
  else {item.node.position.sub(state.pivot).applyQuaternion(q).add(state.pivot);item.node.quaternion.premultiply(q)}
 }
 document.documentElement.dataset.openState=id+':'+fraction;
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
 detailRow('当前状态',asset.status);const size=asset.normalized_bounds_m[1].map((v,i)=>v-asset.normalized_bounds_m[0][i]);
 detailRow('模型包围尺寸（含已建附件）',size.map(v=>(v*1000).toFixed(1)+' mm').join(' × '));detailRow('物理比例 / 部件', '1 : 1 · '+asset.part_count+' 个部件');detailRow('工位',asset.station);
 if(asset.note)detailRow('待确认内容',asset.note);
 const a=document.createElement('a');a.href=root+(asset.sources||asset.source_artifact.path);a.target='_blank';a.textContent='查看模型来源与重构依据 ↗';$('asset-detail').append(a);
 if(manifest.reference_comparisons?.[id]){const ref=manifest.reference_comparisons[id];if(ref.dimensions_label)detailRow('厂家标注尺寸',ref.dimensions_label);detailRow('比对边界',ref.model_scope);for(const source of ref.sources){const link=document.createElement('a');link.href=source.url;link.target='_blank';link.rel='noopener';link.textContent=source.label+' ↗';if(source.scope)link.title=source.scope;$('asset-detail').append(link)}}
 resetStates();const state=[...states.values()].find(s=>s.config.asset===id);$('state-control').hidden=!state;$('state-slider').value=0;
 if(state){$('state-label').textContent=state.config.label;$('state-slider').oninput=()=>applyState(state.config.id,Number($('state-slider').value)/100)}
 if(focus){$('isolate').checked=true;const bounds=new THREE.Box3().setFromObject(groups.get(id));const c=bounds.getCenter(new THREE.Vector3());const extent=Math.max(...bounds.getSize(new THREE.Vector3()).toArray());setView([c.x+extent*1.2,c.y-extent*1.8,c.z+extent*1.3],c.toArray())}
 visibility();document.documentElement.dataset.selectedAsset=id;
}
function renderInventory(){
 const query=$('search').value.toLowerCase(),filter=$('filter').value;let count=0;$('inventory').replaceChildren();
 for(const item of inventory.items){const placed=assetList.filter(a=>a.resource_id===item.id),authored=item.authored_scene_components||[],hasGeometry=placed.length||authored.length;if(query&&!JSON.stringify(item).toLowerCase().includes(query))continue;if(filter==='placed'&&!hasGeometry||filter==='missing'&&hasGeometry)continue;
  const tr=document.createElement('tr');const first=document.createElement('td');
  if(placed.length){const b=document.createElement('button');b.textContent=item.label;b.onclick=()=>{selectAsset(placed[0].id);$('viewport').scrollIntoView({behavior:'smooth',block:'center'})};first.append(b)}else first.textContent=item.label;
  tr.append(first);const categories={equipment:'论文设备',tools:'工具与夹具',consumables:'材料与耗材',additional_reconstructed_materials:'补充材料/夹具',accessory:'独立附件',robot:'机器人',authored_facility_requirement:'实验室设施'};
  for(const text of [categories[item.category]||item.category,placed.length?'已放置 '+placed.length+' 个实例':authored.length?'已建部分设计几何（'+authored.length+' 组），待完整性审查':'尚未放入场景','待验收']){const td=document.createElement('td');td.textContent=text;tr.append(td)}$('inventory').append(tr);count++;
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
const storageKey='sciencegym-lab-review-notes-v1';try{$('review-notes').value=localStorage.getItem(storageKey)||''}catch{}
$('review-notes').oninput=()=>{try{localStorage.setItem(storageKey,$('review-notes').value);$('notes-status').textContent='已保存到此浏览器'}catch{$('notes-status').textContent='浏览器存储不可用，可下载保存'}};
$('export-notes').onclick=()=>{const record={scene_revision:report?.scene_sha256,created_at:new Date().toISOString(),notes:$('review-notes').value,kind:'review_comments_not_acceptance'};const url=URL.createObjectURL(new Blob([JSON.stringify(record,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='sciencegym-lab-review.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
try{
 [manifest,inventory,risks,report,bodyReport]=await Promise.all([read(folder+'scene.json'),read(folder+'inventory.json'),read(folder+'risk_register.json'),read(folder+'layout_checks.json'),read(folder+'body_envelope.json')]);
 if(report.scene_sha256!==fetchedHashes.get(folder+'scene.json')||inventory.scene_artifact.sha256!==report.scene_sha256)throw Error('场景版本与几何检查 / 清单记录不一致，请重新生成检查');
 if(manifest.envelope.body_evidence.sha256!==fetchedHashes.get(folder+'body_envelope.json'))throw Error('H2 空间测量记录与场景版本不一致');
 $('body-envelope').textContent='已有 H2 记录中：收臂姿态外接半径 '+bodyReport.standing.radial_extent_m.toFixed(3)+' m；'+bodyReport.samples+' 个姿态样本最大 '+bodyReport.maximum_sampled.radial_extent_m.toFixed(3)+' m。当前用 0.65 m 半径另加 0.10 m 设计余量检查通道。此结果不包含 Dex5-S Pro、携物和行走。';
 assetList.push(...manifest.assets);$('asset-count').textContent=assetList.length;
 const present=inventory.items.filter(i=>i.scene_instances?.length||i.authored_scene_components?.length).length;$('inventory-coverage').textContent='部分几何 '+present+'/'+inventory.items.length+' 项；其余 '+(inventory.items.length-present)+' 项尚缺';
 // GLTFLoader sanitizes names containing dots; preserve the original identifiers
 // used by the independently checked state manifest.
 const prepare=model=>model.scene.traverse(node=>{const association=model.parser.associations.get(node);const original=association?.nodes===undefined?null:model.parser.json.nodes[association.nodes]?.name;if(original)node.name=original;if(node.isMesh){node.castShadow=true;node.receiveShadow=true}});
 const built=await loadPinned(manifest.architecture.path,manifest.architecture.sha256);prepare(built);architecture=built.scene;
 const architectureParts=new Map(manifest.architecture.part_records.map(p=>[p.id,p]));
 architecture.traverse(node=>{if(!node.isMesh)return;const part=architectureParts.get(node.name);node.userData.cutaway=part&&(['wall_upper','window','ceiling','ceiling_fixture','identification_label'].includes(part.role)||node.name.startsWith('door_'));if(node.material?.transparent)node.castShadow=false});
 scene.add(architecture);visibility();
 for(let i=0;i<assetList.length;i+=3){await Promise.all(assetList.slice(i,i+3).map(async a=>{const model=await loadPinned(a.geometry,a.geometry_sha256);prepare(model);const group=model.scene;group.position.set(...a.position_m);group.traverse(o=>{if(o.isMesh)o.userData.assetId=a.id});groups.set(a.id,group);scene.add(group);const option=document.createElement('option');option.value=a.id;option.textContent=a.label;$('asset-select').append(option)}));$('loading').textContent='载入模型 '+Math.min(i+3,assetList.length)+' / '+assetList.length}
 for(const config of manifest.inspection_states){const group=groups.get(config.asset),asset=assetList.find(a=>a.id===config.asset);const parts=[];group.traverse(node=>{if(config.parts.includes(node.name))parts.push({node,position:node.position.clone(),quaternion:node.quaternion.clone()})});if(parts.length!==config.parts.length)throw Error(config.id+' 的开闭部件未完整匹配');const p=config.pivot_m||[0,0,0];const n=asset.normalization_matrix;states.set(config.id,{config,parts,pivot:new THREE.Vector3(p[0]+n[0][3],p[1]+n[1][3],p[2]+n[2][3])})}
 buildOverlays();visibility();renderInventory();
 for(const c of report.routes){const tr=document.createElement('tr');for(const text of [c.label,c.declared_width_m.toFixed(1)+' m',c.provisional_transit_clear&&c.declared_corridor_clear?'几何通过':'存在冲突']){const td=document.createElement('td');td.textContent=text;tr.append(td)}$('route-table').append(tr)}
 for(const risk of risks.items){const d=document.createElement('div');d.className='risk-card';const h=document.createElement('h3');h.textContent=risk.title;const status=document.createElement('strong');status.textContent=risk.status_label;const current=document.createElement('p');current.textContent=risk.current_design;const missing=document.createElement('p');missing.textContent='待完成：'+risk.remaining;d.append(h,status,current,missing);$('risks').append(d)}
 $('loading').remove();$('layout-status').textContent=report.passed?'范围内通过':'需修正';document.documentElement.dataset.sceneLoaded='true';document.documentElement.dataset.assetCount=assetList.length;document.documentElement.dataset.meshCount=renderer.info.render.calls;
}catch(error){$('error').textContent='场景加载失败：'+error.message;$('loading').textContent='加载失败，见页面底部说明';$('layout-status').textContent='未通过版本核对';console.error(error)}
