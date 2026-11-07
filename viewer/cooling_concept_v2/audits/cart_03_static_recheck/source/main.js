import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {HandIK} from './hand_ik.js';
import {batchStaticMeshes} from '../lab_review_v1/render_batches.js';
const root='../../',read=async p=>{const r=await fetch(root+p);if(!r.ok)throw Error(p);return r.json()},$=id=>document.getElementById(id);
const clean=new URLSearchParams(location.search).has('clean');if(clean)document.body.classList.add('clean');
const scene=new THREE.Scene();scene.background=new THREE.Color('#bacdd5');const camera=new THREE.PerspectiveCamera(48,innerWidth/innerHeight,.025,120);camera.up.set(0,0,1);
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setSize(innerWidth,innerHeight);renderer.setPixelRatio(1);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.0;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;$('stage').prepend(renderer.domElement);
const pmrem=new THREE.PMREMGenerator(renderer);scene.environment=pmrem.fromScene(new RoomEnvironment(),.04).texture;scene.environmentIntensity=.4;scene.environmentRotation.x=Math.PI/2;
const hemi=new THREE.HemisphereLight(0xeaf6ff,0xa0a390,.75);hemi.position.set(0,0,10);scene.add(hemi);
const sun=new THREE.DirectionalLight(0xfff4df,2.5);sun.position.set(5,13,18);sun.target.position.set(5,13,0);sun.castShadow=true;Object.assign(sun.shadow.camera,{left:-13,right:13,top:14,bottom:-14,near:1,far:40});sun.shadow.mapSize.set(2048,2048);sun.shadow.normalBias=.005;scene.add(sun,sun.target);
const fill=new THREE.DirectionalLight(0xe4efff,.5);fill.position.set(4,1,3);scene.add(fill);
const localKey=new THREE.SpotLight(0xfff8ea,38,10,1.0,.8,2);localKey.castShadow=true;localKey.shadow.mapSize.set(1024,1024);localKey.shadow.normalBias=.003;localKey.shadow.bias=-.0001;scene.add(localKey,localKey.target);
const loader=new GLTFLoader(),groups=new Map(),sourceHashes={},nodeRest=[],robotParts=[];let manifest,kin,poses,architecture,robotFrames,witness,handIK,graspProfile;let contactDiagnostics=[];const extraMeshes=new Map();
const V=p=>new THREE.Vector3(...p),M=a=>new THREE.Matrix4().fromArray(a.flat()).transpose();const clamp=THREE.MathUtils.clamp,smooth=t=>{t=clamp(t,0,1);return t*t*(3-2*t)},mix=(a,b,t)=>a+(b-a)*t,angle=(a,b,t)=>a+Math.atan2(Math.sin(b-a),Math.cos(b-a))*t;
function prepare(model){model.scene.traverse(n=>{const a=model.parser.associations.get(n);if(a?.nodes!==undefined)n.name=model.parser.json.nodes[a.nodes]?.name||n.name;if(n.isMesh){if(!n.geometry.attributes.normal){if(n.geometry.index)n.geometry=n.geometry.toNonIndexed();n.geometry.computeVertexNormals()}n.castShadow=!n.material.transparent;n.receiveShadow=true;}});}
async function load(path,hash){const r=await fetch(root+path);const b=await r.arrayBuffer();const actual=[...new Uint8Array(await crypto.subtle.digest('SHA-256',b))].map(x=>x.toString(16).padStart(2,'0')).join('');if(actual!==hash)throw Error('Source geometry changed: '+path);sourceHashes[path]=hash;const g=await loader.parseAsync(b,new URL(root+path,location.href).href);prepare(g);return g.scene;}
const phases=[];let end=0,last=[6,1.25],lastYaw=Math.PI/2;
function work(id,title,detail,duration,action,refs=[]){const p={id,title,detail,duration,action,kind:'work',start:end,end:end+duration,position:[...last],yaw:lastYaw,refs};phases.push(p);end=p.end;return p;}
function move(id,title,points,yaw,mode='rest'){const points3=[V([...last,0]),...points.map(p=>V([...p,0]))];const curve=new THREE.CatmullRomCurve3(points3,false,'centripetal');const length=curve.getLength(),duration=length/.62+1.4;const p={id,title,detail:mode==='push'?'沿主通道转运白／黑装置和采集设备':'在同一实验室中转移至下一工位',kind:'move',start:end,end:end+duration,duration,curve,length,fromYaw:lastYaw,yaw,mode,refs:['MOVE.02','MOVE.04']};phases.push(p);last=[...points.at(-1)];lastYaw=yaw;end=p.end;return p;}
const intro=work('intro','论文实验准备','Bhatia et al. · 定向辐射冷却实验',6,'intro');
move('to_bath','前往温度校准工位',[[6,4.4],[3.8,4.5],[2.9,5.12]],Math.PI/2);
const cal=work('calibration','校准温度探头','水浴、参考 RTD 与热电偶通道比对',21,'bath',['CAL_MOUNT','CAL_ACQUIRE']);
move('to_reference','核对参考温度读数',[[2.1,4.65],[.8,5.12]],Math.PI/2);
work('reference','核对参考与通道','检查参考 RTD 和已分配探头身份',10,'panel',['CAL_MOUNT','CAL_ACQUIRE']);
move('to_cary','转移至光学测量工位',[[2.1,4.6],[4.4,4.6],[4.4,7.3],[2.65,7.8]],Math.PI/2);
const cary=work('solar','太阳波段光学测量','先参考、再装样、闭盖扫描与取样',23,'cary',['OPT_REFERENCE','OPT_MOUNT','OPT_SCAN','OPT_UNLOAD']);
move('to_ftir','转移至红外光谱工位',[[6,7.25],[9.19,7.8]],Math.PI/2);
const ftir=work('infrared','红外光学测量','参考与样品依次装夹，完成红外扫描',23,'ftir',['OPT_REFERENCE','OPT_MOUNT','OPT_SCAN','OPT_UNLOAD']);
move('to_white','前往白色装置装配台',[[7.5,7.2],[6,4.2],[6,1.95],[4.5,1.95],[3.65,2.19]],Math.PI/2);
const assembleWhite=work('assemble_white','白色装置检查与探头安装','检查双层纳米 PE 膜，安装探头并复位屏蔽与反射部件',27,'assemble_white',['BASE','EMITTER','FILM','SHIELD','REFLECTOR','TC_ATTACH']);
move('to_black','前往黑色对照装置工位',[[4.5,1.95],[6.4,1.95],[9.55,2.19]],Math.PI/2);
const assembleBlack=work('assemble_black','黑色对照装置检查与探头安装','保持装置结构一致，区分白／黑发射体身份',25,'assemble_black',['BASE','EMITTER','FILM','SHIELD','REFLECTOR','TC_ATTACH']);
move('to_wiring','准备采集与转运',[[7.4,1.95],[6.3,1.95],[4.905,1.78]],-Math.PI/2);
const wiring=work('wiring','连接探头与采集通道','输出关闭状态下接线、检查极性与线缆固定',18,'wiring',['TC_ATTACH','SYNC','STOP_SAFE']);
move('to_pick_white','装载白色装置',[[4.6,1.95],[4.25,1.95],[3.65,2.19]],Math.PI/2);
const pickWhite=work('pick_white','双手托持白色装置','从结构底座承托，避开薄膜和光学表面',8,'pick',['MOVE.02']);
move('carry_white','将白色装置放上小车',[[3.65,1.8],[4.4,1.95],[4.70,1.71]],-Math.PI/2,'carry');
const placeWhite=work('place_white','白色装置入车','放稳后松手',10,'place',['MOVE.04']);
move('to_pick_black','装载黑色对照装置',[[4.70,1.95],[6.3,1.95],[9.55,2.19]],Math.PI/2);
const pickBlack=work('pick_black','双手托持黑色装置','保持白／黑样机身份独立',8,'pick',['MOVE.02']);
move('carry_black','将黑色装置放上小车',[[9.55,1.8],[6.3,1.95],[5.30,1.71]],-Math.PI/2,'carry');
const placeBlack=work('place_black','黑色装置入车','保持装置间距与采集设备空间',10,'place',['MOVE.04']);
move('grasp_cart','握住小车把手',[[5.6,1.95],[6.25,1.9],[6.25,1.25],[6.03,1.25]],Math.PI);
work('take_cart_handle','双手握住小车把手','准备转运',5,'push_grip',['MOVE.02']);
const pushTurn=move('turn_cart','转向主通道',[[5.7,1.25],[5.4,1.65],[5.5,2.6],[6,3.7]],Math.PI/2,'push');
const pushOutdoor=move('outdoor_transfer','把实验装置运至室外',[[6,5.2],[6,8.8],[6,11.6],[6,13.27]],Math.PI/2,'push');
work('release_cart_handle','停稳小车','松开把手，准备卸载',5,'push_release',['MOVE.04']);
move('approach_black_cart','卸下黑色对照装置',[[6.75,13.4],[6.47,14.00]],Math.PI);
const unloadBlack=work('unload_black','从小车取出黑色装置','双手支持底座',8,'pick',['SITE_SETUP']);
move('carry_black_out','布置黑色对照装置',[[8,14.2],[9.5,15.12]],Math.PI/2,'carry');
const installBlack=work('install_black','黑色装置就位','放置在独立室外支撑台上',10,'place',['SITE_SETUP']);
move('approach_white_cart','卸下白色冷却装置',[[9.5,14.3],[7.2,14.5],[6.47,14.60]],Math.PI);
const unloadWhite=work('unload_white','从小车取出白色装置','双手支持底座',8,'pick',['SITE_SETUP']);
move('carry_white_out','布置白色冷却装置',[[6.9,14.60],[6.9,13.35],[4.5,13.35],[3.4,14.3],[2.5,15.12]],Math.PI/2,'carry');
const installWhite=work('install_white','白色装置就位','确认装置朝向与探头线缆',10,'place',['SITE_SETUP']);
move('to_logger','连接室外采集通道',[[4.3,13.3],[6.9,13.3],[6.55,14.4]],Math.PI);
const outdoorConnect=work('outdoor_connect','检查延长线与采集','连接已标识探头、固定线缆并开始同步记录',16,'wiring',['SITE_SETUP','ENV_SETUP','SYNC']);
const baseline=work('baseline','遮盖基线','两只铝盖保持闭合；论文基线为五分钟，此处压缩展示等待',7,'wait',['LID_BASELINE']);
move('to_white_lid','移除白色装置铝盖',[[6.9,13.3],[4.3,13.3],[3.6,14.3],[2.5,15.12]],Math.PI/2);
const openWhite=work('open_white','移除白色装置铝盖','保留两层 PE 膜，把铝盖放到支撑台',14,'lid_white',['LID_REMOVE']);
const trackWhite=work('track_white','调整白色装置反射片','移动并锁定反射片，使其遮挡发射体处直射日光',11,'track_white',['TRACK_ADJUST']);
move('to_black_lid','移除黑色装置铝盖',[[4.5,13.3],[7.5,13.3],[9.5,15.12]],Math.PI/2);
const openBlack=work('open_black','移除黑色装置铝盖','将第二只铝盖放到独立位置',14,'lid_black',['LID_REMOVE']);
const trackBlack=work('track_black','调整黑色装置反射片','完成对照装置的遮阳调整',11,'track_black',['TRACK_ADJUST']);
move('leave_optical_region','离开光学测量区域',[[8.5,14.2],[6.9,14.4],[6.55,14.4]],Math.PI);
const acquire=work('acquire','记录白／黑装置温度','退出遮挡范围；展示采集过程，不生成实验结果',9,'wait',['TRACKED_STAGNATION']);
const stop=work('stop','停止采集并断开连接','确认输出关闭、保存记录，再处理线缆',12,'wiring',['STOP_SAFE','UNMOUNT']);
move('to_collect_black','收纳黑色装置',[[8,14.2],[9.5,15.12]],Math.PI/2);
const coverBlack=work('cover_black','盖回黑色装置铝盖','取回支撑台上的铝盖，盖好后再搬运',14,'cover_black',['UNMOUNT','RESET']);
const collectBlack=work('collect_black','收回黑色装置','保留薄膜与探头，承托底座',8,'pick',['UNMOUNT']);
move('return_black','黑色装置回到小车',[[8,14.2],[7.1,14.00],[6.47,14.00]],Math.PI,'carry');
const stowBlack=work('stow_black','收纳黑色装置','放稳在原分配位置',10,'place',['RESET']);
move('to_collect_white','收纳白色装置',[[6.9,13.3],[4.2,13.3],[2.5,15.12]],Math.PI/2);
const coverWhite=work('cover_white','盖回白色装置铝盖','取回铝盖并保护发射孔，随后收纳装置',14,'cover_white',['UNMOUNT','RESET']);
const collectWhite=work('collect_white','收回白色装置','保持器件身份与完整结构',8,'pick',['UNMOUNT']);
move('return_white','白色装置回到小车',[[3.6,14.3],[4.3,13.3],[6.9,13.3],[6.9,14.60],[6.47,14.60]],Math.PI,'carry');
const stowWhite=work('stow_white','收纳白色装置','把装置放回小车并检查台面',10,'place',['RESET']);
move('finish_position','完成实验后的收纳',[[7.1,14.60],[7.2,13.3]],Math.PI/4);
const finish=work('finish','实验流程完成','白／黑装置、探头和记录保持对应',7,'finish',['ARCHIVE','RESET']);
function phaseAt(t){return phases.find(p=>t<p.end)||phases.at(-1)}
function robotAt(t){const p=phaseAt(clamp(t,0,end)),u=clamp((t-p.start)/p.duration,0,1);if(p.kind==='work')return {p,time:t,position:V([...p.position,0]),yaw:p.yaw,u,distance:0};const ramp=Math.min(1,p.duration/3),v=p.length/(p.duration-ramp);const elapsed=u*p.duration;let dist=elapsed<ramp?v*elapsed*elapsed/(2*ramp):elapsed>p.duration-ramp?p.length-v*(p.duration-elapsed)**2/(2*ramp):v*(elapsed-ramp/2);const a=clamp(dist/p.length,0,1),position=p.curve.getPointAt(a),tangent=p.curve.getTangentAt(a);let yaw=Math.atan2(tangent.y,tangent.x);yaw=angle(p.fromYaw,yaw,smooth(elapsed/1.2));yaw=angle(yaw,p.yaw,smooth((elapsed-(p.duration-1.2))/1.2));return {p,time:t,position,yaw,u,distance:dist};}
function cartAt(t){if(t<pushTurn.start)return {position:V([5,1.25,0]),yaw:0};const r=robotAt(Math.min(t,pushOutdoor.end-.000001));return {position:r.position.clone().add(V([Math.cos(r.yaw)*1.03,Math.sin(r.yaw)*1.03,0])),yaw:r.yaw+Math.PI};}
function slot(t,which){const c=cartAt(t);return {position:c.position.clone().add(V([which==='white'?-.30:.30,0,.859]).applyAxisAngle(V([0,0,1]),c.yaw)),yaw:c.yaw+Math.PI};}
const initialWhite={position:V([3.65,2.60,.9]),yaw:0},initialBlack={position:V([9.55,2.60,.9]),yaw:0};
const outsideWhite={position:V([2.5,15.55,.9]),yaw:0},outsideBlack={position:V([9.5,15.55,.9]),yaw:0};
function held(t){const r=robotAt(t);return {position:r.position.clone().add(V([.40,0,.94]).applyAxisAngle(V([0,0,1]),r.yaw)),yaw:r.yaw-Math.PI/2};}
function blendPose(a,b,u){return {position:a.position.clone().lerp(b.position,smooth(u)),yaw:angle(a.yaw,b.yaw,smooth(u))};}
function payload(t,which){let state=which==='white'?initialWhite:initialBlack;const legs=which==='white'?[[pickWhite,placeWhite,v=>slot(v,'white')],[unloadWhite,installWhite,()=>outsideWhite],[collectWhite,stowWhite,v=>slot(v,'white')]]:[[pickBlack,placeBlack,v=>slot(v,'black')],[unloadBlack,installBlack,()=>outsideBlack],[collectBlack,stowBlack,v=>slot(v,'black')]];let current=()=>state;
 for(const [pick,place,dest] of legs){
  if(t<pick.start)return current(t);
  if(t<pick.end){const source=current(pick.start),raised={position:source.position.clone().add(V([0,0,.13])),yaw:source.yaw},elapsed=t-pick.start;if(elapsed<4)return source;if(elapsed<5.2)return blendPose(source,raised,(elapsed-4)/1.2);return blendPose(raised,held(t),(elapsed-5.2)/1.8);}
  if(t<place.start)return held(t);
  if(t<place.end){const target=dest(t),above={position:target.position.clone().add(V([0,0,.13])),yaw:target.yaw},elapsed=t-place.start;if(elapsed<2.5)return blendPose(held(place.start),above,elapsed/2.5);return blendPose(above,target,(elapsed-2.5)/2);}
  current=dest;
 }return current(t);}
