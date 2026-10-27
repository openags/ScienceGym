import * as THREE from 'three';

// A separately inspectable exchange episode with declared initial conditions.
// It does not replace delivery, acquisition, or the full paper timeline.
const matrix = rows => new THREE.Matrix4().fromArray(rows.flat()).transpose();
const clamp = THREE.MathUtils.clamp;
const smooth = x => x * x * (3 - 2 * x);

function sample(segment, time) {
  const rows = segment.rows, elapsed = clamp(time - segment.start, 0, segment.duration_s);
  let low = 0, high = rows.length - 1;
  while (high - low > 1) {
    const mid = (low + high) >> 1;
    if (rows[mid].time_s <= elapsed) low = mid; else high = mid;
  }
  const a = rows[low], b = rows[high];
  let u = a === b ? 0 : clamp((elapsed - a.time_s) / (b.time_s - a.time_s), 0, 1);
  if (segment.interpolation === 'smooth') u = smooth(u);
  const q = Object.fromEntries(Object.keys(a.q).map(n => [n, THREE.MathUtils.lerp(a.q[n], b.q[n], u)]));
  const rootA = matrix(a.root), rootB = matrix(b.root);
  const p = new THREE.Vector3().setFromMatrixPosition(rootA).lerp(new THREE.Vector3().setFromMatrixPosition(rootB), u);
  const rotation = new THREE.Quaternion().setFromRotationMatrix(rootA).slerp(new THREE.Quaternion().setFromRotationMatrix(rootB), u);
  const root = new THREE.Matrix4().compose(p, rotation, new THREE.Vector3(1, 1, 1));
  const elements = root.clone().transpose().toArray();
  return {q, root, rootRows: Array.from({length: 4}, (_, i) => elements.slice(i * 4, i * 4 + 4)), closure: THREE.MathUtils.lerp(a.closure, b.closure, u)};
}

