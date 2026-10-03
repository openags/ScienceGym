import copy,json,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from record_contract import validate_plateau,validate_transfer,validate_modification
P=pathlib.Path(__file__).resolve().parent.parent

def read(n):return json.loads((P/n).read_text())
def plateau():
    r=dict(id='synthetic-only',attempt_id='a',sample_id='s',assembly_version=2,condition_signature='c',calibration_id='k',step_start_s=0,step_end_s=300,summary_start_s=180,summary_end_s=300,sampling_period_s=10,emitter_area_m2=0.0019634954,temperature_units='C',power_units='W',data_class='synthetic_mock',samples=[],stable=True,shade_valid=True,output_saturated=False,intervention_intervals=[])
    r['samples']=[dict(time_s=t,temperature=20.0,power=0.04,sample_id='s',assembly_version=2,condition_signature='c',calibration_id='k',valid=True) for t in range(180,301,10)]
    return r
class Package(unittest.TestCase):
    def setUp(self):
        self.o=read('operations.json');self.ops={v['id']:v for v in self.o['operations']};self.b=read('branches.json')['branches']
    def test_json_parse(self):
        for f in P.rglob('*.json'):
            if '_work' not in f.parts:json.loads(f.read_text())
    def test_unique_operations(self):self.assertEqual(len(self.ops),self.o['operation_count'])
    def test_eleven_routes(self):self.assertEqual(len(self.b),11)
    def test_physical_inventory(self):
        self.assertEqual({b['id'] for b in self.b},{'BUILD_PAIR','CALIBRATE','OPT_HEMISPHERICAL','OPT_ANGULAR','ENVIRONMENT','TRACKED_STAGNATION','PID_POWER','FIXED_LDPE','MAP_CLEAR_DAY','MAP_CLEAR_NIGHT','MAP_HAZY_NOON'})
    def test_operation_references(self):
        for b in self.b:
            self.assertTrue(b['operation_ids']);self.assertTrue(set(b['operation_ids'])<=self.ops.keys())
    def test_evidence_references(self):
        es=read('provenance.json')['evidence']
        for o in self.ops.values():self.assertTrue(set(o['evidence_ids'])<=es.keys())
    def test_unknown_references(self):
        us={u['id'] for u in read('unknown_parameters.json')['unknowns']}
        for o in self.ops.values():self.assertTrue(set(o['unknown_parameter_ids'])<=us)
    def test_station_references(self):
        st={s['id'] for s in read('station_contracts.json')['stations']}
        for o in self.ops.values():self.assertIn(o['location_id'],st)
    def test_actions_explicit(self):
        for o in self.ops.values():
            for k in ['actor','source_station_id','target_station_id','manipulated_objects','tools_or_interfaces','operator_actions','device_process','preconditions','postconditions','completion_evidence']:self.assertTrue(o[k],(o['id'],k))
            self.assertEqual(o['actor'],'mobile_human_like_robot_operator')
    def test_dag(self):
        edges=read('dependencies.json')['edges'];adj={k:[] for k in self.ops}
        for e in edges:
            self.assertIn(e['from'],self.ops);self.assertIn(e['to'],self.ops);adj[e['from']].append(e['to'])
        seen=set();stack=set()
        def visit(n):
            self.assertNotIn(n,stack)
            if n in seen:return
            stack.add(n)
            for a in adj[n]:visit(a)
            stack.remove(n);seen.add(n)
        for n in adj:visit(n)
    def test_optical_station_binding(self):
        for i in ['OPT_REFERENCE','OPT_MOUNT','OPT_SCAN','OPT_UNLOAD']:self.assertEqual(set(self.ops[i]['station_options']),{'WS_UVVIS','WS_FTIR'})
    def test_robot_output_unload(self):
        self.assertIn('COAT_UNLOAD',self.ops['LAYOUT']['depends_on']);self.assertIn('CAL_UNLOAD',self.ops['TC_ATTACH']['depends_on'])
    def test_parametric_closure(self):
        for i in ['STOP_SAFE','UNMOUNT']:self.assertEqual(self.ops[i]['location_id'],'WS_ACTIVE')
    def test_modified_qc_separate(self):
        self.assertEqual(self.ops['FIXED_QC']['depends_on'],['FIXED_SWAP']);self.assertIn('FIXED_QC',self.ops['BAND_CHECK']['depends_on'])
    def test_source_byte_boundary(self):
        a=read('source_access_audit.json');self.assertIsNone(a['sources'][0]['local_byte_hash']);self.assertEqual(a['sources'][1]['pages'],25)
    def test_models_not_physical(self):
        self.assertTrue(all(v['status'] in ['documented_not_run','concept_only'] for v in read('nonmanual_scope.json')['exclusions']))
    def test_unknown_no_defaults(self):self.assertTrue(all(u['default'] is None for u in read('unknown_parameters.json')['unknowns']))
    def test_night_not_tracking(self):self.assertNotIn('TRACK_ADJUST',next(b for b in self.b if b['id']=='MAP_CLEAR_NIGHT')['operation_ids'])
    def test_boundary(self):
        x=read('RELEASE_BOUNDARY.json')
        for k in ['publisher_bytes','physical_simulation','robot_execution','remote_write','license_modified']:self.assertFalse(x[k])
    def test_actor_no_answer_key(self):self.assertIn('source_outcomes.json',read('agent_visible.json')['forbidden'])
