import * as THREE from 'three';
const M=a=>new THREE.Matrix4().fromArray(a.flat()).transpose();
const clamp=THREE.MathUtils.clamp,smooth=u=>u*u*(3-2*u);
function interpolateMatrix(a,b,u){
 const pa=new THREE.Vector3(),pb=new THREE.Vector3(),qa=new THREE.Quaternion(),qb=new THREE.Quaternion(),scale=new THREE.Vector3();
 M(a).decompose(pa,qa,scale);M(b).decompose(pb,qb,scale);
 return new THREE.Matrix4().compose(pa.lerp(pb,u),qa.slerp(qb,u),new THREE.Vector3(1,1,1));
}
export function referenceAt(data,time,ik){
 time=clamp(time,0,data.duration_s);
 const segment=data.segments.find(s=>time<s.end)||data.segments.at(-1),elapsed=clamp(time-segment.start,0,segment.duration_s),rows=segment.rows;
 let i=1;while(i<rows.length-1&&elapsed>rows[i].time_s)i++;
 const a=rows[i-1],b=rows[i],linear=clamp((elapsed-a.time_s)/(b.time_s-a.time_s),0,1),u=segment.interpolation==='linear'?linear:smooth(linear);
 const q=Object.fromEntries(Object.keys(a.q).map(n=>[n,THREE.MathUtils.lerp(a.q[n],b.q[n],u)]));
 const root=interpolateMatrix(a.root,b.root,u),position=new THREE.Vector3().setFromMatrixPosition(root),yaw=Math.atan2(root.elements[1],root.elements[0]);
 let reference,handTarget=null;
 if(segment.mode==='held_fk'){
  reference=root.clone().multiply(ik.forward(q).world.get('left_palm_force_sensor')).multiply(M(data.reference_in_palm));
  const correction=interpolateMatrix(...segment.endpoint_reference_corrections,smooth(elapsed/segment.duration_s));reference.premultiply(correction);
 }else{
  const offset=a.reference_offset.map((v,k)=>THREE.MathUtils.lerp(v,b.reference_offset[k],u));
  reference=new THREE.Matrix4().makeTranslation(...data.reference_port_m.map((v,k)=>v+offset[k]));
 }
 if(a.hand_target&&b.hand_target)handTarget=interpolateMatrix(a.hand_target,b.hand_target,u);
 return {q,root,position,yaw,reference,handTarget,closed:THREE.MathUtils.lerp(a.closed,b.closed,u),stage:segment.id,mode:segment.mode};
}
