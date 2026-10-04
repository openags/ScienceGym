"""Independently authored adversarial checks for bounded synthetic contracts.

These tests do not run equipment, physical simulation, imaging, FE inversion, or
source-data analysis. Passing them is not scientific validation or authentication.
"""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('independent_wetting_contract', ROOT / 'tests' / 'contract.py')
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)


def read(name):
    return json.loads((ROOT / name).read_text())


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class IndependentSourceAndScopeTests(unittest.TestCase):
    def test_exact_reviewed_route_and_operation_identity(self):
        branches = read('branches.json')['branches']
        ops = read('operations.json')['operations']
        self.assertEqual([b['id'] for b in branches], [f'R{i:02d}' for i in range(16)])
        self.assertEqual(len(ops), 74)
        self.assertEqual(len({o['id'] for o in ops}), 74)
        projection = [{'id': b['id'], 'operations': [{'id': o['id'], 'description': o['description']} for o in ops if o['route_id'] == b['id']]} for b in branches]
        self.assertEqual(sha(projection), '7769af859a816a08fd1d2a89bebbd0a19909e21ca26b5a8ae8c00b01791adddb')
        for b in branches:
            self.assertEqual(b['route_operation_ids'], [o['id'] for o in ops if o['route_id'] == b['id']])
            self.assertIs(b['physical_implemented'], False)
            self.assertIs(b['closeout_reachable_on_abort'], True)
        for o in ops:
            self.assertEqual(o['step_origin'], 'independently_authored_robot_task_design')
            self.assertIs(o['source_is_robot_protocol'], False)
            self.assertIs(o['physical_implemented'], False)

    def test_reviewed_facts_and_repeat_semantics_preserved(self):
        for name, expected in [('source_parameters.json', 'fb32e4e52f1d840b005a58c8f1065c77fb09876a232270efb482708c5b2322cf'), ('controls_and_repeats.json', '8c3574dda030d57a28ddccfba345395db1cef3275084a343b7a26ec2c856742f')]:
            d = read(name)
            d.pop('schema_version')
            self.assertEqual(sha(d), expected)
        p = read('source_parameters.json')
        self.assertEqual(p['macroscopic']['analysis_origin_volume_nL'], 55)
        self.assertEqual(p['microscopy']['fig3_CY9_10_placed_volume_nL']['fast'], 49)
        self.assertEqual(p['microscopy']['separate_detection_limit_branch']['material'], 'PDMS30:1')
        fits = p['analysis_reference']['reported_ridge_fits']
        self.assertNotEqual(fits['current_placement_P1_geometry']['purpose'], fits['Ur_Uz_displacements']['purpose'])

    def test_all_reviewed_cautions_and_gaps_retained(self):
        conflicts = read('source_conflicts.json')['conflicts']
        unknowns = read('unknown_parameters.json')['unknowns']
        self.assertEqual({c['id'] for c in conflicts}, {f'C{i:02d}' for i in range(1, 11)})
        self.assertEqual({u['id'] for u in unknowns}, {f'U{i:02d}' for i in range(1, 26)})
        source_conflict_keys = ('id', 'topic', 'type', 'evidence', 'source_a', 'source_b', 'policy')
        source_unknown_keys = ('id', 'unknown', 'routes', 'resolution_required', 'state')
        self.assertEqual(sha([{k: c[k] for k in source_conflict_keys} for c in conflicts]), '8db90d8b6e95ede1f21b9a6ac49056b207b6a68bb322ff3c02ec1abd92eaa6f6')
        self.assertEqual(sha([{k: u[k] for k in source_unknown_keys} for u in unknowns]), '7ba2b2e9a68272b7421b3ceb158f76b2a2de41c970351031bbce86b125aca045')
        for c in conflicts:
            self.assertTrue(c['operation_ids'])
            self.assertTrue(c['scope_tags'])
            for op in c['operation_ids']:
                self.assertIn(c['id'], C.OPS[op]['conflict_ids'])
        for u in unknowns:
            self.assertEqual(u['state'], 'unresolved_not_defaulted')
            self.assertIs(u['safe_closeout_exception'], True)
            for op in u['operation_ids']:
                self.assertIn(u['id'], C.OPS[op]['unknown_ids'])

    def test_conflict_holds_are_scoped_and_never_execution_authority(self):
        for cid, caution in C.CONFLICTS.items():
            tag = caution['scope_tags'][0]
            for oid in C.OPS:
                r = C.scope_holds(oid, [tag])
                self.assertEqual(cid in r['conflicts'], oid in caution['operation_ids'])
                self.assertIs(r['permission_to_execute'], False)
                self.assertIs(r['safe_closeout_always_reachable'], True)
                self.assertEqual(C.scope_holds(oid, [])['conflicts'], [])
        for oid in C.BRANCHES['R15']['route_operation_ids']:
            self.assertEqual(C.scope_holds(oid, sorted({t for c in C.CONFLICTS.values() for t in c['scope_tags']}))['conflicts'], [])

    def test_unread_source_data_gap_does_not_block_independent_observations(self):
        for oid in C.OPS:
            ordinary = C.scope_holds(oid, [])
            source = C.scope_holds(oid, ['original_source_reanalysis'])
            self.assertNotIn('U22', ordinary['qualification'])
            self.assertEqual('U22' in source['qualification'], oid in C.UNKNOWNS['U22']['operation_ids'])
            if oid.startswith('R15'):
                self.assertEqual(source['qualification'], [])
        self.assertEqual(set(C.UNKNOWNS['U25']['operation_ids']), {'R09_O06', 'R14_O02'})
        self.assertNotIn('U25', C.scope_holds('R09_O02', [])['qualification'])
        self.assertEqual(C.UNKNOWNS['U07']['operation_ids'], ['R13_O05'])
        self.assertNotIn('U07', C.scope_holds('R13_O01', [])['qualification'])

    def test_material_ancestry_is_scoped(self):
        self.assertNotIn('R02', C.route_ancestors('R09', 'PDMS'))
        self.assertIn('R01', C.route_ancestors('R09', 'PDMS'))
        self.assertNotIn('R01', C.route_ancestors('R11', 'CY'))
        self.assertIn('R02', C.route_ancestors('R11', 'CY'))
        self.assertEqual(C.route_ancestors('R15', 'MULTI'), [])
        for route, material in [('R01', 'CY'), ('R02', 'PDMS'), ('R09', 'CY'), ('R10', 'CY')]:
            with self.subTest(route=route, material=material), self.assertRaises(C.ContractError):
                C.route_ancestors(route, material)

    def test_rigid_angle_and_ridge_analysis_material_scopes(self):
        self.assertEqual(C.OPS['R09_O06']['material_ids'], ['PDMS_9:1'])
        for oid in ('R14_O03', 'R14_O04', 'R14_O05'):
            self.assertEqual(set(C.OPS[oid]['material_ids']), {'CY_5:6', 'CY_9:10'})
        f = C.fixture('R09:METADATA_OK')
        record = next(r for r in f['registry'].values() if r['operation_id'] == 'R09_O06')
        self.assertEqual([x['material_id'] for x in record['payload']['constituent_lineages']], ['PDMS_9:1'])

    def test_binding_containment_and_noncontrol_guards(self):
        p = read('asset_binding_plan.json')
        bindings = p['operation_bindings']
        self.assertEqual({b['operation_id'] for b in bindings}, set(C.OPS))
        self.assertEqual(len(bindings), 74)
        for b in bindings:
            self.assertIs(b['physical_motion_qualified'], False)
            self.assertIn('G_NO_CONTROL', b['guard_ids'])
            self.assertIn('G_SCALE', b['guard_ids'])
            if b['operation_id'][:3] in ('R07', 'R11', 'R13', 'R15'):
                self.assertIn('G_CONTAINMENT', b['guard_ids'])
            if b['operation_id'].startswith('R15'):
                self.assertIn('G_SAFE_RELEASE', b['guard_ids'])
        self.assertEqual(C.BRANCHES['R07']['kind'], 'external_service_only')
        self.assertIs(read('nonmanual_scope.json')['all_services_unimplemented'], True)
        self.assertEqual(read('evaluator_reference.json')['actor_visible_allowlist'], ['agent_visible.json'])


