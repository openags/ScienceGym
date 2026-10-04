"""Independent original review tests. These establish bounded design contracts only.

Run: python -m unittest discover -s review -p 'test_independent_contract.py' -v
No source data, source figures, scientific solver or external service is executed.
"""
from __future__ import annotations
import json
import pathlib
import unittest
import sys
sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parents[1]

def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))

class IndependentDesignCoverage(unittest.TestCase):
    def setUp(self):
        self.branches = {x['id']: x for x in read('branches.json')['branches']}
        self.ops = {x['id']: x for x in read('operations.json')['operations']}

    def test_required_reported_families_are_present(self):
        required = {
            'SOURCE_RECONCILIATION', 'STO_FABRICATION', 'KTO_FABRICATION',
            'CNT_SQD_FABRICATION', 'CNT_DQD_FABRICATION', 'MODULE_ASSEMBLY',
            'RF_LINE_CALIBRATION', 'FIXED_LOAD_STO', 'FIXED_LOAD_KTO',
            'STO_KTO_COMPARISON', 'REFLECTION_CIRCUIT_FIT', 'LOSS_BOUND',
            'PERMITTIVITY_MODEL', 'SQD_SNR_MODEL', 'DQD_SNR_MODEL', 'LOSS_SNR_MODEL',
            'SQD_DC_BASELINE', 'SQD_SIDEBAND_READOUT', 'SQD_POWER_DEPENDENCE',
            'SQD_MATCHING_COMPARISON', 'DUAL_FREQUENCY_MATCHING',
            'MAGNETIC_FIELD_RESPONSE', 'DQD_STABILITY_DIAGRAM', 'DQD_JPA_COMPARISON',
            'DQD_CAPACITANCE_SENSITIVITY', 'HYSTERESIS_HISTORY', 'RESONANCE_STABILITY',
            'READOUT_SCALING_PROJECTION'
        }
        self.assertEqual(set(self.branches), required)

    def test_no_duplicate_branch_or_operation_identifiers(self):
        self.assertEqual(len(self.branches), len(read('branches.json')['branches']))
        self.assertEqual(len(self.ops), len(read('operations.json')['operations']))

    def test_routes_and_operations_refer_to_each_other(self):
        for bid, branch in self.branches.items():
            for oid in branch['operation_ids']:
                self.assertIn(oid, self.ops, (bid, oid))
                self.assertIn(bid, self.ops[oid]['branch_ids'], (bid, oid))
            self.assertTrue(set(branch['route_operation_ids']) <= set(branch['operation_ids']))
        for oid, operation in self.ops.items():
            for bid in operation['branch_ids']:
                self.assertIn(oid, self.branches[bid]['operation_ids'], (bid, oid))

    def test_source_locators_exist_for_every_route_and_operation(self):
        evidence = {x['id'] for x in read('evidence_map.json')['evidence']}
        for item in list(self.branches.values()) + list(self.ops.values()):
            self.assertTrue(item['source_evidence_ids'], item['id'])
            self.assertTrue(set(item['source_evidence_ids']) <= evidence, item['id'])

    def test_design_status_does_not_claim_execution(self):
        status = read('STATUS.json')
        for flag in ['whole_paper_execution_complete', 'full_paper_execution_eligible',
                     'whole_paper_complete', 'qualifies_for_full_paper_execution_count',
                     'scientific_reproduction_run', 'physical_geometry_validated']:
            self.assertIs(status[flag], False, flag)
        self.assertEqual(status['circuit_solver'], 'UNIMPLEMENTED')
        self.assertEqual(status['physical_runtime'], 'UNIMPLEMENTED')
        boundary = read('RELEASE_BOUNDARY.json')
        for flag in ['whole_paper_execution_complete', 'physical_execution',
                     'numerical_execution', 'scientific_reproduction',
                     'source_files_exported', 'exact_geometry_validated']:
            self.assertIs(boundary[flag], False, flag)
        self.assertEqual(boundary['validated_runnable_whole_paper_tasks'], 0)

    def test_every_branch_is_design_only(self):
        for branch in self.branches.values():
            self.assertIs(branch['physical_executed'], False, branch['id'])
            self.assertIs(branch['numerical_executed'], False, branch['id'])
            self.assertIn('design', branch['interpretation_limit'].lower())
        for operation in self.ops.values():
            self.assertIs(operation['physical_execution_authority'], False, operation['id'])
            self.assertIs(operation['device_command_implemented'], False, operation['id'])

    def test_closed_routes_include_failure_and_safety_closure(self):
        needed = {'HOLD_QUALIFICATION', 'HOLD_ISOLATION', 'REQUEST_SAFE_OFF',
                  'VERIFY_SAFE_OFF', 'UNDOCK_MODULE', 'ARCHIVE_RECORDS',
                  'CLEAN_STATION', 'STORE_SAMPLE', 'QUARANTINE_SAMPLE'}
        for branch in self.branches.values():
            if branch['execution_class'] == 'closed_service':
                self.assertTrue(needed <= set(branch['operation_ids']), branch['id'])

    def test_assets_are_original_unvalidated_placeholders(self):
        plan = read('asset_binding_plan.json')
        assets = plan['scene_assets']
        self.assertEqual(len(assets), 12)
        self.assertEqual(sum(len(x['required_anchor_ids']) for x in assets), 65)
        for asset in assets:
            self.assertEqual(asset['render_geometry'], 'authored_generic')
            self.assertIs(asset['physical_geometry_validated'], False)
            self.assertEqual(len(asset['required_anchor_ids']), len(set(asset['required_anchor_ids'])))
            self.assertTrue(set(asset['bind_operation_ids']) <= set(self.ops))

    def test_actor_sees_only_symbolic_actions(self):
        visible = read('agent_visible.json')
        for flag in ['source_outcomes_exposed', 'can_declare_measurement',
                     'can_declare_service_qualification', 'can_supply_physical_observation',
                     'physical_implementation']:
            self.assertIs(visible[flag], False, flag)
        self.assertEqual(read('episode_input_contract.json')['actor_event_fields'],
                         ['event_id', 'operation_id', 'evidence_id'])
        self.assertEqual(read('evaluator_reference.json')['actor_visible_allowlist'],
                         ['agent_visible.json'])

    def test_lattice_and_electron_temperatures_stay_distinct(self):
        p = {x['id']:x for x in read('source_parameters.json')['parameters']}
        self.assertEqual(p['P_THERMAL']['facts']['source_lattice_base_mK'], 6)
        self.assertEqual(p['P_THERMAL']['facts']['source_electron_temperature_mK'], 12)

    def test_pad_variants_stay_distinct(self):
        p = {x['id']:x for x in read('source_parameters.json')['parameters']}
        geometry = p['P_GEOMETRY']['facts']
        self.assertEqual(geometry['fixed_load_pad_nominal_diameter_um'], 100)
        self.assertEqual(geometry['QD_pad_nominal_size_um'], [120, 120])
        self.assertEqual(geometry['STO_orientation'], '001')
        self.assertEqual(geometry['KTO_orientation'], '100')

    def test_source_axis_typo_is_not_silently_repaired(self):
        conflicts = read('source_conflicts.json')['conflicts']
        hits = [x for x in conflicts if '215' in json.dumps(x)]
        self.assertTrue(hits, 'The repeated 215 MHz KTO axis label must remain explicit')
        self.assertTrue(any(any(word in json.dumps(x).lower() for word in
                            ['duplicat', 'repeat']) for x in hits))

    def test_source_sqd_inductor_value_and_part_are_not_conflated(self):
        p = {x['id']:x for x in read('source_parameters.json')['parameters']}
        self.assertEqual(p['P_CIRCUIT']['facts']['SQD_model_inductor_nH'], 320)
        self.assertIn('0805CS-331', json.dumps(read('source_conflicts.json')))

    def test_projection_gets_no_spin_or_gigahertz_execution_credit(self):
        text = json.dumps(self.branches['READOUT_SCALING_PROJECTION']).lower()
        self.assertIn('assumption', text)
        self.assertIn('no spin-readout', text)
        self.assertIn('demonstration credit', text)


