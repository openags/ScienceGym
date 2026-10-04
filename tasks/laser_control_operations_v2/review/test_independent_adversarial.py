"""Original independent design checks; offline only, no source-media dependencies."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / name).read_text())


class IndependentDesignTests(unittest.TestCase):
    def test_exact_fifteen_design_routes(self):
        rows = read('branches.json')['branches']
        self.assertEqual({row['id'] for row in rows}, {
            'SYSTEM_DESIGN', 'PIC_DESIGN_FDTD', 'PIC_FABRICATION',
            'PCB_PACKAGING', 'ARCHITECTURE_COMPARISON', 'GAIN_SENSITIVITY',
            'ELECTRONIC_NOISE_BUDGET', 'WAVEGUIDE_TRN', 'RING_TRN_FEM',
            'OPEN_LOOP_CHARACTERIZATION', 'DFB1_STABILIZATION',
            'DFB2_STABILIZATION', 'DFB3_STABILIZATION', 'SIN_NUMERICAL_EXAMPLE',
            'CAVITY_TECHNOLOGY_COMPARISON'})
        self.assertEqual(len(rows), 15)
        for row in rows:
            self.assertIs(row['design_covered'], True)
            self.assertIs(row['physical_executed'], False)
            self.assertIs(row['numerical_executed'], False)
            self.assertTrue(row['required_inputs'])
            self.assertTrue(row['required_outputs'])
            self.assertTrue(row['interpretation_limit'])

    def test_entire_scientific_inventory_is_accounted(self):
        c = read('coverage_matrix.json')
        self.assertEqual(set(c['main_figures']), {f'FIG{i}' for i in range(1, 7)})
        self.assertEqual(set(c['supplementary_notes']), {f'SI_N{i}' for i in range(1, 7)})
        self.assertEqual(set(c['supplementary_figures']), {f'SI_F{i}' for i in range(1, 9)})
        self.assertEqual(set(c['supplementary_tables']), {'SI_T1', 'SI_T2'})
        self.assertEqual(c['supplementary_pages_read'], 17)
        self.assertFalse(c['whole_paper_execution_complete'])

    def test_all_operations_bound_and_non_actuating(self):
        ops = read('operations.json')['operations']
        assets = read('asset_binding_plan.json')['scene_assets']
        operation_ids = {op['id'] for op in ops}
        self.assertEqual(len(operation_ids), len(ops))
        self.assertEqual(operation_ids, {op for a in assets for op in a['bind_operation_ids']})
        self.assertEqual(operation_ids, set(read('agent_visible.json')['allowed_operations']))
        asset_ids = {a['asset_id'] for a in assets}
        for op in ops:
            self.assertFalse(op['device_command_implemented'])
            self.assertFalse(op['physical_execution_authority'])
            self.assertTrue(set(op['asset_ids']) <= asset_ids)

    def test_full_preparation_is_not_shortcut_intake(self):
        routes = {r['id']: r for r in read('preparation_routes.json')['routes']}
        full, intake = routes['FULL_PREPARATION'], routes['PREPARED_INTAKE']
        for op in ['FREEZE_DESIGN', 'REQUEST_PIC_FABRICATION', 'VERIFY_PIC', 'REQUEST_PCB_ASSEMBLY']:
            self.assertIn(op, full['sequence'])
            self.assertNotIn(op, intake['sequence'])
        self.assertEqual(set(intake['does_not_credit']), {'PIC_DESIGN_FDTD', 'PIC_FABRICATION', 'PCB_PACKAGING'})

    def test_actor_and_evaluator_are_explicitly_separated(self):
        actor = read('agent_visible.json')
        inputs = read('episode_input_contract.json')
        self.assertEqual(inputs['actor_fields'], ['event_id', 'operation_id', 'evidence_id'])
        for flag in ['source_outcomes_exposed', 'can_declare_measurement',
                     'can_declare_service_qualification', 'can_supply_physical_observation',
                     'physical_implementation']:
            self.assertIs(actor[flag], False)
        self.assertIs(read('evaluator_reference.json')['actor_access'], False)
        self.assertEqual(read('source_outcomes.json')['visibility'], 'evaluator_reference_only')
        self.assertFalse(read('source_outcomes.json')['completion_thresholds'])

    def test_command_and_state_have_separate_roles(self):
        l = read('lifecycle_contract.json')
        self.assertTrue(set(l['commands_are_not_state_evidence']).isdisjoint(l['independent_state_checks']))
        self.assertEqual(l['safe_undock_order'], ['REQUEST_SAFE_OFF', 'VERIFY_SAFE_OFF', 'UNDOCK_PACKAGE'])
        phases = l['measurement_phases']
        for request, verify in [('REQUEST_ALIGNMENT', 'VERIFY_ALIGNMENT'), ('REQUEST_LOCK', 'VERIFY_LOCK')]:
            self.assertLess(phases.index(request), phases.index(verify))
        closure = l['closure_phases']
        self.assertLess(closure.index('VERIFY_SAFE_OFF'), closure.index('UNDOCK_PACKAGE'))
        self.assertIn('quarantine', l['damage'].lower())
        self.assertIn('contained', l['interrupted_active_attempt'])

    def test_sin_not_physical_and_density_anomaly_is_preserved(self):
        b = next(x for x in read('branches.json')['branches'] if x['id'] == 'SIN_NUMERICAL_EXAMPLE')
        self.assertEqual(b['execution_class'], 'design_only')
        self.assertFalse(b['physical_executed'])
        self.assertFalse(b['numerical_executed'])
        self.assertIn('density', ' '.join(b['required_inputs']))
        card = next(x for x in read('material_cards.json')['cards'] if x['id'] == 'SILICON_NITRIDE_MODEL_ONLY')
        self.assertEqual(card['printed_density_kg_m3'], 329)
        self.assertFalse(card['physical_sample_exists_in_task'])

    def test_dimensions_and_process_label_not_conflated(self):
        card = next(x for x in read('material_cards.json')['cards'] if x['id'] == 'SILICON_PIC')
        self.assertIn('100 nm', card['process_label'])
        self.assertEqual(card['depicted_silicon_thickness_nm'], 220)
        self.assertAlmostEqual(card['pic_footprint_mm'][0] * card['pic_footprint_mm'][1], .456)
        self.assertFalse(card['fabrication_qualified'])

    def test_final_version_and_independent_channels(self):
        conflicts = read('source_conflicts.json')['items']
        final = next(x for x in conflicts if x['id'] == 'FINAL_VERSION_AUTHORITY')
        self.assertIn('comb', final['handling'])
        analyses = read('analysis_contracts.json')
        self.assertIn('cannot independently prove absolute', analyses['in_loop_interpretation'])
        self.assertFalse(analyses['physical_results_computed'])
        source = read('source_outcomes.json')
        self.assertIs(source['final_version_only'], True)
        self.assertEqual([x['id'] for x in source['dfb_results']], ['DFB1', 'DFB2', 'DFB3'])
        self.assertEqual([x['rms_locked_Hz'] for x in source['dfb_results']], [400300., 240300., 140100.])

    def test_source_analysis_context_and_sin_table_are_reference_only(self):
        source = read('source_outcomes.json')
        context = source['analysis_context']
        self.assertEqual(context['independent_RBW_Hz'], 200)
        self.assertEqual(context['in_loop_RBW_Hz'], {'DFB1':51, 'DFB2':51, 'DFB3':103})
        self.assertEqual(context['final_spectrum_lower_extent_Hz'], 500)
        self.assertIn('per-laser loop bandwidth', context['RMS_band'])
        params = source['sin_model_parameters']
        for field, value in {'laser_power_uW':100, 'laser_FM_gain_MHz_per_mA':500,
                             'laser_FM_response_b':2, 'laser_FM_response_fc_MHz':1.6,
                             'input_current_ASD_pA_per_sqrt_Hz':3.2,
                             'current_driver_gain_mA_per_V':2, 'current_driver_BW_kHz':10,
                             'servo_gain_kohm':125, 'servo_BW_MHz':1,
                             'density_kg_m3_literal':329}.items():
            self.assertEqual(params[field], value)
        self.assertFalse(params['executable_settings'])
        power = next(x for x in read('source_conflicts.json')['items'] if x['id'] == 'BIAS_POWER_SCOPE')
        self.assertIn('total system power', power['handling'])

    def test_release_never_claims_physical_execution(self):
        b = read('RELEASE_BOUNDARY.json')
        for key in ['whole_paper_execution_complete', 'real_actuation_implemented',
                    'scientific_simulation_run', 'numerical_reproduction_run',
                    'source_complete_for_robot_execution', 'publisher_assets_included',
                    'author_code_included', 'source_raw_dataset_included',
                    'qualifies_for_full_paper_execution_count']:
            self.assertIs(b[key], False)




"""Independent adversarial tests against the synthetic contract; no hardware use."""
from copy import deepcopy
import importlib.util
from decimal import Decimal, localcontext
import random
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('laser_contract_independent', ROOT / 'tests' / 'contract.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def receipt(bundle, operation):
    return next(r for r in bundle['receipts'].values() if r['operation_id'] == operation)


class IndependentRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.key = 'DFB1:FULL:V0:OK'
        self.b = c.fixture(self.key)

    def reject(self, events=None, registry=None, key=None):
        with self.assertRaises(c.ContractError):
            c.evaluate(self.b['events'] if events is None else events,
                       self.b['receipts'] if registry is None else registry,
                       self.key if key is None else key)

    def test_all_fifty_five_worlds_have_truthful_terminal_classes(self):
        self.assertEqual(len(c.FIXTURE_IDS), 55)
        for key in c.FIXTURE_IDS:
            with self.subTest(key=key):
                b = c.fixture(key)
                result = c.evaluate(b['events'], b['receipts'], key)
                self.assertIs(result['contract_passed'], True)
                self.assertIs(result['synthetic_only'], True)
                self.assertIs(result['physical_execution'], False)
                self.assertIs(result['scientific_reproduction'], False)
                self.assertEqual(result['analysis'] is None, key == 'HOLD' or key.endswith('LOCK_LOSS'))
                self.assertEqual(result['design_route_receipts_checked'], ':FULL:' in key)
                expected = ('qualification_hold' if key == 'HOLD' else
                            'quarantined' if key.endswith('DAMAGED') else
                            'lock_loss_safe_closed' if key.endswith('LOCK_LOSS') else 'stored')
                self.assertEqual(result['closure'], expected)

    def test_every_configuration_cannot_replay_as_every_other(self):
        bundles = {key: c.fixture(key) for key in c.FIXTURE_IDS}
        for target in c.FIXTURE_IDS:
            for attacker in c.FIXTURE_IDS:
                if attacker == target:
                    continue
                with self.subTest(attacker=attacker, target=target):
                    with self.assertRaises(c.ContractError):
                        c.evaluate(bundles[attacker]['events'], bundles[target]['receipts'], target)

    def test_registry_from_every_other_configuration_is_rejected(self):
        for key in c.FIXTURE_IDS:
            if key != self.key:
                with self.subTest(key=key):
                    self.reject(registry=c.fixture(key)['receipts'])

    def test_actor_claims_and_forged_ids_are_rejected(self):
        for field in ['measurement', 'success', 'safe', 'lock_status', 'PSD', 'gain',
                      'source_outcome', 'qualification', 'raw_hash', 'fixture_id', 'result']:
            events = deepcopy(self.b['events'])
            events[0][field] = True
            with self.subTest(field=field): self.reject(events=events)
        for field in ['event_id', 'operation_id', 'evidence_id']:
            for bad in [None, True, 1, 1.0, [], {}, '', 'forged', float('nan')]:
                events = deepcopy(self.b['events'])
                events[0][field] = bad
                with self.subTest(field=field, bad=repr(bad)): self.reject(events=events)

    def test_every_missing_duplicated_or_swapped_event_is_rejected(self):
        base = self.b['events']
        for i in range(len(base)):
            with self.subTest(index=i, kind='missing'): self.reject(events=base[:i]+base[i+1:])
            with self.subTest(index=i, kind='duplicated'): self.reject(events=base[:i]+[base[i]]+base[i:])
        for i in range(len(base)-1):
            events = deepcopy(base)
            events[i], events[i+1] = events[i+1], events[i]
            with self.subTest(index=i, kind='swap'): self.reject(events=events)

    def test_request_acknowledgements_cannot_prove_state(self):
        pairs = [('REQUEST_PIC_FABRICATION', 'VERIFY_PIC'),
                 ('REQUEST_PCB_ASSEMBLY', 'VERIFY_PACKAGING'),
                 ('REQUEST_ALIGNMENT', 'VERIFY_ALIGNMENT'),
                 ('REQUEST_LOCK', 'VERIFY_LOCK'), ('REQUEST_SAFE_OFF', 'VERIFY_SAFE_OFF')]
        for command, state in pairs:
            registry = deepcopy(self.b['receipts'])
            local = {'receipts': registry}
            receipt(local, state)['payload'] = deepcopy(receipt(self.b, command)['payload'])
            with self.subTest(command=command, state=state): self.reject(registry=registry)

    def test_registry_rehashing_cannot_launder_modified_evidence(self):
        mutations = [('VERIFY_SAFE_OFF', 'optical_isolated', False),
                     ('VERIFY_SAFE_OFF', 'electrical_isolated', 1),
                     ('VERIFY_LOCK', 'lock_observed', False),
                     ('VERIFY_LOCK', 'saturation', True),
                     ('VERIFY_REFERENCE_CHAIN', 'ceo_locked', False),
                     ('ARCHIVE', 'all_attempts_retained', False),
                     ('CALIBRATE_DISCRIMINATOR', 'gain_V_per_Hz', float('nan'))]
        for op, field, bad in mutations:
            registry = deepcopy(self.b['receipts'])
            receipt({'receipts': registry}, op)['payload'][field] = bad
            previous = 'GENESIS'
            for r in registry.values():
                r['previous_hash'] = previous
                if type(bad) is float and math.isnan(bad):
                    break
                r['receipt_hash'] = c.digest({k:v for k,v in r.items() if k != 'receipt_hash'})
                previous = r['receipt_hash']
            with self.subTest(operation=op, field=field): self.reject(registry=registry)

    def test_pinned_registry_rejects_type_coercion_and_extra_inventory(self):
        for val in [1, 1.0, 'true', None, [], float('inf')]:
            registry = deepcopy(self.b['receipts'])
            receipt({'receipts': registry}, 'VERIFY_SAFE_OFF')['payload']['optical_isolated'] = val
            with self.subTest(value=repr(val)): self.reject(registry=registry)
        registry = deepcopy(self.b['receipts']); registry['unreferenced'] = {'safe': True}
        self.reject(registry=registry)
        for bad in [None, [], 1, True, 'registry']:
            with self.subTest(registry=repr(bad)):
                with self.assertRaises(c.ContractError): c.evaluate(self.b['events'], bad, self.key)

    def test_in_loop_record_cannot_become_independent_metrology(self):
        registry = deepcopy(self.b['receipts'])
        local = {'receipts': registry}
        receipt(local, 'ACQUIRE_HETERODYNE')['payload']['spectrum'] = deepcopy(receipt(local, 'ACQUIRE_IN_LOOP')['payload']['spectrum'])
        self.reject(registry=registry)
        for field in ['method', 'spectrum']:
            registry = deepcopy(self.b['receipts'])
            receipt({'receipts': registry}, 'ACQUIRE_HETERODYNE')['payload'][field] = 'delayed_self_heterodyne'
            self.reject(registry=registry)

    def test_python_container_coercion_cannot_preserve_registry_hash(self):
        class DictSubclass(dict): pass
        class ListSubclass(list): pass
        for replacement in [tuple, ListSubclass]:
            registry = deepcopy(self.b['receipts'])
            r = receipt({'receipts':registry}, 'ACQUIRE_FREE_RUNNING')['payload']['spectrum']
            r['frequency_Hz'] = replacement(r['frequency_Hz'])
            with self.subTest(replacement=replacement.__name__): self.reject(registry=registry)
        registry = deepcopy(self.b['receipts'])
        first = next(iter(registry))
        registry[first] = DictSubclass(registry[first])
        self.reject(registry=registry)
        for value in [{1:'numeric key'}, {float('nan'):'NaN key'}, {'tuple':(1,2)}, {'set':{1,2}}]:
            with self.subTest(value=repr(value)), self.assertRaises(c.ContractError): c.canonical(value)
        cycle = {}; cycle['cycle'] = cycle
        with self.assertRaises(c.ContractError): c.canonical(cycle)

    def test_spectra_preserve_servo_bump_and_signed_gain(self):
        for key in ['DFB1:FULL:V0:OK', 'DFB2:PREPARED:V1:OK', 'DFB3:FULL:V2:OK']:
            b = c.fixture(key)
            result = c.evaluate(b['events'], b['receipts'], key)['analysis']
            self.assertTrue(any(x < 0 for x in result['suppression_dB']))
            self.assertGreater(result['independent_rms_locked_Hz'], result['in_loop_relative_rms_Hz'])
            self.assertEqual(result['missing_tails'], 'not estimated')
            self.assertFalse(result['physical_measurement'])
        self.assertEqual(c.voltage_psd_to_frequency([4, 16], -2), [1, 4])


class IndependentArithmeticTests(unittest.TestCase):
    def test_constant_and_linear_psd_rms_with_partial_bounds(self):
        self.assertAlmostEqual(c.rms_frequency([1,2,3], [4,4,4], 1,3), math.sqrt(8))
        self.assertAlmostEqual(c.rms_frequency([1,2,3], [2,4,6], 1.25,2.75), math.sqrt(2.75**2-1.25**2))

    def test_beta_integrates_psd_area_not_excess_above_line(self):
        beta = 8*math.log(2)/math.pi**2
        # S = 2 beta intersects beta f at f=2.  Only [1,2] contributes.
        self.assertAlmostEqual(c.beta_linewidth([1,2,3], [2*beta]*3, 1,3), math.sqrt(8*math.log(2)*2*beta))
        self.assertEqual(c.beta_linewidth([1,2,3], [.1,.1,.1], 1,3), 0)
        self.assertAlmostEqual(c.beta_linewidth([1,2,3], [4,4,4], 1,3), math.sqrt(8*math.log(2)*8))

    def test_randomized_piecewise_integration_matches_decimal_oracle(self):
        rng = random.Random(271828)
        with localcontext() as ctx:
            ctx.prec = 60
            B = Decimal(str(8*math.log(2)/math.pi**2))
            for trial in range(150):
                f = [1.,2.,4.,8.,16.]
                s = [rng.uniform(0,20) for _ in f]
                area = Decimal(0)
                beta_area = Decimal(0)
                for i in range(len(f)-1):
                    a,b,u,v = map(lambda x:Decimal(str(x)), (f[i],f[i+1],s[i],s[i+1]))
                    area += (b-a)*(u+v)/2
                    da,db = u-B*a,v-B*b
                    if da <= 0 and db <= 0:
                        continue
                    l,r = a,b
                    if da*db < 0:
                        root = a+(b-a)*da/(da-db)
                        if da < 0: l=root
                        else: r=root
                    slope = (v-u)/(b-a)
                    yl,yr = u+slope*(l-a),u+slope*(r-a)
                    beta_area += (r-l)*(yl+yr)/2
                with self.subTest(trial=trial):
                    self.assertAlmostEqual(c.rms_frequency(f,s,1,16),float(area.sqrt()),places=12)
                    self.assertAlmostEqual(c.beta_linewidth(f,s,1,16),float(beta_area.sqrt())*math.sqrt(8*math.log(2)),places=11)

    def test_suppression_keeps_sign_and_avoids_ratio_overflow(self):
        self.assertEqual(c.suppression_dB([10,1,1e300], [1,10,1e-300]), [10,-10,6000])

    def test_invalid_arrays_and_support_fail_closed(self):
        pairs = [(None,[1,2,3]), ([1,2,3],None), ((1,2,3),[1,2,3]),
                 ([1,2],[1,2]), ([1,2,3],[1,2]), ([1,1,3],[1,2,3]),
                 ([1,3,2],[1,2,3]), ([0,1,2],[1,2,3]),
                 ([True,2,3],[1,2,3]), ([1,'2',3],[1,2,3]),
                 ([1,2,3],[1,True,3]), ([1,2,3],[1,-1,3])]
        for bad in [float('nan'),float('inf'),float('-inf')]:
            pairs.extend([([1,2,bad],[1,2,3]), ([1,2,3],[1,2,bad])])
        for f,s in pairs:
            with self.subTest(f=repr(f),s=repr(s)), self.assertRaises(c.ContractError): c.validate_arrays(f,s)
        for low,high in [(0,3),(1,4),(2,2),(3,1),(True,3),(1,float('inf'))]:
            for function in [c.rms_frequency,c.beta_linewidth]:
                with self.subTest(function=function.__name__,low=low,high=high), self.assertRaises(c.ContractError): function([1,2,3],[1,2,3],low,high)

    def test_gain_invalid_and_nonfinite_conversion_rejected(self):
        for gain in [0,True,'1',float('nan'),float('inf'),1e-300,1e300]:
            with self.subTest(gain=repr(gain)), self.assertRaises(c.ContractError): c.voltage_psd_to_frequency([1,2,3],gain)
        with self.assertRaises(c.ContractError): c.voltage_psd_to_frequency([1e308],1e-7)

    def test_huge_integer_reports_contract_error(self):
        with self.assertRaises(c.ContractError): c.validate_arrays([1,2,10**400],[1,1,1])

    def test_large_finite_unity_crossing_is_not_biased_by_overflow(self):
        self.assertEqual(c.unity_crossings([1,2,3],[1e308,1,1],[1,1e308,1e308]), [1.5])

    def test_all_unity_directions_and_plateaus_are_explicit(self):
        f = [1,2,3,4]
        self.assertEqual(c.unity_crossings(f,[2,1,2,1],[1,2,1,2]), [1.5,2.5,3.5])
        details = c.unity_crossing_details(f,[2,1,2,1],[1,2,1,2])
        self.assertEqual([x['direction'] for x in details], ['downward','upward','downward'])
        self.assertEqual(c.unity_crossing_details(f,[2,1,1,0],[1,1,1,1]),
                         [{'kind':'unity_plateau','support_Hz':[2.,3.],'direction':'ambiguous'}])
        self.assertEqual(c.unity_crossings(f,[2,1,1,0],[1,1,1,1]), [2.,3.])
        touch = c.unity_crossing_details([1,2,3],[2,1,2],[1,1,1])
        self.assertEqual(touch, [{'kind':'point','frequency_Hz':2.,'direction':'touch'}])
        endpoint = c.unity_crossing_details([1,2,3],[1,2,3],[1,1,1])
        self.assertEqual(endpoint, [{'kind':'point','frequency_Hz':1.,'direction':'endpoint'}])

    def test_beta_result_cannot_be_nonfinite(self):
        try:
            value = c.beta_linewidth([1,2,3], [4e307]*3, 1,3)
        except c.ContractError:
            return
        self.assertTrue(math.isfinite(value))
        self.assertAlmostEqual(value / math.sqrt(8e307), math.sqrt(8*math.log(2)))


if __name__ == '__main__': unittest.main()
