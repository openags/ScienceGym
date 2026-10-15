import copy
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import planner
import solar_geometry

class PilotTests(unittest.TestCase):
    def setUp(self):self.plan=planner.compile_reference(planner.fixture())
    def event(self,oid):return next(e for e in self.plan['occurrences'] if e['operation_id']==oid)
    def rejects(self):
        with self.assertRaises(planner.PlanError):planner.verify_plan(self.plan)
    def test_complete_symbolic_campaign(self):
        result=planner.verify_plan(self.plan)
        self.assertEqual(result['physical_successes'],0)
        self.assertEqual(self.plan['counts']['operation_definitions_used'],63)
    def test_missing_coat_rejected(self):
        self.event('COAT_RUN')['coat_iterations'].pop();self.rejects()
    def test_unprepared_optical_witness_rejected(self):
        self.plan['occurrences']=[e for e in self.plan['occurrences'] if not(e['operation_id']=='COAT_UNLOAD' and e['payload_ids']==['W_white'])];self.rejects()
    def test_missing_witness_parent_lot(self):
        self.event('WITNESS_PREP')['parent_material_lots'].pop('W_white');self.rejects()
    def test_nonempty_repeats(self):
        f=planner.fixture();f['optical_repeats']=0
        with self.assertRaises(planner.PlanError):planner.compile_reference(f)
    def test_missing_pid_target_rejected(self):
        f=planner.fixture();f['pid_targets_K_relative_ambient']=[]
        with self.assertRaises(planner.PlanError):planner.compile_reference(f)
    def test_pid_target_order(self):
        f=planner.fixture();f['pid_targets_K_relative_ambient']=[1,-1]
        with self.assertRaises(planner.PlanError):planner.compile_reference(f)
    def test_physical_claim_rejected(self):
        f=planner.fixture();f['qualified_for_execution']=True
        with self.assertRaises(planner.PlanError):planner.compile_reference(f)
    def test_stale_optical_reference(self):
        self.event('ANGLE_SCAN')['reference_configuration_id']='previous_accessory';self.rejects()
    def test_no_optical_reference(self):
        self.plan['occurrences']=[e for e in self.plan['occurrences'] if e['operation_id']!='OPT_REFERENCE'];self.rejects()
    def test_missing_one_optical_condition(self):
        self.plan['occurrences'].remove(self.event('OPT_SCAN'));self.rejects()
    def test_missing_one_angular_condition(self):
        self.plan['occurrences'].remove(self.event('ANGLE_SCAN'));self.rejects()
    def test_missing_one_map_condition(self):
        self.plan['occurrences'].remove(self.event('MAP_LOG'));self.rejects()
    def test_missing_pid_plateau(self):
        self.plan['occurrences'].remove(self.event('PID_STEP'));self.rejects()
    def test_shared_pid_controller(self):
        self.event('PID_STEP')['independent_controller_ids']=['SMU_W','SMU_W'];self.rejects()
    def test_missing_restoration(self):
        self.plan['occurrences']=[e for e in self.plan['occurrences'] if e['operation_id']!='RESTORE_TRACKED'];self.rejects()
    def test_heater_left_on_map_assembly(self):
        self.plan['occurrences']=[e for e in self.plan['occurrences'] if e['operation_id']!='HEATER_REMOVE'];self.rejects()
    def test_missing_assembly_inspection(self):
        self.plan['occurrences']=[e for e in self.plan['occurrences'] if e['operation_id']!='ASSEMBLY_QC'];self.rejects()
    def test_duplicate_map_probe(self):
        e=self.event('MAP_LOG');e['sensor_ids'][-1]=e['sensor_ids'][0];self.rejects()
    def test_map_duration(self):
        self.event('MAP_LOG')['duration_s']=300;self.rejects()
    def test_pid_duration(self):
        self.event('PID_STEP')['duration_s']=120;self.rejects()
    def test_missing_transfer(self):
        e=self.event('MOVE');self.plan['occurrences'].remove(e);self.rejects()
    def test_wrong_transfer_origin(self):
        self.event('MOVE')['origin']='WS_OUTDOOR';self.rejects()
    def test_fabricated_attempt(self):
        self.event('STAG_LOG')['attempts']=[{'success':True}];self.rejects()
    def test_duplicate_occurrence_id(self):
        self.plan['occurrences'][1]['id']=self.plan['occurrences'][0]['id'];self.rejects()
    def test_one_film_layer(self):
        s=planner.initial_states()['white'];s['film_layers']=1
        with self.assertRaises(planner.PlanError):planner.validate_state(s)
    def test_unsupported_payload(self):
        s=planner.initial_states()['white'];s['supported']=False
        with self.assertRaises(planner.PlanError):planner.validate_state(s)
    def test_no_energized_transfer(self):
        states=planner.initial_states();states['white']['heater_output']=True
        with self.assertRaises(planner.PlanError):planner.transition(states,{'operation_id':'MOVE','payload_ids':['white'],'origin':'WS_STOCK','destination':'WS_ASSEMBLY'})
    def test_stale_qc(self):
        s=planner.initial_states()['white'];s.update(location='WS_OUTDOOR',film_layers=2,assembly_revision=3,qc_revision=2,probe_calibration='cal')
        with self.assertRaises(planner.PlanError):planner.validate_state(s,True)
    def test_actor_projection_strips_trusted_records(self):
        episode={'selected_branches':['PID_POWER'],'source_outcomes':{'T':-20},'reference_plan':self.plan,
                 'qualified_parameter_cards':{'card':{'target':0,'future_records':[1],'hidden_state':42}}}
        projected=planner.actor_projection(episode)
        self.assertEqual(projected,{'selected_branches':['PID_POWER'],'qualified_parameter_cards':{'card':{'target':0}}})
        projected['selected_branches'].append('X');self.assertEqual(episode['selected_branches'],['PID_POWER'])
    def test_physical_metric_units(self):
        m=planner.scientific_metrics(1,.1,.05,800,700,'sun_normal')
        self.assertAlmostEqual(m['heater_power_W_m2'],.1/(math.pi*.025**2))
        self.assertEqual(m['diffuse_W_m2'],100)
    def test_ghi_cannot_replace_gti(self):
        with self.assertRaises(planner.PlanError):planner.scientific_metrics(1,.1,.05,800,700,'horizontal')
    def test_zero_area_rejected(self):
        with self.assertRaises(planner.PlanError):planner.scientific_metrics(1,.1,0,800,700,'sun_normal')
    def test_valid_negative_diffuse_is_not_clipped(self):
        m=planner.scientific_metrics(1,.1,.05,690,700,'sun_normal');self.assertEqual(m['diffuse_W_m2'],-10)
    def test_nonfinite_measurement(self):
        with self.assertRaises(planner.PlanError):planner.scientific_metrics(float('nan'),.1,.05,800,700,'sun_normal')
    def test_solar_track_intersection(self):
        r=solar_geometry.track_points([{'time_id':'t','azimuth_deg':90,'elevation_deg':45}],.15)
        p=r['samples'][0]['position_m'];self.assertAlmostEqual(p[0],.15);self.assertAlmostEqual(p[1],0)
        self.assertTrue(r['samples'][0]['sampled_full_aperture_shade'])
    def test_low_sun_aperture_shading_fails(self):
        r=solar_geometry.track_points([{'time_id':'t','azimuth_deg':180,'elevation_deg':10}],.15)
        self.assertFalse(r['samples'][0]['sampled_full_aperture_shade'])
    def test_below_horizon_rejected(self):
        with self.assertRaises(ValueError):solar_geometry.track_points([{'time_id':'t','azimuth_deg':180,'elevation_deg':-1}],.15)

if __name__=='__main__':unittest.main()
