const NS = 'http://www.w3.org/2000/svg';
const node = (tag, attributes = {}, text) => {
  const el = document.createElementNS(NS, tag);
  for (const [key, value] of Object.entries(attributes)) el.setAttribute(key, value);
  if (text !== undefined) el.textContent = text;
  return el;
};

export async function installRoute(film, delivery, seek) {
  const response = await fetch('measurement_route.json');
  if (!response.ok) throw Error('工位路线暂不可用');
  const data = await response.json();
  if (data.video_sha256 !== delivery.video_sha256) throw Error('路线与视频版本不一致');
  const panel = document.getElementById('route-panel');
  const svg = document.getElementById('route-map');
  const rows = data.samples;
  let full = false, marker, progress, projected, project;

  function draw() {
    svg.replaceChildren();
    const bounds = full ? [-6.5, -.5, 12.5, 20.5] : [-.4, 6.1, 12.4, 10.7];
    const height = full ? 660 : 340;
    const scale = Math.min(960 / (bounds[2] - bounds[0]), (height - 40) / (bounds[3] - bounds[1]));
    const left = (1000 - (bounds[2] - bounds[0]) * scale) / 2;
    project = (x, y) => [left + (x - bounds[0]) * scale, 20 + (bounds[3] - y) * scale];
    svg.setAttribute('viewBox', `0 0 1000 ${height}`);
    svg.append(node('title', {}, '实验室平面图：备料台与 FTIR 工位之间的机器人移动路线'));
    function rect(bounds, fill, stroke) {
      const [x, y] = project(bounds[0], bounds[3]);
      return node('rect', {x, y, width: (bounds[2] - bounds[0]) * scale,
        height: (bounds[3] - bounds[1]) * scale, fill, stroke: stroke || 'none'});
    }
    for (const [lo, hi] of data.floors) svg.append(rect([lo[0], lo[1], hi[0], hi[1]], '#17232d', '#435562'));
    for (const [lo, hi] of data.walls) svg.append(rect([lo[0], lo[1], hi[0], hi[1]], '#526470'));
    const seen = new Set();
    for (const surface of data.surfaces) {
      const key = JSON.stringify(surface.xy_bounds_m);
      if (seen.has(key)) continue;
      seen.add(key);
      svg.append(rect(surface.xy_bounds_m, '#30434f', '#536b78'));
    }
    if (full) {
      for (const zone of data.zones) {
        const b = zone.bounds_m, [x, y] = project((b[0] + b[2]) / 2, (b[1] + b[3]) / 2);
        svg.append(node('text', {x, y, fill: '#91a5b1', 'text-anchor': 'middle', 'font-size': 15}, zone.label.split(' · ')[0]));
      }
    }
    projected = rows.map(r => project(r[1], r[2]).map(v => v.toFixed(2)).join(','));
    svg.append(node('polyline', {points: projected.join(' '), fill: 'none', stroke: '#627b82',
      'stroke-width': 3, 'stroke-linejoin': 'round', 'stroke-dasharray': '5 5'}));
    progress = node('polyline', {fill: 'none', stroke: '#8de0d0', 'stroke-width': 3, 'stroke-linejoin': 'round'});
    svg.append(progress);
    const compact = svg.clientWidth < 600, labelScale = compact ? 1000 / Math.max(300, svg.clientWidth) : 1;
    for (const station of data.stations) {
      const [x, y] = project(...station.position_m);
      const g = node('g', {class: 'map-station', role: 'button', tabindex: 0,
        'aria-label': `跳转到${station.label}`, transform: `translate(${x} ${y})`});
      const width = compact ? (full ? 56 : 76)*labelScale : station.id === 'ftir' ? 170 : 126;
      const label = compact ? (station.id === 'ftir' ? 'FTIR' : '取样台') : station.label;
      const size = (compact ? (full ? 11 : 14) : 16)*labelScale;
      const labelHeight = (compact ? 26 : 34)*labelScale;
      g.append(node('rect', {x: -width/2, y: -labelHeight/2, width, height: labelHeight, rx: 6, fill: '#203d43', stroke: '#8de0d0'}));
      g.append(node('text', {'text-anchor': 'middle', y: size*.33, fill: '#e4fff7', 'font-size': size}, label));
      g.onclick = () => seek(station.time_s);
      g.onkeydown = e => {if (e.key === 'Enter' || e.key === ' ') {e.preventDefault();seek(station.time_s);}};
      svg.append(g);
    }
    marker = node('g', {id: 'route-robot'});
    marker.append(node('circle', {r: 9, fill: '#b1f5e7', stroke: '#10151c', 'stroke-width': 3}));
    marker.append(node('path', {d: 'M 10 -5 L 19 0 L 10 5 Z', fill: '#b1f5e7'}));
    svg.append(marker);
    const [sx, sy] = project(full ? 10 : .4, full ? .4 : 6.5);
    svg.append(node('path', {d: `M ${sx} ${sy-4} v 8 M ${sx} ${sy} h ${scale} M ${sx+scale} ${sy-4} v 8`, stroke: '#adbdc5', fill: 'none'}));
    svg.append(node('text', {x: sx+scale/2, y: sy+21, fill: '#adbdc5', 'text-anchor': 'middle', 'font-size': 14}, '1 m'));
    update();
  }

  function update() {
    if (!marker) return;
    const time = Math.max(0, Math.min(film.currentTime || 0, data.duration_s));
    let lo = 0, hi = rows.length - 1;
    while (hi - lo > 1) {const mid = (lo + hi) >> 1;if (rows[mid][0] <= time) lo = mid;else hi = mid;}
    if (time >= rows[hi][0]) lo = hi;
    const a = rows[lo], b = rows[Math.min(lo + 1, rows.length - 1)];
    const u = a === b ? 0 : (time - a[0]) / (b[0] - a[0]);
    const [x, y] = project(a[1]+u*(b[1]-a[1]), a[2]+u*(b[2]-a[2]));
    const yaw = a[3]+u*Math.atan2(Math.sin(b[3]-a[3]), Math.cos(b[3]-a[3]));
    marker.setAttribute('transform', `translate(${x} ${y}) rotate(${-yaw*180/Math.PI})`);
    marker.dataset.time = String(time);
    marker.dataset.phase = a[4];
    progress.setAttribute('points', projected.slice(0, lo+1).join(' ')+` ${x},${y}`);
    document.getElementById('route-action').textContent = data.phase_titles[a[4]] || a[4];
    document.getElementById('route-payload').textContent = a[6] === 'white' ? '携带白色样片与镊子' : a[5] ? '携带镊子' : '白色样片与镊子已放置';
  }
  for (const button of document.querySelectorAll('[data-map-view]')) {
    button.onclick = () => {
      full = button.dataset.mapView === 'full';
      document.querySelectorAll('[data-map-view]').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
      draw();
    };
  }
  film.addEventListener('timeupdate', update);
  film.addEventListener('seeked', update);
  panel.hidden = false;
  draw();
  let lastWidth = svg.clientWidth;
  new ResizeObserver(() => {
    if (Math.abs(svg.clientWidth - lastWidth) > 1) {lastWidth = svg.clientWidth;draw();}
  }).observe(svg);
}
