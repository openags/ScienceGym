// Retiming preserves the existing contact/object choreography while allowing
// free-arm paths to take the time their source joint limits require.
const clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
const smooth=v=>{v=clamp(v,0,1);return v*v*(3-2*v)};

export function retimeWork(paths,id,originalDuration,action){
  if(action==='pick'){
    const route=paths[id];
    if(!route)return {duration:originalDuration,originalDuration,planningPending:true};
    return {duration:originalDuration-2+route.duration_s,originalDuration,
      motionTiming:{kind:'pick',entry:route.duration_s}};
  }
  if(action==='place'){
    const route=paths[id];
    if(!route)return {duration:originalDuration,originalDuration,planningPending:true};
    return {duration:originalDuration-2+route.duration_s,originalDuration,
      motionTiming:{kind:'place',exit:route.duration_s}};
  }
  if(action.startsWith('lid_')||action.startsWith('cover_')){
    const entry=paths[id+'_entry'],exit=paths[id+'_exit'];
    if(!entry||!exit)return {duration:originalDuration,originalDuration,planningPending:true};
    return {duration:originalDuration-4+entry.duration_s+exit.duration_s,originalDuration,
      motionTiming:{kind:'lid',entry:entry.duration_s,exit:exit.duration_s}};
  }
  return {duration:originalDuration,originalDuration};
}

export function actionElapsed(phase,time){
  const e=clamp(time-phase.start,0,phase.duration),m=phase.motionTiming;
  if(!m)return e;
  if(m.kind==='pick')return e<m.entry?2*e/m.entry:e-m.entry+2;
  if(m.kind==='place'){
    if(e<6.8)return e;
    return e<6.8+m.exit?6.8+2*(e-6.8)/m.exit:e-m.exit+2;
  }
  if(e<m.entry)return 2*e/m.entry;
  if(e<m.entry+8.8)return 2+e-m.entry;
  if(e<m.entry+8.8+m.exit)return 10.8+2*(e-m.entry-8.8)/m.exit;
  return 12.8+e-m.entry-8.8-m.exit;
}

export function freeArmPath(paths,phase,time){
  const m=phase.motionTiming,e=time-phase.start;
  if(!m)return null;
  if(m.kind==='pick')return e<m.entry?{route:paths[phase.id],time:e}:null;
  if(m.kind==='place')return e>=6.8?{route:paths[phase.id],time:m.exit-(e-6.8)}:null;
  if(e<m.entry)return {route:paths[phase.id+'_entry'],time:e};
  if(e>=m.entry+8.8)return {route:paths[phase.id+'_exit'],time:m.exit-(e-m.entry-8.8)};
  return null;
}

export function samplePath(route,time){
  const t=clamp(time,0,route.duration_s),q={...route.base_q};
  let i=1;while(i<route.knot_times_s.length-1&&t>route.knot_times_s[i])i++;
  const amount=smooth((t-route.knot_times_s[i-1])/(route.knot_times_s[i]-route.knot_times_s[i-1]));
  route.joints.forEach((name,k)=>{
    const value=route.knots[i-1][k]+amount*(route.knots[i][k]-route.knots[i-1][k]);
    const aliases=route.generalized_finger_joint[name];
    if(aliases)aliases.forEach(n=>{q[n]=value});else q[name]=value;
  });
  return q;
}
