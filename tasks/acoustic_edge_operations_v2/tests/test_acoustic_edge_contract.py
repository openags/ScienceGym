"""Adversarial tests use invented records only; no acoustic solver or hardware."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,shutil,tempfile,unittest
from record_contract import validate_run,validate_transfer,validate_derivative,modal_amplitudes,project_actor
from verify_package import verify,EXPECTED
ROOT=Path(__file__).resolve().parents[1]

def load(name):return json.loads((ROOT/name).read_text())

def run_fixture(branch='DISC_2D'):
    typ='sweep' if branch in ['NO_OBJECT','HALF_APERTURE'] else ('scan_1d' if branch.endswith('1D') else 'scan_2d')
    coords=[[],[]] if typ=='sweep' else [[0.0],[0.6]] if typ=='scan_1d' else [[0.0,0.0],[1.6,0.0]]
    bind={'guide_id':'G-SYNTH','guide_version':1,'target_id':None if branch=='NO_OBJECT' else 'T-SYNTH','target_version':None if branch=='NO_OBJECT' else 1,'rig_signature':'RIG-SYNTH-1','channel_map_id':'MAP-SYNTH-1','calibration_id':'CAL-SYNTH-1','reference_id':'REF-SYNTH-1'}
    r={**bind,'branch_id':branch,'acquisition_type':typ,'data_class':'synthetic_mock','sensor_serials':['S1','S2','S3','S4'],'physical_step_mm':None if typ=='sweep' else 0.6 if typ=='scan_1d' else 1.6,'repeat_count':1,'source_enabled':True,'configuration_valid':True,'condition_verified':True,'schedule':[],'records':[],'calibration':{'calibration_id':bind['calibration_id'],'channel_map_id':bind['channel_map_id'],'sensor_serials':['S1','S2','S3','S4'],'guide_version':1,'valid':True,'valid_from':0,'valid_until':100},'final_state':{'source_off':True,'motion_stopped':True,'target_stored_or_absent':True,'records_archived':True}}
    for i,c in enumerate(coords):
        q={'point_id':str(i),'coordinates_mm':c,'frequency_hz':7000+100*i if typ=='sweep' else 7740}
        r['schedule'].append(q)
        r['records'].append({**bind,**q,'raw_id':'RAW-SYNTH-'+str(i),'attempt_id':'ATTEMPT-SYNTH-1','timestamp':10+i,'complex_pressures':[[2,1],[3,-1],[0,1],[1,1]],'sensor_serials':['S1','S2','S3','S4'],'data_class':'synthetic_mock','valid':True,'failure_reason':None,'settled':True,'reference_locked':True,'clipped':False,'motion_stopped':True})
    return r

def transfer_fixture():return {'entity_id':'G-SYNTH','origin':'print','destination':'inspection','identity_at_destination':'G-SYNTH','detached':True,'source_safe':True,'retained':True,'docked':True,'old_version':1,'new_version':1}
def derivative_fixture():return {'data_class':'derived_analysis','raw_parent_ids':['R1','R2'],'processing_version':'P-SYNTH-1','acquisition_step_mm':1.6,'display_step_mm':0.8,'creates_measured_samples':False,'validity_mask_preserved':True}

class AcquisitionTests(unittest.TestCase):
    def test_all_seven_synthetic_branches_pass(self):
        for b in ['NO_OBJECT','HALF_APERTURE','SINGLE_EDGE_1D','PLATE_32_1D','ROD_10_1D','DISC_2D','ETH_2D']:
            with self.subTest(branch=b):self.assertEqual(validate_run(run_fixture(b)),[])
    def test_null_schedule_rejected(self):
        r=run_fixture();r['schedule']=None;self.assertIn('empty_or_unknown_schedule',validate_run(r))
    def test_empty_schedule_rejected(self):
        r=run_fixture();r['schedule']=[];self.assertTrue(validate_run(r))
    def test_missing_raw_point_rejected(self):
        r=run_fixture();r['records'].pop();self.assertIn('missing_valid_schedule_point',validate_run(r))
    def test_duplicate_record_rejected(self):
        r=run_fixture();r['records'].append(deepcopy(r['records'][0]));self.assertIn('duplicate_raw_id',validate_run(r))
    def test_duplicate_scheduled_point_rejected(self):
        r=run_fixture();r['schedule'].append(deepcopy(r['schedule'][0]));self.assertIn('duplicate_schedule_point',validate_run(r))
    def test_magnitude_only_rejected(self):
        r=run_fixture();r['records'][0]['complex_pressures']=[1,2,3,4];self.assertIn('complex_four_channels_required',validate_run(r))
    def test_missing_channel_rejected(self):
        r=run_fixture();r['records'][0]['complex_pressures'].pop();self.assertTrue(validate_run(r))
    def test_nan_pressure_rejected(self):
        r=run_fixture();r['records'][0]['complex_pressures'][0][1]=float('nan');self.assertTrue(validate_run(r))
    def test_bool_pressure_rejected(self):
        r=run_fixture();r['records'][0]['complex_pressures'][0][0]=True;self.assertTrue(validate_run(r))
    def test_duplicated_sensor_rejected(self):
        r=run_fixture();r['sensor_serials']=['S1']*4;self.assertIn('four_unique_sensors_required',validate_run(r))
    def test_stale_raw_version_rejected(self):
        r=run_fixture();r['records'][0]['guide_version']=0;self.assertIn('raw_binding_mismatch:guide_version',validate_run(r))
    def test_stale_channel_map_rejected(self):
        r=run_fixture();r['calibration']['channel_map_id']='old';self.assertIn('calibration_binding_mismatch:channel_map_id',validate_run(r))
    def test_expired_calibration_rejected(self):
        r=run_fixture();r['calibration']['valid_until']=5;self.assertIn('expired_calibration',validate_run(r))
    def test_unsettled_point_rejected(self):
        r=run_fixture();r['records'][0]['settled']=False;self.assertIn('invalid_point_gate:settled',validate_run(r))
    def test_lost_reference_rejected(self):
        r=run_fixture();r['records'][0]['reference_locked']=False;self.assertTrue(validate_run(r))
    def test_clipping_rejected(self):
        r=run_fixture();r['records'][0]['clipped']=True;self.assertIn('clipped_or_unknown',validate_run(r))
    def test_wrong_actual_coordinate_rejected(self):
        r=run_fixture();r['records'][0]['coordinates_mm']=[0,99];self.assertIn('wrong_actual_condition',validate_run(r))
    def test_display_step_rejected_as_acquisition(self):
        r=run_fixture();r['physical_step_mm']=0.8;self.assertIn('display_grid_used_for_acquisition',validate_run(r))
    def test_falsely_labelled_grid_rejected(self):
        r=run_fixture();r['schedule'][1]['coordinates_mm']=[0.8,0];r['records'][1]['coordinates_mm']=[0.8,0];self.assertIn('coordinates_not_on_physical_grid',validate_run(r))
    def test_numerical_record_rejected(self):
        r=run_fixture();r['data_class']='numerical_prediction';self.assertIn('not_acquisition_data',validate_run(r))
    def test_literature_record_rejected(self):
        r=run_fixture();r['records'][0]['data_class']='literature_reference';self.assertTrue(validate_run(r))
    def test_missing_repeat_count_rejected(self):
        r=run_fixture();r['repeat_count']=None;self.assertIn('unresolved_repeat_count',validate_run(r))
    def test_zero_repeats_rejected(self):
        r=run_fixture();r['repeat_count']=0;self.assertTrue(validate_run(r))
    def test_repeat_count_cannot_inflate_single_run(self):
        r=run_fixture();r['repeat_count']=2;self.assertIn('repeat_expansion_not_implemented_in_single_run_validator',validate_run(r))
    def test_baseline_with_target_rejected(self):
        r=run_fixture('NO_OBJECT');r['target_id']='T-SYNTH';self.assertIn('baseline_contains_target',validate_run(r))
    def test_safe_shutdown_required(self):
        r=run_fixture();r['final_state']['source_off']=False;self.assertIn('unsafe_or_incomplete_closure',validate_run(r))
    def test_retained_invalid_attempt_then_valid_retry(self):
        r=run_fixture();q=deepcopy(r['records'][0]);q.update(raw_id='FAILED',attempt_id='FAILED-ATTEMPT',timestamp=9,valid=False,failure_reason='reference_not_locked',reference_locked=False);r['records'].insert(0,q);self.assertEqual(validate_run(r),[])
    def test_invalid_attempt_never_completes_point(self):
        r=run_fixture();r['records'][0].update(valid=False,failure_reason='lost_reference');self.assertIn('missing_valid_schedule_point',validate_run(r))
    def test_success_does_not_require_paper_trend(self):
        r=run_fixture();r['records'][0]['complex_pressures']=[[0,0]]*4;self.assertEqual(validate_run(r),[])
    def test_malformed_run_returns_errors(self):
        self.assertTrue(validate_run(None));self.assertTrue(validate_run({}))

class DerivedAndHandlingTests(unittest.TestCase):
    def test_complex_mode_algebra_retains_phase(self):
        d=modal_amplitudes([[2,2],[4,-2],[0,2],[2,2]])
        self.assertEqual(d['a00_pair13'],1+2j);self.assertEqual(d['a01'],1+0j);self.assertEqual(d['a10'],1-2j)
    def test_pair_disagreement_not_silently_erased(self):
        d=modal_amplitudes([[2,0],[8,0],[0,0],[0,0]]);self.assertNotEqual(d['a00_pair13'],d['a00_pair24'])
    def test_bad_mode_channels_raise(self):
        with self.assertRaises(ValueError):modal_amplitudes([1,2,3,4])
    def test_transfer_passes(self):self.assertEqual(validate_transfer(transfer_fixture()),[])
    def test_tethered_transfer_rejected(self):
        r=transfer_fixture();r['detached']=False;self.assertIn('unsafe_transfer',validate_transfer(r))
    def test_identity_swap_rejected(self):
        r=transfer_fixture();r['identity_at_destination']='OTHER';self.assertTrue(validate_transfer(r))
    def test_transport_cannot_rewrite_history(self):
        r=transfer_fixture();r['new_version']=2;self.assertTrue(validate_transfer(r))
    def test_display_derivation_passes(self):self.assertEqual(validate_derivative(derivative_fixture(),['R1','R2'],'scan_2d'),[])
    def test_interpolation_cannot_mint_measurements(self):
        d=derivative_fixture();d['creates_measured_samples']=True;self.assertTrue(validate_derivative(d,['R1','R2'],'scan_2d'))
    def test_derivative_requires_exact_raw_parents(self):
        d=derivative_fixture();d['raw_parent_ids']=['OTHER'];self.assertTrue(validate_derivative(d,['R1','R2'],'scan_2d'))
    def test_invalid_mask_cannot_disappear(self):
        d=derivative_fixture();d['validity_mask_preserved']=False;self.assertTrue(validate_derivative(d,['R1','R2'],'scan_2d'))

class StaticAndBoundaryTests(unittest.TestCase):
    def test_static_and_exact_manifest(self):self.assertEqual(verify(ROOT),[])
    def test_source_byte_honesty(self):
        a=load('source_access_audit.json');self.assertIsNone(a['main']['source_byte_sha256']);self.assertFalse(a['main']['local_pdf_bytes_obtained'])
    def test_all_eight_conflicts_retained(self):self.assertEqual(len(load('source_conflicts.json')['conflicts']),8)
    def test_numerical_branches_are_separate(self):
        n=load('nonmanual_scope.json');self.assertEqual(len(n['numerical_branches']),3);self.assertFalse(n['numerical_execution_authorized_or_performed'])
    def test_actor_goal_has_no_reference_route(self):
        goal=load('agent_visible.json')['goals'][0];goal['reference_route']=['SECRET'];goal['expected_scientific_outcomes']=[3]
        out=project_actor(goal,{}, {}, []);self.assertNotIn('SECRET',json.dumps(out));self.assertNotIn('expected_scientific_outcomes',json.dumps(out))
    def test_actor_nested_card_oracle_rejected(self):
        g=load('agent_visible.json')['goals'][0]
        with self.assertRaises(ValueError):project_actor(g,{}, {'x':{'source_outcomes':[3]}}, [])
    def test_all_loop_input_keys_exist(self):
        cards={c['id']:c for c in load('episode_input_contract.json')['cards']}
        for l in load('branches.json')['loops']:
            if 'input' in l:
                card,key=l['input'].split('.');fields=cards[card]['required_fields']+[x for values in cards[card].get('conditional_required_fields',{}).values() for x in values];self.assertIn(key,fields)
    def test_sweep_homing_card_does_not_require_scan_schedule(self):
        c=next(x for x in load('episode_input_contract.json')['cards'] if x['id']=='scan_card');self.assertNotIn('ordered_coordinates',c['required_fields']);self.assertIn('ordered_coordinates',c['conditional_required_fields']['scan_1d_or_scan_2d'])
    def test_abort_archive_needs_no_analysis_recipe(self):
        o=next(x for x in load('operations.json')['operations'] if x['id']=='ARCHIVE');self.assertNotIn('U_ANALYSIS',o['unknown_parameter_ids'])
    def test_supplied_target_has_nonfabrication_route(self):
        f=next(x for x in load('branches.json')['families'] if x['id']=='F_TARGET');r=f['route_variants']['supplied_part'];self.assertIn('TARGET_RECEIVE',r);self.assertNotIn('TARGET_PROCESS',r)
    def test_target_release_precedes_transfer(self):
        f=next(x for x in load('branches.json')['families'] if x['id']=='F_TARGET');r=f['route_variants']['manufactured_in_episode'];self.assertLess(r.index('TARGET_RELEASE'),r.index('TRANSFER'))
    def test_calibration_in_situ(self):
        op=next(x for x in load('operations.json')['operations'] if x['id']=='CALIBRATE');self.assertEqual(op['station_id'],'WS_RIG')
    def test_calibration_outputs_not_initial_gates(self):
        c=next(x for x in load('episode_input_contract.json')['cards'] if x['id']=='calibration_card');self.assertNotIn('raw_standard_records',c['required_fields']);self.assertIn('raw_standard_records',c['generated_result_fields'])
    def test_abort_does_not_require_enabled_source(self):
        ops={o['id']:o for o in load('operations.json')['operations']};self.assertEqual(ops['ABORT_CLOSE']['depends_on'],[]);self.assertEqual(ops['ARCHIVE']['depends_on'],[]);self.assertEqual(ops['STOP']['depends_on'],[])
    def test_actor_required_preparation_cards(self):
        for g in load('agent_visible.json')['goals']:
            self.assertIn('fabrication_card',g['required_public_cards']);self.assertIn('scan_card',g['required_public_cards'])
            if g['id'] in ['DISC_2D','ETH_2D']:self.assertIn('resolution_card',g['required_public_cards'])
    def test_extra_file_fails_exact_allowlist(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'p';shutil.copytree(ROOT,p);(p/'extra.txt').write_text('not allowed');self.assertTrue(any('exact_path_set' in e for e in verify(p)))
    def test_broadened_manifest_still_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'p';shutil.copytree(ROOT,p);m=json.loads((p/'EXPORT_ALLOWLIST.json').read_text());m['allowlist'].append('extra.txt');(p/'EXPORT_ALLOWLIST.json').write_text(json.dumps(m));self.assertIn('manifest_allowlist_broadened',verify(p))
    def test_modified_payload_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'p';shutil.copytree(ROOT,p);q=p/'README.md';q.write_text(q.read_text()+'\nChanged\n');self.assertIn('payload_hash:README.md',verify(p))
    def test_symlink_payload_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'p';shutil.copytree(ROOT,p);q=p/'README.md';q.unlink();q.symlink_to(p/'TASK_DESIGN.md');self.assertIn('symlink:README.md',verify(p))
    def test_missing_payload_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'p';shutil.copytree(ROOT,p);(p/'README.md').unlink();self.assertTrue(any('exact_path_set' in e for e in verify(p)))

if __name__=='__main__':unittest.main(verbosity=2)