class IndependentEvaluatorMutationTests(unittest.TestCase):
    def rejected(self, fixture, events=None, registry=None):
        with self.assertRaises(C.ContractError):
            C.evaluate(events if events is not None else fixture['events'], registry if registry is not None else fixture['registry'], fixture['fixture_id'])

    def test_all_64_bounded_fixtures_remain_nonphysical(self):
        self.assertEqual(len(C.FIXTURE_IDS), 64)
        for fid in C.FIXTURE_IDS:
            with self.subTest(fid=fid):
                f = C.fixture(fid)
                r = C.evaluate(f['events'], f['registry'], fid)
                self.assertIs(r['contract_passed'], True)
                self.assertEqual(r['validated_runnable_whole_paper_tasks'], 0)
                for key in ('whole_paper_execution_complete', 'physical_execution', 'physical_simulation', 'scientific_reproduction', 'source_data_reanalysis'):
                    self.assertIs(r[key], False)
                self.assertEqual([e['operation_id'] for e in f['events'][-4:]], C.BRANCHES['R15']['route_operation_ids'])

    def test_every_event_omission_duplication_order_and_operation_mutation(self):
        for fid in C.FIXTURE_IDS:
            f = C.fixture(fid)
            for index in range(len(f['events'])):
                with self.subTest(fid=fid, index=index):
                    e = copy.deepcopy(f['events']); e.pop(index); self.rejected(f, events=e)
                    e = copy.deepcopy(f['events']); e.append(copy.deepcopy(e[index])); self.rejected(f, events=e)
                    e = copy.deepcopy(f['events']); e[index]['operation_id'] = 'R99_O99'; self.rejected(f, events=e)
            self.rejected(f, events=list(reversed(f['events'])))

    def test_every_actor_extra_field_is_rejected(self):
        f = C.fixture('R07:METADATA_OK')
        for key in ('success', 'safe', 'qualified', 'physical_execution', 'sensor_values', 'source_outcomes', 'material_id', 'registry_digest', 'service_receipt', 'payload'):
            with self.subTest(key=key):
                e = copy.deepcopy(f['events']); e[0][key] = True; self.rejected(f, events=e)

    def test_every_context_field_cannot_be_rebound(self):
        for fid in ('R07:METADATA_OK', 'R11:METADATA_OK', 'R15:ISOLATION_HOLD'):
            f = C.fixture(fid)
            for rid in f['registry']:
                for key in C.CONTEXT:
                    with self.subTest(fid=fid, rid=rid, key=key):
                        registry = copy.deepcopy(f['registry'])
                        registry[rid]['context'][key] = ['wrong_scope'] if key == 'scope_tags' else 'wrong_revision_or_identity'
                        self.rejected(f, registry=registry)

    def test_registry_content_cannot_be_laundered_by_rehash(self):
        f = C.fixture('R13:METADATA_OK')
        rid = next(iter(f['registry']))
        for key, value in [('synthetic_only', False), ('physical_qualified', True), ('physical_execution', True), ('source_outcome_used', True), ('status', 'SUCCESS'), ('record_type', 'sensor_observation')]:
            with self.subTest(key=key):
                registry = copy.deepcopy(f['registry']); registry[rid]['payload'][key] = value
                C.digest(registry)
                self.rejected(f, registry=registry)
        for key, value in [('role', 'actor_assertion'), ('depends_on', []), ('evidence_id', 'forged')]:
            registry = copy.deepcopy(f['registry'])
            target = list(registry)[1] if key == 'depends_on' else rid
            registry[target][key] = value
            self.rejected(f, registry=registry)

    def test_cross_fixture_replay_and_unknown_fixture_are_rejected(self):
        a = C.fixture('R09:METADATA_OK'); b = C.fixture('R09:DATA_HOLD')
        self.rejected(a, registry=b['registry'])
        self.rejected(a, events=b['events'])
        for fid in ('R09:SUCCESS', 'R99:METADATA_OK', '', None, True):
            with self.subTest(fid=fid), self.assertRaises(C.ContractError):
                C.fixture(fid)

    def test_mixed_campaign_keeps_detection_limit_material_separate(self):
        f = C.fixture('R11:METADATA_OK')
        self.assertEqual(f['context']['material_id'], 'MULTI')
        records = {r['operation_id']: r for r in f['registry'].values()}
        detection = records['R11_O06']['payload']['constituent_lineages']
        dynamic = records['R11_O05']['payload']['constituent_lineages']
        self.assertEqual([x['material_id'] for x in detection], ['PDMS_30:1'])
        self.assertEqual({x['material_id'] for x in dynamic}, {'CY_5:6', 'CY_9:10'})
        for x in detection:
            self.assertIn('R01', x['preparation_ancestry'])
            self.assertNotIn('R02', x['preparation_ancestry'])
        for x in dynamic:
            self.assertIn('R02', x['preparation_ancestry'])
            self.assertNotIn('R01', x['preparation_ancestry'])
        for field in ('sample_id', 'spot_id', 'droplet_id'):
            self.assertTrue({x[field] for x in detection}.isdisjoint({x[field] for x in dynamic}))
        for oid in ('R11_O05', 'R11_O06'):
            registry = copy.deepcopy(f['registry'])
            rid = next(k for k, v in registry.items() if v['operation_id'] == oid)
            registry[rid]['payload']['constituent_lineages'][0]['material_id'] = 'wrong_material'
            self.rejected(f, registry=registry)

    def test_isolation_failure_cannot_release_or_remove(self):
        for route in C.BRANCHES:
            f = C.fixture(route + ':ISOLATION_HOLD')
            records = {r['operation_id']: r for r in f['registry'].values()}
            self.assertIs(records['R15_O01']['payload']['safe_release_observed_synthetic'], False)
            self.assertEqual(records['R15_O01']['payload']['disposition'], 'held_contained')
            self.assertIs(records['R15_O02']['payload']['physical_removed'], False)
            self.assertEqual(records['R15_O02']['payload']['disposition'], 'held_contained')
            self.assertIs(records['R15_O03']['payload']['attempts_preserved'], True)
            for oid, key, value in [('R15_O01', 'safe_release_observed_synthetic', True), ('R15_O02', 'physical_removed', True), ('R15_O03', 'attempts_preserved', False)]:
                registry = copy.deepcopy(f['registry'])
                rid = next(k for k, v in registry.items() if v['operation_id'] == oid)
                registry[rid]['payload'][key] = value
                self.rejected(f, registry=registry)


