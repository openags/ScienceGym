import * as THREE from 'three';

const matrix = rows => new THREE.Matrix4().fromArray(rows.flat()).transpose();
const clamp = THREE.MathUtils.clamp;
const apply = (node, pose) => pose.decompose(node.position, node.quaternion, node.scale);

function sample(segment, time) {
  const rows = segment.rows, elapsed = clamp(time - segment.start, 0, segment.duration_s);
  let lo = 0, hi = rows.length - 1;
  while (hi - lo > 1) {const mid = (lo + hi) >> 1; if (rows[mid].time_s <= elapsed) lo = mid; else hi = mid;}
  const a = rows[lo], b = rows[hi];
  let u = clamp((elapsed - a.time_s) / (b.time_s - a.time_s), 0, 1);
  if (segment.interpolation === 'smooth') u = u * u * (3 - 2 * u);
  const q = Object.fromEntries(Object.keys(a.q).map(n => [n, THREE.MathUtils.lerp(a.q[n], b.q[n], u)]));
  const rootA = matrix(a.root), rootB = matrix(b.root);
  const position = new THREE.Vector3().setFromMatrixPosition(rootA).lerp(new THREE.Vector3().setFromMatrixPosition(rootB), u);
  const rotation = new THREE.Quaternion().setFromRotationMatrix(rootA).slerp(new THREE.Quaternion().setFromRotationMatrix(rootB), u);
  const root = new THREE.Matrix4().compose(position, rotation, new THREE.Vector3(1, 1, 1));
  const values = root.clone().transpose().toArray();
  return {q, root, rootRows: Array.from({length: 4}, (_, i) => values.slice(i * 4, i * 4 + 4)), lid: THREE.MathUtils.lerp(a.lid_m, b.lid_m, u), supportedCover: matrix(a.cover_matrix)};
}

