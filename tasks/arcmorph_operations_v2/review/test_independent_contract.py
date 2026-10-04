"""Independent original tests of the declared offline task contract; no physical qualification."""
from copy import deepcopy
from dataclasses import replace
import sys
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('independent_task_contract', ROOT / 'tests' / 'contract.py')
C = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(C)

def read(name):
    return json.loads((ROOT / name).read_text())

def pair_fixture():
    keys = ('front_camera', 'front_lens', 'front_mount', 'side_camera', 'side_lens',
            'side_mount', 'fixture', 'height_reference', 'scale_reference')
    current = {k: k + ':revision1' for k in keys}
    cal = dict(calibration_id='synthetic-cal', revisions=deepcopy(current),
               reference_ids=[current['height_reference'], current['scale_reference']],
               valid_interval=[0, 100], role='independent_calibration', synthetic_only=True)
    token = dict(token_id='synthetic-token', specimen_id='synthetic-specimen',
                 configuration_revision='synthetic-cfg1', calibration_id='synthetic-cal',
                 lock_interval=[10, 20], active=True, all_locks=True, stable=True, synthetic_only=True)
    rows = []
    for n, view in enumerate(('front', 'side'), 1):
        rows.append(dict(capture_id='synthetic-capture' + str(n), camera_id=current[view + '_camera'],
                         lens_id=current[view + '_lens'], view_role=view, specimen_id=token['specimen_id'],
                         configuration_revision=token['configuration_revision'], token_id=token['token_id'],
                         calibration_id=token['calibration_id'], file_hash=str(n) * 64, time=10+n,
                         quality_ok=True, evidence_kind='synthetic_observation', synthetic_only=True))
    return rows, token, cal, current

def state():
    return dict(stock_id='synthetic-stock', specimen_id='synthetic-specimen', family_id='PP',
                drawing_revision='synthetic-drawing1', carrier_id='synthetic-carrier',
                station_id='synthetic-station1', revision=1, history=['synthetic-folded'],
                mounted=False, loaded=False, supported=True, synthetic_only=True)