class IndependentRuntimeNegatives(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec = importlib.util.spec_from_file_location('independent_target_contract', ROOT / 'tests' / 'contract.py')
        cls.c = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.c)

    def setUp(self):
        from copy import deepcopy
        self.copy = deepcopy
        self.fid = 'DQD_JPA_COMPARISON:PREPARED:GOOD'
        self.base = self.c.fixture(self.fid)

    def check_rejected(self, events=None, registry=None):
        with self.assertRaises(self.c.ContractError):
            self.c.evaluate(self.base['events'] if events is None else events,
                            self.base['receipts'] if registry is None else registry,
                            self.fid)

    def test_every_registered_fixture_remains_bookkeeping_only(self):
        for fid in self.c.FIXTURE_IDS:
            with self.subTest(fid=fid):
                f = self.c.fixture(fid)
                out = self.c.evaluate(f['events'], f['receipts'], fid)
                self.assertIs(out['contract_passed'], True)
                for key in ['whole_campaign_complete', 'physical_execution',
                            'numerical_solver_execution', 'scientific_reproduction',
                            'whole_paper_execution_complete', 'source_expected_outcome_used',
                            'production_authentication_established']:
                    self.assertIs(out[key], False)

    def test_forged_actor_assertions_are_rejected(self):
        for key, value in [('success', True), ('safe_release_observed', True),
                           ('qualification', 'approved'), ('voltage', 1.0),
                           ('sensor_value', 0.0), ('payload', {})]:
            with self.subTest(key=key):
                ev = self.copy(self.base['events']); ev[0][key] = value
                self.check_rejected(events=ev)

    def test_every_revision_relabel_is_rejected(self):
        for key in self.c.CONTEXT_KEYS:
            with self.subTest(key=key):
                reg = self.copy(self.base['receipts'])
                next(iter(reg.values()))['context'][key] = 'foreign-revision'
                self.check_rejected(registry=reg)

    def test_request_acknowledgement_cannot_become_observation(self):
        reg = self.copy(self.base['receipts'])
        row = next(r for r in reg.values() if r['operation_id'].startswith('REQUEST_'))
        row['payload']['role'] = 'independent_record'
        self.check_rejected(registry=reg)

    def test_raw_payload_and_self_rehashed_registry_are_rejected(self):
        reg = self.copy(self.base['receipts'])
        row = next(r for r in reg.values() if r['operation_id'] == 'ACQUIRE_RECORDS')
        row['payload']['raw']['x'][0] += 0.5
        row['payload']['raw_hash'] = self.c.digest(row['payload']['raw'])
        self.check_rejected(registry=reg)

    def test_missing_duplicate_replayed_and_reordered_events_are_rejected(self):
        ev = self.copy(self.base['events']); self.check_rejected(events=ev[:-1])
        ev = self.copy(self.base['events']); ev[1] = self.copy(ev[0]); self.check_rejected(events=ev)
        ev = self.copy(self.base['events']); ev[0], ev[1] = ev[1], ev[0]; self.check_rejected(events=ev)
        ev = self.copy(self.base['events']); ev[0]['evidence_id'] = ev[1]['evidence_id']; self.check_rejected(events=ev)

    def test_foreign_fixture_registry_cannot_establish_authority(self):
        f = self.c.fixture('DQD_JPA_COMPARISON:FULL:GOOD')
        self.check_rejected(registry=f['receipts'])
        self.check_rejected(events=f['events'])

    def test_hold_or_damage_never_earns_good_completion(self):
        for outcome in ['DAMAGED', 'DATA_HOLD', 'ISOLATION_HOLD']:
            fid = 'DQD_JPA_COMPARISON:PREPARED:' + outcome
            f = self.c.fixture(fid); out = self.c.evaluate(f['events'], f['receipts'], fid)
            self.assertIs(out['synthetic_instance_complete'], False)
            if outcome == 'ISOLATION_HOLD':
                ops = {e['operation_id'] for e in f['events']}
                self.assertNotIn('UNDOCK_MODULE', ops)
                self.assertNotIn('STORE_SAMPLE', ops)
                self.assertIn('HOLD_ISOLATION', ops)

    def test_prepared_entry_cannot_earn_fabrication_credit(self):
        out = self.c.evaluate(self.base['events'], self.base['receipts'], self.fid)
        self.assertIs(out['synthetic_preparation_lineage_checked'], False)
        for r in self.base['receipts'].values():
            if 'fabrication_credit' in r['payload']:
                self.assertIs(r['payload']['fabrication_credit'], False)

    def phase(self):
        return {'regime':'under','evidence_kind':'independent_phase','phase_record_id':'phase-v1',
                'calibration_revision':'cal-v1','expected_calibration_revision':'cal-v1'}

    def test_phase_requires_real_nonempty_revision_ids(self):
        for bad in [None, '', True, 1, [], {}]:
            with self.subTest(bad=bad):
                r = self.phase(); r['calibration_revision'] = bad; r['expected_calibration_revision'] = bad
                with self.assertRaises(self.c.ContractError): self.c.phase_regime(r)

    def test_magnitude_only_or_stale_phase_cannot_label_coupling(self):
        for field, value in [('evidence_kind','magnitude_only'), ('calibration_revision','stale'),
                             ('phase_record_id',''), ('regime','unknown')]:
            r = self.phase(); r[field] = value
            with self.assertRaises(self.c.ContractError): self.c.phase_regime(r)

    def pair(self):
        left = {'sample_id':'shared-chip','varactor_ids':['freq-pad','match-pad'],'device_id':'dqd-device',
                'circuit_revision':'dqd-circuit-v2','reference_plane_revision':'rf-v2',
                'filter_revision':'filter-v2','thermal_revision':'thermal-v1','history_revision':'history-v5',
                'carrier_plan_revision':'carrier-v1','acquisition_plan_revision':'acquisition-v1',
                'comparison_region_id':'roi-A','baseline_revision':'baseline-v1',
                'amplifier_state':'off','gain_noise_revision':'gain-off-v1','transition_id':'A',
                'snr_dB':3.0,'saturated':False,'power_broadened':False,'synthetic_only':True}
        right = self.copy(left); right.update(amplifier_state='on',gain_noise_revision='gain-on-v1',snr_dB=8.0)
        return left, right

    def test_jpa_pair_rejects_every_shared_context_mismatch(self):
        for field in ['sample_id','varactor_ids','device_id','circuit_revision',
                      'reference_plane_revision','filter_revision','thermal_revision',
                      'history_revision','transition_id','carrier_plan_revision','acquisition_plan_revision',
                      'comparison_region_id','baseline_revision']:
            with self.subTest(field=field):
                l,r = self.pair(); r[field] = ['other-pad','match-pad'] if field == 'varactor_ids' else 'foreign'
                with self.assertRaises(self.c.ContractError): self.c.paired_readout(l,r,'JPA_OFF_ON')

    def test_jpa_pair_rejects_nonlinearity_unpaired_calibration_or_order(self):
        for field, value in [('saturated',True),('power_broadened',True),
                             ('gain_noise_revision','gain-off-v1'),('amplifier_state','off')]:
            l,r = self.pair(); r[field] = value
            with self.assertRaises(self.c.ContractError): self.c.paired_readout(l,r,'JPA_OFF_ON')
        l,r = self.pair()
        self.assertEqual(self.c.paired_readout(l,r,'JPA_OFF_ON')['snr_improvement_dB'],5.0)
        with self.assertRaises(self.c.ContractError): self.c.paired_readout(r,l,'JPA_OFF_ON')

    def reconfiguration(self):
        b = {'varactor_ids':['shared-freq','shared-match'],'material':'STO','device_id':'sqd',
             'device_kind':'SQD','module_revision':'module-v1','circuit_revision':'circuit-v1',
             'calibration_revision':'cal-v1','history_revision':'history-v7',
             'series_capacitor_present':False,'synthetic_only':True}
        a = self.copy(b); a.update(device_id='dqd',device_kind='DQD',module_revision='module-v2',
                                  circuit_revision='circuit-v2',calibration_revision='cal-v2',
                                  series_capacitor_present=True)
        return b,a

    def test_reconfiguration_preserves_specimen_but_invalidates_changed_module(self):
        b,a = self.reconfiguration()
        out = self.c.reconfiguration(b,a)
        self.assertIs(out['same_varactors_preserved'],True)
        self.assertIs(out['physical_reassembly_executed'],False)
        for field in ['device_id','module_revision','circuit_revision','calibration_revision']:
            with self.subTest(field=field):
                b,a = self.reconfiguration(); a[field] = b[field]
                with self.assertRaises(self.c.ContractError): self.c.reconfiguration(b,a)

    def test_reconfiguration_rejects_swap_reset_and_missing_series_capacitor(self):
        for field,value in [('varactor_ids',['replacement-freq','replacement-match']),
                            ('material','KTO'),('history_revision','fresh-history'),
                            ('series_capacitor_present',False),('synthetic_only',False)]:
            b,a = self.reconfiguration(); a[field] = value
            with self.assertRaises(self.c.ContractError): self.c.reconfiguration(b,a)

    def test_numeric_nonfinite_boolean_and_units_rejected(self):
        for bad in [float('nan'),float('inf'),float('-inf'),True,'1',None]:
            for fn,args in [(self.c.reflection,(bad,0,50)),
                            (self.c.loss_bound,(bad,1e-12,1e6)),
                            (self.c.snr_from_power,(bad,1)),
                            (self.c.sensitivity,(bad,3,100,'e'))]:
                with self.subTest(fn=fn.__name__,bad=bad):
                    with self.assertRaises(self.c.ContractError): fn(*args)
        for unit in ['C','pF','Hz','',None]:
            with self.assertRaises(self.c.ContractError): self.c.sensitivity(1,3,100,unit)
        with self.assertRaises(self.c.ContractError): self.c.sensitivity(1,3,0,'e')
        with self.assertRaises(self.c.ContractError): self.c.sensitivity(1,3,100,'e',True)

    def test_nonpositive_derived_arithmetic_is_rejected(self):
        for fn,args in [(self.c.series_capacitance,(5e-324,5e-324)),
                        (self.c.sensitivity,(5e-324,0,2,'F')),
                        (self.c.snr_from_power,(5e-324,1e308))]:
            with self.subTest(fn=fn.__name__):
                with self.assertRaises(self.c.ContractError): fn(*args)

    def test_arithmetic_uses_independent_synthetic_values(self):
        self.assertAlmostEqual(self.c.series_capacitance(2e-12,6e-12),1.5e-12)
        self.assertAlmostEqual(self.c.snr_from_power(8,2)['dB'],6.020599913279624)
        self.assertAlmostEqual(self.c.sensitivity(4,0,2,'e')['value'],2.0)
        self.assertEqual(self.c.reflection(50,0,50)['magnitude'],0.0)
        self.assertIs(self.c.reflection(50,0,50)['phase_defined'],False)
        self.assertIs(self.c.loss_bound(1,1e-12,1e6)['intrinsic_loss_measured'],False)

    def test_stability_rejects_incomplete_or_reversed_time_data(self):
        raw = {'time_s':[0,2,4],'x':[0,1,2],'y':[0,0,0],
               'units':{'time':'s','quadrature':'dimensionless'},'synthetic_only':True}
        out = self.c.stability(raw)
        self.assertAlmostEqual(out['x_drift_per_s'],0.5)
        self.assertIs(out['no_drift_claimed'],False)
        self.assertIs(out['varactor_noise_absence_claimed'],False)
        for field,value in [('time_s',[0,2,2]),('time_s',[4,2,0]),('x',[0,1]),
                            ('y',[0,float('nan'),0]),('synthetic_only',False),
                            ('units',{'time':'ms','quadrature':'dimensionless'})]:
            bad=self.copy(raw);bad[field]=value
            with self.assertRaises(self.c.ContractError):self.c.stability(bad)

    def histories(self):
        f={'direction':'forward','history_id':'f-history','samples':[
           {'coordinate_id':'p1','minimum_magnitude':0.2},
           {'coordinate_id':'p2','minimum_magnitude':0.4}],'synthetic_only':True}
        r={'direction':'reverse','history_id':'r-history','samples':[
           {'coordinate_id':'p2','minimum_magnitude':0.3},
           {'coordinate_id':'p1','minimum_magnitude':0.1}],'synthetic_only':True}
        return f,r

    def test_hysteresis_aligns_coordinates_and_rejects_missing_history(self):
        f,r=self.histories();out=self.c.hysteresis(f,r)
        self.assertAlmostEqual(out['differences']['p1'],0.1)
        self.assertAlmostEqual(out['differences']['p2'],0.1)
        for field,value in [('direction','forward'),('history_id','f-history'),('synthetic_only',False)]:
            f,r=self.histories();r[field]=value
            with self.assertRaises(self.c.ContractError):self.c.hysteresis(f,r)
        f,r=self.histories();r['samples'][0]['coordinate_id']='foreign'
        with self.assertRaises(self.c.ContractError):self.c.hysteresis(f,r)
        f,r=self.histories();r['samples'][0]['coordinate_id']='p1'
        with self.assertRaises(self.c.ContractError):self.c.hysteresis(f,r)


    def test_material_comparison_uses_distinct_consistent_constituents(self):
        for entry in ['FULL','PREPARED']:
            fid='STO_KTO_COMPARISON:'+entry+':GOOD'
            f=self.c.fixture(fid)
            raw_receipt=next(r for r in f['receipts'].values() if r['operation_id']=='ACQUIRE_RECORDS')
            constituents=raw_receipt['payload']['raw']['comparison_constituents']
            self.assertEqual(set(constituents),{'STO','KTO'})
            self.assertNotEqual(constituents['STO']['sample_id'],constituents['KTO']['sample_id'])
            self.assertNotEqual(constituents['STO']['material_revision'],constituents['KTO']['material_revision'])
            self.assertTrue(f['context']['sample_id'].endswith(':comparison_bundle'))
            for material,record in constituents.items():
                self.assertEqual(record['material'],material)
                self.assertNotEqual(record['sample_id'],f['context']['sample_id'])
            if entry=='FULL':
                seen=set()
                for receipt in f['receipts'].values():
                    payload=receipt['payload']
                    if 'constituent' in payload:
                        record=payload['constituent'];seen.add(record['material'])
                        self.assertEqual(record,constituents[record['material']])
                        self.assertEqual(payload['comparison_bundle_id'],f['context']['sample_id'])
                self.assertEqual(seen,{'STO','KTO'})
            else:
                ancestry=next(r for r in f['receipts'].values() if r['operation_id']=='VERIFY_ANCESTRY')
                self.assertEqual(ancestry['payload']['comparison_constituents'],constituents)
            bad=self.copy(f['receipts'])
            raw=next(r for r in bad.values() if r['operation_id']=='ACQUIRE_RECORDS')
            raw['payload']['raw']['comparison_constituents']['KTO']['sample_id']=constituents['STO']['sample_id']
            raw['payload']['raw_hash']=self.c.digest(raw['payload']['raw'])
            with self.assertRaises(self.c.ContractError):self.c.evaluate(f['events'],bad,fid)

    def test_field_and_dual_tuning_retain_sqd_circuit_scope(self):
        branches={x['id']:x for x in read('branches.json')['branches']}
        for bid in ['MAGNETIC_FIELD_RESPONSE','DUAL_FREQUENCY_MATCHING']:
            with self.subTest(branch=bid):
                branch=branches[bid]
                self.assertIn('CNT_SQD_FABRICATION',branch['full_preparation_branch_ids'])
                self.assertIn('REQUEST_SQD_BASELINE',branch['route_operation_ids'])
                self.assertIn('VERIFY_DEVICE_BASELINE',branch['route_operation_ids'])
                self.assertNotIn('REQUEST_FIXED_LOAD_SCAN',branch['route_operation_ids'])
                self.assertIn('complex reflection and phase',branch['acquisition_mode'])
                self.assertIn('no sideband/charge-sensitivity credit',branch['acquisition_mode'])
                f=self.c.fixture(bid+':FULL:GOOD')
                operations=[e['operation_id'] for e in f['events']]
                for op in ['REQUEST_NANOTUBE_GROWTH','VERIFY_NANOTUBE_GROWTH','VERIFY_SECOND_LITHOGRAPHY']:
                    self.assertIn(op,operations)
                self.assertNotIn('ANALYZE_SQD_SENSITIVITY',operations)
                self.assertLess(operations.index('VERIFY_DEVICE_BASELINE'),operations.index('ACQUIRE_RECORDS'))

    def test_assembly_consumes_prepared_ancestry_without_fabrication_credit(self):
        f=self.c.fixture('MODULE_ASSEMBLY:FULL:GOOD')
        operations=[e['operation_id'] for e in f['events']]
        self.assertIn('RECEIVE_PREPARED',operations)
        self.assertIn('VERIFY_ANCESTRY',operations)
        self.assertLess(operations.index('VERIFY_ANCESTRY'),operations.index('REQUEST_DIE_ATTACH'))
        for r in f['receipts'].values():
            if 'fabrication_credit' in r['payload']:
                self.assertIs(r['payload']['fabrication_credit'],False)


