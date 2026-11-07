const $=id=>document.getElementById(id),root='../../';let report,stockPlan,labInventory;
const stockLabels={copper_sheet_stock:'铜板',aluminum_sheet_stock:'铝板',foam_stock:'泡沫板',acrylic_stock:'亚克力板',mylar_stock:'镀铝 PET',nano_pe_stock:'纳米多孔 PE',ldpe_stock:'LDPE',frame_machining_stock:'框架加工铝坯',cover_adhesive_stock:'带离型纸转移胶膜'};
const unitLabels={instrument_or_probe:'台／支',tool:'件',vessel:'个',probe:'支',sheet:'张',plate:'块',tube:'段',roll:'卷',blank:'块',cart:'辆',tray:'个',connector_pair:'对',kit:'套',lead:'根','T-nut':'个','inspection asset':'件',individual_length:'根',fastener_or_pad_package:'件／包'};
Object.assign(unitLabels,{assembly:'组',mask_set:'套遮罩',mirror:'片',can:'罐',bottle:'瓶',camera:'台'});
const kindLabels={inventory_item:'实物／材料',assembly_component:'设备子组件',interface_requirement:'接口与配套',facility_requirement:'场地与服务',output_state:'待制造成品',configuration_state:'换装状态',frame_requirement:'坐标依据',acceptance_condition:'验收条件'};
const mm=v=>Number((v*1000).toFixed(3));
function cutLabel(c){
 const color=c.id.includes('white')?'白色装置':c.id.includes('black')?'黑色装置':'';
 if(c.attachment_reservation){const r=c.attachment_reservation;return color+' · '+({BUILD_PAIR:'初装',FIXED_LDPE:'LDPE 换装',RESTORE_TRACKED:'恢复跟踪构型'}[r.stage])+' · '+({lower:'下层膜胶环',upper:'上层膜胶环',aperture:'顶盖胶环'}[r.location])}
 if(c.id.includes('witness'))return (c.id.includes('shortwave')?'短波':c.id.includes('infrared')?'红外':'铜质')+'光学试片预留，最终规格待定';
 if(c.id.includes('restore'))return '白色装置恢复用膜 · 第 '+c.id.at(-1)+' 层';
 if(c.id.includes('layer'))return color+'覆盖膜 · 第 '+c.id.at(-1)+' 层';
 for(const [key,label] of [['frame_bridge','底板连接板'],['frame_lower_clamp','立柱下夹块'],['frame_upper_clamp','立柱上夹块'],['frame_carriage_lower','反射片下夹板'],['frame_carriage_upper','反射片上夹板']])if(c.id.includes(key))return color+' · '+label;
 for(const [key,label] of [['base_foil','底板贴膜'],['foam_wrap','泡沫包覆毛坯'],['support_wrap','支撑管包覆毛坯'],['emitter','铜发射片'],['foam','泡沫层'],['base','底板'],['platform','升降台上平台'],['aperture','开口板'],['reflector','反射片'],['track','反射片轨道'],['fixed_band','固定遮阳带'],['spacer','覆盖膜间隔环']])if(c.id.includes(key))return color+' · '+label;
 return c.id;
}
function svg(tag,attributes,text){const node=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [key,value] of Object.entries(attributes))node.setAttribute(key,String(value));if(text!==undefined)node.textContent=text;return node}
function renderStock(){
 const row=stockPlan.sheets.find(s=>s.id===$('stock-sheet').value),[w,h]=row.size_m.map(mm),drawing=$('stock-plan');
 drawing.replaceChildren();drawing.setAttribute('viewBox',[-18,-18,w+36,h+36].join(' '));
 drawing.append(svg('title',{},stockLabels[row.asset_id]+' · '+w+' × '+h+' mm 原料下料预留图'));
 drawing.append(svg('rect',{x:0,y:0,width:w,height:h,fill:'#edf2ed',stroke:'#76958c','stroke-width':.5}));
 drawing.append(svg('text',{x:w/2,y:-6,'text-anchor':'middle','font-size':7,fill:'#31584f'},w+' mm'));
 drawing.append(svg('text',{x:-6,y:h/2,transform:'rotate(-90 -6 '+h/2+')','text-anchor':'middle','font-size':7,fill:'#31584f'},h+' mm'));
 $('stock-dimensions').textContent=w+' × '+h+' mm · 厚 '+mm(row.thickness_m)+' mm';$('stock-cuts').replaceChildren();
 for(const [i,c] of row.cuts.entries()){
  const points=c.outline_m.map(p=>p.map(mm)),xs=points.map(p=>p[0]),ys=points.map(p=>p[1]),bounds=[Math.min(...xs),Math.min(...ys),Math.max(...xs),Math.max(...ys)];
  const color=c.reservation_only?'#ba873b':c.wrapped_surface?'#5b82a2':'#347d6c';
  const polygon=svg('polygon',{points:points.map(p=>p.join(',')).join(' '),fill:color,'fill-opacity':.2,stroke:color,'stroke-width':.7,'data-cut-id':c.id});
  if(c.reservation_only||c.wrapped_surface)polygon.setAttribute('stroke-dasharray','3 2');
  polygon.append(svg('title',{},cutLabel(c)));drawing.append(polygon,svg('text',{x:(bounds[0]+bounds[2])/2,y:(bounds[1]+bounds[3])/2+2,'text-anchor':'middle','font-size':8,fill:'#173d35'},i+1));
  const facing=c.facing_allowance_m>.000001?' · 原厚 '+mm(c.required_thickness_m)+' mm，需铣至 '+mm(c.output_finished_thickness_m)+' mm':'';
  const li=element('li',cutLabel(c)+' · '+Number((bounds[2]-bounds[0]).toFixed(2))+' × '+Number((bounds[3]-bounds[1]).toFixed(2))+' mm'+facing);li.dataset.cutId=c.id;$('stock-cuts').append(li);
 }
 drawing.dataset.sheet=row.id;
}
const poolLabels={heater:'加热片',smu:'电源／源表',probes:'K 型温度探头',daq:'温度采集器',bath:'校准水浴',dmm:'参考读数仪表',reference_rtd:'参考 RTD',ambient_rtd:'环境 RTD',uvvis:'可见／近红外仪器',dra:'DRA 积分球',ftir:'红外光谱仪',integratir:'IntegratIR 积分球',tracker:'太阳跟踪器',dni:'直射辐射计',gti:'总辐射计',weather_logger:'气象记录器'};
const roleLabels={white_emitter:'白色发射体',black_emitter:'黑色发射体',white_heater_source:'白色加热通道',black_heater_source:'黑色加热通道',temperature_log:'温度记录',calibration_log:'校准记录',calibration_bath:'校准水浴',reference_readout:'参考读数',reference:'参考探头',ambient:'环境温度',solar_tracking:'太阳跟踪',direct_solar:'直射辐射',global_solar:'总辐射',weather_log:'气象记录',shortwave:'短波测量',shortwave_accessory:'短波附件',infrared:'红外测量',infrared_accessory:'红外附件'};
const branchLabels={BUILD_PAIR:'制作白／黑成对装置',CALIBRATE:'校准温度探头',OPT_HEMISPHERICAL:'半球光学测量',OPT_ANGULAR:'角度光学测量',ENVIRONMENT:'环境监测',TRACKED_STAGNATION:'跟踪构型停滞温度',PID_POWER:'成对加热与冷却功率',FIXED_LDPE:'固定遮阳带与 LDPE 换装',MAP_CLEAR_DAY:'晴朗白天热分布',MAP_CLEAR_NIGHT:'晴朗夜间热分布',MAP_HAZY_NOON:'多云近午热分布'};
poolLabels.lab_jacks='升降台';roleLabels.white_height_adjuster='白色装置升降台';roleLabels.black_height_adjuster='黑色装置升降台';
unitLabels.catalog_lab_jack='台';unitLabels.fastener_or_washer='件';unitLabels.lined_adhesive_sheet='张（带离型纸）';unitLabels.reusable_hand_tool='件（共用）';
const roleName=role=>roleLabels[role]||(role.startsWith('map_')?'热分布点 '+role.slice(4):role.startsWith('calibration_probe_')?'校准探头 '+role.slice(18):role);
function element(tag,text){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e}
function card(target,title,detail){const e=element('div');e.className='risk-card';e.append(element('h3',title),element('p',detail));$(target).append(e)}
function renderIdentities(){
 const mode=$('identity-filter').value;
 const rows=labInventory.identities.filter(e=>mode==='all'||mode==='weather'&&(e.installed_reference_present||e.preparation_reference_present)||mode==='unplaced'&&e.initial_state_status==='initial_placement_missing'||mode==='reused'&&e.base_candidate_placement&&e.installed_reference_present);
 $('identity-rows').replaceChildren();
 const status={base_candidate_placement_unqualified:'已有陈列位置，初始状态未验收',context_candidate_placement_unqualified:'已有工具台位置，初始状态未验收',initial_placement_missing:'初始存放位置待补',facility_design_not_portable_stock:'场地设计，不计可搬运库存'};
 for(const e of rows){const tr=element('tr');tr.dataset.identity=e.id;
  const contexts=[...new Set(e.representations.map(r=>({base_display:'基础陈列',weather_installed_reference:'安装参考',weather_partial_preparation:'低位准备参考'}[r.context])))];
  for(const value of [e.label,e.id,contexts.join(' / '),status[e.initial_state_status]])tr.append(element('td',value));$('identity-rows').append(tr);
 }
 $('identity-visible').textContent='显示 '+rows.length+' / '+labInventory.identities.length+' 个审查身份。';
}
function renderInstallation(){
 const c=labInventory.counts;$('installation-summary').textContent=c.installation_requirements+' 项安装补充需求，其中 '+c.installation_needs_without_candidate+' 项尚无候选物品，'+c.installation_quantities_unallocated+' 项数量或容量待分配。';
 for(const n of labInventory.installation_requirements){const tr=element('tr');tr.dataset.need=n.id;
  const unit={tool:'件',container:'管',g:'g',wipe:'张',tie:'根',pack:'包',collection_point:'处'}[n.unit]||n.unit;
  const status=n.candidate_ids.length?'候选未验收；初始准备待核对':'缺少候选物品';
  for(const value of [n.label,n.required_quantity===null?'待分配':n.required_quantity+' '+unit,n.candidate_ids.join('、')||'—',status])tr.append(element('td',value));$('installation-needs').append(tr);
 }
 $('identity-summary').textContent=c.base_identities+' 个基础陈列身份 + '+c.context_identities+' 个气象站组合身份 − '+c.reused_identities+' 个重复展示身份 + '+c.preparation_only_identities+' 根临时扎带 = '+c.unique_review_identities+' 个审查身份（含 '+c.facility_designs+' 个场地设计）。这不是可执行初始库存数量。';
 $('identity-filter').addEventListener('change',renderIdentities);renderIdentities();
}
function render(){
 const branch=$('allocation-branch').value,query=$('allocation-search').value.trim().toLowerCase(),filter=$('allocation-filter').value,kind=$('allocation-kind').value;
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
 const rows=report.components.filter(c=>(branch==='all'||c.branch_ids.includes(branch))&&(kind==='all'||c.requirement_kind===kind)&&(!query||JSON.stringify(c).toLowerCase().includes(query))&&(filter==='all'||filter==='unallocated'&&c.quantity_status==='unallocated'||filter==='missing'&&c.stock_quantity_applicable&&(!c.staged_candidates||c.staged_candidates.quantity===0)||filter==='quantified'&&c.required_quantity!==null||filter==='nonstock'&&!c.stock_quantity_applicable));
 $('allocation-components').replaceChildren();
 for(const c of rows){const s=c.staged_candidates,tr=element('tr');tr.dataset.component=c.id;
  const ids=s?[...new Set(s.members.map(m=>m.asset_id))].join('、'):'—';
  const unit=unitLabels[c.required_unit||s?.unit]||c.required_unit||s?.unit||'件';
  const quantity=!c.stock_quantity_applicable?'不计库存数量':c.required_quantity===null?'待分配':c.required_quantity+' '+unit+'（选定）';
  const candidate=!c.stock_quantity_applicable?'需状态／验收证据':s?s.quantity+' '+unit:'无逐件绑定';
  const state=!c.stock_quantity_applicable?'要求仍待完成':c.quantity_deficit?'缺少 '+c.quantity_deficit+' '+unit+'候选绑定':c.required_quantity===null?'数量、规格与配套待核对':'数量已有候选；完整性未验收';
  for(const value of [c.resource_id+' / '+c.label,kindLabels[c.requirement_kind],quantity,candidate,ids])tr.append(element('td',value));
  const status=element('td',state),details=element('details');details.append(element('summary','数量依据与剩余条件'),element('p',c.quantity_basis));
  for(const text of c.remaining_requirements)details.append(element('p',text));
  if(c.state_or_acceptance_requirement)details.append(element('p','关联对象：'+c.state_or_acceptance_requirement.subjects.join('、')));
  status.append(details);tr.append(status);
  $('allocation-components').append(tr);
 }
 $('allocation-visible').textContent='显示 '+rows.length+' / '+report.components.length+' 项组件需求。';
}
async function start(){
 const response=await fetch(root+'assets/cooling_lab_v1/campaign_allocation.json',{cache:'no-store'});if(!response.ok)throw Error('无法读取分配记录');report=await response.json();
 for(const source of report.source_artifacts){const r=await fetch(root+source.path,{cache:'no-store'});if(!r.ok)throw Error('缺失依据：'+source.path);const bytes=await r.arrayBuffer(),digest=await crypto.subtle.digest('SHA-256',bytes);const actual=[...new Uint8Array(digest)].map(v=>v.toString(16).padStart(2,'0')).join('');if(actual!==source.sha256)throw Error('分配记录已过期：'+source.path);if(source.path===report.stock_allocation.path){if(actual!==report.stock_allocation.sha256)throw Error('下料分配版本不一致');stockPlan=JSON.parse(new TextDecoder().decode(bytes))}}
 if(!stockPlan)throw Error('缺少已核对的下料分配');
 const inventoryResponse=await fetch(root+'assets/cooling_lab_v1/laboratory_inventory.json',{cache:'no-store'});if(!inventoryResponse.ok)throw Error('无法读取统一物品总表');labInventory=await inventoryResponse.json();
 for(const source of labInventory.source_artifacts){const r=await fetch(root+source.path,{cache:'no-store'});if(!r.ok)throw Error('缺失总表依据：'+source.path);const digest=await crypto.subtle.digest('SHA-256',await r.arrayBuffer());const actual=[...new Uint8Array(digest)].map(v=>v.toString(16).padStart(2,'0')).join('');if(actual!==source.sha256)throw Error('物品总表已过期：'+source.path)}
 const c=report.counts;$('allocation-counts').textContent=c.scene_instances+' 个场景实例中，'+c.reference_only_instances+' 个仅作完成态或备选参考。'+c.component_requirements+' 项要求：'+c.selected_quantity_components+' 项已有选定数量，'+c.unallocated_component_quantities+' 项数量或规格待分配，'+c.non_stock_requirements+' 项状态／坐标／校准要求不计库存数量。'+c.incomplete_component_requirements+' 项均未完成验收；完整分支通过 0 / '+c.branches+'。';
 for(const [kind,count] of Object.entries(c.requirements_by_kind)){const option=element('option',kindLabels[kind]+'（'+count+'）');option.value=kind;$('allocation-kind').append(option)}
 for(const b of report.branches){const option=element('option',b.id+' · '+branchLabels[b.id]);option.value=b.id;$('allocation-branch').append(option)}
 for(const p of report.physical_instances.filter(p=>!p.initial_stock_credit))card('allocation-references',p.id+' · '+p.label,p.note);
 for(const gap of report.remaining)card('allocation-remaining',gap.label,gap.detail);
 for(const id of ['allocation-branch','allocation-filter','allocation-kind','allocation-search'])$(id).addEventListener(id==='allocation-search'?'input':'change',render);
 $('stock-summary').textContent=stockPlan.sheets.length+' 片原料，'+stockPlan.sheets.reduce((n,s)=>n+s.cuts.length,0)+' 项轮廓／试片预留，以及 '+stockPlan.tubes.length+' 段空心管、'+stockPlan.profiles.length+' 根定尺型材。下料保留 1 mm 边缘与切割间隔；加工尚未验收。';
 const sheetNumbers={};for(const s of stockPlan.sheets){sheetNumbers[s.asset_id]=(sheetNumbers[s.asset_id]||0)+1;const o=element('option',stockLabels[s.asset_id]+' · 第 '+sheetNumbers[s.asset_id]+' 片 · 厚 '+mm(s.thickness_m)+' mm');o.value=s.id;$('stock-sheet').append(o)}
 for(const t of stockPlan.tubes)$('stock-tubes').append(element('p',(t.id.includes('white')?'白色':'黑色')+'装置 · '+(t.asset_id==='pe_tube_stock'?'PE':t.asset_id==='frame_profile_stock'?'立柱铝':'遮罩铝')+'管，内径 '+mm(t.inner_diameter_m)+' / 外径 '+mm(t.outer_diameter_m)+' mm：原长 '+mm(t.raw_length_m)+' → 成品 '+mm(t.finished_length_m)+' mm，另留 '+mm(t.cut_allowance_m)+' mm 切割余量。'));
 for(const p of stockPlan.profiles)$('stock-profiles').append(element('p',(p.id.includes('white')?'白色':'黑色')+'装置 · '+(p.id.endsWith('left')?'左':'右')+'侧 20-2020 型材，选定采购长度 '+mm(p.length_m)+' mm；未验收供应公差。'));
 for(const c of stockPlan.angle_cuts)$('stock-angles').append(element('p',(c.id.includes('white')?'白色':'黑色')+'装置 · 第 '+c.id.at(-1)+' 个角铝固定片：切宽 '+mm(c.finished_length_m)+' mm，另留 '+mm(c.kerf_allowance_m)+' mm 切割余量；孔位加工未验收。'));
 $('stock-sheet').addEventListener('change',renderStock);renderStock();render();renderInstallation();document.documentElement.dataset.allocationLoaded='true';
}
start().catch(e=>{$('allocation-error').textContent=String(e);document.documentElement.dataset.allocationLoaded='error'});
