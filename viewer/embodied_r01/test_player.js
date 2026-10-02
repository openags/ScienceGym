'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
class Element{constructor(){this.children=[];this.attrs={};this.disabled=false;this.hidden=false;this.value='';this.textContent='';}replaceChildren(...xs){this.children=xs;}append(...xs){this.children.push(...xs);}setAttribute(k,v){this.attrs[k]=v;}}
function setup(frames){const elements=new Map(),timers=new Map();let id=0;const context={window:{EMBODIED_TASK:{title:'Unit-test fixture only',frames}},document:{getElementById:k=>{if(!elements.has(k))elements.set(k,new Element());return elements.get(k);},createElement:()=>new Element()},setInterval:fn=>{timers.set(++id,fn);return id;},clearInterval:i=>timers.delete(i),console};vm.createContext(context);vm.runInContext(fs.readFileSync(__dirname+'/player.js','utf8'),context);return {api:context.window.EmbodiedTaskPlayer,e:k=>elements.get(k),timers};}
const frames=Array.from({length:3},(_,i)=>({id:'TEST_'+i,title:'Synthetic UI fixture '+i,image:'not-loaded-in-mock-'+i+'.jpg',action:'Inspect fixture',station:'TEST',objects:['test object'],sample_state_before:'test before',sample_state_after:'test after',evidence:[],authored_notes:'Unit test only'}));
const {api,e,timers}=setup(frames);
assert.equal(api.index,0);assert.equal(e('steps').children.length,3);assert.equal(e('previous').disabled,true);assert.equal(e('next').disabled,false);
e('next').onclick();assert.equal(api.index,1);e('previous').onclick();assert.equal(api.index,0);
e('steps').onchange({target:{value:'2'}});assert.equal(api.index,2);assert.equal(e('next').disabled,true);
e('speed').value='1400';e('play').onclick();assert.equal(api.index,0);assert.equal(api.playing,true);assert.equal(timers.size,1);
[...timers.values()][0]();assert.equal(api.index,1);[...timers.values()][0]();assert.equal(api.index,2);assert.equal(api.playing,false);assert.equal(timers.size,0);
api.show(-8);assert.equal(api.index,0);api.show(100);assert.equal(api.index,2);api.show('malformed');assert.equal(api.index,0);
api.play();e('frame').onerror();assert.equal(api.playing,false);assert.equal(e('imageError').hidden,false);assert.equal(e('frame').hidden,true);e('frame').onload();assert.equal(e('frame').hidden,false);
e('seek').oninput({target:{value:'1'}});assert.equal(api.index,1);assert.equal(e('steps').value,1);
const empty=setup([]);assert.equal(empty.e('play').disabled,true);empty.api.play();assert.equal(empty.timers.size,0);
console.log('PASS: mocked-DOM controls, selection, range bounds, playback end, image failure and empty-state handling. No browser or robot execution tested.');
