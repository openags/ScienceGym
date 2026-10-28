import * as THREE from 'three';
import {batchStaticMeshes} from './render_batches.js';

// Review-only alternative to the installed station. These mutually exclusive
// scenes retain object identities; switching never moves a simulated object.
export class WeatherInitialStock {
 constructor(composition){this.parent=composition;this.enabled=false;this.toolIds=new Set()}
 async load(){
  const p=this.parent,base=p.root+'assets/cooling_lab_v1/';
  this.record=await p.read(base+'weather_initial_stock_assets.json');
  this.checks=await p.read(base+'weather_initial_stock_checks.json');
  for(const ref of [...this.record.source_artifacts,...this.checks.source_artifacts]){
   const path=p.root+ref.path;
   if(!p.hashes.has(path)){
    const r=await fetch(path);if(!r.ok)throw Error('初始备料来源不可读：'+ref.path);
    const bytes=await r.arrayBuffer(),h=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),x=>x.toString(16).padStart(2,'0')).join('');p.hashes.set(path,h);
   }
   if(p.hashes.get(path)!==ref.sha256)throw Error('初始备料来源版本不一致：'+ref.path);
  }
  if(!this.checks.passed||this.record.owner_acceptance!==null||this.record.robot_use_qualified||this.record.initial_stock_credit)throw Error('初始备料检查未通过或验收状态不一致');
  const loaded=await p.loadPinned(this.record.geometry.path,this.record.geometry.sha256);p.prepare(loaded);
  this.group=loaded.scene;this.actualParts=[];this.group.traverse(n=>{if(n.isMesh)this.actualParts.push(n.name)});
  if(this.actualParts.length!==this.record.geometry.parts||this.actualParts.some(n=>!this.record.geometry.part_records.some(r=>r.id===n)))throw Error('初始备料部件不完整');
  this.batch=batchStaticMeshes(this.group);this.group.visible=false;p.scene.add(this.group);
  this.toolIds=new Set(this.record.retained_tool_modules.map(m=>m.id));
  for(const m of this.record.retained_tool_modules){
   const current=p.modules.get(m.id)?.record;
   if(!current||current.geometry.sha256!==m.geometry.sha256||JSON.stringify(current.to_world)!==JSON.stringify(m.to_world))throw Error('初始备料与同一工具的位置不一致：'+m.id);
  }
  this.regions=[['all','完整备料布局',null],['fabrication_fixture','长杆件与折叠三脚架','fabrication_fixture'],
   ['fabrication_storage_shelf_3','三个托盘与安装零件','fabrication_storage_shelf_3'],
   ['raw_stock_shelf_3','未裁切线材与完整扎带','raw_stock_shelf_3'],
   ['specimens_shelf_1','未装配风速计与 RS3','specimens_shelf_1'],
   ['specimens_shelf_2','温湿度探头、记录仪与接地线','specimens_shelf_2']];
  const select=document.getElementById('weather-initial-focus');
  for(const [id,label] of this.regions){const option=document.createElement('option');option.value=id;option.textContent=label;select.append(option)}
  select.onchange=()=>{this.setEnabled(true);this.focus(select.value)};
  const checkbox=document.getElementById('weather-initial');checkbox.onchange=()=>this.setEnabled(checkbox.checked);checkbox.disabled=false;select.disabled=false;
  document.getElementById('weather-initial-status').textContent=this.record.geometry.parts+' 个备料部件；38 个天气站相关物品身份沿用同一套库存。当前是拆箱后的静态候选，尚未完成初始库存验收。';
  window.scienceGymWeatherInitialStock=()=>({enabled:this.enabled,visible:this.group.visible,parts:this.actualParts,
   worldBounds:(()=>{const b=new THREE.Box3().setFromObject(this.group,true);return [b.min.toArray(),b.max.toArray()]})(),
   identities:this.record.physical_identity_ids,batch:this.batch,ownerAcceptance:this.record.owner_acceptance,
   initialStockCredit:this.record.initial_stock_credit,robotUseQualified:this.record.robot_use_qualified});
  document.documentElement.dataset.weatherInitialLoaded='true';
 }
 setEnabled(value){this.enabled=value;document.getElementById('weather-initial').checked=value;if(value){this.parent.enabled=false;document.getElementById('weather-composed').checked=false}this.parent.refresh()}
 disable(){this.enabled=false;document.getElementById('weather-initial').checked=false}
 boundsForRegion(id){
  const support=this.regions.find(r=>r[0]===id)?.[2],surfaces=new Map(this.record.support_surfaces.map(s=>[s.id,s])),b=new THREE.Box3();
  for(const g of this.record.groups){const s=surfaces.get(g.support),parent=s?.physical_support_part?'fabrication_storage_shelf_3':g.support;
   if(!support||parent===support)b.union(new THREE.Box3(new THREE.Vector3(...g.bounds_m[0]),new THREE.Vector3(...g.bounds_m[1])));
  }
  for(const lead of this.record.leads)if(lead.authored_shape&&(!support||lead.support===support)){
   const part=this.record.geometry.part_records.find(p=>p.id===lead.part);b.union(new THREE.Box3(new THREE.Vector3(...part.bounds_m[0]),new THREE.Vector3(...part.bounds_m[1])));
  }
  return b;
 }
 focus(id){
  const b=this.boundsForRegion(id),centre=b.getCenter(new THREE.Vector3()),size=b.getSize(new THREE.Vector3());
  const viewport=document.getElementById('viewport'),aspect=viewport.clientWidth/viewport.clientHeight;
  const distance=Math.max(...size.toArray())*(id==='all'?1.25:1.8)/Math.min(1,aspect);
  const direction=id==='all'?[.4,-1,.9]:id==='fabrication_fixture'?[.15,1,.6]:id==='fabrication_storage_shelf_3'?[.1,-1,.10]:[.1,1,.10];
  document.getElementById('show-walls').checked=id!=='all';this.parent.refresh();
  this.parent.focus(centre.clone().addScaledVector(new THREE.Vector3(...direction).normalize(),distance).toArray(),centre.toArray());
 }
 obstacles(){return this.enabled?this.record.groups.map(g=>({bounds_m:g.bounds_m})):[]}
}
