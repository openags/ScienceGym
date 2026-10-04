/* Unit smoke tests against a minimal mocked DOM. Not browser/visual QA. */
'use strict';const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');const ROOT=path.resolve(__dirname,'..');
class El{constructor(tag){this.tagName=tag;this.attrs={};this.children=[];this.style={setProperty(){}};this.dataset={};this.hidden=false;this.value='';this.className='';this.classList={toggle:(name,on)=>{let s=new Set(this.className.split(' ').filter(Boolean));on?s.add(name):s.delete(name);this.className=[...s].join(' ');}};}setAttribute(k,v){this.attrs[k]=String(v);if(k.startsWith('data-'))this.dataset[k.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=String(v);if(k==='value')this.value=v;}append(...x){this.children.push(...x);}replaceChildren(...x){this.children=x;}set textContent(v){this.text=String(v);this.children=[];}get textContent(){return this.text||'';}}
const ids=[...fs.readFileSync(path.join(ROOT,'index.html'),'utf8').matchAll(/\bid="([^"]+)"/g)].map(x=>x[1]);const elements=Object.fromEntries(ids.map(id=>[id,new El('div')]));['route','dependencies','contract'].forEach(tab=>{elements['tab-'+tab].setAttribute('role','tab');elements['tab-'+tab].setAttribute('data-tab',tab);});
const walk=(roots)=>roots.flatMap(n=>n instanceof El?[n,...walk(n.children)]:[]);const document={documentElement:new El('html'),getElementById:id=>elements[id],createElement:tag=>new El(tag),createTextNode:t=>String(t),querySelectorAll:selector=>{const all=walk(Object.values(elements));if(selector==='nav button')return elements.families.children;if(selector==='[role=tab]')return all.filter(x=>x.attrs.role==='tab');if(selector==='.operation')return all.filter(x=>x.className.split(' ').includes('operation'));throw Error('Unimplemented selector '+selector);}};
const data={};for(const key of ['chiral','microscopy','fibre','thermoelectric','dispim','acoustic','perovskite','prismatic','emvp','cooling','wavefront','bianisotropic','edge','origami_memory','ring_origami','mechanical_backprop','granular_assembly','beaded','thermal_jamming','horn_acoustics','mechanical_logic','cold_shape','gear','hydrogel_optical','atmospheric_optics','afm_metrology','martian_geophysics','transistor','laser_control','solar_water','sucrose_metrology','actuator_metrology','woven','lockable_origami','varactor','wetting'])data[key]=JSON.parse(fs.readFileSync(path.join(ROOT,'data',key+'.json'),'utf8'));
let hash='',onHash;const location={get hash(){return hash;},set hash(value){hash=value.startsWith('#')?value:'#'+value;if(onHash)onHash();}};const window={SCIENCEGYM_DATA:data,addEventListener:(n,fn)=>{if(n==='hashchange')onHash=fn;}};const context={window,document,location,console,atob,Uint8Array,Blob:class{constructor(parts,options){this.parts=parts;this.options=options;}},URL:{createObjectURL:()=> 'blob:mock-test',revokeObjectURL:()=>{}}};vm.createContext(context);if(process.argv[2]){const standalone=fs.readFileSync(process.argv[2],'utf8');for(const match of standalone.matchAll(/<script>([\s\S]*?)<\/script>/g))vm.runInContext(match[1],context);}else{vm.runInContext(fs.readFileSync(path.join(ROOT,'app.js'),'utf8'),context);}let routeCount=0,occurrenceCount=0;
for(const [key,f]of Object.entries(window.ScienceGymExplorer.data)){for(const r of f.routes){location.hash=[key,r.id,'',0].join('/');const state=window.ScienceGymExplorer.state;assert.strictEqual(state.family,key);assert.strictEqual(state.route,r.id);assert(state.steps.length>0||r.route_kind==='numerical'||r.metadata_only);assert.strictEqual(document.querySelectorAll('.operation').length,state.steps.length);assert.strictEqual(document.querySelectorAll('.operation').filter(x=>x.attrs['aria-pressed']==='true').length,state.steps.length?1:0);if(state.steps.length){const last=state.steps[state.steps.length-1];location.hash=[key,r.id,last.id,last.index].join('/');assert.strictEqual(state.op,last.id);assert.strictEqual(state.occurrence,last.index);}else{assert.strictEqual(state.op,null);}routeCount++;occurrenceCount+=state.steps.length;}}
location.hash='dispim/D-R01/P001/7';assert.strictEqual(window.ScienceGymExplorer.state.op,'P001');let ps=window.ScienceGymExplorer.state.steps.filter(s=>s.id==='P001');assert.strictEqual(ps.length,2);location.hash=['dispim','D-R01','P001',ps[1].index].join('/');assert.strictEqual(window.ScienceGymExplorer.state.occurrence,ps[1].index);
elements.operationSearch.oninput({target:{value:'inventory'}});assert(document.querySelectorAll('.operation').some(x=>x.className.includes('match')));elements.operationSearch.oninput({target:{value:''}});assert(!document.querySelectorAll('.operation').some(x=>x.className.includes('match')));
elements['tab-dependencies'].onclick();assert.strictEqual(elements.routeView.hidden,true);assert.strictEqual(elements.dependenciesView.hidden,false);elements['tab-route'].onclick();assert.strictEqual(elements.routeView.hidden,false);
location.hash='perovskite/SPIN_MODULES';
const depTexts=walk([elements.dependenciesView]).map(x=>x.textContent);
assert(depTexts.some(x=>x.includes('P1 before module layers')),'Text partial-order rule must be visible');
assert(!depTexts.includes('undefined'),'Do not render string constraints as undefined edges');
// Prismatic partial-order membership has no chronological adjacency arrows.
for(const r of window.ScienceGymExplorer.data.prismatic.routes){
 location.hash=['prismatic',r.id].join('/');
 const nodes=walk([elements.routeCanvas]);
 assert(!nodes.some(x=>x.className.split(' ').includes('connector')),r.id+' invented an adjacency edge');
 assert(!nodes.some(x=>x.textContent.includes('undefined')),r.id+' has an undefined loop binding');
 assert(window.ScienceGymExplorer.state.steps.some(s=>s.id==='QUARANTINE'),'Conditional recovery must be inspectable');
}
location.hash='prismatic/CUBE_HINGE_COMPARISON';
let prismaticText=walk([elements.routeCanvas]).map(x=>x.textContent).join('\n');
assert(prismaticText.includes('hinge_material'));
assert(prismaticText.includes('target_attempts'));
assert(prismaticText.includes('attempts_per_target'));
assert(prismaticText.includes('Between conditions only'));
assert(prismaticText.includes('Conditional recovery only'));
const quarantine=window.ScienceGymExplorer.state.steps.find(s=>s.id==='QUARANTINE');
location.hash=['prismatic','CUBE_HINGE_COMPARISON','QUARANTINE',quarantine.index].join('/');
assert.strictEqual(window.ScienceGymExplorer.state.op,'QUARANTINE');
// Navigation and repeated clicks never execute or count the template as complete.
const before=JSON.stringify(window.ScienceGymExplorer.data.prismatic);
document.querySelectorAll('.operation').at(-1).onclick();
document.querySelectorAll('.operation').at(-1).onclick();
assert.strictEqual(JSON.stringify(window.ScienceGymExplorer.data.prismatic),before);
elements['tab-dependencies'].onclick();
assert(walk([elements.dependenciesView]).some(x=>x.textContent.includes('Declared template prerequisites')));
elements['tab-contract'].onclick();
assert(walk([elements.contractView]).some(x=>x.textContent==='source conflicts'));
assert(walk([elements.contractView]).some(x=>x.textContent==='RELEASE BOUNDARY'));
location.hash='prismatic/PNEUMATIC_TWO_POUCH';
assert.strictEqual(elements.routeView.hidden,false);
assert(walk([elements.routeCanvas]).some(x=>x.textContent.includes('attempts_per_program')));
// EmVP memberships retain source condition dispatch without adjacency arrows.
for(const r of window.ScienceGymExplorer.data.emvp.routes){
 location.hash=['emvp',r.id].join('/');
 const nodes=walk([elements.routeCanvas]);
 assert(!nodes.some(x=>x.className.split(' ').includes('connector')),r.id+' invented an adjacency edge');
 assert(!nodes.some(x=>x.textContent.includes('undefined')),r.id+' has undefined metadata');
}
location.hash='emvp/CONTROL_SINGLE_MATERIAL_CAGE';
const emvpText=walk([elements.routeCanvas]).map(x=>x.textContent).join('\n');
for(const name of ['Condition Mat1-only','Condition Mat2-only','Condition combined-material','specimen count unknown'])assert(emvpText.includes(name));
assert.strictEqual(window.ScienceGymExplorer.state.steps.filter(x=>x.id==='O_VAM_DIRECT').length,2);
assert.strictEqual(window.ScienceGymExplorer.state.steps.filter(x=>x.id==='O_DEPOSIT_POS').length,1);
assert.strictEqual(window.ScienceGymExplorer.state.steps.filter(x=>x.id==='O_PLAN').length,3);
const emvpBefore=JSON.stringify(window.ScienceGymExplorer.data.emvp);
const directSteps=window.ScienceGymExplorer.state.steps.filter(x=>x.id==='O_VAM_DIRECT');
location.hash=['emvp','CONTROL_SINGLE_MATERIAL_CAGE','O_VAM_DIRECT',directSteps[1].index].join('/');
assert.strictEqual(window.ScienceGymExplorer.state.occurrence,directSteps[1].index);
document.querySelectorAll('.operation').at(-1).onclick();document.querySelectorAll('.operation').at(-1).onclick();
assert.strictEqual(JSON.stringify(window.ScienceGymExplorer.data.emvp),emvpBefore);
elements['tab-dependencies'].onclick();
const emvpDeps=walk([elements.dependenciesView]).map(x=>x.textContent).join('\n');
assert(emvpDeps.includes('Conditional prerequisites'));assert(emvpDeps.includes('D_DIRECT'));assert(emvpDeps.includes('selected single-material or pure-VAM condition'));
assert(!emvpDeps.includes('undefined'));
elements['tab-contract'].onclick();assert(walk([elements.contractView]).some(x=>x.textContent==='source conflicts'));
location.hash='emvp/POSITIVE_HELIX/O_PLAN/0';
const inspectorText=walk([elements.inspector]).map(x=>x.textContent).join('\n');
assert(inspectorText.includes('No postconditions field supplied'));
assert(inspectorText.includes('M_SCOPE'));
assert(inspectorText.includes('Results and Discussion'));
elements.operationSearch.oninput({target:{value:'U_GEOMETRY'}});assert(document.querySelectorAll('.operation').some(x=>x.className.includes('match')));
location.hash='emvp/CONTROL_VAM_NEGATIVE';assert.strictEqual(elements.routeView.hidden,false);assert.strictEqual(elements.operationSearch.value,'');
// Cooling leaves retain membership, symbolic schedules, receipt gates and transport.
for(const r of window.ScienceGymExplorer.data.cooling.routes){
 location.hash=['cooling',r.id].join('/');
 const nodes=walk([elements.routeCanvas]);
 assert(!nodes.some(x=>x.className.split(' ').includes('connector')),r.id+' invented chronological adjacency');
 assert(!nodes.some(x=>x.textContent.includes('undefined')),r.id+' has undefined metadata');
 assert.strictEqual(window.ScienceGymExplorer.state.steps.length,r.detail.operation_ids.length);
 assert.deepStrictEqual(Array.from(window.ScienceGymExplorer.state.steps,s=>s.id),Array.from(r.detail.operation_ids));
 assert(nodes.some(x=>x.textContent.includes('L_REPEAT')));
 assert(nodes.some(x=>x.textContent.includes('physical MOVE instance')));
}
location.hash='cooling/MAP_CLEAR_NIGHT';
assert(!window.ScienceGymExplorer.state.steps.some(x=>x.id==='TRACK_ADJUST'));
assert(!walk([elements.routeCanvas]).some(x=>x.textContent.includes('L_TRACK')));
assert(walk([elements.routeCanvas]).some(x=>x.textContent.includes('Three independent condition leaves')));
location.hash='cooling/PID_POWER';
assert(walk([elements.routeCanvas]).some(x=>x.textContent.includes('L_PID')));
const coolingBefore=JSON.stringify(window.ScienceGymExplorer.data.cooling);
document.querySelectorAll('.operation').at(-1).onclick();document.querySelectorAll('.operation').at(-1).onclick();
assert.strictEqual(JSON.stringify(window.ScienceGymExplorer.data.cooling),coolingBefore);
elements['tab-dependencies'].onclick();
const coolingDeps=walk([elements.dependenciesView]).map(x=>x.textContent).join('\n');
for(const text of ['Conditional receipt gates','Current assembly revision','prior STEP_SUMMARY','requires_one_complete_family','Required physical transport'])assert(coolingDeps.includes(text),text);
elements['tab-contract'].onclick();
for(const text of ['unknowns','independent review','source conflicts','lineage'])assert(walk([elements.contractView]).some(x=>x.textContent===text));
location.hash='cooling/BUILD_PAIR';
const fab=window.ScienceGymExplorer.state.steps.find(x=>x.id==='FAB_RUN');
location.hash=['cooling','BUILD_PAIR','FAB_RUN',fab.index].join('/');
const coolingInspector=walk([elements.inspector]).map(x=>x.textContent).join('\n');
assert(coolingInspector.includes('Device process · separate from operator manipulation'));
assert(coolingInspector.includes('E_BUILD'));
assert(coolingInspector.includes('Note 2, PDF p13'));
elements.operationSearch.oninput({target:{value:'U_FAB'}});assert(document.querySelectorAll('.operation').some(x=>x.className.includes('match')));
location.hash='cooling/OPT_ANGULAR';assert.strictEqual(elements.routeView.hidden,false);assert.strictEqual(elements.operationSearch.value,'');
location.hash='bad-family/bad-route';assert.strictEqual(window.ScienceGymExplorer.state.family,'chiral');location.hash='#%invalid';assert.strictEqual(window.ScienceGymExplorer.state.family,'chiral');
console.log(`PASS: mocked-DOM rendering of ${routeCount} routes / ${occurrenceCount} displayed operation occurrences; selection, repeated IDs, search, tabs and malformed-hash fallback`);

// Three acoustic schemas: physical/numerical isolation, all endpoints, no stale selection.
for(const key of ['wavefront','bianisotropic','edge']){
 const f=window.ScienceGymExplorer.data[key],before=JSON.stringify(f);
 for(const r of f.routes){
  location.hash=[key,r.id].join('/');
  assert(!walk([elements.routeCanvas]).some(x=>x.className.split(' ').includes('connector')));
  assert(!walk([elements.dependenciesView]).some(x=>x.textContent.includes('undefined')));
  assert(elements.routeBadge.textContent.includes(r.route_kind.toUpperCase()));
  if(r.route_kind==='numerical'){
   assert(elements.routeTitle.textContent.includes('NOT RUN'));
   if(!window.ScienceGymExplorer.state.steps.length){
    assert.strictEqual(window.ScienceGymExplorer.state.op,null);
    assert(walk([elements.inspector]).some(x=>x.textContent.includes('no operation-ID route')));
    elements.operationSearch.oninput({target:{value:'source'}});
    assert.strictEqual(elements.searchCount.textContent,'0 matches');
   }else{
    assert(window.ScienceGymExplorer.state.steps.every(x=>x.op.detail.kind==='digital_job'));
   }
  }
  elements['tab-dependencies'].onclick();elements['tab-contract'].onclick();elements['tab-route'].onclick();
  location.hash=[key,r.id].join('/');
 }
 assert.strictEqual(JSON.stringify(f),before);
}
location.hash='edge/F_GUIDE';
const transfers=window.ScienceGymExplorer.state.steps.filter(x=>x.id==='TRANSFER');
assert.strictEqual(transfers.length,4);
location.hash=['edge','F_GUIDE','TRANSFER',transfers[3].index].join('/');
assert.strictEqual(window.ScienceGymExplorer.state.occurrence,transfers[3].index);
location.hash='edge/F_TARGET';
const alternatives=walk([elements.routeCanvas]).map(x=>x.textContent).join('\n');
assert(alternatives.includes('Exclusive alternatives'));assert(alternatives.includes('supplied_part'));
assert(alternatives.includes('manufactured_in_episode'));
location.hash='edge/SINGLE_EDGE_1D';
const physicalHash=location.hash;
document.querySelectorAll('.operation')[0].onclick();document.querySelectorAll('.operation')[0].onclick();
location.hash='edge/N_FE_1D';assert.strictEqual(window.ScienceGymExplorer.state.op,null);
location.hash=physicalHash;assert(window.ScienceGymExplorer.state.op);
location.hash='wavefront/N_COUPLE';assert.strictEqual(window.ScienceGymExplorer.state.op,null);
location.hash='wavefront/N_COUPLE/ARRAY_LOAD/0';assert.strictEqual(window.ScienceGymExplorer.state.op,null);
location.hash='bianisotropic/RETRIEVAL_NUMERICAL';
assert(!window.ScienceGymExplorer.state.steps.some(x=>x.id==='MIC_CAL'));
console.log('PASS: acoustic boundary navigation, empty dispositions, repeated transfers, alternatives, tabs, state immutability and hash-history restoration');

// Mechanical source grammars, metadata-only dispositions and per-display bindings.
for(const key of ['origami_memory','ring_origami','mechanical_backprop']){
 const f=window.ScienceGymExplorer.data[key],before=JSON.stringify(f);
 for(const r of f.routes){
  location.hash=[key,r.id].join('/');
  assert(elements.routeBadge.textContent.includes(r.route_kind.toUpperCase()));
  assert(!walk([elements.routeCanvas,elements.dependenciesView,elements.inspector]).some(x=>x.textContent.includes('undefined')));
  if(r.metadata_only){
   assert.strictEqual(window.ScienceGymExplorer.state.op,null);
   assert.strictEqual(window.ScienceGymExplorer.state.steps.length,0);
   assert(walk([elements.inspector]).some(x=>x.textContent.includes('no operation-ID route')));
   elements.operationSearch.oninput({target:{value:'force'}});assert.strictEqual(elements.searchCount.textContent,'0 matches');
  }else{
   document.querySelectorAll('.operation')[0].onclick();document.querySelectorAll('.operation')[0].onclick();
  }
  if(key==='origami_memory')assert(!walk([elements.routeCanvas]).some(x=>x.className.split(' ').includes('connector')));
  elements['tab-dependencies'].onclick();elements['tab-contract'].onclick();elements['tab-route'].onclick();
 }
 assert.strictEqual(JSON.stringify(f),before);
}
location.hash='ring_origami/TRI_TORSION';
assert(walk([elements.routeCanvas]).some(x=>x.textContent.includes('not direct torque measurement')));
location.hash='ring_origami/ELEMENT_RESPONSE';
assert(walk([elements.routeCanvas]).some(x=>x.textContent.includes('Concurrent source obligations')));
elements['tab-dependencies'].onclick();
assert(walk([elements.dependenciesView]).some(x=>x.textContent.includes('D_TORQUE')));
location.hash='ring_origami/PREP_THICK';
assert(walk([elements.routeCanvas]).some(x=>x.textContent.includes('Conditional postprocessing only')));
const ringTransfers=window.ScienceGymExplorer.state.steps.filter(x=>x.id==='TRANSFER');assert(ringTransfers.length>2);
location.hash=['ring_origami','PREP_THICK','TRANSFER',ringTransfers.at(-1).index].join('/');
assert(walk([elements.inspector]).some(x=>x.textContent.includes('Source occurrence binding')));
assert(walk([elements.inspector]).some(x=>x.textContent.includes('WS_ASSEMBLY')));
location.hash='mechanical_backprop/GRADIENT_SEPARATE';
const phases=window.ScienceGymExplorer.state.steps.filter(x=>x.id==='BASELINE');assert.strictEqual(phases.length,2);
assert.strictEqual(phases[0].sourceOccurrence.source_node.bindings.active_force_role,'forward_only');
assert.strictEqual(phases[1].sourceOccurrence.source_node.bindings.active_force_role,'adjoint_only');
location.hash=['mechanical_backprop','GRADIENT_SEPARATE','BASELINE',phases[1].index].join('/');
assert.strictEqual(window.ScienceGymExplorer.state.occurrence,phases[1].index);
assert(walk([elements.inspector]).some(x=>x.textContent.includes('adjoint_only')));
const phaseHash=location.hash;
location.hash='mechanical_backprop/N_SWITCH/BASELINE/0';assert.strictEqual(window.ScienceGymExplorer.state.op,null);
location.hash=phaseHash;assert.strictEqual(window.ScienceGymExplorer.state.occurrence,phases[1].index);
location.hash='mechanical_backprop/REGRESSION_SWEEP';
assert(walk([elements.routeCanvas]).some(x=>x.textContent.includes('mass_g')));
const moves=window.ScienceGymExplorer.state.steps.filter(x=>x.id==='MOVE');assert.strictEqual(moves.length,10);
location.hash=['mechanical_backprop','REGRESSION_SWEEP','MOVE',moves.at(-1).index].join('/');
assert(walk([elements.inspector]).some(x=>x.textContent.includes('transfer_contract')));
assert(walk([elements.inspector]).some(x=>x.textContent.includes('source_station')));
location.hash='ring_origami/N_TORQUE_DERIVATION';assert.strictEqual(window.ScienceGymExplorer.state.op,null);
assert(elements.routeTitle.textContent.includes('NOT DIRECT MEASUREMENT'));
location.hash='origami_memory/N_FREQ';assert.strictEqual(window.ScienceGymExplorer.state.op,null);
assert(elements.routeTitle.textContent.includes('NOT IMPLEMENTED'));
console.log('PASS: mechanical nested templates, qualified dependency rules, occurrence bindings, numerical/proposal/analysis isolation, repeated transfers, empty selections and immutable navigation');

// Assembly schemas: typed exclusive choices, scoped DAGs, source gates and empty nonmanual views.
for(const key of ['granular_assembly','beaded','thermal_jamming']){
 const f=window.ScienceGymExplorer.data[key],before=JSON.stringify(f);
 for(const r of f.routes){
  location.hash=[key,r.id].join('/');
  assert(elements.routeBadge.textContent.includes(r.route_kind.toUpperCase()));
  assert(!walk([elements.routeCanvas,elements.dependenciesView,elements.inspector]).some(x=>x.textContent.includes('undefined')));
  if(r.metadata_only){
   assert.strictEqual(window.ScienceGymExplorer.state.op,null);
   assert.strictEqual(window.ScienceGymExplorer.state.steps.length,0);
   elements.operationSearch.oninput({target:{value:'sample'}});assert.strictEqual(elements.searchCount.textContent,'0 matches');
  }else{
   const first=window.ScienceGymExplorer.state.steps[0],last=window.ScienceGymExplorer.state.steps.at(-1);
   location.hash=[key,r.id,last.id,last.index].join('/');
   document.querySelectorAll('.operation').at(-1).onclick();document.querySelectorAll('.operation').at(-1).onclick();
   assert.strictEqual(window.ScienceGymExplorer.state.occurrence,last.index);
   location.hash=[key,r.id,first.id,first.index].join('/');
  }
  if(key!=='beaded'&&r.route_kind==='physical'){
   assert(!walk([elements.routeCanvas]).some(x=>x.className.split(' ').includes('connector')));
   assert.deepStrictEqual(Array.from(window.ScienceGymExplorer.state.steps,s=>s.id),Array.from(r.detail.operation_ids));
  }
  elements['tab-dependencies'].onclick();elements['tab-contract'].onclick();elements['tab-route'].onclick();
 }
 assert.strictEqual(JSON.stringify(f),before);
}
location.hash='beaded/ANGLE_SWATCHES';
const beadedText=walk([elements.routeCanvas]).map(x=>x.textContent).join('\n');
for(const t of ['Exclusive alternatives','robot_enclosed_preparation','qualified_supplied_part','robot_weave','preassembled','already_at_WS_WEAVE','Conditional recovery only','block_affected_loop_never_expand_as_zero_success'])assert(beadedText.includes(t),t);
const beadedMoves=window.ScienceGymExplorer.state.steps.filter(x=>x.id==='MOVE');assert(beadedMoves.length>3);
const lastBeadedMove=beadedMoves.at(-1);location.hash=['beaded','ANGLE_SWATCHES','MOVE',lastBeadedMove.index].join('/');
assert.strictEqual(window.ScienceGymExplorer.state.occurrence,lastBeadedMove.index);
assert(walk([elements.inspector]).some(x=>x.textContent.includes('Source occurrence binding')));
assert(walk([elements.inspector]).some(x=>x.textContent.includes('Tools · exact source roles')));
const beadedHash=location.hash;
location.hash='beaded/N_CAPSTAN/MOVE/0';assert.strictEqual(window.ScienceGymExplorer.state.op,null);
location.hash=beadedHash;assert.strictEqual(window.ScienceGymExplorer.state.occurrence,lastBeadedMove.index);
location.hash='beaded/WHOLE_PAPER_PRACTICAL';
assert.deepStrictEqual(Array.from(window.ScienceGymExplorer.state.steps,s=>s.id),['QUARANTINE']);
assert(walk([elements.routeCanvas]).some(x=>x.textContent.includes('No universal specimen')));
location.hash='granular_assembly/TRAPPED_COLLISION';
assert(walk([elements.routeCanvas]).some(x=>x.textContent.includes('Stage1')));
assert(walk([elements.routeCanvas]).some(x=>x.textContent.includes('POSTCURE')));
elements['tab-dependencies'].onclick();assert(walk([elements.dependenciesView]).some(x=>x.textContent.includes('TRAPPED_COLLISION · scoped')));
location.hash='thermal_jamming/TEMP_PHI';
assert(walk([elements.routeCanvas]).some(x=>x.textContent.includes('optional_cold_arm')));
assert(walk([elements.inspector]).some(x=>x.textContent.includes('Device process · separate from robot manipulation')));
location.hash='thermal_jamming/CYCLE_PULL';
assert(walk([elements.routeCanvas]).some(x=>x.textContent.includes('Final REINSERT may be omitted only')));
location.hash='thermal_jamming/SCOPE_COMPUTATIONAL_ONLY/PLAN/0';assert.strictEqual(window.ScienceGymExplorer.state.op,null);
location.hash='thermal_jamming/SCOPE_DEVICE_OWNED';assert.strictEqual(window.ScienceGymExplorer.state.op,null);
assert(elements.routeTitle.textContent.includes('NOT ROBOT LABOR'));
location.hash='thermal_jamming/SCOPE_REFERENCE_ONLY';assert.strictEqual(window.ScienceGymExplorer.state.op,null);
console.log('PASS: assembly exclusive preparation/custody choices, scoped causal gates, symbolic loops, numerical/device isolation, repeated bindings, empty selections, immutable navigation and hash restoration');

// Final source packages: membership, source incompleteness, closed services and analysis isolation.
for(const key of ['horn_acoustics','mechanical_logic','cold_shape']){
 const f=window.ScienceGymExplorer.data[key],before=JSON.stringify(f);
 for(const r of f.routes){
  location.hash=[key,r.id].join('/');
  assert(elements.routeBadge.textContent.includes(r.route_kind.toUpperCase()));
  assert(!walk([elements.routeCanvas]).some(x=>x.className.split(' ').includes('connector')));
  assert(!walk([elements.routeCanvas,elements.dependenciesView,elements.inspector]).some(x=>x.textContent.includes('undefined')));
  if(r.metadata_only){
   assert.strictEqual(window.ScienceGymExplorer.state.op,null);
   assert.strictEqual(window.ScienceGymExplorer.state.steps.length,0);
   elements.operationSearch.oninput({target:{value:'sample'}});assert.strictEqual(elements.searchCount.textContent,'0 matches');
  }else{
   assert.deepStrictEqual(Array.from(window.ScienceGymExplorer.state.steps,s=>s.id),Array.from(r.detail.operation_ids));
   const first=window.ScienceGymExplorer.state.steps[0],last=window.ScienceGymExplorer.state.steps.at(-1);
   location.hash=[key,r.id,last.id,last.index].join('/');
   document.querySelectorAll('.operation').at(-1).onclick();document.querySelectorAll('.operation').at(-1).onclick();
   assert.strictEqual(window.ScienceGymExplorer.state.occurrence,last.index);
   location.hash=[key,r.id,first.id,first.index].join('/');
  }
  elements['tab-dependencies'].onclick();elements['tab-contract'].onclick();elements['tab-route'].onclick();
 }
 assert.strictEqual(JSON.stringify(f),before);
}
location.hash='horn_acoustics/B_WITH';
assert(elements.routeBasis.textContent.includes('190 positions and ten technical readouts'));
assert(walk([elements.routeCanvas]).some(x=>x.textContent.includes('ten valid technical-readout slots')));
location.hash='horn_acoustics/B_COMPARE_CLOSE';
assert(elements.routeTitle.textContent.includes('PHYSICAL / DERIVED ANALYSIS CLOSURE'));
const hornClosureHash=location.hash;
location.hash='horn_acoustics/N_FOCUS/POINT_READ/0';assert.strictEqual(window.ScienceGymExplorer.state.op,null);
location.hash=hornClosureHash;assert.strictEqual(window.ScienceGymExplorer.state.route,'B_COMPARE_CLOSE');
location.hash='mechanical_logic/NOR';
assert(elements.routeBasis.textContent.includes('source_complete is false'));
assert(elements.routeBasis.textContent.includes('Main figure panels and actual movie contents remain uninspected'));
assert(walk([elements.routeCanvas]).some(x=>x.textContent.includes('new_verified_AU_reset_before_each_independent_case')));
location.hash='mechanical_logic/VOLATILE_STORAGE';
assert(walk([elements.routeCanvas]).some(x=>x.textContent.includes('no_power_gap_during_hold')));
location.hash='mechanical_logic/MICROSCALE_MEMS/PLAN/0';assert.strictEqual(window.ScienceGymExplorer.state.op,null);
assert(elements.routeTitle.textContent.includes('NOT IMPLEMENTED'));
location.hash='cold_shape/RESIN_BATCH/RESIN_WAIT/7';
assert.strictEqual(window.ScienceGymExplorer.state.op,'RESIN_WAIT');
assert(walk([elements.inspector]).some(x=>x.textContent.includes('Closed qualified service process')));
assert(walk([elements.inspector]).some(x=>x.textContent.includes('qualified_closed_service')));
assert(walk([elements.inspector]).some(x=>x.textContent.includes('Conditional postconditions')));
assert(walk([elements.routeCanvas]).some(x=>x.textContent.includes('Service owns all opening, mixing and waste-contact operations')));
location.hash='cold_shape/MEMORY_TEN_CYCLES';
assert(walk([elements.routeCanvas]).some(x=>x.textContent.includes('apply only the stated source scope')));
assert(walk([elements.routeCanvas]).some(x=>x.textContent.includes('required_phase_order')));
location.hash='cold_shape/N_DMA_FIT/PLAN/0';assert.strictEqual(window.ScienceGymExplorer.state.op,null);
assert(elements.routeTitle.textContent.includes('NOT INDEPENDENT VALIDATION'));
assert(elements.routeBasis.textContent.includes('source workbook remain uninspected'));
location.hash='cold_shape/N_FEA';assert.strictEqual(window.ScienceGymExplorer.state.op,null);
console.log('PASS: final materials membership, technical/independent counts, ReMM source-incomplete and unread-media boundaries, symbolic repeats, closed hazardous services, derived-fit isolation, immutable navigation and empty-view clearing');

// Gear and hydrogel: source procedure grammar versus authored navigation.
let natureRoutes=0,natureEntries=0,natureSelections=0;
for(const key of ['gear','hydrogel_optical']){
 const f=window.ScienceGymExplorer.data[key],before=JSON.stringify(f);
 for(const r of f.routes){
  location.hash=[key,r.id].join('/');natureRoutes++;
  const state=window.ScienceGymExplorer.state,all=walk([elements.routeCanvas]),entries=state.steps.length;
  natureEntries+=entries;
  assert.strictEqual(elements.routeView.hidden,false);
  assert.strictEqual(state.op,entries?state.steps[0].id:null);
  assert.strictEqual(r.metadata_only,entries===0);
  assert(elements.routeBasis.textContent.includes('Authored navigation'));
  assert(!all.some(x=>x.textContent.includes('undefined')));
  const connectors=all.filter(x=>x.className.split(' ').includes('connector'));
  if(key==='gear'&&['physical','preparation'].includes(r.route_kind))assert.strictEqual(connectors.length,entries-1,'Gear authored recipe order lost');
  else assert.strictEqual(connectors.length,0,'Invented operation adjacency');
  if(key==='hydrogel_optical'&&r.route_kind==='physical'){
   assert.deepStrictEqual(Array.from(state.steps,s=>s.id),Array.from(r.detail.operation_ids));
   assert(r.controls.some(c=>c.id==='CTRL_BASELINE'));
   assert(all.some(x=>x.textContent.includes('Per-service phase order only')));
   assert(elements.routeBasis.textContent.includes('CLOSED QUALIFIED SERVICES ONLY'));
  }
  for(let i=0;i<entries;i++){
   const step=state.steps[i];location.hash=[key,r.id,step.id,i].join('/');natureSelections++;
   assert.strictEqual(state.occurrence,i);assert.strictEqual(state.op,step.id);
   const texts=walk([elements.inspector]).map(x=>x.textContent).join('\n');
   assert(texts.includes('Source-defined actions'));
   if(key==='gear'&&['physical','preparation'].includes(r.route_kind)){
    assert(texts.includes('Source occurrence binding'));
    if(step.id==='TRANSFER')assert(texts.includes(step.sourceOccurrence.source_node.destination_station));
   }
   if(key==='hydrogel_optical')assert(texts.includes('Closed qualified service process'));
  }
  if(entries){document.querySelectorAll('.operation')[0].onclick();document.querySelectorAll('.operation')[0].onclick();}
  elements['tab-dependencies'].onclick();assert.strictEqual(elements.dependenciesView.hidden,false);
  const deps=walk([elements.dependenciesView]).map(x=>x.textContent).join('\n');
  assert(deps.includes(key==='gear'?'Typed recipe dependency graph':'service phase order'));
  elements['tab-contract'].onclick();const contracts=walk([elements.contractView]).map(x=>x.textContent).join('\n');
  for(const required of ['unknowns','source conflicts','source access audit','lineage'])assert(contracts.includes(required));
  assert.strictEqual(JSON.stringify(f),before,'Inspection mutated source data');
 }
}
assert.strictEqual(natureRoutes,77);
location.hash='gear/TAIJI_PLUS';
const gearTransfers=window.ScienceGymExplorer.state.steps.filter(s=>s.id==='TRANSFER');assert(gearTransfers.length>1);
for(const step of gearTransfers){location.hash=['gear','TAIJI_PLUS',step.id,step.index].join('/');assert.strictEqual(window.ScienceGymExplorer.state.occurrence,step.index);}
location.hash='gear/N_CONTACT/NUMERICAL_RUN/1';assert.strictEqual(window.ScienceGymExplorer.state.op,'NUMERICAL_RUN');
location.hash='gear/I_MACRO_VIDEO/NUMERICAL_RUN/1';assert.strictEqual(window.ScienceGymExplorer.state.op,null);assert.strictEqual(document.querySelectorAll('.operation').length,0);
assert(elements.routeTitle.textContent.includes('ILLUSTRATIVE ONLY'));
location.hash='hydrogel_optical/BEAM_POWER';elements.operationSearch.oninput({target:{value:'U_SCENE'}});assert(document.querySelectorAll('.operation').some(x=>x.className.includes('match')));
location.hash='hydrogel_optical/N_FITS/FORM_LOAD/3';assert.strictEqual(window.ScienceGymExplorer.state.op,null);assert.strictEqual(elements.operationSearch.value,'');
assert(elements.routeBasis.textContent.includes('four Extended Data image sets remain uninspected'));
assert(elements.routeBasis.textContent.includes('Video 9 is accelerated 20 times'));
location.hash='hydrogel_optical/NO_SUCH_ROUTE';assert.strictEqual(window.ScienceGymExplorer.state.route,'BEAM_POWER');
console.log(`PASS: Nature Materials ${natureRoutes} records / ${natureEntries} display entries / ${natureSelections} individual selections; exact gear order and transfers, hydrogel membership, closed-service and nonphysical boundaries, no source mutation`);

// Cross-disciplinary source scopes, all entries, empty views and read-only navigation.
let crossRoutes=0,crossEntries=0,crossSelections=0;
for(const key of ['atmospheric_optics','afm_metrology','martian_geophysics','transistor']){
 const f=window.ScienceGymExplorer.data[key],before=JSON.stringify(f);
 for(const r of f.routes){
  location.hash=[key,r.id].join('/');crossRoutes++;
  const state=window.ScienceGymExplorer.state,all=walk([elements.routeCanvas]),entries=state.steps.length;crossEntries+=entries;
  assert.strictEqual(state.op,entries?state.steps[0].id:null);assert.strictEqual(r.metadata_only,entries===0);
  assert(!all.some(x=>x.className.split(' ').includes('connector')),'Invented cross-disciplinary chronology');
  assert(!all.some(x=>x.textContent.includes('undefined')));
  if(r.source_file==='branches.json')assert.deepStrictEqual(Array.from(state.steps,x=>x.id),Array.from(r.detail.operation_ids));
  for(let i=0;i<entries;i++){
   const step=state.steps[i];location.hash=[key,r.id,step.id,i].join('/');crossSelections++;
   assert.strictEqual(state.op,step.id);assert.strictEqual(state.occurrence,i);
   const text=walk([elements.inspector]).map(x=>x.textContent).join('\n');
   assert(text.includes('Source-defined actions'));assert(text.includes(step.op.source_pointer));
   assert(!text.includes('undefined'));
  }
  if(entries){document.querySelectorAll('.operation')[0].onclick();document.querySelectorAll('.operation')[0].onclick();}
  elements['tab-dependencies'].onclick();assert.strictEqual(elements.dependenciesView.hidden,false);
  elements['tab-contract'].onclick();const text=walk([elements.contractView]).map(x=>x.textContent).join('\n');
  for(const required of ['source conflicts','episode input contract','lineage','control packages'])assert(text.includes(required));
  assert.strictEqual(JSON.stringify(f),before,'Navigation mutated cross-disciplinary source');
 }
}
assert.strictEqual(crossRoutes,135);
location.hash='atmospheric_optics/TIS';assert(elements.routeBadge.textContent.includes('ANALYSIS'));
assert(elements.routeBasis.textContent.includes('main figure pixels remain uninspected'));
assert(elements.routeBasis.textContent.includes('jobs and records move'));
location.hash='atmospheric_optics/SIM_WWS';assert(elements.routeBadge.textContent.includes('NUMERICAL'));
location.hash='afm_metrology/ARRAY_CAL';assert(elements.routeBasis.textContent.includes('not full fabrication'));
location.hash='afm_metrology/PREP_ARRAY';assert(elements.routeTitle.textContent.includes('INCOMPLETE'));
location.hash='afm_metrology/SESSION_TEARDOWN';assert.strictEqual(window.ScienceGymExplorer.state.op,'FINAL_SESSION_TEARDOWN');
location.hash='afm_metrology/SCOPE_NUMERICAL_ONLY_1/FINAL_SESSION_TEARDOWN/0';assert.strictEqual(window.ScienceGymExplorer.state.op,null);
location.hash='martian_geophysics/ARCHIVE';assert(elements.routeBadge.textContent.includes('DATA_CURATION'));
location.hash='martian_geophysics/SOLIDUS_FIT';assert(elements.routeBadge.textContent.includes('NUMERICAL'));
location.hash='transistor/HIGHK';assert(walk([elements.routeCanvas]).some(x=>x.textContent.includes('Canonical lifecycle catalog')));
elements.operationSearch.oninput({target:{value:'safe'}});assert(document.querySelectorAll('.operation').some(x=>x.className.includes('match')));
const crossHistory=location.hash;
location.hash='transistor/SCOPE_NUMERICAL_ONLY_1/RECEIVE/0';assert.strictEqual(window.ScienceGymExplorer.state.op,null);assert.strictEqual(elements.operationSearch.value,'');
location.hash=crossHistory;assert.strictEqual(window.ScienceGymExplorer.state.route,'HIGHK');
location.hash='transistor/NO_SUCH_ROUTE';assert.strictEqual(window.ScienceGymExplorer.state.route,'PREP');
console.log(`PASS: cross-disciplinary ${crossRoutes} records / ${crossEntries} display entries / ${crossSelections} individual selections; exact scopes, closed services, AFM teardown and bounded fabrication, no chronology, no mutation`);
// Paired source views: scope labels, source hold defaults, every operation and immutable navigation.
const pairedKeys=['laser_control','solar_water','sucrose_metrology','actuator_metrology'];
const holdDefaults={laser_control:'QUALIFICATION_HOLD',solar_water:'RECEIPT',sucrose_metrology:'FLOW_HOLD',actuator_metrology:'DIRECTION_HOLD'};
let pairedRoutes=0,pairedEntries=0,pairedSelections=0;
for(const key of pairedKeys){
 const f=window.ScienceGymExplorer.data[key],frozen=JSON.stringify(f);
 const scope=key==='laser_control'?'PAPER-LEVEL DESIGN':'BOUNDED SUBSET';
 const nav=elements.families.children.find(e=>e.dataset.family===key);assert(nav);nav.onclick();
 assert.strictEqual(window.ScienceGymExplorer.state.route,holdDefaults[key]);
 assert.strictEqual(elements.familyScope.textContent,scope);
 assert(walk([nav]).some(x=>x.textContent.includes(scope)));
 const links=walk([elements.assetLinks]).filter(x=>x.tagName==='a');
 assert.strictEqual(links.length,key==='solar_water'?0:4);
 for(const a of links)assert(a.attrs.href.includes('/f803612db28652d2e2dd574d8039c36b7136f399/assets/'));
 for(const r of f.routes){
  location.hash=[key,r.id].join('/');const all=walk([elements.routeCanvas]);
  assert(!all.some(x=>x.className.split(' ').includes('connector')),key+'/'+r.id+' invented chronology');
  assert(!all.some(x=>x.textContent.includes('undefined')),key+'/'+r.id+' has undefined source value');
  const steps=[...window.ScienceGymExplorer.state.steps];
  assert.strictEqual(document.querySelectorAll('.operation').length,steps.length);
  for(const step of steps){
   location.hash=[key,r.id,step.id,step.index].join('/');assert.strictEqual(window.ScienceGymExplorer.state.op,step.id);
   assert.strictEqual(window.ScienceGymExplorer.state.occurrence,step.index);
   const text=walk([elements.inspector]).map(x=>x.textContent).join('\n');assert(text.includes(step.id));
   assert(text.includes('Parameters and additional contract'));
   if(step.op.detail.required_output)assert(text.includes(step.op.detail.required_output));
   pairedSelections++;
  }
  if(steps.length){document.querySelectorAll('.operation').at(-1).onclick();document.querySelectorAll('.operation').at(-1).onclick();}
  elements.operationSearch.oninput({target:{value:'archive'}});assert(document.querySelectorAll('.operation').length===steps.length);
  elements['tab-contract'].onclick();const contracts=walk([elements.contractView]).map(x=>x.textContent).join('\n');
  for(const text of ['nonmanual scope','lineage','unknowns','provenance','source conflicts','episode input contract'])assert(contracts.includes(text),key+' lost '+text);
  elements['tab-dependencies'].onclick();assert.strictEqual(elements.dependenciesView.hidden,false);
  pairedRoutes++;pairedEntries+=steps.length;
 }
 location.hash=key+'/INVALID_ROUTE';assert.strictEqual(window.ScienceGymExplorer.state.route,holdDefaults[key]);
 assert.strictEqual(elements.operationSearch.value,'');assert.strictEqual(elements.routeView.hidden,false);
 assert.strictEqual(JSON.stringify(f),frozen);
}
assert.strictEqual(pairedRoutes,60);assert.strictEqual(pairedEntries,570);assert.strictEqual(pairedSelections,570);
location.hash='sucrose_metrology/CALIBRATE';assert(!window.ScienceGymExplorer.state.steps.some(s=>['UNDOCK','INVALIDATE_CALIBRATION'].includes(s.id)));
location.hash='sucrose_metrology/SESSION_TEARDOWN';assert(window.ScienceGymExplorer.state.steps.some(s=>s.id==='INVALIDATE_CALIBRATION'));
const pairedHistory=location.hash;location.hash='actuator_metrology/DIRECTION_HOLD';location.hash=pairedHistory;assert.strictEqual(window.ScienceGymExplorer.state.route,'SESSION_TEARDOWN');
location.hash='laser_control/QUALIFICATION_HOLD';assert(!window.ScienceGymExplorer.state.steps.some(s=>s.id==='REQUEST_LOCK'));
location.hash='chiral/R01';assert.strictEqual(elements.familyScope.textContent,'PAPER-LEVEL DESIGN');assert.strictEqual(elements.assetLinks.children.length,0);
console.log(`PASS: paired ${pairedRoutes} records / ${pairedEntries} display entries / ${pairedSelections} individual selections; explicit 29+3 scopes, default holds, separate teardown/recovery, source contracts, asset links and immutable navigation`);
// Woven whole-paper DESIGN: independent source classes, no scientific execution.
const woven=window.ScienceGymExplorer.data.woven,wovenBefore=JSON.stringify(woven);
const wovenNav=elements.families.children.find(e=>e.dataset.family==='woven');assert(wovenNav);wovenNav.onclick();
assert.strictEqual(window.ScienceGymExplorer.state.route,'QUALIFICATION_HOLD');
assert.strictEqual(elements.familyScope.textContent,'WHOLE-PAPER DESIGN');
assert.deepStrictEqual(Array.from(window.ScienceGymExplorer.state.steps,s=>s.id),['HOLD_QUALIFICATION']);
const wovenAssets=walk([elements.assetLinks]).filter(x=>x.tagName==='a');assert.strictEqual(wovenAssets.length,4);
for(const a of wovenAssets)assert(a.attrs.href.includes('/d62daed913e2ea04f0b7b0a0f20de9f6d42b7df6/assets/woven_scene_assets_v1/'));
let wovenEntries=0,wovenSelections=0;
for(const r of woven.routes){
 location.hash=['woven',r.id].join('/');const nodes=walk([elements.routeCanvas]);
 assert(!nodes.some(x=>x.className.split(' ').includes('connector')),r.id+' invented chronology');
 assert(!nodes.some(x=>x.textContent.includes('undefined')),r.id+' has undefined source data');
 const steps=[...window.ScienceGymExplorer.state.steps];
 if(r.source_file==='branches.json')assert.deepStrictEqual(Array.from(steps,s=>s.id),Array.from(woven.operations.filter(o=>o.detail.branch_ids.includes(r.id)),o=>o.id));
 for(const step of steps){
  location.hash=['woven',r.id,step.id,step.index].join('/');assert.strictEqual(window.ScienceGymExplorer.state.op,step.id);
  assert.strictEqual(window.ScienceGymExplorer.state.occurrence,step.index);
  const txt=walk([elements.inspector]).map(x=>x.textContent).join('\n');
  for(const value of [step.id,step.op.detail.precondition,step.op.detail.required_output,step.op.detail.failure,'No actions field supplied','No post-state field supplied'])assert(txt.includes(value),r.id+' missing '+value);
  wovenSelections++;
 }
 document.querySelectorAll('.operation').at(-1).onclick();document.querySelectorAll('.operation').at(-1).onclick();
 elements.operationSearch.oninput({target:{value:'hold'}});assert.strictEqual(document.querySelectorAll('.operation').length,steps.length);
 elements['tab-contract'].onclick();let txt=walk([elements.contractView]).map(x=>x.textContent).join('\n');
 for(const value of ['WHOLE-PAPER DESIGN, NOT REPRODUCTION','synthetic','source conflicts','TETRA_STRAND_COUNT','PLASMA_COATING_ORDER','PATTERN_PARAMETER_MAP','lineage','control packages','source access audit','agent visible','No silent correction','Prepared route earns no fabrication credit'])assert(txt.includes(value),value);
 elements['tab-dependencies'].onclick();txt=walk([elements.dependenciesView]).map(x=>x.textContent).join('\n');
 for(const value of ['preparation routes','lifecycle contract','transport routes','unspecified','external order card'])assert(txt.includes(value),value);
 wovenEntries+=steps.length;
}
assert.strictEqual(woven.routes.length,25);assert.strictEqual(wovenEntries,601);assert.strictEqual(wovenSelections,601);
location.hash='woven/PROGRAMMED_FAILURE_EXPERIMENT/REQUEST_SUPPORT_REMOVAL/0';assert.strictEqual(window.ScienceGymExplorer.state.op,'REQUEST_SUPPORT_REMOVAL');
const wovenHistory=location.hash;location.hash='woven/TETRAKAIDECAHEDRON_HOLD';assert(!window.ScienceGymExplorer.state.steps.some(s=>s.id==='REQUEST_TENSION'));
assert(elements.routeTitle.textContent.includes('SOURCE-CONFLICT HOLD'));location.hash=wovenHistory;assert.strictEqual(window.ScienceGymExplorer.state.op,'REQUEST_SUPPORT_REMOVAL');
location.hash='woven/LINEAR_HOMOGENIZATION';assert(elements.routeTitle.textContent.includes('NO SOLVER RUN'));assert(!window.ScienceGymExplorer.state.steps.some(s=>s.id==='REQUEST_TENSION'));
location.hash='woven/INVALID_ROUTE';assert.strictEqual(window.ScienceGymExplorer.state.route,'QUALIFICATION_HOLD');assert.strictEqual(elements.operationSearch.value,'');assert.strictEqual(elements.routeView.hidden,false);
location.hash='woven/QUALIFICATION_HOLD/REQUEST_TENSION/999';assert.strictEqual(window.ScienceGymExplorer.state.op,'HOLD_QUALIFICATION');
assert.strictEqual(JSON.stringify(woven),wovenBefore);
console.log(`PASS: woven 25 inspection records (24 scientific design routes + separate default hold), ${wovenEntries} entries / ${wovenSelections} individual selections; source conflicts, closed services, immutable navigation, 30+3 family scopes`);

// The two recent designs retain source memberships and immutable state under interruption.
let recentRecords=0,recentEntries=0,recentSelections=0;
for(const [key,expected] of Object.entries({lockable_origami:{records:34,branches:30},varactor:{records:29,branches:28}})){
 const f=window.ScienceGymExplorer.data[key],frozen=JSON.stringify(f);
 const nav=elements.families.children.find(e=>e.dataset.family===key);assert(nav);nav.onclick();
 assert.strictEqual(elements.familyScope.textContent,'WHOLE-PAPER DESIGN');
 assert.strictEqual(window.ScienceGymExplorer.state.route,'HOLD_QUALIFICATION');
 assert.deepStrictEqual(Array.from(window.ScienceGymExplorer.state.steps,s=>s.id),['HOLD_QUALIFICATION']);
 const links=walk([elements.assetLinks]).filter(e=>e.tagName==='a');assert.strictEqual(links.length,4);
 for(const a of links)assert(window.SCIENCEGYM_EMBEDDED_FILES?a.attrs.href==='blob:mock-test':a.attrs.href.startsWith('../../assets/'+key+'_scene_assets_v1/'));
 if(window.SCIENCEGYM_EMBEDDED_FILES){for(const item of [...Object.values(f.source_files),...f.asset_links])assert(window.SCIENCEGYM_EMBEDDED_FILES[item.url],item.url+' missing portable source bytes');}
 for(const r of f.routes){
  location.hash=key+'/'+r.id;const nodes=walk([elements.routeCanvas]);
  assert(!nodes.some(n=>n.className.split(' ').includes('connector')),key+'/'+r.id+' invented chronology');
  assert(!nodes.some(n=>n.textContent.includes('undefined')),key+'/'+r.id+' undefined contract');
  const steps=[...window.ScienceGymExplorer.state.steps];
  if(r.source_file==='branches.json')assert.deepStrictEqual(Array.from(steps,s=>s.id),Array.from(r.detail.operation_ids));
  for(const step of steps){
   location.hash=[key,r.id,step.id,step.index].join('/');
   assert.strictEqual(window.ScienceGymExplorer.state.op,step.id);assert.strictEqual(window.ScienceGymExplorer.state.occurrence,step.index);
   const txt=walk([elements.inspector]).map(n=>n.textContent).join('\n');
   for(const expected of [step.id,step.op.detail.action,step.op.detail.precondition,step.op.detail.required_output,step.op.detail.failure,step.op.detail.recovery,'Original authored symbolic task action','No post-state field supplied'])assert(txt.includes(expected),key+' missing '+expected);
   recentSelections++;
  }
  const last=document.querySelectorAll('.operation').at(-1);last.onclick();last.onclick();
  elements.operationSearch.oninput({target:{value:'safe'}});assert.strictEqual(document.querySelectorAll('.operation').length,steps.length);
  elements['tab-contract'].onclick();const txt=walk([elements.contractView]).map(n=>n.textContent).join('\n');
  for(const word of ['source conflicts','source access audit','unknowns','lineage','agent visible','Frozen local source files','remote publication is not asserted'])assert(txt.includes(word),key+' lost '+word);
  elements['tab-dependencies'].onclick();assert.strictEqual(elements.dependenciesView.hidden,false);
  location.hash=key+'/INVALID_ROUTE';assert.strictEqual(window.ScienceGymExplorer.state.route,'HOLD_QUALIFICATION');
  assert.strictEqual(elements.routeView.hidden,false);assert.strictEqual(elements.operationSearch.value,'');
  assert.deepStrictEqual(Array.from(window.ScienceGymExplorer.state.steps,s=>s.id),['HOLD_QUALIFICATION']);
  location.hash=[key,r.id,steps.at(-1).id,steps.at(-1).index].join('/');assert.strictEqual(window.ScienceGymExplorer.state.op,steps.at(-1).id);
  recentRecords++;recentEntries+=steps.length;
 }
 assert.strictEqual(f.routes.length,expected.records);assert.strictEqual(f.context.branches.branches.length,expected.branches);
 for(const suffix of ['NOT_A_COMMAND/-1','REQUEST_SAFE_OFF/999','HOLD_QUALIFICATION/NaN','%E0%A4%A']){
  location.hash=key+'/HOLD_QUALIFICATION/'+suffix;
  if(suffix!=='%E0%A4%A')assert.strictEqual(window.ScienceGymExplorer.state.op,'HOLD_QUALIFICATION');
 }
 assert.strictEqual(JSON.stringify(f),frozen);
}
assert.strictEqual(recentRecords,63);assert.strictEqual(recentSelections,recentEntries);
location.hash='lockable_origami/HOLD_GEOMETRY';assert.deepStrictEqual(Array.from(window.ScienceGymExplorer.state.steps,s=>s.id),['HOLD_GEOMETRY']);
location.hash='varactor/HOLD_QUALIFICATION';assert(!window.ScienceGymExplorer.state.steps.some(s=>s.id.startsWith('REQUEST_')));
console.log(`PASS: recent paper designs ${recentRecords} records / ${recentEntries} entries / ${recentSelections} individual selections; defaults, source/author separation, controls, local links, negative navigation and immutable state`);
// Wetting exact source contracts, metadata-only default and all authored operations.
{
 const f=window.ScienceGymExplorer.data.wetting;const frozen=JSON.stringify(f);
 assert.strictEqual(f.family_scope,'paper_level_design');assert.strictEqual(f.operations.length,74);assert.strictEqual(f.routes.length,17);
 assert.strictEqual(f.context.branches.branches.length,16);assert.strictEqual(f.default_route,'HOLD_QUALIFICATION');
 assert.strictEqual(f.context.source_access_audit.SOURCE_DATA.numeric_cells_read,false);
 let selections=0;
 for(const r of f.routes){
  location.hash='wetting/'+r.id;
  assert.strictEqual(elements.familyScope.textContent,'WHOLE-PAPER DESIGN');
  const nodes=walk([elements.routeCanvas]);assert(!nodes.some(n=>n.className.split(' ').includes('connector')));
  assert(!nodes.some(n=>n.textContent.includes('undefined')));
  const steps=[...window.ScienceGymExplorer.state.steps];
  if(r.source_file==='branches.json')assert.deepStrictEqual(Array.from(steps,s=>s.id),Array.from(r.detail.route_operation_ids));
  else {assert(r.metadata_only);assert.strictEqual(steps.length,0);assert.strictEqual(window.ScienceGymExplorer.state.op,null);}
  for(const step of steps){
   location.hash=['wetting',r.id,step.id,step.index].join('/');
   assert.strictEqual(window.ScienceGymExplorer.state.op,step.id);
   const txt=walk([elements.inspector]).map(n=>n.textContent).join('\n');
   for(const expected of [step.id,step.op.detail.description,step.op.detail.required_record_type,step.op.detail.failure_transition,'independently_authored_robot_task_design','No post-state field supplied'])assert(txt.includes(expected),'wetting missing '+expected);
   const button=document.querySelectorAll('.operation').at(-1);button.onclick();button.onclick();selections++;
  }
  elements.operationSearch.oninput({target:{value:'source'}});assert.strictEqual(document.querySelectorAll('.operation').length,steps.length);
  elements['tab-contract'].onclick();const txt=walk([elements.contractView]).map(n=>n.textContent).join('\n');
  for(const expected of ['source conflicts','source access audit','unknowns','controls and repeats','lineage','Frozen local source files','remote publication is not asserted'])assert(txt.includes(expected),'wetting lost '+expected);
  elements['tab-dependencies'].onclick();assert.strictEqual(elements.dependenciesView.hidden,false);
  location.hash='wetting/INVALID_ROUTE';assert.strictEqual(window.ScienceGymExplorer.state.route,'HOLD_QUALIFICATION');
  assert.strictEqual(window.ScienceGymExplorer.state.steps.length,0);assert.strictEqual(window.ScienceGymExplorer.state.op,null);assert.strictEqual(document.querySelectorAll('.operation').length,0);
 }
 assert.strictEqual(selections,74);
 for(const suffix of ['NOT_A_COMMAND/-1','R07_O01/999','HOLD_QUALIFICATION/NaN','%E0%A4%A']){
  location.hash='wetting/HOLD_QUALIFICATION/'+suffix;
  if(suffix!=='%E0%A4%A'){assert.strictEqual(window.ScienceGymExplorer.state.op,null);assert.strictEqual(window.ScienceGymExplorer.state.steps.length,0);}
  else assert(window.ScienceGymExplorer.data[window.ScienceGymExplorer.state.family]);
 }
 location.hash='wetting/R07/R07_O01/0';assert.strictEqual(window.ScienceGymExplorer.state.op,'R07_O01');
 location.hash='wetting/HOLD_QUALIFICATION';assert.strictEqual(window.ScienceGymExplorer.state.op,null);
 const links=walk([elements.assetLinks]).filter(e=>e.tagName==='a');assert.strictEqual(links.length,4);
 for(const a of links)assert(window.SCIENCEGYM_EMBEDDED_FILES?a.attrs.href==='blob:mock-test':a.attrs.href.startsWith('../../assets/wetting_scene_assets_v1/'));
 if(window.SCIENCEGYM_EMBEDDED_FILES){for(const item of [...Object.values(f.source_files),...f.asset_links])assert(window.SCIENCEGYM_EMBEDDED_FILES[item.url]);}
 assert.strictEqual(JSON.stringify(f),frozen);
 console.log('PASS: wetting 17 views / 16 design routes / 74 individual selections; metadata-only qualification hold, source/author separation, closed external preparation, exact contracts, negative navigation and immutable data');
}
