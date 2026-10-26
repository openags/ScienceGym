const base='../../simulation/g1_cooling_demo/runs/delivery/';
const video=document.querySelector('#video');
const phases=[[0,'站立与定位'],[2,'抬手'],[6,'接近'],[10,'下探'],[14,'夹持'],[18,'抬升'],[22,'移动'],[26,'放回'],[30,'释放'],[33,'收手']];
for(const [t,label] of phases){const b=document.createElement('button');b.textContent=`${t}s ${label}`;b.onclick=()=>{video.currentTime=t;video.play().catch(()=>{});};document.querySelector('#steps').append(b);}
let plot;
const depthVideo=document.querySelector('#depth');
// A local static server may not implement HTTP byte ranges. A complete Blob
// gives the browser a seekable recording on that server as well.
Promise.all([[video,'episode.mp4'],[depthVideo,'head_depth.mp4']].map(async([el,name])=>{
  const response=await fetch(base+name);if(!response.ok)throw Error(name+' unavailable');
  const url=URL.createObjectURL(await response.blob());
  await new Promise((resolve,reject)=>{el.addEventListener('loadedmetadata',resolve,{once:true});el.addEventListener('error',reject,{once:true});el.src=url;el.load();});
  window.addEventListener('pagehide',()=>URL.revokeObjectURL(url),{once:true});
})).then(()=>document.documentElement.dataset.mediaReady='true').catch(()=>{document.querySelector('#error').textContent='视频加载失败，请使用下载视频链接。';});
video.addEventListener('play',()=>{depthVideo.currentTime=video.currentTime;depthVideo.play().catch(()=>{});});
video.addEventListener('pause',()=>depthVideo.pause());
video.addEventListener('ratechange',()=>{depthVideo.playbackRate=video.playbackRate;});
video.addEventListener('seeked',()=>{depthVideo.currentTime=Math.min(video.currentTime,37.9);});
function draw(){if(!plot)return;const c=document.querySelector('#plot'),ctx=c.getContext('2d'),w=c.width,h=c.height,left=45,bottom=h-30,top=16,max=Math.max(12,...plot.tray_height_cm,...plot.tray_y_cm),duration=plot.time.at(-1);ctx.clearRect(0,0,w,h);ctx.font='15px system-ui';ctx.lineWidth=1;for(const v of [0,7,Math.ceil(max)]){const y=bottom-v/max*(bottom-top);ctx.strokeStyle=v===7?'#657986':'#2c414d';ctx.setLineDash(v===7?[5,5]:[]);ctx.beginPath();ctx.moveTo(left,y);ctx.lineTo(w-15,y);ctx.stroke();ctx.fillStyle='#9eb3bd';ctx.fillText(v+' cm',0,y+5);}ctx.setLineDash([]);for(const [key,color] of [['tray_height_cm','#83dfce'],['tray_y_cm','#d8b8f8']]){ctx.strokeStyle=color;ctx.lineWidth=3;ctx.beginPath();plot.time.forEach((t,i)=>{const x=left+t/duration*(w-left-15),y=bottom-plot[key][i]/max*(bottom-top);i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();}ctx.fillStyle='#9eb3bd';for(const t of [0,10,20,30,38])ctx.fillText(t+'s',left+t/duration*(w-left-15)-10,h-5);const x=left+video.currentTime/duration*(w-left-15);ctx.strokeStyle='#fff';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(x,top);ctx.lineTo(x,bottom);ctx.stroke();}
video.addEventListener('timeupdate',()=>{let index=phases.findLastIndex(([t])=>video.currentTime>=t);document.querySelectorAll('#steps button').forEach((b,i)=>b.classList.toggle('active',i===index));draw();});
Promise.all(['verification.json','plot.json'].map(p=>fetch(base+p).then(r=>{if(!r.ok)throw Error(`${p}: HTTP ${r.status}`);return r.json();}))).then(([v,p])=>{document.querySelector('#duration').textContent=v.metrics.duration_s.toFixed(1);document.querySelector('#lift').textContent=(v.metrics.lift_m*100).toFixed(1);document.querySelector('#transfer').textContent=(v.metrics.transfer_m*100).toFixed(1);const status=document.querySelector('#episode-status');status.textContent=v.passed?'单段检查通过':'部分检查未通过';status.classList.toggle('good',v.passed);for(const x of v.checks){const el=document.createElement('div');el.className='check';el.textContent=x.name;const badge=document.createElement('i');badge.textContent=x.passed?'通过':'未通过';badge.style.color=x.passed?'#83dfce':'#f0ca90';el.append(badge);document.querySelector('#checks').append(el);}plot=p;draw();document.documentElement.dataset.ready='true';}).catch(e=>{document.querySelector('#error').textContent='验证记录尚未就绪：'+e.message;});
