import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

const $=id=>document.getElementById(id),root='../../',folder=root+'assets/cooling_lab_v1/';
const hashes=new Map();
async function bytes(path){const response=await fetch(path);if(!response.ok)throw Error(path+': '+response.status);const data=await response.arrayBuffer();hashes.set(path,Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',data)),x=>x.toString(16).padStart(2,'0')).join(''));return data}
async function json(path){return JSON.parse(new TextDecoder().decode(await bytes(path)))}
const scene=new THREE.Scene();scene.background=new THREE.Color('#d6e2e5');
const renderer=new THREE.WebGLRenderer({antialias:false,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(Math.max(devicePixelRatio,1.5),2));renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;
$('mount-viewport').append(renderer.domElement);
const camera=new THREE.PerspectiveCamera(38,1,.001,10);camera.up.set(0,0,1);
const controls=new OrbitControls(camera,renderer.domElement);controls.minDistance=.12;controls.maxDistance=2.8;
const pmrem=new THREE.PMREMGenerator(renderer),room=new RoomEnvironment();scene.environment=pmrem.fromScene(room,.04).texture;scene.environmentIntensity=.45;scene.environmentRotation.x=Math.PI/2;room.dispose();pmrem.dispose();
scene.add(new THREE.HemisphereLight(0xf3f6ff,0xb7baac,.85));const key=new THREE.DirectionalLight(0xfff9e8,2);key.position.set(1,-2,3);scene.add(key);
let pending=false;function render(){if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;renderer.render(scene,camera)})}controls.addEventListener('change',render);
new ResizeObserver(()=>{const w=$('mount-viewport').clientWidth,h=$('mount-viewport').clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();render()}).observe($('mount-viewport'));
const guides=new THREE.Group();scene.add(guides);
let model,report,instrument,factory,selected,assembly,config,meshes=new Map(),coverRest=new Map(),view='front';

async function load(ref,yUp=false){
 const path=root+ref.path,data=await bytes(path);if(hashes.get(path)!==ref.sha256)throw Error('模型版本不匹配：'+ref.path);
 const loaded=await new GLTFLoader().parseAsync(data,root),original=loaded.scene;
 original.traverse(o=>{const node=loaded.parser.associations.get(o)?.nodes;if(node!==undefined)o.name=loaded.parser.json.nodes[node].name||o.name});
 if(yUp)original.rotation.x=Math.PI/2;original.updateMatrixWorld(true);
 const flat=new THREE.Group();original.traverse(o=>{if(!o.isMesh)return;const mesh=new THREE.Mesh(o.geometry.clone().applyMatrix4(o.matrixWorld),o.material.clone());mesh.name=o.name;if(!mesh.geometry.attributes.normal)mesh.geometry.computeVertexNormals();flat.add(mesh)});return flat;
}
function line(points,color,dashed=false){const geometry=new THREE.BufferGeometry().setFromPoints(points.map(p=>new THREE.Vector3(...p)));const material=dashed?new THREE.LineDashedMaterial({color,dashSize:.006,gapSize:.004}):new THREE.LineBasicMaterial({color});const line=new THREE.Line(geometry,material);if(dashed)line.computeLineDistances();guides.add(line);return line}
function dispose(group){group.traverse(o=>{o.geometry?.dispose();if(o.material){for(const m of Array.isArray(o.material)?o.material:[o.material])m.dispose()}})}
function setView(name){view=name;const center=new THREE.Vector3(-.011,-.150,.175),directions={front:[.26,-.51,.29],back:[-.32,.48,.30],side:[.57,-.04,.14],top:[0,-.001,.67],overview:[.82,-1.1,.70]};if(name==='overview')center.set(0,0,.19);controls.target.copy(center);camera.position.copy(center).add(new THREE.Vector3(...directions[name]));camera.lookAt(center);controls.update();render()}
function update(){
 if(!config)return;const radians=-Number($('mount-cover').value)*Math.PI/180,lift=Number($('mount-lift').value)/1000;
 const pivot=new THREE.Vector3(...model.instrument_cover.pivot_m),rotation=new THREE.Matrix4().makeRotationAxis(new THREE.Vector3(...model.instrument_cover.axis),radians);
 const matrix=new THREE.Matrix4().makeTranslation(...pivot.toArray()).multiply(rotation).multiply(new THREE.Matrix4().makeTranslation(...pivot.clone().negate().toArray()));
 for(const [name,rest] of coverRest){const part=instrument.getObjectByName(name);part.matrix.copy(matrix).multiply(rest);part.matrixAutoUpdate=false}
 const cutaway=$('mount-cutaway').checked,coverNames=new Set(model.instrument_cover.parts);
 instrument.children.forEach(o=>{o.visible=!cutaway||coverNames.has(o.name)||['mount_socket_','detector_motors','auxiliary','sample_bay_purge'].some(p=>o.name.startsWith(p))||['sample_compartment_floor','sample_bay_rear_wall'].includes(o.name)});
 assembly.position.z=lift;guides.visible=$('mount-guides').checked;
 guides.children.forEach(o=>{if(o.userData.followsAccessory)o.position.z=lift});
 $('cover-angle').textContent=$('mount-cover').value+'°';$('lift-height').textContent=$('mount-lift').value+' mm';
 $('mount-status').textContent='几何检查视图 · '+(cutaway?'外壳已隐藏':'完整外壳')+' · 安装未验收';
 document.documentElement.dataset.mountCover=$('mount-cover').value;document.documentElement.dataset.mountLift=$('mount-lift').value;render();
}
async function select(identity){
 document.documentElement.dataset.mountLoaded='false';config=model.configurations.find(c=>c.id===identity);selected=report.configurations.find(c=>c.id===identity);
 const [accessory,hardware]=await Promise.all([load(config.accessory_geometry),load(config.hardware)]);
 if(assembly){scene.remove(assembly);dispose(assembly)}assembly=new THREE.Group();meshes=new Map();
 for(const o of [...accessory.children]){if(config.excluded_loose_parts.includes(o.name)){accessory.remove(o);dispose(o);continue}o.geometry.translate(...config.accessory_translation_m);meshes.set('accessory:'+o.name,o)}
 hardware.children.forEach(o=>meshes.set('hardware:'+o.name,o));assembly.add(accessory,hardware);scene.add(assembly);
 const bad=new Set(selected.closed_cover_penetration_pairs.flat());for(const [name,o] of meshes)if(bad.has(name)){o.material.color.set('#bb3728');o.material.emissive?.set('#310300')}
 for(const child of [...guides.children]){guides.remove(child);dispose(child)}
 const focus=model.datums.beam_focus_m;line([[-.15,focus[1],focus[2]],[.13,focus[1],focus[2]]],0x168a61);
 const [y,z]=config.accessory_input_ray_yz_m;line([[-.15,y,z],[.13,y,z]],0xd47620,true).userData.followsAccessory=true;
 const [cx,cy]=model.datums.factory_plate_center_xy_m,roof=model.datums.factory_plate_top_m+model.datums.cover_clearance_m;
 line([[cx-.103,cy-.126,roof],[cx+.103,cy-.126,roof],[cx+.103,cy+.126,roof],[cx-.103,cy+.126,roof],[cx-.103,cy-.126,roof]],0x3976bd,true);
 $('mount-finding').textContent=identity==='harrick_hrs'?'名义闭盖空间可容纳当前候选；推断的前折转镜光轴相差 60 mm。若整体平移去对齐，该模型会穿过样品舱后方结构，不能作为已兼容的安装配置。':'按当前推断尺寸与光轴高度安装后，最高部件超出名义舱盖净空约 16 mm，闭盖时发生相交。开盖可查看结构，但不代表可以这样运行仪器。';
 const mm=x=>(x*1000).toFixed(1)+' mm';const rows=[['底板上表面 / 光束高度',mm(model.datums.factory_plate_top_m)+' / '+mm(focus[2])],['附件底面 / 最高点',mm(config.accessory_translation_m[2])+' / '+mm(selected.highest_accessory_z_m)],['名义舱盖余量',mm(selected.nominal_roof_margin_m)],['候选光轴 Y / Z 偏差',selected.nominal_input_ray_offset_yz_m.map(mm).join(' / ')],['闭盖几何',selected.closed_cover_fit?'当前名义尺寸下无相交':'不通过'],['开盖后垂直装入采样',selected.insertion_geometry_clear?'25 个静态采样未发现相交':'发现相交，见原始记录'],['厂家安装兼容 / 操作验收','均未通过']];
 $('mount-metrics').replaceChildren(...rows.map(([label,value])=>{const row=document.createElement('tr'),th=document.createElement('th'),td=document.createElement('td');th.textContent=label;td.textContent=value;row.append(th,td);return row}));
 const blocked=selected.driver_access.filter(c=>!c.clear);$('mount-driver').textContent='附件固定螺钉的直线工具空间：'+(selected.driver_access.length-blocked.length)+' / '+selected.driver_access.length+' 处未发现相交。'+(blocked.length?'其余位置需要核对拆装顺序与真实壳体结构。':'手部方向、扭矩和接触尚未检查。');
 $('mount-conflicts').textContent=JSON.stringify({closed_cover:selected.closed_cover_penetration_pairs,open_instrument:selected.open_instrument_penetration_pairs,driver_access:blocked,limits:model.limits},null,2);
 $('mount-lift').value='0';$('mount-cover').value='90';update();setView(view);document.documentElement.dataset.mountAsset=identity;document.documentElement.dataset.mountLoaded='true';
}
function error(e){$('mount-error').textContent=String(e);document.documentElement.dataset.mountLoaded='error';console.error(e)}
async function init(){
 $('mount-select').disabled=true;
 [model,report]=await Promise.all([json(folder+'ftir_mounts.json'),json(folder+'ftir_mount_checks.json')]);
 const ref=report.source_artifacts.find(r=>r.path.endsWith('/ftir_mounts.json'));if(!ref||ref.sha256!==hashes.get(folder+'ftir_mounts.json'))throw Error('安装检查与模型版本不匹配');
 const sources=await json(folder+'ftir_mount_sources.json');const sourceRef=model.source_artifacts.find(r=>r.path.endsWith('/ftir_mount_sources.json'));if(sourceRef.sha256!==hashes.get(folder+'ftir_mount_sources.json'))throw Error('来源记录版本不匹配');
 for(const s of sources.sources){const a=document.createElement('a');a.href=s.url;a.textContent=s.document||s.id;a.target='_blank';a.rel='noopener';$('mount-sources').append(a)}
 [instrument,factory]=await Promise.all([load(model.instrument,true),load(model.factory_floor)]);scene.add(instrument,factory);
 for(const name of model.instrument_cover.parts){const o=instrument.getObjectByName(name);if(!o)throw Error('缺少舱盖零件 '+name);coverRest.set(name,o.matrix.clone())}
 $('mount-select').addEventListener('change',()=>{const selectBox=$('mount-select');selectBox.disabled=true;select(selectBox.value).catch(error).finally(()=>selectBox.disabled=false)});
 for(const id of ['mount-cover','mount-lift','mount-cutaway','mount-guides'])$(id).addEventListener('input',update);
 $('mount-views').addEventListener('click',e=>{if(e.target.dataset.view)setView(e.target.dataset.view)});await select($('mount-select').value);$('mount-select').disabled=false;
}
init().catch(error);