export async function installOpticalEpisode(ctx, filename = 'optical_episode.json') {
  const episode = await ctx.read('viewer/cooling_concept_v2/' + filename);
  if (!episode.continuous_at_segment_boundaries) throw Error('Optical episode has discontinuous boundaries');
  const descriptor = episode.deformable_tool;
  if (descriptor.model !== 'symmetric_fixed_heel_cantilever_v1') throw Error('Unknown tweezer deformation');
  const tool = ctx.groups.get(descriptor.id), source = ctx.manifest.assets.find(a => a.id === descriptor.id);
  const meshes = [];
  tool.traverse(node => {
    if (!node.isMesh) return;
    node.geometry = node.geometry.clone();
    meshes.push({node, rest: node.geometry.attributes.position.array.slice(), sign: node.name.startsWith('ptfe_spring_arm_') ? Number(node.name.split('_').at(-1)) : 0});
  });
  if (meshes.filter(m => m.sign).length !== 2) throw Error('Expected both source tweezer arms');
  let lastClosure;
  function deform(closure) {
    if (!(closure >= 0 && closure <= 1)) throw Error('Invalid tweezer closure');
    if (closure === lastClosure) return;
    for (const {node, rest, sign} of meshes) {
      const attribute = node.geometry.attributes.position;
      for (let i = 0; i < rest.length; i += 3) {
        const a = 1 - clamp(rest[i] / descriptor.length_m, 0, 1);
        attribute.array[i + 1] = rest[i + 1] - sign * descriptor.tip_deflection_m * closure * a * a * (3 - a) / 2;
      }
      attribute.needsUpdate = true;
      node.geometry.computeVertexNormals();
      node.geometry.computeBoundingSphere();
      node.geometry.computeBoundingBox();
    }
    lastClosure = closure;
  }
  ctx.reset();
  const deformationSamples = [0, Math.max(...episode.segments.flatMap(s => s.rows.map(r => r.closure))), 1].map(closure => {
    deform(closure);
    return {closure, parts: meshes.map(({node}) => ({name: node.name, node_matrix: node.matrix.toArray(), vertices: Array.from(node.geometry.attributes.position.array), indices: node.geometry.index ? Array.from(node.geometry.index.array) : Array.from({length: node.geometry.attributes.position.count}, (_, i) => i)}))};
  });
  const deformableGeometry = [{...descriptor, source: source.geometry, source_sha256: source.geometry_sha256, samples: deformationSamples}];
  const palmToTool = matrix(episode.tool_T_palm).invert(), toolToHolder = matrix(episode.holder_T_tool).invert();
  const apply = (group, pose) => pose.decompose(group.position, group.quaternion, group.scale);
  const phases = episode.segments.map(s => ({id: s.id, start: s.start, end: s.end, duration: s.duration_s, kind: s.interpolation === 'linear' && s.duration_s > 2 ? 'move' : 'work', action: s.id, refs: s.source_operation_refs}));
  function poseAt(t) {
    t = clamp(t, 0, episode.duration_s);
    const index = episode.segments.findIndex(s => t < s.end);
    const selected = index < 0 ? episode.segments.length - 1 : index;
    const segment = episode.segments[selected], state = sample(segment, t);
    // Instrument state is fixed for this separately initialized episode.
    // reset() ran at installation; each moving group is assigned below.
    const r = ctx.pose(state.q, state.rootRows); r.p = phases[selected];
    const toolPose = segment.tool_held ? state.root.clone().multiply(ctx.handIK.forward(state.q).world.get('right_palm_force_sensor')).multiply(palmToTool) : matrix(episode.tool_rest);
    apply(tool, toolPose); deform(state.closure);
    apply(ctx.groups.get('tray_white'), matrix(episode.tray_matrix));
    for (const kind of ['white', 'black']) {
      const pose = segment.held_specimen === kind ? toolPose.clone().multiply(toolToHolder) : matrix(segment.stored_specimens[kind]);
      apply(ctx.groups.get('optical_witness_' + kind), pose);
    }
    ctx.scene.updateMatrixWorld(true);
    return {t, r, segment, state};
  }
  const clean = new URLSearchParams(location.search).has('clean');
  let now = 0, playing = false, previousClock = performance.now();
  function renderAt(t) {
    const frame = poseAt(t); now = frame.t;
    ctx.camera.position.copy(frame.r.position).add(new THREE.Vector3(1.1, -1.6, 1.95));
    ctx.camera.lookAt(frame.r.position.clone().add(new THREE.Vector3(.04, .27, .85)));
    ctx.localKey.position.copy(frame.r.position).add(new THREE.Vector3(1, -.2, 2.4));
    ctx.localKey.target.position.copy(frame.r.position).add(new THREE.Vector3(0, .3, 1));
    ctx.renderer.render(ctx.scene, ctx.camera);
    if (!clean) {
      const activity = frame.segment.id.includes('_delivery') ? '工位间送样' : frame.segment.id.includes('_retrieve') ? '取回与收纳' : '装样与工具归位';
      document.getElementById('title').textContent = (frame.segment.id.startsWith('white') ? '白色' : '黑色') + '试片 · ' + activity;
      document.getElementById('detail').textContent = '红外工位取放检查 · ' + frame.segment.id;
      document.getElementById('seek').value = now;
    }
    window.currentFrame = {time_s: now, stage: frame.segment.id, robot_position: frame.r.position.toArray(), robot_yaw: frame.r.yaw};
  }
  window.auditFrame = t => {
    const {t: time, r, segment, state} = poseAt(t);
    return {...ctx.snapshot(time, r), deformable_states: {[descriptor.id]: state.closure}, optical_state: {tool_held: segment.tool_held, held_specimen: segment.held_specimen, stored_specimens: segment.stored_specimens}};
  };
  window.renderAt = renderAt;
  window.concept = {
    manifest: ctx.manifest, sourceHashes: ctx.sourceHashes, extraGeometry: ctx.extraGeometry, deformableGeometry,
    opticalEpisode: {scope: episode.scope, status: episode.status, initial_conditions: episode.initial_conditions, whole_scene_validation_pending: episode.whole_scene_validation_pending},
    duration: episode.duration_s, phases, criticalTimes: episode.segments.flatMap(s => [s.start, s.end]),
    assetCount: ctx.groups.size, robotCount: 1, renderAt,
    rendererInfo: () => ctx.renderer.info.render,
    frameJpeg: t => {renderAt(t); return ctx.renderer.domElement.toDataURL('image/jpeg', .92).split(',')[1];}
  };
  const seek = document.getElementById('seek'), play = document.getElementById('play');
  seek.max = episode.duration_s;
  play.onclick = () => {playing = !playing; previousClock = performance.now(); play.textContent = playing ? '暂停' : '播放';};
  seek.oninput = e => {playing = false; play.textContent = '播放'; renderAt(Number(e.target.value));};
  // No replacement film exists yet. Do not expose the original film as this episode.
  document.querySelector('a[download]').hidden = true;
  const steps = document.querySelector('a[href="workflow.json"]');
  steps.href = filename; steps.textContent = '取放步骤与初始条件';
  function tick(clock) {
    if (playing) {
      renderAt(now + (clock - previousClock) / 1000);
      if (now >= episode.duration_s) {playing = false; play.textContent = '播放';}
    }
    previousClock = clock; requestAnimationFrame(tick);
  }
  renderAt(0); requestAnimationFrame(tick);
}
