const $=id=>document.getElementById(id),root='../../';let report;
const poolLabels={heater:'加热片',smu:'电源／源表',probes:'K 型温度探头',daq:'温度采集器',bath:'校准水浴',dmm:'参考读数仪表',reference_rtd:'参考 RTD',ambient_rtd:'环境 RTD',uvvis:'可见／近红外仪器',dra:'DRA 积分球',ftir:'红外光谱仪',integratir:'IntegratIR 积分球',tracker:'太阳跟踪器',dni:'直射辐射计',gti:'总辐射计',weather_logger:'气象记录器'};
const roleLabels={white_emitter:'白色发射体',black_emitter:'黑色发射体',white_heater_source:'白色加热通道',black_heater_source:'黑色加热通道',temperature_log:'温度记录',calibration_log:'校准记录',calibration_bath:'校准水浴',reference_readout:'参考读数',reference:'参考探头',ambient:'环境温度',solar_tracking:'太阳跟踪',direct_solar:'直射辐射',global_solar:'总辐射',weather_log:'气象记录',shortwave:'短波测量',shortwave_accessory:'短波附件',infrared:'红外测量',infrared_accessory:'红外附件'};
const branchLabels={BUILD_PAIR:'制作白／黑成对装置',CALIBRATE:'校准温度探头',OPT_HEMISPHERICAL:'半球光学测量',OPT_ANGULAR:'角度光学测量',ENVIRONMENT:'环境监测',TRACKED_STAGNATION:'跟踪构型停滞温度',PID_POWER:'成对加热与冷却功率',FIXED_LDPE:'固定遮阳带与 LDPE 换装',MAP_CLEAR_DAY:'晴朗白天热分布',MAP_CLEAR_NIGHT:'晴朗夜间热分布',MAP_HAZY_NOON:'多云近午热分布'};
const roleName=role=>roleLabels[role]||(role.startsWith('map_')?'热分布点 '+role.slice(4):role.startsWith('calibration_probe_')?'校准探头 '+role.slice(18):role);
function element(tag,text){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e}
function card(target,title,detail){const e=element('div');e.className='risk-card';e.append(element('h3',title),element('p',detail));$(target).append(e)}
function render(){
 const branch=$('allocation-branch').value,query=$('allocation-search').value.trim().toLowerCase(),filter=$('allocation-filter').value;
 $('branch-allocation').replaceChildren();
 for(const b of report.branches.filter(b=>branch==='all'||b.id===branch)){
  const box=element('details');box.open=branch!=='all';box.append(element('summary',b.id+' · '+branchLabels[b.id]));
  box.append(element('p',b.apparatus_ids.length?'共用装置身份：'+b.apparatus_ids.join('、'):'此分支不占用已完成的室外装置。'));
  const table=element('table'),body=element('tbody');
  const priority=['heater','smu','probes','daq'];const rank=id=>priority.includes(id)?priority.indexOf(id):priority.length;
  for(const p of [...b.allocations].sort((a,b)=>rank(a.pool_id)-rank(b.pool_id))){const tr=element('tr');tr.append(element('td',poolLabels[p.pool_id]),element('td',p.simultaneous_units+' 件'),element('td',p.roles.map(r=>roleName(r.role)+' → '+(r.physical_id||'缺失')).join('；')));body.append(tr)}
  table.append(body);box.append(table);
  box.append(element('p','这里只列已选定数量的核心设备；下面组件表保留全部关联需求与未分配项。'));$('branch-allocation').append(box);
 }
 const rows=report.components.filter(c=>(branch==='all'||c.branch_ids.includes(branch))&&(!query||JSON.stringify(c).toLowerCase().includes(query))&&(filter==='all'||filter==='unallocated'&&c.required_quantity===null||filter==='missing'&&!c.staged_candidates||filter==='quantified'&&c.required_quantity!==null));
 $('allocation-components').replaceChildren();
 for(const c of rows){const s=c.staged_candidates,tr=element('tr');tr.dataset.component=c.id;
  const ids=s?[...new Set(s.members.map(m=>m.asset_id))].join('、'):'—';
  for(const value of [c.resource_id+' / '+c.label,c.required_quantity===null?'待分配':c.required_quantity+' 件（选定）',s?s.quantity+' '+s.unit:'无逐件绑定',ids,c.quantity_deficit?'缺少 '+c.quantity_deficit+' 件':c.required_quantity===null?'用量与完整性待核对':'数量已有候选；完整性未验收'])tr.append(element('td',value));
  $('allocation-components').append(tr);
 }
 $('allocation-visible').textContent='显示 '+rows.length+' / '+report.components.length+' 项组件需求。';
}
async function start(){
 const response=await fetch(root+'assets/cooling_lab_v1/campaign_allocation.json',{cache:'no-store'});if(!response.ok)throw Error('无法读取分配记录');report=await response.json();
 for(const source of report.source_artifacts){const r=await fetch(root+source.path,{cache:'no-store'});if(!r.ok)throw Error('缺失依据：'+source.path);const digest=await crypto.subtle.digest('SHA-256',await r.arrayBuffer());const actual=[...new Uint8Array(digest)].map(v=>v.toString(16).padStart(2,'0')).join('');if(actual!==source.sha256)throw Error('分配记录已过期：'+source.path)}
 const c=report.counts;$('allocation-counts').textContent=c.scene_instances+' 个场景实例中，'+c.reference_only_instances+' 个仅作完成态或备选参考。'+c.component_requirements+' 项组件需求中，'+c.selected_quantity_components+' 项已有选定数量，'+c.unallocated_component_quantities+' 项用量待分配；完整分支通过 0 / '+c.branches+'。';
 for(const b of report.branches){const option=element('option',b.id+' · '+branchLabels[b.id]);option.value=b.id;$('allocation-branch').append(option)}
 for(const p of report.physical_instances.filter(p=>!p.initial_stock_credit))card('allocation-references',p.id+' · '+p.label,p.note);
 for(const gap of report.remaining)card('allocation-remaining',gap.label,gap.detail);
 for(const id of ['allocation-branch','allocation-filter','allocation-search'])$(id).addEventListener(id==='allocation-search'?'input':'change',render);
 render();document.documentElement.dataset.allocationLoaded='true';
}
start().catch(e=>{$('allocation-error').textContent=String(e);document.documentElement.dataset.allocationLoaded='error'});