export async function installCaryEpisode(ctx, episode) {
  if (!episode.continuous_at_segment_boundaries) throw Error('Discontinuous Cary episode');
  ctx.reset();
  const initial = episode.initial_scene;
  for (const [id, values] of Object.entries(initial.groups)) {
    if (id !== 'g1') apply(ctx.groups.get(id), new THREE.Matrix4().fromArray(values));
  }
  ctx.scene.updateMatrixWorld(true);
  const worldPose = (node, pose) => apply(node, node.parent.matrixWorld.clone().invert().multiply(pose));
  const lookup = new Map(ctx.nodeRest.map(n => [n.asset + '::' + n.node.name, n.node]));
  for (const part of initial.parts) worldPose(lookup.get(part.asset + '::' + part.name), new THREE.Matrix4().fromArray(part.matrix));
  ctx.scene.updateMatrixWorld(true);
  for (const [id, values] of Object.entries(initial.extra_matrices)) worldPose(ctx.extraMeshes.get(id), new THREE.Matrix4().fromArray(values));
  ctx.scene.updateMatrixWorld(true);
  const access = [...episode.lid_parts, ...episode.cover_parts].map(name => {
    const node = lookup.get('cary::' + name);
    return {name, node, rest: node.matrixWorld.clone(), lid: episode.lid_parts.includes(name)};
  });
  const inverseGrasp = matrix(episode.grasp_palm_world).invert();
  const phases = episode.segments.map(s => ({id: s.id, start: s.start, end: s.end, duration: s.duration_s, kind: s.interpolation === 'linear' ? 'move' : 'work', action: s.id}));
  function poseAt(t) {
    t = clamp(t, 0, episode.duration_s);
    let index = episode.segments.findIndex(s => t < s.end);
    if (index < 0) index = episode.segments.length - 1;
    const segment = episode.segments[index], state = sample(segment, t), r = ctx.pose(state.q, state.rootRows); r.p = phases[index];
    const cover = segment.cover_held ? state.root.clone().multiply(ctx.handIK.forward(state.q).world.get('right_palm_force_sensor')).multiply(inverseGrasp) : state.supportedCover;
    const slide = new THREE.Matrix4().makeTranslation(0, state.lid, 0);
    for (const part of access) worldPose(part.node, (part.lid ? slide : cover).clone().multiply(part.rest));
    ctx.scene.updateMatrixWorld(true);
    return {t, r, segment, state, cover};
  }
  const clean = new URLSearchParams(location.search).has('clean');
  let now = 0, playing = false, previousClock = performance.now();
  const labels = {
    lid_slide: '滑开仪器主盖', step_to_hood: '调整操作位置', hood_unhook: '提起舱罩脱钩',
    hood_step_back: '携舱罩退步', hood_carry_sideways: '搬至台面暂存位置',
    hood_approach_support: '靠近台面', hood_lower_onto_support: '将舱罩放稳',
    hood_release_on_bench: '松开把手', hood_return_hand: '收回操作手',
    return_to_lid: '返回主盖操作位置', extension_step_push_lid: '迈步推开主盖',
    extension_release_pull: '松开主盖把手', extension_step_back_after_release: '退步离开主盖'
  };
  function renderAt(t) {
    const frame = poseAt(t); now = frame.t;
    ctx.camera.position.copy(frame.r.position).add(new THREE.Vector3(1.15, -1.65, 1.95));
    ctx.camera.lookAt(frame.r.position.clone().add(new THREE.Vector3(.08, .38, .85)));
    ctx.localKey.position.copy(frame.r.position).add(new THREE.Vector3(.8, -.2, 2.4));
    ctx.localKey.target.position.copy(frame.r.position).add(new THREE.Vector3(0, .35, 1));
    ctx.renderer.render(ctx.scene, ctx.camera);
    if (!clean) {
      document.getElementById('title').textContent = labels[frame.segment.id] || 'Cary 仪器开舱操作';
      document.getElementById('detail').textContent = frame.segment.id;
      document.getElementById('seek').value = now;
    }
    window.currentFrame = {time_s: now, stage: frame.segment.id, robot_position: frame.r.position.toArray(), robot_yaw: frame.r.yaw};
  }
  window.auditFrame = t => {
    const {t: time, r, segment, state, cover} = poseAt(t);
    return {...ctx.snapshot(time, r), cary_state: {lid_m: state.lid, cover_held: segment.cover_held, cover_matrix: cover.toArray()}};
  };
  window.renderAt = renderAt;
  window.concept = {
    manifest: ctx.manifest, sourceHashes: ctx.sourceHashes, extraGeometry: ctx.extraGeometry,
    caryEpisode: {scope: episode.scope, status: episode.status, initial_conditions: episode.initial_conditions, whole_scene_validation_pending: episode.whole_scene_validation_pending},
    duration: episode.duration_s, phases, criticalTimes: episode.segments.flatMap(s => s.rows.map(r => s.start + r.time_s)),
    assetCount: ctx.groups.size, robotCount: 1, renderAt, rendererInfo: () => ctx.renderer.info.render,
    frameJpeg: t => {renderAt(t); return ctx.renderer.domElement.toDataURL('image/jpeg', .92).split(',')[1];}
  };
  const seek = document.getElementById('seek'), play = document.getElementById('play'); seek.max = episode.duration_s;
  play.onclick = () => {playing = !playing; previousClock = performance.now(); play.textContent = playing ? '暂停' : '播放';};
  seek.oninput = e => {playing = false; play.textContent = '播放'; renderAt(Number(e.target.value));};
  document.querySelector('a[download]').hidden = true;
  const steps = document.querySelector('a[href="workflow.json"]'); steps.href = 'cary_access_episode.json'; steps.textContent = '开舱步骤与初始条件';
  function tick(clock) {
    if (playing) {renderAt(now + (clock - previousClock) / 1000); if (now >= episode.duration_s) {playing = false; play.textContent = '播放';}}
    previousClock = clock; requestAnimationFrame(tick);
  }
  renderAt(0); requestAnimationFrame(tick);
}
