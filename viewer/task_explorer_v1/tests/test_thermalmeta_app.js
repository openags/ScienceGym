/* Independent thermalmeta mocked-DOM navigation audit; no adapter imports.
 * Expectations come from byte-pinned raw package documents. This is not real
 * browser, visual, scientific, or physical qualification.
 * Run: node tests/test_thermalmeta_app.js [path/to/standalone.html]
 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const assert = require('assert'), crypto = require('crypto');
const VIEW = path.resolve(__dirname, '..'), ROOT = path.resolve(VIEW, '../..');
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const source = name => read(path.join(ROOT, 'tasks/thermalmeta_operations_v2', name));
const stages = source('operations.json').stages, branches = source('branches.json');
const matrix = source('coverage_matrix.json').stages, binding = source('scene_binding_contract.json');
const outcomes = source('source_outcomes_reference.json');
const expectedRoutes = new Map(branches.families.map(b => [b.id,
  matrix.filter(row => row.branch_ids.includes(b.id)).map(row => row.stage_id)]));
const metadataRoutes = [
  ...branches.child_branches.map(b => b.id), ...binding.condition_views.map(c => c.condition_id),
  'PREPARATION_REFERENCE', 'CONTROLS_REFERENCE', 'OUTCOMES_REFERENCE', 'BINDINGS_REFERENCE',
  'SERVICE_CUSTODY_HOLD', 'HOLD_UNQUALIFIED'
];
for (const id of metadataRoutes) expectedRoutes.set(id, []);
expectedRoutes.set('OPERATIONS_REFERENCE', stages.map(s => s.id));

class Element {
  constructor(tag) {
    this.tagName = tag; this.attrs = {}; this.children = []; this.dataset = {};
    this.style = {setProperty() {}}; this.value = ''; this.hidden = false; this.className = '';
    this.classList = {toggle: (name, on) => {
      const values = new Set(this.className.split(' ').filter(Boolean));
      on ? values.add(name) : values.delete(name); this.className = [...values].join(' ');
    }};
  }
  setAttribute(key, value) {
    this.attrs[key] = String(value);
    if (key.startsWith('data-')) this.dataset[key.slice(5).replace(/-([a-z])/g, (_, x) => x.toUpperCase())] = String(value);
    if (key === 'value') this.value = value;
  }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = nodes; }
  set textContent(value) { this.text = String(value); this.children = []; }
  get textContent() { return this.text || ''; }
}
const ids = [...fs.readFileSync(path.join(VIEW, 'index.html'), 'utf8').matchAll(/\bid="([^"]+)"/g)].map(m => m[1]);
const elements = Object.fromEntries(ids.map(id => [id, new Element('div')]));
for (const tab of ['route', 'dependencies', 'contract']) {
  elements['tab-' + tab].setAttribute('role', 'tab');
  elements['tab-' + tab].setAttribute('data-tab', tab);
}
const walk = roots => roots.flatMap(n => n instanceof Element ? [n, ...walk(n.children)] : []);
const text = element => walk([element]).map(n => n.textContent).join('\n');
const document = {
  documentElement: new Element('html'), getElementById: id => elements[id],
  createElement: tag => new Element(tag), createTextNode: value => String(value),
  querySelectorAll: selector => {
    const nodes = walk(Object.values(elements));
    if (selector === 'nav button') return elements.families.children;
    if (selector === '[role=tab]') return nodes.filter(n => n.attrs.role === 'tab');
    if (selector === '.operation') return nodes.filter(n => n.className.split(' ').includes('operation'));
    throw Error('Unsupported selector: ' + selector);
  }
};
let hash = '#thermalmeta', handler;
const location = {get hash() { return hash; }, set hash(value) {
  hash = value.startsWith('#') ? value : '#' + value; if (handler) handler();
}};
const window = {
  SCIENCEGYM_DATA: Object.fromEntries(['chiral', 'thermalmeta'].map(id => [id, read(path.join(VIEW, 'data', id + '.json'))])),
  addEventListener: (event, callback) => { if (event === 'hashchange') handler = callback; }
};
const context = {window, document, location, console, atob, Uint8Array,
  Blob: class {constructor(parts, options) { this.parts = parts; this.options = options; }},
  URL: {createObjectURL: () => 'blob:independent-thermalmeta', revokeObjectURL() {}}};
vm.createContext(context);
if (process.argv[2]) {
  for (const script of fs.readFileSync(process.argv[2], 'utf8').matchAll(/<script>([\s\S]*?)<\/script>/g)) {
    vm.runInContext(script[1], context);
  }
} else vm.runInContext(fs.readFileSync(path.join(VIEW, 'app.js'), 'utf8'), context);
const explorer = window.ScienceGymExplorer, family = explorer.data.thermalmeta, state = explorer.state;
const frozen = JSON.stringify(family);
assert.strictEqual(state.family, 'thermalmeta');
assert.strictEqual(state.route, 'HOLD_UNQUALIFIED');
assert.strictEqual(state.op, null); assert.strictEqual(state.steps.length, 0);
assert.strictEqual(family.routes.length, 37);
const familyButton = elements.families.children.find(b => b.dataset.family === 'thermalmeta');
assert(familyButton);
let selections = 0;
for (const [routeId, expectedIds] of expectedRoutes) {
  location.hash = 'thermalmeta/' + routeId;
  assert.deepStrictEqual(Array.from(state.steps, s => s.id), expectedIds, routeId + ' source-derived membership');
  assert.strictEqual(document.querySelectorAll('.operation').length, expectedIds.length);
  assert(!walk([elements.routeCanvas]).some(n => n.className.split(' ').includes('connector')),
    'No invented adjacency: ' + routeId);
  assert(!text(elements.routeCanvas).includes('undefined'));
  for (const step of [...state.steps]) {
    location.hash = ['thermalmeta', routeId, step.id, step.index].join('/');
    assert.strictEqual(state.op, step.id); assert.strictEqual(state.occurrence, step.index);
    const sourceStage = stages.find(s => s.id === step.id);
    assert(text(elements.inspector).includes(sourceStage.title));
    assert(text(elements.inspector).includes('No observed post-state field supplied'));
    assert(text(elements.inspector).includes('no additional action or hardware command is invented'));
    assert(text(elements.inspector).includes(sourceStage.execution_surface));
    document.querySelectorAll('.operation')[step.index].onclick();
    document.querySelectorAll('.operation')[step.index].onclick();
    assert.strictEqual(state.op, step.id);
    selections++;
  }
  elements['tab-dependencies'].onclick();
  assert.strictEqual(elements.dependenciesView.hidden, false);
  assert(text(elements.dependenciesView).includes('Exact dependency, loop, failure and custody contracts remain authoritative'));
  assert(text(elements.dependenciesView).includes('SERVICE_CUSTODY_HOLD'));
  elements['tab-contract'].onclick();
  assert(text(elements.contractView).includes('does not evaluate completion or produce scientific results'));
  elements['tab-route'].onclick(); assert.strictEqual(elements.routeView.hidden, false);
}
assert.strictEqual(selections, [...expectedRoutes.values()].reduce((sum, ids) => sum + ids.length, 0));
assert.strictEqual(metadataRoutes.length, 24);
// Stale selection, repeated clicks, search and hostile deep links never activate metadata.
for (const id of metadataRoutes) {
  for (const suffix of ['P11/0', 'P20/999', 'UNKNOWN/-1', 'P11/NaN']) {
    location.hash = 'thermalmeta/B01/P11/0';
    elements.operationSearch.oninput({target: {value: 'thermal'}});
    location.hash = 'thermalmeta/' + id + '/' + suffix;
    assert.strictEqual(state.op, null); assert.strictEqual(state.steps.length, 0);
    assert.strictEqual(document.querySelectorAll('.operation').length, 0);
    assert.strictEqual(elements.operationSearch.value, '');
    assert(!text(elements.inspector).includes(stages[10].title));
    elements.operationSearch.oninput({target: {value: 'source'}});
    assert.strictEqual(elements.searchCount.textContent, '0 matches');
  }
}
for (const target of ['thermalmeta', 'thermalmeta/INVALID_ROUTE/P11/0', 'thermalmeta//P20/0']) {
  location.hash = 'thermalmeta/B01/P11/0'; location.hash = target;
  assert.strictEqual(state.route, 'HOLD_UNQUALIFIED'); assert.strictEqual(state.op, null);
}
location.hash = 'thermalmeta/B01/P11/0'; familyButton.onclick(); familyButton.onclick();
assert.strictEqual(state.route, 'HOLD_UNQUALIFIED'); assert.strictEqual(state.op, null);
location.hash = 'thermalmeta/%invalid/P11/0'; assert.strictEqual(state.family, 'chiral');
familyButton.onclick(); assert.strictEqual(state.route, 'HOLD_UNQUALIFIED');
// Outcomes remain exact cited source references, never new measurements/reward thresholds.
location.hash = 'thermalmeta/OUTCOMES_REFERENCE';
assert(text(elements.routeDetails).includes(outcomes.status));
assert(text(elements.routeDetails).includes(outcomes.qualification_warning));
assert(text(elements.routeDetails).includes(outcomes.experimental.raw_numeric_curves));
assert.strictEqual(elements.routeTitle.textContent, 'AUTHOR-REPORTED OUTCOMES · no new telemetry');
assert.strictEqual(state.op, null);
// Source selectors do not become evidence of independently manufactured specimens.
for (const cell of binding.condition_views) {
  location.hash = 'thermalmeta/' + cell.condition_id;
  assert(text(elements.routeDetails).includes(cell.specimen_id));
  assert(text(elements.routeDetails).includes(cell.profile_number_to_orientation_status));
  assert.strictEqual(state.op, null);
}
location.hash = 'thermalmeta/SERVICE_CUSTODY_HOLD';
assert(text(elements.routeDetails).includes('Never successful and never authorizes retrieval'));
assert(text(elements.routeDetails).includes('timeout'));
assert.strictEqual(state.op, null);
location.hash = 'thermalmeta/OPERATIONS_REFERENCE/P15/14';
assert(text(elements.inspector).includes(stages[14].title));
assert(text(elements.inspector).includes('H_RELEASE'));
const saved = location.hash;
location.hash = 'thermalmeta/OUTCOMES_REFERENCE'; location.hash = saved;
assert.strictEqual(state.route, 'OPERATIONS_REFERENCE'); assert.strictEqual(state.op, 'P15');
// Every linked recursive document and preview keeps exact local/standalone bytes.
elements['tab-contract'].onclick();
const links = walk([elements.contractView]).filter(n => n.tagName === 'a' && Object.hasOwn(family.source_files, n.textContent));
assert.strictEqual(links.length, 56);
for (const link of links) {
  const item = family.source_files[link.textContent];
  assert.strictEqual(link.attrs.href, window.SCIENCEGYM_EMBEDDED_FILES ? 'blob:independent-thermalmeta' : item.url);
}
for (const item of [...Object.values(family.source_files), ...family.asset_links]) {
  const bytes = fs.readFileSync(path.resolve(VIEW, item.url));
  assert.strictEqual(crypto.createHash('sha256').update(bytes).digest('hex'), item.sha256);
  if (window.SCIENCEGYM_EMBEDDED_FILES) {
    const embedded = window.SCIENCEGYM_EMBEDDED_FILES[item.url];
    assert(embedded, 'Missing embedded thermalmeta source: ' + item.url);
    assert(Buffer.from(embedded.base64, 'base64').equals(bytes), 'Changed embedded source: ' + item.url);
  }
}
location.hash = 'thermalmeta/HOLD_UNQUALIFIED';
assert.strictEqual(JSON.stringify(family), frozen, 'Inspection cannot mutate data or mark completion');
console.log('PASS: independent thermalmeta mocked-DOM audit, 37 views / ' + selections +
  ' source-derived selections, 24 metadata-only views, hostile links, repeated navigation, hold/custody boundaries, exact source and embedded bytes, immutable family');
