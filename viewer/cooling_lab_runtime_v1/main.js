const base='../../simulation/g1_cooling_demo/runs/laboratory_tool_transport_01/';
const main=document.querySelector('#episode'),depth=document.querySelector('#depth'),status=document.querySelector('#status');
for(const [id,file]of Object.entries({download:'episode.mp4',verdict:'transport_verification.json',geometry:'laboratory_verification.json',payload:'payload_containment_100hz.json',trace:'trace.npz'}))document.querySelector('#'+id).href=base+file;
const load=async name=>{const r=await fetch(base+name);if(!r.ok)throw Error('运行记录暂不可用：'+name);return r.json();};
Promise.all([load('result.json'),load('transport_verification.json'),load('laboratory_verification.json'),load('payload_containment_100hz.json')]).then(([run,verdict,geometry,payload])=>{
 const metrics=[`${run.simulated_seconds.toFixed(2)} 秒连续运行`,`抬升 ${(verdict.metrics.lift_m*100).toFixed(2)} cm`,`返回误差 ${(verdict.metrics.final_displacement_m*1000).toFixed(2)} mm`,`工具留存 ${payload.samples} 帧`];
 for(const text of metrics){const span=document.createElement('span');span.textContent=text;document.querySelector('#metrics').append(span);}
 status.textContent=verdict.passed&&geometry.passed&&payload.passed?'本次接触运行、场景对应与工具留存检查通过。':'检查中发现未通过项，请查看独立评估记录。';
 const names={raise:'抬手',close:'接触抓取',lift:'抬起',transfer:'转移',release:'松开',retract:'收回双手',complete:'稳定保持'};
 for(const event of run.actor_last_output.policy_events){if(!names[event.state])continue;const button=document.createElement('button');button.textContent=`${event.phase===1?'返回 · ':''}${names[event.state]} ${event.time_s.toFixed(1)}s`;button.onclick=()=>{main.currentTime=event.time_s;main.play().catch(()=>{});};document.querySelector('#chapters').append(button);}
 document.documentElement.dataset.ready='true';
}).catch(error=>status.textContent=error.message);
async function seekable(video){const response=await fetch(video.getAttribute('src'));if(!response.ok)throw Error('录像暂不可用');const url=URL.createObjectURL(await response.blob()),t=video.currentTime,playing=!video.paused;await new Promise(resolve=>{video.addEventListener('loadedmetadata',resolve,{once:true});video.src=url;video.load();});video.currentTime=t;if(playing)await video.play();window.addEventListener('pagehide',()=>URL.revokeObjectURL(url),{once:true});}
Promise.all([seekable(main),seekable(depth)]).then(()=>document.documentElement.dataset.mediaReady='true').catch(error=>status.textContent=error.message);
function sync(){if(Number.isFinite(depth.duration)&&Math.abs(depth.currentTime-main.currentTime)>.16)depth.currentTime=Math.min(main.currentTime,depth.duration);}
main.addEventListener('timeupdate',sync);main.addEventListener('seeked',sync);main.addEventListener('play',()=>{sync();depth.play().catch(()=>{});});main.addEventListener('pause',()=>depth.pause());main.addEventListener('ratechange',()=>depth.playbackRate=main.playbackRate);