class IndependentInventory(unittest.TestCase):
    def test_inventory_and_identifiers(self):
        self.assertEqual(set(C.BRANCHES), {'CS1','CS2','CS3','CS4','PP_PREP','PP_RIGID','PP_SHEAR'})
        self.assertEqual(set(C.OPS), {'R%02d' % i for i in range(31)})
        self.assertEqual(set(C.CONFLICTS), {'C%02d' % i for i in range(1,11)})
        self.assertEqual(set(C.UNKNOWNS), {'U%02d' % i for i in range(1,15)})
        self.assertEqual(len(read('coverage_matrix.json')['coverage']), 20)
        self.assertEqual({a['id'] for a in read('asset_binding_plan.json')['assets']}, {'A%02d' % i for i in range(1,13)})
        self.assertEqual(len(read('nonmanual_scope.json')['dispositions']), 6)
    def test_source_records_preserved_when_source_review_present(self):
        source = ROOT.parent / 'next-paper-review-20261004-evening'
        if not source.is_dir():
            self.skipTest('Accepted source-review directory not part of portable export')
        pairs = [('source_facts.json','source_parameters.json','facts'),
                 ('coverage_map.json','coverage_matrix.json','coverage'),
                 ('source_conflicts.json','source_conflicts.json','conflicts'),
                 ('unknowns.json','unknown_parameters.json','unknowns'),
                 ('source_outcomes_reference.json','source_outcomes.json','rows')]
        for original, authored, key in pairs:
            a=json.loads((source/original).read_text())[key]; b=read(authored)[key]
            self.assertEqual(len(a),len(b))
            for old,new in zip(a,b):
                for k,v in old.items():
                    with self.subTest(file=original,record=old.get('id'),field=k): self.assertEqual(new[k],v)
        for item in read('provenance.json')['source_review_hashes']:
            self.assertEqual(hashlib.sha256((source/item['document']).read_bytes()).hexdigest(),item['sha256'])
    def test_single_quantitative_specimen_and_eight_configurations(self):
        x=read('controls_and_repeats.json')
        self.assertEqual((x['source_quantitative_specimens'],x['source_quantitative_sets'],x['source_configurations']),(1,1,8))
        self.assertIsNone(x['source_technical_repeats_per_configuration'])
        self.assertIsNone(x['authored_repeat_default'])
        rigid=C.fixture('PP_RIGID:METADATA_OK')
        records=list(rigid['registry'].values())
        self.assertEqual(len({r['context']['specimen_id'] for r in records}),1)
        self.assertEqual(len({r['context']['stock_id'] for r in records}),1)
        for op in ('R13','R14','R15','R16','R17','R18'):
            self.assertEqual(sum(r['operation_id']==op for r in records),8)
    def test_four_cardstock_families_remain_distinct(self):
        for family in ('CS1','CS2','CS3','CS4'):
            branch=C.BRANCHES[family]
            self.assertEqual(branch['state_slots'],['ground','rigid','sheared'])
            records=list(C.fixture(family+':METADATA_OK')['registry'].values())
            self.assertEqual({r['context']['family_id'] for r in records},{family})
            self.assertEqual(sum(r['operation_id']=='R28' for r in records),3)
            self.assertIn('R07',[r['operation_id'] for r in records])
    def test_source_conflicts_and_unknowns_not_resolved_by_nominal_art(self):
        self.assertTrue(all(x['status']=='open' for x in C.CONFLICTS.values()))
        self.assertTrue(all(x['default'] is None for x in C.UNKNOWNS.values()))
        self.assertFalse(read('asset_binding_plan.json')['nominal_anchor_is_motion_permission'])
        facts={x['id']:x['reported'] for x in read('source_parameters.json')['facts']}
        self.assertEqual((facts['F02']['height_mm_methods'],facts['F02']['height_mm_figure']),(383.63,383.65))
        self.assertFalse(facts['F06']['quantitative_shear_validation'])
        self.assertIsNone(facts['F06']['load_magnitude'])
        self.assertTrue(facts['F08']['not_physical_specimen_defaults'])
    def test_truthful_release_boundary(self):
        boundary=read('RELEASE_BOUNDARY.json')
        self.assertEqual(boundary['validated_runnable_whole_paper_tasks'],0)
        for key in ('whole_paper_execution_complete','physical_execution','physical_simulation',
                    'scientific_reproduction','source_data_reanalysis','source_files_exported',
                    'exact_geometry_validated','hardware_safety_qualified','source_math_validated',
                    'repository_changes','remote_writes'):
            self.assertIs(boundary[key],False)
    def test_actor_allowlist_and_observation_separation(self):
        self.assertEqual(read('evaluator_reference.json')['actor_visible_allowlist'],['agent_visible.json'])
        actor=read('agent_visible.json')
        self.assertFalse(actor['source_outcomes_exposed'])
        self.assertFalse(actor['can_declare_observation'])
        self.assertNotIn('radius',json.dumps(actor).lower())
        self.assertEqual(read('analysis_contracts.json')['observables'],['height','interior_radius','exterior_radius'])
        self.assertTrue(read('analysis_contracts.json')['analysis_hold_does_not_erase_acquisition'])

class IndependentReplay(unittest.TestCase):
    def test_all_finite_replays_have_honest_scope(self):
        for fid in C.FIXTURE_IDS:
            with self.subTest(fixture=fid):
                f=C.fixture(fid);r=C.evaluate(f['events'],f['registry'],fid)
                self.assertTrue(r['contract_passed'])
                self.assertEqual(r['synthetic_metadata_complete'],fid.endswith(':METADATA_OK'))
                for k in ('physical_execution','physical_simulation','scientific_reproduction',
                          'source_data_reanalysis','whole_paper_execution_complete'):
                    self.assertIs(r[k],False)
                self.assertEqual(r['validated_runnable_whole_paper_tasks'],0)
    def test_actor_cannot_forge_values_roles_or_registry(self):
        fid='PP_RIGID:METADATA_OK';f=C.fixture(fid)
        for field in C.CONTEXT:
            with self.subTest(field=field):
                reg=deepcopy(f['registry']);next(iter(reg.values()))['context'][field]='forged'
                with self.assertRaises(C.ContractError):C.evaluate(f['events'],reg,fid)
        for field,value in [('role','actor_self_approved'),('operation_id','R30'),('depends_on',[])]:
            reg=deepcopy(f['registry']);last=list(reg)[-1];reg[last][field]=value
            with self.assertRaises(C.ContractError):C.evaluate(f['events'],reg,fid)
        for key in ('success','height','interior_radius','physical_qualified'):
            events=deepcopy(f['events']);events[0][key]=True
            with self.assertRaises(C.ContractError):C.evaluate(events,f['registry'],fid)
    def test_missing_repeated_reordered_or_other_fixture_events_reject(self):
        fid='CS2:METADATA_OK';f=C.fixture(fid)
        bad=[f['events'][:-1],f['events']+[f['events'][-1]],list(reversed(f['events']))]
        swapped=deepcopy(f['events']);swapped[0],swapped[1]=swapped[1],swapped[0];bad.append(swapped)
        for events in bad:
            with self.assertRaises(C.ContractError):C.evaluate(events,f['registry'],fid)
        other=C.fixture('CS1:METADATA_OK')
        with self.assertRaises(C.ContractError):C.evaluate(other['events'],other['registry'],fid)

