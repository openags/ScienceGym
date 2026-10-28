import * as THREE from 'three';

// Reuse the existing source-joint cover solver and reviewed reference motion.
// The caller supplies the original laboratory closures; no scene is reset here.
export function createMeasurementSourceActions(ctx) {
  const ids = ['ftir_open', 'ftir_close', 'reference_restore', 'reference_store'];
  const selected = Object.fromEntries(ids.map(id => {
    const phase = ctx.phases.find(p => p.id === id);
    if (!phase) throw Error('Missing source action: ' + id);
    return [id, phase];
  }));
  const rows = matrix => {
    const values = matrix.clone().transpose().toArray();
    return Array.from({length: 4}, (_, i) => values.slice(i * 4, i * 4 + 4));
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
    const root = new THREE.Matrix4().makeRotationZ(r.yaw).setPosition(r.position.x, r.position.y, r.rootZ);
    return {q, root: rows(root), cover_angle_rad: ctx.ftirCoverAngle(t)};
  }
  return {sample, descriptions: Object.fromEntries(ids.map(id => [id, {
    source_phase: id, duration_s: selected[id].duration,
    first: sample(id, 0), last: sample(id, selected[id].duration)
  }]))};
}