class IndependentCircuitCardNegatives(unittest.TestCase):
    setUpClass = IndependentRuntimeNegatives.__dict__['setUpClass']
    setUp = IndependentRuntimeNegatives.setUp
    def test_branch_cards_reject_wrong_family_and_field_substitution(self):
        cards = {x['id']:x for x in read('circuit_family_cards.json')['cards']}
        for family, card in cards.items():
            out = self.c.circuit_card(card, family)
            self.assertIs(out['hardware_qualified'], False)
            self.assertIs(out['physical_topology_verified'], False)
            for wrong in set(cards) - {family}:
                with self.assertRaises(self.c.ContractError): self.c.circuit_card(cards[wrong], family)
        for field,value in [('model_inductor_nH',320),
                            ('substrate_class',cards['SQD']['substrate_class']),
                            ('bias_tee',cards['SQD']['bias_tee']),
                            ('matching_series_capacitor_pF',None),
                            ('JPA_incorporated',False)]:
            bad=self.copy(cards['DQD']);bad[field]=value
            with self.assertRaises(self.c.ContractError):self.c.circuit_card(bad,'DQD')
        self.assertEqual(cards['SQD']['bias_tee'], {'coupling_capacitor_pF':100,'resistor_ohm':1000,'inductor_nH':470})
        self.assertEqual(cards['DQD']['bias_tee'], {'coupling_capacitor_pF':220,'resistor_ohm':10000,'inductor_nH':470})
        self.assertEqual(cards['SQD']['inductor_part_code'],'0805CS-331')
        self.assertEqual(cards['SQD']['model_inductor_nH'],320)
        self.assertIsNone(cards['SQD']['manufacturer_nominal_inductor_nH'])

if __name__ == '__main__':
    unittest.main()
