/* Unit smoke tests against a minimal mocked DOM. Not browser/visual QA. */
'use strict';const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');const ROOT=path.resolve(__dirname,'..');
class El{constructor(tag){this.tagName=tag;this.attrs={};this.children=[];this.style={setProperty(){}};this.dataset={};this.hidden=false;this.value='';this.className='';this.classList={toggle:(name,on)=>{let s=new Set(this.className.split(' ').filter(Boolean));on?s.add(name):s.delete(name);this.className=[...s].join(' ');}};}setAttribute(k,v){this.attrs[k]=String(v);if(k.startsWith('data-'))this.dataset[k.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=String(v);if(k==='value')this.value=v;}append(...x){this.children.push(...x);}replaceChildren(...x){this.children=x;}set textContent(v){this.text=String(v);this.children=[];}get textContent(){return this.text||'';}}
const ids=[...fs.readFileSync(path.join(ROOT,'index.html'),'utf8').matchAll(/\bid="([^"]+)"/g)].map(x=>x[1]);const elements=Object.fromEntries(ids.map(id=>[id,new El('div')]));['route','dependencies','contract'].forEach(tab=>{elements['tab-'+tab].setAttribute('role','tab');elements['tab-'+tab].setAttribute('data-tab',tab);});
const walk=(roots)=>roots.flatMap(n=>n instanceof El?[n,...walk(n.children)]:[]);const document={documentElement:new El('html'),getElementById:id=>elements[id],createElement:tag=>new El(tag),createTextNode:t=>String(t),querySelectorAll:selector=>{const all=walk(Object.values(elements));if(selector==='nav button')return elements.families.children;if(selector==='[role=tab]')return all.filter(x=>x.attrs.role==='tab');if(selector==='.operation')return all.filter(x=>x.className.split(' ').includes('operation'));throw Error('Unimplemented selector '+selector);}};
const data={};for(const key of ['chiral','microscopy','fibre','thermoelectric','dispim','acoustic','perovskite','prismatic','emvp'])data[key]=JSON.parse(fs.readFileSync(path.join(ROOT,'data',key+'.json'),'utf8'));
let hash='',onHash;const location={get hash(){return hash;},set hash(value){hash=value.startsWith('#')?value:'#'+value;if(onHash)onHash();}};const window={SCIENCEGYM_DATA:data,addEventListener:(n,fn)=>{if(n==='hashchange')onHash=fn;}};const context={window,document,location,console,Blob:class{constructor(parts,options){this.parts=parts;this.options=options;}},URL:{createObjectURL:()=> 'blob:mock-test',revokeObjectURL:()=>{}}};vm.createContext(context);if(process.argv[2]){const standalone=fs.readFileSync(process.argv[2],'utf8');for(const match of standalone.matchAll(/<script>([\s\S]*?)<\/script>/g))vm.runInContext(match[1],context);}else{vm.runInContext(fs.readFileSync(path.join(ROOT,'app.js'),'utf8'),context);}let routeCount=0,occurrenceCount=0;
for(const [key,f]of Object.entries(window.ScienceGymExplorer.data)){for(const r of f.routes){location.hash=[key,r.id,'',0].join('/');const state=window.ScienceGymExplorer.state;assert.strictEqual(state.family,key);assert.strictEqual(state.route,r.id);assert(state.steps.length>0);assert.strictEqual(document.querySelectorAll('.operation').length,state.steps.length);assert.strictEqual(document.querySelectorAll('.operation').filter(x=>x.attrs['aria-pressed']==='true').length,1);const last=state.steps[state.steps.length-1];location.hash=[key,r.id,last.id,last.index].join('/');assert.strictEqual(state.op,last.id);assert.strictEqual(state.occurrence,last.index);routeCount++;occurrenceCount+=state.steps.length;}}
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
location.hash='bad-family/bad-route';assert.strictEqual(window.ScienceGymExplorer.state.family,'chiral');location.hash='#%invalid';assert.strictEqual(window.ScienceGymExplorer.state.family,'chiral');
console.log(`PASS: mocked-DOM rendering of ${routeCount} routes / ${occurrenceCount} displayed operation occurrences; selection, repeated IDs, search, tabs and malformed-hash fallback`);
