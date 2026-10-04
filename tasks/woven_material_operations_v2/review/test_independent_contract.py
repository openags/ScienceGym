"""Independent finite-contract review with declarative and Fraction oracles.

Author fixture() is used only to obtain valid finite input, never as the oracle
for inventory, terminal semantics, physical boundaries or arithmetic values.
"""
from copy import deepcopy
from fractions import Fraction
import importlib.util
import json
import math
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('woven_review_contract',ROOT/'tests/contract.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
PHYSICAL=('TENSION_BCC','TENSION_CUBIC','TENSION_OCTAHEDRON','TENSION_DIAMOND','CYCLIC_BCC_TENSION','CYCLIC_BCC_COMPRESSION','CYCLIC_OCTAHEDRON_COMPRESSION','GRADED_RADIUS','GRADED_TURNS')
MODES=('OK','DAMAGED','DATA_HOLD','ISOLATION_HOLD')
MODELS=('LINEAR_HOMOGENIZATION','MATERIAL_CHARACTERIZATION','BEAM_CONTINUUM_COMPARISON','NONLINEAR_BEAM_MODEL','FAILURE_VARIABILITY','CURVATURE_CONTACT','PATTERNED_DEFORMATION_MODEL','PATTERNED_FAILURE_MODEL')
EXPECTED_IDS={f'{b}:{r}:{m}' for b in PHYSICAL for r in ('FULL','PREPARED') for m in MODES}
EXPECTED_IDS|={f'PROGRAMMED_FAILURE_EXPERIMENT:{r}:{m}' for r in ('PLASMA_FIRST','COAT_FIRST','PREPARED') for m in MODES}
EXPECTED_IDS|={'MODEL:'+b for b in MODELS}
EXPECTED_IDS|={'HOLD:'+b for b in ('QUALIFICATION','TETRAKAIDECAHEDRON','CUBIC_CONNECTIVITY','CALIBRATION')}
def read(name):return json.loads((ROOT/name).read_text())
def evaluate(f):return c.evaluate(f['events'],f['receipts'],f['fixture_id'])
def by_op(f,op):return next(r for r in f['receipts'].values() if r['operation_id']==op)

class NumericOracles(unittest.TestCase):
    def tensile(self,**kw):
        args=dict(time=[0,1,2,3],displacement=[0,1,2,3],force=[0,2,4,6],area=2,height=4,relative_density=.5,solid_density=10,solid_modulus=8,fit_indices=[0,1,2,3])
        args.update(kw);return c.reduce_tension(**args)
    def test_tension_closed_form(self):
        r=self.tensile()
        expected={'strain':[0,.25,.5,.75],'stretch':[1,1.25,1.5,1.75],'stress_Pa':[0,1,2,3],'fit_modulus_Pa':4,'loading_work_J_m3':1.125,'specific_loading_work_J_kg':.225,'modulus_per_density_Pa_m3_kg':.8,'relative_specific_modulus':1,'source_figure_specific_modulus_m3_kg':.1}
        for key,value in expected.items():
            with self.subTest(key=key):self.assertEqual(r[key],value)
        self.assertEqual(r['energy_kind'],'monotonic_loading_work_not_hysteresis_loss')
    def test_nonzero_origin_and_fit_subset_fraction_oracle(self):
        r=self.tensile(displacement=[1,2,4,6],force=[5,8,14,30],area=2,height=4,fit_indices=[0,1,2])
        x=[Fraction(v,4) for v in [1,2,4,6]];y=[Fraction(v,2) for v in [5,8,14,30]]
        work=sum((b-a)*(u+v)/2 for a,b,u,v in zip(x,x[1:],y,y[1:]))
        self.assertAlmostEqual(r['loading_work_J_m3'],float(work));self.assertAlmostEqual(r['fit_modulus_Pa'],6);self.assertEqual(r['support_strain'],[.25,1.5])
    def test_reject_invalid_numeric_scalars(self):
        for key in ('area','height','relative_density','solid_density','solid_modulus'):
            for value in (0,-1,True,'1',None,float('nan'),float('inf'),10**500):
                with self.subTest(key=key,value=repr(value)[:30]):
                    with self.assertRaises(c.ContractError):self.tensile(**{key:value})
        with self.assertRaises(c.ContractError):self.tensile(relative_density=1.00001)
    def test_reject_bad_vectors(self):
        for change in [{'time':[0,1,1,3]},{'time':[1,0,2,3]},{'force':[0,1]},{'force':[0,True,2,3]},{'force':[0,-1,2,3]},{'displacement':[0,1,1,2]},{'displacement':[0,1,2,1]},{'displacement':[-1,0,1,2]},{'time':(0,1,2,3)},{'force':[0,float('nan'),2,3]},{'force':[0,float('inf'),2,3]}]:
            with self.subTest(change=change):
                with self.assertRaises(c.ContractError):self.tensile(**change)
    def test_reject_bad_fit_indices(self):
        for value in ([],[0],[0,0],[2,1],[0,4],[-1,1],[0,True],[0,1.0],(0,1),None):
            with self.subTest(value=value):
                with self.assertRaises(c.ContractError):self.tensile(fit_indices=value)
    def test_cycle_loss_independent_closed_polygon(self):
        for sign in (1,-1):
            d=[0,1,2,1,0,1,2,1,0];f=[0,3,4,1,0,2,3,1,0]
            r=c.cycle_loss(list(range(9)),[sign*x for x in d],[sign*x for x in f],2,4,[[0,2,4],[4,6,8]],0)
            self.assertEqual([v['loss_J_m3'] for v in r],[.25,.125]);self.assertEqual([v['relative_to_first'] for v in r],[1,.5]);self.assertEqual(r[0]['direction'],'tension' if sign==1 else 'compression')
    def test_cycle_explicit_closing_segment(self):
        d=[0,1,2,1,Fraction(1,10)];f=[0,3,4,1,Fraction(1,2)];x=d+[d[0]];y=f+[f[0]]
        expected=sum((b-a)*(u+v)/2 for a,b,u,v in zip(x,x[1:],y,y[1:]))
        r=c.cycle_loss([0,1,2,3,4],list(map(float,d)),list(map(float,f)),1,1,[[0,2,4]],.1)
        self.assertAlmostEqual(r[0]['loss_J_m3'],float(expected));self.assertTrue(r[0]['closure_segment_included'])
    def test_cycle_no_absolute_value_or_zero_baseline(self):
        for force in ([0,1,4,3,0],[0,2,4,2,0],[0,0,0,0,0]):
            with self.subTest(force=force):
                with self.assertRaises(c.ContractError):c.cycle_loss([0,1,2,3,4],[0,1,2,1,0],force,1,1,[[0,2,4]],0)
    def test_cycle_bad_segmentation_or_closure(self):
        for segments in ([],[[0,2,3]],[[1,2,4]],[[0,0,4]],[[0,4,2]],[[0,True,4]],[[0,2,4],[3,4,5]]):
            with self.subTest(segments=segments):
                with self.assertRaises(c.ContractError):c.cycle_loss([0,1,2,3,4],[0,1,2,1,0],[0,3,4,1,0],1,1,segments,0)
        with self.assertRaises(c.ContractError):c.cycle_loss([0,1,2,3,4],[0,1,2,1,.01],[0,3,4,1,0],1,1,[[0,2,4]],0)
        with self.assertRaises(c.ContractError):c.cycle_loss([0,1,2,3,4],[0,2,1,.5,0],[0,3,4,1,0],1,1,[[0,2,4]],0)
    def test_cycle_nonfinite_boolean_and_extreme_reject(self):
        for field,value in [('area',True),('height',0),('closure_tolerance',-1),('closure_tolerance',float('nan'))]:
            kwargs=dict(time=[0,1,2,3,4],displacement=[0,1,2,1,0],force=[0,3,4,1,0],area=1,height=1,cycles=[[0,2,4]],closure_tolerance=0);kwargs[field]=value
            with self.subTest(field=field):
                with self.assertRaises(c.ContractError):c.cycle_loss(**kwargs)
    def test_finite_overflow_rejects_not_inf(self):
        with self.assertRaises(c.ContractError):self.tensile(area=5e-324)
        with self.assertRaises(c.ContractError):c.integrate([0,1e308],[1e308,1e308])
    def test_representable_normalization_not_silent_zero(self):
        try:r=c.reduce_tension([0,1,2],[0,1,2],[0,1e300,2e300],1,1,1,1e308,1e308,[0,1,2])
        except c.ContractError:return
        expected=float(Fraction.from_float(1e300)/Fraction.from_float(1e308)/Fraction.from_float(1e308));self.assertGreater(expected,0);self.assertEqual(r['source_figure_specific_modulus_m3_kg'],expected)
    def test_representable_fit_not_silent_zero(self):
        try:r=c.reduce_tension([0,1,2,3],[0,1e-100,2e-100,1],[0,1e-250,2e-250,1],1,1,1,1,1,[0,1,2])
        except c.ContractError:return
        expected=float(Fraction.from_float(1e-250)/Fraction.from_float(1e-100));self.assertGreater(expected,0);self.assertTrue(math.isclose(r['fit_modulus_Pa'],expected,rel_tol=1e-12,abs_tol=0))
    def test_representable_integral_not_silent_zero(self):
        tiny=math.nextafter(0.0,1.0)
        try:actual=c.integrate([0,1e308],[tiny,tiny])
        except c.ContractError:return
        expected=float(Fraction.from_float(tiny)*Fraction.from_float(1e308));self.assertGreater(expected,0);self.assertEqual(actual,expected)

class RecordAndLifecycle(unittest.TestCase):
    def test_independent_fixture_inventory_and_all_outcomes(self):
        self.assertEqual(len(EXPECTED_IDS),96);self.assertEqual(set(c.FIXTURE_IDS),EXPECTED_IDS);self.assertEqual(len(c.FIXTURE_IDS),96)
        for fid in sorted(EXPECTED_IDS):
            with self.subTest(fid=fid):
                f=c.fixture(fid);r=evaluate(f);mode=fid.split(':')[-1];physical=not fid.startswith(('MODEL:','HOLD:'));complete=physical and mode in ('OK','DAMAGED')
                self.assertTrue(r['contract_passed']);self.assertEqual(r['synthetic_measurement_complete'],complete);self.assertEqual(r['sample_reusable'],physical and mode=='OK')
                self.assertEqual(r['synthetic_preparation_lineage_checked'],complete and ':PREPARED:' not in fid);self.assertEqual(r['numerical_metadata_contract_checked'],fid.startswith('MODEL:'))
                for key in ('physical_execution','numerical_solver_execution','scientific_reproduction','whole_paper_execution_complete','source_expected_outcome_used'):self.assertIs(r[key],False)
                terminal='HELD_CONTAINED' if fid.startswith('HOLD:') or mode=='ISOLATION_HOLD' else 'QUARANTINED_SYNTHETIC' if mode=='DAMAGED' else 'CLOSED_SYNTHETIC';self.assertEqual(r['terminal_state'],terminal)
    def test_safe_release_damage_and_data_hold(self):
        for fid in EXPECTED_IDS:
            f=c.fixture(fid);ops=[e['operation_id'] for e in f['events']];self.assertEqual(ops[-2:],['ARCHIVE','CLEAN_STORE'])
            if fid.endswith('ISOLATION_HOLD'):
                self.assertNotIn('VERIFY_SAFE_OFF',ops);self.assertNotIn('UNDOCK_SAMPLE',ops);self.assertEqual(by_op(f,'CLEAN_STORE')['payload']['disposition'],'contained')
            if fid.endswith('DAMAGED'):
                self.assertLess(ops.index('VERIFY_SAFE_OFF'),ops.index('UNDOCK_SAMPLE'));self.assertLess(ops.index('UNDOCK_SAMPLE'),ops.index('QUARANTINE'));self.assertFalse(by_op(f,'CLEAN_STORE')['payload']['reusable'])
            if fid.endswith('DATA_HOLD'):
                self.assertIn('HOLD_DATA',ops);self.assertNotIn('ANALYZE_CYCLES',ops);self.assertNotIn('ANALYZE_TENSION',ops);self.assertNotIn('COMPARE_RESPONSE',ops)
    def test_plasma_coating_partial_order_independent(self):
        for route in ('PLASMA_FIRST','COAT_FIRST'):
            for mode in MODES:
                f=c.fixture(f'PROGRAMMED_FAILURE_EXPERIMENT:{route}:{mode}');ops=[e['operation_id'] for e in f['events']]
                for before,after in [('VERIFY_PRINT','REQUEST_DEVELOP_RINSE'),('VERIFY_DEVELOP_RINSE','REQUEST_CPD'),('VERIFY_CPD','REQUEST_SUPPORT_REMOVAL'),('VERIFY_CPD','REQUEST_COATING'),('VERIFY_SUPPORT_REMOVAL','RECEIVE_SAMPLE'),('VERIFY_COATING','RECEIVE_SAMPLE')]:self.assertLess(ops.index(before),ops.index(after))
                first='VERIFY_SUPPORT_REMOVAL' if route=='PLASMA_FIRST' else 'VERIFY_COATING';later='REQUEST_COATING' if route=='PLASMA_FIRST' else 'REQUEST_SUPPORT_REMOVAL';self.assertLess(ops.index(first),ops.index(later))
                for op in ('REQUEST_SUPPORT_REMOVAL','VERIFY_SUPPORT_REMOVAL','REQUEST_COATING','VERIFY_COATING'):
                    payload=by_op(f,op)['payload'];self.assertEqual(payload['external_order_card'],f['context']['process_order_revision']);self.assertEqual(payload['source_plasma_coating_order'],'unspecified')
    def test_tetra_hold_is_not_bcc_cubic_hold(self):
        f=c.fixture('HOLD:TETRAKAIDECAHEDRON');self.assertEqual([e['operation_id'] for e in f['events']],['REGISTER_INPUTS','HOLD_GEOMETRY','ARCHIVE','CLEAN_STORE'])
        for b in ('TENSION_BCC','TENSION_CUBIC'):
            f=c.fixture(b+':FULL:OK');self.assertTrue(evaluate(f)['synthetic_measurement_complete']);self.assertIn('FREEZE_GRAPH',[e['operation_id'] for e in f['events']])
    def test_prepared_entry_cannot_claim_preparation(self):
        f=c.fixture('TENSION_BCC:PREPARED:OK');self.assertNotIn('REQUEST_PRINT',[e['operation_id'] for e in f['events']]);self.assertFalse(by_op(f,'RECEIVE_SAMPLE')['payload']['preparation_credit']);by_op(f,'RECEIVE_SAMPLE')['payload']['preparation_credit']=True
        with self.assertRaises(c.ContractError):evaluate(f)
    def test_each_context_field_single_or_coherent_forgery(self):
        original=c.fixture('TENSION_BCC:FULL:OK')
        for key in original['context']:
            for coherent in (False,True):
                f=deepcopy(original);rows=list(f['receipts'].values()) if coherent else [by_op(f,'ACQUIRE_TEST_DATA')]
                for row in rows:
                    row['context']=dict(row['context']);row['context'][key]='FORGED_OTHER_CONTEXT'
                with self.subTest(key=key,coherent=coherent):
                    with self.assertRaises(c.ContractError):evaluate(f)
    def test_payload_mutations_all_receipts(self):
        for fid in ('TENSION_BCC:FULL:OK','PROGRAMMED_FAILURE_EXPERIMENT:COAT_FIRST:DAMAGED','MODEL:NONLINEAR_BEAM_MODEL'):
            original=c.fixture(fid)
            for rid in original['receipts']:
                f=deepcopy(original);f['receipts'][rid]['payload']['synthetic_only']=False
                with self.subTest(fid=fid,rid=rid):
                    with self.assertRaises(c.ContractError):evaluate(f)
    def test_event_mutations_each_position(self):
        original=c.fixture('TENSION_CUBIC:FULL:OK')
        for i in range(len(original['events'])):
            for kind in ('missing','duplicate','injection','request_as_observation','reorder'):
                f=deepcopy(original)
                if kind=='missing':del f['events'][i]
                elif kind=='duplicate':f['events'].insert(i,deepcopy(f['events'][i]))
                elif kind=='injection':f['events'][i]['success']=True
                elif kind=='request_as_observation':f['events'][i]['operation_id']='REQUEST_PRINT';f['events'][i]['evidence_id']='FORGED'
                else:
                    j=(i+1)%len(f['events']);f['events'][i],f['events'][j]=f['events'][j],f['events'][i]
                with self.subTest(i=i,kind=kind):
                    with self.assertRaises(c.ContractError):evaluate(f)
    def test_cross_episode_route_and_model_replay(self):
        a=c.fixture('TENSION_BCC:FULL:OK')
        for other in ('TENSION_CUBIC:FULL:OK','TENSION_BCC:PREPARED:OK','TENSION_BCC:FULL:DAMAGED','MODEL:NONLINEAR_BEAM_MODEL'):
            b=c.fixture(other)
            with self.assertRaises(c.ContractError):c.evaluate(b['events'],b['receipts'],a['fixture_id'])
            with self.assertRaises(c.ContractError):c.evaluate(a['events'],b['receipts'],a['fixture_id'])
    def test_raw_hash_timebase_and_analysis_mutations(self):
        original=c.fixture('CYCLIC_BCC_COMPRESSION:FULL:OK')
        mutations=[lambda p:p.update(raw_hash='forged'),lambda p:p['raw'].update(timebase_revision='wrong'),lambda p:p['raw']['image_ids'].pop(),lambda p:p['raw']['force_N'].__setitem__(1,float('nan')),lambda p:p['raw']['force_N'].__setitem__(1,True),lambda p:p['raw'].update(synthetic_only=False)]
        for i,mutation in enumerate(mutations):
            f=deepcopy(original);mutation(by_op(f,'ACQUIRE_TEST_DATA')['payload'])
            with self.subTest(i=i):
                with self.assertRaises(c.ContractError):evaluate(f)
        f=deepcopy(original);by_op(f,'ANALYZE_CYCLES')['payload']['reduction'][0]['loss_J_m3']=0
        with self.assertRaises(c.ContractError):evaluate(f)
    def test_unsafe_release_and_fake_reuse_reject(self):
        for fid,op,key,value in [('TENSION_BCC:FULL:ISOLATION_HOLD','HOLD_ISOLATION','safe_release_observed',True),('TENSION_BCC:FULL:DAMAGED','CLEAN_STORE','reusable',True),('PROGRAMMED_FAILURE_EXPERIMENT:PLASMA_FIRST:OK','VERIFY_SUPPORT_REMOVAL','external_order_card',None)]:
            f=c.fixture(fid);by_op(f,op)['payload'][key]=value
            with self.subTest(fid=fid):
                with self.assertRaises(c.ContractError):evaluate(f)
    def test_unknown_fixture_wrong_type_and_noncanonical(self):
        for fid in ('',None,True,[],{},'TENSION_BCC:FULL:REAL','HOLD:TETRAKAIDECAHEDRON:OK'):
            with self.subTest(fid=fid):
                with self.assertRaises(c.ContractError):c.evaluate([],{},fid)
        for value in ({1:'not JSON'},set(),float('nan'),10**500):
            with self.assertRaises(c.ContractError):c.canonical(value)

class DeclarativeDesign(unittest.TestCase):
    def test_route_operation_coverage_and_no_execution(self):
        branches=read('branches.json')['branches'];ops=read('operations.json')['operations']
        self.assertEqual(len(branches),24);self.assertEqual(len({x['id'] for x in branches}),24);self.assertEqual(len(ops),48);self.assertEqual(len({x['id'] for x in ops}),48);ids={x['id'] for x in branches}
        for row in branches:self.assertTrue(row['design_covered']);self.assertFalse(row['physical_executed']);self.assertFalse(row['numerical_executed'])
        for row in ops:self.assertTrue(set(row['branch_ids'])<=ids);self.assertFalse(row['device_command_implemented']);self.assertFalse(row['physical_execution_authority'])
        cov=read('coverage_matrix.json');self.assertEqual(cov['supplementary_figures']['SI_F17'],'NONLINEAR_BEAM_MODEL');self.assertTrue(cov['whole_paper_design_accounted_for']);self.assertFalse(cov['whole_paper_execution_complete']);self.assertEqual(len(cov['main_figures']),5);self.assertEqual(len(cov['supplementary_notes']),5);self.assertEqual(len(cov['supplementary_figures']),17);self.assertEqual(len(cov['supplementary_videos']),5)
    def test_actor_projection_schema_and_no_targets(self):
        actor=read('agent_visible.json');self.assertEqual(set(actor),{'schema_version','task_id','title','goal','allowed_operations','stop_when','source_outcomes_exposed','can_declare_measurement','can_declare_service_qualification','can_supply_physical_observation','physical_implementation','scene_assets_are_static_placeholders'})
        for key in ('source_outcomes_exposed','can_declare_measurement','can_declare_service_qualification','can_supply_physical_observation','physical_implementation'):self.assertIs(actor[key],False)
        self.assertEqual(read('evaluator_reference.json')['actor_projection'],['agent_visible.json']);self.assertEqual(set(actor['allowed_operations']),{r['id'] for r in read('operations.json')['operations']})
        for marker in ('source_outcomes.json','receipts','fit_modulus'):self.assertNotIn(marker,json.dumps(actor))
    def test_all_evidence_ids_resolve_and_captions_have_source_locators(self):
        entries=read('evidence_map.json')['entries'];ids={e['id'] for e in entries};self.assertEqual(len(ids),len(entries))
        def references(value):
            if isinstance(value,dict):
                yield from value.get('source_evidence_ids',[])
                for item in value.values():yield from references(item)
            elif isinstance(value,list):
                for item in value:yield from references(item)
        for path in ROOT.glob('*.json'):
            with self.subTest(file=path.name):self.assertLessEqual(set(references(json.loads(path.read_text()))),ids)
        for entry in entries:self.assertNotIn('reading-index item',entry.get('locator',''))
        provenance=read('provenance.json');self.assertEqual(provenance['source_license'],'CC BY-NC-ND 4.0');self.assertFalse(provenance['source_files_exported']);self.assertFalse(provenance['physical_or_numerical_science_executed'])
    def test_all_services_closed_no_hardware(self):
        for row in read('station_contracts.json')['services']:self.assertTrue(row['closed']);self.assertTrue(row['qualification_required']);self.assertFalse(row['hardware_driver']);self.assertFalse(row['request_is_observation'])
        for row in read('asset_binding_plan.json')['scene_assets']:self.assertEqual(row['render_geometry'],'authored_generic');self.assertFalse(row['physical_geometry_validated']);self.assertIsInstance(row['asset_available'],bool)
    def test_conflicts_preserve_final_pattern_parameter_and_radius_scope(self):
        conflicts=read('source_conflicts.json')['items'];self.assertLessEqual({'TETRA_STRAND_COUNT','CUBIC_MODULAR_RULE','PATTERN_AXIS_ORDER','FAILURE_VARIABLE','CONTINUUM_SUPPORT','PLASMA_COATING_ORDER','PATTERN_PARAMETER_MAP','RADIUS_EXAMPLE','NORMALIZATION','GRADIENT_UNITS','SIZE_SCOPE'},{x['id'] for x in conflicts})
        text=(ROOT/'source_conflicts.json').read_text()+(ROOT/'branches.json').read_text()
        for marker in ('8/3','7/3','1/5','1/10','TETRA_STRAND_COUNT','CUBIC_MODULAR_RULE','PATTERN_AXIS_ORDER','FAILURE_VARIABLE','PLASMA_COATING_ORDER'):
            with self.subTest(marker=marker):self.assertIn(marker,text)
if __name__=='__main__':unittest.main()
