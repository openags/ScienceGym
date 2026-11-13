const base='../../simulation/g1_cooling_demo/runs/laboratory_isolated_tool_01/';
const approachBase='../../simulation/g1_cooling_demo/runs/ftir_approach_11/';
Promise.all(['result.json','physical_slider_review.json','continuous_approach_review.json','slider_video.json'].map(async name=>{
 const response=await fetch(approachBase+name);if(!response.ok)throw Error('连续接近记录暂不可用：'+name);return response.json();
})).then(([run,physics,replay,video])=>{
 const complete=physics.passed&&replay.passed&&physics.trace_sha256===replay.trace_sha256&&video.trace_sha256===replay.trace_sha256;
 document.querySelector('#approach-status').textContent=complete?`${run.simulated_seconds.toFixed(1)} 秒连续运行，接近位移 ${replay.handoff_truth_review.executed_horizontal_displacement_m.toFixed(2)} 米，最终滑窗开口 ${(physics.final_slider_travel_m*1000).toFixed(2)} mm。独立物理检查与 ${replay.motor_outputs_compared.toLocaleString()} 次控制输出回放通过。`:'连续接近记录存在未通过项或轨迹不一致，请查看评估。';
 const names={continuous_station_handoff:'到达工位',seek_contact_endpoint:'接触滑窗',push_endpoint:'推窗结束',withdraw_endpoint:'撤手',slider_outcome_confirmed:'视觉确认'};
 for(const event of run.actor_last_output.events){if(!names[event.state])continue;const button=document.createElement('button');button.textContent=`${names[event.state]} ${event.time_s.toFixed(1)}s`;button.onclick=()=>{const video=document.querySelector('#approach');video.currentTime=event.time_s;video.play().catch(()=>{});};document.querySelector('#approach-chapters').append(button);}
 document.documentElement.dataset.approachReady=String(complete);
}).catch(error=>document.querySelector('#approach-status').textContent=error.message);
const main=document.querySelector('#episode'),depth=document.querySelector('#depth'),status=document.querySelector('#status');
for(const [id,file]of Object.entries({download:'episode.mp4',verdict:'transport_verification.json',geometry:'laboratory_verification.json',payload:'payload_containment_100hz.json',isolation:'isolation_verification.json',trace:'trace.npz'}))document.querySelector('#'+id).href=base+file;
const load=async name=>{const r=await fetch(base+name);if(!r.ok)throw Error('运行记录暂不可用：'+name);return r.json();};
Promise.all([load('result.json'),load('transport_verification.json'),load('laboratory_verification.json'),load('payload_containment_100hz.json'),load('isolation_verification.json')]).then(([run,verdict,geometry,payload,isolation])=>{
 const metrics=[`${run.simulated_seconds.toFixed(2)} 秒连续运行`,`抬升 ${(verdict.metrics.lift_m*100).toFixed(2)} cm`,`返回误差 ${(verdict.metrics.final_displacement_m*1000).toFixed(2)} mm`,`工具留存 ${payload.samples} 帧`];
 for(const text of metrics){const span=document.createElement('span');span.textContent=text;document.querySelector('#metrics').append(span);}
 status.textContent=verdict.passed&&geometry.passed&&payload.passed&&isolation.passed&&run.actor_access_isolated?'本次接触运行、场景对应、工具留存与控制器访问隔离检查通过。':'检查中发现未通过项，请查看独立评估记录。';
 const names={raise:'抬手',close:'接触抓取',lift:'抬起',transfer:'转移',release:'松开',retract:'收回双手',complete:'稳定保持'};
 for(const event of run.actor_last_output.policy_events){if(!names[event.state])continue;const button=document.createElement('button');button.textContent=`${event.phase===1?'返回 · ':''}${names[event.state]} ${event.time_s.toFixed(1)}s`;button.onclick=()=>{main.currentTime=event.time_s;main.play().catch(()=>{});};document.querySelector('#chapters').append(button);}
 document.documentElement.dataset.ready='true';
}).catch(error=>status.textContent=error.message);
async function seekable(video){const response=await fetch(video.getAttribute('src'));if(!response.ok)throw Error('录像暂不可用');const url=URL.createObjectURL(await response.blob()),t=video.currentTime,playing=!video.paused;await new Promise(resolve=>{video.addEventListener('loadedmetadata',resolve,{once:true});video.src=url;video.load();});video.currentTime=t;if(playing)await video.play();window.addEventListener('pagehide',()=>URL.revokeObjectURL(url),{once:true});}
Promise.all([seekable(main),seekable(depth),seekable(document.querySelector('#walking')),seekable(document.querySelector('#approach'))]).then(()=>document.documentElement.dataset.mediaReady='true').catch(error=>status.textContent=error.message);
function sync(){if(Number.isFinite(depth.duration)&&Math.abs(depth.currentTime-main.currentTime)>.16)depth.currentTime=Math.min(main.currentTime,depth.duration);}
main.addEventListener('timeupdate',sync);main.addEventListener('seeked',sync);main.addEventListener('play',()=>{sync();depth.play().catch(()=>{});});main.addEventListener('pause',()=>depth.pause());main.addEventListener('ratechange',()=>depth.playbackRate=main.playbackRate);
const walkingBase='../../simulation/g1_cooling_demo/runs/laboratory_walking_07/';
for(const [id,file]of Object.entries({download:'episode.mp4',verdict:'walking_verification.json',geometry:'laboratory_verification.json',isolation:'isolation_verification.json',trace:'trace.npz'}))document.querySelector('#walking-'+id).href=walkingBase+file;
Promise.all(['result.json','walking_verification.json','laboratory_verification.json','isolation_verification.json'].map(async name=>{const response=await fetch(walkingBase+name);if(!response.ok)throw Error('行走记录暂不可用');return response.json();})).then(([run,verdict,geometry,isolation])=>{
 const forward=verdict.checks.find(c=>c.name==='forward_motion_exceeds_one_metre').forward_m;
 document.querySelector('#walking-status').textContent=verdict.passed&&geometry.passed&&isolation.passed?`${run.simulated_seconds.toFixed(0)} 秒连续运行，前进 ${forward.toFixed(2)} 米；${run.parking_time_s.toFixed(2)} 秒切换站立控制。行走、接触和独立重放检查通过。`:'行走检查存在未通过项，请查看记录。';
 document.documentElement.dataset.walkingReady='true';
}).catch(error=>document.querySelector('#walking-status').textContent=error.message);