class IndependentNumericAndProvenanceTests(unittest.TestCase):
    def test_finite_number_hostiles(self):
        for value in (True, False, '1', None, float('nan'), float('inf'), -float('inf'), 10 ** 10000):
            with self.subTest(kind=type(value).__name__), self.assertRaises(C.ContractError):
                C.finite(value)

    def test_macro_origin_boundary_and_hostile_scopes(self):
        good = dict(cohort='macro', time_s=[0, 1, 2], volume_nL=[60, 54, 50], evidence_kind='synthetic_observation', synthetic_only=True)
        self.assertEqual(C.macro_origin(good)['origin_bracket_s'], [0, 1])
        self.assertIsNone(C.macro_origin(good)['interpolated_timestamp'])
        for key, value in [('cohort', 'microscopy'), ('volume_nL', [49, 48, 47]), ('time_s', [0, 0, 2]), ('volume_nL', [60, 55, 55]), ('volume_nL', [60, 50, 60]), ('synthetic_only', False), ('evidence_kind', 'source_reference')]:
            bad = copy.deepcopy(good); bad[key] = value
            # A later rise after a single downward bracket does not itself invent a second crossing.
            if value == [60, 50, 60]:
                bad['time_s'] = [0, 1, 2, 3]; bad['volume_nL'] = [60, 50, 60, 50]
            with self.subTest(key=key, value=value), self.assertRaises(C.ContractError): C.macro_origin(bad)

    def test_stack_timing_and_overflow_rejection(self):
        good = dict(stack_id='stack', start_s=0, end_s=2, plane_time_s=[0.2, 1.2], z_um=[0, 1], side_time_s=[0.2, 1.2], environment_interval_s=[0, 2], sync_tolerance_s=0, synthetic_only=True)
        self.assertIs(C.stack_timing(good)['instantaneous'], False)
        for key, value in [('plane_time_s', [1.2, 0.2]), ('z_um', [1, 1]), ('side_time_s', [0.3, 1.3]), ('environment_interval_s', [0.1, 2]), ('synthetic_only', False)]:
            bad = copy.deepcopy(good); bad[key] = value
            with self.subTest(key=key), self.assertRaises(C.ContractError): C.stack_timing(bad)
        overflow = dict(stack_id='overflow', start_s=-1e308, end_s=1e308, plane_time_s=[-1e308, 1e308], z_um=[0, 1], side_time_s=[-1e308, 1e308], environment_interval_s=[-1e308, 1e308], sync_tolerance_s=0, synthetic_only=True)
        with self.assertRaises(C.ContractError): C.stack_timing(overflow)

    def test_repeat_ledger_preserves_hierarchy_and_no_pseudoreplication(self):
        rows = [dict(sample_id='s', spot_id='p', droplet_id='d', timepoint_id=str(i), cohort_id='c') for i in range(24)]
        result = C.repeat_ledger(rows)
        self.assertEqual((result['distinct_samples'], result['distinct_droplets'], result['timepoints']), (1, 1, 24))
        self.assertIs(result['statistical_independence_established'], False)
        self.assertIs(result['source_cohort_overlap_resolved'], False)
        for key, value in [('sample_id', 'other'), ('spot_id', 'other'), ('timepoint_id', '0')]:
            bad = copy.deepcopy(rows); bad[-1][key] = value
            with self.subTest(key=key), self.assertRaises(C.ContractError): C.repeat_ledger(bad)
        duplicate = copy.deepcopy(rows); duplicate.append(dict(rows[0], cohort_id='another_figure'))
        with self.assertRaises(C.ContractError): C.repeat_ledger(duplicate)

    def test_imputed_inferred_annotations_cannot_claim_observation(self):
        for kind in ('observed', 'manual_annotation', 'imputed', 'inferred_reference'):
            row = dict(point_id='p', kind=kind, xyz_m=[0, 1e-6, 2e-6], raw_parent_id='raw', method_revision='v1', directly_measured=kind == 'observed')
            self.assertEqual(C.coordinate_layers([row]), {'p': kind})
            bad = dict(row, directly_measured=not row['directly_measured'])
            with self.subTest(kind=kind), self.assertRaises(C.ContractError): C.coordinate_layers([bad])
            with self.assertRaises(C.ContractError): C.coordinate_layers([row, row])
            with self.assertRaises(C.ContractError): C.coordinate_layers([dict(row, raw_parent_id='')])

    def test_correspondence_requires_unique_pairs_and_boundary(self):
        good = dict(array_id='array', pairs=[['a', 'x'], ['b', 'y'], ['c', 'z']], boundary_evidence_id='boundary', boundary_stationary=True, synthetic_only=True)
        result = C.marker_correspondence(good)
        self.assertEqual(result['reference_kind'], 'inferred_reference')
        self.assertIs(result['captured_reference_image'], False)
        self.assertIs(result['graph_solver_executed'], False)
        for key, value in [('pairs', [['a', 'x'], ['b', 'x'], ['c', 'z']]), ('boundary_stationary', False), ('boundary_evidence_id', ''), ('synthetic_only', False)]:
            bad = copy.deepcopy(good); bad[key] = value
            with self.subTest(key=key), self.assertRaises(C.ContractError): C.marker_correspondence(bad)

    def test_source_angle_and_P1_displacement_semantics(self):
        good = dict(theta_star_rad=1.5, psi_rad=0.2, theta_r_rad=1.7, theta_r_kind='source_reference_only', psi_fit_field='P1_current_placement', displacement_fit_fields=['Ur', 'Uz'], synthetic_only=True)
        r = C.angle_comparison(good)
        self.assertAlmostEqual(r['residual_rad'], 0)
        self.assertEqual(r['comparison_kind'], 'source_reference_model')
        self.assertIs(r['new_measurement_gate_satisfied'], False)
        self.assertIs(r['observed_depinning'], False)
        for key, value in [('psi_fit_field', 'Uz'), ('displacement_fit_fields', ['P1_current_placement']), ('theta_r_kind', 'new_observation'), ('theta_r_rad', 99.7), ('synthetic_only', False)]:
            bad = copy.deepcopy(good); bad[key] = value
            with self.subTest(key=key), self.assertRaises(C.ContractError): C.angle_comparison(bad)

    def test_traction_dimensional_scope_and_nonphysical_result(self):
        good = dict(tractions_Pa=[[3, 4, 0]], triangle_areas_m2=[2], area_measure='reference_physical_area', window_policy_id='synthetic_window', conflict_dispositions={'C02': 'synthetic_scope_choice', 'C03': 'synthetic_dimensional_audit'}, sector_angle_rad=1, synthetic_only=True)
        result = C.traction_area(good)
        self.assertEqual(result['sum_magnitude_times_area'], 10)
        self.assertEqual(result['unit'], 'N')
        self.assertIs(result['equilibrium_force_balance_established'], False)
        self.assertIs(result['scientific_model_validated'], False)
        for key, value in [('area_measure', 'polar_dr_dtheta'), ('triangle_areas_m2', [-1]), ('conflict_dispositions', {'C02': 'synthetic_scope_choice'}), ('sector_angle_rad', 0), ('sector_angle_rad', 2 * math.pi + 1), ('tractions_Pa', [[1e308, 1e308, 1e308]]), ('synthetic_only', False)]:
            bad = copy.deepcopy(good); bad[key] = value
            with self.subTest(key=key), self.assertRaises(C.ContractError): C.traction_area(bad)

    def test_age_custody_and_humidity_do_not_claim_physical_qualification(self):
        age = dict(material_family='CY', cure_utc='2026-01-01T00:00:00Z', experiment_utc='2026-01-15T00:00:00Z', storage_receipt_id='dated_record', custody_basis='synthetic_dated_custody', synthetic_only=True)
        self.assertIs(C.age_eligibility(age)['eligible_synthetic_window'], True)
        self.assertIs(C.age_eligibility(age)['real_storage_qualified'], False)
        self.assertIs(C.age_eligibility(dict(age, experiment_utc='2026-01-08T00:00:00Z'))['eligible_synthetic_window'], False)
        for basis in ('filesystem_mtime', 'simulated_timer'):
            with self.assertRaises(C.ContractError): C.age_eligibility(dict(age, custody_basis=basis))
        with self.assertRaises(C.ContractError): C.age_eligibility(dict(age, cure_utc='2026-01-01T00:00:00'))
        rh = dict(setpoint_percent=90, measured_percent=89, stability_pp=1, sensor_accuracy_pp=3, claimed_absolute_accuracy_pp=3, synthetic_only=True)
        self.assertIs(C.humidity_semantics(rh)['absolute_accuracy_validated'], False)
        with self.assertRaises(C.ContractError): C.humidity_semantics(dict(rh, claimed_absolute_accuracy_pp=1))

    def test_retry_preserves_failure_and_requires_new_identity(self):
        a = dict(attempt_id='a1', sample_id='sample', spot_id='spot1', droplet_id='d1', acquisition_id='acq1', qualified_spot_receipt='q1', previous_failure_id='failure')
        b = dict(attempt_id='a2', sample_id='sample', spot_id='spot2', droplet_id='d2', acquisition_id='acq2', qualified_spot_receipt='q2', previous_failure_id='failure')
        self.assertIs(C.retry_lineage(a, b)['physical_retry_executed'], False)
        for key in ('attempt_id', 'spot_id', 'droplet_id', 'acquisition_id', 'qualified_spot_receipt'):
            with self.subTest(key=key), self.assertRaises(C.ContractError): C.retry_lineage(a, dict(b, **{key: a[key]}))
        with self.assertRaises(C.ContractError): C.retry_lineage(a, dict(b, previous_failure_id='erased_failure'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
