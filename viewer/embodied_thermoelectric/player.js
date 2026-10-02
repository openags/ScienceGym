'use strict';
(()=>{
const data=window.EMBODIED_TASK||{},frames=data.frames||[],$=id=>document.getElementById(id);let index=0,timer=null;
const asText=v=>typeof v==='string'?v:JSON.stringify(v,null,2);
function fill(id,value){const target=$(id);target.replaceChildren();if(value==null){target.textContent='Not specified';return;}const entries=Array.isArray(value)?value:[value];for(const item of entries){const p=document.createElement('p');p.textContent=asText(item);target.append(p);}}
function stop(){if(timer!==null)clearInterval(timer);timer=null;$('play').textContent='Play';$('play').setAttribute('aria-pressed','false');}
function show(n){if(!frames.length)return;n=Number(n);if(!Number.isFinite(n))n=0;index=Math.max(0,Math.min(frames.length-1,Math.trunc(n)));const f=frames[index];$('frame').alt=f.alt||f.title||f.id||'Illustrated laboratory task state';$('frame').src=f.image;$('stepCount').textContent=`STEP ${index+1} / ${frames.length} · ${f.id||''}`;$('stepTitle').textContent=f.title||f.id||'Reference step';$('action').textContent=asText(f.action||f.actions||'No action description supplied');$('station').textContent=asText(f.station||'Not specified');fill('objects',f.objects);fill('before',f.sample_state_before);fill('after',f.sample_state_after);fill('evidence',f.evidence);fill('authored',f.authored_notes);$('seek').value=index;$('steps').value=index;$('previous').disabled=index===0;$('next').disabled=index===frames.length-1;if(index===frames.length-1)stop();}
function play(){if(!frames.length)return;if(timer!==null){stop();return;}if(index===frames.length-1)show(0);$('play').textContent='Pause';$('play').setAttribute('aria-pressed','true');timer=setInterval(()=>show(index+1),Number($('speed').value));}
$('title').textContent=data.title||'Embodied laboratory task';fill('limits',[...(data.limitations||['No physical simulation or robot execution is claimed']),data.attribution||'',data.model_license||''].filter(Boolean));$('seek').max=Math.max(0,frames.length-1);
frames.forEach((f,i)=>{const o=document.createElement('option');o.value=i;o.textContent=`${String(i+1).padStart(2,'0')} · ${f.id||''} · ${f.title||''}`;$('steps').append(o);});
$('previous').onclick=()=>{stop();show(index-1);};$('next').onclick=()=>{stop();show(index+1);};$('play').onclick=play;$('seek').oninput=e=>{stop();show(Number(e.target.value));};$('steps').onchange=e=>{stop();show(Number(e.target.value));};$('speed').onchange=()=>{if(timer!==null){stop();play();}};
$('frame').onerror=()=>{stop();$('imageError').hidden=false;$('frame').hidden=true;};$('frame').onload=()=>{$('imageError').hidden=true;$('frame').hidden=false;};
if(frames.length)show(0);else{$('action').textContent='No verified frames have been supplied.';['previous','next','play','seek','steps'].forEach(id=>$(id).disabled=true);}
window.EmbodiedTaskPlayer={show,stop,play,data,get index(){return index;},get playing(){return timer!==null;}};
})();