function jointPose(r){let q={...poses.poses.rest,...poses.poses.stance};const p=r.p;let mode=p.kind==='move'?p.mode:({pick:'carry',place:'carry',wait:'rest',intro:'rest',finish:'rest'}[p.action]||'work');if(p.kind==='work'){if(p.action==='wiring')mode='low';if(p.action?.startsWith('lid_')||p.action?.startsWith('cover_'))mode='rest';if(['push_grip','push_release'].includes(p.action))mode='push';if(p.action==='bath')mode='inspect';if(['cary','ftir'].includes(p.action))mode=r.u<.12||(r.u>.65&&r.u<.77)?'lid':r.u>.4&&r.u<.65?'rest':'work';}let amount=p.kind==='move'?(mode==='rest'?0:1):Math.min(smooth((r.u*p.duration)/2),smooth(((1-r.u)*p.duration)/2));if(p.action==='push_grip')amount=smooth(r.u*p.duration/2);if(p.action==='push_release')amount=1-smooth(r.u*p.duration/2);if(['pick','place'].includes(p.action))amount=p.action==='pick'?smooth(r.u*3):1-smooth((r.u-.75)*4);if(mode!=='rest'){const target=poses.poses[mode]||poses.poses.work;for(const [n,v] of Object.entries(target))q[n]=mix(q[n]||0,v,amount);}
 const speed=p.kind==='move'?Math.min(1,r.u*p.duration,(1-r.u)*p.duration):0;let cycle=(r.distance/.55)%1;const i=cycle*64,j=Math.floor(i),a=i-j;for(const [n,v] of Object.entries(poses.gait[j]||poses.gait[0]))q[n]=mix(poses.poses.stance[n],mix(v,poses.gait[Math.min(64,j+1)][n],a),speed);
 if(mode==='rest'&&p.kind==='move'){q.left_shoulder_pitch_joint=.45+.08*Math.sin(cycle*2*Math.PI)*speed;q.right_shoulder_pitch_joint=.45-.08*Math.sin(cycle*2*Math.PI)*speed;}
 for(const side of ['left','right'])for(const name of ['index','middle','ring','little'])q[side+'_'+name+'_1_joint']=(mode==='push'?.7:mode==='carry'?.35:.22)*amount;
 return q;
}
function groundedRootZ(q){
 const world=handIK.forward(q).world;let minimum=Infinity;
 for(const [name,vertices]of Object.entries(poses.sole_vertices_m)){
  const a=world.get(name).elements;
  for(const p of vertices)minimum=Math.min(minimum,a[2]*p[0]+a[6]*p[1]+a[10]*p[2]+a[14]);
 }
 return -minimum;
}
function constrainHands(r,q){
 const p=r.p,t=r.time,elapsed=t-p.start,handling=p.mode==='carry'||['pick','place'].includes(p.action),pushing=p.mode==='push'||['push_grip','push_release'].includes(p.action);
 r.rootZ=groundedRootZ(q);contactDiagnostics=[];if(!handling&&!pushing)return constrainTaskHands(r,q);
 Object.assign(q,poses.poses[handling?'carry':'push']);if(handling)q.waist_pitch_joint=.15;
 if(['pick','place'].includes(p.action)){
  const which=p.id.includes('white')?'white':'black',height=payload(t,which).position.z-payload(p.action==='pick'?p.start:p.end,which).position.z;
  q.waist_pitch_joint=.15+.20*(1-smooth((height-.005)/.08))*(p.action==='pick'?1-smooth((elapsed-5.2)/1.8):smooth(elapsed/2.5));
 }
 const rootMatrix=new THREE.Matrix4().makeRotationZ(r.yaw).setPosition(r.position.x,r.position.y,r.rootZ),inverse=rootMatrix.clone().invert();
 const restQ={...q};for(const side of ['left','right'])for(const joint of handIK.arm[side])restQ[joint.name]=poses.poses.rest[joint.name]||0;
 const rest=handIK.forward(restQ);
 for(const side of ['left','right']){
  let point,normal,forward,grip=.35,identity;
  if(handling){
   const which=p.id.includes('white')?'white':'black',object=payload(t,which),sign=side==='left'?-1:1;
   const rotation=new THREE.Matrix4().makeRotationZ(object.yaw);identity='cooler_'+which;
   grip=graspProfile.left.finger_angle_rad;point=V([sign*Math.abs(graspProfile.left.palm_x_m),graspProfile.left.palm_y_m,.135]).applyMatrix4(rotation).add(object.position);
   normal=V([-sign,0,0]).transformDirection(rotation);forward=V([0,1,0]).transformDirection(rotation);
  }else{
   const cart=cartAt(t),rotation=new THREE.Matrix4().makeRotationZ(cart.yaw);identity='utility_cart';
   point=V([graspProfile.cart.palm_x_m,side==='left'?graspProfile.cart.palm_y_m:-graspProfile.cart.palm_y_m,graspProfile.cart.palm_z_m]).applyMatrix4(rotation).add(cart.position);
   forward=V([Math.cos(r.yaw),Math.sin(r.yaw),0]);normal=V([0,0,-1]);grip=graspProfile.cart.finger_angle_rad;
  }
  const contact=point.clone(),rotation=handIK.orientation(side,forward,normal);
  const restPose=rootMatrix.clone().multiply(rest.world.get(side+'_palm_force_sensor')),restPoint=new THREE.Vector3().setFromMatrixPosition(restPose);
  let orientationAmount=1,closed=1;
  if(p.action==='pick'){
   const lifted=restPoint.clone();lifted.z=Math.max(1.20,point.z+.08);
   const pregrasp=point.clone().addScaledVector(normal,-.10);
   if(elapsed<.8)point=restPoint.clone().lerp(lifted,smooth(elapsed/.8));
   else if(elapsed<2)point=lifted.clone().lerp(pregrasp,smooth((elapsed-.8)/1.2));
   else if(elapsed<3.8)point=pregrasp.clone().lerp(contact,smooth((elapsed-2)/1.8));
   orientationAmount=smooth(elapsed/2);closed=smooth((elapsed-2)/1.8);
  }else if(p.action==='place'){
   closed=1-smooth((elapsed-5)/1.8);
   point.addScaledVector(normal,-.10*(1-closed));
  }else if(p.action==='push_grip'){
   orientationAmount=smooth(elapsed/2);closed=smooth((elapsed-2)/1.8);point.add(V([0,0,.08*(1-closed)]));if(elapsed<2)point=restPoint.clone().lerp(point,orientationAmount);
  }else if(p.action==='push_release'){
   closed=1-smooth(elapsed/1.8);point.add(V([0,0,.08*(1-closed)]));orientationAmount=1-smooth((elapsed-2)/2);point=restPoint.clone().lerp(point,orientationAmount);
  }
  let jointApproach=false,waypointError=null;
  if((p.action==='pick'&&elapsed<2)||(p.action==='place'&&elapsed>=6.8)){
   // Change orientation through feasible arm configurations before contact.
   // Cartesian quaternion interpolation can demand unreachable wrist poses.
   const localRotation=new THREE.Matrix4().makeRotationZ(-r.yaw).multiply(rotation);
   const safe=V([.32,side==='left'?.28:-.28,1.13]).applyMatrix4(rootMatrix);
   const pregrasp=contact.clone().addScaledVector(normal,-.10);
   const safeQ={...q,waist_pitch_joint:.15},preQ={...q,waist_pitch_joint:.35};restQ.waist_pitch_joint=0;const safeError=handIK.solve(safeQ,side,safe.clone().applyMatrix4(inverse),localRotation);
   const preError=handIK.solve(preQ,side,pregrasp.clone().applyMatrix4(inverse),localRotation);waypointError=Math.max(safeError,preError);
   const approachTime=p.action==='pick'?elapsed:2-clamp(elapsed-6.8,0,2);
   const from=approachTime<.8?restQ:safeQ,to=approachTime<.8?safeQ:preQ,amount=smooth(approachTime<.8?approachTime/.8:(approachTime-.8)/1.2);
   for(const joint of handIK.arm[side])q[joint.name]=mix(from[joint.name]||0,to[joint.name]||0,amount);
   q.waist_pitch_joint=mix(from.waist_pitch_joint||0,to.waist_pitch_joint||0,amount);
   const actual=rootMatrix.clone().multiply(handIK.forward(q).world.get(side+'_palm_force_sensor'));
   point=new THREE.Vector3().setFromMatrixPosition(actual);jointApproach=true;
  }
  if((p.action==='push_grip'&&elapsed<2)||(p.action==='push_release'&&elapsed>=2)){
   const preQ={...q},pregrasp=contact.clone().add(V([0,0,.08]));
   const localRotation=new THREE.Matrix4().makeRotationZ(-r.yaw).multiply(rotation);
   waypointError=handIK.solve(preQ,side,pregrasp.applyMatrix4(inverse),localRotation);
   const amount=smooth(p.action==='push_grip'?elapsed/2:1-(elapsed-2)/2);
   for(const joint of handIK.arm[side])q[joint.name]=mix(restQ[joint.name]||0,preQ[joint.name]||0,amount);
   point=new THREE.Vector3().setFromMatrixPosition(rootMatrix.clone().multiply(handIK.forward(q).world.get(side+'_palm_force_sensor')));jointApproach=true;
  }
  const desired=new THREE.Quaternion().setFromRotationMatrix(restPose).slerp(new THREE.Quaternion().setFromRotationMatrix(rotation),orientationAmount);
  const localRotation=new THREE.Matrix4().makeRotationZ(-r.yaw).multiply(new THREE.Matrix4().makeRotationFromQuaternion(desired));
  const error=jointApproach?null:handIK.solve(q,side,point.clone().applyMatrix4(inverse),localRotation);
  for(const name of ['index','middle','ring','little'])q[side+'_'+name+'_1_joint']=mix(0,grip,closed);
  if(handling){q[side+'_thumb_1_joint']=graspProfile.left.thumb_1_rad*(p.action==='pick'?smooth(elapsed/1.8):p.action==='place'?1-smooth((elapsed-6.8)/1.8):1);q[side+'_thumb_2_joint']=graspProfile.left.thumb_2_rad*closed;}else{q[side+'_thumb_1_joint']=graspProfile.cart.thumb_1_rad*(p.action==='push_grip'?smooth(elapsed/1.8):p.action==='push_release'?1-smooth((elapsed-2)/1.8):1);q[side+'_thumb_2_joint']=graspProfile.cart.thumb_2_rad*closed;}
  contactDiagnostics.push({side,object:identity,target_m:point.toArray(),contact_m:contact.toArray(),position_error_m:error,orientation_error_rad:jointApproach?null:handIK.lastRotationError,waypoint_position_error_m:waypointError,grip_fraction:closed,path_kind:jointApproach?'joint_space_pregrasp':'cartesian_target'});
 }
 return q;
}
function poseRobot(r){const q=constrainHands(r,jointPose(r)),world=new Map([[kin.root_link,M(kin.root_matrix)]]);for(const j of kin.joints){if(j.mimic)q[j.name]=Number(j.mimic.offset||0)+Number(j.mimic.multiplier||1)*(q[j.mimic.joint]||0);const transform=M(j.origin_matrix);if(q[j.name])transform.multiply(new THREE.Matrix4().makeRotationAxis(V(j.axis),q[j.name]));world.set(j.id,world.get(j.parent).clone().multiply(transform));}for(const item of robotParts){const link=kin.part_links[item.node.name];if(!link)continue;const matrix=world.get(link).clone().multiply(item.bindInverse).multiply(item.rest);matrix.decompose(item.node.position,item.node.quaternion,item.node.scale);}const robot=groups.get('g1');robot.position.set(r.position.x,r.position.y,r.rootZ);robot.rotation.z=r.yaw;robot.updateMatrixWorld(true);robotFrames=world;return world;}
function actionAmount(p,t){const u=clamp((t-p.start)/p.duration,0,1);return smooth(u/.22)*(1-smooth((u-.72)/.22));}
function applyState(id,fraction){const state=manifest.inspection_states.find(s=>s.id===id);if(!state)return;const asset=manifest.assets.find(a=>a.id===state.asset),n=M(asset.normalization_matrix);for(const item of nodeRest){if(item.asset!==state.asset||!state.parts.includes(item.node.name))continue;if(state.kind==='slide'){item.node.position.add(V(state.axis).multiplyScalar(state.maximum*fraction));}else{const pivot=V(state.pivot_m).applyMatrix4(n),rot=new THREE.Matrix4().makeRotationAxis(V(state.axis),state.maximum*fraction),trans=new THREE.Matrix4().makeTranslation(...pivot.toArray()).multiply(rot).multiply(new THREE.Matrix4().makeTranslation(...pivot.clone().negate().toArray())).multiply(item.rest);trans.decompose(item.node.position,item.node.quaternion,item.node.scale);}}}
function opticalOpen(p,t){if(t<p.start||t>p.end)return 0;const u=(t-p.start)/p.duration;return smooth(u/.09)*(1-smooth((u-.30)/.10))+smooth((u-.65)/.09)*(1-smooth((u-.90)/.10));}
const lidMeshes={};let cables=[];
function lidAt(t,which){
 const object=payload(t,which),local=lidMeshes[which].userData.local;
 const covered={position:local.clone().applyAxisAngle(V([0,0,1]),object.yaw).add(object.position),yaw:object.yaw};
 const stored={position:V([which==='white'?2.80:9.80,15.42,.901]),yaw:0};
 const remove=which==='white'?openWhite:openBlack,replace=which==='white'?coverWhite:coverBlack;
 if(t<remove.start||t>=replace.end)return covered;
 if(t>=remove.end&&t<replace.start)return stored;
 const returning=t>=replace.start,p=returning?replace:remove,e=t-p.start;
 const from=returning?stored:covered,to=returning?covered:stored;
 const waypoint=(pose,offset)=>({position:pose.position.clone().add(V(offset)),yaw:pose.yaw});
 // Pull forward beneath the reflector before moving upward and sideways.
 const knots=returning?[[0,from],[4,from],[5,waypoint(from,[0,0,.12])],[6.5,waypoint(to,[0,-.12,.04])],[8,waypoint(to,[0,-.02,.02])],[9,to],[14,to]]:
  [[0,from],[4,from],[5,waypoint(from,[0,-.02,.02])],[6,waypoint(from,[0,-.12,.04])],[7.5,waypoint(to,[0,0,.12])],[9,to],[14,to]];
 for(let i=1;i<knots.length;i++)if(e<=knots[i][0])return blendPose(knots[i-1][1],knots[i][1],(e-knots[i-1][0])/(knots[i][0]-knots[i-1][0]));
 return to;
}
function constrainTaskHands(r,q){
 const p=r.p;if(!p.action?.startsWith('lid_')&&!p.action?.startsWith('cover_'))return q;
 const elapsed=r.time-p.start,which=p.id.includes('white')?'white':'black',pose=lidAt(r.time,which);
 for(const side of ['left','right'])for(const joint of handIK.arm[side])q[joint.name]=poses.poses.rest[joint.name]||0;
 const rootMatrix=new THREE.Matrix4().makeRotationZ(r.yaw).setPosition(r.position.x,r.position.y,r.rootZ),inverse=rootMatrix.clone().invert();
 const palm=new THREE.Matrix4().makeRotationZ(pose.yaw).setPosition(pose.position).multiply(M(graspProfile.lid.palm_matrix));
 const point=new THREE.Vector3().setFromMatrixPosition(palm),rotation=inverse.clone().multiply(palm),contact=point.clone();
 const retreat=V([-.06,0,.08]).applyAxisAngle(V([0,0,1]),r.yaw);
 const approach=smooth((elapsed-2)/1.8),release=smooth((elapsed-9)/1.8),closed=approach*(1-release);
 point.addScaledVector(retreat,elapsed<4?1-approach:release);
 const restQ={...q,waist_pitch_joint:0};q.waist_pitch_joint=.15;
 let error,waypointError=null,jointSpace=false;
 if(elapsed<2||elapsed>=10.8){
  const preQ={...q};waypointError=handIK.solve(preQ,'right',point.clone().applyMatrix4(inverse),rotation);
  const amount=smooth(elapsed<2?elapsed/2:1-(elapsed-10.8)/2);
  for(const joint of handIK.arm.right)q[joint.name]=mix(restQ[joint.name]||0,preQ[joint.name]||0,amount);
  q.waist_pitch_joint=.15*amount;jointSpace=true;error=null;
 }else error=handIK.solve(q,'right',point.clone().applyMatrix4(inverse),rotation);
 for(const [name,value]of Object.entries(graspProfile.lid.q))q[name]=value*closed;
 q.right_thumb_1_joint=graspProfile.lid.q.right_thumb_1_joint*smooth(elapsed/1.8)*(1-smooth((elapsed-10.8)/1.8));
 contactDiagnostics.push({side:'right',object:'aperture_lid_'+which,target_m:point.toArray(),contact_m:contact.toArray(),position_error_m:error,orientation_error_rad:jointSpace?null:handIK.lastRotationError,waypoint_position_error_m:waypointError,grip_fraction:closed,path_kind:jointSpace?'joint_space_pregrasp':'cartesian_target'});
 return q;
}
function animateObjects(t,r){for(const n of nodeRest){n.rest.decompose(n.node.position,n.node.quaternion,n.node.scale)}for(const [id,which]of[['cooler_white','white'],['cooler_black','black']]){const p=payload(t,which),g=groups.get(id);g.position.copy(p.position);g.rotation.z=p.yaw;g.updateMatrixWorld(true);}
 const c=cartAt(t),cart=groups.get('utility_cart');cart.position.copy(c.position);cart.rotation.z=c.yaw;
 for(const [id,local]of[['daq',[0,0,.859]],['smu_white',[-.30,0,.25]],['smu_black',[.12,0,.25]]]){const g=groups.get(id);g.position.copy(c.position).add(V(local).applyAxisAngle(V([0,0,1]),c.yaw));g.rotation.z=c.yaw+Math.PI/2;}
 applyState('bath_lid',.55*actionAmount(cal,t));applyState('cary_lid',opticalOpen(cary,t));applyState('nicolet_cover',opticalOpen(ftir,t));
 // Assemblies start fabricated. Inspection must not levitate their bonded films or fastened parts.
 for(const which of ['white','black']){const pose=lidAt(t,which);lidMeshes[which].position.copy(pose.position);lidMeshes[which].rotation.z=pose.yaw;}
 for(const [p,id]of[[trackWhite,'cooler_white'],[trackBlack,'cooler_black']]){const a=smooth((t-p.start)/p.duration);if(a<=0)continue;for(const n of nodeRest)if(n.asset===id&&(n.node.name.includes('solar_reflector')||n.node.name.includes('frame_carriage')))n.node.position.x+=.025*a;}
 if(witness){const hand=new THREE.Vector3(.035,0,0).applyMatrix4(robotFrames.get('left_palm_force_sensor')).applyMatrix4(groups.get('g1').matrixWorld);let pos=V([1.4,5.7,.9]);const reference=phases.find(p=>p.id==='reference');if(t>=reference.start)pos.lerp(hand,smooth((t-reference.start-reference.duration+4)/3));for(const [p,port]of[[cary,[2.65,8.30,1.025]],[ftir,[9.19,8.30,1.06]]]){if(t>=p.start&&t<p.end){const u=(t-p.start)/p.duration;const load=smooth((u-.12)/.16)*(1-smooth((u-.76)/.12));pos=hand.clone().lerp(V(port),load);}}if(t>ftir.end){const dest=V([9.75,8.05,.853]);pos=hand.clone().lerp(dest,smooth((t-ftir.end)/2));}witness.position.copy(pos);}
 for(const cable of cables){const show=t>=outdoorConnect.start&&t<stop.end;const progress=clamp((t-outdoorConnect.start)/10,0,1)*(1-smooth((t-stop.start-3)/8));cable.visible=show;cable.geometry.setDrawRange(0,Math.floor(cable.geometry.index.count*progress/3)*3);}
 scene.updateMatrixWorld(true);
}
function desiredCamera(t){const r=robotAt(t),isMove=r.p.kind==='move';const offset=V(isMove?[-2.1,-2.25,1.9]:[1.2,-1.8,1.85]).applyAxisAngle(V([0,0,1]),r.yaw);let position=r.position.clone().add(offset);if(r.position.y<10){position.x=clamp(position.x,.45,11.55);position.y=clamp(position.y,.5,9.6);position.z=clamp(position.z,1.65,2.5);}const look=r.position.clone().add(V([.25,0,.88]).applyAxisAngle(V([0,0,1]),r.yaw));if(t<intro.end){const u=smooth(t/intro.duration);position=V([7.7,.7,2.1]).lerp(position,u);look.lerp(V([5.7,4.5,1.0]),1-u);}return {position,look};}
function cameraAt(t){const position=new THREE.Vector3(),look=new THREE.Vector3();let total=0;for(let j=-3;j<=3;j++){const weight=4-Math.abs(j),d=desiredCamera(clamp(t+j*.35,0,end));position.addScaledVector(d.position,weight);look.addScaledVector(d.look,weight);total+=weight;}camera.position.copy(position.divideScalar(total));camera.lookAt(look.divideScalar(total));}
let now=0,playing=false,clock=performance.now();
function renderAt(t){now=clamp(t,0,end);const r=robotAt(now);poseRobot(r);scene.updateMatrixWorld(true);animateObjects(now,r);cameraAt(now);localKey.position.set(r.position.x+1,r.position.y-1,3.12);localKey.target.position.set(r.position.x,r.position.y,0);renderer.render(scene,camera);if(!clean){$('title').textContent=r.p.title;$('detail').textContent=r.p.detail;$('seek').value=now;}window.currentFrame={time_s:now,stage:r.p.id,robot_position:r.position.toArray(),robot_yaw:r.yaw,white:payload(now,'white').position.toArray(),black:payload(now,'black').position.toArray(),cart:cartAt(now).position.toArray()};}
try{
 [manifest,poses,graspProfile]=await Promise.all([read('assets/cooling_lab_v1/scene.json'),read('viewer/cooling_concept_v2/motion_poses.json'),read('viewer/cooling_concept_v2/grasp_profile.json')]);kin=manifest.inspection_states.find(s=>s.id==='g1_hands_inspection').kinematics;handIK=new HandIK(kin);
 architecture=await load(manifest.architecture.path,manifest.architecture.sha256);const roles=new Map(manifest.architecture.part_records.map(p=>[p.id,p.role]));architecture.traverse(n=>{if(n.isMesh)n.userData.cutaway=['ceiling','ceiling_fixture'].includes(roles.get(n.name));});batchStaticMeshes(architecture);scene.add(architecture);
 for(const p of manifest.room_design.light_positions_m){const light=new THREE.PointLight(0xfff5df,6,8,2);light.position.set(...p);scene.add(light);}
 for(let i=0;i<manifest.assets.length;i+=5){await Promise.all(manifest.assets.slice(i,i+5).map(async a=>{const g=await load(a.geometry,a.geometry_sha256);const protectedParts=new Set(a.id==='g1'?a.part_names:manifest.inspection_states.filter(s=>s.asset===a.id).flatMap(s=>s.parts));if(a.id.startsWith('cooler_'))a.part_names.forEach(n=>protectedParts.add(n));batchStaticMeshes(g,protectedParts);g.position.set(...a.position_m);groups.set(a.id,g);scene.add(g);g.traverse(n=>{if(!n.isMesh)return;n.updateMatrix();if(a.id==='g1'){const link=kin.part_links[n.name];if(link)robotParts.push({node:n,rest:n.matrix.clone(),bindInverse:M(kin.bind_world[link]).invert()});}else nodeRest.push({asset:a.id,node:n,rest:n.matrix.clone()});});}));$('loading').textContent=`载入实验室设备 ${Math.min(i+5,manifest.assets.length)} / ${manifest.assets.length}`;}
 const cartDeck=new THREE.Group();cartDeck.name='transport_leveling_deck';
 const deckMaterial=new THREE.MeshStandardMaterial({color:0x475359,roughness:.86});
 const board=new THREE.Mesh(new THREE.BoxGeometry(1.15,.43,.012),deckMaterial);board.position.set(-.015,0,.853);cartDeck.add(board);extraMeshes.set('transport_leveling_deck',board);
 for(const x of [-.18,.23])for(const y of [-.17,.17]){const pad=new THREE.Mesh(new THREE.BoxGeometry(.06,.06,.007),deckMaterial);pad.position.set(x,y,.8435);cartDeck.add(pad);extraMeshes.set('transport_deck_pad_'+x+'_'+y,pad);}
 cartDeck.traverse(n=>{if(n.isMesh){n.castShadow=true;n.receiveShadow=true}});groups.get('utility_cart').add(cartDeck);
 groups.get('tray_white').position.set(3.12,2.8,.9);groups.get('tray_black').position.set(9.7,3.4,.9);
 for(const [which,id]of[['white','cooler_white'],['black','cooler_black']]){const g=groups.get(id);g.updateMatrixWorld(true);let plate;g.traverse(n=>{if(n.name.endsWith('__aperture_plate'))plate=n;});plate.geometry.computeBoundingBox();const box=plate.geometry.boundingBox.clone().applyMatrix4(plate.matrix);const local=box.getCenter(new THREE.Vector3());local.z=box.max.z+.001;const lid=new THREE.Mesh(new THREE.CylinderGeometry(.037,.037,.002,48),new THREE.MeshStandardMaterial({color:0xc6ccce,metalness:.85,roughness:.25}));lid.geometry.rotateX(Math.PI/2);lid.userData.local=local;lid.castShadow=true;lid.receiveShadow=true;scene.add(lid);lidMeshes[which]=lid;extraMeshes.set('aperture_lid_'+which,lid);const tab=new THREE.Mesh(new THREE.BoxGeometry(.014,.002,.040),lid.material);tab.position.set(0,-.026,.021);tab.rotation.z=graspProfile.lid.tab_normal_angle_rad-Math.PI/2;tab.castShadow=true;lid.add(tab);extraMeshes.set('aperture_lid_tab_'+which,tab);}
 for(const x of [2.5,9.5]){const pts=[V([x,15.55,.97]),V([x+.28,15.4,.89]),V([x+.45,15.3,.12]),V([x+.45,14.8,.025]),V([6,14.8,.025]),V([6,14.3,.86])];const curve=new THREE.CatmullRomCurve3(pts),geom=new THREE.TubeGeometry(curve,120,.002,5,false),line=new THREE.Mesh(geom,new THREE.MeshStandardMaterial({color:0x282b2d,roughness:.8}));scene.add(line);cables.push(line);}
 const material=new THREE.MeshStandardMaterial({color:0xe8e6d5,roughness:.85,metalness:.05});witness=new THREE.Mesh(new THREE.CylinderGeometry(.025,.025,.001,48),material);witness.geometry.rotateX(Math.PI/2);witness.castShadow=true;scene.add(witness);extraMeshes.set('optical_witness',witness);
 window.handCheck=t=>{const r=robotAt(t),joints=constrainHands(r,jointPose(r));return {time_s:t,phase:r.p.id,joints,targets:contactDiagnostics};};
 window.auditFrame=t=>{const r=robotAt(t);poseRobot(r);scene.updateMatrixWorld(true);animateObjects(t,r);const robot=groups.get('g1');return {time_s:t,phase:r.p.id,kind:r.p.kind,action:r.p.action||r.p.mode,joints:constrainHands(r,jointPose(r)),hand_targets:contactDiagnostics,robot_position:r.position.toArray(),robot_yaw:r.yaw,groups:Object.fromEntries([...groups].map(([id,g])=>[id,g.matrixWorld.toArray()])),links:Object.fromEntries([...robotFrames].map(([id,m])=>[id,robot.matrixWorld.clone().multiply(m).toArray()])),parts:nodeRest.filter(n=>['cooler_white','cooler_black','cary','nicolet','bath'].includes(n.asset)).map(n=>({asset:n.asset,name:n.node.name,matrix:n.node.matrixWorld.toArray()})),extra_matrices:Object.fromEntries([...extraMeshes].map(([id,n])=>[id,n.matrixWorld.toArray()])),lids:Object.fromEntries(Object.entries(lidMeshes).map(([id,n])=>[id,n.position.toArray()])),witness:witness.position.toArray()};};
 window.concept={extraGeometry:[...extraMeshes].map(([id,n])=>({id,vertices:Array.from(n.geometry.attributes.position.array),indices:n.geometry.index?Array.from(n.geometry.index.array):Array.from({length:n.geometry.attributes.position.count},(_,i)=>i)})),duration:end,phases:phases.map(({curve,...p})=>p),sourceHashes,assetCount:groups.size,robotCount:1,renderAt,rendererInfo:()=>renderer.info.render,frameJpeg:t=>{renderAt(t);return renderer.domElement.toDataURL('image/jpeg',.92).split(',')[1]}};window.renderAt=renderAt;renderAt(0);$('seek').max=end;$('loading').remove();document.documentElement.dataset.ready='true';
 $('play').onclick=()=>{playing=!playing;clock=performance.now();$('play').textContent=playing?'暂停':'播放';};$('seek').oninput=e=>{playing=false;renderAt(Number(e.target.value));};function tick(t){if(playing){renderAt(now+(t-clock)/1000);if(now>=end)playing=false;}clock=t;requestAnimationFrame(tick);}requestAnimationFrame(tick);
}catch(e){$('error').textContent=e.stack;console.error(e);}
