import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
const $=id=>document.getElementById(id),root='../../',folder='assets/cooling_lab_v1/',cache=new Map(),states={},tools=new Map(),rigs=new Map();
async function bytes(path){if(cache.has(path))return cache.get(path);const response=await fetch(root+path);if(!response.ok)throw Error('无法读取 '+path);const buffer=await response.arrayBuffer(),sha=[...new Uint8Array(await crypto.subtle.digest('SHA-256',buffer))].map(v=>v.toString(16).padStart(2,'0')).join('');const value={buffer,sha};cache.set(path,value);return value}
async function json(path){return JSON.parse(new TextDecoder().decode((await bytes(path)).buffer))}
async function verify(ref){const value=await bytes(ref.path);if(value.sha!==ref.sha256)throw Error('文件与检查版本不一致：'+ref.path);return value.buffer}
async function model(ref,offset=new THREE.Matrix4()){
 const source=await new GLTFLoader().parseAsync(await verify(ref),root),group=new THREE.Group(),parts=new Map();source.scene.updateMatrixWorld(true);
 source.scene.traverse(o=>{if(!o.isMesh)return;const index=source.parser.associations.get(o)?.nodes,name=source.parser.json.nodes[index]?.name||o.name,m=new THREE.Mesh(o.geometry.clone(),o.material.clone());m.name=name;m.matrix.multiplyMatrices(offset,o.matrixWorld);m.matrixAutoUpdate=false;m.castShadow=true;m.receiveShadow=true;parts.set(name,m);group.add(m)});
 if(ref.parts!==undefined&&parts.size!==ref.parts)throw Error('部件数量不一致：'+ref.path);return {group,parts};
}
let renderer,scene,camera,controls,light,robot,marker,storage,ground,remainders,view='oblique',radius=1,pending=false,selected;const centre=new THREE.Vector3();
const labels={tool_mount_1_nut_left:'下方左螺母工具',tool_mount_1_nut_right:'下方右螺母工具',tool_mount_2_nut_left:'上方左螺母工具',tool_mount_2_nut_right:'上方右螺母工具',tool_rs3_clamp:'辐射罩卡箍工具',logger_front:'记录器正面',logger_clasp_1:'记录器下卡扣',logger_clasp_2:'记录器上卡扣',temperature_coil_upper:'温湿度线圈上方扎带',wind_coil_upper:'风传感器线圈上方扎带',wind_mount:'风传感器安装部位',cutoffs_tray:'推车余料盘',plugs_tray:'推车零件盘',cart_handle:'推车把手',temporary_leg:'临时固定带 · 三脚架腿',temporary_brace:'临时固定带 · 撑杆',free_plug_tray:'低位网络插头盘'};
function render(){if(pending||!renderer)return;pending=true;requestAnimationFrame(()=>{pending=false;const d=camera.position.distanceTo(centre);camera.near=Math.max(.0001,d-radius*1.6);camera.far=d+radius*1.6;camera.updateProjectionMatrix();renderer.render(scene,camera)})}
function fit(){
 const state=states[$('workspace-context').value],box=new THREE.Box3();
 if($('workspace-whole').checked){box.setFromObject(state.model.group);if(storage.group.visible)box.union(new THREE.Box3().setFromObject(storage.group))}
 else {const p=new THREE.Vector3(...selected.point_m);box.set(p.clone().addScalar(-.35),p.clone().addScalar(.35))}
 if(robot.group.visible)box.union(new THREE.Box3().setFromObject(robot.group));box.getCenter(centre);radius=box.getSize(new THREE.Vector3()).length()/2;
 const direction={oblique:[1,-1,.65],front:[0,-1,.12],rear:[0,1,.12],top:[0,-.001,1]}[view],v=THREE.MathUtils.degToRad(camera.fov/2),h=Math.atan(Math.tan(v)*camera.aspect),distance=radius/Math.sin(Math.min(v,h))*1.08;
 controls.target.copy(centre);camera.position.copy(centre).addScaledVector(new THREE.Vector3(...direction).normalize(),distance);camera.lookAt(centre);controls.update();light.position.copy(centre).add(new THREE.Vector3(-3,-4,6));light.target.position.copy(centre);light.target.updateMatrixWorld();$('workspace-size').textContent='观察范围：'+box.getSize(new THREE.Vector3()).toArray().map(x=>x.toFixed(2)).join(' × ')+' m';render();
}
function update(){
 const key=$('workspace-context').value,state=states[key];selected=state.report.targets.find(t=>t.id===$('workspace-target').value);const result=selected.result,valid=result.position_candidate;
 for(const [id,s] of Object.entries(states))s.model.group.visible=id===key;storage.group.visible=key==='installed';remainders.group.visible=key==='installed';
 for(const [id,t] of tools)t.group.visible=key==='installed'&&id===selected.id;
 robot.group.visible=valid;
 if(valid){if(Object.keys(result.visual_transforms).length!==robot.parts.size)throw Error('完整机器人姿态缺失');for(const [name,mesh] of robot.parts){const transform=result.visual_transforms[name];if(!transform)throw Error('缺少机器人部件 '+name);mesh.matrix.set(...transform.flat());mesh.matrixWorldNeedsUpdate=true}}
 for(const [id,rig] of rigs){rig.group.visible=valid;if(valid){const matrix=result.rig_transforms[id];if(!matrix)throw Error('缺少腕部附件姿态 '+id);rig.group.matrix.set(...matrix.flat());rig.group.matrixAutoUpdate=false;rig.group.matrixWorldNeedsUpdate=true}}
 marker.position.set(...selected.point_m);marker.material.color.set(valid?0xe58b27:0xc93136);
 $('workspace-status').textContent=(key==='installed'?'最终安装参考':'低位桅杆局部检查')+' · '+labels[selected.id]+' · 未验收';
 $('workspace-result').textContent=valid?'找到静态位置候选；位置误差 '+(result.position_error_m*1000).toFixed(3)+' mm。双手、身体、腕部附件与当前设备的三角网格检查未见交叠。':'本次有限搜索未找到位置候选；保留候选的位置误差 '+(result.position_error_m*1000).toFixed(1)+' mm。失败结果保留，机器人不显示。';
 $('workspace-basis').textContent='检查点使用掌心空间预留，不代表已握住物件。姿态：'+(result.posture_id==='nominal_standing'?'名义站立':'静态屈膝')+'；搜索次数：'+selected.attempts+'。';fit();
}
function changeContext(){const state=states[$('workspace-context').value];$('workspace-target').replaceChildren();for(const t of state.report.targets){const option=document.createElement('option');option.value=t.id;option.textContent=labels[t.id]+' · '+(t.result.position_candidate?'候选':'待解决');$('workspace-target').append(option)}update()}
try{
 const station=await json(folder+'weather_station_assets.json'),prep=await json(folder+'weather_preparation_assets.json'),prepChecks=await json(folder+'weather_preparation_checks.json'),stored=await json(folder+'weather_storage_assets.json');
 const reports={installed:await json(folder+'weather_workspace_checks.json'),preparation:await json(folder+'weather_preparation_workspace_checks.json')};
 const groundRecord=await json(folder+'outdoor_ground_assets.json'),groundChecks=await json(folder+'outdoor_ground_checks.json');for(const ref of [...groundRecord.source_artifacts,...groundChecks.source_artifacts])await verify(ref);if(!groundChecks.passed)throw Error('候选室外地面版本不一致');
 const remainderRecord=await json(folder+'weather_remainders_assets.json'),remainderChecks=await json(folder+'weather_remainders_checks.json');for(const ref of [...remainderRecord.source_artifacts,...remainderChecks.source_artifacts])await verify(ref);if(!remainderChecks.passed||remainderChecks.existing_static_pose_witnesses.length!==reports.installed.counts.position_candidates)throw Error('新增余料的原姿态空间检查不完整');
 for(const record of [station,prep,prepChecks,stored,...Object.values(reports)])for(const ref of record.source_artifacts)await verify(ref);
 if(!prepChecks.passed||[station,prep,...Object.values(reports)].some(r=>r.owner_acceptance!==null||r.robot_use_qualified))throw Error('未验收状态不一致');
 for(const [key,record] of Object.entries({installed:station,preparation:prep})){const offset=key==='installed'?new THREE.Matrix4().makeTranslation(...station.station_origin_world_m.map(x=>-x)):new THREE.Matrix4();states[key]={report:reports[key],model:await model(record.geometry,offset)}}
 robot=await model(reports.installed.robot_geometry);storage=await model(stored.geometry);
 remainders=await model(remainderRecord.geometry);
 ground=await model(groundRecord.geometry,new THREE.Matrix4().makeTranslation(...station.station_origin_world_m.map(x=>-x)));
 for(const t of reports.installed.targets)if(t.tool_pose)tools.set(t.id,await model(t.tool_pose.tool_geometry,new THREE.Matrix4().set(...t.tool_pose.tool_to_station.flat())));
 const rig=await json('assets/g1_sensor_rig_v1/rig.json');for(const attachment of rig.attachments)rigs.set(attachment.id,await model({path:attachment.geometry_path,sha256:attachment.geometry_sha256}));
 renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(Math.max(devicePixelRatio,1.5),2));renderer.toneMapping=THREE.ACESFilmicToneMapping;$('lift-viewport').append(renderer.domElement);scene=new THREE.Scene();scene.background=new THREE.Color('#e0e6e5');
 for(const s of Object.values(states))scene.add(s.model.group);scene.add(robot.group,storage.group,ground.group,remainders.group);for(const m of [...tools.values(),...rigs.values()])scene.add(m.group);
 marker=new THREE.Mesh(new THREE.SphereGeometry(.015,24,16),new THREE.MeshStandardMaterial({color:0xe58b27}));scene.add(marker);camera=new THREE.PerspectiveCamera(38,1,.0001,100);camera.up.set(0,0,1);controls=new OrbitControls(camera,renderer.domElement);controls.minDistance=.05;controls.maxDistance=30;controls.addEventListener('change',render);
 const pmrem=new THREE.PMREMGenerator(renderer),room=new RoomEnvironment();scene.environment=pmrem.fromScene(room,.04).texture;scene.environmentIntensity=.6;scene.environmentRotation.x=Math.PI/2;room.dispose();pmrem.dispose();scene.add(new THREE.HemisphereLight(0xf3f6ff,0xb5b2a9,1));light=new THREE.DirectionalLight(0xfff9ef,2);scene.add(light,light.target);
 for(const el of document.querySelectorAll('.lift-controls select,.lift-controls button,.lift-controls input'))el.disabled=false;$('workspace-context').addEventListener('change',changeContext);$('workspace-target').addEventListener('change',update);$('workspace-whole').addEventListener('change',fit);$('workspace-views').addEventListener('click',e=>{const v=e.target.closest('button')?.dataset.view;if(v){view=v;fit()}});
 $('workspace-counts').textContent=Object.entries(reports).map(([key,r])=>(key==='installed'?'最终安装参考':'低位局部检查')+'：'+r.counts.targets+' 个检查点中，'+r.counts.position_candidates+' 个找到位置候选，'+r.counts.needs_revision+' 个仍待解决。').join(' ');
 changeContext();new ResizeObserver(()=>{renderer.setSize($('lift-viewport').clientWidth,$('lift-viewport').clientHeight);camera.aspect=$('lift-viewport').clientWidth/$('lift-viewport').clientHeight;fit()}).observe($('lift-viewport'));
 window.scienceGymWeatherWorkspace=()=>({context:$('workspace-context').value,target:selected.id,positionCandidate:selected.result.position_candidate,robotVisible:robot.group.visible,robotParts:robot.parts.size,groundParts:ground.parts.size,rigGroups:[...rigs.values()].filter(m=>m.group.visible).length,contextParts:states[$('workspace-context').value].model.parts.size,storageVisible:storage.group.visible,remainderParts:remainders.parts.size,remaindersVisible:remainders.group.visible,toolsVisible:[...tools.values()].filter(m=>m.group.visible).length,robotTransforms:robot.group.visible?Object.fromEntries([...robot.parts].map(([n,m])=>[n,m.matrix.clone().transpose().elements])):{},rigTransforms:robot.group.visible?Object.fromEntries([...rigs].map(([n,m])=>[n,m.group.matrix.clone().transpose().elements])):{},fullWorkspaceQualified:false,robotUseQualified:false});document.documentElement.dataset.workspaceLoaded='true';
}catch(error){renderer?.dispose();$('lift-viewport').replaceChildren();$('lift-error').textContent=String(error);$('workspace-status').textContent='版本与检查不一致，暂不显示。';document.documentElement.dataset.workspaceLoaded='error'}
