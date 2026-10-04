"""Independent finite synthetic contract tests; no physical or scientific validation."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('independently_loaded_contract', ROOT / 'tests' / 'contract.py')
C = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(C)


def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def policy():
    return dict(policy_id='independent:policy', frozen_at=2, specimen_count=1,
                run_count=2, day_count=1, order_digest='independent:order',
                metrics_digest='independent:metrics', uncertainty_digest='independent:uncertainty',
                stopping_digest='independent:stop', budget_digest='independent:budget',
                role='independent_policy', synthetic_only=True)


def configuration(mode='photon', epoch='independent:epoch'):
    return dict(epoch_id=epoch, detector_mode=mode, controller_revision='independent:controller',
                source_revision='independent:source', configuration_id='independent:configuration',
                synthetic_only=True)


def readiness_record(mode='photon', branches=None):
    r = configuration(mode)
    r.update(receipt_id='independent:readiness', valid_interval=[3, 9],
             allowed_branches=branches or ['B04', 'B06', 'B07', 'B08'],
             role='independent_readiness', interlocked=True,
             calibration_digest='independent:calibration', uncertainty_digest='independent:uncertainty')
    return r


def ledger(mode='photon', encoding='hadamard'):
    expected, rows = [], []
    for i in range(4):
        e = dict(display_id='independent:display:'+str(i), pattern_digest='independent:pattern:'+str(i),
                 coefficient_id='independent:coefficient:'+str(i//2), sign=1 if i%2 == 0 else -1)
        expected.append(e)
        r = dict(e)
        r.update(raw_id='independent:raw:'+str(i), run_id='independent:run', sample_id='independent:sample',
                 epoch_id='independent:epoch', detector_mode=mode, dmd_index=i, controller_index=i,
                 detector_index=i, time=10+i, exposure=0.03, value=i,
                 unit='count' if mode == 'photon' else 'ADC_unit', overload=False, missing=False,
                 evidence_kind='synthetic_observation', synthetic_only=True)
        rows.append(r)
    m = dict(run_id='independent:run', sample_id='independent:sample', epoch_id='independent:epoch',
             detector_mode=mode, encoding=encoding, matrix_digest='independent:matrix',
             normalization_id='independent:normalization', physical_display_convention='complementary_pairs',
             expected_displays=expected, declared_coefficients=2, synthetic_only=True)
    return m, rows


def closeout(hold=False):
    return dict(disposition='supported_hold' if hold else 'closed_synthetic',
                branch_status={b:'blocked' for b in C.BRANCHES},
                active_leases=['independent:lease'] if hold else [], dock_occupied=hold,
                safe_access_observed=not hold, all_samples_accounted=True,
                custody='observed_supported_hold' if hold else 'storage_or_quarantine',
                archive_complete=True, failed_records_retained=True,
                robot_outside_enclosure=True, synthetic_only=True)


class IndependentStaticTests(unittest.TestCase):
    def test_exact_operation_branch_station_asset_and_gap_ids(self):
        self.assertEqual(set(C.OPS), {'R%02d'%i for i in range(1,23)})
        self.assertEqual(set(C.BRANCHES), {'B%02d'%i for i in range(1,9)})
        self.assertEqual({s['id'] for s in read('station_contracts.json')['stations']}, {'S%02d'%i for i in range(1,6)})
        self.assertEqual({a for o in C.OPS.values() for a in o['asset_ids']}, {'A%02d'%i for i in range(1,14)})
        gaps = read('unknown_parameters.json')['unknowns']
        self.assertEqual({g['id'] for g in gaps}, {'U%02d'%i for i in range(1,15)})
        self.assertTrue(all(g['resolved'] is False and g['physical_default'] is None for g in gaps))

    def test_operation_graph_is_acyclic_and_all_edges_exist(self):
        visited, active = set(), set()
        def visit(k):
            self.assertNotIn(k, active)
            if k in visited:
                return
            active.add(k)
            for dep in C.OPS[k]['depends_on']:
                self.assertIn(dep, C.OPS)
                visit(dep)
            active.remove(k)
            visited.add(k)
        for k in C.OPS:
            visit(k)
        self.assertIn('R10', C.OPS['R11']['depends_on'])

    def test_source_and_authored_classes_are_separate(self):
        self.assertTrue(all(o['classification']=='authored_robot_translation' for o in C.OPS.values()))
        self.assertTrue(all(o['physical_execution_qualified'] is False and o['runtime']=='unimplemented' for o in C.OPS.values()))
        facts={f['id']:f for f in read('source_parameters.json')['facts']}
        self.assertEqual(len(facts),22)
        for o in C.OPS.values():
            self.assertLessEqual(set(o['source_anchors']),set(facts))
        self.assertTrue(read('evidence_map.json')['source_outcomes_are_never_observations'])
        self.assertEqual(read('RELEASE_BOUNDARY.json')['validated_runnable_whole_paper_tasks'],0)

    def test_dynamic_rate_is_analog_and_grid_specific(self):
        b=C.BRANCHES['B03']
        self.assertEqual(b['detector_mode'],'analog')
        self.assertEqual({tuple(x['grid']):x['source_rate_reference_Hz_approx'] for x in b['condition_slots']}, {(16,16):10,(32,32):2.5})
        self.assertFalse(b['rate_is_target_or_default'])
        self.assertFalse(b['movie_playback_is_acquisition_time'])
        for key in ('B04','B06','B07','B08'):
            self.assertEqual(C.BRANCHES[key]['detector_mode'],'photon')
            self.assertFalse(any('source_rate_reference_Hz_approx' in x for x in C.BRANCHES[key]['condition_slots']))

    def test_condition_matrices_and_unresolved_source_fields(self):
        self.assertEqual([len(C.BRANCHES[b]['condition_slots']) for b in sorted(C.BRANCHES)], [4,8,2,10,9,15,4,3])
        self.assertIsNone(C.BRANCHES['B05']['detector_mode'])
        self.assertTrue(all(x['exposure_policy'] is None for x in C.BRANCHES['B05']['condition_slots']))
        self.assertIsNone(C.BRANCHES['B07']['physical_display_convention'])
        self.assertTrue(all(x['grid_policy'] is None for x in C.BRANCHES['B08']['condition_slots']))
        self.assertFalse(C.BRANCHES['B05']['same_power_is_equal_dose'])
        self.assertFalse(read('branches.json')['condition_slots_are_independent_repeats'])

    def test_preparation_and_transfers_do_not_skip_lineage(self):
        p=read('preparation_routes.json')
        self.assertEqual({x['id'] for x in p['materials']},{'M01','M02'})
        self.assertLessEqual({'stock_lot_id','approved_drawing_revision','fabrication_job_id','sample_id','carrier_id','reference_image_id','independent_inspection_receipt_id','safe_release_receipt_id'},set(p['required_chain']))
        self.assertIsNone(p['service_internal_instructions'])
        t=read('transport_routes.json')['transfers']
        self.assertEqual(len(t),6)
        self.assertTrue(all(x['mounted_or_acquiring_transfer_forbidden'] for x in t))
        self.assertEqual({(x['source_station'],x['destination_station']) for x in t if x['operation_id']=='R17'}, {('S03','S01'),('S01','S03')})

    def test_all_operations_have_failure_edges(self):
        edges=read('lifecycle_contract.json')['failure_edges']
        self.assertEqual({x['operation_id'] for x in edges},set(C.OPS))
        self.assertTrue(all(x['requires_scientific_success'] is False for x in edges))

    def test_actor_context_cannot_supply_truth(self):
        a=read('agent_visible.json')
        self.assertEqual(set(a['permitted_actor_message_fields']),{'event_id','operation_id','evidence_id'})
        self.assertFalse(read('evaluator_reference.json')['isolation_implemented'])
        self.assertEqual(read('evaluator_reference.json')['actor_visible_allowlist'],['agent_visible.json'])


class IndependentGuardTests(unittest.TestCase):
    def reject(self, func, *args):
        with self.assertRaises(C.ContractError):
            func(*args)

    def test_policy_requires_prospective_freeze(self):
        p=policy()
        self.assertTrue(C.campaign_policy(p,3)['prospective_policy_valid_synthetic'])
        self.reject(C.campaign_policy,p,2)
        self.reject(C.campaign_policy,p,1)

    def test_policy_rejects_missing_counts_false_authority_and_nonfinite_values(self):
        for key,value in [('run_count',0),('specimen_count',None),('day_count',True),('frozen_at',float('nan')),('role','actor')]:
            with self.subTest(key=key):
                p=policy();p[key]=value;self.reject(C.campaign_policy,p,3)

    def test_preparation_rejects_request_only_and_wrong_lineage(self):
        p=dict(stock_lot_id='lot',output_stock_lot_id='lot',drawing_revision='drawing',output_drawing_revision='drawing',job_id='job',completed_job_id='job',sample_id='sample',carrier_id='carrier',reference_id='reference',completed=True,inspected=True,safe_release=True,role='independent_fabrication',synthetic_only=True)
        self.assertTrue(C.preparation(p)['prepared_lineage_valid_synthetic'])
        for k,v in [('completed',False),('inspected',False),('safe_release',False),('completed_job_id','wrong'),('output_stock_lot_id','wrong'),('output_drawing_revision','wrong'),('role','service_request')]:
            with self.subTest(key=k):
                r=copy.deepcopy(p);r[k]=v;self.reject(C.preparation,r)

    def test_custody_rejects_teleportation_and_unsafe_transfer(self):
        before=dict(sample_id='sample',carrier_id='carrier',stock_lot_id='lot',drawing_revision='drawing',station_id='S01',slot_id='rack',revision=2,history=['prior'],mounted=False,acquiring=False,supported=True,synthetic_only=True)
        after=copy.deepcopy(before);after.update(station_id='S03',slot_id='dock',revision=3,history=['prior','transfer'])
        receipt=dict(sample_id='sample',carrier_id='carrier',from_station='S01',from_slot='rack',to_station='S03',to_slot='dock',source_occupant='carrier',destination_empty=True,safe_release=True,retention=True,transform_revision='transform',role='independent_custody',synthetic_only=True)
        self.assertTrue(C.custody_transfer(before,after,receipt)['custody_valid_synthetic'])
        for target,key,value in [('before','mounted',True),('before','acquiring',True),('after','carrier_id','replacement'),('after','history',['transfer']),('receipt','source_occupant','other'),('receipt','destination_empty',False),('receipt','safe_release',False),('receipt','retention',False),('receipt','from_station','S02')]:
            with self.subTest(target=target,key=key):
                b,a,r=map(copy.deepcopy,(before,after,receipt));{'before':b,'after':a,'receipt':r}[target][key]=value;self.reject(C.custody_transfer,b,a,r)

    def test_readiness_requires_current_epoch_branch_mode_and_interval(self):
        r=readiness_record();current=configuration()
        self.assertTrue(C.readiness(r,current,'B06',5)['ready_synthetic'])
        for k,v in [('epoch_id','stale'),('controller_revision','stale'),('configuration_id','stale'),('detector_mode','analog'),('source_revision','stale'),('interlocked',False),('allowed_branches',['B04'])]:
            with self.subTest(key=k):
                bad=copy.deepcopy(r);bad[k]=v;self.reject(C.readiness,bad,current,'B06',5)
        self.reject(C.readiness,r,current,'B06',10)
        self.reject(C.readiness,readiness_record('analog',['B06']),configuration('analog'),'B06',5)

    def test_b05_does_not_inherit_unresolved_detector_and_exposure(self):
        for mode in ('photon','analog','spatial_diagnostic'):
            with self.subTest(mode=mode):
                self.reject(C.readiness,readiness_record(mode,['B05']),configuration(mode),'B05',5)

    def test_b05_explicit_policy_is_bound_and_does_not_claim_source_equivalence(self):
        r=readiness_record('analog',['B05']);current=configuration('analog')
        p=dict(branch_id='B05',epoch_id=current['epoch_id'],readiness_id=r['receipt_id'],
               detector_mode='analog',exposure_policy_digest='independent:exposure',
               budget_policy_digest='independent:budget',provenance='approved_authored_departure',
               role='independent_branch_policy',synthetic_only=True)
        out=C.readiness(r,current,'B05',5,p)
        self.assertTrue(out['ready_synthetic'])
        self.assertFalse(out['source_equivalence_established'])
        self.assertFalse(out['physical_qualified'])
        for k,v in [('epoch_id','old'),('readiness_id','other'),('detector_mode','photon'),
                    ('exposure_policy_digest',''),('budget_policy_digest',''),('provenance','assumed'),
                    ('role','actor'),('branch_id','B04')]:
            with self.subTest(key=k):
                bad=copy.deepcopy(p);bad[k]=v;self.reject(C.readiness,r,current,'B05',5,bad)

    def test_b05_even_explicit_policy_cannot_use_spatial_diagnostic_mode(self):
        r=readiness_record('spatial_diagnostic',['B05']);current=configuration('spatial_diagnostic')
        p=dict(branch_id='B05',epoch_id=current['epoch_id'],readiness_id=r['receipt_id'],
               detector_mode='spatial_diagnostic',exposure_policy_digest='independent:exposure',
               budget_policy_digest='independent:budget',provenance='qualified_source_specific_evidence',
               role='independent_branch_policy',synthetic_only=True)
        self.reject(C.readiness,r,current,'B05',5,p)

    def test_configuration_change_invalidates_readiness(self):
        old=configuration('analog','epoch-old');new=configuration('photon','epoch-new');new['configuration_id']='config-new'
        r=dict(old_epoch='epoch-old',new_epoch='epoch-new',safe_idle=True,active_acquisition_lease=False,readiness_invalidated=True,role='independent_configuration_change',synthetic_only=True)
        self.assertTrue(C.configuration_change(old,new,r)['fresh_readiness_required'])
        for k,v in [('safe_idle',False),('active_acquisition_lease',True),('readiness_invalidated',False),('old_epoch','wrong')]:
            bad=copy.deepcopy(r);bad[k]=v;self.reject(C.configuration_change,old,new,bad)
        bad=copy.deepcopy(new);bad['epoch_id']='epoch-old';r['new_epoch']='epoch-old';self.reject(C.configuration_change,old,bad,r)

    def test_exclusive_lease_and_independent_safe_release(self):
        e=dict(action='acquire',station_id='S03',lease_id='lease',run_id='run',purpose='acquisition',safe_release=False,role='independent_lease',synthetic_only=True)
        state=C.lease_transition({},e)
        self.reject(C.lease_transition,state,e)
        release=copy.deepcopy(e);release['action']='release';self.reject(C.lease_transition,state,release)
        release['safe_release']=True;self.assertEqual(C.lease_transition(state,release),{})
        release['run_id']='other';self.reject(C.lease_transition,state,release)

    def test_valid_ledger_counts_physical_displays_separately(self):
        for mode in ('analog','photon'):
            m,r=ledger(mode);out=C.pattern_ledger(m,r,'independent:epoch')
            self.assertEqual((out['physical_displays'],out['signed_coefficients'],out['independent_runs']),(4,2,1))
            self.assertFalse(out['dose_equivalence_established'])

    def test_acquisition_bundle_binds_sample_mode_run_and_lease_purpose(self):
        m,rows=ledger();current=configuration();receipt=readiness_record()
        receipt['valid_interval']=[3,19]
        lease=dict(lease_id='independent:lease',run_id=m['run_id'],purpose='acquisition')
        self.assertTrue(C.acquisition_bundle('B04',m,rows,current,receipt,lease,m['sample_id'],5)['bundle_valid_synthetic'])
        self.reject(C.acquisition_bundle,'B04',m,rows,current,receipt,lease,'wrong-sample',5)
        for key,value in [('run_id','other-run'),('purpose','motion')]:
            bad=copy.deepcopy(lease);bad[key]=value
            self.reject(C.acquisition_bundle,'B04',m,rows,current,receipt,bad,m['sample_id'],5)
        analog,analog_rows=ledger('analog')
        self.reject(C.acquisition_bundle,'B04',analog,analog_rows,current,receipt,lease,m['sample_id'],5)

    def test_acquisition_bundle_rejects_events_outside_readiness_interval(self):
        m,rows=ledger();current=configuration();receipt=readiness_record()
        lease=dict(lease_id='independent:lease',run_id=m['run_id'],purpose='acquisition')
        self.reject(C.acquisition_bundle,'B04',m,rows,current,receipt,lease,m['sample_id'],5)
        receipt['valid_interval']=[3,13]
        self.reject(C.acquisition_bundle,'B04',m,rows,current,receipt,lease,m['sample_id'],5)

    def test_acquisition_bundle_rejects_wrong_compressed_encoding(self):
        m,rows=ledger();current=configuration();receipt=readiness_record();receipt['valid_interval']=[3,19]
        lease=dict(lease_id='independent:lease',run_id=m['run_id'],purpose='acquisition')
        self.reject(C.acquisition_bundle,'B07',m,rows,current,receipt,lease,m['sample_id'],5)
        m['encoding']='random'
        self.assertTrue(C.acquisition_bundle('B07',m,rows,current,receipt,lease,m['sample_id'],5)['bundle_valid_synthetic'])

    def test_dynamic_bundle_requires_motion_lease_and_mapping_cannot_use_bucket_ledger(self):
        m,rows=ledger('analog');current=configuration('analog');receipt=readiness_record('analog',['B02','B03']);receipt['valid_interval']=[3,19]
        lease=dict(lease_id='independent:lease',run_id=m['run_id'],purpose='motion')
        self.assertTrue(C.acquisition_bundle('B03',m,rows,current,receipt,lease,m['sample_id'],5)['bundle_valid_synthetic'])
        lease['purpose']='acquisition'
        self.reject(C.acquisition_bundle,'B03',m,rows,current,receipt,lease,m['sample_id'],5)
        self.reject(C.acquisition_bundle,'B01',m,rows,current,receipt,lease,m['sample_id'],5)

    def test_ledger_rejects_cross_device_mismatch_missing_duplicate_and_reorder(self):
        for k,v in [('dmd_index',3),('controller_index',3),('detector_index',3),('raw_id','independent:raw:1'),('display_id','wrong'),('sample_id','wrong'),('epoch_id','stale'),('pattern_digest','wrong'),('overload',True),('missing',True),('time',11),('exposure',0),('value',-1),('unit','ADC_unit')]:
            with self.subTest(key=k):
                m,r=ledger();r[0][k]=v;self.reject(C.pattern_ledger,m,r,'independent:epoch')
        m,r=ledger();self.reject(C.pattern_ledger,m,r[:-1],'independent:epoch')
        self.reject(C.pattern_ledger,m,list(reversed(r)),'independent:epoch')
        self.reject(C.pattern_ledger,m,r,'stale')

    def test_complements_must_be_adjacent_signed_and_distinct(self):
        for alteration in ('signs','coefficient','same_pattern','count','unresolved_convention'):
            with self.subTest(alteration=alteration):
                m,r=ledger()
                if alteration=='signs':m['expected_displays'][1]['sign']=r[1]['sign']=1
                elif alteration=='coefficient':m['expected_displays'][1]['coefficient_id']=r[1]['coefficient_id']='other'
                elif alteration=='same_pattern':m['expected_displays'][1]['pattern_digest']=r[1]['pattern_digest']=r[0]['pattern_digest']
                elif alteration=='count':m['declared_coefficients']=4
                else:m['encoding']='random';m['physical_display_convention']=None
                self.reject(C.pattern_ledger,m,r,'independent:epoch')

    def test_ledger_rejects_nonnumeric_nonfinite_and_extra_fields(self):
        for value in (True,float('nan'),float('inf'),'1',None):
            m,r=ledger('analog');r[0]['value']=value;self.reject(C.pattern_ledger,m,r,'independent:epoch')
        m,r=ledger();r[0]['success']=True;self.reject(C.pattern_ledger,m,r,'independent:epoch')

    def test_mapping_requires_spatial_sensor_empty_dock_and_distinct_raw_maps(self):
        r=dict(sensor_kind='spatial_diagnostic',sensor_id='spatial-sensor',registration_digest='registration',epoch_id='epoch',empty_dock=True,object_removed=True,all_on_hash='all-on',uncorrected_pump_hash='uncorrected',corrected_pump_hash='corrected',representative_sfg_hash='sfg',valid_pixel_mask_hash='valid-mask',near_zero_excluded=True,coverage_policy_digest='coverage',uncertainty_digest='uncertainty',role='independent_spatial_diagnostic',synthetic_only=True)
        self.assertFalse(C.mapping_evidence(r)['full_set_sfg_proved'])
        for k,v in [('sensor_kind','bucket'),('empty_dock',False),('object_removed',False),('near_zero_excluded',False),('corrected_pump_hash','uncorrected'),('role','actor')]:
            bad=copy.deepcopy(r);bad[k]=v;self.reject(C.mapping_evidence,bad)

    def test_analysis_pair_requires_common_raw_data_and_independent_provenance(self):
        b={k:k for k in ('result_id','raw_digest','matrix_digest','calibration_digest','correction_digest','software_digest','parameters_digest','reference_digest','metrics_digest','uncertainty_digest','residual_digest')}
        b.update(weights_digest=None,role='independent_analysis',kind='synthetic_analysis',synthetic_only=True)
        d=copy.deepcopy(b);d.update(result_id='denoised-result',weights_digest='weights')
        self.assertFalse(C.analysis_pair(b,d)['scientific_accuracy_proved'])
        for k in ('raw_digest','matrix_digest','calibration_digest','correction_digest','reference_digest','metrics_digest','uncertainty_digest'):
            bad=copy.deepcopy(d);bad[k]='different';self.reject(C.analysis_pair,b,bad)
        bad=copy.deepcopy(d);bad['weights_digest']=None;self.reject(C.analysis_pair,b,bad)

    def test_repeat_ledger_preserves_failed_runs_and_rejects_pseudoreplication(self):
        rows=[dict(run_id='run-'+str(i),sample_id='sample',day_id='day',reload_id='reload-'+str(i),calibration_epoch='epoch',policy_id='independent:policy',independent_unit='acquisition_run',physical_display_count=4,frame_count=1,raw_manifest_digest='raw-'+str(i),status='accepted_synthetic' if i==0 else 'rejected_synthetic',synthetic_only=True) for i in range(2)]
        self.assertEqual(C.repeat_ledger(policy(),rows)['independent_runs'],2)
        for k,v in [('run_id','run-0'),('independent_unit','physical_display'),('policy_id','posthoc'),('sample_id','other')]:
            bad=copy.deepcopy(rows);bad[1][k]=v;self.reject(C.repeat_ledger,policy(),bad)
        self.reject(C.repeat_ledger,policy(),rows[:1])

    def test_retry_requires_new_attempt_run_and_raw_ids_with_failure_link(self):
        old=dict(run_id='run-old',attempt_id='attempt-old',sample_id='sample',series_id='series',raw_ids=['raw-old'],prior_failure_id='failure',policy_id='policy',synthetic_only=True)
        new=copy.deepcopy(old);new.update(run_id='run-new',attempt_id='attempt-new',raw_ids=['raw-new'])
        self.assertTrue(C.retry(old,new)['failure_preserved'])
        for k,v in [('run_id','run-old'),('attempt_id','attempt-old'),('raw_ids',['raw-old']),('prior_failure_id','erased'),('policy_id','posthoc'),('sample_id','replacement')]:
            bad=copy.deepcopy(new);bad[k]=v;self.reject(C.retry,old,bad)
        new.update(sample_id='replacement',series_id='new-series');self.assertTrue(C.retry(old,new)['failure_preserved'])

    def test_closeout_is_not_scientific_success_and_accepts_honest_hold(self):
        for hold in (False,True):
            out=C.closeout(closeout(hold));self.assertFalse(out['whole_paper_execution_complete']);self.assertFalse(out['all_branch_metadata_complete']);self.assertEqual(out['fully_closed_synthetic'],not hold)

    def test_closeout_rejects_missing_branch_dock_lease_or_safe_evidence(self):
        for k,v in [('dock_occupied',True),('active_leases',['still-open']),('safe_access_observed',False),('archive_complete',False),('failed_records_retained',False),('all_samples_accounted',False)]:
            bad=closeout();bad[k]=v;self.reject(C.closeout,bad)
        bad=closeout();del bad['branch_status']['B08'];self.reject(C.closeout,bad)
        bad=closeout(True);bad['robot_outside_enclosure']=False;self.reject(C.closeout,bad)

    def test_occupied_hold_cannot_erase_open_lease(self):
        bad=closeout(True);bad['active_leases']=[];self.reject(C.closeout,bad)

    def test_unknown_holds_do_not_turn_into_physical_permission(self):
        for op in C.OPS:
            self.assertFalse(C.scope_holds(op,['physical_execution'])['physical_execution_enabled'])
        self.assertIn('U14',C.scope_holds('R13',['physical_execution'])['unresolved'])
        self.assertIn('U13',C.scope_holds('R07',['physical_execution'])['unresolved'])

    def test_all_evaluator_fixtures_remain_bounded(self):
        for fid in C.FIXTURE_IDS:
            f=C.fixture(fid);out=C.evaluate(f['events'],f['registry'],fid)
            self.assertTrue(out['contract_passed']);self.assertEqual(out['validated_runnable_whole_paper_tasks'],0)
            for key in ('physical_execution','physical_simulation','scientific_reproduction','source_data_reanalysis','whole_paper_execution_complete'):
                self.assertFalse(out[key])

    def test_actor_forgery_registry_mutation_reorder_and_omission_fail(self):
        fid='ALL_BRANCHES:METADATA_OK';f=C.fixture(fid)
        events=copy.deepcopy(f['events']);events[0]['success']=True;self.reject(C.evaluate,events,f['registry'],fid)
        events=copy.deepcopy(f['events']);events[1]=events[0];self.reject(C.evaluate,events,f['registry'],fid)
        self.reject(C.evaluate,f['events'][::-1],f['registry'],fid)
        self.reject(C.evaluate,f['events'][:-1],f['registry'],fid)
        registry=copy.deepcopy(f['registry']);registry[f['events'][0]['evidence_id']]['payload']['source_outcome_used']=True;self.reject(C.evaluate,f['events'],registry,fid)


if __name__ == '__main__':
    unittest.main()
