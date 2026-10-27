import * as THREE from 'three';

const matrix = rows => new THREE.Matrix4().fromArray(rows.flat()).transpose();
const clamp = THREE.MathUtils.clamp, smooth = u => u*u*(3-2*u);
const matrixRows = value => {
  const a=value.clone().transpose().toArray();
  return Array.from({length:4},(_,i)=>a.slice(i*4,i*4+4));
};

function interpolate(segment,elapsed) {
  const rows=segment.rows;
  let lo=0,hi=rows.length-1;
  while(hi-lo>1){const mid=(lo+hi)>>1;if(rows[mid].time_s<=elapsed)lo=mid;else hi=mid;}
  const a=rows[lo],b=rows[hi];
  let u=a===b?0:clamp((elapsed-a.time_s)/(b.time_s-a.time_s),0,1);
  if(segment.interpolation==='smooth')u=smooth(u);
  const q=Object.fromEntries(Object.keys(a.q).map(n=>[n,THREE.MathUtils.lerp(a.q[n],b.q[n],u)]));
  const ra=matrix(a.root),rb=matrix(b.root);
  const p=new THREE.Vector3().setFromMatrixPosition(ra).lerp(new THREE.Vector3().setFromMatrixPosition(rb),u);
  const rotation=new THREE.Quaternion().setFromRotationMatrix(ra).slerp(new THREE.Quaternion().setFromRotationMatrix(rb),u);
  const root=new THREE.Matrix4().compose(p,rotation,new THREE.Vector3(1,1,1));
  return {q,root:matrixRows(root),closure:THREE.MathUtils.lerp(a.closure||0,b.closure||0,u),
    button_travel_m:THREE.MathUtils.lerp(a.button_travel_m||0,b.button_travel_m||0,u)};
}

