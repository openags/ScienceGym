import * as THREE from 'three';

// Reuse the existing source-joint cover solver and reviewed reference motion.
// The caller supplies the original laboratory closures; no scene is reset here.
export function createMeasurementSourceActions(ctx) {
  let coverHandCorrection=null;
  function setCoverHandCorrection(value){
    const names=Object.keys(value.new_q);
    if(names.length!==2||!names.every(n=>['right_index_1_joint','right_thumb_2_joint'].includes(n)))throw Error('Unexpected cover contact correction');
    if(!names.every(n=>Number.isFinite(value.new_q[n])&&value.old_q[n]>0))throw Error('Invalid cover contact correction');
    coverHandCorrection=structuredClone(value);
  }
  const ids = ['ftir_open', 'ftir_close', 'reference_restore', 'reference_store'];
  const selected = Object.fromEntries(ids.map(id => {
    const phase = ctx.phases.find(p => p.id === id);
    if (!phase) throw Error('Missing source action: ' + id);
    return [id, phase];
  }));
  const rows = matrix => {
    const values = matrix.clone().transpose().toArray();
    return Array.from({length: 4}, (_, i) => values.slice(i * 4, i * 4 + 4));
  };
  function sample(id, elapsed) {
    const phase = selected[id];
    if (!phase) throw Error('Unsupported measurement source action: ' + id);
    const local = THREE.MathUtils.clamp(elapsed, 0, phase.duration);
    if (id.startsWith('reference_')) {
      const time = id === 'reference_store' ? local : phase.duration - local;
      const state = ctx.referenceAt(ctx.referenceTransfer, time, ctx.handIK);
      const delta = state.reference.clone().multiply(new THREE.Matrix4().makeTranslation(
        ...ctx.referenceTransfer.reference_port_m.map(v => -v)));
      return {q: state.q, root: rows(state.root), cover_angle_rad: -65 * Math.PI / 180,
        reference_delta: rows(delta), reference_mode: state.mode,
        reference_stage: state.stage, reference_grip: state.closed};
    }
    // Stay inside this named phase at its last endpoint; the original timeline
    // selects the next phase exactly at a boundary.
    const t = Math.min(phase.end - 1e-9, phase.start + local);
    const r = ctx.robotAt(t), q = ctx.constrainHands(r, ctx.jointPose(r));
    if(coverHandCorrection)for(const [name,value] of Object.entries(coverHandCorrection.new_q)){
      q[name]=(q[name]??0)*value/coverHandCorrection.old_q[name];
    }
    const root = new THREE.Matrix4().makeRotationZ(r.yaw).setPosition(r.position.x, r.position.y, r.rootZ);
    if(coverHandCorrection&&local>6&&local<13.4){
      // Refine the contact interval's arm residual; do not widen collision
      // tolerances or move the handle. Blend back to the saved free-arm paths.
      const profile=ctx.coverProfile,angle=ctx.ftirCoverAngle(t),inverse=root.clone().invert();
      const smooth=x=>{x=THREE.MathUtils.clamp(x,0,1);return x*x*(3-2*x);};
      const rotation=new THREE.Matrix4().makeRotationX(angle);
      const hinge=new THREE.Vector3(...profile.hinge_m);
      const center=new THREE.Vector3(...profile.handle_center_m).sub(hinge).applyMatrix4(rotation).add(hinge);
      const palm=rotation.clone().setPosition(center).multiply(new THREE.Matrix4().fromArray(profile.palm_matrix.flat()).transpose());
      const point=new THREE.Vector3().setFromMatrixPosition(palm);
      const approach=smooth((local-6)/2),release=smooth((local-11.4)/2);
      point.addScaledVector(new THREE.Vector3(...profile.approach_offset_m),local<8.2?1-approach:release);
      const precise={...q};
      const fit=ctx.opticalIK.iterate(precise,'right',point.applyMatrix4(inverse),inverse.clone().multiply(palm),100,{position:1e-7,rotation:1e-6});
      const weight=smooth((local-6)/1.8)*(1-smooth((local-11.4)/2));
      if(weight===1&&(fit.error>1e-6||fit.rotationError>1e-5))throw Error('Cover contact refinement did not converge');
      for(const joint of ctx.handIK.arm.right)q[joint.name]=THREE.MathUtils.lerp(q[joint.name],precise[joint.name],weight);
    }
    return {q, root: rows(root), cover_angle_rad: ctx.ftirCoverAngle(t)};
  }
  return {sample, setCoverHandCorrection, descriptions: Object.fromEntries(ids.map(id => [id, {
    source_phase: id, duration_s: selected[id].duration,
    first: sample(id, 0), last: sample(id, selected[id].duration)
  }]))};
}