class IndependentGuards(unittest.TestCase):
    def test_custody_preserves_parentage_history_and_support(self):
        before=state();after=deepcopy(before);after.update(revision=2,history=before['history']+['synthetic-moved'],station_id='synthetic-station2')
        self.assertTrue(C.custody_transition(before,after)['custody_valid_synthetic'])
        for key,value in [('stock_id','other'),('specimen_id','other'),('family_id','CS1'),('drawing_revision','other'),
                          ('revision',1),('history',['erased']),('carrier_id','other'),('mounted',True),('loaded',True),('supported',False)]:
            with self.subTest(field=key):
                bad=deepcopy(after);bad[key]=value
                with self.assertRaises(C.ContractError):C.custody_transition(before,bad)
    def test_service_request_never_substitutes_completion(self):
        r=dict(stock_id='s',output_parent_stock_id='s',job_id='j',completed_job_id='j',drawing_revision='d',
               output_drawing_revision='d',receipt_role='independent_completion',completed=True,safe_release=True,supported=True,synthetic_only=True)
        self.assertTrue(C.service_handoff(r)['synthetic_handoff_valid'])
        for key,value in [('output_parent_stock_id','other'),('completed_job_id','other'),('output_drawing_revision','other'),
                          ('receipt_role','request'),('completed',False),('safe_release',False),('supported',False)]:
            bad=deepcopy(r);bad[key]=value
            with self.assertRaises(C.ContractError):C.service_handoff(bad)
    def test_fold_plan_requires_every_dependency_ordered_edge(self):
        p=dict(plan_id='p',family_id='PP',drawing_revision='d',edges=['e1','e2'],depends_on={'e1':[],'e2':['e1']},synthetic_only=True)
        rows=[dict(edge_id=e,plan_id='p',drawing_revision='d',actions=['support','engage','bounded_fold','release','inspect'],
                   inspection='accepted_synthetic',receipt_id='receipt-'+e,synthetic_only=True) for e in p['edges']]
        self.assertTrue(C.fold_ledger(p,rows)['fold_ledger_complete'])
        for bad in (rows[:1],list(reversed(rows)),[rows[0],rows[0]]):
            with self.assertRaises(C.ContractError):C.fold_ledger(p,bad)
        for key,value in [('drawing_revision','stale'),('actions',['service_complete']),('inspection','failed'),('receipt_id',rows[0]['receipt_id'])]:
            bad=deepcopy(rows);bad[1][key]=value
            with self.assertRaises(C.ContractError):C.fold_ledger(p,bad)
    def test_independent_device_leases_and_safe_release(self):
        def event(device,lease):
            return dict(action='acquire',device_id=device,lease_id=lease,specimen_id='s',job_id='j',safe_release=False,supported=True,synthetic_only=True)
        front=event('front','lf');side=event('side','ls')
        state=C.lease_transition({},front);state=C.lease_transition(state,side)
        self.assertEqual(set(state),{'front','side'})
        with self.assertRaises(C.ContractError):C.lease_transition(state,front)
        collision=event('third','lf')
        with self.assertRaises(C.ContractError):C.lease_transition(state,collision)
        release=deepcopy(front);release.update(action='release',safe_release=True)
        self.assertEqual(set(C.lease_transition(state,release)),{'side'})
        for key,value in [('lease_id','ls'),('specimen_id','other'),('job_id','other'),('safe_release',False),('supported',False)]:
            bad=deepcopy(release);bad[key]=value
            with self.assertRaises(C.ContractError):C.lease_transition(state,bad)
    def test_capture_pair_rejects_every_stale_calibration_component(self):
        rows,token,cal,current=pair_fixture()
        self.assertTrue(C.capture_pair(rows,token,cal,current)['pair_valid_synthetic'])
        for key in current:
            with self.subTest(component=key):
                stale=deepcopy(current);stale[key]+='-changed'
                with self.assertRaises(C.ContractError):C.capture_pair(rows,token,cal,stale)
    def test_pair_custody_quality_interval_and_source_outcome_rejections(self):
        rows,token,cal,current=pair_fixture()
        for key,value in [('view_role','front'),('specimen_id','other'),('configuration_revision','stale'),
                          ('token_id','other'),('calibration_id','other'),('file_hash',rows[0]['file_hash']),
                          ('capture_id',rows[0]['capture_id']),('camera_id',rows[0]['camera_id']),
                          ('time',21),('time',float('nan')),('quality_ok',False),('evidence_kind','published_observation')]:
            with self.subTest(field=key,value=value):
                bad=deepcopy(rows);bad[1][key]=value
                with self.assertRaises(C.ContractError):C.capture_pair(bad,token,cal,current)
        for key in ('active','all_locks','stable'):
            bad=deepcopy(token);bad[key]=False
            with self.assertRaises(C.ContractError):C.capture_pair(rows,bad,cal,current)
    def test_two_view_lenses_must_not_alias(self):
        rows,token,cal,current=pair_fixture();rows[1]['lens_id']=rows[0]['lens_id']
        with self.assertRaises(C.ContractError):C.capture_pair(rows,token,cal,current)
    def test_scoped_model_and_raw_gates_allow_new_image_custody(self):
        h=C.scope_holds('R25','PP',['new_observation_extraction'],unresolved=['U11','U14'])
        self.assertEqual(h['conflicts'],[])
        self.assertEqual(h['unknowns'],[])
        self.assertIn('C02',C.scope_holds('R25','PP',['model_comparison'],unresolved=[])['conflicts'])
        self.assertIn('C07',C.scope_holds('R25','PP',['source_raw_correspondence'],unresolved=[])['conflicts'])
        self.assertNotIn('C01',C.scope_holds('R04','CS1',['source_matched_geometry'],unresolved=[])['conflicts'])
        self.assertIn('C01',C.scope_holds('R04','PP',['source_matched_geometry'],unresolved=[])['conflicts'])
        self.assertIn('C04',C.scope_holds('R04','CS2',['source_matched_geometry'],unresolved=[])['conflicts'])
        self.assertNotIn('C04',C.scope_holds('R04','CS3',['source_matched_geometry'],unresolved=[])['conflicts'])
    def test_fixture_specific_unmount_and_incomplete_release_reject(self):
        for fixture,op in [('corner','R22'),('rigid','R30')]:
            r=dict(fixture_kind=fixture,fixture_id='synthetic-fixture',specimen_id='synthetic-specimen',operation_id=op,lease_id='lease',load_removed=True,safe_release=True,
                   supported=True,mounts_detached=True,fixture_empty=True,carrier_occupied=True,token_invalidated=True,synthetic_only=True)
            current={k:r[k] for k in ('fixture_kind','fixture_id','specimen_id','lease_id')};current['mounted']=True
            self.assertTrue(C.unmount(r,current)['lease_may_close_synthetic'])
            wrong=deepcopy(r);wrong['operation_id']='R30' if op=='R22' else 'R22'
            with self.assertRaises(C.ContractError):C.unmount(wrong,current)
            for key in ('load_removed','safe_release','supported','mounts_detached','fixture_empty','carrier_occupied','token_invalidated'):
                bad=deepcopy(r);bad[key]=False
                with self.assertRaises(C.ContractError):C.unmount(bad,current)
            for key in ('fixture_kind','fixture_id','specimen_id','lease_id'):
                bad=deepcopy(current);bad[key]='other'
                with self.assertRaises(C.ContractError):C.unmount(r,bad)
            bad=deepcopy(current);bad['mounted']=False
            with self.assertRaises(C.ContractError):C.unmount(r,bad)
    def test_cameras_lenses_and_references_must_bind_current_identities(self):
        rows,token,cal,current=pair_fixture()
        for key in ('camera_id','lens_id'):
            bad=deepcopy(rows);bad[0][key]='unrelated-device'
            with self.assertRaises(C.ContractError):C.capture_pair(bad,token,cal,current)
        bad=deepcopy(cal);bad['reference_ids']=['other-ref1','other-ref2']
        with self.assertRaises(C.ContractError):C.capture_pair(rows,token,bad,current)
        for side,front in [('side_camera','front_camera'),('side_lens','front_lens'),('scale_reference','height_reference')]:
            bad_current=deepcopy(current);bad_current[side]=bad_current[front]
            bad_cal=deepcopy(cal);bad_cal['revisions']=deepcopy(bad_current)
            with self.assertRaises(C.ContractError):C.capture_pair(rows,token,bad_cal,bad_current)
    def test_held_closeout_never_claims_unload_or_storage(self):
        r=dict(disposition='supported_hold',loaded=True,mounted=True,open_leases=['live'],supported=True,
               transported_to_storage=False,station_inventory_complete=False,evidence_archive_complete=True,
               selected_route_status={'PP_RIGID':'held'},synthetic_only=True)
        out=C.closeout(r);self.assertTrue(out['accounted_for']);self.assertFalse(out['fully_closed_synthetic']);self.assertFalse(out['physical_complete'])
        for key,value in [('disposition','closed_synthetic'),('transported_to_storage',True),('supported',False),('evidence_archive_complete',False)]:
            bad=deepcopy(r);bad[key]=value
            with self.assertRaises(C.ContractError):C.closeout(bad)
    def test_observables_are_not_curve_agreement_or_source_values(self):
        r=dict(pair_id='synthetic-pair',raw_hashes=['1'*64,'2'*64],height=.18,
               interior_radius=.061,exterior_radius=.093,
               uncertainties={'height':.001,'interior_radius':.002,'exterior_radius':.003},
               units='m',method_id='synthetic-method',kind='synthetic_observation',synthetic_only=True)
        out=C.observables(r)
        self.assertTrue(out['observables_separated'])
        self.assertFalse(out['curve_agreement_tested'])
        self.assertFalse(out['scientific_reproduction'])
        for key,value in [('kind','published_observations'),('kind','model_prediction'),('units','cm'),
                          ('raw_hashes',['1'*64,'1'*64]),('height',True),('height',float('inf')),
                          ('interior_radius',.1),('method_id','')]:
            bad=deepcopy(r);bad[key]=value
            with self.assertRaises(C.ContractError):C.observables(bad)
        bad=deepcopy(r);bad['coarse_grained_radius_prediction']=.093
        with self.assertRaises(C.ContractError):C.observables(bad)
    def test_repeat_ledger_preserves_specimen_parentage_and_no_independence_claim(self):
        rows=[dict(series_id='series',specimen_id='specimen',stock_id='stock',configuration_id='H%02d'%i,
                   attempt_id='attempt1',pair_id='pair%d'%i,kind='source_aligned_slot',synthetic_only=True) for i in range(1,9)]
        out=C.repeat_ledger(rows)
        self.assertEqual((out['distinct_specimens'],out['configuration_slots'],out['accepted_pairs']),(1,8,8))
        self.assertFalse(out['statistical_independence_established'])
        self.assertFalse(out['source_repeats_established'])
        for key,value in [('specimen_id','replacement'),('stock_id','other'),('pair_id','pair1')]:
            bad=deepcopy(rows);bad[-1][key]=value
            with self.assertRaises(C.ContractError):C.repeat_ledger(bad)
    def test_retry_keeps_rejections_and_replacement_starts_new_series(self):
        before=dict(attempt_id='a1',specimen_id='s1',series_id='series1',token_id='t1',capture_ids=['c1','c2'],
                    raw_hashes=['1'*64,'2'*64],previous_failure_id='failure1',synthetic_only=True)
        after=deepcopy(before);after.update(attempt_id='a2',token_id='t2',capture_ids=['c3','c4'],raw_hashes=['3'*64,'4'*64])
        self.assertTrue(C.retry(before,after)['failure_preserved'])
        for key,value in [('attempt_id','a1'),('token_id','t1'),('capture_ids',['c1','c4']),('raw_hashes',['1'*64,'4'*64]),
                          ('previous_failure_id','other'),('specimen_id','replacement')]:
            bad=deepcopy(after);bad[key]=value
            with self.assertRaises(C.ContractError):C.retry(before,bad)
        replacement=deepcopy(after);replacement.update(specimen_id='s2',series_id='series2')
        self.assertTrue(C.retry(before,replacement)['failure_preserved'])

