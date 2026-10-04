"""Independent read-only viewer fidelity and adversarial pairing tests.

Run from this repository, or set SCIENCEGYM_ROOT to its checkout. Any mutation of
source bytes is confined to an ephemeral copy; the release candidate is untouched.
This does not establish physical execution, scientific validation or source fidelity
beyond the frozen authored JSON contracts.
"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(os.environ['SCIENCEGYM_ROOT']).resolve() if 'SCIENCEGYM_ROOT' in os.environ else Path(__file__).resolve().parents[3]
VIEWER = ROOT / 'viewer/task_explorer_v1'
TASK = ROOT / 'tasks/midinfrared_operations_v2'
ASSET = ROOT / 'assets/midinfrared_scene_assets_v1'
sys.path.insert(0, str(VIEWER))
import midinfrared_adapters as adapter

ALIASES = {'unknown_parameters.json': 'unknowns', 'evaluator_reference.json': 'acceptance', 'lineage_contract.json': 'lineage'}

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def unpool(f, value):
    if isinstance(value, dict):
        if set(value) == {'$shared'}:
            return unpool(f, f['shared'][value['$shared']])
        return {k: unpool(f, v) for k, v in value.items()}
    if isinstance(value, list):
        return [unpool(f, v) for v in value]
    return value

def walks(nodes):
    for node in nodes:
        yield node
        yield from walks(node.get('children', []))

def pointer(document, value):
    for part in value.lstrip('/').split('/') if value else []:
        part = part.replace('~1', '/').replace('~0', '~')
        document = document[int(part)] if isinstance(document, list) else document[part]
    return document

class MidinfraredIndependent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = {p.relative_to(TASK).as_posix(): load(p) for p in TASK.rglob('*.json')}
        cls.generated_pooled = load(VIEWER / 'data/midinfrared.json')
        cls.generated = unpool(cls.generated_pooled, cls.generated_pooled)
        cls.live = adapter.adapt_midinfrared(TASK)
        cls.temp = tempfile.TemporaryDirectory(prefix='midinfrared-independent-')
        cls.copy_root = Path(cls.temp.name)
        cls.copy_task = cls.copy_root / 'tasks/midinfrared_operations_v2'
        cls.copy_asset = cls.copy_root / 'assets/midinfrared_scene_assets_v1'
        shutil.copytree(TASK, cls.copy_task)
        shutil.copytree(ASSET, cls.copy_asset)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_recursive_json_lossless(self):
        self.assertEqual(len(self.docs), 34)
        expected = {ALIASES.get(n, n.removesuffix('.json')): d for n, d in self.docs.items()}
        self.assertEqual(len(expected), len(self.docs), 'Context-name collision would drop source JSON')
        for f in [self.live, self.generated]:
            self.assertEqual(f['context'], expected)
            self.assertEqual(set(f['source_files']), set(self.docs))
            for n in self.docs:
                with self.subTest(file=n):
                    self.assertEqual(f['source_files'][n]['sha256'], hashlib.sha256((TASK/n).read_bytes()).hexdigest())
                    self.assertEqual(f['source_files'][n]['repository_path'], 'tasks/midinfrared_operations_v2/'+n)

    def test_generated_equals_live_after_lossless_unpool(self):
        f = copy.deepcopy(self.generated)
        f.pop('shared')
        self.assertEqual(f, self.live)

    def test_js_and_json_payloads_identical(self):
        text = (VIEWER/'data/midinfrared.js').read_text()
        prefix = 'window.SCIENCEGYM_DATA=window.SCIENCEGYM_DATA||{};window.SCIENCEGYM_DATA["midinfrared"]='
        self.assertTrue(text.startswith(prefix))
        payload = text[len(prefix):].strip().removesuffix(';')
        self.assertEqual(json.loads(payload), self.generated_pooled)

    def test_operation_fields_exact_and_unexecuted(self):
        raw = self.docs['operations.json']['operations']
        self.assertEqual([o['id'] for o in raw], [f'R{i:02}' for i in range(1,23)])
        for f in [self.live, self.generated]:
            self.assertEqual(len(f['operations']), len(raw))
            for o, mapped in zip(raw, f['operations']):
                with self.subTest(operation=o['id']):
                    self.assertEqual(mapped['detail'], o)
                    self.assertEqual(mapped['title'], o['name'])
                    self.assertEqual(mapped['actions'], o['substeps'])
                    self.assertEqual(mapped['pre'], o['entry_guards'])
                    self.assertIn('No observed post-state', mapped['post'])
                    self.assertEqual(mapped['objects'], {'asset_ids':o['asset_ids'],'required_inputs':o['inputs']})
                    self.assertEqual(mapped['sources'], o['source_anchors'])
                    self.assertEqual(mapped['acceptance'], {k:o[k] for k in ['outputs','observations_to_record','evidence_role','service_request_is_completion']})
                    self.assertEqual(mapped['recovery'], {k:o[k] for k in ['failure_closeout','failure_disposition']})
                    self.assertEqual(mapped['provenance'], {k:o[k] for k in ['classification','physical_execution_qualified','runtime']})
                    self.assertIs(mapped['provenance']['physical_execution_qualified'], False)
                    self.assertEqual(mapped['provenance']['runtime'], 'unimplemented')
                    self.assertEqual(pointer(self.docs[mapped['source_file']], mapped['source_pointer']), o)

    def test_exact_branch_membership_without_invented_chronology(self):
        branches = self.docs['branches.json']['branches']
        for f in [self.live, self.generated]:
            routes = [r for r in f['routes'] if r['route_kind']=='experimental_design']
            self.assertEqual(len(routes), 8)
            for branch, route in zip(branches, routes):
                with self.subTest(branch=branch['id']):
                    self.assertEqual(route['id'], branch['id'])
                    self.assertEqual(route['detail'], branch)
                    nodes = list(walks(route['nodes']))
                    self.assertEqual([n['id'] for n in nodes if n['type']=='op'], branch['operations'])
                    self.assertTrue(all(n.get('ordered') is False for n in nodes if n['type'] in ['obligations','condition']))
                    self.assertEqual([n['meta']['source_contract'] for n in nodes if n['type']=='condition'], [branch])
                    for node in nodes:
                        if node['type']=='op':
                            self.assertEqual(pointer(self.docs[node['meta']['source_file']], node['meta']['source_pointer']), node['id'])
                            self.assertIn('not execution', node['meta']['meaning'])

    def test_inventory_metadata_references_and_default_hold(self):
        for f in [self.live, self.generated]:
            routes = {r['id']:r for r in f['routes']}
            self.assertEqual(len(routes), 14)
            inventory = routes['OPERATIONS_REFERENCE']
            self.assertEqual([n['id'] for n in walks(inventory['nodes']) if n['type']=='op'], [o['id'] for o in self.docs['operations.json']['operations']])
            self.assertEqual(inventory['detail'], self.docs['operations.json'])
            required = {'PREPARATION_REFERENCE':'preparation_routes.json','CONTROLS_REFERENCE':'controls_and_repeats.json','RECOVERY_REFERENCE':'recovery_boundaries.json','NONMANUAL_REFERENCE':'nonmanual_scope.json',f['default_route']:'episode_input_contract.json'}
            self.assertEqual(f['default_route'], 'HOLD_QUALIFICATION')
            self.assertEqual(f['default_route'], self.docs['episode_input_contract.json']['default'])
            self.assertNotIn(f['default_route'], [o['id'] for o in f['operations']])
            for identifier, file in required.items():
                r=routes[identifier]
                self.assertIs(r['metadata_only'], True)
                self.assertEqual(r['detail'], self.docs[file])
                self.assertFalse([n for n in walks(r['nodes']) if n['type']=='op'])

    def test_controls_lineage_failed_holds_and_repeats_retained(self):
        context=self.generated['context']
        for file in ['controls_and_repeats.json','lineage_contract.json','lifecycle_contract.json','transport_routes.json','recovery_boundaries.json','safety_boundaries.json']:
            self.assertEqual(context[ALIASES.get(file,file.removesuffix('.json'))], self.docs[file])
        controls=context['controls_and_repeats']
        self.assertEqual(len(controls['controls']),12)
        repeat=controls['authored_repeat_plan']
        for field in ['number_of_specimens','number_of_independent_runs','number_of_days']:
            self.assertIsNone(repeat[field])
        self.assertIn('failed-run evidence',context['lineage']['immutable_records'])
        self.assertIn('all successful and failed branches -> final archive manifest',context['lineage']['required_edges'])
        self.assertEqual(self.generated['dependencies']['operation_dependencies'], [{'operation_id':o['id'],'depends_on':o['depends_on']} for o in self.docs['operations.json']['operations']])

    def test_source_facts_design_and_unavailable_evidence_separate(self):
        f=self.generated
        self.assertEqual(f['evidence'], {v['id']:v for v in self.docs['source_parameters.json']['facts']})
        self.assertEqual(f['context']['source_outcomes']['classification'], 'author_reported_outcomes_not_robot_success_thresholds')
        self.assertEqual(f['context']['controls_and_repeats']['classification'],'authored_robot_translation')
        self.assertEqual(f['visibility'],'author_evaluator_reference_only')
        self.assertIs(f['actor_projection_implemented'],False)
        self.assertIn('Raw data and modified source code remain unavailable',f['source_warnings'])
        self.assertIn('not reviewed continuously',f['source_warnings'])
        self.assertIn('not a paper quotation',f['operations'][0]['display_title_basis'])
        boundary=f['context']['RELEASE_BOUNDARY']
        self.assertEqual(boundary['validated_runnable_whole_paper_tasks'],0)
        for key in ['whole_paper_execution_complete','physical_execution','physical_simulation','scientific_reproduction','source_data_reanalysis','source_files_exported','exact_geometry_validated','hardware_safety_qualified']:
            self.assertIs(boundary[key],False)

    def test_rate_modes_unknowns_and_counting_limits(self):
        f=self.generated
        self.assertIn('Approximately 10 Hz is a source reference only for analog 16x16 dynamic imaging',f['source_warnings'])
        self.assertIn('32x32 retains approximately 2.5 Hz',f['source_warnings'])
        self.assertIn('Neither rate is a hardware default',f['source_warnings'])
        self.assertIn('photon-counting rate',f['source_warnings'])
        unknown=f['context']['unknowns']['unknowns']
        self.assertEqual([u['id'] for u in unknown],[f'U{i:02}' for i in range(1,15)])
        self.assertTrue(all(u['resolved'] is False and u['physical_default'] is None for u in unknown))
        branches={b['id']:b for b in f['context']['branches']['branches']}
        self.assertIsNone(branches['B05']['detector_mode'])
        self.assertEqual(branches['B01']['detector_mode'],'spatial_diagnostic')
        self.assertEqual(branches['B08']['sample_role'],'silicon')
        self.assertIn('not independent repeats',f['status'])

    def test_12_exact_pins_22_bindings_44_anchors_and_asset_links(self):
        plan=self.generated['context']['asset_binding_plan']
        self.assertEqual(len(plan['final_asset_hashes']),12)
        self.assertEqual(len(plan['operation_bindings']),22)
        self.assertEqual(len({a for b in plan['operation_bindings'] for a in b['anchor_ids']}),44)
        for pin in plan['final_asset_hashes']:
            data=(ASSET/pin['path']).read_bytes()
            self.assertEqual(len(data),pin['bytes'])
            self.assertEqual(hashlib.sha256(data).hexdigest(),pin['sha256'])
        self.assertEqual(load(ASSET/'task_binding_snapshot.json')['binding_plan'],plan)
        for link in self.generated['asset_links']:
            self.assertEqual(hashlib.sha256((ROOT/link['path']).read_bytes()).hexdigest(),link['sha256'])
        self.assertEqual(len(self.generated['asset_links']),4)
        self.assertIn('unqualified',self.generated['asset_boundary'])

    def test_independent_negative_projection_probes(self):
        probes={
            'deleted_nested_review':lambda f:f['context'].pop('review/INDEPENDENT_REVIEW'),
            'source_document_omitted':lambda f:f['source_files'].pop('lineage_contract.json'),
            'source_hash_corrupted':lambda f:f['source_files']['operations.json'].__setitem__('sha256','0'*64),
            'control_dropped':lambda f:f['context']['controls_and_repeats']['controls'].pop(),
            'failed_evidence_dropped':lambda f:f['context']['lineage']['immutable_records'].remove('failed-run evidence'),
            'failed_archive_edge_dropped':lambda f:f['context']['lineage']['required_edges'].pop(),
            'gap_falsely_resolved':lambda f:f['context']['unknowns']['unknowns'][-1].__setitem__('resolved',True),
            'repeat_count_invented':lambda f:f['context']['controls_and_repeats']['authored_repeat_plan'].__setitem__('number_of_independent_runs',1),
            'required_output_claimed_observed':lambda f:f['operations'][0].__setitem__('post',f['operations'][0]['acceptance']['outputs']),
            'physical_qualification_invented':lambda f:f['operations'][0]['provenance'].__setitem__('physical_execution_qualified',True),
            'live_runtime_invented':lambda f:f['operations'][0]['provenance'].__setitem__('runtime','executed'),
            'scientific_credit_invented':lambda f:f['context']['RELEASE_BOUNDARY'].__setitem__('validated_runnable_whole_paper_tasks',1),
            'source_reanalysis_claimed':lambda f:f['context']['RELEASE_BOUNDARY'].__setitem__('source_data_reanalysis',True),
            'source_facts_omitted':lambda f:f['evidence'].pop('F01'),
            'wrong_source_pointer':lambda f:f['operations'][0].__setitem__('source_pointer','/operations/1'),
            'branch_membership_changed':lambda f:f['routes'][0]['nodes'][0]['children'].reverse(),
            'chronology_invented':lambda f:f['routes'][0]['nodes'][0].__setitem__('ordered',True),
            'photon_count_rate_claimed':lambda f:f.__setitem__('source_warnings','10 Hz applies to all photon-counting grids'),
            'default_hold_removed':lambda f:f.__setitem__('default_route','B01'),
            'hold_operation_invented':lambda f:f['operations'].append({'id':'HOLD_QUALIFICATION'}),
            'actor_permission_invented':lambda f:f.__setitem__('actor_projection_implemented',True),
            'source_sensor_default_invented':lambda f:f['context']['branches']['branches'][4].__setitem__('detector_mode','photon_count'),
            'binding_owner_changed':lambda f:f['context']['asset_binding_plan']['operation_bindings'][0].__setitem__('primary_asset_id','A01'),
            'asset_boundary_qualification_invented':lambda f:f.__setitem__('asset_boundary','Safety-qualified exact physical simulation')}
        for name, change in probes.items():
            with self.subTest(probe=name):
                f=copy.deepcopy(self.live);change(f)
                with self.assertRaises(ValueError):adapter.validate_projection(f,TASK)

    def test_independent_negative_pinned_asset_byte_probe(self):
        p=self.copy_asset/'affordances.json';original=p.read_bytes()
        try:
            p.write_bytes(original+b'\n')
            with self.assertRaisesRegex(ValueError,'Task-pinned scene file changed'):
                adapter.adapt_midinfrared(self.copy_task)
        finally:p.write_bytes(original)

    def test_independent_negative_wrapped_snapshot_probe(self):
        p=self.copy_asset/'task_binding_snapshot.json';original=p.read_bytes()
        try:
            doc=json.loads(original);doc['binding_plan']['operation_bindings'][0]['primary_target']='wrong.target'
            p.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError,'Task/asset snapshot mismatch'):
                adapter.adapt_midinfrared(self.copy_task)
        finally:p.write_bytes(original)

    def test_independent_negative_asset_pinned_task_probe(self):
        p=self.copy_task/'operations.json';original=p.read_bytes()
        try:
            doc=json.loads(original);doc['operations'][0]['name']+=' corrupted'
            p.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError,'Asset-pinned task file changed'):
                adapter.adapt_midinfrared(self.copy_task)
        finally:p.write_bytes(original)

if __name__=='__main__':
    unittest.main(verbosity=2)