export async function installMeasurementEpisode(ctx,sourceActions) {
  const episode=await ctx.read('viewer/cooling_concept_v2/single_measurement_episode.json');
  if(!episode.continuous_at_segment_boundaries)throw Error('Measurement episode has discontinuous boundaries');
  if(episode.cover_hand_correction)sourceActions.setCoverHandCorrection(episode.cover_hand_correction);
  const descriptor=episode.deformable_tool,tool=ctx.groups.get(descriptor.id);
  if(descriptor.model!=='symmetric_fixed_heel_cantilever_v1')throw Error('Unknown tool deformation');
  const source=ctx.manifest.assets.find(a=>a.id===descriptor.id),meshes=[];
  tool.traverse(node=>{
    if(!node.isMesh)return;
    node.geometry=node.geometry.clone();
    meshes.push({node,rest:node.geometry.attributes.position.array.slice(),
      sign:node.name.startsWith('ptfe_spring_arm_')?Number(node.name.split('_').at(-1)):0});
  });
  if(meshes.filter(m=>m.sign).length!==2)throw Error('Expected both source tweezer arms');
  let lastClosure;
  function deform(closure){
    if(!(closure>=0&&closure<=1))throw Error('Invalid tweezer closure');
    if(closure===lastClosure)return;
    for(const {node,rest,sign} of meshes){
      const a=node.geometry.attributes.position;
      for(let i=0;i<rest.length;i+=3){
        const distance=1-clamp(rest[i]/descriptor.length_m,0,1);
        a.array[i+1]=rest[i+1]-sign*descriptor.tip_deflection_m*closure*distance*distance*(3-distance)/2;
      }
      a.needsUpdate=true;node.geometry.computeVertexNormals();node.geometry.computeBoundingSphere();node.geometry.computeBoundingBox();
    }
    lastClosure=closure;
  }
  ctx.reset();
  const deformationSamples=[0,Math.max(...episode.segments.flatMap(s=>(s.rows||[]).map(r=>r.closure||0))),1].map(closure=>{
    deform(closure);
    return {closure,parts:meshes.map(({node})=>({name:node.name,node_matrix:node.matrix.toArray(),
      vertices:Array.from(node.geometry.attributes.position.array),indices:node.geometry.index?
        Array.from(node.geometry.index.array):Array.from({length:node.geometry.attributes.position.count},(_,i)=>i)}))};
  });
  const deformableGeometry=[{...descriptor,source:source.geometry,source_sha256:source.geometry_sha256,samples:deformationSamples}];
  const palmToTool=matrix(episode.tool_T_palm).invert(),toolToHolder=matrix(episode.holder_T_tool).invert();
  const apply=(group,pose)=>pose.decompose(group.position,group.quaternion,group.scale);
  const pikeWorld=new THREE.Matrix4().makeTranslation(...ctx.manifest.assets.find(a=>a.id==='pike').position_m);
  const referenceParts=ctx.nodeRest.filter(n=>n.asset==='pike'&&['gold_reference_holder','gold_reference_shoulder','diffuse_gold_reference_face'].includes(n.node.name));
  const keys=new Map(ctx.nodeRest.filter(n=>n.asset==='nicolet'&&/^scan_key_[0-3]$/.test(n.node.name)).map(n=>[n.node.name,n]));
  if(keys.size!==4)throw Error('Acquisition buttons must retain separate source nodes');
  const interfaces=await ctx.read('assets/nicolet_6700_v1/interfaces.json');
  const buttonAxes=new Map(interfaces.interfaces.filter(i=>i.kind==='push_button').map(i=>[i.id,new THREE.Vector3(...i.axis)]));
  const phases=episode.segments.map(s=>({id:s.id,start:s.start,end:s.end,duration:s.duration_s,
    action:s.source_action||s.id,kind:s.kind||'work',refs:s.source_operation_refs||[]}));
  function poseAt(time){
    const t=clamp(time,0,episode.duration_s);
    let index=episode.segments.findIndex(s=>t<s.end);if(index<0)index=episode.segments.length-1;
    const segment=episode.segments[index],elapsed=clamp(t-segment.start,0,segment.duration_s);
    const state=segment.source_action?sourceActions.sample(segment.source_action,
      elapsed*segment.source_duration_s/segment.duration_s):interpolate(segment,elapsed);
    const root=matrix(state.root),r=ctx.pose(state.q,state.root);r.p=phases[index];
    const closure=state.closure||0;
    const toolPose=segment.tool_held?root.clone().multiply(ctx.handIK.forward(state.q).world.get('right_palm_force_sensor')).multiply(palmToTool):matrix(episode.tool_rest);
    apply(tool,toolPose);deform(closure);apply(ctx.groups.get('tray_white'),matrix(episode.tray_matrix));
    for(const kind of ['white','black']){
      const pose=segment.held_specimen===kind?toolPose.clone().multiply(toolToHolder):matrix(segment.stored_specimens[kind]);
      apply(ctx.groups.get('optical_witness_'+kind),pose);
    }
    const reference=state.reference_delta||segment.reference_delta;
    const local=pikeWorld.clone().invert().multiply(matrix(reference)).multiply(pikeWorld);
    for(const part of referenceParts)apply(part.node,local.clone().multiply(part.rest));
    const cover=state.cover_angle_rad??segment.cover_angle_rad;
    ctx.applyState('nicolet_cover',cover/(-Math.PI/2));
    for(const key of keys.values())apply(key.node,key.rest);
    if(segment.button){
      const key=keys.get('scan_key_'+segment.button.split('_').at(-1));
      key.node.position.addScaledVector(buttonAxes.get(segment.button),state.button_travel_m||0);
    }
    ctx.scene.updateMatrixWorld(true);
    return {t,r,segment,state,reference,cover,closure};
  }
  const clean=new URLSearchParams(location.search).has('clean');
  let now=0,playing=false,previousClock=performance.now();
  function renderAt(time){
    const frame=poseAt(time);now=frame.t;
    const {segment,r}=frame;
    if(segment.button){
      const target=new THREE.Vector3(9.45,8.45,1.09);
      ctx.camera.position.copy(target).add(new THREE.Vector3(.48,-.65,.48));ctx.camera.lookAt(target);
    }else{
      const moving=segment.kind==='move';
      ctx.camera.position.copy(r.position).add(new THREE.Vector3(moving?1.3:1.1,moving?-2.1:-1.6,moving?2.25:1.95));
      ctx.camera.position.x=clamp(ctx.camera.position.x,.5,11.5);
      ctx.camera.lookAt(r.position.clone().add(new THREE.Vector3(.04,.27,.85)));
    }
    ctx.localKey.position.copy(r.position).add(new THREE.Vector3(1,-.2,2.4));
    ctx.localKey.target.position.copy(r.position).add(new THREE.Vector3(0,.3,1));
    ctx.renderer.render(ctx.scene,ctx.camera);
    if(ctx.renderer.getContext().isContextLost())throw Error('Measurement renderer lost its WebGL context');
    if(!clean){
      document.getElementById('title').textContent=segment.title||'跨工位红外测量';
      document.getElementById('detail').textContent=segment.id;
      document.getElementById('seek').value=now;
    }
    window.currentFrame={time_s:now,stage:segment.id,robot_position:r.position.toArray(),robot_yaw:r.yaw};
  }
  window.auditFrame=time=>{
    const frame=poseAt(time);
    return {...ctx.snapshot(frame.t,frame.r),deformable_states:{[descriptor.id]:frame.closure},
      optical_state:{tool_held:frame.segment.tool_held,held_specimen:frame.segment.held_specimen,stored_specimens:frame.segment.stored_specimens},
      measurement_state:{cover_angle_rad:frame.cover,reference_delta:frame.reference,
        button:frame.segment.button||null,button_travel_m:frame.state.button_travel_m||0,
        source_action:frame.segment.source_action||null,source_action_elapsed_s:frame.segment.source_action?
          (frame.t-frame.segment.start)*frame.segment.source_duration_s/frame.segment.duration_s:null,
        acquisition:frame.segment.acquisition||null}};
  };
  window.renderAt=renderAt;
  window.concept={manifest:ctx.manifest,sourceHashes:ctx.sourceHashes,extraGeometry:ctx.extraGeometry,deformableGeometry,
    measurementEpisode:{scope:episode.scope,status:episode.status,initial_conditions:episode.initial_conditions},
    duration:episode.duration_s,phases,criticalTimes:episode.segments.flatMap(s=>[
      s.start,s.end,...(s.critical_local_times_s||[]).map(t=>s.start+t)]),assetCount:ctx.groups.size,robotCount:1,renderAt,
    rendererInfo:()=>ctx.renderer.info.render,
    frameJpeg:t=>{renderAt(t);return ctx.renderer.domElement.toDataURL('image/jpeg',.92).split(',')[1];}};
  const seek=document.getElementById('seek'),play=document.getElementById('play');seek.max=episode.duration_s;
  play.onclick=()=>{playing=!playing;previousClock=performance.now();play.textContent=playing?'暂停':'播放';};
  seek.oninput=e=>{playing=false;play.textContent='播放';renderAt(Number(e.target.value));};
  document.querySelector('a[download]').hidden=true;
  const steps=document.querySelector('a[href="workflow.json"]');steps.href='single_measurement_episode.json';steps.textContent='完整测量步骤';
  function tick(clock){if(playing){renderAt(now+(clock-previousClock)/1000);if(now>=episode.duration_s){playing=false;play.textContent='播放';}}
    previousClock=clock;requestAnimationFrame(tick);}
  renderAt(0);requestAnimationFrame(tick);
}
