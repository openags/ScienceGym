import * as THREE from 'three';

const vec=a=>new THREE.Vector3(...a);
const mat=a=>new THREE.Matrix4().fromArray(a.flat()).transpose();

function solveLinear(a,b){
  a=a.map((row,i)=>[...row,b[i]]);
  for(let k=0;k<b.length;k++){
    let best=k;for(let i=k+1;i<b.length;i++)if(Math.abs(a[i][k])>Math.abs(a[best][k]))best=i;
    [a[k],a[best]]=[a[best],a[k]];const scale=a[k][k];
    if(Math.abs(scale)<1e-12)return b.map(()=>0);
    for(let j=k;j<=b.length;j++)a[k][j]/=scale;
    for(let i=0;i<b.length;i++)if(i!==k){const factor=a[i][k];for(let j=k;j<=b.length;j++)a[i][j]-=factor*a[k][j];}
  }
  return a.map(row=>row[b.length]);
}

export class HandIK{
  constructor(kin){
    this.kin=kin;this.origins=new Map(kin.joints.map(j=>[j.name,mat(j.origin_matrix)]));
    this.axes=new Map(kin.joints.map(j=>[j.name,vec(j.axis)]));
    this.arm={};this.localBasis={};const zero=this.forward({});
    for(const side of ['left','right']){
      this.arm[side]=kin.joints.filter(j=>j.name.startsWith(side+'_')&&/shoulder|elbow|wrist/.test(j.name)&&j.type==='revolute');
      const palm=zero.world.get(side+'_palm_force_sensor'),finger=new THREE.Vector3().setFromMatrixPosition(zero.world.get(side+'_index_force_sensor_3')).applyMatrix4(palm.clone().invert());
      finger.z=0;finger.normalize();const normal=vec([0,0,1]);
      this.localBasis[side]=new THREE.Matrix4().makeBasis(finger,normal.clone().cross(finger),normal).transpose();
    }
  }
  forward(q){
    const world=new Map([[this.kin.root_link,mat(this.kin.root_matrix)]]),joints=new Map();
    for(const j of this.kin.joints){
      const before=world.get(j.parent).clone().multiply(this.origins.get(j.name));
      if(j.type==='revolute')joints.set(j.name,{position:new THREE.Vector3().setFromMatrixPosition(before),axis:this.axes.get(j.name).clone().transformDirection(before)});
      const value=j.mimic?Number(j.mimic.offset||0)+Number(j.mimic.multiplier||1)*(q[j.mimic.joint]||0):(q[j.name]||0);
      if(value)before.multiply(new THREE.Matrix4().makeRotationAxis(this.axes.get(j.name),value));
      world.set(j.id,before);
    }
    return {world,joints};
  }
  orientation(side,forward,normal){
    forward=forward.clone().normalize();normal=normal.clone().normalize();
    return new THREE.Matrix4().makeBasis(forward,normal.clone().cross(forward),normal).multiply(this.localBasis[side]);
  }
  solve(q,side,target,rotation){
    const initial={...q},names=this.arm[side],sign=side==='left'?1:-1;
    let result=this.iterate(q,side,target,rotation),best={...q};
    if(result.error>.003||result.rotationError>.03){
      for(const seed of [[-.8,sign*.3,0,1.2,0,0,0],[-1.2,sign*.3,sign*.7,.8,0,0,0],[-1.5,sign*.7,0,1.2,0,0,0]]){
        const candidate={...initial};names.forEach((j,i)=>candidate[j.name]=seed[i]);
        const test=this.iterate(candidate,side,target,rotation);
        if(test.error+.1*test.rotationError<result.error+.1*result.rotationError){result=test;best=candidate;}
        if(result.error<.0003&&result.rotationError<.005)break;
      }
    }
    for(const j of names)q[j.name]=best[j.name];
    this.lastRotationError=result.rotationError;return result.error;
  }
  iterate(q,side,target,rotation,iterations=65){
    const names=this.arm[side],weight=.22;let error=Infinity;
    for(let iteration=0;iteration<iterations;iteration++){
      const fk=this.forward(q),palm=fk.world.get(side+'_palm_force_sensor'),position=new THREE.Vector3().setFromMatrixPosition(palm);
      const dp=target.clone().sub(position);error=dp.length();
      const current=new THREE.Quaternion().setFromRotationMatrix(palm),desired=new THREE.Quaternion().setFromRotationMatrix(rotation),delta=desired.multiply(current.invert()).normalize();
      if(delta.w<0)delta.set(-delta.x,-delta.y,-delta.z,-delta.w);
      const norm=Math.hypot(delta.x,delta.y,delta.z),angle=2*Math.atan2(norm,delta.w),dr=norm>1e-9?vec([delta.x,delta.y,delta.z]).multiplyScalar(angle/norm):vec([0,0,0]);
      if(error<.0002&&dr.length()<.004)break;
      const residual=[dp.x,dp.y,dp.z,weight*dr.x,weight*dr.y,weight*dr.z];
      const columns=names.map(j=>{const k=fk.joints.get(j.name),linear=k.axis.clone().cross(position.clone().sub(k.position));return [linear.x,linear.y,linear.z,weight*k.axis.x,weight*k.axis.y,weight*k.axis.z]});
      const normal=Array.from({length:6},(_,i)=>Array.from({length:6},(_,j)=>columns.reduce((s,c)=>s+c[i]*c[j],0)+(i===j?.00008:0)));
      const dual=solveLinear(normal,residual);
      names.forEach((joint,i)=>{const step=THREE.MathUtils.clamp(columns[i].reduce((s,c,k)=>s+c*dual[k],0),-.18,.18);q[joint.name]=THREE.MathUtils.clamp((q[joint.name]||0)+step,joint.limits.lower+.001,joint.limits.upper-.001)});
    }
    const actual=this.forward(q).world.get(side+'_palm_force_sensor');
    const rotationError=new THREE.Quaternion().setFromRotationMatrix(actual).angleTo(new THREE.Quaternion().setFromRotationMatrix(rotation));
    return {error:new THREE.Vector3().setFromMatrixPosition(actual).distanceTo(target),rotationError};
  }
}
