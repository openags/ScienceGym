/* Independent frictional mocked-DOM navigation audit, derived from frozen raw
 * source contracts. No adapter imports, no physical or scientific qualification.
 * Run: node tests/test_frictional_app.js [path/to/standalone.html]
 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const assert = require('assert'), crypto = require('crypto');
const VIEW = path.resolve(__dirname, '..'), ROOT = path.resolve(VIEW, '../..');
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const source = name => read(path.join(ROOT, 'tasks/frictional_operations_v2', name));
const stages = source('operations.json').operations, branches = source('branches.json').branches;
const outcomes = source('source_outcomes_reference.json');
const oracle = read(path.join(__dirname, 'frictional_frozen_oracle.json'));
for (const pack of Object.values(oracle.packages)) {
  for (const [name, pin] of Object.entries(pack.files)) {
    const bytes = fs.readFileSync(path.join(ROOT, pack.folder, name));
    assert.strictEqual(bytes.length, pin.bytes);
    assert.strictEqual(crypto.createHash('sha256').update(bytes).digest('hex'), pin.sha256);
  }
}
const expectedRoutes = new Map(branches.map(b => [b.id,
  stages.filter(o => o.branch_ids.includes(b.id)).map(o => o.id)]));
expectedRoutes.set('OPERATIONS_REFERENCE', stages.map(o => o.id));
const metadataRoutes = ['PREPARATION_REFERENCE', 'CONTROLS_REFERENCE', 'FAILURE_REFERENCE',
  'BINDINGS_REFERENCE', 'OUTCOMES_REFERENCE', 'HOLD_QUALIFICATION'];
for (const id of metadataRoutes) expectedRoutes.set(id, []);
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
let hash = '#frictional', handler;
const location = {get hash() { return hash; }, set hash(value) {
  hash = value.startsWith('#') ? value : '#' + value; if (handler) handler();
}};
const window = {
  SCIENCEGYM_DATA: Object.fromEntries(['chiral', 'frictional'].map(id => [id, read(path.join(VIEW, 'data', id + '.json'))])),
  addEventListener: (event, callback) => { if (event === 'hashchange') handler = callback; }
};
const context = {window, document, location, console, atob, Uint8Array,
  Blob: class {constructor(parts, options) { this.parts = parts; this.options = options; }},
  URL: {createObjectURL: () => 'blob:independent-frictional', revokeObjectURL() {}}};
vm.createContext(context);
if (process.argv[2]) {
  for (const script of fs.readFileSync(process.argv[2], 'utf8').matchAll(/<script>([\s\S]*?)<\/script>/g)) {
    vm.runInContext(script[1], context);
  }
} else vm.runInContext(fs.readFileSync(path.join(VIEW, 'app.js'), 'utf8'), context);
const explorer = window.ScienceGymExplorer, family = explorer.data.frictional, state = explorer.state;
const frozen = JSON.stringify(family);
assert.strictEqual(state.family, 'frictional');
assert.strictEqual(state.route, 'HOLD_QUALIFICATION');
assert.strictEqual(state.op, null); assert.strictEqual(state.steps.length, 0);
assert.strictEqual(family.routes.length, 16);
const familyButton = elements.families.children.find(b => b.dataset.family === 'frictional');
assert(familyButton);
let selections = 0;
for (const [routeId, expectedIds] of expectedRoutes) {
  location.hash = 'frictional/' + routeId;
  assert.deepStrictEqual(Array.from(state.steps, s => s.id), expectedIds, routeId + ' raw-source operation membership');
  assert.strictEqual(document.querySelectorAll('.operation').length, expectedIds.length);
  assert(!walk([elements.routeCanvas]).some(n => n.className.split(' ').includes('connector')), 'No invented adjacency: ' + routeId);
  assert(!text(elements.routeCanvas).includes('undefined'));
  for (const step of [...state.steps]) {
    location.hash = ['frictional', routeId, step.id, step.index].join('/');
    assert.strictEqual(state.op, step.id); assert.strictEqual(state.occurrence, step.index);
    const sourceStage = stages.find(s => s.id === step.id);
    assert(text(elements.inspector).includes(sourceStage.name));
    assert(text(elements.inspector).includes('No observed post-state field supplied'));
    assert(text(elements.inspector).includes('no live device control'));
    assert(text(elements.inspector).includes(sourceStage.gate));
    if(sourceStage.dependency_rule) assert(text(elements.inspector).includes(sourceStage.dependency_rule));
    assert(text(elements.inspector).includes(sourceStage.required_output));
    document.querySelectorAll('.operation')[step.index].onclick();
    document.querySelectorAll('.operation')[step.index].onclick();
    assert.strictEqual(state.op, step.id);
    selections++;
  }
  elements['tab-dependencies'].onclick();
  assert.strictEqual(elements.dependenciesView.hidden, false);
  assert(text(elements.dependenciesView).includes('Evidence ingestion order is not a physical schedule'));
  assert(text(elements.dependenciesView).includes('all job closeouts'));
  elements['tab-contract'].onclick();
  assert(text(elements.contractView).includes('does not evaluate completion or produce scientific results'));
  elements['tab-route'].onclick(); assert.strictEqual(elements.routeView.hidden, false);
}
assert.strictEqual(selections, [...expectedRoutes.values()].reduce((n, ids) => n + ids.length, 0));
// Clear stale stage/search state and reject hostile selections on all metadata routes.
for (const routeId of metadataRoutes) {
  for (const suffix of ['R07/0', 'R12/999', 'UNKNOWN/-1', 'R07/NaN']) {
    location.hash = 'frictional/B06/R07/2';
    elements.operationSearch.oninput({target: {value: 'pressure'}});
    location.hash = 'frictional/' + routeId + '/' + suffix;
    assert.strictEqual(state.op, null); assert.strictEqual(state.steps.length, 0);
    assert.strictEqual(document.querySelectorAll('.operation').length, 0);
    assert.strictEqual(elements.operationSearch.value, '');
    assert(!text(elements.inspector).includes(stages[6].name));
    elements.operationSearch.oninput({target: {value: 'source'}});
    assert.strictEqual(elements.searchCount.textContent, '0 matches');
  }
}
for (const target of ['frictional', 'frictional/INVALID_ROUTE/R07/0', 'frictional//R12/0']) {
  location.hash = 'frictional/B06/R07/2'; location.hash = target;
  assert.strictEqual(state.route, 'HOLD_QUALIFICATION'); assert.strictEqual(state.op, null);
}
location.hash = 'frictional/B06/R07/2'; familyButton.onclick(); familyButton.onclick();
assert.strictEqual(state.route, 'HOLD_QUALIFICATION'); assert.strictEqual(state.op, null);
location.hash = 'frictional/%invalid/R07/0'; assert.strictEqual(state.family, 'chiral');
familyButton.onclick(); assert.strictEqual(state.route, 'HOLD_QUALIFICATION');
// Outcomes, source conflicts, closed services, borrowed references and custody stay explicit.
location.hash = 'frictional/OUTCOMES_REFERENCE';
assert(text(elements.routeDetails).includes(outcomes.use));
for (const outcome of outcomes.outcomes) assert(text(elements.routeDetails).includes(outcome.expectation));
assert.strictEqual(elements.routeTitle.textContent, 'AUTHOR-REPORTED OUTCOMES · never new measurement telemetry');
assert.strictEqual(state.op, null);
location.hash = 'frictional/B06';
assert(text(elements.routeDetails).includes('Viscosity-rate scaling control'));
location.hash = 'frictional/B07';
assert(text(elements.routeDetails).includes('High-phi granular-fracturing extension'));
location.hash = 'frictional/B08';
assert(text(elements.routeDetails).includes('no task-count increment'));
location.hash = 'frictional/B09';
assert(text(elements.routeDetails).includes('Boyle-law conflict'));
location.hash = 'frictional/BINDINGS_REFERENCE';
for (const phrase of ['CC BY-NC-SA 3.0 Unported', 'evidence_only_proxy', 'physical_motion_target', 'original_assets_only']) {
  assert(text(elements.routeDetails).includes(phrase));
}
location.hash = 'frictional/HOLD_QUALIFICATION';
for(const phrase of ['Coral0.1 versus1.0', 'Boyle-law sign', 'No invented formulation', 'No silent formula repair']) {
  assert(text(elements.routeDetails).includes(phrase));
}
assert.strictEqual(state.op, null);
location.hash = 'frictional/OPERATIONS_REFERENCE/R11/10';
assert(text(elements.inspector).includes('including failures, before R08-R10'));
assert(text(elements.inspector).includes('repeatable by job'));
const saved = location.hash;
location.hash = 'frictional/OUTCOMES_REFERENCE'; location.hash = saved;
assert.strictEqual(state.route, 'OPERATIONS_REFERENCE'); assert.strictEqual(state.op, 'R11');
location.hash = 'frictional/OPERATIONS_REFERENCE/R12/11';
assert(text(elements.inspector).includes('no single global R11 token'));
// Every source and preview resolves to exact local bytes or exact embedded bytes.
elements['tab-contract'].onclick();
const links = walk([elements.contractView]).filter(n => n.tagName === 'a' && Object.hasOwn(family.source_files, n.textContent));
assert.strictEqual(links.length, 73);
for (const link of links) {
  const item = family.source_files[link.textContent];
  assert.strictEqual(link.attrs.href, window.SCIENCEGYM_EMBEDDED_FILES ? 'blob:independent-frictional' : item.url);
}
for (const item of [...Object.values(family.source_files), ...family.asset_links]) {
  const bytes = fs.readFileSync(path.resolve(VIEW, item.url));
  assert.strictEqual(crypto.createHash('sha256').update(bytes).digest('hex'), item.sha256);
  if (window.SCIENCEGYM_EMBEDDED_FILES) {
    const embedded = window.SCIENCEGYM_EMBEDDED_FILES[item.url];
    assert(embedded, 'Missing embedded source: ' + item.url);
    assert(Buffer.from(embedded.base64, 'base64').equals(bytes), 'Changed embedded source: ' + item.url);
  }
}
location.hash = 'frictional/HOLD_QUALIFICATION';
assert.strictEqual(JSON.stringify(family), frozen, 'Inspection cannot mutate sources or invent completion');
console.log('PASS: independent frictional mocked-DOM audit, 16 views / ' + selections +
  ' raw-source selections, 6 metadata-only views, hostile links, repeated navigation, source-claim/geometry boundaries, 73 exact source links, immutable family');