class Records(unittest.TestCase):
    def test_valid_synthetic_plateau(self):self.assertEqual(validate_plateau(plateau()),[])
    def test_missing_fields(self):
        r=plateau();del r['emitter_area_m2'];self.assertTrue(validate_plateau(r))
    def test_shifted_window(self):
        r=plateau();r['summary_start_s']=170;self.assertIn('shifted_summary_window',validate_plateau(r))
    def test_bad_duration(self):
        r=plateau();r['step_end_s']=360;self.assertIn('wrong_step_duration',validate_plateau(r))
    def test_missing_sample(self):
        r=plateau();r['samples'].pop(4);self.assertIn('incomplete_summary_coverage',validate_plateau(r))
    def test_wrong_assembly(self):
        r=plateau();r['samples'][0]['assembly_version']=1;self.assertIn('lineage_mismatch:assembly_version',validate_plateau(r))
    def test_wrong_calibration(self):
        r=plateau();r['samples'][0]['calibration_id']='wrong';self.assertIn('lineage_mismatch:calibration_id',validate_plateau(r))
    def test_source_as_measurement(self):
        r=plateau();r['data_class']='source_reported';self.assertIn('source_or_model_not_observation',validate_plateau(r))
    def test_instability(self):
        r=plateau();r['stable']=False;self.assertIn('not_stable',validate_plateau(r))
    def test_shading_fault(self):
        r=plateau();r['shade_valid']=False;self.assertIn('shade_not_verified',validate_plateau(r))
    def test_intervention(self):
        r=plateau();r['intervention_intervals']=[[200,210]];self.assertIn('intervention_in_summary',validate_plateau(r))
    def test_nonfinite(self):
        r=plateau();r['samples'][0]['power']=float('nan');self.assertIn('nonfinite_sample',validate_plateau(r))
    def test_duplicate(self):
        r=plateau();r['samples'].append(copy.deepcopy(r['samples'][-1]));self.assertIn('duplicate_timestamp',validate_plateau(r))
    def test_transfer_positive(self):
        r=dict(entity_id='s',origin='lab',destination='roof',detach_confirmed=True,output_safe=True,retained_carrier=True,destination_docked=True,identity_at_destination='s');self.assertEqual(validate_transfer(r),[])
    def test_transfer_live_tether(self):
        r=dict(entity_id='s',origin='lab',destination='roof',detach_confirmed=False,output_safe=True,retained_carrier=True,destination_docked=True,identity_at_destination='s');self.assertTrue(validate_transfer(r))
    def test_modification_positive(self):
        r=dict(assembly_id='a',old_version=1,new_version=2,removed_ids=['disk','film'],installed_ids=['band','ldpe'],post_qc_version=2);self.assertEqual(validate_modification(r),[])
    def test_stale_qc(self):
        r=dict(assembly_id='a',old_version=1,new_version=2,removed_ids=['disk'],installed_ids=['band'],post_qc_version=1);self.assertIn('stale_qc',validate_modification(r))
    def test_relabel_only(self):
        r=dict(assembly_id='a',old_version=1,new_version=1,removed_ids=['disk'],installed_ids=['disk'],post_qc_version=1);self.assertIn('same_component_relabelled',validate_modification(r))
if __name__=='__main__':unittest.main(verbosity=2)
