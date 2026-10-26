import * as THREE from 'three';
import {batchStaticMeshes} from './render_batches.js';

// A downstream scene composition. Alternative representations reuse physical
// identities; toggling this reviewer state never changes a simulation state.
export class WeatherComposition {
 constructor({scene,groups,architecture,read,hashes,loadPinned,prepare,refresh,focus}){
  Object.assign(this,{scene,groups,architecture,read,hashes,loadPinned,prepare,refresh,focus});
  this.enabled=false;this.modules=new Map();this.root='../../';
 }
 async load(){
  const base=this.root+'assets/cooling_lab_v1/';
  this.record=await this.read(base+'weather_scene_binding.json');
  this.checks=await this.read(base+'weather_scene_binding_checks.json');
  for(const ref of [...this.record.source_artifacts,...this.checks.source_artifacts]){
   const path=this.root+ref.path;
   if(!this.hashes.has(path)){
    const response=await fetch(path);if(!response.ok)throw Error('天气站来源不可读：'+ref.path);
    const bytes=await response.arrayBuffer();const h=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),x=>x.toString(16).padStart(2,'0')).join('');this.hashes.set(path,h);
   }
   if(this.hashes.get(path)!==ref.sha256)throw Error('天气站组合记录版本不一致：'+ref.path);
  }
  if(!this.checks.passed||this.record.owner_acceptance!==null||this.record.robot_use_qualified)throw Error('天气站组合范围或检查状态不一致');
  this.floorParts=[];this.architecture.traverse(n=>{if(this.record.hide_architecture_parts.includes(n.name))this.floorParts.push(n)});
  if(this.floorParts.length!==this.record.hide_architecture_parts.length)throw Error('室外原地面没有独立保留');
  for(const m of this.record.modules){
   const model=await this.loadPinned(m.geometry.path,m.geometry.sha256);this.prepare(model);
   const group=model.scene;let actual=[];group.traverse(n=>{if(n.isMesh)actual.push(n.name)});
   if(actual.length!==m.geometry.parts||actual.some(n=>!m.geometry.part_records.some(p=>p.id===n)))throw Error('天气站部件不完整：'+m.id);
   const batch=batchStaticMeshes(group);group.applyMatrix4(new THREE.Matrix4().fromArray(m.to_world.flat()).transpose());group.visible=false;
   this.scene.add(group);this.modules.set(m.id,{group,record:m,actualParts:actual,batch});
   if(m.id!=='ground'){const option=document.createElement('option');option.value=m.id;option.textContent=m.label;document.getElementById('weather-focus').append(option)}
  }
  const body=document.getElementById('weather-identities');
  for(const e of this.record.physical_entities){const row=document.createElement('tr');
   for(const text of [e.label,e.existing_scene_identity?'沿用 '+e.id:'新增候选 '+e.id,e.representations.length+' 个几何部件',e.id.startsWith('weather_tie_')?'原扎带与截尾共用身份':'选定 1 件／套，数量待验收']){const td=document.createElement('td'),inspector={weather_wire_rope_cutter:['wire_rope_cutter.html','查看刀口与内部'],weather_adjustable_wrench:['adjustable_wrench.html','查看钳口与螺母适配']}[e.id];if(text===e.label&&inspector){const a=document.createElement('a');a.href=inspector[0];a.textContent=text+' · '+inspector[1]+' ↗';td.append(a)}else td.textContent=text;row.append(td)}body.append(row);
  }
  document.getElementById('weather-focus').onchange=e=>{if(e.target.value){document.getElementById('weather-composed').checked=true;this.setEnabled(true);this.focusModule(e.target.value)}};
  document.getElementById('weather-composed').onchange=e=>this.setEnabled(e.target.checked);
  document.getElementById('weather-composed').disabled=false;
  document.getElementById('weather-composition-status').textContent='已载入 '+this.record.physical_entities.length+' 个逐件归属记录；其中 U30 与小车沿用原实例。安装参考与备料参考互斥显示，均未完成初始库存与运动验证。';
  window.scienceGymWeatherComposition=()=>{
   this.scene.updateMatrixWorld(true);
   return {enabled:this.enabled,modules:[...this.modules].map(([id,m])=>({id,visible:m.group.visible,parts:m.actualParts.length,sourceParts:m.actualParts,worldMatrix:m.group.matrixWorld.toArray(),bounds:new THREE.Box3().setFromObject(m.group,true).min.toArray().concat(new THREE.Box3().setFromObject(m.group,true).max.toArray()),batch:m.batch})),
    baseVisibility:Object.fromEntries([...this.groups].map(([id,g])=>[id,g.visible])),floorVisibility:this.floorParts.map(p=>p.visible),entities:this.record.physical_entities.length,ownerAcceptance:this.record.owner_acceptance,robotUseQualified:this.record.robot_use_qualified};
  };
  document.documentElement.dataset.weatherCompositionLoaded='true';
 }
 setEnabled(enabled){this.enabled=enabled;document.getElementById('weather-composed').checked=enabled;this.refresh()}
 applyVisibility(isolate){
  for(const {group} of this.modules.values())group.visible=this.enabled&&!isolate;
  for(const p of this.floorParts||[])p.visible=!this.enabled;
  if(this.enabled&&!isolate)for(const id of this.record.hide_scene_asset_ids)this.groups.get(id).visible=false;
  document.documentElement.dataset.weatherComposition=this.enabled?'installed_reference':'base_staging_reference';
 }
 cameraObstacles(){
  if(!this.enabled)return [];
  return [...this.modules].filter(([id])=>id!=='ground').map(([,m])=>{const b=new THREE.Box3().setFromObject(m.group);return {bounds_m:[b.min.toArray(),b.max.toArray()]}});
 }
 focusModule(id){
  const group=this.modules.get(id).group,bounds=new THREE.Box3().setFromObject(group),center=bounds.getCenter(new THREE.Vector3());
  const size=bounds.getSize(new THREE.Vector3()),distance=Math.max(...size.toArray())*(id==='station'?1.5:2.4);
  this.focus(center.clone().add(new THREE.Vector3(.8,-1,.65).normalize().multiplyScalar(distance)).toArray(),center.toArray());
 }
}
