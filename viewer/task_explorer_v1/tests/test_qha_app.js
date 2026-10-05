/* Independent QHA-focused mocked-DOM navigation audit. No adapter imports.
 * The source packages, independently byte-pinned by test_qha_independent.py,
 * supply route/operation expectations. This is not browser or visual QA.
 * Run: node tests/test_qha_app.js [path/to/standalone.html]
 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const assert = require('assert'), crypto = require('crypto');
const VIEW = path.resolve(__dirname, '..');
const ROOT = path.resolve(VIEW, '../..');
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const source = name => read(path.join(ROOT, 'tasks/qha_operations_v2', name));
const operations = source('operations.json').operations;
const branches = source('branches.json').branches;
const outcomes = source('source_outcomes_reference.json');
const expectedRoutes = new Map(branches.map(b => [b.id, b.operations]));
expectedRoutes.set('OPERATIONS_REFERENCE', operations.map(o => o.id));
for (const id of ['CONTROLS_REFERENCE', 'FAILURE_REFERENCE', 'BINDINGS_REFERENCE',
                  'OUTCOMES_REFERENCE', 'HOLD_QUALIFICATION']) expectedRoutes.set(id, []);

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
let hash = '#qha', handler;
const location = {get hash() { return hash; }, set hash(value) {
  hash = value.startsWith('#') ? value : '#' + value; if (handler) handler();
}};
const window = {
  SCIENCEGYM_DATA: Object.fromEntries(['chiral', 'qha'].map(id => [id, read(path.join(VIEW, 'data', id + '.json'))])),
  addEventListener: (event, callback) => { if (event === 'hashchange') handler = callback; }
};
const context = {window, document, location, console, atob, Uint8Array,
  Blob: class {constructor(parts, options) { this.parts = parts; this.options = options; }},
  URL: {createObjectURL: () => 'blob:independent-qha', revokeObjectURL() {}}};
vm.createContext(context);
if (process.argv[2]) {
  for (const script of fs.readFileSync(process.argv[2], 'utf8').matchAll(/<script>([\s\S]*?)<\/script>/g)) {
    vm.runInContext(script[1], context);
  }
} else vm.runInContext(fs.readFileSync(path.join(VIEW, 'app.js'), 'utf8'), context);
const explorer = window.ScienceGymExplorer, family = explorer.data.qha, state = explorer.state;
const frozen = JSON.stringify(family);
assert.strictEqual(state.family, 'qha');
assert.strictEqual(state.route, 'HOLD_QUALIFICATION');
assert.strictEqual(state.op, null);
assert.strictEqual(state.steps.length, 0);
assert.strictEqual(family.routes.length, 17);
const familyButton = elements.families.children.find(b => b.dataset.family === 'qha');
assert(familyButton);
let occurrences = 0;
for (const [routeId, expectedIds] of expectedRoutes) {
  location.hash = 'qha/' + routeId;
  assert.deepStrictEqual(Array.from(state.steps, s => s.id), expectedIds, routeId + ' source-derived membership');
  assert.strictEqual(document.querySelectorAll('.operation').length, expectedIds.length);
  assert(!walk([elements.routeCanvas]).some(n => n.className.split(' ').includes('connector')), 'No invented adjacency: ' + routeId);
  assert(!text(elements.routeCanvas).includes('undefined'));
  for (const step of [...state.steps]) {
    location.hash = ['qha', routeId, step.id, step.index].join('/');
    assert.strictEqual(state.op, step.id); assert.strictEqual(state.occurrence, step.index);
    const sourceOp = operations.find(o => o.id === step.id);
    assert(text(elements.inspector).includes(sourceOp.name));
    assert(text(elements.inspector).includes('No observed post-state field supplied'));
    assert(text(elements.inspector).includes('no live device control'));
    assert(text(elements.inspector).includes('Design/evidence-schema coverage only'));
    document.querySelectorAll('.operation')[step.index].onclick();
    document.querySelectorAll('.operation')[step.index].onclick();
    assert.strictEqual(state.op, step.id);
    occurrences++;
  }
  elements['tab-dependencies'].onclick();
  assert.strictEqual(elements.dependenciesView.hidden, false);
  assert(text(elements.dependenciesView).includes('only exact dependency and lifecycle contracts'));
  elements['tab-contract'].onclick();
  assert(text(elements.contractView).includes('does not evaluate completion or produce scientific results'));
  elements['tab-route'].onclick();
  assert.strictEqual(elements.routeView.hidden, false);
}
assert.strictEqual(occurrences, 30);
// Stale selection and hostile deep links cannot activate a metadata-only route.
for (const id of ['CONTROLS_REFERENCE', 'FAILURE_REFERENCE', 'BINDINGS_REFERENCE',
                  'OUTCOMES_REFERENCE', 'HOLD_QUALIFICATION']) {
  for (const suffix of ['R05/0', 'R14/999', 'UNKNOWN/-1', 'R05/NaN']) {
    location.hash = 'qha/DIRECT/R05/0';
    elements.operationSearch.oninput({target: {value: 'CCC'}});
    location.hash = 'qha/' + id + '/' + suffix;
    assert.strictEqual(state.op, null); assert.strictEqual(state.steps.length, 0);
    assert.strictEqual(document.querySelectorAll('.operation').length, 0);
    assert.strictEqual(elements.operationSearch.value, '');
    assert(!text(elements.inspector).includes(operations[5].name));
    elements.operationSearch.oninput({target: {value: 'source'}});
    assert.strictEqual(elements.searchCount.textContent, '0 matches');
  }
}
for (const target of ['qha', 'qha/INVALID_ROUTE/R05/0', 'qha//R14/0']) {
  location.hash = 'qha/DIRECT/R05/0'; location.hash = target;
  assert.strictEqual(state.route, 'HOLD_QUALIFICATION'); assert.strictEqual(state.op, null);
}
location.hash = 'qha/DIRECT/R05/0'; familyButton.onclick(); familyButton.onclick();
assert.strictEqual(state.route, 'HOLD_QUALIFICATION'); assert.strictEqual(state.op, null);
location.hash = 'qha/%invalid/R05/0'; assert.strictEqual(state.family, 'chiral');
familyButton.onclick(); assert.strictEqual(state.route, 'HOLD_QUALIFICATION');
// No new telemetry: source outcomes are a zero-operation reference with exact units and guards.
location.hash = 'qha/OUTCOMES_REFERENCE';
assert(text(elements.routeDetails).includes(outcomes.classification));
assert(text(elements.routeDetails).includes(outcomes.grading_rule));
assert.strictEqual(elements.routeTitle.textContent, 'AUTHOR-REPORTED OUTCOMES · never new measurement telemetry');
for (const outcome of outcomes.outcomes) {
  assert(text(elements.routeDetails).includes(outcome.id));
  assert(text(elements.routeDetails).includes(outcome.uncertainty_semantics));
}
assert.strictEqual(state.op, null);
// Sanitization is audit lineage only; it creates no new operation or scientific design.
elements['tab-contract'].onclick();
for (const label of ['review/SANITIZED REPIN LINEAGE', 'review/SANITIZED REPIN REVIEW']) {
  assert(text(elements.contractView).includes(label));
}
assert(text(elements.contractView).includes('review/deep_buffer_scan.json'));
assert(text(elements.contractView).includes('review/native_equivalence.json'));
assert.strictEqual(family.context.release_boundary.paper_design_count, 1);
assert.strictEqual(family.summary_counts.source_json_documents, 40);
assert.strictEqual(family.summary_counts.asset_json_documents, 28);
location.hash = 'qha/CLOSE/R14/0';
assert(text(elements.inspector).includes('"R03"'));
assert(text(elements.inspector).includes('Join every started service branch'));
const saved = location.hash;
location.hash = 'qha/OUTCOMES_REFERENCE'; location.hash = saved;
assert.strictEqual(state.route, 'CLOSE'); assert.strictEqual(state.op, 'R14');
// All source/asset links retain exact local bytes, including embedded standalone payloads.
elements['tab-contract'].onclick();
const links = walk([elements.contractView]).filter(n => n.tagName === 'a' && Object.hasOwn(family.source_files, n.textContent));
assert.strictEqual(links.length, 68);
for (const link of links) {
  const item = family.source_files[link.textContent];
  assert.strictEqual(link.attrs.href, window.SCIENCEGYM_EMBEDDED_FILES ? 'blob:independent-qha' : item.url);
}
for (const item of [...Object.values(family.source_files), ...family.asset_links]) {
  const bytes = fs.readFileSync(path.resolve(VIEW, item.url));
  assert.strictEqual(crypto.createHash('sha256').update(bytes).digest('hex'), item.sha256);
  if (window.SCIENCEGYM_EMBEDDED_FILES) {
    const embedded = window.SCIENCEGYM_EMBEDDED_FILES[item.url];
    assert(embedded, 'Missing embedded QHA source: ' + item.url);
    assert(Buffer.from(embedded.base64, 'base64').equals(bytes), 'Changed embedded QHA source: ' + item.url);
  }
}
location.hash = 'qha/HOLD_QUALIFICATION';
assert.strictEqual(JSON.stringify(family), frozen, 'Inspection must not mutate source data or mark completion');
console.log('PASS: independent QHA mocked-DOM audit, 17 views / 30 selections, exact source memberships, metadata-only outcome/hold hostile links, default fallback, repeated navigation, source/embedded bytes, no chronology or generated telemetry, immutable family');