class IndependentSceneBinding(unittest.TestCase):
    def test_sibling_nominal_contract_matches(self):
        scene=ROOT.parent/'arcmorph_scene_assets_v1'
        contract=scene/'operation_binding_contract.json'
        if not contract.is_file():self.skipTest('Separately distributed scene contract unavailable')
        s=json.loads(contract.read_text());task=read('asset_binding_plan.json')
        self.assertEqual(s['units'],'m')
        self.assertEqual(s['roots'],{f'A{i:02}':f'ASSET.A{i:02}' for i in range(1,13)})
        index={r['operation_id']:r for r in s['operations']}
        self.assertEqual(set(index),set(C.OPS))
        for b in task['operation_bindings']:
            with self.subTest(operation=b['operation_id']):
                other=index[b['operation_id']]
                self.assertEqual(set(b['asset_ids']),set(other['asset_ids']))
                self.assertEqual(set(b['anchor_ids']),{other['primary_anchor'],other['control_anchor']})
                self.assertFalse(other['physical_execution_enabled'])
                self.assertIsNone(other['qualified_pose'])
        metadata=json.loads((scene/'asset_metadata.json').read_text())
        self.assertEqual(metadata['task_id'],read('agent_visible.json')['task_id'])
        self.assertFalse(metadata['physical_execution_enabled'])
        self.assertFalse(metadata['physical_geometry_validated'])
        self.assertEqual(task['family_aliases'],{'PP1':'PP'})
        self.assertEqual({task['family_aliases'].get(k,k) for k in metadata['physical_families']},
                         {'CS1','CS2','CS3','CS4','PP'})
    def test_all_contextual_release_selectors_match_the_sibling(self):
        scene=ROOT.parent/'arcmorph_scene_assets_v1'
        if not (scene/'affordances.json').is_file():self.skipTest('Separately distributed affordances unavailable')
        anchors={r['anchor_id']:r for r in json.loads((scene/'affordances.json').read_text())['anchors']}
        rows=read('asset_binding_plan.json')['contextual_anchor_bindings']
        expected={('R19','rigid_metrology','ANCHOR.R19.primary'),
                  ('R19','corner_load','ANCHOR.R19.corner_release'),
                  ('R19','rigid_demo','ANCHOR.R19.rigid_demo_release'),
                  ('R22','corner_load','ANCHOR.R22.corner_unmount'),
                  ('R30','rigid_metrology','ANCHOR.R30.primary'),
                  ('R30','rigid_demo','ANCHOR.R30.rigid_demo_unmount')}
        self.assertEqual({(r['operation_id'],r['actual_fixture_class'],r['anchor_id']) for r in rows},expected)
        self.assertEqual(len(rows),6)
        targets={'corner_load':'qual.corner.base','rigid_demo':'qual.rigid_demo_support'}
        for r in rows:
            a=anchors[r['anchor_id']]
            self.assertEqual(a['target_object'],('rig.sample_slider.0' if r['operation_id']=='R19' else 'rig.mount.0') if r['actual_fixture_class']=='rigid_metrology' else targets[r['actual_fixture_class']])
            self.assertEqual(a['asset_id'],'A07' if r['actual_fixture_class']=='rigid_metrology' else 'A11')
            self.assertFalse(a['physical_execution_enabled'])
            self.assertIsNone(a['qualified_pose'])

    def scene_file(self,name):
        path=ROOT.parent/'arcmorph_scene_assets_v1'/name
        if not path.is_file():self.skipTest('Separately distributed scene file unavailable: '+name)
        return path
    def scene_json(self,name):
        return json.loads(self.scene_file(name).read_text())
    def scene_guards(self):
        spec=importlib.util.spec_from_file_location('independent_scene_guards',self.scene_file('semantic_controls.py'))
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
        return module
    def test_concrete_targets_match_operation_scope_and_task_mapping(self):
        bindings={r['operation_id']:r for r in self.scene_json('operation_bindings.json')['operations']}
        contracts={r['operation_id']:r for r in self.scene_json('operation_binding_contract.json')['operations']}
        task={r['operation_id']:r for r in read('asset_binding_plan.json')['operation_bindings']}
        self.assertEqual(set(bindings),set(C.OPS))
        expected={
            'R06':('fab.load_dock','fab.job_token_slot'),
            'R10':('rig.mount.0','rig.M2_reference_bolt.0'),
            'R13':('rig.L_plate_upright.0','rig.plate_control.0'),
            'R14':('rig.sample_slider.0','rig.sample_lock.0'),
            'R19':('rig.sample_slider.0','rig.sample_lock.0'),
            'R22':('qual.corner.base','qual.control.screen'),
            'R26':('qual.rigid_demo_support','qual.rigid.support_handle-0.25'),
            'R27':('qual.rigid_demo_support','qual.rigid.support_handle-0.25'),
            'R30':('rig.mount.0','rig.M2_reference_bolt.0')}
        for op,b in bindings.items():
            with self.subTest(operation=op):
                for key,value in contracts[op].items():self.assertEqual(b[key],value)
                self.assertEqual(task[op]['primary_target'],b['primary_target'])
                self.assertEqual(task[op]['control_target'],b['control_target'])
        for op,targets in expected.items():
            self.assertEqual((bindings[op]['primary_target'],bindings[op]['control_target']),targets)
        self.assertEqual(bindings['R06']['primary_asset_id'],'A04')
        self.assertNotEqual(bindings['R26']['primary_target'],bindings['R22']['primary_target'])
    def test_anchor_targets_ownership_and_inventory_coordinates_agree(self):
        inventory=self.scene_json('asset_inventory.json')
        rows=[(a['asset_id'],p) for a in inventory['assets'] for p in a['parts']]
        parts={p['scene_object']:(owner,p) for owner,p in rows}
        self.assertEqual(len(parts),len(rows))
        anchors=self.scene_json('affordances.json')['anchors']
        self.assertEqual(len(anchors),66)
        by_id={a['anchor_id']:a for a in anchors}
        for a in anchors:
            with self.subTest(anchor=a['anchor_id']):
                target_owner,target=parts[a['target_object']]
                anchor_owner,anchor=parts[a['scene_object']]
                self.assertEqual(target_owner,a['asset_id']);self.assertEqual(anchor_owner,a['asset_id'])
                for n in range(3):
                    self.assertAlmostEqual(a['translation_m'][n],target['translation_m'][n],places=5)
                    self.assertAlmostEqual(a['translation_m'][n],anchor['translation_m'][n],places=5)
                self.assertFalse(a['physical_execution_enabled']);self.assertIsNone(a['qualified_pose'])
        for b in self.scene_json('operation_bindings.json')['operations']:
            self.assertEqual(by_id[b['primary_anchor']]['target_object'],b['primary_target'])
            self.assertEqual(by_id[b['control_anchor']]['target_object'],b['control_target'])
    def test_dimension_inputs_are_distinct_from_measured_static_extents(self):
        metadata=self.scene_json('asset_metadata.json');variants=self.scene_json('variants.json')['variants']
        topology=self.scene_json('specimen_topology.json')
        self.assertIn('nominal generator inputs',metadata['dimension_semantics'])
        self.assertIn('not fabrication dimensions',metadata['dimension_semantics'])
        inputs=metadata['authored_template_generation_parameters_mm']
        self.assertFalse(topology['source_geometry_used']);self.assertFalse(topology['physical_folding_validated'])
        self.assertEqual(len(topology['static_variants']),20)
        for v in variants:
            self.assertEqual(v['dimensions_mm'],inputs[v['family_id']])
            self.assertFalse(v['qualified_state_available']);self.assertFalse(v['state_change_is_physical_folding'])
        for v in topology['static_variants']:
            self.assertFalse(v['qualified']);self.assertTrue(v['illustration_not_physical_fold'])
            self.assertEqual(v['nominal_generation_span_m'],[x/1000 for x in inputs[v['family_id']][:2]])
            bounds=v['panel_surface_bounds_m'];extent=v['panel_surface_extent_m']
            for n in range(3):self.assertAlmostEqual(extent[n],bounds['max'][n]-bounds['min'][n],places=7)
            for edge in v['creases']:
                for key in ('mountain_valley','fold_order','fold_motion_limit'):self.assertIsNone(edge[key])
        hold=metadata['dimensional_hold'];self.assertEqual(hold['conflict_id'],'C01')
        self.assertIsNone(hold['resolution']);self.assertFalse(hold['fabrication_from_source_dimensions_allowed'])
    def test_scene_state_registry_matches_current_bindings_and_guard_scope(self):
        states=self.scene_json('states.json')
        bindings={b['operation_id']:b for b in self.scene_json('operation_binding_contract.json')['operations']}
        operations={r['id']:r for r in states['operations']}
        self.assertEqual(set(operations),set(C.OPS))
        for op,row in operations.items():
            self.assertEqual(row['asset_ids'],bindings[op]['asset_ids'])
            self.assertEqual(row['primary_anchor'],bindings[op]['primary_anchor'])
            self.assertEqual(row['control_anchor'],bindings[op]['control_anchor'])
            self.assertFalse(row['physical_execution'])
        self.assertEqual(operations['R26']['semantic_api'],['mount_candidate'])
        self.assertEqual(operations['R27']['semantic_api'],[])
        self.assertEqual(operations['R27']['implementation_status'],'metadata_only_not_implemented')
        self.assertEqual(operations['R19']['semantic_api'],['remove_load_candidate'])
        for op in ('R22','R30'):self.assertEqual(operations[op]['semantic_api'],['release_mount_candidate'])
        for key,value in states['initial_defaults'].items():
            if key!='note':self.assertIsNone(value)
        self.assertTrue(states['claims']['semantic_tests_only'])
        for key,value in states['claims'].items():
            if key!='semantic_tests_only':self.assertFalse(value)
    def test_scene_release_guards_preserve_actual_fixture_lease_and_unload_order(self):
        G=self.scene_guards()
        for kind,route,op in [('rigid_metrology','PP_RIGID','R30'),('rigid_demo','CS1','R30'),('corner','PP_SHEAR','R22')]:
            base=G.initial_state(specimen_id='EXAMPLE-specimen',stock_id='EXAMPLE-stock',material_batch='EXAMPLE-lot',route_id=route,carrier_id='EXAMPLE-carrier')
            base=replace(base,phase='folded',baseline_evidence_id='EXAMPLE-baseline')
            mount=G.Mount('EXAMPLE-fixture','EXAMPLE-rev1',kind,'EXAMPLE-lease',('EXAMPLE-a1','EXAMPLE-a2'),job_id='EXAMPLE-job',job_status='complete')
            mounted=G.mount_candidate(base,mount,evidence_id='EXAMPLE-mounted',interface_qualified=True)
            self.assertEqual(mounted.history[-1].operation_id,{'rigid_metrology':'R10','rigid_demo':'R26','corner':'R20'}[kind])
            loaded=replace(mounted,load_state='present',active_capture_token_id='EXAMPLE-token')
            evidence=G.ReleaseEvidence('EXAMPLE-release',base.specimen_id,mount.fixture_revision,mount.lease_id,base.carrier_id,mount.attachment_ids,True,True,'EXAMPLE-method',True)
            with self.assertRaises(G.SemanticHold):G.release_mount_candidate(loaded,op,evidence)
            with self.assertRaises(G.SemanticHold):G.transport_candidate(loaded,source=loaded.station,destination='storage',carrier_id=base.carrier_id,custody_receipt_id='EXAMPLE-transport')
            arguments=dict(evidence_id='EXAMPLE-unloaded',fixture_revision=mount.fixture_revision,removal_confirmed=True,method_id='EXAMPLE-method',support_confirmed=True,safe_to_open=True)
            for key,value in [('fixture_revision','stale'),('removal_confirmed',False),('support_confirmed',False),('safe_to_open',False)]:
                bad=dict(arguments);bad[key]=value
                with self.assertRaises(G.SemanticHold):G.remove_load_candidate(loaded,**bad)
            unloaded=G.remove_load_candidate(loaded,**arguments)
            self.assertIsNone(unloaded.active_capture_token_id)
            with self.assertRaises(G.SemanticHold):G.release_mount_candidate(unloaded,'R30' if op=='R22' else 'R22',evidence)
            for key,value in [('specimen_id','other'),('fixture_revision','stale'),('lease_id','stale'),('carrier_id','other'),('detached_attachment_ids',('EXAMPLE-a1',)),('fixture_empty',False),('supported',False)]:
                with self.assertRaises(G.SemanticHold):G.release_mount_candidate(unloaded,op,replace(evidence,**{key:value}))
            if kind=='corner':
                with self.assertRaises(G.SemanticHold):G.release_mount_candidate(unloaded,op,replace(evidence,hardware_accounted=False))
                with self.assertRaises(G.SemanticHold):G.release_mount_candidate(replace(unloaded,mount=replace(mount,job_status='running')),op,evidence)
            released=G.release_mount_candidate(unloaded,op,evidence)
            self.assertIsNone(released.mount);self.assertTrue(released.carrier_retained)
            self.assertTrue(G.check_append_only(unloaded,released))
            with self.assertRaises(G.SemanticHold):G.release_mount_candidate(released,op,evidence)
    def test_scene_r13_cannot_substitute_for_cardstock_or_corner_operations(self):
        G=self.scene_guards()
        for kind,route in [('rigid_metrology','PP_RIGID'),('rigid_demo','CS1'),('corner','PP_SHEAR')]:
            base=G.initial_state(specimen_id='EXAMPLE-s',stock_id='EXAMPLE-stock',material_batch='EXAMPLE-lot',route_id=route,carrier_id='EXAMPLE-carrier')
            mount=G.Mount('EXAMPLE-fixture','EXAMPLE-rev1',kind,'EXAMPLE-lease',('EXAMPLE-a1',))
            current=replace(base,phase='folded',baseline_evidence_id='EXAMPLE-baseline',mount=mount,load_removal_evidence_id='EXAMPLE-removal')
            if kind=='rigid_metrology':
                out=G.configuration_candidate(current,configuration_revision='EXAMPLE-cfg1',evidence_id='EXAMPLE-config')
                self.assertEqual(out.history[-1].operation_id,'R13')
            else:
                with self.assertRaises(G.SemanticHold):G.configuration_candidate(current,configuration_revision='EXAMPLE-cfg1',evidence_id='EXAMPLE-config')
    def test_paired_review_receipt_pins_current_semantic_files(self):
        receipt=read('review/INDEPENDENT_REVIEW.json')['observed_sibling_contract_hashes']
        expected={'operation_binding_contract.json','operation_bindings.json','asset_metadata.json','affordances.json',
                  'variants.json','asset_inventory.json','specimen_topology.json','semantic_controls.py','states.json'}
        self.assertEqual(set(receipt),expected)
        for name,value in receipt.items():self.assertEqual(hashlib.sha256(self.scene_file(name).read_bytes()).hexdigest(),value)

if __name__=='__main__':unittest.main()

